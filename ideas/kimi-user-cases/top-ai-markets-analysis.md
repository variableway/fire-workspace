# 2025-2026 全球 Top AI Skill & Prompt 市场分析

> 分析日期：2026-04-16
> 数据来源：SkillsMP、LobeHub、agentskill.sh、skills.sh、ClawHub、PromptBase、FlowGPT、AIPRM、Coze、Claude Skills Marketplace 等公开信息

---

## 核心结论（先读这个）

**Prompt 市场正在萎缩，Skill 市场正在爆发。**

- **Prompt 市场**：2024 年是高峰期，2025-2026 年进入"红海"——数量泛滥、同质化严重、变现困难。头部平台（PromptBase、FlowGPT）虽然还活着，但增长放缓。
- **Skill 市场**：2025 年下半年开始快速增长，尤其是基于 `SKILL.md` 标准的开源 Skill 生态。原因是：AI 从"聊天工具"进化为"执行代理"，用户需要的不再是"一句话怎么写"，而是"一套完整的工作流怎么跑"。

**对于小白**：**直接用国内的扣子 (Coze) 和 Claude 官方 Skill 市场**，零门槛。
**对于进阶用户**：**关注 skills.sh (Vercel) 和 LobeHub**，建立自己的 Skill 库。

---

## 第一部分：Skill 市场 Top 6

### 1. SkillsMP —— 规模最大的 Skill 发现引擎

| 维度 | 信息 |
|------|------|
| **规模** | 425,000+ skills |
| **标准** | 基于 open `SKILL.md` 标准 |
| **特点** | 更像搜索引擎/聚合器，而非严格审核的市场 |
| **安装方式** | 浏览网站 → 下载 ZIP → 手动安装 |
| **支持工具** | Claude Code、Codex CLI、ChatGPT、Kimi CLI |

**优点**：
- 数量最大，覆盖几乎所有你能想到的领域
- 支持 AI 智能搜索，找 Skill 比较高效
- 完全免费

**缺点**：
- **没有官方 CLI**，无法一键安装（这是最大痛点）
- 质量参差不齐，因为没有严格的审核机制
- 依赖 GitHub 仓库，很多 Skill 已经停止维护

**适合谁**：想"淘货"的进阶用户，愿意花时间筛选和测试。

**是否可直接使用**：⚠️ **半可直接**。需要下载 ZIP 后手动放到对应目录。

---

### 2. LobeHub Skills —— 增长最快的精品 Skill 市场

| 维度 | 信息 |
|------|------|
| **规模** | 169,739+ skills |
| **特点** | 强调质量检查、社区反馈、产品化体验 |
| **安装方式** | CLI 一键安装 |
| **支持工具** | Claude Code、Cursor、Copilot 等 |

**优点**：
- 有**质量门槛**和社区评分，平均水平更高
- **一键安装**：`npx -y @lobehub/market-cli skills install <skill-name> --agent claude-code`
- 与 LobeHub 生态打通，体验接近真正的"App Store"

**缺点**：
- 部分高质量 Skill 可能需要 LobeHub 会员/付费计划
- 对非 LobeHub 用户的兼容性不是 100%

**适合谁**：追求效率、愿意为质量付费的专业用户。

**是否可直接使用**：✅ **可直接使用**。CLI 安装最顺畅。

---

### 3. agentskill.sh —— 安全导向的 Skill 市场

| 维度 | 信息 |
|------|------|
| **规模** | 110,000+ skills |
| **特点** | 每个 Skill 都有安全评分和审计详情 |
| **安装方式** | Claude Code 插件 + `/learn` 命令 |
| **支持工具** | Claude Code、Cursor、Copilot、Windsurf、Zed |

**优点**：
- **安全性是最大卖点**——在企业/团队环境中很有价值
- 安装简单：先添加 marketplace，然后 `/plugin install`
- 支持 20+ 种 AI 工具

