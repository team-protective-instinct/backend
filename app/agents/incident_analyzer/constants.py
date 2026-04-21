from enum import Enum


class AnalyzerNodeName(str, Enum):
    AGENT = "agent"
    TOOLS = "tools"
    GENERATE_REPORT = "generate_report"
