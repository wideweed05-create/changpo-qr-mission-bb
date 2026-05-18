
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

def get_secret_value(key_name):
    try:
        return st.secrets.get(key_name, "")
    except Exception:
        return ""

def api_key_input(label, secret_name, placeholder):
    secret_value = get_secret_value(secret_name)
    if secret_value:
        st.success(f"{label}가 보안 설정에 저장되어 있습니다.")
        return secret_value
    return st.text_input(label, type="password", placeholder=placeholder)

gq = generated_from_url()

st.title("🌿 팜어드벤처")
st.caption("공공데이터 기반 QR 농장 체험 웹앱 · v14 서비스형 구조")

with st.sidebar:
    st.header("팜어드벤처")
    menu = st.radio("메뉴", ["홈", "방문객 모드", "농장주 모드", "관리자 모드", "설정"])

    st.divider()
    st.subheader("기본 정보")
    st.session_state.visitor_name = st.text_input("이름/팀명", st.session_state.visitor_name or "", placeholder="예: 1조 / 방문객")
    st.session_state.visitor_type = st.selectbox("방문자 유형", VISITORS, index=VISITORS.index(st.session_state.visitor_type))
    st.session_state.crop = st.selectbox("체험 작목", list(CROPS), index=list(CROPS).index(st.session_state.crop))
    st.session_state.theme = st.selectbox("체험 테마", list(THEMES), index=list(THEMES).index(st.session_state.theme))

if gq:
    menu = "방문객 모드"

