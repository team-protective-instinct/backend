---
doc_type: playbook
tactic: Reconnaissance
title: Reconnaissance 대응 절차서
recommended_action_hints:
  - block_ip
  - block_network_traffic
source_refs:
  - title: ATC RE&CT Framework
    url: https://atc-project.github.io/atc-react/
    location_hint: Response Playbook
    note: 대응 절차서를 조건, 순서, 대응 행위 중심으로 구성하는 방식 참고
  - title: MITRE D3FEND - Network Traffic Analysis
    url: https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/
    location_hint: Network Traffic Analysis
    note: 비인가 활동 탐지를 위한 네트워크 트래픽 분석 근거 참고
  - title: MITRE D3FEND - Network Traffic Filtering
    url: https://d3fend.mitre.org/technique/d3f:NetworkTrafficFiltering/
    location_hint: Network Traffic Filtering
    note: 의심 출발지 또는 비인가 트래픽 제한 조치 근거 참고
  - title: NIST SP 800-61r3 Incident Response Recommendations
    url: https://csrc.nist.gov/pubs/sp/800/61/r3/final
    location_hint: Incident response recommendations
    note: 탐지, 대응, 복구 활동을 조직의 위험 관리 절차와 연결하는 원칙 참고
  - title: CISA Cybersecurity Incident & Vulnerability Response Playbooks
    url: https://www.cisa.gov/resources-tools/resources/federal-government-cybersecurity-incident-and-vulnerability-response-playbooks
    location_hint: Incident Response Playbook
    note: 사고 식별 이후 표준화된 대응 절차 구성 방식 참고
  - title: KISA 정보통신분야 침해사고 대응 안내서
    url: https://www.krcert.or.kr/kr/bbs/view.do?bbsId=B0000127&menuNo=205021&nttId=71853&pageIndex=1
    location_hint: 침해사고 조치 가이드
    note: 국내 침해사고 예방 및 대응 요령 참고
---

# Reconnaissance 대응 절차서

## 1. 대응 목적

Reconnaissance는 공격자가 본격적인 침투 전에 대상 시스템의 열린 포트, 실행 중인 서비스, 취약한 엔드포인트, 웹 경로, 계정 정보 등을 수집하는 단계이다.

본 절차서는 외부 출발지에서 반복적인 포트 스캔, 서비스 식별, 웹 취약점 탐색, 디렉터리 브루트포싱 등이 탐지되었을 때 대응 계획 수립 agent가 참고할 대응 근거를 제공하는 것을 목적으로 한다.

단, 이 문서는 실제 방어 API를 직접 실행하기 위한 명령서가 아니다. `block_ip`, `block_network_traffic` 등의 API 이름은 대응 계획 수립을 위한 `recommended_action_hints`로만 사용되며, 실제 실행 여부와 파라미터 검증은 관리자 승인 이후 Victim MCP Server에서 수행한다.

## 2. 적용 조건

다음 조건 중 하나 이상이 확인될 때 본 절차서를 참고한다.

- 짧은 시간 동안 하나의 외부 IP에서 다수의 포트 접근 시도가 발생한 경우
- `/admin`, `/login`, `/phpmyadmin`, `/server-status`, `/backup` 등 민감 경로에 대한 반복 접근이 확인된 경우
- HTTP 404, 403, 401 응답을 대량으로 유발하는 디렉터리 탐색 패턴이 확인된 경우
- 동일 출발지에서 여러 User-Agent 또는 비정상 User-Agent를 사용한 반복 요청이 확인된 경우
- Nmap, masscan, sqlmap, gobuster, dirb, nikto 등 자동화 도구 사용이 의심되는 요청 패턴이 확인된 경우
- 취약점 탐색으로 보이는 요청이 WAF, Sigma rule, 웹 로그, 네트워크 로그에서 반복 탐지된 경우

## 3. 주요 로그 근거

대응 계획 수립 전에 다음 로그 근거를 우선 확인한다.

- 출발지 IP
- 목적지 IP 및 포트
- 요청 시간대와 반복 횟수
- 접근한 URL 경로
- HTTP Method
- HTTP 응답 코드
- User-Agent
- 동일 출발지의 요청 간격
- 동일 출발지에서 접근한 서로 다른 포트 수
- 동일 출발지에서 접근한 서로 다른 경로 수
- 기존 허용된 보안 점검 도구 또는 내부 스캐너 여부
- 최근 취약점 점검, 모의해킹, 운영 점검 일정과의 연관성

## 4. 분석 절차

1. 탐지된 이벤트가 단발성 요청인지 반복적 탐색인지 확인한다.
2. 출발지 IP가 내부 보안 점검 장비, 클라우드 헬스체크, 정상 모니터링 시스템인지 확인한다.
3. 동일 출발지에서 다수 포트 또는 다수 URL 경로에 접근했는지 확인한다.
4. HTTP 404, 403, 401 응답이 짧은 시간에 집중되었는지 확인한다.
5. 취약점 스캐너 또는 자동화 도구로 보이는 User-Agent, 요청 간격, URL 패턴이 있는지 확인한다.
6. 공격 정황이 반복적이고 명확한 경우, 대응 후보로 네트워크 차단 또는 집중 감시를 고려한다.
7. 정상 점검 가능성이 있거나 근거가 부족한 경우, 즉시 차단하지 않고 추가 로그 확인 또는 관리자 검토를 요청한다.