**缺点**：
- 部分 Skill 需要插件生态支持，配置门槛略高于 LobeHub
- 免费版和付费版的功能差异较大

**适合谁**：企业开发者、对安全敏感的用户、使用 Claude Code 的工程师。

**是否可直接使用**：✅ **可直接使用**。尤其适合 Claude Code 用户。

---

### 4. skills.sh (by Vercel) —— 最具公信力的 Skill 市场

| 维度 | 信息 |
|------|------|
| **规模** | 87,000+ unique skills |
| **背书** | **Vercel 官方出品** |
| **特点** | 公共排行榜 + 安装追踪 |
| **安装方式** | `npx skills add <repo> --skill <skill-name>` |

**优点**：
- **Vercel 背书 = 长期可信度最高**
- 有公开排行榜，可以看到哪些 Skill 最受欢迎
- 单命令安装，体验简洁
- 与 GitHub 仓库直接关联，更新透明

**缺点**：
- 数量不是最多的
- 对非开发者用户来说， still 需要一些命令行基础
- 主要是代码/开发向 Skill，生活/创意类偏少

**适合谁**：开发者、Vercel 用户、希望建立长期 Skill 库的用户。

**是否可直接使用**：✅ **可直接使用**。`npx skills add` 一键搞定。

---

### 5. ClawHub (OpenClaw) —— 元数据最丰富的 Skill 市场

| 维度 | 信息 |
|------|------|
| **规模** | 20,000+ registered skills |
| **特点** | 使用信号、安装量、安全扫描、许可证、运行时要求 |
| **安装方式** | `npx clawhub@latest install <skill-name>` |
| **支持工具** | OpenClaw、Claude Code |

**优点**：
- **每个 Skill 的详情页信息最全**——你可以看到安装量、安全扫描结果、依赖要求
- 与 OpenClaw 生态深度集成
- 有一些非常有趣的创意 Skill（如 Poe Chat、Agent Vibes TTS）

**缺点**：
- 数量相对较小（相比 SkillsMP 的 42 万）
- 主要围绕 OpenClaw，跨平台能力一般

**适合谁**：OpenClaw/Claude Code 用户、喜欢尝鲜的创意工作者。

**是否可直接使用**：✅ **可直接使用**。`npx clawhub@latest install` 非常方便。

---

### 6. Claude Skills Marketplace (claudeskills.info) ——  curated 精品库

| 维度 | 信息 |
|------|------|
| **规模** | 未公开总数，但增长迅速 |
| **特点** | 针对 Claude Code 专门优化的 curated collection |
| **代表 Skill** | Prompt Engineering Library、NotebookLM Integration、YouTube Transcript、Deep Research、Social Media Content Engine |
| **安装方式** | 多为手动安装或命令行 |

**优点**：
- ** curated = 质量有保障**
- 很多 Skill 直接解决开发者日常工作流痛点
- Prompt Engineering Library 等系列 Skill 非常实用

**缺点**：
- 只面向 Claude Code 用户
- 安装方式不统一，有些需要手动 clone
- 非开发者类 Skill 较少

**适合谁**：Claude Code 重度用户、软件开发者。

**是否可直接使用**：✅ **可直接使用**（仅限 Claude Code 用户）。

---

## 第二部分：Prompt 市场 Top 5

### 1. PromptBase —— Prompt 界的亚马逊

| 维度 | 信息 |
|------|------|
| **规模** | 230,000+ prompts |
| **定价** | $1.99 - $9.99 / prompt |
| **佣金** | 平台抽 20%（标准销售），10%（定制工作） |
| **覆盖模型** | GPT、Midjourney、DALL·E、Stable Diffusion |

**优点**：
- **最大的 curated prompt 市场**，品类最全
- 有质量审核，买家有保障
- 创作者可以赚到真金白银（月入几百到几千美元）

