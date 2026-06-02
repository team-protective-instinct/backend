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

#### 주요 환경 변수

| 구분 | 환경 변수 | 설명 | 기본값/예시 |
| --- | --- | --- | --- |
| Database | `DB_USER` | PostgreSQL 사용자명 | `root` |
| Database | `DB_PASSWORD` | PostgreSQL 비밀번호 | 팀 내 공유값 입력 |
| Database | `DB_HOST` | PostgreSQL 호스트 | 로컬 실행: `localhost`, Docker Compose 내부: `db` |
| Database | `DB_PORT` | PostgreSQL 포트 | `5432` |
| Database | `DB_NAME` | PostgreSQL 데이터베이스명 | `capstone` |
| LLM | `LLM_PROVIDER` | 사용할 LLM provider. `gemini`, `anthropic`, `openai` 중 하나 | `gemini` |
| LLM | `LLM_MODEL` | 사용할 모델명 | `gemini-3.1-pro` |
| LLM | `GOOGLE_API_KEY` | Gemini 및 RAG embedding 호출에 사용하는 API key | `your_google_api_key_here` |
| LLM | `ANTHROPIC_API_KEY` | Anthropic provider 사용 시 필요한 API key | `your_anthropic_api_key_here` |
| LLM | `OPENAI_API_KEY` | OpenAI provider 사용 시 필요한 API key | `your_openai_api_key_here` |
| RAG | `RAG_EMBEDDING_MODEL` | playbook chunk embedding 생성에 사용할 모델 | `gemini-embedding-001` |

> `.env`에는 API key, DB 비밀번호 같은 민감 정보가 포함됩니다. 실제 값이 들어간 `.env` 파일은 Git에 커밋하지 않습니다.

#### Elasticsearch MCP 로그 검색 설정

incident analyzer가 Elasticsearch MCP 서버를 통해 추가 로그를 조회할 수 있습니다. 기본값은 비활성화이며, 필요할 때만 켭니다.

```bash
ELASTICSEARCH_MCP_ENABLED=false
ELASTICSEARCH_MCP_URL=http://localhost:8085/mcp
ELASTICSEARCH_MCP_ALLOWED_INDEX_PATTERN=logstash-*
ELASTICSEARCH_MCP_SERVICE_FIELD=fields.service
ELASTICSEARCH_MCP_SERVICE_VALUE=dvwa-apache
ELASTICSEARCH_MCP_MAX_RESULTS=20
ELASTICSEARCH_MCP_MAX_WINDOW_MINUTES=30
ELASTICSEARCH_MCP_REQUEST_TIMEOUT_SECONDS=10
```

- `ELASTICSEARCH_MCP_ENABLED`: MCP 로그 검색 사용 여부
- `ELASTICSEARCH_MCP_URL`: MCP 서버 주소
- `ELASTICSEARCH_MCP_ALLOWED_INDEX_PATTERN`: 조회 허용 index pattern
- `ELASTICSEARCH_MCP_SERVICE_FIELD`: 서비스 필터를 적용할 필드
- `ELASTICSEARCH_MCP_SERVICE_VALUE`: 필터 값
- `ELASTICSEARCH_MCP_MAX_RESULTS`: 한 번에 반환할 최대 결과 수
- `ELASTICSEARCH_MCP_MAX_WINDOW_MINUTES`: 조회할 수 있는 최대 시간 범위
- `ELASTICSEARCH_MCP_REQUEST_TIMEOUT_SECONDS`: MCP 응답 대기 시간

#### Victim MCP 설정

response plan agent가 victim 시스템의 추가 컨텍스트를 조회할 수 있습니다. 기본값은 비활성화이며, 필요할 때만 켭니다.

```bash
VICTIM_MCP_ENABLED=false
VICTIM_MCP_URL=http://localhost:9001/mcp
VICTIM_MCP_REQUEST_TIMEOUT_SECONDS=10
VICTIM_MCP_MAX_RESULT_CHARS=6000
```

- `VICTIM_MCP_ENABLED`: Victim MCP 컨텍스트 조회 사용 여부
- `VICTIM_MCP_URL`: Victim MCP 서버 주소
- `VICTIM_MCP_REQUEST_TIMEOUT_SECONDS`: MCP 응답 대기 시간
- `VICTIM_MCP_MAX_RESULT_CHARS`: MCP 응답에서 사용할 최대 문자 수

### 5. 데이터베이스(PostgreSQL) 실행

