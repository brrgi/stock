"""
날짜 선택 가능한 대시보드 생성
2025년 매주 마지막 거래일 기준 진입신호 조회
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime, timedelta
from generate_modern_dashboard import generate_modern_dashboard
from data_collector import StockDataCollector
from advanced_entry_signals import AdvancedEntryAnalyzer
from david_ryan_complete import DavidRyanComplete
from rs_calculator import RSCalculator
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
WEB_DIR = os.path.join(PROJECT_ROOT, "web")


def get_weekly_last_trading_days_2025():
    """2025년 매주 마지막 거래일 반환"""
    # 간단하게 매주 금요일로 시작 (실제로는 거래일 캘린더 필요)
    fridays = []
    current = datetime(2025, 1, 3)  # 2025년 첫 금요일
    end_date = datetime.now()

    while current <= end_date:
        fridays.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=7)

    return fridays


def analyze_stocks_for_date(target_date_str):
    """특정 날짜의 진입신호 분석"""
    print(f"\n{'='*60}")
    print(f"분석 날짜: {target_date_str}")
    print(f"{'='*60}")

    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')

    # 1. 종목 목록 가져오기 (KOSPI + KOSDAQ 상위)
    collector = StockDataCollector()

    # 간단하게 results 디렉토리의 최신 CSV에서 종목 코드 가져오기
    results_dir = 'results'
    csv_files = [f for f in os.listdir(results_dir) if f.startswith('진입신호_전체_고급') and f.endswith('.csv')]

    if not csv_files:
        print("종목 목록 CSV 파일을 찾을 수 없습니다.")
        # 기본 종목 리스트 사용
        tickers = ['005930', '000660', '035720', '051910', '035420']  # 예시
    else:
        latest_csv = sorted(csv_files)[-1]
        csv_path = os.path.join(results_dir, latest_csv)
        df = pd.read_csv(csv_path, encoding='utf-8-sig', dtype={'종목코드': str})
        tickers = df['종목코드'].str.zfill(6).unique()[:30]  # 상위 30개

    print(f"분석 종목 수: {len(tickers)}")

    # 2. 해당 날짜까지의 가격 데이터 수집
    print("\n가격 데이터 수집 중...")
    price_data_dict = {}

    start_date = (target_date - timedelta(days=400)).strftime('%Y-%m-%d')

    for i, ticker in enumerate(tickers, 1):
        try:
            print(f"  [{i}/{len(tickers)}] {ticker}", end='\r')
            df = collector.get_stock_price_data(ticker, start_date, target_date_str)

            if df is not None and len(df) >= 200:
                # 해당 날짜까지만 사용
                df_filtered = df[df.index <= target_date]
                if len(df_filtered) >= 200:
                    price_data_dict[ticker] = df_filtered
        except Exception as e:
            continue

    print(f"\n수집 완료: {len(price_data_dict)}개 종목")

    # 3. RS Rating 계산
    print("\nRS Rating 계산 중...")
    calculator = RSCalculator()
    all_returns = {}

    for ticker, df in price_data_dict.items():
        try:
            recent = df.tail(252)
            if len(recent) >= 60:
                perf_3m = (recent['Close'].iloc[-1] / recent['Close'].iloc[-60] - 1) * 100 if len(recent) >= 60 else 0
                perf_6m = (recent['Close'].iloc[-1] / recent['Close'].iloc[-120] - 1) * 100 if len(recent) >= 120 else 0
                perf_9m = (recent['Close'].iloc[-1] / recent['Close'].iloc[-180] - 1) * 100 if len(recent) >= 180 else 0
                perf_12m = (recent['Close'].iloc[-1] / recent['Close'].iloc[-252] - 1) * 100 if len(recent) >= 252 else 0

                weighted_return = (perf_3m * 0.4) + (perf_6m * 0.2) + (perf_9m * 0.2) + (perf_12m * 0.2)
                all_returns[ticker] = weighted_return
        except:
            continue

    sorted_returns = sorted(all_returns.items(), key=lambda x: x[1], reverse=True)
    rs_ratings = {}
    for idx, (ticker, _) in enumerate(sorted_returns):
        percentile = (1 - idx / len(sorted_returns)) * 100
        rs_ratings[ticker] = int(percentile)

    # 4. 진입신호 분석
    print("\n진입신호 분석 중...")
    entry_signals = []

    for ticker, df in price_data_dict.items():
        try:
            rs_rating = rs_ratings.get(ticker, 50)

            # David Ryan 분석
            ryan_analyzer = DavidRyanComplete()
            ryan_signal = ryan_analyzer.analyze_entry_signal(ticker, df, rs_rating)

            # Minervini 분석
            minervini_analyzer = AdvancedEntryAnalyzer()
            minervini_signal = minervini_analyzer.analyze_entry_signal(ticker, df, rs_rating)

            # 진입신호가 있는 경우만 추가
            if ryan_signal['entry_signal'] or minervini_signal['entry_signal']:
                entry_signals.append({
                    '종목코드': ticker,
                    '종목명': df.attrs.get('name', ticker),
                    'RS등급': rs_rating,
                    '현재가': df['Close'].iloc[-1],
                    'Ryan_진입신호': ryan_signal['entry_signal'],
                    'Ryan_신호강도': ryan_signal['signal_strength'],
                    'Ryan_진입가': ryan_signal['entry_price'],
                    'Ryan_손절가': ryan_signal['stop_loss'],
                    'Ryan_추가매수1': ryan_signal['add_on_prices'][0] if ryan_signal['add_on_prices'] else None,
                    'Ryan_추가매수2': ryan_signal['add_on_prices'][1] if len(ryan_signal['add_on_prices']) > 1 else None,
                    'Ryan_손익비': ryan_signal.get('risk_reward_ratio', 0),
                    'Ryan_근거': ' | '.join(ryan_signal['reasons']),
                    'Ryan_경고': ' | '.join(ryan_signal['warnings']) if ryan_signal['warnings'] else None,
                    '미너비니_진입신호': minervini_signal['entry_signal'],
                    '미너비니_신호강도': minervini_signal['signal_strength'],
                    '미너비니_진입가': minervini_signal['entry_price'],
                    '미너비니_손절가': minervini_signal['stop_loss'],
                    '미너비니_패턴': minervini_signal.get('pattern_type'),
                    '미너비니_근거': ' | '.join(minervini_signal['reasons']),
                    '양쪽_모두_신호': ryan_signal['entry_signal'] and minervini_signal['entry_signal']
                })
        except Exception as e:
            print(f"\n  오류 ({ticker}): {str(e)}")
            continue

    # DataFrame으로 변환
    if not entry_signals:
        print("진입신호가 없습니다.")
        return None, None

    df_signals = pd.DataFrame(entry_signals)
    df_signals = df_signals.sort_values('RS등급', ascending=False)

    print(f"\n발견된 진입신호: {len(df_signals)}개")

    return df_signals, price_data_dict


def main():
    """메인 실행"""
    # 날짜 목록 가져오기
    dates = get_weekly_last_trading_days_2025()

    print(f"사용 가능한 날짜: {len(dates)}개")
    print("날짜 목록:", dates[:5], "...")

    # 가장 최근 날짜로 분석 (테스트)
    target_date = dates[-1]

    # 진입신호 분석
    entry_signals, price_data = analyze_stocks_for_date(target_date)

    if entry_signals is None:
        print("분석 실패")
        return

    # 대시보드 생성
    print("\n대시보드 생성 중...")
    os.makedirs(WEB_DIR, exist_ok=True)
    output_file = generate_modern_dashboard(
        entry_signals.head(20),
        price_data,
        os.path.join(WEB_DIR, 'dashboard_dated.html'),
        title=f"진입신호 - {target_date}"
    )

    print(f"\n완료: {os.path.abspath(output_file)}")
    os.system(f'start {output_file}')


if __name__ == "__main__":
    main()
