#!/usr/bin/env python3
"""Query and safely edit Seller Central Price Discounts through a logged-in Wenmai browser."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import websocket

MARKETPLACE_ID = "ATVPDKIKX0DER"
DISCOUNTS_URL = "https://sellercentral.amazon.com/discounts"
ALLOWED_ORIGIN = "https://bot.hitoor.com"
DETAIL_PREFIX = "https://sellercentral.amazon.com/discounts/detail/US/"


class Cdp:
    def __init__(self, url: str):
        self.ws = websocket.create_connection(url, origin=ALLOWED_ORIGIN, timeout=30)
        self.next_id = 0

    def call(self, method: str, params: Optional[dict] = None) -> dict:
        self.next_id += 1
        request_id = self.next_id
        self.ws.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(message["error"].get("message", str(message["error"])))
                return message.get("result", {})

    def evaluate(self, expression: str, await_promise: bool = False) -> Any:
        result = self.call("Runtime.evaluate", {
            "expression": expression,
            "awaitPromise": await_promise,
            "returnByValue": True,
        })
        payload = result.get("result", {})
        if payload.get("subtype") == "error":
            raise RuntimeError(payload.get("description") or "浏览器脚本执行失败")
        return payload.get("value")

    def close(self) -> None:
        self.ws.close()


def discover_debug_ports() -> List[int]:
    output = subprocess.check_output(["ps", "-axo", "command="], text=True)
    ports: List[int] = []
    for line in output.splitlines():
        if "WenMaiAIBrowser" not in line:
            continue
        match = re.search(r"--remote-debugging-port=(\d+)", line)
        if match and int(match.group(1)) not in ports:
            ports.append(int(match.group(1)))
    return ports


def get_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)


def select_tab() -> dict:
    for port in discover_debug_ports():
        try:
            tabs = get_json(f"http://127.0.0.1:{port}/json/list")
        except Exception:
            continue
        pages = [tab for tab in tabs if tab.get("type") == "page"]
        seller_tabs = [tab for tab in pages if "sellercentral.amazon.com" in tab.get("url", "")]
        if seller_tabs:
            discount_tabs = [tab for tab in seller_tabs if "/discounts" in tab.get("url", "")]
            return (discount_tabs or seller_tabs)[0]
    raise RuntimeError("未发现已登录的稳卖浏览器 Seller Central 页面")


def wait_until(cdp: Cdp, expression: str, timeout: float = 20, interval: float = 0.5) -> Any:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = cdp.evaluate(expression)
        if last:
            return last
        time.sleep(interval)
    return last


def collect_promotion_ids(cdp: Cdp) -> List[str]:
    current_url = cdp.evaluate("location.href") or ""
    detail_match = re.search(r"/discounts/detail/[^/]+/([0-9a-f-]{36})", current_url, re.I)
    if detail_match:
        return [detail_match.group(1)]

    cdp.call("Network.enable")
    cdp.evaluate(f"location.href={json.dumps(DISCOUNTS_URL)}")
    wait_until(cdp, "document.readyState === 'complete'", timeout=15)
    time.sleep(3)

    ids = cdp.evaluate(r'''(()=>{
      const values=[];
      for(const a of document.querySelectorAll('a[href*="/discounts/detail/"]')) values.push(a.href);
      for(const e of performance.getEntriesByType('resource')) values.push(e.name);
      const ids=[];
      for(const value of values){
        const matches=String(value).match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/ig)||[];
        for(const id of matches) if(!ids.includes(id)) ids.push(id);
      }
      return ids;
    })()''') or []
    if ids:
        return ids

    body = cdp.evaluate("document.body.innerText") or ""
    if "价格折扣" not in body and "Price Discounts" not in body:
        raise RuntimeError("稳卖浏览器尚未登录 Seller Central")
    raise RuntimeError("未能自动识别活动 ID；请在浏览器中打开任一价格折扣活动详情后重试")


def fetch_promotion(cdp: Cdp, promotion_id: str) -> dict:
    path = (
        "/discounts/api/getPromotion?marketplaceId=" + MARKETPLACE_ID
        + "&promotionId=" + promotion_id + "&includeAsinMetrics=true"
    )
    expression = f"fetch({json.dumps(path)}).then(async r => ({{status:r.status,text:await r.text()}}))"
    raw = cdp.evaluate(expression, await_promise=True)
    if not raw or raw.get("status") != 200:
        raise RuntimeError(f"活动 {promotion_id} 详情接口请求失败")
    data = json.loads(raw["text"])
    if data.get("promotionDetails"):
        return data["promotionDetails"]
    raise RuntimeError(f"活动 {promotion_id} 未返回 promotionDetails")


def load_spapi_helper():
    helper_path = (
        Path(os.environ.get(
            "WENMAI_HOME",
            str(Path.home() / "Library/Application Support/Wenmai Agent/wenmai-cli"),
        ))
        / "skills/amazon-spapi-niuman/scripts/amazon_spapi_tool.py"
    )
    spec = importlib.util.spec_from_file_location("amazon_spapi_tool", helper_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载 Amazon SP-API 助手")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    creds = helper.load_env(helper.DEFAULT_ENV)
    helper.require_config(creds)
    session = helper.session_for(creds)
    access_token = helper.get_access_token(session, creds)
    return helper, creds, session, access_token


def enrich_prices(items: List[dict]) -> None:
    try:
        helper, creds, session, access_token = load_spapi_helper()
    except Exception as exc:
        print(f"价格补充跳过: {exc}", file=sys.stderr)
        return

    for item in items:
        try:
            response = helper.spapi_get(
                session, creds, access_token, "/products/pricing/v0/price",
                params={"MarketplaceId": MARKETPLACE_ID, "ItemType": "Sku", "Skus": item["sku"]},
            )
        except Exception:
            continue
        payload = response.get("payload") or []
        if not payload or payload[0].get("status") != "Success":
            continue
        offers = ((payload[0].get("Product") or {}).get("Offers") or [])
        if not offers:
            continue
        offer = offers[0]
        regular = (offer.get("RegularPrice") or {}).get("Amount")
        listing = ((offer.get("BuyingPrice") or {}).get("ListingPrice") or {}).get("Amount")
        if regular is not None:
            item["regular_price"] = round(float(regular), 2)
        if listing is not None:
            item["discounted_price"] = round(float(listing), 2)
        if regular is not None and listing is not None:
            item["discount_amount"] = round(float(regular) - float(listing), 2)
        time.sleep(0.2)


def normalize(details: dict, enrich: bool = True) -> dict:
    promotion = details.get("promotion") or {}
    basic = promotion.get("promotionBasic") or {}
    raw_metrics = details.get("metrics") or {}
    metrics = {key: value for key, value in raw_metrics.items() if key.lower() != "asins"}
    items = []
    for selector in details.get("productSelectorsList") or []:
        discount = selector.get("percentageOffDiscount") or {}
        client_errors = selector.get("clientErrors") or []
        server_errors = selector.get("errors") or []
        items.append({
            "sku": selector.get("sku"),
            "discount_percent": discount.get("percentage"),
            "minimum_discounted_price": discount.get("minimumDiscountedPrice"),
            "committed_quantity": selector.get("quantity"),
            # Do not interpret aggregateValidationOutcome alone as a real error.
            "validation_has_error": bool(client_errors or server_errors),
            "validation_error_count": len(client_errors) + len(server_errors),
        })
    if enrich:
        enrich_prices(items)
    return {
        "promotion_id": basic.get("promotionId"),
        "title": basic.get("title"),
        "status": basic.get("status"),
        "audience": (basic.get("customerTarget") or {}).get("audience"),
        "start_date": promotion.get("startDate"),
        "end_date": promotion.get("endDate"),
        "product_count": len(items),
        "committed_units": sum(int(item.get("committed_quantity") or 0) for item in items),
        "metrics": metrics,
        "products": items,
    }


def query(cdp: Cdp, promotion_id: Optional[str] = None, enrich: bool = True) -> dict:
    ids = [promotion_id] if promotion_id else collect_promotion_ids(cdp)
    activities = [normalize(fetch_promotion(cdp, pid), enrich=enrich) for pid in ids]
    running = [activity for activity in activities if activity.get("status") == "Running"]
    return {
        "source": "Seller Central > Marketing/Advertising > Price Discounts",
        "marketplace_id": MARKETPLACE_ID,
        "activity_count": len(activities),
        "running_activity_count": len(running),
        "activities": activities,
    }


def product_map(activity: dict) -> Dict[str, dict]:
    return {str(item.get("sku")): item for item in activity.get("products", []) if item.get("sku")}


def find_unique_target(cdp: Cdp, sku: str, promotion_id: Optional[str]) -> Tuple[dict, dict]:
    result = query(cdp, promotion_id=promotion_id, enrich=False)
    matches = []
    for activity in result["activities"]:
        item = product_map(activity).get(sku)
        if item:
            matches.append((activity, item))
    if not matches:
        raise RuntimeError(f"未在已读取的价格折扣活动中找到 SKU：{sku}")
    if len(matches) != 1:
        raise RuntimeError(f"SKU {sku} 同时存在于多个活动，请指定 --promotion-id")
    return matches[0]


def open_detail_and_wait(cdp: Cdp, promotion_id: str, sku: str) -> None:
    target_url = DETAIL_PREFIX + promotion_id
    current = cdp.evaluate("location.href") or ""
    if target_url not in current:
        cdp.evaluate(f"location.href={json.dumps(target_url)}")
    wait_until(cdp, "document.readyState === 'complete'", timeout=20)
    found = wait_until(
        cdp,
        f"!!document.querySelector('[role=\"row\"][row-id={json.dumps(sku)}]')",
        timeout=15,
    )
    if found:
        return
    # AG Grid virtualizes rows. Scroll through the grid without selecting or editing anything.
    for ratio in (0, .2, .4, .6, .8, 1):
        expression = f'''(()=>{{
          const viewport=document.querySelector('.ag-body-viewport');
          if(viewport) viewport.scrollTop=(viewport.scrollHeight-viewport.clientHeight)*{ratio};
          return true;
        }})()'''
        cdp.evaluate(expression)
        time.sleep(0.6)
        if cdp.evaluate(f"!!document.querySelector('[role=\"row\"][row-id={json.dumps(sku)}]')"):
            return
    raise RuntimeError(f"活动详情页未找到 SKU 行：{sku}")


def stage_percent(cdp: Cdp, sku: str, percent: int) -> dict:
    expression = f'''(()=>{{
      const row=document.querySelector('[role="row"][row-id={json.dumps(sku)}]');
      if(!row) return {{ok:false,error:'SKU row not found'}};
      const input=row.querySelector('[col-id="percentOff"] kat-input');
      if(!input) return {{ok:false,error:'discount input not found'}};
      const before=Number(input.value ?? input.getAttribute('value'));
      input.value=String({percent});
      input.setAttribute('value',String({percent}));
      input.dispatchEvent(new InputEvent('input',{{bubbles:true,composed:true,inputType:'insertText',data:String({percent})}}));
      input.dispatchEvent(new Event('change',{{bubbles:true,composed:true}}));
      input.dispatchEvent(new Event('blur',{{bubbles:true,composed:true}}));
      return {{ok:true,before,after:Number(input.value ?? input.getAttribute('value'))}};
    }})()'''
    result = cdp.evaluate(expression) or {}
    if not result.get("ok") or int(result.get("after", -1)) != percent:
        raise RuntimeError("未能在活动编辑页准确设置目标折扣")
    time.sleep(1.5)
    state = cdp.evaluate(f'''(()=>{{
      const row=document.querySelector('[role="row"][row-id={json.dumps(sku)}]');
      const button=document.querySelector('kat-button.submit-button');
      return {{
        percent:Number(row?.querySelector('[col-id="percentOff"] kat-input')?.value),
        price_preview:(row?.querySelector('[col-id="pricePreview"]')?.innerText||'').replace(/\\s+/g,' ').trim(),
        submit_enabled:!!button && !(button.disabled||button.hasAttribute('disabled'))
      }};
    }})()''') or {}
    if state.get("percent") != percent or not state.get("submit_enabled"):
        raise RuntimeError("编辑页未形成可提交的目标折扣变更")
    return state


def click_submit(cdp: Cdp) -> None:
    result = cdp.evaluate(r'''(()=>{
      const button=document.querySelector('kat-button.submit-button');
      if(!button) return {ok:false,error:'submit button not found'};
      if(button.disabled||button.hasAttribute('disabled')) return {ok:false,error:'submit button disabled'};
      button.click(); return {ok:true};
    })()''') or {}
    if not result.get("ok"):
        raise RuntimeError("无法提交编辑：" + str(result.get("error") or "未知原因"))
    # A successful submission normally returns to the discounts dashboard.
    wait_until(cdp, "location.pathname === '/discounts' || document.readyState === 'complete'", timeout=20)
    time.sleep(2)


def verify_persisted(cdp: Cdp, promotion_id: str, sku: str, percent: int, before: Dict[str, dict]) -> dict:
    deadline = time.time() + 35
    latest = None
    while time.time() < deadline:
        details = fetch_promotion(cdp, promotion_id)
        latest = normalize(details, enrich=False)
        item = product_map(latest).get(sku)
        if item and item.get("discount_percent") == percent:
            break
        time.sleep(2)
    if latest is None:
        raise RuntimeError("提交后未能读取活动详情")
    after = product_map(latest)
    target = after.get(sku)
    config_verified = bool(target and target.get("discount_percent") == percent)
    changed_others = []
    for other_sku, old in before.items():
        if other_sku == sku:
            continue
        new = after.get(other_sku)
        if not new or new.get("discount_percent") != old.get("discount_percent"):
            changed_others.append(other_sku)
    return {
        "activity": latest,
        "config_verified": config_verified,
        "other_skus_unchanged": not changed_others,
        "unexpected_changed_skus": changed_others,
    }


def set_discount(cdp: Cdp, sku: str, percent: int, submit: bool, promotion_id: Optional[str]) -> dict:
    sku = sku.strip()
    if not sku:
        raise RuntimeError("SKU 不能为空")
    if percent < 1 or percent > 99:
        raise RuntimeError("折扣百分比必须为 1 到 99 的整数")

    activity, target = find_unique_target(cdp, sku, promotion_id)
    pid = activity["promotion_id"]
    current = int(target.get("discount_percent"))
    status = activity.get("status")
    if status == "Running" and percent < current:
        raise RuntimeError("运行中的活动不能降低折扣百分比，因为这会提高折后价")
    if percent == current:
        return {
            "ok": True,
            "action": "no_change",
            "sku": sku,
            "promotion_id": pid,
            "activity_title": activity.get("title"),
            "status": status,
            "discount_percent": current,
            "submitted": False,
            "message": "目标折扣与当前配置相同，无需提交",
        }

    plan = {
        "ok": True,
        "action": "set_discount",
        "sku": sku,
        "promotion_id": pid,
        "activity_title": activity.get("title"),
        "status": status,
        "before_percent": current,
        "target_percent": percent,
        "committed_quantity": target.get("committed_quantity"),
        "minimum_discounted_price": target.get("minimum_discounted_price"),
        "submitted": False,
    }
    if not submit:
        plan["dry_run"] = True
        plan["message"] = "仅生成修改计划；加入 --submit 后才会操作 Seller Central"
        return plan

    before = product_map(activity)
    open_detail_and_wait(cdp, pid, sku)
    staged = stage_percent(cdp, sku, percent)
    click_submit(cdp)
    verification = verify_persisted(cdp, pid, sku, percent, before)
    if not verification["config_verified"]:
        raise RuntimeError("已点击提交，但活动接口尚未确认目标折扣已保存")

    # Enrich the verified target once; live Offer price may lag behind saved campaign config.
    verified_activity = verification["activity"]
    verified_target = product_map(verified_activity)[sku]
    enrich_prices([verified_target])
    regular = verified_target.get("regular_price")
    live_discounted = verified_target.get("discounted_price")
    expected = round(float(regular) * (100 - percent) / 100, 2) if regular is not None else None
    sync_pending = bool(expected is not None and live_discounted is not None and abs(expected - live_discounted) > 0.011)

    return {
        **plan,
        "submitted": True,
        "dry_run": False,
        "page_price_preview": staged.get("price_preview"),
        "config_verified": verification["config_verified"],
        "other_skus_unchanged": verification["other_skus_unchanged"],
        "unexpected_changed_skus": verification["unexpected_changed_skus"],
        "validation_has_error": verified_target.get("validation_has_error"),
        "validation_error_count": verified_target.get("validation_error_count"),
        "regular_price": regular,
        "live_discounted_price": live_discounted,
        "expected_discounted_price": expected,
        "live_price_sync_pending": sync_pending,
        "review_status": "submitted_not_yet_proven_approved",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Seller Central Price Discounts query/editor")
    sub = parser.add_subparsers(dest="command")
    query_parser = sub.add_parser("query", help="只读查询活动；默认命令")
    query_parser.add_argument("--promotion-id")
    query_parser.add_argument("--no-price-enrichment", action="store_true")

    set_parser = sub.add_parser("set-discount", help="精确修改单个 SKU 的折扣百分比")
    set_parser.add_argument("--sku", required=True)
    set_parser.add_argument("--percent", required=True, type=int)
    set_parser.add_argument("--promotion-id")
    set_parser.add_argument("--submit", action="store_true", help="实际提交；缺省为只读计划")

    args = parser.parse_args()
    command = args.command or "query"
    cdp = None
    try:
        tab = select_tab()
        cdp = Cdp(tab["webSocketDebuggerUrl"])
        if command == "query":
            result = query(
                cdp,
                promotion_id=getattr(args, "promotion_id", None),
                enrich=not getattr(args, "no_price_enrichment", False),
            )
        else:
            result = set_discount(cdp, args.sku, args.percent, args.submit, args.promotion_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "stage": command, "error": str(exc)[:800]}, ensure_ascii=False, indent=2))
        return 1
    finally:
        if cdp:
            cdp.close()


if __name__ == "__main__":
    raise SystemExit(main())
