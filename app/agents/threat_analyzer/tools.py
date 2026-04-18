from langchain_core.tools import tool


@tool
def check_ip_reputation(ip_address: str) -> str:
    """IP 주소의 악성 여부 및 위협 인텔리전스 정보를 확인합니다."""
    print(f"  [Tool 실행] IP 평판 조회 중... ({ip_address})")

    malicious_ips = ["103.22.1.5", "45.33.22.11"]
    internal_ips = ["192.168.1.100", "10.0.0.5"]

    if ip_address in malicious_ips:
        return f"경고: {ip_address}는 과거 웹 해킹 이력이 있는 악성 IP로 분류되어 있습니다."
    elif ip_address in internal_ips:
        return f"안전: {ip_address}는 내부망 IP입니다."
    return f"중립: {ip_address}에 대한 특별한 위협 정보가 없습니다."


@tool
def analyze_payload(payload: str) -> str:
    """HTTP 요청 페이로드(URI, Body 등)를 분석하여 공격 시그니처를 확인합니다."""
    print(f"  [Tool 실행] 페이로드 분석 중... ({payload})")

    payload_upper = payload.upper()
    if "UNION SELECT" in payload_upper or "OR 1=1" in payload_upper:
        return "위험: 명백한 SQL Injection 시그니처가 탐지되었습니다."
    elif "<SCRIPT>" in payload_upper or "ONERROR=" in payload_upper:
        return "위험: XSS (Cross-Site Scripting) 공격 시그니처가 탐지되었습니다."

    return "안전: 알려진 공격 시그니처가 발견되지 않았습니다. 정상적인 요청일 가능성이 높습니다."
