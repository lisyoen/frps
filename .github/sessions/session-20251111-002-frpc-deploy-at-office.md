# Session: session-20251111-002-frpc-deploy-at-office

## 세션 정보

- **세션 ID**: session-20251111-002-frpc-deploy-at-office
- **날짜**: 2025-11-11
- **상태**: ⏸️ 일시 중단 (네트워크 제한으로 FRP 연결 불가)
- **작업자**: 회사 Spark 장비에서 작업
- **이전 세션**: session-20251111-001-frp-setup (완료)
- **차단 이유**: 회사 방화벽에서 외부 IP(110.13.119.7) 접속 차단

## 작업 목적

회사 LLM 서버(172.21.113.31)에 FRP 클라이언트(frpc)를 설치하여 집에서 회사 LLM API에 접근할 수 있도록 구성

## 작업 환경

### 집 환경 (완료)
- ✅ miniPC (110.13.119.7): FRP 서버(frps) 설치 및 실행 완료
- ✅ Git 저장소: github.com/lisyoen/frps
- ✅ 설정 파일: configs/frps.toml (실제 값으로 커밋됨)

### 회사 환경 (일부 완료, 연결 차단)
- ✅ LLM 서버 (172.21.113.31): FRP 클라이언트(frpc) 설치 완료
- ✅ Hostname: spark-9ea9
- ✅ Architecture: ARM64 (aarch64)
- ✅ LLM 모델: Qwen3-Coder-30B (DGX Spark)
- ✅ LLM API 포트: 4000 (내부)
- ❌ 외부 연결: 차단됨 (ping, FRP 포트 7000, HTTP 포트 8081 모두 타임아웃)

## 작업 계획

### 1단계: 저장소 클론 및 환경 확인
```bash
# 회사 LLM 서버에서 실행
git clone https://github.com/lisyoen/frps.git
cd frps

# 현재 세션 파일 확인
cat .github/sessions/session-20251111-002-frpc-deploy-at-office.md

# 개발 환경 확인 (필요 시)
cat .github/development-environment.md
```

### 2단계: FRP 클라이언트 설치
```bash
# configs/frpc.toml 설정 확인
cat configs/frpc.toml

# 설정이 맞는지 검토:
# - serverAddr = "110.13.119.7" (miniPC 공인 IP)
# - serverPort = 7000
# - auth.token = "deasea!1"
# - localIP = "172.21.113.31" (LLM 서버 내부 IP)
# - localPort = 4000 (LLM API 포트)

# 자동 설치 실행
sudo bash scripts/install-frpc.sh

# 서비스 상태 확인
sudo systemctl status frpc
sudo journalctl -u frpc -n 50
```

### 3단계: 연결 테스트
```bash
# FRP 연결 테스트
bash scripts/test-frp.sh

# LLM API 테스트
bash scripts/test-llm-api.sh

# 또는 수동 테스트
curl -X POST http://110.13.119.7:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-Coder-30B",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### 4단계: 문제 해결 (필요 시)

#### 연결 실패 시
```bash
# 로그 확인
sudo journalctl -u frpc -n 100

# 네트워크 연결 확인
nc -zv 110.13.119.7 7000

# 방화벽 확인 (필요 시)
sudo iptables -L -n | grep 7000
```

#### 설정 수정이 필요한 경우
```bash
# frpc.toml 수정
sudo nano /etc/frp/frpc.toml

# 서비스 재시작
sudo systemctl restart frpc
sudo systemctl status frpc
```

## 예상 결과

### 성공 시
- ✅ frpc 서비스가 정상 실행 중 (systemctl status frpc → active (running))
- ✅ miniPC frps 서버와 정상 연결 (로그에 "login to server success" 표시)
- ✅ 집에서 `http://110.13.119.7:8081` 접속 시 LLM API 응답 받음
- ✅ `test-llm-api.sh` 실행 시 정상 응답

### 문제 발생 시
- 🔍 frpc 로그 확인: `sudo journalctl -u frpc -n 100`
- 🔍 frps 로그 확인 (miniPC에서): `sudo journalctl -u frps -n 100`
- 🔍 방화벽 확인: miniPC 7000, 8081 포트 개방 상태
- 🔍 네트워크 연결 확인: 회사 → miniPC 공인 IP 접근 가능 여부

## 테스트 방법

### miniPC에서 테스트 (집)
```bash
# frps 서버 상태 확인
sudo systemctl status frps

# 클라이언트 연결 확인
sudo journalctl -u frps | grep "client login"

# HTTP 프록시 테스트
curl http://localhost:8081/v1/models
```

### LLM 서버에서 테스트 (회사)
```bash
# frpc 클라이언트 상태 확인
sudo systemctl status frpc

# 로컬 LLM API 확인
curl http://localhost:4000/v1/models

# FRP 터널 통한 외부 접근 테스트 (miniPC 통해)
curl http://110.13.119.7:8081/v1/models
```

## 주의사항

1. **보안**
   - 현재 토큰(`deasea!1`)은 개발용
   - 프로덕션 사용 시 반드시 변경 필요
   - miniPC 방화벽 설정 확인 (7000, 8081 포트만 개방)

2. **네트워크**
   - 회사 방화벽에서 110.13.119.7:7000 접속 허용 필요
   - miniPC 공인 IP 변경 시 frpc.toml 업데이트 필요

3. **서비스 관리**
   - frpc는 systemd로 자동 시작됨
   - 서버 재부팅 후에도 자동 실행
   - 로그는 `journalctl -u frpc`로 확인

## 다음 작업 (완료 후)

1. **세션 완료 업데이트**
   ```bash
   # 이 파일의 "상태" 부분을 "완료 ✅"로 변경
   nano .github/sessions/session-20251111-002-frpc-deploy-at-office.md
   ```

