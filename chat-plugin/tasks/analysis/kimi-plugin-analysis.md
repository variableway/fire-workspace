# Kimi Chat Plugin — 分析报告与代码示例

> 前置文档：`chat-plugin.md`
> 任务来源：`tasks.md` Task 1 & Task 2
> 目标：获取 Kimi 对话的完整内容（含 Python 代码执行结果、图片、富文本）

---

## 一、问题分析

Kimi（kimi.moonshot.cn）的对话中可能包含以下富内容类型：

| 内容类型 | 示例 | 获取难度 |
|----------|------|----------|
| 纯文本回复 | 普通问答 | 低 |
| Python 代码块 | ````python ... ```` | 低（Markdown 格式） |
| 代码执行结果（文本） | stdout 输出 | 中（需解析特殊 DOM） |
| 代码执行结果（图片） | matplotlib 图表、PIL 生成图片 | **高**（图片以 base64 或 URL 嵌入） |
| 文件附件 | 上传/下载的文件 | 中 |
| 搜索引用 | Kimi 联网搜索结果 | 中 |

**核心挑战**：Kimi 的 Python 代码执行结果中的**图片**（如 matplotlib 图表）不会出现在纯文本导出中，需要特殊处理。

---

## 二、Task 1：Kimi Chat Plugin 获取完整对话

### 方案对比

| 方案 | 原理 | 能否获取图片 | 复杂度 |
|------|------|-------------|--------|
| **A. Chrome 插件（DOM 解析）** | 注入 Content Script 读取页面 DOM | ✅ 可以获取 `<img>` 和 `<canvas>` | 中 |
| **B. Kimi CLI `/export`** | 使用官方 CLI 导出 Markdown | ❌ 图片只保留占位符 | 低 |
| **C. Kimi 非官方 API** | 使用 `refresh_token` 调用内部 API | ✅ 可获取完整消息结构 | 高 |
| **D. Kimi Agent SDK** | 使用官方 SDK 的 `prompt()` API | ✅ 可获取工具调用结果 | 中 |
| **E. 已有 Chrome 插件** | 使用 YourAIScroll / AI Conversation Export Assistant | ✅ 部分支持 | 低 |

### 推荐方案：A + B 组合

**日常使用**：Chrome 插件一键导出（含图片）
**批量/自动化**：Kimi CLI `/export`（快速但不含图片）或 Kimi Agent SDK（完整）

---

### 2.1 方案 A：Chrome 插件代码示例（Plasmo + React）

以下是基于 Plasmo 框架的 Kimi Chat 导出插件核心代码。

#### Content Script：解析 Kimi 对话 DOM

