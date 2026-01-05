"""
Send signal summary to Telegram.
Env:
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
"""

import argparse
import json
import os
from datetime import datetime

import requests


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
WEEKLY_DIR = os.path.join(PROJECT_ROOT, "data", "weekly_data")
INTRADAY_DIR = os.path.join(PROJECT_ROOT, "data", "intraday")


def parse_args():
    parser = argparse.ArgumentParser(description="텔레그램 신호 전송")
    parser.add_argument("--source", type=str, default="weekly",
                        help="weekly 또는 intraday")
    parser.add_argument("--limit", type=int, default=20,
                        help="상위 N개만 전송")
    parser.add_argument("--min-rs", type=int, default=0,
                        help="최소 RS 등급")
    parser.add_argument("--only-both", action="store_true",
                        help="Ryan+Minervini 둘 다 신호만")
    return parser.parse_args()


def _load_weekly_latest():
    index_path = os.path.join(WEEKLY_DIR, "index.json")
    if not os.path.exists(index_path):
        raise FileNotFoundError("weekly index.json not found")
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)
    if not index:
        raise ValueError("weekly index.json empty")

    if isinstance(index[0], dict):
        dates = [item.get("date") for item in index if item.get("date")]
    else:
        dates = [d for d in index if d]
    if not dates:
        raise ValueError("no dates in weekly index.json")

    latest_date = sorted(dates, reverse=True)[0]
    data_path = os.path.join(WEEKLY_DIR, f"signals_{latest_date}.json")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"signals file not found: {data_path}")
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def _load_intraday_latest():
    data_path = os.path.join(INTRADAY_DIR, "latest.json")
    if not os.path.exists(data_path):
        raise FileNotFoundError("intraday latest.json not found")
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def _format_message(data, limit, min_rs, only_both):
    date = data.get("date", "")
    time = data.get("time")
    header = f"[{date}]"
    if time:
        header = f"[{date} {time}]"

    signals = data.get("signals", [])
    filtered = []
    for item in signals:
        rs = int(item.get("RS등급") or 0)
        if rs < min_rs:
            continue
        has_ryan = bool(item.get("Ryan_진입신호"))
        has_min = bool(item.get("미너비니_진입신호"))
        if only_both and not (has_ryan and has_min):
            continue
        filtered.append(item)

    filtered.sort(key=lambda x: int(x.get("RS등급") or 0), reverse=True)
    filtered = filtered[:limit] if limit > 0 else filtered

    lines = [f"{header} Ryan+Minervini 상위 신호"]
    if not filtered:
        lines.append("신호 없음")
        return "\n".join(lines)

    for idx, item in enumerate(filtered, start=1):
        name = item.get("종목명") or item.get("종목코드") or "-"
        code = item.get("종목코드") or "-"
        rs = item.get("RS등급") or "-"
        lines.append(f"{idx}) {name}({code}) RS {rs}")
    return "\n".join(lines)


def _send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": message})
    if not resp.ok:
        raise RuntimeError(f"Telegram send failed: {resp.status_code} {resp.text}")


def main():
    args = parse_args()
    source = args.source.lower()
    if source not in {"weekly", "intraday"}:
        raise ValueError("source는 weekly 또는 intraday여야 합니다.")

    data = _load_weekly_latest() if source == "weekly" else _load_intraday_latest()
    message = _format_message(data, args.limit, args.min_rs, args.only_both)
    _send_telegram(message)
    print("텔레그램 전송 완료")


if __name__ == "__main__":
    main()