**缺点**：
- **2025 年后增长明显放缓**——因为模型越来越强，对"购买 prompt"的需求在下降
- 很多 prompt 很快过时（尤其是依赖特定模型版本的）
- 图像 prompt 占比过高，文本/工作流 prompt 偏少

**适合谁**：设计师、需要特定图像风格 prompt 的用户、想通过卖 prompt 变现的创作者。

**是否可直接使用**：✅ **可直接使用**。购买后立刻下载。

---

### 2. FlowGPT —— 社区驱动的 Prompt + AI App 平台

| 维度 | 信息 |
|------|------|
| **规模** | 未公开具体 prompt 数，但社区非常活跃 |
| **收入** | ~$1.9M 年收入 |
| **融资** | $10M Pre-Series A（2024年初） |
| **特点** | Prompt 库 + 多模型 AI Chat + 社区 "AI Apps" |

**优点**：
- **社区活跃度最高**——不只是买 prompt，还能和创作者互动
- 可以直接在平台上测试 prompt，不需要自己配置 API
- 有 prompt 悬赏和竞赛机制，创新氛围好

**缺点**：
- 质量参差不齐，因为社区上传门槛低
- 免费内容多，但优质内容需要付费/订阅
- 对企业用户来说不够系统化

**适合谁**：喜欢探索、测试新 prompt 的普通用户和创作者。

**是否可直接使用**：✅ **可直接使用**。网页直接测试和复制。

---

### 3. AIPRM —— ChatGPT 内的 Prompt 增强层

| 维度 | 信息 |
|------|------|
| **规模** | 4,500+ 1-click prompts |
| **定价** | 免费 + 付费订阅（$37 写作包 / $150 全包） |
| **形态** | Chrome 扩展 + ChatGPT 内嵌 |
| **强项** | SEO、内容营销、SaaS |

**优点**：
- **无缝集成在 ChatGPT 对话界面中**，体验最流畅
- 一键使用，不需要复制粘贴
- SEO/营销类 prompt 非常专业和细分

**缺点**：
- **只服务 ChatGPT 用户**
- 订阅制，长期使用成本不低
- 非营销类 prompt 相对薄弱

**适合谁**：营销人员、SEO 从业者、ChatGPT 重度用户。

**是否可直接使用**：✅ **可直接使用**（需要安装 Chrome 扩展）。

---

### 4. PromptHero —— 图像 Prompt 的社交市场

| 维度 | 信息 |
|------|------|
| **特点** | 图像 prompt 为主，带生成结果展示 |
| **定价** | 免费 + Pro ($19.99/月) |
| **覆盖** | Midjourney、DALL·E、Stable Diffusion |

**优点**：
- **视觉学习效果最好**——每个 prompt 都配生成图
- 有 prompt engineering 课程，适合新手入门
- 社区氛围好，艺术家和设计师聚集

**缺点**：
- 几乎只做图像 prompt
- 免费版功能有限

**适合谁**：AI 绘画爱好者、设计师、视觉创作者。

**是否可直接使用**：✅ **可直接使用**。免费浏览大量 prompt。

---

### 5. OpenAI GPT Store —— 官方但半死不活

| 维度 | 信息 |
|------|------|
| **形态** | ChatGPT 内置的 GPTs 商店 |
| **特点** | 官方 curated + 用户自创 |
| **变现** | 仅在美国部分地区开放 monetization |

**优点**：
- 官方出品，与 ChatGPT 无缝集成
- 有一些非常实用的垂直 GPTs（如论文润色、编程辅助）

**缺点**：
- **商业化进展极其缓慢**，创作者激励不足
- 大量低质量 GPTs 充斥，发现机制差
- 2025 年后热度明显下滑，很多优质 GPT 停止更新

**适合谁**：ChatGPT Plus 用户，想快速找一个特定场景的 GPT。

**是否可直接使用**：✅ **可直接使用**。但期望值不要太高。

---

## 第三部分：国内市场