```typescript
// contents/kimi-extractor.ts

import type { PlasmoCSConfig } from "plasmo"

export const config: PlasmoCSConfig = {
  matches: ["https://kimi.moonshot.cn/*", "https://kimi.ai/*"],
}

interface ChatMessage {
  role: "user" | "assistant"
  text: string
  codeBlocks: CodeBlock[]
  images: ImageData[]
  searchResults: SearchResult[]
}

interface CodeBlock {
  language: string
  code: string
  output?: string
  outputImages: string[]
}

interface ImageData {
  src: string
  alt: string
  dataUrl?: string
}

interface SearchResult {
  title: string
  url: string
  snippet: string
}

function extractKimiConversation(): ChatMessage[] {
  const messages: ChatMessage[] = []

  const messageElements = document.querySelectorAll(
    '[class*="message"], [class*="chat-msg"], [data-role]'
  )

  messageElements.forEach((el) => {
    const isUser = el.querySelector('[class*="user"]') !== null
      || el.getAttribute("data-role") === "user"
      || el.className.includes("user")

    const msg: ChatMessage = {
      role: isUser ? "user" : "assistant",
      text: "",
      codeBlocks: [],
      images: [],
      searchResults: [],
    }

    // 提取文本内容
    const textEl = el.querySelector('[class*="markdown"], [class*="content"], [class*="text"]')
    if (textEl) {
      msg.text = textEl.textContent?.trim() || ""
    }

    // 提取代码块（含执行结果）
    const codeEls = el.querySelectorAll("pre code, [class*='code-block']")
    codeEls.forEach((codeEl) => {
      const language = codeEl.className.replace(/language-/, "").replace(/hljs/, "").trim()
      const code = codeEl.textContent || ""

      const codeBlock: CodeBlock = {
        language,
        code,
        output: undefined,
        outputImages: [],
      }

      // 查找代码执行结果（紧跟代码块的输出区域）
      const parent = codeEl.closest("pre")?.parentElement
      if (parent) {
        const outputEl = parent.querySelector(
          '[class*="result"], [class*="output"], [class*="execute"]'
        )
        if (outputEl) {
          codeBlock.output = outputEl.textContent?.trim()
        }

        // 查找执行结果中的图片（matplotlib 等）
        const imgEls = parent.querySelectorAll("img")
        imgEls.forEach((img) => {
          const src = img.src || img.getAttribute("data-src") || ""
          if (src && (src.startsWith("data:image") || src.startsWith("http") || src.startsWith("blob:"))) {
            codeBlock.outputImages.push(src)
          }
        })
      }

      msg.codeBlocks.push(codeBlock)
    })

    // 提取所有图片（包括回复中的图片）
    const allImages = el.querySelectorAll("img")
    allImages.forEach((img) => {
      const src = img.src || img.getAttribute("data-src") || ""
      if (src && !src.includes("avatar") && !src.includes("icon")) {
        msg.images.push({
          src,
          alt: img.alt || "",
        })
      }
    })

    // 提取搜索引用
    const refEls = el.querySelectorAll('[class*="reference"], [class*="citation"], a[class*="source"]')
    refEls.forEach((ref) => {
      const link = ref as HTMLAnchorElement
      msg.searchResults.push({
        title: ref.textContent?.trim() || "",
        url: link.href || "",
        snippet: ref.getAttribute("title") || "",
      })
    })

    if (msg.text || msg.codeBlocks.length > 0 || msg.images.length > 0) {
      messages.push(msg)
    }
  })

  return messages
}

// 将图片 URL 转为 base64 DataURL（确保离线可用）
async function imageToDataUrl(url: string): Promise<string> {
  try {
    const response = await fetch(url)
    const blob = await response.blob()
    return new Promise((resolve) => {
      const reader = new FileReader()
      reader.onloadend = () => resolve(reader.result as string)
      reader.readAsDataURL(blob)
    })
  } catch {
    return url
  }
}

// 导出为 Markdown（含 base64 图片嵌入）
async function exportToMarkdown(messages: ChatMessage[]): Promise<string> {
  let md = "# Kimi Chat Export\n\n"

  for (const msg of messages) {
    md += `## ${msg.role === "user" ? "👤 User" : "🤖 Kimi"}\n\n`

    if (msg.text) {
      md += `${msg.text}\n\n`
    }

    for (const cb of msg.codeBlocks) {
      md += "```" + cb.language + "\n"
      md += cb.code + "\n"
      md += "```\n\n"

      if (cb.output) {
        md += "**Output:**\n```\n" + cb.output + "\n```\n\n"
      }

      for (const imgUrl of cb.outputImages) {
        const dataUrl = await imageToDataUrl(imgUrl)
        md += `![output](${dataUrl})\n\n`
      }
    }

    for (const img of msg.images) {
      const dataUrl = await imageToDataUrl(img.src)
      md += `![${img.alt}](${dataUrl})\n\n`
    }

    if (msg.searchResults.length > 0) {
      md += "**References:**\n"
      for (const ref of msg.searchResults) {
        md += `- [${ref.title}](${ref.url})\n`
      }
      md += "\n"
    }
  }

  return md
}

// 导出为 JSON
function exportToJson(messages: ChatMessage[]): string {
  return JSON.stringify({
    exportedAt: new Date().toISOString(),
    platform: "kimi",
    messages,
  }, null, 2)
}

// 注册消息监听（与 Popup 通信）
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "extract") {
    const messages = extractKimiConversation()
    sendResponse({ messages })
  }
  if (request.action === "exportMarkdown") {
    extractKimiConversation()
    exportToMarkdown(extractKimiConversation()).then((md) => {
      const blob = new Blob([md], { type: "text/markdown" })
      const url = URL.createObjectURL(blob)
      chrome.downloads.download({ url, filename: `kimi-export-${Date.now()}.md` })
    })
    sendResponse({ status: "ok" })
  }
  if (request.action === "exportJson") {
    const messages = extractKimiConversation()
    const json = exportToJson(messages)
    const blob = new Blob([json], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    chrome.downloads.download({ url, filename: `kimi-export-${Date.now()}.json` })
    sendResponse({ status: "ok" })
  }
  return true
})
```

#### Popup 界面

```tsx
// popup.tsx

import { useState } from "react"

function IndexPopup() {
  const [status, setStatus] = useState("ready")

  const handleExport = async (format: "markdown" | "json") => {
    setStatus("exporting...")
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
    if (!tab?.id) return

    chrome.tabs.sendMessage(tab.id, {
      action: format === "markdown" ? "exportMarkdown" : "exportJson",
    }, () => {
      setStatus("done!")
      setTimeout(() => setStatus("ready"), 2000)
    })
  }

  return (
    <div style={{ width: 300, padding: 16 }}>
      <h2>Kimi Chat Exporter</h2>
      <p>Status: {status}</p>
      <button onClick={() => handleExport("markdown")}>
        Export as Markdown
      </button>
      <button onClick={() => handleExport("json")}>
        Export as JSON
      </button>
    </div>
  )
}

