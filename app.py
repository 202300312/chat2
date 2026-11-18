"""모두를 위한 학교 콘서트장 설계하기 — independent v16 app."""
from __future__ import annotations
import copy, json, io, time
from pathlib import Path
import streamlit as st
import pandas as pd
from core import database as db
from core import engine
from core import ai
from core.drag_component import designer
from core import lesson_pdf

st.set_page_config(page_title='모두를 위한 학교 콘서트장 설계하기',page_icon='🌱',layout='wide',initial_sidebar_state='expanded')
# Keep the page responsive at browser zoom 80% without clipping or overriding Streamlit DOM.
st.markdown("""<style>
:root {color-scheme:light}
html,body,#root,[data-testid="stApp"],[data-testid="stAppViewContainer"] {height:100%!important;overflow:hidden!important}
[data-testid="stAppViewContainer"] {background:linear-gradient(135deg,#f3f9ef,#fcfdf8 65%,#f2faed)}
[data-testid="stHeader"] {background:#f8fcf7}
[data-testid="stAppViewContainer"] [data-testid="stMain"] {height:100dvh!important;overflow-y:auto!important;overflow-x:hidden!important;min-width:0!important;flex:1 1 auto!important}
[data-testid="stMainBlockContainer"],.block-container {max-width:1560px!important;width:100%!important;min-width:0!important;margin:0 auto!important;padding:1.15rem clamp(.8rem,2vw,2rem) 2.2rem!important}
/* Permanent navigation, no collapse control. Account anchored at bottom. */
[data-testid="stSidebar"] {width:220px!important;min-width:220px!important;max-width:220px!important;background:#edf6e9!important;border-right:1px solid #d6e6d2!important;transform:none!important}
[data-testid="stSidebarCollapseButton"],[data-testid="collapsedControl"],[data-testid="stSidebarCollapsedControl"],button[aria-label="Close sidebar"],button[aria-label="Open sidebar"] {display:none!important}
[data-testid="stSidebarContent"] {height:100dvh!important;overflow:hidden!important;padding:.6rem .5rem!important}
[data-testid="stSidebarUserContent"] {height:calc(100dvh - 1.3rem)!important;overflow-y:auto!important;display:flex!important;flex-direction:column!important}
[data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] {min-height:100%!important;display:flex!important;flex-direction:column!important;gap:.3rem!important;align-items:stretch!important}
.st-key-account_footer {margin-top:auto!important;position:sticky!important;bottom:0!important;background:#edf6e9!important;border-top:1px solid #d4e3ce;padding:.65rem .2rem .3rem!important;z-index:10}
[data-testid="stSidebar"] .stButton button {width:100%!important;justify-content:flex-start!important;text-align:left!important;border:0!important;box-shadow:none!important;border-radius:9px!important;padding:.65rem!important;min-height:44px!important;font-size:1rem!important;font-weight:550!important;white-space:normal!important}
[data-testid="stSidebar"] .stButton button[kind="secondary"] {background:transparent!important;color:#263e31!important}
[data-testid="stSidebar"] .stButton button[kind="primary"] {background:#d5ebd5!important;color:#18563a!important}
[data-testid="stSidebar"] .stButton button:hover {background:#daeeda!important}
[data-testid="stChatMessage"] {border-radius:14px!important;padding:.75rem 1rem!important}
[data-testid="stChatMessage"] p {font-size:1.04rem;line-height:1.6}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {background:#deeed8;border:1px solid #c5dfbd;margin-left:min(8%,70px)}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {background:#fff;border:1px solid #dfe9d7;margin-right:min(5%,50px)}
.stMarkdown p,.stMarkdown li {font-size:1rem;line-height:1.55}
[data-testid="stCaptionContainer"] p {font-size:.9rem}
.stButton button,.stDownloadButton button {white-space:normal}
/* The PDF review action is the single, prominent red assessment button. */
.st-key-evaluate_uploaded_pdf_v14 button {background:#bf393c!important;color:white!important;border:1px solid #a7282b!important;font-weight:750!important;font-size:1.08rem!important}
.st-key-evaluate_uploaded_pdf_v14 button:hover:not(:disabled) {background:#9f252b!important;color:white!important}
.st-key-evaluate_uploaded_pdf_v14 button:disabled {background:#e2bdbe!important;color:#725b5b!important}
/* v16: Color-coded download and account action. */
.st-key-download_design_pdf_v16 button {background:#FFD84D!important;color:#3B3105!important;border:1px solid #E1B721!important;font-weight:750!important;box-shadow:0 2px 4px #b9a13222!important}
.st-key-download_design_pdf_v16 button:hover {background:#F7C824!important;color:#302902!important;border-color:#BC9516!important}
[data-testid="stSidebar"] .st-key-logout_v16 button {background:#C92F3B!important;color:#FFFFFF!important;border:1px solid #A92330!important;font-weight:700!important;justify-content:center!important}
[data-testid="stSidebar"] .st-key-logout_v16 button:hover {background:#AC1F2A!important;color:#FFFFFF!important}
/* v16: distinguish planning controls from the canvas without sacrificing readability. */
.st-key-room_settings_card [data-testid="stExpander"] {background:#E9F5E4!important;border:1px solid #A9D5A4!important;border-radius:12px!important}
.st-key-room_settings_card [data-testid="stExpander"] summary {background:#D7EED0!important;border-radius:11px!important;color:#1C5C38!important;font-weight:750!important}
.st-key-custom_facility_card [data-testid="stExpander"] {background:#FFF8E0!important;border:1px solid #E4CE83!important;border-radius:12px!important}
.st-key-custom_facility_card [data-testid="stExpander"] summary {background:#FDF0BE!important;border-radius:11px!important;color:#67510B!important;font-weight:750!important}
.st-key-room_settings_card [data-testid="stExpander"] summary p,.st-key-custom_facility_card [data-testid="stExpander"] summary p {font-weight:750!important;font-size:1.05rem!important}
/* Keep the activity inside a single main scrollport. */
[data-testid="stMain"] [data-testid="stVerticalBlock"] {min-width:0}
[data-testid="stMain"] iframe {max-width:100%!important}
@media(max-width:850px){[data-testid="stSidebar"]{width:190px!important;min-width:190px!important;max-width:190px!important}[data-testid="stMainBlockContainer"]{padding-left:.5rem!important;padding-right:.5rem!important}}
</style>""",unsafe_allow_html=True)

