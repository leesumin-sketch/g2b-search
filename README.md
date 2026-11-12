# 나라장터 입찰공고 + 사전규격 통합검색 (Streamlit)

## API 설정
- 사전규격 API Endpoint: `https://apis.data.go.kr/1230000/ao/HrcspSsstndrdInfoService`
- 입찰공고 API Endpoint: `https://apis.data.go.kr/1230000/ad/BidPublicInfoService02`
- 사전규격 API의 공식 검색조건별 오퍼레이션(용역/물품/공사/외자)을 사용합니다.
- 첨부한 인증키는 소스에 기록하지 않았습니다. 두 서비스에 동일한 인증키를 사용한다면 Streamlit Secrets에 **한 번만** 등록하세요.

```toml
G2B_API_KEY = "본인의_공공데이터포털_일반인증키"
```

- 사전규격에 별도 키를 사용해야 할 때만 `G2B_PRESPEC_API_KEY`를 추가합니다.
- 공공데이터포털에서 **사전규격정보서비스 활용신청이 승인**되었는지 확인하세요. 인증키가 같아도 서비스별 권한은 다를 수 있습니다.

## 기존 GitHub / Streamlit 업데이트
1. ZIP을 풀고 `app.py`, `g2b_api.py`, `prespec_api.py`, `requirements.txt`, `.gitignore`, `README.md`를 기존 GitHub 저장소 최상위에 업로드/교체합니다. ZIP 파일 자체를 올리지 마세요.
2. GitHub에서 **Commit changes**를 누릅니다.
3. 기존 Streamlit 앱이 변경사항을 반영하도록 기다린 뒤 새로고침합니다.
4. 앱에서 `사전규격`을 선택해 용역 등 소규모 검색으로 테스트합니다.
5. 오류가 있으면 Streamlit 앱 관리화면의 Logs를 확인하세요.

## 기능
- 입찰공고/사전규격 선택, 검색어(쉼표 구분), 기간, 업무구분 선택
- 공식 API가 상세 URL을 반환하는 항목은 제목 클릭으로 새 탭 이동
- 나라장터 메인 바로가기 버튼, 선택형 엑셀 다운로드
- 사전규격 API의 결과 제목 필드 및 날짜 조회조건은 실제 응답에 따라 추가 조정이 필요할 수 있습니다.

## 보안
- 실제 API 키를 GitHub, README, 코드, 오류 스크린샷에 올리지 마세요.
- 과거 키가 공개 저장소에 들어간 적이 있다면 소스에서 지우는 것만으로 기록이 없어지지 않으므로 재발급을 권장합니다.

## 검증 범위
- Python 문법 및 파일 구성 검증. 실제 API 호출과 Streamlit 배포는 인증키가 있는 환경에서 별도로 검증해야 합니다.
