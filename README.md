# Fast Reverse Proxy Server (FRPS)

회사 내부망의 LLM 서버를 외부(집)에서 안전하게 호출하기 위한 FRP 기반 역방향 프록시 환경

## 📋 목차

- [프로젝트 개요](#프로젝트-개요)
- [시스템 구성](#시스템-구성)
- [설치 방법](#설치-방법)
- [설정](#설정)
- [사용 방법](#사용-방법)
- [테스트](#테스트)
- [문제 해결](#문제-해결)

---

## 🎯 프로젝트 개요

본 프로젝트는 **FRP(Fast Reverse Proxy)** 를 사용하여 회사 폐쇄망 내부의 LLM 서버를 외부에서 접근 가능하도록 만듭니다.

### 왜 FRP인가?

- **회사 네트워크 특성**: 외부에서 직접 접근 불가, outbound 트래픽만 허용
- **SSH/VPN 불가**: 일반적인 터널링 방식 사용 불가
- **해결책**: 사무실 → 집 방향의 역방향 연결로 터널 구축

### 주요 기능

- ✅ 역방향 HTTP 프록시 (사무실 → 집)
- ✅ LLM API 중계 (Qwen3-Coder-30B)
- ✅ 토큰 기반 인증
- ✅ systemd 서비스 자동화
- ✅ 로그 관리 및 모니터링

---

## 🏗️ 시스템 구성

```
[회사 내부망]                    [인터넷]                [집]
┌──────────────────┐            
│ LLM 서버          │            
│ 172.21.113.31    │            
│ Port: 4000       │            
└────────┬─────────┘            
         │                      
         │ frpc (client)        
         │ Outbound →           
         └──────────────────────────→  ┌─────────────────┐
                                       │ miniPC          │
                                       │ 110.13.119.7    │
                                       │ frps (server)   │
                                       │ Port: 7000,8081 │
                                       └────────┬────────┘
                                                │
                                                ↓
                                       ┌─────────────────┐
                                       │ 집 PC           │
                                       │ HTTP Client     │
                                       └─────────────────┘
```

### 역할 분담

| 구분 | 호스트 | 역할 | 소프트웨어 |
|------|--------|------|------------|
| **Server** | miniPC (집) | FRP 서버, 외부 접속 중계 | frps |
| **Client** | LLM 서버 (회사) | FRP 클라이언트, 역방향 연결 | frpc |
| **User** | 집 PC | HTTP 요청 발신 | curl, Postman 등 |

### 포트 구성

- **7000**: FRP 제어 포트 (frpc ↔ frps)
- **8081**: HTTP 프록시 포트 (외부 → LLM API)
- **4000**: LLM API 원본 포트 (내부망)

---

## 🚀 설치 방법

### 1. miniPC에 FRP 서버 설치

```bash
# 저장소 클론
git clone https://github.com/lisyoen/frps.git
cd frps

# 서버 설치 스크립트 실행 (root 권한 필요)
sudo bash scripts/install-frps.sh
```

설치 스크립트는 다음을 수행합니다:
- FRP v0.65.0 바이너리 다운로드 및 설치
- 설정 파일 생성 (`/etc/frp/frps.toml`)
- systemd 서비스 등록 및 시작
- 자동 재시작 설정

### 2. 사무실 LLM 서버에 FRP 클라이언트 설치

```bash
# 저장소 클론 (사무실 서버에서 실행)
git clone https://github.com/lisyoen/frps.git
cd frps

# 클라이언트 설치 스크립트 실행 (root 권한 필요)
sudo bash scripts/install-frpc.sh
```

---

## ⚙️ 설정

### FRP 서버 설정 (miniPC)

파일: `/etc/frp/frps.toml`

```toml
bindAddr = "0.0.0.0"
bindPort = 7000
auth.token = "deasea!1"
vhostHTTPPort = 8081
log.level = "info"
log.maxDays = 7
transport.heartbeatTimeout = 90
```

**주요 설정:**
- `bindPort`: 클라이언트 연결 포트 (7000)
- `auth.token`: 인증 토큰 (클라이언트와 일치해야 함)
- `vhostHTTPPort`: HTTP 프록시 포트 (8081)

### FRP 클라이언트 설정 (사무실 LLM 서버)

파일: `/etc/frp/frpc.toml`

```toml
serverAddr = "110.13.119.7"  # miniPC 공인 IP
serverPort = 7000
auth.token = "deasea!1"
log.level = "info"
log.maxDays = 7
transport.heartbeatTimeout = 90

[[proxies]]
name = "llm-api"
type = "http"
localIP = "172.21.113.31"
localPort = 4000
customDomains = ["llm.local"]
```

**주요 설정:**
- `serverAddr`: miniPC의 공인 IP 주소
- `localIP`: LLM API 서버 IP (172.21.113.31)
- `localPort`: LLM API 포트 (4000)
- `customDomains`: 가상 호스트 이름 (Host 헤더 사용)

---

## 🎮 사용 방법

### 서비스 제어 (miniPC)

```bash
# 서비스 시작
sudo systemctl start frps

# 서비스 중지
sudo systemctl stop frps

# 서비스 재시작
sudo systemctl restart frps

# 서비스 상태 확인
sudo systemctl status frps

# 로그 확인 (실시간)
sudo journalctl -u frps -f

# 로그 확인 (최근 50줄)
sudo journalctl -u frps -n 50
```

### 서비스 제어 (사무실 LLM 서버)

```bash
# 서비스 시작
sudo systemctl start frpc

# 서비스 상태 확인
sudo systemctl status frpc

# 로그 확인
sudo journalctl -u frpc -f
```

### LLM API 호출 (집 PC에서)

#### 1. 모델 목록 조회

```bash
curl -H "Host: llm.local" \
     http://110.13.119.7:8081/v1/models
```

#### 2. Chat Completion API 호출

```bash
curl -H "Host: llm.local" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer sk-Dwgun2yU_YQkounRcLEuGA" \
     -d '{
       "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
       "messages": [
         {"role": "user", "content": "Hello, how are you?"}
       ],
       "max_tokens": 100,
       "temperature": 0.7
     }' \
     http://110.13.119.7:8081/v1/chat/completions
```

**주의:** `Host: llm.local` 헤더는 필수입니다. FRP가 이를 통해 프록시를 식별합니다.

---

## 🧪 테스트

### 전체 연결 테스트

```bash
cd ~/frps
bash scripts/test-frp.sh
```

테스트 항목:
1. FRP 서버 상태 확인
2. FRP 클라이언트 상태 확인
3. FRP 제어 포트 연결 테스트 (7000)
4. FRP HTTP 포트 연결 테스트 (8081)
5. LLM API 접근 테스트

### LLM API 상세 테스트

```bash
cd ~/frps
bash scripts/test-llm-api.sh
```

테스트 항목:
1. `/v1/models` 엔드포인트 테스트
2. `/v1/chat/completions` 엔드포인트 테스트

---

## 🔧 문제 해결

### 1. FRP 서버가 시작되지 않음

**원인 확인:**
```bash
sudo journalctl -u frps -n 50
```

**가능한 원인:**
- 포트 7000 또는 8081이 이미 사용 중
- 설정 파일 문법 오류
- 권한 문제

**해결:**
```bash
# 포트 사용 확인
sudo netstat -tlnp | grep -E '7000|8081'

# 설정 파일 문법 확인
/opt/frp/frps -c /etc/frp/frps.toml --verify

# 서비스 재시작
sudo systemctl restart frps
```

### 2. FRP 클라이언트 연결 실패

**원인 확인:**
```bash
sudo journalctl -u frpc -n 50
```

**가능한 원인:**
- miniPC 공인 IP가 변경됨
- 인증 토큰 불일치
- 방화벽 차단

**해결:**
```bash
# miniPC 공인 IP 확인 (miniPC에서 실행)
curl ifconfig.me

# frpc.toml의 serverAddr 업데이트
sudo vi /etc/frp/frpc.toml

# 서비스 재시작
sudo systemctl restart frpc
```

### 3. LLM API 호출 실패

**원인 확인:**
```bash
# frpc 로그 확인 (사무실 서버)
sudo journalctl -u frpc -f

# LLM API 직접 테스트 (사무실 서버)
curl http://172.21.113.31:4000/v1/models
```

**가능한 원인:**
- LLM 서버가 다운되어 있음
- frpc 설정의 localIP/localPort 오류
- Host 헤더 누락

**해결:**
```bash
# Host 헤더 반드시 포함
curl -H "Host: llm.local" http://110.13.119.7:8081/v1/models
```

### 4. 로그 파일 크기 증가

로그는 `/var/log/frp/` 디렉토리에 저장되며, `maxDays = 7` 설정으로 7일 후 자동 삭제됩니다.

**수동 정리:**
```bash
sudo rm -f /var/log/frp/*.log
sudo systemctl restart frps
sudo systemctl restart frpc
```

---

## 📊 모니터링

### 실시간 로그 모니터링

```bash
# FRP 서버 로그 (miniPC)
sudo journalctl -u frps -f

# FRP 클라이언트 로그 (사무실)
sudo journalctl -u frpc -f
```

### 서비스 상태 확인

```bash
# 서비스 실행 중인지 확인
systemctl is-active frps
systemctl is-active frpc

# 상세 상태 확인
systemctl status frps --no-pager -l
```

### 네트워크 연결 확인

```bash
# FRP 포트 리스닝 확인
sudo netstat -tlnp | grep -E '7000|8081'

# 활성 연결 확인
sudo netstat -tnp | grep frp
```

---

## 🔐 보안 고려사항

### 현재 보안 수준

- ✅ 토큰 기반 인증 (`auth.token`)
- ✅ 특정 포트만 오픈 (7000, 8081)
- ⚠️ HTTP 통신 (암호화 없음)

### 향후 개선 계획

1. **HTTPS 적용**: 8443 포트로 TLS 암호화 통신
2. **OAuth2/JWT**: 토큰 인증 강화
3. **Cloudflare Tunnel**: DDNS 없이 안전한 접근
4. **Rate Limiting**: API 호출 빈도 제한
5. **IP 화이트리스트**: 특정 IP만 접근 허용

---

## 📚 참고 자료

- [FRP GitHub](https://github.com/fatedier/frp)
- [FRP 공식 문서](https://github.com/fatedier/frp/blob/dev/README.md)
- [프로젝트 목표](.github/project-goal.md)
- [개발 환경 정보](.github/development-environment.md)

---

## 🤝 기여

버그 리포트, 기능 제안, 풀 리퀘스트 환영합니다!

---

## 📄 라이선스

이 프로젝트는 개인 사용 목적으로 만들어졌습니다.

---

## 👤 작성자

**이창연** (lisyoen@gmail.com)

- GitHub: [@lisyoen](https://github.com/lisyoen)
- Date: 2025-11-11

