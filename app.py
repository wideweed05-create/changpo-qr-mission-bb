
import streamlit as st
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote
import pandas as pd
import io, zipfile
try:
    import qrcode
except Exception:
    qrcode = None

st.set_page_config(page_title="팜어드벤처 | 창포마을 QR 미션", page_icon="🌿", layout="centered")

MISSION_FILE = Path("mission_responses.csv")
QUIZ_FILE = Path("quiz_responses.csv")
GEN_FILE = Path("generated_mission_sets.csv")

CROPS = {
    "딸기": {
        "summary": "딸기는 서늘한 환경을 좋아하는 과채류로, 흰 꽃이 핀 뒤 열매가 맺히고 붉게 익어갑니다.",
        "feature": "흰 꽃, 세 장처럼 보이는 잎, 붉게 익는 열매",
        "env": "서늘한 온도, 적절한 습도, 환기 관리",
        "info": ["딸기는 너무 덥지 않은 서늘한 환경에서 비교적 잘 자랍니다.", "딸기 잎은 보통 3장의 작은 잎이 모인 형태로 보입니다.", "습도가 너무 높으면 병이 생기기 쉬워 환기가 중요합니다."],
        "quiz": [("딸기는 어떤 환경에서 비교적 잘 자랄까요?", ["서늘한 환경", "항상 어두운 환경", "물이 전혀 없는 환경", "매우 뜨거운 환경"], "서늘한 환경"), ("딸기 잎의 특징으로 알맞은 것은?", ["3장의 작은 잎이 모여 보인다", "잎이 전혀 없다", "바늘처럼 뾰족하다", "물속에서만 자란다"], "3장의 작은 잎이 모여 보인다")]
    },
    "토마토": {
        "summary": "토마토는 햇빛을 좋아하는 과채류로, 노란 꽃이 핀 뒤 초록색 열매가 생기고 점차 붉게 익습니다.",
        "feature": "노란 꽃, 특유의 잎 향, 초록색에서 붉게 익는 열매",
        "env": "충분한 햇빛, 물 관리, 통풍",
        "info": ["토마토는 햇빛이 충분한 환경에서 잘 자랍니다.", "토마토 꽃은 노란색으로 피는 경우가 많습니다.", "토마토 열매는 초록색에서 붉은색으로 변하며 익어갑니다."],
        "quiz": [("토마토가 잘 자라는 데 중요한 조건은?", ["충분한 햇빛", "완전한 어둠", "얼음물", "소금물"], "충분한 햇빛"), ("토마토 꽃은 보통 어떤 색일까요?", ["노란색", "검은색", "파란색", "회색"], "노란색")]
    },
    "상추": {
        "summary": "상추는 잎을 먹는 채소로, 잎의 색과 모양을 쉽게 관찰할 수 있어 교육형 체험에 적합합니다.",
        "feature": "넓은 잎, 다양한 잎 색과 주름, 빠른 생장",
        "env": "적절한 햇빛, 물 관리, 서늘한 환경",
        "info": ["상추는 잎을 주로 먹는 채소입니다.", "상추 잎은 넓고 부드러운 편이며 색과 모양이 다양합니다.", "상추는 자라는 모습을 비교적 쉽게 관찰할 수 있습니다."],
        "quiz": [("상추에서 우리가 주로 먹는 부분은?", ["잎", "나무껍질", "씨앗 껍질", "뿌리만"], "잎"), ("상추 잎에서 관찰하기 좋은 것은?", ["잎의 색과 모양", "금속 광택", "돌처럼 딱딱한 표면", "깃털"], "잎의 색과 모양")]
    },
    "버섯": {
        "summary": "버섯은 잎과 꽃이 뚜렷하지 않은 균류로, 갓과 자루의 모양을 관찰하기 좋은 체험 소재입니다.",
        "feature": "갓과 자루, 잎과 꽃이 없는 형태, 부드러운 질감",
        "env": "온도와 습도 관리, 청결한 재배 환경",
        "info": ["버섯은 갓과 자루의 모양을 관찰하기 좋습니다.", "버섯 재배에서는 온도와 습도 관리가 중요합니다.", "버섯은 청결한 재배 환경이 중요합니다."],
        "quiz": [("버섯을 관찰할 때 보기 좋은 부분은?", ["갓과 자루", "꽃잎과 꽃가루", "나뭇가지", "가시"], "갓과 자루"), ("버섯 재배에서 중요한 관리 요소는?", ["온도와 습도", "소금물", "강한 직사광선", "모래성"], "온도와 습도")]
    },
    "허브": {
        "summary": "허브는 향을 가진 식물이 많아 향기 체험과 감정 회복 미션에 적합합니다.",
        "feature": "향이 나는 잎, 다양한 잎 모양, 차와 음식 활용",
        "env": "적절한 햇빛, 물 관리, 통풍",
        "info": ["허브는 향을 가진 식물이 많습니다.", "허브 잎을 살짝 문지르면 향이 더 잘 느껴지는 경우가 있습니다.", "허브는 차, 음식, 향기 체험 등에 활용될 수 있습니다."],
        "quiz": [("허브 체험에서 쉽게 느낄 수 있는 감각은?", ["향기", "금속 소리", "전기 신호", "짠맛만"], "향기"), ("허브 잎을 관찰할 때 보기 좋은 것은?", ["향과 잎 모양", "철사 굵기", "유리 조각", "플라스틱 색"], "향과 잎 모양")]
    }
}