### 1. 扣子 (Coze) —— 国内最成熟的 AI Agent 平台

| 维度 | 信息 |
|------|------|
| **公司** | 字节跳动（火山引擎） |
| **特点** | 可视化 Bot 搭建 + 工作流编排 + 插件市场 |
| **定价** | 免费额度 generous |

**优点**：
- **国内体验最完整的 Agent 平台**
- 有海量官方插件和社区 Bot
- 支持工作流编排（闲鱼图文生成、PPT 制作等）
- 可以直接发布到飞书、抖音、微信

**缺点**：
- 主要面向 Bot/Agent 场景，对纯 Prompt/Skill 的支持不如海外平台
- 企业级功能需要火山引擎付费

**适合谁**：**国内小白和中小企业首选**。零代码搭建自己的 AI 助手。

**是否可直接使用**：✅ **强力推荐。国内直接使用最方便。**

---

### 2. Kimi+ 智能体商店

| 维度 | 信息 |
|------|------|
| **公司** | 月之暗面 |
| **特点** | Kimi 内置的智能体和提示词市场 |

**优点**：
- 与 Kimi 对话无缝结合
- 有一些非常实用的办公智能体（PPT 助手、长文阅读等）

**缺点**：
- 生态规模不如扣子
- 商业化路径尚不清晰

**适合谁**：Kimi 用户，想快速调用特定场景能力。

**是否可直接使用**：✅ **可直接使用**。

---

### 3. 智谱清言 智能体

| 维度 | 信息 |
|------|------|
| **公司** | 智谱 AI |
| **特点** | GLM 模型 + 智能体搭建 + 办公小浣熊等工具 |

**优点**：
- 办公场景工具链完整（PPT、数据分析、文档处理）
- 清华背景，技术实力强

**缺点**：
- 用户量和社区活跃度不如扣子和 Kimi

**适合谁**：需要办公自动化、数据分析的用户。

**是否可直接使用**：✅ **可直接使用**。

---

### 4. LiblibAI —— 国内 AI 绘画/模型社区

| 维度 | 信息 |
|------|------|
| **特点** | AI 绘画模型分享 + Prompt 交流 |
| **定位** | 国内版 Civitai |

**优点**：
- 模型和 LoRA 资源丰富
- 有大量中文优化过的图像 prompt

**缺点**：
- 只聚焦图像生成

**适合谁**：AI 绘画爱好者、设计师。

**是否可直接使用**：✅ **可直接使用**。

---

## 第四部分：选型建议（按用户类型）

### 小白用户（0 基础，不想写代码）

| 优先级 | 推荐平台 | 理由 |
|--------|---------|------|
| **P0** | **扣子 (Coze)** | 国内最成熟，零代码，直接发布到飞书/微信 |
| **P0** | **AIPRM** | 如果你用 ChatGPT，这是体验最流畅的 prompt 增强层 |
| **P1** | **FlowGPT** | 免费探索大量 prompt，社区活跃 |
| **P1** | **Claude Skills Marketplace** | 如果你用 Claude Code，有很多现成可用的开发 Skill |

**小白的最短路径**：
- 日常办公/生活 → **扣子 (Coze)**
- 营销文案/SEO → **AIPRM + ChatGPT**
- 图像生成 → **PromptHero / LiblibAI**
- 代码辅助 → **Claude Code + Claude Skills Marketplace**

---

### 进阶用户（会写代码，想建立个人工作流）

| 优先级 | 推荐平台 | 理由 |
|--------|---------|------|
| **P0** | **skills.sh (Vercel)** | 最可信、有排行榜、一键安装、更新透明 |
| **P0** | **LobeHub Skills** | 质量最高、CLI 最顺畅、生态最产品化 |
| **P0** | **ClawHub** | 如果你是 OpenClaw/Claude Code 用户，元数据最全 |
| **P1** | **agentskill.sh** | 企业环境优先，有安全评分和审计 |
| **P1** | **PromptBase** | 需要购买特定领域的高质量 prompt 时备用 |
| **P2** | **SkillsMP** | 当其他市场找不到时，来这里"大海捞针" |

