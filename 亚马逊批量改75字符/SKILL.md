---
name: amazon-batch-75-char-title
description: 亚马逊批量改75字符标题。用于批量改写 Amazon listing Product Name/商品名 与 Product Highlight/Item Highlights/商品亮点，默认将标题控制在70-74字符、商品亮点控制在110-120字符，同时按75/125新规、JP 80/150例外、中东站后台差异、COSMO关键词、禁用字符、促销词、重复词、移动端前段和批量上传安全流程进行校验。用户提到亚马逊批量标题改写、75字符标题、商品亮点补长、CSV/Excel表格改标题、标题太短漏卖点、Seller Central上传前校验时使用。
---

# 亚马逊批量改75字符标题

## Core Rule

默认输出高信息密度版本，而不是极短标题：

- Product Name / 商品名：目标 70-74 字符；硬上限多数站点 75，日本站硬上限 80。
- Product Highlight / Item Highlights / 商品亮点：目标 110-120 字符；硬上限多数站点 125，日本站硬上限 150。
- 优先级：硬性合规 > 目标长度 > COSMO埋词 > 文案顺滑。
- 字符数按实际字符串长度计算，包含空格和标点。

如果原始资料不足以自然写到目标区间，不要硬塞重复词；保持合规，并在输出的“提醒/备注”列说明信息不足。

## Workflow

1. 读取用户 CSV/Excel，保留原文件，不覆盖；输出使用递增版本名。
2. 识别站点列（`site`、`站点`、`Site`、`サイト`）。没有站点时默认 `us`，但在备注中说明默认值。
3. 从每行提取品牌、型号/系列、品类、产品形态、核心功能、关键规格、变体属性、卖点和场景词。
4. 改写 Product Name：先回答“这是什么产品”，再放最有搜索价值的功能或规格。
5. 改写 Product Highlight：补充标题放不下的参数、材质、兼容性、使用场景、差异化卖点和疑虑消除信息。
6. 校验字符数、禁用字符、促销/主观词、重复实词、COSMO覆盖、标题/亮点重复度和移动端前段。
7. 输出 CSV/Excel，并给出总行数、违规数、警告数、标题长度分布、亮点长度分布。

## Product Name Pattern

优先使用：

```text
[Brand] [Model/Series] [Product Form] [Product Type] [Core Function] [Key Spec or Variant]
```

执行要点：

- 前 40-45 字符必须看得出品牌/型号/产品类型/核心功能。
- 保留自然关键词组，例如 `Noise Cancelling Headphones`，不要为了凑字符拆散常用词。
- 子体可包含颜色、尺寸、包装数量等变体属性；父体通常不写具体颜色/尺寸。
- 使用阿拉伯数字表达数量和规格，例如 `2-Pack`，不要写 `Two-Pack`。
- 不要机械截断原标题尾部；先把词分成产品身份词、流量关键词、变体属性、转化卖点、低价值补充词。

## Highlight Pattern

商品亮点负责补足购买决策信息：

```text
[Key Differentiator], [Material/Spec], [Compatibility or Use Case], [Pain Point], [Scene]
```

执行要点：

- 前 20-30 字符放最强差异化卖点或最能减少疑虑的参数。
- 不要重复 Product Name 已经讲清楚的内容；重复词过多时重写亮点而不是换同义词堆砌。
- Name + Highlight 合计埋入 2-3 个 COSMO 关键词，优先选择场景词和痛点词。
- 预算词只在不触发促销/主观风险时使用；`Great Value`、`Best Value`、`Best Price`、`Premium`、`High Quality` 等默认避开。

## Hard Compliance

必须检查：

- 标题禁用特殊字符：`!` `$` `?` `_` `{` `}` `^` `¬` `¦`。
- 不写促销或主观评价：`Free Shipping`、`100% Quality Guaranteed`、`Best Seller`、`Hot Item`、`Great Value`、`Best Value`、`Best Price`、`Premium`、`High Quality` 等。
- 同一实词最多出现 2 次，品牌词也计算在内。
- 不要全大写或全小写；品牌官方写法、型号和行业缩写可保留。
- AE/SA 以及 EG/TR 等可能存在后台上线差异的站点，必须提醒以卖家后台类目模板、字段报错和站点公告为准。

## Output Columns

批量改写结果优先输出这些中文列，原始列可保留在后面：

```text
站点, ASIN, 原标题, 品牌, 类目, 标题字段名, 改写标题, 标题字符数, 标题字符上限,
亮点字段名, 改写商品亮点, 亮点字符数, 亮点字符上限, COSMO关键词,
是否合规, 问题, 提醒, 备注
```

`是否合规` 使用 `YES/NO`。硬性违规写入“问题”；目标长度不足、AE/SA后台差异、移动端预览、信息不足等写入“提醒/备注”。

## Scripts

Use the scripts from this skill directory:

```bash
python scripts/validate_dense_titles.py --input result.csv --site us
python scripts/validate_titles.py --input result.csv --site us --show-previews
python scripts/prepare_upload.py --input result.csv --output amazon_flat_file.txt --site us
```

- `validate_dense_titles.py` enforces the 70-74 / 110-120 target ranges by default and exits non-zero on misses.
- Add `--warn-only-targets` when the user only wants hard Amazon policy validation.
- `prepare_upload.py` only creates a minimal draft for mapping into the exact Seller Central category template; it is not a universal upload template.

## References

- Read `references/length-strategy.md` when deciding what to keep in title vs highlight, especially if the user worries the copy is too short or missing selling points.
- Read `references/policy-details.md` when explaining the policy logic, exceptions, upload workflow, or parent/child cautions.
- Read `references/cosmo-keywords.md` when selecting site-specific COSMO scene, pain-point, or budget-intent keywords.
