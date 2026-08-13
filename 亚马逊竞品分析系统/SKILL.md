---
name: amazon-competitive-intelligence-monitor
description: "Use when the user wants to create, run, refresh, inspect, or troubleshoot the Amazon competitive intelligence monitoring system from only an Amazon marketplace and one own ASIN. Automatically discovers and verifies competitors, builds keyword intelligence, stores snapshots and changes in SQLite, monitors Listing data, generates evidence-based optimization suggestions, and presents the local HTML dashboard."
---

# Amazon Competitive Intelligence Monitor

## Purpose

Operate the local Amazon competitive intelligence system in:

`/Users/mac/Documents/稳卖Agent 2`

The system is a persistent HTML dashboard plus SQLite storage and a background Worker. It is not a static report. Use the bundled CLI for repeatable actions and use the browser URL for visual inspection.

## Trigger Examples

Use this skill when the user asks to:

- 从站点和一个自有 ASIN 创建 Amazon 监控项目
- 自动发现、核验或刷新竞品
- 检查竞品 ASIN 是否真实、价格是否可信
- 查看关键词排名、Keyword Gap、Listing 变化或市场信号
- 查看 Dashboard、竞品池、竞品历史快照或执行日志
- 启动、检查、暂停或排查 Amazon 监控任务
- 把 Amazon 竞品监控封装成长期运行的 Skill

## Non-Negotiable Data Rules

1. The user only needs to provide `marketplace` and `own_asin`. Do not require manual competitor ASINs or keyword lists unless a data source explicitly fails and the user requests a fallback.
2. Never treat a keyword-search row as a confirmed competitor. Search results are candidates only.
3. A current competitor must pass ASIN detail verification and product-boundary relevance checks. The detail response ASIN must exactly match the requested ASIN.
4. Price displayed as current must come from ASIN detail or a clearly named historical source. Never reuse an unverified search-list price. Missing price is `N/A`, never `0`.
5. A data-source match is not a guarantee that Amazon frontend stock or purchase availability is current. Describe verified rows as `数据源已核验`, not `前台可售`.
6. Exclude own ASIN, parent/child variations, duplicate ASINs, accessories, replacement parts, consumables, unrelated products, children/kids products when the own product is adult-focused, and multipacks/bundles when comparing single units.
7. Keep raw payloads, failure reasons, source names, and capture times. One failed field or ASIN must not abort the whole run.
8. Never expose, print, store, or commit the Wenmai API key. Read it only from `WENMAI_API_KEY` or `WENMAI_SECRET_KEY` in the process environment.
9. Never automatically modify an Amazon Listing. Recommendations require human acceptance and create a version record only.

## Quick Start

The project server should be kept alive by `launchd` or another service for browser-closed scheduling. For local testing:

```bash
cd "/Users/mac/Documents/稳卖Agent 2"
python3 run.py
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765).

Use the CLI for deterministic operations:

```bash
python3 "/Users/mac/.codex/skills/亚马逊竞品分析系统/scripts/monitor.py" health
python3 "/Users/mac/.codex/skills/亚马逊竞品分析系统/scripts/monitor.py" create --marketplace US --asin B0FXHWC1NJ --name "US Water Bottle"
python3 "/Users/mac/.codex/skills/亚马逊竞品分析系统/scripts/monitor.py" wait --task-id 25
python3 "/Users/mac/.codex/skills/亚马逊竞品分析系统/scripts/monitor.py" refresh-competitors --project-id 1
python3 "/Users/mac/.codex/skills/亚马逊竞品分析系统/scripts/monitor.py" competitors --project-id 1
python3 "/Users/mac/.codex/skills/亚马逊竞品分析系统/scripts/monitor.py" dashboard --project-id 1
```

The CLI starts the local server automatically when an API action needs it. It does not print secrets.

## Workflow

### 1. Create or select a project

Validate the marketplace and ASIN. Use the existing project when the same marketplace and ASIN already exist. Create a new project only when the user asks for a new monitoring project.

The first run executes:

1. Load own ASIN and Listing/product details.
2. Save product boundary, category node path, and variation ASINs.
3. Discover candidates using the own product's fine-grained category node first; keyword discovery is fallback only.
4. Verify candidate ASIN details and prices one by one.
5. Filter and score the verified pool into A/B/C/D tiers.
6. Build the keyword library and first rank snapshot.
7. Save immutable historical snapshots and initialize scheduled Worker tasks.

### 2. Inspect data quality before analysis

Run:

```bash
monitor.py competitors --project-id <id>
```

Report separately:

- `verified`: current data-source-verified competitors eligible for monitoring
- `candidates`: unverified, rejected, or failed candidates that must not enter monitoring
- `price_source`: the source used for each price
- `verification_reason`: why a candidate was accepted, rejected, or isolated

If the user says an ASIN cannot be found on Amazon, do not silently promote it. Re-run detail verification, compare the returned detail ASIN exactly, check the Amazon frontend URL if network access is available, and label any remaining uncertainty.

### 3. Run recurring skills

Use the corresponding server task endpoints or CLI commands:

- `competitor_discovery`: weekly category-first discovery, boundary filtering, verification, scoring, and stale-pool handling.
- `keyword_rank_monitor`: daily own-ASIN and competitor keyword rank capture.
- `competitor_snapshot`: daily price, rating, review, BSR, and Listing snapshot.
- `competitor_listing_refresh`: refresh the top verified competitor Listings.
- `competitor_history_refresh`: store Keepa-backed price and BSR series for the recent window.
- `competitor_change_analysis`: compare dated snapshots and write before/after changes.
- `weekly_listing_optimization`: generate evidence-first Listing recommendations.

Check task completion with:

```bash
monitor.py task --task-id <id>
```

A task that fails must remain visible as failed with an error and source. Do not report success based only on a queued response.

### 4. Present results for decisions

For Dashboard or daily brief requests, answer in this order:

1. Today’s 3-5 highest-priority facts.
2. ASINs and keywords supporting each fact.
3. Time window and source for each metric.
4. Separate factual observation from AI interpretation.
5. A concrete recommended action and whether it needs human approval.

For Listing recommendations, always include target position, current text, suggested text, added keyword or selling point, evidence count, related ASINs, ranking evidence, priority, and a warning when product capability has not been verified.

## Data Model and Provenance

SQLite is stored at:

`/Users/mac/Documents/稳卖Agent 2/data/amazon_intel.db`

Core entities include `projects`, `products`, `product_boundaries`, `competitors`, `competitor_candidates`, `competitor_snapshots`, `competitor_changes`, `keywords`, `keyword_rank_history`, `listing_snapshots`, `listing_versions`, `listing_recommendations`, `optimization_tracking`, `market_signals`, `skills`, `schedules`, `task_runs`, `raw_payloads`, and `data_failures`.

Current values and history are separate. Never overwrite a historical date with current values. Historical rows use uniqueness constraints such as `project_id + asin + snapshot_date` and `project_id + asin + keyword + rank_date`.

Read [references/operations.md](references/operations.md) for the source mapping, verification rubric, task map, and troubleshooting checklist.

## Mock and Real Data

`auto` is the normal mode. If a Wenmai key is available, the existing Wenmai scripts are used. If a provider is unavailable, the affected records are explicitly marked as partial, failed, or `MOCK DATA`; they must not be mixed with verified current competitors.

When a user asks whether data is real, show the source and capture time. Do not infer realness from a plausible title or price alone.

## Completion Criteria

Do not call the task complete until:

- the project can be opened at the local dashboard;
- the own ASIN and category boundary are saved;
- current competitors and isolated candidates are separate;
- current prices have explicit sources or `N/A`;
- history is persisted in SQLite;
- task status and failure reasons are inspectable;
- Python and JavaScript checks pass when code was changed.
