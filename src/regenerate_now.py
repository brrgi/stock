"""대시보드 강제 재생성 - 디버깅 출력 포함"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("대시보드 재생성 시작")
print("=" * 60)

import pandas as pd
from generate_modern_dashboard import generate_modern_dashboard
from data_collector import StockDataCollector
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
WEB_DIR = os.path.join(PROJECT_ROOT, "web")

# 1. CSV 로드
results_dir = os.path.join(PROJECT_ROOT, 'results')
csv_files = [f for f in os.listdir(results_dir) if f.startswith('진입신호_전체_고급') and f.endswith('.csv')]

if not csv_files:
    print("❌ 진입신호 CSV 파일을 찾을 수 없습니다.")
    sys.exit(1)

latest_csv = sorted(csv_files)[-1]
csv_path = os.path.join(results_dir, latest_csv)

print(f"\n📂 CSV 로드: {latest_csv}")
entry_signals = pd.read_csv(csv_path, encoding='utf-8-sig')
print(f"✅ 진입신호: {len(entry_signals)}개 종목")

# 2. 가격 데이터 수집
print(f"\n📊 가격 데이터 수집 중...")
tickers = entry_signals['종목코드'].unique()[:20]
collector = StockDataCollector()

price_data_dict = {}
for i, ticker in enumerate(tickers, 1):
    try:
        print(f"  [{i}/{len(tickers)}] {ticker}", end='\r')
        start_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
        df = collector.get_stock_price_data(ticker, start_date)
        if df is not None and len(df) > 0:
            price_data_dict[ticker] = df
    except Exception as e:
        print(f"\n  ⚠️ {ticker} 실패: {str(e)}")
        continue

print(f"\n✅ {len(price_data_dict)}개 종목 데이터 수집 완료")

# 3. 대시보드 생성
print(f"\n🎨 대시보드 생성 중...")
os.makedirs(WEB_DIR, exist_ok=True)
output_file = generate_modern_dashboard(
    entry_signals,
    price_data_dict,
    os.path.join(WEB_DIR, 'dashboard.html')
)

print(f"\n✅ 대시보드 생성 완료!")
print(f"📂 파일: {os.path.abspath(output_file)}")

# 4. 검증
print(f"\n🔍 trend_template 검증 중...")
with open(output_file, 'r', encoding='utf-8') as f:
    content = f.read()

import re
match = re.search(r'"trend_template":\s*\{[^}]+\}', content)
if match:
    print("trend_template 샘플:")
    print(match.group(0)[:200] + "...")
else:
    print("⚠️ trend_template을 찾을 수 없습니다.")

# 5. 브라우저로 열기
print(f"\n🌐 브라우저에서 대시보드 여는 중...")
os.system(f'start {output_file}')

print(f"\n{'=' * 60}")
print("완료!")
print(f"{'=' * 60}")
