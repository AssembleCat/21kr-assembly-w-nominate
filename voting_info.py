import requests
import json
import os
from datetime import datetime

def load_api_key(file_path="api_key.txt"):
    try:
        with open(file_path, 'r') as f:
            api_key = f.read().strip()
        return api_key
    except FileNotFoundError:
        print(f"API 키 파일({file_path})을 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"API 키 로드 중 오류 발생: {e}")
        return None

def get_assembly_bills(api_key=None, age='22'):
    if api_key is None:
        api_key = load_api_key()
        if api_key is None:
            return {"error": "API 키를 로드할 수 없습니다."}
            
    url = "https://open.assembly.go.kr/portal/openapi/nojepdqqaweusdfbi"
    
    params = {
        'KEY': api_key,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 100,
        'AGE': age,
        'BILL_ID': 'temp'
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        try:
            result = response.json()
            print(f"응답 키: {list(result.keys())}")
            
            if 'RESULT' in result and 'CODE' in result['RESULT'] and result['RESULT']['CODE'].startswith('ERROR'):
                error_code = result['RESULT']['CODE']
                error_message = result['RESULT']['MESSAGE']
                print(f"API 오류: {error_code} - {error_message}")
                return {"error": f"{error_code}: {error_message}"}
                
            return result
        except json.JSONDecodeError:
            return {"error": "응답을 JSON으로 파싱할 수 없습니다."}
    else:
        return {"error": f"API 요청 실패: {response.status_code}"}

def print_bill_info(bill_data):
    try:
        if "error" in bill_data:
            print(f"오류: {bill_data['error']}")
            return
            
        print("API 응답 구조:")
        print(json.dumps(bill_data, indent=2, ensure_ascii=False)[:500] + "...")
        
        if not bill_data or not isinstance(bill_data, dict):
            print(f"유효하지 않은 응답 형식: {type(bill_data)}")
            return
            
        if len(bill_data.keys()) == 0:
            print("응답에 키가 없습니다.")
            return
            
        first_key = list(bill_data.keys())[0]
        print(f"첫 번째 키: {first_key}")
        
        if not isinstance(bill_data[first_key], list):
            print(f"첫 번째 키의 값이 리스트가 아닙니다: {type(bill_data[first_key])}")
            return
            
        if len(bill_data[first_key]) < 2:
            print(f"첫 번째 키의 값 리스트 길이가 충분하지 않습니다: {len(bill_data[first_key])}")
            return
        
        head_info = bill_data[first_key][0].get('head', [])
        total_count = 0
        result_code = ""
        result_message = ""
        
        for item in head_info:
            if 'list_total_count' in item:
                total_count = item['list_total_count']
            if 'RESULT' in item:
                result_code = item['RESULT'].get('CODE', '')
                result_message = item['RESULT'].get('MESSAGE', '')
        
        print(f"API 응답 결과: {result_code} - {result_message}")
        print(f"총 조회 건수: {total_count}")
        
        items = bill_data[first_key][1].get('row', [])
        
        if not items:
            print("조회된 법률안이 없습니다.")
            return
        
        print(f"조회된 법률안 수: {len(items)}개")
        print("\n" + "="*80)
        
        for idx, item in enumerate(items, 1):
            if idx > 5:
                print(f"... 외 {len(items) - 5}개")
                break
                
            print(f"[{idx}] 법률안 정보")
            print(f"의안번호: {item.get('BILL_NO', '정보 없음')}")
            print(f"의안명: {item.get('BILL_NAME', '정보 없음')}")
            print(f"법률명: {item.get('LAW_TITLE', '정보 없음')}")
            print(f"소관위원회: {item.get('CURR_COMMITTEE', '정보 없음')}")
            print(f"투표 결과: {item.get('RESULT_VOTE_MOD', '정보 없음')}")
            print(f"투표 일자: {item.get('VOTE_DATE', '정보 없음')}")
            print(f"의원명: {item.get('HG_NM', '정보 없음')} ({item.get('POLY_NM', '정보 없음')})")
            print(f"지역구: {item.get('ORIG_NM', '정보 없음')}")
            print(f"상세 URL: {item.get('BILL_URL', '정보 없음')}")
            print("="*80)
    
    except Exception as e:
        import traceback
        print(f"데이터 출력 중 오류 발생: {e}")
        print(traceback.format_exc())

def get_next_filename(base_name="assembly_bills"):
    index = 1
    while True:
        filename = f"{base_name}_{index}.csv"
        if not os.path.exists(filename):
            return filename
        index += 1

def save_to_csv(bill_data, filename=None):
    import csv
    
    try:
        if "error" in bill_data:
            print(f"오류로 인해 CSV 저장을 건너뜁니다: {bill_data['error']}")
            return None
            
        if filename is None:
            filename = get_next_filename()
        
        if not bill_data or not isinstance(bill_data, dict) or len(bill_data.keys()) == 0:
            print("유효하지 않은 응답 형식입니다.")
            return None
            
        first_key = list(bill_data.keys())[0]
        
        if not isinstance(bill_data[first_key], list) or len(bill_data[first_key]) < 2:
            print("유효하지 않은 응답 구조입니다.")
            return None
        
        items = bill_data[first_key][1].get('row', [])
        
        if not items:
            print("저장할 데이터가 없습니다.")
            return None
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = items[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for item in items:
                writer.writerow(item)
                
        print(f"{filename} 파일로 저장되었습니다.")
        return filename
    
    except Exception as e:
        import traceback
        print(f"CSV 저장 중 오류 발생: {e}")
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    api_key = load_api_key()
    if api_key is None:
        print("API 키를 로드할 수 없어 프로그램을 종료합니다.")
        exit(1)
    
    age = '22'
    
    print(f"22대 국회 본회의 표결정보를 조회합니다...")
    
    result = get_assembly_bills(api_key, age)
    
    if "error" in result:
        print(result["error"])
    else:
        print_bill_info(result)
        
        saved_filename = save_to_csv(result)
        if saved_filename:
            print(f"데이터가 {saved_filename} 파일로 저장되었습니다.")
