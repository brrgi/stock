"""
상세 체크리스트 포함 웹 대시보드 생성
"""

import pandas as pd
import os
from datetime import datetime
import json
from advanced_entry_signals import AdvancedEntryAnalyzer


def analyze_stock_details(ticker, price_data, rs_rating):
    """종목별 상세 분석 정보 생성"""
    analyzer = AdvancedEntryAnalyzer()

    details = {
        'ryan': {},
        'minervini': {},
        'technical': {}
    }

    if len(price_data) < 60:
        return details

    # David Ryan 상세 분석
    htf = analyzer.check_high_tight_flag(price_data)
    base = analyzer.check_base_quality(price_data)
    dryup = analyzer.check_volume_dryup(price_data)
    volume_bo = analyzer.check_volume_breakout(price_data)

    current_price = price_data['Close'].iloc[-1]
    pivot = price_data['High'].iloc[-10:].max()
    distance_from_pivot = ((pivot - current_price) / pivot) * 100

    high_52w = price_data['High'].iloc[-252:].max() if len(price_data) >= 252 else price_data['High'].max()
    distance_from_high = ((high_52w - current_price) / high_52w) * 100

    details['ryan'] = {
        'rs_rating': {
            'value': rs_rating,
            'passed': rs_rating >= 90,
            'excellent': rs_rating >= 95,
            'label': f'RS Rating {rs_rating}'
        },
        'high_tight_flag': {
            'passed': htf['pattern'],
            'label': f"High Tight Flag 패턴 ({htf.get('gain', 0):.0f}% 상승)" if htf['pattern'] else 'High Tight Flag 패턴 미형성',
            'strength': htf.get('strength', 0)
        },
        'base_quality': {
            'passed': base['score'] >= 70,
            'label': f"베이스 품질 {base['quality']} (깊이 {base['depth']:.1f}%)",
            'score': base['score']
        },
        'volume_dryup': {
            'passed': dryup['dryup'],
            'label': f"거래량 건조 ({dryup['ratio']:.0f}%)" if dryup['dryup'] else '거래량 건조 미확인',
        },
        'pivot_proximity': {
            'passed': distance_from_pivot <= 1,
            'label': f'피봇 포인트 {distance_from_pivot:.1f}% 거리'
        },
        'volume_breakout': {
            'passed': volume_bo['breakout'],
            'label': f"거래량 {volume_bo.get('volume_ratio', 0):.1f}배" if volume_bo['breakout'] else '거래량 돌파 미확인'
        },
        '52w_high': {
            'passed': distance_from_high <= 15,
            'label': f'52주 최고가 {distance_from_high:.1f}% 이내'
        }
    }

    # Mark Minervini 트렌드 템플릿 상세
    if len(price_data) >= 200:
        template = analyzer.check_trend_template_detailed(price_data)
        vcp = analyzer.check_vcp_detailed(price_data)

        current_price = price_data['Close'].iloc[-1]
        ma_50 = template['ma_50']
        ma_150 = template['ma_150']
        ma_200 = template['ma_200']

        ma_200_past = price_data['Close'].iloc[-220:-200].mean() if len(price_data) >= 220 else ma_200
        ma_200_rising = ma_200 > ma_200_past

        high_52w = price_data['High'].iloc[-252:].max() if len(price_data) >= 252 else price_data['High'].max()
        low_52w = price_data['Low'].iloc[-252:].min() if len(price_data) >= 252 else price_data['Low'].min()

        gain_from_low = ((current_price - low_52w) / low_52w * 100) if low_52w > 0 else 0
        distance_from_high_pct = ((high_52w - current_price) / high_52w * 100)

        details['minervini'] = {
            'template_1': {
                'passed': current_price > ma_150,
                'label': f'현재가({current_price:,.0f}) > 150일 이평({ma_150:,.0f})'
            },
            'template_2': {
                'passed': current_price > ma_200,
                'label': f'현재가({current_price:,.0f}) > 200일 이평({ma_200:,.0f})'
            },
            'template_3': {
                'passed': ma_150 > ma_200,
                'label': f'150일 이평({ma_150:,.0f}) > 200일 이평({ma_200:,.0f})'
            },
            'template_4': {
                'passed': ma_200_rising,
                'label': f'200일 이평선 상승 추세 {"확인" if ma_200_rising else "미확인"}'
            },
            'template_5': {
                'passed': ma_50 > ma_150,
                'label': f'50일 이평({ma_50:,.0f}) > 150일 이평({ma_150:,.0f})'
            },
            'template_6': {
                'passed': current_price > ma_50,
                'label': f'현재가({current_price:,.0f}) > 50일 이평({ma_50:,.0f})'
            },
            'template_7': {
                'passed': gain_from_low >= 30,
                'label': f'52주 최저 대비 +{gain_from_low:.1f}% (30% 이상 필요)'
            },
            'template_8': {
                'passed': distance_from_high_pct <= 25,
                'label': f'52주 최고가 대비 {distance_from_high_pct:.1f}% 이내 (25% 이내 필요)'
            },
            'vcp_pattern': {
                'passed': vcp['vcp'],
                'label': f"VCP {vcp['quality']} ({vcp.get('stages', 0)}단계)" if vcp['vcp'] else 'VCP 패턴 미형성',
                'quality': vcp.get('quality', 'None')
            },
            'rs_rating': {
                'passed': rs_rating >= 80,
                'excellent': rs_rating >= 90,
                'label': f'RS Rating {rs_rating} (80 이상 필요)'
            }
        }

    return details


