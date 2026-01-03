"""백테스트 대시보드만 재생성"""
import pandas as pd
import os
from generate_backtest_dashboard import generate_backtest_dashboard

# results 폴더에서 가장 최근 백테스트 CSV 파일 찾기
results_dir = 'results'
csv_files = [f for f in os.listdir(results_dir) if f.startswith('백테스팅결과') and f.endswith('.csv')]

if not csv_files:
    print("백테스트 CSV 파일을 찾을 수 없습니다.")
    exit(1)

# 가장 최근 파일
latest_csv = sorted(csv_files)[-1]
csv_path = os.path.join(results_dir, latest_csv)

print(f"CSV 파일 로드: {csv_path}")

# CSV 로드
backtest_df = pd.read_csv(csv_path, encoding='utf-8-sig')
backtest_df['date'] = pd.to_datetime(backtest_df['date'])

print(f"데이터 포인트: {len(backtest_df)}개")
print(f"고유 날짜: {len(backtest_df['date'].unique())}개")
print(f"고유 종목: {len(backtest_df['ticker'].unique())}개")

# 대시보드 생성
output_file = generate_backtest_dashboard(backtest_df, 'backtest_dashboard.html')

print(f"\n대시보드 생성 완료: {output_file}")
print(f"대시보드 열기: {os.path.abspath(output_file)}")

# 대시보드 열기
os.system(f'start {output_file}')
