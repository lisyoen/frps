# Session 20251112-001: 터널 서버 구현 (MiniPC)

**날짜**: 2025-11-12  
**위치**: MiniPC (집, SSH Remote from MainPC)  
**상태**: ✅ 완료

---

## 개발 환경

**현재 작업**: 개발 환경
- **개발 서버**: MiniPC (Ubuntu/Linux Mint 22, 192.168.50.196, 집)
- **개발 클라이언트**: MainPC (Windows 11, 192.168.50.102, 집)
  - SSH Remote로 MiniPC 접속하여 서버 개발

**향후 운영 환경**:
- **운영 서버**: MiniPC (systemd 서비스로 자동 실행)
- **운영 클라이언트**: SubPC (Windows 11, 회사 내부망, Windows 서비스)

---

## 목표

집(MiniPC)에서 실행되는 HTTP 터널 서버 구현 완료

---

## 작업 내용

### 1. 프로젝트 구조 생성 ✅
- `tunnel-server/` 디렉토리 생성
- `tunnel_server.py` - 메인 서버 코드
- `config.yaml` - 설정 파일
- `requirements.txt` - Python 의존성
- `README.md` - 사용 설명서
- `test_server.py` - 테스트 스크립트

### 2. 터널 서버 핵심 기능 구현 ✅

#### 커맨드 채널 (8089 포트)
- SubPC와 영구 연결 유지
- NEW_CONN/READY/ERROR 메시지 파싱
- 텍스트 기반 프로토콜 (줄 구분)

#### 데이터 채널 (8091 포트)
- HTTP 트래픽 및 SubPC 터널 연결 수락
- 첫 바이트로 클라이언트/터널 구분
- 다중 연결 지원

#### IP 기반 클라이언트 매칭
- `pending_clients` - 클라이언트 대기 큐
- `pending_tunnels` - 터널 대기 큐
- client_ip를 키로 매칭

#### 양방향 TCP Relay
- `_relay_bidirectional()` 메서드
- 첫 바이트 포함한 완전한 데이터 전달
- 양쪽 소켓 종료 처리
- 에러 핸들링

### 3. 로깅 및 설정 ✅
- colorlog를 통한 컬러 로깅
- YAML 설정 파일 지원
- 통계 정보 (연결 수, 전송 바이트)
- 상세한 디버그 메시지

### 4. 테스트 ✅
- 가상환경 생성 및 패키지 설치
- 포트 8091로 변경 (8090은 Apache 사용 중)
- 서버 백그라운드 실행 성공
- 테스트 스크립트 실행 성공
  - ✓ 커맨드 채널 연결
  - ✓ READY 메시지 전송
  - ✓ 데이터 채널 HTTP 요청
  - ✓ 503 에러 응답 (SubPC 없음, 정상)

---

## 생성된 파일

```
tunnel-server/
├── tunnel_server.py      # 메인 서버 (500+ lines)
├── config.yaml           # 설정 파일
├── requirements.txt      # pyyaml, colorlog
├── README.md             # 사용 설명서
├── test_server.py        # 테스트 스크립트
├── server.log            # 서버 로그
└── venv/                 # Python 가상환경 (gitignore)
```

---

## 테스트 결과

```
터널 서버 테스트 시작

============================================================
포트 상태 확인
============================================================
✓ 커맨드 채널 (포트 8089): LISTEN
✓ 데이터 채널 (포트 8091): LISTEN

============================================================
커맨드 채널 테스트
============================================================
✓ 커맨드 채널 연결 성공
✓ READY 메시지 전송: 192.168.50.100
✓ 커맨드 채널 종료

============================================================
데이터 채널 테스트
============================================================
✓ 데이터 채널 연결 성공
✓ HTTP 요청 전송
✓ 응답 수신: b'HTTP/1.1 503 Service Unavailable\r\n\r\nTunnel not ready\n'
✓ 데이터 채널 종료
```

**서버 로그 확인:**
- ✓ 커맨드 채널 연결됨
- ✓ READY 메시지 파싱
- ✓ 데이터 채널 HTTP 요청 감지
- ✓ SubPC 없을 때 503 에러 응답

---

## Git 커밋

**커밋 메시지:**
```
터널 서버 구현 완료 (MiniPC)

- asyncio 기반 HTTP 터널 서버 구현
  - 커맨드 채널 (8089): SubPC와 영구 연결
  - 데이터 채널 (8091): HTTP 트래픽 relay
- NEW_CONN/READY/ERROR 프로토콜 파싱
- IP 기반 클라이언트 매칭
- 양방향 TCP relay 구현
- 컬러 로깅 (colorlog)
- YAML 설정 파일
- 로컬 테스트 성공 (503 에러 확인)

다음: 클라이언트 구현 (Windows 11, 회사)
```

**커밋 해시**: c553990

---

## 다음 단계

### 1. 클라이언트 개발 (MainPC, 집에서 개발)
- [ ] `tunnel-client/` 디렉토리 생성
- [ ] `tunnel_client.py` 메인 코드
- [ ] HTTP CONNECT 프록시 연결 (30.30.30.27:8080)
- [ ] 커맨드 채널 영구 연결 (MiniPC:8089)
- [ ] NEW_CONN 메시지 수신 및 파싱
- [ ] 데이터 채널 연결 (MiniPC:8091)
- [ ] 대상 서버 연결 (172.21.113.31:4000)
- [ ] 양방향 relay

### 2. 통합 테스트 (MainPC + MiniPC)
- [ ] MainPC → MiniPC (로컬 네트워크)
- [ ] 프록시 시뮬레이션
- [ ] LLM API 호출 테스트

### 3. 운영 배포 (SubPC, 회사)
- [ ] SubPC에 코드 배포 (git pull)
- [ ] 회사 프록시 경유 테스트
- [ ] Windows 서비스 등록
- [ ] MiniPC systemd 서비스 등록

---

## 참고

- **프로토콜 문서**: `.github/tunnel-protocol.md`
- **프로젝트 목표**: `.github/project-goal.md`
- **이전 세션**: session-20251111-005 (프로토콜 설계)

---

## 결론

MiniPC 터널 서버 구현 완료. 로컬 테스트 성공.

**다음 작업**: MainPC에서 클라이언트 개발 → MiniPC와 로컬 네트워크 테스트 → SubPC 운영 배포

**세션 종료 위치**: MiniPC (집, SSH Remote)  
**다음 세션 시작 위치**: MainPC (집, Windows 11) 또는 MiniPC (계속 개발)
