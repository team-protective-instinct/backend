from typing import Any


def extract_text_from_content(content: Any) -> str:
    """
    Extracts plain text content from LangChain message content.
    Handles strings, lists of strings, lists of dicts (e.g. Anthropic block format),
    and object-based block formats.
    """
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict):
                if part.get("type") == "text" and "text" in part:
                    text_parts.append(str(part["text"]))
            elif hasattr(part, "type") and getattr(part, "type") == "text":
                if hasattr(part, "text"):
                    text_parts.append(str(getattr(part, "text")))
        return "\n".join(text_parts)
    return str(content)
