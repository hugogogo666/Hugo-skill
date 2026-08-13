#!/usr/bin/env python3
"""Validate dense Amazon title rewrite output.

This validator keeps the hard Amazon policy checks from title_policy.py and
adds the preferred information-density target ranges:
Product Name 70-74 chars and Item Highlights 110-120 chars by default.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

from title_policy import (
    first_value,
    get_site_config,
    prohibited_chars,
    promotional_phrases,
    validate_title,
)


ASIN_ALIASES = ["ASIN", "asin", "Asin"]
SITE_ALIASES = ["site", "Site", "站点", "サイト"]
NAME_ALIASES = [
    "product_name",
    "产品名称",
    "ProductName",
    "Product Name",
    "Item Name",
    "标题",
    "title",
    "Title",
    "改写标题",
    "商品名",
    "Nome do Produto",
]
HIGHLIGHT_ALIASES = [
    "highlight",
    "商品亮点",
    "Highlight",
    "Product Highlight",
    "Item Highlights",
    "改写商品亮点",
    "商品ハイライト",
    "Destaque",
]
BRAND_ALIASES = ["brand", "品牌", "Brand"]
CATEGORY_ALIASES = ["category", "品类", "类目", "Category"]


def target_message(label: str, value: int, low: int, high: int) -> str:
    if value < low:
        return f"{label} {value}<{low} 目标字符，下限信息密度不足"
    if value > high:
        return f"{label} {value}>{high} 目标字符，虽可能未超硬上限但不符合本skill目标"
    return ""


def row_id(asin: str, index: int) -> str:
    return asin or f"row-{index}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate dense 75-char Amazon title rewrite CSV")
    ap.add_argument("--input", "-i", required=True, help="Input CSV file")
    ap.add_argument("--output", "-o", help="Optional CSV report path with validation columns")
    ap.add_argument("--site", default="us", help="Default site when no site column exists")
    ap.add_argument("--title-min", type=int, default=70, help="Preferred Product Name minimum")
    ap.add_argument("--title-max", type=int, default=74, help="Preferred Product Name maximum")
    ap.add_argument("--highlight-min", type=int, default=110, help="Preferred Highlight minimum")
    ap.add_argument("--highlight-max", type=int, default=120, help="Preferred Highlight maximum")
    ap.add_argument("--min-cosmo", type=int, default=2, help="Minimum COSMO words to require")
    ap.add_argument("--allow-low-cosmo", action="store_true", help="Warn manually instead of failing low COSMO coverage")
    ap.add_argument("--warn-only-targets", action="store_true", help="Do not fail when only preferred target ranges are missed")
    ap.add_argument("--show-previews", action="store_true", help="Include mobile-visible title/highlight previews as warnings")
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        return 1

    total = 0
    hard_violations = 0
    target_misses = 0
    warnings_count = 0
    title_lengths: list[int] = []
    highlight_lengths: list[int] = []
    report_rows: list[dict[str, str]] = []
    fieldnames: list[str] = []

    with open(args.input, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])

        for index, row in enumerate(reader, start=2):
            total += 1
            asin = first_value(row, ASIN_ALIASES)
            site = first_value(row, SITE_ALIASES) or args.site
            product_name = first_value(row, NAME_ALIASES)
            highlight = first_value(row, HIGHLIGHT_ALIASES)
            brand = first_value(row, BRAND_ALIASES)
            category = first_value(row, CATEGORY_ALIASES)
            cfg = get_site_config(site)

            result = validate_title(
                product_name,
                highlight,
                site=site,
                brand=brand,
                category=category,
                min_cosmo=args.min_cosmo,
                check_cosmo=not args.allow_low_cosmo,
                include_previews=args.show_previews,
            )

            issues = list(result["issues"])
            warnings = list(result["warnings"])

            title_low = min(args.title_min, cfg["name_max"])
            title_high = min(args.title_max, cfg["name_max"])
            highlight_low = min(args.highlight_min, cfg["highlight_max"])
            highlight_high = min(args.highlight_max, cfg["highlight_max"])

            target_issues = [
                msg
                for msg in [
                    target_message(result["name_field"], result["name_len"], title_low, title_high),
                    target_message(result["highlight_field"], result["highlight_len"], highlight_low, highlight_high),
                ]
                if msg
            ]

            highlight_bad_chars = prohibited_chars(highlight)
            if highlight_bad_chars:
                issues.append("商品亮点含禁用特殊字符：" + " ".join(highlight_bad_chars))

            highlight_promos = promotional_phrases(highlight)
            if highlight_promos:
                issues.append("商品亮点含促销/主观评价词：" + "; ".join(highlight_promos))

            title_lengths.append(result["name_len"])
            highlight_lengths.append(result["highlight_len"])

            if issues:
                hard_violations += 1
                print(
                    f"[FAIL] {row_id(asin, index)} site={site} "
                    f"name={result['name_len']}/{result['name_limit']} "
                    f"highlight={result['highlight_len']}/{result['highlight_limit']}: "
                    + "; ".join(issues)
                )

            if target_issues:
                target_misses += 1
                level = "WARN" if args.warn_only_targets else "MISS"
                print(
                    f"[{level}] {row_id(asin, index)} site={site}: "
                    + "; ".join(target_issues)
                )

            if warnings:
                warnings_count += 1
                print(f"[WARN] {row_id(asin, index)} site={site}: {'; '.join(warnings)}")

            out_row = dict(row)
            out_row.update(
                {
                    "dense_title_ok": "YES" if not issues and not target_issues else "NO",
                    "dense_hard_issues": "; ".join(issues),
                    "dense_target_issues": "; ".join(target_issues),
                    "dense_warnings": "; ".join(warnings),
                    "dense_cosmo_words": "; ".join(result["cosmo_words"]),
                    "dense_title_len": str(result["name_len"]),
                    "dense_highlight_len": str(result["highlight_len"]),
                }
            )
            report_rows.append(out_row)

    if args.output:
        extra_fields = [
            "dense_title_ok",
            "dense_hard_issues",
            "dense_target_issues",
            "dense_warnings",
            "dense_cosmo_words",
            "dense_title_len",
            "dense_highlight_len",
        ]
        out_fields = fieldnames + [f for f in extra_fields if f not in fieldnames]
        with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(report_rows)

    def avg(values: list[int]) -> float:
        return sum(values) / len(values) if values else 0.0

    print(
        "\nTotal: "
        f"{total}, Hard Violations: {hard_violations}, "
        f"Target Misses: {target_misses}, Warnings: {warnings_count}"
    )
    print(
        "Title lengths: "
        f"min={min(title_lengths) if title_lengths else 0}, "
        f"max={max(title_lengths) if title_lengths else 0}, "
        f"avg={avg(title_lengths):.1f}"
    )
    print(
        "Highlight lengths: "
        f"min={min(highlight_lengths) if highlight_lengths else 0}, "
        f"max={max(highlight_lengths) if highlight_lengths else 0}, "
        f"avg={avg(highlight_lengths):.1f}"
    )

    if hard_violations:
        return 1
    if target_misses and not args.warn_only_targets:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