def generate_detailed_dashboard(entry_signals, price_data_dict, output_file='dashboard_detailed.html'):
    """상세 체크리스트가 포함된 웹 대시보드 생성"""

    # 각 종목의 상세 분석 데이터 생성
    stock_details = {}
    for idx, row in entry_signals.head(20).iterrows():
        ticker = row['종목코드']
        if ticker in price_data_dict:
            rs_rating = row['RS등급']
            stock_details[ticker] = analyze_stock_details(ticker, price_data_dict[ticker], rs_rating)

    # 차트 데이터 준비
    chart_data_json = {}
    for idx, row in entry_signals.head(20).iterrows():
        ticker = row['종목코드']
        if ticker in price_data_dict:
            df = price_data_dict[ticker].tail(120)
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
    <title>주식 진입 신호 상세 분석</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            max-width: 1600px;
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

        .stock-card {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }}

        .stock-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #f0f0f0;
        }}

        .stock-name {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}

        .stock-code {{
            color: #666;
            font-size: 1.2em;
            margin-top: 5px;
        }}

        .rs-badge {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 30px;
            font-size: 1.5em;
            font-weight: bold;
        }}

        .analysis-section {{
            margin-bottom: 30px;
        }}

        .section-title {{
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .section-icon {{
            font-size: 1.3em;
        }}

        .checklist {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
        }}

        .check-item {{
            display: flex;
            align-items: center;
            padding: 12px;
            margin-bottom: 10px;
            background: white;
            border-radius: 8px;
            border-left: 4px solid #ddd;
            transition: all 0.3s;
        }}

        .check-item:hover {{
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .check-item.passed {{
            border-left-color: #4CAF50;
        }}

        .check-item.failed {{
            border-left-color: #f44336;
        }}

        .check-item.excellent {{
            border-left-color: #FF9800;
            background: #FFF3E0;
        }}

        .check-icon {{
            font-size: 1.5em;
            margin-right: 15px;
            min-width: 30px;
            text-align: center;
        }}

        .check-label {{
            flex: 1;
            font-size: 1.05em;
            color: #333;
        }}

        .check-value {{
            font-weight: bold;
            margin-left: 10px;
            color: #666;
        }}

        .strategy-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}

        .price-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }}

        .price-item {{
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 8px;
        }}

        .price-label {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 8px;
        }}

        .price-value {{
            font-size: 1.4em;
            font-weight: bold;
            color: #333;
        }}

        .price-value.entry {{
            color: #2196F3;
        }}

        .price-value.stop {{
            color: #f44336;
        }}

        .chart-container {{
            margin-top: 30px;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 10px;
        }}

        .chart-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
        }}

        .btn-group {{
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }}

        .btn {{
            flex: 1;
            padding: 15px 25px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            text-align: center;
            transition: all 0.3s;
        }}

        .btn-tradingview {{
            background: #2962FF;
            color: white;
        }}

        .btn-tradingview:hover {{
            background: #1E53E5;
            transform: translateY(-2px);
        }}

        .btn-naver {{
            background: #03C75A;
            color: white;
        }}

        .btn-naver:hover {{
            background: #02B350;
            transform: translateY(-2px);
        }}

        .summary-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            margin-left: 10px;
        }}

        .badge-excellent {{
            background: #4CAF50;
            color: white;
        }}

        .badge-good {{
            background: #2196F3;
            color: white;
        }}

        .badge-warning {{
            background: #FF9800;
            color: white;
        }}

        @media (max-width: 1024px) {{
            .strategy-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 주식 진입 신호 상세 분석</h1>
            <div style="color: #666; font-size: 1.1em; margin-top: 10px;">
                David Ryan & Mark Minervini 전략 체크리스트
            </div>
            <div style="color: #999; font-size: 0.9em; margin-top: 10px;">
                생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}
            </div>
        </div>
"""

    # 각 종목 카드 생성
    for idx, row in entry_signals.head(20).iterrows():
        ticker = row['종목코드']
        name = row['종목명']
        rs = row['RS등급']
        current_price = row['현재가']

        details = stock_details.get(ticker, {})
        ryan = details.get('ryan', {})
        minervini = details.get('minervini', {})

        # Ryan 통과 개수
        ryan_passed = sum(1 for k, v in ryan.items() if isinstance(v, dict) and v.get('passed', False))
        ryan_total = len([k for k in ryan.keys() if isinstance(ryan[k], dict)])

        # Minervini 통과 개수
        minervini_passed = sum(1 for k, v in minervini.items() if isinstance(v, dict) and v.get('passed', False))
        minervini_total = len([k for k in minervini.keys() if isinstance(minervini[k], dict)])

        html_content += f"""
        <div class="stock-card">
            <div class="stock-header">
                <div>
                    <div class="stock-name">{name}</div>
                    <div class="stock-code">{ticker}</div>
                </div>
                <div class="rs-badge">RS {rs}</div>
            </div>

            <div class="price-info">
                <div class="price-item">
                    <div class="price-label">현재가</div>
                    <div class="price-value">{current_price:,.0f}원</div>
                </div>
"""

        if 'Ryan_진입가' in row and pd.notna(row['Ryan_진입가']):
            html_content += f"""
                <div class="price-item">
                    <div class="price-label">Ryan 진입가</div>
                    <div class="price-value entry">{row['Ryan_진입가']:,.0f}원</div>
                </div>
                <div class="price-item">
                    <div class="price-label">Ryan 손절가</div>
                    <div class="price-value stop">{row['Ryan_손절가']:,.0f}원</div>
                </div>
"""

        if '미너비니_진입가' in row and pd.notna(row['미너비니_진입가']):
            html_content += f"""
                <div class="price-item">
                    <div class="price-label">Minervini 진입가</div>
                    <div class="price-value entry">{row['미너비니_진입가']:,.0f}원</div>
                </div>
                <div class="price-item">
                    <div class="price-label">Minervini 손절가</div>
                    <div class="price-value stop">{row['미너비니_손절가']:,.0f}원</div>
                </div>
"""

        html_content += """
            </div>

            <div class="strategy-grid">
"""

        # David Ryan 체크리스트
        html_content += f"""
                <div class="analysis-section">
                    <div class="section-title">
                        <span class="section-icon">🎯</span>
                        David Ryan 전략
                        <span class="summary-badge {'badge-excellent' if ryan_passed >= 6 else 'badge-good' if ryan_passed >= 4 else 'badge-warning'}">
                            {ryan_passed}/{ryan_total} 조건 충족
                        </span>
                    </div>
                    <div class="checklist">
"""

        # Ryan 체크 항목들
        for key, item in ryan.items():
            if isinstance(item, dict):
                passed = item.get('passed', False)
                excellent = item.get('excellent', False)
                label = item.get('label', '')

                icon = '✓' if passed else '✗'
                css_class = 'excellent' if excellent else ('passed' if passed else 'failed')

                html_content += f"""
                        <div class="check-item {css_class}">
                            <div class="check-icon">{'🌟' if excellent else icon}</div>
                            <div class="check-label">{label}</div>
                        </div>
"""

        html_content += """
                    </div>
                </div>
"""

        # Mark Minervini 체크리스트
        html_content += f"""
                <div class="analysis-section">
                    <div class="section-title">
                        <span class="section-icon">📈</span>
                        Mark Minervini 전략
                        <span class="summary-badge {'badge-excellent' if minervini_passed >= 9 else 'badge-good' if minervini_passed >= 7 else 'badge-warning'}">
                            {minervini_passed}/{minervini_total} 조건 충족
                        </span>
                    </div>
                    <div class="checklist">
"""

        # Minervini 체크 항목들
        for key, item in minervini.items():
            if isinstance(item, dict):
                passed = item.get('passed', False)
                excellent = item.get('excellent', False)
                label = item.get('label', '')

                icon = '✓' if passed else '✗'
                css_class = 'excellent' if excellent else ('passed' if passed else 'failed')

                html_content += f"""
                        <div class="check-item {css_class}">
                            <div class="check-icon">{'🌟' if excellent else icon}</div>
                            <div class="check-label">{label}</div>
                        </div>
"""

        html_content += """
                    </div>
                </div>
            </div>
"""

        # 차트
        if ticker in chart_data_json:
            tradingview_url = f"https://www.tradingview.com/chart/?symbol=KRX%3A{ticker}"
            naver_url = f"https://finance.naver.com/item/main.nhn?code={ticker}"

            html_content += f"""
            <div class="chart-container">
                <div class="chart-title">📊 가격 및 거래량 차트 (최근 120일)</div>
                <canvas id="chart-{ticker}" style="max-height: 400px;"></canvas>
                <div class="btn-group">
                    <a href="{tradingview_url}" target="_blank" class="btn btn-tradingview">
                        TradingView에서 상세 분석 →
                    </a>
                    <a href="{naver_url}" target="_blank" class="btn btn-naver">
                        네이버 금융에서 보기 →
                    </a>
                </div>
            </div>
"""

        html_content += """
        </div>
"""

    html_content += """
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
                            backgroundColor: 'rgba(118, 75, 162, 0.3)',
                            yAxisID: 'y1',
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
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

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n[상세 대시보드 생성 완료] {output_file}")
    return output_file


if __name__ == "__main__":
    print("상세 웹 대시보드 생성 모듈...")
