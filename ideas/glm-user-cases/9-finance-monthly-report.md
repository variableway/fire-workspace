# 具体 Use Case：💰 月度消费报告与预算管理

> 优先级：P1（记账 MVP 完成后延伸）
> 来源：金融话题

## 一、用户故事

**小赵的月底**：
> 4 月最后一天，小龙虾主动推送了月度报告：
> "4 月消费报告来了！总支出 ¥6,320，比 3 月少了 ¥800。最大变化是餐饮从 ¥2,400 降到了 ¥1,600，你做得很好！但交通费翻了一倍，主要是打车多了，建议下周试试地铁。"
>
> 小赵："下个月餐饮预算设 2000，交通设 500。"
> 小龙虾："✅ 预算已设置。我会在超支 80% 时提醒你。"

---

## 二、核心交互设计

### 2.1 自动月度报告

```
Agent (主动推送/用户触发):
  📊 4月消费报告

  💰 总支出: ¥6,320 (3月: ¥7,120, ↓11%)

  📈 分类趋势:
  ┌──────────┬─────────┬─────────┬──────┐
  │ 类别     │  4月     │  3月     │ 变化  │
  ├──────────┼─────────┼─────────┼──────┤
  │ 🏠 房租  │ ¥1,500  │ ¥1,500  │ ─    │
  │ 🍜 餐饮  │ ¥1,600  │ ¥2,400  │ ↓33% │
  │ 🚕 交通  │ ¥680    │ ¥320    │ ↑113%│
  │ 🛒 日用  │ ¥420    │ ¥380    │ ↑11% │
  │ 🎮 娱乐  │ ¥280    │ ¥350    │ ↓20% │
  │ 📚 学习  │ ¥150    │ ¥120    │ ↑25% │
  │ 👔 服饰  │ ¥690    │ ¥0      │ NEW  │
  │ 📦 其他  │ ¥1,000  │ ¥2,050  │ ↓51% │
  └──────────┴─────────┴─────────┴──────┘

  🔍 关键发现:
  1. ✅ 餐饮消费控制得很好，减少了外卖
  2. ⚠️ 交通费翻倍，打车 12 次，建议改地铁
  3. ⚠️ 服饰 ¥690 为单笔大额（外套 ¥299 + 鞋 ¥390）

  💡 3条建议:
  1. 打车改为地铁+骑行，月省约 ¥400
  2. 餐饮继续保持，可以尝试更多自己做饭
  3. 下月建议总预算: ¥5,500 (不含房租)

  [查看每日明细] [设置下月预算] [导出 PDF]
```

### 2.2 预算设置与提醒

```
用户: 下个月餐饮预算2000，交通500，娱乐300
Agent:
  ✅ 5月预算已设置

  ┌──────────┬────────┬────────┐
  │ 类别     │ 预算    │ 状态    │
  ├──────────┼────────┼────────┤
  │ 🍜 餐饮  │ ¥2,000 │ ⏳ 等待  │
  │ 🚕 交通  │ ¥500   │ ⏳ 等待  │
  │ 🎮 娱乐  │ ¥300   │ ⏳ 等待  │
  └──────────┴────────┴────────┘

  🔔 我会在以下时间提醒你:
  - 类别达到预算 80% 时
  - 月底前 5 天，总预算使用超过 90% 时

  [设置总预算] [查看上月对比]
```

### 2.3 超支提醒（实时）

```
Agent (自动推送):
  ⚠️ 餐饮预算提醒

  当前餐饮消费: ¥1,650 / 预算 ¥2,000 (82.5%)
  剩余预算: ¥350
  距月底还有 12 天，日均可用: ¥29

  最近 5 笔餐饮:
  - 4/19 晚餐 ¥85
  - 4/18 午餐 ¥42
  - 4/17 外卖 ¥58
  - 4/16 午餐 ¥35
  - 4/16 早餐 ¥15

  💡 建议: 本周尝试自己带饭 2-3 次

  [查看详情] [调整预算]
```

### 2.4 消费趋势查询

```
用户: 最近三个月餐饮花了多少
Agent:
  📈 餐饮消费趋势 (近3月)

  2月: ¥2,800 ████████████████████████
  3月: ¥2,400 ████████████████████
  4月: ¥1,600 █████████████

  📉 持续下降！4月比2月少了 43%

  人均每餐:
  - 2月: ¥47
  - 3月: ¥40
  - 4月: ¥32

  👍 省钱效果明显，继续保持！

  [按周查看] [和预算对比]
```

---

## 三、GLM 调用方案

### 3.1 月度报告生成

