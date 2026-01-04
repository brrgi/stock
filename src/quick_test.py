"""
빠른 테스트용 - 상위 200개 종목만 분석
"""

import pandas as pd
from datetime import datetime
import os

from data_collector import StockDataCollector
from rs_calculator import RSCalculator
from screener import LeadingStockScreener


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


def main():
    """메인 실행 함수"""
    print("="*80)
    print("          한국 주식 RS Rating 스크리너 (빠른 테스트)")
    print("          시가총액 상위 200개 종목 분석")
    print("="*80)

    # 1. 데이터 수집
    print("\n[1단계] 주식 데이터 수집")
    print("-" * 80)

    collector = StockDataCollector()

    # 전체 종목 리스트 가져오기
    stock_list = collector.get_stock_list('ALL')

    # 거래 가능한 종목 필터링
    tradable_stocks = collector.filter_tradable_stocks(
        stock_list,
        min_price=5000,      # 최소 주가 5000원
        min_market_cap=1000  # 최소 시가총액 1000억원
    )

    # 시가총액 기준 상위 200개만 선택
    tradable_stocks = tradable_stocks.nlargest(200, 'Marcap')
    print(f"\n[선택] 시가총액 상위 {len(tradable_stocks)}개 종목으로 분석")

    # 가격 데이터 수집
    print(f"\n[데이터 수집] 예상 소요 시간: 약 {len(tradable_stocks) * 0.1 / 60:.1f}분")

    price_data = collector.get_bulk_price_data(
        tradable_stocks,
        period_days=252,  # 1년치 데이터
        delay=0.1         # API 호출 간격 (초)
    )

    # 2. RS Rating 계산
    print("\n[2단계] RS Rating 계산")
    print("-" * 80)

    calculator = RSCalculator()
    stocks_with_rs = calculator.calculate_all_rs_ratings(price_data, tradable_stocks)

    # 상위 RS Rating 종목 저장
    print("\n[RS Rating TOP 30]")
    print(stocks_with_rs[['Code', 'Name', 'RS_Rating', 'Performance']].head(30))
    save_results(stocks_with_rs.head(50), 'top_rs_stocks_quick')

    # 3. 주도주 스크리닝
    print("\n[3단계] 주도주 스크리닝")
    print("-" * 80)

    screener = LeadingStockScreener()
    leading_stocks = screener.screen_leading_stocks(
        stocks_with_rs,
        price_data,
        min_rs=70,            # RS Rating 70 이상 (테스트용으로 낮춤)
        min_volume_surge=15,  # 거래량 15% 이상 증가
        near_high=True        # 52주 최고가 근접
    )

    # 4. 잠재력별 분류
    print("\n[4단계] 성장 잠재력 분석")
    print("-" * 80)

    categories = screener.categorize_by_potential(leading_stocks, price_data)

    # 5. 결과 저장
    print("\n[5단계] 결과 저장")
    print("-" * 80)

    if len(leading_stocks) > 0:
        save_results(leading_stocks, 'leading_stocks_quick')

        # 고성장 잠재력 종목만 별도 저장
        if len(categories['high_potential']) > 0:
            high_potential_df = pd.DataFrame(categories['high_potential'])
            save_results(high_potential_df, 'high_potential_stocks_quick')

    # 6. 결과 요약 출력
    print("\n" + "="*80)
    print("                    주도주 스크리닝 결과 요약")
    print("="*80)

    print(f"\n총 발견된 주도주: {len(leading_stocks)}개\n")

    # 잠재력별 통계
    print("【 성장 잠재력별 분류 】")
    print(f"  ★ 고성장 잠재력 (2-10배): {len(categories['high_potential'])}개")
    print(f"  ▲ 중간 잠재력: {len(categories['moderate_potential'])}개")
    print(f"  ■ 안정적 성장: {len(categories['steady_growth'])}개")

    # 고성장 잠재력 종목 상세 출력
    if len(categories['high_potential']) > 0:
        print(f"\n【 고성장 잠재력 종목 】")
        print("-" * 80)

        high_potential_df = pd.DataFrame(categories['high_potential'])
        high_potential_df = high_potential_df.sort_values('RS_Rating', ascending=False)

        for idx, row in high_potential_df.iterrows():
            print(f"\n{idx+1}. {row['Name']} ({row['Code']})")
            print(f"   RS Rating: {row['RS_Rating']}")
            print(f"   성과: {row['Performance']:.2f}%")
            print(f"   거래량 증가: {row['Volume_Surge']:.2f}%")
            print(f"   가격 강도: {row.get('Price_Strength', 0):.2f}%")
            print(f"   현재가: {row['Current_Price']:,.0f}원")

    print("\n" + "="*80)
    print("\n프로그램 실행 완료!")
    print(f"결과 파일은 'results' 폴더에 저장되었습니다.\n")


if __name__ == "__main__":
    main()
