---
name: amazon-ad-execution-erp-demo
description: Maintain and extend the standalone Amazon Ads automatic-execution ERP demo at /Users/mac/Documents/店铺Demo. Use when the user asks to modify the AdPilot advertising dashboard, simulated Amazon Ads data, Campaign/ASIN/Keyword monitoring, automation rules, Safety Guard, status auto-adjustment, trend/metric panels, or to debug/start this advertising project. Keep it strictly separate from the Amazon competitor-analysis project.
---

# Amazon Ads 自动执行 ERP Demo

## 项目边界

- 只操作广告项目：`/Users/mac/Documents/店铺Demo`。
- 禁止读取、合并或修改竞品分析项目：`/Users/mac/Documents/Amazon竞品分析Demo`，除非用户明确要求。
- 广告项目使用 `data/adpilot-db.json`；竞品分析项目使用独立数据库。
- 这是模拟 Amazon Ads 数据，不得声称已连接真实 Amazon 账户。

## 技术结构

- `index.html`：页面入口和左侧导航。
- `app.js`：前端页面、指标卡、自动化规则交互和本地规则持久化。
- `styles.css`：界面样式。
- `server.js`：本地 HTTP 服务与模拟 API。
- `mock-data.js`：50 个虚拟 ASIN、100 个 Campaign、400 个 Keyword/Target、150 个 Search Term 与 30 日指标。
- `engine.js`：广告规则判断和 Dry Run 决策引擎。
- `data/adpilot-db.json`：广告模拟数据库。

## 运行与验证

在项目目录执行：

```bash
npm test
npm start
```

默认访问 `http://localhost:8080`。如果 8080 被占用，服务会自动切换到 8081；以终端实际输出为准。

检查接口：

```text
GET /api/health
GET /api/dashboard?days=7|14|30
GET /api/asins
GET /api/campaigns
GET /api/keywords
GET /api/search-terms
POST /api/rules
POST /api/rules/preview
POST /api/safety/evaluate
```

## 功能实现要求

### 广告自动化

- 规则包括 ROAS、CPC、最少点击数、最低花费、统计周期、执行间隔和 Dry Run。
- 用户第一次点击“保存规则”后，必须把规则持久化，并自动应用到广告活动；不能要求用户每次重新勾选条件。
- 当前模拟规则保存到浏览器 `localStorage` 的 `adpilot-auto-config`。
- 保存规则后应立即重新计算广告状态：命中规则显示“已暂停”，未命中显示“运行中”，未接管显示“未接管”。
- 规则切换、阈值修改和保存后必须保持页面状态一致；显示命中原因和执行记录。
- 模拟模式只改变本地演示状态，不修改真实 Amazon 账户。

### 指标面板

首页优先展示易读的核心广告指标卡，而不是难以解释的 Spend/Sales 折线图：

- Impressions
- Clicks
- CTR
- CPC
- Spend
- Orders
- Sales
- CVR
- ACoS
- ROAS

支持 7/14/30 日切换，并在页面内解释指标含义。

### 数据与展示

- 保留 50 个虚拟 ASIN 的真实可运行模拟数据。
- 页面需展示 Campaign → ASIN → Keyword/Search Term 的层级关系。
- 所有状态、规则、操作均需明确标注为模拟或 Dry Run。
- 发生数据读取失败时使用中性提示，例如“当前数据暂不可获取”，不要暴露内部服务归责信息。

## 修改流程

1. 先确认需求属于广告项目，不要把竞品分析功能混入。
2. 读取相关文件，优先修改最小范围。
3. 若改动自动化规则，检查 `localStorage` 持久化、首次保存、刷新后恢复和状态重算。
4. 运行 `node --check app.js`、`node --check server.js` 和 `npm test`。
5. 启动服务并检查 `/api/health`，必要时检查首页是否返回 200。
6. 向用户返回完整本地路径，并说明启动地址和验证结果。
