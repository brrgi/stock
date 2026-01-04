"""
현재 진입신호 CSV를 JSON으로 변환 (간단 버전)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import json
import numpy as np
from datetime import datetime, timedelta
from data_collector import StockDataCollector


class NumpyEncoder(json.JSONEncoder):
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


# 1. CSV 로드
results_dir = 'results'
csv_files = [f for f in os.listdir(results_dir) if f.startswith('진입신호_전체_고급') and f.endswith('.csv')]

latest_csv = sorted(csv_files)[-1]
csv_path = os.path.join(results_dir, latest_csv)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "weekly_data")

entry_signals = pd.read_csv(csv_path, encoding='utf-8-sig', dtype={'종목코드': str})
entry_signals['종목코드'] = entry_signals['종목코드'].str.zfill(6)

print(f"CSV: {csv_path}")
print(f"종목: {len(entry_signals)}")

# 2. 가격 데이터
tickers = entry_signals['종목코드'].unique()[:20]
collector = StockDataCollector()
price_data_dict = {}

print("\n가격 데이터...")
for i, ticker in enumerate(tickers, 1):
    try:
        ticker_str = str(ticker).zfill(6)
        print(f"  [{i}/{len(tickers)}] {ticker_str}", end='\r')
        start_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
        df = collector.get_stock_price_data(ticker_str, start_date)
        if df is not None and len(df) > 0:
            price_data_dict[ticker_str] = df
    except:
        continue

print(f"\n수집: {len(price_data_dict)}개")

# 3. Signals 리스트 생성
signals_list = []
for _, row in entry_signals.head(20).iterrows():
    ticker = str(row['종목코드']).zfill(6)
    signals_list.append({
        '종목코드': ticker,
        '종목명': row['종목명'],
        'RS등급': int(row['RS등급']),
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
        'trend_template': {
            'above_150_200': True,
            'ma150_above_200': True,
            'ma200_rising': True,
            'ma50_above_150_200': True,
            'above_50': True,
            'above_52w_low': bool(row['미너비니_신호강도'] >= 70),
            'near_52w_high': True,
            'rs_strong': bool(row['RS등급'] >= 70)
        }
    })

# 4. 차트 데이터
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

print(f"\nJSON 저장: {filename}")
print(f"진입신호: {len(signals_list)}개")
