from langchain_core.tools import tool


@tool
def check_ip_reputation(ip_address: str) -> str:
    """Check the reputation and threat intelligence information of an IP address."""
    print(f"  [Tool Execution] Checking IP reputation... ({ip_address})")

    malicious_ips = ["103.22.1.5", "45.33.22.11"]
    internal_ips = ["192.168.1.100", "10.0.0.5"]

    if ip_address in malicious_ips:
        return f"Warning: {ip_address} is classified as a malicious IP with a history of web hacking."
    elif ip_address in internal_ips:
        return f"Safe: {ip_address} is an internal network IP."
    return f"Neutral: No specific threat information found for {ip_address}."


@tool
def analyze_payload(payload: str) -> str:
    """Analyze the HTTP request payload (URI, Body, etc.) to check for attack signatures."""
    print(f"  [Tool Execution] Analyzing payload... ({payload})")

    payload_upper = payload.upper()
    if "UNION SELECT" in payload_upper or "OR 1=1" in payload_upper:
        return "Critical: Obvious SQL Injection signature detected."
    elif "<SCRIPT>" in payload_upper or "ONERROR=" in payload_upper:
        return "Critical: XSS (Cross-Site Scripting) attack signature detected."

    return "Safe: No known attack signatures found. Likely a normal request."
