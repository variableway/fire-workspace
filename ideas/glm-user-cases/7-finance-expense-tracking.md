# 具体 Use Case：💰 自然语言记账

> 优先级：P0（与拍照识热量并列第一个落地）
> 来源：金融话题

## 一、用户故事

**小张的日常**：
> 午饭吃完，随口说了一句："午饭 35"。
> 小龙虾秒回："✅ 午餐 ¥35，已记录。本月餐饮累计 ¥1,280。"
>
> 周末逛街："买了件外套，打折 299。"
> 小龙虾："✅ 服饰 ¥299。本月服饰累计 ¥299。需要设置服饰预算吗？"
>
> 月底："这个月花了多少？"
> 小龙虾发了一张饼图和明细："本月共消费 ¥5,230，前三大类是餐饮(38%)、房租(29%)、交通(12%)。比上月少花了 ¥420。"

---

## 二、核心交互设计

### 2.1 一句话记账（MVP）

```
用户: 午饭花了35
Agent:
  ✅ 已记录

  🍜 午餐 | ¥35 | 2026-04-16 12:30
  ─────────────────────────────
  📊 今日: ¥35  本月餐饮: ¥1,280

用户: 打车去公司22块
Agent:
  ✅ 已记录

  🚕 交通 | ¥22 | 2026-04-16 08:45
  ─────────────────────────────
  📊 今日: ¥57  本月交通: ¥340
```

### 2.2 批量 / 复杂记账

```
用户: 昨天超市买了东西，牛奶12，面包8，水果25，一共45
Agent:
  ✅ 已记录 3 笔 (2026-04-15)

  | 类别   | 商品     | 金额  |
  |--------|---------|------|
  | 🥛 日用 | 牛奶     | ¥12  |
  | 🍞 日用 | 面包     | ¥8   |
  | 🍎 水果 | 水果     | ¥25  |
  |        | **合计** | **¥45** |

  [修改分类] [查看昨日明细]
```

### 2.3 分类纠正

```
用户: 刚才那个牛奶应该是食品
Agent:
  ✅ 已更新

  🥛 牛奶 ¥12: 日用 → 食品

  记住了，以后牛奶归入食品类。
```

### 2.4 查询与统计

```
用户: 这个月花了多少
Agent:
  📊 2026年4月 消费报告 (截至 4/16)

  💰 总支出: ¥5,230

  ┌──────────┬────────┬──────┬─────────┐
  │ 类别     │ 金额    │ 占比  | 趋势     │
  ├──────────┼────────┼──────┼─────────┤
  │ 🏠 房租  │ ¥1,500 │ 29%  │ ─       │
  │ 🍜 餐饮  │ ¥1,280 │ 24%  │ ↓ 比上月少 │
  │ 🚕 交通  │ ¥340   │  6%  │ ↑ 比上月多 │
  │ 🛒 日用  │ ¥420   │  8%  │ ─       │
  │ 🎮 娱乐  │ ¥280   │  5%  │ ↓       │
  │ 📚 学习  │ ¥150   │  3%  │ ↑       │
  │ 💊 医疗  │ ¥0     │  0%  │ ─       │
  │ 📦 其他  │ ¥1,260 │ 24%  │         │
  └──────────┴────────┴──────┴─────────┘

  💡 比上月同期少花 ¥420，主要是餐饮少了

  [查看每日明细] [设置预算] [导出 CSV]
```

---

## 三、GLM 调用方案

### 3.1 意图识别 Prompt（轻量）

```
判断用户消息是否是记账意图，如果是，提取记账信息。

输入: "${userMessage}"
输出 JSON:
{
  "is_expense": true/false,
  "amount": 数字或null,
  "category": "餐饮|交通|房租|日用|服饰|娱乐|学习|医疗|通讯|其他",
  "items": [
    { "name": "商品名", "amount": 数字, "category": "分类" }
  ],
  "date": "YYYY-MM-DD或null(默认今天)",
  "note": "备注或null",
  "confidence": 0.0-1.0
}

分类规则：
- 吃的喝的 → 餐饮
- 打车/地铁/加油/停车 → 交通
- 水电煤/物业 → 房租 (或单独 房屋)
- 超市/日用品 → 日用
- 衣服/鞋包 → 服饰
- 电影/KTV/游戏 → 娱乐
- 书/课/考试 → 学习
- 药/医院 → 医疗
- 手机话费/宽带 → 通讯
- 不好判断的 → 其他
```

