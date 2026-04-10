from fastapi import APIRouter, HTTPException
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.chat_service import create_chat_response

router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"]
)

@router.post("", response_model=ChatResponse)
async def chat_with_agent(chat_request: ChatRequest):
    """
    LangGraph 기반의 AI 에이전트에게 메시지를 보내고 응답을 받습니다.
    """
    if not chat_request.message.strip():
        raise HTTPException(status_code=400, detail="메시지가 비어있습니다.")
    
    reply = create_chat_response(chat_request.message)
    return ChatResponse(reply=reply)
