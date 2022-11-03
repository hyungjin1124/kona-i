import zipfile
import pandas as pd
from io import BytesIO
import json
import os
from google.cloud import dialogflow
import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="C:/Users/Hyungjink/Documents/chatbot/i--sgtd-73fd1d3cd2bc.json"

# form_class = uic.loadUiType("./json_parser_ui.ui")[0]

# #화면을 띄우는데 사용되는 Class 선언
# class WindowClass(QDialog, form_class) :
#     def __init__(self) :
#         super().__init__()
#         self.setupUi(self)

#         self.fileSelection.clicked.connect(self.fileSelect)

#     def fileSelect(self):
#         print("file Select!!!")


# 압축 폴더안의 파일명과 파일내용을 저장하는 함수
def unzip(file_path):
    folder = {}

    with zipfile.ZipFile(file_path, 'r') as zip_obj:
        file_names = zip_obj.namelist()
        for file_name in file_names:
            if file_name.startswith('intents/') and not file_name.split('/')[1].startswith(('(0. 백업)', '(0. 삭제)', '(0. 임시)')): # (백업), (삭제), (임시)로 시작하는 파일 제외
                zip_read = zip_obj.read(file_name)
                temp = json.load(BytesIO(zip_read))
                folder[file_name.split('/')[1].replace('.json', '')] = temp # intents/와 .json 같은 불필요한 부분 제거하고 intent명만 저장

    return folder 

# "intent"와 "intent_usersays_ko"이 모두 매칭되는지 확인하고 매칭되지 않을시 제거하는 함수 
def pair_checking(folder):
    an_files = [key for key in folder if not key.endswith('_usersays_ko')]
    ex_files = [key.replace('_usersays_ko', '') for key in folder if key.endswith('_usersays_ko')]
    print(f"Before deliting: {len(folder)}")

    for i in an_files: # 예문 파일만 있는 경우 
        if i not in ex_files:
            del folder[i]
            print(f'Delete {i} file')
    
    for j in ex_files: # 답변 파일만 있는 경우
        if j not in an_files:
            del folder[f'{j}_usersays_ko']
            print(f'Delete {j}_usersays_ko file')

    print(f"After deliting: {len(folder)}")

    return folder

# 인텐트별 예문 목록, 예문개수 및 속성 값 추출파싱하는 함수
def get_examples(file_name, data_list):
    ex_list = []
    entity = [] 
    entity_list = []
    entity_dict = {} 
    entity_cnt = 0 # 엔티티 개수
    ex_cnt = 0 # 예문 개수 
    intent_name = file_name.replace('_usersays_ko', '')

    for dic in data_list:
        sentence = '' # 예문 
        data = dic.get("data")

        for i in data:
            text = i.get('text')
            alias = i.get('alias')
            sentence += text # 예문 만들기
                
            if 'alias' in i: # 엔티티가 있는 경우 
                if alias in entity_dict: # dictionary에 해당 엔티티명의 list가 있는 경우 
                    if text not in entity_dict[alias]: # 엔티티명을 key값으로 가지는 list에 해당 text가 없을 경우  
                        entity_dict[alias].append(text) # 추가 
                else: # 해당 엔티티명의 list가 없을 경우
                    entity_dict[alias] = [text] # 해당 엔티티명을 key로 가지는 배열을 만들고 text를 추가
                    entity_cnt += 1 # 엔티티명을 새로 추가했으므로 엔티티개수 +1
        sentence = sentence.replace('\u11a2', '')
        ex_list.append([intent_name, sentence]) 
        ex_cnt += 1 # 예문개수 +1 

    if entity_dict: # 엔티티가 있을 때만
        entity_list.append(entity_dict) # 엔티티 리스트에 추가
    entity.append([intent_name, ex_cnt, entity_cnt, entity_list])

    df = pd.DataFrame(ex_list, columns = ['인텐트명', '예문'])
    df2 = pd.DataFrame(entity, columns = ['인텐트명', '예문개수', '엔티티 개수', '엔티티 리스트'])

    return df, df2 

# 인텐트별 답변 목록 
def get_answer(file_name, data_dict):
    an_list = []
    speech = data_dict.get('responses')[0].get('messages')[0].get('speech')[0]
    speech = speech.replace('\n', '').replace('\xa0', '')
    an_list.append([file_name, speech])
    df = pd.DataFrame(an_list, columns = ['인텐트명', '답변'])

    return df

def detect_intent_texts(project_id, session_id, texts, language_code):
    """Returns the result of detect intent with texts as inputs.

    Using the same `session_id` between requests allows continuation
    of the conversation."""
    session_client = dialogflow.SessionsClient()

    session = session_client.session_path(project_id, session_id)
    # print("Session path: {}\n".format(session))

    # for text in texts:
    text_input = dialogflow.TextInput(text=texts, language_code=language_code)

    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    return response.query_result.intent.display_name, response.query_result.fulfillment_text