### 3.2 月度报告生成 Prompt

```
基于以下消费数据，生成一份简洁的月度消费报告：

${expenseData}

要求：
1. 总支出和分类占比
2. 与上月的环比变化
3. 3 条具体省钱建议
4. 发现异常消费（某天或某类突然很高）
5. 输出纯文本，不用 JSON
```

### 3.3 模型选择

| 步骤 | 模型 | 原因 |
|------|------|------|
| 记账信息提取 | **GLM-4.5-air** | 结构化提取，简单快速，成本低 |
| 分类纠正 | GLM-4.5-air | 简单规则 |
| 月度报告生成 | **GLM-5.1** | 需要分析推理和写作能力 |
| 省钱建议 | GLM-5.1 | 需要财务知识 |

---

## 四、数据结构

```typescript
interface ExpenseRecord {
  id: string;
  amount: number;
  category: ExpenseCategory;
  subCategory?: string;         // 如: 餐饮.午餐
  items?: ExpenseItem[];         // 一笔消费包含多件商品
  note?: string;
  date: string;                  // YYYY-MM-DD
  time: string;                  // HH:mm
  source: 'voice' | 'text' | 'photo' | 'manual';
  corrected?: boolean;
  createdAt: number;
}

type ExpenseCategory =
  | '餐饮' | '交通' | '房租' | '日用'
  | '服饰' | '娱乐' | '学习' | '医疗'
  | '通讯' | '储蓄' | '其他';

interface ExpenseItem {
  name: string;
  amount: number;
  category: ExpenseCategory;
}

interface MonthlyReport {
  month: string;                 // YYYY-MM
  totalAmount: number;
  categoryBreakdown: Record<ExpenseCategory, number>;
  dailyAverage: number;
  topExpenses: ExpenseRecord[];  // 单笔最高的5笔
  comparedToLastMonth: {
    totalDiff: number;
    categoryDiffs: Record<ExpenseCategory, number>;
  };
  suggestions: string[];
}

interface BudgetConfig {
  monthlyTotal?: number;
  categories: Partial<Record<ExpenseCategory, number>>;
}
```

---

## 五、与拍照识热量的联动

拍照识热量和自然语言记账是**天然联动**的两个功能：

```
联动场景 1：拍照 → 自动记账
  用户拍照识别了红烧肉 (560 kcal)
  → Agent 回复热量后追加: "[记一笔 ¥45]"
  → 用户点击 → 自动创建 ExpenseRecord (source: 'photo')

联动场景 2：饮食 + 消费统计
  月度报告同时展示:
  - 饮食热量趋势 (来自拍照识别)
  - 餐饮消费趋势 (来自记账)
  - "本月餐饮 ¥2,100，日均 1,750 kcal，花费和热量匹配"
```

---

## 六、实现 Task 分解

| # | Task | 预计 | 依赖 |
|---|------|------|------|
| T1 | 记账意图识别 Prompt + GLM-4.5-air 调用 | 3h | GLM API 模块 |
| T2 | ExpenseRecord Store + 持久化 | 3h | 无 |
| T3 | 记账确认卡片组件 | 2h | T1, T2 |
| T4 | 分类纠正交互 | 2h | T3 |
| T5 | 月度统计页面（表格 + 简单图表） | 4h | T2 |
| T6 | 月度报告生成（GLM-5.1） | 3h | T5 |
| T7 | CSV 导出 | 2h | T2 |
| T8 | 预算设置 + 超支提醒 | 3h | T2 |

**总计约 22h，MVP（T1-T4）约 10h，2-3 天可完成。**

---

## 七、与现有项目集成

| 项目模块 | 集成点 |
|----------|--------|
| ChatPanel | "午饭35" 发到聊天框 → Agent 自动识别为记账 |
| GLM API | 轻量调用 GLM-4.5-air 提取结构化数据 |
| Store (Zustand) | 新增 expenseStore，persist 到 tauri-plugin-store |
| 定时任务 (Cron) | 每月 1 号自动生成上月报告 |
| 拍照识热量 | source: 'photo' 联动记账 |
