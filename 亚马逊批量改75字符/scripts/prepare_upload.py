#!/usr/bin/env python3
"""Prepare a minimal Amazon Seller Central title-update draft file.

Converts the validated result CSV (from generate_titles.py or import_titles.py)
into a tab-separated draft with only title-related update fields.

Use this as a paste/mapping aid for the exact category template downloaded
from Seller Central. Category templates vary; do not treat this file as a
universal upload template.
"""

import argparse
import csv
import os
import sys

from title_policy import first_value


ASIN_ALIASES = ["ASIN", "asin", "Asin"]
SKU_ALIASES = ["SKU", "sku", "seller_sku", "item_sku", "卖家SKU", "SKU编号"]
NAME_ALIASES = [
    "product_name", "Product Name", "Item Name", "产品名称", "标题", "改写标题",
    "商品名", "Nome do Produto",
]
HIGHLIGHT_ALIASES = [
    "highlight", "Product Highlight", "Item Highlights", "商品亮点",
    "改写商品亮点", "商品ハイライト", "Destaque",
]
COMPLIANT_ALIASES = ["compliant", "是否合规", "準拠"]


def main():
    ap = argparse.ArgumentParser(description="Prepare Amazon flat file from validated title CSV")
    ap.add_argument("--input", "-i", required=True, help="Validated title CSV (from generate or import)")
    ap.add_argument("--output", "-o", default="amazon_flat_file.txt", help="Output flat file path")
    ap.add_argument("--site", default="", help="Accepted for workflow compatibility; category template still controls upload fields")
    ap.add_argument("--feed-type", choices=["inventory", "listing"], default="listing",
                    help="Feed type (default: listing)")
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Amazon flat file header for listing loader
    if args.feed_type == "listing":
        # Partial update draft. Paste/map these columns into the exact category template.
        flat_header = [
            "SKU", "ASIN", "Product Name", "Item Highlights",
            "Update Delete", "feed_product_type"
        ]
    else:
        flat_header = [
            "SKU", "ASIN", "Product Name", "Item Highlights",
            "Update Delete"
        ]

    rows_exported = 0
    rows_skipped = 0

    with open(args.input, newline="", encoding="utf-8-sig") as fin:
        reader = csv.DictReader(fin)
        with open(args.output, "w", newline="", encoding="utf-8") as fout:
            writer = csv.writer(fout, delimiter="\t")
            writer.writerow(flat_header)

            for row in reader:
                sku = first_value(row, SKU_ALIASES)
                asin = first_value(row, ASIN_ALIASES)
                pname = first_value(row, NAME_ALIASES)
                hl = first_value(row, HIGHLIGHT_ALIASES)
                compliant = first_value(row, COMPLIANT_ALIASES)

                if not asin:
                    rows_skipped += 1
                    continue

                if compliant == "NO":
                    rows_skipped += 1
                    continue

                if args.feed_type == "listing":
                    out_row = [sku, asin, pname, hl, "PartialUpdate", ""]
                else:
                    out_row = [sku, asin, pname, hl, "PartialUpdate"]

                writer.writerow(out_row)
                rows_exported += 1

    print(f"Exported {rows_exported} titles to Amazon flat file: {args.output}")
    if rows_skipped:
        print(f"Skipped {rows_skipped} non-compliant or empty rows")
    print("\nSafety checklist before upload:")
    print("- Keep the original category listing report unchanged as a backup.")
    print("- Use the exact category template for these SKUs; split mixed categories.")
    print("- Submit only necessary fields plus required identifiers as PartialUpdate.")
    print("- Test 2-5 representative SKUs first, including parent/child variants when relevant.")
    print("- Review the processing report, detail page, search result page, mobile view, and variation relationship.")

    if rows_exported == 0:
        print("Warning: no rows were exported — check input for compliant titles", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
