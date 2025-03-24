import pandas as pd
from datetime import datetime

def filter_bills(input_file, target_results):
    print(f"'{input_file}' 파일 읽는 중...")
    df = pd.read_csv(input_file)
    
    original_count = len(df)
    print(f"원본 데이터 개수: {original_count}개")
    
    result_counts_before = df['PROC_RESULT_CD'].value_counts().to_dict()
    
    filtered_df = df[df['PROC_RESULT_CD'].isin(target_results)]
    
    filtered_count = len(filtered_df)
    print(f"필터링 후 데이터 개수: {filtered_count}개")
    print(f"제거된 데이터 개수: {original_count - filtered_count}개")
    
    result_counts_after = filtered_df['PROC_RESULT_CD'].value_counts().to_dict()
    
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = f"../../data/filtered_bills_{now}.csv"
    filtered_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"필터링된 데이터가 '{output_csv}'에 저장되었습니다.")
    
    output_txt = f"../../data/filtering_results_{now}.txt"
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(f"원본 파일: {input_file}\n")
        f.write(f"필터링 기준: {', '.join(target_results)}\n\n")
        
        f.write("=== 필터링 전 처리 결과별 개수 ===\n")
        for result, count in sorted(result_counts_before.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{result}: {count}개\n")
        
        f.write("\n=== 필터링 후 처리 결과별 개수 ===\n")
        for result, count in sorted(result_counts_after.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{result}: {count}개\n")
        
        f.write(f"\n총 {original_count}개 중 {filtered_count}개 남음 ({original_count - filtered_count}개 제거됨)\n")
        f.write(f"제거 비율: {((original_count - filtered_count) / original_count) * 100:.2f}%\n")
    
    print(f"필터링 결과가 '{output_txt}'에 저장되었습니다.")
    
    return output_csv, output_txt

if __name__ == "__main__":
    input_file = "../../data/assembly_bills_21_20250317_175143.csv"
    
    target_results = ["원안가결", "수정가결", "부결"]
    
    output_csv, output_txt = filter_bills(input_file, target_results)
    
    print("\n=== 결과 파일 내용 ===")
    with open(output_txt, 'r', encoding='utf-8') as f:
        print(f.read())
