"""
2025년 매주 금요일 백테스팅
각 금요일마다 David Ryan + Minervini 점수 추적
"""

import pandas as pd
from datetime import datetime, timedelta
import os
import webbrowser
from data_collector import StockDataCollector
from rs_calculator import RSCalculator
from david_ryan_complete import DavidRyanComplete
from advanced_entry_signals import AdvancedEntryAnalyzer
from generate_backtest_dashboard import generate_backtest_dashboard

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
WEB_DIR = os.path.join(PROJECT_ROOT, "web")


def get_fridays_2025():
    """2025년 모든 금요일 날짜 리스트"""
    fridays = []
    current = datetime(2025, 1, 3)  # 2025년 1월 3일 (첫 금요일)
    end_date = datetime.now()  # 오늘까지

    while current <= end_date:
        fridays.append(current)
        current += timedelta(days=7)

    return fridays


def backtest_stock_on_date(ticker, price_data, target_date, collector):
    """특정 날짜에 종목 분석"""
    try:
        # 해당 날짜까지의 데이터만 사용
        df = price_data[price_data.index <= target_date]

        if len(df) < 200:  # 최소 200일 데이터 필요
            return None

        # RS Rating 계산
        calculator = RSCalculator()

        # 단일 종목용 RS 계산 (간이 버전)
        recent_data = df.tail(252)
        if len(recent_data) < 60:
            return None

        # 가중치 RS 계산
        perf_3m = (recent_data['Close'].iloc[-1] / recent_data['Close'].iloc[-60] - 1) * 100 if len(recent_data) >= 60 else 0
        perf_6m = (recent_data['Close'].iloc[-1] / recent_data['Close'].iloc[-120] - 1) * 100 if len(recent_data) >= 120 else 0
        perf_9m = (recent_data['Close'].iloc[-1] / recent_data['Close'].iloc[-180] - 1) * 100 if len(recent_data) >= 180 else 0
        perf_12m = (recent_data['Close'].iloc[-1] / recent_data['Close'].iloc[-240] - 1) * 100 if len(recent_data) >= 240 else 0

        rs_score = (perf_3m * 0.4) + (perf_6m * 0.2) + (perf_9m * 0.2) + (perf_12m * 0.2)

        # 백분위 변환 (간이: 절대값 기준)
        if rs_score > 50:
            rs_rating = 90
        elif rs_score > 30:
            rs_rating = 80
        elif rs_score > 15:
            rs_rating = 70
        else:
            rs_rating = int(max(50, min(99, 50 + rs_score)))

        # David Ryan 분석
        ryan_analyzer = DavidRyanComplete()
        ryan_signal = ryan_analyzer.david_ryan_complete_signal(df, rs_rating)

        # Minervini 분석
        minervini_analyzer = AdvancedEntryAnalyzer()
        minervini_signal = minervini_analyzer.mark_minervini_advanced_signal(df, rs_rating)

        # 현재가
        current_price = df['Close'].iloc[-1]

        return {
            'date': target_date,
            'price': current_price,
            'rs_rating': rs_rating,
            'ryan_score': ryan_signal['signal_strength'],
            'ryan_signal': ryan_signal['entry_signal'],
            'ryan_entry': ryan_signal['entry_price'],
            'ryan_stop': ryan_signal['stop_loss'],
            'minervini_score': minervini_signal['signal_strength'],
            'minervini_signal': minervini_signal['entry_signal'],
            'minervini_entry': minervini_signal['entry_price']
        }

    except Exception as e:
        print(f"[에러] {ticker} {target_date.strftime('%Y-%m-%d')} 분석 실패: {e}")
        return None


def run_backtest(tickers, output_file='backtest_results.xlsx'):
    """백테스팅 실행"""
    print("="*100)
    print("          2025년 매주 금요일 백테스팅")
    print("="*100)

    fridays = get_fridays_2025()
    print(f"\n백테스팅 기간: {fridays[0].strftime('%Y-%m-%d')} ~ {fridays[-1].strftime('%Y-%m-%d')}")
    print(f"총 {len(fridays)}주 분석\n")

    collector = StockDataCollector()
    all_results = []

    for ticker in tickers:
        print(f"\n[분석 시작] {ticker}")

        # 전체 가격 데이터 수집 (2024년부터)
        try:
            start_date = (datetime.now() - timedelta(days=500)).strftime('%Y-%m-%d')
            price_data = collector.get_stock_price_data(ticker, start_date)

            if price_data is None or len(price_data) < 200:
                print(f"[스킵] {ticker} - 데이터 부족")
                continue

            # 각 금요일마다 분석
            for friday in fridays:
                result = backtest_stock_on_date(ticker, price_data, friday, collector)

                if result:
                    result['ticker'] = ticker
                    all_results.append(result)

                    status = "✓ 진입신호" if result['ryan_signal'] or result['minervini_signal'] else "대기"
                    print(f"  {friday.strftime('%Y-%m-%d')}: RS {result['rs_rating']} | Ryan {result['ryan_score']}점 | Minervini {result['minervini_score']}점 - {status}")

        except Exception as e:
            print(f"[에러] {ticker} 데이터 수집 실패: {e}")
            continue

    # 결과 저장
    if all_results:
        df = pd.DataFrame(all_results)

        # 날짜순 정렬
        df = df.sort_values(['ticker', 'date']).reset_index(drop=True)

        # 현재가 대비 수익률 계산
        current_prices = {}
        for ticker in df['ticker'].unique():
            ticker_data = df[df['ticker'] == ticker]
            if len(ticker_data) > 0:
                current_prices[ticker] = ticker_data['price'].iloc[-1]

        df['current_price'] = df['ticker'].map(current_prices)
        df['return_pct'] = ((df['current_price'] - df['price']) / df['price'] * 100).round(2)

        # 엑셀 저장
        output_path = os.path.join('results', output_file)
        os.makedirs('results', exist_ok=True)

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 전체 데이터
            df.to_excel(writer, sheet_name='전체백테스팅', index=False)

            # 종목별 시트
            for ticker in df['ticker'].unique():
                ticker_df = df[df['ticker'] == ticker].copy()
                ticker_df.to_excel(writer, sheet_name=ticker[:31], index=False)

        print(f"\n[저장 완료] {output_path}")
        print(f"총 {len(all_results)}개 데이터 포인트 생성")

        # 요약 통계
        print("\n[요약 통계]")
        print(f"  분석 종목 수: {df['ticker'].nunique()}")
        print(f"  평균 RS Rating: {df['rs_rating'].mean():.1f}")
        print(f"  David Ryan 진입신호: {df['ryan_signal'].sum()}회")
        print(f"  Minervini 진입신호: {df['minervini_signal'].sum()}회")
        print(f"  평균 수익률: {df['return_pct'].mean():.2f}%")

        # 웹 대시보드 생성
        print("\n[웹 대시보드 생성]")
        os.makedirs(WEB_DIR, exist_ok=True)
        dashboard_file = generate_backtest_dashboard(
            df,
            os.path.join(WEB_DIR, 'backtest_dashboard.html')
        )

        # 브라우저로 열기
        abs_path = os.path.abspath(dashboard_file)
        print(f"대시보드 열기: {abs_path}")
        webbrowser.open('file://' + abs_path)

        return df
    else:
        print("\n[실패] 백테스팅 결과 없음")
        return None


if __name__ == "__main__":
    # 테스트용 종목 리스트
    test_tickers = ['005930', '000660', '035720', '005380', '051910']  # 삼성전자, SK하이닉스, 카카오, 현대차, LG화학

    run_backtest(test_tickers)
