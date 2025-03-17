import requests
import pandas as pd
import os
import json
from datetime import datetime
import time

def read_api_key():
    with open('../api_key.txt', 'r') as f:
        return f.read().strip()

def get_voting_info_for_bill(api_key, bill_id, age='21', max_retries=3, retry_delay=2):
    url = "https://open.assembly.go.kr/portal/openapi/nojepdqqaweusdfbi"
    
    params = {
        'KEY': api_key,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 300,  # 한 번에 최대한 많은 데이터를 가져오기
        'AGE': age,
        'BILL_ID': bill_id
    }
    
    for retry in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"오류 발생: {response.status_code}")
                print(response.text)
                if retry < max_retries - 1:
                    print(f"{retry_delay}초 후 재시도 ({retry+1}/{max_retries})...")
                    time.sleep(retry_delay)
                    continue
                return None
            
            data = response.json()
            
            if 'nojepdqqaweusdfbi' in data:
                result_code = data['nojepdqqaweusdfbi'][0]['head'][1]['RESULT']['CODE']
                if result_code != 'INFO-000':
                    print(f"API 오류: {result_code}")
                    print(data['nojepdqqaweusdfbi'][0]['head'][1]['RESULT']['MESSAGE'])
                    return None
                
                items = data['nojepdqqaweusdfbi'][1]['row']
                if not items:
                    print(f"법안 ID {bill_id}에 대한 표결 정보가 없습니다.")
                    return []
                
                return items
            else:
                print("응답 데이터 형식이 올바르지 않습니다.")
                print(data)
                return None
                
        except requests.exceptions.ConnectionError as e:
            print(f"연결 오류 발생: {e}")
            if retry < max_retries - 1:
                print(f"{retry_delay}초 후 재시도 ({retry+1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
                print(f"최대 재시도 횟수({max_retries})를 초과했습니다.")
                return None
        except json.JSONDecodeError:
            print("JSON 파싱 오류")
            if retry < max_retries - 1:
                print(f"{retry_delay}초 후 재시도 ({retry+1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
                return None
        except Exception as e:
            print(f"오류 발생: {str(e)}")
            if retry < max_retries - 1:
                print(f"{retry_delay}초 후 재시도 ({retry+1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
                return None
    
    return None

def collect_voting_data_for_bills(api_key, bills_csv):
    print(f"{bills_csv} 파일에서 법안 정보를 읽는 중...")
    df = pd.read_csv(bills_csv)
    
    if 'BILL_ID' not in df.columns:
        print("CSV 파일에 BILL_ID 열이 없습니다.")
        return None
    
    total_bills = len(df)
    print(f"총 {total_bills}개의 법안에 대한 표결 정보를 수집합니다.")
    
    all_voting_data = []
    success_count = 0
    error_count = 0
    empty_count = 0
    
    # 진행 상황을 저장할 파일 생성
    progress_file = "../data/voting_collection_progress.txt"
    with open(progress_file, 'w', encoding='utf-8') as f:
        f.write(f"21대 국회 표결정보 수집 진행 상황\n")
        f.write(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    try:
        for idx, row in df.iterrows():
            bill_id = row['BILL_ID']
            bill_name = row['BILL_NM'] if 'BILL_NM' in df.columns else "알 수 없음"
            
            print(f"[{idx+1}/{total_bills}] '{bill_name}' (ID: {bill_id}) 법안의 표결 정보를 수집 중...")
            
            # 진행 상황 업데이트
            if idx % 10 == 0:
                with open(progress_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{idx+1}/{total_bills}] 처리 중... (성공: {success_count}, 없음: {empty_count}, 오류: {error_count})\n")
            
            voting_data = get_voting_info_for_bill(api_key, bill_id)
            
            if voting_data is None:
                print(f"  - 오류 발생, 다음 법안으로 넘어갑니다.")
                error_count += 1
            elif len(voting_data) == 0:
                print(f"  - 표결 정보가 없습니다.")
                empty_count += 1
            else:
                print(f"  - {len(voting_data)}개의 표결 정보를 수집했습니다.")
                all_voting_data.extend(voting_data)
                success_count += 1
            
            # 중간 저장 (100개 법안마다)
            if idx > 0 and idx % 100 == 0 and all_voting_data:
                temp_filename = f"../data/voting_info_21_temp_{idx}.csv"
                temp_df = pd.DataFrame(all_voting_data)
                temp_df.to_csv(temp_filename, index=False, encoding='utf-8-sig')
                print(f"중간 저장: {temp_filename} ({len(all_voting_data)}개 데이터)")
                
                with open(progress_file, 'a', encoding='utf-8') as f:
                    f.write(f"중간 저장 완료: {temp_filename} ({len(all_voting_data)}개 데이터)\n")
            
            # API 요청 간 간격 두기 (초당 요청 수 제한 방지)
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n사용자에 의해 수집이 중단되었습니다.")
        with open(progress_file, 'a', encoding='utf-8') as f:
            f.write(f"\n사용자에 의해 수집이 중단되었습니다. ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
    except Exception as e:
        print(f"\n오류로 인해 수집이 중단되었습니다: {str(e)}")
        with open(progress_file, 'a', encoding='utf-8') as f:
            f.write(f"\n오류로 인해 수집이 중단되었습니다: {str(e)} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
    
    # 최종 진행 상황 저장
    with open(progress_file, 'a', encoding='utf-8') as f:
        f.write(f"\n수집 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"표결 정보 수집 결과:\n")
        f.write(f"- 성공: {success_count}개 법안\n")
        f.write(f"- 정보 없음: {empty_count}개 법안\n")
        f.write(f"- 오류: {error_count}개 법안\n")
        f.write(f"- 총 수집된 표결 정보: {len(all_voting_data)}개\n")
    
    print(f"\n표결 정보 수집 완료:")
    print(f"- 성공: {success_count}개 법안")
    print(f"- 정보 없음: {empty_count}개 법안")
    print(f"- 오류: {error_count}개 법안")
    print(f"- 총 수집된 표결 정보: {len(all_voting_data)}개")
    
    return all_voting_data

def save_to_csv(data, filename=None):
    if not data:
        print("저장할 데이터가 없습니다.")
        return None
    
    if filename is None:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/voting_info_21_{now}.csv"
    else:
        filename = f"data/{filename}"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"{len(data)}개의 데이터가 {filename}에 저장되었습니다.")
    
    return filename

def analyze_voting_data(data):
    if not data:
        print("분석할 데이터가 없습니다.")
        return None
    
    # 표결 결과별 통계
    vote_result_counts = {}
    for item in data:
        result = item.get('RESULT_VOTE_MOD', '미정')
        if result in vote_result_counts:
            vote_result_counts[result] += 1
        else:
            vote_result_counts[result] = 1
    
    print("\n표결 결과별 통계:")
    for result, count in sorted(vote_result_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"- {result}: {count}개")
    
    # 정당별 통계
    party_counts = {}
    for item in data:
        party = item.get('POLY_NM', '미상')
        if party in party_counts:
            party_counts[party] += 1
        else:
            party_counts[party] = 1
    
    print("\n정당별 통계:")
    for party, count in sorted(party_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"- {party}: {count}개")
    
    # 법안별 통계
    bill_counts = {}
    for item in data:
        bill_no = item.get('BILL_NO', '미상')
        if bill_no in bill_counts:
            bill_counts[bill_no] += 1
        else:
            bill_counts[bill_no] = 1
    
    print(f"\n총 법안 수: {len(bill_counts)}개")
    
    # 의원별 통계
    member_counts = {}
    for item in data:
        member = item.get('HG_NM', '미상')
        if member in member_counts:
            member_counts[member] += 1
        else:
            member_counts[member] = 1
    
    print(f"\n총 의원 수: {len(member_counts)}명")
    
    return {
        'vote_results': vote_result_counts,
        'parties': party_counts,
        'bills': bill_counts,
        'members': member_counts
    }

def save_analysis_to_txt(analysis, data, filename=None):
    if not analysis:
        print("저장할 분석 결과가 없습니다.")
        return None
    
    if filename is None:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/voting_analysis_{now}.txt"
    else:
        filename = f"data/{filename}"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=== 21대 국회 본회의 표결정보 분석 결과 ===\n\n")
        
        f.write(f"수집 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("1. 표결 결과별 통계\n")
        for result, count in sorted(analysis['vote_results'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"- {result}: {count}개\n")
        
        f.write("\n2. 정당별 통계\n")
        for party, count in sorted(analysis['parties'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"- {party}: {count}개\n")
        
        f.write(f"\n3. 총 법안 수: {len(analysis['bills'])}개\n")
        
        f.write(f"\n4. 총 의원 수: {len(analysis['members'])}명\n")
        
        total_votes = sum(analysis['vote_results'].values())
        f.write(f"\n5. 총 투표 수: {total_votes}개\n")
        
        f.write("\n6. 의원 1인당 평균 투표 수: ")
        unique_members = len(analysis['members'])
        if unique_members > 0:
            f.write(f"{total_votes / unique_members:.2f}개\n")
        else:
            f.write("계산할 수 없음\n")
        
        # 상위 10개 법안 (투표 수 기준)
        f.write("\n7. 투표 수 기준 상위 10개 법안\n")
        for bill_no, count in sorted(analysis['bills'].items(), key=lambda x: x[1], reverse=True)[:10]:
            bill_name = "알 수 없음"
            for item in data:
                if item.get('BILL_NO') == bill_no:
                    bill_name = item.get('BILL_NAME', '알 수 없음')
                    break
            f.write(f"- {bill_no} ({bill_name}): {count}개 투표\n")
    
    print(f"분석 결과가 {filename}에 저장되었습니다.")
    return filename

def main():
    api_key = read_api_key()
    
    print("21대 국회 본회의 표결정보 수집 시작...")
    
    bills_csv = "../data/filtered_bills_20250317_175551.csv"
    voting_data = collect_voting_data_for_bills(api_key, bills_csv)
    
    if voting_data:
        print(f"\n총 {len(voting_data)}개의 표결정보를 수집했습니다.")
        
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"voting_info_21_{now}.csv"
        csv_path = save_to_csv(voting_data, csv_filename)
        
        analysis_results = analyze_voting_data(voting_data)
        txt_filename = f"voting_analysis_{now}.txt"
        txt_path = save_analysis_to_txt(analysis_results, voting_data, txt_filename)
        
        print("\n수집된 정보 필드:")
        if voting_data and len(voting_data) > 0:
            for key in voting_data[0].keys():
                print(f"- {key}")
        
        print("\n작업이 완료되었습니다.")
        print(f"- CSV 파일: {csv_path}")
        print(f"- 분석 결과: {txt_path}")

if __name__ == "__main__":
    main()