**进阶用户的最短路径**：
- 建立自己的 Skill 库 → **skills.sh + LobeHub**
- 安全敏感的企业项目 → **agentskill.sh**
- OpenClaw 生态深度用户 → **ClawHub**
- 想买/卖 prompt 变现 → **PromptBase**

---

## 第五部分：可直接使用的推荐清单

### 立即可用的海外 Skill（免费/开源）

| Skill 名称 | 来源市场 | 用途 | 安装命令 |
|-----------|---------|------|---------|
| **Prompt Engineering Library** | Claude Skills | 为 Claude Code 提供 curated prompt 模板 | 手动安装 |
| **poe-chat** | ClawHub | 在 Claude Code 中调用 Poe 的多模型能力 | `npx clawhub@latest install poe-chat` |
| **youtube-transcript** | Claude Skills | 获取 YouTube 字幕并总结 | 手动安装 |
| **postgres** | Claude Skills | 安全地执行只读 PostgreSQL 查询 | 手动安装 |
| **vercel-react-best-practices** | skills.sh | React 开发最佳实践 Skill | `npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-react-best-practices` |
| **subagent-driven-development** | Claude Skills | 子代理驱动开发，代码审查检查点 | 手动安装 |

### 立即可用的海外 Prompt（免费/低价）

| Prompt 类型 | 推荐平台 | 价格 |
|------------|---------|------|
| SEO/营销 Prompt | AIPRM | 免费 + 订阅 |
| Midjourney 图像 Prompt | PromptHero | 免费浏览 |
| ChatGPT 通用 Prompt | FlowGPT | 免费测试 |
| 专业级图像 Prompt | PromptBase | $1.99 - $9.99 |

### 立即可用的国内平台

| 平台 | 最佳场景 | 访问方式 |
|------|---------|---------|
| **扣子 (Coze)** | Bot/Agent/工作流 | coze.cn |
| **Kimi+** | 长文处理/办公辅助 | kimi.moonshot.cn |
| **智谱清言** | 数据分析/PPT/文档 | chatglm.cn |
| **LiblibAI** | AI 绘画/模型 | liblib.art |

---

## 第六部分：趋势判断

### Prompt 市场的未来：萎缩但细分领域仍有价值

- **通用 Prompt 已死**：GPT-4o、Claude 3.5 等模型越来越强，"怎么问"的重要性在下降
- **垂直 Prompt 仍有价值**：特定领域的复杂 prompt（如医学影像分析 prompt、建筑渲染 prompt）仍然有市场
- **Prompt 正在被"封装成 Skill"**：单独卖 prompt 的生意不好做了，但把 prompt + 工具 + 工作流打包成 Skill，价值会更高

### Skill 市场的未来：爆发式增长，但标准之战刚开始

- **SKILL.md 标准正在成为事实标准**：SkillsMP、skills.sh、ClawHub 都在围绕这个标准构建
- **安装体验决定胜负**：谁能做到"一行命令安装 + 自动配置依赖"，谁就能赢
- **质量 > 数量**：LobeHub 的 curated 模式可能是长期更可持续的路径
- **国内 Skill 市场尚处早期**：扣子、Kimi+ 还在做 Agent/Bot，真正的 CLI-based Skill 市场（像海外的 skills.sh）在国内几乎空白——**这是一个巨大的机会**

---

## 一句话总结

> **2026 年的 AI 市场格局已经清晰：Prompt 是过渡形态，Skill 是终极形态。小白用户直接用扣子 + AIPRM 就能覆盖 90% 需求；进阶用户应该立刻开始建立自己的 Skill 库，首选 skills.sh 和 LobeHub。对于国内创业者而言，CLI-based 的 Skill 市场还是一片蓝海。**
