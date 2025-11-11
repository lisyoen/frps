# Session: session-20251111-004-frp-websocket-upgrade

## 세션 정보

- **세션 ID**: session-20251111-004-frp-websocket-upgrade
- **날짜**: 2025-11-11
- **상태**: 대기 중 ⏸️
- **작업자**: 집 MiniPC에서 작업 예정
- **이전 세션**: session-20251111-003-frps-install-minipc (완료)

## 작업 목적

FRP를 WebSocket Secure(wss) 프로토콜로 전환하여 회사 방화벽 우회
- **문제**: 회사 방화벽이 순수 TCP FRP 트래픽을 DPI로 차단
- **해결**: WebSocket over HTTPS로 일반 웹사이트 통신처럼 위장

## 현재 상황

### 완료된 작업
- ✅ session-20251111-001: FRP 설정 파일 작성
- ✅ session-20251111-002: 회사 Spark FRP 클라이언트 설치
- ✅ session-20251111-003: MiniPC FRP 서버 설치 (TCP, 포트 8000/8081)

### 문제점
- ❌ 회사 Spark → MiniPC 연결 실패 (포트 8000)
- 🔍 원인 분석: 포트 문제가 아닌 **프로토콜 수준 차단**
  - 회사 방화벽이 DPI로 FRP 핸드셰이크 패턴 탐지
  - SSH, RDP처럼 프로토콜 시그니처로 차단
  - 순수 TCP는 내용이 노출되어 탐지 가능

### 해결 방안
- ✅ **WebSocket Secure (wss)** 사용
  - HTTPS 프로토콜 위에서 동작
  - 일반 웹사이트 통신으로 위장
  - 포트 443 사용 (표준 HTTPS 포트)
  - 패킷 분석 시 웹브라우저 트래픽으로 보임

## 작업 환경

### 집 MiniPC
- **Hostname**: MiniPC
- **OS**: Linux (Ubuntu-based)
- **내부 IP**: 192.168.50.196
- **공인 IP**: 110.13.119.7
- **Gateway**: 192.168.50.1 (ASUS RT-AX53U)
- **현재 FRP**: 포트 8000(TCP), 8081(HTTP)
- **변경 목표**: 포트 443(WSS), 8081(HTTP)

### 회사 Spark (대기 중)
- **상태**: FRP 클라이언트 대기 중
- **IP**: 172.21.113.31
- **변경 필요**: serverPort=443, transport.protocol="wss"

## 작업 계획

### 1단계: 라우터 포트 포워딩 설정
```bash
# 브라우저에서 ASUS RT-AX53U 관리 페이지 접속
# URL: http://192.168.50.1

# 설정 경로:
# Advanced Settings → WAN → Virtual Server/Port Forwarding

# 추가할 규칙:
# Service Name: frp-wss
# Port Range: 443
# Local IP: 192.168.50.196
# Local Port: 443
# Protocol: TCP
```

**⚠️ 주의**: 
- 443 포트가 다른 서비스(NGINX, Apache 등)와 충돌하지 않는지 확인
- 기존 웹서버가 있다면 다른 포트로 이동 필요

### 2단계: FRP 서버 설정 변경

#### 현재 설정 확인
```bash
cd ~/frps
cat configs/frps.toml

# 현재 설정:
# bindPort = 8000
# vhostHTTPPort = 8081
# (transport.protocol 없음 = 기본 TCP)
```

#### 설정 파일 수정
```bash
nano configs/frps.toml

# 변경 내용:
# bindPort = 8000  →  bindPort = 443
# transport.protocol 추가: "wss"
```

**변경 후 설정:**
```toml
# FRP Server Configuration (MiniPC)
# Version: v0.65.0
# Location: /etc/frp/frps.toml

# Server bind address and port
bindAddr = "0.0.0.0"
bindPort = 443  # HTTPS 표준 포트로 변경

# Authentication token (must match client)
auth.token = "deasea!1"

# HTTP vhost configuration
vhostHTTPPort = 8081

# Transport protocol - WebSocket Secure
transport.protocol = "wss"

# Log configuration
log.level = "info"
log.maxDays = 7

# Maximum connections per proxy
maxPortsPerClient = 0

# Enable heartbeat
transport.heartbeatTimeout = 90
```

### 3단계: 설정 파일 배포 및 서비스 재시작
```bash
# 443 포트 사용 중인 프로세스 확인
sudo netstat -tlnp | grep :443
sudo lsof -i :443

# 기존 서비스 중지 (필요 시)
# sudo systemctl stop nginx  # 또는 apache2

# 설정 파일 복사
sudo cp configs/frps.toml /etc/frp/frps.toml

# 권한 확인
sudo chmod 600 /etc/frp/frps.toml

# 서비스 재시작
sudo systemctl restart frps

# 상태 확인
sudo systemctl status frps --no-pager
```

### 4단계: 서비스 확인
```bash
# 포트 리스닝 확인
sudo netstat -tlnp | grep -E '443|8081'
# 예상 결과:
# tcp 0.0.0.0:443 ... LISTEN ... frps
# tcp 0.0.0.0:8081 ... LISTEN ... frps

# 로그 확인
sudo journalctl -u frps -n 50 --no-pager

# 실시간 로그 모니터링
sudo journalctl -u frps -f

# 예상 로그:
# "start frpc service for config file [/etc/frp/frps.toml]"
# "frps uses command line arguments for config"
```

