"""
CSV 파일 컬럼명을 한글로 변환
"""

import pandas as pd
import os
from glob import glob


def convert_entry_signals_to_korean(df):
    """진입 신호 파일 컬럼명 한글 변환"""
    korean_columns = {
        'Code': '종목코드',
        'Name': '종목명',
        'RS_Rating': 'RS등급',
        'Current_Price': '현재가',
        'ONeil_Signal': '오닐_진입신호',
        'ONeil_Strength': '오닐_신호강도',
        'ONeil_Entry': '오닐_진입가',
        'ONeil_Stop': '오닐_손절가',
        'ONeil_Reasons': '오닐_근거',
        'Minervini_Signal': '미너비니_진입신호',
        'Minervini_Strength': '미너비니_신호강도',
        'Minervini_Entry': '미너비니_진입가',
        'Minervini_Stop': '미너비니_손절가',
        'Minervini_Reasons': '미너비니_근거',
        'Both_Signal': '양쪽_모두_신호'
    }

    return df.rename(columns=korean_columns)


def convert_leading_stocks_to_korean(df):
    """주도주 파일 컬럼명 한글 변환"""
    korean_columns = {
        'Code': '종목코드',
        'Name': '종목명',
        'RS_Rating': 'RS등급',
        'Performance': '수익률(%)',
        'Volume_Surge': '거래량증가율(%)',
        'Price_Strength': '가격강도(%)',
        'Volatility': '변동성(%)',
        'Current_Price': '현재가',
        '52W_High': '52주최고가',
        'Market': '시장',
        'Sector': '업종',
        'MarketCap': '시가총액'
    }

    return df.rename(columns=korean_columns)


def convert_top_rs_to_korean(df):
    """RS Rating 상위 종목 파일 컬럼명 한글 변환"""
    korean_columns = {
        'Code': '종목코드',
        'ISU_CD': '표준코드',
        'Name': '종목명',
        'Market': '시장',
        'Dept': '부문',
        'Close': '종가',
        'ChangeCode': '대비부호',
        'Changes': '대비',
        'ChagesRatio': '등락률',
        'Open': '시가',
        'High': '고가',
        'Low': '저가',
        'Volume': '거래량',
        'Amount': '거래대금',
        'Marcap': '시가총액',
        'Stocks': '상장주식수',
        'MarketId': '시장ID',
        'Performance': '수익률(%)',
        'RS_Rating': 'RS등급'
    }

    return df.rename(columns=korean_columns)


def convert_all_csv_files():
    """results 폴더의 모든 CSV 파일을 한글로 변환"""

    results_folder = 'results'

    if not os.path.exists(results_folder):
        print("results 폴더가 없습니다.")
        return

    # 모든 CSV 파일 찾기
    csv_files = glob(os.path.join(results_folder, '*.csv'))

    if not csv_files:
        print("CSV 파일이 없습니다.")
        return

    print(f"\n총 {len(csv_files)}개 파일 변환 시작...\n")

    for csv_file in csv_files:
        try:
            # 파일명에서 타입 판단
            filename = os.path.basename(csv_file)

            # CSV 읽기
            df = pd.read_csv(csv_file, encoding='utf-8-sig')

            # 파일 타입에 따라 변환
            if 'entry_signals' in filename:
                df_korean = convert_entry_signals_to_korean(df)
                print(f"[OK] {filename} - 진입신호 파일 변환 완료")
            elif 'leading_stocks' in filename:
                df_korean = convert_leading_stocks_to_korean(df)
                print(f"[OK] {filename} - 주도주 파일 변환 완료")
            elif 'top_rs' in filename or 'high_potential' in filename:
                # 컬럼 확인 후 적절한 변환 함수 선택
                if 'ISU_CD' in df.columns:
                    df_korean = convert_top_rs_to_korean(df)
                else:
                    df_korean = convert_leading_stocks_to_korean(df)
                print(f"[OK] {filename} - RS등급 파일 변환 완료")
            else:
                print(f"[?] {filename} - 알 수 없는 파일 형식, 건너뜀")
                continue

            # 한글 버전으로 저장 (원본 덮어쓰기)
            df_korean.to_csv(csv_file, index=False, encoding='utf-8-sig')

            # Excel 파일도 있으면 변환
            excel_file = csv_file.replace('.csv', '.xlsx')
            if os.path.exists(excel_file):
                df_korean.to_excel(excel_file, index=False, engine='openpyxl')
                print(f"     Excel 파일도 변환 완료")

        except Exception as e:
            print(f"[ERR] {filename} - 오류 발생: {e}")

    print(f"\n변환 완료!\n")


if __name__ == "__main__":
    print("="*80)
    print("          CSV 파일 한글 변환")
    print("="*80)

    convert_all_csv_files()
