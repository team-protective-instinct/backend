from app.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.tools import tool


# dummy tool
@tool
def get_bot_info() -> str:
    """Returns basic information about this bot."""
    return (
        "이 봇은 LangGraph와 Google Gemini를 사용해 만들어진 간단한 질의응답 봇입니다."
    )


# 도구 리스트
tools = [get_bot_info]


def get_agent_executor():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.7,
    )

    # React Agent 생성 (도구를 사용할 수 있는 대화형 에이전트)
    agent_executor = create_agent(llm, tools)
    return agent_executor


# 전역 에이전트 생성
agent = get_agent_executor()


def run_agent(user_message: str) -> str:
    # 에이전트 실행
    result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})

    # 마지막 응답 반환
    return result["messages"][-1].content
