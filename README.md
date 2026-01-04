# 한국 주식 RS Rating 스크리너

윌리엄 오닐의 RS Rating 개념을 활용한 한국 주식 주도주 스크리닝 시스템

## 기능

- RS Rating 계산 (상대강도 평가)
- 주도주 스크리닝
- 2배~10배 성장 가능성 종목 발굴

## 설치

```bash
pip install -r requirements.txt
```

## 사용법

```bash
python src/main.py
```

## 대시보드 (로컬)

```bash
# 패키지 설치
pip install -r requirements.txt

# 주간 데이터 생성 (최근 26주 + 오늘)
python src/generate_weekly_data.py --weeks 26

# 인터랙티브 대시보드 생성
python src/create_interactive_dashboard.py

# 로컬 서버 실행
python -m http.server 8001 --bind 127.0.0.1
```

브라우저에서 아래 주소를 열면 됩니다.

```
http://127.0.0.1:8001/web/dashboard_interactive.html
```

## 노트북에서 동일하게 사용하기

### 1) Git으로 동기화 (추천)

```bash
git clone <REPO_URL>
cd stock-rs-screener
pip install -r requirements.txt
python src/generate_weekly_data.py --weeks 26
python src/create_interactive_dashboard.py
python -m http.server 8001 --bind 127.0.0.1
```

### 2) 폴더 복사/압축

`stock-rs-screener` 폴더를 그대로 복사하거나 ZIP으로 옮긴 뒤,
위의 "대시보드 (로컬)" 순서대로 실행하면 동일하게 동작합니다.

## 프로젝트 구조

```
stock-rs-screener/
├── src/                   # 파이썬 모듈/스크립트
├── scripts/               # 실행용 배치 파일
├── data/                  # 데이터/캐시
├── web/                   # 생성된 대시보드 및 정적 파일
├── requirements.txt       # 필요 패키지
└── results/               # 결과 저장 폴더
```
