# 具体 Use Case：🍜 每周食谱生成

> 优先级：P1（与拍照识热量 + 记账联动后做）
> 来源：食话题

## 一、用户故事

**小陈的日常**：
> 周日晚上不知道下周吃什么，打开小龙虾："下周食谱，减脂，每天 1800 大卡，不吃辣。"
> 小龙虾 30 秒生成了完整的周一到周日三餐计划，每餐都标注了热量和做法。
> 小陈："把购物清单发我。"
> 小龙虾发了一份按超市区域分类的清单，直奔超市。
>
> 周三下班，拍了张冰箱照片："冰箱里还有这些，今晚能做什么？"
> 小龙虾看了看冰箱里的鸡蛋、番茄、剩米饭："番茄鸡蛋盖饭，20 分钟搞定，420 kcal。"

---

## 二、核心交互设计

### 2.1 生成一周食谱

```
用户: 下周食谱，减脂1800大卡，两人吃
Agent:
  🍽️ 一周食谱（减脂 1800 kcal/人 × 2人）

  📅 周一
  🌅 早餐: 全麦吐司+牛油果+水煮蛋 (380 kcal)
  🌞 午餐: 鸡胸肉藜麦沙拉 (520 kcal)
  🌙 晚餐: 清蒸鲈鱼+糙米饭+炒西兰花 (620 kcal)
  🍎 加餐: 希腊酸奶+蓝莓 (280 kcal)

  📅 周二
  🌅 早餐: 燕麦牛奶+香蕉 (350 kcal)
  🌞 午餐: 牛肉卷饼+蔬菜汤 (550 kcal)
  🌙 晚餐: 虾仁豆腐+杂粮饭 (600 kcal)
  🍎 加餐: 坚果+苹果 (300 kcal)

  ... (周三至周日)

  [生成购物清单] [替换某餐] [查看做法] [导出 PDF]
```

### 2.2 购物清单

```
用户: 购物清单
Agent:
  🛒 本周购物清单（2 人份）

  🥩 肉类/海鲜
  - 鸡胸肉 500g
  - 鲈鱼 1 条 (~400g)
  - 虾仁 300g
  - 牛肉馅 300g

  🥬 蔬菜
  - 西兰花 2 颗
  - 番茄 4 个
  - 生菜 1 把
  - 黄瓜 2 根

  🥛 乳制品
  - 牛奶 1L
  - 希腊酸奶 4 杯

  🍚 主食
  - 糙米 1kg
  - 全麦吐司 1 袋
  - 藜麦 500g

  🥚 其他
  - 鸡蛋 10 个
  - 牛油果 3 个
  - 蓝莓 1 盒

  [按超市区域排序] [在 XX 超市下单] [调整份量]
```

### 2.3 冰箱清理（剩菜利用）

```
用户: [发送冰箱照片]
Agent:
  🧊 冰箱里有：
  - 鸡蛋 4 个
  - 番茄 2 个
  - 剩米饭 1 盒
  - 小葱少许

  👨‍🍳 推荐菜谱（按省事程度排序）：

  1. 🥇 番茄鸡蛋盖饭 (20 min, 420 kcal)
     番茄炒蛋浇在热米饭上，撒葱花

  2. 🥈 番茄蛋花汤 + 煎蛋拌饭 (25 min, 380 kcal)

  3. 🥉 蛋炒饭 + 番茄蛋汤 (15 min, 520 kcal)
     米饭冷藏过更好炒

  [看做法] [全部记一笔]
```

### 2.4 替换单餐

```
用户: 周二午餐换个别的
Agent:
  🔄 替换建议（550 kcal 左右）：

  1. 鸡胸肉三明治 + 水果沙拉 (540 kcal)
  2. 日式照烧鸡腿饭 (560 kcal)
  3. 三文鱼牛油果poke bowl (520 kcal)

  输入序号选择，或告诉我你想吃什么。
```

---

## 三、GLM 调用方案

### 3.1 食谱生成 Prompt