### 5단계: 방화벽 설정 (필요 시)
```bash
# ufw 사용 중인 경우
sudo ufw allow 443/tcp comment 'FRP WSS Port'
sudo ufw status

# iptables 사용 중인 경우
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -L -n | grep 443
```

### 6단계: 연결 테스트 (로컬)
```bash
# WebSocket 연결 테스트 (curl)
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: test" \
  https://localhost:443

# 또는 openssl로 TLS 연결 확인
openssl s_client -connect localhost:443

# 로그에서 연결 확인
sudo tail -f /var/log/frp/frps.log
```

### 7단계: Git 동기화
```bash
# 변경사항 확인
git status
git diff configs/frps.toml

# 커밋
git add configs/frps.toml
git add configs/frpc.toml  # 클라이언트도 함께 수정
git commit -m "FRP WebSocket(wss) 전환: 포트 443, 프로토콜 wss"
git push

# 푸시 확인
git log -1
```

## frpc.toml도 함께 수정

회사 Spark에서 사용할 클라이언트 설정도 업데이트:

```bash
nano configs/frpc.toml

# 변경 내용:
# serverPort = 8000  →  serverPort = 443
# transport.protocol 추가: "wss"
```

**변경 후 설정:**
```toml
# FRP Client Configuration (Office LLM Server)
# Version: v0.65.0
# Location: /etc/frp/frpc.toml

# Server connection
serverAddr = "110.13.119.7"
serverPort = 443  # HTTPS 포트로 변경

# Authentication token (must match server)
auth.token = "deasea!1"

# Transport protocol - WebSocket Secure
transport.protocol = "wss"

# Log configuration
log.level = "info"
log.maxDays = 7

# Enable heartbeat
transport.heartbeatTimeout = 90

# Proxy configuration for LLM API
[[proxies]]
name = "llm-api"
type = "http"
localIP = "172.21.113.31"
localPort = 4000
customDomains = ["llm.local"]
```

## 예상 결과

### 성공 시
- ✅ frps 서비스가 포트 443에서 리스닝
- ✅ 로그에 "start frps service" 메시지
- ✅ WebSocket 프로토콜로 통신 준비 완료
- ✅ 회사 Spark에서 연결 시 일반 HTTPS 트래픽으로 보임

### 문제 발생 시

#### 포트 443 이미 사용 중
```bash
# 사용 중인 프로세스 확인
sudo lsof -i :443

# 해결 방법:
# 1. 기존 웹서버(nginx/apache)를 다른 포트로 이동
# 2. 또는 FRP를 8443 같은 다른 포트로 설정
#    (단, 회사 방화벽에서 8443도 허용하는지 확인 필요)
```

#### WebSocket 연결 실패
```bash
# 설정 파일 문법 확인
sudo frps -c /etc/frp/frps.toml verify

# 로그에서 오류 확인
sudo journalctl -u frps -n 100 --no-pager | grep -i error
```

#### 라우터 포트 포워딩 안 됨
```bash
# 외부에서 테스트 (다른 네트워크에서)
# 또는 온라인 포트 체커 사용
# https://www.yougetsignal.com/tools/open-ports/
```

## 다음 작업 (완료 후)

### 회사 Spark에서 작업
```bash
# Git pull
cd /home/score/frps && git pull

# 클라이언트 설정 업데이트
sudo cp configs/frpc.toml /etc/frp/frpc.toml

# 서비스 재시작
sudo systemctl restart frpc

# 연결 확인
sudo journalctl -u frpc -n 50
sudo tail -30 /var/log/frp/frpc.log

# 성공 시 로그:
# "login to server success"
# "start proxy success: [llm-api]"
```

## 참고 문서

- **FRP WebSocket 문서**: https://github.com/fatedier/frp#transport
- **설정 파일**: `configs/frps.toml`, `configs/frpc.toml`
- **이전 세션**: `.github/sessions/session-20251111-003-frps-install-minipc.md`

## 체크리스트

- [ ] 라우터 443 포트 포워딩 추가
- [ ] 포트 443 충돌 확인 및 해결
- [ ] configs/frps.toml 수정 (bindPort=443, protocol=wss)
- [ ] configs/frpc.toml 수정 (serverPort=443, protocol=wss)
- [ ] /etc/frp/frps.toml 업데이트
- [ ] frps 서비스 재시작
- [ ] 포트 443 리스닝 확인
- [ ] 방화벽 설정 (필요 시)
- [ ] Git 커밋 및 푸시
- [ ] 세션 파일 업데이트

---

**작업 시작**: 집 MiniPC에서 위 단계를 따라 FRP를 WebSocket(wss)으로 전환하세요.

**중요 포인트**:
1. 포트 443은 표준 HTTPS 포트 - 대부분의 방화벽에서 허용
2. WebSocket은 HTTP 업그레이드 - 일반 웹사이트처럼 보임
3. 패킷이 암호화되어 DPI로 FRP 탐지 불가능
