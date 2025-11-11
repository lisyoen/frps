# Session: session-20251111-003-frps-install-minipc

## 세션 정보

- **세션 ID**: session-20251111-003-frps-install-minipc
- **날짜**: 2025-11-11
- **상태**: 진행 중 🔄
- **작업자**: 집 MiniPC
- **이전 세션**: session-20251111-002-frpc-deploy-at-office (일시 중단)

## 작업 목적

집 MiniPC(192.168.50.196)에 FRP 서버(frps)를 설치하여 회사 LLM 서버가 연결할 수 있는 중계 서버 구축

## 현재 상황

### 완료된 작업
- ✅ session-20251111-001: FRP 설정 파일 및 설치 스크립트 작성 완료
- ✅ session-20251111-002: 회사 Spark 장비에 FRP 클라이언트(frpc) 설치 완료

### 미완료 작업
- ✅ 집 MiniPC에 FRP 서버(frps) 설치 완료
- ✅ 포트 변경: 7000 → 8000 (공유기 8000~8999 범위 제한)
- ✅ frps 정상 실행 중 (포트 8000, 8081 리스닝)
- ⏳ 회사 frpc 재설정 필요 (serverPort를 8000으로 변경)
- ⏳ 회사 frpc 재시작 후 연결 테스트 필요

## 작업 환경

### 집 MiniPC
- **Hostname**: MiniPC
- **OS**: Linux (Ubuntu-based)
- **Architecture**: x86_64 (amd64)
- **내부 IP**: 192.168.50.196
- **공인 IP**: 110.13.119.7
- **Gateway**: 192.168.50.1 (ASUS RT-AX53U)
- **개방 포트**: 22, 80, 3000, 3389, 5432, 8080, 8088, 8500, 8888
- **필요 포트**: 7000 (FRP 제어), 8081 (FRP HTTP 프록시)

### 회사 Spark (대기 중)
- **상태**: FRP 클라이언트 설치 완료, MiniPC 연결 대기 중
- **IP**: 172.21.113.31
- **LLM Port**: 4000
- **연결 대상**: 110.13.119.7:7000 (MiniPC FRP 서버)

## 작업 계획

### 1단계: 저장소 확인
```bash
# MiniPC에서 실행
cd ~
ls -la frps  # 저장소 존재 확인

# 없으면 클론
git clone https://github.com/lisyoen/frps.git
cd frps
git pull  # 최신 상태로 업데이트
```

### 2단계: FRP 서버 설치
```bash
# 설정 파일 확인
cat configs/frps.toml

# 주요 설정 확인:
# - bindPort = 7000 (제어 포트)
# - vhostHTTPPort = 8081 (HTTP 프록시)
# - auth.token = "deasea!1" (회사 frpc와 동일)

# 자동 설치 실행
sudo bash scripts/install-frps.sh

# 예상 작업:
# - FRP v0.65.0 다운로드 (x86_64)
# - /opt/frp/frps 설치
# - /etc/frp/frps.toml 설정
# - systemd 서비스 등록
# - 자동 시작
```

### 3단계: 서비스 상태 확인
```bash
# 서비스 실행 확인
sudo systemctl status frps

# 로그 확인
sudo journalctl -u frps -n 50

# 포트 리스닝 확인
sudo netstat -tlnp | grep -E '7000|8081'
# 또는
sudo ss -tlnp | grep -E '7000|8081'
```

### 4단계: 방화벽 설정 (필요 시)
```bash
# ufw 사용 중인 경우
sudo ufw allow 7000/tcp comment 'FRP Control Port'
sudo ufw allow 8081/tcp comment 'FRP HTTP Proxy'
sudo ufw status

# iptables 사용 중인 경우
sudo iptables -A INPUT -p tcp --dport 7000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8081 -j ACCEPT
sudo iptables -L -n | grep -E '7000|8081'
```

### 5단계: 라우터 포트 포워딩 확인
```bash
# 공인 IP 확인
curl ifconfig.me
# 예상: 110.13.119.7

# 라우터(192.168.50.1)에서 설정 필요:
# - 외부 7000 → 192.168.50.196:7000
# - 외부 8081 → 192.168.50.196:8081
```

