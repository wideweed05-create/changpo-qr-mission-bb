
import streamlit as st
from pathlib import Path
from datetime import datetime
import pandas as pd
import io, zipfile
try:
    import qrcode
except Exception:
    qrcode = None

st.set_page_config(page_title='팜어드벤처 | 창포마을 QR 미션', page_icon='🌿', layout='centered')
DATA_PATH = Path('mission_responses.csv')

MISSIONS = [
    {'id':'welcome','title':'1번 QR · 입구 환영 미션','emoji':'🌿','place':'농장 입구','task':'천천히 숨을 3번 들이마시고, 오늘 농장에서 기대하는 감정을 하나 골라보세요.','choices':['편안함','기대감','호기심','회복','즐거움'],'effect':'긴장을 낮추고 체험 몰입을 유도합니다.'},
    {'id':'observe','title':'2번 QR · 식물 관찰 미션','emoji':'🔍','place':'창포/식물 관찰 구역','task':'가장 눈에 들어오는 식물 하나를 고르고 색·모양·향 중 하나를 자세히 관찰해보세요.','choices':['색이 인상적이다','모양이 독특하다','향이 좋다','촉감이 궁금하다'],'effect':'오감을 활용해 자연과 상호작용하도록 돕습니다.'},
    {'id':'scent','title':'3번 QR · 향기 기억 미션','emoji':'💐','place':'허브/향기 체험 구역','task':'식물의 향을 맡고 떠오르는 기억이나 기분을 짧게 적어보세요.','choices':['어릴 적 기억','가족','여행','휴식','새로운 느낌'],'effect':'향기 자극을 통해 정서적 안정과 긍정적 회상을 유도합니다.'},
    {'id':'walk','title':'4번 QR · 느린 걷기 미션','emoji':'🚶','place':'마을길/산책로','task':'30초 동안 평소보다 천천히 걸으며 주변에서 들리는 소리 1가지를 찾아보세요.','choices':['바람 소리','새소리','발걸음 소리','사람들의 목소리','기타 자연 소리'],'effect':'신체 움직임과 자연 감각을 연결해 마음을 안정시킵니다.'},
    {'id':'message','title':'5번 QR · 오늘의 치유 문장','emoji':'📝','place':'마무리 공간/포토존','task':'오늘 체험을 마치며 나에게 해주고 싶은 말을 한 문장으로 적어보세요.','choices':['수고했어','천천히 가도 괜찮아','오늘 잘 쉬었다','다시 오고 싶다','내가 나를 돌보는 시간'],'effect':'체험의 감정을 정리하고 만족감을 높입니다.'},
]
MISSION_BY_ID={m['id']:m for m in MISSIONS}

if 'completed' not in st.session_state: st.session_state.completed=[]
if 'visitor_name' not in st.session_state: st.session_state.visitor_name=''
if 'visitor_type' not in st.session_state: st.session_state.visitor_type='일반 성인'
if 'theme' not in st.session_state: st.session_state.theme='힐링형'

def save_response(name, vtype, theme, mission, choice, memo):
    row={'timestamp':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'visitor_name':name or '익명','visitor_type':vtype,'theme':theme,'mission_id':mission['id'],'mission_title':mission['title'],'place':mission['place'],'choice':choice,'memo':memo,'earned_points':10}
    if DATA_PATH.exists():
        df=pd.read_csv(DATA_PATH, encoding='utf-8-sig')
        df=pd.concat([df,pd.DataFrame([row])], ignore_index=True)
    else: df=pd.DataFrame([row])
    df.to_csv(DATA_PATH, index=False, encoding='utf-8-sig')

def read_responses():
    if DATA_PATH.exists(): return pd.read_csv(DATA_PATH, encoding='utf-8-sig')
    return pd.DataFrame(columns=['timestamp','visitor_name','visitor_type','theme','mission_id','mission_title','place','choice','memo','earned_points'])

def make_qr(url):
    if qrcode is None: return None
    img=qrcode.make(url); buf=io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0); return buf