if menu == "홈":
    st.header("농장 체험을 QR 미션으로 바꾸다")
    st.write(
        "팜어드벤처는 농장주가 작목과 테마를 선택하면 QR 미션을 만들고, "
        "방문객은 스마트폰으로 미션과 작목 퀴즈를 수행하며 포인트와 수료증을 받는 체험형 웹앱입니다."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("방문객")
        st.write("QR을 찍고 작물 관찰 미션과 퀴즈를 수행합니다.")
    with c2:
        st.subheader("농장주")
        st.write("작목·방문객 유형·테마를 입력해 QR 미션 세트를 생성합니다.")
    with c3:
        st.subheader("관리자")
        st.write("미션 완료 기록, 퀴즈 응답, 포인트 데이터를 확인합니다.")

    st.divider()
    st.subheader("주요 기능")
    st.write("1. 현재 위치 기반 기상청·에어코리아 공공데이터 조회")
    st.write("2. 작목별 쉬운 퀴즈와 관찰 미션 제공")
    st.write("3. 농장주용 QR 미션 자동 생성")
    st.write("4. 방문자 포인트·수료증 발급")
    st.write("5. 관리자 데이터 확인 및 CSV 다운로드")
    st.write("6. API 키 보안 저장 시 자동 공공데이터 조회")
    st.info("왼쪽 메뉴를 방문객·농장주·관리자 중심으로 정리했습니다.")

elif menu == "방문객 모드":
    st.header("방문객 모드")
    tab_mission, tab_quiz, tab_points = st.tabs(["오늘의 미션", "작목 퀴즈", "내 포인트·수료증"])

    with tab_mission:
        if gq:
            mission = gq["mission"]
            crop = gq["crop"]
            visitor = gq["visitor"]
            theme = gq["theme"]

            st.subheader(mission["title"])
            st.write(f"**농장:** {gq['farm']}")
            st.write(f"**작목:** {crop}")
            st.write(f"**방문객 유형:** {visitor}")
            st.write(f"**테마:** {theme}")
            st.write(f"**장소:** {mission['place']}")
            st.write(f"**미션:** {mission['task']}")

            choice = st.radio("가장 가까운 답을 선택하세요.", mission["choices"], key="visitor_generated_choice")
            memo = st.text_area("짧은 기록을 남겨보세요.", placeholder="예: 딸기 잎 모양이 생각보다 신기했다.", key="visitor_generated_memo")

            if st.button("미션 완료하기", key="visitor_generated_done"):
                save_mission(mission, crop, visitor, theme, "농장주 생성 미션", choice, memo)
                st.success("미션이 완료되었습니다. 10P가 적립되었습니다.")
        else:
            st.write("QR을 찍고 들어오면 해당 미션이 바로 열립니다. 아래에서는 기본 미션을 테스트할 수 있습니다.")

            selected = st.selectbox("기본 미션 선택", [m["title"] for m in STATIC])
            mission = next(m for m in STATIC if m["title"] == selected)

            st.subheader(mission["title"])
            st.write(f"**장소:** {mission['place']}")

            if mission["id"] == "observe":
                c = CROPS[st.session_state.crop]
                task = f"{st.session_state.crop}의 대표 특징인 '{c['feature']}'을 관찰하고 가장 눈에 띄는 점을 적어보세요."
                st.write(f"**작목 연계 미션:** {task}")
            else:
                st.write(f"**미션:** {mission['task']}")

            choice = st.radio("가장 가까운 답을 선택하세요.", mission["choices"], key="visitor_basic_choice")
            memo = st.text_area("짧은 기록을 남겨보세요.", placeholder="예: 잎 모양이 인상적이었다.", key="visitor_basic_memo")

            if st.button("미션 완료하기", key="visitor_basic_done"):
                if mission["id"] not in st.session_state.completed:
                    st.session_state.completed.append(mission["id"])
                save_mission(
                    mission,
                    st.session_state.crop,
                    st.session_state.visitor_type,
                    st.session_state.theme,
                    "기본 QR 미션",
                    choice,
                    memo
                )
                st.success("미션이 완료되었습니다. 10P가 적립되었습니다.")

    with tab_quiz:
        crop = st.session_state.crop
        c = CROPS[crop]
        st.subheader(f"{crop} 퀴즈")
        st.write(c["summary"])
        if c.get("source"):
            st.caption(f"작목 정보 출처: {c.get('source')}")
        if c.get("source_url"):
            st.caption(f"출처 URL/메모: {c.get('source_url')}")
        for info in c["info"]:
            st.write("- " + info)
        if c.get("observation_point"):
            st.info(f"관찰 포인트: {c.get('observation_point')}")
        if c.get("safety_note"):
            st.warning(f"안전 주의: {c.get('safety_note')}")

        q = st.selectbox("퀴즈 선택", c["quiz"], format_func=lambda x: x[0], key="visitor_quiz_select")
        choice = st.radio("정답 선택", q[1], key="visitor_quiz_choice")

        if st.button("정답 확인 및 기록 저장", key="visitor_quiz_done"):
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
            if ok:
                st.success("정답입니다. 5P가 적립되었습니다.")
            else:
                st.error(f"아쉽습니다. 정답은 {q[2]}입니다.")

    with tab_points:
        name = st.session_state.visitor_name or "익명"
        mission_count, quiz_count, total_points = visitor_points(name)

        a, b, c = st.columns(3)
        a.metric("완료 미션", f"{mission_count}개")
        b.metric("퀴즈 참여", f"{quiz_count}개")
        c.metric("보유 포인트", f"{total_points}P")

        status = "수료" if total_points >= 50 or mission_count >= 5 else "진행 중"
        coupon = "농산물 5% 할인 쿠폰" if status == "수료" else "50P 달성 시 쿠폰 발급"

        certificate = f"""🌿 팜어드벤처 체험 수료증

이름/팀명: {name}
체험 작목: {st.session_state.crop}
체험 테마: {st.session_state.theme}
방문자 유형: {st.session_state.visitor_type}

완료 미션 수: {mission_count}개
퀴즈 참여 수: {quiz_count}개
획득 포인트: {total_points}P
수료 상태: {status}
혜택: {coupon}

발급 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        st.text_area("수료증 미리보기", certificate, height=300)
        st.download_button("수료증 TXT 다운로드", certificate.encode("utf-8-sig"), "farm_adventure_certificate.txt", "text/plain")

elif menu == "농장주 모드":
    st.header("농장주 모드")
    st.write("농장 운영자가 QR 미션을 만들고, 당일 체험 환경을 분석하며, 출력물을 준비하는 공간입니다.")

    tab_gen, tab_env, tab_print = st.tabs(["QR 미션 생성", "오늘의 체험 환경 분석", "배치표·출력물"])

    with tab_gen:
        farm = st.text_input("농장명", "창포마을 치유농장")
        region = st.text_input("지역/구역명", "창포마을")
        crop = st.selectbox("대표 작목", list(CROPS), index=list(CROPS).index(st.session_state.crop), key="owner_crop")
        visitor = st.selectbox("주 방문객 유형", VISITORS, index=VISITORS.index(st.session_state.visitor_type), key="owner_visitor")
        theme = st.selectbox("미션 테마", list(THEMES), index=list(THEMES).index(st.session_state.theme), key="owner_theme")
        count = st.slider("생성할 미션 수", 3, 5, 5)
        base = base_url_widget("owner_base_url", "QR에 사용할 앱 주소")

        if st.button("미션 세트 생성하기"):
            st.session_state.generated = gen_missions(farm, region, crop, visitor, theme, count)
            append_csv(GEN_FILE, {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "farm_name": farm,
                "region": region,
                "crop": crop,
                "visitor_type": visitor,
                "theme": theme,
                "mission_count": count
            })
            st.success("미션 세트가 생성되었습니다.")

        if st.session_state.generated:
            st.subheader("생성된 미션")
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for idx, m in enumerate(st.session_state.generated):
                    url = gen_url(base, farm, region, crop, visitor, theme, idx)
                    qr = qr_png(url)

                    with st.container(border=True):
                        st.markdown(f"### {m['title']}")
                        st.write(f"**장소:** {m['place']}")
                        st.write(f"**미션:** {m['task']}")
                        st.code(url, language="text")
                        if qr:
                            st.image(qr, width=150)
                            zip_file.writestr(f"mission_{idx+1}.png", qr.getvalue())
                            st.download_button(
                                f"{idx+1}번 QR 다운로드",
                                qr.getvalue(),
                                f"mission_{idx+1}.png",
                                "image/png",
                                key=f"owner_qr_{idx}"
                            )

            zip_buffer.seek(0)
            st.download_button("전체 QR ZIP 다운로드", zip_buffer.getvalue(), "farm_adventure_qr_set.zip", "application/zip")
            mission_df = pd.DataFrame(st.session_state.generated)
            st.download_button(
                "미션 목록 CSV 다운로드",
                mission_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                "generated_missions.csv",
                "text/csv"
            )

    with tab_env:
        st.subheader("오늘의 체험 환경 분석")
        st.write("현재 위치 또는 기본 위치를 기준으로 기상청·에어코리아 공공데이터를 불러와 체험 코스를 추천합니다.")

        use_geo = st.checkbox("📍 현재 위치 사용하기", value=False)
        default_lat = st.session_state.get("geo_lat", 35.9869726448865)
        default_lon = st.session_state.get("geo_lon", 127.259542032894)

        if use_geo:
            if get_geolocation is None:
                st.error("위치 인식 컴포넌트가 설치되지 않았습니다.")
            else:
                location = get_geolocation()
                lat_result, lon_result, geo_info = parse_geolocation_result(location)
                if lat_result and lon_result:
                    st.session_state.geo_lat = lat_result
                    st.session_state.geo_lon = lon_result
                    default_lat = lat_result
                    default_lon = lon_result
                    st.success("현재 위치를 인식했습니다.")
                elif geo_info:
                    st.warning(geo_info)

        col_lat, col_lon = st.columns(2)
        with col_lat:
            lat = st.number_input("위도", value=float(default_lat), format="%.13f")
        with col_lon:
            lon = st.number_input("경도", value=float(default_lon), format="%.13f")

        nx_calc, ny_calc = dfs_xy_conv(lat, lon)
        st.write(f"기상청 격자 좌표: **nx {nx_calc}, ny {ny_calc}**")

        with st.expander("API 인증키"):
            kma_key = api_key_input("기상청 API 키", "KMA_API_KEY", "기상청 API 키")
            air_key = api_key_input("에어코리아 API 키", "AIRKOREA_API_KEY", "에어코리아 API 키")

        col_air1, col_air2 = st.columns(2)
        with col_air1:
            sido = st.selectbox("시도명", ["전북", "전남", "광주", "충남", "충북", "경남", "경북", "서울", "경기", "인천", "대전", "대구", "부산", "울산", "강원", "제주", "세종"])
        with col_air2:
            station = st.text_input("측정소명", placeholder="비워두면 자동 선택")

        if st.button("공공데이터 불러오기"):
            try:
                weather = fetch_kma_ultra_forecast(kma_key, nx_calc, ny_calc)
                st.session_state.latest_weather = weather
                st.success("기상청 데이터를 불러왔습니다.")
            except Exception as e:
                st.error(f"기상청 호출 실패: {e}")

            try:
                air = fetch_airkorea_sido(air_key, sido_name=sido, station_name=station)
                st.session_state.latest_air = air
                st.success("에어코리아 데이터를 불러왔습니다.")
            except Exception as e:
                st.error(f"에어코리아 호출 실패: {e}")

        weather = st.session_state.get("latest_weather")
        air = st.session_state.get("latest_air")

        if weather:
            st.subheader("기상 데이터")
            wa, wb, wc, wd = st.columns(4)
            wa.metric("기온", f"{weather['temp']}℃")
            wb.metric("강수량", f"{weather['rain']}mm")
            wc.metric("풍속", f"{weather['wind']}m/s")
            wd.metric("하늘상태", weather["sky"])
            temp, rain, wind = weather["temp"], weather["rain"], weather["wind"]
        else:
            st.subheader("기상 수동 입력")
            temp = st.slider("기온(℃)", -10, 40, 22)
            rain = st.slider("강수량(mm)", 0, 50, 0)
            wind = st.slider("풍속(m/s)", 0, 20, 2)

        if air:
            st.subheader("대기질 데이터")
            aa, ab, ac, ad = st.columns(4)
            aa.metric("PM10", f"{air['pm10']}㎍/㎥")
            ab.metric("PM2.5", f"{air['pm25']}㎍/㎥")
            ac.metric("오존", f"{air['o3']}ppm")
            ad.metric("통합대기", air["khai_grade"])
            st.write(f"측정소: **{air['station']}** / 측정 시각: **{air['data_time']}**")
            pm = combined_air_grade(air["pm10_grade"], air["pm25_grade"], air["o3_grade"])
        else:
            st.subheader("대기질 수동 입력")
            pm = st.selectbox("미세먼지 상태", ["좋음", "보통", "나쁨", "매우나쁨"], index=1)

        st.divider()
        s, reasons = score(temp, rain, wind, pm, st.session_state.visitor_type)
        st.metric("오늘의 치유체험 적합도", f"{s}점")

        if s >= 80:
            st.success("추천 코스: 표준 야외형 코스")
        elif s >= 60:
            st.warning("추천 코스: 혼합형 코스")
        else:
            st.error("추천 코스: 실내·단축형 코스")

        for r in reasons:
            st.write("- " + r)

    with tab_print:
        if st.session_state.generated:
            mission_set = st.session_state.generated
            st.success("현재 생성된 미션 세트를 기준으로 출력물을 만듭니다.")
        else:
            mission_set = gen_missions("창포마을 치유농장", "창포마을", st.session_state.crop, st.session_state.visitor_type, st.session_state.theme, 5)
            st.info("생성된 미션 세트가 없어 현재 기본값으로 출력물 예시를 만듭니다.")

        st.subheader("현장 배치표")
        placement = pd.DataFrame([
            {
                "순서": i + 1,
                "QR 제목": m["title"],
                "권장 배치 장소": m["place"],
                "운영 포인트": m["task"][:60] + ("..." if len(m["task"]) > 60 else "")
            }
            for i, m in enumerate(mission_set)
        ])
        st.dataframe(placement, use_container_width=True)
        st.download_button(
            "배치표 CSV 다운로드",
            placement.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
            "placement_plan.csv",
            "text/csv"
        )

        guide = """🌿 팜어드벤처 QR 미션 안내

참여 방법
1. 농장 곳곳에 있는 QR 코드를 스마트폰으로 스캔합니다.
2. 화면에 나오는 작목 관찰 미션과 퀴즈를 수행합니다.
3. 미션을 완료하면 포인트가 적립됩니다.
4. 포인트가 쌓이면 수료증과 리워드를 확인할 수 있습니다.

주의사항
- 작물을 함부로 꺾거나 훼손하지 않습니다.
- 농장 운영자의 안내에 따라 이동합니다.
- 날씨나 대기질에 따라 실내형·단축형 코스로 운영될 수 있습니다.
"""
        st.text_area("출력용 안내문", guide, height=260)
        st.download_button("안내문 TXT 다운로드", guide.encode("utf-8-sig"), "visitor_guide.txt", "text/plain")

        checklist = pd.DataFrame([
            {"구분": "QR 준비", "체크 내용": "QR 이미지가 정상 출력되었는가?"},
            {"구분": "동선 점검", "체크 내용": "방문자가 안전하게 이동할 수 있는가?"},
            {"구분": "작물 보호", "체크 내용": "만지면 안 되는 구역이 안내되어 있는가?"},
            {"구분": "공공데이터 확인", "체크 내용": "당일 날씨와 대기질을 확인했는가?"},
            {"구분": "데이터 확인", "체크 내용": "관리자 모드에 응답이 저장되는가?"},
        ])
        st.table(checklist)
        st.download_button(
            "운영 체크리스트 CSV 다운로드",
            checklist.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
            "operation_checklist.csv",
            "text/csv"
        )

elif menu == "관리자 모드":
    st.header("관리자 모드")
    tab_data, tab_crop, tab_reset = st.tabs(["방문 기록", "작목 데이터", "데이터 초기화"])

    with tab_data:
        mdf = read_csv(MISSION_FILE)
        qdf = read_csv(QUIZ_FILE)
        gdf = read_csv(GEN_FILE)

        a, b, c = st.columns(3)
        a.metric("미션 응답", f"{len(mdf)}개")
        b.metric("퀴즈 응답", f"{len(qdf)}개")
        c.metric("생성 기록", f"{len(gdf)}개")

        st.subheader("미션 응답")
        if mdf.empty:
            st.info("아직 미션 응답이 없습니다.")
        else:
            st.dataframe(mdf, use_container_width=True)
            st.download_button("미션 응답 CSV 다운로드", mdf.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), "mission_responses.csv", "text/csv")

        st.subheader("퀴즈 응답")
        if qdf.empty:
            st.info("아직 퀴즈 응답이 없습니다.")
        else:
            st.dataframe(qdf, use_container_width=True)
            st.download_button("퀴즈 응답 CSV 다운로드", qdf.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), "quiz_responses.csv", "text/csv")

        st.subheader("농장주 미션 생성 기록")
        if gdf.empty:
            st.info("아직 생성 기록이 없습니다.")
        else:
            st.dataframe(gdf, use_container_width=True)
            st.download_button("생성 기록 CSV 다운로드", gdf.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), "generated_mission_sets.csv", "text/csv")

    with tab_crop:
        st.subheader("작목 데이터")
        if CROP_DB_FILE.exists():
            crop_df = pd.read_csv(CROP_DB_FILE, encoding="utf-8-sig").fillna("")
            st.dataframe(crop_df, use_container_width=True)
            st.download_button("작목 DB 다운로드", crop_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), "crop_quiz_data.csv", "text/csv")
        else:
            st.info("crop_quiz_data.csv 파일이 없습니다.")

    with tab_reset:
        st.warning("테스트 데이터를 삭제할 때만 사용하세요.")
        if st.button("현재 화면 진행률 초기화"):
            st.session_state.completed = []
            st.success("진행률이 초기화되었습니다.")

        if st.button("미션 응답 삭제"):
            if MISSION_FILE.exists():
                MISSION_FILE.unlink()
                st.success("미션 응답이 삭제되었습니다.")

        if st.button("퀴즈 응답 삭제"):
            if QUIZ_FILE.exists():
                QUIZ_FILE.unlink()
                st.success("퀴즈 응답이 삭제되었습니다.")

        if st.button("생성 기록 삭제"):
            if GEN_FILE.exists():
                GEN_FILE.unlink()
                st.success("생성 기록이 삭제되었습니다.")

elif menu == "설정":
    st.header("설정")
    st.subheader("앱 주소")
    base = base_url_widget("settings_base_url", "QR 생성 기본 주소")

    st.subheader("기본 QR 코드")
    st.write("농장주 모드에서 만든 QR과 별도로, 기본 5개 미션 QR을 생성할 수 있습니다.")

    if qrcode is None:
        st.error("qrcode 패키지가 설치되지 않았습니다.")
    else:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for m in STATIC:
                url = f"{base}/?mission={m['id']}"
                qr = qr_png(url)
                st.write(f"**{m['title']}**")
                st.code(url, language="text")
                if qr:
                    st.image(qr, width=140)
                    zip_file.writestr(f"{m['id']}_qr.png", qr.getvalue())
                st.divider()
        zip_buffer.seek(0)
        st.download_button("기본 QR 전체 ZIP 다운로드", zip_buffer.getvalue(), "basic_qr_codes.zip", "application/zip")

    st.subheader("API 키 보안 설정")
    st.info(
        "v14에서는 Streamlit Secrets에 API 키를 저장하면 화면 입력 없이 자동으로 사용됩니다. "
        "Secrets가 없을 경우에만 농장주 모드의 체험 환경 분석 화면에서 직접 입력하면 됩니다."
    )
    st.code(
        'KMA_API_KEY = "기상청_일반_인증키"\nAIRKOREA_API_KEY = "에어코리아_일반_인증키"',
        language="toml"
    )