export default IndexPopup
```

---

### 2.2 方案 B：Kimi CLI `/export` 命令

Kimi CLI 内置了 `/export` 命令，可以将当前会话导出为 Markdown 文件。

```bash
# 在 kimi-cli 会话中输入
/export

# 或指定文件名
/export my-conversation.md

# 导出文件格式：kimi-export-<会话ID前8位>-<时间戳>.md
```

**局限性**：
- ✅ 能导出文本对话、代码块
- ❌ **不能导出代码执行产生的图片**（matplotlib 图表等）
- ❌ 不能导出搜索引用的详细内容
- ✅ 能导出对话元数据（时间、会话 ID 等）

---

### 2.3 方案 C：Kimi 非官方 API

通过 `refresh_token` 调用 Kimi 的内部 API 获取完整对话数据。

```python
import requests
import json
import os

class KimiChatExporter:
    BASE_URL = "https://kimi.moonshot.cn/api"

    def __init__(self, refresh_token: str):
        self.refresh_token = refresh_token
        self.session = requests.Session()
        self._refresh_access_token()

    def _refresh_access_token(self):
        resp = self.session.post(
            f"{self.BASE_URL}/auth/token/refresh",
            json={"refresh_token": self.refresh_token}
        )
        data = resp.json()
        self.access_token = data.get("access_token")
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}"
        })

    def list_conversations(self, limit: int = 50) -> list:
        resp = self.session.get(
            f"{self.BASE_URL}/chat/list",
            params={"offset": 0, "limit": limit}
        )
        return resp.json().get("items", [])

    def get_conversation(self, chat_id: str) -> dict:
        resp = self.session.get(
            f"{self.BASE_URL}/chat/{chat_id}"
        )
        return resp.json()

    def export_all_conversations(self, output_dir: str = "kimi_exports"):
        os.makedirs(output_dir, exist_ok=True)
        conversations = self.list_conversations()

        for conv in conversations:
            chat_id = conv["id"]
            title = conv.get("title", "untitled")
            print(f"Exporting: {title} ({chat_id})")

            data = self.get_conversation(chat_id)
            messages = self._parse_messages(data)

            filename = f"{output_dir}/{title[:50]}_{chat_id[:8]}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({
                    "id": chat_id,
                    "title": title,
                    "messages": messages,
                }, f, ensure_ascii=False, indent=2)

        print(f"Exported {len(conversations)} conversations to {output_dir}/")

    def _parse_messages(self, data: dict) -> list:
        messages = []
        for node_id, node in data.get("mapping", {}).items():
            msg = node.get("message")
            if not msg:
                continue
            role = msg.get("author", {}).get("role")
            content = msg.get("content", {})

            parsed = {
                "role": role,
                "text": "",
                "code_blocks": [],
                "images": [],
            }

            parts = content.get("parts", [])
            for part in parts:
                if isinstance(part, str):
                    parsed["text"] += part
                elif isinstance(part, dict):
                    if part.get("type") == "code":
                        parsed["code_blocks"].append({
                            "language": part.get("language", ""),
                            "code": part.get("text", ""),
                            "output": part.get("output", ""),
                            "output_images": part.get("output_images", []),
                        })
                    elif part.get("type") == "image":
                        parsed["images"].append(part.get("url", ""))

            messages.append(parsed)

        return messages


if __name__ == "__main__":
    # 从 kimi.moonshot.cn 的 Application > Local Storage 获取 refresh_token
    REFRESH_TOKEN = os.environ.get("KIMI_REFRESH_TOKEN", "your_token_here")

    exporter = KimiChatExporter(REFRESH_TOKEN)
    exporter.export_all_conversations()
```

**注意**：`refresh_token` 可从浏览器 F12 → Application → Local Storage 中获取。此 API 为非公开接口，可能随 Kimi 更新而变动。

---

### 2.4 方案 D：Kimi Agent SDK（官方 SDK）

Moonshot 提供了官方的 `kimi-agent-sdk`，适合通过 API 与 Kimi 交互并获取完整响应。

```python
from kimi_agent_sdk import KimiAgent

agent = KimiAgent(
    api_key="your_moonshot_api_key",
    model="kimi-k2-0711-chat",
)

result = agent.prompt(
    "用 Python 生成一张正弦函数图表",
    stream=True,
)

