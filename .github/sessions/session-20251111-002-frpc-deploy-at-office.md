# Session: session-20251111-002-frpc-deploy-at-office

## 세션 정보

- **세션 ID**: session-20251111-002-frpc-deploy-at-office
- **날짜**: 2025-11-11
- **상태**: 대기 중 ⏸️
- **작업자**: 회사 LLM 서버에서 재개 예정
- **이전 세션**: session-20251111-001-frp-setup (완료)

## 작업 목적

회사 LLM 서버(172.21.113.31)에 FRP 클라이언트(frpc)를 설치하여 집에서 회사 LLM API에 접근할 수 있도록 구성

## 작업 환경

### 집 환경 (현재 완료)
- ✅ miniPC (110.13.119.7): FRP 서버(frps) 설치 및 실행 완료
- ✅ Git 저장소: github.com/lisyoen/frps
- ✅ 설정 파일: configs/frps.toml (실제 값으로 커밋됨)

### 회사 환경 (작업 예정)
- 🔄 LLM 서버 (172.21.113.31): FRP 클라이언트(frpc) 설치 필요
- 🔄 LLM 모델: Qwen3-Coder-30B (DGX Spark)
- 🔄 LLM API 포트: 4000 (내부), 8081 (외부 HTTP 프록시)

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

*아래 체크리스트를 작업하며 업데이트하세요*

- [ ] 저장소 클론 완료
- [ ] configs/frpc.toml 설정 검토
- [ ] install-frpc.sh 실행
- [ ] frpc 서비스 정상 실행 확인
- [ ] miniPC frps와 연결 확인
- [ ] test-frp.sh 테스트 성공
- [ ] test-llm-api.sh 테스트 성공
- [ ] 세션 파일 업데이트 및 커밋

---

**작업 시작**: 회사 LLM 서버에서 이 파일을 열고 위 단계를 따라 진행하세요.
