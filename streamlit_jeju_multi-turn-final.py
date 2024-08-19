import os
import sys

import streamlit as st
import googlemaps
import random
from datetime import datetime
import folium
from streamlit_folium import st_folium
# from geopy.geocoders import Nominatim
# from streamlit_folium import st_folium
import requests
from openai import OpenAI
import json
from pprint import pprint
import streamlit.components.v1 as components

import random
import numpy as np
import gc
import re

# for Predibase
from predibase import Predibase, FinetuningConfig, DeploymentConfig

# for MongoDB
import pymongo
import certifi
from datetime import datetime

# setting for Predibase
# Get a KEY from https://app.predibase.com/
PREDIBASE_API_TOKEN= 'pb_lPDQJzoPWgyIUW2pVu4HKg'
# api_token: str = userdata.get('PREDIBASE_API_KEY')
pb = Predibase(api_token=PREDIBASE_API_TOKEN)


# 업스테이지 API 키와 엔드포인트 설정
UPSTAGE_API_KEY = "up_YsiiwBJ4YwMmf70RuQBLMdgLrI3DS"
openai_client = OpenAI(api_key=UPSTAGE_API_KEY, base_url="https://api.upstage.ai/v1/solar")
SOLAR_MODEL_ENDPOINT = "https://api.upstage.ai/v1/solar"

# API 키와 클라이언트 설정
UPSTAGE_API_KEY = "up_YsiiwBJ4YwMmf70RuQBLMdgLrI3DS"
client = OpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v1/solar"
)

# 구글 맵스 API 키와 엔드포인트 설정
GOOGLE_MAPS_API_KEY = "AIzaSyBBMupOEJ7CpSzcz7_TvCKIOE5kI1R-5_4" #"YOUR_GOOGLE_MAPS_API_KEY"
GOOGLE_MAPS_ENDPOINT = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json'
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)


