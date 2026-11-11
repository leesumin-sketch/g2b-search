"""나라장터 입찰공고 검색: 공고명 클릭 시 나라장터 원문 새 탭 열기."""
import html
import io
import os
from datetime import datetime
from urllib.parse import urlparse

import pandas as pd
import streamlit as st
from g2b_api import G2BError, search

st.set_page_config(page_title="나라장터 입찰공고 검색", page_icon="🔎", layout="wide")
st.title("🔎 나라장터 입찰공고 검색")
st.caption("공고명을 클릭하면 나라장터 원문을 새 탭에서 엽니다. 엑셀 다운로드는 선택 사항입니다.")

api_key = os.environ.get("G2B_API_KEY", "").strip()
if not api_key:
    try:
        api_key = str(st.secrets.get("G2B_API_KEY", "")).strip()
    except (FileNotFoundError, KeyError):
        pass
if not api_key:
    st.error("API 키가 설정되지 않았습니다. Streamlit 앱 설정 → Secrets에 G2B_API_KEY를 등록하세요.")
    st.stop()

with st.form("search_form"):
    keywords_text = st.text_input("검색 키워드", placeholder="예: 산학협력, 교육, 연구용역", help="쉼표 또는 줄바꿈으로 키워드를 구분하세요.")
    col1, col2 = st.columns(2)
    with col1:
        days = st.number_input("검색 기간 (최근 일수)", min_value=1, max_value=365, value=30)
    with col2:
        kinds = st.multiselect("업무구분", ["용역", "물품", "공사", "외자"], default=["용역", "물품", "공사"])
    include_closed = st.checkbox("마감된 공고도 포함", value=False)
    submitted = st.form_submit_button("입찰공고 검색", type="primary", use_container_width=True)

if submitted:
    keywords = list(dict.fromkeys(k.strip() for k in keywords_text.replace("\n", ",").split(",") if k.strip()))
    if not keywords:
        st.warning("검색 키워드를 입력하세요.")
    elif not kinds:
        st.warning("업무구분을 하나 이상 선택하세요.")
    elif len(keywords) > 10:
        st.warning("키워드는 한 번에 10개까지 검색할 수 있습니다.")
    else:
        results, errors = [], []
        progress = st.progress(0, text="검색을 시작합니다...")
        for i, keyword in enumerate(keywords):
            try:
                frame = search(keyword, kinds, int(days), api_key, include_closed=include_closed)
                if not frame.empty:
                    results.append(frame)
            except G2BError:
                errors.append(f"「{keyword}」 검색 실패: API 인증 또는 연결 상태를 확인하세요.")
            progress.progress((i + 1) / len(keywords), text=f"{i + 1}/{len(keywords)} 키워드 검색 완료")
        st.session_state["results"] = pd.concat(results, ignore_index=True) if results else pd.DataFrame()
        st.session_state["errors"] = errors
        st.session_state["searched"] = True
        st.session_state["page"] = 1

def official_url(value):
    """API가 반환한 나라장터 주소만 링크로 사용합니다."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (host == "g2b.go.kr" or host.endswith(".g2b.go.kr")):
        return None
    return value

def display(value, fallback="-"):
    if pd.isna(value) or str(value).strip() == "":
        return fallback
    return str(value)

if st.session_state.get("searched"):
    for message in st.session_state.get("errors", []):
        st.error(message)
    df = st.session_state["results"]
    if df.empty:
        st.info("조회된 입찰공고가 없습니다.")
    else:
        st.metric("검색 결과", f"{len(df):,}건")
        st.caption("공고명 클릭 → 나라장터 상세 공고 새 탭 열기 (원문 주소가 없는 공고는 링크가 표시되지 않습니다).")
        per_page = 20
        total_pages = (len(df) + per_page - 1) // per_page
        page = st.number_input("페이지", min_value=1, max_value=total_pages, value=min(st.session_state.get("page", 1), total_pages), step=1)
        st.session_state["page"] = page
        view = df.iloc[(page - 1) * per_page:page * per_page]
        for _, row in view.iterrows():
            name = html.escape(display(row.get("공고명"), "제목 없는 공고"))
            url = official_url(row.get("공고상세URL"))
            with st.container(border=True):
                if url:
                    st.markdown(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer" style="font-size:1.1rem;font-weight:650;text-decoration:none;">{name} ↗</a>', unsafe_allow_html=True)
                else:
                    st.markdown(f"**{name}**")
                    st.caption("나라장터 원문 링크가 제공되지 않은 공고입니다.")
                meta = [
                    f"업무구분: {display(row.get('업무구분'))}",
                    f"공고기관: {display(row.get('공고기관'))}",
                    f"수요기관: {display(row.get('수요기관'))}",
                    f"마감일: {display(row.get('입찰마감일시'))}",
                    f"공고번호: {display(row.get('공고번호'))}",
                ]
                st.caption("  |  ".join(meta))
                amount = row.get("배정예산")
                if pd.notna(amount):
                    try:
                        st.caption(f"배정예산: {float(amount):,.0f}원")
                    except (ValueError, TypeError):
                        pass
        with st.expander("선택 기능: 검색 결과 엑셀 다운로드"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="입찰공고", index=False)
                ws = writer.sheets["입찰공고"]
                ws.freeze_panes = "A2"
                ws.auto_filter.ref = ws.dimensions
                for column in ws.columns:
                    letter = column[0].column_letter
                    ws.column_dimensions[letter].width = min(48, max(14, max(len(str(c.value or "")) for c in list(column)[:200]) + 2))
            st.download_button("📥 엑셀 다운로드", data=output.getvalue(), file_name=f"입찰공고_{datetime.now():%Y%m%d_%H%M}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.divider()
st.caption("데이터는 공공데이터포털 조달청 API 기준이며, 별도 데이터베이스에 저장하지 않습니다. 원문 링크는 API에서 제공된 주소만 사용합니다.")
