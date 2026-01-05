"""
한국 주식 데이터 수집 모듈
FinanceDataReader를 사용하여 코스피/코스닥 주식 데이터 수집
"""

import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
import time
import requests
import json
from bs4 import BeautifulSoup
from io import StringIO


class StockDataCollector:
    def __init__(self):
        """주식 데이터 수집기 초기화"""
        self.kospi_list = None
        self.kosdaq_list = None

    def get_stock_list(self, market='ALL'):
        """
        한국 주식 종목 리스트 가져오기

        Args:
            market (str): 'KOSPI', 'KOSDAQ', 또는 'ALL'

        Returns:
            DataFrame: 종목 리스트
        """
        print(f"[데이터 수집] {market} 종목 리스트 가져오는 중...")

        def fetch_listing(kind):
            for attempt in range(3):
                try:
                    return fdr.StockListing(kind)
                except Exception as e:
                    if attempt == 2:
                        raise
                    time.sleep(2)

        def fetch_krx_marcap(kind):
            mkt_map = {'KRX-MARCAP':'ALL', 'KRX':'ALL', 'KOSPI':'STK', 'KOSDAQ':'KSQ', 'KONEX':'KNX'}
            if kind not in mkt_map:
                raise ValueError("market은 'KOSPI', 'KOSDAQ', 또는 'ALL'이어야 합니다.")

            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://data.krx.co.kr/'
            }
            url = 'https://data.krx.co.kr/comm/bldAttendant/executeForResourceBundle.cmd?baseName=krx.mdc.i18n.component&key=B128.bld'
            meta = requests.get(url, headers=headers, timeout=10).json()
            date_str = meta['result']['output'][0]['max_work_dt']

            data = {
                'bld': 'dbms/MDC/STAT/standard/MDCSTAT01501',
                'mktId': mkt_map[kind],
                'trdDd': date_str,
                'share': '1',
                'money': '1',
                'csvxls_isNo': 'false',
            }
            url = 'https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd'
            resp = requests.post(url, headers=headers, data=data, timeout=20)
            payload = resp.json()
            df = pd.DataFrame(payload['OutBlock_1'])
            df = df.replace(r',', '', regex=True)
            numeric_cols = ['CMPPREVDD_PRC', 'FLUC_RT', 'TDD_OPNPRC', 'TDD_HGPRC', 'TDD_LWPRC',
                            'ACC_TRDVOL', 'ACC_TRDVAL', 'MKTCAP', 'LIST_SHRS']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            df = df.sort_values('MKTCAP', ascending=False)
            cols_map = {'ISU_SRT_CD':'Code', 'ISU_ABBRV':'Name',
                        'TDD_CLSPRC':'Close', 'SECT_TP_NM': 'Dept', 'FLUC_TP_CD':'ChangeCode',
                        'CMPPREVDD_PRC':'Changes', 'FLUC_RT':'ChagesRatio', 'ACC_TRDVOL':'Volume',
                        'ACC_TRDVAL':'Amount', 'TDD_OPNPRC':'Open', 'TDD_HGPRC':'High', 'TDD_LWPRC':'Low',
                        'MKTCAP':'Marcap', 'LIST_SHRS':'Stocks', 'MKT_NM':'Market', 'MKT_ID': 'MarketId' }
            df = df.rename(columns=cols_map).reset_index(drop=True)
            return df

        def fetch_naver_market_sum(sosok, pages=25):
            rows = []
            for page in range(1, pages + 1):
                url = f"https://finance.naver.com/sise/sise_market_sum.nhn?sosok={sosok}&page={page}"
                resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
                if resp.status_code != 200 or len(resp.text) < 1000:
                    break

                dfs = pd.read_html(StringIO(resp.text), header=0)
                if not dfs:
                    break
                df = None
                for table in dfs:
                    if '종목명' in table.columns:
                        df = table
                        break
                if df is None:
                    break
                df = df.dropna(how='all')

                soup = BeautifulSoup(resp.text, 'html.parser')
                links = soup.select('table.type_2 a')
                codes = []
                for a in links:
                    href = a.get('href', '')
                    if 'code=' in href:
                        code = href.split('code=')[-1]
                        if code.isdigit():
                            codes.append(code.zfill(6))

                df = df[df['종목명'].notna()].reset_index(drop=True)
                if len(codes) < len(df):
                    codes = codes + [None] * (len(df) - len(codes))

                df = df.rename(columns={'종목명': 'Name', '시가총액': 'Marcap', '상장주식수': 'Stocks'})
                df['Code'] = codes[:len(df)]
                df['Market'] = 'KOSPI' if sosok == 0 else 'KOSDAQ'
                df['Marcap'] = pd.to_numeric(df['Marcap'].astype(str).str.replace(',', ''), errors='coerce')
                df['Stocks'] = pd.to_numeric(df['Stocks'].astype(str).str.replace(',', ''), errors='coerce')
                # Naver market sum uses units: Marcap in 억, Stocks in 천주
                df['Marcap'] = df['Marcap'] * 100000000
                df['Stocks'] = df['Stocks'] * 1000
                rows.append(df[['Code', 'Name', 'Market', 'Marcap', 'Stocks']])

            if not rows:
                return pd.DataFrame(columns=['Code', 'Name', 'Market', 'Marcap', 'Stocks'])
            combined = pd.concat(rows, ignore_index=True)
            combined = combined.dropna(subset=['Code'])
            combined = combined.drop_duplicates(subset=['Code']).reset_index(drop=True)
            return combined

        try:
            if market == 'ALL':
                stock_list = fetch_krx_marcap('KRX')
            elif market == 'KOSPI':
                stock_list = fetch_krx_marcap('KOSPI')
            elif market == 'KOSDAQ':
                stock_list = fetch_krx_marcap('KOSDAQ')
            else:
                raise ValueError("market은 'KOSPI', 'KOSDAQ', 또는 'ALL'이어야 합니다.")
        except Exception:
            # Fallback to FDR listing if KRX endpoint fails
            try:
                if market == 'ALL':
                    kospi = fetch_listing('KOSPI')
                    kosdaq = fetch_listing('KOSDAQ')
                    stock_list = pd.concat([kospi, kosdaq], ignore_index=True)
                elif market == 'KOSPI':
                    stock_list = fetch_listing('KOSPI')
                elif market == 'KOSDAQ':
                    stock_list = fetch_listing('KOSDAQ')
                else:
                    raise ValueError("market은 'KOSPI', 'KOSDAQ', 또는 'ALL'이어야 합니다.")
            except Exception:
                # Final fallback to Naver market sum pages
                kospi = fetch_naver_market_sum(0)
                kosdaq = fetch_naver_market_sum(1)
                stock_list = pd.concat([kospi, kosdaq], ignore_index=True)

        print(f"[데이터 수집] 총 {len(stock_list)}개 종목 발견")
        return stock_list

    def get_intraday_price_snapshot(self, market='ALL', pages=25):
        """
        장중 가격 스냅샷(무료/비공식) 수집
        - Naver 시장 요약 페이지 기반 (지연/누락 가능)
        - 반환 컬럼: Code, Name, Market, Close
        """
        def fetch_naver_market_sum(sosok, pages=25):
            rows = []
            for page in range(1, pages + 1):
                url = f"https://finance.naver.com/sise/sise_market_sum.nhn?sosok={sosok}&page={page}"
                resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
                if resp.status_code != 200 or len(resp.text) < 1000:
                    break

                dfs = pd.read_html(StringIO(resp.text), header=0)
                if not dfs:
                    break
                df = None
                for table in dfs:
                    if '종목명' in table.columns:
                        df = table
                        break
                if df is None:
                    break
                df = df.dropna(how='all')

                soup = BeautifulSoup(resp.text, 'html.parser')
                links = soup.select('table.type_2 a')
                codes = []
                for a in links:
                    href = a.get('href', '')
                    if 'code=' in href:
                        code = href.split('code=')[-1]
                        if code.isdigit():
                            codes.append(code.zfill(6))

                df = df[df['종목명'].notna()].reset_index(drop=True)
                if len(codes) < len(df):
                    codes = codes + [None] * (len(df) - len(codes))

                df = df.rename(columns={'종목명': 'Name', '현재가': 'Close'})
                df['Code'] = codes[:len(df)]
                df['Market'] = 'KOSPI' if sosok == 0 else 'KOSDAQ'
                df['Close'] = pd.to_numeric(df['Close'].astype(str).str.replace(',', ''), errors='coerce')
                rows.append(df[['Code', 'Name', 'Market', 'Close']])

            if not rows:
                return pd.DataFrame(columns=['Code', 'Name', 'Market', 'Close'])
            combined = pd.concat(rows, ignore_index=True)
            combined = combined.dropna(subset=['Code'])
            combined = combined.drop_duplicates(subset=['Code']).reset_index(drop=True)
            return combined

        if market == 'ALL':
            kospi = fetch_naver_market_sum(0, pages=pages)
            kosdaq = fetch_naver_market_sum(1, pages=pages)
            snapshot = pd.concat([kospi, kosdaq], ignore_index=True)
        elif market == 'KOSPI':
            snapshot = fetch_naver_market_sum(0, pages=pages)
        elif market == 'KOSDAQ':
            snapshot = fetch_naver_market_sum(1, pages=pages)
        else:
            raise ValueError("market은 'KOSPI', 'KOSDAQ', 또는 'ALL'이어야 합니다.")

        return snapshot.reset_index(drop=True)

    def get_stock_price_data(self, ticker, start_date, end_date=None):
        """
        특정 종목의 가격 데이터 가져오기

        Args:
            ticker (str): 종목 코드
            start_date (str): 시작 날짜 (YYYY-MM-DD)
            end_date (str): 종료 날짜 (YYYY-MM-DD), 없으면 오늘

        Returns:
            DataFrame: 가격 데이터
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        try:
            df = fdr.DataReader(ticker, start_date, end_date)
            return df
        except Exception as e:
            print(f"[오류] {ticker} 데이터 수집 실패: {e}")
            return None

    def get_bulk_price_data(self, stock_list, period_days=252, delay=0.1):
        """
        여러 종목의 가격 데이터 일괄 수집

        Args:
            stock_list (DataFrame): 종목 리스트
            period_days (int): 수집할 기간 (영업일 기준, 252일 = 약 1년)
            delay (float): 각 요청 사이의 지연 시간 (초)

        Returns:
            dict: {종목코드: DataFrame} 형태의 딕셔너리
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days * 2)  # 주말/공휴일 고려해서 2배

        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        price_data = {}
        total = len(stock_list)

        print(f"\n[데이터 수집] {total}개 종목 가격 데이터 수집 시작...")
        print(f"[데이터 수집] 기간: {start_str} ~ {end_str}")

        for idx, row in stock_list.iterrows():
            ticker = row['Code']
            name = row['Name']

            if (idx + 1) % 50 == 0:
                print(f"[진행상황] {idx + 1}/{total} 종목 처리 중... ({name})")

            df = self.get_stock_price_data(ticker, start_str, end_str)

            if df is not None and len(df) > 0:
                price_data[ticker] = df

            time.sleep(delay)  # API 호출 제한 방지

        print(f"\n[데이터 수집 완료] 총 {len(price_data)}개 종목 데이터 수집 성공")
        return price_data

    def filter_tradable_stocks(self, stock_list, min_price=1000, min_market_cap=100):
        """
        거래 가능한 종목만 필터링

        Args:
            stock_list (DataFrame): 종목 리스트
            min_price (int): 최소 주가 (원)
            min_market_cap (int): 최소 시가총액 (억원)

        Returns:
            DataFrame: 필터링된 종목 리스트
        """
        print(f"\n[필터링] 거래 가능 종목 필터링 중...")
        print(f"[필터링] 조건: 주가 >= {min_price}원, 시가총액 >= {min_market_cap}억원")

        # 시가총액이 있는 종목만
        filtered = stock_list[stock_list['Marcap'].notna()].copy()

        # 시가총액 필터링 (억원 단위)
        filtered = filtered[filtered['Marcap'] >= min_market_cap * 100000000]

        # 관리종목, 정리매매 제외
        if 'Sector' in filtered.columns:
            filtered = filtered[~filtered['Sector'].str.contains('관리종목|정리매매', na=False)]

        print(f"[필터링 완료] {len(filtered)}개 종목 선택됨 (전체 {len(stock_list)}개 중)")

        return filtered.reset_index(drop=True)


if __name__ == "__main__":
    # 테스트 코드
    collector = StockDataCollector()

    # 전체 종목 리스트 가져오기
    stock_list = collector.get_stock_list('ALL')
    print(f"\n전체 종목 수: {len(stock_list)}")
    print(stock_list.head())

    # 거래 가능한 종목만 필터링
    tradable_stocks = collector.filter_tradable_stocks(stock_list)
    print(f"\n거래 가능 종목 수: {len(tradable_stocks)}")

    # 샘플로 삼성전자 데이터 가져오기
    print("\n[테스트] 삼성전자 최근 데이터:")
    samsung = collector.get_stock_price_data('005930', '2024-01-01')
    if samsung is not None:
        print(samsung.tail())
