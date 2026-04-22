# 具体 Use Case：📸 拍照识物（万物识别）

> 优先级：P1（拍照识热量完成后自然延伸）
> 来源：photo 话题

## 一、用户故事

**小王的日常**：
> 散步看到一棵树不认识，拍照发给小龙虾："这是什么树？"
> 小龙虾："这是银杏树（Ginkgo biloba），秋天叶子会变金黄。目前正处于生长期。"
>
> 超市看到一瓶酒不知道好不好："这酒怎么样？"
> 小龙虾："这是 2020 年份的茅台王子酒，市场参考价 ¥280-320。酱香型，适合送礼或收藏。"
>
> 朋友发了个表情包不知道出处："这个是什么角色？"
> 小龙虾："这是《间谍过家家》中的阿尼亚·福杰（Anya Forger）。"

---

## 二、核心交互设计

### 2.1 通用物品识别

```
用户: [发送一张植物照片]
Agent:
  🔍 识别结果：银杏（Ginkgo biloba）

  📋 基本信息：
  - 科属：银杏科 银杏属
  - 类型：落叶乔木
  - 原产地：中国
  - 特点：活化石植物，2.7 亿年前已存在

  🌿 养护知识：
  - 喜阳光充足，耐寒
  - 生长缓慢但寿命极长
  - 秋季叶色金黄，观赏价值高

  [这是什么科？] [附近哪里有？] [继续探索]
```

### 2.2 商品识别 + 比价

```
用户: [发送一张商品包装照片]
Agent:
  🔍 识别结果：农夫山泉东方树叶 茉莉花茶 500ml

  📋 商品信息：
  - 品牌：农夫山泉 东方树叶
  - 类型：无糖茶饮料
  - 规格：500ml
  - 主要成分：水、茶叶、维生素C

  💰 参考价格：
  - 超市零售：¥4.5-5.5
  - 电商整箱(15瓶)：¥55-65 (约 ¥3.7/瓶)

  📊 营养：0 糖 0 脂，热量约 0 kcal ✅

  [在哪里买便宜] [同类对比]
```

### 2.3 文档/文字识别（OCR）

```
用户: [发送一张菜单照片]
Agent:
  🔍 识别到菜单内容：

  | 菜品         | 价格   |
  |-------------|--------|
  | 小炒黄牛肉   | ¥ 48   |
  | 剁椒鱼头     | ¥ 58   |
  | 干锅花菜     | ¥ 28   |
  | 酸辣土豆丝   | ¥ 18   |
  | 米饭         | ¥  2   |

  👥 4 人就餐推荐：小炒黄牛肉 + 剁椒鱼头 + 干锅花菜 + 米饭
  预估 ¥140，人均 ¥35

  [帮我点菜] [记录消费]
```

---

## 三、GLM 调用方案

### 3.1 统一识别 Prompt

```
你是一个全能的物品识别助手。请分析这张照片，识别其中的主要内容。

输出 JSON：
{
  "type": "plant|animal|food|product|document|scene|art|vehicle|other",
  "items": [
    {
      "name": "中文名称",
      "name_en": "English name",
      "confidence": 0.0-1.0,
      "description": "100字以内的简要介绍",
      "details": {
        // 根据类型填充不同字段
      }
    }
  ],
  "tags": ["标签1", "标签2"],
  "suggested_questions": ["用户可能想追问的3个问题"]
}

类型特定的 details 字段：
- plant: family, genus, care_tips, flowering_season
- food: calories, ingredients, cuisine_type
- product: brand, price_range, purchase_channels
- document: text_content (OCR), language, document_type
- scene: location_type, weather, time_of_day
```

### 3.2 二次深入调用

当用户追问时，使用上下文 + GLM 深入回答：

```
用户追问: 这种花怎么养？
→ GLM-5.1 (纯文本)：
  上下文: 用户刚识别了"蝴蝶兰"
  Prompt: "关于蝴蝶兰的养护方法，从光照、浇水、施肥、温度四个方面详细说明"
```

---

## 四、数据结构

```typescript
interface RecognitionResult {
  id: string;
  photoUrl: string;
  type: 'plant' | 'animal' | 'food' | 'product' | 'document' | 'scene' | 'art' | 'vehicle' | 'other';
  items: RecognizedItem[];
  tags: string[];
  createdAt: number;
}

interface RecognizedItem {
  name: string;
  nameEn: string;
  confidence: number;
  description: string;
  details: Record<string, string | number>;
}

// 识别历史（方便回溯和积累知识）
interface RecognitionHistory {
  items: RecognitionResult[];
  // 按标签聚合
  tagIndex: Map<string, string[]>;
}
```

---

## 五、与拍照识热量的关系

```
拍照识热量 (已实现)
  │
  ├── 识别逻辑复用: 图片上传 → GLM 多模态 → JSON 解析
  ├── UI 复用: 识别结果卡片组件
  │
  └── 扩展点:
      ├── 新增识别类型 (plant, product, document...)
      ├── prompt 切换 (食物 prompt → 通用 prompt)
      └── 追问对话 (上下文记忆)
```

**改动量**：
- 在食物识别基础上，新增 1 个通用 prompt 模板
- 新增 type 路由（食物走食物 prompt，其他走通用 prompt）
- 识别结果卡片新增 type 判断，渲染不同 detail 字段
- **约 40% 代码可复用**

---

## 六、实现 Task 分解

| # | Task | 预计 | 依赖 |
|---|------|------|------|
| T1 | 通用识别 prompt 模板 | 3h | 拍照识热量 T4 |
| T2 | 识别类型路由（先判断是食物还是其他） | 2h | T1 |
| T3 | 通用识别结果卡片 | 3h | T2 |
| T4 | OCR 文字提取（文档类型） | 4h | T2 |
| T5 | 商品详情 + 价格查询 | 4h | T2 |
| T6 | 识别历史页面 | 3h | T3 |

**总计约 19h，在拍照识热量基础上约需 1 周。**
