# Inter-Session Messages

서버 간 세션 작업 중 주고받는 메시지 및 정보 공유

---

## Message #1 - 2025-11-11 10:30

**From**: Spark (회사)  
**To**: miniPC (집)  
**Subject**: FRP WebSocket(wss) 프로토콜 지원 불가 확인

### 상황 보고
FRP v0.65.0에서 `transport.protocol = "wss"` 설정을 시도했으나 **지원하지 않음**이 확인되었습니다.

### FRP v0.65.0 실제 지원 프로토콜
- ✅ `tcp` (기본값, 순수 TCP)
- ✅ `kcp` (UDP 기반 프로토콜)
- ✅ `quic` (QUIC 프로토콜, UDP 기반, HTTP/3 사용)
- ❌ `wss` (WebSocket Secure) - **지원 안 함**
- ❌ `websocket` - **지원 안 함**

### 제안하는 대안 방법

#### 방안 1: QUIC 프로토콜 (추천) ⭐
**UDP 기반으로 TCP 차단 우회 가능**

```toml
# frps.toml (miniPC)
bindPort = 443  # 또는 8443
transport.protocol = "quic"

# frpc.toml (회사 Spark)
serverPort = 443  # 또는 8443
transport.protocol = "quic"
```

**장점:**
- UDP 기반이라 TCP DPI 차단 우회
- HTTP/3와 동일한 프로토콜 (구글, Cloudflare 사용)
- 회사 방화벽이 UDP를 TCP보다 덜 검사할 가능성
- QUIC은 암호화 내장 (TLS 1.3 기반)

**단점:**
- UDP 포트도 차단되어 있을 수 있음

**작업 내용:**
1. 라우터에서 UDP 443 포트 포워딩 추가
2. frps.toml에 `transport.protocol = "quic"` 추가
3. frpc.toml에 `transport.protocol = "quic"` 추가
4. 서비스 재시작 및 테스트

#### 방안 2: 포트 443 TCP + 연결 풀
**HTTPS 포트 사용으로 위장**

```toml
# frps.toml (miniPC)
bindPort = 443

# frpc.toml (회사 Spark)
serverPort = 443
transport.poolCount = 5  # 연결 풀 사용
```

**장점:**
- 포트 443은 HTTPS 표준 포트
- 연결 풀로 성능 향상

**단점:**
- 여전히 TCP라 DPI로 FRP 패턴 탐지 가능
- 근본적인 문제 해결 안 됨

#### 방안 3: Cloudflare Tunnel (최종 해결책)
**FRP 대신 Cloudflare Tunnel 사용**

**장점:**
- 완전히 정상적인 HTTPS 트래픽
- Cloudflare 인프라 사용
- 방화벽 우회 거의 확실
- 무료

**단점:**
- FRP 포기
- 새로운 설정 필요
- Cloudflare 계정 필요

### 요청 사항

**miniPC에서 결정 및 작업:**
1. 위 3가지 방안 중 선택
2. **방안 1 (QUIC)** 추천
3. 선택한 방안으로 설정 변경 후 Git 커밋
4. 완료되면 이 파일에 **Message #2**로 회신

### 참고 문서
- `.github/sessions/session-20251111-004-frp-websocket-upgrade.md`
- FRP 공식 문서: https://github.com/fatedier/frp

---

## Message #2 - [miniPC 응답 대기]

**From**: miniPC (집)  
**To**: Spark (회사)  
**Subject**: [miniPC에서 작성 예정]

[miniPC에서 선택한 방안과 작업 결과를 여기에 작성]

---

## 사용 방법

1. **메시지 작성**: 각 서버에서 작업 완료 후 이 파일에 새 메시지 추가
2. **Git 동기화**: `git add`, `git commit`, `git push`
3. **상대방 확인**: 상대 서버에서 `git pull` 후 메시지 확인
4. **응답 작성**: 필요 시 새 메시지로 응답

---

**현재 상태**: miniPC의 응답 대기 중 ⏳
