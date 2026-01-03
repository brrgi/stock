"""
결과 파일명을 한글로 변경
"""

import os
from glob import glob


def rename_result_files():
    """results 폴더의 파일명을 한글로 변경"""

    results_folder = 'results'

    if not os.path.exists(results_folder):
        print("results 폴더가 없습니다.")
        return

    # 파일명 매핑 (영어 -> 한글)
    rename_mapping = {
        'entry_signals_all': '진입신호_전체',
        'entry_signals_both': '진입신호_양쪽모두',
        'entry_signals_oneil': '진입신호_윌리엄오닐',
        'entry_signals_minervini': '진입신호_마크미너비니',
        'leading_stocks_quick': '주도주_목록',
        'leading_stocks': '주도주_전체',
        'high_potential_stocks_quick': '고성장종목_2-10배',
        'high_potential_stocks': '고성장종목_전체',
        'top_rs_stocks_quick': 'RS등급_상위종목',
        'top_rs_stocks': 'RS등급_전체'
    }

    # 모든 파일 찾기
    all_files = glob(os.path.join(results_folder, '*'))

    print("\n파일명 변경 시작...\n")

    renamed_count = 0

    for file_path in all_files:
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1]  # .csv 또는 .xlsx

        # 타임스탬프 추출 (예: _20260101_014331)
        for eng_name, kor_name in rename_mapping.items():
            if filename.startswith(eng_name):
                # 타임스탬프 부분 추출
                timestamp_part = filename.replace(eng_name, '').replace(file_ext, '')

                # 새 파일명 생성
                new_filename = f"{kor_name}{timestamp_part}{file_ext}"
                new_file_path = os.path.join(results_folder, new_filename)

                # 파일명 변경
                try:
                    os.rename(file_path, new_file_path)
                    print(f"[OK] {filename}")
                    print(f"  -> {new_filename}")
                    renamed_count += 1
                except Exception as e:
                    print(f"[ERR] {filename} - 오류: {e}")

                break

    print(f"\n총 {renamed_count}개 파일명 변경 완료!\n")


if __name__ == "__main__":
    print("="*80)
    print("          결과 파일명 한글 변경")
    print("="*80)

    rename_result_files()
