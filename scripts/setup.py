"""One-time setup for wechat-article-reader skill.

Installs wechat-reader, applies Windows Chrome path patch, installs Playwright.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent  # wechat-article-reader/
WECHAT_READER_DIR = SKILL_DIR.parent / "wechat-reader"
BROWSER_BRIDGE = WECHAT_READER_DIR / "wechat_reader" / "browser_bridge.py"


def clone_wechat_reader():
    if WECHAT_READER_DIR.exists():
        print(f"[OK] wechat-reader already cloned at {WECHAT_READER_DIR}")
        return
    print("[*] Cloning wechat-reader from GitHub...")
    subprocess.run(
        ["git", "clone", "https://github.com/xiguawang/wechat-reader.git"],
        cwd=WECHAT_READER_DIR.parent,
        check=True,
    )
    print("[OK] Cloned.")


def install_wechat_reader():
    print("[*] Installing wechat-reader (pip install -e .)...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        cwd=WECHAT_READER_DIR,
        check=True,
    )
    print("[OK] Installed.")


def apply_windows_patch():
    if platform.system() != "Windows":
        print("[SKIP] Not Windows; no patch needed.")
        return

    bridge_path = BROWSER_BRIDGE
    if not bridge_path.exists():
        print(f"[WARN] bridge file not found at {bridge_path}; skipping patch.")
        return

    content = bridge_path.read_text(encoding="utf-8")

    # Check if patch already applied
    if "LOCALAPPDATA" in content:
        print("[OK] Windows Chrome path patch already applied.")
        return

    # Add import os if missing
    if "import os" not in content:
        content = content.replace(
            "import asyncio\nimport json",
            "import asyncio\nimport json\nimport os",
            1,
        )

    # Add Windows Chrome paths
    old_candidates = """def browser_executable_candidates() -> list[str]:
    candidates = [
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    return [candidate for candidate in candidates if candidate and Path(candidate).exists()]"""

    new_candidates = """def browser_executable_candidates() -> list[str]:
    candidates = [
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\\Google\\Chrome\\Application\\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\\Google\\Chrome\\Application\\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\\Google\\Chrome\\Application\\chrome.exe"),
    ]
    return [candidate for candidate in candidates if candidate and Path(candidate).exists()]"""

    if old_candidates in content:
        content = content.replace(old_candidates, new_candidates)
        bridge_path.write_text(content, encoding="utf-8")
        print("[OK] Windows Chrome path patch applied.")
    else:
        print("[WARN] Could not find the candidate list to patch. It may have already been modified.")


def install_playwright_chromium():
    print("[*] Installing Playwright Chromium browser...")
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("[OK] Playwright Chromium installed.")
    else:
        print(f"[WARN] Playwright install output: {result.stdout[-200:]}{result.stderr[-200:]}")
        print("     You may need to run: python -m playwright install chromium")


def main():
    print("=== wechat-article-reader setup ===\n")

    # Step 1: Clone wechat-reader
    clone_wechat_reader()

    # Step 2: Install
    install_wechat_reader()

    # Step 3: Windows patch
    apply_windows_patch()

    # Step 4: Playwright Chromium
    install_playwright_chromium()

    print("\n=== Setup complete ===")
    print("You can now use: python scripts/read_article.py <wechat_url>")
    print()
    print("NOTE: The first time you read an article, a Chrome browser will open.")
    print("      If a captcha appears, manually solve it in the browser window.")


if __name__ == "__main__":
    main()
