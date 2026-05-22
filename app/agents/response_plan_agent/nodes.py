import json
from functools import lru_cache
from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm
from app.schemas import ResponsePlanDraft

from .prompt import GENERATE_RESPONSE_PLAN_REQUEST, RESPONSE_PLAN_AGENT_SYSTEM_PROMPT
from .state import ResponsePlanState


@lru_cache(maxsize=1)
def _get_llm_resources():
    llm = get_llm(temperature=0.3)
    return {"response_plan_llm": llm.with_structured_output(ResponsePlanDraft)}


def generate_response_plan(state: ResponsePlanState):
    resources = _get_llm_resources()
    user_prompt = HumanMessage(
        content=(
            f"{GENERATE_RESPONSE_PLAN_REQUEST}\n\n"
            "[Incident Context]\n"
            f"{json.dumps(state['context'], ensure_ascii=False, indent=2)}\n\n"
            "[Retrieved Playbook Chunks]\n"
            f"{json.dumps(state['retrieved_chunks'], ensure_ascii=False, indent=2)}"
        )
    )
    draft = cast(
        ResponsePlanDraft,
        resources["response_plan_llm"].invoke(
            [SystemMessage(content=RESPONSE_PLAN_AGENT_SYSTEM_PROMPT), user_prompt]
        ),
    )
    return {"response_plan": draft}
