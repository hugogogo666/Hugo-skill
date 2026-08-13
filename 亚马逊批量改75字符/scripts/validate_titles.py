#!/usr/bin/env python3
"""Validate Amazon title CSV against title policy and COSMO keyword coverage.

Expected input CSV columns (at minimum):
  ASIN, product_name, highlight

Chinese/generated aliases are supported, including:
  站点, 改写标题, 改写商品亮点

Optional columns are ignored. Output prints violations to stdout and exits
non-zero if any title is non-compliant.
"""

import argparse
import csv
import sys

from title_policy import first_value, validate_title


ASIN_ALIASES = ["ASIN", "asin", "Asin"]
SITE_ALIASES = ["site", "Site", "站点", "サイト"]
NAME_ALIASES = [
    "product_name", "产品名称", "ProductName", "Product Name", "Item Name",
    "标题", "title", "Title", "改写标题", "商品名", "Nome do Produto",
]
HIGHLIGHT_ALIASES = [
    "highlight", "商品亮点", "Highlight", "Product Highlight", "Item Highlights",
    "改写商品亮点", "商品ハイライト", "Destaque",
]
BRAND_ALIASES = ["brand", "品牌", "Brand"]
CATEGORY_ALIASES = ["category", "品类", "类目", "Category"]


def main():
    ap = argparse.ArgumentParser(description="Validate Amazon title CSV")
    ap.add_argument("--input", "-i", required=True, help="Input CSV file")
    ap.add_argument("--site", default="us", help="Default site when no site column exists")
    ap.add_argument("--min-cosmo", type=int, default=2, help="Minimum COSMO words to require")
    ap.add_argument("--allow-low-cosmo", action="store_true", help="Warn manually instead of failing low COSMO coverage")
    ap.add_argument("--show-previews", action="store_true", help="Include mobile-visible title/highlight previews as warnings")
    args = ap.parse_args()

    violations = 0
    warnings = 0
    total = 0

    with open(args.input, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            asin = first_value(row, ASIN_ALIASES)
            site = first_value(row, SITE_ALIASES) or args.site
            pname = first_value(row, NAME_ALIASES)
            hl = first_value(row, HIGHLIGHT_ALIASES)
            brand = first_value(row, BRAND_ALIASES)
            category = first_value(row, CATEGORY_ALIASES)

            result = validate_title(
                pname,
                hl,
                site=site,
                brand=brand,
                category=category,
                min_cosmo=args.min_cosmo,
                check_cosmo=not args.allow_low_cosmo,
                include_previews=args.show_previews,
            )

            if result["issues"]:
                violations += 1
                print(
                    f"[FAIL: {'; '.join(result['issues'])}] "
                    f"ASIN={asin} site={site} "
                    f"name_len={result['name_len']}/{result['name_limit']} "
                    f"highlight_len={result['highlight_len']}/{result['highlight_limit']} "
                    f"cosmo={len(result['cosmo_words'])}"
                )
                print(f"  product_name: {pname}")
                print(f"  highlight: {hl}")
            if result["warnings"]:
                warnings += 1
                print(f"[WARN] ASIN={asin} site={site}: {'; '.join(result['warnings'])}")

    print(f"\nTotal: {total}, Violations: {violations}, Warnings: {warnings}")
    if violations:
        sys.exit(1)


if __name__ == "__main__":
    main()
