# GLM 用户用例分析：摄影技术分析与图片处理

> 来源：tasks/analysis/user-use-case/2-photo.md

## 一、用例概述

用户通过聊天发送图片给"小龙虾"（OpenClaw Agent），Agent 对图片进行实时分析，返回结构化分析结果，并支持图片的本地/云端保存。核心场景：**拍照即分析，分析即学习，学习即提升**。

---

## 二、场景分解

| 序号 | 场景 | 输入 | 输出 | 触发方式 |
|------|------|------|------|----------|
| S1 | 发送图片消息 | 图片文件 (JPG/PNG/HEIC) | 图片接收确认 + 自动分析 | 聊天消息附件 |
| S2 | 图片下载到本地 | 聊天中的图片 | 本地文件路径 | Agent 自动 |
| S3 | 聊天框展示分析 | 图片 | 摄影参数分析 + 构图分析 | Agent 自动 |
| S4 | 实时分析返回结果 | 图片 + 分析维度 | 结构化评分和建议 | Agent 自动 |
| S5 | 保存到本地/云端 | 分析结果 + 图片 | 本地文件或飞书文件 | 用户确认 |

---

## 三、功能模块分析

### 3.1 图片接收与预处理模块

**职责**：接收用户上传的图片，进行格式转换和预处理

```
处理流程:
├── 图片接收 → 聊天附件 / 拖拽上传 / 粘贴剪贴板
├── 格式检测 → JPG/PNG/HEIC/WebP/AVIF
├── 格式转换 → HEIC → JPG (如需) / 统一为可处理格式
├── 尺寸检查 → 最大 20MB，超过则压缩
├── EXIF 提取 → 拍摄参数（光圈、快门、ISO、焦距等）
└── 缩略图生成 → 用于聊天框展示
```

**技术方案**：

| 功能 | 推荐技术 | 说明 |
|------|----------|------|
| 格式检测 | `file-type` npm 包 | magic bytes 检测 |
| HEIC 转换 | `heic-convert` | Mac/手机常见格式 |
| 图片压缩 | `sharp` | 高质量缩放，控制体积 |
| EXIF 提取 | `exifr` npm 包 | 支持全面，无原生依赖 |
| 缩略图 | `sharp` | 生成 300px 宽预览 |

### 3.2 图片分析模块（核心）

**职责**：使用 GLM 多模态能力对图片进行摄影技术分析

```
分析维度:
├── D1 基础参数分析 → EXIF 数据解读 + 参数评价
├── D2 构图分析     → 三分法/对称/引导线/框架构图等
├── D3 光线分析     → 自然光/人造光/逆光/侧光/柔光
├── D4 色彩分析     → 色调/饱和度/对比度/色彩搭配
├── D5 主题表达     → 主题明确度/情感传达/故事性
└── D6 综合评分     → 总分 + 各维度得分 + 改进建议
```

**技术方案**：

| 分析维度 | 实现方式 | 说明 |
|----------|----------|------|
| D1 基础参数 | EXIF 数据 + GLM 解读 | 纯文本分析，GLM-4.5-air 足够 |
| D2-D5 视觉分析 | **GLM-5.1 多模态 API** | 需要视觉理解能力 |
| D6 综合评分 | GLM-5.1 | 综合各维度打分 |

**GLM 多模态调用方式**：

```typescript
// 图片分析 API 调用示例
const analysis = await glmClient.chat({
  model: 'GLM-5.1',
  messages: [
    {
      role: 'user',
      content: [
        {
          type: 'image_url',
          image_url: { url: `data:image/jpeg;base64,${base64Image}` }
        },
        {
          type: 'text',
          text: `请作为专业摄影教练分析这张照片，从以下维度评价：
            1. 构图（三分法/对称/引导线/前景/层次）
            2. 光线（方向/质量/色温/氛围）
            3. 色彩（搭配/饱和度/对比度/情绪）
            4. 主题表达（故事性/情感/视觉冲击）
            5. 拍摄参数（根据 EXIF 数据评价参数选择）

            输出 JSON 格式，每个维度 1-10 分，附带具体改进建议。
            拍摄参数: ${exifData}`
        }
      ]
    }
  ],
  response_format: { type: 'json_object' }
});
```

### 3.3 分析结果渲染模块

**职责**：将分析结果可视化展示给用户

```
展示组件:
├── 雷达图     → 5 个维度的得分可视化 (recharts / echarts)
├── 参数卡片   → EXIF 参数展示（光圈/快门/ISO/焦距）
├── 构图辅助线 → 在原图上叠加三分法/黄金螺旋参考线
├── 改进建议   → 按优先级排序的可操作建议列表
└── 相似参考   → 推荐优秀作品链接（可选）
```

### 3.4 图片存储模块

**职责**：管理分析过的图片和结果

```
存储策略:
├── 原图存储    → workspace/photos/{date}/{timestamp}_{filename}
├── 缩略图      → workspace/photos/.thumbnails/{hash}.webp
├── 分析结果    → workspace/photos/.analysis/{hash}.json
├── 飞书上传    → 飞书 API → 指定图片文件夹
└── 相册管理    → 按日期/评分/标签分类浏览
```

---

## 四、数据结构设计

