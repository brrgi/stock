"""
전체 분석 실행 - David Ryan + Mark Minervini + 웹 대시보드
"""

import sys
import os
# 현재 디렉토리를 최우선으로 import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime
import webbrowser

from data_collector import StockDataCollector
from rs_calculator import RSCalculator
from advanced_entry_signals import AdvancedEntryAnalyzer
from david_ryan_complete import DavidRyanComplete
from generate_modern_dashboard import generate_modern_dashboard
from convert_to_korean import convert_entry_signals_to_korean

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
WEB_DIR = os.path.join(PROJECT_ROOT, "web")


def save_results(data, filename, folder=None):
    """결과 저장"""
    if folder is None:
        folder = os.path.join(PROJECT_ROOT, 'results')
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    csv_path = os.path.join(folder, f'{filename}_{timestamp}.csv')
    data.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"[저장] {csv_path}")

    excel_path = os.path.join(folder, f'{filename}_{timestamp}.xlsx')
    data.to_excel(excel_path, index=False, engine='openpyxl')
    print(f"[저장] {excel_path}")

    return csv_path, excel_path


def main():
    """메인 실행"""
    print("="*100)
    print("          주식 진입 신호 종합 분석 시스템")
    print("          David Ryan + Mark Minervini + Web Dashboard")
    print("="*100)

    # 1. 데이터 수집
    print("\n[1단계] 데이터 수집")
    print("-" * 100)

    collector = StockDataCollector()
    stock_list = collector.get_stock_list('ALL')
    tradable_stocks = collector.filter_tradable_stocks(
        stock_list,
        min_price=5000,
        min_market_cap=1000
    )

    # 시가총액 상위 200개
    tradable_stocks = tradable_stocks.nlargest(200, 'Marcap')
    print(f"\n시가총액 상위 {len(tradable_stocks)}개 종목 분석")

    # 가격 데이터 수집
    price_data = collector.get_bulk_price_data(tradable_stocks, period_days=252, delay=0.1)

    # 2. RS Rating 계산
    print("\n[2단계] RS Rating 계산")
    print("-" * 100)

    calculator = RSCalculator()
    stocks_with_rs = calculator.calculate_all_rs_ratings(price_data, tradable_stocks)

    # RS 70 이상만
    high_rs_stocks = stocks_with_rs[stocks_with_rs['RS_Rating'] >= 70].copy()
    print(f"\nRS Rating 70 이상: {len(high_rs_stocks)}개")

    # 3. 진입 신호 분석
    print("\n[3단계] 고급 진입 신호 분석 (David Ryan Complete + Mark Minervini)")
    print("-" * 100)

    ryan_analyzer = DavidRyanComplete()
    minervini_analyzer = AdvancedEntryAnalyzer()

    results = []

    for idx, row in high_rs_stocks.iterrows():
        ticker = row['Code']
        if ticker not in price_data:
            continue

        price_df = price_data[ticker]
        rs_rating = row['RS_Rating']

        # David Ryan 완전 분석
        ryan_signal = ryan_analyzer.david_ryan_complete_signal(price_df, rs_rating)

        # Mark Minervini 고급 분석
        minervini_signal = minervini_analyzer.mark_minervini_advanced_signal(price_df, rs_rating)

        # 둘 중 하나라도 신호면 포함
        if ryan_signal['entry_signal'] or minervini_signal['entry_signal']:
            # 추가매수 가격 추출
            add_on_prices = ryan_signal.get('add_on_prices', [])
            add_on_1 = add_on_prices[0] if len(add_on_prices) > 0 else None
            add_on_2 = add_on_prices[1] if len(add_on_prices) > 1 else None

            results.append({
                'Code': ticker,
                'Name': row['Name'],
                'RS_Rating': rs_rating,
                'Current_Price': price_df['Close'].iloc[-1],

                # David Ryan Complete
                'Ryan_Signal': ryan_signal['entry_signal'],
                'Ryan_Strength': ryan_signal['signal_strength'],
                'Ryan_Entry': ryan_signal['entry_price'],
                'Ryan_Stop': ryan_signal['stop_loss'],
                'Ryan_AddOn_1': add_on_1,
                'Ryan_AddOn_2': add_on_2,
                'Ryan_RR_Ratio': ryan_signal.get('risk_reward_ratio', 0),
                'Ryan_Reasons': ' | '.join(ryan_signal['reasons']),
                'Ryan_Warnings': ' | '.join(ryan_signal.get('warnings', [])),

                # Mark Minervini
                'Minervini_Signal': minervini_signal['entry_signal'],
                'Minervini_Strength': minervini_signal['signal_strength'],
                'Minervini_Entry': minervini_signal['entry_price'],
                'Minervini_Stop': minervini_signal['stop_loss'],
                'Minervini_Pattern': minervini_signal['pattern_type'],
                'Minervini_Reasons': ' | '.join(minervini_signal['reasons']),

                # 종합
                'Both_Signal': ryan_signal['entry_signal'] and minervini_signal['entry_signal']
            })

    result_df = pd.DataFrame(results)

    if len(result_df) > 0:
        result_df = result_df.sort_values('RS_Rating', ascending=False).reset_index(drop=True)

    print(f"\n[분석 완료]")
    print(f"  David Ryan 진입 신호: {len(result_df[result_df['Ryan_Signal']])}개")
    print(f"  Mark Minervini 진입 신호: {len(result_df[result_df['Minervini_Signal']])}개")
    print(f"  두 전략 모두 신호: {len(result_df[result_df['Both_Signal']])}개")

    # 4. 한글 변환
    print("\n[4단계] 한글 변환")
    print("-" * 100)

    korean_columns = {
        'Code': '종목코드',
        'Name': '종목명',
        'RS_Rating': 'RS등급',
        'Current_Price': '현재가',
        'Ryan_Signal': 'Ryan_진입신호',
        'Ryan_Strength': 'Ryan_신호강도',
        'Ryan_Entry': 'Ryan_진입가',
        'Ryan_Stop': 'Ryan_손절가',
        'Ryan_AddOn_1': 'Ryan_추가매수1',
        'Ryan_AddOn_2': 'Ryan_추가매수2',
        'Ryan_RR_Ratio': 'Ryan_손익비',
        'Ryan_Reasons': 'Ryan_근거',
        'Ryan_Warnings': 'Ryan_경고',
        'Minervini_Signal': '미너비니_진입신호',
        'Minervini_Strength': '미너비니_신호강도',
        'Minervini_Entry': '미너비니_진입가',
        'Minervini_Stop': '미너비니_손절가',
        'Minervini_Pattern': '미너비니_패턴',
        'Minervini_Reasons': '미너비니_근거',
        'Both_Signal': '양쪽_모두_신호'
    }

    result_df_korean = result_df.rename(columns=korean_columns)

    # 5. 결과 저장
    print("\n[5단계] 결과 저장")
    print("-" * 100)

    if len(result_df_korean) > 0:
        # 전체
        save_results(result_df_korean, '진입신호_전체_고급')

        # David Ryan만
        ryan_only = result_df_korean[result_df_korean['Ryan_진입신호'] == True]
        if len(ryan_only) > 0:
            save_results(ryan_only, '진입신호_DavidRyan')

        # Minervini만
        minervini_only = result_df_korean[result_df_korean['미너비니_진입신호'] == True]
        if len(minervini_only) > 0:
            save_results(minervini_only, '진입신호_Minervini고급')

        # 양쪽 모두
        both = result_df_korean[result_df_korean['양쪽_모두_신호'] == True]
        if len(both) > 0:
            save_results(both, '진입신호_양쪽모두_최고')

    # 6. 웹 대시보드 생성
    print("\n[6단계] Modern 2단 레이아웃 대시보드 생성")
    print("-" * 100)

    if len(result_df_korean) > 0:
        os.makedirs(WEB_DIR, exist_ok=True)
        dashboard_file = generate_modern_dashboard(
            result_df_korean,
            price_data,
            os.path.join(WEB_DIR, 'dashboard.html')
        )

        # 브라우저로 열기
        abs_path = os.path.abspath(dashboard_file)
        print(f"\n대시보드 열기: {abs_path}")
        webbrowser.open('file://' + abs_path)

    print("\n" + "="*100)
    print("                         분석 완료!")
    print("="*100)
    print(f"\n총 {len(result_df_korean)}개 진입 신호 발견")
    print(f"웹 대시보드가 브라우저에서 열렸습니다.")
    print(f"결과 파일은 'results' 폴더에 저장되었습니다.\n")


if __name__ == "__main__":
    main()