def generate_query_and_check(user_input):
    prompt = f"""
    사용자 입력: "{user_input}"
    이 문장이 구글 맵스 API 쿼리 검색이 필요한 문장인지 확인하고, 필요하다면 검색 쿼리로 생성해 주세요. 검색이 필요한 문장은 사용자가 식당명 또는 관광지명에 대한 구체적인 정보를 원할 때만입니다. 모든 문장에 대해서 검색 쿼리르 생성하지 마세요. 그리고 검색 쿼리만 생상하고 부연설명은 함께 생성하지 마세요.
    예시: 
    - 문장: "돈사돈 주소가 어떻게 돼?" -> 검색 쿼리: "돈사돈"
    - 문장: "제주토종흑돼지 월요일 휴무야?" -> 검색 쿼리: "제주토종흑돼지"
    - 문장: "김녕해수욕장 운영시간?" -> 검색 쿼리: 김녕해수욕장"
    - 문장: "카페한라산 영업시간 언제까지야?" -> 검색 쿼리: 카페한라산"
    - 문장: "오늘 날씨 어때?" -> 검색 쿼리: "N/A"
    - 문장: 애월 카페거리는 정말 멋지지! -> 검색 쿼리: "N/A"
    - 문장: 오 고마워 블로그 리뷰 찾아볼게ㅎㅎ -> 검색 쿼리: "N/A"
    - 문장: 너는 제주도 가본 적 있어? -> 검색 쿼리: "N/A"
    - 문장: 제주도 여행 알아보고 있었어ㅎㅎ -> 검색 쿼리: "N/A"
    """

    try:
        # 업스테이지 모델 호출
        query_response = client.chat.completions.create(
            model="solar-1-mini-chat",
            messages=[
                {"role": "system", "content": "You are an assistant that helps to determine if a Google Maps API query is needed and generates the query."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=70,  # 응답의 최대 토큰 수 설정
        )
        
        # 응답 본문 출력
        pprint(query_response)
        
        # 응답에서 쿼리 추출
        output = query_response.choices[0].message.content.strip()
        if '검색 쿼리:' in output:
            query = output.split('검색 쿼리:')[1].strip()
            if query == "N/A" or "n/a" in query.lower() or "검색 필요 없음" in query:
                return False, None

            # # 정규 표현식 패턴: 큰따옴표로 감싸인 문자열을 추출
            # pattern = r'"(.*?)"'
            # # re.findall()을 사용하여 모든 매칭된 문자열을 리스트로 반환
            # query = re.findall(pattern, query)[0]
            query = query.split('\n\n')[0].strip()
            query = query.split('\n')[0].strip()
            print("검색 쿼리 키워드: ", query)
            return True, query
        return False, None

    except Exception as e:
        print(f"Error: {e}")
        return False, None
    

@st.cache_resource
def search_place(query):
    if query:
        # 제주도의 중심 좌표와 반경 설정 (약 20km)
        center_location = (33.5, 126.5)
        radius = 20000  # 반경 20km
        
        # 장소 검색 요청
        response = gmaps.places_nearby(location=center_location, radius=radius, keyword=query)
        
        if response['status'] == 'OK':
            results = response['results']
            if results:
                # 첫 번째 결과를 가져옵니다.
                place_id = results[0]['place_id']
                
                # 장소 세부 정보 요청
                details_response = gmaps.place(place_id=place_id)
                if details_response['status'] == 'OK':
                    place = details_response['result']
                    name = place.get('name', 'N/A')
                    address = place.get('formatted_address', 'N/A')
                    phone_number = place.get('formatted_phone_number', 'N/A')
                    website = place.get('website', 'N/A')
                    location = place['geometry']['location']
                    lat, lng = location['lat'], location['lng']
                    
                    # 장소의 유형을 가져옵니다.
                    types = place.get('types', [])
                    type_str = ", ".join(types) if types else "N/A"
                    
                    
                    # 결과 출력
                    info_details = f"● Place Name: {name}\n\n● Place Types: {type_str}\n\n● Address: {address}\n\n● Phone Number: {phone_number}\n\n● Website: {website}"
                else:
                    info_details = "Error occurred while fetching place details."
                    lat, lng, name = None, None, None
            else:
                info_details = "No results found."
                lat, lng, name = None, None, None
        else:
            info_details = "Error occurred during the search."
            lat, lng, name = None, None, None

        return info_details, lat, lng, name
    return "No query provided.", None, None, None





# setting for MongoDB
ca = certifi.where() # 보안 설정

MONGO_USERNAME = "lhk4862"  # MongoDB 계정 사용자 이름
MONGO_PASSWORD = "mwozcGbsYzeD6NEf"  # MongoDB 계정 비밀번호
CLUSTER_ADDRESS = "small-talk.objdhkl.mongodb.net"  # MongoDB 클러스터 주소
APP_NAME = "small-talk"
DB_NAME = "evaluation_small-talk_db"


# DB 연결 함수
def get_db_collection(chat_model_name):
    COLLECTION_NAME = "jeju_tour_chatbot"
    client = pymongo.MongoClient(
        f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@{CLUSTER_ADDRESS}/{DB_NAME}?retryWrites=true&w=majority&appName={APP_NAME}",
        tlsCAFile=ca
    )
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    return collection

# 연결 테스트 함수
def test_db_connection():
    try:
        client = pymongo.MongoClient(
            f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@{CLUSTER_ADDRESS}/{DB_NAME}?retryWrites=true&w=majority&appName={APP_NAME}",
            tlsCAFile=ca
        )
        client.server_info()  # MongoDB 서버 정보 가져오기 시도
        print("Successfully connected to MongoDB Atlas!")
    except pymongo.errors.ServerSelectionTimeoutError as err:
        print(f"Failed to connect to MongoDB Atlas: {err}")

# 초기 연결 테스트
###test_db_connection()


# additional settings
FILEPATH = os.path.abspath(__file__)
sys.path.append(os.path.join(os.path.dirname(FILEPATH), '../'))



### Definitions for DB
def save_chat_to_db(chats, collection):
    ###collection.insert_one(chat)
    # chats (list of dict): 저장할 채팅 데이터의 리스트
    if chats:
        collection.insert_many(chats)

def load_chat_from_db(chat_id, collection):
    return collection.find_one({"_id": chat_id})

# 평가 세션 ID 및 평가 시작 시각 초기화
def initialize_evaluation_session(collection):
    # Initialize session state variables if not already initialized
    if 'db_chats_list' not in st.session_state:
        st.session_state.db_chats_list = []
    if 'session_id' not in st.session_state:
        ###st.session_state.session_id = 1  # 첫 번째 평가 세션 ID 설정
        last_evaluation = collection.find_one(sort=[("evaluation_starttime", -1)])
        
        if last_evaluation and last_evaluation.get('session_id') is not None:
            last_session_id = last_evaluation['session_id']
        else:
            last_session_id = 0  # 기본값 설정
        
        st.session_state.session_id = last_session_id + 1
    if 'evaluation_starttime' not in st.session_state:
        st.session_state.evaluation_starttime = datetime.now().strftime("%y%m%d_%H:%M:%S")  # 현재 시각으로 평가 시작 시각 설정


        
def clear_unused_memory():
    gc.collect()

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(**st.secrets["mongo"])


def make_history_prompt(chat, template_type):
    history_message = ""
    for turn_dict in chat:
        role, content = turn_dict['role'], turn_dict['content'] # 발화자 구분 (0: 사용자, 1: 시스템)
        print("= = = = 디버깅 = = = =")
        print("= = turn_dict['role']: ", role)
        print("= = = turn_dict['content']: ", content, end="\n")

        if template_type == "multiturn-chat":
            if role == 'user':
                if history_message == "": history_message += f"<|im_start|>user\n{content}"
                else: history_message += f"<|im_end|><|im_start|>user\n{content}"
            else:
                history_message += f"<|im_end|><|im_start|>assistant\n{content}"


    if template_type == "multiturn-chat":
        history_message += f"<|im_end|><|im_start|>assistant\n"
        
            
    return history_message




# 사용자와의 대화 기록 저장
if 'history' not in st.session_state:
    st.session_state['history'] = []
    st.session_state.messages_4 = []
    st.session_state.db_chats_list = []
    st.session_state.current_model = 'multiturn-chat'  # 예시로 설정
    
# 사용자 대화 입력
def get_user_input():
    user_input = st.text_input("You:", key="input", placeholder="Type here...")
    return user_input


def main():
    st.title("Jeju Tour Chatbot")



    with st.sidebar:
        clear_chat = st.button('Clear Chat')
        eval_mode = st.checkbox('DB 저장모드')
        
        evaluator_name = ""
        if eval_mode:
            evaluator_name = st.text_input('사용자 이름을 입력하세요.')

    
    
    
    
    if 'chat_model' not in st.session_state:
        st.session_state.current_model = "multiturn-chat"
        st.session_state.adapter_id = "jeju-multiturn-chat-model/3"
        st.session_state.lorax_client = pb.deployments.client("solar-1-mini-chat-240612")
        # with st.spinner("채팅 모델 로딩 중..."):
        #     st.session_state.chat_model, st.session_state.chat_tokenizer = load_chat_model(model_name=st.session_state.chat_model_name, saved_model_path=st.session_state.chat_saved_model_path, device_number=device_number, this_seed_value=random_seed_value, including_lm_head=including_lm_head)


     # HTML 및 JavaScript 코드
    # 기본 좌표 (제주도)
    default_location = [33.4996, 126.5312]
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        #map {{
            height: 400px;
            width: 100%;
        }}
        </style>
    </head>
    <body>
        <input id="searchBox" type="text" placeholder="Search for a place" />
        <div id="map"></div>
        <script>
        function initMap() {{
            var map = new google.maps.Map(document.getElementById('map'), {{
            center: {{lat: {default_location[0]}, lng: {default_location[1]}}},
            zoom: 15
            }});
            
            var input = document.getElementById('searchBox');
            var searchBox = new google.maps.places.SearchBox(input);
            map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);
            
            searchBox.addListener('places_changed', function() {{
            var places = searchBox.getPlaces();
            if (places.length == 0) {{
                return;
            }}
            
            var bounds = new google.maps.LatLngBounds();
            places.forEach(function(place) {{
                if (!place.geometry) {{
                console.log("Returned place contains no geometry");
                return;
                }}
                
                var marker = new google.maps.Marker({{
                map: map,
                title: place.name,
                position: place.geometry.location
                }});
                
                // Add the latitude, longitude, and place ID to Streamlit
                var lat = place.geometry.location.lat();
                var lng = place.geometry.location.lng();
                var place_id = place.place_id;
                document.getElementById('lat').value = lat;
                document.getElementById('lng').value = lng;
                document.getElementById('place_id').value = place_id;
                document.getElementById('place_info').value = JSON.stringify(place);

                if (place.geometry.viewport) {{
                bounds.union(place.geometry.viewport);
                }} else {{
                bounds.extend(place.geometry.location);
                }}
            }});
            map.fitBounds(bounds);
            }});
        }}
        </script>
        <script async defer
        src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_API_KEY}&libraries=places&callback=initMap">
        </script>
        <input id="lat" type="hidden">
        <input id="lng" type="hidden">
        <input id="place_id" type="hidden">
        <input id="place_info" type="hidden">
    </body>
    </html>
    """

    # Streamlit에 HTML 임베딩
    components.html(html_code, height=500)


    if clear_chat:
        if eval_mode:
            collection = get_db_collection(st.session_state.current_model)
            initialize_evaluation_session(collection)


    if ('messages_4' not in st.session_state) or clear_chat:
        st.session_state.messages_4 = []
    if 'map_data' not in st.session_state:
        st.session_state['map_data'] = None

    # if 'current_model' not in st.session_state or st.session_state.current_model != model_choice:
    #     st.session_state.current_model = model_choice
    #     with st.spinner(f"Loading {model_choice}..."):
    #         st.session_state.chat_model, st.session_state.chat_tokenizer = load_chat_model(model_name, saved_model_path, device_number, this_seed_value=random_seed_value, including_lm_head=including_lm_head)


    if st.session_state.current_model == "multiturn-chat":
        messages = st.session_state.messages_4

    for message in messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])

    


    # 평가자 이름 설정
    if eval_mode and evaluator_name:
        evaluator_name = evaluator_name.strip()
        if evaluator_name:
            st.session_state.evaluator_name = evaluator_name

    evaluator_name = st.session_state.get('evaluator_name', 'Unknown')
    # st.write('' if evaluator_name=='Unknown' else f"현재 평가자: {evaluator_name}")
    
    
    
    if eval_mode:
        collection = get_db_collection(st.session_state.current_model)
        initialize_evaluation_session(collection)
    

    # DB - List of dict 정의
    # if eval_mode:
    
    evaluation_starttime = st.session_state.get('evaluation_starttime', None)
    session_id = st.session_state.get('session_id', None)
    # if evaluation_starttime:
    #     st.write(f"평가 시작 시각: {st.session_state.evaluation_starttime}")
    # if session_id is not None:
    #     st.write(f"평가 세션 ID: {session_id}")

    chat_instruction = 'Chat with Upstage Solar model!'

    # [1] Multi-turn Conversation Chit-chat on Touring Jeju
    if prompt := st.chat_input(chat_instruction): # st.chat_input
        # 사용자 입력을 처리하는 부분
        with st.chat_message('user'):
            st.markdown(prompt)  # 입력된 문장을 사용자 메시지로 화면에 표시

        # 대화 기록 초기화가 필요한 경우
        if clear_chat:
            if st.session_state.current_model == "multiturn-chat":
                st.session_state.messages_4 = []
            st.session_state.db_chats_list = []  # DB 저장 리스트도 초기화

        # 입력된 문장을 현재 모델에 맞는 메시지 리스트에 저장
        if st.session_state.current_model == "multiturn-chat":
            st.session_state.messages_4.append({'role': 'user', 'content': prompt})

        # 현재 모델에 맞는 메시지 리스트 선택
        messages = (
            st.session_state.messages_4 ###if st.session_state.current_model == 'multiturn-chat'
        )

        print("get_output_content 함수에 들어가는 messages: ", messages)
        if messages[-1]['role'] != 'user':
            print(f"ERROR !!! (messages: {messages})")

        # 모델 추론 로직
        if st.session_state.current_model == "multiturn-chat":
            input_prompt = make_history_prompt(messages, template_type=st.session_state.current_model)
            
            
            # [2] Determine search needs and extract queries
            # 쿼리 생성 여부 확인 및 쿼리 생성
            need_search, query = generate_query_and_check(messages[-1]['content'])
            
            if need_search and query:
                # 장소 검색
                info_details, lat, lng, place_name = search_place(f"제주 {query}")

                
                if info_details in ["Error occurred while fetching place details.", "No results found.", "Error occurred during the search."]:
                    # 오류 또는 결과 없음 시 랜덤 답변 생성
                    error_messages = [
                        f"아쉽게도 {query}에 대한 정보는 찾지 못했어",
                        f"{query}의 정보를 찾을 수 없네. 다른 곳은 어때?",
                        f"{query}에 대한 구체적인 정보가 없다 ㅠㅠ",
                        f"{query}에 대한 정보는 검색되지 않네ㅠ",
                        f"{query}의 구체적인 정보는 검색이 안 나오네ㅠ"
                    ]
                    error_response = random.choice(error_messages)
                    response = error_response[:]
                    st.markdown(response)
                    
                    # 모델의 응답을 메시지 리스트에 추가
                    if st.session_state.current_model == "multiturn-chat":
                        st.session_state.messages_4.append({'role': 'assistant', 'content': error_response})
                    
                else:
                    info_messages = [
                        f"{query}의 구체적인 정보는 다음과 같아!",
                        f"{query} 정보를 알려줄게!",
                        f"{query}에 대해 다음과 같은 정보를 제공하고 있어",
                        f"{query}에 대해 검색되는 정보는 다음과 같아!",
                        f"{query}의 구체적인 정보는 다음과 같아. 참고해~"
                    ]
                    info_response = random.choice(info_messages)
                    response = info_response + f"\n\n{info_details}"
                    st.markdown(response)
    
                    # 모델의 응답을 메시지 리스트에 추가
                    if st.session_state.current_model == "multiturn-chat":
                        st.session_state.messages_4.append({'role': 'assistant', 'content': response}) ### info_response
                        
                    # 지도 데이터를 세션 상태에 저장
                    st.session_state['map_data'] = {'lat': lat, 'lng': lng, 'name': place_name}    
    
    
            # [1] Generate Multi-turn model based response
            else:
                response = st.session_state.lorax_client.generate(input_prompt, adapter_id=st.session_state.adapter_id, max_new_tokens=1000).generated_text
                print("prompt: ", input_prompt)
                print("response: ", response)
            

        # 세션에 지도 정보가 있는지 확인하고 표시
        # if 'map_data' in st.session_state and st.session_state['map_data'] is not None:
        #     map_data = st.session_state['map_data']
        #     lat, lng = map_data['lat'], map_data['lng']
        #     map_ = folium.Map(location=[lat, lng], zoom_start=15)
        #     folium.Marker([lat, lng], popup=map_data['name']).add_to(map_)
        #     st_folium(map_, width=700, height=500)
            
        #     # # 지도를 렌더링하고 유지하도록 st.write 사용
        #     # st.write(st_folium(map_, width=700, height=500))


        # 평가 모드일 때 DB에 데이터 저장
        if eval_mode:
            evaluation_starttime = datetime.now().strftime("%y%m%d_%H:%M:%S")
            this_turn_id = (len(messages) // 2 + 1)
            db_instance_row = {
                'session_id': session_id,
                'evaluator_name': evaluator_name,
                'evaluation_starttime': evaluation_starttime,
                'function_model': st.session_state.current_model,
                'turn_id': this_turn_id,
                'user_utterance': messages[-1]['content'],
                'system_response': response
            }
            st.session_state.db_chats_list.append(db_instance_row)

        if not (need_search and query):
        # 대화 종료 시그널 처리
            if response == "TERMINATED" or "TERMINATED" in response:
                if st.button("New Chat"):
                    if eval_mode and st.session_state.db_chats_list:
                        initialize_evaluation_session(collection)
                        
                    if st.session_state.current_model == 'Sparta-large (LLAMA-3)':
                        st.session_state.messages_4 = []
                    st.session_state.db_chats_list = []

                    del st.session_state.current_model
                    ###del st.session_state.chat_tokenizer
                    clear_unused_memory()
                    st.experimental_rerun()
                    
            else:
                with st.chat_message('assistant'):
                    if response != "TERMINATED":
                        st.markdown(response)

            # 모델의 응답을 메시지 리스트에 추가
            if st.session_state.current_model == "multiturn-chat":
                st.session_state.messages_4.append({'role': 'assistant', 'content': response})





    # "DB에 저장하기" 버튼 추가
    if st.button('대화 저장하기'):
        if eval_mode and st.session_state.db_chats_list:
            collection = get_db_collection(st.session_state.current_model) ### 여기 한줄 더 추가 (0628)
            save_chat_to_db(st.session_state.db_chats_list, collection)
            st.session_state.db_chats_list = []  # 저장 후 리스트 초기화
            if evaluator_name!='Unknown':
                st.write(f"현재 평가자: {evaluator_name}")
            if evaluation_starttime:
                st.write(f"평가 시작 시각: {st.session_state.evaluation_starttime}")
            # if session_id is not None:
            #     st.write(f"평가 세션 ID: {session_id}")
            st.success("채팅 기록이 성공적으로 저장되었습니다.")
            initialize_evaluation_session(collection)
        else:
            st.warning("저장할 채팅 기록이 없습니다.")
            
            
            

            

if __name__ == '__main__':
    main()