import streamlit as st
from datetime import datetime
from pathlib import Path
import pandas as pd
import io
import zipfile

try:
    import qrcode
except ImportError:
    qrcode = None

st.set_page_config(
    page_title="창포마을 치유농장 QR 미션",
    page_icon="🌿",
    layout="centered"
)

DATA_PATH = Path("mission_responses.csv")

MISSIONS = [
    {
        "id": "welcome",
        "title": "1번 QR · 입구 환영 미션",
        "emoji": "🌿",
        "place": "농장 입구 / 안내판 앞",
        "task": "천천히 숨을 3번 들이마시고 내쉬며, 오늘 농장에서 기대하는 감정을 하나 골라보세요.",
        "choices": ["편안함", "기대감", "호기심", "회복", "즐거움"],
        "effect": "방문자의 긴장을 낮추고, 체험에 몰입할 준비를 돕습니다."
    },
    {
        "id": "observe",
        "title": "2번 QR · 식물 관찰 미션",
        "emoji": "🔍",
        "place": "창포 또는 식물 관찰 구역",
        "task": "가장 눈에 들어오는 식물 하나를 고르고, 색·모양·향 중 하나를 자세히 관찰해보세요.",
        "choices": ["색이 인상적이다", "모양이 독특하다", "향이 좋다", "촉감이 궁금하다"],
        "effect": "오감을 활용해 자연과 상호작용하며 집중력을 높입니다."
    },
    {
        "id": "scent",
        "title": "3번 QR · 향기 기억 미션",
        "emoji": "💐",
        "place": "허브 / 향기 체험 구역",
        "task": "식물의 향을 맡고 떠오르는 기억이나 기분을 짧게 적어보세요.",
        "choices": ["어릴 적 기억", "가족", "여행", "휴식", "새로운 느낌"],
        "effect": "향기 자극을 통해 정서적 안정과 긍정적 회상을 유도합니다."
    },
    {
        "id": "walk",
        "title": "4번 QR · 느린 걷기 미션",
        "emoji": "🚶",
        "place": "마을길 / 산책로",
        "task": "30초 동안 평소보다 천천히 걸으며 주변에서 들리는 소리 1가지를 찾아보세요.",
        "choices": ["바람 소리", "새소리", "발걸음 소리", "사람들의 목소리", "기타 자연 소리"],
        "effect": "신체 움직임과 자연 감각을 연결해 마음을 안정시킵니다."
    },
    {
        "id": "message",
        "title": "5번 QR · 오늘의 치유 문장",
        "emoji": "📝",
        "place": "마무리 공간 / 포토존",
        "task": "오늘 체험을 마치며 나에게 해주고 싶은 말을 한 문장으로 적어보세요.",
        "choices": ["수고했어", "천천히 가도 괜찮아", "오늘 잘 쉬었다", "다시 오고 싶다", "내가 나를 돌보는 시간"],
        "effect": "체험의 감정을 정리하고, 방문자의 만족감을 높입니다."
    },
]

MISSION_BY_ID = {m["id"]: m for m in MISSIONS}

if "completed" not in st.session_state:
    st.session_state.completed = []
if "visitor_name" not in st.session_state:
    st.session_state.visitor_name = ""

def save_response(visitor_name, mission, choice, memo):
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "visitor_name": visitor_name or "익명",
        "mission_id": mission["id"],
        "mission_title": mission["title"],
        "place": mission["place"],
        "choice": choice,
        "memo": memo
    }

    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")

def read_responses():
    if DATA_PATH.exists():
        return pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    return pd.DataFrame(columns=[
        "timestamp", "visitor_name", "mission_id", "mission_title", "place", "choice", "memo"
    ])

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

st.title("🌿 창포마을 치유농장 QR 미션")
st.caption("공공데이터 활용 경진대회용 MVP · QR 기반 체험 미션 프로토타입 v3")

query_mission = st.query_params.get("mission", "")

with st.sidebar:
    st.header("메뉴")
    menu = st.radio(
        "이동할 화면을 선택하세요.",
        ["홈", "QR 미션 체험", "QR 코드 만들기", "관리자 데이터", "초기화"]
    )

    st.divider()
    st.write("현재 테스트 주소")
    st.code("http://localhost:8501", language="text")
    st.caption("localhost는 내 컴퓨터에서만 안정적으로 테스트됩니다. 실제 스마트폰 QR용은 나중에 배포 주소가 필요합니다.")

if query_mission in MISSION_BY_ID:
    menu = "QR 미션 체험"

