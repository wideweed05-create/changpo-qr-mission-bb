import streamlit as st
from datetime import datetime
from pathlib import Path
import pandas as pd
import io
import zipfile
import random

try:
    import qrcode
except ImportError:
    qrcode = None

st.set_page_config(
    page_title="팜어드벤처 | 창포마을 QR 미션",
    page_icon="🌿",
    layout="centered"
)

DATA_PATH = Path("mission_responses.csv")
QUIZ_PATH = Path("quiz_responses.csv")

MISSIONS = [
    {
        "id": "welcome",
        "title": "1번 QR · 입구 환영 미션",
        "emoji": "🌿",
        "place": "농장 입구 / 안내판 앞",
        "task": "천천히 숨을 3번 들이마시고 내쉬며, 오늘 농장에서 기대하는 감정을 하나 골라보세요.",
        "choices": ["편안함", "기대감", "호기심", "회복", "즐거움"],
        "effect": "방문자의 긴장을 낮추고, 체험에 몰입할 준비를 돕습니다.",
    },
    {
        "id": "observe",
        "title": "2번 QR · 식물 관찰 미션",
        "emoji": "🔍",
        "place": "작물 관찰 구역",
        "task": "작물의 잎, 줄기, 꽃, 열매 중 하나를 골라 자세히 관찰해보세요.",
        "choices": ["잎이 인상적이다", "꽃이 눈에 띈다", "열매가 궁금하다", "향이 좋다"],
        "effect": "오감을 활용해 자연과 상호작용하며 집중력을 높입니다.",
    },
    {
        "id": "scent",
        "title": "3번 QR · 향기 기억 미션",
        "emoji": "💐",
        "place": "허브 / 향기 체험 구역",
        "task": "식물의 향을 맡고 떠오르는 기억이나 기분을 짧게 적어보세요.",
        "choices": ["어릴 적 기억", "가족", "여행", "휴식", "새로운 느낌"],
        "effect": "향기 자극을 통해 정서적 안정과 긍정적 회상을 유도합니다.",
    },
    {
        "id": "walk",
        "title": "4번 QR · 느린 걷기 미션",
        "emoji": "🚶",
        "place": "마을길 / 산책로",
        "task": "30초 동안 평소보다 천천히 걸으며 주변에서 들리는 소리 1가지를 찾아보세요.",
        "choices": ["바람 소리", "새소리", "발걸음 소리", "사람들의 목소리", "기타 자연 소리"],
        "effect": "신체 움직임과 자연 감각을 연결해 마음을 안정시킵니다.",
    },
    {
        "id": "message",
        "title": "5번 QR · 오늘의 치유 문장",
        "emoji": "📝",
        "place": "마무리 공간 / 포토존",
        "task": "오늘 체험을 마치며 나에게 해주고 싶은 말을 한 문장으로 적어보세요.",
        "choices": ["수고했어", "천천히 가도 괜찮아", "오늘 잘 쉬었다", "다시 오고 싶다", "내가 나를 돌보는 시간"],
        "effect": "체험의 감정을 정리하고, 방문자의 만족감을 높입니다.",
    },
]

MISSION_BY_ID = {m["id"]: m for m in MISSIONS}