**⚠️ 주의**: ASUS RT-AX53U 라우터 관리 페이지에서 포트 포워딩 설정 필요
- 웹 브라우저: http://192.168.50.1
- 포트 포워딩 → Virtual Server/Port Forwarding
- 7000, 8081 포트를 192.168.50.196으로 매핑

### 6단계: 연결 테스트
```bash
# 로컬 테스트
curl http://localhost:8081/v1/models
# 예상: frpc 연결 전이므로 에러 또는 타임아웃 (정상)

# FRP 서버 로그 모니터링
sudo journalctl -u frps -f

# 회사 frpc가 연결되면 로그에 다음과 같은 메시지 출력:
# "client login info: ... login from xxx.xxx.xxx.xxx"
# "start proxy success: proxy: [llm-api]"
```

### 7단계: 회사 Spark에서 재연결 테스트
```bash
# 회사 Spark 장비에서 실행 (나중에)
sudo systemctl restart frpc
sudo journalctl -u frpc -n 50

# 성공 시 로그:
# "login to server success"
# "start proxy success: [llm-api]"
```

### 8단계: 최종 테스트
```bash
# MiniPC 또는 집 PC에서 실행
cd ~/frps
bash scripts/test-frp.sh
bash scripts/test-llm-api.sh

# 또는 수동 테스트
curl -H "Host: llm.local" http://110.13.119.7:8081/v1/models

# 성공 시: 회사 LLM 서버의 모델 목록 반환
```

## 예상 결과

### 성공 시
- ✅ frps 서비스 정상 실행 (`systemctl status frps`)
- ✅ 포트 7000, 8081 리스닝 중 (`netstat` 확인)
- ✅ 회사 frpc가 연결 성공 (frps 로그에 "client login" 표시)
- ✅ 집에서 `http://110.13.119.7:8081` 접속 시 LLM API 응답

### 문제 발생 시

#### 서비스 시작 실패
```bash
# 로그 확인
sudo journalctl -u frps -n 100

# 일반적인 문제:
# - 포트 충돌: 7000, 8081 포트가 이미 사용 중
# - 설정 오류: frps.toml 문법 오류
# - 권한 문제: /var/log/frp/ 디렉토리 권한
```

#### 포트 리스닝 안 됨
```bash
# 포트 충돌 확인
sudo netstat -tlnp | grep -E '7000|8081'
sudo lsof -i :7000
sudo lsof -i :8081

# 충돌 프로세스 종료 후 재시작
sudo systemctl restart frps
```

#### 외부 접속 안 됨
```bash
# 방화벽 확인
sudo ufw status verbose
sudo iptables -L -n

# 라우터 포트 포워딩 확인
# - 브라우저에서 192.168.50.1 접속
# - Port Forwarding 설정 확인
```

## MiniPC 작업 결과 (2025-11-11 10:14)

### 완료된 작업
1. ✅ 포트 충돌 문제 해결
   - 공유기 제한: 8000~8999 범위만 외부 포트 포워딩 가능
   - 기존 7000 → 8000으로 변경
   - configs/frps.toml, configs/frpc.toml 수정

2. ✅ frps 서비스 재시작
   - 설정 파일 적용: `/etc/frp/frps.toml`
   - 서비스 정상 실행 확인
   ```
   ● frps.service - FRP Server (frps)
      Active: active (running)
      frps tcp listen on 0.0.0.0:8000
      http service listen on 0.0.0.0:8081
   ```

3. ✅ Git 동기화 완료
   - 커밋: "포트 변경: 7000 -> 8000 (공유기 8000~8999 범위 제한)"
   - 푸시 완료 → 회사에서 git pull 가능

### 회사에서 수행할 작업

**중요**: 회사 Spark 장비에서 다음 작업 필요

1. **Git Pull 및 설정 파일 업데이트**
   ```bash
   cd ~/frps  # 또는 저장소 경로
   git pull
   
   # 변경된 frpc.toml 확인
   cat configs/frpc.toml
   # serverPort = 8000 으로 변경된 것 확인
   ```

2. **frpc 설정 파일 적용**
   ```bash
   sudo cp configs/frpc.toml /etc/frp/frpc.toml
   sudo chown frpc:frpc /etc/frp/frpc.toml
   sudo chmod 600 /etc/frp/frpc.toml
   ```

