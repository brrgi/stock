"""
날짜별 백테스트 기능이 포함된 대시보드 생성
헤더에 날짜 선택 드롭다운 추가
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
from advanced_entry_signals import AdvancedEntryAnalyzer
from david_ryan_complete import DavidRyanComplete


def analyze_stock_details(ticker, price_data, rs_rating):
    """종목별 상세 분석"""
    ryan_analyzer = DavidRyanComplete()
    minervini_analyzer = AdvancedEntryAnalyzer()

    ryan_signal = ryan_analyzer.david_ryan_complete_signal(price_data, rs_rating)
    minervini_signal = minervini_analyzer.mark_minervini_advanced_signal(price_data, rs_rating)

    return {
        'ryan': ryan_signal,
        'minervini': minervini_signal
    }


def generate_dashboard_with_backtest_dates(backtest_df, price_data_dict, output_file='dashboard.html'):
    """
    날짜별 백테스트가 가능한 대시보드 생성

    Args:
        backtest_df: 백테스트 결과 DataFrame (date, ticker, price, ryan_signal 등 포함)
        price_data_dict: {ticker: DataFrame} 종목별 가격 데이터
        output_file: 출력 파일명
    """

    # 날짜별로 그룹화
    dates = sorted(backtest_df['date'].unique())
    date_strings = [pd.to_datetime(d).strftime('%Y-%m-%d') for d in dates]

    # 날짜별 데이터 준비
    timeline_data = {}
    all_chart_data = {}
    all_stock_analysis = {}

    for date in dates:
        date_str = pd.to_datetime(date).strftime('%Y-%m-%d')
        date_data = backtest_df[backtest_df['date'] == date].copy()

        # 진입 신호가 있는 종목만
        signals = date_data[
            (date_data['ryan_signal'] == True) |
            (date_data['minervini_signal'] == True)
        ].copy()

        # 종목 리스트 데이터
        stocks_list = []
        for _, row in signals.iterrows():
            ticker = row['ticker']
            stocks_list.append({
                'ticker': ticker,
                'rs_rating': int(row['rs_rating']),
                'ryan_score': int(row['ryan_score']),
                'minervini_score': int(row['minervini_score']),
                'ryan_signal': bool(row['ryan_signal']),
                'minervini_signal': bool(row['minervini_signal']),
                'price': float(row['price']),
                'current_price': float(row['current_price']),
                'return_pct': float(row.get('return_pct', 0))
            })

            # 차트 데이터와 분석 (종목별로 한 번만 처리)
            if ticker not in all_chart_data and ticker in price_data_dict:
                df = price_data_dict[ticker].tail(252).copy()

                # 이동평균선 계산
                ma_50 = df['Close'].rolling(50).mean()
                ma_150 = df['Close'].rolling(150).mean() if len(df) >= 150 else pd.Series([None] * len(df))
                ma_200 = df['Close'].rolling(200).mean() if len(df) >= 200 else pd.Series([None] * len(df))

                all_chart_data[ticker] = {
                    'dates': df.index.strftime('%Y-%m-%d').tolist(),
                    'open': [float(x) if pd.notna(x) else None for x in df['Open'].tolist()],
                    'high': [float(x) if pd.notna(x) else None for x in df['High'].tolist()],
                    'low': [float(x) if pd.notna(x) else None for x in df['Low'].tolist()],
                    'close': [float(x) if pd.notna(x) else None for x in df['Close'].tolist()],
                    'volume': [float(x) if pd.notna(x) else None for x in df['Volume'].tolist()],
                    'ma_50': [float(x) if pd.notna(x) else None for x in ma_50.tolist()],
                    'ma_150': [float(x) if pd.notna(x) else None for x in ma_150.tolist()],
                    'ma_200': [float(x) if pd.notna(x) else None for x in ma_200.tolist()]
                }

                # 분석 데이터
                all_stock_analysis[ticker] = analyze_stock_details(ticker, price_data_dict[ticker], row['rs_rating'])

        timeline_data[date_str] = {
            'total': len(date_data),
            'signals': len(signals),
            'stocks': stocks_list
        }

    # HTML 생성 시작
    html = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>David Ryan 진입 신호 대시보드 (날짜별)</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0e27;
            color: #d1d4dc;
            height: 100vh;
            overflow: hidden;
        }

        .container {
            display: flex;
            height: 100vh;
        }

        /* 왼쪽 패널 - 종목 리스트 */
        .left-panel {
            width: 350px;
            background: #131722;
            border-right: 1px solid #2a2e39;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .header h1 {
            font-size: 1.3em;
            margin-bottom: 10px;
            color: white;
        }

        .header .subtitle {
            font-size: 0.85em;
            opacity: 0.9;
            color: white;
            margin-bottom: 15px;
        }

        /* 날짜 선택 드롭다운 */
        .date-selector {
            margin-top: 15px;
        }

        .date-selector label {
            display: block;
            color: white;
            font-size: 0.9em;
            margin-bottom: 8px;
            font-weight: 600;
        }

        .date-selector select {
            width: 100%;
            padding: 10px 12px;
            background: rgba(255, 255, 255, 0.15);
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            color: white;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .date-selector select:hover {
            background: rgba(255, 255, 255, 0.25);
            border-color: rgba(255, 255, 255, 0.5);
        }

        .date-selector select:focus {
            outline: none;
            border-color: #ffd700;
            background: rgba(255, 255, 255, 0.2);
        }

        .date-selector option {
            background: #131722;
            color: white;
        }

        .stock-list {
            flex: 1;
            padding: 10px;
        }

        .stock-item {
            background: #1e222d;
            padding: 15px;
            margin-bottom: 8px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }

        .stock-item:hover {
            background: #2a2e39;
            border-left-color: #667eea;
        }

        .stock-item.active {
            background: #2a2e39;
            border-left-color: #667eea;
            box-shadow: 0 0 0 1px #667eea;
        }

        .stock-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .stock-name {
            font-size: 1.1em;
            font-weight: bold;
            color: #fff;
        }

        .stock-code {
            font-size: 0.85em;
            color: #787b86;
        }

        .rs-badge {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: bold;
            color: white;
        }

        .stock-signals {
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
        }

        .signal-badge {
            padding: 3px 8px;
            border-radius: 8px;
            font-size: 0.75em;
            font-weight: 600;
        }

        .signal-badge.ryan { background: #26a69a; color: white; }
        .signal-badge.minervini { background: #2962ff; color: white; }
        .signal-badge.both { background: #ffd700; color: #000; }

        .return-badge {
            padding: 3px 8px;
            border-radius: 8px;
            font-size: 0.75em;
            font-weight: 600;
        }

        .return-badge.positive { background: #26a69a; color: white; }
        .return-badge.negative { background: #ef5350; color: white; }

        /* 오른쪽 패널 - 상세 정보 */
        .right-panel {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }

        .detail-header {
            background: #131722;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
        }

        .detail-title {
            font-size: 2em;
            font-weight: bold;
            color: #fff;
            margin-bottom: 10px;
        }

        .detail-meta {
            display: flex;
            gap: 20px;
            align-items: center;
        }

        .meta-item {
            font-size: 0.95em;
            color: #787b86;
        }

        .meta-value {
            color: #d1d4dc;
            font-weight: 600;
        }

        .external-links {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }

        .external-link {
            padding: 8px 16px;
            background: #2a2e39;
            color: #d1d4dc;
            text-decoration: none;
            border-radius: 8px;
            font-size: 0.9em;
            font-weight: 600;
            transition: all 0.2s;
            border: 1px solid #2a2e39;
        }

        .external-link:hover {
            background: #667eea;
            border-color: #667eea;
            color: white;
        }

        /* 차트 영역 */
        .chart-section {
            background: #131722;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }

        .chart-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #2962ff;
            margin-bottom: 15px;
        }

        .combined-chart {
            position: relative;
            height: 500px;
        }

        /* 가격 정보 그리드 */
        .price-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .price-card {
            background: #131722;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 2px solid #2a2e39;
        }

        .price-label {
            color: #787b86;
            font-size: 0.85em;
            margin-bottom: 8px;
        }

        .price-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #fff;
        }

        .price-value.entry { color: #26a69a; }
        .price-value.stop { color: #ef5350; }
        .price-value.positive { color: #26a69a; }
        .price-value.negative { color: #ef5350; }

        /* 분석 섹션 */
        .analysis-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .analysis-box {
            background: #131722;
            padding: 20px;
            border-radius: 12px;
        }

        .analysis-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #2962ff;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .score-badge {
            background: #2a2e39;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 1.1em;
            font-weight: bold;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        .score-badge.excellent {
            background: linear-gradient(135deg, #26a69a 0%, #1de9b6 100%);
            color: white;
        }
        .score-badge.good {
            background: linear-gradient(135deg, #2962ff 0%, #448aff 100%);
            color: white;
        }
        .score-badge.warning {
            background: linear-gradient(135deg, #ff9800 0%, #ffb74d 100%);
            color: white;
        }

        .check-item {
            padding: 12px;
            margin-bottom: 10px;
            background: #1e222d;
            border-radius: 8px;
            border-left: 4px solid #2a2e39;
            font-size: 1em;
            line-height: 1.6;
        }

        .check-item.passed {
            border-left-color: #26a69a;
            background: rgba(38, 166, 154, 0.05);
        }
        .check-item.failed {
            border-left-color: #ef5350;
            background: rgba(239, 83, 80, 0.05);
        }

        .check-icon {
            display: inline-block;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            text-align: center;
            line-height: 24px;
            font-weight: bold;
            margin-right: 10px;
            font-size: 0.9em;
        }

        .check-icon.pass {
            background: #26a69a;
            color: white;
        }

        .check-icon.fail {
            background: #ef5350;
            color: white;
        }

        .check-desc {
            display: block;
            color: #787b86;
            font-size: 0.85em;
            margin-top: 5px;
            margin-left: 34px;
        }

        .empty-state {
            text-align: center;
            padding: 100px 20px;
            color: #787b86;
        }

        .empty-state h2 {
            font-size: 2em;
            margin-bottom: 10px;
        }

        @media (max-width: 1200px) {
            .analysis-section { grid-template-columns: 1fr; }
        }

        @media (max-width: 768px) {
            .container { flex-direction: column; }
            .left-panel { width: 100%; height: 40vh; }
            .right-panel { height: 60vh; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 왼쪽 패널 -->
        <div class="left-panel">
            <div class="header">
                <h1>🎯 David Ryan 진입 신호</h1>
                <div class="subtitle" id="header-subtitle">총 0개 종목 발견</div>

                <!-- 날짜 선택 드롭다운 -->
                <div class="date-selector">
                    <label for="date-select">📅 백테스트 날짜</label>
                    <select id="date-select" onchange="changeDate(this.value)">
                        <option value="">날짜를 선택하세요</option>
"""

    # 날짜 옵션 추가 (최신 날짜가 위로)
    for date_str in reversed(date_strings):
        signals_count = timeline_data[date_str]['signals']
        badge = f" ({signals_count}개 신호)" if signals_count > 0 else ""
        html += f'                        <option value="{date_str}">{date_str}{badge}</option>\n'

    html += """                    </select>
                </div>
            </div>
            <div class="stock-list" id="stock-list">
                <div class="empty-state">
                    <h2>📅</h2>
                    <p>위에서 날짜를 선택하세요</p>
                </div>
            </div>
        </div>

        <!-- 오른쪽 패널 -->
        <div class="right-panel">
            <div id="detail-content" class="empty-state">
                <h2>👈 종목을 선택하세요</h2>
                <p>왼쪽 목록에서 종목을 클릭하면 상세 분석을 볼 수 있습니다</p>
            </div>
        </div>
    </div>

    <script>
        const timelineData = """ + json.dumps(timeline_data, default=str) + """;
        const chartData = """ + json.dumps(all_chart_data, default=str) + """;
        const stockAnalysis = """ + json.dumps(all_stock_analysis, default=str) + """;

        let currentChart = null;
        let currentDate = null;

        // 날짜 변경
        function changeDate(dateStr) {
            if (!dateStr) return;

            currentDate = dateStr;
            const data = timelineData[dateStr];

            // 헤더 업데이트
            document.getElementById('header-subtitle').textContent =
                data.signals + '개 진입 신호 (총 ' + data.total + '개 분석)';

            // 종목 리스트 렌더링
            const stockList = document.getElementById('stock-list');
            if (data.stocks.length === 0) {
                stockList.innerHTML = '<div class="empty-state"><h2>🔍</h2><p>진입 신호 없음</p></div>';
                return;
            }

            stockList.innerHTML = '';
            data.stocks.forEach(stock => {
                const item = document.createElement('div');
                item.className = 'stock-item';
                item.onclick = () => showStock(stock.ticker, dateStr);
                item.setAttribute('data-ticker', stock.ticker);

                // 신호 배지
                let signals = '';
                if (stock.ryan_signal && stock.minervini_signal) {
                    signals = '<span class="signal-badge both">양쪽 모두 ⭐</span>';
                } else if (stock.ryan_signal) {
                    signals = '<span class="signal-badge ryan">Ryan</span>';
                } else if (stock.minervini_signal) {
                    signals = '<span class="signal-badge minervini">Minervini</span>';
                }

                // 수익률 배지
                const returnPct = stock.return_pct || 0;
                const returnClass = returnPct > 0 ? 'positive' : 'negative';
                const returnBadge = '<span class="return-badge ' + returnClass + '">' +
                    (returnPct > 0 ? '+' : '') + returnPct.toFixed(1) + '%</span>';

                item.innerHTML =
                    '<div class="stock-item-header">' +
                        '<div>' +
                            '<div class="stock-name">' + stock.ticker + '</div>' +
                            '<div class="stock-code">RS ' + stock.rs_rating + '</div>' +
                        '</div>' +
                        '<div class="rs-badge">RS ' + stock.rs_rating + '</div>' +
                    '</div>' +
                    '<div class="stock-signals">' + signals + ' ' + returnBadge + '</div>';

                stockList.appendChild(item);
            });
        }

        function showStock(ticker, entryDate) {
            // 활성화 표시
            document.querySelectorAll('.stock-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector('[data-ticker="' + ticker + '"]').classList.add('active');

            // 종목 데이터 찾기
            const dateData = timelineData[entryDate];
            const stock = dateData.stocks.find(s => s.ticker === ticker);
            if (!stock) return;

            const data = chartData[ticker];
            if (!data) return;

            const analysis = stockAnalysis[ticker];

            // 상세 화면 생성
            let html =
                '<div class="detail-header">' +
                    '<div class="detail-title">' + ticker + '</div>' +
                    '<div class="detail-meta">' +
                        '<div class="meta-item">진입일: <span class="meta-value">' + entryDate + '</span></div>' +
                        '<div class="meta-item">RS 등급: <span class="meta-value">' + stock.rs_rating + '</span></div>' +
                        '<div class="meta-item">진입가: <span class="meta-value">' + stock.price.toLocaleString() + '원</span></div>' +
                        '<div class="meta-item">현재가: <span class="meta-value">' + stock.current_price.toLocaleString() + '원</span></div>' +
                    '</div>' +
                    '<div class="external-links">' +
                        '<a href="https://www.tradingview.com/chart/?symbol=KRX:' + ticker + '" target="_blank" class="external-link">📈 TradingView에서 보기</a>' +
                        '<a href="https://finance.naver.com/item/main.naver?code=' + ticker + '" target="_blank" class="external-link">📊 네이버 증권에서 보기</a>' +
                    '</div>' +
                '</div>' +
                '<div class="chart-section">' +
                    '<div class="chart-title">📊 가격 & 거래량 차트</div>' +
                    '<div class="combined-chart"><canvas id="combined-chart"></canvas></div>' +
                '</div>' +
                '<div class="price-grid">' +
                    '<div class="price-card">' +
                        '<div class="price-label">진입가 (' + entryDate + ')</div>' +
                        '<div class="price-value entry">' + stock.price.toLocaleString() + '원</div>' +
                    '</div>' +
                    '<div class="price-card">' +
                        '<div class="price-label">현재가</div>' +
                        '<div class="price-value">' + stock.current_price.toLocaleString() + '원</div>' +
                    '</div>';

            const returnPct = stock.return_pct || 0;
            const returnClass = returnPct > 0 ? 'positive' : 'negative';
            html +=
                    '<div class="price-card">' +
                        '<div class="price-label">수익률</div>' +
                        '<div class="price-value ' + returnClass + '">' + (returnPct > 0 ? '+' : '') + returnPct.toFixed(2) + '%</div>' +
                    '</div>' +
                '</div>';

            // 분석 섹션
            html += '<div class="analysis-section">';

            // David Ryan 분석
            if (analysis && analysis.ryan) {
                const ryan = analysis.ryan;
                const scoreClass = stock.ryan_score >= 150 ? 'excellent' : stock.ryan_score >= 100 ? 'good' : 'warning';

                html +=
                    '<div class="analysis-box">' +
                        '<div class="analysis-title">🎯 David Ryan 완전 전략' +
                            '<span class="score-badge ' + scoreClass + '">' + stock.ryan_score + '점</span>' +
                        '</div>';

                const checks = [
                    { label: 'RS Rating ≥ 90', desc: '상대강도지수 90 이상: 전체 종목 중 상위 10% 성과', passed: ryan.rs_check || false },
                    { label: '이동평균선 정배열', desc: '현재가 > 50일선 > 150일선 > 200일선: 강한 상승추세', passed: ryan.ma_alignment || false },
                    { label: '52주 포지션 양호', desc: '현재가가 52주 최고가 대비 -15% 이내', passed: ryan.year_position_check || false },
                    { label: 'VCP 패턴', desc: '변동성 축소 패턴: 조정 폭이 점점 감소하며 베이스 형성', passed: ryan.vcp_detected || false },
                    { label: 'VDU (거래량 감소)', desc: '거래량 건조: 돌파 직전 거래량 감소', passed: ryan.vdu_detected || false },
                    { label: '피봇 돌파', desc: '베이스 패턴의 저항선을 상향 돌파', passed: ryan.pivot_breakout || false },
                    { label: '거래량 증가 확인', desc: '돌파 시 거래량이 50일 평균 대비 40% 이상 증가', passed: ryan.volume_surge || false }
                ];

                checks.forEach(check => {
                    const iconClass = check.passed ? 'pass' : 'fail';
                    const iconText = check.passed ? '⭕' : '❌';
                    const cssClass = check.passed ? 'passed' : 'failed';
                    html +=
                        '<div class="check-item ' + cssClass + '">' +
                            '<span class="check-icon ' + iconClass + '">' + iconText + '</span>' +
                            '<strong>' + check.label + '</strong>' +
                            '<span class="check-desc">' + check.desc + '</span>' +
                        '</div>';
                });

                html += '</div>';
            }

            // Minervini 분석
            if (analysis && analysis.minervini) {
                const minervini = analysis.minervini;
                const scoreClass = stock.minervini_score >= 80 ? 'excellent' : stock.minervini_score >= 60 ? 'good' : 'warning';

                html +=
                    '<div class="analysis-box">' +
                        '<div class="analysis-title">📈 Mark Minervini Trend Template' +
                            '<span class="score-badge ' + scoreClass + '">' + stock.minervini_score + '점</span>' +
                        '</div>';

                const template = minervini.trend_template || {};
                const checks = [
                    { label: '1. 현재가 > 150일/200일 이평', desc: '가격이 장기 이동평균선 위에서 거래', passed: template.above_150_200 || false },
                    { label: '2. 150일 이평 > 200일 이평', desc: '중기선이 장기선보다 위: 추세 전환 완료', passed: template.ma150_above_200 || false },
                    { label: '3. 200일 이평선 상승 중', desc: '장기 추세선이 상승: 지속 가능한 상승장', passed: template.ma200_rising || false },
                    { label: '4. 50일 이평 > 150일/200일 이평', desc: '단기선이 중장기선 위: 강한 모멘텀', passed: template.ma50_above_150_200 || false },
                    { label: '5. 현재가 > 50일 이평', desc: '단기 추세 상승 중', passed: template.above_50 || false },
                    { label: '6. 현재가 52주 최저가 대비 +30%', desc: '바닥에서 충분히 상승', passed: template.above_low_30pct || false },
                    { label: '7. 현재가 52주 최고가 대비 -25% 이내', desc: '고점 근처 거래', passed: template.near_high_25pct || false },
                    { label: '8. RS Rating ≥ 70', desc: '상위 30% 성과', passed: template.rs_strong || false }
                ];

                checks.forEach(check => {
                    const iconClass = check.passed ? 'pass' : 'fail';
                    const iconText = check.passed ? '⭕' : '❌';
                    const cssClass = check.passed ? 'passed' : 'failed';
                    html +=
                        '<div class="check-item ' + cssClass + '">' +
                            '<span class="check-icon ' + iconClass + '">' + iconText + '</span>' +
                            '<strong>' + check.label + '</strong>' +
                            '<span class="check-desc">' + check.desc + '</span>' +
                        '</div>';
                });

                html += '</div>';
            }

            html += '</div>';

            document.getElementById('detail-content').innerHTML = html;

            // 차트 그리기
            drawCombinedChart(data, ticker, entryDate);
        }

        function drawCombinedChart(data, ticker, entryDate) {
            if (currentChart) {
                currentChart.destroy();
            }

            // 진입 날짜 인덱스
            const entryIdx = data.dates.indexOf(entryDate);

            // 거래량 로그 스케일
            const maxVolume = Math.max(...data.volume.filter(v => v !== null && v > 0));
            const minVolume = Math.min(...data.volume.filter(v => v !== null && v > 0));
            const priceMax = Math.max(...data.high.filter(v => v !== null));
            const priceMin = Math.min(...data.low.filter(v => v !== null));
            const priceRange = priceMax - priceMin;

            const scaledVolume = data.volume.map(v => {
                if (!v || v <= 0) return priceMin;
                const logV = Math.log(v / minVolume + 1);
                const logMax = Math.log(maxVolume / minVolume + 1);
                return priceMin + (logV / logMax) * priceRange * 0.25;
            });

            // 차트 어노테이션
            const annotations = {};
            const analysis = stockAnalysis[ticker];

            if (analysis && analysis.ryan) {
                const ryan = analysis.ryan;

                // 진입 시점 표시
                if (entryIdx >= 0) {
                    const entryPrice = data.close[entryIdx];
                    annotations.entryLine = {
                        type: 'line',
                        xMin: entryIdx,
                        xMax: entryIdx,
                        borderColor: '#26a69a',
                        borderWidth: 3,
                        borderDash: [5, 5],
                        label: {
                            display: true,
                            content: '진입',
                            position: 'start',
                            backgroundColor: '#26a69a',
                            color: 'white'
                        }
                    };
                }
            }

            const ctx = document.getElementById('combined-chart');
            currentChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [
                        {
                            label: '거래량',
                            data: scaledVolume,
                            type: 'bar',
                            backgroundColor: data.volume.map((vol, idx) => {
                                if (idx === 0) return 'rgba(102, 126, 234, 0.25)';
                                return data.close[idx] >= data.close[idx-1]
                                    ? 'rgba(38, 166, 154, 0.25)'
                                    : 'rgba(239, 83, 80, 0.25)';
                            }),
                            yAxisID: 'y',
                            order: 3
                        },
                        {
                            label: '종가',
                            data: data.close,
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.05)',
                            borderWidth: 3,
                            tension: 0,
                            pointRadius: 0,
                            pointHoverRadius: 5,
                            fill: false,
                            yAxisID: 'y',
                            order: 1
                        },
                        {
                            label: '50일 이평',
                            data: data.ma_50,
                            borderColor: '#26a69a',
                            borderWidth: 2,
                            tension: 0.1,
                            pointRadius: 0,
                            fill: false,
                            yAxisID: 'y',
                            order: 0
                        },
                        {
                            label: '150일 이평',
                            data: data.ma_150,
                            borderColor: '#ff9800',
                            borderWidth: 2,
                            tension: 0.1,
                            pointRadius: 0,
                            fill: false,
                            yAxisID: 'y',
                            order: 0
                        },
                        {
                            label: '200일 이평',
                            data: data.ma_200,
                            borderColor: '#e91e63',
                            borderWidth: 2,
                            tension: 0.1,
                            pointRadius: 0,
                            fill: false,
                            yAxisID: 'y',
                            order: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: { color: '#d1d4dc' }
                        },
                        tooltip: {
                            backgroundColor: '#1e222d',
                            titleColor: '#d1d4dc',
                            bodyColor: '#d1d4dc',
                            borderColor: '#2a2e39',
                            borderWidth: 1,
                            callbacks: {
                                label: function(context) {
                                    const label = context.dataset.label || '';
                                    const idx = context.dataIndex;
                                    if (label === '종가') {
                                        return [
                                            '시가: ' + data.open[idx]?.toLocaleString() + '원',
                                            '고가: ' + data.high[idx]?.toLocaleString() + '원',
                                            '저가: ' + data.low[idx]?.toLocaleString() + '원',
                                            '종가: ' + data.close[idx]?.toLocaleString() + '원'
                                        ];
                                    } else if (label === '거래량') {
                                        return '거래량: ' + data.volume[idx]?.toLocaleString();
                                    } else {
                                        return label + ': ' + context.parsed.y?.toLocaleString() + '원';
                                    }
                                }
                            }
                        },
                        annotation: {
                            clip: false,
                            annotations: annotations
                        }
                    },
                    layout: {
                        padding: {
                            top: 40,
                            right: 20,
                            bottom: 10,
                            left: 10
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: '#2a2e39' },
                            ticks: { color: '#787b86', maxTicksLimit: 10 }
                        },
                        y: {
                            type: 'linear',
                            position: 'left',
                            grid: { color: '#2a2e39' },
                            ticks: {
                                color: '#787b86',
                                callback: value => value.toLocaleString() + '원'
                            },
                            grace: '10%'
                        }
                    }
                }
            });
        }

        // 가장 최근 날짜로 자동 선택
        const dates = Object.keys(timelineData).sort().reverse();
        if (dates.length > 0) {
            document.getElementById('date-select').value = dates[0];
            changeDate(dates[0]);
        }
    </script>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n[날짜별 백테스트 대시보드 생성] {output_file}")
    return output_file


if __name__ == "__main__":
    print("날짜별 백테스트 대시보드 생성 모듈...")
