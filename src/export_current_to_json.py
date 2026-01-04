"""
현재 진입신호를 JSON 형식으로 weekly_data에 저장
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import json
import numpy as np
from datetime import datetime
from generate_modern_dashboard import NumpyEncoder
from data_collector import StockDataCollector
from advanced_entry_signals import AdvancedEntryAnalyzer
from david_ryan_complete import DavidRyanComplete

# 1. 최신 CSV 로드
results_dir = 'results'
csv_files = [f for f in os.listdir(results_dir) if f.startswith('진입신호_전체_고급') and f.endswith('.csv')]

if not csv_files:
    print("CSV 파일을 찾을 수 없습니다.")
    exit(1)

latest_csv = sorted(csv_files)[-1]
csv_path = os.path.join(results_dir, latest_csv)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "weekly_data")

entry_signals = pd.read_csv(csv_path, encoding='utf-8-sig', dtype={'종목코드': str})
entry_signals['종목코드'] = entry_signals['종목코드'].str.zfill(6)

print(f"CSV 로드: {csv_path}")
print(f"종목 수: {len(entry_signals)}")

# 2. 가격 데이터 수집
tickers = entry_signals['종목코드'].unique()[:20]
collector = StockDataCollector()
price_data_dict = {}

print("\n가격 데이터 수집 중...")
for i, ticker in enumerate(tickers, 1):
    try:
        ticker_str = str(ticker).zfill(6)
        print(f"  [{i}/{len(tickers)}] {ticker_str}", end='\r')
        from datetime import timedelta
        start_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
        df = collector.get_stock_price_data(ticker_str, start_date)
        if df is not None and len(df) > 0:
            price_data_dict[ticker_str] = df
    except Exception as e:
        continue

print(f"\n수집 완료: {len(price_data_dict)}개")

# 3. 상세 분석 데이터 추가
print("\n상세 분석 중...")
ryan_analyzer = DavidRyanComplete()
minervini_analyzer = AdvancedEntryAnalyzer()

signals_list = []
for _, row in entry_signals.head(20).iterrows():
    ticker = str(row['종목코드']).zfill(6)

    if ticker not in price_data_dict:
        continue

    df = price_data_dict[ticker]
    rs_rating = row['RS등급']

    try:
        # Ryan 분석
        ryan = ryan_analyzer.analyze_entry_signal(ticker, df, rs_rating)

        # Minervini 분석
        minervini = minervini_analyzer.analyze_entry_signal(ticker, df, rs_rating)

        signal_dict = {
            '종목코드': ticker,
            '종목명': row['종목명'],
            'RS등급': int(rs_rating),
            '현재가': float(row['현재가']),
            'Ryan_진입신호': bool(row['Ryan_진입신호']),
            'Ryan_신호강도': int(row['Ryan_신호강도']),
            'Ryan_진입가': float(row['Ryan_진입가']),
            'Ryan_손절가': float(row['Ryan_손절가']),
            'Ryan_추가매수1': float(row['Ryan_추가매수1']) if pd.notna(row.get('Ryan_추가매수1')) else None,
            'Ryan_추가매수2': float(row['Ryan_추가매수2']) if pd.notna(row.get('Ryan_추가매수2')) else None,
            'Ryan_손익비': float(row['Ryan_손익비']),
            'Ryan_근거': str(row['Ryan_근거']),
            'Ryan_경고': str(row['Ryan_경고']) if pd.notna(row.get('Ryan_경고')) else None,
            '미너비니_진입신호': bool(row['미너비니_진입신호']),
            '미너비니_신호강도': int(row['미너비니_신호강도']),
            '미너비니_진입가': float(row['미너비니_진입가']),
            '미너비니_손절가': float(row['미너비니_손절가']),
            '미너비니_패턴': row.get('미너비니_패턴'),
            '미너비니_근거': str(row['미너비니_근거']),
            '양쪽_모두_신호': bool(row['양쪽_모두_신호']),
            'trend_template': minervini.get('trend_template', {})
        }
        signals_list.append(signal_dict)
    except Exception as e:
        print(f"\n오류 ({ticker}): {str(e)}")
        continue

print(f"분석 완료: {len(signals_list)}개")

# 4. 차트 데이터 생성
chart_data = {}
for ticker, df in price_data_dict.items():
    chart_data[ticker] = {
        'dates': df.index.strftime('%Y-%m-%d').tolist(),
        'open': df['Open'].tolist(),
        'high': df['High'].tolist(),
        'low': df['Low'].tolist(),
        'close': df['Close'].tolist(),
        'volume': df['Volume'].tolist()
    }

# 5. JSON 저장
os.makedirs(DATA_DIR, exist_ok=True)
today = datetime.now().strftime('%Y-%m-%d')

output = {
    'date': today,
    'signals': signals_list,
    'chart_data': chart_data
}

filename = os.path.join(DATA_DIR, f'signals_{today}.json')
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(output, f, cls=NumpyEncoder, ensure_ascii=False, indent=2)

print(f"\nJSON 저장 완료: {filename}")
print(f"진입신호: {len(signals_list)}개")
