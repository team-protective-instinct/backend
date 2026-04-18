from typing import Annotated, Optional, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from app.schemas.agent_schema import FinalSecurityAnalysis, IncidentReport


class AgentState(TypedDict):
    """
    Agent의 상태를 나타내는 TypedDict입니다.
    - messages: LLM과의 대화 기록 (add_messages 리듀서를 통해 누적 관리)
    - final_analysis: LLM이 내린 최종 보안 분석 결과 (FinalSecurityAnalysis 모델)
    - incident_report: 최종 사건 보고서 (IncidentReport 모델)
    """

    messages: Annotated[list[BaseMessage], add_messages]
    final_analysis: Optional[FinalSecurityAnalysis]
    incident_report: Optional[IncidentReport]