프로젝트는 로컬 환경에서 **Docker Compose**를 이용해 PostgreSQL 및 `pgvector`를 실행합니다. 원활한 실행을 위해 PC에 [Docker Desktop](https://www.docker.com/products/docker-desktop/) 또는 Docker가 설치되어 있어야 합니다.

백그라운드에서 데이터베이스 컨테이너를 실행하려면 다음 명령어를 입력합니다:

```bash
docker compose up -d
```

> 💡 컨테이너를 중지하려면 `docker compose down`을 사용합니다. 볼륨 마운트 처리가 되어 있으므로 컨테이너를 중지 및 재생성해도 로컬 DB 데이터는 보존됩니다.

#### 전체 백엔드 스택 실행

`docker-compose.yml`에는 DB뿐 아니라 API 서버와 두 worker도 함께 정의되어 있습니다.

| 서비스 | 역할 | 포트/비고 |
| --- | --- | --- |
| `db` | PostgreSQL + pgvector 데이터베이스 | `${DB_PORT}:5432` |
| `api` | FastAPI 백엔드 서버 | `8000:8000` |
| `incident-worker` | 수집된 incident 로그를 AI로 분석 | 별도 포트 없음 |
| `response-plan-worker` | 정탐 incident의 대응 계획 생성 | 별도 포트 없음 |

전체 서비스를 한 번에 실행하려면 다음 명령어를 사용합니다.

```bash
docker compose up -d --build
```

실행 중인 컨테이너 상태를 확인합니다.

```bash
docker compose ps
```

로그를 확인합니다.

```bash
# 전체 로그
docker compose logs -f

# API 서버 로그만 확인
docker compose logs -f api

# worker 로그만 확인
docker compose logs -f incident-worker
docker compose logs -f response-plan-worker
```

전체 서비스를 중지하려면 다음 명령어를 사용합니다.

```bash
docker compose down
```

### 6. 로컬 서버 실행

동작 중인 데이터베이스를 포함해 모든 준비가 완료되었다면 서버를 실행합니다. `uv run` 명령어로 가상환경 내의 `uvicorn`을 바로 실행할 수 있습니다.

```bash
uv run uvicorn app.main:app --reload --reload-dir app
```

*(참고: `app.main:app`은 `app` 폴더 내 `main.py`의 `app` 인스턴스를 의미합니다.)*

같은 네트워크의 다른 기기도 FastAPI 서버에 접속할 수 있도록 하려면, `--host` 옵션을 추가하여 서버를 모든 인터페이스에서 수신하도록 설정할 수 있습니다:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app
```

서버가 실행되면, 브라우저를 열고 FastAPI의 자동 생성 API 문서 메인 화면인 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 에 접속하여 제대로 실행되었는지 확인합니다.

### 7. AI Worker 실행

웹훅으로 수신된 알림은 먼저 `incidents` 테이블에 저장되고, AI 분석은 별도 worker 프로세스에서 처리됩니다.

#### Incident Agent Worker

의심 로그를 분석해 정오탐을 판별합니다.

```bash
uv run python -m app.workers.incident_agent_worker
```

#### Response Plan Agent Worker

정탐으로 판별된 incident에 대해 대응 계획서를 생성합니다.

```bash
uv run python -m app.workers.response_plan_agent_worker
```

로컬 개발 시에는 API 서버와 두 worker를 각각 별도 터미널에서 실행합니다.

## 🗄️ 데이터베이스 마이그레이션

이 프로젝트는 SQLAlchemy 모델 변경 사항을 Alembic migration으로 관리합니다. 자세한 사용법은 [`migrations/README.md`](./migrations/README.md)를 참고하세요.

마이그레이션 명령어는 프로젝트 루트에서 실행합니다. 실행 전 `.env`의 DB 설정이 올바른지, PostgreSQL 컨테이너가 실행 중인지 확인합니다.

```bash
# 현재 DB에 적용된 migration 확인
uv run alembic current

# 아직 적용되지 않은 migration을 최신 버전까지 적용
uv run alembic upgrade head

# 모델 변경 사항을 기반으로 새 migration 생성
uv run alembic revision --autogenerate -m "add incident severity field"

# 직전 migration 한 단계 롤백
uv run alembic downgrade -1
```

새 migration을 만들었다면 `migrations/versions/`에 생성된 파일의 `upgrade()`와 `downgrade()` 내용을 반드시 직접 확인합니다. 특히 테이블/컬럼 삭제, 컬럼 rename, nullable 변경은 데이터 손실이 발생할 수 있으므로 팀원과 확인한 뒤 적용합니다.

## 📚 Playbook / RAG 인덱싱

`playbooks/` 디렉터리의 Markdown 대응 문서는 RAG 검색을 위해 DB의 vector table에 인덱싱할 수 있습니다.

먼저 dry-run으로 문서 로딩과 chunk 분할이 정상 동작하는지 확인합니다.

```bash
uv run python -m app.scripts.index_playbooks --dry-run
```

실제 embedding 생성 및 DB 저장을 수행하려면 dry-run 옵션을 제거합니다.

```bash
uv run python -m app.scripts.index_playbooks
```

자주 사용하는 옵션은 다음과 같습니다.

| 옵션 | 설명 | 기본값 |
| --- | --- | --- |
| `--playbooks-dir` | 인덱싱할 Markdown playbook 디렉터리 | `playbooks` |
| `--dry-run` | embedding 생성과 DB 저장 없이 로딩/chunk 분할만 확인 | 비활성화 |
| `--chunk-size` | chunk 최대 크기 | 코드 기본값 사용 |
| `--chunk-overlap` | chunk 간 중복 크기 | 코드 기본값 사용 |
| `--batch-size` | embedding/저장 처리 batch 크기 | `32` |
| `--limit` | 앞에서부터 N개 chunk만 인덱싱 | 제한 없음 |
| `--embedding-model` | embedding 생성 모델 | `RAG_EMBEDDING_MODEL` 기본값 |

예시:

```bash
# 처음 10개 chunk만 테스트 인덱싱
uv run python -m app.scripts.index_playbooks --limit 10

# 다른 디렉터리의 playbook 인덱싱
uv run python -m app.scripts.index_playbooks --playbooks-dir ./playbooks
```

RAG 인덱싱은 DB와 LLM embedding API를 사용합니다. 실행 전 PostgreSQL이 실행 중인지, `.env`의 `GOOGLE_API_KEY`와 `RAG_EMBEDDING_MODEL` 값이 올바른지 확인합니다.
