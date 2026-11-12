"""나라장터 사전규격 검색. API 응답 필드 차이를 고려해 원본을 보존한다."""
from datetime import datetime, timedelta
import pandas as pd
from g2b_api import G2BError

BASE = 'https://apis.data.go.kr/1230000/ao/HrcspSsstndrdInfoService'
OPS = {
    '용역':'getPublicPrcureThngInfoServcPPSSrch',
    '물품':'getPublicPrcureThngInfoThngPPSSrch',
    '공사':'getPublicPrcureThngInfoCnstwkPPSSrch',
    '외자':'getPublicPrcureThngInfoFrgcptPPSSrch',
}
# 공식 API에서 사전규격별 전용 상세 URL이 반환될 경우에만 상세 바로가기를 노출한다.
NAME_KEYS = ('prdctNm','prdctClsfcNoNm','bsnsNm','specNm','bidNtceNm','prcrmntNm','thngNm')
ID_KEYS = ('bfSpecRgstNo','specRgstNo','prcrmntReqNo','publicPrcureNo')
DATE_KEYS = ('rgstDt','bfSpecRgstDt','specRgstDt','opninRgstDt','publicPrcureDt')
ORG_KEYS = ('dminsttNm','ntceInsttNm','orderInsttNm','insttNm')
AMOUNT_KEYS = ('asignBdgtAmt','bdgtAmt','presmptPrce')
URL_KEYS = ('bfSpecDtlUrl','specDtlUrl','detailUrl','publicPrcureDtlUrl','bidNtceDtlUrl')
CLOSE_KEYS = ('opninRgstClseDt','opnnClseDt','opinionClseDt')


def first(item, keys):
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return value
    return ''


def fetch(kind, start, end, api_key, session=None, max_pages=40):
    # 사전규격 검색조건 API는 업무별로 분리되어 있다.
    # 날짜 조회 조건은 서버에 전달하고, 키워드는 결과에 다시 적용한다.
    from g2b_api import call
    page = 1
    result = []
    while page <= max_pages:
        body = call(OPS[kind], {
            'pageNo':page, 'numOfRows':100, 'inqryDiv':1,
            'inqryBgnDt':start.strftime('%Y%m%d%H%M'),
            'inqryEndDt':end.strftime('%Y%m%d%H%M'),
        }, api_key, session=session, base_url=BASE)
        got = body.get('items') or []
        if isinstance(got, dict): got = got.get('item',got)
        if isinstance(got, dict): got = [got]
        if not isinstance(got, list): got=[]
        result.extend(x for x in got if isinstance(x,dict))
        total = int(body.get('totalCount') or 0)
        if not got or page * 100 >= total:
            return result
        page += 1
    raise G2BError('사전규격 검색 결과가 너무 많습니다. 검색 기간을 줄여 다시 조회해 주세요.')


def search(keyword, kinds, days, api_key, now=None, session=None):
    end = now or datetime.now()
    start = end - timedelta(days=days)
    rows = []
    for kind in kinds:
        if kind not in OPS: raise ValueError('지원하지 않는 업무구분입니다.')
        current = start
        while current < end:
            stop = min(current + timedelta(days=6),end)
            for item in fetch(kind,current,stop,api_key,session=session):
                # 원본 필드의 제목 외에도 검색을 허용한다.
                title = str(first(item,NAME_KEYS))
                if keyword.casefold() not in title.casefold():
                    continue
                rows.append({
                    '업무구분':kind,'사전규격명':title,
                    '사전규격등록번호':first(item,ID_KEYS),
                    '등록일시':first(item,DATE_KEYS),
                    '수요기관':first(item,ORG_KEYS),
                    '배정예산':first(item,AMOUNT_KEYS),
                    '의견등록마감일시':first(item,CLOSE_KEYS),
                    '공고상세URL':first(item,URL_KEYS),
                })
            current=stop
    df=pd.DataFrame(rows)
    if df.empty: return df
    df.insert(0,'검색키워드',keyword)
    df=df.drop_duplicates(subset=['업무구분','사전규격등록번호','사전규격명'])
    df['배정예산']=pd.to_numeric(df['배정예산'],errors='coerce')
    return df.sort_values('등록일시',ascending=False)
