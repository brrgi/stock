"""
백테스팅 결과 웹 대시보드 생성 - 타임라인 방식
"""

import pandas as pd
import json
import os


def generate_backtest_dashboard(backtest_df, output_file='backtest_dashboard.html'):
    """백테스팅 결과를 웹 대시보드로 생성 - 금요일별 타임라인"""

    # 날짜별로 데이터 그룹화
    dates = sorted(backtest_df['date'].unique())

    # 날짜별 데이터 구조
    timeline_data = {}
    for date in dates:
        date_str = pd.to_datetime(date).strftime('%Y-%m-%d')
        date_data = backtest_df[backtest_df['date'] == date].copy()

        # 진입 신호가 있는 종목만
        signals = date_data[
            (date_data['ryan_signal'] == True) |
            (date_data['minervini_signal'] == True)
        ].to_dict('records')

        timeline_data[date_str] = {
            'total_stocks': len(date_data),
            'signals': len(signals),
            'stocks': signals
        }

    # 종목별 전체 히스토리 (차트용)
    tickers = backtest_df['ticker'].unique()
    stock_history = {}
    for ticker in tickers:
        ticker_data = backtest_df[backtest_df['ticker'] == ticker].sort_values('date')
        stock_history[ticker] = {
            'dates': ticker_data['date'].dt.strftime('%Y-%m-%d').tolist(),
            'prices': ticker_data['price'].tolist(),
            'rs_ratings': ticker_data['rs_rating'].tolist(),
            'ryan_scores': ticker_data['ryan_score'].tolist(),
            'minervini_scores': ticker_data['minervini_score'].tolist(),
            'current_price': ticker_data['current_price'].iloc[-1],
            'name': ticker
        }

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>백테스팅 타임라인 - 2025년 매주 금요일</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0e27;
            color: #d1d4dc;
            height: 100vh;
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 1.8em;
            color: white;
            margin-bottom: 5px;
        }}

        .header p {{
            font-size: 0.9em;
            color: rgba(255,255,255,0.9);
        }}

        .main-container {{
            display: flex;
            height: calc(100vh - 100px);
        }}

        /* 왼쪽 - 날짜 타임라인 */
        .timeline-panel {{
            width: 250px;
            background: #131722;
            border-right: 2px solid #2a2e39;
            overflow-y: auto;
        }}

        .timeline-item {{
            padding: 15px 20px;
            border-bottom: 1px solid #2a2e39;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .timeline-item:hover {{
            background: #1e222d;
        }}

        .timeline-item.active {{
            background: #667eea;
            border-left: 4px solid #ffd700;
        }}

        .timeline-date {{
            font-size: 1.1em;
            font-weight: bold;
            color: #fff;
            margin-bottom: 5px;
        }}

        .timeline-stats {{
            font-size: 0.85em;
            color: #787b86;
        }}

        .signal-badge {{
            background: #26a69a;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            margin-left: 5px;
        }}

        /* 가운데 - 종목 리스트 */
        .stocks-panel {{
            width: 350px;
            background: #0d1117;
            border-right: 2px solid #2a2e39;
            overflow-y: auto;
        }}

        .stocks-header {{
            padding: 20px;
            background: #131722;
            border-bottom: 2px solid #2a2e39;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        .stocks-header h2 {{
            font-size: 1.3em;
            color: #fff;
            margin-bottom: 5px;
        }}

        .stocks-header p {{
            font-size: 0.9em;
            color: #787b86;
        }}

        .stock-item {{
            padding: 15px 20px;
            border-bottom: 1px solid #2a2e39;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .stock-item:hover {{
            background: #1e222d;
        }}

        .stock-item.active {{
            background: #2a2e39;
            border-left: 4px solid #26a69a;
        }}

        .stock-name {{
            font-size: 1.1em;
            font-weight: bold;
            color: #fff;
            margin-bottom: 5px;
        }}

        .stock-info {{
            display: flex;
            justify-content: space-between;
            font-size: 0.85em;
            color: #787b86;
        }}

        .stock-score {{
            color: #ffd700;
            font-weight: bold;
        }}

        /* 오른쪽 - 차트 영역 */
        .chart-panel {{
            flex: 1;
            background: #0a0e27;
            overflow-y: auto;
            padding: 30px;
        }}

        .chart-header {{
            margin-bottom: 20px;
        }}

        .chart-title {{
            font-size: 1.8em;
            color: #fff;
            margin-bottom: 10px;
        }}

        .chart-meta {{
            display: flex;
            gap: 30px;
            font-size: 0.95em;
        }}

        .meta-item {{
            color: #787b86;
        }}

        .meta-value {{
            color: #fff;
            font-weight: bold;
            margin-left: 5px;
        }}

        .meta-value.positive {{
            color: #26a69a;
        }}

        .meta-value.negative {{
            color: #ef5350;
        }}

        .chart-container {{
            background: #131722;
            padding: 20px;
            border-radius: 15px;
            height: 500px;
            margin-bottom: 20px;
        }}

        .score-cards {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }}

        .score-card {{
            background: #131722;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }}

        .score-label {{
            color: #787b86;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}

        .score-value {{
            font-size: 2em;
            font-weight: bold;
            color: #ffd700;
        }}

        .empty-state {{
            text-align: center;
            padding: 100px 20px;
            color: #787b86;
        }}

        .empty-state h2 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 백테스팅 타임라인</h1>
        <p>2025년 매주 금요일 진입 신호 추적 - 진입 시점부터 현재까지 수익률</p>
    </div>

    <div class="main-container">
        <!-- 왼쪽: 날짜 타임라인 -->
        <div class="timeline-panel" id="timeline-panel">
        </div>

        <!-- 가운데: 종목 리스트 -->
        <div class="stocks-panel">
            <div class="stocks-header">
                <h2 id="selected-date">날짜 선택</h2>
                <p id="selected-stats">왼쪽에서 날짜를 선택하세요</p>
            </div>
            <div id="stocks-list"></div>
        </div>

        <!-- 오른쪽: 차트 -->
        <div class="chart-panel">
            <div class="empty-state" id="chart-content">
                <h2>📈</h2>
                <p>종목을 선택하면 진입 이후 가격 추이를 볼 수 있습니다</p>
            </div>
        </div>
    </div>

    <script>
        const timelineData = """ + json.dumps(timeline_data, default=str) + """;
        const stockHistory = """ + json.dumps(stock_history, default=str) + """;
        let currentChart = null;
        let selectedDate = null;
        let selectedTicker = null;

        // 타임라인 렌더링
        function renderTimeline() {
            const panel = document.getElementById('timeline-panel');
            panel.innerHTML = '';

            Object.keys(timelineData).forEach(date => {
                const data = timelineData[date];
                const item = document.createElement('div');
                item.className = 'timeline-item';
                item.innerHTML = '<div class="timeline-date">' + date + '</div>' +
                    '<div class="timeline-stats">분석: ' + data.total_stocks + '개 ' +
                    '<span class="signal-badge">' + data.signals + '개 신호</span></div>';
                item.onclick = () => selectDate(date);
                panel.appendChild(item);
            });
        }

        // 날짜 선택
        function selectDate(date) {
            selectedDate = date;

            // 타임라인 활성화 표시
            document.querySelectorAll('.timeline-item').forEach(item => {
                item.classList.remove('active');
            });
            event.currentTarget.classList.add('active');

            // 종목 리스트 업데이트
            const data = timelineData[date];
            document.getElementById('selected-date').textContent = date;
            document.getElementById('selected-stats').textContent =
                data.signals + '개 진입 신호 (총 ' + data.total_stocks + '개 분석)';

            const stocksList = document.getElementById('stocks-list');
            stocksList.innerHTML = '';

            if (data.stocks.length === 0) {
                stocksList.innerHTML = '<div class="empty-state"><p>진입 신호 없음</p></div>';
                return;
            }

            data.stocks.forEach(stock => {
                const item = document.createElement('div');
                item.className = 'stock-item';

                const returnPct = stock.return_pct || 0;
                const returnClass = returnPct > 0 ? 'positive' : 'negative';

                item.innerHTML = '<div class="stock-name">' + stock.ticker + '</div>' +
                    '<div class="stock-info">' +
                    '<span>RS <span class="stock-score">' + stock.rs_rating + '</span></span> ' +
                    '<span>Ryan <span class="stock-score">' + stock.ryan_score + '</span></span> ' +
                    '<span class="' + returnClass + '">' + (returnPct > 0 ? '+' : '') + returnPct.toFixed(1) + '%</span>' +
                    '</div>';
                item.onclick = () => selectStock(stock.ticker, date, stock);
                stocksList.appendChild(item);
            });
        }

        // 종목 선택 및 차트 표시
        function selectStock(ticker, entryDate, stockData) {
            selectedTicker = ticker;

            // 활성화 표시
            document.querySelectorAll('.stock-item').forEach(item => {
                item.classList.remove('active');
            });
            event.currentTarget.classList.add('active');

            // 차트 그리기
            const history = stockHistory[ticker];
            if (!history) return;

            // 진입 날짜 인덱스 찾기
            const entryIdx = history.dates.indexOf(entryDate);
            const entryPrice = stockData.price;
            const currentPrice = history.current_price;
            const returnPct = ((currentPrice - entryPrice) / entryPrice * 100).toFixed(2);
            const returnClass = returnPct > 0 ? 'positive' : 'negative';

            const chartPanel = document.getElementById('chart-content');
            chartPanel.innerHTML =
                '<div class="chart-header">' +
                    '<div class="chart-title">' + ticker + '</div>' +
                    '<div class="chart-meta">' +
                        '<div class="meta-item">진입일: <span class="meta-value">' + entryDate + '</span></div>' +
                        '<div class="meta-item">진입가: <span class="meta-value">' + entryPrice.toLocaleString() + '원</span></div>' +
                        '<div class="meta-item">현재가: <span class="meta-value">' + currentPrice.toLocaleString() + '원</span></div>' +
                        '<div class="meta-item">수익률: <span class="meta-value ' + returnClass + '">' +
                        (returnPct > 0 ? '+' : '') + returnPct + '%</span></div>' +
                    '</div>' +
                '</div>' +
                '<div class="chart-container"><canvas id="price-chart"></canvas></div>' +
                '<div class="score-cards">' +
                    '<div class="score-card">' +
                        '<div class="score-label">RS Rating 변화</div>' +
                        '<div class="score-value">' + stockData.rs_rating + ' → ' + history.rs_ratings[history.rs_ratings.length-1] + '</div>' +
                    '</div>' +
                    '<div class="score-card">' +
                        '<div class="score-label">Ryan Score 변화</div>' +
                        '<div class="score-value">' + stockData.ryan_score + ' → ' + history.ryan_scores[history.ryan_scores.length-1] + '</div>' +
                    '</div>' +
                    '<div class="score-card">' +
                        '<div class="score-label">Minervini Score 변화</div>' +
                        '<div class="score-value">' + stockData.minervini_score + ' → ' + history.minervini_scores[history.minervini_scores.length-1] + '</div>' +
                    '</div>' +
                '</div>';

            if (currentChart) {
                currentChart.destroy();
            }

            const ctx = document.getElementById('price-chart');
            currentChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: history.dates,
                    datasets: [{
                        label: '가격',
                        data: history.prices,
                        borderColor: '#667eea',
                        borderWidth: 3,
                        fill: false,
                        tension: 0.1,
                        pointRadius: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#1e222d',
                            titleColor: '#d1d4dc',
                            bodyColor: '#d1d4dc',
                            callbacks: {
                                label: (context) => '가격: ' + context.parsed.y.toLocaleString() + '원'
                            }
                        },
                        annotation: {
                            annotations: {
                                entry: {
                                    type: 'line',
                                    xMin: entryIdx,
                                    xMax: entryIdx,
                                    borderColor: '#26a69a',
                                    borderWidth: 2,
                                    borderDash: [5, 5],
                                    label: {
                                        display: true,
                                        content: '진입',
                                        position: 'start',
                                        backgroundColor: '#26a69a',
                                        color: 'white'
                                    }
                                },
                                entryPrice: {
                                    type: 'line',
                                    yMin: entryPrice,
                                    yMax: entryPrice,
                                    borderColor: '#ffd700',
                                    borderWidth: 2,
                                    borderDash: [5, 5],
                                    label: {
                                        display: true,
                                        content: '진입가',
                                        position: 'end',
                                        backgroundColor: '#ffd700',
                                        color: '#000'
                                    }
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: '#2a2e39' },
                            ticks: { color: '#787b86', maxTicksLimit: 10 }
                        },
                        y: {
                            grid: { color: '#2a2e39' },
                            ticks: {
                                color: '#787b86',
                                callback: value => value.toLocaleString() + '원'
                            }
                        }
                    }
                }
            });
        }

        // 초기화
        renderTimeline();
    </script>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n[백테스팅 타임라인 대시보드 생성] {output_file}")
    return output_file


if __name__ == "__main__":
    print("백테스팅 타임라인 대시보드 생성 모듈...")
