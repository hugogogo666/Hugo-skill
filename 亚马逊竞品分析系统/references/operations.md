# Operations Reference

## Source Priority

1. Existing structured Wenmai/SellerSprite/Keepa/SIF responses.
2. Existing local database records and raw payloads.
3. Public Amazon frontend checks for spot verification only.
4. Clearly labelled mock data for UI development only.

Relevant local provider wrappers are in:

- `backend/providers.py`
- `backend/worker.py`
- `/Users/mac/.codex/skills/wenmai-sellersprite-asin-detail`
- `/Users/mac/.codex/skills/wenmai-sellersprite-product-search`
- `/Users/mac/.codex/skills/wenmai-keepa-product-history`
- `/Users/mac/.codex/skills/wenmai-sif-asin-keywords`

## Competitor Verification Rubric

### Candidate stage

Search and category endpoints produce candidates. Candidate fields can include ASIN, title, category, search source, units, revenue, and a provisional score. Candidate price is not a current price until detail verification.

### Verified stage

A candidate enters the active pool only when all applicable checks pass:

- detail endpoint succeeds;
- returned detail ASIN exactly equals the requested ASIN;
- title and category are present enough to identify the product;
- title/category match the own product boundary;
- product is not own ASIN or one of its variations;
- product is not clearly an accessory, replacement, consumable, unrelated category, children-only product, or multipack/bundle;
- price is taken from detail and stored with `price_source` and capture time. If absent, store `N/A` and do not use the search price.

The data-source verification label does not guarantee frontend stock. If frontend confirmation matters, check `https://www.amazon.com/dp/<ASIN>` for US or the matching marketplace URL and report ambiguity such as bot challenge, 500 response, or unavailable state.

### Tiering

Competitor score is a 0-100 relevance score with explainable components:

- product form 25
- core function 20
- keyword overlap 20
- search intent 15
- scenario/target user 10
- price band 5
- category 5

Use A/B/C/D only after verification and relevance filtering. Do not inflate the pool to reach a target count.

## Five Core Skills

| Skill | Input | Output | Persistence | Schedule |
|---|---|---|---|---|
| Competitor discovery | project, own product boundary, category node | candidates, verification results, scores, tiers, stale rows | `competitor_candidates`, `competitors`, `raw_payloads`, `data_failures` | weekly |
| Keyword rank monitor | project, keyword library, own ASIN, verified competitors | organic/ad ranks, deltas, alerts | `keyword_rank_history`, `keyword_alerts` | daily |
| Competitor snapshot | verified ASIN pool | current daily facts and Listing snapshot | `competitor_snapshots`, `listing_snapshots` | daily |
| Change analysis | dated snapshots | before/after changes, evidence and severity | `competitor_changes`, `listing_changes` | after snapshot |
| Weekly Listing optimization | product Listing, keyword/rank changes, competitor evidence | specific recommendations requiring human review | `listing_recommendations` | weekly |

## Troubleshooting

### ASIN appears in SellerSprite but not on Amazon frontend

1. Confirm the requested ASIN and marketplace.
2. Call ASIN detail and compare the returned ASIN exactly.
3. Open the marketplace detail URL if possible.
4. Check title, category, availability, and price separately.
5. Keep the row as candidate or mark it unavailable when frontend status cannot be confirmed.

### Price looks strange

Check `price_source`, `price_captured_at`, and raw payload. A search result price is provisional and must not be shown as current. Variation, multipack, coupon, and list price can explain differences; do not normalize them away without evidence.

### All sections show the same data

Check that each page calls its own endpoint and that current rows are not being used in place of history. Dashboard, competitor pool, snapshots, changes, keywords, and Listing snapshots must query separate entities and preserve dates.

### Browser is closed but tasks stop

The Worker runs only while the Python process is alive. Use macOS `launchd` or Linux `systemd` to keep `python3 run.py` alive. Browser timers are not a valid scheduler.

### Provider failure

Record the endpoint/source, request ID when available, affected ASIN or keyword, error reason, and timestamp. Continue independent ASINs and show `N/A` for unavailable fields.