CROP_INFO = {
    "딸기": {
        "summary": "딸기는 서늘한 환경을 좋아하는 과채류로, 꽃이 핀 뒤 열매가 맺히며 붉게 익어갑니다.",
        "easy_info": [
            "딸기는 너무 덥지 않은 서늘한 환경에서 비교적 잘 자랍니다.",
            "딸기 잎은 보통 3장의 작은 잎이 모인 형태로 보입니다.",
            "딸기 꽃은 대체로 흰색이며, 꽃이 핀 뒤 열매가 생깁니다.",
            "딸기 재배에서는 습도가 너무 높으면 병이 생기기 쉬워 환기가 중요합니다.",
            "딸기는 열매의 색이 초록색에서 붉은색으로 변하면서 익어갑니다."
        ],
        "quiz": [
            {
                "question": "딸기는 어떤 환경에서 비교적 잘 자랄까요?",
                "options": ["너무 더운 환경", "서늘한 환경", "항상 어두운 환경", "물이 전혀 없는 환경"],
                "answer": "서늘한 환경",
                "explain": "딸기는 고온에 약한 편이라 너무 더운 환경보다는 서늘한 환경이 재배에 유리합니다."
            },
            {
                "question": "딸기 잎의 특징으로 알맞은 것은 무엇일까요?",
                "options": ["대체로 3장의 작은 잎이 모여 보인다", "잎이 바늘처럼 뾰족하다", "잎이 전혀 없다", "잎이 물속에서만 자란다"],
                "answer": "대체로 3장의 작은 잎이 모여 보인다",
                "explain": "딸기 잎은 방문객이 관찰하기 좋은 대표적인 특징 중 하나입니다."
            },
            {
                "question": "딸기 재배에서 습도가 너무 높으면 왜 주의해야 할까요?",
                "options": ["병이 생기기 쉬워서", "딸기 색이 파랗게 변해서", "잎이 모두 사라져서", "꽃이 검은색으로만 피어서"],
                "answer": "병이 생기기 쉬워서",
                "explain": "습도가 높으면 병해 발생 가능성이 커질 수 있어 환기와 관리가 중요합니다."
            },
            {
                "question": "딸기 꽃은 보통 어떤 색으로 많이 알려져 있을까요?",
                "options": ["흰색", "검은색", "파란색", "회색"],
                "answer": "흰색",
                "explain": "딸기는 흰색 꽃이 핀 뒤 열매가 맺히는 과정을 관찰할 수 있습니다."
            },
        ],
        "mission_templates": [
            "딸기 잎을 관찰하고 잎이 몇 장으로 나뉘어 보이는지 적어보세요.",
            "딸기 열매의 색을 관찰하고 익어가는 단계를 상상해보세요.",
            "딸기 꽃이나 열매를 보고 가장 눈에 띄는 특징을 한 문장으로 적어보세요."
        ]
    },
    "토마토": {
        "summary": "토마토는 햇빛을 좋아하는 과채류로, 꽃이 핀 뒤 초록색 열매가 생기고 점차 붉게 익습니다.",
        "easy_info": [
            "토마토는 햇빛이 충분한 환경에서 잘 자랍니다.",
            "토마토 줄기와 잎에서는 특유의 향이 납니다.",
            "토마토 꽃은 노란색으로 피는 경우가 많습니다.",
            "토마토는 열매가 초록색에서 붉은색으로 변하면서 익어갑니다.",
            "토마토 재배에서는 물 관리와 통풍이 중요합니다."
        ],
        "quiz": [
            {
                "question": "토마토가 잘 자라는 데 중요한 조건은 무엇일까요?",
                "options": ["충분한 햇빛", "완전한 어둠", "얼음물", "바람이 전혀 없는 밀폐 공간"],
                "answer": "충분한 햇빛",
                "explain": "토마토는 햇빛을 좋아하는 작물로 알려져 있습니다."
            },
            {
                "question": "토마토 꽃은 보통 어떤 색으로 많이 알려져 있을까요?",
                "options": ["노란색", "검은색", "보라색", "회색"],
                "answer": "노란색",
                "explain": "토마토는 노란색 꽃이 핀 뒤 열매가 달리는 모습을 관찰할 수 있습니다."
            },
            {
                "question": "토마토 열매가 익을 때 흔히 나타나는 변화는 무엇일까요?",
                "options": ["초록색에서 붉은색으로 변한다", "잎으로 변한다", "뿌리로 변한다", "항상 흰색만 유지된다"],
                "answer": "초록색에서 붉은색으로 변한다",
                "explain": "토마토는 익어가며 색이 변하는 과정을 관찰하기 좋은 작물입니다."
            },
        ],
        "mission_templates": [
            "토마토 잎이나 줄기에서 느껴지는 향을 표현해보세요.",
            "토마토 열매의 색을 보고 익은 정도를 추측해보세요.",
            "토마토 꽃이나 열매를 관찰하고 가장 인상적인 점을 적어보세요."
        ]
    },
    "상추": {
        "summary": "상추는 잎을 먹는 채소로, 잎의 색과 모양을 쉽게 관찰할 수 있어 교육형 체험에 적합합니다.",
        "easy_info": [
            "상추는 잎을 주로 먹는 채소입니다.",
            "상추 잎은 넓고 부드러운 편이며 색과 모양이 다양합니다.",
            "상추는 비교적 짧은 기간 안에 자라는 모습을 관찰하기 좋습니다.",
            "상추 재배에는 물 관리와 햇빛이 중요합니다."
        ],
        "quiz": [
            {
                "question": "상추에서 우리가 주로 먹는 부분은 어디일까요?",
                "options": ["잎", "나무껍질", "씨앗 껍질", "뿌리만"],
                "answer": "잎",
                "explain": "상추는 잎채소로, 잎을 주로 먹습니다."
            },
            {
                "question": "상추 잎을 관찰할 때 보기 좋은 특징은 무엇일까요?",
                "options": ["잎의 색과 모양", "금속 광택", "돌처럼 딱딱한 표면", "날개 모양의 깃털"],
                "answer": "잎의 색과 모양",
                "explain": "상추는 잎의 색, 주름, 크기 등을 관찰하기 좋습니다."
            },
        ],
        "mission_templates": [
            "상추 잎의 색과 모양을 관찰하고 느낌을 적어보세요.",
            "상추 잎을 자세히 보고 가장자리 모양을 표현해보세요.",
            "상추가 식탁에 오기까지 필요한 과정을 상상해보세요."
        ]
    },
    "버섯": {
        "summary": "버섯은 잎과 꽃이 없는 균류로, 갓과 자루의 모양을 관찰하기 좋은 체험 소재입니다.",
        "easy_info": [
            "버섯은 일반 채소처럼 잎과 꽃이 뚜렷하게 보이지 않습니다.",
            "버섯은 갓과 자루의 모양을 관찰하기 좋습니다.",
            "버섯 재배에서는 온도, 습도, 청결 관리가 중요합니다.",
            "버섯은 어둡고 습한 환경에서 자라는 종류가 많습니다."
        ],
        "quiz": [
            {
                "question": "버섯을 관찰할 때 보기 좋은 부분은 무엇일까요?",
                "options": ["갓과 자루", "꽃잎과 꽃가루", "나뭇가지와 열매", "뾰족한 가시"],
                "answer": "갓과 자루",
                "explain": "버섯은 갓과 자루의 모양, 색, 질감을 관찰하기 좋습니다."
            },
            {
                "question": "버섯 재배에서 특히 중요한 관리 요소는 무엇일까요?",
                "options": ["온도와 습도", "모래성 쌓기", "소금물 주기", "강한 직사광선만 주기"],
                "answer": "온도와 습도",
                "explain": "버섯은 재배 환경의 온도와 습도 관리가 중요합니다."
            },
        ],
        "mission_templates": [
            "버섯의 갓 모양을 관찰하고 어떤 물건과 닮았는지 적어보세요.",
            "버섯의 색과 질감을 관찰하고 느낌을 표현해보세요.",
            "버섯이 자라는 환경을 보고 왜 습도 관리가 중요할지 생각해보세요."
        ]
    },
    "허브": {
        "summary": "허브는 향을 가진 식물이 많아 향기 체험, 감정 회복, 기억 회상 미션에 적합합니다.",
        "easy_info": [
            "허브는 향을 가진 식물이 많습니다.",
            "허브는 잎을 손으로 살짝 문지르면 향이 더 잘 느껴지는 경우가 있습니다.",
            "허브는 차, 음식, 향기 체험 등에 활용될 수 있습니다.",
            "허브 관찰에서는 잎의 향, 모양, 색을 함께 살펴볼 수 있습니다."
        ],
        "quiz": [
            {
                "question": "허브 체험에서 가장 쉽게 느낄 수 있는 감각은 무엇일까요?",
                "options": ["향기", "금속 소리", "전기 신호", "짠맛만"],
                "answer": "향기",
                "explain": "허브는 향기 체험과 연결하기 좋은 식물입니다."
            },
            {
                "question": "허브 잎을 관찰할 때 살펴보기 좋은 것은 무엇일까요?",
                "options": ["향과 잎 모양", "철사 굵기", "유리 조각", "플라스틱 색"],
                "answer": "향과 잎 모양",
                "explain": "허브는 향, 색, 잎 모양을 관찰하는 체험에 적합합니다."
            },
        ],
        "mission_templates": [
            "허브 향을 맡고 떠오르는 기억을 한 단어로 적어보세요.",
            "허브 잎의 모양과 향을 함께 관찰해보세요.",
            "허브 향을 맡은 뒤 지금 기분이 어떻게 바뀌었는지 표현해보세요."
        ]
    },
}

