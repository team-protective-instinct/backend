from enum import Enum


class ResponsePlanNodeName(str, Enum):
    COLLECT_VICTIM_CONTEXT = "collect_victim_context"
    GENERATE_PLAN = "generate_plan"
