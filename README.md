# 나라장터 입찰공고 검색 (Streamlit 배포용)

## 기능
- 키워드(쉼표 구분), 검색 기간, 업무구분, 마감공고 포함 여부 검색
- 공고명을 클릭하면 API에서 제공한 **나라장터 원문 URL을 새 탭**으로 엽니다.
- 공고번호/기관/마감일/예산을 목록에서 확인
- 엑셀 다운로드는 접힌 선택 메뉴로 유지
- API 키는 소스코드에 저장하지 않음

## GitHub 업로드
1. ZIP 압축을 풉니다.
2. GitHub 저장소를 만든 뒤 `app.py`, `g2b_api.py`, `requirements.txt`, `.gitignore`, `README.md`를 업로드합니다.
3. **API 인증키나 `.streamlit/secrets.toml` 파일은 업로드하지 마세요.**

## Streamlit Community Cloud 배포
1. https://share.streamlit.io 에 로그인합니다.
2. Create app → GitHub 저장소 선택 → Main file path `app.py`.
3. Advanced settings → Secrets에 아래 내용을 등록합니다.

```toml
G2B_API_KEY = "본인의_공공데이터포털_API_키"
```

4. Deploy를 클릭합니다. 이미 배포한 앱이라면 GitHub 저장소에서 파일을 교체하면 재배포됩니다.

## 로컬 실행
```bash
pip install -r requirements.txt
# 환경변수 G2B_API_KEY를 설정한 뒤
streamlit run app.py
```

## 참고
- 링크는 API의 `bidNtceDtlUrl`을 사용하며, HTTPS 나라장터(`g2b.go.kr` 및 하위 도메인) 링크만 표시합니다.
- API가 URL을 제공하지 않거나 다른 도메인 URL을 제공하면 링크가 표시되지 않습니다.
- 실제 API 응답 및 나라장터 상세 페이지 이동은 배포 후 확인이 필요합니다.
- 공개 앱은 누구나 접근할 수 있으므로 사내 전용이면 별도 접근 제한을 구성하세요.
