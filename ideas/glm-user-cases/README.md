# GLM 用户用例分析

从用户视角分析如何使用小龙虾（OpenClaw Agent + GLM API）解决实际问题的用例集合。

## 核心入口

```
📝 随手记（万能入口）── 一个输入框，AI 自动分类
  ├─ 文字 → todo/记账/心情/日程/笔记
  ├─ 图片 → 食物识别/识物/此刻记录
  ├─ 链接 → XHS/知乎/任意 URL 内容分析
  └─ 语音 → 任意上述类型
```

## 优先级排序（按落地顺序）

```
Phase 0 (P0) ── 📝 随手记 + 📸 拍照秒识
Phase 1 (P1) ── 💰 记账 + 🍜 食谱 + 📱 XHS 分析
Phase 2 (P2) ── 扩展场景（穿搭、健康、知识管理等）
```

## 文件索引

### 设计与策略

| 文件 | 说明 |
|------|------|
| [4-prioritization-analysis.md](./4-prioritization-analysis.md) | 优先级筛选：评分框架、落地顺序 |
| [10-feature-discovery-and-entry.md](./10-feature-discovery-and-entry.md) | 用户发现与入口设计 |
| [11-instant-wow-scenarios.md](./11-instant-wow-scenarios.md) | 即刻可见的 5 个场景 |
| [**12-casual-record-everything.md**](./12-casual-record-everything.md) | **随手记：万能入口，用户只管发，AI 来分** |
| [13-social-browsing-analysis.md](./13-social-browsing-analysis.md) | XHS/社交媒体浏览分析 |

### 具体 Use Case（按落地顺序）

| 文件 | 话题 | 优先级 | 核心交互 | 预计工时 |
|------|------|:------:|----------|----------|
| [5-photo-food-calorie-recognition.md](./5-photo-food-calorie-recognition.md) | 📸 拍照识热量 | **P0** | 拍照→识别食物→估算热量→记一笔 | MVP 23h |
| [7-finance-expense-tracking.md](./7-finance-expense-tracking.md) | 💰 自然语言记账 | **P0** | "午饭35"→自动分类记录→月度统计 | MVP 10h |
| [6-photo-object-recognition.md](./6-photo-object-recognition.md) | 📸 拍照识物 | P1 | 万物识别+商品比价+OCR | 19h |
| [8-food-meal-planning.md](./8-food-meal-planning.md) | 🍜 每周食谱 | P1 | 生成食谱→购物清单→冰箱清理 | MVP 16h |
| [9-finance-monthly-report.md](./9-finance-monthly-report.md) | 💰 月度报告 | P1 | 自动月报+预算+超支提醒 | MVP 12h |

### 全景分析（参考）

| 文件 | 话题 | 核心场景 |
|------|------|----------|
| [1-download-book-analysis.md](./1-download-book-analysis.md) | 下载书籍与文档处理 | URL 下载、PDF/EPUB 分析、知识提取 |
| [2-photo-analysis.md](./2-photo-analysis.md) | 摄影技术分析与图片处理 | 图片分析、EXIF 解读、构图评价 |
| [3-personal-assistant-analysis.md](./3-personal-assistant-analysis.md) | 个人助理 (10 个子场景) | 饮食/出行/学习/财务/健康等 |

## 共性技术栈

- **大模型**: 智谱 GLM-5.1 (复杂分析) + GLM-4.5-air (轻量任务)
- **前端**: Next.js + React + Tailwind CSS + shadcn/ui
- **桌面**: Tauri 2.x
- **状态管理**: Zustand + tauri-plugin-store
- **聊天入口**: 统一 ChatPanel → 意图识别路由

## Use Case 之间的联动

```
📝随手记（万能入口）
  ├→ 📸拍照 → 识热量/识物/此刻
  ├→ 💰记账 → 月度报告/预算
  ├→ 📱XHS链接 → 内容分析/收藏/Todo
  ├→ 😊心情 → 情绪曲线/周报
  ├→ ✅Todo → 提醒/完成追踪
  └→ 🍜食谱 → 购物清单/饮食记录
```

> 来源：tasks/analysis/user-use-case/