```
基于以下消费数据，生成月度消费报告：

月份: ${month}
消费数据: ${JSON.stringify(expenses)}
上月数据: ${JSON.stringify(lastMonthExpenses)}
预算设置: ${JSON.stringify(budget)}

输出要求：
1. 总支出和分类明细
2. 与上月的环比分析（找出变化最大的 3 个类别）
3. 关键发现（异常消费、节省亮点）
4. 3 条具体的、可操作的建议
5. 语气友好，像朋友聊天，不要像银行账单
```

### 3.2 超支预警逻辑

```typescript
// 不需要 GLM，纯规则引擎
function checkBudgetAlert(expenses, budget, today) {
  const monthProgress = today.getDate() / daysInMonth(today);
  const alerts = [];

  for (const [category, limit] of Object.entries(budget.categories)) {
    const spent = sumByCategory(expenses, category);
    const ratio = spent / limit;

    if (ratio >= 0.8 && ratio < 1.0) {
      alerts.push({
        level: 'warning',
        category,
        spent,
        limit,
        remaining: limit - spent,
        dailyAllowance: (limit - spent) / remainingDays,
      });
    }
    if (ratio >= 1.0) {
      alerts.push({
        level: 'over',
        category,
        spent,
        limit,
        overspent: spent - limit,
      });
    }
  }
  return alerts;
}
```

### 3.3 模型选择

| 任务 | 模型 | 原因 |
|------|------|------|
| 月度报告文案 | **GLM-5.1** | 需要分析和写作能力 |
| 建议生成 | GLM-5.1 | 需要推理 |
| 趋势分析文案 | GLM-4.5-air | 基于数据的简单总结 |
| 预算建议 | GLM-4.5-air | 简单计算+建议 |
| 超支检测 | **纯规则** | 不需要 AI |

---

## 四、数据结构

```typescript
interface MonthlyReport {
  month: string;                          // YYYY-MM
  totalAmount: number;
  categories: CategorySummary[];
  comparedToLastMonth: ComparisonResult;
  keyFindings: string[];
  suggestions: string[];
  topExpenses: ExpenseRecord[];           // 单笔最高 5 笔
  dailyAverage: number;
  weekdayVsWeekend: {
    weekday: { count: number; avg: number };
    weekend: { count: number; avg: number };
  };
}

interface CategorySummary {
  category: ExpenseCategory;
  amount: number;
  count: number;
  percentage: number;
  lastMonth: number;
  change: number;                         // 正数=增加，负数=减少
  changePercent: number;
}

interface BudgetConfig {
  monthlyTotal?: number;
  categories: Partial<Record<ExpenseCategory, number>>;
  alertThreshold: number;                 // 0.8 = 80%时提醒
  alertDays: number[];                    // 每月哪几天检查 [15, 20, 25, 28]
}
```

---

## 五、与记账功能的依赖关系

```
自然语言记账 (Phase 1)
  │
  ├── 积累 1 个月数据
  │
  └── 月度报告 (Phase 2)
       │
       ├── 预算设置 (Phase 2)
       │    └── 超支提醒 (Phase 2)
       │
       └── 趋势分析 (Phase 3)
            └── 年度总结 (Phase 3)
```

**前置条件**：至少积累 1 个月的记账数据才能生成有意义的月度报告。

---

## 六、实现 Task 分解

| # | Task | 预计 | 依赖 |
|---|------|------|------|
| T1 | 月度消费数据聚合函数 | 3h | 记账 T2 (ExpenseRecord Store) |
| T2 | 环比分析逻辑 | 2h | T1 |
| T3 | GLM-5.1 月度报告 Prompt | 3h | T2 |
| T4 | 报告展示页面（表格 + 图表） | 4h | T3 |
| T5 | 预算设置页面 | 3h | T1 |
| T6 | 超支检测 + 消息推送 | 3h | T5 |
| T7 | 趋势图（3 个月对比） | 3h | T1 |
| T8 | PDF 报告导出 | 3h | T4 |

**总计约 24h，MVP（T1-T4）约 12h。需要记账功能运行 1 个月后才有数据。**

---

## 七、定时任务集成

利用 OpenClaw 的 cron 功能实现自动化：

| 定时任务 | Cron | 说明 |
|----------|------|------|
| 预算检查 | 每日 20:00 | 检查是否有类别接近超支 |
| 月度报告 | 每月 1 日 9:00 | 自动生成上月报告并推送 |
| 周报 | 每周日 21:00 | 本周消费快速总结 |
| 年度总结 | 1月1日 10:00 | 全年消费报告 |
