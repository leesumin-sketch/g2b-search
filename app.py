"""나라장터 입찰공고·사전규격 통합검색 Streamlit 앱."""
import html
import io
import os
from datetime import datetime
from urllib.parse import urlparse, quote

import pandas as pd
import streamlit as st
from g2b_api import G2BError, search as search_bids
from prespec_api import search as search_specs

G2B_HOME = 'https://www.g2b.go.kr/'
st.set_page_config(page_title='나라장터 통합검색',page_icon='🔎',layout='wide')
st.title('🔎 나라장터 통합검색')
st.caption('입찰공고와 사전규격을 검색하고 공식 나라장터 페이지로 이동할 수 있습니다.')
st.link_button('🏛️ 나라장터 공식 홈페이지 바로가기 ↗',G2B_HOME,help='나라장터 메인화면으로 이동합니다. 공식 사이트의 상단 메뉴를 사용할 수 있습니다.')

def secret(name):
    value = os.environ.get(name,'').strip()
    if value: return value
    try: return str(st.secrets.get(name,'')).strip()
    except (FileNotFoundError,KeyError): return ''

bid_key=secret('G2B_API_KEY')
spec_key=secret('G2B_PRESPEC_API_KEY') or bid_key
if not bid_key:
    st.error('API 인증키가 없습니다. Streamlit 앱 설정 → Secrets에 G2B_API_KEY를 등록하세요.')
    st.stop()

mode=st.radio('검색할 자료', ['입찰공고','사전규격'], horizontal=True)
with st.form('search_form'):
    keyword_text=st.text_input('검색 키워드',placeholder='예: 산학협력, 교육, 연구용역',help='쉼표 또는 줄바꿈으로 구분하세요.')
    left,right=st.columns(2)
    with left: days=st.number_input('검색 기간 (최근 일수)',min_value=1,max_value=365,value=30)
    with right: kinds=st.multiselect('업무구분',['용역','물품','공사','외자'],default=['용역','물품','공사'])
    include_closed=st.checkbox('마감된 공고도 포함',value=False,disabled=mode!='입찰공고')
    submit=st.form_submit_button('🔍 검색하기',type='primary',use_container_width=True)

if submit:
    keywords=list(dict.fromkeys(k.strip() for k in keyword_text.replace('\n',',').split(',') if k.strip()))
    if not keywords: st.warning('검색 키워드를 입력하세요.')
    elif not kinds: st.warning('업무구분을 하나 이상 선택하세요.')
    elif len(keywords)>10: st.warning('키워드는 최대 10개까지 입력할 수 있습니다.')
    else:
        frames=[];errors=[]
        progress=st.progress(0,text='검색을 시작합니다...')
        for idx,kw in enumerate(keywords):
            try:
                if mode=='입찰공고': frame=search_bids(kw,kinds,int(days),bid_key,include_closed=include_closed)
                else: frame=search_specs(kw,kinds,int(days),spec_key)
                if not frame.empty: frames.append(frame)
            except G2BError as exc:
                errors.append(f'{kw}: {exc}')
            progress.progress((idx+1)/len(keywords),text=f'{idx+1}/{len(keywords)} 키워드 완료')
        st.session_state['result']=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()
        st.session_state['mode']=mode
        st.session_state['errors']=errors
        st.session_state['page']=1


def official_url(value):
    if not isinstance(value,str): return None
    value=value.strip()
    parsed=urlparse(value)
    host=(parsed.hostname or '').lower()
    if parsed.scheme!='https' or not (host=='g2b.go.kr' or host.endswith('.g2b.go.kr')): return None
    return value


def show(value):
    try:
        if pd.isna(value): return '-'
    except (TypeError,ValueError): return '-'
    return str(value).strip() or '-'

if st.session_state.get('mode') == mode:
    for error in st.session_state.get('errors',[]): st.error(error)
    df=st.session_state['result']
    if df.empty:
        st.info('검색 결과가 없습니다. 사전규격 검색이 실패했다면 별도 API 활용신청 승인 여부도 확인해 주세요.')
    else:
        st.metric(f'{mode} 검색 결과',f'{len(df):,}건')
        st.caption('사전규격명은 클릭해 상세정보를 확인할 수 있습니다. 공식 상세주소가 제공되면 나라장터 원문이 새 탭으로 열립니다.')
        per_page=20
        max_page=(len(df)+per_page-1)//per_page
        page=st.number_input('페이지',min_value=1,max_value=max_page,value=min(st.session_state.get('page',1),max_page),step=1)
        st.session_state['page']=page
        for _,item in df.iloc[(page-1)*per_page:page*per_page].iterrows():
            title=show(item.get('공고명') if mode=='입찰공고' else item.get('사전규격명'))
            url=official_url(item.get('공고상세URL'))
            with st.container(border=True):
                if url:
                    st.markdown(f'<a href="{html.escape(url,quote=True)}" target="_blank" rel="noopener noreferrer" style="font-size:1.08rem;font-weight:650;text-decoration:none">{html.escape(title)} ↗</a>',unsafe_allow_html=True)
                elif mode == '사전규격':
                    # 공식 상세 URL이 없는 API 항목은 잘못된 URL을 만들어 내지 않고
                    # 해당 항목의 세부 정보를 앱에서 펼쳐 보여준다.
                    with st.expander(f'📄 {title}  ·  상세정보 보기', expanded=False):
                        st.write(f"**사전규격등록번호:** {show(item.get('사전규격등록번호'))}")
                        st.write(f"**수요기관:** {show(item.get('수요기관'))}")
                        st.write(f"**등록일시:** {show(item.get('등록일시'))}")
                        st.write(f"**의견등록마감일시:** {show(item.get('의견등록마감일시'))}")
                        st.info('이 공고는 API에서 공식 상세페이지 주소를 제공하지 않습니다. 나라장터에서 아래 등록번호로 검색하면 원문을 찾을 수 있습니다.')
                        st.link_button('🏛️ 나라장터에서 확인 ↗', G2B_HOME)
                else:
                    st.markdown(f'**{html.escape(title)}**')
                    st.caption('이 항목은 공식 API에서 확인 가능한 원문 상세주소가 제공되지 않았습니다.')
                if mode=='입찰공고':
                    cols=['업무구분','공고기관','수요기관','입찰마감일시','공고번호']
                else:
                    cols=['업무구분','수요기관','등록일시','의견등록마감일시','사전규격등록번호']
                st.caption('  |  '.join(f'{key}: {show(item.get(key))}' for key in cols))
                amount=item.get('배정예산')
                if pd.notna(amount):
                    try: st.caption(f'배정예산: {float(amount):,.0f}원')
                    except (ValueError,TypeError): pass
        with st.expander('📥 선택 기능: 엑셀 다운로드'):
            output=io.BytesIO()
            with pd.ExcelWriter(output,engine='openpyxl') as writer:
                df.to_excel(writer,sheet_name=mode,index=False)
                ws=writer.sheets[mode]
                ws.freeze_panes='A2'
                ws.auto_filter.ref=ws.dimensions
                for col in ws.columns:
                    ws.column_dimensions[col[0].column_letter].width=min(50,max(14,max(len(str(c.value or '')) for c in list(col)[:200])+2))
            st.download_button('엑셀 다운로드',output.getvalue(),file_name=f'{mode}_{datetime.now():%Y%m%d_%H%M}.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
else:
    st.info(f'{mode} 검색 조건을 입력하고 검색하기를 눌러 주세요.')

st.divider()
st.caption('공식 나라장터 사이트와 별도로 운영되는 검색 도구입니다. 나라장터 메뉴는 공식 홈페이지에서 이용할 수 있습니다.')