```
你是一个专业的营养师和烹饪专家。请根据以下要求生成一周食谱：

用户要求：
- 目标: ${goal} (减脂/增肌/维持/控糖)
- 每日热量: ${calories} kcal
- 人数: ${people} 人
- 忌口: ${restrictions}
- 偏好: ${preferences}

输出 JSON：
{
  "week_plan": [
    {
      "day": "周一",
      "meals": {
        "breakfast": {
          "name": "菜名",
          "calories": 数字,
          "ingredients": ["食材1 量", "食材2 量"],
          "cook_time_min": 数字,
          "difficulty": "简单|中等|复杂",
          "brief_steps": "一句话做法"
        },
        "lunch": { ... },
        "dinner": { ... },
        "snack": { ... }
      },
      "daily_total": 数字
    }
  ],
  "shopping_list": [
    { "category": "肉类", "items": ["食材 量"] }
  ],
  "nutrition_summary": {
    "avg_daily_protein": 数字,
    "avg_daily_fat": 数字,
    "avg_daily_carbs": 数字
  }
}
```

### 3.2 冰箱剩菜利用 Prompt

```
根据冰箱里的食材，推荐 3 道可以做的菜。

冰箱食材: ${ingredients_from_photo}
用户偏好: ${preferences}

输出 JSON：
{
  "recipes": [
    {
      "name": "菜名",
      "calories": 数字,
      "cook_time_min": 数字,
      "difficulty": "简单|中等",
      "ingredients_used": ["用了哪些冰箱食材"],
      "need_extra": ["需要额外买的"],
      "steps": ["步骤1", "步骤2", ...]
    }
  ]
}
```

### 3.3 模型选择

| 任务 | 模型 | 原因 |
|------|------|------|
| 一周食谱生成 | **GLM-5.1** | 需要营养学知识和推理 |
| 购物清单生成 | GLM-4.5-air | 结构化提取，简单 |
| 冰箱剩菜推荐 | **GLM-5.1** (多模态) | 需要图片识别 + 食谱知识 |
| 单餐替换 | GLM-4.5-air | 简单替换逻辑 |

---

## 四、数据结构

```typescript
interface MealPlan {
  id: string;
  goal: '减脂' | '增肌' | '维持' | '控糖' | '自定义';
  dailyCalories: number;
  people: number;
  restrictions: string[];
  preferences: string[];
  weekStart: string;              // YYYY-MM-DD (周一)
  days: DayMeal[];
  shoppingList: ShoppingCategory[];
  createdAt: number;
}

interface DayMeal {
  day: string;                    // 周一~周日
  date: string;                   // YYYY-MM-DD
  meals: {
    breakfast: Meal;
    lunch: Meal;
    dinner: Meal;
    snack: Meal;
  };
  dailyTotal: number;
}

interface Meal {
  name: string;
  calories: number;
  ingredients: string[];
  cookTimeMin: number;
  difficulty: '简单' | '中等' | '复杂';
  briefSteps: string;
}

interface ShoppingCategory {
  category: string;               // 肉类/蔬菜/乳制品/主食/调味品
  items: string[];                // ["鸡胸肉 500g", ...]
}

interface FridgeInventory {
  id: string;
  photoUrl: string;
  items: string[];                // GLM 从冰箱照片识别的食材
  recognizedAt: number;
}
```

---

## 五、与拍照识热量的联动闭环

```
闭环 1: 食谱 → 拍照验证
  生成了食谱：周二午餐 = 鸡胸肉沙拉
  → 用户做好了，拍照发过来
  → GLM 识别：确实是鸡胸肉沙拉
  → 自动匹配到食谱，标记"已执行"
  → 同时触发记账 (拍照识热量 → 记一笔)

闭环 2: 实际饮食 → 偏差提醒
  食谱安排了 520 kcal 午餐
  → 用户实际吃了红烧肉 (830 kcal)
  → Agent: "今天午餐超标了 310 kcal，建议晚餐清淡一些"

闭环 3: 积累偏好数据
  用户连续 3 周生成的食谱中，总是替换"三文鱼"
  → Agent 学习到：用户不喜欢三文鱼
  → 后续食谱不再推荐三文鱼
```

---

## 六、实现 Task 分解

| # | Task | 预计 | 依赖 |
|---|------|------|------|
| T1 | 食谱生成 Prompt + GLM 调用 | 4h | GLM API 模块 |
| T2 | 一周食谱展示页面 | 4h | T1 |
| T3 | 购物清单生成与展示 | 3h | T2 |
| T4 | 单餐替换交互 | 3h | T2 |
| T5 | MealPlan Store + 持久化 | 2h | T2 |
| T6 | 冰箱拍照 → 剩菜推荐 | 4h | 拍照识物能力 |
| T7 | 偏好学习（记录替换历史） | 4h | T4 |
| T8 | 食谱 PDF 导出 | 3h | T2 |

**总计约 27h，MVP（T1-T5）约 16h，2 周可完成。**
