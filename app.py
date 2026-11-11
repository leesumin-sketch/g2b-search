import io
import os
from datetime import datetime
import pandas as pd
import streamlit as st
from g2b_api import G2BError, search

st.set_page_config(page_title='나라장터 입찰공고 검색', page_icon='🔎', layout='wide')
st.title('🔎 나라장터 입찰공고 검색')
st.caption('공공데이터포털 · 조달청 입찰공고정보서비스 | 검색 결과를 엑셀로 내려받을 수 있습니다.')

# Streamlit Community Cloud의 Secrets 또는 로컬 환경변수에서만 인증키를 읽습니다.
api_key = os.environ.get('G2B_API_KEY', '').strip()
if not api_key:
    try:
        api_key = str(st.secrets.get('G2B_API_KEY', '')).strip()
    except (FileNotFoundError, KeyError):
        pass
if not api_key:
    st.error('API 키가 설정되지 않았습니다. 배포 서비스의 Secrets에 G2B_API_KEY를 등록하세요.')
    st.stop()

with st.form('search_form'):
    keywords_text = st.text_input('검색 키워드', placeholder='예: 산학협력, 교육, 연구용역', help='쉼표 또는 줄바꿈으로 여러 키워드를 구분하세요.')
    col1, col2 = st.columns(2)
    with col1:
        days = st.number_input('검색 기간 (최근 일수)', min_value=1, max_value=365, value=30, step=1)
    with col2:
        kinds = st.multiselect('업무구분', ['용역','물품','공사','외자'], default=['용역','물품','공사'])
    include_closed = st.checkbox('마감된 공고도 포함', value=False, help='기본값은 입찰마감일시가 지난 공고를 제외합니다.')
    submitted = st.form_submit_button('입찰공고 검색', type='primary', use_container_width=True)

if submitted:
    keywords = list(dict.fromkeys(k.strip() for k in keywords_text.replace('\n', ',').split(',') if k.strip()))
    if not keywords:
        st.warning('검색 키워드를 입력하세요.')
    elif not kinds:
        st.warning('업무구분을 하나 이상 선택하세요.')
    elif len(keywords) > 10:
        st.warning('키워드는 한 번에 10개까지 검색할 수 있습니다.')
    else:
        results, errors = [], []
        progress = st.progress(0, text='검색을 시작합니다...')
        for i, keyword in enumerate(keywords):
            try:
                frame = search(keyword, kinds, int(days), api_key, include_closed=include_closed)
                if not frame.empty:
                    results.append(frame)
            except G2BError:
                errors.append(f'「{keyword}」 검색 실패: API 인증 또는 연결 상태를 확인하세요.')
            progress.progress((i+1)/len(keywords), text=f'{i+1}/{len(keywords)} 키워드 검색 완료')
        st.session_state['results'] = pd.concat(results, ignore_index=True) if results else pd.DataFrame()
        st.session_state['errors'] = errors
        st.session_state['searched'] = True

if st.session_state.get('searched'):
    for message in st.session_state.get('errors', []):
        st.error(message)
    df = st.session_state['results']
    if df.empty:
        st.info('조회된 입찰공고가 없습니다.')
    else:
        st.metric('검색 결과', f'{len(df):,}건')
        st.dataframe(df, use_container_width=True, hide_index=True, column_config={'공고상세URL':st.column_config.LinkColumn('공고 상세보기')})
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='입찰공고', index=False)
            ws = writer.sheets['입찰공고']
            ws.freeze_panes = 'A2'
            ws.auto_filter.ref = ws.dimensions
            for column in ws.columns:
                letter = column[0].column_letter
                ws.column_dimensions[letter].width = min(48, max(14, max(len(str(c.value or '')) for c in list(column)[:200]) + 2))
        st.download_button('📥 검색 결과 엑셀 다운로드', data=output.getvalue(), file_name=f'입찰공고_{datetime.now():%Y%m%d_%H%M}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', type='primary')

st.divider()
st.caption('공고 데이터는 공공데이터포털 API 응답 기준입니다. 검색 결과는 별도 서버 DB에 저장하지 않습니다.')
