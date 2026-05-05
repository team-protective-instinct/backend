---
doc_type: playbook
tactic: Execution
title: Execution 대응계획서
recommended_action_hints:
  - terminate_process
  - quarantine_file
source_refs:
  - title: NIST SP 800-61r3
    url: https://csrc.nist.gov/pubs/sp/800/61/r3/final
    location_hint: Containment, Eradication, Recovery
    note: 침해 사고 대응 단계와 봉쇄 원칙 참고
  - title: CISA Incident Response Playbook
    url: https://www.cisa.gov/resources-tools/resources/federal-government-cybersecurity-incident-and-vulnerability-response-playbooks
    location_hint: Incident response playbook
    note: 사고 대응 절차와 조치 승인 흐름 참고
  - title: MITRE D3FEND
    url: https://d3fend.mitre.org/
    location_hint: Defensive techniques
    note: 실행 행위에 대한 방어 기법 분류 참고
---

# Execution 대응계획서

## 대응 목적

공격자가 시스템 내부에서 악성 스크립트나 바이너리를 실행하는 행위를 중단시키는 것을 목표로 한다. 대응 계획은 실행 흔적, 프로세스 계층, 파일 경로, 네트워크 접근 근거를 함께 검토하여 정상 서비스 영향이 작도록 수립한다.

## 주요 탐지 정황

- /tmp, /dev/shm 등 임시 경로에서 스크립트 실행
- bash, sh, python, perl 등의 비정상 실행
- 웹 서비스 계정 하위에서 의심 프로세스 생성
- 외부 IP 접근 이후 명령 실행 흔적

## 대응 원칙

- 의심 하위 프로세스를 우선 식별한다.
- 정상 서비스 부모 프로세스는 근거 없이 종료하지 않는다.
- 생성된 의심 파일은 격리 대상으로 검토한다.
- 근거가 부족하면 추가 로그 확인을 요청한다.

## 권장 대응

- 의심 프로세스 PID가 확인되면 terminate_process 계열 대응을 고려한다.
- 의심 파일 경로가 확인되면 quarantine_file 계열 대응을 고려한다.
- 동일 IP에서 반복 접근이 확인되면 네트워크 차단 여부를 검토한다.

여기서 recommended_action_hints는 대응 계획 agent가 참고할 수 있는 방향 힌트이며, 실제 실행 명령이 아니다. 실행 가능 여부, 필수 파라미터 검증, 위험 대상 검증은 Victim MCP Server가 담당한다.

## 주의사항

- 정상 서비스 프로세스를 잘못 종료하지 않도록 한다.
- 시스템 핵심 파일은 명확한 근거 없이 격리하지 않는다.
- 관리자 승인 전에는 실제 방어 조치를 실행하지 않는다.
