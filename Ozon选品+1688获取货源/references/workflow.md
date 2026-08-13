# 两阶段工作流状态

| 状态 | 允许动作 | 禁止动作 |
|---|---|---|
| SCREENING_REQUIRED | 调用Ozon数据源、生成候选池 | 调用1688图片搜索 |
| SCREENING_COMPLETED | 展示候选摘要、请求用户确认 | 未确认就搜图 |
| SELECTION_CONFIRMED | 调用1688图片搜索、生成匹配结果 | 修改Ozon、计算利润 |
| IMAGE_MATCHING_COMPLETED | 汇报匹配结果、等待利润分析指令 | 自动上架或跟卖 |