def score_course(temp, rain, wind, pm, sky, vtype):
    score=100; reasons=[]
    if temp<5: score-=25; reasons.append('기온이 매우 낮아 실외 체류 시간을 줄이는 것이 좋습니다.')
    elif temp<10: score-=12; reasons.append('다소 쌀쌀하므로 짧은 야외 미션 중심이 적절합니다.')
    elif temp>32: score-=25; reasons.append('기온이 높아 그늘·실내형 체험 비중을 높이는 것이 좋습니다.')
    elif temp>28: score-=12; reasons.append('조금 더울 수 있어 휴식 구간을 자주 배치하는 것이 좋습니다.')
    else: reasons.append('기온이 야외 치유농장 활동에 비교적 적합합니다.')
    if rain>=10: score-=30; reasons.append('강수량이 많아 실내형 또는 처마형 체험으로 전환하는 것이 좋습니다.')
    elif rain>0: score-=12; reasons.append('비가 예상되어 우산 동선과 미끄럼 주의 안내가 필요합니다.')
    else: reasons.append('강수 조건은 야외 체험 진행에 큰 제약이 없습니다.')
    if wind>=8: score-=15; reasons.append('바람이 강해 야외 안내판·포토존 안전 확인이 필요합니다.')
    elif wind>=5: score-=7; reasons.append('바람이 다소 있어 안내물 점검이 필요합니다.')
    score -= {'좋음':0,'보통':5,'나쁨':20,'매우나쁨':35}.get(pm,0)
    if pm in ['나쁨','매우나쁨']: reasons.append('대기질이 좋지 않아 실내형 감각·회고 미션을 우선 추천합니다.')
    else: reasons.append('대기질 조건은 야외 활동에 큰 제약이 없습니다.')
    if sky in ['흐림','비']: score-=5; reasons.append('흐리거나 비가 오는 날은 밝은 색 관찰·향기 체험 중심이 좋습니다.')
    if vtype in ['고령층','가족/아동','요양원/복지기관']: score-=5; reasons.append('방문자 특성을 고려해 이동 거리를 짧게 설계하는 것이 좋습니다.')
    score=max(0,min(100,score))
    if pm in ['나쁨','매우나쁨'] or rain>=10 or temp>32 or temp<5:
        label='실내·단축형 코스'; ids=['welcome','scent','message']; msg='날씨나 대기질 부담을 줄이기 위해 이동을 줄이고 감각·회고형 미션 중심으로 운영하세요.'
    elif vtype in ['고령층','가족/아동','요양원/복지기관']:
        label='안전 배려형 코스'; ids=['welcome','observe','scent','message']; msg='체력 부담을 줄이고 관찰·향기 체험을 중심으로 천천히 진행하세요.'
    else:
        label='표준 야외형 코스'; ids=['welcome','observe','scent','walk','message']; msg='현재 조건에서는 전체 QR 미션을 순서대로 진행하기 좋습니다.'
    return score,label,[MISSION_BY_ID[i]['title'] for i in ids],msg,reasons

def theme_hint(theme):
    return {'힐링형':'감정 기록, 향기, 산책, 회고 중심의 부드러운 미션에 적합합니다.','추리형':'작물 단서 찾기, QR 암호, 관찰 퀴즈를 결합하면 몰입도가 높아집니다.','교육형':'작물 특징, 생육 단계, 농업 지식을 퀴즈로 연결하는 방식이 좋습니다.','가족형':'함께 말하기, 사진 인증, 협동 미션을 넣으면 가족 단위 참여에 적합합니다.','고령층 배려형':'짧은 동선, 향기 기억, 회상 질문, 충분한 휴식 안내가 중요합니다.'}.get(theme,'')

st.title('🌿 팜어드벤처: 창포마을 QR 미션')
st.caption('공공데이터 기반 치유농장 QR 미션 MVP v4')
query_mission=st.query_params.get('mission','')
with st.sidebar:
    menu=st.radio('메뉴', ['홈','공공데이터 추천','QR 미션 체험','QR 코드 만들기','관리자 데이터','대회 발표 요약','초기화'])
if query_mission in MISSION_BY_ID: menu='QR 미션 체험'

st.subheader('방문자 기본 정보')
st.session_state.visitor_name=st.text_input('방문자 이름 또는 팀명', value=st.session_state.visitor_name, placeholder='예: 1조 / 창포팀')
c1,c2=st.columns(2)
with c1: st.session_state.visitor_type=st.selectbox('방문자 유형',['일반 성인','가족/아동','고령층','요양원/복지기관','학생 단체','연인/친구'])
with c2: st.session_state.theme=st.selectbox('체험 테마',['힐링형','추리형','교육형','가족형','고령층 배려형'])
st.progress(len(st.session_state.completed)/len(MISSIONS))
st.write(f"현재 완료한 미션: **{len(st.session_state.completed)} / {len(MISSIONS)}개** · 획득 포인트: **{len(st.session_state.completed)*10}P**")

