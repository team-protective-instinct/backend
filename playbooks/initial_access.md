---
doc_type: playbook
tactic: Initial Access
title: Initial Access 대응 절차서
recommended_action_hints:
  - block_ip
  - block_network_traffic
  - disable_user_account
  - quarantine_file
source_refs:
  - title: ATC RE&CT Framework
    url: https://atc-project.github.io/atc-react/
    location_hint: Response Playbook
    note: 대응 절차서를 조건, 순서, 대응 행위 중심으로 구성하는 방식 참고
  - title: MITRE D3FEND - Network Traffic Analysis
    url: https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/
    location_hint: Network Traffic Analysis
    note: 외부 침투 시도와 비인가 네트워크 활동 분석 근거 참고
  - title: MITRE D3FEND - Account Locking
    url: https://d3fend.mitre.org/technique/d3f:AccountLocking/
    location_hint: Account Locking
    note: 악용 계정 또는 의심 계정에 대한 접근 제한 개념 참고
  - title: NIST SP 800-61r3 Incident Response Recommendations
    url: https://csrc.nist.gov/pubs/sp/800/61/r3/final
    location_hint: Incident response recommendations
    note: 사고 대응 과정에서 탐지, 분석, 봉쇄, 복구 원칙 참고
  - title: CISA Cybersecurity Incident & Vulnerability Response Playbooks
    url: https://www.cisa.gov/resources-tools/resources/federal-government-cybersecurity-incident-and-vulnerability-response-playbooks
    location_hint: Incident Response Playbook
    note: 사고 식별 이후 표준화된 대응 절차 구성 방식 참고
  - title: KISA 정보통신분야 침해사고 대응 안내서
    url: https://www.krcert.or.kr/kr/bbs/view.do?bbsId=B0000127&menuNo=205021&nttId=71853&pageIndex=1
    location_hint: 침해사고 조치 가이드
    note: 국내 침해사고 예방 및 대응 요령 참고
---

# Initial Access 대응 절차서

## 1. 대응 목적

Initial Access는 공격자가 외부에서 보호 대상 시스템에 최초로 접근하거나 침투 foothold를 확보하려는 단계이다.

본 절차서는 웹 취약점 exploit, 웹쉘 업로드, 유효 계정 악용, 비정상 로그인, 원격 서비스 접근 시도 등이 탐지되었을 때 대응 계획 수립 agent가 참고할 대응 근거를 제공하는 것을 목적으로 한다.

단, 이 문서는 실제 방어 API를 직접 실행하기 위한 명령서가 아니다. `block_ip`, `block_network_traffic`, `disable_user_account`, `quarantine_file` 등의 API 이름은 대응 계획 수립을 위한 `recommended_action_hints`로만 사용되며, 실제 실행 여부와 파라미터 검증은 관리자 승인 이후 Victim MCP Server에서 수행한다.

## 2. 적용 조건

다음 조건 중 하나 이상이 확인될 때 본 절차서를 참고한다.

- 외부 IP에서 웹 애플리케이션 취약점 exploit 요청이나 파일 업로드 취약점 악용 시도가 반복적으로 확인된 경우
- `/admin/upload.php` 같은 업로드 경로에서 HTTP POST 업로드 요청이 발생하고, 비정상 확장자 또는 실행 가능한 파일이 업로드된 경우
- 웹쉘 업로드 이후 웹 서버 경로에 `shell.php` 같은 PHP 웹쉘 의심 파일이 생성된 경우
- 업로드 요청 또는 파일 내용에서 `cmd` 파라미터, `system` 함수, `passthru` 함수 등 원격 코드 실행으로 이어질 수 있는 업로드 시도 정황이 확인된 경우
- 로그인 실패가 반복된 뒤 성공 로그인이 발생한 경우
- 평소 사용하지 않던 국가, IP, User-Agent에서 계정 로그인이 발생한 경우
- VPN, SSH, RDP, 관리자 페이지 등 원격 접근 경로에서 비정상 인증 시도가 확인된 경우
- 취약점 exploit 요청이나 업로드 이후 Execution 또는 Persistence 단계로 이어질 가능성이 있는 로그가 확인된 경우

## 3. 주요 로그 근거

대응 계획 수립 전에 다음 로그 근거를 우선 확인한다.

