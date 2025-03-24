import requests
import pandas as pd
import os
import json
from datetime import datetime

def read_api_key():
    with open('../../api_key.txt', 'r') as f:
        return f.read().strip()

def get_assembly_bills(api_key, age='21'):
    url = "https://open.assembly.go.kr/portal/openapi/nwbpacrgavhjryiph"
    
    page_index = 1
    page_size = 100
    all_data = []
    
    while True:
        params = {
            'KEY': api_key,
            'Type': 'json',
            'pIndex': page_index,
            'pSize': page_size,
            'AGE': age,
            'BILL_KIND': '법률안'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            print(f"오류 발생: {response.status_code}")
            print(response.text)
            break
        
        try:
            data = response.json()
            
            if 'nwbpacrgavhjryiph' in data:
                result_code = data['nwbpacrgavhjryiph'][0]['head'][1]['RESULT']['CODE']
                if result_code != 'INFO-000':
                    print(f"API 오류: {result_code}")
                    print(data['nwbpacrgavhjryiph'][0]['head'][1]['RESULT']['MESSAGE'])
                    break
                
                items = data['nwbpacrgavhjryiph'][1]['row']
                if not items:
                    print("더 이상 데이터가 없습니다.")
                    break
                
                all_data.extend(items)
                print(f"페이지 {page_index} 데이터 {len(items)}개 수집 완료")
                
                if len(items) < page_size:
                    break
                
                page_index += 1
            else:
                print("응답 데이터 형식이 올바르지 않습니다.")
                print(data)
                break
        except json.JSONDecodeError:
            print("JSON 파싱 오류")
            print(response.text)
            break
        except Exception as e:
            print(f"오류 발생: {str(e)}")
            break
    
    return all_data

def save_to_csv(data, filename=None):
    if not data:
        print("저장할 데이터가 없습니다.")
        return
    
    if filename is None:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"../../data/assembly_bills_21_{now}.csv"
    else:
        filename = f"../../data/{filename}"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"데이터가 '{filename}'에 저장되었습니다.")
    return filename

def analyze_bills(data):
    if not data:
        print("분석할 데이터가 없습니다.")
        return
    
    result_counts = {}
    for item in data:
        result = item.get('PROC_RESULT_CD', '미정')
        if result in result_counts:
            result_counts[result] += 1
        else:
            result_counts[result] = 1
    
    print("\n처리 결과별 통계:")
    for result, count in sorted(result_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"- {result}: {count}개")
    
    proposer_counts = {}
    for item in data:
        proposer = item.get('PROPOSER', '미상')
        if proposer in proposer_counts:
            proposer_counts[proposer] += 1
        else:
            proposer_counts[proposer] = 1
    
    print("\n상위 10명 제안자별 통계:")
    for proposer, count in sorted(proposer_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"- {proposer}: {count}개")
    
    committee_counts = {}
    for item in data:
        committee = item.get('COMMITTEE_NM', '미상')
        if committee in committee_counts:
            committee_counts[committee] += 1
        else:
            committee_counts[committee] = 1
    
    print("\n소관위원회별 통계:")
    for committee, count in sorted(committee_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"- {committee}: {count}개")

def main():
    api_key = read_api_key()
    
    print("21대 국회 법률안 데이터 수집 시작...")
    assembly_data = get_assembly_bills(api_key, age='21')
    
    filename = save_to_csv(assembly_data)
    
    if assembly_data:
        print(f"\n총 {len(assembly_data)}개의 법률안 정보를 수집했습니다.")
        
        analyze_bills(assembly_data)
        
        print("\n수집된 정보 필드:")
        for key in assembly_data[0].keys():
            print(f"- {key}")

        # 분석 결과를 텍스트 파일로 저장
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"../../data/bill_analysis_{now}.txt", "w", encoding="utf-8") as f:
            f.write(f"총 {len(assembly_data)}개의 법률안 정보를 수집했습니다.\n")
            f.write("수집된 정보 필드:\n")
            for key in assembly_data[0].keys():
                f.write(f"- {key}\n")

if __name__ == "__main__":
    main()
