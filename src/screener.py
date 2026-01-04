"""
주도주 스크리닝 모듈
RS Rating 및 기타 지표를 활용한 주도주 선별
"""

import pandas as pd
import numpy as np
from datetime import datetime


class LeadingStockScreener:
    def __init__(self):
        """주도주 스크리너 초기화"""
        pass

    def calculate_volume_surge(self, price_data, recent_days=20, baseline_days=60):
        """
        거래량 급증 확인

        Args:
            price_data (DataFrame): 가격 데이터
            recent_days (int): 최근 기간 (영업일)
            baseline_days (int): 기준 기간 (영업일)

        Returns:
            float: 거래량 증가율 (%), None if 계산 불가
        """
        if len(price_data) < baseline_days:
            return None

        try:
            recent_volume = price_data['Volume'].iloc[-recent_days:].mean()
            baseline_volume = price_data['Volume'].iloc[-baseline_days:-recent_days].mean()

            if baseline_volume == 0 or pd.isna(baseline_volume):
                return None

            volume_surge = ((recent_volume - baseline_volume) / baseline_volume) * 100
            return volume_surge

        except Exception as e:
            return None

    def calculate_volatility(self, price_data, period=20):
        """
        가격 변동성 계산 (표준편차)

        Args:
            price_data (DataFrame): 가격 데이터
            period (int): 계산 기간 (영업일)

        Returns:
            float: 변동성 (%), None if 계산 불가
        """
        if len(price_data) < period:
            return None

        try:
            returns = price_data['Close'].pct_change().iloc[-period:]
            volatility = returns.std() * np.sqrt(252) * 100  # 연율화
            return volatility

        except Exception as e:
            return None

    def is_near_52week_high(self, price_data, threshold=0.85):
        """
        52주 최고가 근접 여부 확인

        Args:
            price_data (DataFrame): 가격 데이터
            threshold (float): 최고가 대비 임계값 (0.85 = 15% 이내)

        Returns:
            bool: 52주 최고가 근접 여부
        """
        if len(price_data) < 252:
            return False

        try:
            current_price = price_data['Close'].iloc[-1]
            high_52w = price_data['High'].iloc[-252:].max()

            if high_52w == 0 or pd.isna(high_52w):
                return False

            ratio = current_price / high_52w
            return ratio >= threshold

        except Exception as e:
            return False

    def calculate_price_strength(self, price_data):
        """
        가격 강도 계산 (최근 상승 일수 비율)

        Args:
            price_data (DataFrame): 가격 데이터

        Returns:
            float: 상승 일수 비율 (0~100)
        """
        if len(price_data) < 20:
            return None

        try:
            recent_changes = price_data['Close'].pct_change().iloc[-20:]
            up_days = (recent_changes > 0).sum()
            strength = (up_days / 20) * 100
            return strength

        except Exception as e:
            return None

    def screen_leading_stocks(self, stock_data_with_rs, price_data_dict,
                               min_rs=80, min_volume_surge=20, near_high=True):
        """
        주도주 스크리닝

        Args:
            stock_data_with_rs (DataFrame): RS Rating이 포함된 종목 데이터
            price_data_dict (dict): {종목코드: DataFrame} 가격 데이터
            min_rs (int): 최소 RS Rating
            min_volume_surge (float): 최소 거래량 증가율 (%)
            near_high (bool): 52주 최고가 근접 여부 필터

        Returns:
            DataFrame: 스크리닝된 주도주 리스트
        """
        print(f"\n[주도주 스크리닝] 시작...")
        print(f"[조건] RS Rating >= {min_rs}, 거래량 증가 >= {min_volume_surge}%, 52주 고가 근접: {near_high}")

        # RS Rating 필터링
        candidates = stock_data_with_rs[stock_data_with_rs['RS_Rating'] >= min_rs].copy()
        print(f"[1단계] RS Rating {min_rs} 이상: {len(candidates)}개 종목")

        # 추가 지표 계산
        results = []

        for idx, row in candidates.iterrows():
            ticker = row['Code']
            if ticker not in price_data_dict:
                continue

            price_data = price_data_dict[ticker]

            # 거래량 급증 확인
            volume_surge = self.calculate_volume_surge(price_data)
            if volume_surge is None or volume_surge < min_volume_surge:
                continue

            # 52주 최고가 근접 확인
            if near_high and not self.is_near_52week_high(price_data):
                continue

            # 변동성 계산
            volatility = self.calculate_volatility(price_data)

            # 가격 강도 계산
            price_strength = self.calculate_price_strength(price_data)

            # 현재 가격 정보
            current_price = price_data['Close'].iloc[-1]
            high_52w = price_data['High'].iloc[-252:].max() if len(price_data) >= 252 else None

            results.append({
                'Code': ticker,
                'Name': row['Name'],
                'RS_Rating': row['RS_Rating'],
                'Performance': row['Performance'],
                'Volume_Surge': volume_surge,
                'Price_Strength': price_strength,
                'Volatility': volatility,
                'Current_Price': current_price,
                '52W_High': high_52w,
                'Market': row.get('Market', 'N/A'),
                'Sector': row.get('Dept', 'N/A'),
                'MarketCap': row.get('Marcap', 0)
            })

        result_df = pd.DataFrame(results)

        if len(result_df) > 0:
            # RS Rating 기준 정렬
            result_df = result_df.sort_values('RS_Rating', ascending=False).reset_index(drop=True)

        print(f"[스크리닝 완료] {len(result_df)}개 주도주 발견")

        return result_df

    def categorize_by_potential(self, screened_stocks, price_data_dict):
        """
        성장 잠재력에 따라 종목 분류

        Args:
            screened_stocks (DataFrame): 스크리닝된 종목들
            price_data_dict (dict): 가격 데이터

        Returns:
            dict: 잠재력별로 분류된 종목
        """
        print("\n[잠재력 분석] 종목 분류 중...")

        categories = {
            'high_potential': [],      # 고성장 잠재력 (2-10배)
            'moderate_potential': [],  # 중간 잠재력
            'steady_growth': []        # 안정적 성장
        }

        for idx, row in screened_stocks.iterrows():
            ticker = row['Code']

            # 고성장 잠재력 기준:
            # 1. RS Rating 90 이상
            # 2. 거래량 급증 50% 이상
            # 3. 가격 강도 60% 이상
            if (row['RS_Rating'] >= 90 and
                row['Volume_Surge'] >= 50 and
                row.get('Price_Strength', 0) >= 60):
                categories['high_potential'].append(row)

            # 중간 잠재력 기준:
            # 1. RS Rating 85 이상
            # 2. 거래량 급증 30% 이상
            elif (row['RS_Rating'] >= 85 and
                  row['Volume_Surge'] >= 30):
                categories['moderate_potential'].append(row)

            # 안정적 성장
            else:
                categories['steady_growth'].append(row)

        print(f"  - 고성장 잠재력: {len(categories['high_potential'])}개")
        print(f"  - 중간 잠재력: {len(categories['moderate_potential'])}개")
        print(f"  - 안정적 성장: {len(categories['steady_growth'])}개")

        return categories


if __name__ == "__main__":
    print("주도주 스크리너 테스트...")
    # 실제 테스트는 main.py에서 진행
