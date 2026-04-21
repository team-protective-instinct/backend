from typing import List, Literal, Optional, Dict
from pydantic import BaseModel, Field


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


class SecurityAnalysisReport(BaseModel):
    """Integrated security analysis report for final verdict and future response planning"""
    # 최종 통합 보안 분석 보고서: 정오탐 판정 결과와 함께 대응 에이전트가 사용할 핵심 데이터를 포함합니다.

    # --- [Step 1: Verdict & Confidence] ---
    is_true_positive: bool = Field(description="Final classification result (True: True Positive, False: False Positive)") # 최종 판결 (True: 정탐, False: 오탐)
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence level of the verdict (0-1)") # 판정에 대한 신뢰도 점수 (0~1)

    # --- [Step 2: Summary & Classification] ---
    executive_summary: str = Field(
        description="A concise reasoning that synthesizes the indicators to explain the verdict (within 3 sentences)"
    ) # 검토된 지표들을 종합하여 정탐/오탐 이유를 설명하는 3문장 이내의 종합 요약
    attack_type: str = Field(description="Name of the attack type (e.g., SQL Injection, Brute Force)") # 공격 유형 명칭
    mitre_attack_ids: List[str] = Field(description="List of relevant MITRE ATT&CK Technique IDs (e.g., T1190)") # 관련 MITRE ATT&CK ID 목록

    # --- [Step 3: Detailed Evidence for Responder Agent] ---
    detailed_analysis: str = Field(description="Detailed analysis content summarizing the CoT reasoning in natural language") # CoT 분석 근거를 자연스러운 문장으로 요약한 상세 내용
    key_indicators: List[IndicatorEvaluation] = Field(
        min_length=1, 
        description="List of key indicators used for analysis. Irrelevant indicators can be omitted."
    ) # 분석에 사용된 주요 지표 목록
    iocs: Dict[str, List[str]] = Field(
        description="Structured list of IOCs including attacker_ips, target_uris, and suspicious_payloads"
    ) # 공격자 IP, 대상 URI, 악성 페이로드 등을 포함한 구조화된 IOC 목록
