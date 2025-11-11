# HTTP Tunnel Protocol 설계

## 1. 목적
MiniPC(집)와 SubPC(회사) 간의 TCP 터널을 구축하여, 집에서 회사 내부망의 임의 서버(예: LLM API)에 HTTP 요청을 전달한다.

**핵심 요구사항:**
- 회사 방화벽 우회 (HTTP CONNECT 프록시 경유)
- 순수 HTTP 프로토콜만 사용 (DPI 우회)
- 동시 다중 연결 지원

---

## 2. 장비 구성

### MiniPC (집) - 터널 서버
- **역할**: 터널 서버, 클라이언트 요청을 SubPC로 라우팅
- **위치**: 집 (공인 IP: 110.13.119.7)
- **포트**:
  - **8089**: 커맨드 채널 (SubPC와 영구 연결, 명령 전달)
  - **8090**: 데이터 채널 (HTTP 트래픽, 다중 연결 가능)

### SubPC (회사) - 터널 클라이언트
- **역할**: 터널 클라이언트, 회사 내부망 서버로 HTTP 프록시
- **위치**: 회사 내부망 (항상 켜둠)
- **연결**:
  - MiniPC:8089에 영구 연결 (HTTP CONNECT 터널, 회사 프록시 경유)
  - MiniPC:8090에 요청별 연결 (HTTP CONNECT 터널, 회사 프록시 경유)
- **대상**: 회사 내부망 서버 (예: 172.21.113.31:4000 - LLM API)

### 클라이언트 (집) - 터널 사용자
- **역할**: HTTP 요청 발생 (MainPC, 노트북 등)
- **연결**: MiniPC:8090에 순수 HTTP 요청

---

## 3. 네트워크 구조

### 개발 환경 (개발 중)
```
[집]
┌──────────────────┐
│   MainPC         │ ← 개발 클라이언트 (Windows 11)
│ (192.168.50.102) │    - 터널 클라이언트 개발
└────────┬─────────┘    - Git 작업
         │ SSH Remote
         ↓
┌────────────────────┐
│     MiniPC          │ ← 개발 서버 (Ubuntu/Linux Mint 22)
│ (192.168.50.196)   │    - 터널 서버 개발
│  8089: 커맨드 채널  │    - 테스트 실행
│  8091: 데이터 채널  │
└─────────────────────┘
```

### 운영 환경 (개발 완료 후)
```
[집]                         [회사 프록시]              [회사 내부망]
┌──────────────────┐         30.30.30.27:8080         ┌──────────────┐
│  클라이언트       │                                  │    SubPC      │
│  (MainPC)        │                                  │  (항상 켜짐)  │
└────────┬─────────┘                                  └──────┬───────┘
         │ HTTP                                              │
         │                                                   │ HTTP CONNECT
         ↓                                                   │ (터널 유지)
┌────────────────────┐                                      │
│     MiniPC          │                                      │
│  (터널 서버)        │ ←────────────────────────────────────┘
│                     │
│  8089: 커맨드 채널  │ ←─── SubPC 영구 연결 (명령 수신)
│  8091: 데이터 채널  │ ←─── 클라이언트 HTTP 요청
│                     │ ←─── SubPC 요청별 연결 (HTTP 터널)
└─────────────────────┘

                                                        ┌──────────────────┐
                                                        │   LLM 서버       │
                                                        │ 172.21.113.31:4000│
                                                        └──────────────────┘
                                                               ↑
                                                               │ HTTP
                                                               │
                                                        SubPC가 프록시 전달
```

---

## 4. 터널 프로토콜 시퀀스

### Phase 1: 초기 연결 (시스템 시작 시 1회)
```
1. MiniPC가 8089, 8090 포트 LISTEN
2. SubPC가 MiniPC:8089에 HTTP CONNECT 터널 연결 (영구 유지)
   - 회사 프록시(30.30.30.27:8080) 경유
   - 커맨드 채널로 사용
```

### Phase 2: HTTP 요청 처리 (요청마다 반복)
```
1. 클라이언트(MainPC)가 MiniPC:8090에 HTTP 요청
   - 예: POST http://110.13.119.7:8090/v1/chat/completions

2. MiniPC가 클라이언트 소켓 accept()
   - client_ip 추출 (예: 192.168.50.100)
   - pending_clients[client_ip] = client_socket 저장

3. MiniPC → SubPC (8089 커맨드 채널):
   "NEW_CONN 192.168.50.100 172.21.113.31:4000\n"
   
4. SubPC가 커맨드 수신 후:
   a) 대상 서버 파싱: 172.21.113.31:4000
   b) MiniPC:8090에 HTTP CONNECT 터널 연결 (새 소켓)
   c) MiniPC에게 "READY 192.168.50.100\n" 응답 (8089로)

5. MiniPC가 READY 수신:
   - pending_clients[192.168.50.100] 찾기
   - client_socket ↔ tunnel_socket 양방향 relay 시작

6. 데이터 전송:
   클라이언트 → MiniPC:8090 → SubPC → 172.21.113.31:4000
   클라이언트 ← MiniPC:8090 ← SubPC ← 172.21.113.31:4000

7. HTTP 요청 완료 후:
   - 양쪽 소켓 종료
   - pending_clients[192.168.50.100] 삭제

8. 다음 요청은 2번부터 반복
```

---

## 5. 커맨드 프로토콜 (8089 포트)

### 프로토콜 포맷
```
텍스트 기반, 줄바꿈(\n)으로 구분
```

