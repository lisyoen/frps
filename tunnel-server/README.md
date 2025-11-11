# HTTP Tunnel Server

회사 방화벽(DPI)를 우회하여 집(MiniPC)에서 회사 내부망 LLM 서버에 안전하게 접근하기 위한 커스텀 HTTP 터널 서버입니다.

## 개발 및 운영 환경

### 개발 환경 (개발 중)
- **개발 서버**: MiniPC (Ubuntu/Linux Mint 22, 192.168.50.196, 집)
  - tunnel-server 개발 및 테스트
- **개발 클라이언트**: MainPC (Windows 11, 192.168.50.102, 집)
  - tunnel-client 개발
  - SSH Remote로 MiniPC 접속하여 서버 개발

### 운영 환경 (개발 완료 후)
- **운영 서버**: MiniPC (Ubuntu/Linux Mint 22, 192.168.50.196, 집)
  - tunnel-server 운영 (systemd 서비스)
- **운영 클라이언트**: SubPC (Windows 11, 회사 내부망)
  - tunnel-client 운영 (Windows 서비스)
  - 회사 프록시 경유 (30.30.30.27:8080)

## 프로젝트 구조

```
frps/
├── tunnel-server/          # MiniPC (Ubuntu, 집)
│   ├── tunnel_server.py    # 터널 서버 메인
│   ├── config.yaml         # 설정 파일
│   ├── requirements.txt    # Python 의존성
│   ├── test_server.py      # 테스트 스크립트
│   └── venv/               # Python 가상환경
├── tunnel-client/          # SubPC (Windows 11, 회사) - TODO
│   └── tunnel_client.py
└── .github/
    └── tunnel-protocol.md  # 프로토콜 설계 문서
```

## 아키텍처

```
### 운영 환경 구조
```
[집]                         [회사 프록시]              [회사 내부망]
┌──────────────────┐         30.30.30.27:8080         ┌──────────────┐
│  사용자           │                                  │    SubPC      │
│  (MainPC)        │                                  │  (항상 켜짐)  │
└────────┬─────────┘                                  └──────┬───────┘
         │ HTTP                                              │
         ↓                                                   │ HTTP CONNECT
┌────────────────────┐                                      │ (터널 유지)
│     MiniPC          │                                      │
│  (터널 서버)        │ ←────────────────────────────────────┘
│                     │
│  8089: 커맨드 채널  │ ←─── SubPC 영구 연결 (명령 수신)
│  8091: 데이터 채널  │ ←─── 사용자 HTTP 요청
│                     │ ←─── SubPC 요청별 연결 (HTTP 터널)
└─────────────────────┘
                                                        ┌──────────────────┐
                                                        │   LLM 서버       │
                                                        │ 172.21.113.31:4000│
                                                        └──────────────────┘
```
```

## 설치 및 실행

### 1. 의존성 설치

```bash
cd tunnel-server
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### 2. 설정 수정 (필요 시)

`config.yaml` 파일에서 포트 및 타임아웃 설정:

```yaml
server:
  command_port: 8089
  data_port: 8091
  bind_address: "0.0.0.0"

timeouts:
  pending_timeout: 5
  relay_timeout: 30

logging:
  level: "INFO"
  colored: true

default_target:
  host: "172.21.113.31"
  port: 4000
```

### 3. 서버 실행

```bash
# 포그라운드 (디버깅용)
./venv/bin/python tunnel_server.py

# 백그라운드
nohup ./venv/bin/python tunnel_server.py > server.log 2>&1 &
```

### 4. 테스트

```bash
./venv/bin/python test_server.py
```

## 프로토콜

### 커맨드 채널 (8089 포트)

SubPC와 영구 연결 유지, 텍스트 기반 명령 전달:

#### NEW_CONN (MiniPC → SubPC)
```
NEW_CONN <client_ip> <target_host>:<target_port>\n
예: NEW_CONN 192.168.50.100 172.21.113.31:4000\n
```

#### READY (SubPC → MiniPC)
```
READY <client_ip>\n
예: READY 192.168.50.100\n
```

#### ERROR (SubPC → MiniPC)
```
ERROR <client_ip> <error_message>\n
예: ERROR 192.168.50.100 Connection refused\n
```

### 데이터 채널 (8091 포트)

- 클라이언트 HTTP 요청 수락
- SubPC 터널 연결 수락
- IP 기반 매칭 후 양방향 TCP Relay

## 현재 상태

### ✅ 완료된 기능
- [x] 커맨드 채널 (8089) - SubPC 연결 및 명령 수신
- [x] 데이터 채널 (8091) - HTTP 요청 및 터널 연결
- [x] NEW_CONN/READY/ERROR 프로토콜 파싱
- [x] IP 기반 클라이언트 매칭
- [x] 양방향 TCP Relay
- [x] 에러 처리 (503, 502, 504)
- [x] 컬러 로깅 (colorlog)
- [x] YAML 설정 파일
- [x] 로컬 테스트 스크립트

### 🚧 TODO
- [ ] SubPC 터널 클라이언트 구현 (Windows 11)
- [ ] HTTP CONNECT 프록시 연결 (30.30.30.27:8080)
- [ ] 회사 프록시 경유 테스트
- [ ] LLM API 실제 요청 테스트
- [ ] systemd 서비스 등록
- [ ] 자동 재시작 및 헬스체크

## 다음 단계

### 1. 클라이언트 개발 (MainPC, 집)
   - `tunnel-client/tunnel_client.py` 생성
   - HTTP CONNECT 프록시 연결 구현
   - 커맨드 채널 리스너
   - 대상 서버 프록시

### 2. 통합 테스트 (MainPC + MiniPC)
   - MainPC → MiniPC (로컬 네트워크 테스트)
   - 프록시 시뮬레이션
   - LLM API 호출 테스트

### 3. 운영 배포 (SubPC, 회사)
   - SubPC에 코드 배포 (git pull)
   - 회사 프록시 경유 테스트
   - Windows 서비스 등록
   - MiniPC systemd 서비스 등록

## 로그 확인

```bash
# 실시간 로그
tail -f server.log

# 최근 100줄
tail -100 server.log
```

## 문제 해결

### 포트 이미 사용 중
```bash
# 포트 사용 확인
sudo netstat -tlnp | grep -E ':(8089|8091)'

# 프로세스 종료
pkill -f tunnel_server.py
```

### 방화벽 설정 (MiniPC)
```bash
# 라우터 포트 포워딩 확인
# 8089, 8091 → 192.168.50.196
```

## 참고

- **프로토콜 상세**: `.github/tunnel-protocol.md`
- **프로젝트 목표**: `.github/project-goal.md`
- **개발 환경**: `.github/development-environment.md`
