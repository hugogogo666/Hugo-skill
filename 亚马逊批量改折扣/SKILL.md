---
name: amazon-sellercentral-batch-discounts
description: 查询和安全修改 Amazon Seller Central 的价格折扣（Price Discounts）。用于“批量折扣”“哪些 SKU 在打折”“折扣力度”“把某个 SKU 改为 X%”“应用并提交审核”等请求。默认只读；仅在用户明确给出 SKU、目标折扣并要求提交时修改现有活动。复用已登录的纽迈 Amazon US 店铺环境，不创建或删除活动。
---

# Amazon Seller Central Price Discounts

通过已登录的 Seller Central 页面读取价格折扣活动，并在明确授权后精确修改单个 SKU。

## 固定命令

助手：

```bash
HELPER="$WENMAI_HOME/skills/亚马逊批量改折扣/scripts/batch_discounts.py"
```

只读查询：

```bash
python3 "$HELPER" query
```

生成修改计划，不操作页面：

```bash
python3 "$HELPER" set-discount --sku GM-01 --percent 7
```

用户明确要求应用、提交或提交审核后：

```bash
python3 "$HELPER" set-discount --sku GM-01 --percent 7 --submit
```

目标活动不唯一时增加：

```bash
--promotion-id <UUID>
```

## 数据权威

- 活动、SKU、折扣百分比、承诺数量：Seller Central `discounts/api/getPromotion`。
- 原价和当前实时 Offer 价：店铺 SP-API，仅用于价格补充和同步验证。
- 不得使用 Product Pricing API 推断活动数量或活动 SKU。
- 折扣百分比直接读取 `percentageOffDiscount.percentage`，不得用价格反推。

## 校验规则

不要单独把 `aggregateValidationOutcome=ERROR` 判定为商品错误。仅当以下字段存在具体内容时报告实际错误：

- `clientErrors`
- `errors`

二者为空时，输出“无具体校验错误”。

## 修改安全规则

1. 用户必须明确提供 SKU、目标折扣百分比并要求实际提交。
2. 提交前重新查询，确保目标 SKU 只存在于一个活动；否则停止并要求指定活动。
3. 仅修改目标 SKU 的折扣百分比。
4. 不修改活动名称、日期、受众、承诺数量、最低折后价或其他 SKU。
5. 运行中的活动不得降低折扣百分比，因为这会提高折后价。
6. 不创建、删除或取消活动。
7. 缺少 `--submit` 时只能返回计划，不得改动页面。

## 提交与验证

提交后必须执行以下验证：

1. Seller Central 返回价格折扣控制面板。
2. 重新读取 `getPromotion`，确认目标 SKU 已保存为目标折扣。
3. 对比提交前后所有其他 SKU，确认折扣未变化。
4. 检查目标 SKU 的具体错误数量。
5. 补充读取实时 Offer 价。

活动配置保存成功不等于审核已经通过，也不等于前台价格已经同步。若活动接口已是新折扣，但实时 Offer 仍为旧价格，明确输出“已提交并保存，价格同步或审核状态待确认”，不得声称前台已经生效。

## 浏览器前置条件

- 默认店铺：纽迈 / Niubelety from California。
- 默认站点：Amazon US / `ATVPDKIKX0DER`。
- 复用已登录的 Seller Central 页面，不读取或索要账号密码。
- 未发现浏览器或登录状态时，停止并提示用户打开对应店铺的 Seller Central 价格折扣页面。

## 输出隐私

面向用户只显示：

- 活动名称和状态
- SKU
- 原价、折扣百分比、折后价、优惠金额
- 承诺数量
- 提交与验证状态

不得显示 ASIN、产品名称、标题、Cookie、令牌或店铺密钥。
