from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class Severity(str, Enum):
    """Severity levels of the incident""" # 사건의 심각도 수준

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Info"


IndicatorName = Literal[
    "repeated_detection",  # 반복 탐지
    "multi_event_correlation",  # 상관관계 분석
    "kill_chain_match",  # MITRE ATT&CK 킬체인 성립
    "non_standard_path_exec",  # 비표준 경로 실행
    "service_shell_spawn",  # 대화형 쉘 파생
    "privilege_escalation",  # 권한 상승
    "sensitive_resource_access",  # 민감 자원 접근
    "defense_evasion_persistence",  # 방어 회피 및 지속성 유지
    "approved_infra",  # 사전 승인 인프라 (FP 정황)
    "authorized_maintenance",  # 정상 유지보수 (FP 정황)
    "normal_business_pattern",  # 정상 패턴 (FP 정황)
]


class IndicatorEvaluation(BaseModel):
    """Evaluation of an individual indicator""" # 개별 지표 평가

    name: IndicatorName = Field(description="Select from the pre-defined indicator names") # 정의된 지표 명칭 중 선택
    is_detected: bool = Field(description="Whether this indicator was detected in the logs") # 해당 지표의 탐지 여부 (로그상 참/거짓)
    reasoning: str = Field(description="Logical reasoning for the detection with log evidence (1-2 sentences)") # 해당 판단에 대한 구체적 로그 근거 (1~2문장)


class FinalSecurityAnalysis(BaseModel):
    """Final decision of the threat analysis (Structured Output)""" # 정오탐 판별 최종 결과

    # Step 1: List only relevant indicators (Token Efficiency)
    key_indicators: List[IndicatorEvaluation] = Field(
        min_length=1, 
        description="List of key indicators used for analysis. Irrelevant indicators can be omitted."
    ) # 분석에 사용된 주요 지표 목록 (관련 없는 지표는 제외 가능)

    # Step 2: Executive Summary
    executive_summary: str = Field(
        description="A concise reasoning that synthesizes the indicators to explain the verdict (within 3 sentences)"
    ) # 검토된 지표들을 종합하여 정탐/오탐 이유를 설명하는 3문장 이내의 종합 논증

    # Step 3: Final Decision
    is_true_positive: bool = Field(description="Final classification result (True: True Positive, False: False Positive)") # 최종 판결 (True: 정탐, False: 오탐)
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence level of the verdict (0-1)") # 판정에 대한 신뢰도 점수 (0~1)



class IncidentReport(BaseModel):
    """Final incident report for management and response teams""" # 최종 사건 보고서 (경영진/실무 대응용)

    summary: str = Field(description="High-level summary including timestamp, attack type, and final verdict") # 사건 발생 일시, 공격 유형, 최종 판결을 포함한 핵심 요약
    severity: Severity = Field(description="Severity level of the threat") # 위협의 심각도 단계
    threat_indicators: List[str] = Field(
        description="IOC list including attacker IPs, target URIs, and malicious payloads"
    ) # IOC 리스트 (공격자 IP, 대상 URI, 악성 페이로드 등)
    mitre_attack_mapping: Optional[str] = Field(
        description="Relevant MITRE ATT&CK Tactics and Techniques (e.g., T1059.003)"
    ) # 관련 MITRE ATT&CK Tactic 및 Technique (예: T1059.003)
    detailed_analysis: str = Field(description="Detailed analysis content summarizing the CoT reasoning in natural language") # CoT 분석 근거를 자연스러운 문장으로 요약한 상세 내용
    recommended_actions: List[str] = Field(
        description="Detailed list of response actions (e.g., block IP, deeper inspection, FP exception)"
    ) # 즉각적인 차단, 점검, 예외 처리 등 대응 방안 리스트
