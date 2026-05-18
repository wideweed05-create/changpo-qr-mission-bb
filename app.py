
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote, unquote
from zoneinfo import ZoneInfo
import pandas as pd
import requests

try:
    from streamlit_js_eval import get_geolocation
except Exception:
    get_geolocation = None
import io, zipfile, math, re
try:
    import qrcode
except Exception:
    qrcode = None

st.set_page_config(page_title="팜어드벤처 | 창포마을 QR 미션", page_icon="🌿", layout="centered")

MISSION_FILE = Path("mission_responses.csv")
QUIZ_FILE = Path("quiz_responses.csv")
GEN_FILE = Path("generated_mission_sets.csv")
CROP_DB_FILE = Path("crop_quiz_data.csv")

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


def load_crop_db(default_crops):
    """crop_quiz_data.csv가 있으면 외부 작목 DB를 우선 사용합니다."""
    if not CROP_DB_FILE.exists():
        return default_crops
    try:
        df = pd.read_csv(CROP_DB_FILE, encoding="utf-8-sig").fillna("")
        if df.empty:
            return default_crops

        crops = {}
        for _, row in df.iterrows():
            crop = str(row.get("crop", "")).strip()
            if not crop:
                continue

            quizzes = []
            for idx in [1, 2, 3]:
                q = str(row.get(f"quiz{idx}_question", "")).strip()
                opts = str(row.get(f"quiz{idx}_options", "")).strip()
                ans = str(row.get(f"quiz{idx}_answer", "")).strip()
                if q and opts and ans:
                    quizzes.append((q, [x.strip() for x in opts.split("|") if x.strip()], ans))

            if not quizzes:
                quizzes = default_crops.get(crop, {}).get("quiz", [])

            info = []
            for col in ["info1", "info2", "info3", "info4", "info5"]:
                val = str(row.get(col, "")).strip()
                if val:
                    info.append(val)

            crops[crop] = {
                "summary": str(row.get("summary", "")).strip() or default_crops.get(crop, {}).get("summary", ""),
                "feature": str(row.get("feature", "")).strip() or default_crops.get(crop, {}).get("feature", ""),
                "env": str(row.get("environment", "")).strip() or default_crops.get(crop, {}).get("env", ""),
                "info": info or default_crops.get(crop, {}).get("info", []),
                "quiz": quizzes,
                "source": str(row.get("source", "")).strip(),
                "source_url": str(row.get("source_url", "")).strip(),
                "observation_point": str(row.get("observation_point", "")).strip(),
                "safety_note": str(row.get("safety_note", "")).strip(),
            }

        return crops if crops else default_crops
    except Exception as e:
        st.warning(f"작목 DB 파일을 읽는 중 오류가 발생해 기본 데이터를 사용합니다: {e}")
        return default_crops

CROPS = load_crop_db(CROPS)


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


