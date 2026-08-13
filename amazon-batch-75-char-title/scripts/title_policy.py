#!/usr/bin/env python3
"""Shared Amazon title policy checks for the title rewrite skill."""

from __future__ import annotations

from collections import Counter
import re
from typing import Iterable


SITE_CONFIG = {
    "us": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "ca": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "mx": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "uk": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "de": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "fr": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "it": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "es": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "nl": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "se": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "pl": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "jp": {"name_field": "商品名", "name_max": 80, "highlight_field": "商品ハイライト", "highlight_max": 150},
    "au": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "sg": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "in": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "br": {"name_field": "Nome do Produto", "name_max": 75, "highlight_field": "Destaque", "highlight_max": 125},
    "ae": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
    "sa": {"name_field": "Product Name", "name_max": 75, "highlight_field": "Item Highlights", "highlight_max": 125},
}

POLICY_CAVEAT_SITES = {"ae", "sa", "eg", "tr"}

PROHIBITED_TITLE_CHARS = set("!$?_{}^¬¦")

PROMOTIONAL_OR_SUBJECTIVE_PHRASES = [
    "free shipping",
    "100% quality guaranteed",
    "quality guaranteed",
    "best seller",
    "bestseller",
    "hot item",
    "hot sale",
    "top quality",
    "best quality",
    "high quality",
    "premium",
    "great value",
    "best value",
    "best price",
    "limited time",
    "sale",
]

STOPWORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "of",
    "on", "or", "the", "to", "with", "without", "de", "del", "la", "las",
    "le", "les", "el", "los", "di", "da", "do", "dos", "das", "para", "por",
    "und", "mit", "der", "die", "das", "ein", "eine", "en", "et", "pour",
}

COSMO_WORDS = [
    "for dorm", "for travel", "for office", "for home", "for car",
    "for gym", "for kitchen", "for bathroom", "for desk", "for camping",
    "for hiking", "for kids", "for baby", "for pet", "for seniors",
    "for beginners", "for women", "for men", "for outdoor", "for indoor",
    "portable", "mini", "small", "compact", "travel size",
    "easy clean", "easy to clean", "no spill", "leak proof", "quick dry",
    "no noise", "lightweight", "durable", "sturdy", "anti slip", "rust proof",
    "waterproof", "sweatproof", "fade resistant", "stain resistant",
    "dishwasher safe", "bpa free", "easy to use", "space saving",
    "affordable", "budget", "cost effective",
]

COSMO_PATTERNS = [re.compile(re.escape(word), re.IGNORECASE) for word in COSMO_WORDS]
WORD_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9+'-]*")


def get_site_config(site: str | None) -> dict:
    return SITE_CONFIG.get((site or "us").strip().lower(), SITE_CONFIG["us"])


def count_chars(text: str) -> int:
    return len(text or "")


def count_cosmo_words(text: str) -> list[str]:
    found = []
    for index, pattern in enumerate(COSMO_PATTERNS):
        if pattern.search(text or ""):
            found.append(COSMO_WORDS[index])
    return found


def prohibited_chars(text: str) -> list[str]:
    return sorted({ch for ch in text or "" if ch in PROHIBITED_TITLE_CHARS})


def promotional_phrases(text: str) -> list[str]:
    lowered = (text or "").casefold()
    return [phrase for phrase in PROMOTIONAL_OR_SUBJECTIVE_PHRASES if phrase in lowered]


def normalized_words(text: str) -> list[str]:
    words = []
    for token in WORD_PATTERN.findall(text or ""):
        word = token.casefold().strip("-'")
        if len(word) > 3 and word.endswith("s"):
            word = word[:-1]
        if len(word) < 2 or word in STOPWORDS:
            continue
        words.append(word)
    return words


def repeated_words(text: str) -> list[tuple[str, int]]:
    counts = Counter(normalized_words(text))
    return sorted((word, count) for word, count in counts.items() if count > 2)


def case_issue(text: str) -> str:
    latin_words = re.findall(r"[A-Za-z]{2,}", text or "")
    if len(latin_words) < 3:
        return ""
    if all(word.isupper() for word in latin_words):
        return "标题不应全大写"
    if all(word.islower() for word in latin_words):
        return "标题不应全小写"
    return ""


