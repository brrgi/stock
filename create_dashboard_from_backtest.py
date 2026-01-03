"""백테스트 CSV로부터 날짜별 대시보드 생성"""
import pandas as pd
import os
from generate_dashboard_with_dates import generate_dashboard_with_backtest_dates
from data_collector import StockDataCollector

# 1. 백테스트 CSV 찾기
results_dir = 'results'
csv_files = [f for f in os.listdir(results_dir) if f.startswith('백테스팅결과') and f.endswith('.csv')]

if not csv_files:
    print("백테스트 CSV 파일을 찾을 수 없습니다. 먼저 backtest_weekly.py를 실행하세요.")
    exit(1)

latest_csv = sorted(csv_files)[-1]
csv_path = os.path.join(results_dir, latest_csv)

print(f"📂 CSV 로드: {csv_path}")

# 2. CSV 로드
backtest_df = pd.read_csv(csv_path, encoding='utf-8-sig')
backtest_df['date'] = pd.to_datetime(backtest_df['date'])

print(f"✅ 데이터 포인트: {len(backtest_df)}개")
print(f"✅ 고유 날짜: {len(backtest_df['date'].unique())}개")
print(f"✅ 고유 종목: {len(backtest_df['ticker'].unique())}개")

# 3. 종목별 가격 데이터 수집
print("\n📊 종목별 가격 데이터 수집 중...")
tickers = backtest_df['ticker'].unique()
collector = StockDataCollector()

price_data_dict = {}
for i, ticker in enumerate(tickers, 1):
    try:
        print(f"  [{i}/{len(tickers)}] {ticker} 데이터 수집 중...")
        start_date = (backtest_df['date'].min() - pd.Timedelta(days=300)).strftime('%Y-%m-%d')
        df = collector.get_stock_price_data(ticker, start_date)
        if df is not None and len(df) > 0:
            price_data_dict[ticker] = df
    except Exception as e:
        print(f"  ⚠️ {ticker} 수집 실패: {str(e)}")
        continue

print(f"\n✅ {len(price_data_dict)}개 종목 데이터 수집 완료")

# 4. 대시보드 생성
print("\n🎨 대시보드 생성 중...")
output_file = generate_dashboard_with_backtest_dates(backtest_df, price_data_dict, 'dashboard.html')

print(f"\n✅ 대시보드 생성 완료!")
print(f"📂 파일 위치: {os.path.abspath(output_file)}")

# 5. 대시보드 열기
import webbrowser
webbrowser.open(os.path.abspath(output_file))
print("\n🌐 브라우저에서 대시보드를 열었습니다.")