# 파싱
def parsing(folder):
    total_ex_df = pd.DataFrame(columns= ['인텐트명', '예문']) # 예문 DataFrame
    total_an_df = pd.DataFrame(columns = ['인텐트명', '답변']) # 답변 DataFrame
    total_entity_df = pd.DataFrame(columns = ['인텐트명', '예문개수', '엔티티 개수', '엔티티 리스트']) # 예문개수 및 속성값 DataFrame
    for file_name, contents in folder.items():
        if file_name.endswith('_usersays_ko'): # _usersays_ko으로 끝나는 파일에서 예문 파싱
            ex_df, entity_df = get_examples(file_name, contents)
            total_ex_df = pd.concat([total_ex_df, ex_df], ignore_index=True) # 인텐트별 예문 목록 
            total_entity_df = pd.concat([total_entity_df, entity_df], ignore_index = True) # 예문개수 및 속성값
        else:
            an_df = get_answer(file_name, contents) 
            total_an_df = pd.concat([total_an_df, an_df], ignore_index=True) # 인텐트별 답변 목록

    # response와 호출 결과가 다른 인텐트의 목록
    ex_list = list(total_ex_df["예문"].values)
    real_intent = []
    real_response = []
    call_intent = []
    call_response = []
    ex = []
    for i in ex_list:
        print(f"Processing {ex_list.index(i)} / {len(ex_list)}")
        call_int, call_res = detect_intent_texts("i--sgtd", '123456789', i, 'ko')
        call_res = call_res.replace('\n', '') # 호출 response에는 \n가 포함되어 있기 때문에 제거
        real_int = total_ex_df[total_ex_df['예문'] == i]['인텐트명'].values[0]
        response = total_an_df[total_an_df["인텐트명"] == real_int]["답변"].values[0]

        if call_res != response: 
            print('*' * 30)
            print(real_int)
            print(response)
            print(call_int)
            print(call_res)
            print(i)
            print('*' * 30)
            real_intent.append(real_int)
            real_response.append(response)
            call_intent.append(call_int)
            call_response.append(call_res)
            ex.append(i)

    miss_match_df = pd.DataFrame({
        "인텐트명": real_intent,
        "호출 인텐트명": call_intent,
        "response": real_response,
        "호출_response": call_response,
        "예문": ex
    })

    return total_ex_df, total_an_df, total_entity_df, miss_match_df

# Dataframe, 파일경로, 시트명을 입력받아 dataframe을 excel파일로 변환하는 함수
def df_to_excel(df, file_path, sheet_name):
    if not os.path.exists(file_path):
        with pd.ExcelWriter(file_path, mode = 'w', engine = 'openpyxl') as writer:
            df.to_excel(writer, index = False, encoding='cp949', sheet_name = sheet_name)
    else:
        with pd.ExcelWriter(file_path, mode = 'a', engine = 'openpyxl') as writer:
            xl = pd.ExcelFile(file_path)
            sheet_names = xl.sheet_names
            if sheet_name not in sheet_names:
                df.to_excel(writer, index = False, encoding='cp949', sheet_name = sheet_name)

def main():
    try:
        folder = unzip('김포페이_임시.zip')
        folder = pair_checking(folder)

        ex_df, an_df, cnt_df, miss_match_df = parsing(folder)

        ex_df = ex_df.sort_values(by=['인텐트명']).reset_index(drop=True) 
        an_df = an_df.sort_values(by=['인텐트명']).reset_index(drop=True) 
        cnt_df = cnt_df.sort_values(by=['인텐트명']).reset_index(drop=True) 
        miss_match_df = miss_match_df.sort_values(by=['인텐트명']).reset_index(drop=True) 

        df_to_excel(ex_df, './경기지역화폐_테스트.xlsx', '인텐트별 예문')
        df_to_excel(an_df, './경기지역화폐_테스트.xlsx', '인텐트별 답변')
        df_to_excel(cnt_df, './경기지역화폐_테스트.xlsx', '예문개수 및 속성값')
        df_to_excel(miss_match_df, './김포페이_테스트.xlsx', '실제 response와 호출 결과가 다른 인텐트 및 예문')
    except Exception as ex:
        print(ex)

if __name__ == '__main__':
    #QApplication : 프로그램을 실행시켜주는 클래스
    # app = QApplication(sys.argv) 

    # #WindowClass의 인스턴스 생성
    # myWindow = WindowClass() 

    # #프로그램 화면을 보여주는 코드
    # myWindow.show()

    # #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    # app.exec_()
    main()