@st.cache_resource
def start_db():
    db.initialize();return True
@st.cache_resource
def ai_pool():return ai.pool()
start_db()

if 'user' not in st.session_state:st.session_state.user=None

def login_screen():
    st.title('🌱 모두를 위한 학교 콘서트장 설계하기')
    st.caption('우리 학교 강당에 적용할 친환경 아이디어를 함께 설계합니다.')
    with st.form('login'):
        login=st.text_input('로그인 ID',placeholder='team1 ~ team6 또는 teacher')
        password=st.text_input('비밀번호',type='password')
        if st.form_submit_button('로그인',type='primary',use_container_width=True):
            user=db.authenticate(login.strip().lower(),password)
            if user:
                st.session_state.user=user
                st.rerun()
            else:st.error('ID 또는 비밀번호가 올바르지 않습니다.')
    with st.expander('최초 계정 안내'):
        st.write('초기 로그인 정보는 교사에게 제공되는 `data/initial_credentials.txt`에서 확인할 수 있습니다. 교사 비밀번호를 학생에게 공유하지 마세요.')
        st.write('학생에게는 해당 모둠 계정만 알려주세요. 학교 밖으로 서버를 공개하지 마세요.')

if not st.session_state.user:
    login_screen(); st.stop()

user=st.session_state.user
# ChatGPT-style left navigation; account actions remain at the bottom of the sidebar.
if 'page_v16' not in st.session_state:
    st.session_state.page_v16='design'
