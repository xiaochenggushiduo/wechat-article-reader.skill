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

### Step 2: Extract article code

Run the bundled helper to extract code from an article:

```bash
python <skill_path>/scripts/read_article.py <article_url>
```

What the script does:
1. Opens a Chrome browser and navigates to the article
2. If captcha appears, the user manually solves it in the browser
3. **Extracts only code blocks** from the article (strips Chinese prose/commentary)
4. **Detects the programming language** (R / Python / etc.)
5. Saves the code to `wechat_code_extracted.txt` (temporary name)
6. Saves a JSON metadata file alongside it

The script saves code to a default filename. **The AI must then:**

### Step 3: Analyze code & rename file

After the script completes, read the saved code file and:

1. **Read the file** — open `wechat_code_extracted.txt` and examine the code content
2. **Identify key functions** — look for function/method definitions (e.g. `needleman_wunsch <- function(...)`)
3. **Identify key packages/libraries** — look for `library()`, `require()`, `import` statements
4. **Identify the algorithm/technique** — understand what the code does (e.g. "Needleman-Wunsch global alignment")
5. **Compose a keyword-based filename** — join 3-6 key terms with `-`, e.g.:
   - `NeedlemanWunsch-GlobalAlignment-Biostrings.txt`
   - `initialize_matrices-create_alignment_plot-ggplot2.txt`
6. **Rename the file** — use `os.rename()` or `mv` to rename `wechat_code_extracted.txt` to the keyword-based name
7. **Update the JSON metadata** — add the `keywords` field and new filename to the `.json` file

Example interaction:

```
$ python scripts/read_article.py "https://mp.weixin.qq.com/s?__biz=..."
→ Saved code to: wechat_code_extracted.txt

# AI reads the file, sees it's R code with functions:
#   needleman_wunsch(), initialize_matrices(), create_alignment_plot()
#   libraries: Biostrings, ggplot2, tidyverse

# AI renames:
$ mv wechat_code_extracted.txt needleman_wunsch-initialize_matrices-Biostrings-ggplot2.txt
```

### Step 4: Handle the captcha (interactive)

When the browser opens and the article page shows a captcha:

1. **The user will see a Chrome window open** with the captcha page
2. **Tell the user explicitly:** "请在浏览器窗口中完成微信安全验证（可能包括点击验证、滑动验证或扫码），验证通过后文章将自动保存"
3. **The script waits up to 120 seconds** for the user to complete verification
4. Once verified, the article code is automatically extracted and saved
5. **Then proceed to Step 3** — read the file, analyze keywords, and rename

**Important:** If this is running in a headless/remote environment (SSH, CI/CD), the captcha cannot be solved interactively. In that case, use the `wechat_reader` `strategy="playwright"` option which may work if the session cookies are still fresh, or warn the user that interactive verification is required.

## Code Extraction Logic

The skill uses these techniques to separate code from prose:

1. **Section markers** — detects `# =====`, `# 步骤N`, `# 第X部分` as code section boundaries
2. **Language-specific patterns** — recognizes function definitions (`<- function`), library calls (`library()`), ggplot syntax, etc.
3. **Chinese character filter** — lines with Chinese characters (outside comments) are treated as prose and stripped
4. **Keyword extraction** — scans for function names, package names (`library()`), ggplot geoms, and meaningful identifiers

## Keyword-based Filename

The output `.txt` filename is auto-generated from the top 5-8 extracted keywords:

- Function names get highest weight (e.g. `needleman_wunsch`, `create_alignment_plot`)
- Package/library names get medium weight (e.g. `Biostrings`, `ggplot2`, `tidyverse`)
- Common identifiers are filtered out as stopwords
- Keywords are joined with `-` as the filename

## CLI Options

```
python scripts/read_article.py <url> [选项]

  --output, -o    指定输出路径（默认：关键词自动生成）
  --timeout, -t   验证码等待超时（默认 120s）
  --raw           同时保存原始文章内容
  --strategy, -s  浏览器策略：auto / attach / launch / playwright
```

## Python API

```python
from wechat_reader import read_article_sync
from pathlib import Path
import sys
sys.path.insert(0, "<path_to_wechat_reader>")

result = read_article_sync(url, strategy="auto", wait_for_manual_verify=120, timeout=30)

if result.status == "ok" and result.content:
    # Extract code and keywords
    from read_article import extract_code, extract_keywords
    code = extract_code(result.content)
    keywords = extract_keywords(code)
    print(f"Keywords: {', '.join(keywords)}")
    print(f"Code:\n{code}")
```

## Windows-specific Notes

On Windows, the original `wechat-reader` cannot find Chrome because it only checks Linux/macOS paths. The setup script automatically applies a patch to `browser_bridge.py` to add these paths:

```python
"C:/Program Files/Google/Chrome/Application/chrome.exe"
"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
"%LOCALAPPDATA%\\Google\\Chrome\\Application\\chrome.exe"
```

Chrome is typically installed at `C:\Program Files\Google\Chrome\Application\chrome.exe` on Windows.

## Output Format

When the script runs successfully:

| File | Content |
|---|---|
| `wechat_code_extracted.txt` | Extracted code only (no prose) — **temporary name** |
| `wechat_code_extracted.json` | Metadata (title, author, language, etc.) |

After AI analysis and rename:

| File | Content |
|---|---|
| `<keywords>.txt` | Renamed with keyword-based title |
| `<keywords>.json` | Updated metadata with keyword list |

## Common Status Values

| Status | Meaning | Action |
|---|---|---|
| `ok` | Article retrieved successfully | Use the content |
| `captcha_required` | Captcha page detected | User must solve captcha in browser |
| `rate_limited` | Too many requests | Wait and retry |
| `browser_not_found` | Chrome not installed | Install Chrome, or run Playwright's bundled Chromium |
| `browser_not_ready` | Playwright not set up | Run `python -m playwright install chromium` |
| `navigation_failed` | Could not navigate to URL | Check URL validity |
