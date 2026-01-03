"""
최근 N주 매주 마지막 거래일 데이터 생성
각 날짜별 진입신호를 JSON 파일로 저장
"""

import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime, timedelta
from data_collector import StockDataCollector
from advanced_entry_signals import AdvancedEntryAnalyzer
from david_ryan_complete import DavidRyanComplete
from rs_calculator import RSCalculator
import json
import numpy as np
import glob
import csv


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types"""
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


def get_recent_weekly_fridays(weeks):
    """최근 N주 금요일 (오늘 기준 최소 1주 전까지)"""
    end_date = datetime.now() - timedelta(days=7)
    offset = (end_date.weekday() - 4) % 7  # Friday=4
    last_friday = end_date - timedelta(days=offset)
    fridays = [last_friday - timedelta(days=7 * i) for i in range(weeks)]
    return sorted(fridays)


def analyze_date(target_date, price_data_dict, debug=False, debug_sample=10):
    """특정 날짜 분석 (price_data_dict: {ticker: full_df})"""
    print(f"\n분석 날짜: {target_date.strftime('%Y-%m-%d')}")

    start_date = (target_date - timedelta(days=400)).strftime('%Y-%m-%d')
    end_date = target_date.strftime('%Y-%m-%d')
    print(f"  데이터 범위: {start_date} ~ {end_date}")

    # RS Rating 계산
    all_returns = {}
    filtered_data = {}
    for ticker, df in price_data_dict.items():
        try:
            df_filtered = df[df.index <= target_date]
            if len(df_filtered) < 200:
                continue
            filtered_data[ticker] = df_filtered
            recent = df_filtered.tail(252)
            if len(recent) >= 60:
                p3 = (recent['Close'].iloc[-1] / recent['Close'].iloc[-60] - 1) * 100 if len(recent) >= 60 else 0
                p6 = (recent['Close'].iloc[-1] / recent['Close'].iloc[-120] - 1) * 100 if len(recent) >= 120 else 0
                p9 = (recent['Close'].iloc[-1] / recent['Close'].iloc[-180] - 1) * 100 if len(recent) >= 180 else 0
                p12 = (recent['Close'].iloc[-1] / recent['Close'].iloc[-252] - 1) * 100 if len(recent) >= 252 else 0
                all_returns[ticker] = (p3 * 0.4) + (p6 * 0.2) + (p9 * 0.2) + (p12 * 0.2)
        except:
            continue

    sorted_returns = sorted(all_returns.items(), key=lambda x: x[1], reverse=True)
    rs_ratings = {ticker: int((1 - idx / len(sorted_returns)) * 100) for idx, (ticker, _) in enumerate(sorted_returns)}

    # 진입신호 분석
    ryan_analyzer = DavidRyanComplete()
    minervini_analyzer = AdvancedEntryAnalyzer()
    entry_signals = []
    debug_rows = []

    for ticker, df in filtered_data.items():
        try:
            rs = rs_ratings.get(ticker, 50)
            ryan = ryan_analyzer.david_ryan_complete_signal(df, rs)
            minervini = minervini_analyzer.mark_minervini_advanced_signal(df, rs)

            if debug:
                debug_rows.append({
                    'ticker': ticker,
                    'name': df.attrs.get('name', ticker),
                    'rs': rs,
                    'ryan_signal': ryan.get('entry_signal'),
                    'ryan_strength': ryan.get('signal_strength'),
                    'ryan_reasons': ryan.get('reasons', []),
                    'min_signal': minervini.get('entry_signal'),
                    'min_strength': minervini.get('signal_strength'),
                    'min_reasons': minervini.get('reasons', []),
                })

            if ryan['entry_signal'] or minervini['entry_signal']:
                entry_signals.append({
                    '종목코드': ticker,
                    '종목명': df.attrs.get('name', ticker),
                    'RS등급': rs,
                    '현재가': float(df['Close'].iloc[-1]),
                    'Ryan_진입신호': ryan['entry_signal'],
                    'Ryan_신호강도': ryan['signal_strength'],
                    'Ryan_진입가': float(ryan['entry_price']),
                    'Ryan_손절가': float(ryan['stop_loss']),
                    'Ryan_추가매수1': float(ryan['add_on_prices'][0]) if ryan['add_on_prices'] else None,
                    'Ryan_추가매수2': float(ryan['add_on_prices'][1]) if len(ryan['add_on_prices']) > 1 else None,
                    'Ryan_손익비': float(ryan.get('risk_reward_ratio', 0)),
                    'Ryan_근거': ' | '.join(ryan['reasons']),
                    'Ryan_경고': ' | '.join(ryan['warnings']) if ryan['warnings'] else None,
                    'ryan_checks': {
                        'rs_check': bool(ryan.get('rs_check')),
                        'ma_alignment': bool(ryan.get('ma_alignment')),
                        'year_position_check': bool(ryan.get('year_position_check')),
                        'vcp_detected': bool(ryan.get('vcp_detected')),
                        'vdu_detected': bool(ryan.get('vdu_detected')),
                        'pivot_breakout': bool(ryan.get('pivot_breakout')),
                        'volume_surge': bool(ryan.get('volume_surge'))
                    },
                    '미너비니_진입신호': minervini['entry_signal'],
                    '미너비니_신호강도': minervini['signal_strength'],
                    '미너비니_진입가': float(minervini['entry_price']),
                    '미너비니_손절가': float(minervini['stop_loss']),
                    '미너비니_패턴': minervini.get('pattern_type'),
                    '미너비니_근거': ' | '.join(minervini['reasons']),
                    'minervini_checks': minervini.get('minervini_checks', {}),
                    '양쪽_모두_신호': ryan['entry_signal'] and minervini['entry_signal'],
                    'trend_template': minervini.get('trend_template', {})
                })
        except Exception as e:
            continue

    print(f"  진입신호: {len(entry_signals)}개")
    if debug:
        print(f"  [디버그] filtered_data: {len(filtered_data)} / rs_ratings: {len(rs_ratings)}")

    def _safe_reason_list(reasons):
        safe = []
        for reason in reasons:
            if reason is None:
                continue
            safe.append(reason.encode('ascii', 'ignore').decode('ascii'))
        return safe

    if debug:
        if not debug_rows:
            # 강제 샘플 출력: 상위 2개 종목만 직접 점검
            forced = list(filtered_data.items())[:2]
            print(f"  [디버그] 강제 샘플 {len(forced)}개 종목")
            for ticker, df in forced:
                rs = rs_ratings.get(ticker, 50)
                ryan = ryan_analyzer.david_ryan_complete_signal(df, rs)
                minervini = minervini_analyzer.mark_minervini_advanced_signal(df, rs)
                ryan_reasons = _safe_reason_list(ryan.get('reasons', [])[:3])
                min_reasons = _safe_reason_list(minervini.get('reasons', [])[:3])
                print(f"    - {ticker} {df.attrs.get('name', ticker)} RS {rs}")
                print(f"      Ryan: {ryan.get('entry_signal')} / {ryan.get('signal_strength')} / {ryan_reasons}")
                print(f"      Min:  {minervini.get('entry_signal')} / {minervini.get('signal_strength')} / {min_reasons}")
        else:
            debug_rows.sort(key=lambda x: x['rs'], reverse=True)
            sample = min(debug_sample, len(debug_rows))
            print(f"  [디버그] 샘플 {sample}개 종목")
            for row in debug_rows[:sample]:
                ryan_reasons = _safe_reason_list(row['ryan_reasons'][:3])
                min_reasons = _safe_reason_list(row['min_reasons'][:3])
                print(f"    - {row['ticker']} {row['name']} RS {row['rs']}")
                print(f"      Ryan: {row['ryan_signal']} / {row['ryan_strength']} / {ryan_reasons}")
                print(f"      Min:  {row['min_signal']} / {row['min_strength']} / {min_reasons}")

    return entry_signals, filtered_data


def parse_args():
    parser = argparse.ArgumentParser(description="주간 진입신호 데이터 생성")
    parser.add_argument("--weeks", type=str, default="12",
                        help="생성할 최근 주 수 (숫자 또는 all)")
    parser.add_argument("--debug-date", type=str, default="",
                        help="디버그할 날짜 (YYYY-MM-DD)")
    parser.add_argument("--debug-sample", type=int, default=10,
                        help="디버그 출력 샘플 종목 수")
    return parser.parse_args()


def load_name_overrides():
    """results CSV에서 종목명 보정 맵 로드 (있으면 우선 적용)"""
    overrides = {}
    for path in glob.glob(os.path.join('results', '*.csv')):
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    continue
                if '종목코드' not in reader.fieldnames or '종목명' not in reader.fieldnames:
                    continue
                for row in reader:
                    code = (row.get('종목코드') or '').strip()
                    name = (row.get('종목명') or '').strip()
                    if not code or not name:
                        continue
                    if code.isdigit() and len(code) < 6:
                        code = code.zfill(6)
                    if code not in overrides:
                        overrides[code] = name
        except Exception:
            continue
    return overrides


def main():
    """메인"""
    args = parse_args()
    name_overrides = load_name_overrides()
    # 전체 종목 리스트 가져오기 (코스피+코스닥)
    collector = StockDataCollector()
    stock_list = collector.get_stock_list('ALL')
    tradable = collector.filter_tradable_stocks(stock_list)
    top_n = 600
    tradable = tradable.sort_values('Marcap', ascending=False).head(top_n)
    tradable['Code'] = tradable['Code'].astype(str).str.zfill(6)
    tickers = tradable['Code'].tolist()
    name_map = dict(zip(tradable['Code'], tradable.get('Name', tradable['Code'])))
    if name_overrides:
        name_map.update(name_overrides)
    print(f"분석 대상 종목 수: {len(tickers)}개 (시총 상위 {top_n})")

    # 각 날짜별 데이터 생성
    weeks_arg = str(args.weeks).strip().lower()
    if weeks_arg == "all":
        weeks_count = 52
    else:
        try:
            weeks_count = max(1, int(weeks_arg))
        except ValueError:
            weeks_count = 12

    dates = get_recent_weekly_fridays(weeks_count)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    debug_date = None
    if args.debug_date:
        try:
            debug_date = datetime.strptime(args.debug_date, "%Y-%m-%d")
            if debug_date not in dates:
                dates.append(debug_date)
                dates = sorted(dates)
        except ValueError:
            print("debug-date 형식 오류 (YYYY-MM-DD). 무시합니다.")
    if all(date.date() != today.date() for date in dates):
        dates.append(today)
        dates = sorted(dates)
    print(f"총 {len(dates)}개 날짜")
    target_dates = dates

    # 데이터 저장 디렉토리
    os.makedirs('weekly_data', exist_ok=True)

    # 가격 데이터 사전 수집 (전체 기간 1회)
    earliest = min(dates) - timedelta(days=400)
    latest = datetime.now()
    start_str = earliest.strftime('%Y-%m-%d')
    end_str = latest.strftime('%Y-%m-%d')

    print(f"\n[사전 수집] 전체 종목 가격 데이터")
    print(f"[기간] {start_str} ~ {end_str}")
    price_data_dict = {}
    total_tickers = len(tickers)
    for i, ticker in enumerate(tickers, 1):
        try:
            pct = (i / total_tickers) * 100
            print(f"  [{i}/{total_tickers}] {ticker} ({pct:.1f}%)", end='\r')
            df = collector.get_stock_price_data(ticker, start_str, end_str)
            if df is not None and len(df) >= 200:
                df.attrs['name'] = name_map.get(ticker, ticker)
                price_data_dict[ticker] = df
        except:
            continue

    print(f"\n[사전 수집 완료] {len(price_data_dict)}개 종목")

    latest_prices = {}
    for ticker, df in price_data_dict.items():
        try:
            latest_prices[ticker] = float(df['Close'].iloc[-1])
        except Exception:
            continue

    latest_path = os.path.join('weekly_data', 'latest_prices.json')
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(latest_prices, f, ensure_ascii=False, indent=2)

    generated_dates = []
    generated_index = []
    total_dates = len(target_dates)
    for idx, date in enumerate(target_dates, 1):
        pct_dates = (idx / total_dates) * 100
        date_str = date.strftime('%Y-%m-%d')
        is_debug = debug_date is not None and date.date() == debug_date.date()
        print(f"\n[진행] 날짜 분석 {idx}/{total_dates} ({pct_dates:.1f}%)")
        signals, price_data = analyze_date(
            date,
            price_data_dict,
            debug=is_debug,
            debug_sample=args.debug_sample
        )

        # JSON 저장
        signal_tickers = []
        for row in signals:
            code = str(row.get('종목코드', '')).zfill(6)
            if code and code not in signal_tickers:
                signal_tickers.append(code)

        chart_payload = {}
        for ticker in signal_tickers:
            df = price_data_dict.get(ticker)
            if df is None:
                continue
            chart_payload[ticker] = {
                'dates': df.index.strftime('%Y-%m-%d').tolist(),
                'open': df['Open'].tolist(),
                'high': df['High'].tolist(),
                'low': df['Low'].tolist(),
                'close': df['Close'].tolist(),
                'volume': df['Volume'].tolist()
            }

        output = {
            'date': date_str,
            'signals': signals,
            'chart_data': chart_payload
        }

        filename = f'weekly_data/signals_{date_str}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, cls=NumpyEncoder, ensure_ascii=False, indent=2)

        print(f"  저장: {filename}")
        generated_dates.append(date_str)
        generated_index.append({"date": date_str, "signals": len(signals)})

    # 날짜 인덱스 저장
    index_path = os.path.join('weekly_data', 'index.json')
    index_payload = sorted(generated_index, key=lambda item: item["date"], reverse=True)
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_payload, f, ensure_ascii=False, indent=2)

    print("\n완료!")


if __name__ == "__main__":
    main()