with st.sidebar:
    st.markdown('### 🌱 콘서트장 설계실')
    st.caption('수업 메뉴')
    if user['role']=='teacher':
        st.markdown('**교사 관리실**')
    else:
        nav_options={'design':'✏️ 콘서트장 설계도 만들기','chat':'💬 AI챗봇에게 물어보기'}
        for nav_id, nav_text in nav_options.items():
            if st.button(nav_text, key=f'nav_v16_{nav_id}',
                         use_container_width=True,
                         type='primary' if st.session_state.page_v16==nav_id else 'secondary'):
                if st.session_state.page_v16 != nav_id:
                    st.session_state.page_v16=nav_id
                    st.rerun()
    
    with st.container(key='account_footer'):
        st.divider()
        st.markdown(f'**👤 {user["display"]}**')
        st.caption(f'계정: {user["login"]}')
        with st.expander('🔑 비밀번호 변경',expanded=False):
            with st.form('change_pwd_v10'):
                old=st.text_input('현재 비밀번호',type='password')
                new=st.text_input('새 비밀번호 (8자 이상)',type='password')
                if st.form_submit_button('비밀번호 변경',use_container_width=True):
                    if db.change_password(user['id'],old,new): st.success('비밀번호가 변경되었습니다.')
                    else: st.error('현재 비밀번호 또는 새 비밀번호를 확인하세요.')
        if st.button('로그아웃',key='logout_v16',use_container_width=True):
            st.session_state.clear()
            st.rerun()

if user['role']=='teacher':
    st.title('📊 모두를 위한 학교 콘서트장 설계하기 · 교사 관리실')
    st.caption('모둠별 설계안과 챗봇 사용 기록을 조회합니다. 학생 설계는 교사 화면에서 직접 덮어쓰지 않습니다.')
    teams=db.teams()
    st.dataframe(pd.DataFrame([{'모둠':t['display'],'버전':t['revision'],'마지막 저장':t['updated_at']} for t in teams]),hide_index=True,use_container_width=True)
    choice=st.selectbox('조회할 모둠',teams,format_func=lambda x:x['display'])
    d,rev,_=db.get_design(choice['id'])
    if d:
        st.markdown('**모둠 공동 문서**')
        st.write(db.get_team_document(choice['id'])['body'] or '기록 없음')
        st.image(engine.plan_bytes(d),caption=f'{choice["display"]} 설계도 · v{rev}',use_container_width=True)
        with st.expander('친환경 설계 검토 (규칙 기반)'):
            st.write(engine.rules_feedback(d))
        st.download_button('설계도 PDF 저장',lesson_pdf.design_to_pdf(d,choice['display']),file_name=f'{choice["login"]}_design.pdf',mime='application/pdf')
        st.subheader('이전 검토 기록')
        for r in db.reviews(choice['id']):
            with st.expander(f'검토 #{r["id"]} · v{r["revision"]} · {r["decision"]} · {r["created_at"]}'):
                st.write(r['feedback']);st.caption('학생 판단: '+r['reason'])
        st.subheader('최근 대화')
        for msg in db.chats(choice['id'],20):
            with st.chat_message('assistant' if msg['role']=='assistant' else 'user'):
                st.write(msg['text'])
    st.stop()

# Team session: each group is persisted separately; same-group concurrent edits require a refresh on conflict.
team_id=user['id']
if st.session_state.get('loaded_team') != team_id:
    d,rev,_=db.get_design(team_id)
    st.session_state.design=d
    st.session_state.revision=rev
    st.session_state.loaded_team=team_id
    st.session_state.dirty=False
    st.session_state.next_id=max((x['id'] for x in d['items']),default=0)+1

D=st.session_state.design

def touch():st.session_state.dirty=True

def save():
    new_rev=db.save_design(team_id,D,st.session_state.revision)
    if new_rev is None:
        st.error('다른 창에서 설계도를 먼저 저장했습니다. 저장이 취소되었습니다. 다른 학생의 저장본이 먼저 반영되었습니다. 새로 로그인해 최신 설계를 확인하세요.')
    else:
        st.session_state.revision=new_rev;st.session_state.dirty=False
        st.success(f'설계안 v{new_rev} 저장 완료')