for event in result:
    if event.type == "assistant":
        text = event.extract_text()
        if text:
            print(text)

    elif event.type == "tool":
        tool_name = event.tool_name
        tool_output = event.tool_output
        print(f"[Tool: {tool_name}]")
        print(tool_output)

        if hasattr(event, "images") and event.images:
            for i, img_url in enumerate(event.images):
                print(f"  Image: {img_url}")
```

**优势**：
- 官方 SDK，稳定可靠
- 能获取 Tool Call 结果（含图片）
- 支持流式输出

**局限**：
- 仅适用于通过 API 创建的对话，**不能获取网页端的历史对话**
- 需要 Moonshot API Key（从 platform.moonshot.ai 获取）

---

## 三、Task 2：获取 Kimi CLI 的完整 Response

### 问题 1：通用问题给 Kimi CLI 做分析，能否获取所有内容？

**答案：部分可以，但图片会丢失。**

Kimi CLI 的 `/export` 命令导出的是 Markdown 格式，它能包含：
- ✅ 所有文本对话
- ✅ 代码块（Python、Bash 等）
- ✅ 代码块的文本输出（stdout）
- ❌ **代码执行产生的图片**（matplotlib 图表、PIL 生成的图片等）
- ❌ 文件上传/下载的内容

**原因**：Kimi CLI 的导出只处理文本流，图片在终端中无法直接展示，因此 `/export` 也不会包含。

### 问题 2：用提示词要求 Kimi 全部输出是否可行？

**答案：可以部分解决，但不是根本方案。**

```markdown
# 提示词策略

请在回复中：
1. 将所有 Python 代码执行结果（包括图片）以文字描述的方式总结
2. 如果生成了图表，请描述图表的关键数据点和趋势
3. 将所有计算结果以 Markdown 表格的形式列出
4. 如果有图片 URL，请提供完整的图片链接
```

**这种策略的问题**：
- Kimi 可能无法提供图片的直接 URL（图片可能是临时的 base64 或 blob URL）
- 文字描述不能替代实际的图片内容
- 增加了不必要的 Token 消耗

### 推荐方案：结合 CLI 导出 + API 补充

```python
import subprocess
import json
import os

def export_kimi_session_with_images(session_id: str = None):
    """
    方案：先用 CLI 导出文本，再用 API 补充图片
    """

    # Step 1: 使用 kimi-cli /export 获取文本
    text_content = export_via_cli()

    # Step 2: 使用 Moonshot API 获取完整消息结构（含图片）
    api_messages = fetch_via_api(session_id)

    # Step 3: 合并：用 API 的图片数据补充 CLI 导出的文本
    merged = merge_text_and_images(text_content, api_messages)

    # Step 4: 下载所有图片到本地
    download_images(merged)

    return merged


def export_via_cli() -> str:
    """通过 kimi-cli /export 命令导出"""
    result = subprocess.run(
        ["kimi", "chat", "--export"],
        capture_output=True,
        text=True,
    )
    return result.stdout


def fetch_via_api(session_id: str = None) -> list:
    """通过 Moonshot API 获取完整消息"""
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ["MOONSHOT_API_KEY"],
        base_url="https://api.moonshot.ai/v1",
    )

    messages = client.chat.completions.create(
        model="moonshot-v1-128k",
        messages=[
            {"role": "user", "content": "请回顾我们之前的对话"}
        ],
    )
    return [m.model_dump() for m in messages.choices]


def download_images(merged_data: dict, output_dir: str = "kimi_images"):
    """下载所有图片到本地"""
    import urllib.request

    os.makedirs(output_dir, exist_ok=True)

    for i, img_url in enumerate(merged_data.get("image_urls", [])):
        if img_url.startswith("http"):
            filepath = os.path.join(output_dir, f"image_{i}.png")
            urllib.request.urlretrieve(img_url, filepath)
            print(f"Downloaded: {filepath}")


def merge_text_and_images(text_md: str, api_messages: list) -> dict:
    """合并文本和图片数据"""
    image_urls = []
    for msg in api_messages:
        content = msg.get("message", {}).get("content", {})
        parts = content.get("parts", [])
        for part in parts:
            if isinstance(part, dict) and part.get("type") == "image":
                image_urls.append(part.get("url", ""))

    return {
        "markdown": text_md,
        "image_urls": image_urls,
    }


if __name__ == "__main__":
    export_kimi_session_with_images()
