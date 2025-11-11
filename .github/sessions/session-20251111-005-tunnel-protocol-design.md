# Session 20251111-005: HTTP 터널 프로토콜 설계 완료

**날짜**: 2025-11-11  
**위치**: 회사 Spark (DGX)  
**상태**: ✅ 완료 (설계 단계)

---

## 목표

회사 방화벽(DPI)을 우회하여 집(miniPC)에서 회사 내부망 LLM 서버(172.21.113.31:4000)에 접근할 수 있는 HTTP 터널 시스템 설계

---

## 주요 발견 사항

### 1. FRP 프로토콜 차단 확인 ❌
- FRP v0.65.0의 프로토콜 자체가 회사 DPI에 차단됨
- `proxyURL` 설정에도 불구하고 "session shutdown" 에러 지속
- 프로토콜 패턴 감지로 핸드셰이크 단계에서 차단

### 2. HTTP CONNECT 터널 작동 확인 ✅
**Spark (Linux) 테스트:**
```python
# Python socket으로 HTTP CONNECT 터널 성공
프록시 경유 → miniPC:8089 → HTTP/1.1 200 Connection established
```

**업무 PC (Windows 11) 테스트:**
```powershell
# PowerShell로 HTTP CONNECT 터널 성공
프록시: 30.30.30.27:8080
Target: 110.13.119.7:8089
✅ TCP 터널 성립!
```

### 3. 회사 네트워크 정책 분석
- ✅ HTTP/HTTPS (프록시 경유): 허용
- ✅ HTTP CONNECT (임의 TCP 터널): 허용
- ❌ 직접 TCP 연결 (비표준 포트): 차단
- ❌ UDP (모든 포트): 차단
- ❌ FRP 프로토콜: DPI 차단

---

## 설계 결과

### 최종 아키텍처

```
[집]                         [회사 프록시]              [회사 내부망]
┌──────────────────┐         30.30.30.27:8080         ┌──────────────┐
│  사용자           │                                  │    SubPC      │
│  (HOME-DESKTOP)  │                                  │  (항상 켜짐)  │
└────────┬─────────┘                                  └──────┬───────┘
         │ HTTP                                              │
         ↓                                                   │ HTTP CONNECT
┌────────────────────┐                                      │ (터널 유지)
│     miniPC          │                                      │
│  (터널 서버)        │ ←────────────────────────────────────┘
│                     │
│  8089: 커맨드 채널  │ ←─── SubPC 영구 연결 (명령 수신)
│  8090: 데이터 채널  │ ←─── 사용자 HTTP 요청
│                     │ ←─── SubPC 요청별 연결 (HTTP 터널)
└─────────────────────┘
                                                        ┌──────────────────┐
                                                        │   LLM 서버       │
                                                        │ 172.21.113.31:4000│
                                                        └──────────────────┘
```

### 포트 구성
- **8089**: 커맨드 채널 (SubPC → miniPC 영구 연결)
- **8090**: 데이터 채널 (다중 HTTP 연결)

### 핵심 프로토콜
**NEW_CONN (miniPC → SubPC):**
```
NEW_CONN <client_ip> <target_host>:<target_port>\n
예: NEW_CONN 192.168.50.100 172.21.113.31:4000\n
```

**READY (SubPC → miniPC):**
```
READY <client_ip>\n
예: READY 192.168.50.100\n
```

### IP 기반 클라이언트 매칭
- 클라이언트 IP로 `pending_clients` 딕셔너리 관리
- SubPC가 READY 응답 시 해당 IP의 소켓과 매칭
- 양방향 TCP relay 시작

---

## 생성된 파일

1. **`.github/tunnel-protocol.md`**
   - 완전한 프로토콜 설계 문서
   - 시퀀스 다이어그램
   - Python 구현 예시 코드

2. **`scripts/http-tunnel-test.py`**
   - 터널 테스트 스크립트 (포트 8089로 수정)

3. **`scripts/reverse-http-tunnel-server.py`**
   - Spark 역방향 터널 서버 (미사용)