### 명령어 목록

#### 1. NEW_CONN (MiniPC → SubPC)
```
NEW_CONN <client_ip> <target_host>:<target_port>\n

예시:
NEW_CONN 192.168.50.100 172.21.113.31:4000\n
```
**의미**: 클라이언트(client_ip)의 요청을 target_host:target_port로 터널링 요청

**파라미터:**
- `client_ip`: 클라이언트의 IP 주소 (매칭 키)
- `target_host:target_port`: 회사 내부망 대상 서버

#### 2. READY (SubPC → MiniPC)
```
READY <client_ip>\n

예시:
READY 192.168.50.100\n
```
**의미**: MiniPC:8090에 터널 연결 완료, client_ip로 매칭하여 relay 시작

**파라미터:**
- `client_ip`: 대기 중인 클라이언트 IP (pending_clients에서 찾기)

#### 3. ERROR (SubPC → MiniPC)
```
ERROR <client_ip> <error_message>\n

예시:
ERROR 192.168.50.100 Connection refused\n
```
**의미**: 대상 서버 연결 실패, 클라이언트에게 에러 응답

---

## 6. 데이터 채널 (8090 포트)

### 특징
- **순수 TCP Relay**: HTTP 프로토콜 수정 없이 그대로 전달
- **다중 연결**: 동일 포트에 여러 클라이언트 동시 연결 가능
- **IP 기반 매칭**: client_ip로 pending_clients와 tunnel_socket 매칭

### TCP 소켓 동작
```
MiniPC:8090 LISTEN

클라이언트1 연결 → accept() → socket_A (192.168.50.100:54321)
클라이언트2 연결 → accept() → socket_B (192.168.50.101:54322)

SubPC 연결1 → accept() → socket_C (회사프록시IP:random)
SubPC 연결2 → accept() → socket_D (회사프록시IP:random)

매칭:
socket_A ↔ socket_C (client_ip로 매칭)
socket_B ↔ socket_D (client_ip로 매칭)
```

---

## 7. 에러 처리

### 타임아웃
- 클라이언트 연결 후 5초 내 SubPC 응답 없으면 → 연결 종료
- pending_clients에서 제거

### 연결 실패
- SubPC가 대상 서버 연결 실패 시 → ERROR 전송
- MiniPC가 클라이언트에게 502 Bad Gateway 응답

### 중복 IP
- 같은 IP에서 동시 다중 요청 시 **순차 처리**
- 실제 사용 환경에서는 발생하지 않음 (1인 사용)

---

## 8. 구현 참고사항

### MiniPC 서버 (Python 예시)
```python
import asyncio

pending_clients = {}  # client_ip → client_socket
command_channel = None  # SubPC와의 8089 연결

async def handle_command_channel(reader, writer):
    """8089 포트: SubPC 커맨드 채널"""
    global command_channel
    command_channel = writer
    
    while True:
        line = await reader.readline()
        if not line:
            break
        
        # READY 또는 ERROR 처리
        cmd, client_ip, *args = line.decode().strip().split()
        
        if cmd == "READY" and client_ip in pending_clients:
            # 다음 데이터 채널 연결을 이 클라이언트와 매칭
            pass

async def handle_data_channel(reader, writer):
    """8090 포트: HTTP 데이터 채널"""
    client_ip = writer.get_extra_info('peername')[0]
    
    pending_clients[client_ip] = (reader, writer)
    
    # SubPC에게 터널 요청
    await command_channel.write(
        f"NEW_CONN {client_ip} 172.21.113.31:4000\n".encode()
    )
    
    # SubPC 터널 연결 대기...

async def relay(reader1, writer1, reader2, writer2):
    """양방향 데이터 relay"""
    async def copy(r, w):
        try:
            while True:
                data = await r.read(4096)
                if not data:
                    break
                w.write(data)
                await w.drain()
        finally:
            w.close()
    
    await asyncio.gather(
        copy(reader1, writer2),
        copy(reader2, writer1)
    )
```

### SubPC 클라이언트 (Python 예시)
```python
async def connect_tunnel():
    """MiniPC:8089에 영구 연결"""
    reader, writer = await connect_via_proxy(
        "110.13.119.7", 8089,
        proxy="30.30.30.27:8080"
    )
    
    while True:
        line = await reader.readline()
        cmd, client_ip, target = line.decode().strip().split()
        
        if cmd == "NEW_CONN":
            # MiniPC:8090에 새 터널 연결
            await handle_new_connection(client_ip, target, writer)

async def handle_new_connection(client_ip, target, cmd_writer):
    """새 HTTP 터널 연결"""
    host, port = target.split(":")
    
    # MiniPC:8090에 HTTP CONNECT 터널
    tunnel_reader, tunnel_writer = await connect_via_proxy(
        "110.13.119.7", 8090,
        proxy="30.30.30.27:8080"
    )
    
    # 대상 서버 연결
    target_reader, target_writer = await asyncio.open_connection(host, int(port))
    
    # READY 전송
    await cmd_writer.write(f"READY {client_ip}\n".encode())
    
    # 양방향 relay
    await relay(tunnel_reader, tunnel_writer, target_reader, target_writer)
```

---

## 9. 보안 고려사항

- **인증**: 현재 없음 (내부 사용 목적)
- **암호화**: HTTPS 사용 시 TLS는 end-to-end 유지
- **접근 제어**: client_ip로 제한 가능 (필요 시) 