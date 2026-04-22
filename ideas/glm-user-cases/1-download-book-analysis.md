# GLM 用户用例分析：下载书籍与文档处理

> 来源：tasks/analysis/user-use-case/1-download-book.md

## 一、用例概述

用户通过聊天（飞书/桌面 App）发送书籍或文档资源给"小龙虾"（OpenClaw Agent），Agent 自动下载、保存、分析文档内容，并返回结构化分析结果。核心场景：**看到就下载，下载就分析，分析完就能用**。

---

## 二、场景分解

| 序号 | 场景 | 输入 | 输出 | 触发方式 |
|------|------|------|------|----------|
| S1 | 发送下载指令 | URL / 关键词 / 文件附件 | 下载确认 + 文件预览 | 聊天消息 |
| S2 | 自动下载到本地 | 文件 URL | 本地文件路径 | Agent 自动 |
| S3 | 在聊天框中展示 | PDF/EPUB 文件 | 摘要 + 目录 + 关键章节 | Agent 自动 |
| S4 | 保存到飞书文件夹 | 本地文件 | 飞书云文档链接 | 用户确认 |
| S5 | PDF 智能分析 | PDF 文件 | 结构化摘要、思维导图、问答 | 用户触发 |
| S6 | EPUB 智能分析 | EPUB 文件 | 章节拆分、摘要、知识卡片 | 用户触发 |

---

## 三、功能模块分析

### 3.1 下载引擎模块

**职责**：根据用户输入（URL / 关键词 / 文件）自动下载文件

```
输入类型:
├── 直接 URL → HTTP 下载 (支持 PDF/EPUB/MOBI/TXT)
├── 关键词   → 搜索引擎 → 匹配资源 → 下载
├── 文件附件 → 直接保存
└── DOI/ISBN → 学术数据库检索 → 下载
```

**技术方案**：

| 功能 | 推荐技术 | 说明 |
|------|----------|------|
| HTTP 下载 | `axios` / `node-fetch` | 支持断点续传、进度回调 |
| 文件格式检测 | `file-type` npm 包 | 通过 magic bytes 判断真实格式 |
| 文件存储 | `tauri-plugin-fs` (桌面) / `multer` (Web) | 桌面模式写本地，Web 模式写服务端 |
| 飞书上传 | 飞书开放 API `upload_all` | 需要飞书 App 凭证 |

**关键流程**：
```
用户发送 URL
  → URL 解析 (判断协议、域名、文件类型)
  → 安全检查 (白名单域名、文件大小限制 < 100MB)
  → HTTP 下载 (流式写入，显示进度)
  → 格式校验 (magic bytes)
  → 保存到工作区 downloads/ 目录
  → 触发文档分析模块
```

### 3.2 PDF 分析模块

**职责**：提取 PDF 内容并生成结构化分析

```
分析层次:
├── L1 元数据提取 → 标题、作者、页数、目录
├── L2 文本提取   → 全文 OCR (扫描版) / 文本提取 (电子版)
├── L3 结构化分析 → 章节识别、关键概念提取、摘要生成
└── L4 深度分析   → 知识图谱、思维导图、问答对生成
```

**技术方案**：

| 层级 | 推荐技术 | 说明 |
|------|----------|------|
| L1 元数据 | `pdf-lib` / `pdf-parse` | Node.js 纯 JS 方案 |
| L2 文本提取 | `pdf-parse` (电子版) / `tesseract.js` (扫描版) | 电子版优先 OCR 兜底 |
| L3 结构化分析 | **GLM-5.1 API** + prompt 工程 | 调用 GLM 大模型做章节摘要 |
| L4 深度分析 | **GLM-5.1 API** + 结构化 prompt | 生成思维导图 JSON、知识卡片 |

**GLM Prompt 示例（L3 结构化分析）**：
```
你是一个专业的文档分析助手。请对以下 PDF 文本内容进行结构化分析：

要求：
1. 提取章节结构（标题层级）
2. 每个章节生成 50 字以内的摘要
3. 提取关键概念和术语（10-20 个）
4. 生成全文 200 字摘要
5. 识别可操作的步骤或清单

输出格式：JSON
```

### 3.3 EPUB 分析模块

**职责**：解析 EPUB 电子书并生成结构化分析

```
处理流程:
├── EPUB 解包 → ZIP 解压 → 获取 OPF 元数据
├── 目录提取 → NCX / Nav 解析 → 章节列表
├── 内容提取 → HTML → 纯文本 (每章节)
├── 图片提取 → 保存到工作区 images/ 目录
└── 结构化分析 → 复用 PDF 分析模块的 L3/L4
```

**技术方案**：

| 功能 | 推荐技术 |
|------|----------|
| EPUB 解析 | `epub2` / `epubjs` npm 包 |
| HTML→文本 | `cheerio` (Node.js) |
| 图片处理 | 提取后保存为本地文件 |
| 内容分析 | GLM-5.1 API (同 PDF) |

### 3.4 文件管理模块

**职责**：管理下载的文件，支持多存储目标

```
存储策略:
├── 本地存储    → workspace/downloads/{date}/{filename}
├── 飞书云文档  → 飞书 API → 指定文件夹
├── 分析缓存    → workspace/cache/{file-hash}.json
└── 知识库归档  → workspace/KM/{category}/{filename}
```

