"""trend_template 필드 테스트"""
import pandas as pd
from data_collector import StockDataCollector
from advanced_entry_signals import AdvancedEntryAnalyzer
from datetime import datetime, timedelta

# 종목 선택
ticker = "005930"  # 삼성전자
rs_rating = 85

print(f"\n{'='*60}")
print(f"종목: {ticker}, RS Rating: {rs_rating}")
print(f"{'='*60}\n")

# 데이터 수집
collector = StockDataCollector()
start_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
price_data = collector.get_stock_price_data(ticker, start_date)

if price_data is None:
    print("데이터 수집 실패")
    exit(1)

print(f"데이터 수집 완료: {len(price_data)}일")

# 분석 실행
analyzer = AdvancedEntryAnalyzer()
signal = analyzer.mark_minervini_advanced_signal(price_data, rs_rating)

print(f"\n진입 신호: {signal['entry_signal']}")
print(f"신호 강도: {signal['signal_strength']}")

print(f"\n{'='*60}")
print("Trend Template 개별 체크:")
print(f"{'='*60}")

template = signal['trend_template']
for key, value in template.items():
    status = "✅ PASS" if value else "❌ FAIL"
    print(f"{status}  {key}: {value} (type: {type(value).__name__})")

# 실제 계산값도 출력
current_price = price_data['Close'].iloc[-1]
ma_50 = price_data['Close'].iloc[-50:].mean()
ma_150 = price_data['Close'].iloc[-150:].mean()
ma_200 = price_data['Close'].iloc[-200:].mean()

high_52w = price_data['High'].iloc[-252:].max() if len(price_data) >= 252 else price_data['High'].max()
low_52w = price_data['Low'].iloc[-252:].min() if len(price_data) >= 252 else price_data['Low'].min()

print(f"\n{'='*60}")
print("실제 계산값:")
print(f"{'='*60}")
print(f"현재가: {current_price:,.0f}원")
print(f"MA 50: {ma_50:,.0f}원")
print(f"MA 150: {ma_150:,.0f}원")
print(f"MA 200: {ma_200:,.0f}원")
print(f"52주 최고: {high_52w:,.0f}원")
print(f"52주 최저: {low_52w:,.0f}원")
print(f"RS Rating: {rs_rating}")

# 7번 조건: 52주 최고가 대비
high_distance_pct = ((high_52w - current_price) / high_52w * 100)
print(f"\n[7번] 52주 최고가 대비: -{high_distance_pct:.2f}% (25% 이내면 PASS)")
print(f"   → {high_distance_pct <= 25}")

# 6번 조건: 52주 최저가 대비
low_gain_pct = ((current_price - low_52w) / low_52w * 100) if low_52w > 0 else 0
print(f"[6번] 52주 최저가 대비: +{low_gain_pct:.2f}% (30% 이상이면 PASS)")
print(f"   → {low_gain_pct >= 30}")

# 8번 조건: RS Rating
print(f"[8번] RS Rating: {rs_rating} (70 이상이면 PASS)")
print(f"   → {rs_rating >= 70}")