THEMES = {
    "힐링형": "감정 기록, 향기, 산책, 회고 중심의 부드러운 미션",
    "추리형": "작물 단서 찾기, QR 암호, 관찰 퀴즈 중심의 몰입 미션",
    "교육형": "작물 특징, 생육환경, 재배 상식을 배우는 미션",
    "가족형": "함께 말하기, 사진 인증, 협동 활동 중심 미션",
    "고령층 배려형": "짧은 동선, 향기 기억, 회상 질문, 휴식 중심 미션"
}
VISITORS = ["일반 성인", "가족/아동", "고령층", "요양원/복지기관", "학생 단체", "연인/친구"]
STATIC = [
    {"id":"welcome","title":"1번 QR · 입구 환영 미션","place":"농장 입구","task":"오늘 농장에서 기대하는 감정을 하나 골라보세요.","choices":["편안함","기대감","호기심","회복"]},
    {"id":"observe","title":"2번 QR · 작물 관찰 미션","place":"작물 관찰 구역","task":"선택한 작물의 잎, 꽃, 열매 중 하나를 관찰해보세요.","choices":["잎","꽃","열매","향"]},
    {"id":"scent","title":"3번 QR · 향기 기억 미션","place":"향기 체험 구역","task":"식물의 향을 맡고 떠오르는 기분을 적어보세요.","choices":["휴식","기억","가족","여행"]},
    {"id":"walk","title":"4번 QR · 느린 걷기 미션","place":"산책로","task":"천천히 걸으며 들리는 소리 하나를 찾아보세요.","choices":["바람","새","발걸음","목소리"]},
    {"id":"message","title":"5번 QR · 오늘의 치유 문장","place":"마무리 공간","task":"오늘 나에게 해주고 싶은 말을 적어보세요.","choices":["수고했어","괜찮아","잘 쉬었다","다시 오고 싶다"]}
]

def init():
    st.session_state.setdefault("visitor_name", "")
    st.session_state.setdefault("visitor_type", "일반 성인")
    st.session_state.setdefault("theme", "힐링형")
    st.session_state.setdefault("crop", "딸기")
    st.session_state.setdefault("completed", [])
    st.session_state.setdefault("generated", [])
    st.session_state.setdefault("app_base_url", guess_base_url() or "https://changpo-qr-mission-bb.streamlit.app")

def append_csv(path, row):
    df = pd.DataFrame([row])
    if path.exists():
        old = pd.read_csv(path, encoding="utf-8-sig")
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")

def read_csv(path):
    return pd.read_csv(path, encoding="utf-8-sig") if path.exists() else pd.DataFrame()

def qr_png(url):
    if qrcode is None: return None
    img = qrcode.make(url)
    buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0); return buf