2. **current-session.md 업데이트**
   ```bash
   # 현재 세션 정보 업데이트
   nano .github/current-session.md
   ```

3. **Git 커밋**
   ```bash
   git add .github/
   git commit -m "세션 session-20251111-002-frpc-deploy-at-office 완료: 회사 LLM 서버 FRP 클라이언트 설치"
   git push
   ```

4. **집에서 최종 테스트**
   - miniPC에서 git pull
   - 집 PC에서 LLM API 접근 테스트
   - VSCode에서 LLM 사용 테스트

## 참고 문서

- **설치 가이드**: `README.md`
- **프로젝트 목표**: `.github/project-goal.md`
- **개발 환경**: `.github/development-environment.md`
- **이전 세션**: `.github/sessions/session-20251111-001-frp-setup.md`

## 진행 상황 (회사에서 작업하며 업데이트)

### 실제 작업 결과 (2025-11-11)

#### ✅ 완료된 작업
- [x] 저장소 클론 완료 (이미 존재함)
- [x] configs/frpc.toml 설정 검토 완료
  - serverAddr: 110.13.119.7 (miniPC 공인 IP)
  - serverPort: 7000
  - auth.token: deasea!1
  - localIP: 172.21.113.31 (Spark 내부 IP)
  - localPort: 4000 (LLM API)
- [x] FRP 클라이언트 바이너리 설치
  - ⚠️ 처음 AMD64 다운로드 후 "Exec format error" 발생
  - ✅ ARM64(aarch64) 버전으로 재설치 완료
  - Binary: `/opt/frp/frpc`
- [x] systemd 서비스 생성 및 실행
  - Service: `/etc/systemd/system/frpc.service`
  - Config: `/etc/frp/frpc.toml`
  - Status: active (running)

#### ❌ 연결 실패 - 회사 네트워크 제한
- [x] frpc 서비스는 정상 실행 중
- [x] 하지만 miniPC(110.13.119.7:7000) 연결 실패
- [x] 로그 오류: `dial tcp 110.13.119.7:7000: i/o timeout`
- [x] 네트워크 테스트 결과:
  ```bash
  # Ping 테스트
  ping -c 3 110.13.119.7
  # 결과: 100% packet loss
  
  # Netcat 테스트
  nc -zv -w 5 110.13.119.7 7000
  # 결과: Connection timed out
  
  # HTTP 포트 테스트
  curl -I --connect-timeout 5 http://110.13.119.7:8081
  # 결과: Timeout was reached
  ```

#### 🔍 문제 원인 분석
**회사 네트워크 정책으로 외부 연결 차단**
- ❌ 외부 IP로 ping 불가
- ❌ 외부 특정 포트(7000, 8081) 연결 불가
- ⚠️ 아웃바운드 연결이 방화벽/프록시로 제한됨

#### 📝 해결 방안 (추후 작업 필요)
1. **네트워크 팀에 요청**
   - 회사 방화벽에서 110.13.119.7:7000 아웃바운드 허용 요청
   - 또는 특정 IP 대역 화이트리스트 추가

2. **대안 1: Cloudflare Tunnel 사용**
   - miniPC에 Cloudflare Tunnel 설치
   - FRP 대신 Cloudflare Tunnel로 회사 → 집 연결
   - 장점: HTTPS, 443 포트 사용 (일반적으로 열려있음)

3. **대안 2: 회사 내부 게이트웨이 서버 경유**
   - 회사에 외부 접속이 가능한 게이트웨이가 있다면 활용
   - SSH 터널링 또는 Proxy 경유

4. **대안 3: VPN 사용**
   - 회사 VPN이 있다면 VPN 경유로 접속
   - 또는 개인 VPN 서버 구축

#### 📋 현재 상태 (2025-11-11 10:16 업데이트)

**포트 변경 후 재테스트 완료**
- ✅ **miniPC (session-003)**: FRP 서버 포트 8000으로 변경 및 설치 완료
- ✅ **Spark 클라이언트**: 설정 파일 업데이트 (serverPort: 7000 → 8000)
- ✅ **서비스 재시작**: frpc 재시작 완료
- ❌ **연결 실패**: `dial tcp 110.13.119.7:8000: i/o timeout` (여전히 차단)

**결론**
- FRP 설정은 완벽: 포트 8000으로 통일 완료
- 회사 방화벽 문제: 포트 7000뿐만 아니라 8000도 차단됨
- 근본 원인: 회사 네트워크 정책으로 외부 IP 특정 포트 아웃바운드 차단
- **작업 상태**: ⏸️ 대기 (네트워크 정책 변경 또는 대안 필요)

---

- **FRP 클라이언트 설치**: ✅ 완료
- **설정 파일**: ✅ 포트 8000으로 업데이트 완료
- **서비스 실행**: ✅ 정상
- **네트워크 연결**: ❌ 차단됨 (회사 정책, 포트 8000도 동일)

---

*아래 체크리스트는 원래 계획*

- [x] 저장소 클론 완료
- [x] configs/frpc.toml 설정 검토
- [x] install-frpc.sh 실행 (수동 설치로 대체)
- [x] frpc 서비스 정상 실행 확인
- [❌] miniPC frps와 연결 확인 → **네트워크 차단으로 실패**
- [❌] test-frp.sh 테스트 성공 → **연결 불가로 스킵**
- [❌] test-llm-api.sh 테스트 성공 → **연결 불가로 스킵**
- [ ] 세션 파일 업데이트 및 커밋 (지금 진행 중)

---

**작업 시작**: 회사 LLM 서버에서 이 파일을 열고 위 단계를 따라 진행하세요.