---

## 개발 전략

### Phase 1: 개발 (업무 PC)
```
업무PC(Windows 11, 개발) → 프록시 → miniPC(서버)
```
- VSCode로 클라이언트 개발
- 실시간 테스트 및 디버깅

### Phase 2: 배포 (SubPC)
```
SubPC(Windows 11, 프로덕션) → 프록시 → miniPC(서버)
```
- 항상 켜둠
- Git pull로 코드 배포

### 프로젝트 구조 (Monorepo)
```
frps/
├── .github/
│   └── tunnel-protocol.md
├── tunnel-server/          # miniPC (Ubuntu Mint)
│   ├── tunnel_server.py
│   ├── requirements.txt
│   └── config.yaml
├── tunnel-client/          # 업무PC/SubPC (Windows 11)
│   ├── tunnel_client.py
│   ├── requirements.txt
│   └── config.yaml
└── common/
    └── protocol.py
```

---

## 다음 단계

### 1. 서버 구현 (miniPC)
- [ ] `tunnel-server/tunnel_server.py` 생성
- [ ] 커맨드 채널 구현 (8089 포트)
- [ ] 데이터 채널 구현 (8090 포트)
- [ ] IP 기반 매칭 로직
- [ ] 양방향 TCP relay

### 2. 클라이언트 구현 (업무PC)
- [ ] `tunnel-client/tunnel_client.py` 생성
- [ ] HTTP CONNECT 프록시 연결
- [ ] 커맨드 채널 리스너
- [ ] 대상 서버 프록시
- [ ] 에러 처리

### 3. 테스트
- [ ] 로컬 테스트 (프록시 없이)
- [ ] 업무PC → miniPC 테스트 (프록시 경유)
- [ ] LLM API 실제 요청 테스트

### 4. 배포
- [ ] SubPC에 코드 복사
- [ ] Windows 서비스 등록
- [ ] 자동 시작 설정

---

## 기술적 세부사항

### HTTP CONNECT 터널링
```python
# 프록시 연결
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("30.30.30.27", 8080))

# CONNECT 요청
sock.sendall(b"CONNECT 110.13.119.7:8089 HTTP/1.1\r\nHost: 110.13.119.7:8089\r\n\r\n")

# 응답 확인
response = sock.recv(4096)
# "HTTP/1.1 200 Connection established" 확인

# 이제 sock은 순수 TCP 터널
```

### 클라이언트 매칭 로직
```python
pending_clients = {}  # client_ip → client_socket

# 클라이언트 연결 시
client_ip = writer.get_extra_info('peername')[0]
pending_clients[client_ip] = (reader, writer)
await cmd_channel.write(f"NEW_CONN {client_ip} 172.21.113.31:4000\n")

# READY 수신 시
if client_ip in pending_clients:
    client_reader, client_writer = pending_clients.pop(client_ip)
    await relay(client_reader, client_writer, tunnel_reader, tunnel_writer)
```

---

## 참고 사항

### 테스트 환경
- **miniPC**: Ubuntu Mint 22, Python 3.12.3
- **SubPC**: Windows 11, Python 3.11
- **업무PC**: Windows 11, Python 3.11
- **회사 프록시**: 30.30.30.27:8080

### 네트워크 정보
- miniPC 공인 IP: 110.13.119.7
- 라우터 포트 포워딩: 8000~8999
- 회사 LLM: 172.21.113.31:4000

### Git 저장소
- Repository: https://github.com/lisyoen/frps
- Branch: main
- Commit: 2f6fc2e "HTTP 터널 프로토콜 설계 문서 완성"

---

## 결론

FRP 실패 후 커스텀 HTTP 터널 프로토콜 설계 완료. 회사 프록시의 HTTP CONNECT 지원을 활용하여 임의의 TCP 터널링 가능함을 확인. 다음 세션에서 업무PC로 이동하여 구현 시작 예정.

**세션 종료 위치**: Spark (회사)  
**다음 세션 시작 위치**: 업무PC (회사, Windows 11)
