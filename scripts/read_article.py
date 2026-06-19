"""
Read a WeChat Official Account article and extract only code blocks.

Usage:
    python read_article.py <url> [options]

The code file is saved, then the AI should read it, analyze the content,
summarize keywords, and rename the file accordingly.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
WECHAT_READER_DIR = SKILL_DIR.parent / "wechat-reader"
if WECHAT_READER_DIR.exists():
    sys.path.insert(0, str(WECHAT_READER_DIR))


# ── Language detection ──────────────────────────────────────────────

LANG_PATTERNS = {
    "R": [
        r"library\(.*\)", r"require\(.*\)", r"<- function\b",
        r"ggplot\(.*\)", r"%>%", r"data\.frame\b", r"paste0?\(",
        r"BiocManager\b", r"file\.path\b", r"set\.seed\b",
    ],
    "Python": [
        r"import \w+", r"from \w+ import", r"def \w+\(.*\)",
        r"class \w+", r"if __name__", r"print\(f",
    ],
}


def detect_language(lines: list[str]) -> str:
    text = "\n".join(lines).lower()
    lang_scores = {}
    for lang, patterns in LANG_PATTERNS.items():
        lang_scores[lang] = sum(1 for p in patterns if re.search(p, text, re.I))
    return max(lang_scores, key=lang_scores.get) if max(lang_scores.values()) > 3 else "Unknown"


# ── Code extraction ─────────────────────────────────────────────────

SECTION_HEADER = re.compile(r"^#{3,}\s*[-=]+\s*$|^#{3,}\s*第.{1,4}部分|^#{3,}\s*(?:步骤|Step)\s*\d+|^#{3,}\s*(?:Part|Section)\s*\d+", re.I)
NUMBERED_LIST = re.compile(r"^\d{1,2}\.[\u4e00-\u9fffA-Za-z]")
PROMO_KEYWORDS = ["粉丝群", "公众号", "视频号", "联系作者", "可加我", "扫码", "付费合集", "课程上线"]
CODE_MARKER = re.compile(r"(?:\w+\s*(?:<-|=)\s*)?function\b|library\(|import\s|^#{3,}\s*=")


def is_code_section_line(line: str) -> bool:
    """Line is keepable within a code section."""
    stripped = line.strip()
    if not stripped:
        return True
    if SECTION_HEADER.match(stripped):
        return True
    if stripped.startswith("#"):
        return True
    if re.search(r"[\u4e00-\u9fff]", stripped):
        return False
    return True


def is_promo_section(lines: list[str], idx: int) -> bool:
    """Check if current position is in the promotion/ad section."""
    window = " ".join(lines[idx:idx+5])
    return any(kw in window for kw in PROMO_KEYWORDS)


def is_numbered_method_list(lines: list[str], idx: int) -> bool:
    """Check if current position is the numbered method list (e.g. '1. 序列比对...')."""
    count = 0
    for i in range(idx, min(idx + 40, len(lines))):
        if NUMBERED_LIST.match(lines[i].strip()):
            count += 1
            if count >= 5:
                return True
        else:
            count = 0
    return False


def extract_code(content: str) -> str:
    lines = content.split("\n")
    lang = detect_language(lines)

    # Find first code section marker
    code_start = 0
    for i, line in enumerate(lines):
        if CODE_MARKER.search(line):
            code_start = max(0, i - 2)  # include a few lines before
            break
    # Fallback: find section header
    if code_start == 0:
        for i, line in enumerate(lines):
            if SECTION_HEADER.match(line.strip()):
                code_start = i
                break

    code_lines = []
    in_code = True
    for i, line in enumerate(lines[code_start:], start=code_start):
        stripped = line.strip()

        # Stop at promo/ad section
        if is_promo_section(lines, i):
            break
        # Stop at numbered method list
        if is_numbered_method_list(lines, i):
            break

        if is_code_section_line(line):
            code_lines.append(line)
        else:
            code_lines.append("")

    return "\n".join(code_lines).strip()


# ── Main ─────────────────────────────────────────────────────────────

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip("._ ")[:80]


def parse_args():
    parser = argparse.ArgumentParser(description="Extract code from WeChat article")
    parser.add_argument("url", help="WeChat article URL")
    parser.add_argument("--output", "-o", default=None, help="Output file path")
    parser.add_argument("--timeout", "-t", type=int, default=120, help="Captcha wait timeout (default: 120)")
    parser.add_argument("--strategy", "-s", default="auto", choices=["auto", "attach", "launch", "playwright"])
    parser.add_argument("--raw", action="store_true", help="Save raw content alongside code")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        from wechat_reader import read_article_sync
    except ImportError:
        print("ERROR: wechat_reader not installed. Run python scripts/setup.py first.")
        sys.exit(1)

    print(f"Reading article: {args.url[:80]}...")
    print()
    print("A Chrome browser will open. If a captcha appears,")
    print("please complete the verification in the browser window.")
    print(f"The script will wait up to {args.timeout} seconds.")
    print()

    result = read_article_sync(args.url, strategy=args.strategy, wait_for_manual_verify=args.timeout, timeout=30)

    print(f"\nStatus: {result.status}")

    if result.status != "ok" or not result.content:
        print(f"Hint: {result.hint}" if result.hint else f"No content. Status: {result.status}")
        return

    # Extract code
    code = extract_code(result.content)
    lang = detect_language(code.split("\n"))

    if not code.strip():
        code = result.content
        lang = "Unknown"

    print(f"Article: {result.title}")
    print(f"Author: {result.author}")
    print(f"Language: {lang}")
    print(f"Code length: {len(code)} chars ({len(code.splitlines())} lines)")

    # Save code to temp/default file; AI will rename it after analysis
    output_path = args.output or "wechat_code_extracted.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"\nSaved code to: {output_path}")

    # Save metadata
    meta = {
        "source_url": args.url,
        "article_title": result.title,
        "author": result.author,
        "account_name": result.account_name,
        "publish_time": result.publish_time,
        "fetched_at": result.fetched_at,
        "language": lang,
        "code_lines": len(code.splitlines()),
        "code_file": output_path,
    }
    meta_path = Path(output_path).with_suffix(".json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"Saved metadata to: {meta_path}")

    # Save raw if requested
    if args.raw:
        raw_path = Path(output_path).with_suffix(".raw.txt")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(result.content)
        print(f"Saved raw article to: {raw_path}")

    print("\n--- First 10 lines ---")
    for line in code.split("\n")[:10]:
        print(line)

    print(f"\n=== NEXT STEP: Read the saved code file, analyze its content to")
    print(f"    identify key functions/packages/algorithms, then compose a")
    print(f"    keyword-based filename and rename the .txt file accordingly. ===")


if __name__ == "__main__":
    main()
