# 具体 Use Case：📸 拍照识别食物热量

> 优先级：P0（第一个落地）
> 来源：photo 话题 + 食话题交叉点

## 一、用户故事

**小李的日常**：
> 早上 9 点到公司，路边买了个煎饼果子。想记录一下热量，但懒得打开薄荷去搜。
> 掏出手机拍了一张，发给小龙虾："这个多少热量？"
> 小龙虾 3 秒回复："煎饼果子，约 450 大卡，碳水和油脂偏高。"
> 小李："记一下，早饭。"
> 小龙虾："✅ 已记录。"

---

## 二、核心交互设计

### 2.1 单图识别（MVP）

```
用户: [发送一张红烧肉照片]
Agent:
  📸 识别结果：红烧肉
  🔥 热量估算：约 280 kcal / 100g
  📏 份量估算：约 200g（盘子大小参考）
  📊 总热量：约 560 kcal

  营养成分（估算）:
  ┌──────────┬────────┐
  │ 蛋白质   │  28g   │
  │ 脂肪     │  42g   │
  │ 碳水     │  12g   │
  └──────────┴────────┘

  [记一笔] [查看同类食物对比]
```

### 2.2 多图 / 一桌菜

```
用户: [发送一张满桌菜的照片]
Agent:
  📸 识别到 5 道菜：

  | # | 菜品       | 热量(估算) |
  |---|-----------|-----------|
  | 1 | 宫保鸡丁  | 320 kcal  |
  | 2 | 麻婆豆腐  | 180 kcal  |
  | 3 | 清炒时蔬  |  80 kcal  |
  | 4 | 番茄蛋汤  | 120 kcal  |
  | 5 | 米饭      | 230 kcal  |
  |   | **合计**  | **930 kcal** |

  这顿饭营养比较均衡 👍
  [全部记一笔] [逐个调整份量]
```

### 2.3 追问与纠正

```
Agent: 📸 识别结果：宫保鸡丁，约 320 kcal
用户:  不是宫保鸡丁，是辣子鸡
Agent: ✅ 已纠正为辣子鸡
       🔥 辣子鸡 热量：约 380 kcal（比宫保鸡丁略高，油脂更多）

       我会记住这个纠正，下次提高识别准确度。
```

---

## 三、GLM 调用方案

### 3.1 Prompt 设计

```
你是一个专业的食物识别和热量估算助手。

请分析这张照片中的食物，输出 JSON：
{
  "items": [
    {
      "name": "食物名称",
      "name_en": "英文俗名",
      "category": "主食|肉类|蔬菜|汤类|水果|饮品|零食|调味品",
      "calories_per_100g": 数字,
      "estimated_weight_g": 数字,      // 根据盘子/碗/手作为参照
      "total_calories": 数字,
      "protein_g": 数字,
      "fat_g": 数字,
      "carbs_g": 数字,
      "confidence": 0.0-1.0            // 识别置信度
    }
  ],
  "total_calories": 数字,
  "meal_type": "早餐|午餐|晚餐|加餐",  // 根据时间判断
  "notes": "补充说明（如有不确定的地方）"
}

注意事项：
1. 如果无法识别某道菜，confidence 设为 0，name 填 "未知菜品"
2. 份量估算基于常见餐具尺寸（盘子≈家用 8 寸盘，碗≈家用饭碗）
3. 多道菜时，逐个识别并列出
4. 如果不是食物照片，返回 { "error": "NOT_FOOD" }
```

### 3.2 模型选择

| 步骤 | 模型 | 原因 |
|------|------|------|
| 食物识别 + 热量估算 | **GLM-5.1** (多模态) | 需要视觉理解 + 知识推理 |
| 营养数据补全 | GLM-4.5-air | 结构化数据提取，速度快 |
| 用户纠正学习 | GLM-4.5-air | 简单文本处理 |

### 3.3 调用时序

```
图片上传 (≤ 4MB)
  → Base64 编码
  → GLM-5.1 多模态调用 (图片 + prompt)
  → 解析 JSON 结果
  → 如果 confidence < 0.7，标注"识别不确定，请确认"
  → 渲染卡片
  → 用户可纠正 → 更新记忆
```

---

## 四、数据结构

```typescript
interface FoodRecord {
  id: string;
  photoUrl: string;              // 本地图片路径
  items: FoodItem[];
  totalCalories: number;
  mealType: '早餐' | '午餐' | '晚餐' | '加餐';
  date: string;                  // YYYY-MM-DD
  time: string;                  // HH:mm
  note?: string;                 // 用户备注
  corrected?: boolean;           // 是否经过用户纠正
  createdAt: number;
}

interface FoodItem {
  name: string;
  category: string;
  caloriesPer100g: number;
  estimatedWeight: number;       // g
  totalCalories: number;
  protein: number;
  fat: number;
  carbs: number;
  confidence: number;            // 0-1
}

interface DailyNutrition {
  date: string;
  meals: FoodRecord[];
  totalCalories: number;
  totalProtein: number;
  totalFat: number;
  totalCarbs: number;
  targetCalories?: number;       // 用户设定的每日目标
}
```

---

## 五、扩展场景（后续 Phase）

### 5.1 饮食日记

```
📊 今日饮食 (4月16日)

🌅 早餐  08:30  煎饼果子    450 kcal
🌞 午餐  12:15  红烧肉套餐  830 kcal
🌙 晚餐  --:--  (尚未记录)

累计: 1,280 / 目标 1,800 kcal
剩余: 520 kcal

[拍照记录晚餐] [查看本周趋势]
```

### 5.2 周报 / 月报

```
📊 4月第3周 饮食报告

  日均热量: 1,850 kcal (目标 1,800)
  超标天数: 2 天
  最常吃: 鸡胸肉 (5次), 米饭 (7次)

  营养分布:
  🥩 蛋白质  85g/天  (✅ 达标)
  🧈 脂肪    62g/天  (⚠️ 略高)
  🍞 碳水   220g/天  (✅ 达标)

  💡 建议: 脂肪偏高，建议减少油炸食品，清蒸/水煮替代

  [查看详细] [导出报告]
```

### 5.3 与食谱生成联动

```
用户: 这周想减脂，每天 1800 大卡，刚才午饭吃了红烧肉
Agent: 午餐 830 kcal 已记录。

       为了控制在 1,800 kcal，建议调整：
       🌅 早餐: 400 kcal → 燕麦 + 鸡蛋
       🌙 晚餐: 570 kcal → 清蒸鱼 + 蔬菜

       [生成本周食谱] [查看推荐晚餐]
```

---

## 六、实现 Task 分解

| # | Task | 预计 | 依赖 |
|---|------|------|------|
| T1 | ChatPanel 支持图片消息发送 | 3h | 无 |
| T2 | 图片预处理（压缩、Base64） | 2h | T1 |
| T3 | GLM 多模态 API 封装 | 3h | 无 |
| T4 | 食物识别 Prompt + JSON 解析 | 4h | T3 |
| T5 | 食物记录卡片渲染 | 3h | T4 |
| T6 | FoodRecord Store + 持久化 | 2h | T5 |
| T7 | 用户纠正交互 | 2h | T5 |
| T8 | 每日/每周统计页面 | 4h | T6 |

**总计约 23h，建议 2 人 sprint 1 周完成 MVP（T1-T5）。**