name = st.text_input(
    "방문자 이름 또는 팀명을 입력하세요.",
    value=st.session_state.visitor_name,
    placeholder="예: 1조 / 정성원 / 창포팀"
)
st.session_state.visitor_name = name

completed_count = len(st.session_state.completed)
total_count = len(MISSIONS)
progress = completed_count / total_count
st.progress(progress)
st.write(f"현재 완료한 미션: **{completed_count} / {total_count}개**")

if menu == "홈":
    st.header("서비스 개요")
    st.write(
        "이 앱은 창포마을 치유농장 방문자가 QR 코드를 찍으며 "
        "입구 → 식물 관찰 → 향기 체험 → 산책 → 마무리 회고 순서로 이동하도록 돕는 "
        "체험형 미션 서비스입니다."
    )

    st.subheader("이번 v3에서 추가된 기능")
    st.write("1. 미션별 QR 코드 자동 생성")
    st.write("2. 방문자의 선택과 메모를 CSV 파일로 저장")
    st.write("3. 관리자 화면에서 응답 데이터 확인")
    st.write("4. 응답 데이터를 엑셀에서 열 수 있는 CSV로 다운로드")

    st.success("이제 단순 화면이 아니라, 실제 대회 시연용 MVP 구조에 가까워졌습니다.")

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
    st.write(f'**미션:** {mission["task"]}')

    choice = st.radio("가장 가까운 느낌을 선택하세요.", mission["choices"])
    memo = st.text_area(
        "짧은 기록을 남겨보세요.",
        placeholder="예: 향이 생각보다 편안했고, 잠깐 쉬어가는 느낌이 들었다."
    )

    st.caption(f'기대 효과: {mission["effect"]}')

    if st.button("이 미션 완료하기"):
        complete_mission(mission["id"])
        save_response(st.session_state.visitor_name, mission, choice, memo)
        st.success("미션 완료! 응답이 저장되었습니다.")

    if mission["id"] in st.session_state.completed:
        st.success("이미 완료한 미션입니다.")

    if len(st.session_state.completed) == len(MISSIONS):
        st.balloons()
        st.header("🎉 모든 미션 완료")
        display_name = st.session_state.visitor_name or "방문자"
        st.write(f"**{display_name}님, 창포마을 치유농장 QR 미션을 모두 완료했습니다.**")
        st.write("오늘의 체험이 자연 속에서 쉬어가는 시간이 되었기를 바랍니다.")
        st.caption(f"완료 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

elif menu == "QR 코드 만들기":
    st.header("QR 코드 만들기")
    st.write("미션별 주소를 QR 코드로 만들어 확인하는 화면입니다.")

    base_url = st.text_input(
        "앱 기본 주소",
        value="http://localhost:8501",
        help="지금은 PC 테스트용 주소입니다. 나중에 Streamlit Cloud 등에 배포하면 실제 배포 주소로 바꿔 넣으면 됩니다."
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

    st.warning(
        "중요: localhost QR은 같은 컴퓨터 테스트용입니다. "
        "스마트폰으로 QR을 찍어 실제 접속하려면 앱을 인터넷에 배포해야 합니다."
    )

elif menu == "관리자 데이터":
    st.header("관리자 데이터")
    st.write("방문자가 완료한 미션 기록을 확인하는 화면입니다.")

    df = read_responses()

    if df.empty:
        st.info("아직 저장된 응답이 없습니다. QR 미션 체험에서 미션을 완료하면 여기에 기록됩니다.")
    else:
        st.dataframe(df, use_container_width=True)
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="응답 데이터 CSV 다운로드",
            data=csv_data.encode("utf-8-sig"),
            file_name="mission_responses.csv",
            mime="text/csv"
        )

        st.subheader("간단 요약")
        st.write(f"총 응답 수: **{len(df)}개**")
        st.write("미션별 응답 수")
        st.bar_chart(df["mission_title"].value_counts())

elif menu == "초기화":
    st.header("진행 상황 초기화")
    st.warning("테스트를 다시 시작하고 싶을 때만 누르세요.")

    if st.button("내 화면의 미션 완료 기록 초기화"):
        reset_progress()
        st.success("현재 화면의 진행률이 초기화되었습니다.")

    if st.button("저장된 응답 CSV 삭제"):
        if DATA_PATH.exists():
            DATA_PATH.unlink()
            st.success("저장된 응답 데이터가 삭제되었습니다.")
        else:
            st.info("삭제할 응답 데이터가 없습니다.")