def content_words(text: str) -> set[str]:
    return {word for word in normalized_words(text) if len(word) > 3}


def highlight_repetition_warnings(product_name: str, highlight: str) -> list[str]:
    if not highlight:
        return []
    overlap = sorted(content_words(product_name) & content_words(highlight))
    if len(overlap) >= 4:
        sample = ", ".join(overlap[:6])
        return [f"商品亮点与标题重复词较多：{sample}"]
    return []


def preview_warnings(product_name: str, highlight: str) -> list[str]:
    warnings = []
    if count_chars(product_name) > 45:
        warnings.append(f"移动端标题前45字符预览：{product_name[:45]}")
    if highlight and count_chars(highlight) > 30:
        warnings.append(f"商品亮点前30字符预览：{highlight[:30]}")
    return warnings


def is_media_category(category: str) -> bool:
    lowered = (category or "").casefold()
    media_terms = ("books", "music", "video", "dvd", "blu-ray", "media")
    return any(term in lowered for term in media_terms)


def validate_title(
    product_name: str,
    highlight: str = "",
    *,
    site: str | None = "us",
    brand: str = "",
    category: str = "",
    min_cosmo: int = 2,
    check_cosmo: bool = True,
    include_previews: bool = False,
) -> dict:
    cfg = get_site_config(site)
    site_code = (site or "us").strip().lower()
    product_name = product_name or ""
    highlight = highlight or ""

    issues: list[str] = []
    warnings: list[str] = []
    name_len = count_chars(product_name)
    highlight_len = count_chars(highlight)
    media_exception = is_media_category(category)

    if not product_name.strip():
        issues.append("产品名称为空")
    elif name_len > cfg["name_max"] and not media_exception:
        issues.append(f"{cfg['name_field']} {name_len}>{cfg['name_max']} 字符")
    elif name_len > cfg["name_max"]:
        warnings.append("媒介类目可能不适用75字符新规，请以类目模板和后台提示为准")

    if highlight and highlight_len > cfg["highlight_max"]:
        issues.append(f"{cfg['highlight_field']} {highlight_len}>{cfg['highlight_max']} 字符")

    bad_chars = prohibited_chars(product_name)
    if bad_chars:
        issues.append("标题含禁用特殊字符：" + " ".join(bad_chars))

    promos = promotional_phrases(product_name)
    if promos:
        issues.append("标题含促销/主观评价词：" + "; ".join(promos))

    repeats = repeated_words(product_name)
    if repeats:
        issues.append("标题同一实词超过2次：" + "; ".join(f"{word}={count}" for word, count in repeats))

    case_msg = case_issue(product_name)
    if case_msg:
        issues.append(case_msg)

    if brand and product_name and not product_name.casefold().startswith(brand.casefold()[: min(len(brand), 12)]):
        warnings.append("标题首段未明显前置品牌/核心商品词，请人工确认是否合理")

    if site_code in POLICY_CAVEAT_SITES:
        warnings.append("该站点可能存在新标题字段上线差异，请以后台类目模板为准")

    cosmo = count_cosmo_words(product_name + " " + highlight)
    if check_cosmo and len(cosmo) < min_cosmo and product_name:
        issues.append(f"COSMO 词仅 {len(cosmo)} 个，不足 {min_cosmo} 个")

    warnings.extend(highlight_repetition_warnings(product_name, highlight))
    if include_previews:
        warnings.extend(preview_warnings(product_name, highlight))

    return {
        "name_len": name_len,
        "highlight_len": highlight_len,
        "name_limit": cfg["name_max"],
        "highlight_limit": cfg["highlight_max"],
        "name_field": cfg["name_field"],
        "highlight_field": cfg["highlight_field"],
        "cosmo_words": cosmo,
        "issues": issues,
        "warnings": warnings,
        "compliant": not issues,
    }


def first_value(row: dict, aliases: Iterable[str]) -> str:
    row_lower = {key.strip().casefold(): key for key in row}
    for alias in aliases:
        source = row_lower.get(alias.casefold())
        if source is not None:
            return (row.get(source) or "").strip()
    return ""
