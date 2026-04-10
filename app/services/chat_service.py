from app.agents.chat_agent import run_agent


def create_chat_response(user_message: str) -> str:
    """
    사용자의 메시지를 받아서 LangGraph 에이전트로 전달 후 응답을 반환합니다.
    """
    try:
        reply = run_agent(user_message)
        return reply
    except Exception as e:
        # 에러 핸들링을 추가할 수 있습니다.
        return f"초기화 오류 또는 에이전트 실행 실패: {str(e)}"
