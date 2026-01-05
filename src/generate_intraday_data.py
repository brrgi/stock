"""
Intraday snapshot generator (approximate).
Uses free Naver market summary prices (delayed/unstable) and daily history.
"""

import argparse
import json
import os
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from data_collector import StockDataCollector
from generate_weekly_data import analyze_date


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
INTRADAY_DIR = os.path.join(PROJECT_ROOT, "data", "intraday")


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder for numpy types."""
    def default(self, obj):
        if isinstance(obj, (np.bool_, np.bool8)):
            return bool(obj)
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if pd.isna(obj):
            return None
        return super().default(obj)


def parse_args():
    parser = argparse.ArgumentParser(description="장중(무료) 스냅샷 신호 생성")
    parser.add_argument("--market", type=str, default="ALL",
                        help="시장: ALL/KOSPI/KOSDAQ")
    parser.add_argument("--limit", type=int, default=200,
                        help="상위 N 종목만 처리 (시가총액 기준, 0이면 전체)")
    parser.add_argument("--pages", type=int, default=25,
                        help="네이버 시세 페이지 수 (시장당)")
    parser.add_argument("--delay", type=float, default=0.05,
                        help="종목별 데이터 요청 지연(초)")
    return parser.parse_args()


def _coerce_price(value):
    try:
        return float(value)
    except Exception:
        return None


def _append_intraday_price(df, current_price, target_date):
    if df is None or len(df) == 0 or current_price is None:
        return df

    df = df.copy()
    target_day = pd.Timestamp(target_date.date())
    if df.index[-1].date() != target_day.date():
        new_row = pd.DataFrame(
            {
                "Open": current_price,
                "High": current_price,
                "Low": current_price,
                "Close": current_price,
                "Volume": 0,
            },
            index=[target_day],
        )
        df = pd.concat([df, new_row])
    else:
        last_idx = df.index[-1]
        df.loc[last_idx, "Close"] = current_price
        if "High" in df.columns:
            df.loc[last_idx, "High"] = max(float(df.loc[last_idx, "High"]), current_price)
        if "Low" in df.columns:
            df.loc[last_idx, "Low"] = min(float(df.loc[last_idx, "Low"]), current_price)
    return df


def main():
    args = parse_args()
    market = args.market.upper()
    if market not in {"ALL", "KOSPI", "KOSDAQ"}:
        raise ValueError("market은 ALL/KOSPI/KOSDAQ만 지원합니다.")

    collector = StockDataCollector()
    stock_list = collector.get_stock_list(market)
    tradable = collector.filter_tradable_stocks(stock_list)
    tradable = tradable.sort_values("Marcap", ascending=False)
    if args.limit > 0:
        tradable = tradable.head(args.limit)

    print(f"[장중] 대상 종목 수: {len(tradable)}")

    snapshot = collector.get_intraday_price_snapshot(market, pages=args.pages)
    price_map = {
        row["Code"]: _coerce_price(row["Close"])
        for _, row in snapshot.iterrows()
    }

    target_date = datetime.now()
    start_date = (target_date - timedelta(days=420)).strftime("%Y-%m-%d")

    price_data_dict = {}
    for idx, row in tradable.iterrows():
        ticker = row["Code"]
        name = row["Name"]
        current_price = price_map.get(ticker)
        if current_price is None:
            continue

        df = collector.get_stock_price_data(ticker, start_date)
        if df is None or len(df) < 200:
            continue

        df.attrs["name"] = name
        df = df[df.index <= target_date]
        df = _append_intraday_price(df, current_price, target_date)
        price_data_dict[ticker] = df

        if (idx + 1) % 50 == 0:
            print(f"[장중] 진행 {idx + 1}/{len(tradable)}")
        if args.delay > 0:
            time.sleep(args.delay)

    if not price_data_dict:
        print("[장중] 유효한 데이터가 없습니다.")
        return

    entry_signals, _ = analyze_date(target_date, price_data_dict)
    payload = {
        "date": target_date.strftime("%Y-%m-%d"),
        "time": target_date.strftime("%H:%M"),
        "source": "intraday",
        "signals": entry_signals,
        "note": "Intraday snapshot (free sources, delayed/unstable).",
    }

    os.makedirs(INTRADAY_DIR, exist_ok=True)
    latest_path = os.path.join(INTRADAY_DIR, "latest.json")
    summary_path = os.path.join(INTRADAY_DIR, "summary.json")

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)

    summary = {
        "date": payload["date"],
        "time": payload["time"],
        "signals": len(payload.get("signals", [])),
        "source": payload["source"],
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"[장중] 완료: {latest_path}")


if __name__ == "__main__":
    main()