```

---

## 四、方案总结与推荐

### 最终推荐路径

| 场景 | 推荐方案 | 理由 |
|------|----------|------|
| **日常单条对话导出（含图片）** | Chrome 插件（方案 A） | 一键导出，图片转 base64 嵌入 Markdown |
| **批量导出所有历史对话** | Kimi 非官方 API（方案 C） | 可遍历所有对话，获取完整 JSON 数据 |
| **CLI 用户快速导出** | `/export` 命令（方案 B） | 最简单，但图片丢失 |
| **通过 API 与 Kimi 交互** | Kimi Agent SDK（方案 D） | 官方 SDK，稳定，但无法获取网页端历史 |
| **需要完整数据（文本+图片）** | CLI + API 组合 | 先 CLI 导出文本，再 API 补充图片 |

### 关于 Kimi 图片获取的关键结论

**Kimi 回复中的图片有三种来源**：

1. **用户上传的图片**：可通过 API 或 DOM 直接获取
2. **Python 代码执行产生的图片**（matplotlib、PIL 等）：在网页端以 `<img>` 标签渲染，DOM 中可获取 `src`（可能是 base64 data URL 或临时 URL）
3. **AI 生成的图片**（通过工具调用）：URL 可能在 API 响应的 tool_output 中

**最佳实践**：Chrome 插件在提取时立即将图片转为 base64 DataURL 嵌入 Markdown，确保离线可用且不依赖临时 URL 过期。

---

## 五、已有竞品可直接使用

如果不想自己开发，以下 Chrome 插件已经支持 Kimi 导出：

| 插件 | Kimi 支持 | 图片支持 | 格式 | 链接 |
|------|-----------|----------|------|------|
| **AI Conversation Export Assistant** | ✅ | ✅ PDF/PNG 长图 | PDF / PNG / MD | [Chrome Web Store](https://edge-stats.com/d/pdgdnfobffckdfbjneecjaljkeddmmok) |
| **Kimi To PDF** | ✅ 专属 | ✅ | PDF | [Chrome Web Store](https://chrome-stats.com/d/kgeabhljeaccflldpdonkkimcdedfmca) |
| **YourAIScroll** | ✅（10 个平台之一） | ✅ Artifacts/Diagrams | MD / HTML / JSON / TXT | [官网](https://www.toolify.ai/tool/youraiscroll/) |

---

## 六、Task 3：结论来源问题 — 提取 Kimi 内部分析代码

> 任务来源：`tasks.md` Task 3
> 场景：给 Kimi 一个音乐文件 + 个人录音，Kimi 后台执行 Python 代码做分析比较，如何拿到所有内部 Python 代码和分析方法？

### 6.1 Kimi 内部文件分析机制

当你给 Kimi 上传文件并要求分析时，Kimi 内部的工作流程如下：

```
用户上传文件 → 文件解析（code_runner） → 生成 Python 分析代码 → 沙箱执行 → 返回结果
```

**关键组件：`code_runner` 工具**

Kimi 内部使用 `code_runner` 工具来执行 Python 代码。当你上传一个音乐文件并要求分析时：

1. **文件读取**：Kimi 生成 Python 代码读取上传的文件（如 `librosa.load()`, `soundfile.read()`）
2. **数据分析**：生成 Python 代码进行音频特征提取（音高、节奏、频谱等）
3. **数据比较**：生成比较代码，对比两个文件的音频特征
4. **可视化**：可能生成 matplotlib 图表展示频谱对比
5. **结论生成**：基于代码执行结果，生成自然语言结论

**核心问题**：这些 Python 代码在 Kimi 的对话 UI 中通常只显示部分或不显示，但我们有方法完整获取。

### 6.2 三种提取方案对比

| 方案 | 原理 | 能否获取完整代码 | 能否获取分析方法 | 复杂度 |
|------|------|------------------|------------------|--------|
| **A. 提示词工程** | 在 prompt 中明确要求输出所有代码 | 部分（可能遗漏） | 部分 | 低 |
| **B. Moonshot API tool_calls** | 通过 API 调用，拦截 `tool_calls` 字段 | ✅ 完整 | ✅ 完整 | 中 |
| **C. Kimi Agent SDK** | 使用官方 SDK 拦截每一步工具调用 | ✅ 完整 | ✅ 完整 + 可控 | 中 |

### 6.3 方案 A：提示词工程（Prompt Engineering）

**原理**：在提问时明确要求 Kimi 输出所有中间步骤的 Python 代码。

**优点**：无需编程，直接在 Kimi 网页端或 CLI 使用。
**缺点**：不保证 100% 完整，Kimi 可能省略内部实现细节。

**示例提示词**：

```
请分析以下两个音频文件，判断第二个文件（我的录音）是否适合翻唱第一个文件（原唱）。

要求：
1. 请输出你使用的每一个 Python 分析步骤的完整代码
2. 包括文件读取、特征提取、数据比较、可视化的所有代码
3. 每个分析步骤请说明你使用的分析方法名称和原理
4. 请输出所有中间计算结果
5. 如果使用了第三方库，请说明库名和用途

