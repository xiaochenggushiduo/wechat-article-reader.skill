"""
Convenience script to read a WeChat Official Account article using wechat-reader.

Usage:
    python read_article.py <url> [--output <path>] [--timeout <seconds>]

Examples:
    python read_article.py "https://mp.weixin.qq.com/s?__biz=..."
    python read_article.py "https://mp.weixin.qq.com/s/SHORTID"
    python read_article.py "https://mp.weixin.qq.com/s?__biz=..." --output article.txt --timeout 60
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Find wechat-reader (sibling directory to this skill)
SKILL_DIR = Path(__file__).resolve().parent.parent
WECHAT_READER_DIR = SKILL_DIR.parent / "wechat-reader"

if WECHAT_READER_DIR.exists():
    sys.path.insert(0, str(WECHAT_READER_DIR))
else:
    # Fallback: maybe installed as package
    pass


def parse_args():
    parser = argparse.ArgumentParser(description="Read WeChat Official Account article")
    parser.add_argument("url", help="WeChat article URL (mp.weixin.qq.com/...)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output file path (default: article_<timestamp>.txt)")
    parser.add_argument("--timeout", "-t", type=int, default=120,
                        help="Timeout in seconds for manual captcha verification (default: 120)")
    parser.add_argument("--json", action="store_true",
                        help="Also save article metadata as JSON")
    parser.add_argument("--strategy", "-s", default="auto",
                        choices=["auto", "attach", "launch", "playwright"],
                        help="Browser strategy (default: auto)")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        from wechat_reader import read_article_sync
    except ImportError:
        print("ERROR: wechat_reader is not installed.")
        print("Run setup script first:")
        print(f"  python {SKILL_DIR / 'scripts' / 'setup.py'}")
        sys.exit(1)

    url = args.url

    print(f"Reading article: {url[:80]}...")
    print()
    print("A Chrome browser will open. If a captcha appears,")
    print("please manually complete the verification in the browser.")
    print(f"The script will wait up to {args.timeout} seconds.")
    print()

    result = read_article_sync(
        url,
        strategy=args.strategy,
        wait_for_manual_verify=args.timeout,
        timeout=30,
    )

    print()
    print(f"Status: {result.status}")

    if result.status == "ok" and result.content:
        print(f"Title: {result.title}")
        print(f"Author: {result.author}")
        print(f"Account: {result.account_name}")
        print(f"Published: {result.publish_time}")
        print(f"Content length: {len(result.content)} chars")
        print()

        # Save content
        output_path = args.output
        if not output_path:
            timestamp = result.fetched_at[:10] if result.fetched_at else "now"
            output_path = f"wechat_article_{timestamp}.txt"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.content)
        print(f"Saved article to: {output_path}")

        # Save metadata as JSON if requested
        if args.json:
            meta = {
                "title": result.title,
                "author": result.author,
                "account_name": result.account_name,
                "publish_time": result.publish_time,
                "fetched_at": result.fetched_at,
                "url": url,
                "content_file": output_path,
            }
            meta_path = Path(output_path).with_suffix(".json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            print(f"Saved metadata to: {meta_path}")

        # Print preview
        print()
        print("--- Preview (first 500 chars) ---")
        print(result.content[:500])

    elif result.hint:
        print(f"Hint: {result.hint}")
        if result.status == "captcha_required":
            print()
            print("A captcha is blocking access. When using this script interactively,")
            print("the browser should open automatically. Complete the verification")
            print("in the browser window and the article will be extracted.")
            print()
            print("To retry with longer wait:")
            print(f"  python {__file__} \"{url}\" --timeout 180")
    else:
        print(f"No content retrieved. Status: {result.status}")


if __name__ == "__main__":
    main()