def number_field(label,value,minval,maxval,step,key):
    return st.number_input(label,min_value=minval,max_value=maxval,value=float(value),step=step,key=key)

st.title('🌱 모두를 위한 학교 콘서트장 설계하기')

st.caption(f'{user["display"]} · 현재 저장 버전 v{st.session_state.revision} · {"저장되지 않은 변경 있음" if st.session_state.dirty else "저장됨"}')
page=st.session_state.page_v16

if page=='design':
    st.subheader('콘서트장 설계도 만들기')
    st.caption('친환경 시설을 선택하거나 끌어 강당에 배치하고, 우리 모둠의 설계 의도를 기록하세요.')
    with st.container(key='room_settings_card'):
        with st.expander('강당 크기 및 관객 수 설정',expanded=False):
            with st.form('room_settings'):
                c1,c2,c3=st.columns(3)
                rw=c1.number_input('강당 가로(m)',min_value=5.,max_value=60.,value=float(D['room_w']),step=1.)
                rh=c2.number_input('강당 세로(m)',min_value=5.,max_value=50.,value=float(D['room_h']),step=1.)
                people=c3.number_input('관객 수',min_value=0,max_value=5000,value=int(D['people']),step=10)
                st.caption('PDF 기반 인원 대비 평가를 위해 아래 계획값을 입력할 수 있습니다. 알 수 없는 값은 0으로 두면 감점하지 않습니다.')
                s1,s2=st.columns(2)
                seat_cap=s1.number_input('계획 관객석 총 좌석 수 (0=미입력)',min_value=0,max_value=5000,value=int(D.get('planned_seats',0)),step=10,help='설계도에서 관객석 구역이 몇 석을 수용하는지 학생이 확인한 값입니다.')
                recycle_limit=s2.number_input('분리배출 시설 1개당 계획 이용 인원 (0=미입력)',min_value=0,max_value=5000,value=int(D.get('recycle_service_capacity',0)),step=10,help='모둠에서 정한 운영 가정입니다. 법적 기준이나 실제 인증값을 뜻하지 않습니다.')
                if st.form_submit_button('강당 조건 적용'):
                    D.update(room_w=rw,room_h=rh,people=people,planned_seats=seat_cap,recycle_service_capacity=recycle_limit);touch();st.rerun()
    with st.container(key='custom_facility_card'):
        with st.expander('➕ 학생이 원하는 시설 추가하기'):
            with st.form('custom_facility_form',clear_on_submit=True):
                coln,colw,colh=st.columns(3)
                custom_name=coln.text_input('시설 이름',max_chars=30,placeholder='예: 다회용 컵 반납함')
                custom_w=colw.number_input('초기 가로(m)',min_value=0.25,max_value=float(D['room_w']),value=min(2.0,float(D['room_w'])),step=0.25)
                custom_h=colh.number_input('초기 세로(m)',min_value=0.25,max_value=float(D['room_h']),value=min(1.5,float(D['room_h'])),step=0.25)
                if st.form_submit_button('시설 목록에 추가',type='primary'):
                    name=custom_name.strip()
                    if not name:st.error('시설 이름을 입력하세요.')
                    else:
                        cid='custom_'+str(max([int(k.split('_')[-1]) for k in D.get('custom_facilities',{}) if k.split('_')[-1].isdigit()]+[0])+1)
                        D.setdefault('custom_facilities',{})[cid]=[name,'#b4ded0',[float(custom_w),float(custom_h)]]
                        touch();st.rerun()
    all_facilities={**engine.FACILITIES,**D.get('custom_facilities',{})}
    action=designer(D,all_facilities,key=f'layout_v16_{team_id}')
    if action and action.get('nonce') != st.session_state.get('last_action_nonce'):
        st.session_state.last_action_nonce=action['nonce']
        typ=action.get('type')
        if typ=='add' and action.get('kind') in all_facilities:
            kind=action['kind'];w,h=all_facilities[kind][2]
            x=max(0.,min(float(action.get('x',0)),max(0,D['room_w']-w)))
            y=max(0.,min(float(action.get('y',0)),max(0,D['room_h']-h)))
            D['items'].append({'id':st.session_state.next_id,'kind':kind,'x':round(x,2),'y':round(y,2),'w':float(w),'h':float(h),'rotation':0})
            st.session_state.next_id+=1;touch();st.rerun()
        elif typ=='move':
            item=next((a for a in D['items'] if a['id']==action.get('id')),None)
            if item:
                item['x']=max(0.,min(float(action.get('x',item['x'])),max(0,D['room_w']-item['w'])))
                item['y']=max(0.,min(float(action.get('y',item['y'])),max(0,D['room_h']-item['h'])))
                touch();st.rerun()
        elif typ=='transform':
            item=next((a for a in D['items'] if a['id']==action.get('id')),None)
            if item:
                try:
                    nw=float(action.get('w',item['w']));nh=float(action.get('h',item['h']))
                    nx=float(action.get('x',item['x']));ny=float(action.get('y',item['y']))
                    angle=float(action.get('rotation',item.get('rotation',0)))%360
                    if 0.25<=nw<=D['room_w'] and 0.25<=nh<=D['room_h'] and all(map(__import__('math').isfinite,[nx,ny,nw,nh,angle])):
                        item.update(x=round(max(-0.25,min(nx,D['room_w']-0.25)),3),y=round(max(-0.25,min(ny,D['room_h']-0.25)),3),w=round(nw,3),h=round(nh,3),rotation=round(angle,1))
                        touch();st.rerun()
                except (TypeError,ValueError):st.warning('시설 크기 또는 회전 값이 올바르지 않습니다.')
        elif typ=='delete':
            before=len(D['items']);D['items']=[x for x in D['items'] if x['id']!=action.get('id')]
            if len(D['items'])<before:touch();st.rerun()
    st.caption('강당 실측 자료를 기준으로 배치하고, 변경한 설계안은 저장하세요.')
    st.markdown('#### 함께 작성하는 설계 설명 문서')
    st.caption('같은 모둠 계정으로 접속한 학생들은 하나의 문서를 함께 사용합니다. 같은 모둠의 학생은 저장된 공동 문서를 이용할 수 있습니다. 다른 학생이 동시에 수정한 경우에는 저장 충돌을 안내합니다.')
    if st.session_state.get('doc_team')!=team_id or st.session_state.pop('doc_refresh_pending',False):
        doc=db.get_team_document(team_id)
        st.session_state.doc_team=team_id
        st.session_state.doc_text=doc['body']
        st.session_state.doc_revision=doc['revision']
    notes=st.text_area('모둠 공동 설계 설명',key='doc_text',height=150,placeholder='선정한 친환경 시설, 배치 이유, 예상 효과, 실제 검증할 내용 등을 공동으로 기록해 보세요.')
    if st.button('💾 공동 문서 저장',use_container_width=True):
        if db.save_team_document(team_id,notes,st.session_state.doc_revision):
            st.session_state.doc_revision+=1;st.success('공동 문서가 저장되었습니다.')
        else:st.warning('다른 학생이 먼저 저장했습니다. 필요한 내용은 복사해서 보관하고 새로 접속한 뒤 확인하세요.')
    c1,c2=st.columns(2)
    with c1:
        if st.button('💾 설계도 저장',type='primary',use_container_width=True):save()
    with c2:
        st.download_button('📄 설계도 PDF 내려받기',lesson_pdf.design_to_pdf(D,user['display']),file_name=f'{user["login"]}_design.pdf',mime='application/pdf',use_container_width=True,key='download_design_pdf_v16')

