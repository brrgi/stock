"""
TradingView 스타일 차트 대시보드
Lightweight Charts 사용
"""

import pandas as pd
import os
from datetime import datetime
import json
from advanced_entry_signals import AdvancedEntryAnalyzer


def analyze_stock_details(ticker, price_data, rs_rating):
    """종목별 상세 분석"""
    analyzer = AdvancedEntryAnalyzer()

    details = {'ryan': {}, 'minervini': {}}

    if len(price_data) < 60:
        return details

    # David Ryan 분석
    htf = analyzer.check_high_tight_flag(price_data)
    base = analyzer.check_base_quality(price_data)
    dryup = analyzer.check_volume_dryup(price_data)
    volume_bo = analyzer.check_volume_breakout(price_data)

    current_price = price_data['Close'].iloc[-1]
    pivot = price_data['High'].iloc[-30:].max()
    distance_from_pivot = ((pivot - current_price) / pivot) * 100

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
            'label': f"High Tight Flag 패턴 ({htf.get('gain', 0):.0f}% 상승)" if htf['pattern'] else 'High Tight Flag 패턴 미형성'
        },
        'base_quality': {
            'passed': base['score'] >= 70,
            'label': f"베이스 품질 {base['quality']} (깊이 {base['depth']:.1f}%, 타이트 {base['tightness']:.1f}%)"
        },
        'volume_dryup': {
            'passed': dryup['dryup'],
            'label': f"거래량 건조 ({dryup['ratio']:.0f}%)" if dryup['dryup'] else '거래량 건조 미확인'
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
            'template_1': {'passed': current_price > ma_150, 'label': f'현재가({current_price:,.0f}) > 150일 이평({ma_150:,.0f})'},
            'template_2': {'passed': current_price > ma_200, 'label': f'현재가 > 200일 이평({ma_200:,.0f})'},
            'template_3': {'passed': ma_150 > ma_200, 'label': f'150일({ma_150:,.0f}) > 200일({ma_200:,.0f})'},
            'template_4': {'passed': template['score'] >= 87.5, 'label': '200일 이평선 상승 추세'},
            'template_5': {'passed': ma_50 > ma_150, 'label': f'50일({ma_50:,.0f}) > 150일'},
            'template_6': {'passed': current_price > ma_50, 'label': f'현재가 > 50일 이평({ma_50:,.0f})'},
            'template_7': {'passed': template['checks_passed'] >= 7, 'label': '52주 최저 대비 30% 이상'},
            'template_8': {'passed': distance_from_high <= 25, 'label': f'52주 최고가 25% 이내({distance_from_high:.1f}%)'},
            'vcp_pattern': {'passed': vcp['vcp'], 'label': f"VCP {vcp['quality']}" if vcp['vcp'] else 'VCP 미형성'},
            'rs_rating': {'passed': rs_rating >= 80, 'excellent': rs_rating >= 90, 'label': f'RS {rs_rating}'}
        }

    return details


