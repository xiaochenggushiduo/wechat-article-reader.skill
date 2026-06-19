# wechat-article-reader

读微信公众号文章，绕过验证码。

## 原理

使用 [wechat-reader](https://github.com/xiguawang/wechat-reader)（Playwright + 真实 Chrome 浏览器）打开微信文章页面。遇到验证码时，用户手动在浏览器中完成验证，脚本等待验证通过后自动提取文章内容。

## 前置依赖

- Python 3.11+
- Google Chrome

## 快速开始

```bash
# 1. 安装
python scripts/setup.py

# 2. 读文章
python scripts/read_article.py "https://mp.weixin.qq.com/s?__biz=..."

# 遇到验证码？在弹出来的浏览器窗口里手动完成验证，脚本会自动继续
```

## 命令行参数

```
python scripts/read_article.py <url> [选项]

选项：
  --output, -o    输出文件路径
  --timeout, -t   验证码等待超时秒数（默认 120）
  --json          同时保存元数据为 JSON
  --strategy, -s  浏览器策略：auto / attach / launch / playwright
```

## Python API

```python
from wechat_reader import read_article_sync

result = read_article_sync(
    "https://mp.weixin.qq.com/s?__biz=...",
    strategy="auto",
    wait_for_manual_verify=120,
)

if result.status == "ok":
    print(result.title)    # 文章标题
    print(result.author)   # 作者
    print(result.content)  # 正文
```

## Skill 文件

`wechat-article-reader.skill` 是 [Claude Code / Opencode](https://opencode.ai) 的 AI Agent skill 文件，让 AI 自动调用此流程读取微信文章。安装方法：

```bash
# 将 .skill 文件放入 skills 目录即可自动加载
```

## 输出字段

| 字段 | 说明 |
|---|---|
| `title` | 文章标题 |
| `author` | 作者名 |
| `content` | 正文纯文本 |
| `publish_time` | 发布时间 |
| `html` | 原始 HTML（可选） |

## 状态码

| 状态 | 含义 | 处理 |
|---|---|---|
| `ok` | 成功 | 直接使用内容 |
| `captcha_required` | 遇到验证码 | 在浏览器中手动完成 |
| `rate_limited` | 频率限制 | 稍后重试 |
| `browser_not_found` | 未安装 Chrome | 安装 Chrome 或使用 Playwright Chromium |
| `browser_not_ready` | Playwright 未就绪 | 运行 `python -m playwright install chromium` |

## Windows 注意

脚本会自动给 `wechat-reader` 打补丁添加 Windows Chrome 路径，无需手动配置。

## 致谢

基于 [xiguawang/wechat-reader](https://github.com/xiguawang/wechat-reader) 构建。