THEME_GUIDE = {
    "힐링형": "감정 기록, 향기, 산책, 회고 중심의 부드러운 미션이 적합합니다.",
    "추리형": "작물 단서 찾기, QR 암호, 관찰 퀴즈를 결합하면 몰입도가 높아집니다.",
    "교육형": "작물의 특징, 생육 환경, 재배 상식을 퀴즈로 연결하는 방식이 좋습니다.",
    "가족형": "함께 말하기, 사진 인증, 협동 미션을 넣으면 가족 단위 참여에 적합합니다.",
    "고령층 배려형": "짧은 동선, 향기 기억, 회상 질문, 충분한 휴식 안내가 중요합니다."
}


def init_state():
    if "completed" not in st.session_state:
        st.session_state.completed = []
    if "visitor_name" not in st.session_state:
        st.session_state.visitor_name = ""
    if "visitor_type" not in st.session_state:
        st.session_state.visitor_type = "일반 성인"
    if "theme" not in st.session_state:
        st.session_state.theme = "힐링형"
    if "crop" not in st.session_state:
        st.session_state.crop = "딸기"


def save_response(visitor_name, visitor_type, theme, crop, mission, choice, memo):
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "visitor_name": visitor_name or "익명",
        "visitor_type": visitor_type,
        "theme": theme,
        "crop": crop,
        "mission_id": mission["id"],
        "mission_title": mission["title"],
        "place": mission["place"],
        "choice": choice,
        "memo": memo,
        "earned_points": 10
    }

    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")