def gen_missions(farm, region, crop, visitor, theme, count=5):
    c = CROPS[crop]
    missions = [
        {"id":"gen1","title":f"1번 QR · {farm} 입장 미션","place":"농장 입구","task":f"{farm}에 들어서며 오늘 {crop} 체험에서 기대되는 느낌을 하나 골라보세요.","choices":["기대돼요","편안해지고 싶어요","배우고 싶어요","사진을 남기고 싶어요"]},
        {"id":"gen2","title":f"2번 QR · {crop} 관찰 미션","place":f"{crop} 관찰 구역","task":f"{crop}의 대표 특징인 '{c['feature']}'을 관찰하고 가장 눈에 띄는 점을 적어보세요.","choices":["잎","꽃","열매","향/질감"]},
        {"id":"gen3","title":f"3번 QR · {crop} 생육환경 퀴즈","place":"작물 설명판 앞","task":f"{crop}이 잘 자라는 데 중요한 환경은 무엇일까요? 힌트: {c['env']}","choices":["온도","습도","햇빛","물 관리","통풍"]},
        {"id":"gen4","title":f"4번 QR · {theme} 스토리 미션","place":"체험 동선 중간","task":f"{THEMES[theme]} 방향으로 {crop}을 보고 떠오르는 이야기나 느낌을 적어보세요.","choices":["힐링","추리","교육","가족","회상"]},
        {"id":"gen5","title":"5번 QR · 마무리 수료 미션","place":"마무리 공간","task":f"오늘 {crop} 체험에서 새롭게 알게 된 점 하나와 기억에 남는 순간을 적어보세요.","choices":["작물 특징","재배 환경","농장 분위기","함께한 사람"]}
    ]
    if theme == "추리형": missions[2]["task"] = f"단서: {crop}의 생육환경은 '{c['env']}'입니다. 이 조건이 왜 중요한지 추리해보세요."
    if theme == "가족형": missions[3]["task"] = f"가족이나 친구와 함께 {crop}을 관찰하고 서로 다르게 본 점을 이야기해보세요."
    if theme == "고령층 배려형": missions[3]["task"] = f"가까운 자리에서 천천히 {crop}을 관찰하고 떠오르는 기억을 이야기해보세요."
    return missions[:count]

def gen_url(base, farm, region, crop, visitor, theme, idx):
    return f"{base}/?mode=generated&farm={quote(farm)}&region={quote(region)}&crop={quote(crop)}&visitor={quote(visitor)}&theme={quote(theme)}&idx={idx}"

def generated_from_url():
    if st.query_params.get("mode", "") != "generated": return None
    farm = unquote(st.query_params.get("farm", "창포마을")); region = unquote(st.query_params.get("region", "지역"))
    crop = unquote(st.query_params.get("crop", "딸기")); visitor = unquote(st.query_params.get("visitor", "일반 성인")); theme = unquote(st.query_params.get("theme", "힐링형"))
    idx = int(st.query_params.get("idx", "0")); crop = crop if crop in CROPS else "딸기"; theme = theme if theme in THEMES else "힐링형"
    ms = gen_missions(farm, region, crop, visitor, theme, 5); idx = max(0, min(idx, len(ms)-1))
    return {"farm":farm,"region":region,"crop":crop,"visitor":visitor,"theme":theme,"idx":idx,"mission":ms[idx]}

