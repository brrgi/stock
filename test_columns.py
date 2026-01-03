import FinanceDataReader as fdr

# 종목 리스트 가져오기
stock_list = fdr.StockListing('KOSPI')
print("컬럼명:")
print(stock_list.columns.tolist())
print("\n샘플 데이터:")
print(stock_list.head())
