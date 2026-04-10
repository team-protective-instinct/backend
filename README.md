# Capstone Backend

캡스톤디자인 프로젝트 백엔드 레포지토리입니다.
이 프로젝트는 **FastAPI** 프레임워크와 의존성 관리를 위한 **uv**를 사용합니다.

## 🚀 초기 환경 설정 가이드

### 1. Python 설치 확인
프로젝트는 **Python 3.11 이상**의 버전을 요구합니다. PC에 Python 3.11+ 버전이 설치되어 있는지 확인해 주세요.
```bash
python --version
# 또는
python3 --version
```

### 2. 패키지 매니저 `uv` 설치
이 프로젝트는 빠르고 가벼운 패키지 매니저인 `uv`를 사용합니다.

- **macOS / Linux**:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Windows**:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
> 설치 후 터미널을 다시 시작해야 할 수도 있습니다. `uv --version`으로 올바르게 설치되었는지 확인해 주세요.

### 3. 프로젝트 의존성 설치
프로젝트 폴더로 이동한 뒤, 패키지들을 설치합니다.
```bash
cd capstone-backend

# 가상환경(.venv) 자동 생성 및 의존성 패키지 설치
uv sync
```

### 4. 환경 변수 설정
데이터베이스 연동 등 중요한 설정값은 `.env` 파일을 통해 관리합니다. 환경 변수 템플릿 파일인 `.env.example`을 복사하여 `.env` 파일을 만들어주세요.

```bash
# .env.example 파일을 .env라는 이름으로 복사
cp .env.example .env
```
생성된 `.env` 파일을 열고, 팀 내 공유된 데이터베이스 정보 및 설정값을 입력합니다.

### 5. 로컬 서버 실행
모든 준비가 완료되었다면 서버를 실행합니다. `uv run` 명령어로 가상환경 내의 `uvicorn`을 바로 실행할 수 있습니다.

```bash
uv run uvicorn app.main:app --reload
```
*(참고: `app.main:app`은 `app` 폴더 내 `main.py`의 `app` 인스턴스를 의미합니다.)*

서버가 실행되면, 브라우저를 열고 FastAPI의 자동 생성 API 문서 메인 화면인 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 에 접속하여 제대로 실행되었는지 확인합니다.
