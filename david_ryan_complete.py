"""
David Ryan 완전 구현 전략
상세 명세서 기반
"""

import pandas as pd
import numpy as np
from entry_signals import EntrySignalAnalyzer


class DavidRyanComplete(EntrySignalAnalyzer):
    def __init__(self):
        """David Ryan 완전 전략 분석기"""
        super().__init__()

    # ========== 1. 산업군 및 시장 필터 ==========

    def check_market_direction(self, index_data):
        """
        시장 방향성 확인
        - KOSPI/KOSDAQ이 50일 이평선 위
        - 50일선이 200일선 위 (정배열)
        """
        if len(index_data) < 200:
            return {'direction_ok': False, 'reason': '데이터 부족'}

        current = index_data['Close'].iloc[-1]
        ma_50 = index_data['Close'].iloc[-50:].mean()
        ma_200 = index_data['Close'].iloc[-200:].mean()

        above_ma50 = current > ma_50
        ma50_above_ma200 = ma_50 > ma_200

        direction_ok = above_ma50 and ma50_above_ma200

        return {
            'direction_ok': direction_ok,
            'current': current,
            'ma_50': ma_50,
            'ma_200': ma_200,
            'above_ma50': above_ma50,
            'golden_cross': ma50_above_ma200,
            'reason': '시장 정배열' if direction_ok else '시장 약세'
        }

    def check_industry_strength(self, stock_sector, sector_performance):
        """
        산업군 강도 확인
        - 최근 3~6개월 수익률 상위 10~20% 산업군
        """
        if stock_sector not in sector_performance:
            return {'strong_sector': False, 'rank': None}

        sector_rank = sector_performance[stock_sector]['rank']
        total_sectors = len(sector_performance)

        # 상위 20% 이내
        top_20_pct = int(total_sectors * 0.2)
        strong = sector_rank <= top_20_pct

        return {
            'strong_sector': strong,
            'rank': sector_rank,
            'total': total_sectors,
            'percentile': (sector_rank / total_sectors) * 100,
            'performance': sector_performance[stock_sector]['return']
        }

    # ========== 2. 펀더멘털 필터 ==========

    def check_eps_growth(self, fundamental_data):
        """
        EPS 성장률 확인
        - 분기별 EPS 성장률 >= 25% (전년 동기 대비)
        - 최근 3분기 가속화 확인
        """
        if 'eps_growth_quarterly' not in fundamental_data:
            return {'strong_eps': False, 'growth': None}

        growth = fundamental_data['eps_growth_quarterly']

        # 25% 이상
        strong = growth >= 25

        # 가속화 확인 (최근 3분기)
        accelerating = False
        if 'eps_growth_history' in fundamental_data:
            history = fundamental_data['eps_growth_history']
            if len(history) >= 3:
                accelerating = history[-1] > history[-2] > history[-3]

        return {
            'strong_eps': strong,
            'growth': growth,
            'accelerating': accelerating,
            'bonus': 10 if accelerating else 0
        }

    def check_sales_growth(self, fundamental_data):
        """
        매출 성장률 확인
        - 최근 분기 >= 20% (전년 동기 대비)
        """
        if 'sales_growth_quarterly' not in fundamental_data:
            return {'strong_sales': False, 'growth': None}

        growth = fundamental_data['sales_growth_quarterly']
        strong = growth >= 20

        return {
            'strong_sales': strong,
            'growth': growth
        }

    def check_institutional_ownership(self, ownership_data):
        """
        기관/외국인 수급 확인
        - 최근 1개월 보유비중 증가
        """
        if 'recent_change' not in ownership_data:
            return {'increasing': False, 'change': 0}

        change = ownership_data['recent_change']
        increasing = change > 0

        return {
            'increasing': increasing,
            'change': change,
            'current': ownership_data.get('current', 0)
        }

    # ========== 3. 기술적 필터 (강화) ==========

    def check_moving_average_alignment(self, price_data):
        """
        이동평균선 정배열 확인
        현재가 > MA(50) > MA(150) > MA(200)
        MA(200) 우상향 1개월 이상
        """
        if len(price_data) < 200:
            return {'aligned': False, 'score': 0}

        current = price_data['Close'].iloc[-1]
        ma_50 = price_data['Close'].iloc[-50:].mean()
        ma_150 = price_data['Close'].iloc[-150:].mean()
        ma_200 = price_data['Close'].iloc[-200:].mean()

        # 정배열 확인
        aligned = (current > ma_50 > ma_150 > ma_200)

        # MA(200) 기울기 (1개월 전과 비교)
        ma_200_past = price_data['Close'].iloc[-220:-200].mean() if len(price_data) >= 220 else ma_200
        ma_200_rising = ma_200 > ma_200_past

        score = 0
        if current > ma_50:
            score += 25
        if ma_50 > ma_150:
            score += 25
        if ma_150 > ma_200:
            score += 25
        if ma_200_rising:
            score += 25

        return {
            'aligned': aligned and ma_200_rising,
            'score': score,
            'current': current,
            'ma_50': ma_50,
            'ma_150': ma_150,
            'ma_200': ma_200,
            'ma_200_rising': ma_200_rising
        }

    def check_52week_position(self, price_data):
        """
        52주 최저가 대비 위치
        - 최저가 대비 25~30% 이상 상승
        """
        if len(price_data) < 252:
            lookback = len(price_data)
        else:
            lookback = 252

        current = price_data['Close'].iloc[-1]
        low_52w = price_data['Low'].iloc[-lookback:].min()
        high_52w = price_data['High'].iloc[-lookback:].max()

        gain_from_low = ((current - low_52w) / low_52w) * 100 if low_52w > 0 else 0
        distance_from_high = ((high_52w - current) / high_52w) * 100

        # 25% 이상 상승, 고점 대비 25% 이내
        good_position = gain_from_low >= 25 and distance_from_high <= 25

        return {
            'good_position': good_position,
            'gain_from_low': gain_from_low,
            'distance_from_high': distance_from_high,
            'low_52w': low_52w,
            'high_52w': high_52w
        }

    def check_vcp_detailed_ryan(self, price_data):
        """
        VCP (Volatility Contraction Pattern) - David Ryan 버전
        - 베이스 내 고점 대비 저점 하락폭이 점진적 축소
        - 예: -20% → -10% → -5%
        """
        if len(price_data) < 120:
            return {'vcp': False, 'contractions': []}

        # 최근 4개 구간으로 나누기
        periods = [60, 40, 25, 15]
        contractions = []

        for period in periods:
            if len(price_data) >= period:
                segment = price_data.iloc[-period:]
                high = segment['High'].max()
                low = segment['Low'].min()
                contraction_pct = ((high - low) / high) * 100
                contractions.append(contraction_pct)

        # 수축 패턴 확인
        if len(contractions) >= 3:
            is_contracting = all(contractions[i] > contractions[i+1]
                                for i in range(len(contractions)-1))

            if is_contracting and contractions[-1] < 8:
                return {
                    'vcp': True,
                    'contractions': contractions,
                    'final_tightness': contractions[-1],
                    'quality': 'Excellent' if contractions[-1] < 5 else 'Good'
                }

        return {'vcp': False, 'contractions': contractions}

    # ========== 4. 거래량 분석 (강화) ==========

    def check_volume_dry_up_complete(self, price_data, lookback=10):
        """
        VDU (Volume Dry-Up) 완전 구현
        - 돌파 직전 며칠간 거래량이 50일 평균 대비 50% 미만
        """
        if len(price_data) < 60:
            return {'vdu': False, 'ratio': 100}

        recent_volume = price_data['Volume'].iloc[-lookback:].mean()
        avg_volume_50d = price_data['Volume'].iloc[-50:].mean()

        if avg_volume_50d == 0:
            return {'vdu': False, 'ratio': 100}

        ratio = (recent_volume / avg_volume_50d) * 100

        # 50% 미만이면 VDU 신호
        vdu = ratio < 50

        return {
            'vdu': vdu,
            'ratio': ratio,
            'recent_volume': recent_volume,
            'avg_volume_50d': avg_volume_50d,
            'signal': 'Strong VDU' if vdu else 'Normal'
        }

    def check_pivot_breakout_volume(self, price_data, pivot_price):
        """
        피벗 돌파 거래량 확인
        - 돌파 시점 거래량이 평균 대비 +50~100% 이상
        """
        if len(price_data) < 50:
            return {'volume_surge': False, 'ratio': 0}

        current_price = price_data['Close'].iloc[-1]
        current_volume = price_data['Volume'].iloc[-1]
        avg_volume = price_data['Volume'].iloc[-50:].mean()

        # 피벗 근처 (1% 이내)
        near_pivot = abs((current_price - pivot_price) / pivot_price) <= 0.01

        if avg_volume == 0:
            return {'volume_surge': False, 'ratio': 0}

        volume_ratio = (current_volume / avg_volume)

        # 1.5배 이상 (50% 증가)
        volume_surge = near_pivot and volume_ratio >= 1.5

        return {
            'volume_surge': volume_surge,
            'ratio': volume_ratio,
            'current_volume': current_volume,
            'avg_volume': avg_volume,
            'near_pivot': near_pivot
        }

    # ========== 5. 리스크 관리 ==========

    def calculate_entry_and_stops(self, price_data, pivot_price):
        """
        진입가 및 손절가 계산
        - 진입: 피벗 돌파 (pivot + 0.1%)
        - 손절: 진입가 -7%
        - 추가매수: 진입가 +2~3%
        """
        entry_price = pivot_price * 1.001  # 피벗 + 0.1%
        stop_loss = entry_price * 0.93     # -7%
        add_on_price_1 = entry_price * 1.02  # +2%
        add_on_price_2 = entry_price * 1.03  # +3%

        current_price = price_data['Close'].iloc[-1]
        risk_pct = ((entry_price - stop_loss) / entry_price) * 100
        potential_reward = ((pivot_price * 1.20 - entry_price) / entry_price) * 100  # 20% 목표

        return {
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'add_on_1': add_on_price_1,
            'add_on_2': add_on_price_2,
            'risk_pct': risk_pct,
            'reward_potential': potential_reward,
            'risk_reward_ratio': potential_reward / risk_pct if risk_pct > 0 else 0,
            'current_price': current_price
        }

    # ========== 종합 진입 신호 ==========

    def david_ryan_complete_signal(self, price_data, rs_rating, fundamental_data=None):
        """
        David Ryan 완전 진입 신호

        필수 조건:
        1. RS >= 90
        2. 이동평균선 정배열
        3. 52주 포지션 양호
        4. VCP 또는 VDU
        5. 피벗 돌파 + 거래량 증가
        """
        signal = {
            'entry_signal': False,
            'signal_strength': 0,
            'entry_price': 0,
            'stop_loss': 0,
            'add_on_prices': [],
            'reasons': [],
            'warnings': [],
            # 개별 체크 결과 플래그 (대시보드용)
            'rs_check': False,
            'ma_alignment': False,
            'year_position_check': False,
            'vcp_detected': False,
            'vdu_detected': False,
            'pivot_breakout': False,
            'volume_surge': False
        }

        if len(price_data) < 200:
            signal['reasons'].append('데이터 부족')
            return signal

        total_score = 0

        # 1. RS Rating (필수 90+)
        if rs_rating < 90:
            signal['reasons'].append(f'RS {rs_rating} < 90 (부적격)')
            signal['rs_check'] = False
            return signal

        signal['rs_check'] = True
        if rs_rating >= 95:
            signal['reasons'].append(f'⭐ RS {rs_rating} (최상위 5%)')
            total_score += 25
        else:
            signal['reasons'].append(f'✓ RS {rs_rating} (상위 10%)')
            total_score += 20

        # 2. 이동평균선 정배열 (필수)
        ma_align = self.check_moving_average_alignment(price_data)
        signal['ma_alignment'] = ma_align['aligned']
        if not ma_align['aligned']:
            signal['reasons'].append('✗ 이동평균선 정배열 미충족')
            signal['warnings'].append('정배열 형성 대기 필요')
            return signal

        signal['reasons'].append(f"✓ 이동평균선 정배열 완벽 ({ma_align['score']}점)")
        total_score += ma_align['score']

        # 3. 52주 포지션
        pos_52w = self.check_52week_position(price_data)
        signal['year_position_check'] = pos_52w['good_position']
        if pos_52w['good_position']:
            signal['reasons'].append(
                f"✓ 52주 포지션 양호 (저점 대비 +{pos_52w['gain_from_low']:.1f}%, 고점 대비 -{pos_52w['distance_from_high']:.1f}%)"
            )
            total_score += 15
        else:
            signal['warnings'].append(
                f"주의: 52주 포지션 ({pos_52w['gain_from_low']:.1f}% 상승)"
            )

        # 4. VCP 패턴
        vcp = self.check_vcp_detailed_ryan(price_data)
        signal['vcp_detected'] = vcp['vcp']
        if vcp['vcp']:
            signal['reasons'].append(
                f"⭐ VCP {vcp['quality']} (변동성 {vcp['final_tightness']:.1f}%)"
            )
            total_score += 20

        # 5. Volume Dry-Up
        vdu = self.check_volume_dry_up_complete(price_data)
        signal['vdu_detected'] = vdu['vdu']
        if vdu['vdu']:
            signal['reasons'].append(f"⭐ VDU 확인 (거래량 {vdu['ratio']:.0f}%)")
            total_score += 15

        # 6. 피벗 포인트 및 돌파
        pivot = price_data['High'].iloc[-30:].max()
        current_price = price_data['Close'].iloc[-1]
        distance_from_pivot = ((pivot - current_price) / pivot) * 100

        if distance_from_pivot <= 1:
            signal['pivot_breakout'] = True
            signal['reasons'].append(f'✓ 피벗 근접 ({distance_from_pivot:.1f}%)')
            total_score += 20

            # 거래량 돌파 확인
            vol_breakout = self.check_pivot_breakout_volume(price_data, pivot)
            signal['volume_surge'] = vol_breakout['volume_surge']
            if vol_breakout['volume_surge']:
                signal['reasons'].append(f"⭐ 거래량 폭증 ({vol_breakout['ratio']:.1f}배)")
                total_score += 25
            elif vol_breakout['ratio'] >= 1.3:
                signal['reasons'].append(f"✓ 거래량 증가 ({vol_breakout['ratio']:.1f}배)")
                total_score += 15
        else:
            signal['pivot_breakout'] = False
            signal['volume_surge'] = False

        # 7. 펀더멘털 (보너스)
        if fundamental_data:
            eps = self.check_eps_growth(fundamental_data)
            if eps['strong_eps']:
                bonus = '⭐' if eps['accelerating'] else '✓'
                signal['reasons'].append(f"{bonus} EPS 성장 {eps['growth']:.1f}%")
                total_score += 10 + eps['bonus']

            sales = self.check_sales_growth(fundamental_data)
            if sales['strong_sales']:
                signal['reasons'].append(f"✓ 매출 성장 {sales['growth']:.1f}%")
                total_score += 10

        # 진입가/손절가 계산
        risk_mgmt = self.calculate_entry_and_stops(price_data, pivot)
        signal['entry_price'] = risk_mgmt['entry_price']
        signal['stop_loss'] = risk_mgmt['stop_loss']
        signal['add_on_prices'] = [risk_mgmt['add_on_1'], risk_mgmt['add_on_2']]
        signal['risk_reward_ratio'] = risk_mgmt['risk_reward_ratio']

        # 최종 점수
        signal['signal_strength'] = total_score

        # 진입 신호 (120점 이상 = 매우 강력)
        if total_score >= 120:
            signal['entry_signal'] = True
            signal['reasons'].insert(0, f'🎯 강력한 진입 신호 (점수: {total_score})')
        elif total_score >= 100:
            signal['entry_signal'] = True
            signal['reasons'].insert(0, f'✓ 진입 가능 (점수: {total_score})')
        else:
            signal['reasons'].insert(0, f'⏳ 진입 대기 (점수: {total_score})')

        return signal


if __name__ == "__main__":
    print("David Ryan 완전 전략 구현...")
