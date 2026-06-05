from enum import Enum


class ResponsePlanNodeName(str, Enum):
    AGENT = "agent"
    TOOLS = "tools"
    SUMMARIZE = "summarize"
