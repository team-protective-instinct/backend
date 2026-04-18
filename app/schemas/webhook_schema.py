from typing import Any, cast
from pydantic import BaseModel, Field, ConfigDict


class LogEntry(BaseModel):
    """웹 서버 / WAF 에서 수집된 단일 로그 엔트리"""

    timestamp: str = Field(
        ...,
        description="로그 발생 시각 (ISO-8601 / 자유 형식)",
        examples=["2026-04-14T10:23:45+09:00"],
    )
    source_ip: str = Field(
        ...,
        description="요청 발신 IP 주소",
        examples=["103.22.1.5"],
    )
    method: str = Field(
        ...,
        description="HTTP 메서드",
        examples=["GET"],
    )
    uri: str = Field(
        ...,
        description="요청 URI (쿼리스트링 포함)",
        examples=["/login.php?user=admin' OR 1=1 --"],
    )
    user_agent: str = Field(
        default="",
        description="User-Agent 헤더",
        examples=["Mozilla/5.0"],
    )
    status_code: int | None = Field(
        default=None,
        description="HTTP 응답 상태 코드",
        examples=[200, 403],
    )
    body: str | None = Field(
        default=None,
        description="요청 바디 (POST 데이터 등)",
        examples=["username=admin&password=1234"],
    )
    rule_id: str | None = Field(
        default=None,
        description="WAF/IDS 룰 ID (탐지 룰이 있는 경우)",
        examples=["942100"],
    )
    rule_message: str | None = Field(
        default=None,
        description="WAF/IDS 룰 설명 메시지",
        examples=["SQL Injection Attack Detected"],
    )


# ── 더미 데이터: OpenAPI docs 에서 버튼 하나로 바로 테스트 ────────

_DUMMY_LOGS = [
    {
        "timestamp": "2026-04-14T10:23:45+09:00",
        "source_ip": "103.22.1.5",
        "method": "GET",
        "uri": "/login.php?user=admin' OR 1=1 --",
        "user_agent": "Mozilla/5.0",
        "status_code": 403,
        "body": None,
        "rule_id": "942100",
        "rule_message": "SQL Injection Attack Detected via libinjection",
    },
    {
        "timestamp": "2026-04-14T10:23:47+09:00",
        "source_ip": "103.22.1.5",
        "method": "GET",
        "uri": "/admin/config.php?id=1 UNION SELECT username,password FROM users--",
        "user_agent": "Mozilla/5.0",
        "status_code": 403,
        "body": None,
        "rule_id": "942260",
        "rule_message": "SQL Injection Attack: UNION query detected",
    },
]


class WebhookAlertRequest(BaseModel):
    """
    Webhook 알림 요청 본문.
    ElastAlert2·ModSecurity 등 외부 시스템이 전송하는 알림 페이로드를 수용합니다.
    """

    alert_name: str = Field(
        default="sql_injection_detected",
        description="알림 규칙 이름",
        examples=["sql_injection_detected"],
    )
    severity: str = Field(
        default="high",
        description="알림 심각도 (critical / high / medium / low / info)",
        examples=["high"],
    )
    logs: list[LogEntry] = Field(
        ...,
        description="분석 대상 로그 목록 (1건 이상)",
        min_length=1,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "alert_name": "sql_injection_detected",
                    "severity": "high",
                    "logs": cast(Any, _DUMMY_LOGS),
                }
            ]
        }
    )
