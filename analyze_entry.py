"""
진입 시점 분석 실행 스크립트
기존 RS Rating 결과에 진입 신호 추가
"""

import pandas as pd
from datetime import datetime
import os

from data_collector import StockDataCollector
from rs_calculator import RSCalculator
from entry_signals import EntrySignalAnalyzer


def save_results(data, filename, folder='results'):
    """결과를 파일로 저장"""
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # CSV 저장
    csv_path = os.path.join(folder, f'{filename}_{timestamp}.csv')
    data.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"[저장완료] CSV: {csv_path}")

    # Excel 저장
    excel_path = os.path.join(folder, f'{filename}_{timestamp}.xlsx')
    data.to_excel(excel_path, index=False, engine='openpyxl')
    print(f"[저장완료] Excel: {excel_path}")

    return csv_path, excel_path


def print_entry_summary(entry_signals):
    """진입 신호 요약 출력"""
    print("\n" + "="*100)
    print("                         진입 시점 분석 결과 요약")
    print("="*100)

    # 두 전략 모두 신호
    both_signals = entry_signals[entry_signals['Both_Signal'] == True]

    if len(both_signals) > 0:
        print(f"\n【 ★★★ 윌리엄 오닐 + 마크 미너비니 모두 진입 신호 】 ({len(both_signals)}개)")
        print("-" * 100)

        for idx, row in both_signals.head(10).iterrows():
            print(f"\n{idx+1}. {row['Name']} ({row['Code']}) - RS Rating: {row['RS_Rating']}")
            print(f"   현재가: {row['Current_Price']:,.0f}원")
            print(f"   ")
            print(f"   [윌리엄 오닐] 신호 강도: {row['ONeil_Strength']}점")
            print(f"      진입가: {row['ONeil_Entry']:,.0f}원 | 손절가: {row['ONeil_Stop']:,.0f}원")
            print(f"      사유: {row['ONeil_Reasons']}")
            print(f"   ")
            print(f"   [마크 미너비니] 신호 강도: {row['Minervini_Strength']}점")
            print(f"      진입가: {row['Minervini_Entry']:,.0f}원 | 손절가: {row['Minervini_Stop']:,.0f}원")
            print(f"      사유: {row['Minervini_Reasons']}")

    # 윌리엄 오닐만
    oneil_only = entry_signals[(entry_signals['ONeil_Signal'] == True) &
                               (entry_signals['Minervini_Signal'] == False)]

    if len(oneil_only) > 0:
        print(f"\n\n【 윌리엄 오닐 진입 신호 】 ({len(oneil_only)}개)")
        print("-" * 100)

        for idx, row in oneil_only.head(5).iterrows():
            print(f"\n{row['Name']} ({row['Code']}) - RS {row['RS_Rating']}")
            print(f"   현재가: {row['Current_Price']:,.0f}원 | 진입: {row['ONeil_Entry']:,.0f}원 | 손절: {row['ONeil_Stop']:,.0f}원")
            print(f"   {row['ONeil_Reasons']}")

    # 마크 미너비니만
    minervini_only = entry_signals[(entry_signals['Minervini_Signal'] == True) &
                                   (entry_signals['ONeil_Signal'] == False)]

    if len(minervini_only) > 0:
        print(f"\n\n【 마크 미너비니 진입 신호 】 ({len(minervini_only)}개)")
        print("-" * 100)

        for idx, row in minervini_only.head(5).iterrows():
            print(f"\n{row['Name']} ({row['Code']}) - RS {row['RS_Rating']}")
            print(f"   현재가: {row['Current_Price']:,.0f}원 | 진입: {row['Minervini_Entry']:,.0f}원 | 손절: {row['Minervini_Stop']:,.0f}원")
            print(f"   {row['Minervini_Reasons']}")

    print("\n" + "="*100)


def main():
    """메인 실행 함수"""
    print("="*100)
    print("          진입 시점 분석 - 윌리엄 오닐 & 마크 미너비니")
    print("          시가총액 상위 200개 종목 분석")
    print("="*100)

    # 1. 데이터 수집
    print("\n[1단계] 주식 데이터 수집")
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
    print(f"\n[선택] 시가총액 상위 {len(tradable_stocks)}개 종목으로 분석")

    # 가격 데이터 수집
    print(f"\n[데이터 수집] 약 {len(tradable_stocks) * 0.1 / 60:.1f}분 소요 예상")
    price_data = collector.get_bulk_price_data(tradable_stocks, period_days=252, delay=0.1)

    # 2. RS Rating 계산
    print("\n[2단계] RS Rating 계산")
    print("-" * 100)

    calculator = RSCalculator()
    stocks_with_rs = calculator.calculate_all_rs_ratings(price_data, tradable_stocks)

    # RS Rating 70 이상만 진입 분석
    high_rs_stocks = stocks_with_rs[stocks_with_rs['RS_Rating'] >= 70].copy()
    print(f"\n[필터링] RS Rating 70 이상: {len(high_rs_stocks)}개 종목")

    # 3. 진입 시점 분석
    print("\n[3단계] 진입 시점 분석")
    print("-" * 100)

    analyzer = EntrySignalAnalyzer()
    entry_signals = analyzer.analyze_all_entry_signals(high_rs_stocks, price_data)

    # 4. 결과 저장
    print("\n[4단계] 결과 저장")
    print("-" * 100)

    if len(entry_signals) > 0:
        # 전체 진입 신호
        save_results(entry_signals, 'entry_signals_all')

        # 두 전략 모두 신호
        both_signals = entry_signals[entry_signals['Both_Signal'] == True]
        if len(both_signals) > 0:
            save_results(both_signals, 'entry_signals_both')

        # 윌리엄 오닐
        oneil_signals = entry_signals[entry_signals['ONeil_Signal'] == True]
        if len(oneil_signals) > 0:
            save_results(oneil_signals, 'entry_signals_oneil')

        # 마크 미너비니
        minervini_signals = entry_signals[entry_signals['Minervini_Signal'] == True]
        if len(minervini_signals) > 0:
            save_results(minervini_signals, 'entry_signals_minervini')

    # 5. 결과 요약 출력
    if len(entry_signals) > 0:
        print_entry_summary(entry_signals)
    else:
        print("\n진입 신호를 찾지 못했습니다.")

    print("\n프로그램 실행 완료!")
    print(f"결과 파일은 'results' 폴더에 저장되었습니다.\n")


if __name__ == "__main__":
    main()