if menu=='홈':
    st.header('서비스 개요')
    st.write('팜어드벤처는 창포마을 치유농장을 대상으로 한 QR 미션 기반 체험 MVP입니다. 방문자는 QR을 따라 미션을 수행하고, 농장주는 방문자 기록을 데이터로 확인할 수 있습니다.')
    st.subheader('v4 핵심 변화')
    st.write('1. 기온·강수·풍속·미세먼지 값을 활용한 체험 적합도 계산')
    st.write('2. 방문자 유형별 추천 코스 제안')
    st.write('3. 체험 테마 선택 기능 추가')
    st.write('4. 공공데이터 활용 구조와 대회 발표 요약 화면 추가')
    st.info('현재 MVP는 공공데이터 값을 수동 입력하여 추천 로직을 시연합니다. 향후에는 기상청, 에어코리아, 농업기상 API와 자동 연동할 수 있습니다.')

elif menu=='공공데이터 추천':
    st.header('공공데이터 기반 체험 추천')
    st.write('API 키 없이도 시연 가능한 추천 로직입니다. 실제 서비스 단계에서는 기상·대기질 공공데이터 API 값을 자동으로 받아오도록 확장합니다.')
    a,b=st.columns(2)
    with a:
        temp=st.slider('기온(℃)',-10,40,22); rain=st.slider('예상 강수량(mm)',0,50,0); sky=st.selectbox('하늘 상태',['맑음','구름많음','흐림','비'])
    with b:
        wind=st.slider('풍속(m/s)',0,20,2); pm=st.selectbox('미세먼지 상태',['좋음','보통','나쁨','매우나쁨']); vt=st.selectbox('추천 기준 방문자 유형',['일반 성인','가족/아동','고령층','요양원/복지기관','학생 단체','연인/친구'])
    score,label,course,msg,reasons=score_course(temp,rain,wind,pm,sky,vt)
    st.metric('오늘의 치유체험 적합도', f'{score}점')
    if score>=80: st.success('야외형 치유농장 체험에 적합한 조건입니다.')
    elif score>=60: st.warning('체험은 가능하지만 일부 동선 조정이 필요합니다.')
    else: st.error('실외 체험 비중을 줄이고 안전·실내형 프로그램을 우선하는 것이 좋습니다.')
    st.subheader(f'추천 코스: {label}'); st.write(msg)
    for i,x in enumerate(course,1): st.write(f'{i}. {x}')
    st.subheader('추천 근거')
    for r in reasons: st.write(f'- {r}')
    st.subheader('선택 테마 반영'); st.info(theme_hint(st.session_state.theme))
    st.subheader('공공데이터 적용 구조')
    st.table([
        {'공공데이터':'기상청 단기예보','활용값':'기온, 강수량, 하늘상태, 풍속','앱 적용':'야외/실내 코스 추천, 안전 안내'},
        {'공공데이터':'에어코리아 대기오염정보','활용값':'미세먼지, 초미세먼지, 오존','앱 적용':'실외 체류 시간 조정, 민감군 안내'},
        {'공공데이터':'농업기상 관측데이터','활용값':'기온, 습도, 강수량, 일사량','앱 적용':'농장 현장 환경 기반 체험 운영 판단'},
        {'공공데이터':'농산물 가격·제철 정보','활용값':'가격 하락 품목, 제철 농산물','앱 적용':'향후 포인트 할인·농산물 리워드 추천'}])

elif menu=='QR 미션 체험':
    st.header('QR 미션 체험')
    default=0
    if query_mission in MISSION_BY_ID: default=[m['id'] for m in MISSIONS].index(query_mission)
    title=st.selectbox('미션 선택',[m['title'] for m in MISSIONS], index=default)
    m=next(x for x in MISSIONS if x['title']==title)
    st.subheader(f"{m['emoji']} {m['title']}"); st.write(f"**장소:** {m['place']}"); st.write(f"**미션:** {m['task']}")
    st.caption(f"현재 테마 적용 방향: {theme_hint(st.session_state.theme)}")
    choice=st.radio('가장 가까운 느낌을 선택하세요.', m['choices'])
    memo=st.text_area('짧은 기록을 남겨보세요.', placeholder='예: 향이 생각보다 편안했고 잠깐 쉬어가는 느낌이 들었다.')
    st.caption(f"기대 효과: {m['effect']}")
    if st.button('이 미션 완료하기'):
        if m['id'] not in st.session_state.completed: st.session_state.completed.append(m['id'])
        save_response(st.session_state.visitor_name, st.session_state.visitor_type, st.session_state.theme, m, choice, memo)
        st.success('미션 완료! 응답이 저장되고 10P가 적립되었습니다.')
    if len(st.session_state.completed)==len(MISSIONS):
        st.balloons(); st.header('🎉 모든 미션 완료')
        st.write(f"**{st.session_state.visitor_name or '방문자'}님, 창포마을 치유농장 QR 미션을 모두 완료했습니다.**")
        st.write('획득 포인트: **50P** / 사용 가능 쿠폰: **창포마을 농산물 5% 할인 쿠폰**')