- 외부 출발지 IP
- 접근 대상 URL 또는 서비스
- 요청 시간대와 반복 횟수
- HTTP Method
- HTTP 응답 코드
- 외부 IP의 비정상 파일 업로드 요청 여부
- `/admin/upload.php` 등 업로드 대상 URL과 HTTP POST 업로드 정황
- 업로드된 파일명과 확장자
- 업로드 파일 저장 경로
- `shell.php` 같은 PHP 웹쉘 의심 파일명
- 요청 파라미터 또는 파일 내용에 포함된 `cmd`, `system`, `passthru` 표현
- 로그인 성공/실패 이력
- 인증에 사용된 계정명
- User-Agent
- 동일 IP에서의 이전 Reconnaissance 정황
- 동일 계정의 평소 접속 위치 또는 접속 패턴
- 취약점 exploit 이후 생성된 파일, 프로세스, 네트워크 연결 여부

## 4. 분석 절차

1. 탐지된 접근이 단순 요청인지 실제 침투 시도인지 구분한다.
2. 외부 출발지 IP가 이전 Reconnaissance 단계에서 탐지된 IP와 동일한지 확인한다.
3. 웹 취약점 exploit 요청이 실제 파일 생성, 명령 실행, 비정상 응답 코드와 연결되는지 확인한다.
4. 파일 업로드가 확인된 경우 파일명, 확장자, 저장 경로, 생성 시각을 확인한다.
5. 로그인 이벤트가 포함된 경우 실패 횟수, 성공 시각, 계정명, 출발지 IP를 함께 확인한다.
6. 유효 계정 악용 가능성이 있는 경우 정상 사용자 활동인지 관리자 검토가 필요한지 판단한다.
7. 침투 정황이 명확한 경우 네트워크 차단, 계정 비활성화, 의심 파일 격리 등을 대응 후보로 제안한다.
8. 근거가 부족하거나 정상 업무 가능성이 있는 경우 safe_failure 또는 추가 로그 확인을 우선한다.

## 5. 대응 방향

### 5.1 외부 출발지 제어

다음 조건이 충족되면 `block_ip` 또는 `block_network_traffic` 계열 대응을 후보로 제안할 수 있다.

- 동일 외부 IP에서 exploit 요청 또는 인증 시도가 반복됨
- 정상 점검, 모니터링, 허용된 스캐너가 아님
- 해당 IP에서 취약점 탐색 이후 실제 침투 시도 정황이 이어짐
- 차단으로 인한 정상 서비스 영향이 낮음

주의:
- 단일 실패 로그인만으로 차단을 제안하지 않는다.
- CDN, 프록시, NAT, 클라우드 공용 IP는 오탐 가능성이 있으므로 추가 검토가 필요하다.
- 전체 네트워크 차단처럼 영향 범위가 큰 조치는 관리자 승인이 반드시 필요하다.

### 5.2 계정 접근 제한

다음 조건이 충족되면 `disable_user_account` 계열 대응을 후보로 제안할 수 있다.

- 동일 계정에 대해 다수의 실패 로그인 후 성공 로그인이 발생함
- 평소와 다른 위치, IP, 시간대, User-Agent에서 로그인이 발생함
- 침투에 악용된 것으로 의심되는 계정이 특정됨
- 해당 계정이 추가 명령 실행이나 파일 생성과 연결됨

주의:
- 업무용 정상 계정일 가능성이 있으면 즉시 비활성화보다 관리자 확인을 우선한다.
- 핵심 운영 계정, 서비스 계정, 시스템 계정은 영향도를 평가한 뒤 조치한다.
- 계정 비활성화는 실제 실행 명령이 아니라 대응 계획 후보로 제안한다.

### 5.3 의심 파일 격리

다음 조건이 충족되면 `quarantine_file` 계열 대응을 후보로 제안할 수 있다.

- 업로드된 파일이 웹쉘 또는 악성 스크립트로 의심됨
- 파일 생성 시각이 exploit 요청 또는 업로드 요청과 연결됨
- 파일 경로가 웹 서버 실행 경로 또는 임시 실행 경로에 위치함
- 동일 파일에서 후속 Execution 이벤트가 발생했거나 발생 가능성이 높음

주의:
- 시스템 핵심 파일이나 정상 서비스 파일을 근거 없이 격리하지 않는다.
- 파일 경로가 명확하지 않으면 safe_failure 또는 추가 확인을 우선한다.
- 격리 전 파일 해시, 생성 시각, 소유자, 접근 로그를 근거로 남기는 것을 권장한다.

## 6. recommended_action_hints

### block_ip

다음 조건이 충족될 때 대응 후보로 제안한다.