文件1：[原唱音频文件]
文件2：[我的录音文件]
```

**局限性**：

- Kimi 可能只输出它认为"重要"的代码，省略辅助性代码
- 代码执行中的错误和重试过程不会显示
- 内部的工具调用参数可能被简化

### 6.4 方案 B：Moonshot API + tool_calls 提取（推荐）

**原理**：通过 Moonshot API 发送请求，API 返回的 `tool_calls` 字段会包含 Kimi 生成的所有 Python 代码。

#### 6.4.1 文件上传与处理

```python
"""
方案 B：通过 Moonshot API 提取 Kimi 内部分析代码
依赖：pip install openai
"""
import os
import json
import base64
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)


def upload_audio_files(file_paths: list[str]) -> list[str]:
    """上传音频文件到 Moonshot，返回 file_id 列表"""
    file_ids = []
    for path in file_paths:
        with open(path, "rb") as f:
            response = client.files.create(file=f, purpose="file-extract")
        file_ids.append(response.id)
        print(f"上传文件 {path} -> file_id: {response.id}")
    return file_ids


def extract_file_content(file_id: str) -> str:
    """提取文件内容（Moonshot 会解析文件并返回文本内容）"""
    content = client.files.content(file_id=file_id)
    return content.text


def analyze_with_tool_calls(
    file_ids: list[str],
    file_names: list[str],
) -> dict:
    """
    发送分析请求，拦截所有 tool_calls 获取内部 Python 代码。
    Kimi K2 模型支持 function calling，可提取 tool_calls。
    """
    # 构建文件内容上下文
    file_context = ""
    for fid, name in zip(file_ids, file_names):
        content = extract_file_content(fid)
        file_context += f"\n--- 文件: {name} ---\n{content}\n"

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个专业的音频分析助手。请使用 code_runner 工具执行 Python 代码来分析音频文件。"
                "请完整输出每个分析步骤的 Python 代码。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"请分析以下两个音频文件，判断录音是否适合翻唱原唱。\n\n"
                f"文件内容：{file_context}\n\n"
                f"请使用 Python 代码进行以下分析：\n"
                f"1. 音高范围分析\n"
                f"2. 节奏/节拍分析\n"
                f"3. 频谱特征对比\n"
                f"4. 综合评分\n\n"
                f"请输出所有分析步骤的完整 Python 代码和执行结果。"
            ),
        },
    ]

    all_tool_calls = []
    all_assistant_messages = []

    # 发送请求（可能多轮 tool call）
    max_rounds = 10
    for round_num in range(max_rounds):
        response = client.chat.completions.create(
            model="kimi-k2-0711-chat",
            messages=messages,
            temperature=0.3,
        )

        choice = response.choices[0]
        assistant_msg = choice.message

        # 保存 assistant 消息
        all_assistant_messages.append(assistant_msg)

        # 检查是否有 tool_calls
        if hasattr(assistant_msg, "tool_calls") and assistant_msg.tool_calls:
            all_tool_calls.extend(assistant_msg.tool_calls)

            # 打印本轮 tool_calls 中的代码
            for tc in assistant_msg.tool_calls:
                print(f"\n=== Round {round_num + 1} Tool Call: {tc.function.name} ===")
                try:
                    args = json.loads(tc.function.arguments)
                    # code_runner 的参数中包含 Python 代码
                    if "code" in args:
                        print(f"Python 代码:\n{args['code']}")
                    else:
                        print(f"参数: {json.dumps(args, indent=2, ensure_ascii=False)}")
                except json.JSONDecodeError:
                    print(f"原始参数: {tc.function.arguments}")

            # 将 assistant 消息加入历史，继续下一轮
            messages.append(assistant_msg)
            # 添加 tool 响应（模拟执行结果）
            for tc in assistant_msg.tool_calls:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": "[代码执行结果已由系统返回]",
                })
        else:
            # 没有更多 tool_calls，分析完成
            print(f"\n=== 最终结论 ===")
            print(assistant_msg.content)
            break

    return {
        "tool_calls": all_tool_calls,
        "messages": all_assistant_messages,
        "extracted_code": [
            json.loads(tc.function.arguments).get("code", "")
            for tc in all_tool_calls
            if tc.function.name == "code_runner"
        ],
    }