---

## 四、数据结构设计

### 4.1 核心类型

```typescript
interface DownloadTask {
  id: string;
  source: 'url' | 'keyword' | 'attachment';
  url?: string;
  keyword?: string;
  status: 'pending' | 'downloading' | 'analyzing' | 'completed' | 'failed';
  progress: number;          // 0-100
  file?: FileInfo;
  analysis?: DocumentAnalysis;
  createdAt: number;
  updatedAt: number;
}

interface FileInfo {
  filename: string;
  format: 'pdf' | 'epub' | 'mobi' | 'txt';
  size: number;              // bytes
  localPath: string;
  feishuUrl?: string;
  hash: string;              // SHA-256
}

interface DocumentAnalysis {
  title: string;
  author?: string;
  pageCount?: number;
  summary: string;           // 全文摘要
  chapters: Chapter[];
  keyConcepts: string[];
  mindMap?: MindMapNode;     // 思维导图根节点
  flashCards?: FlashCard[];  // 知识卡片
  createdAt: number;
}

interface Chapter {
  title: string;
  level: number;             // 1=章, 2=节
  summary: string;
  keyPoints: string[];
}

interface MindMapNode {
  label: string;
  children: MindMapNode[];
}

interface FlashCard {
  question: string;
  answer: string;
  category: string;
}
```

---

## 五、GLM 集成方案

### 5.1 API 调用链路

```
文档上传完成
  → 文本提取 (PDF/EPUB → 纯文本)
  → 文本分块 (每块 ≤ 4000 tokens，保留章节边界)
  → 逐块调用 GLM-5.1 API (流式)
    → Prompt: 文档分析 + 结构化输出
  → 合并分析结果
  → 调用 GLM-5.1 生成全局摘要和知识图谱
  → 存储分析结果到 cache
  → 在聊天界面展示
```

### 5.2 模型选择

| 任务 | 推荐模型 | 原因 |
|------|----------|------|
| 章节摘要、关键概念提取 | GLM-4.5-air | 速度快、成本低，摘要任务够用 |
| 深度分析、知识图谱生成 | GLM-5.1 | 需要更强的推理能力 |
| 全文摘要合成 | GLM-5.1 | 需要全局理解能力 |
| OCR 辅助纠错 | GLM-4.5-air | 简单文本处理即可 |

### 5.3 Token 管理策略

- 单次分析上限：4096 tokens 输入
- 长文档分块：按章节自然分段，每块 3000-4000 tokens
- 缓存策略：相同文件 hash 的分析结果缓存，避免重复调用
- 流式输出：使用 SSE 流式返回，实时显示分析进度

---

## 六、交互流程设计

### 6.1 主流程（用户视角）

```
用户: 帮我下载这本书 https://example.com/ai-book.pdf
Agent: 正在下载《AI入门》...
       ████████████████████ 100%
       ✅ 已下载到 workspace/downloads/

       正在分析文档...
       📖 共 256 页，12 章
       📝 生成摘要中...

       📋 全文摘要:
       本书系统介绍了人工智能的基础概念...
       [查看完整分析] [生成知识卡片] [开始对话问答]
```

### 6.2 追问流程

```
用户: 第三章讲了什么？
Agent: 📖 第三章：深度学习基础 (P.45-78)

       核心内容：
       1. 神经网络基本结构
       2. 反向传播算法
       3. 常见激活函数对比

       📝 摘要：本章介绍了...

       [查看原始内容] [生成练习题]
```

---

## 七、实现优先级

| 优先级 | 功能模块 | 依赖 | 预计工时 |
|--------|----------|------|----------|
| P0 | URL 下载 + 本地保存 | 无 | 2h |
| P0 | PDF 文本提取 | 无 | 3h |
| P0 | GLM 摘要生成 | GLM API | 2h |
| P1 | EPUB 解析 | 无 | 3h |
| P1 | 章节结构化分析 | GLM API | 4h |
| P1 | 飞书云文档上传 | 飞书 API | 4h |
| P2 | 知识图谱生成 | GLM API | 6h |
| P2 | 知识卡片/FlashCard | GLM API | 4h |
| P2 | 思维导图可视化 | 前端组件 | 4h |
| P3 | OCR 扫描版支持 | tesseract.js | 4h |
| P3 | 对话式文档问答 | RAG | 8h |

---

## 八、与现有项目的集成点

| 集成点 | 当前状态 | 需要的工作 |
|--------|----------|------------|
| 聊天界面 (ChatPanel) | 已有 GLM 聊天 skill | 扩展消息类型支持文件附件 |
| 工作区管理 (Workspace) | 已实现文件树浏览 | 添加 downloads/ 目录和文件预览 |
| GLM API 调用模块 | glm-client.ts 已设计 | 添加文档分析专用 prompt |
| 终端面板 (Terminal) | PTY 已实现 | 可用终端执行 pdf 工具命令 |
| 持久化存储 (Store) | Zustand + tauri-plugin-store | 扩展 DownloadTask 状态 |
| 教程系统 | MDX 教程已实现 | 可将分析结果导出为 MDX 教程 |
