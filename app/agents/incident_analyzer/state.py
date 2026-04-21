from typing import NotRequired, TypedDict
from langgraph.graph import MessagesState
from app.schemas.agent_schema import SecurityAnalysisReport


class AgentState(MessagesState):
    """
    Agent의 상태를 나타내는 TypedDict입니다.
    MessagesState를 상속받아 messages 필드를 기본 제공합니다.
    - analysis_result: LLM이 내린 최종 보안 분석 및 보고서 통합 결과
    - context: 에이전트 실행에 필요한 추가 메타데이터 (ID, 설정 등)
    """

    analysis_result: NotRequired[SecurityAnalysisReport]
    context: NotRequired[dict]
