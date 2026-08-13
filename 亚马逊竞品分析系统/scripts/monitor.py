#!/usr/bin/env python3
"""Small, secret-safe CLI for the local Amazon Intelligence server."""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


APP_ROOT = Path("/Users/mac/Documents/稳卖Agent 2")
BASE_URL = os.environ.get("AMZ_INTEL_URL", "http://127.0.0.1:8765").rstrip("/")


def request(path, method="GET", payload=None):
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"error": raw or str(exc)}
        raise RuntimeError(detail.get("error") or str(exc)) from exc
    except urllib.error.URLError as exc:
        raise ConnectionError(str(exc.reason)) from exc


def ensure_server():
    try:
        request("/api/health")
        return None
    except (ConnectionError, OSError):
        log_path = Path(os.environ.get("AMZ_INTEL_LOG", "/tmp/amazon-intelligence-skill.log"))
        handle = log_path.open("a", encoding="utf-8")
        process = subprocess.Popen([sys.executable, "run.py"], cwd=APP_ROOT, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
        handle.close()
        for _ in range(30):
            time.sleep(0.2)
            try:
                request("/api/health")
                return process
            except (ConnectionError, OSError):
                continue
        raise RuntimeError(f"无法启动本地服务，日志：{log_path}")


def print_json(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Amazon Intelligence local monitor CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("health")
    create = sub.add_parser("create")
    create.add_argument("--marketplace", required=True)
    create.add_argument("--asin", required=True)
    create.add_argument("--name")
    create.add_argument("--mode", choices=["auto", "real", "mock"], default="auto")

    for name in ("dashboard", "competitors", "keywords", "tasks"):
        command = sub.add_parser(name)
        command.add_argument("--project-id", type=int, required=True)

    refresh = sub.add_parser("refresh-competitors")
    refresh.add_argument("--project-id", type=int, required=True)
    for name in ("snapshot", "history", "changes", "listing-refresh", "keyword-rank", "listing-optimization"):
        command = sub.add_parser(name)
        command.add_argument("--project-id", type=int, required=True)

    task = sub.add_parser("task")
    task.add_argument("--task-id", type=int, required=True)
    wait = sub.add_parser("wait")
    wait.add_argument("--task-id", type=int, required=True)
    wait.add_argument("--timeout", type=int, default=900)

    args = parser.parse_args()
    ensure_server()

    if args.command == "health":
        print_json(request("/api/health"))
        return
    if args.command == "create":
        result = request("/api/projects", "POST", {"name": args.name or "", "marketplace": args.marketplace.upper(), "asin": args.asin.upper(), "mode": args.mode})
        print_json(result)
        return
    if args.command in {"dashboard", "competitors", "keywords", "tasks"}:
        route = {"dashboard": "dashboard", "competitors": "competitors", "keywords": "keywords", "tasks": "tasks"}[args.command]
        print_json(request(f"/api/projects/{args.project_id}/{route}"))
        return
    if args.command == "task":
        print_json(request(f"/api/tasks/{args.task_id}"))
        return
    if args.command == "wait":
        deadline = time.time() + args.timeout
        while True:
            result = request(f"/api/tasks/{args.task_id}")
            if result.get("status") not in {"queued", "running"} or time.time() >= deadline:
                print_json(result)
                return
            time.sleep(2)

    skill = {
        "refresh-competitors": "competitor_discovery",
        "snapshot": "competitor_snapshot",
        "history": "competitor_history_refresh",
        "changes": "competitor_change_analysis",
        "listing-refresh": "competitor_listing_refresh",
        "keyword-rank": "keyword_rank_monitor",
        "listing-optimization": "weekly_listing_optimization",
    }[args.command]
    result = request(f"/api/projects/{args.project_id}/run/{skill}", "POST")
    print_json(result)


if __name__ == "__main__":
    main()
