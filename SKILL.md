---
name: wechat-article-reader
description: >
  Read/fetch content from WeChat Official Account articles (mp.weixin.qq.com) using a real browser to bypass captcha/IP blocks.
  Trigger when the user needs to extract article content from any WeChat Official Account link, especially when direct HTTP requests (curl/requests/httpx) return captcha pages, blank pages, or login walls.
  Use this skill for ALL weixin/wechat article reading tasks — it handles verification interactively and returns structured article data (title, author, content, publish time).
---

# WeChat Article Reader Skill

Read WeChat Official Account articles that are otherwise blocked by captcha. Uses **wechat-reader** (Playwright + real Chrome browser) to navigate to the article page. When a captcha appears, the user manually completes it in the opened browser window, and the skill waits for resolution before extracting content.

## Dependencies

- Python 3.11+
- Google Chrome (installed on the system)
- `wechat-reader` (cloned from GitHub, installed as editable package)
- `playwright` Python package + bundled Chromium

## Step-by-step Workflow

### Step 1: Setup (one-time)

Run the bundled setup script to install wechat-reader and ensure all dependencies are in place:

```bash
python <skill_path>/scripts/setup.py
```

This will:
1. Clone `wechat-reader` from GitHub if not already installed
2. `pip install -e .` from the wechat-reader directory
3. Apply a **Windows Chrome path patch** (if on Windows) so `wechat-reader` can find Chrome
4. Run `playwright install chromium` to ensure Playwright's browser is ready

### Step 2: Extract article

Use the bundled helper to extract an article:

```python
python <skill_path>/scripts/read_article.py <article_url> [--output <path>]
```

Or use the Python API directly:

```python
import sys
sys.path.insert(0, "<path_to_wechat_reader>")

from wechat_reader import read_article_sync

url = "https://mp.weixin.qq.com/s?__biz=..."
result = read_article_sync(url, strategy="auto", wait_for_manual_verify=120, timeout=30)

if result.status == "ok":
    print(f"Title: {result.title}")
    print(f"Author: {result.author}")
    print(f"Content: {result.content}")
else:
    print(f"Status: {result.status}")
    print(f"Hint: {result.hint}")
```

### Step 3: Handle the captcha (interactive)

When the browser opens and the article page shows a captcha:

1. **The user will see a Chrome window open** with the captcha page
2. **Tell the user explicitly:** "请在浏览器窗口中完成微信安全验证（可能包括点击验证、滑动验证或扫码），验证通过后文章将自动保存"
3. **The script waits up to 120 seconds** for the user to complete verification
4. Once verified, the article content is automatically extracted and saved

**Important:** If this is running in a headless/remote environment (SSH, CI/CD), the captcha cannot be solved interactively. In that case, use the `wechat_reader` `strategy="playwright"` option which may work if the session cookies are still fresh, or warn the user that interactive verification is required.

## Windows-specific Notes

On Windows, the original `wechat-reader` cannot find Chrome because it only checks Linux/macOS paths. The setup script automatically applies a patch to `browser_bridge.py` to add these paths:

```python
"C:/Program Files/Google/Chrome/Application/chrome.exe"
"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
"%LOCALAPPDATA%\\Google\\Chrome\\Application\\chrome.exe"
```

Chrome is typically installed at `C:\Program Files\Google\Chrome\Application\chrome.exe` on Windows.

## Output Format

When `result.status == "ok"`, the skill returns:

| Field | Description |
|---|---|
| `title` | Article title |
| `author` | Author/account name |
| `content` | Full article text (plain text extracted from DOM) |
| `publish_time` | Publication date string |
| `html` | Raw HTML content (optional) |

## Common Status Values

| Status | Meaning | Action |
|---|---|---|
| `ok` | Article retrieved successfully | Use the content |
| `captcha_required` | Captcha page detected | User must solve captcha in browser |
| `rate_limited` | Too many requests | Wait and retry |
| `browser_not_found` | Chrome not installed | Install Chrome, or run Playwright's bundled Chromium |
| `browser_not_ready` | Playwright not set up | Run `python -m playwright install chromium` |
| `navigation_failed` | Could not navigate to URL | Check URL validity |
