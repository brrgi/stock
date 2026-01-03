"""
David Ryan 스타일 프로페셔널 차트 대시보드
- 캔들스틱 차트
- 피봇 포인트 표시
- 진입 시점 화살표
- 베이스 패턴 하이라이트
"""

import pandas as pd
import os
from datetime import datetime
import json
from advanced_entry_signals import AdvancedEntryAnalyzer


def analyze_stock_details(ticker, price_data, rs_rating):
    """종목별 상세 분석"""
    analyzer = AdvancedEntryAnalyzer()

    details = {
        'ryan': {},
        'minervini': {},
        'chart_markers': {}
    }

    if len(price_data) < 60:
        return details

    current_price = price_data['Close'].iloc[-1]

    # 피봇 포인트 찾기
    pivot = price_data['High'].iloc[-30:].max()
    pivot_idx = price_data['High'].iloc[-30:].idxmax()

    # 베이스 저점 찾기
    base_low = price_data['Low'].iloc[-30:].min()
    base_low_idx = price_data['Low'].iloc[-30:].idxmin()

    # 진입 시점 판단
    distance_from_pivot = ((pivot - current_price) / pivot) * 100
    is_at_pivot = distance_from_pivot <= 2

    details['chart_markers'] = {
        'pivot_point': {
            'date': pivot_idx.strftime('%Y-%m-%d') if hasattr(pivot_idx, 'strftime') else str(pivot_idx),
            'price': float(pivot),
            'label': 'Pivot Point'
        },
        'base_low': {
            'date': base_low_idx.strftime('%Y-%m-%d') if hasattr(base_low_idx, 'strftime') else str(base_low_idx),
            'price': float(base_low),
            'label': 'Base Low'
        },
        'current_signal': is_at_pivot,
        'entry_price': float(pivot * 1.001)
    }

    # David Ryan 분석
    htf = analyzer.check_high_tight_flag(price_data)
    base = analyzer.check_base_quality(price_data)
    dryup = analyzer.check_volume_dryup(price_data)
    volume_bo = analyzer.check_volume_breakout(price_data)

    high_52w = price_data['High'].iloc[-252:].max() if len(price_data) >= 252 else price_data['High'].max()
    distance_from_high = ((high_52w - current_price) / high_52w) * 100

    details['ryan'] = {
        'rs_rating': {
            'value': rs_rating,
            'passed': rs_rating >= 90,
            'excellent': rs_rating >= 95,
            'label': f'RS Rating {rs_rating} (90+ 필요)'
        },
        'high_tight_flag': {
            'passed': htf['pattern'],
            'label': f"High Tight Flag 패턴 ({htf.get('gain', 0):.0f}% 상승)" if htf['pattern'] else 'High Tight Flag 패턴 미형성',
            'strength': htf.get('strength', 0)
        },
        'base_quality': {
            'passed': base['score'] >= 70,
            'label': f"베이스 품질 {base['quality']} (깊이 {base['depth']:.1f}%, 타이트 {base['tightness']:.1f}%)",
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
            'label': f"거래량 {volume_bo.get('volume_ratio', 0):.1f}배 증가" if volume_bo['breakout'] else '거래량 돌파 대기'
        },
        '52w_high': {
            'passed': distance_from_high <= 15,
            'label': f'52주 최고가 {distance_from_high:.1f}% 이내'
        }
    }

    # Mark Minervini 분석
    if len(price_data) >= 200:
        template = analyzer.check_trend_template_detailed(price_data)
        vcp = analyzer.check_vcp_detailed(price_data)

        ma_50 = template['ma_50']
        ma_150 = template['ma_150']
        ma_200 = template['ma_200']

        details['minervini'] = {
            'template_1': {
                'passed': current_price > ma_150,
                'label': f'현재가({current_price:,.0f}) > 150일 이평({ma_150:,.0f})'
            },
            'template_2': {
                'passed': current_price > ma_200,
                'label': f'현재가 > 200일 이평 ({ma_200:,.0f}원)'
            },
            'template_3': {
                'passed': ma_150 > ma_200,
                'label': f'150일({ma_150:,.0f}) > 200일({ma_200:,.0f}) 이평'
            },
            'template_4': {
                'passed': template['score'] >= 87.5,
                'label': f'200일 이평선 상승 추세'
            },
            'template_5': {
                'passed': ma_50 > ma_150,
                'label': f'50일({ma_50:,.0f}) > 150일 이평'
            },
            'template_6': {
                'passed': current_price > ma_50,
                'label': f'현재가 > 50일 이평 ({ma_50:,.0f}원)'
            },
            'template_7': {
                'passed': template['checks_passed'] >= 7,
                'label': f'52주 최저 대비 30% 이상 상승'
            },
            'template_8': {
                'passed': distance_from_high <= 25,
                'label': f'52주 최고가 25% 이내 (현재 {distance_from_high:.1f}%)'
            },
            'vcp_pattern': {
                'passed': vcp['vcp'],
                'label': f"VCP {vcp['quality']} ({vcp.get('stages', 0)}단계)" if vcp['vcp'] else 'VCP 패턴 미형성',
                'quality': vcp.get('quality', 'None')
            },
            'rs_rating': {
                'passed': rs_rating >= 80,
                'excellent': rs_rating >= 90,
                'label': f'RS Rating {rs_rating} (80+ 필요, 90+ 이상적)'
            }
        }

        # 이동평균선 데이터 추가
        details['chart_markers']['ma_50'] = float(ma_50)
        details['chart_markers']['ma_150'] = float(ma_150)
        details['chart_markers']['ma_200'] = float(ma_200)

    return details