## 5. 대응 방향

### 5.1 감시 강화

다음 경우에는 즉시 차단보다 감시 강화를 우선 고려한다.

- 요청 수가 적고 단발성인 경우
- 정상 보안 점검 또는 모니터링일 가능성이 있는 경우
- 출발지 IP가 클라우드, CDN, 프록시, NAT 환경에 속해 있어 실제 공격자 식별이 불명확한 경우
- 서비스 영향도와 오탐 가능성이 높은 경우

대응 계획에는 다음 내용을 포함할 수 있다.

- 해당 출발지 IP를 집중 감시 대상으로 등록
- 동일 IP 또는 동일 Subnet에서의 반복 요청 여부 확인
- WAF 또는 로그 수집 시스템에서 동일 패턴 탐지 강화
- 이후 Initial Access 또는 Execution 단계로 이어지는지 추적

### 5.2 차단 후보 제안

다음 조건이 함께 충족되면 `block_ip` 또는 `block_network_traffic` 계열 대응을 후보로 제안할 수 있다.

- 동일 외부 IP에서 반복적인 포트 스캔 또는 경로 탐색이 확인됨
- 정상 점검, 모니터링, 헬스체크 트래픽이 아님
- 여러 민감 경로 또는 여러 포트에 대한 탐색이 확인됨
- 취약점 스캐너 또는 자동화 도구 사용 정황이 있음
- 동일 출발지에서 이후 공격 단계로 이어질 가능성이 높음

## 6. recommended_action_hints

### block_ip

다음 조건이 충족될 때 대응 후보로 제안한다.

- 외부 출발지 IP가 명확함
- 반복적인 포트 스캔 또는 웹 경로 탐색이 확인됨
- 정상 점검 또는 허용된 스캐너가 아님
- 차단으로 인한 정상 서비스 영향이 낮음

주의:

- 공유 NAT, CDN, 클라우드 사업자 IP인 경우 즉시 차단보다 추가 검토가 필요하다.
- 단발성 요청만으로 차단을 제안하지 않는다.
- `block_ip`는 실제 실행 명령이 아니라 대응 계획 agent가 참고하는 후보 API이다.

### block_network_traffic

다음 조건이 충족될 때 대응 후보로 제안한다.

- 특정 포트 또는 특정 프로토콜에 대한 반복 탐색이 확인됨
- 특정 출발지 또는 Subnet에서 유사한 탐색이 지속됨
- 네트워크 단계에서 임시 제한이 필요한 상황임

주의:

- 전체 네트워크 차단처럼 영향 범위가 큰 조치는 관리자 승인이 반드시 필요하다.
- 정상 사용자 트래픽까지 차단될 가능성이 있으면 safe failure 또는 관리자 검토를 우선한다.

## 7. 금지 및 주의사항

- Tactic이 Reconnaissance로 분류되었다는 이유만으로 즉시 차단을 확정하지 않는다.
- 단일 로그 이벤트만으로 `block_ip`를 제안하지 않는다.
- 정상 보안 점검, 모의해킹, 취약점 진단, 모니터링 트래픽을 공격으로 단정하지 않는다.
- 클라우드, CDN, 프록시, NAT 대역은 오탐 가능성이 있으므로 추가 확인이 필요하다.
- RAG는 실제 방어 API를 실행하지 않는다.
- 실제 차단, 네트워크 제한, 방화벽 정책 변경은 관리자 승인 이후 Victim MCP Server가 수행한다.

## 8. safe_failure 조건

다음 조건 중 하나 이상이 있으면 safe_failure 후보로 판단한다.

- 출발지 IP가 불명확한 경우
- 정상 점검 트래픽인지 공격 트래픽인지 구분하기 어려운 경우
- 반복성이나 공격 패턴을 확인할 로그가 부족한 경우
- 차단 대상이 CDN, 프록시, 클라우드 공용 IP일 가능성이 높은 경우
- 차단 시 정상 서비스 영향 범위를 판단할 수 없는 경우
- 검색된 playbook 또는 policy 근거가 부족한 경우

safe_failure 상태에서는 대응 계획 agent가 차단을 확정하지 않고, 추가 로그 확인 또는 관리자 검토 요청을 우선 제안해야 한다.

## 9. 대응 계획 생성 시 포함할 근거

대응 계획 agent는 Reconnaissance 대응 계획을 생성할 때 다음 근거를 포함해야 한다.

- 탐지된 출발지 IP
- 탐지된 목적지 IP 또는 서비스
- 반복 요청 횟수
- 접근한 포트 또는 URL 경로
- User-Agent 또는 도구 사용 정황
- 정상 점검 여부 확인 결과
- 선택한 대응 후보 API와 그 이유
- 차단 또는 감시 강화가 필요한 근거
- 관리자 승인이 필요한 이유

## 10. 후속 확인

Reconnaissance 대응 이후에는 다음 항목을 확인한다.

- 동일 IP 또는 Subnet에서 재시도가 발생하는지 확인
- Initial Access 관련 이벤트로 이어지는지 확인
- 웹쉘 업로드, 로그인 시도, 취약점 exploit 요청이 뒤따르는지 확인
- 차단 또는 감시 강화 후 정상 서비스 영향이 발생했는지 확인
- 반복 패턴이 확인되면 WAF 또는 탐지 룰 개선 대상으로 기록
