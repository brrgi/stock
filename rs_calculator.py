"""
RS (Relative Strength) Rating 계산 모듈
윌리엄 오닐의 RS Rating 개념 구현
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class RSCalculator:
    def __init__(self):
        """RS Rating 계산기 초기화"""
        pass

    def calculate_price_performance(self, price_data, period_days):
        """
        특정 기간 동안의 가격 성과 계산

        Args:
            price_data (DataFrame): 가격 데이터
            period_days (int): 기간 (영업일)

        Returns:
            float: 수익률 (%), None if 계산 불가
        """
        if len(price_data) < period_days:
            return None

        try:
            current_price = price_data['Close'].iloc[-1]
            past_price = price_data['Close'].iloc[-period_days]

            if past_price == 0 or pd.isna(past_price) or pd.isna(current_price):
                return None

            performance = ((current_price - past_price) / past_price) * 100
            return performance

        except Exception as e:
            return None

    def calculate_weighted_performance(self, price_data):
        """
        가중 성과 계산 (최근 데이터에 더 높은 가중치)
        IBD 방식: 최근 3개월 40%, 6개월 전~3개월 전 20%, 9개월 전~6개월 전 20%, 12개월 전~9개월 전 20%

        Args:
            price_data (DataFrame): 가격 데이터

        Returns:
            float: 가중 성과, None if 계산 불가
        """
        # 영업일 기준 (1년 = 약 252일)
        period_1q = 63   # 3개월
        period_2q = 126  # 6개월
        period_3q = 189  # 9개월
        period_4q = 252  # 12개월

        if len(price_data) < period_4q:
            return None

        try:
            # 각 분기별 수익률 계산
            perf_1q = self.calculate_price_performance(price_data, period_1q)  # 최근 3개월
            perf_2q = self.calculate_price_performance(price_data, period_2q)  # 최근 6개월
            perf_3q = self.calculate_price_performance(price_data, period_3q)  # 최근 9개월
            perf_4q = self.calculate_price_performance(price_data, period_4q)  # 최근 12개월

            if any(x is None for x in [perf_1q, perf_2q, perf_3q, perf_4q]):
                return None

            # 각 구간별 성과 계산
            q1_return = perf_1q  # 0~3개월
            q2_return = perf_2q - perf_1q  # 3~6개월
            q3_return = perf_3q - perf_2q  # 6~9개월
            q4_return = perf_4q - perf_3q  # 9~12개월

            # 가중치 적용 (최근에 더 높은 가중치)
            weighted_performance = (
                q1_return * 0.4 +  # 최근 3개월: 40%
                q2_return * 0.2 +  # 3~6개월: 20%
                q3_return * 0.2 +  # 6~9개월: 20%
                q4_return * 0.2    # 9~12개월: 20%
            )

            return weighted_performance

        except Exception as e:
            print(f"[오류] 가중 성과 계산 실패: {e}")
            return None

    def calculate_rs_rating(self, stock_performance, all_performances):
        """
        RS Rating 계산 (0~99 점수)

        Args:
            stock_performance (float): 해당 종목의 성과
            all_performances (list): 모든 종목의 성과 리스트

        Returns:
            int: RS Rating (0~99)
        """
        if stock_performance is None or pd.isna(stock_performance):
            return 0

        # 유효한 성과 값만 필터링
        valid_performances = [p for p in all_performances if p is not None and not pd.isna(p)]

        if len(valid_performances) == 0:
            return 0

        # 백분위수 계산 (해당 종목보다 낮은 성과를 가진 종목의 비율)
        rank = sum(1 for p in valid_performances if p < stock_performance)
        percentile = (rank / len(valid_performances)) * 100

        # 0~99로 스케일링
        rs_rating = min(99, int(percentile))

        return rs_rating

    def calculate_all_rs_ratings(self, price_data_dict, stock_list):
        """
        모든 종목의 RS Rating 계산

        Args:
            price_data_dict (dict): {종목코드: DataFrame} 형태의 가격 데이터
            stock_list (DataFrame): 종목 리스트

        Returns:
            DataFrame: RS Rating이 추가된 종목 리스트
        """
        print("\n[RS Rating 계산] 시작...")

        # 1단계: 모든 종목의 가중 성과 계산
        performances = {}
        for ticker, price_data in price_data_dict.items():
            perf = self.calculate_weighted_performance(price_data)
            performances[ticker] = perf

        print(f"[RS Rating 계산] {len(performances)}개 종목 성과 계산 완료")

        # 2단계: RS Rating 계산
        all_perfs = list(performances.values())

        rs_ratings = {}
        for ticker, perf in performances.items():
            rs_rating = self.calculate_rs_rating(perf, all_perfs)
            rs_ratings[ticker] = {
                'Performance': perf,
                'RS_Rating': rs_rating
            }

        # 3단계: 결과를 DataFrame으로 변환
        result_df = stock_list.copy()
        result_df['Performance'] = result_df['Code'].map(lambda x: rs_ratings.get(x, {}).get('Performance'))
        result_df['RS_Rating'] = result_df['Code'].map(lambda x: rs_ratings.get(x, {}).get('RS_Rating', 0))

        # 결과가 있는 종목만 필터링
        result_df = result_df[result_df['Performance'].notna()].copy()

        # RS Rating 기준 내림차순 정렬
        result_df = result_df.sort_values('RS_Rating', ascending=False).reset_index(drop=True)

        print(f"[RS Rating 계산 완료] 총 {len(result_df)}개 종목")
        print(f"\n[통계]")
        print(f"  - RS Rating 90 이상: {len(result_df[result_df['RS_Rating'] >= 90])}개")
        print(f"  - RS Rating 80 이상: {len(result_df[result_df['RS_Rating'] >= 80])}개")
        print(f"  - RS Rating 70 이상: {len(result_df[result_df['RS_Rating'] >= 70])}개")

        return result_df

    def calculate_recent_momentum(self, price_data, periods=[5, 20, 60]):
        """
        최근 모멘텀 계산 (단기, 중기, 장기)

        Args:
            price_data (DataFrame): 가격 데이터
            periods (list): 계산할 기간 리스트 (영업일)

        Returns:
            dict: {기간: 수익률} 형태의 딕셔너리
        """
        momentum = {}
        for period in periods:
            perf = self.calculate_price_performance(price_data, period)
            momentum[f'{period}D'] = perf

        return momentum


if __name__ == "__main__":
    # 테스트 코드
    import sys
    sys.path.append('.')
    from data_collector import StockDataCollector

    print("RS Calculator 테스트 시작...\n")

    # 데이터 수집
    collector = StockDataCollector()
    stock_list = collector.get_stock_list('KOSPI')
    tradable = collector.filter_tradable_stocks(stock_list[:100])  # 테스트용으로 100개만

    print("\n샘플 데이터로 RS Rating 계산 테스트 중...")
    price_data = collector.get_bulk_price_data(tradable.head(10), delay=0.2)

    # RS Rating 계산
    calculator = RSCalculator()
    result = calculator.calculate_all_rs_ratings(price_data, tradable.head(10))

    print("\n[결과]")
    print(result[['Code', 'Name', 'RS_Rating', 'Performance']].head(10))