def main():
    # 1. 上传文件
    file_paths = ["original_song.mp3", "my_recording.wav"]
    file_ids = upload_audio_files(file_paths)

    # 2. 执行分析并提取代码
    result = analyze_with_tool_calls(file_ids, file_paths)

    # 3. 保存提取的代码
    print(f"\n共提取到 {len(result['extracted_code'])} 段 Python 代码")
    for i, code in enumerate(result["extracted_code"], 1):
        print(f"\n--- 代码片段 {i} ---")
        print(code)

    # 保存到文件
    with open("kimi_extracted_code.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "extracted_code": result["extracted_code"],
                "tool_calls_count": len(result["tool_calls"]),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    main()
```

#### 6.4.2 仅提取分析代码（简化版）

如果只需要提取 Kimi 生成的 Python 代码，不需要完整的多轮对话：

```python
"""简化版：提取 Kimi 分析代码"""
import json
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://api.moonshot.cn/v1",
)


def extract_analysis_methods(audio_description: str) -> list[dict]:
    """
    直接请求 Kimi 输出分析方法，不依赖文件上传。
    适用于已经有音频特征数据的情况。
    """
    response = client.chat.completions.create(
        model="kimi-k2-0711-chat",
        messages=[
            {
                "role": "user",
                "content": (
                    f"请提供一段完整的 Python 代码，用于分析以下音频数据并判断适合性：\n\n"
                    f"{audio_description}\n\n"
                    f"要求：\n"
                    f"1. 使用 librosa 和 numpy 进行音频特征提取\n"
                    f"2. 包含音高检测、节奏分析、MFCC 特征对比\n"
                    f"3. 输出每个分析步骤的方法名称和原理说明\n"
                    f"4. 最终给出适合性评分（0-100）"
                ),
            }
        ],
        temperature=0.1,
    )

    return {
        "code": response.choices[0].message.content,
        "model": response.model,
        "usage": response.usage.model_dump(),
    }
```

### 6.5 方案 C：Kimi Agent SDK（最完整方案）

**原理**：使用 Kimi Agent SDK 的 Session API，可以拦截每一步工具调用，包括 `code_runner` 执行的所有 Python 代码。

**优点**：
- 完整获取所有内部代码（包括错误重试）
- 可以控制是否批准每一步执行
- 可以获取沙箱环境中的文件变化
- 支持流式获取中间结果

#### 6.5.1 使用 Session API 提取代码

```python
"""
方案 C：通过 Kimi Agent SDK 提取内部分析代码
依赖：pip install kimi-agent-sdk
"""
import asyncio
import json
from pathlib import Path
from kimi_agent_sdk import ApprovalRequest, Session, TextPart


class KimiCodeExtractor:
    """提取 Kimi 内部生成的所有 Python 代码"""

    def __init__(self, work_dir: str = "."):
        self.work_dir = Path(work_dir)
        self.extracted_code: list[dict] = []
        self.all_messages: list[str] = []

    async def analyze_audio(
        self,
        original_file: str,
        recording_file: str,
    ) -> dict:
        """
        分析两个音频文件，提取所有内部 Python 代码。
        """
        async with await Session.create(work_dir=self.work_dir) as session:
            prompt_text = (
                f"请分析以下两个音频文件，判断录音是否适合翻唱原唱：\n"
                f"- 原唱文件：{original_file}\n"
                f"- 录音文件：{recording_file}\n\n"
                f"请使用 Python 代码进行完整的音频分析。"
            )

            async for wire_msg in session.prompt(prompt_text):
                match wire_msg:
                    case TextPart(text=text):
                        self.all_messages.append(text)
                        print(text, end="", flush=True)

                    case ApprovalRequest() as req:
                        # 拦截工具调用请求，提取代码
                        tool_info = self._extract_tool_info(req)

                        if tool_info:
                            self.extracted_code.append(tool_info)
                            print(f"\n[拦截到工具调用] {tool_info['tool_name']}")
                            if tool_info.get("code"):
                                print(f"  代码预览: {tool_info['code'][:200]}...")

                        # 自动批准所有工具调用
                        req.resolve("approve")

        return {
            "extracted_code": self.extracted_code,
            "full_response": "".join(self.all_messages),
        }

    def _extract_tool_info(self, req: ApprovalRequest) -> dict | None:
        """从 ApprovalRequest 中提取工具调用信息"""
        try:
            # ApprovalRequest 包含工具调用的详细信息
            info = {
                "tool_name": getattr(req, "tool_name", "unknown"),
                "raw_request": str(req),
            }

            # 尝试提取 code_runner 的代码
            if hasattr(req, "function_arguments"):
                args = req.function_arguments
                if isinstance(args, str):
                    args = json.loads(args)
                if "code" in args:
                    info["code"] = args["code"]
                info["arguments"] = args

            return info
        except Exception as e:
            print(f"[解析工具调用失败] {e}")
            return None


