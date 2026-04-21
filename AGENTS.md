# AI Agent Instructions for this Project

## Python Environment & Package Management
- 이 프로젝트는 `uv`를 패키지 매니저로 사용합니다.
- **에이전트 제약 사항:** 에이전트는 터미널에서 직접 `uv` 관련 명령어(`uv sync`, `uv add`, `uv pip install` 등)를 실행하지 마세요.
- **사용자 가이드:** 패키지 추가나 환경 동기화가 필요한 경우, 에이전트는 수행할 명령어만 텍스트로 제안하고 사용자에게 실행을 요청하세요.
- **인터프리터 경로:** 항상 프로젝트 루트의 `.venv/bin/python`을 사용하도록 코드를 작성하세요.