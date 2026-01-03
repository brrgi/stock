"""현재 시점의 진입신호로 dashboard.html 생성"""
import sys
import os
# 현재 디렉토리를 최우선으로 import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from generate_modern_dashboard import generate_modern_dashboard
from data_collector import StockDataCollector

# 1. 가장 최근 진입신호 CSV 찾기
results_dir = 'results'
csv_files = [f for f in os.listdir(results_dir) if f.startswith('진입신호_전체_고급') and f.endswith('.csv')]

if not csv_files:
    print("진입신호 CSV 파일을 찾을 수 없습니다.")
    exit(1)

latest_csv = sorted(csv_files)[-1]
csv_path = os.path.join(results_dir, latest_csv)

print(f"CSV: {csv_path}")

# 2. CSV 로드
entry_signals = pd.read_csv(csv_path, encoding='utf-8-sig', dtype={'종목코드': str})
# 종목코드를 6자리로 패딩
entry_signals['종목코드'] = entry_signals['종목코드'].str.zfill(6)

print(f"Signal: {len(entry_signals)} stocks")

# 3. 종목별 가격 데이터 수집
print("\nPrice data...")
tickers = entry_signals['종목코드'].unique()[:20]  # 상위 20개만
collector = StockDataCollector()

price_data_dict = {}
for i, ticker in enumerate(tickers, 1):
    try:
        ticker_str = str(ticker).zfill(6)  # 6자리 문자열로 변환
        print(f"  [{i}/{len(tickers)}] {ticker_str}")
        from datetime import datetime, timedelta
        start_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
        df = collector.get_stock_price_data(ticker_str, start_date)
        if df is not None and len(df) > 0:
            price_data_dict[ticker_str] = df
    except Exception as e:
        print(f"  Failed: {ticker} - {str(e)}")
        continue

print(f"\nCollected: {len(price_data_dict)} stocks")

# 4. 대시보드 생성
print("\nGenerating dashboard...")
output_file = generate_modern_dashboard(entry_signals, price_data_dict, 'dashboard.html')

print(f"\nDone: {os.path.abspath(output_file)}")

# 5. 대시보드 열기
print("\nOpening browser...")
os.system(f'start {output_file}')