def save_quiz_response(visitor_name, visitor_type, theme, crop, question, selected, answer, correct):
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "visitor_name": visitor_name or "익명",
        "visitor_type": visitor_type,
        "theme": theme,
        "crop": crop,
        "question": question,
        "selected": selected,
        "answer": answer,
        "correct": correct,
        "earned_points": 5 if correct else 0
    }

    if QUIZ_PATH.exists():
        df = pd.read_csv(QUIZ_PATH, encoding="utf-8-sig")
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_csv(QUIZ_PATH, index=False, encoding="utf-8-sig")


def read_csv(path, columns):
    if path.exists():
        return pd.read_csv(path, encoding="utf-8-sig")
    return pd.DataFrame(columns=columns)


def make_qr_png(url):
    if qrcode is None:
        return None
    img = qrcode.make(url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def complete_mission(mission_id):
    if mission_id not in st.session_state.completed:
        st.session_state.completed.append(mission_id)


def reset_progress():
    st.session_state.completed = []


def healing_score(temp, rain, wind, pm_grade, sky, visitor_type):
    score = 100
    reasons = []

    if temp < 5:
        score -= 25
        reasons.append("기온이 매우 낮아 야외 체류 시간을 줄이는 것이 좋습니다.")
    elif temp < 10:
        score -= 12
        reasons.append("다소 쌀쌀하므로 짧은 야외 미션 중심이 적절합니다.")
    elif temp > 32:
        score -= 25
        reasons.append("기온이 높아 그늘·실내형 체험 비중을 높이는 것이 좋습니다.")
    elif temp > 28:
        score -= 12
        reasons.append("조금 더울 수 있어 휴식 구간을 자주 배치하는 것이 좋습니다.")
    else:
        reasons.append("기온이 치유농장 야외 활동에 비교적 적합합니다.")

    if rain >= 10:
        score -= 30
        reasons.append("강수량이 많아 실내형 또는 처마형 체험으로 전환하는 것이 좋습니다.")
    elif rain > 0:
        score -= 12
        reasons.append("비가 예상되어 우산 동선과 미끄럼 주의 안내가 필요합니다.")
    else:
        reasons.append("강수 조건은 야외 체험 진행에 큰 제약이 없습니다.")

    if wind >= 8:
        score -= 15
        reasons.append("바람이 강해 야외 안내판·포토존 안전 확인이 필요합니다.")
    elif wind >= 5:
        score -= 7
        reasons.append("바람이 다소 있어 야외 구조물과 안내물 점검이 필요합니다.")

    pm_penalty = {"좋음": 0, "보통": 5, "나쁨": 20, "매우나쁨": 35}
    score -= pm_penalty.get(pm_grade, 0)
    if pm_grade in ["나쁨", "매우나쁨"]:
        reasons.append("대기질이 좋지 않아 실내형 감각·회고 미션을 우선 추천합니다.")
    else:
        reasons.append("대기질 조건은 야외 활동에 큰 제약이 없습니다.")

    if sky in ["흐림", "비"]:
        score -= 5
        reasons.append("흐리거나 비가 오는 날은 밝은 색 관찰·향기 체험 중심이 좋습니다.")

    if visitor_type in ["고령층", "가족/아동"]:
        score -= 5
        reasons.append("방문자 특성을 고려해 이동 거리를 짧게 설계하는 것이 좋습니다.")
    elif visitor_type == "요양원/복지기관":
        score -= 8
        reasons.append("복지기관 단체 방문은 안전 인솔과 휴식 지점 배치가 중요합니다.")

    return max(0, min(100, score)), reasons


def recommend_course(score, pm_grade, rain, temp, visitor_type):
    if pm_grade in ["나쁨", "매우나쁨"] or rain >= 10 or temp > 32 or temp < 5:
        label = "실내·단축형 코스"
        course_ids = ["welcome", "scent", "message"]
        message = "날씨나 대기질 부담을 줄이기 위해 이동을 줄이고 감각·회고형 미션 중심으로 운영하세요."
    elif visitor_type in ["고령층", "가족/아동", "요양원/복지기관"]:
        label = "안전 배려형 코스"
        course_ids = ["welcome", "observe", "scent", "message"]
        message = "참여자의 체력 부담을 줄이고, 관찰·향기 체험을 중심으로 천천히 진행하세요."
    elif score >= 80:
        label = "표준 야외형 코스"
        course_ids = ["welcome", "observe", "scent", "walk", "message"]
        message = "현재 조건에서는 전체 QR 미션을 순서대로 진행하기 좋습니다."
    else:
        label = "혼합형 코스"
        course_ids = ["welcome", "observe", "scent", "message"]
        message = "일부 야외 미션은 가능하지만, 체류 시간과 휴식 지점을 조정하는 것이 좋습니다."

    return label, [MISSION_BY_ID[cid]["title"] for cid in course_ids], message


def theme_hint(theme):
    return THEME_GUIDE.get(theme, "")


def get_crop_mission(crop, theme):
    crop_data = CROP_INFO[crop]
    base = random.choice(crop_data["mission_templates"])
    if theme == "추리형":
        return f"{base} 그리고 이 특징이 어떤 생육환경과 관련 있을지 단서처럼 추리해보세요."
    if theme == "교육형":
        return f"{base} 관찰한 내용을 바탕으로 작물의 생육 특징을 하나 배워보세요."
    if theme == "가족형":
        return f"{base} 가족이나 친구와 서로 관찰한 점을 비교해보세요."
    if theme == "고령층 배려형":
        return f"{base} 가까운 자리에서 천천히 관찰하고 편안하게 이야기해보세요."
    return base


init_state()

st.title("🌿 팜어드벤처: 창포마을 QR 미션")
st.caption("작목별 쉬운 퀴즈 생성 기능이 추가된 v5")

query_mission = st.query_params.get("mission", "")

with st.sidebar:
    st.header("메뉴")
    menu = st.radio(
        "이동할 화면을 선택하세요.",
        [
            "홈",
            "팜어드벤처 소개",
            "공공데이터 추천",
            "작목 퀴즈 생성",
            "QR 미션 체험",
            "QR 코드 만들기",
            "관리자 데이터",
            "초기화"
        ]
    )

if query_mission in MISSION_BY_ID:
    menu = "QR 미션 체험"

st.subheader("방문자 기본 정보")
name = st.text_input(
    "방문자 이름 또는 팀명을 입력하세요.",
    value=st.session_state.visitor_name,
    placeholder="예: 1조 / 정성원 / 창포팀"
)
st.session_state.visitor_name = name

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.session_state.visitor_type = st.selectbox(
        "방문자 유형",
        ["일반 성인", "가족/아동", "고령층", "요양원/복지기관", "학생 단체", "연인/친구"],
        index=["일반 성인", "가족/아동", "고령층", "요양원/복지기관", "학생 단체", "연인/친구"].index(st.session_state.visitor_type)
        if st.session_state.visitor_type in ["일반 성인", "가족/아동", "고령층", "요양원/복지기관", "학생 단체", "연인/친구"] else 0
    )
with col_b:
    st.session_state.theme = st.selectbox(
        "체험 테마",
        ["힐링형", "추리형", "교육형", "가족형", "고령층 배려형"],
        index=["힐링형", "추리형", "교육형", "가족형", "고령층 배려형"].index(st.session_state.theme)
        if st.session_state.theme in ["힐링형", "추리형", "교육형", "가족형", "고령층 배려형"] else 0
    )
with col_c:
    st.session_state.crop = st.selectbox(
        "체험 작목",
        list(CROP_INFO.keys()),
        index=list(CROP_INFO.keys()).index(st.session_state.crop)
        if st.session_state.crop in CROP_INFO else 0
    )

mission_points = len(st.session_state.completed) * 10
st.progress(len(st.session_state.completed) / len(MISSIONS))
st.write(f"현재 완료한 미션: **{len(st.session_state.completed)} / {len(MISSIONS)}개** · 미션 포인트: **{mission_points}P**")

if menu == "홈":
    st.header("서비스 개요")
    st.write(
        "팜어드벤처는 작목별 특징과 공공데이터 기반 운영 조건을 활용해 "
        "농장 방문객에게 QR 미션과 쉬운 작물 퀴즈를 제공하는 치유농장 체험 MVP입니다."
    )

    st.subheader("v5 핵심 기능")
    st.write("1. 작목별 쉬운 정보 제공")
    st.write("2. 작목 특징 기반 퀴즈 생성")
    st.write("3. 작목별 관찰 미션 추천")
    st.write("4. 대회 발표 요약 메뉴를 '팜어드벤처 소개'로 변경")
    st.write("5. 방문자 퀴즈 기록 저장")

elif menu == "팜어드벤처 소개":
    st.header("팜어드벤처 소개")
    st.subheader("한 줄 설명")
    st.success(
        "팜어드벤처는 작목 정보, 공공데이터, QR 미션을 결합해 "
        "농장을 방문객 맞춤형 농장뮤지엄으로 바꾸는 체험 플랫폼입니다."
    )

    st.subheader("문제 인식")
    st.write(
        "기존 농촌 체험은 수확·만들기 중심의 일회성 프로그램이 많아 재방문 유도와 데이터 기반 개선이 어렵습니다. "
        "또한 농장주가 매번 새로운 스토리와 퀴즈를 만들기 어렵다는 문제가 있습니다."
    )

    st.subheader("해결 방식")
    st.write(
        "농장주는 작목과 테마를 선택하고, 방문객은 QR을 따라 이동하며 작물 관찰 미션과 쉬운 퀴즈를 수행합니다. "
        "앱은 방문자 기록을 저장해 농장 운영 개선에 활용할 수 있도록 돕습니다."
    )

    st.subheader("공공데이터 활용 방향")
    st.write("1. 기상·대기질 데이터: 당일 체험 코스 추천")
    st.write("2. 작목 생육 정보: 작목별 퀴즈와 관찰 미션 생성")
    st.write("3. 농산물 가격·제철 정보: 향후 포인트 리워드와 농산물 할인 추천에 활용")

    st.subheader("향후 확장")
    st.write("1. 농장주 원클릭 미션 생성기")
    st.write("2. 실제 공공데이터 API 자동 연동")
    st.write("3. 수료증 및 포인트 마켓")
    st.write("4. RAG 기반 안전한 AI 미션 생성")

elif menu == "공공데이터 추천":
    st.header("공공데이터 기반 체험 추천")
    st.write(
        "현재는 API 키 없이 수동 입력으로 추천 로직을 시연합니다. "
        "향후 기상청, 에어코리아, 농업기상 API와 자동 연동할 수 있습니다."
    )

    col1, col2 = st.columns(2)
    with col1:
        temp = st.slider("기온(℃)", min_value=-10, max_value=40, value=22)
        rain = st.slider("예상 강수량(mm)", min_value=0, max_value=50, value=0)
        sky = st.selectbox("하늘 상태", ["맑음", "구름많음", "흐림", "비"])
    with col2:
        wind = st.slider("풍속(m/s)", min_value=0, max_value=20, value=2)
        pm_grade = st.selectbox("미세먼지 상태", ["좋음", "보통", "나쁨", "매우나쁨"])
        visitor_type_for_recommend = st.selectbox(
            "추천 기준 방문자 유형",
            ["일반 성인", "가족/아동", "고령층", "요양원/복지기관", "학생 단체", "연인/친구"],
            index=["일반 성인", "가족/아동", "고령층", "요양원/복지기관", "학생 단체", "연인/친구"].index(st.session_state.visitor_type)
        )

    score, reasons = healing_score(temp, rain, wind, pm_grade, sky, visitor_type_for_recommend)
    label, course, message = recommend_course(score, pm_grade, rain, temp, visitor_type_for_recommend)

    st.metric("오늘의 치유체험 적합도", f"{score}점")
    if score >= 80:
        st.success("야외형 치유농장 체험에 적합한 조건입니다.")
    elif score >= 60:
        st.warning("체험은 가능하지만 일부 동선 조정이 필요합니다.")
    else:
        st.error("실외 체험 비중을 줄이고 안전·실내형 프로그램을 우선하는 것이 좋습니다.")

    st.subheader(f"추천 코스: {label}")
    st.write(message)
    for i, item in enumerate(course, start=1):
        st.write(f"{i}. {item}")

    st.subheader("추천 근거")
    for r in reasons:
        st.write(f"- {r}")

    st.subheader("공공데이터 적용 구조")
    st.table([
        {"공공데이터": "기상청 단기예보", "활용값": "기온, 강수량, 하늘상태, 풍속", "앱 적용": "야외/실내 코스 추천"},
        {"공공데이터": "에어코리아 대기오염정보", "활용값": "미세먼지, 초미세먼지, 오존", "앱 적용": "실외 체류 시간 조정"},
        {"공공데이터": "농업기상 관측데이터", "활용값": "기온, 습도, 일사량", "앱 적용": "농장 현장 환경 판단"},
        {"공공데이터": "작목 생육 정보", "활용값": "작물 특징, 생육환경, 관찰 포인트", "앱 적용": "퀴즈와 미션 생성"}
    ])

elif menu == "작목 퀴즈 생성":
    st.header("작목별 쉬운 퀴즈 생성")
    crop = st.session_state.crop
    crop_data = CROP_INFO[crop]

    st.subheader(f"선택 작목: {crop}")
    st.write(crop_data["summary"])

    st.write("작목 기본 정보")
    for info in crop_data["easy_info"]:
        st.write(f"- {info}")

    st.divider()
    st.subheader("추천 관찰 미션")
    st.info(get_crop_mission(crop, st.session_state.theme))

    st.divider()
    st.subheader("퀴즈 풀기")
    quiz = st.selectbox(
        "풀어볼 퀴즈를 선택하세요.",
        crop_data["quiz"],
        format_func=lambda q: q["question"]
    )
    selected = st.radio("정답을 선택하세요.", quiz["options"])

    if st.button("정답 확인 및 기록 저장"):
        correct = selected == quiz["answer"]
        save_quiz_response(
            st.session_state.visitor_name,
            st.session_state.visitor_type,
            st.session_state.theme,
            crop,
            quiz["question"],
            selected,
            quiz["answer"],
            correct
        )

        if correct:
            st.success(f"정답입니다! 5P가 적립되었습니다. 설명: {quiz['explain']}")
        else:
            st.error(f"아쉽습니다. 정답은 '{quiz['answer']}'입니다. 설명: {quiz['explain']}")

    st.caption("현재 퀴즈는 시연용 데이터 기반입니다. 향후 농사로·농촌진흥청 등 공식 작목 정보를 연결해 확장할 수 있습니다.")

elif menu == "QR 미션 체험":
    st.header("QR 미션 체험")

    default_index = 0
    if query_mission in MISSION_BY_ID:
        default_index = [m["id"] for m in MISSIONS].index(query_mission)

    selected_title = st.selectbox(
        "미션을 선택하세요.",
        [m["title"] for m in MISSIONS],
        index=default_index
    )
    mission = next(m for m in MISSIONS if m["title"] == selected_title)

    st.divider()
    st.subheader(f'{mission["emoji"]} {mission["title"]}')
    st.write(f'**장소:** {mission["place"]}')

    if mission["id"] == "observe":
        crop_mission = get_crop_mission(st.session_state.crop, st.session_state.theme)
        st.write(f"**작목 연계 미션:** {crop_mission}")
    else:
        st.write(f'**미션:** {mission["task"]}')

    st.caption(f"현재 테마: {st.session_state.theme} · {theme_hint(st.session_state.theme)}")

    choice = st.radio("가장 가까운 느낌을 선택하세요.", mission["choices"])
    memo = st.text_area("짧은 기록을 남겨보세요.", placeholder="예: 잎 모양이 생각보다 독특했다.")

    st.caption(f'기대 효과: {mission["effect"]}')

    if st.button("이 미션 완료하기"):
        complete_mission(mission["id"])
        save_response(
            st.session_state.visitor_name,
            st.session_state.visitor_type,
            st.session_state.theme,
            st.session_state.crop,
            mission,
            choice,
            memo
        )
        st.success("미션 완료! 응답이 저장되고 10P가 적립되었습니다.")

    if mission["id"] in st.session_state.completed:
        st.success("이미 완료한 미션입니다.")

    if len(st.session_state.completed) == len(MISSIONS):
        st.balloons()
        st.header("🎉 모든 미션 완료")
        display_name = st.session_state.visitor_name or "방문자"
        st.write(f"**{display_name}님, 창포마을 치유농장 QR 미션을 모두 완료했습니다.**")
        st.write("미션 포인트: **50P**")
        st.write("사용 가능 쿠폰: **창포마을 농산물 5% 할인 쿠폰**")
        st.caption(f"완료 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

elif menu == "QR 코드 만들기":
    st.header("QR 코드 만들기")
    base_url = st.text_input(
        "앱 기본 주소",
        value="http://localhost:8501",
        help="배포 주소가 있으면 이 칸에 Streamlit 앱 주소를 넣으세요."
    ).strip().rstrip("/")

    if qrcode is None:
        st.error("qrcode 패키지가 설치되지 않았습니다. requirements.txt에 qrcode[pil]이 필요합니다.")
    else:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for m in MISSIONS:
                url = f"{base_url}/?mission={m['id']}"
                qr_buffer = make_qr_png(url)
                if qr_buffer is not None:
                    zip_file.writestr(f"{m['id']}_qr.png", qr_buffer.getvalue())

                st.subheader(m["title"])
                st.code(url, language="text")
                st.image(qr_buffer, width=180)
                st.download_button(
                    label=f"{m['title']} QR 이미지 다운로드",
                    data=qr_buffer.getvalue(),
                    file_name=f"{m['id']}_qr.png",
                    mime="image/png"
                )
                st.divider()

        zip_buffer.seek(0)
        st.download_button(
            label="전체 QR 이미지 ZIP으로 다운로드",
            data=zip_buffer.getvalue(),
            file_name="changpo_qr_codes.zip",
            mime="application/zip"
        )

elif menu == "관리자 데이터":
    st.header("관리자 데이터")
    mission_df = read_csv(DATA_PATH, [
        "timestamp", "visitor_name", "visitor_type", "theme", "crop", "mission_id",
        "mission_title", "place", "choice", "memo", "earned_points"
    ])
    quiz_df = read_csv(QUIZ_PATH, [
        "timestamp", "visitor_name", "visitor_type", "theme", "crop", "question",
        "selected", "answer", "correct", "earned_points"
    ])

    total_mission_records = len(mission_df)
    total_quiz_records = len(quiz_df)
    total_points = 0
    if not mission_df.empty and "earned_points" in mission_df.columns:
        total_points += int(mission_df["earned_points"].sum())
    if not quiz_df.empty and "earned_points" in quiz_df.columns:
        total_points += int(quiz_df["earned_points"].sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("미션 기록", f"{total_mission_records}개")
    c2.metric("퀴즈 기록", f"{total_quiz_records}개")
    c3.metric("총 적립 포인트", f"{total_points}P")

    st.subheader("미션 응답 데이터")
    if mission_df.empty:
        st.info("아직 저장된 미션 응답이 없습니다.")
    else:
        st.dataframe(mission_df, use_container_width=True)
        st.download_button(
            label="미션 응답 CSV 다운로드",
            data=mission_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
            file_name="mission_responses.csv",
            mime="text/csv"
        )

    st.subheader("퀴즈 응답 데이터")
    if quiz_df.empty:
        st.info("아직 저장된 퀴즈 응답이 없습니다.")
    else:
        st.dataframe(quiz_df, use_container_width=True)
        st.download_button(
            label="퀴즈 응답 CSV 다운로드",
            data=quiz_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
            file_name="quiz_responses.csv",
            mime="text/csv"
        )

        if "crop" in quiz_df.columns:
            st.subheader("작목별 퀴즈 참여 수")
            st.bar_chart(quiz_df["crop"].value_counts())

elif menu == "초기화":
    st.header("진행 상황 초기화")
    st.warning("테스트를 다시 시작하고 싶을 때만 누르세요.")

    if st.button("내 화면의 미션 완료 기록 초기화"):
        reset_progress()
        st.success("현재 화면의 진행률이 초기화되었습니다.")

    if st.button("저장된 미션 응답 CSV 삭제"):
        if DATA_PATH.exists():
            DATA_PATH.unlink()
            st.success("저장된 미션 응답 데이터가 삭제되었습니다.")
        else:
            st.info("삭제할 미션 응답 데이터가 없습니다.")

    if st.button("저장된 퀴즈 응답 CSV 삭제"):
        if QUIZ_PATH.exists():
            QUIZ_PATH.unlink()
            st.success("저장된 퀴즈 응답 데이터가 삭제되었습니다.")
        else:
            st.info("삭제할 퀴즈 응답 데이터가 없습니다.")
