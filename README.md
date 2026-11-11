# 나라장터 입찰공고 검색 — Streamlit 배포용

## 구성
- `app.py`: 검색 화면, 결과표, 엑셀 다운로드
- `g2b_api.py`: 원본 검색 로직 기반 (기본 마감공고 제외 / 체크 시 포함)
- `requirements.txt`: Python 패키지 목록
- `.gitignore`: API 인증키 등 비밀 파일 업로드 방지

## GitHub에 업로드
1. GitHub → New repository → `g2b-search` 생성
2. 이 폴더 **안의** `app.py`, `g2b_api.py`, `requirements.txt`, `README.md`, `.gitignore` 업로드 후 Commit changes
3. 인증키는 **절대 코드나 GitHub 파일에 넣지 마세요.**

## Streamlit Community Cloud 배포
1. https://share.streamlit.io/ 에서 GitHub로 로그인
2. Create app → GitHub 저장소 선택
3. Main file path: `app.py`
4. Advanced settings → Secrets 에 다음 형식으로 설정:

```toml
G2B_API_KEY = "여기에_현재_인증키_입력"
```

5. Deploy 클릭 → 발급된 `*.streamlit.app` 주소 접속

**참고:** 인증키를 바꿀 필요는 없지만, 기존 업로드 코드에 키가 포함되어 있었으므로 외부에 공개된 적이 있다면 재발급을 권장합니다. GitHub 공개 저장소에는 이 배포용 파일만 올리세요. 웹 앱을 공개하면 외부인이 API 호출을 유발할 수 있으니 필요하면 앱 접근 제한을 설정하세요.

## 로컬 실행
```bash
pip install -r requirements.txt
# 환경변수 G2B_API_KEY 설정 후
streamlit run app.py
```

실제 API 연결은 인증키·공공데이터포털 서비스 상태에 따라 달라집니다.
