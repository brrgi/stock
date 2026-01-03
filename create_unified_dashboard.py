"""
통합 대시보드: 현재 + 백테스트 날짜 선택
"""

import pandas as pd
import os
from datetime import datetime, timedelta
from data_collector import StockDataCollector
from screener_complete import run_complete_screening

print("="*60)
print("  통합 대시보드 생성")
print("  - 현재 시점 진입 신호")
print("  - 백테스트 날짜별 조회 (2025년 금요일)")
print("="*60)

# 1. 현재 시점 스크리닝 실행
print("\n[1단계] 현재 시점 진입 신호 분석 중...")
current_results = run_complete_screening()

# 2. 백테스트 데이터 확인
print("\n[2단계] 백테스트 데이터 확인 중...")
results_dir = 'results'
backtest_csv_files = [f for f in os.listdir(results_dir) if f.startswith('백테스팅결과') and f.endswith('.csv')]

has_backtest = len(backtest_csv_files) > 0
backtest_df = None

if has_backtest:
    latest_backtest = sorted(backtest_csv_files)[-1]
    backtest_path = os.path.join(results_dir, latest_backtest)
    print(f"✅ 백테스트 파일 발견: {latest_backtest}")
    backtest_df = pd.read_csv(backtest_path, encoding='utf-8-sig')
    backtest_df['date'] = pd.to_datetime(backtest_df['date'])
    print(f"   - 날짜: {len(backtest_df['date'].unique())}개")
    print(f"   - 종목: {len(backtest_df['ticker'].unique())}개")
else:
    print("⚠️ 백테스트 데이터 없음 (현재 시점만 표시)")

# 3. 가격 데이터 수집
print("\n[3단계] 가격 데이터 수집 중...")

# 현재 시점 종목들
current_tickers = set(current_results['combined'][:20]['종목코드'].tolist())

# 백테스트 종목들
backtest_tickers = set()
if has_backtest:
    backtest_tickers = set(backtest_df['ticker'].unique())

all_tickers = list(current_tickers | backtest_tickers)
print(f"총 {len(all_tickers)}개 종목 데이터 수집...")

collector = StockDataCollector()
price_data_dict = {}

for i, ticker in enumerate(all_tickers, 1):
    try:
        print(f"  [{i}/{len(all_tickers)}] {ticker}", end='\r')
        start_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
        df = collector.get_stock_price_data(ticker, start_date)
        if df is not None and len(df) > 0:
            price_data_dict[ticker] = df
    except Exception as e:
        continue

print(f"\n✅ {len(price_data_dict)}개 종목 수집 완료")

# 4. 대시보드 생성
print("\n[4단계] 통합 대시보드 생성 중...")

from generate_modern_dashboard_unified import generate_unified_dashboard

output_file = generate_unified_dashboard(
    current_results=current_results,
    backtest_df=backtest_df,
    price_data_dict=price_data_dict,
    output_file='dashboard.html'
)

print(f"\n✅ 대시보드 생성 완료!")
print(f"📂 {os.path.abspath(output_file)}")
print("\n🌐 브라우저에서 여는 중...")

os.system(f'start {output_file}')
