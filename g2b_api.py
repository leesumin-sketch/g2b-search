"""나라장터 입찰공고 API 조회 로직. 인증키는 환경변수로만 주입."""
import os
import time
from datetime import datetime, timedelta
import pandas as pd
import requests

BASE = 'https://apis.data.go.kr/1230000/ad/BidPublicInfoService02'
OPS = {'용역':'getBidPblancListInfoServcPPSSrch02','물품':'getBidPblancListInfoThngPPSSrch02','공사':'getBidPblancListInfoCnstwkPPSSrch02','외자':'getBidPblancListInfoFrgcptPPSSrch02'}
COLS = {'bidNtceNo':'공고번호','bidNtceOrd':'차수','bidNtceNm':'공고명','ntceInsttNm':'공고기관','dminsttNm':'수요기관','cntrctCnclsMthdNm':'계약방법','bidNtceDt':'공고일시','bidClseDt':'입찰마감일시','opengDt':'개찰일시','asignBdgtAmt':'배정예산','presmptPrce':'추정가격','bidNtceDtlUrl':'공고상세URL'}
ROWS = 100
CHUNK_DAYS = 6

class G2BError(Exception):
    pass

def call(op, params, api_key, session=None, retries=3, base_url=None):
    if not api_key:
        raise G2BError('API 인증키가 설정되지 않았습니다. 배포 환경의 G2B_API_KEY를 확인하세요.')
    client = session or requests
    payload = {'serviceKey': api_key, 'type':'json', **params}
    for attempt in range(retries):
        try:
            response = client.get(f'{base_url or BASE}/{op}', params=payload, timeout=30)
            if response.status_code in (401,403):
                raise G2BError('API 인증 오류: 공공데이터포털 활용 승인 및 인증키를 확인하세요.')
            if response.status_code in (429,500,502,503,504) and attempt < retries-1:
                time.sleep(min(2**attempt, 4))
                continue
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            # requests 예외에는 URL 쿼리스트링(인증키)이 포함될 수 있으므로 원문을 노출하지 않음
            raise G2BError('API 연결 또는 응답 처리에 실패했습니다. 잠시 후 다시 시도하세요.') from None
        if not isinstance(data, dict):
            raise G2BError('API 응답 형식이 올바르지 않습니다.')
        resp = data.get('response')
        if not isinstance(resp, dict):
            raise G2BError('API에서 정상적인 응답을 받지 못했습니다. 인증 및 서비스 상태를 확인하세요.')
        head = resp.get('header') or {}
        if str(head.get('resultCode', '00')).zfill(2) != '00':
            raise G2BError('API 조회 오류가 발생했습니다. 서비스 상태 또는 조회 조건을 확인하세요.')
        body = resp.get('body') or {}
        return body if isinstance(body, dict) else {}
    raise G2BError('API 응답 실패')

def fetch(op, keyword, start, end, api_key, session=None):
    items, page = [], 1
    while True:
        body = call(op, {'pageNo':page,'numOfRows':ROWS,'inqryDiv':1,'inqryBgnDt':start.strftime('%Y%m%d%H%M'),'inqryEndDt':end.strftime('%Y%m%d%H%M'),'bidNtceNm':keyword}, api_key, session=session)
        got = body.get('items') or []
        if isinstance(got, dict):
            got = got.get('item', got)
        if isinstance(got, dict):
            got = [got]
        if not isinstance(got, list):
            got = []
        items.extend(x for x in got if isinstance(x, dict))
        total = int(body.get('totalCount') or 0)
        if not got or page*ROWS >= total:
            return items
        page += 1

def search(keyword, kinds, days, api_key, include_closed=False, now=None, session=None):
    end = now or datetime.now()
    begin = end - timedelta(days=days)
    rows = []
    for kind in kinds:
        if kind not in OPS:
            raise ValueError('지원하지 않는 업무구분입니다.')
        start = begin
        while start < end:
            stop = min(start + timedelta(days=CHUNK_DAYS), end)
            for item in fetch(OPS[kind], keyword, start, stop, api_key, session=session):
                rows.append({**item, '업무구분':kind})
            start = stop
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    keep = ['업무구분'] + [c for c in COLS if c in df.columns]
    df = df[keep].rename(columns=COLS)
    dedup = [c for c in ('업무구분','공고번호','차수') if c in df.columns]
    if dedup:
        df = df.drop_duplicates(subset=dedup)
    for col in ('배정예산','추정가격'):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    if not include_closed and '입찰마감일시' in df.columns:
        # API 응답은 YYYY-MM-DD HH:MM:SS 또는 YYYYMMDDHHMM 형식일 수 있습니다.
        due_text = df['입찰마감일시'].astype('string').str.strip()
        compact = due_text.str.fullmatch(r'\d{12}|\d{14}', na=False)
        parsed = pd.to_datetime(due_text.where(~compact), errors='coerce')
        parsed_compact = pd.to_datetime(due_text.where(compact), format='%Y%m%d%H%M%S', errors='coerce')
        parsed_12 = pd.to_datetime(due_text.where(due_text.str.fullmatch(r'\d{12}', na=False)), format='%Y%m%d%H%M', errors='coerce')
        due = parsed.fillna(parsed_compact).fillna(parsed_12)
        df = df[due.isna() | (due >= end)]
    df.insert(0, '검색키워드', keyword)
    return df.sort_values('공고일시', ascending=False) if '공고일시' in df.columns else df
