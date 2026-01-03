"""
웹 대시보드 생성 - 차트 포함
"""

import pandas as pd
import os
from datetime import datetime
import json


def generate_dashboard_html(entry_signals, price_data_dict, output_file='dashboard.html'):
    """
    진입 신호와 차트를 포함한 웹 대시보드 생성
    """

    # 차트 데이터 준비
    chart_data_json = {}
    for idx, row in entry_signals.head(20).iterrows():
        ticker = row['종목코드']
        if ticker in price_data_dict:
            df = price_data_dict[ticker].tail(120)  # 최근 120일
            chart_data_json[ticker] = {
                'dates': df.index.strftime('%Y-%m-%d').tolist(),
                'prices': df['Close'].tolist(),
                'volumes': df['Volume'].tolist(),
                'highs': df['High'].tolist(),
                'lows': df['Low'].tolist()
            }

    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>주식 진입 신호 대시보드</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }}

        .header h1 {{
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header .subtitle {{
            color: #666;
            font-size: 1.1em;
        }}

        .header .timestamp {{
            color: #999;
            font-size: 0.9em;
            margin-top: 10px;
        }}

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .summary-card .number {{
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}

        .summary-card .label {{
            color: #666;
            font-size: 1.1em;
        }}

        .stock-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            transition: transform 0.3s, box-shadow 0.3s;
        }}

        .stock-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        }}

        .stock-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }}

        .stock-name {{
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }}

        .stock-code {{
            color: #666;
            font-size: 1.1em;
        }}

        .rs-rating {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 1.2em;
            font-weight: bold;
        }}

        .signal-badges {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}

        .badge {{
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }}

        .badge-success {{
            background: #4CAF50;
            color: white;
        }}

        .badge-warning {{
            background: #FF9800;
            color: white;
        }}

        .badge-info {{
            background: #2196F3;
            color: white;
        }}

        .stock-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}

        .detail-item {{
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}

        .detail-label {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 5px;
        }}

        .detail-value {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }}

        .strategy-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}

        .strategy-box {{
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border: 2px solid #e0e0e0;
        }}

        .strategy-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .strategy-reasons {{
            color: #555;
            line-height: 1.8;
            font-size: 0.95em;
        }}

        .chart-container {{
            margin-top: 20px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
        }}

        .chart-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
        }}

        canvas {{
            max-height: 400px;
        }}

        .btn-tradingview {{
            display: inline-block;
            background: #2962FF;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 15px;
            transition: background 0.3s;
        }}

        .btn-tradingview:hover {{
            background: #1E53E5;
        }}

        .btn-naver {{
            display: inline-block;
            background: #03C75A;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 15px;
            margin-left: 10px;
            transition: background 0.3s;
        }}

        .btn-naver:hover {{
            background: #02B350;
        }}

        @media (max-width: 768px) {{
            .strategy-section {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 주식 진입 신호 대시보드</h1>
            <div class="subtitle">David Ryan & Mark Minervini 전략 기반</div>
            <div class="timestamp">생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}</div>
        </div>

        <div class="summary-cards">
            <div class="summary-card">
                <div class="label">전체 진입 신호</div>
                <div class="number">{len(entry_signals)}</div>
            </div>
            <div class="summary-card">
                <div class="label">David Ryan 신호</div>
                <div class="number">{len(entry_signals[entry_signals['Ryan_진입신호'] == True]) if 'Ryan_진입신호' in entry_signals.columns else 0}</div>
            </div>
            <div class="summary-card">
                <div class="label">Minervini 신호</div>
                <div class="number">{len(entry_signals[entry_signals['미너비니_진입신호'] == True]) if '미너비니_진입신호' in entry_signals.columns else 0}</div>
            </div>
            <div class="summary-card">
                <div class="label">평균 RS 등급</div>
                <div class="number">{int(entry_signals['RS등급'].mean())}</div>
            </div>
        </div>

        <div id="stocks-container">
"""

    # 각 종목 카드 생성
    for idx, row in entry_signals.head(20).iterrows():
        ticker = row['종목코드']
        name = row['종목명']
        rs = row['RS등급']
        current_price = row['현재가']

        # 진입 신호 배지
        badges = []
        if row.get('Ryan_진입신호', False):
            badges.append('<span class="badge badge-success">David Ryan ✓</span>')
        if row.get('미너비니_진입신호', False):
            badges.append('<span class="badge badge-success">Minervini ✓</span>')
        if row.get('오닐_진입신호', False):
            badges.append('<span class="badge badge-info">O\'Neil ✓</span>')

        badges_html = ''.join(badges) if badges else '<span class="badge badge-warning">분석 중</span>'

        # 트레이딩뷰 링크 (한국 주식은 KRX: 접두사)
        tradingview_url = f"https://www.tradingview.com/chart/?symbol=KRX%3A{ticker}"
        naver_url = f"https://finance.naver.com/item/main.nhn?code={ticker}"

        html_content += f"""
            <div class="stock-card">
                <div class="stock-header">
                    <div>
                        <div class="stock-name">{name}</div>
                        <div class="stock-code">{ticker}</div>
                    </div>
                    <div class="rs-rating">RS {rs}</div>
                </div>

                <div class="signal-badges">
                    {badges_html}
                </div>

                <div class="stock-details">
                    <div class="detail-item">
                        <div class="detail-label">현재가</div>
                        <div class="detail-value">{current_price:,.0f}원</div>
                    </div>
"""

        # Ryan 데이터
        if 'Ryan_진입가' in row and pd.notna(row['Ryan_진입가']):
            html_content += f"""
                    <div class="detail-item">
                        <div class="detail-label">Ryan 진입가</div>
                        <div class="detail-value">{row['Ryan_진입가']:,.0f}원</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Ryan 손절가</div>
                        <div class="detail-value" style="color: #f44336;">{row['Ryan_손절가']:,.0f}원</div>
                    </div>
"""

        # Minervini 데이터
        if '미너비니_진입가' in row and pd.notna(row['미너비니_진입가']):
            html_content += f"""
                    <div class="detail-item">
                        <div class="detail-label">Minervini 진입가</div>
                        <div class="detail-value">{row['미너비니_진입가']:,.0f}원</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Minervini 손절가</div>
                        <div class="detail-value" style="color: #f44336;">{row['미너비니_손절가']:,.0f}원</div>
                    </div>
"""

        html_content += """
                </div>

                <div class="strategy-section">
"""

        # Ryan 전략
        if 'Ryan_근거' in row and pd.notna(row['Ryan_근거']):
            html_content += f"""
                    <div class="strategy-box">
                        <div class="strategy-title">
                            🎯 David Ryan 분석
                        </div>
                        <div class="strategy-reasons">{row['Ryan_근거'].replace(' | ', '<br>• ')}</div>
                    </div>
"""

        # Minervini 전략
        if '미너비니_근거' in row and pd.notna(row['미너비니_근거']):
            html_content += f"""
                    <div class="strategy-box">
                        <div class="strategy-title">
                            📈 Mark Minervini 분석
                        </div>
                        <div class="strategy-reasons">{row['미너비니_근거'].replace(' | ', '<br>• ')}</div>
                    </div>
"""

        html_content += """
                </div>
"""

        # 차트
        if ticker in chart_data_json:
            html_content += f"""
                <div class="chart-container">
                    <div class="chart-title">📊 가격 및 거래량 차트 (최근 120일)</div>
                    <canvas id="chart-{ticker}"></canvas>
                    <a href="{tradingview_url}" target="_blank" class="btn-tradingview">TradingView에서 보기 →</a>
                    <a href="{naver_url}" target="_blank" class="btn-naver">네이버 금융에서 보기 →</a>
                </div>
"""

        html_content += """
            </div>
"""

    html_content += """
        </div>
    </div>

    <script>
        const chartData = """ + json.dumps(chart_data_json) + """;

        Object.keys(chartData).forEach(ticker => {
            const data = chartData[ticker];
            const ctx = document.getElementById('chart-' + ticker);

            if (ctx) {
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.dates,
                        datasets: [{
                            label: '종가',
                            data: data.prices,
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            borderWidth: 2,
                            tension: 0.1,
                            yAxisID: 'y',
                        }, {
                            label: '거래량',
                            data: data.volumes,
                            type: 'bar',
                            backgroundColor: 'rgba(118, 75, 162, 0.5)',
                            yAxisID: 'y1',
                        }]
                    },
                    options: {
                        responsive: true,
                        interaction: {
                            mode: 'index',
                            intersect: false,
                        },
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        let label = context.dataset.label || '';
                                        if (label) {
                                            label += ': ';
                                        }
                                        if (context.parsed.y !== null) {
                                            if (context.dataset.label === '종가') {
                                                label += context.parsed.y.toLocaleString() + '원';
                                            } else {
                                                label += context.parsed.y.toLocaleString();
                                            }
                                        }
                                        return label;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                type: 'linear',
                                display: true,
                                position: 'left',
                                title: {
                                    display: true,
                                    text: '가격 (원)'
                                }
                            },
                            y1: {
                                type: 'linear',
                                display: true,
                                position: 'right',
                                title: {
                                    display: true,
                                    text: '거래량'
                                },
                                grid: {
                                    drawOnChartArea: false,
                                }
                            }
                        }
                    }
                });
            }
        });
    </script>
</body>
</html>
"""

    # 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n[대시보드 생성 완료] {output_file}")
    return output_file


if __name__ == "__main__":
    print("웹 대시보드 생성 모듈...")
