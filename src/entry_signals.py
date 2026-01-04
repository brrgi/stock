"""
진입 시점 분석 모듈
윌리엄 오닐(CAN SLIM)과 마크 미너비니(SEPA) 전략 기반
"""

import pandas as pd
import numpy as np


class EntrySignalAnalyzer:
    def __init__(self):
        """진입 시점 분석기 초기화"""
        pass

    # ========== 윌리엄 오닐 진입 전략 ==========

    def check_cup_with_handle(self, price_data, lookback=60):
        """
        컵 앤 핸들 패턴 확인 (William O'Neil)

        Args:
            price_data (DataFrame): 가격 데이터
            lookback (int): 확인할 기간

        Returns:
            dict: 패턴 정보
        """
        if len(price_data) < lookback:
            return {'pattern': False, 'type': None, 'depth': 0}

        recent_data = price_data.iloc[-lookback:]

        # 최고가와 최저가 찾기
        high_price = recent_data['High'].max()
        low_price = recent_data['Low'].min()
        current_price = price_data['Close'].iloc[-1]

        # 조정 깊이 계산
        correction_depth = ((high_price - low_price) / high_price) * 100

        # 컵 형성 기준: 12-33% 조정 (이상적)
        if 12 <= correction_depth <= 33:
            # 현재 최고가 근처 (5% 이내)
            if current_price >= high_price * 0.95:
                return {
                    'pattern': True,
                    'type': 'Cup with Handle',
                    'depth': correction_depth,
                    'high': high_price,
                    'pivot': high_price
                }

        return {'pattern': False, 'type': None, 'depth': correction_depth}

    def check_flat_base(self, price_data, lookback=30):
        """
        플랫 베이스 패턴 확인 (William O'Neil)

        Args:
            price_data (DataFrame): 가격 데이터
            lookback (int): 확인할 기간 (최소 5주)

        Returns:
            dict: 패턴 정보
        """
        if len(price_data) < lookback:
            return {'pattern': False, 'tightness': 0}

        recent_data = price_data.iloc[-lookback:]

        # 가격 범위 계산
        high = recent_data['High'].max()
        low = recent_data['Low'].min()
        price_range = ((high - low) / low) * 100

        # 플랫 베이스: 10-15% 이내 횡보
        if price_range <= 15:
            current_price = price_data['Close'].iloc[-1]
            # 베이스 상단 근처 (5% 이내)
            if current_price >= high * 0.95:
                return {
                    'pattern': True,
                    'tightness': price_range,
                    'pivot': high,
                    'weeks': lookback / 5
                }

        return {'pattern': False, 'tightness': price_range}

    def check_volume_breakout(self, price_data, threshold=1.5):
        """
        거래량 돌파 확인 (William O'Neil)

        Args:
            price_data (DataFrame): 가격 데이터
            threshold (float): 평균 대비 배수 (1.5배 이상)

        Returns:
            dict: 거래량 돌파 정보
        """
        if len(price_data) < 50:
            return {'breakout': False, 'volume_ratio': 0}

        # 최근 거래량 vs 50일 평균
        current_volume = price_data['Volume'].iloc[-1]
        avg_volume_50 = price_data['Volume'].iloc[-50:].mean()

        volume_ratio = current_volume / avg_volume_50

        # 가격 상승과 함께 거래량 증가
        price_up = price_data['Close'].iloc[-1] > price_data['Close'].iloc[-2]

        if volume_ratio >= threshold and price_up:
            return {
                'breakout': True,
                'volume_ratio': volume_ratio,
                'strength': 'Strong' if volume_ratio >= 2.0 else 'Moderate'
            }

        return {'breakout': False, 'volume_ratio': volume_ratio}

    def william_oneil_entry_signal(self, price_data, rs_rating):
        """
        윌리엄 오닐 종합 진입 신호

        핵심 원칙:
        1. RS Rating 80 이상
        2. 컵 앤 핸들 또는 플랫 베이스 패턴
        3. 피봇 포인트 돌파 (신고가 또는 베이스 상단)
        4. 거래량 급증 (평균 대비 40-50% 이상)
        5. 52주 최고가 대비 15% 이내

        Args:
            price_data (DataFrame): 가격 데이터
            rs_rating (int): RS Rating

        Returns:
            dict: 진입 신호 정보
        """
        signal = {
            'entry_signal': False,
            'signal_strength': 0,
            'entry_price': 0,
            'stop_loss': 0,
            'reasons': []
        }

        if len(price_data) < 60:
            return signal

        current_price = price_data['Close'].iloc[-1]

        # 1. RS Rating 체크
        if rs_rating < 80:
            return signal

        signal['reasons'].append(f'RS Rating {rs_rating} (80+ ✓)')
        signal['signal_strength'] += 20

        # 2. 컵 앤 핸들 패턴
        cup_handle = self.check_cup_with_handle(price_data)
        if cup_handle['pattern']:
            signal['reasons'].append(f"컵 앤 핸들 패턴 (조정 {cup_handle['depth']:.1f}%)")
            signal['signal_strength'] += 30
            signal['entry_price'] = cup_handle['pivot'] * 1.001  # 피봇 + 0.1%
            signal['stop_loss'] = cup_handle['pivot'] * 0.93  # 7-8% 손절

        # 3. 플랫 베이스 패턴
        flat_base = self.check_flat_base(price_data)
        if flat_base['pattern']:
            signal['reasons'].append(f"플랫 베이스 ({flat_base['tightness']:.1f}% 타이트)")
            signal['signal_strength'] += 25
            if signal['entry_price'] == 0:
                signal['entry_price'] = flat_base['pivot'] * 1.001
                signal['stop_loss'] = flat_base['pivot'] * 0.93

        # 4. 거래량 돌파
        volume_bo = self.check_volume_breakout(price_data)
        if volume_bo['breakout']:
            signal['reasons'].append(f"거래량 돌파 ({volume_bo['volume_ratio']:.1f}배)")
            signal['signal_strength'] += 25

        # 5. 52주 최고가 근접
        high_52w = price_data['High'].iloc[-252:].max() if len(price_data) >= 252 else price_data['High'].max()
        distance_from_high = ((high_52w - current_price) / high_52w) * 100

        if distance_from_high <= 15:
            signal['reasons'].append(f'52주 최고가 {distance_from_high:.1f}% 이내')
            signal['signal_strength'] += 20

        # 기본 진입가/손절가 설정 (패턴 없을 경우)
        if signal['entry_price'] == 0:
            signal['entry_price'] = current_price * 1.02  # 현재가 + 2%
            signal['stop_loss'] = current_price * 0.93

        # 진입 신호 판정 (70점 이상)
        if signal['signal_strength'] >= 70:
            signal['entry_signal'] = True

        return signal

    # ========== 마크 미너비니 진입 전략 (SEPA) ==========

    def check_stage_2_uptrend(self, price_data):
        """
        스테이지 2 상승 추세 확인 (Mark Minervini)

        조건:
        - 주가가 150일, 200일 이동평균선 위
        - 150일 이평선이 200일 이평선 위
        - 200일 이평선이 상승 중
        - 주가가 52주 최저가 대비 30% 이상 상승
        - 주가가 52주 최고가 대비 25% 이내

        Args:
            price_data (DataFrame): 가격 데이터

        Returns:
            dict: 스테이지 분석 정보
        """
        if len(price_data) < 200:
            return {'stage_2': False, 'details': []}

        current_price = price_data['Close'].iloc[-1]

        # 이동평균선 계산
        ma_50 = price_data['Close'].iloc[-50:].mean()
        ma_150 = price_data['Close'].iloc[-150:].mean()
        ma_200 = price_data['Close'].iloc[-200:].mean()

        # 200일 이평선 기울기
        ma_200_past = price_data['Close'].iloc[-220:-200].mean()
        ma_200_rising = ma_200 > ma_200_past

        # 52주 최고/최저
        high_52w = price_data['High'].iloc[-252:].max() if len(price_data) >= 252 else price_data['High'].max()
        low_52w = price_data['Low'].iloc[-252:].min() if len(price_data) >= 252 else price_data['Low'].min()

        details = []
        checks = 0

        # 체크리스트
        if current_price > ma_150:
            details.append('주가 > 150일 이평 ✓')
            checks += 1
        else:
            details.append('주가 > 150일 이평 ✗')

        if current_price > ma_200:
            details.append('주가 > 200일 이평 ✓')
            checks += 1
        else:
            details.append('주가 > 200일 이평 ✗')

        if ma_150 > ma_200:
            details.append('150일 > 200일 이평 ✓')
            checks += 1
        else:
            details.append('150일 > 200일 이평 ✗')

        if ma_200_rising:
            details.append('200일 이평 상승 중 ✓')
            checks += 1
        else:
            details.append('200일 이평 상승 중 ✗')

        # 52주 최저가 대비 30% 이상 상승
        gain_from_low = ((current_price - low_52w) / low_52w) * 100
        if gain_from_low >= 30:
            details.append(f'52주 최저 대비 +{gain_from_low:.1f}% ✓')
            checks += 1
        else:
            details.append(f'52주 최저 대비 +{gain_from_low:.1f}% ✗')

        # 52주 최고가 대비 25% 이내
        distance_from_high = ((high_52w - current_price) / high_52w) * 100
        if distance_from_high <= 25:
            details.append(f'52주 최고가 {distance_from_high:.1f}% 이내 ✓')
            checks += 1
        else:
            details.append(f'52주 최고가 {distance_from_high:.1f}% 이내 ✗')

        # 50일 이평선 위 (추가 조건)
        if current_price > ma_50:
            details.append('주가 > 50일 이평 ✓')
            checks += 1

        return {
            'stage_2': checks >= 6,  # 7개 중 6개 이상
            'checks_passed': checks,
            'total_checks': 7,
            'details': details,
            'ma_50': ma_50,
            'ma_150': ma_150,
            'ma_200': ma_200
        }

    def check_vcp_pattern(self, price_data, lookback=60):
        """
        VCP (Volatility Contraction Pattern) 확인 (Mark Minervini)

        변동성이 점점 축소되는 패턴
        - 3-4번의 조정이 점점 작아짐
        - 마지막 조정이 가장 작음 (타이트)

        Args:
            price_data (DataFrame): 가격 데이터
            lookback (int): 확인할 기간

        Returns:
            dict: VCP 패턴 정보
        """
        if len(price_data) < lookback:
            return {'vcp': False, 'contractions': []}

        recent_data = price_data.iloc[-lookback:]

        # 최근 3개 조정 구간 찾기
        highs = recent_data['High'].rolling(window=5).max()
        lows = recent_data['Low'].rolling(window=5).min()

        # 간단 버전: 최근 30일, 20일, 10일의 변동폭 비교
        vol_30 = ((recent_data['High'].iloc[-30:].max() - recent_data['Low'].iloc[-30:].min()) /
                  recent_data['Low'].iloc[-30:].min() * 100)
        vol_20 = ((recent_data['High'].iloc[-20:].max() - recent_data['Low'].iloc[-20:].min()) /
                  recent_data['Low'].iloc[-20:].min() * 100)
        vol_10 = ((recent_data['High'].iloc[-10:].max() - recent_data['Low'].iloc[-10:].min()) /
                  recent_data['Low'].iloc[-10:].min() * 100)

        contractions = [vol_30, vol_20, vol_10]

        # VCP 조건: 변동성이 축소되는가?
        if vol_30 > vol_20 > vol_10 and vol_10 < 5:  # 마지막 조정이 5% 미만으로 타이트
            return {
                'vcp': True,
                'contractions': contractions,
                'tightness': vol_10
            }

        return {'vcp': False, 'contractions': contractions}

    def mark_minervini_entry_signal(self, price_data, rs_rating):
        """
        마크 미너비니 종합 진입 신호 (SEPA - Specific Entry Point Analysis)

        핵심 원칙:
        1. 스테이지 2 상승 추세
        2. RS Rating 80 이상 (업계 1-2위)
        3. VCP 패턴 또는 타이트한 통합
        4. 피봇 포인트 돌파
        5. 적절한 거래량 (폭발적이지 않아도 됨, 평균 이상)

        Args:
            price_data (DataFrame): 가격 데이터
            rs_rating (int): RS Rating

        Returns:
            dict: 진입 신호 정보
        """
        signal = {
            'entry_signal': False,
            'signal_strength': 0,
            'entry_price': 0,
            'stop_loss': 0,
            'reasons': []
        }

        if len(price_data) < 200:
            return signal

        current_price = price_data['Close'].iloc[-1]

        # 1. 스테이지 2 상승 추세 (가장 중요!)
        stage_2 = self.check_stage_2_uptrend(price_data)
        if not stage_2['stage_2']:
            signal['reasons'].append(f"스테이지 2 미충족 ({stage_2['checks_passed']}/7)")
            return signal

        signal['reasons'].append(f"스테이지 2 상승추세 ({stage_2['checks_passed']}/7) ✓")
        signal['signal_strength'] += 40

        # 2. RS Rating
        if rs_rating >= 90:
            signal['reasons'].append(f'RS Rating {rs_rating} (최상위) ✓')
            signal['signal_strength'] += 30
        elif rs_rating >= 80:
            signal['reasons'].append(f'RS Rating {rs_rating} (우수) ✓')
            signal['signal_strength'] += 20
        else:
            signal['reasons'].append(f'RS Rating {rs_rating} (부족)')
            return signal

        # 3. VCP 패턴
        vcp = self.check_vcp_pattern(price_data)
        if vcp['vcp']:
            signal['reasons'].append(f"VCP 패턴 (타이트니스 {vcp['tightness']:.1f}%) ✓")
            signal['signal_strength'] += 30

        # 4. 피봇 포인트 (최근 최고가)
        pivot = price_data['High'].iloc[-10:].max()

        # 현재가가 피봇 근처 (1% 이내)
        if current_price >= pivot * 0.99:
            signal['reasons'].append(f'피봇 포인트 근접 ✓')
            signal['signal_strength'] += 20
            signal['entry_price'] = pivot * 1.001  # 피봇 + 0.1%
        else:
            signal['entry_price'] = pivot * 1.001

        # 5. 손절가 설정 (미너비니: 최대 7-8% 손절)
        # 최근 저점 또는 이동평균선 중 가까운 곳
        recent_low = price_data['Low'].iloc[-10:].min()
        ma_50 = stage_2['ma_50']

        # 손절선은 최근 저점과 50일 이평 중 높은 곳
        stop_candidate = max(recent_low, ma_50)
        stop_loss_pct = ((current_price - stop_candidate) / current_price) * 100

        # 최대 8% 손절
        if stop_loss_pct <= 8:
            signal['stop_loss'] = stop_candidate
        else:
            signal['stop_loss'] = current_price * 0.92  # 8% 손절

        signal['reasons'].append(f'손절선: {stop_loss_pct:.1f}%')

        # 진입 신호 판정 (80점 이상)
        if signal['signal_strength'] >= 80:
            signal['entry_signal'] = True

        return signal

    def analyze_all_entry_signals(self, stock_data_with_rs, price_data_dict):
        """
        모든 종목의 진입 신호 분석

        Args:
            stock_data_with_rs (DataFrame): RS Rating이 포함된 종목 데이터
            price_data_dict (dict): 가격 데이터

        Returns:
            DataFrame: 진입 신호가 추가된 데이터
        """
        print("\n[진입 시점 분석] 윌리엄 오닐 & 마크 미너비니 전략")
        print("-" * 80)

        results = []

        for idx, row in stock_data_with_rs.iterrows():
            ticker = row['Code']

            if ticker not in price_data_dict:
                continue

            price_data = price_data_dict[ticker]
            rs_rating = row['RS_Rating']

            # 두 전략 모두 분석
            oneil_signal = self.william_oneil_entry_signal(price_data, rs_rating)
            minervini_signal = self.mark_minervini_entry_signal(price_data, rs_rating)

            # 둘 중 하나라도 진입 신호면 포함
            if oneil_signal['entry_signal'] or minervini_signal['entry_signal']:
                results.append({
                    'Code': ticker,
                    'Name': row['Name'],
                    'RS_Rating': rs_rating,
                    'Current_Price': price_data['Close'].iloc[-1],

                    # 윌리엄 오닐
                    'ONeil_Signal': oneil_signal['entry_signal'],
                    'ONeil_Strength': oneil_signal['signal_strength'],
                    'ONeil_Entry': oneil_signal['entry_price'],
                    'ONeil_Stop': oneil_signal['stop_loss'],
                    'ONeil_Reasons': ' | '.join(oneil_signal['reasons']),

                    # 마크 미너비니
                    'Minervini_Signal': minervini_signal['entry_signal'],
                    'Minervini_Strength': minervini_signal['signal_strength'],
                    'Minervini_Entry': minervini_signal['entry_price'],
                    'Minervini_Stop': minervini_signal['stop_loss'],
                    'Minervini_Reasons': ' | '.join(minervini_signal['reasons']),

                    # 종합
                    'Both_Signal': oneil_signal['entry_signal'] and minervini_signal['entry_signal']
                })

        result_df = pd.DataFrame(results)

        if len(result_df) > 0:
            result_df = result_df.sort_values('RS_Rating', ascending=False).reset_index(drop=True)

        print(f"\n[분석 완료]")
        print(f"  - 윌리엄 오닐 진입 신호: {len(result_df[result_df['ONeil_Signal']])}개")
        print(f"  - 마크 미너비니 진입 신호: {len(result_df[result_df['Minervini_Signal']])}개")
        print(f"  - 두 전략 모두 신호: {len(result_df[result_df['Both_Signal']])}개")

        return result_df


if __name__ == "__main__":
    print("진입 시점 분석 모듈 테스트...")