```typescript
interface PhotoAnalysis {
  id: string;
  imageUrl: string;            // 原图路径
  thumbnailUrl: string;        // 缩略图路径
  exif: ExifData;
  scores: PhotoScores;
  analysis: DimensionAnalysis[];
  suggestions: Suggestion[];
  tags: string[];              // AI 生成标签
  createdAt: number;
}

interface ExifData {
  camera?: string;             // 相机型号
  lens?: string;               // 镜头
  aperture?: string;           // 光圈 f/2.8
  shutterSpeed?: string;       // 快门 1/200s
  iso?: number;                // ISO 400
  focalLength?: string;        // 焦距 50mm
  whiteBalance?: string;       // 白平衡
  exposureCompensation?: string;
  dateTime?: string;           // 拍摄时间
  gps?: { lat: number; lng: number };
}

interface PhotoScores {
  overall: number;             // 总分 1-10
  composition: number;         // 构图
  lighting: number;            // 光线
  color: number;               // 色彩
  theme: number;               // 主题表达
  technique: number;           // 技术参数
}

interface DimensionAnalysis {
  dimension: 'composition' | 'lighting' | 'color' | 'theme' | 'technique';
  score: number;
  comment: string;             // 50-100 字评价
  highlights: string[];        // 亮点
}

interface Suggestion {
  priority: 'high' | 'medium' | 'low';
  category: string;
  content: string;             // 具体改进建议
  example?: string;            // 示例说明
}
```

---

## 五、GLM 集成方案

### 5.1 调用链路

```
用户发送图片
  → 图片预处理 (格式转换 + 压缩 + EXIF 提取)
  → 保存原图到本地
  → 图片 Base64 编码 (< 4MB)
  → 调用 GLM-5.1 多模态 API
    → 发送图片 + 分析 prompt
    → 流式接收分析结果
  → 解析 JSON 结果
  → 渲染分析卡片 (雷达图 + 建议)
  → 用户可追问细节
```

### 5.2 多轮对话支持

```
用户: [发送照片]
Agent: 📸 照片分析完成！

       综合评分: 7.5/10
       ┌──────────┬───────┐
       │ 构图     │  8/10 │ ████████░░
       │ 光线     │  7/10 │ ███████░░░
       │ 色彩     │  8/10 │ ████████░░
       │ 主题     │  7/10 │ ███████░░░
       │ 技术     │  8/10 │ ████████░░
       └──────────┴───────┘

       📷 Canon EOS R5 · 50mm · f/1.8 · 1/200s · ISO 400

       💡 改进建议:
       1. [高] 左侧留白过多，可适当裁剪增强主体
       2. [中] 背景虚化效果优秀，可尝试更低角度拍摄
       3. [低] 白平衡偏暖，后期可微调色温

用户: 构图方面能再详细说说吗？
Agent: 🎨 构图详细分析：

       你使用了中心构图法，主体位于画面中央...
       [显示构图辅助线叠加图]

       📐 建议尝试:
       - 三分法构图：将主体移到左侧 1/3 线交叉点
       - 前景框架：利用左侧树叶作为前景框架
```

### 5.3 模型选择

| 任务 | 推荐模型 | 原因 |
|------|----------|------|
| 图片视觉分析 | GLM-5.1 | 需要多模态视觉理解能力 |
| EXIF 参数解读 | GLM-4.5-air | 纯文本分析，速度快 |
| 改进建议生成 | GLM-5.1 | 需要专业摄影知识推理 |
| 追问细节回答 | GLM-4.5-air | 基于已有分析上下文回答 |

---

## 六、与 EPUB 分析的关联

原始需求提到"如果是 EPUB 如何进行分析和处理"，这里的 EPUB 场景是：

| 场景 | 说明 | 处理方式 |
|------|------|----------|
| EPUB 中的插图 | 书中的摄影示例图 | 提取图片 → 调用图片分析模块 |
| 摄影教程 EPUB | 包含摄影教学内容 | 复用"下载书籍"用例的分析流程 |
| 图片+文字混合分析 | 教程中图文对照 | 分别处理后关联展示 |

---

## 七、实现优先级

| 优先级 | 功能模块 | 依赖 | 预计工时 |
|--------|----------|------|----------|
| P0 | 图片接收 + EXIF 提取 | 无 | 3h |
| P0 | GLM 多模态分析调用 | GLM Vision API | 4h |
| P0 | 分析结果聊天展示 | ChatPanel | 3h |
| P1 | 雷达图评分可视化 | recharts/echarts | 3h |
| P1 | 本地图片存储 + 相册 | tauri-plugin-fs | 4h |
| P1 | 改进建议列表 | GLM API | 2h |
| P2 | 构图辅助线叠加 | Canvas / SVG | 6h |
| P2 | 飞书图片上传 | 飞书 API | 4h |
| P2 | 多图对比分析 | GLM API | 4h |
| P3 | 摄影学习计划推荐 | GLM API | 4h |
| P3 | EXIF 参数教学 | GLM API | 3h |

---

## 八、与现有项目的集成点

| 集成点 | 当前状态 | 需要的工作 |
|--------|----------|------------|
| 聊天界面 (ChatPanel) | 文本消息已实现 | 扩展支持图片消息类型 |
| GLM API 模块 (glm-client.ts) | 文本 API 已设计 | 添加多模态（图片+文本）调用 |
| 文件系统 (tauri-plugin-fs) | 工作区文件管理已有 | 添加 photos/ 目录管理 |
| 持久化存储 (Store) | Zustand store 已有 | 扩展 PhotoAnalysis 状态 |
| 教程系统 | MDX 教程已有 | 可将分析结果生成为摄影学习教程 |