def generate_tradingview_dashboard(entry_signals, price_data_dict, output_file='dashboard_final.html'):
    """TradingView 스타일 최종 대시보드"""

    stock_details = {}
    for idx, row in entry_signals.head(20).iterrows():
        ticker = row['종목코드']
        if ticker in price_data_dict:
            stock_details[ticker] = analyze_stock_details(ticker, price_data_dict[ticker], row['RS등급'])

    # 차트 데이터
    chart_data_json = {}
    for idx, row in entry_signals.head(20).iterrows():
        ticker = row['종목코드']
        if ticker in price_data_dict:
            df = price_data_dict[ticker].tail(120).copy()

            # 캔들스틱 데이터
            candles = []
            volumes = []
            for date, row_data in df.iterrows():
                date_str = date.strftime('%Y-%m-%d')
                candles.append({
                    'time': date_str,
                    'open': float(row_data['Open']),
                    'high': float(row_data['High']),
                    'low': float(row_data['Low']),
                    'close': float(row_data['Close'])
                })
                volumes.append({
                    'time': date_str,
                    'value': float(row_data['Volume']),
                    'color': '#26a69a' if row_data['Close'] >= row_data['Open'] else '#ef5350'
                })

            # 이동평균선
            ma_50_data = []
            ma_150_data = []
            for i in range(len(df)):
                date_str = df.index[i].strftime('%Y-%m-%d')
                if i >= 49:
                    ma_50 = df['Close'].iloc[i-49:i+1].mean()
                    ma_50_data.append({'time': date_str, 'value': float(ma_50)})
                if i >= 149:
                    ma_150 = df['Close'].iloc[i-149:i+1].mean()
                    ma_150_data.append({'time': date_str, 'value': float(ma_150)})

            chart_data_json[ticker] = {
                'candles': candles,
                'volume': volumes,
                'ma50': ma_50_data,
                'ma150': ma_150_data
            }

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>주식 진입 신호 - TradingView 스타일</title>
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0e27;
            color: #d1d4dc;
            padding: 20px;
        }}
        .container {{ max-width: 1800px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px;
            border-radius: 20px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; color: white; }}
        .stock-card {{
            background: #131722;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        .stock-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #2a2e39;
        }}
        .stock-name {{ font-size: 2em; font-weight: bold; color: #fff; }}
        .stock-code {{ color: #787b86; font-size: 1.1em; margin-top: 5px; }}
        .rs-badge {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 15px 30px;
            border-radius: 30px;
            font-size: 1.5em;
            font-weight: bold;
            color: white;
        }}
        .chart-wrapper {{
            background: #1e222d;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        .chart-title {{
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #2962ff;
            font-weight: 600;
        }}
        .chart-container {{ height: 500px; margin-bottom: 10px; }}
        .volume-container {{ height: 150px; }}
        .price-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .price-item {{
            background: #1e222d;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 2px solid #2a2e39;
        }}
        .price-label {{ color: #787b86; font-size: 0.9em; margin-bottom: 10px; }}
        .price-value {{ font-size: 1.6em; font-weight: bold; color: #fff; }}
        .price-value.entry {{ color: #26a69a; }}
        .price-value.stop {{ color: #ef5350; }}
        .analysis-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}
        .analysis-box {{
            background: #1e222d;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #2a2e39;
        }}
        .analysis-title {{
            font-size: 1.4em;
            font-weight: bold;
            margin-bottom: 20px;
            color: #2962ff;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .score-badge {{
            background: #2a2e39;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.7em;
            margin-left: auto;
        }}
        .score-badge.excellent {{ background: #26a69a; }}
        .score-badge.good {{ background: #2962ff; }}
        .score-badge.warning {{ background: #ff9800; }}
        .check-item {{
            display: flex;
            align-items: center;
            padding: 12px;
            margin-bottom: 10px;
            background: #131722;
            border-radius: 10px;
            border-left: 4px solid #2a2e39;
        }}
        .check-item.passed {{ border-left-color: #26a69a; }}
        .check-item.failed {{ border-left-color: #ef5350; }}
        .check-item.excellent {{ border-left-color: #ffd700; background: rgba(255, 215, 0, 0.05); }}
        .check-icon {{ font-size: 1.3em; margin-right: 15px; min-width: 30px; }}
        .check-label {{ flex: 1; color: #d1d4dc; }}
        .btn-group {{ display: flex; gap: 15px; margin-top: 20px; }}
        .btn {{
            flex: 1;
            padding: 15px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: bold;
            text-align: center;
            transition: all 0.3s;
        }}
        .btn-tradingview {{ background: #2962ff; color: white; }}
        .btn-tradingview:hover {{ background: #1e53e5; transform: translateY(-2px); }}
        .btn-naver {{ background: #03c75a; color: white; }}
        .btn-naver:hover {{ background: #02b350; transform: translateY(-2px); }}
        @media (max-width: 1200px) {{ .analysis-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 주식 진입 신호 분석</h1>
            <div style="font-size: 1.1em; margin-top: 10px;">David Ryan & Mark Minervini 전략</div>
            <div style="font-size: 0.9em; opacity: 0.8; margin-top: 10px;">{datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}</div>
        </div>
"""

    for idx, row in entry_signals.head(20).iterrows():
        ticker = row['종목코드']
        name = row['종목명']
        rs = row['RS등급']
        current_price = row['현재가']

        details = stock_details.get(ticker, {})
        ryan = details.get('ryan', {})
        minervini = details.get('minervini', {})

        ryan_passed = sum(1 for v in ryan.values() if isinstance(v, dict) and v.get('passed', False))
        ryan_total = len([k for k in ryan.keys() if isinstance(ryan[k], dict)])
        minervini_passed = sum(1 for v in minervini.values() if isinstance(v, dict) and v.get('passed', False))
        minervini_total = len([k for k in minervini.keys() if isinstance(minervini[k], dict)])

        html += f"""
        <div class="stock-card">
            <div class="stock-header">
                <div>
                    <div class="stock-name">{name}</div>
                    <div class="stock-code">{ticker}</div>
                </div>
                <div class="rs-badge">RS {rs}</div>
            </div>

            <div class="chart-wrapper">
                <div class="chart-title">📊 캔들스틱 차트</div>
                <div id="chart-{ticker}" class="chart-container"></div>
                <div id="volume-{ticker}" class="volume-container"></div>
            </div>

            <div class="price-info">
                <div class="price-item">
                    <div class="price-label">현재가</div>
                    <div class="price-value">{current_price:,.0f}원</div>
                </div>
"""

        if 'Ryan_진입가' in row and pd.notna(row['Ryan_진입가']):
            html += f"""
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
            html += f"""
                <div class="price-item">
                    <div class="price-label">🎯 Minervini 진입가</div>
                    <div class="price-value entry">{row['미너비니_진입가']:,.0f}원</div>
                </div>
                <div class="price-item">
                    <div class="price-label">🛑 Minervini 손절가</div>
                    <div class="price-value stop">{row['미너비니_손절가']:,.0f}원</div>
                </div>
"""

        html += """
            </div>
            <div class="analysis-grid">
"""

        # David Ryan
        ryan_class = 'excellent' if ryan_passed >= 6 else 'good' if ryan_passed >= 4 else 'warning'
        html += f"""
                <div class="analysis-box">
                    <div class="analysis-title">
                        🎯 David Ryan 전략
                        <span class="score-badge {ryan_class}">{ryan_passed}/{ryan_total}</span>
                    </div>
"""
        for item in ryan.values():
            if isinstance(item, dict):
                icon = '🌟' if item.get('excellent') else ('✓' if item.get('passed') else '✗')
                css = 'excellent' if item.get('excellent') else ('passed' if item.get('passed') else 'failed')
                html += f"""
                    <div class="check-item {css}">
                        <div class="check-icon">{icon}</div>
                        <div class="check-label">{item.get('label', '')}</div>
                    </div>
"""
        html += """
                </div>
"""

        # Mark Minervini
        minervini_class = 'excellent' if minervini_passed >= 9 else 'good' if minervini_passed >= 7 else 'warning'
        html += f"""
                <div class="analysis-box">
                    <div class="analysis-title">
                        📈 Mark Minervini 전략
                        <span class="score-badge {minervini_class}">{minervini_passed}/{minervini_total}</span>
                    </div>
"""
        for item in minervini.values():
            if isinstance(item, dict):
                icon = '🌟' if item.get('excellent') else ('✓' if item.get('passed') else '✗')
                css = 'excellent' if item.get('excellent') else ('passed' if item.get('passed') else 'failed')
                html += f"""
                    <div class="check-item {css}">
                        <div class="check-icon">{icon}</div>
                        <div class="check-label">{item.get('label', '')}</div>
                    </div>
"""
        html += """
                </div>
            </div>
"""

        # 링크
        html += f"""
            <div class="btn-group">
                <a href="https://www.tradingview.com/chart/?symbol=KRX%3A{ticker}" target="_blank" class="btn btn-tradingview">
                    TradingView 차트 분석 →
                </a>
                <a href="https://finance.naver.com/item/main.nhn?code={ticker}" target="_blank" class="btn btn-naver">
                    네이버 금융 정보 →
                </a>
            </div>
        </div>
"""

    html += """
    </div>
    <script>
        const chartData = """ + json.dumps(chart_data_json) + """;

        Object.keys(chartData).forEach(ticker => {
            const data = chartData[ticker];

            // 캔들스틱 차트
            const chartEl = document.getElementById('chart-' + ticker);
            const chart = LightweightCharts.createChart(chartEl, {
                layout: { background: { color: '#1e222d' }, textColor: '#d1d4dc' },
                grid: { vertLines: { color: '#2a2e39' }, horzLines: { color: '#2a2e39' } },
                crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
                timeScale: { borderColor: '#2a2e39' },
                rightPriceScale: { borderColor: '#2a2e39' }
            });

            const candleSeries = chart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350'
            });
            candleSeries.setData(data.candles);

            // 50일 이평선
            if (data.ma50 && data.ma50.length > 0) {
                const ma50 = chart.addLineSeries({ color: '#26a69a', lineWidth: 2 });
                ma50.setData(data.ma50);
            }

            // 150일 이평선
            if (data.ma150 && data.ma150.length > 0) {
                const ma150 = chart.addLineSeries({ color: '#ff9800', lineWidth: 2 });
                ma150.setData(data.ma150);
            }

            chart.timeScale().fitContent();

            // 거래량 차트
            const volumeEl = document.getElementById('volume-' + ticker);
            const volumeChart = LightweightCharts.createChart(volumeEl, {
                layout: { background: { color: '#1e222d' }, textColor: '#d1d4dc' },
                grid: { vertLines: { color: '#2a2e39' }, horzLines: { color: '#2a2e39' } },
                timeScale: { borderColor: '#2a2e39', visible: false },
                rightPriceScale: { borderColor: '#2a2e39' }
            });

            const volumeSeries = volumeChart.addHistogramSeries({
                priceFormat: { type: 'volume' },
                priceScaleId: ''
            });
            volumeSeries.setData(data.volume);

            volumeChart.timeScale().fitContent();
        });
    </script>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n[TradingView 스타일 대시보드 생성] {output_file}")
    return output_file


if __name__ == "__main__":
    print("TradingView 스타일 대시보드...")