def dfs_xy_conv(lat, lon):
    """위도·경도를 기상청 단기예보 격자 좌표 nx, ny로 변환합니다."""
    RE = 6371.00877
    GRID = 5.0
    SLAT1 = 30.0
    SLAT2 = 60.0
    OLON = 126.0
    OLAT = 38.0
    XO = 43
    YO = 136
    DEGRAD = math.pi / 180.0

    re_km = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (sf ** sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re_km * sf / (ro ** sn)

    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re_km * sf / (ra ** sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    x = int(ra * math.sin(theta) + XO + 0.5)
    y = int(ro - ra * math.cos(theta) + YO + 0.5)
    return x, y

def ultra_base_time(now=None):
    """기상청 초단기예보 조회에 사용할 base_date, base_time을 계산합니다."""
    if now is None:
        now = datetime.now(ZoneInfo("Asia/Seoul"))
    # 초단기예보는 매시 30분 이후 자료가 안정적으로 조회되므로, 45분 전이면 이전 시각을 사용합니다.
    if now.minute < 45:
        now = now - timedelta(hours=1)
    return now.strftime("%Y%m%d"), now.strftime("%H00"), now.strftime("%Y-%m-%d %H:%M")

def parse_rain(value):
    if value is None:
        return 0.0
    text_value = str(value)
    if "강수없음" in text_value or text_value.strip() in ["0", "0.0"]:
        return 0.0
    if "1mm 미만" in text_value:
        return 0.5
    nums = re.findall(r"\d+(?:\.\d+)?", text_value)
    if not nums:
        return 0.0
    return float(nums[0])

def sky_label(code):
    return {"1": "맑음", "3": "구름많음", "4": "흐림"}.get(str(code), str(code))

def pty_label(code):
    return {
        "0": "없음",
        "1": "비",
        "2": "비/눈",
        "3": "눈",
        "5": "빗방울",
        "6": "빗방울눈날림",
        "7": "눈날림"
    }.get(str(code), str(code))

def fetch_kma_ultra_forecast(service_key, nx, ny):
    """기상청 단기예보 조회서비스의 초단기예보를 호출합니다."""
    if not service_key:
        raise ValueError("기상청 API 인증키를 입력해야 합니다.")

    base_date, base_time, requested_at = ultra_base_time()
    url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"

    keys_to_try = []
    for key in [service_key, unquote(service_key)]:
        if key and key not in keys_to_try:
            keys_to_try.append(key)

    last_error = None

    for key in keys_to_try:
        params = {
            "serviceKey": key,
            "pageNo": 1,
            "numOfRows": 1000,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": int(nx),
            "ny": int(ny),
        }

        try:
            response = requests.get(url, params=params, timeout=12)
            response.raise_for_status()
            data = response.json()
            header = data.get("response", {}).get("header", {})
            result_code = str(header.get("resultCode", ""))
            result_msg = header.get("resultMsg", "")

            if result_code != "00":
                last_error = f"{result_code} / {result_msg}"
                continue

            items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            if isinstance(items, dict):
                items = [items]
            if not items:
                raise ValueError("응답은 성공했지만 예보 데이터가 비어 있습니다.")

            grouped = {}
            for item in items:
                key_time = (item.get("fcstDate", ""), item.get("fcstTime", ""))
                grouped.setdefault(key_time, {})[item.get("category")] = item.get("fcstValue")

            first_time = sorted(grouped.keys())[0]
            values = grouped[first_time]

            temp = float(values.get("T1H", 22))
            rainfall = parse_rain(values.get("RN1", 0))
            wind = float(values.get("WSD", 2))
            sky = sky_label(values.get("SKY", "1"))
            pty = pty_label(values.get("PTY", "0"))

            # 강수형태가 있으면 강수량 값이 작더라도 비/눈이 있다는 판단을 추천 로직에 반영합니다.
            adjusted_rain = max(rainfall, 1.0) if pty != "없음" and rainfall == 0 else rainfall

            return {
                "source": "기상청_단기예보 조회서비스 - 초단기예보조회",
                "base_date": base_date,
                "base_time": base_time,
                "requested_at": requested_at,
                "fcst_date": first_time[0],
                "fcst_time": first_time[1],
                "nx": int(nx),
                "ny": int(ny),
                "temp": temp,
                "rain": adjusted_rain,
                "rain_raw": values.get("RN1", "0"),
                "wind": wind,
                "sky": sky,
                "pty": pty,
                "raw_values": values
            }
        except Exception as e:
            last_error = str(e)

    raise RuntimeError(f"기상청 공공데이터 호출에 실패했습니다. {last_error or ''}")


def air_grade_label(value):
    """에어코리아 등급값을 화면 표시용 문구로 변환합니다."""
    mapping = {
        "1": "좋음",
        "2": "보통",
        "3": "나쁨",
        "4": "매우나쁨",
        "좋음": "좋음",
        "보통": "보통",
        "나쁨": "나쁨",
        "매우나쁨": "매우나쁨",
    }
    if value is None:
        return "보통"
    return mapping.get(str(value).strip(), "보통")

def fetch_airkorea_sido(service_key, sido_name="전북", station_name=""):
    """에어코리아 시도별 실시간 측정정보를 호출하고, 지정 측정소 또는 첫 번째 유효 측정소 데이터를 반환합니다."""
    if not service_key:
        raise ValueError("에어코리아 API 인증키를 입력해야 합니다.")

    url = "https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    keys_to_try = []
    for key in [service_key, unquote(service_key)]:
        if key and key not in keys_to_try:
            keys_to_try.append(key)

    last_error = None

    for key in keys_to_try:
        params = {
            "serviceKey": key,
            "returnType": "json",
            "numOfRows": 100,
            "pageNo": 1,
            "sidoName": sido_name,
            "ver": "1.0",
        }

        try:
            response = requests.get(url, params=params, timeout=12)
            response.raise_for_status()
            data = response.json()
            response_obj = data.get("response", {})
            header = response_obj.get("header", {})
            result_code = str(header.get("resultCode", ""))
            result_msg = header.get("resultMsg", "")

            if result_code not in ["00", "0"]:
                last_error = f"{result_code} / {result_msg}"
                continue

            items = response_obj.get("body", {}).get("items", [])
            if isinstance(items, dict):
                items = [items]
            if not items:
                raise ValueError("대기질 응답은 성공했지만 측정 데이터가 비어 있습니다.")

            selected = None
            available_names = [str(item.get("stationName", "")) for item in items if item.get("stationName")]

            if station_name:
                for item in items:
                    name = str(item.get("stationName", ""))
                    if station_name == name or station_name in name:
                        selected = item
                        break

            if selected is None:
                # PM10 또는 PM2.5 값이 있는 첫 번째 측정소를 사용합니다.
                for item in items:
                    if str(item.get("pm10Value", "")).strip() not in ["", "-", "None"] or str(item.get("pm25Value", "")).strip() not in ["", "-", "None"]:
                        selected = item
                        break

            if selected is None:
                selected = items[0]

            return {
                "source": "한국환경공단_에어코리아_대기오염정보 - 시도별 실시간 측정정보조회",
                "sido": sido_name,
                "station": selected.get("stationName", ""),
                "data_time": selected.get("dataTime", ""),
                "pm10": selected.get("pm10Value", "-"),
                "pm25": selected.get("pm25Value", "-"),
                "o3": selected.get("o3Value", "-"),
                "pm10_grade": air_grade_label(selected.get("pm10Grade")),
                "pm25_grade": air_grade_label(selected.get("pm25Grade")),
                "o3_grade": air_grade_label(selected.get("o3Grade")),
                "khai": selected.get("khaiValue", "-"),
                "khai_grade": air_grade_label(selected.get("khaiGrade")),
                "available_stations": available_names[:30],
                "raw": selected,
            }

        except Exception as e:
            last_error = str(e)

    raise RuntimeError(f"에어코리아 공공데이터 호출에 실패했습니다. {last_error or ''}")

def combined_air_grade(pm10_grade, pm25_grade, o3_grade):
    """PM10, PM2.5, O3 등급 중 가장 나쁜 등급을 추천 로직에 반영합니다."""
    order = {"좋음": 1, "보통": 2, "나쁨": 3, "매우나쁨": 4}
    reverse = {1: "좋음", 2: "보통", 3: "나쁨", 4: "매우나쁨"}
    worst = max(order.get(pm10_grade, 2), order.get(pm25_grade, 2), order.get(o3_grade, 2))
    return reverse[worst]


def parse_geolocation_result(location):
    """streamlit_js_eval의 위치 결과를 위도·경도로 안전하게 변환합니다."""
    if not location:
        return None, None, None

    if isinstance(location, dict) and "error" in location:
        error = location.get("error", {})
        return None, None, f"위치 권한 오류: {error.get('message', error)}"

    try:
        # streamlit_js_eval get_geolocation()은 coords 내부 또는 최상위에 좌표를 줄 수 있어 둘 다 처리합니다.
        coords = location.get("coords", location) if isinstance(location, dict) else {}
        lat = coords.get("latitude")
        lon = coords.get("longitude")
        accuracy = coords.get("accuracy", None)

        if lat is None or lon is None:
            return None, None, "위치 정보를 아직 받지 못했습니다. 권한 허용 후 잠시 기다리거나 다시 눌러주세요."

        return float(lat), float(lon), accuracy
    except Exception as e:
        return None, None, f"위치 결과 해석 중 오류가 발생했습니다: {e}"

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
st.caption("발표 시연 모드가 추가된 v12")

with st.sidebar:
    menu = st.radio("메뉴", ["홈","팜어드벤처 소개","시연 모드","농장주 미션 생성기","농장 배치표·출력물","공공데이터 추천","작목 퀴즈 생성","작목 데이터 관리","QR 미션 체험","QR 코드 만들기","수료증·포인트","관리자 데이터","초기화"])
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
    st.success("v12 핵심: 작동형 MVP를 심사위원에게 보여주기 위한 발표 시연 모드와 시연 대본을 추가했습니다.")

elif menu == "팜어드벤처 소개":
    st.header("팜어드벤처 소개")
    st.write("작목 정보, 공공데이터, QR 미션을 결합해 농장을 방문객 맞춤형 농장뮤지엄으로 바꾸는 체험 플랫폼입니다.")
    st.write("농장주는 작목과 테마만 입력하고, 방문객은 QR을 따라 이동하며 관찰·퀴즈·회고 미션을 수행합니다.")
    st.info("향후 실제 공공데이터 API, RAG 기반 안전한 AI 미션 생성, 수료증·포인트 마켓으로 확장할 수 있습니다.")


elif menu == "시연 모드":
    st.header("발표 시연 모드")
    st.write("심사위원에게 팜어드벤처 MVP를 어떤 순서로 보여줄지 정리한 발표용 화면입니다.")

    st.subheader("시연 핵심 메시지")
    st.success(
        "팜어드벤처는 현재 위치 기반 기상·대기질 공공데이터와 작목별 퀴즈 DB를 활용해 "
        "농장주가 QR 미션을 만들고, 방문객이 미션을 수행하며, 농장주는 응답 데이터를 확인하는 작동형 MVP입니다."
    )

    st.subheader("3분 시연 순서")
    demo_steps = [
        {"순서":"1", "화면":"공공데이터 추천", "설명":"현재 위치 또는 창포마을 좌표로 기상청·에어코리아 데이터를 불러와 체험 적합도를 계산합니다."},
        {"순서":"2", "화면":"농장주 미션 생성기", "설명":"농장주가 작목·방문객 유형·테마를 선택하면 QR 미션 세트가 자동 생성됩니다."},
        {"순서":"3", "화면":"작목 퀴즈 생성", "설명":"작목 DB를 바탕으로 방문객 눈높이에 맞는 쉬운 퀴즈를 제공합니다."},
        {"순서":"4", "화면":"QR 미션 체험", "설명":"방문객이 QR을 찍고 미션을 수행하면 응답과 포인트가 저장됩니다."},
        {"순서":"5", "화면":"수료증·포인트", "설명":"미션 완료 결과를 수료증과 포인트 리워드로 연결합니다."},
        {"순서":"6", "화면":"관리자 데이터", "설명":"농장주는 미션·퀴즈·생성 기록을 확인하고 CSV로 다운로드할 수 있습니다."},
    ]
    st.table(demo_steps)

    st.subheader("발표 대본 초안")
    script = """안녕하세요. 저희가 개발한 서비스는 팜어드벤처입니다.

팜어드벤처는 농장주가 작목, 방문객 유형, 체험 테마를 입력하면 QR 미션을 자동으로 생성하고,
방문객은 스마트폰으로 QR을 찍으며 작물 관찰 미션과 쉬운 퀴즈를 수행하는 치유농장 체험 플랫폼입니다.

첫 번째 핵심은 공공데이터 활용입니다.
앱은 사용자의 현재 위치 또는 창포마을 좌표를 기준으로 기상청 단기예보 API와 에어코리아 대기오염정보 API를 불러옵니다.
이 데이터를 바탕으로 기온, 강수량, 풍속, 미세먼지, 초미세먼지, 오존 상태를 확인하고
당일 체험 적합도와 야외형·혼합형·실내형 코스를 추천합니다.

두 번째 핵심은 작목 기반 미션 생성입니다.
작목별 특징과 생육환경 정보를 crop_quiz_data.csv로 분리해 관리하고,
딸기, 토마토, 상추, 버섯, 허브와 같은 작목 정보를 바탕으로 방문객 눈높이에 맞는 퀴즈와 관찰 미션을 제공합니다.

세 번째 핵심은 농장 운영 지원입니다.
농장주는 생성된 QR 미션을 다운로드하고, 농장 배치표와 출력용 안내문, QR 라벨, 운영 체크리스트를 확인할 수 있습니다.
방문객이 미션을 완료하면 관리자 화면에 기록이 저장되고, 향후 프로그램 개선 자료로 활용할 수 있습니다.

따라서 팜어드벤처는 단순한 QR 체험 앱이 아니라,
공공데이터와 작목 정보를 활용해 농장 체험을 맞춤형으로 운영하고 데이터화하는 작동형 MVP입니다.
"""
    st.text_area("대본", script, height=420)
    st.download_button("발표 대본 TXT 다운로드", script.encode("utf-8-sig"), "farm_adventure_demo_script.txt", "text/plain")

    st.subheader("발표 전 체크리스트")
    checklist = [
        {"체크":"기상청 API 키 준비", "상태":"메모장에 저장"},
        {"체크":"에어코리아 API 키 준비", "상태":"메모장에 저장"},
        {"체크":"Streamlit 앱 정상 접속", "상태":"배포 주소 새로고침"},
        {"체크":"공공데이터 추천 정상 작동", "상태":"현재 위치 또는 기본 좌표로 테스트"},
        {"체크":"농장주 미션 생성기 테스트", "상태":"딸기·교육형·가족/아동으로 생성"},
        {"체크":"QR 미션 완료 기록 저장", "상태":"미션 하나 완료 후 관리자 데이터 확인"},
        {"체크":"수료증·포인트 확인", "상태":"포인트와 수료증 화면 확인"},
        {"체크":"작목 DB 출처 보강", "상태":"농사로·농촌진흥청 등 공식자료 출처 입력 예정"},
    ]
    st.table(checklist)
    checklist_df = pd.DataFrame(checklist)
    st.download_button(
        "발표 체크리스트 CSV 다운로드",
        checklist_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        "farm_adventure_demo_checklist.csv",
        "text/csv"
    )

    st.subheader("심사위원 질문 대비")
    st.markdown("""
**Q1. 공공데이터는 실제로 쓰이나요?**  
A. 네. 기상청 단기예보 API와 에어코리아 대기오염정보 API를 호출해 날씨와 대기질 값을 추천 로직에 반영합니다.

**Q2. API가 발표 중 실패하면 어떻게 하나요?**  
A. 수동 입력 백업 기능을 넣어두었습니다. API 실패 시에도 같은 추천 로직을 확인할 수 있습니다.

**Q3. 작목별 퀴즈는 AI가 임의로 만든 건가요?**  
A. 현재는 작동형 MVP를 위해 CSV 기반 작목 DB로 관리하며, 향후 농사로·농촌진흥청 공식자료를 보강해 RAG 방식으로 확장할 수 있습니다.

**Q4. 농장주는 실제로 어떻게 쓰나요?**  
A. 농장주는 작목·방문객 유형·테마를 입력해 QR 미션 세트를 만들고, 출력용 안내문과 배치표를 활용해 현장에 바로 적용할 수 있습니다.
""")

    st.subheader("다음 고도화 방향")
    st.write("1. 작목 DB의 공식 출처 URL 보강")
    st.write("2. 시연용 PPT와 제안서 구조도 제작")
    st.write("3. 관리자 대시보드 시각화 강화")
    st.write("4. RAG 기반 안전한 미션 생성 구조 설계")


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
        mission_set = gen_missions(farm_name, region, crop, visitor_type, theme, 5)
        st.info("아직 생성된 미션 세트가 없어, 현재 입력값 기준으로 예시 미션 세트를 자동 구성했습니다.")

    st.subheader("현장 배치표")
    placement_rows = []
    for idx, mission in enumerate(mission_set, start=1):
        url = gen_url(base, farm_name, region, crop, visitor_type, theme, idx - 1)
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
        "v8.2에서는 앱이 QR을 만드는 것에서 끝나지 않고, "
        "농장주가 실제 현장에 QR을 배치하고 안내문을 출력해 운영할 수 있는 형태까지 확장되었습니다."
    )


elif menu == "공공데이터 추천":
    st.header("현재 위치 기반 공공데이터 추천")
    st.write(
        "v10에서는 사용자가 위치 권한을 허용하면 현재 위도·경도를 자동으로 인식하고, "
        "그 위치를 기상청 격자 좌표로 변환하여 날씨 공공데이터를 불러옵니다. "
        "대기질은 에어코리아 API를 함께 활용해 체험 코스 추천에 반영합니다."
    )

    st.info(
        "위치 정보는 브라우저가 사용자에게 권한을 물어본 뒤 허용한 경우에만 사용할 수 있습니다. "
        "위치 권한이 거부되거나 실패하면 기존처럼 창포마을 기본 좌표 또는 수동 입력값으로 계속 진행할 수 있습니다."
    )

    st.subheader("1. 위치 인식")
    use_geolocation = st.checkbox("📍 현재 위치 사용하기", value=False)

    default_lat = st.session_state.get("geo_lat", 35.9869726448865)
    default_lon = st.session_state.get("geo_lon", 127.259542032894)

    if use_geolocation:
        if get_geolocation is None:
            st.error("위치 인식 컴포넌트가 설치되지 않았습니다. requirements.txt에 streamlit-js-eval이 필요합니다.")
        else:
            st.caption("브라우저에서 위치 권한을 요청하면 허용을 눌러주세요.")
            location = get_geolocation()
            lat_result, lon_result, geo_info = parse_geolocation_result(location)

            if lat_result is not None and lon_result is not None:
                st.session_state["geo_lat"] = lat_result
                st.session_state["geo_lon"] = lon_result
                default_lat = lat_result
                default_lon = lon_result
                if geo_info is not None:
                    st.success(f"현재 위치를 인식했습니다. 정확도 약 {geo_info}m")
                else:
                    st.success("현재 위치를 인식했습니다.")
            elif geo_info:
                st.warning(geo_info)

    st.subheader("2. 위치 좌표 확인")
    st.caption("기본값은 전북특별자치도 완주군 고산면 대아저수로 392 기준입니다. 현재 위치 인식에 성공하면 해당 값으로 바뀝니다.")

    loc1, loc2 = st.columns(2)
    with loc1:
        lat = st.number_input("위도", value=float(default_lat), format="%.13f")
    with loc2:
        lon = st.number_input("경도", value=float(default_lon), format="%.13f")

    calc_nx, calc_ny = dfs_xy_conv(lat, lon)
    st.write(f"기상청 격자 좌표 자동 변환 결과: **nx {calc_nx}, ny {calc_ny}**")

    c1, c2 = st.columns(2)
    with c1:
        nx = st.number_input("기상청 nx", value=int(calc_nx), step=1)
    with c2:
        ny = st.number_input("기상청 ny", value=int(calc_ny), step=1)

    st.subheader("3. API 인증키 입력")
    k1, k2 = st.columns(2)
    with k1:
        kma_key = st.text_input(
            "기상청 단기예보 API 일반 인증키",
            type="password",
            placeholder="기상청 API 키"
        )
    with k2:
        air_key = st.text_input(
            "에어코리아 대기오염정보 API 일반 인증키",
            type="password",
            placeholder="에어코리아 API 키"
        )

    st.caption("인증키는 코드나 GitHub에 저장하지 않고, 테스트할 때 화면에 직접 입력하는 방식입니다.")

    st.subheader("4. 에어코리아 조회 조건")
    air1, air2 = st.columns(2)
    with air1:
        sido_name = st.selectbox(
            "시도명",
            ["전북", "전남", "광주", "충남", "충북", "경남", "경북", "서울", "경기", "인천", "대전", "대구", "부산", "울산", "강원", "제주", "세종"],
            index=0
        )
    with air2:
        station_name = st.text_input(
            "측정소명 선택 입력",
            value="",
            placeholder="비워두면 해당 시도 내 유효 측정소 자동 선택"
        )

    st.caption("정확한 측정소명을 모를 경우 비워두면 됩니다. 앱이 해당 시도 내 유효 측정소 하나를 자동 선택합니다.")

    if st.button("현재 위치 기반 공공데이터 불러오기"):
        weather_error = None
        air_error = None

        try:
            with st.spinner("기상청 공공데이터를 불러오는 중입니다..."):
                weather = fetch_kma_ultra_forecast(kma_key, nx, ny)
            st.session_state["latest_weather"] = weather
            st.success("기상청 공공데이터를 성공적으로 불러왔습니다.")
        except Exception as e:
            weather_error = str(e)
            st.error(f"기상청 호출 실패: {weather_error}")

        try:
            with st.spinner("에어코리아 공공데이터를 불러오는 중입니다..."):
                air = fetch_airkorea_sido(air_key, sido_name=sido_name, station_name=station_name)
            st.session_state["latest_air"] = air
            st.success("에어코리아 공공데이터를 성공적으로 불러왔습니다.")
        except Exception as e:
            air_error = str(e)
            st.error(f"에어코리아 호출 실패: {air_error}")

        if weather_error or air_error:
            st.warning("API 일부가 실패해도 아래 수동 입력 백업으로 추천 로직을 계속 확인할 수 있습니다.")

    weather = st.session_state.get("latest_weather")
    air = st.session_state.get("latest_air")

    st.divider()

    if weather:
        st.subheader("기상청 공공데이터 조회 결과")
        wc1, wc2, wc3, wc4 = st.columns(4)
        wc1.metric("기온", f"{weather['temp']}℃")
        wc2.metric("강수량", f"{weather['rain']}mm")
        wc3.metric("풍속", f"{weather['wind']}m/s")
        wc4.metric("하늘상태", weather["sky"])

        st.write(f"강수형태: **{weather['pty']}**")
        st.write(f"데이터 출처: **{weather['source']}**")
        st.write(f"API 기준 시각: **{weather['base_date']} {weather['base_time']}**")
        st.write(f"예보 적용 시각: **{weather['fcst_date']} {weather['fcst_time']}**")
        st.write(f"좌표: **위도 {lat}, 경도 {lon} / nx {weather['nx']}, ny {weather['ny']}**")

        temp = weather["temp"]
        rain = weather["rain"]
        wind = weather["wind"]
    else:
        st.subheader("기상 데이터 수동 입력 백업")
        bc1, bc2 = st.columns(2)
        with bc1:
            temp = st.slider("기온(℃)", -10, 40, 22)
            rain = st.slider("강수량(mm)", 0, 50, 0)
        with bc2:
            wind = st.slider("풍속(m/s)", 0, 20, 2)

    if air:
        st.subheader("에어코리아 대기질 조회 결과")
        ac1, ac2, ac3, ac4 = st.columns(4)
        ac1.metric("PM10", f"{air['pm10']}㎍/㎥")
        ac2.metric("PM2.5", f"{air['pm25']}㎍/㎥")
        ac3.metric("오존", f"{air['o3']}ppm")
        ac4.metric("통합대기", air["khai_grade"])

        st.write(f"측정소: **{air['station']}**")
        st.write(f"측정 시각: **{air['data_time']}**")
        st.write(f"PM10 등급: **{air['pm10_grade']}** / PM2.5 등급: **{air['pm25_grade']}** / O3 등급: **{air['o3_grade']}**")
        st.write(f"데이터 출처: **{air['source']}**")

        if air.get("available_stations"):
            with st.expander("조회 가능한 측정소 일부 보기"):
                st.write(", ".join(air["available_stations"]))

        pm = combined_air_grade(air["pm10_grade"], air["pm25_grade"], air["o3_grade"])
        st.info(f"추천 로직 반영 대기질 등급: **{pm}**")
    else:
        st.subheader("대기질 수동 입력 백업")
        pm = st.selectbox("미세먼지 상태", ["좋음", "보통", "나쁨", "매우나쁨"], index=1)

    st.divider()
    s, reasons = score(temp, rain, wind, pm, st.session_state.visitor_type)

    st.subheader("위치·날씨·대기질 기반 추천 결과")
    st.metric("오늘의 치유체험 적합도", f"{s}점")

    if s >= 80:
        st.success("추천 코스: 표준 야외형 코스")
        recommended = ["입구 환영 미션", "작물 관찰 미션", "생육환경 퀴즈", "느린 걷기 미션", "마무리 수료 미션"]
    elif s >= 60:
        st.warning("추천 코스: 혼합형 코스")
        recommended = ["입구 환영 미션", "작물 관찰 미션", "향기/감각 미션", "마무리 수료 미션"]
    else:
        st.error("추천 코스: 실내·단축형 코스")
        recommended = ["입구 환영 미션", "향기 기억 미션", "작목 퀴즈 미션", "마무리 수료 미션"]

    st.write("추천 미션 구성")
    for i, item in enumerate(recommended, start=1):
        st.write(f"{i}. {item}")

    st.write("추천 근거")
    for r in reasons:
        st.write("- " + r)

    st.subheader("공공데이터 자동화 구조")
    st.table([
        {"단계": "위치 인식", "활용 정보": "브라우저 위치 권한 기반 위도·경도", "앱 적용": "현재 위치 또는 창포마을 기본 위치 기준 설정"},
        {"단계": "좌표 변환", "활용 정보": "기상청 격자 좌표 nx, ny", "앱 적용": "위도·경도를 단기예보 API 좌표로 변환"},
        {"단계": "기상청 API", "활용 정보": "기온·강수량·풍속·하늘상태", "앱 적용": "체험 적합도 및 코스 추천"},
        {"단계": "에어코리아 API", "활용 정보": "PM10·PM2.5·O3·통합대기환경지수", "앱 적용": "야외/실내 체험 비중 조정"},
        {"단계": "작목 정보", "활용 정보": "작물 특징·생육환경·관찰 포인트", "앱 적용": "퀴즈·미션 자동 생성"}
    ])


elif menu == "작목 퀴즈 생성":
    st.header("작목별 쉬운 퀴즈 생성")
    crop = st.session_state.crop
    c = CROPS[crop]

    st.subheader(crop)
    st.write(c["summary"])

    source = c.get("source", "")
    source_url = c.get("source_url", "")
    if source:
        st.caption(f"작목 정보 출처: {source}")
    if source_url:
        st.caption(f"출처 URL/메모: {source_url}")

    st.write("작목 기본 정보")
    for i in c["info"]:
        st.write("- " + i)

    if c.get("observation_point"):
        st.info(f"방문객 관찰 포인트: {c.get('observation_point')}")
    if c.get("safety_note"):
        st.warning(f"안전 주의: {c.get('safety_note')}")

    st.divider()
    st.subheader("퀴즈 풀기")
    q = st.selectbox("퀴즈 선택", c["quiz"], format_func=lambda x:x[0])
    choice = st.radio("정답 선택", q[1])

    if st.button("정답 확인 및 기록 저장"):
        ok = choice == q[2]
        append_csv(QUIZ_FILE, {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "visitor_name": st.session_state.visitor_name or "익명",
            "visitor_type": st.session_state.visitor_type,
            "theme": st.session_state.theme,
            "crop": crop,
            "question": q[0],
            "selected": choice,
            "answer": q[2],
            "correct": ok,
            "earned_points": 5 if ok else 0
        })
        st.success("정답입니다! 5P 적립") if ok else st.error(f"아쉽습니다. 정답은 {q[2]}입니다.")


elif menu == "작목 데이터 관리":
    st.header("작목 데이터 관리")
    st.write(
        "v11에서는 작목 정보를 app.py 안에만 넣지 않고, crop_quiz_data.csv 파일로 분리했습니다. "
        "팀원이 공식자료를 정리해 CSV에 추가하면 앱의 작목 퀴즈와 미션 생성에 바로 반영할 수 있습니다."
    )

    if CROP_DB_FILE.exists():
        df_crop = pd.read_csv(CROP_DB_FILE, encoding="utf-8-sig").fillna("")
        st.success("crop_quiz_data.csv 파일을 불러왔습니다.")
    else:
        df_crop = pd.DataFrame([
            {
                "crop": crop,
                "summary": data.get("summary", ""),
                "feature": data.get("feature", ""),
                "environment": data.get("env", ""),
                "info1": data.get("info", [""])[0] if len(data.get("info", [])) > 0 else "",
                "info2": data.get("info", ["",""])[1] if len(data.get("info", [])) > 1 else "",
                "info3": data.get("info", ["","",""])[2] if len(data.get("info", [])) > 2 else "",
                "observation_point": data.get("feature", ""),
                "safety_note": "작물을 함부로 꺾거나 훼손하지 않기",
                "quiz1_question": data.get("quiz", [("", [], "")])[0][0] if len(data.get("quiz", [])) > 0 else "",
                "quiz1_options": "|".join(data.get("quiz", [("", [], "")])[0][1]) if len(data.get("quiz", [])) > 0 else "",
                "quiz1_answer": data.get("quiz", [("", [], "")])[0][2] if len(data.get("quiz", [])) > 0 else "",
                "quiz2_question": data.get("quiz", [("", [], "")])[1][0] if len(data.get("quiz", [])) > 1 else "",
                "quiz2_options": "|".join(data.get("quiz", [("", [], "")])[1][1]) if len(data.get("quiz", [])) > 1 else "",
                "quiz2_answer": data.get("quiz", [("", [], "")])[1][2] if len(data.get("quiz", [])) > 1 else "",
                "quiz3_question": "",
                "quiz3_options": "",
                "quiz3_answer": "",
                "source": data.get("source", "공식자료 확인 필요"),
                "source_url": data.get("source_url", "")
            }
            for crop, data in CROPS.items()
        ])
        st.info("외부 CSV가 없어서 현재 앱 기본 작목 데이터를 표로 보여줍니다.")

    st.dataframe(df_crop, use_container_width=True)

    st.download_button(
        "작목 DB CSV 다운로드",
        df_crop.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        "crop_quiz_data.csv",
        "text/csv"
    )

    st.subheader("팀원 자료 정리 양식")
    st.write("새 작목을 추가하거나 공식 출처를 보강할 때는 아래 형식으로 정리하면 됩니다.")
    st.code(
        "crop, summary, feature, environment, info1, info2, info3, observation_point, safety_note, "
        "quiz1_question, quiz1_options, quiz1_answer, source, source_url",
        language="text"
    )

    st.warning(
        "출처가 불명확한 작목 정보는 발표에서 약점이 될 수 있습니다. "
        "농사로, 농촌진흥청, 지자체 농업기술센터 등 공식자료 기반으로 source 칸을 채워주세요."
    )


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
