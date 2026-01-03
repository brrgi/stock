"""어디서 모듈을 import 하는지 확인"""
import advanced_entry_signals
import generate_modern_dashboard

print("advanced_entry_signals 위치:")
print(advanced_entry_signals.__file__)

print("\ngenerate_modern_dashboard 위치:")
print(generate_modern_dashboard.__file__)

# 실제 코드 확인
from advanced_entry_signals import AdvancedEntryAnalyzer
import inspect

print("\n=== AdvancedEntryAnalyzer.mark_minervini_advanced_signal 소스 코드 일부 ===")
source = inspect.getsource(AdvancedEntryAnalyzer.mark_minervini_advanced_signal)
# trend_template 초기화 부분 찾기
for i, line in enumerate(source.split('\n')[50:70], start=50):
    if 'above_' in line or 'near_' in line or 'rs_' in line:
        print(f"{i}: {line}")
