"""
현대적인 2단 레이아웃 대시보드
왼쪽: 종목 리스트, 오른쪽: 차트 + 분석
"""

import pandas as pd
import os
from datetime import datetime
import json
import numpy as np
from advanced_entry_signals import AdvancedEntryAnalyzer
from david_ryan_complete import DavidRyanComplete


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy types"""
    def default(self, obj):
        if isinstance(obj, (np.bool_, np.bool8)):
            return bool(obj)
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def analyze_stock_details(ticker, price_data, rs_rating):
    """종목별 상세 분석"""
    ryan_analyzer = DavidRyanComplete()
    minervini_analyzer = AdvancedEntryAnalyzer()

    ryan_signal = ryan_analyzer.david_ryan_complete_signal(price_data, rs_rating)
    minervini_signal = minervini_analyzer.mark_minervini_advanced_signal(price_data, rs_rating)

    # 디버깅: trend_template 확인
    print(f"\n[{ticker}] RS Rating: {rs_rating}")
    if 'trend_template' in minervini_signal:
        print(f"  trend_template 존재: {minervini_signal['trend_template']}")
    else:
        print(f"  ⚠️ trend_template 없음!")

    return {
        'ryan': ryan_signal,
        'minervini': minervini_signal
    }


def generate_modern_dashboard(entry_signals, price_data_dict, output_file='dashboard_modern.html'):
    """현대적인 2단 레이아웃 대시보드"""

    # 차트 데이터 준비
    chart_data_json = {}
    stock_analysis = {}

    for idx, row in entry_signals.head(20).iterrows():
        ticker = str(row['종목코드']).zfill(6)  # 문자열로 변환하고 6자리 패딩
        if ticker in price_data_dict:
            df = price_data_dict[ticker].tail(252).copy()  # 1년치 데이터

            # 이동평균선 계산
            ma_50 = df['Close'].rolling(50).mean()
            ma_150 = df['Close'].rolling(150).mean() if len(df) >= 150 else pd.Series([None] * len(df))
            ma_200 = df['Close'].rolling(200).mean() if len(df) >= 200 else pd.Series([None] * len(df))

            chart_data_json[ticker] = {
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
            stock_analysis[ticker] = analyze_stock_details(ticker, price_data_dict[ticker], row['RS등급'])

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>David Ryan 진입 신호 대시보드</title>
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

        .container {{
            display: flex;
            height: 100vh;
        }}

        /* 왼쪽 패널 - 종목 리스트 */
        .left-panel {{
            width: 350px;
            background: #131722;
            border-right: 1px solid #2a2e39;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        .header h1 {{
            font-size: 1.3em;
            margin-bottom: 5px;
            color: white;
        }}

        .header .subtitle {{
            font-size: 0.85em;
            opacity: 0.9;
            color: white;
        }}

        .stock-list {{
            flex: 1;
            padding: 10px;
        }}

        .stock-item {{
            background: #1e222d;
            padding: 15px;
            margin-bottom: 8px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }}

        .stock-item:hover {{
            background: #2a2e39;
            border-left-color: #667eea;
        }}

        .stock-item.active {{
            background: #2a2e39;
            border-left-color: #667eea;
            box-shadow: 0 0 0 1px #667eea;
        }}

        .stock-item-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}

        .stock-name {{
            font-size: 1.1em;
            font-weight: bold;
            color: #fff;
        }}

        .stock-code {{
            font-size: 0.85em;
            color: #787b86;
        }}

        .rs-badge {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: bold;
            color: white;
        }}

        .stock-signals {{
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
        }}

        .signal-badge {{
            padding: 3px 8px;
            border-radius: 8px;
            font-size: 0.75em;
            font-weight: 600;
        }}

        .signal-badge.ryan {{ background: #26a69a; color: white; }}
        .signal-badge.minervini {{ background: #2962ff; color: white; }}
        .signal-badge.both {{ background: #ffd700; color: #000; }}

        /* 오른쪽 패널 - 상세 정보 */
        .right-panel {{
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }}

        .detail-header {{
            background: #131722;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
        }}

        .detail-title {{
            font-size: 2em;
            font-weight: bold;
            color: #fff;
            margin-bottom: 10px;
        }}

        .detail-meta {{
            display: flex;
            gap: 20px;
            align-items: center;
        }}

        .meta-item {{
            font-size: 0.95em;
            color: #787b86;
        }}

        .meta-value {{
            color: #d1d4dc;
            font-weight: 600;
        }}

        .external-links {{
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }}

        .external-link {{
            padding: 8px 16px;
            background: #2a2e39;
            color: #d1d4dc;
            text-decoration: none;
            border-radius: 8px;
            font-size: 0.9em;
            font-weight: 600;
            transition: all 0.2s;
            border: 1px solid #2a2e39;
        }}

        .external-link:hover {{
            background: #667eea;
            border-color: #667eea;
            color: white;
        }}

        /* 차트 영역 */
        .chart-section {{
            background: #131722;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }}

        .chart-title {{
            font-size: 1.2em;
            font-weight: 600;
            color: #2962ff;
            margin-bottom: 15px;
        }}

        .combined-chart {{
            position: relative;
            height: 500px;
        }}

        /* 가격 정보 그리드 */
        .price-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}

        .price-card {{
            background: #131722;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 2px solid #2a2e39;
        }}

        .price-label {{
            color: #787b86;
            font-size: 0.85em;
            margin-bottom: 8px;
        }}

        .price-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #fff;
        }}

        .price-value.entry {{ color: #26a69a; }}
        .price-value.stop {{ color: #ef5350; }}

        /* 분석 섹션 */
        .analysis-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}

        .analysis-box {{
            background: #131722;
            padding: 20px;
            border-radius: 12px;
        }}

        .analysis-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2962ff;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .score-badge {{
            background: #2a2e39;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 1.1em;
            font-weight: bold;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}

        .score-badge.excellent {{
            background: linear-gradient(135deg, #26a69a 0%, #1de9b6 100%);
            color: white;
        }}
        .score-badge.good {{
            background: linear-gradient(135deg, #2962ff 0%, #448aff 100%);
            color: white;
        }}
        .score-badge.warning {{
            background: linear-gradient(135deg, #ff9800 0%, #ffb74d 100%);
            color: white;
        }}

        .check-item {{
            padding: 12px;
            margin-bottom: 10px;
            background: #1e222d;
            border-radius: 8px;
            border-left: 4px solid #2a2e39;
            font-size: 1em;
            line-height: 1.6;
        }}

        .check-item.passed {{
            border-left-color: #26a69a;
            background: rgba(38, 166, 154, 0.05);
        }}
        .check-item.failed {{
            border-left-color: #ef5350;
            background: rgba(239, 83, 80, 0.05);
        }}
        .check-item.excellent {{
            border-left-color: #ffd700;
            background: rgba(255, 215, 0, 0.1);
        }}

        .check-icon {{
            display: inline-block;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            text-align: center;
            line-height: 24px;
            font-weight: bold;
            margin-right: 10px;
            font-size: 0.9em;
        }}

        .check-icon.pass {{
            background: #26a69a;
            color: white;
        }}

        .check-icon.fail {{
            background: #ef5350;
            color: white;
        }}

        .check-desc {{
            display: block;
            color: #787b86;
            font-size: 0.85em;
            margin-top: 5px;
            margin-left: 34px;
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

        @media (max-width: 1200px) {{
            .analysis-section {{ grid-template-columns: 1fr; }}
        }}

        @media (max-width: 768px) {{
            .container {{ flex-direction: column; }}
            .left-panel {{ width: 100%; height: 40vh; }}
            .right-panel {{ height: 60vh; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 왼쪽 패널 -->
        <div class="left-panel">
            <div class="header">
                <h1>🎯 David Ryan 진입 신호</h1>
                <div class="subtitle">총 {len(entry_signals)}개 종목 발견 (현재 시점)</div>
            </div>
            <div class="stock-list">
"""

    # 종목 리스트 생성
    for idx, row in entry_signals.head(20).iterrows():
        ticker = str(row['종목코드']).zfill(6)  # 문자열로 변환하고 6자리 패딩
        name = row['종목명']
        rs = row['RS등급']
        ryan = row.get('Ryan_진입신호', False)
        minervini = row.get('미너비니_진입신호', False)
        both = row.get('양쪽_모두_신호', False)

        signals = []
        if both:
            signals.append('<span class="signal-badge both">양쪽 모두 ⭐</span>')
        elif ryan:
            signals.append('<span class="signal-badge ryan">Ryan</span>')
        if minervini and not both:
            signals.append('<span class="signal-badge minervini">Minervini</span>')

        signals_html = ''.join(signals)

        html += f"""
                <div class="stock-item" onclick="showStock('{ticker}')" data-ticker="{ticker}">
                    <div class="stock-item-header">
                        <div>
                            <div class="stock-name">{name}</div>
                            <div class="stock-code">{ticker}</div>
                        </div>
                        <div class="rs-badge">RS {rs}</div>
                    </div>
                    <div class="stock-signals">{signals_html}</div>
                </div>
"""

    html += """
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

    <!-- JSON 데이터를 별도 script 태그에 저장 -->
    <script type="application/json" id="stockData">
""" + json.dumps(json.loads(entry_signals.head(20).to_json(orient='records', force_ascii=False)), cls=NumpyEncoder, ensure_ascii=True) + """
    </script>

    <script type="application/json" id="chartData">
""" + json.dumps(chart_data_json, cls=NumpyEncoder, ensure_ascii=True) + """
    </script>

    <script type="application/json" id="stockAnalysis">
""" + json.dumps(stock_analysis, cls=NumpyEncoder, ensure_ascii=True) + """
    </script>

    <script>
        // JSON 데이터 파싱
        const stockData = JSON.parse(document.getElementById('stockData').textContent);
        const chartData = JSON.parse(document.getElementById('chartData').textContent);
        const stockAnalysis = JSON.parse(document.getElementById('stockAnalysis').textContent);

        // 디버깅: 첫 번째 종목의 분석 데이터 확인
        console.log('=== 디버깅: stockAnalysis ===');
        const firstTicker = Object.keys(stockAnalysis)[0];
        if (firstTicker) {
            console.log('종목:', firstTicker);
            console.log('분석 데이터:', stockAnalysis[firstTicker]);
            if (stockAnalysis[firstTicker].minervini) {
                console.log('Minervini:', stockAnalysis[firstTicker].minervini);
                console.log('trend_template:', stockAnalysis[firstTicker].minervini.trend_template);
            }
        }

        let currentChart = null;

        function showStock(ticker) {
            console.log('=== showStock called ===');
            console.log('ticker:', ticker);

            // 종목 데이터 찾기 (함수 최상위 레벨에서 선언)
            console.log('stockData length:', stockData.length);
            console.log('First stock 종목코드:', stockData[0]?.종목코드);
            const stock = stockData.find(s => s.종목코드 === ticker);
            console.log('Found stock:', stock);
            if (!stock) {
                console.error('Stock not found! ticker:', ticker);
                console.log('Available 종목코드:', stockData.map(s => s.종목코드));
                return;
            }

            console.log('chartData keys:', Object.keys(chartData));
            const data = chartData[ticker];
            console.log('Found chart data:', data ? 'yes' : 'no');
            if (!data) {
                console.error('Chart data not found! ticker:', ticker);
                return;
            }

            try {
                // 활성화 표시
                document.querySelectorAll('.stock-item').forEach(item => {
                    item.classList.remove('active');
                });
                document.querySelector(`[data-ticker="${ticker}"]`).classList.add('active');
            } catch (err) {
                console.error('Error in showStock:', err);
                return;
            }

            // 상세 화면 생성
            let html = `
                <div class="detail-header">
                    <div class="detail-title">${stock.종목명}</div>
                    <div class="detail-meta">
                        <div class="meta-item">종목코드: <span class="meta-value">${stock.종목코드}</span></div>
                        <div class="meta-item">RS 등급: <span class="meta-value">${stock.RS등급}</span></div>
                        <div class="meta-item">현재가: <span class="meta-value">${stock.현재가?.toLocaleString()}원</span></div>
                    </div>
                    <div class="external-links">
                        <a href="https://www.tradingview.com/chart/?symbol=KRX:${ticker}" target="_blank" class="external-link">
                            📈 TradingView에서 보기
                        </a>
                        <a href="https://finance.naver.com/item/main.naver?code=${ticker}" target="_blank" class="external-link">
                            📊 네이버 증권에서 보기
                        </a>
                    </div>
                </div>

                <div class="chart-section">
                    <div class="chart-title">📊 가격 & 거래량 차트</div>
                    <div class="combined-chart">
                        <canvas id="combined-chart"></canvas>
                    </div>
                </div>

                <div class="price-grid">
                    <div class="price-card">
                        <div class="price-label">현재가</div>
                        <div class="price-value">${stock.현재가?.toLocaleString()}원</div>
                    </div>
            `;

            if (stock.Ryan_진입가) {
                html += `
                    <div class="price-card">
                        <div class="price-label">🎯 Ryan 진입가</div>
                        <div class="price-value entry">${stock.Ryan_진입가?.toLocaleString()}원</div>
                    </div>
                    <div class="price-card">
                        <div class="price-label">🛑 Ryan 손절가</div>
                        <div class="price-value stop">${stock.Ryan_손절가?.toLocaleString()}원</div>
                    </div>
                `;

                if (stock.Ryan_추가매수1) {
                    html += `
                        <div class="price-card">
                            <div class="price-label">➕ 추가매수 1차</div>
                            <div class="price-value entry">${stock.Ryan_추가매수1?.toLocaleString()}원</div>
                        </div>
                    `;
                }

                if (stock.Ryan_손익비) {
                    html += `
                        <div class="price-card">
                            <div class="price-label">📊 손익비</div>
                            <div class="price-value">${stock.Ryan_손익비?.toFixed(2)}:1</div>
                        </div>
                    `;
                }
            }

            html += '</div>';

            // 디버깅 패널 (임시)
            html += '<div style="background: #ff9800; color: #000; padding: 15px; border-radius: 10px; margin-bottom: 20px;">';
            html += '<h3>🔧 디버깅 정보</h3>';
            const analysis = stockAnalysis[ticker];
            if (analysis && analysis.minervini && analysis.minervini.trend_template) {
                const tt = analysis.minervini.trend_template;
                html += '<pre style="color: #000; font-size: 12px;">';
                html += 'trend_template:\\n';
                html += JSON.stringify(tt, null, 2);
                html += '</pre>';
            } else {
                html += '<p>⚠️ trend_template 데이터 없음!</p>';
            }
            html += '</div>';

            // 분석 섹션
            html += '<div class="analysis-section">';

            // David Ryan 분석 - 전체 조건 표시
            if (analysis && analysis.ryan) {
                const ryan = analysis.ryan;
                const scoreClass = stock.Ryan_신호강도 >= 80 ? 'excellent' : stock.Ryan_신호강도 >= 60 ? 'good' : 'warning';

                html += `
                    <div class="analysis-box">
                        <div class="analysis-title">
                            🎯 David Ryan 완전 전략
                            <span class="score-badge ${scoreClass}">${stock.Ryan_신호강도}점</span>
                        </div>
                `;

                // 모든 조건 체크리스트 (상세 설명 포함)
                const checks = [
                    {
                        label: 'RS Rating ≥ 90',
                        desc: '상대강도지수 90 이상: 전체 종목 중 상위 10% 성과를 보이는 주도주',
                        passed: ryan.rs_check || false
                    },
                    {
                        label: '이동평균선 정배열',
                        desc: '현재가 > 50일선 > 150일선 > 200일선: 강한 상승추세 확인',
                        passed: ryan.ma_alignment || false
                    },
                    {
                        label: '52주 포지션 양호',
                        desc: '현재가가 52주 최고가 대비 -15% 이내: 신고가 근처에서 거래',
                        passed: ryan.year_position_check || false
                    },
                    {
                        label: 'VCP 패턴',
                        desc: '변동성 축소 패턴: 조정 폭이 점점 감소하며 베이스 형성',
                        passed: ryan.vcp_detected || false
                    },
                    {
                        label: 'VDU (거래량 감소)',
                        desc: '거래량 건조: 돌파 직전 거래량이 50일 평균의 50% 이하로 감소',
                        passed: ryan.vdu_detected || false
                    },
                    {
                        label: '피봇 돌파',
                        desc: '베이스 패턴의 저항선을 상향 돌파하는 시점',
                        passed: ryan.pivot_breakout || false
                    },
                    {
                        label: '거래량 증가 확인',
                        desc: '돌파 시 거래량이 50일 평균 대비 40% 이상 증가',
                        passed: ryan.volume_surge || false
                    }
                ];

                checks.forEach(check => {
                    const iconClass = check.passed ? 'pass' : 'fail';
                    const iconText = check.passed ? '⭕' : '❌';
                    const cssClass = check.passed ? 'passed' : 'failed';
                    html += `
                        <div class="check-item ${cssClass}">
                            <span class="check-icon ${iconClass}">${iconText}</span>
                            <strong>${check.label}</strong>
                            <span class="check-desc">${check.desc}</span>
                        </div>
                    `;
                });

                // 경고사항
                if (stock.Ryan_경고) {
                    const warnings = stock.Ryan_경고.split(' | ').filter(w => w.trim());
                    warnings.forEach(warning => {
                        html += `<div class="check-item failed">⚠️ ${warning}</div>`;
                    });
                }

                html += '</div>';
            }

            // Minervini 분석 - Trend Template 8가지 조건 전체 표시
            if (analysis && analysis.minervini) {
                const minervini = analysis.minervini;
                const scoreClass = stock.미너비니_신호강도 >= 80 ? 'excellent' : stock.미너비니_신호강도 >= 60 ? 'good' : 'warning';

                html += `
                    <div class="analysis-box">
                        <div class="analysis-title">
                            📈 Mark Minervini Trend Template
                            <span class="score-badge ${scoreClass}">${stock.미너비니_신호강도}점</span>
                        </div>
                `;

                // Trend Template 8가지 조건 (상세 설명 포함)
                const template = minervini.trend_template || {};
                const checks = [
                    {
                        label: '1. 현재가 > 150일/200일 이평',
                        desc: '가격이 장기 이동평균선 위에서 거래: Stage 2 상승 추세 확인',
                        passed: template.above_150_200 || false
                    },
                    {
                        label: '2. 150일 이평 > 200일 이평',
                        desc: '중기선이 장기선보다 위: 추세 전환 완료',
                        passed: template.ma150_above_200 || false
                    },
                    {
                        label: '3. 200일 이평선 상승 중',
                        desc: '장기 추세선이 상승: 지속 가능한 상승장',
                        passed: template.ma200_rising || false
                    },
                    {
                        label: '4. 50일 이평 > 150일/200일 이평',
                        desc: '단기선이 중장기선 위: 강한 모멘텀',
                        passed: template.ma50_above_150_200 || false
                    },
                    {
                        label: '5. 현재가 > 50일 이평',
                        desc: '단기 추세 상승 중: 조정 없이 상승',
                        passed: template.above_50 || false
                    },
                    {
                        label: '6. 현재가 52주 최저가 대비 +30%',
                        desc: '바닥에서 충분히 상승: 베이스 형성 완료',
                        passed: template.above_52w_low || false
                    },
                    {
                        label: '7. 현재가 52주 최고가 대비 -25% 이내',
                        desc: '고점 근처 거래: 신고가 돌파 가능성',
                        passed: template.near_52w_high || false
                    },
                    {
                        label: '8. RS Rating ≥ 70',
                        desc: '상위 30% 성과: 시장 대비 우수한 수익률',
                        passed: template.rs_strong || false
                    }
                ];

                checks.forEach(check => {
                    const iconClass = check.passed ? 'pass' : 'fail';
                    const iconText = check.passed ? '⭕' : '❌';
                    const cssClass = check.passed ? 'passed' : 'failed';
                    html += `
                        <div class="check-item ${cssClass}">
                            <span class="check-icon ${iconClass}">${iconText}</span>
                            <strong>${check.label}</strong>
                            <span class="check-desc">${check.desc}</span>
                        </div>
                    `;
                });

                // VCP 패턴 정보
                if (minervini.vcp_stage) {
                    html += `<div class="check-item excellent">🎯 VCP 단계: ${minervini.vcp_stage}</div>`;
                }

                html += '</div>';
            }

            html += '</div>';

            document.getElementById('detail-content').innerHTML = html;

            // 차트 그리기
            drawCombinedChart(data, ticker);
        }

        function drawCombinedChart(data, ticker) {
            if (currentChart) {
                currentChart.destroy();
            }

            // 거래량 스케일 조정 - 로그 스케일로 차이 강조
            const maxVolume = Math.max(...data.volume.filter(v => v !== null && v > 0));
            const minVolume = Math.min(...data.volume.filter(v => v !== null && v > 0));
            const priceMax = Math.max(...data.high.filter(v => v !== null));
            const priceMin = Math.min(...data.low.filter(v => v !== null));
            const priceRange = priceMax - priceMin;

            // 로그 스케일 적용하여 작은 거래량 차이도 보이게
            const scaledVolume = data.volume.map(v => {
                if (!v || v <= 0) return priceMin;
                const logV = Math.log(v / minVolume + 1);
                const logMax = Math.log(maxVolume / minVolume + 1);
                return priceMin + (logV / logMax) * priceRange * 0.25;
            });

            // 차트 어노테이션 생성 - 여러 개 화살표로 표시
            const annotations = {};
            const analysis = stockAnalysis[ticker];

            if (analysis && analysis.ryan) {
                const ryan = analysis.ryan;

                // 최근 데이터 기준으로 여러 시점 찾기
                const recentDays = 20; // 최근 20일 범위
                const startIdx = Math.max(0, data.dates.length - recentDays);

                // 거래량 급증 시점들 찾기 (평균 대비 40% 이상)
                const avgVolume = data.volume.slice(startIdx).reduce((a, b) => a + b, 0) / recentDays;
                const volumeSurgePoints = [];

                for (let i = startIdx; i < data.volume.length; i++) {
                    if (data.volume[i] > avgVolume * 1.4) {
                        volumeSurgePoints.push(i);
                    }
                }

                // 1. VCP 패턴 화살표 (최근 10일 이내)
                if (ryan.vcp_detected) {
                    const vcpIdx = data.dates.length - 8;
                    annotations.vcp = {
                        type: 'label',
                        xValue: vcpIdx,
                        yValue: data.low[vcpIdx] * 0.97,
                        content: '📐 VCP',
                        backgroundColor: 'rgba(255, 193, 7, 0.95)',
                        color: 'white',
                        font: { size: 10, weight: 'bold' },
                        padding: 6,
                        borderRadius: 6,
                        callout: {
                            display: true,
                            side: 'top',
                            borderColor: '#ffc107',
                            borderWidth: 2
                        }
                    };
                }

                // 2. 거래량 감소 화살표 (VDU)
                if (ryan.vdu_detected) {
                    const vduIdx = data.dates.length - 5;
                    annotations.vdu = {
                        type: 'label',
                        xValue: vduIdx,
                        yValue: scaledVolume[vduIdx] * 0.85,
                        content: '💧 VDU',
                        backgroundColor: 'rgba(33, 150, 243, 0.95)',
                        color: 'white',
                        font: { size: 10, weight: 'bold' },
                        padding: 6,
                        borderRadius: 6,
                        callout: {
                            display: true,
                            side: 'top',
                            borderColor: '#2196f3',
                            borderWidth: 2
                        }
                    };
                }

                // 3. 피봇 돌파 화살표
                if (ryan.pivot_breakout) {
                    const pivotIdx = data.dates.length - 3;
                    annotations.pivot = {
                        type: 'label',
                        xValue: pivotIdx,
                        yValue: data.high[pivotIdx] * 1.02,
                        content: '🚀 피봇',
                        backgroundColor: 'rgba(156, 39, 176, 0.95)',
                        color: 'white',
                        font: { size: 10, weight: 'bold' },
                        padding: 6,
                        borderRadius: 6,
                        callout: {
                            display: true,
                            side: 'bottom',
                            borderColor: '#9c27b0',
                            borderWidth: 2
                        }
                    };
                }

                // 4. 거래량 급증 화살표들 (여러 개 가능)
                volumeSurgePoints.forEach((idx, i) => {
                    if (i < 3) { // 최대 3개만 표시
                        annotations[`volumeSurge${i}`] = {
                            type: 'label',
                            xValue: idx,
                            yValue: scaledVolume[idx] * 1.1,
                            content: '📊',
                            backgroundColor: 'rgba(244, 67, 54, 0.95)',
                            color: 'white',
                            font: { size: 12, weight: 'bold' },
                            padding: 4,
                            borderRadius: 6,
                            callout: {
                                display: true,
                                side: 'bottom',
                                borderColor: '#f44336',
                                borderWidth: 2
                            }
                        };
                    }
                });

                // 5. 메인 진입 시점 (모든 조건 종합)
                const entryIdx = data.dates.length - 2;
                const entryPrice = data.close[entryIdx];

                // 조건 개수 세기
                const passedCount = [
                    ryan.rs_check,
                    ryan.ma_alignment,
                    ryan.year_position_check,
                    ryan.vcp_detected,
                    ryan.vdu_detected,
                    ryan.pivot_breakout,
                    ryan.volume_surge
                ].filter(Boolean).length;

                if (passedCount >= 4) { // 4개 이상 조건 충족 시 메인 진입 표시
                    annotations.mainEntry = {
                        type: 'label',
                        xValue: entryIdx,
                        yValue: entryPrice * 1.08,
                        content: [`🎯 진입 (${passedCount}/7)`],
                        backgroundColor: 'rgba(38, 166, 154, 0.95)',
                        color: 'white',
                        font: { size: 12, weight: 'bold' },
                        padding: 10,
                        borderRadius: 8,
                        callout: {
                            display: true,
                            side: 'bottom',
                            borderColor: '#26a69a',
                            borderWidth: 3
                        }
                    };

                    // 진입 포인트 점
                    annotations.entryPoint = {
                        type: 'point',
                        xValue: entryIdx,
                        yValue: entryPrice,
                        backgroundColor: '#26a69a',
                        borderColor: 'white',
                        borderWidth: 3,
                        radius: 10
                    };
                }
            }

            const ctx = document.getElementById('combined-chart');
            currentChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [
                        // 거래량 (로그 스케일 적용, 맨 뒤에)
                        {
                            label: '거래량',
                            data: scaledVolume,
                            type: 'bar',
                            backgroundColor: data.volume.map((vol, idx) => {
                                if (idx === 0) return 'rgba(102, 126, 234, 0.25)';
                                return data.close[idx] >= data.close[idx-1]
                                    ? 'rgba(38, 166, 154, 0.25)'  // 상승일 녹색 (투명도 높임)
                                    : 'rgba(239, 83, 80, 0.25)';   // 하락일 빨강
                            }),
                            yAxisID: 'y',
                            order: 3
                        },
                        // 종가 라인 (굵게)
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
                        // 50일 이평
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
                        // 150일 이평
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
                        // 200일 이평
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
                                            `시가: ${data.open[idx]?.toLocaleString()}원`,
                                            `고가: ${data.high[idx]?.toLocaleString()}원`,
                                            `저가: ${data.low[idx]?.toLocaleString()}원`,
                                            `종가: ${data.close[idx]?.toLocaleString()}원`
                                        ];
                                    } else if (label === '거래량') {
                                        return `거래량: ${data.volume[idx]?.toLocaleString()}`;
                                    } else {
                                        return `${label}: ${context.parsed.y?.toLocaleString()}원`;
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
                            // 라벨이 잘리지 않도록 Y축 범위 조정
                            grace: '10%'
                        }
                    }
                }
            });
        }

        // 첫 번째 종목 자동 선택
        if (stockData.length > 0) {
            showStock(stockData[0].종목코드);
        }
    </script>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n[Modern Dashboard 생성] {output_file}")
    return output_file


if __name__ == "__main__":
    print("Modern Dashboard 생성 모듈...")