elif page=='chat':
    st.subheader('💬 AI챗봇에게 물어보기')
    st.caption('환경 수업에 관해 궁금한 점을 자유롭게 질문하세요. 설계 평가가 필요할 때는 PDF 설계도 평가 기능을 이용하세요.')
    available,details=ai.check_ollama()
    if available:
        st.caption('🟢 로컬 AI 연결됨 · Qwen3 1.7B')
    else:
        st.warning('로컬 AI에 연결할 수 없습니다. Ollama를 실행하고 qwen3:1.7b 모델을 설치하세요.')
        st.caption('연결 상태: '+details)
    if 'job' not in st.session_state: st.session_state.job=None

    # The polling fragment ONLY renders the job status. Chat messages render in
    # the main script to avoid replacing live chat DOM nodes during partial reruns.
    @st.fragment(run_every=3)
    def check_job():
        job=st.session_state.get('job')
        if job is None: return
        if not job.done():
            st.info('⏳ AI가 답변을 작성하고 있습니다. 이 화면을 열어 두면 완료 시 표시됩니다.')
            return
        try:
            answer=job.result()
            db.add_chat(team_id,'assistant',answer)
            st.session_state.ai_done_notice=True
        except Exception as exc:
            st.session_state.ai_error=str(exc)[:220]
        finally:
            st.session_state.job=None
            st.rerun(scope='app')
    check_job()
    if st.session_state.pop('ai_done_notice',False):
        st.success('✅ AI 답변이 도착했습니다. 아래 대화에서 확인할 수 있습니다.')
    if st.session_state.pop('ai_error',None) is not None:
        st.error('AI 응답 처리 중 오류가 발생했습니다. Ollama 연결을 확인하세요.')

    with st.expander('자주 묻는 질문 보기', expanded=False):
        st.markdown("""- 우리 설계안의 잘한 점과 개선할 점을 알려주세요.
- 관객 참여형 발전 장치가 현실적으로 효과가 있을까요?
- 분리배출 시설을 효과적으로 배치하려면 어떻게 해야 하나요?
- LED 조명 교체의 실제 환경적 효과를 확인하려면 어떤 자료가 필요한가요?""")

    with st.expander('📄 강당 조사 PDF',expanded=False):
        st.write('환경 수업에서 한 번에 조사한 강당 자료를 PDF 한 파일로 등록하세요. AI가 추출한 텍스트를 설계 검토에 참고합니다.')
        st.caption('텍스트가 포함된 PDF만 지원합니다. 개인정보가 있는 문서는 업로드하지 마세요. 8MB 이하, 최대 40쪽입니다.')
        current=lesson_pdf.get_document(team_id)
        if current:
            st.success(f'등록된 강당 조사 PDF: {current["filename"]} · 텍스트 {current["chars"]:,}자')
        upload=st.file_uploader('강당 조사 PDF 파일 선택',type=['pdf'],key=f'survey_pdf_v14_{team_id}')
        if upload and st.button('강당 조사 PDF 저장·교체',key=f'upload_survey_v14_{team_id}'):
            try:
                meta=lesson_pdf.save_document(team_id,upload.name,upload.getvalue())
                st.success(f'저장 완료: {meta["filename"]} · {meta["chars"]:,}자 추출')
                st.rerun()
            except ValueError as exc: st.error(str(exc))
        if current:
            if st.button('등록된 강당 조사 PDF 삭제',key=f'remove_survey_v14_{team_id}'):
                lesson_pdf.delete_document(team_id)
                st.rerun()
    facts=lesson_pdf.get_survey_facts(team_id)
    if facts:
        st.caption('PDF에서 확인된 조사 수치: '+ ' · '.join(f'{k}: {v}' for k,v in facts.items())+' (자료 문구를 직접 확인하세요)')
    st.caption('AI는 강당 조사 PDF의 문장을 참고하되, 측정값이 없거나 문서에서 추출되지 않으면 추측하지 않습니다.')
    st.markdown('#### 학생과 AI의 대화')
    st.caption('설계도 PDF를 올려 평가하면 점수·감점 근거·잘한 점·개선할 점·확인이 필요한 부분이 대화창에 표시됩니다.')
    survey_present=bool(lesson_pdf.get_document(team_id))
    design_pdf=st.file_uploader('평가할 설계도 PDF 업로드 (이 웹앱에서 저장한 PDF)',type=['pdf'],key=f'design_pdf_v14_{team_id}',help='이 웹앱에서 내보낸 PDF에는 시설 배치와 강당 치수 데이터가 포함되어 있어 평가할 수 있습니다. 다른 PDF는 자동 도면 판독이 지원되지 않습니다.')
    pdf_design=None
    if design_pdf is not None:
        try:
            pdf_design=lesson_pdf.design_from_pdf(design_pdf.getvalue())
            st.success(f'PDF 설계도 인식: 강당 {pdf_design["room_w"]:g} × {pdf_design["room_h"]:g}m, 시설 {len(pdf_design["items"])}개')
            st.caption('업로드한 PDF의 설계 데이터 기준으로 평가하며, 현재 편집 중인 설계도와는 다를 수 있습니다.')
        except ValueError as e:
            st.warning(str(e))
    if st.button('🔴 업로드한 PDF 설계도 AI 평가',
                 disabled=(pdf_design is None or st.session_state.job is not None),
                 use_container_width=True,key='evaluate_uploaded_pdf_v14'):
        q='업로드한 설계도 PDF를 100점 기준으로 평가해 주세요. 점수, 실제 감점 근거, 잘한 점, 개선할 점, 확인이 필요한 부분을 구분해 주세요.'
        history=db.chats(team_id,8)
        db.add_chat(team_id,'user',q)
        st.session_state.job=ai_pool().submit(ai.review_worker,q,copy.deepcopy(pdf_design),history,lesson_pdf.get_combined_context(team_id),survey_present,lesson_pdf.get_survey_facts(team_id))
        st.rerun()
    msgs=db.chats(team_id,60)
    if not msgs:
        st.info('아직 대화가 없습니다. 아래 입력창에 질문을 작성하세요.')
    for m in msgs:
        with st.chat_message('assistant' if m['role']=='assistant' else 'user',
                             avatar='🌿' if m['role']=='assistant' else '👤'):
            st.markdown('**AI**' if m['role']=='assistant' else '**학생**')
            st.write(m['text'])
            with st.popover('⋮',help='이 메시지 삭제'):
                if st.button('이 메시지 삭제',key=f'del_v14_{m["id"]}',
                             disabled=st.session_state.job is not None):
                    db.delete_chat(team_id,m['id'])
                    st.rerun()

    with st.popover('⋮ 대화 관리'):
        st.caption('대화만 삭제하며 설계도와 공동 문서는 유지됩니다.')
        if st.button('전체 대화 삭제 요청',key='clear_v10',disabled=st.session_state.job is not None):
            st.session_state.confirm_clear_v14=True
        if st.session_state.get('confirm_clear_v14'):
            st.warning('대화가 전부 삭제됩니다. 계속하시겠습니까?')
            if st.button('삭제 확인',key='confirm_v10'):
                db.clear_chats(team_id)
                st.session_state.confirm_clear_v14=False
                st.rerun()
            if st.button('취소',key='cancel_v10'):
                st.session_state.confirm_clear_v14=False
                st.rerun()

    question=st.chat_input('친환경 콘서트장 설계에 관해 질문하세요',
                           disabled=(not available or st.session_state.job is not None),
                           max_chars=1800)
    if question:
        if not ai.in_scope(question):
            db.add_chat(team_id,'user',question)
            db.add_chat(team_id,'assistant',ai.OUT_OF_SCOPE)
            st.rerun()
        else:
            history=db.chats(team_id,8)
            db.add_chat(team_id,'user',question)
            st.session_state.job=ai_pool().submit(ai.worker,question,copy.deepcopy(D),history,lesson_pdf.get_combined_context(team_id),bool(lesson_pdf.get_document(team_id)))
            st.session_state.ai_done_notice=False
            st.rerun()
    st.caption('개인정보를 입력하지 마세요. AI 답변은 참고자료이며 최종 설계는 학생들이 결정합니다.')