def save_mission(mission, crop, visitor, theme, source, choice, memo):
    append_csv(MISSION_FILE, {"timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"visitor_name":st.session_state.visitor_name or "익명","visitor_type":visitor,"theme":theme,"crop":crop,"mission_title":mission["title"],"place":mission["place"],"choice":choice,"memo":memo,"earned_points":10,"source":source})

def score(temp, rain, wind, pm, visitor):
    s=100; reasons=[]
    if temp < 5 or temp > 32: s-=25; reasons.append("기온 부담이 있어 실내·단축형 코스를 권장합니다.")
    elif temp < 10 or temp > 28: s-=12; reasons.append("기온을 고려해 휴식 구간을 배치하는 것이 좋습니다.")
    else: reasons.append("기온이 야외 활동에 비교적 적합합니다.")
    if rain >= 10: s-=30; reasons.append("강수량이 많아 실내형 체험이 적합합니다.")
    elif rain > 0: s-=12; reasons.append("비가 예상되어 미끄럼 주의 안내가 필요합니다.")
    if wind >= 8: s-=15; reasons.append("강풍에 대비해 안내판과 포토존을 점검해야 합니다.")
    if pm == "나쁨": s-=20; reasons.append("미세먼지가 나빠 실외 체류 시간을 줄이는 것이 좋습니다.")
    if pm == "매우나쁨": s-=35; reasons.append("미세먼지가 매우 나빠 실내형 체험을 권장합니다.")
    if visitor in ["고령층","가족/아동","요양원/복지기관"]: s-=5; reasons.append("방문자 특성을 고려해 동선을 짧게 설계합니다.")
    return max(0,min(100,s)), reasons


def guess_base_url():
    """Streamlit Cloud에서는 브라우저 host를 읽어 배포 주소를 추정합니다. 실패하면 빈 문자열을 반환합니다."""
    try:
        host = st.context.headers.get("host", "")
        if not host:
            return ""
        scheme = "https" if "streamlit.app" in host else "http"
        return f"{scheme}://{host}"
    except Exception:
        return ""

def base_url_widget(key, label="앱 기본 주소"):
    default_url = st.session_state.get("app_base_url", "") or guess_base_url()
    url = st.text_input(
        label,
        value=default_url,
        placeholder="예: https://changpo-qr-mission-bb.streamlit.app",
        key=key,
        help="스마트폰으로 찍히는 QR을 만들려면 localhost가 아니라 Streamlit 배포 주소를 넣어야 합니다."
    ).strip().rstrip("/")
    if url:
        st.session_state.app_base_url = url
    if "localhost" in url:
        st.warning("현재 주소가 localhost입니다. 이 QR은 내 컴퓨터에서만 작동합니다. 스마트폰 시연용은 Streamlit 배포 주소로 바꿔주세요.")
    elif url.startswith("https://"):
        st.success("스마트폰 접속용 배포 주소가 적용되었습니다.")
    else:
        st.info("배포 주소를 입력하면 해당 주소를 기준으로 QR이 생성됩니다.")
    return url

def visitor_points(visitor_name):
    mdf = read_csv(MISSION_FILE)
    qdf = read_csv(QUIZ_FILE)
    name = visitor_name or "익명"

    mission_points = 0
    quiz_points = 0
    mission_count = 0
    quiz_count = 0

    if not mdf.empty and "visitor_name" in mdf.columns:
        user_mdf = mdf[mdf["visitor_name"].fillna("익명") == name]
        mission_count = len(user_mdf)
        if "earned_points" in user_mdf.columns:
            mission_points = int(user_mdf["earned_points"].sum())

    if not qdf.empty and "visitor_name" in qdf.columns:
        user_qdf = qdf[qdf["visitor_name"].fillna("익명") == name]
        quiz_count = len(user_qdf)
        if "earned_points" in user_qdf.columns:
            quiz_points = int(user_qdf["earned_points"].sum())

    # 현재 세션에서 완료했지만 아직 CSV 기준으로 잡히지 않는 경우를 보완
    mission_points = max(mission_points, len(st.session_state.get("completed", [])) * 10)
    mission_count = max(mission_count, len(st.session_state.get("completed", [])))

    return mission_count, quiz_count, mission_points + quiz_points

init()
gq = generated_from_url()
st.title("🌿 팜어드벤처: 창포마을 QR 미션")
st.caption("농장 배치표·출력물 기능이 추가된 v8")

with st.sidebar:
    menu = st.radio("메뉴", ["홈","팜어드벤처 소개","농장주 미션 생성기","농장 배치표·출력물","공공데이터 추천","작목 퀴즈 생성","QR 미션 체험","QR 코드 만들기","수료증·포인트","관리자 데이터","초기화"])
if gq: menu = "QR 미션 체험"

st.subheader("방문자 기본 정보")
col1,col2,col3 = st.columns(3)
with col1: st.session_state.visitor_name = st.text_input("이름/팀명", st.session_state.visitor_name)
with col2: st.session_state.visitor_type = st.selectbox("방문자 유형", VISITORS, index=VISITORS.index(st.session_state.visitor_type))
with col3: st.session_state.crop = st.selectbox("체험 작목", list(CROPS), index=list(CROPS).index(st.session_state.crop))
st.session_state.theme = st.selectbox("체험 테마", list(THEMES), index=list(THEMES).index(st.session_state.theme))

if menu == "홈":
    st.header("서비스 개요")
    st.write("팜어드벤처는 농장주가 작목·지역·방문객 유형·테마를 입력하면 작목 특징을 반영한 QR 미션 세트를 자동 생성하는 치유농장 체험 MVP입니다.")
    st.success("v8 핵심: 농장주 미션 생성기, QR 다운로드, 현장 배치표, 출력용 안내문, 수료증·포인트 관리")

elif menu == "팜어드벤처 소개":
    st.header("팜어드벤처 소개")
    st.write("작목 정보, 공공데이터, QR 미션을 결합해 농장을 방문객 맞춤형 농장뮤지엄으로 바꾸는 체험 플랫폼입니다.")
    st.write("농장주는 작목과 테마만 입력하고, 방문객은 QR을 따라 이동하며 관찰·퀴즈·회고 미션을 수행합니다.")
    st.info("향후 실제 공공데이터 API, RAG 기반 안전한 AI 미션 생성, 수료증·포인트 마켓으로 확장할 수 있습니다.")

elif menu == "농장주 미션 생성기":
    st.header("농장주 원클릭 미션 생성기")
    farm = st.text_input("농장명", "창포마을 치유농장")
    region = st.text_input("지역", "창포마을")
    crop = st.selectbox("대표 작목", list(CROPS), index=list(CROPS).index(st.session_state.crop), key="gen_crop")
    visitor = st.selectbox("주 방문객 유형", VISITORS, key="gen_visitor")
    theme = st.selectbox("미션 테마", list(THEMES), key="gen_theme")
    count = st.slider("생성할 미션 수", 3, 5, 5)
    base = base_url_widget("generator_base_url")
    if st.button("미션 세트 생성하기"):
        st.session_state.generated = gen_missions(farm, region, crop, visitor, theme, count)
        append_csv(GEN_FILE, {"timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"farm":farm,"region":region,"crop":crop,"visitor_type":visitor,"theme":theme,"mission_count":count})
        st.success("미션 세트가 생성되었습니다.")
    if st.session_state.generated:
        st.info(CROPS[crop]["summary"])
        zbuf = io.BytesIO()
        with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as z:
            for i,m in enumerate(st.session_state.generated):
                url = gen_url(base, farm, region, crop, visitor, theme, i)
                st.markdown(f"### {m['title']}")
                st.write(f"**장소:** {m['place']}")
                st.write(f"**미션:** {m['task']}")
                st.code(url)
                q = qr_png(url)
                if q:
                    st.image(q, width=160)
                    z.writestr(f"generated_mission_{i+1}.png", q.getvalue())
                    st.download_button(f"{i+1}번 QR 다운로드", q.getvalue(), f"generated_mission_{i+1}.png", "image/png")
        zbuf.seek(0)
        st.download_button("생성 미션 QR 전체 ZIP 다운로드", zbuf.getvalue(), "generated_mission_qr_set.zip", "application/zip")
        st.download_button("생성 미션 목록 CSV 다운로드", pd.DataFrame(st.session_state.generated).to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), "generated_mission_list.csv", "text/csv")


elif menu == "농장 배치표·출력물":
    st.header("농장 배치표·출력물")
    st.write(
        "농장주가 생성한 QR 미션을 실제 현장에 붙일 수 있도록 "
        "배치표, 출력용 안내문, 운영 체크리스트를 자동으로 정리하는 화면입니다."
    )

    farm_name = st.text_input("출력물용 농장명", value="창포마을 치유농장", key="print_farm_name")
    region = st.text_input("출력물용 지역/구역명", value="창포마을", key="print_region")
    crop = st.selectbox("출력물용 작목", list(CROPS.keys()), index=list(CROPS.keys()).index(st.session_state.crop), key="print_crop")
    visitor_type = st.selectbox(
        "출력물용 방문객 유형",
        ["일반 성인", "가족/아동", "고령층", "요양원/복지기관", "학생 단체", "연인/친구"],
        key="print_visitor_type"
    )
    theme = st.selectbox(
        "출력물용 테마",
        ["힐링형", "추리형", "교육형", "가족형", "고령층 배려형"],
        index=["힐링형", "추리형", "교육형", "가족형", "고령층 배려형"].index(st.session_state.theme),
        key="print_theme"
    )
    base = base_url_widget("print_base_url", "출력물용 앱 기본 주소")

    if st.session_state.get("generated"):
        mission_set = st.session_state.generated
        st.info("현재 세션에서 생성된 미션 세트를 우선 사용합니다. 새 조건으로 다시 보고 싶으면 농장주 미션 생성기에서 다시 생성하세요.")
    else:
        mission_set = generate_mission_set(farm_name, region, crop, visitor_type, theme, 5)
        st.info("아직 생성된 미션 세트가 없어, 현재 입력값 기준으로 예시 미션 세트를 자동 구성했습니다.")

    st.subheader("현장 배치표")
    placement_rows = []
    for idx, mission in enumerate(mission_set, start=1):
        url = generated_mission_url(base, farm_name, region, crop, visitor_type, theme, idx - 1)
        placement_rows.append({
            "순서": idx,
            "QR 제목": mission["title"],
            "권장 배치 장소": mission["place"],
            "현장 운영 포인트": mission["task"][:55] + ("..." if len(mission["task"]) > 55 else ""),
            "QR 주소": url
        })

    placement_df = pd.DataFrame(placement_rows)
    st.dataframe(placement_df, use_container_width=True)
    st.download_button(
        "농장 배치표 CSV 다운로드",
        placement_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        "farm_adventure_placement_plan.csv",
        "text/csv"
    )

    st.subheader("출력용 안내문")
    guide_text = f"""🌿 {farm_name} 팜어드벤처 QR 미션 안내

오늘의 작목: {crop}
체험 테마: {theme}
추천 방문객 유형: {visitor_type}

참여 방법
1. 농장 곳곳에 있는 QR 코드를 스마트폰 카메라로 스캔합니다.
2. 화면에 나오는 미션을 읽고 작물을 관찰합니다.
3. 선택지와 짧은 기록을 입력한 뒤 미션 완료 버튼을 누릅니다.
4. 미션과 퀴즈를 완료하면 포인트가 적립됩니다.
5. 마지막에는 수료증과 농산물 할인 쿠폰을 확인할 수 있습니다.

주의사항
- 농장 운영자의 안내에 따라 이동해 주세요.
- 작물은 함부로 꺾거나 훼손하지 않습니다.
- 비나 미세먼지가 있는 날에는 실내형·단축형 코스로 운영될 수 있습니다.
- 고령층, 아동, 단체 방문객은 이동 중 안전에 유의해 주세요.

이 서비스는 작목 정보와 공공데이터를 활용해 농장 체험을 더 쉽고 재미있게 만드는 QR 미션형 체험 서비스입니다.
"""
    st.text_area("A4 안내문 초안", guide_text, height=360)
    st.download_button(
        "출력용 안내문 TXT 다운로드",
        guide_text.encode("utf-8-sig"),
        "farm_adventure_print_guide.txt",
        "text/plain"
    )

    st.subheader("QR 라벨 문구")
    label_lines = []
    for idx, mission in enumerate(mission_set, start=1):
        label_lines.append(f"[{idx}번 QR] {mission['title']}\n장소: {mission['place']}\n안내: QR을 스캔하고 미션을 완료해 주세요.\n")
    label_text = "\n".join(label_lines)
    st.text_area("QR 옆에 붙일 짧은 라벨", label_text, height=260)
    st.download_button(
        "QR 라벨 문구 TXT 다운로드",
        label_text.encode("utf-8-sig"),
        "farm_adventure_qr_labels.txt",
        "text/plain"
    )

    st.subheader("운영 체크리스트")
    checklist = [
        {"구분": "QR 준비", "체크 내용": "생성된 QR을 출력하고 각 구역에 부착했는가?"},
        {"구분": "동선 점검", "체크 내용": "방문자가 QR 순서대로 안전하게 이동할 수 있는가?"},
        {"구분": "작물 보호", "체크 내용": "만지면 안 되는 구역이나 주의 문구가 표시되어 있는가?"},
        {"구분": "공공데이터 확인", "체크 내용": "당일 기온, 강수, 미세먼지 상태를 확인했는가?"},
        {"구분": "방문객 안내", "체크 내용": "미션 수행 방법과 포인트·수료증 안내를 설명했는가?"},
        {"구분": "관리자 확인", "체크 내용": "체험 후 관리자 데이터에 응답이 저장되는지 확인했는가?"},
    ]
    checklist_df = pd.DataFrame(checklist)
    st.table(checklist_df)
    st.download_button(
        "운영 체크리스트 CSV 다운로드",
        checklist_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        "farm_adventure_operation_checklist.csv",
        "text/csv"
    )

    st.subheader("v8 시연 포인트")
    st.success(
        "v8에서는 앱이 QR을 만드는 것에서 끝나지 않고, "
        "농장주가 실제 현장에 QR을 배치하고 안내문을 출력해 운영할 수 있는 형태까지 확장되었습니다."
    )


elif menu == "공공데이터 추천":
    st.header("공공데이터 기반 체험 추천")
    st.caption("현재는 API 없이 수동 입력으로 추천 로직을 시연합니다. 향후 기상청·에어코리아·농업기상 API와 자동 연동 가능합니다.")
    c1,c2 = st.columns(2)
    with c1:
        temp = st.slider("기온(℃)", -10, 40, 22); rain = st.slider("강수량(mm)", 0, 50, 0)
    with c2:
        wind = st.slider("풍속(m/s)", 0, 20, 2); pm = st.selectbox("미세먼지", ["좋음","보통","나쁨","매우나쁨"])
    s, reasons = score(temp, rain, wind, pm, st.session_state.visitor_type)
    st.metric("오늘의 치유체험 적합도", f"{s}점")
    if s >= 80: st.success("표준 야외형 코스를 추천합니다.")
    elif s >= 60: st.warning("혼합형 코스를 추천합니다.")
    else: st.error("실내·단축형 코스를 추천합니다.")
    for r in reasons: st.write("- " + r)
    st.table([
        {"공공데이터":"기상청 단기예보","활용값":"기온·강수·풍속","앱 적용":"체험 코스 추천"},
        {"공공데이터":"에어코리아 대기오염정보","활용값":"미세먼지","앱 적용":"실외 체류 시간 조정"},
        {"공공데이터":"작목 생육 정보","활용값":"작물 특징·환경","앱 적용":"퀴즈·미션 자동 생성"}
    ])

elif menu == "작목 퀴즈 생성":
    st.header("작목별 쉬운 퀴즈 생성")
    crop = st.session_state.crop; c = CROPS[crop]
    st.subheader(crop); st.write(c["summary"])
    for i in c["info"]: st.write("- " + i)
    q = st.selectbox("퀴즈 선택", c["quiz"], format_func=lambda x:x[0])
    choice = st.radio("정답 선택", q[1])
    if st.button("정답 확인 및 기록 저장"):
        ok = choice == q[2]
        append_csv(QUIZ_FILE, {"timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"visitor_name":st.session_state.visitor_name or "익명","visitor_type":st.session_state.visitor_type,"theme":st.session_state.theme,"crop":crop,"question":q[0],"selected":choice,"answer":q[2],"correct":ok,"earned_points":5 if ok else 0})
        st.success("정답입니다! 5P 적립") if ok else st.error(f"아쉽습니다. 정답은 {q[2]}입니다.")

elif menu == "QR 미션 체험":
    st.header("QR 미션 체험")
    if gq:
        m = gq["mission"]
        st.subheader(m["title"]); st.write(f"**농장:** {gq['farm']}"); st.write(f"**작목:** {gq['crop']}"); st.write(f"**테마:** {gq['theme']}")
        st.write(f"**장소:** {m['place']}"); st.write(f"**미션:** {m['task']}")
        choice = st.radio("선택", m["choices"]); memo = st.text_area("기록", placeholder="느낀 점을 적어보세요.")
        if st.button("이 생성 미션 완료하기"):
            save_mission(m, gq["crop"], gq["visitor"], gq["theme"], "농장주 생성 미션", choice, memo)
            st.success("생성 미션 완료! 응답이 저장되었습니다.")
    else:
        qid = st.query_params.get("mission", "")
        idx = [m["id"] for m in STATIC].index(qid) if qid in [m["id"] for m in STATIC] else 0
        m = st.selectbox("미션 선택", STATIC, index=idx, format_func=lambda x:x["title"])
        task = gen_missions("창포마을", "창포마을", st.session_state.crop, st.session_state.visitor_type, st.session_state.theme, 5)[1]["task"] if m["id"] == "observe" else m["task"]
        st.subheader(m["title"]); st.write(f"**장소:** {m['place']}"); st.write(f"**미션:** {task}")
        choice = st.radio("선택", m["choices"]); memo = st.text_area("기록")
        if st.button("이 미션 완료하기"):
            if m["id"] not in st.session_state.completed: st.session_state.completed.append(m["id"])
            save_mission(m, st.session_state.crop, st.session_state.visitor_type, st.session_state.theme, "기본 QR 미션", choice, memo)
            st.success("미션 완료! 응답이 저장되었습니다.")

elif menu == "QR 코드 만들기":
    st.header("기본 QR 코드 만들기")
    base = base_url_widget("basic_qr_base_url")
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as z:
        for m in STATIC:
            url=f"{base}/?mission={m['id']}"; st.subheader(m["title"]); st.code(url)
            q=qr_png(url)
            if q:
                st.image(q, width=160); z.writestr(f"{m['id']}_qr.png", q.getvalue())
    zbuf.seek(0); st.download_button("기본 QR 전체 ZIP 다운로드", zbuf.getvalue(), "basic_qr_set.zip", "application/zip")


elif menu == "수료증·포인트":
    st.header("수료증·포인트")
    display_name = st.session_state.visitor_name or "익명"
    mission_count, quiz_count, total_points = visitor_points(display_name)

    c1, c2, c3 = st.columns(3)
    c1.metric("완료 미션", f"{mission_count}개")
    c2.metric("퀴즈 참여", f"{quiz_count}개")
    c3.metric("보유 포인트", f"{total_points}P")

    st.subheader("창포마을 치유미션 수료증")
    if mission_count >= 5 or total_points >= 50:
        status = "수료"
        coupon = "창포마을 농산물 5% 할인 쿠폰"
        st.success("수료 조건을 달성했습니다. 수료증과 쿠폰을 발급할 수 있습니다.")
    else:
        status = "진행 중"
        coupon = "미션 5개 완료 또는 50P 달성 시 쿠폰 발급"
        st.info("아직 수료 조건 전입니다. 미션과 퀴즈를 더 진행해보세요.")

    certificate = f"""🌿 팜어드벤처 창포마을 치유미션 수료증

이름/팀명: {display_name}
체험 작목: {st.session_state.crop}
체험 테마: {st.session_state.theme}
방문자 유형: {st.session_state.visitor_type}

완료 미션 수: {mission_count}개
퀴즈 참여 수: {quiz_count}개
획득 포인트: {total_points}P
수료 상태: {status}
발급 혜택: {coupon}

위 방문자는 팜어드벤처 QR 미션을 통해 작물 관찰, 생육환경 퀴즈, 치유 회고 활동에 참여하였습니다.

발급 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    st.text_area("수료증 미리보기", certificate, height=320)
    st.download_button(
        "수료증 TXT 다운로드",
        certificate.encode("utf-8-sig"),
        "farm_adventure_certificate.txt",
        "text/plain"
    )

    st.subheader("포인트 마켓 시연")
    st.caption("현재는 실제 결제가 아니라 대회 시연용 리워드 구조입니다.")

    products = [
        {"상품": "창포마을 제철 농산물 꾸러미", "정상가": 20000, "필요 포인트": 50, "할인": 1000},
        {"상품": "못난이 농산물 꾸러미", "정상가": 15000, "필요 포인트": 40, "할인": 1500},
        {"상품": "허브차 체험 키트", "정상가": 12000, "필요 포인트": 30, "할인": 1000},
    ]

    for p in products:
        available = total_points >= p["필요 포인트"]
        final_price = p["정상가"] - p["할인"] if available else p["정상가"]
        with st.container(border=True):
            st.write(f"**{p['상품']}**")
            st.write(f"정상가: {p['정상가']:,}원")
            st.write(f"필요 포인트: {p['필요 포인트']}P")
            if available:
                st.success(f"사용 가능 · 예상 결제가: {final_price:,}원")
            else:
                st.warning(f"포인트 부족 · {p['필요 포인트'] - total_points}P 더 필요")

    st.subheader("v7에서 개선된 QR 주소 처리")
    st.write(
        "이제 QR 생성 화면의 기본 주소가 localhost로 고정되지 않고, "
        "가능하면 현재 접속 중인 Streamlit 배포 주소를 자동으로 불러옵니다. "
        "주소가 다르면 입력칸에서 직접 수정하면 됩니다."
    )


elif menu == "관리자 데이터":
    st.header("관리자 데이터")
    mdf, qdf, gdf = read_csv(MISSION_FILE), read_csv(QUIZ_FILE), read_csv(GEN_FILE)
    total = (mdf["earned_points"].sum() if not mdf.empty and "earned_points" in mdf else 0) + (qdf["earned_points"].sum() if not qdf.empty and "earned_points" in qdf else 0)
    a,b,c = st.columns(3); a.metric("미션 응답", len(mdf)); b.metric("퀴즈 응답", len(qdf)); c.metric("총 포인트", int(total))
    st.subheader("농장주 생성 기록"); st.dataframe(gdf, use_container_width=True) if not gdf.empty else st.info("아직 생성 기록이 없습니다.")
    st.subheader("미션 응답"); st.dataframe(mdf, use_container_width=True) if not mdf.empty else st.info("아직 미션 응답이 없습니다.")
    st.subheader("퀴즈 응답"); st.dataframe(qdf, use_container_width=True) if not qdf.empty else st.info("아직 퀴즈 응답이 없습니다.")

elif menu == "초기화":
    st.header("초기화")
    if st.button("화면 진행률 초기화"):
        st.session_state.completed = []; st.success("초기화되었습니다.")
    for path, label in [(MISSION_FILE,"미션 응답"),(QUIZ_FILE,"퀴즈 응답"),(GEN_FILE,"생성 기록")]:
        if st.button(f"저장된 {label} 삭제"):
            if path.exists(): path.unlink(); st.success(f"{label} 삭제 완료")
            else: st.info("삭제할 데이터가 없습니다.")