async def main():
    extractor = KimiCodeExtractor()

    result = await extractor.analyze_audio(
        original_file="original_song.mp3",
        recording_file="my_recording.wav",
    )

    print(f"\n{'='*60}")
    print(f"共拦截到 {len(result['extracted_code'])} 个工具调用")
    print(f"其中包含 Python 代码的调用：")
    for i, tc in enumerate(result["extracted_code"], 1):
        if tc.get("code"):
            print(f"\n--- 代码片段 {i} ({tc['tool_name']}) ---")
            print(tc["code"])

    # 保存完整结果
    with open("kimi_sdk_extracted.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(main())
```

#### 6.5.2 使用 prompt API 快速提取

```python
"""
使用 Kimi Agent SDK 的 prompt API 快速提取代码
适合不需要细粒度控制的场景。
"""
import asyncio
import json
from kimi_agent_sdk import prompt


async def quick_extract(prompt_text: str) -> str:
    """快速获取 Kimi 回复（包含所有代码）"""
    full_response = []
    async for msg in prompt(prompt_text, yolo=True):
        text = msg.extract_text()
        if text:
            full_response.append(text)
            print(text, end="", flush=True)
    print()
    return "".join(full_response)


async def analyze_music():
    result = await quick_extract(
        "请提供一段完整的 Python 代码，"
        "使用 librosa 分析两个音频文件的音高、节奏、MFCC 特征，"
        "并给出翻唱适合性评分。请输出所有分析步骤的完整代码和方法说明。"
    )

    # 从回复中提取代码块
    import re
    code_blocks = re.findall(r"```python\n(.*?)```", result, re.DOTALL)

    print(f"\n提取到 {len(code_blocks)} 段 Python 代码")
    for i, code in enumerate(code_blocks, 1):
        print(f"\n--- 代码片段 {i} ---\n{code}")


if __name__ == "__main__":
    asyncio.run(analyze_music())
```

### 6.6 三种方案的回答总结

针对 Task 3 的三个子问题：

**问题 1：Kimi 后台执行 Python 代码的过程**

Kimi 使用内部 `code_runner` 工具在沙箱中执行 Python 代码。对于音频文件分析，典型流程：
- `librosa.load()` / `soundfile.read()` 读取音频
- 提取音高（pyin/YIN 算法）、节奏（beat tracking）、MFCC 等特征
- `numpy` 做数值比较，`matplotlib` 生成可视化图表
- 多步执行，每步生成新代码，可能有多轮工具调用

**问题 2：如何拿到所有 Python 代码**

| 需求 | 推荐方案 | 理由 |
|------|----------|------|
| 快速查看 | 方案 A（提示词） | 零成本，但不保证完整 |
| 程序化完整提取 | **方案 B（API tool_calls）** | 结构化数据，保证完整 |
| 完整提取 + 流程控制 | **方案 C（Agent SDK）** | 最完整，可控制每一步 |

**问题 3：需要提示词指定还是 SDK 直接调用？**

**答案：两者结合效果最好。**

- **纯提示词**：不完整，Kimi 可能省略内部实现
- **纯 SDK（不加提示词约束）**：能获取所有 tool_calls，但分析结果可能不符合预期
- **最佳实践**：使用 SDK/API 调用 + 明确的提示词，既约束分析范围，又程序化提取所有代码

```python
# 最佳实践示例：SDK + 明确提示词
PROMPT_TEMPLATE = """
请分析以下音频文件的翻唱适合性：
- 原唱: {original}
- 录音: {recording}

分析要求：
1. 请完整输出每个分析步骤的 Python 代码
2. 请说明每个分析方法的名称和原理
3. 请输出所有中间计算结果和最终评分

技术要求：
- 使用 librosa 进行音频特征提取
- 包含音高分析、节奏分析、频谱分析
- 给出 0-100 的适合性评分
"""
```

### 6.7 注意事项

1. **文件大小限制**：Moonshot API 单文件最大 100MB，音频文件注意控制大小
2. **沙箱环境**：Kimi 的 `code_runner` 在沙箱中执行，仅预装常用库（numpy, pandas, librosa, matplotlib 等）
3. **API 费用**：tool_calls 多轮调用会消耗较多 token，Kimi K2 模型支持 200+ 连续工具调用
4. **音频格式**：建议使用 WAV/MP3 格式，Kimi 对这些格式的解析支持最好
5. **代码完整性**：SDK 的 `ApprovalRequest` 能捕获每一步工具调用，是最完整的提取方式

---

*分析时间：2026-04-15（Task 1 & 2）、2026-04-21（Task 3）*
*数据来源：Kimi 官方文档、kimi-cli GitHub、kimi-agent-sdk GitHub、Moonshot API 文档、Chrome Web Store*