3. **frpc 서비스 재시작**
   ```bash
   sudo systemctl restart frpc
   sudo systemctl status frpc
   ```

4. **연결 확인**
   ```bash
   # frpc 로그 확인
   sudo journalctl -u frpc -n 50
   
   # 성공 시 로그:
   # "login to server success"
   # "start proxy success: [llm-api]"
   ```

5. **LLM API 테스트**
   ```bash
   # 회사 내부에서 테스트
   curl http://localhost:4000/v1/models
   
   # 또는 MiniPC/집에서 외부 테스트
   curl -H "Host: llm.local" http://110.13.119.7:8081/v1/models
   ```

### 사용 중인 포트 (8000~8999 범위)
- 8000: frps 제어 포트 ✅ 사용 중
- 8080: 다른 서비스
- 8081: frps HTTP 프록시 ✅ 사용 중
- 8088: 다른 서비스
- 8090, 8282, 8581, 8880: 다른 서비스들

## 작업 계획

### 1단계: 저장소 확인
```bash
# MiniPC에서 실행
cd ~
ls -la frps  # 저장소 존재 확인

# 없으면 클론
git clone https://github.com/lisyoen/frps.git
cd frps
git pull  # 최신 상태로 업데이트
```

### 2단계: FRP 서버 설치
```bash
# 설정 파일 확인
cat configs/frps.toml

# 주요 설정 확인:
# - bindPort = 7000 (제어 포트)
# - vhostHTTPPort = 8081 (HTTP 프록시)
# - auth.token = "deasea!1" (회사 frpc와 동일)

# 자동 설치 실행
sudo bash scripts/install-frps.sh

# 예상 작업:
# - FRP v0.65.0 다운로드 (x86_64)
# - /opt/frp/frps 설치
# - /etc/frp/frps.toml 설정
# - systemd 서비스 등록
# - 자동 시작
```

### 3단계: 서비스 상태 확인
```bash
# 서비스 실행 확인
sudo systemctl status frps

# 로그 확인
sudo journalctl -u frps -n 50

# 포트 리스닝 확인
sudo netstat -tlnp | grep -E '7000|8081'
# 또는
sudo ss -tlnp | grep -E '7000|8081'
```

### 4단계: 방화벽 설정 (필요 시)
```bash
# ufw 사용 중인 경우
sudo ufw allow 7000/tcp comment 'FRP Control Port'
sudo ufw allow 8081/tcp comment 'FRP HTTP Proxy'
sudo ufw status

# iptables 사용 중인 경우
sudo iptables -A INPUT -p tcp --dport 7000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8081 -j ACCEPT
sudo iptables -L -n | grep -E '7000|8081'
```

### 5단계: 라우터 포트 포워딩 확인
```bash
# 공인 IP 확인
curl ifconfig.me
# 예상: 110.13.119.7

# 라우터(192.168.50.1)에서 설정 필요:
# - 외부 7000 → 192.168.50.196:7000
# - 외부 8081 → 192.168.50.196:8081
```

**⚠️ 주의**: ASUS RT-AX53U 라우터 관리 페이지에서 포트 포워딩 설정 필요
- 웹 브라우저: http://192.168.50.1
- 포트 포워딩 → Virtual Server/Port Forwarding
- 7000, 8081 포트를 192.168.50.196으로 매핑

### 6단계: 연결 테스트
```bash
# 로컬 테스트
curl http://localhost:8081/v1/models
# 예상: frpc 연결 전이므로 에러 또는 타임아웃 (정상)

# FRP 서버 로그 모니터링
sudo journalctl -u frps -f

# 회사 frpc가 연결되면 로그에 다음과 같은 메시지 출력:
# "client login info: ... login from xxx.xxx.xxx.xxx"
# "start proxy success: proxy: [llm-api]"
```

### 7단계: 회사 Spark에서 재연결 테스트
```bash
# 회사 Spark 장비에서 실행 (나중에)
sudo systemctl restart frpc
sudo journalctl -u frpc -n 50

# 성공 시 로그:
# "login to server success"
# "start proxy success: [llm-api]"
```