elif menu=='QR 코드 만들기':
    st.header('QR 코드 만들기')
    base_url=st.text_input('앱 기본 주소', value='http://localhost:8501', help='배포 주소가 있으면 Streamlit 앱 주소를 넣으세요.').strip().rstrip('/')
    if qrcode is None: st.error('qrcode 패키지가 설치되지 않았습니다.')
    else:
        zipbuf=io.BytesIO()
        with zipfile.ZipFile(zipbuf,'w',zipfile.ZIP_DEFLATED) as z:
            for m in MISSIONS:
                url=f"{base_url}/?mission={m['id']}"; qr=make_qr(url); z.writestr(f"{m['id']}_qr.png", qr.getvalue())
                st.subheader(m['title']); st.code(url); st.image(qr, width=180)
                st.download_button(f"{m['title']} QR 이미지 다운로드", qr.getvalue(), file_name=f"{m['id']}_qr.png", mime='image/png')
                st.divider()
        zipbuf.seek(0); st.download_button('전체 QR 이미지 ZIP으로 다운로드', zipbuf.getvalue(), file_name='changpo_qr_codes.zip', mime='application/zip')

elif menu=='관리자 데이터':
    st.header('관리자 데이터')
    df=read_responses()
    if df.empty: st.info('아직 저장된 응답이 없습니다.')
    else:
        a,b,c=st.columns(3); a.metric('참여자 수', f"{df['visitor_name'].nunique()}명"); b.metric('총 미션 기록', f'{len(df)}개'); c.metric('총 적립 포인트', f"{int(df['earned_points'].sum())}P")
        st.dataframe(df, use_container_width=True)
        st.download_button('응답 데이터 CSV 다운로드', df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'), 'mission_responses.csv', 'text/csv')
        st.subheader('미션별 응답 수'); st.bar_chart(df['mission_title'].value_counts())
        st.subheader('테마별 선택 수'); st.bar_chart(df['theme'].value_counts())

elif menu=='대회 발표 요약':
    st.header('대회 발표 요약')
    st.success('팜어드벤처는 날씨·대기질 등 공공데이터와 QR 미션을 결합해 방문자에게 맞춤형 치유농업 체험 동선을 제공하는 창포마을 파일럿 서비스입니다.')
    st.subheader('문제 인식'); st.write('기존 농촌 체험은 수확·만들기 중심의 일회성 프로그램이 많아 재방문 유도와 데이터 기반 개선이 어렵습니다. 또한 날씨, 대기질, 방문자 특성에 따라 체험 동선을 유연하게 바꾸는 체계가 부족합니다.')
    st.subheader('해결 방안'); st.write('방문자는 QR을 따라 미션을 수행하고, 농장주는 관리자 화면에서 방문자 기록을 확인합니다. 기상·대기질·농업기상 데이터를 활용해 당일 체험 적합도와 추천 코스를 제안합니다.')
    st.subheader('MVP 시연 순서'); st.write('1. 공공데이터 추천 화면에서 체험 적합도 확인'); st.write('2. QR 코드 만들기에서 미션별 QR 생성'); st.write('3. 스마트폰으로 QR을 찍어 미션 수행'); st.write('4. 관리자 데이터에서 방문자 응답 확인')
    st.subheader('향후 확장'); st.write('실제 공공데이터 API 자동 연동, 농장주 원클릭 미션 생성기, 수료증과 포인트 마켓, 농산물 가격 하락 품목과 리워드 할인율 연계')

elif menu=='초기화':
    st.header('초기화')
    if st.button('내 화면의 미션 완료 기록 초기화'):
        st.session_state.completed=[]; st.success('현재 화면의 진행률이 초기화되었습니다.')
    if st.button('저장된 응답 CSV 삭제'):
        if DATA_PATH.exists(): DATA_PATH.unlink(); st.success('저장된 응답 데이터가 삭제되었습니다.')
        else: st.info('삭제할 응답 데이터가 없습니다.')