- 외부 출발지 IP가 명확함
- exploit 요청 또는 비정상 인증 시도가 반복됨
- 정상 점검 또는 허용된 접근이 아님
- 차단으로 인한 정상 서비스 영향이 낮음

### block_network_traffic

다음 조건이 충족될 때 대응 후보로 제안한다.

- 특정 포트, 프로토콜, URL 경로로 비정상 접근이 반복됨
- 동일 출발지 또는 동일 Subnet에서 침투 시도가 지속됨
- 네트워크 단계의 임시 제한이 필요한 상황임

### disable_user_account

다음 조건이 충족될 때 대응 후보로 제안한다.

- 침투에 사용된 것으로 의심되는 계정이 특정됨
- 비정상 로그인 이후 악성 행위가 연결됨
- 계정 오남용 가능성이 높음
- 계정 제한으로 인한 업무 영향도를 관리자 검토할 수 있음

### quarantine_file

다음 조건이 충족될 때 대응 후보로 제안한다.

- 악성 업로드 파일 또는 웹쉘 의심 파일 경로가 명확함
- 파일이 exploit 요청과 시간적으로 연결됨
- 후속 명령 실행 또는 지속성 확보에 사용될 가능성이 있음

## 7. 금지 및 주의사항

- Tactic이 Initial Access로 분류되었다는 이유만으로 즉시 차단이나 계정 잠금을 확정하지 않는다.
- 단일 실패 로그인이나 단일 404 요청만으로 공격을 단정하지 않는다.
- 정상 관리자 작업, 취약점 점검, 모의해킹, 운영 배포 작업과 혼동하지 않도록 확인한다.
- 서비스 계정, 관리자 계정, 운영 계정은 조치 전 영향도를 검토한다.
- 업로드 파일이 정상 업무 파일일 가능성이 있으면 격리 전 추가 확인이 필요하다.
- RAG는 실제 방어 API를 실행하지 않는다.
- 실제 차단, 계정 비활성화, 파일 격리는 관리자 승인 이후 Victim MCP Server가 수행한다.

## 8. safe_failure 조건

다음 조건 중 하나 이상이 있으면 safe_failure 후보로 판단한다.

- 외부 출발지 IP가 불명확한 경우
- 침투에 사용된 계정이 특정되지 않은 경우
- 업로드 파일 경로가 불명확한 경우
- 정상 로그인과 계정 탈취를 구분하기 어려운 경우
- 정상 점검 또는 운영 작업 가능성이 있는 경우
- 차단, 계정 비활성화, 파일 격리의 영향 범위를 판단할 수 없는 경우
- 검색된 playbook 또는 policy 근거가 부족한 경우

safe_failure 상태에서는 대응 계획 agent가 차단이나 계정 비활성화를 확정하지 않고, 추가 로그 확인 또는 관리자 검토 요청을 우선 제안해야 한다.

## 9. 대응 계획 생성 시 포함할 근거

대응 계획 agent는 Initial Access 대응 계획을 생성할 때 다음 근거를 포함해야 한다.

- 탐지된 외부 출발지 IP
- 접근 대상 서비스 또는 URL
- exploit 또는 인증 시도 유형
- 웹 애플리케이션 취약점 exploit 또는 파일 업로드 취약점 악용 정황
- 로그인 성공/실패 이력
- 관련 계정명
- 업로드된 파일명과 경로, `shell.php` 같은 PHP 웹쉘 의심 여부
- `/admin/upload.php` 등 업로드 URL, HTTP POST 업로드 방식, 외부 IP의 비정상 파일 업로드 요청 여부
- `cmd` 파라미터, `system` 함수, `passthru` 함수 등 원격 코드 실행으로 이어질 수 있는 단서
- 최초 침투 foothold 확보 시도와 후속 Execution 또는 Persistence 정황 여부
- 선택한 대응 후보 API와 그 이유
- 정상 업무 가능성 검토 결과
- 관리자 승인이 필요한 이유

## 10. 후속 확인

Initial Access 대응 이후에는 다음 항목을 확인한다.

- 동일 IP 또는 Subnet에서 재접근이 발생하는지 확인
- 동일 계정으로 추가 로그인 시도가 발생하는지 확인
- 업로드 파일이 실행되었거나 다른 프로세스를 생성했는지 확인
- Execution, Persistence, Privilege Escalation 단계로 이어지는지 확인
- 계정 비활성화 또는 파일 격리로 인한 정상 서비스 영향이 발생했는지 확인
- 반복 패턴이 확인되면 탐지 룰, WAF 룰, 로그인 정책 개선 대상으로 기록