### 8단계: 최종 테스트
```bash
# MiniPC 또는 집 PC에서 실행
cd ~/frps
bash scripts/test-frp.sh
bash scripts/test-llm-api.sh

# 또는 수동 테스트
curl -H "Host: llm.local" http://110.13.119.7:8081/v1/models

# 성공 시: 회사 LLM 서버의 모델 목록 반환
```

## 예상 결과

### 성공 시
- ✅ frps 서비스 정상 실행 (`systemctl status frps`)
- ✅ 포트 7000, 8081 리스닝 중 (`netstat` 확인)
- ✅ 회사 frpc가 연결 성공 (frps 로그에 "client login" 표시)
- ✅ 집에서 `http://110.13.119.7:8081` 접속 시 LLM API 응답

### 문제 발생 시

#### 서비스 시작 실패
```bash
# 로그 확인
sudo journalctl -u frps -n 100

# 일반적인 문제:
# - 포트 충돌: 7000, 8081 포트가 이미 사용 중
# - 설정 오류: frps.toml 문법 오류
# - 권한 문제: /var/log/frp/ 디렉토리 권한
```

#### 포트 리스닝 안 됨
```bash
# 포트 충돌 확인
sudo netstat -tlnp | grep -E '7000|8081'
sudo lsof -i :7000
sudo lsof -i :8081

# 충돌 프로세스 종료 후 재시작
sudo systemctl restart frps
```

#### 외부 접속 안 됨
```bash
# 방화벽 확인
sudo ufw status verbose
sudo iptables -L -n

# 라우터 포트 포워딩 확인
# - 브라우저에서 192.168.50.1 접속
# - Port Forwarding 설정 확인
```

## MiniPC 작업 결과 (2025-11-11 10:14)

### 완료된 작업
1. ✅ 포트 충돌 문제 해결
   - 공유기 제한: 8000~8999 범위만 외부 포트 포워딩 가능
   - 기존 7000 → 8000으로 변경
   - configs/frps.toml, configs/frpc.toml 수정

2. ✅ frps 서비스 재시작
   - 설정 파일 적용: `/etc/frp/frps.toml`
   - 서비스 정상 실행 확인
   ```
   ● frps.service - FRP Server (frps)
      Active: active (running)
      frps tcp listen on 0.0.0.0:8000
      http service listen on 0.0.0.0:8081
   ```

3. ✅ Git 동기화 완료
   - 커밋: "포트 변경: 7000 -> 8000 (공유기 8000~8999 범위 제한)"
   - 푸시 완료 → 회사에서 git pull 가능

### 회사에서 수행할 작업

**중요**: 회사 Spark 장비에서 다음 작업 필요

1. **Git Pull 및 설정 파일 업데이트**
   ```bash
   cd ~/frps  # 또는 저장소 경로
   git pull
   
   # 변경된 frpc.toml 확인
   cat configs/frpc.toml
   # serverPort = 8000 으로 변경된 것 확인
   ```

2. **frpc 설정 파일 적용**
   ```bash
   sudo cp configs/frpc.toml /etc/frp/frpc.toml
   sudo chown frpc:frpc /etc/frp/frpc.toml
   sudo chmod 600 /etc/frp/frpc.toml
   ```

3. **frpc 서비스 재시작**
   ```bash
   sudo systemctl restart frpc
   sudo systemctl status frpc
   ```

4. **연결 확인**
   ```bash
   # frpc 로그 확인
   sudo journalctl -u frpc -n 50
   
   # 성공 시 로그:
   # "login to server success"
   # "start proxy success: [llm-api]"
   ```

5. **LLM API 테스트**
   ```bash
   # 회사 내부에서 테스트
   curl http://localhost:4000/v1/models
   
   # 또는 MiniPC/집에서 외부 테스트
   curl -H "Host: llm.local" http://110.13.119.7:8081/v1/models
   ```

### 사용 중인 포트 (8000~8999 범위)
- 8000: frps 제어 포트 ✅ 사용 중
- 8080: 다른 서비스
- 8081: frps HTTP 프록시 ✅ 사용 중
- 8088: 다른 서비스
- 8090, 8282, 8581, 8880: 다른 서비스들

---

**작업 시작**: 집 MiniPC에서 위 단계를 따라 FRP 서버를 설치하세요.
**중요**: 라우터 포트 포워딩(7000, 8081)을 꼭 설정해야 외부에서 접속 가능합니다!