def generate_pro_dashboard(entry_signals, price_data_dict, output_file='dashboard_pro.html'):
    """David Ryan 스타일 프로페셔널 대시보드"""

    # 각 종목의 상세 분석
    stock_details = {}
    for idx, row in entry_signals.head(20).iterrows():
        ticker = row['종목코드']
        if ticker in price_data_dict:
            rs_rating = row['RS등급']
            stock_details[ticker] = analyze_stock_details(ticker, price_data_dict[ticker], rs_rating)

    # 차트 데이터 (캔들스틱용)
    chart_data_json = {}
    for idx, row in entry_signals.head(20).iterrows():
        ticker = row['종목코드']
        if ticker in price_data_dict:
            df = price_data_dict[ticker].tail(120)

            # 이동평균선 계산
            ma_50 = df['Close'].rolling(50).mean()
            ma_150 = df['Close'].rolling(150).mean() if len(df) >= 150 else None

            # NaN 값 제거 및 JSON 직렬화 가능하게 변환
            chart_data_json[ticker] = {
                'dates': df.index.strftime('%Y-%m-%d').tolist(),
                'open': [float(x) if pd.notna(x) else None for x in df['Open'].tolist()],
                'high': [float(x) if pd.notna(x) else None for x in df['High'].tolist()],
                'low': [float(x) if pd.notna(x) else None for x in df['Low'].tolist()],
                'close': [float(x) if pd.notna(x) else None for x in df['Close'].tolist()],
                'volume': [float(x) if pd.notna(x) else None for x in df['Volume'].tolist()],
                'ma_50': [float(x) if pd.notna(x) else None for x in ma_50.tolist()],
                'ma_150': [float(x) if pd.notna(x) else None for x in ma_150.tolist()] if ma_150 is not None else []
            }

    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>David Ryan 스타일 진입 분석</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-financial"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
            background: #0a0e27;
            color: #fff;
            padding: 20px;
        }}

        .container {{
            max-width: 1800px;
            margin: 0 auto;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .stock-card {{
            background: #1a1f3a;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            border: 1px solid #2a2f4a;
        }}

        .stock-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #2a2f4a;
        }}

        .stock-name {{
            font-size: 2.2em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .stock-code {{
            color: #8b92b8;
            font-size: 1.2em;
            margin-top: 5px;
        }}

        .rs-badge {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 15px 30px;
            border-radius: 30px;
            font-size: 1.5em;
            font-weight: bold;
            box-shadow: 0 5px 15px rgba(245, 87, 108, 0.4);
        }}

        .chart-section {{
            background: #0f1425;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
        }}

        .chart-title {{
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #667eea;
            font-weight: bold;
        }}

        .price-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}

        .price-item {{
            background: #0f1425;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 2px solid #2a2f4a;
            transition: all 0.3s;
        }}

        .price-item:hover {{
            border-color: #667eea;
            transform: translateY(-3px);
        }}

        .price-label {{
            color: #8b92b8;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}

        .price-value {{
            font-size: 1.6em;
            font-weight: bold;
            color: #fff;
        }}

        .price-value.entry {{
            color: #4CAF50;
        }}

        .price-value.stop {{
            color: #f5576c;
        }}

        .analysis-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}

        .analysis-box {{
            background: #0f1425;
            padding: 25px;
            border-radius: 15px;
            border: 1px solid #2a2f4a;
        }}

        .analysis-title {{
            font-size: 1.4em;
            font-weight: bold;
            margin-bottom: 20px;
            color: #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .score-badge {{
            background: #2a2f4a;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.7em;
            margin-left: auto;
        }}

        .score-badge.excellent {{
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        }}

        .score-badge.good {{
            background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        }}

        .score-badge.warning {{
            background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        }}

        .check-item {{
            display: flex;
            align-items: center;
            padding: 12px;
            margin-bottom: 10px;
            background: #1a1f3a;
            border-radius: 10px;
            border-left: 4px solid #2a2f4a;
            transition: all 0.3s;
        }}

        .check-item:hover {{
            transform: translateX(5px);
            background: #1e2440;
        }}

        .check-item.passed {{
            border-left-color: #4CAF50;
        }}

        .check-item.failed {{
            border-left-color: #f5576c;
        }}

        .check-item.excellent {{
            border-left-color: #FFD700;
            background: linear-gradient(90deg, #1a1f3a 0%, #2a2410 100%);
        }}

        .check-icon {{
            font-size: 1.3em;
            margin-right: 15px;
            min-width: 30px;
        }}

        .check-label {{
            flex: 1;
            color: #e0e0e0;
        }}

        canvas {{
            max-height: 500px;
        }}

        .btn-group {{
            display: flex;
            gap: 15px;
            margin-top: 20px;
        }}

        .btn {{
            flex: 1;
            padding: 15px 25px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: bold;
            text-align: center;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }}

        .btn-tradingview {{
            background: linear-gradient(135deg, #2962FF 0%, #1E53E5 100%);
            color: white;
        }}

        .btn-tradingview:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(41, 98, 255, 0.4);
        }}

        .btn-naver {{
            background: linear-gradient(135deg, #03C75A 0%, #02B350 100%);
            color: white;
        }}

        .btn-naver:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(3, 199, 90, 0.4);
        }}

        .legend-item {{
            display: inline-flex;
            align-items: center;
            margin-right: 20px;
            margin-bottom: 10px;
        }}

        .legend-color {{
            width: 20px;
            height: 4px;
            margin-right: 8px;
            border-radius: 2px;
        }}

        @media (max-width: 1200px) {{
            .analysis-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 David Ryan & Mark Minervini 진입 분석</h1>
            <div class="subtitle">프로페셔널 차트 분석 시스템</div>
            <div style="margin-top: 10px; opacity: 0.8;">
                {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}
            </div>
        </div>
"""

    # 각 종목 카드
    for idx, row in entry_signals.head(20).iterrows():
        ticker = row['종목코드']
        name = row['종목명']
        rs = row['RS등급']
        current_price = row['현재가']

        details = stock_details.get(ticker, {})
        ryan = details.get('ryan', {})
        minervini = details.get('minervini', {})

        ryan_passed = sum(1 for k, v in ryan.items() if isinstance(v, dict) and v.get('passed', False))
        ryan_total = len([k for k in ryan.keys() if isinstance(ryan[k], dict)])

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

            <div class="chart-section">
                <div class="chart-title">📊 캔들스틱 차트 with 진입 신호</div>
                <div style="margin-bottom: 15px;">
                    <span class="legend-item">
                        <span class="legend-color" style="background: #4CAF50;"></span>
                        <span>50일 이평선</span>
                    </span>
                    <span class="legend-item">
                        <span class="legend-color" style="background: #FF9800;"></span>
                        <span>150일 이평선</span>
                    </span>
                    <span class="legend-item">
                        <span class="legend-color" style="background: #2196F3;"></span>
                        <span>200일 이평선</span>
                    </span>
                </div>
                <canvas id="chart-{ticker}"></canvas>
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
                    <div class="price-label">🎯 Ryan 진입가</div>
                    <div class="price-value entry">{row['Ryan_진입가']:,.0f}원</div>
                </div>
                <div class="price-item">
                    <div class="price-label">🛑 Ryan 손절가</div>
                    <div class="price-value stop">{row['Ryan_손절가']:,.0f}원</div>
                </div>
"""

        if '미너비니_진입가' in row and pd.notna(row['미너비니_진입가']):
            html_content += f"""
                <div class="price-item">
                    <div class="price-label">🎯 Minervini 진입가</div>
                    <div class="price-value entry">{row['미너비니_진입가']:,.0f}원</div>
                </div>
                <div class="price-item">
                    <div class="price-label">🛑 Minervini 손절가</div>
                    <div class="price-value stop">{row['미너비니_손절가']:,.0f}원</div>
                </div>
"""

        html_content += """
            </div>

            <div class="analysis-grid">
"""

        # David Ryan 분석
        ryan_score_class = 'excellent' if ryan_passed >= 6 else 'good' if ryan_passed >= 4 else 'warning'
        html_content += f"""
                <div class="analysis-box">
                    <div class="analysis-title">
                        🎯 David Ryan 전략
                        <span class="score-badge {ryan_score_class}">{ryan_passed}/{ryan_total}</span>
                    </div>
"""

        for key, item in ryan.items():
            if isinstance(item, dict):
                passed = item.get('passed', False)
                excellent = item.get('excellent', False)
                label = item.get('label', '')
                icon = '🌟' if excellent else ('✓' if passed else '✗')
                css_class = 'excellent' if excellent else ('passed' if passed else 'failed')

                html_content += f"""
                    <div class="check-item {css_class}">
                        <div class="check-icon">{icon}</div>
                        <div class="check-label">{label}</div>
                    </div>
"""

        html_content += """
                </div>
"""

        # Mark Minervini 분석
        minervini_score_class = 'excellent' if minervini_passed >= 9 else 'good' if minervini_passed >= 7 else 'warning'
        html_content += f"""
                <div class="analysis-box">
                    <div class="analysis-title">
                        📈 Mark Minervini 전략
                        <span class="score-badge {minervini_score_class}">{minervini_passed}/{minervini_total}</span>
                    </div>
"""

        for key, item in minervini.items():
            if isinstance(item, dict):
                passed = item.get('passed', False)
                excellent = item.get('excellent', False)
                label = item.get('label', '')
                icon = '🌟' if excellent else ('✓' if passed else '✗')
                css_class = 'excellent' if excellent else ('passed' if passed else 'failed')

                html_content += f"""
                    <div class="check-item {css_class}">
                        <div class="check-icon">{icon}</div>
                        <div class="check-label">{label}</div>
                    </div>
"""

        html_content += """
                </div>
            </div>
"""

        # 링크 버튼
        tradingview_url = f"https://www.tradingview.com/chart/?symbol=KRX%3A{ticker}"
        naver_url = f"https://finance.naver.com/item/main.nhn?code={ticker}"

        html_content += f"""
            <div class="btn-group">
                <a href="{tradingview_url}" target="_blank" class="btn btn-tradingview">
                    TradingView 차트 분석 →
                </a>
                <a href="{naver_url}" target="_blank" class="btn btn-naver">
                    네이버 금융 정보 →
                </a>
            </div>
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
                // 캔들스틱 데이터 준비
                const candleData = data.dates.map((date, i) => ({
                    x: new Date(date),
                    o: data.open[i],
                    h: data.high[i],
                    l: data.low[i],
                    c: data.close[i]
                }));

                new Chart(ctx, {
                    type: 'candlestick',
                    data: {
                        datasets: [{
                            label: ticker,
                            data: candleData,
                            borderColor: {
                                up: '#4CAF50',
                                down: '#f5576c',
                                unchanged: '#999',
                            },
                            backgroundColor: {
                                up: 'rgba(76, 175, 80, 0.3)',
                                down: 'rgba(245, 87, 108, 0.3)',
                                unchanged: 'rgba(153, 153, 153, 0.3)',
                            }
                        }, {
                            label: '50일 이평',
                            data: data.dates.map((date, i) => ({x: new Date(date), y: data.ma_50[i]})),
                            type: 'line',
                            borderColor: '#4CAF50',
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: false
                        }, {
                            label: '150일 이평',
                            data: data.dates.map((date, i) => ({x: new Date(date), y: data.ma_150[i]})),
                            type: 'line',
                            borderColor: '#FF9800',
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: false
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: {
                                display: true,
                                labels: {
                                    color: '#fff'
                                }
                            },
                            tooltip: {
                                enabled: true
                            }
                        },
                        scales: {
                            x: {
                                type: 'time',
                                time: {
                                    unit: 'day'
                                },
                                ticks: {
                                    color: '#8b92b8'
                                },
                                grid: {
                                    color: '#2a2f4a'
                                }
                            },
                            y: {
                                ticks: {
                                    color: '#8b92b8',
                                    callback: function(value) {
                                        return value.toLocaleString() + '원';
                                    }
                                },
                                grid: {
                                    color: '#2a2f4a'
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

    print(f"\n[프로 대시보드 생성 완료] {output_file}")
    return output_file


if __name__ == "__main__":
    print("David Ryan 스타일 프로 대시보드 생성...")
