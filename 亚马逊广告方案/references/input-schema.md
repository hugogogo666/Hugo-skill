# Excel 输入 JSON 结构

脚本接受 UTF-8 JSON。所有数组均可为空，但应尽可能填入有依据的内容。

```json
{
  "asin": "B0XXXXXXXX",
  "marketplace": "US",
  "snapshot_date": "2026-08-04",
  "product_url": "https://www.amazon.com/dp/B0XXXXXXXX",
  "summary": "一句话诊断",
  "overview": [{"dimension":"评分","value":"4.3 / 165","judgment":"有基础","impact":"大词竞价谨慎"}],
  "keywords": [{"priority":"S","keyword":"core keyword","intent":"核心需求","role":"战略排名","match":"精准","bid":"0.70–0.90","evidence":"数据依据","action":"执行动作","risk":"风险"}],
  "campaigns": [{"name":"SP-EX-Core","type":"SP手动精准","goal":"排名","targets":"核心词","strategy":"动态竞价-仅降低","bid":"0.70–0.90","budget_share":0.25,"rule":"管理规则"}],
  "economics": {"price":19.99,"target_acos":0.30,"expected_cvr":0.15,"target_orders_day":5},
  "roadmap": [{"stage":"准备期","time":"第0–3天","goal":"建立基线","actions":"动作","deliverable":"产出","acceptance":"验收","avoid":"禁止事项"}],
  "rules": [{"scenario":"有单且达标","condition":"近7–14天≥2单","check":"预算限制","action":"加价","range":"+5%–10%","review":"3–5天"}],
  "negatives": [{"term":"wrong term","type":"结构不匹配","match":"否定精准","action":"否定","reason":"原因","scope":"探索活动"}],
  "listing": [{"position":"标题","demand":"核心规格","suggestion":"前置表达","status":"待检查","priority":"高","note":"备注"}],
  "ranking_targets": [{"keyword":"core keyword","current":"约60","target":"40–50","priority":"战略","note":"备注"}],
  "kpis": [{"category":"结构目标","metric":"大词流量占比","current_target":"65%→50%","purpose":"降低依赖","priority":"高","source":"每周记录"}]
}
```

字段要求：

- `budget_share` 使用小数，例如 25% 写为 `0.25`。
- `target_acos` 和 `expected_cvr` 使用小数。
- `bid` 可写数值或区间文本。
- 缺失数据写入 `kpis`，说明影响和获取方式；不要用猜测值伪装成事实。
