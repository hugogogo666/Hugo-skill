# COSMO 关键词分类与埋词策略

## 三大 COSMO 关键词维度

COSMO 算法下的关键词本质是能够匹配场景/需求/意图的中长尾词。统称为场景词，分三类：

### 1. 场景词

描述具体使用场景的词。

示例：
- `small blender for dorm`（宿舍用小搅拌机）
- `travel mini food processor`（旅行用迷你食物处理器）
- `office desk air purifier`（办公桌空气净化器）

### 2. 痛点词

描述用户痛点或需求的词，反映消费者想解决的问题。

示例：
- `easy clean mini food processor`（易清洗）
- `no spill water bottle`（防漏）
- `quick dry towel`（快干）
- `leak proof lunch box`（防漏饭盒）

### 3. 预算词

带预算或价格限定的词，匹配价格敏感搜索。

示例：
- `under $25 portable air pump`（25 美元以下）
- `budget friendly gaming chair`（预算友好）
- `best air purifier under $50`（50 美元以下最佳）

## 埋词原则

### 合规优先

COSMO 埋词不能覆盖标题合规要求。若预算词或价值判断词带有促销、主观评价或禁用符号风险，应优先选择场景词、痛点词或更客观的参数表达。

- 避免在 Product Name 中使用 `Great Value`、`Best Value`、`Best Seller`、`Hot Item` 等主观/促销词。
- 避免在 Product Name 中使用带 `$` 的预算词，因为 `$` 属于标题禁用特殊字符。
- `Item Highlights` 也应尽量客观，用具体参数、兼容性、场景和痛点表达购买理由。

### 新品阶段

新品前期放弃泛大词（如 "blender" "headphones"），主攻口语化场景长尾词（Alexa 用户原生提问句式）。

### 埋词位置

COSMO 关键词应埋入：
1. 产品名称（75 字符）
2. 商品亮点（125 字符）
3. 5 点描述
4. 产品描述
5. Search Terms（ST）

### 埋词优先级（标题字段内）

产品名称（75 字符）中：
- 首词：品牌或核心产品词（A9 权重最高位置）
- 第 2-4 词：核心关键词 + 1 个场景词
- 末尾：关键属性（尺寸/容量/数量）

商品亮点（125 字符）中：
- 补充产品名称未覆盖的场景词/痛点词/预算词
- 不与产品名称重复
- 加入差异化卖点

### 示例对照

产品：便携式 USB 搅拌机

| 字段 | 内容 | 埋入 COSMO 词 |
|------|------|---------------|
| 产品名称 | `Portable USB Blender for Shakes Smoothies Dorm Travel 14oz` | dorm（场景）、travel（场景） |
| 商品亮点 | `BPA free mini blender, easy clean, under $25, dishwasher safe, 6 blade personal fruit juice blender for office` | easy clean（痛点）、under $25（预算）、office（场景） |

## 词库来源

- 竞品 ASIN 反查（提供 10 个以内竞品 ASIN）
- Alexa 原生提问句式挖掘
- 消费者搜索意图分析
- 场景/痛点/预算三维交叉组合
