"""
고급 진입 시점 분석 모듈
David Ryan과 Mark Minervini의 정교한 전략 구현
"""

import pandas as pd
import numpy as np
from entry_signals import EntrySignalAnalyzer


class AdvancedEntryAnalyzer(EntrySignalAnalyzer):
    def __init__(self):
        """고급 진입 분석기 초기화"""
        super().__init__()

    # ========== David Ryan 진입 전략 ==========

    def check_high_tight_flag(self, price_data):
        """
        High Tight Flag 패턴 확인 (David Ryan 선호 패턴)

        조건:
        - 8주(40일) 이내 100% 이상 상승
        - 3-5주(15-25일) 동안 10-25% 조정
        - 조정 후 피봇 근접
        """
        if len(price_data) < 60:
            return {'pattern': False, 'strength': 0}

        # 최근 40일 수익률
        price_40d_ago = price_data['Close'].iloc[-40]
        current_price = price_data['Close'].iloc[-1]
        gain_40d = ((current_price - price_40d_ago) / price_40d_ago) * 100

        if gain_40d >= 100:  # 100% 이상 상승
            # 최근 15-25일 조정 확인
            recent_high = price_data['High'].iloc[-25:].max()
            recent_low = price_data['Low'].iloc[-15:].min()
            correction = ((recent_high - recent_low) / recent_high) * 100

            if 10 <= correction <= 25:
                # 현재가가 최근 고점 근처 (15% 이내)
                if current_price >= recent_high * 0.85:
                    return {
                        'pattern': True,
                        'strength': 100,  # 가장 강력한 패턴
                        'gain': gain_40d,
                        'correction': correction,
                        'pivot': recent_high
                    }

        return {'pattern': False, 'strength': 0}

    def check_base_quality(self, price_data, min_weeks=5):
        """
        베이스 품질 평가 (David Ryan)

        조건:
        - 최소 5주(25일) 이상 횡보
        - 베이스 깊이 12-35%
        - 타이트한 가격 흐름
        """
        min_days = min_weeks * 5

        if len(price_data) < min_days:
            return {'quality': 'Poor', 'score': 0, 'depth': 0}

        base_data = price_data.iloc[-min_days:]

        high = base_data['High'].max()
        low = base_data['Low'].min()
        depth = ((high - low) / high) * 100

        # 베이스 깊이 평가
        if 15 <= depth <= 25:
            quality = 'Excellent'
            score = 90
        elif 12 <= depth <= 35:
            quality = 'Good'
            score = 70
        elif depth < 12:
            quality = 'Too Shallow'
            score = 30
        else:
            quality = 'Too Deep'
            score = 20

        # 타이트니스 평가 (최근 10일 변동폭)
        recent_range = ((base_data['High'].iloc[-10:].max() -
                        base_data['Low'].iloc[-10:].min()) /
                       base_data['Low'].iloc[-10:].min() * 100)

        if recent_range < 5:
            score += 10  # 보너스 점수

        return {
            'quality': quality,
            'score': score,
            'depth': depth,
            'tightness': recent_range,
            'weeks': len(base_data) / 5
        }

    def check_volume_dryup(self, price_data, lookback=10):
        """
        거래량 건조 확인 (David Ryan - 돌파 직전 신호)

        베이스 형성 중 거래량이 감소하면 좋은 신호
        """
        if len(price_data) < lookback * 2:
            return {'dryup': False, 'ratio': 0}

        recent_volume = price_data['Volume'].iloc[-lookback:].mean()
        previous_volume = price_data['Volume'].iloc[-lookback*2:-lookback].mean()

        if previous_volume == 0:
            return {'dryup': False, 'ratio': 0}

        ratio = (recent_volume / previous_volume) * 100

        # 거래량이 30% 이상 감소
        if ratio < 70:
            return {
                'dryup': True,
                'ratio': ratio,
                'signal': 'Strong'  # 돌파 임박 신호
            }

        return {'dryup': False, 'ratio': ratio}

    def david_ryan_entry_signal(self, price_data, rs_rating):
        """
        David Ryan 종합 진입 신호

        핵심:
        1. RS Rating 90+ (가능하면 95+)
        2. High Tight Flag 또는 고품질 베이스
        3. 피봇 포인트 돌파
        4. 거래량 40-50% 증가 (과도함 경계)
        5. 거래량 건조 후 폭발
        """
        signal = {
            'entry_signal': False,
            'signal_strength': 0,
            'entry_price': 0,
            'stop_loss': 0,
            'pattern_type': None,
            'reasons': []
        }

        if len(price_data) < 60:
            return signal

        current_price = price_data['Close'].iloc[-1]

        # 1. RS Rating (David Ryan은 90+ 선호)
        if rs_rating < 90:
            signal['reasons'].append(f'RS Rating {rs_rating} (90 미만, 부족)')
            return signal

        if rs_rating >= 95:
            signal['reasons'].append(f'RS Rating {rs_rating} (최상위 95+)')
            signal['signal_strength'] += 30
        else:
            signal['reasons'].append(f'RS Rating {rs_rating} (우수 90+)')
            signal['signal_strength'] += 20

        # 2. High Tight Flag 확인 (최우선)
        htf = self.check_high_tight_flag(price_data)
        if htf['pattern']:
            signal['reasons'].append(f"High Tight Flag ({htf['gain']:.0f}% 상승 후 {htf['correction']:.1f}% 조정)")
            signal['signal_strength'] += 50
            signal['pattern_type'] = 'High Tight Flag'
            signal['entry_price'] = htf['pivot'] * 1.001
            signal['stop_loss'] = htf['pivot'] * 0.93

        # 3. 베이스 품질 평가
        base = self.check_base_quality(price_data)
        if base['score'] >= 70:
            signal['reasons'].append(f"베이스 품질 {base['quality']} (깊이 {base['depth']:.1f}%, 타이트니스 {base['tightness']:.1f}%)")
            signal['signal_strength'] += 25

        # 4. 거래량 건조 확인
        dryup = self.check_volume_dryup(price_data)
        if dryup['dryup']:
            signal['reasons'].append(f"거래량 건조 (기준 대비 {dryup['ratio']:.0f}%)")
            signal['signal_strength'] += 15

        # 5. 피봇 포인트 근접
        pivot = price_data['High'].iloc[-10:].max()
        distance_from_pivot = ((pivot - current_price) / pivot) * 100

        if distance_from_pivot <= 1:  # 1% 이내
            signal['reasons'].append('피봇 포인트 1% 이내')
            signal['signal_strength'] += 20
            if signal['entry_price'] == 0:
                signal['entry_price'] = pivot * 1.001
                signal['stop_loss'] = pivot * 0.925  # 7.5% 손절

        # 6. 거래량 돌파 확인
        volume_bo = self.check_volume_breakout(price_data, threshold=1.4)
        if volume_bo['breakout']:
            # 과도한 거래량은 경고
            if volume_bo['volume_ratio'] > 2.0:
                signal['reasons'].append(f"거래량 {volume_bo['volume_ratio']:.1f}배 (과도함 주의)")
            else:
                signal['reasons'].append(f"거래량 {volume_bo['volume_ratio']:.1f}배 (적절)")
                signal['signal_strength'] += 15

        # 기본 진입가/손절가 설정
        if signal['entry_price'] == 0:
            signal['entry_price'] = current_price * 1.02
            signal['stop_loss'] = current_price * 0.925

        # 진입 신호 판정 (85점 이상)
        if signal['signal_strength'] >= 85:
            signal['entry_signal'] = True

        return signal

    # ========== Mark Minervini 개선된 VCP 패턴 ==========

    def check_vcp_detailed(self, price_data, lookback=120):
        """
        VCP (Volatility Contraction Pattern) 정교한 분석

        조건:
        - 최소 3회 이상 조정
        - 각 조정의 크기가 점진적으로 축소
        - 마지막 조정이 가장 타이트 (5% 미만)
        - T1, T2, T3, T4 수축 단계
        """
        if len(price_data) < lookback:
            return {'vcp': False, 'contractions': [], 'quality': 'None'}

        # 고점 찾기 (피크)
        highs = price_data['High'].rolling(window=5, center=True).max()
        is_peak = (price_data['High'] == highs)

        # 저점 찾기 (밸리)
        lows = price_data['Low'].rolling(window=5, center=True).min()
        is_valley = (price_data['Low'] == lows)

        # 최근 조정 구간 분석
        contractions = []

        # 간단 버전: 기간별 변동폭 계산
        periods = [60, 40, 25, 15]  # 점점 짧아지는 기간

        for period in periods:
            if len(price_data) >= period:
                segment = price_data.iloc[-period:]
                high = segment['High'].max()
                low = segment['Low'].min()
                contraction = ((high - low) / high) * 100
                contractions.append(contraction)

        # VCP 조건 확인
        if len(contractions) >= 3:
            # 수축 패턴 확인
            is_contracting = all(contractions[i] > contractions[i+1]
                                for i in range(len(contractions)-1))

            last_contraction = contractions[-1]

            if is_contracting and last_contraction < 8:
                # 품질 평가
                if last_contraction < 4:
                    quality = 'Excellent'
                    score = 95
                elif last_contraction < 6:
                    quality = 'Good'
                    score = 80
                else:
                    quality = 'Fair'
                    score = 65

                return {
                    'vcp': True,
                    'contractions': contractions,
                    'quality': quality,
                    'score': score,
                    'tightness': last_contraction,
                    'stages': len(contractions)
                }

        return {'vcp': False, 'contractions': contractions, 'quality': 'None'}

    def check_trend_template_detailed(self, price_data):
        """
        Mark Minervini 트렌드 템플릿 8가지 조건 상세 체크
        """
        if len(price_data) < 200:
            return {'stage_2': False, 'score': 0, 'details': []}

        current_price = price_data['Close'].iloc[-1]

        # 이동평균선 계산
        ma_50 = price_data['Close'].iloc[-50:].mean()
        ma_150 = price_data['Close'].iloc[-150:].mean()
        ma_200 = price_data['Close'].iloc[-200:].mean()

        # 200일 이평선 기울기 (1개월 전과 비교)
        ma_200_past = price_data['Close'].iloc[-220:-200].mean() if len(price_data) >= 220 else ma_200
        ma_200_slope = ((ma_200 - ma_200_past) / ma_200_past) * 100

        # 52주 최고/최저
        high_52w = price_data['High'].iloc[-252:].max() if len(price_data) >= 252 else price_data['High'].max()
        low_52w = price_data['Low'].iloc[-252:].min() if len(price_data) >= 252 else price_data['Low'].min()

        score = 0
        details = []

        # 8가지 조건 체크
        checks = {
            '1. 주가 > 150일 이평': current_price > ma_150,
            '2. 주가 > 200일 이평': current_price > ma_200,
            '3. 150일 > 200일 이평': ma_150 > ma_200,
            '4. 200일 이평 상승': ma_200_slope > 0,
            '5. 50일 > 150일 이평': ma_50 > ma_150,
            '6. 주가 > 50일 이평': current_price > ma_50,
            '7. 52주 최저 대비 +30%': ((current_price - low_52w) / low_52w * 100) >= 30 if low_52w > 0 else False,
            '8. 52주 최고 대비 25% 이내': ((high_52w - current_price) / high_52w * 100) <= 25
        }

        for desc, passed in checks.items():
            if passed:
                details.append(f'{desc} OK')
                score += 12.5
            else:
                details.append(f'{desc} X')

        return {
            'stage_2': score >= 87.5,  # 7개 이상 통과
            'score': score,
            'details': details,
            'checks_passed': sum(checks.values()),
            'ma_50': ma_50,
            'ma_150': ma_150,
            'ma_200': ma_200
        }

    def mark_minervini_advanced_signal(self, price_data, rs_rating):
        """
        Mark Minervini 고급 진입 신호 (VCP + 트렌드 템플릿)
        """
        signal = {
            'entry_signal': False,
            'signal_strength': 0,
            'entry_price': 0,
            'stop_loss': 0,
            'pattern_type': None,
            'reasons': [],
            # 트렌드 템플릿 개별 체크 (대시보드용)
            'trend_template': {
                'above_150_200': False,
                'ma150_above_200': False,
                'ma200_rising': False,
                'ma50_above_150_200': False,
                'above_50': False,
                'above_52w_low': False,
                'near_52w_high': False,
                'rs_strong': False
            },
            # 추가 진입 체크 (대시보드용)
            'minervini_checks': {
                'stage_2': False,
                'rs_ok': False,
                'vcp_detected': False,
                'pivot_near': False,
                'strength_ok': False
            }
        }

        if len(price_data) < 200:
            return signal

        current_price = price_data['Close'].iloc[-1]

        # 1. 트렌드 템플릿 (필수!)
        template = self.check_trend_template_detailed(price_data)

        # 개별 체크 플래그 설정
        ma_50 = template['ma_50']
        ma_150 = template['ma_150']
        ma_200 = template['ma_200']

        # 200일 이평선 기울기 계산
        ma_200_past = price_data['Close'].iloc[-220:-200].mean() if len(price_data) >= 220 else ma_200
        ma_200_slope = ((ma_200 - ma_200_past) / ma_200_past) * 100

        # 52주 최고/최저
        high_52w = price_data['High'].iloc[-252:].max() if len(price_data) >= 252 else price_data['High'].max()
        low_52w = price_data['Low'].iloc[-252:].min() if len(price_data) >= 252 else price_data['Low'].min()

        signal['trend_template']['above_150_200'] = bool((current_price > ma_150) and (current_price > ma_200))
        signal['trend_template']['ma150_above_200'] = bool(ma_150 > ma_200)
        signal['trend_template']['ma200_rising'] = bool(ma_200_slope > 0)
        signal['trend_template']['ma50_above_150_200'] = bool((ma_50 > ma_150) and (ma_50 > ma_200))
        signal['trend_template']['above_50'] = bool(current_price > ma_50)
        signal['trend_template']['above_52w_low'] = bool(((current_price - low_52w) / low_52w * 100) >= 30) if low_52w > 0 else False
        signal['trend_template']['near_52w_high'] = bool(((high_52w - current_price) / high_52w * 100) <= 25)
        signal['trend_template']['rs_strong'] = bool(rs_rating >= 70)

        signal['reasons'].append(f"트렌드 템플릿 {template['checks_passed']}/8")
        signal['minervini_checks']['stage_2'] = bool(template['stage_2'])

        if not template['stage_2']:
            signal['reasons'].append('Stage 2 미충족')
            return signal

        signal['signal_strength'] += 40

        # 2. RS Rating
        signal['minervini_checks']['rs_ok'] = bool(rs_rating >= 80)
        if rs_rating >= 95:
            signal['reasons'].append(f'RS {rs_rating} (최상위)')
            signal['signal_strength'] += 30
        elif rs_rating >= 90:
            signal['reasons'].append(f'RS {rs_rating} (우수)')
            signal['signal_strength'] += 25
        elif rs_rating >= 80:
            signal['reasons'].append(f'RS {rs_rating} (양호)')
            signal['signal_strength'] += 15
        else:
            return signal

        # 3. VCP 패턴
        vcp = self.check_vcp_detailed(price_data)
        signal['minervini_checks']['vcp_detected'] = bool(vcp['vcp'])
        if vcp['vcp']:
            signal['reasons'].append(f"VCP {vcp['quality']} ({vcp['stages']}단계, 타이트 {vcp['tightness']:.1f}%)")
            signal['signal_strength'] += vcp['score'] // 3  # 최대 30점
            signal['pattern_type'] = f"VCP-{vcp['stages']}"

        # 4. 피봇 포인트
        pivot = price_data['High'].iloc[-15:].max()

        if current_price >= pivot * 0.99:
            signal['reasons'].append('피봇 근접/돌파')
            signal['signal_strength'] += 20
            signal['entry_price'] = pivot * 1.001
            signal['minervini_checks']['pivot_near'] = True
        else:
            signal['entry_price'] = pivot * 1.001

        # 5. 손절가 (50일 이평 또는 피봇 기준)
        stop_candidate = max(template['ma_50'], pivot * 0.92)
        signal['stop_loss'] = stop_candidate

        # 진입 신호 판정
        if signal['signal_strength'] >= 90:
            signal['entry_signal'] = True
            signal['minervini_checks']['strength_ok'] = True

        return signal


if __name__ == "__main__":
    print("고급 진입 신호 분석 모듈...")
