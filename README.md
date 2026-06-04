# 서울 시영주차장 실시간 주차 지도 - Flask 버전

이 압축파일은 API 키가 들어간 `.env` 파일을 포함하고 있습니다.

## 실행 방법

1. 압축을 풉니다.
2. `start.bat`을 더블클릭합니다.
3. 브라우저에서 아래 주소로 접속합니다.

```text
http://127.0.0.1:5000
```

## 직접 실행하는 방법

명령 프롬프트에서 압축 푼 폴더로 이동한 뒤 실행합니다.

```bash
pip install -r requirements.txt
python app.py
```

## 최신화 방식

화면은 Flask 서버의 `/api/parkings` 주소에서 서울시 API 최신 데이터를 받아옵니다.

```js
setInterval(loadLatestParkingData, 60000);
```

위 코드 때문에 60초마다 자동으로 최신 주차대수를 다시 불러옵니다.

## 포함 파일

```text
app.py
.env
.env.example
requirements.txt
start.bat
templates/index.html
README.md
```

## 주의

이 프로젝트에는 실제 API 키가 들어간 `.env` 파일이 포함되어 있으므로, 다른 사람에게 공유할 때는 `.env` 파일을 삭제하거나 키를 지우세요.

## PC를 꺼도 24시간 접속 (Render 무료 배포)

PC 전원 없이 항상 접속되게 하려면 클라우드에 배포합니다. (git 설치 없이 GitHub 웹 업로드로 가능)

### 1) GitHub에 코드 올리기
1. https://github.com 가입/로그인 → `New repository` → 이름 입력 → `Create`.
2. 새 저장소 화면에서 `uploading an existing file` 클릭.
3. 폴더 안의 파일을 드래그해서 업로드. **`.env`는 절대 올리지 마세요.**
   - 올릴 파일: `app.py`, `requirements.txt`, `render.yaml`, `.gitignore`, `start.bat`, `templates/index.html`, `README.md`, `.env.example`
4. `Commit changes`.

### 2) Render에서 배포
1. https://render.com 가입(GitHub 계정으로 로그인 가능).
2. `New +` → `Web Service` → 위 GitHub 저장소 연결.
3. 설정값 (대부분 자동 인식됨):
   - Runtime: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - Instance Type: `Free`
4. `Environment` 탭에서 환경변수 추가:
   - Key: `SEOUL_API_KEY`, Value: (본인 서울시 API 키)
5. `Create Web Service` → 빌드 완료 후 `https://<이름>.onrender.com` 주소가 생깁니다.

이 주소는 PC를 꺼도 어디서나 접속되며 https라 휴대폰 GPS도 동작합니다.

### 참고
- 무료 플랜은 일정 시간 접속이 없으면 잠들었다가, 다시 접속하면 깨어나는 데 30~60초 정도 걸립니다(첫 접속만 느림).
- `.env`는 올리지 않으므로, 키는 반드시 Render의 환경변수로 등록해야 합니다.