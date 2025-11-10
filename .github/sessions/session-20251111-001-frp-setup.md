# Session: FRP 역방향 프록시 구축

**세션 ID**: session-20251111-001-frp-setup  
**생성일**: 2025-11-11  
**완료일**: 2025-11-11  
**상태**: 완료 ✅

---

## 작업 목적
회사 내부망의 LLM 서버(172.21.113.31:4000)를 외부(집)에서 안전하게 호출할 수 있도록 Fast Reverse Proxy (FRP) 환경 구축

### 시스템 구성
- **사무실 LLM 서버**: frpc 클라이언트 실행 → miniPC로 아웃바운드 연결
- **miniPC (집)**: frps 서버 실행 → 외부 접속 중계 (포트 7000, 8081)
- **집 PC**: HTTP 요청으로 miniPC를 통해 LLM API 호출

---

## 완료된 작업

### ✅ 1단계: FRP 바이너리 다운로드 및 설치
- FRP v0.65.0 최신 버전 확인
- x86_64 (amd64) 아키텍처 확인
- 자동 다운로드 스크립트 포함

### ✅ 2단계: FRP 서버 설정 (miniPC)
- `configs/frps.toml` 파일 작성
  - bindPort: 7000 (제어 포트)
  - vhostHTTPPort: 8081 (HTTP 포트)
  - auth.token: "deasea!1"
  - 로그 관리 설정 (7일 보관)

### ✅ 3단계: FRP 클라이언트 설정 (사무실)
- `configs/frpc.toml` 파일 작성
  - serverAddr: 110.13.119.7 (miniPC 공인 IP)
  - serverPort: 7000
  - LLM API 프록시 설정 (172.21.113.31:4000)
  - customDomains: ["llm.local"]

### ✅ 4단계: systemd 서비스 등록
- 설치 스크립트에 systemd 서비스 자동 등록 기능 포함
- 자동 시작, 재시작 설정
- 로그 자동 관리 (/var/log/frp/)

### ✅ 5단계: 배포 자동화
- `scripts/install-frps.sh` 작성 (miniPC용)
  - FRP 다운로드 및 설치
  - 설정 파일 배포
  - systemd 서비스 등록
  - 자동 시작 및 상태 확인
- `scripts/install-frpc.sh` 작성 (사무실용)
  - 동일한 자동화 기능

### ✅ 6단계: 테스트 및 검증
- `scripts/test-frp.sh` 작성
  - FRP 서버/클라이언트 상태 확인
  - 포트 연결 테스트 (7000, 8081)
  - LLM API 기본 접근 테스트
- `scripts/test-llm-api.sh` 작성
  - `/v1/models` 엔드포인트 테스트
  - `/v1/chat/completions` 추론 테스트

### ✅ 7단계: 문서화
- `README.md` 상세 작성
  - 프로젝트 개요 및 시스템 구성도
  - 단계별 설치 가이드
  - 설정 파일 설명
  - 사용 방법 및 명령어
  - 테스트 절차
  - 문제 해결 가이드
  - 모니터링 방법
  - 보안 고려사항

---

## 진행 상황

### 2025-11-11

#### 완료 항목
1. ✅ FRP v0.65.0 최신 버전 확인
2. ✅ FRP 서버 설정 파일 작성 (frps.toml)
3. ✅ FRP 클라이언트 설정 파일 작성 (frpc.toml)
4. ✅ FRP 서버 설치 스크립트 작성 (install-frps.sh)
5. ✅ FRP 클라이언트 설치 스크립트 작성 (install-frpc.sh)
6. ✅ 연결 테스트 스크립트 작성 (test-frp.sh)
7. ✅ LLM API 테스트 스크립트 작성 (test-llm-api.sh)
8. ✅ README.md 상세 문서화
9. ✅ Git 커밋 및 푸시

---

## 생성된 파일 목록

### 설정 파일
- `configs/frps.toml` - FRP 서버 설정
- `configs/frpc.toml` - FRP 클라이언트 설정

### 스크립트
- `scripts/install-frps.sh` - FRP 서버 자동 설치 (실행 권한 부여됨)
- `scripts/install-frpc.sh` - FRP 클라이언트 자동 설치 (실행 권한 부여됨)
- `scripts/test-frp.sh` - 연결 테스트 (실행 권한 부여됨)
- `scripts/test-llm-api.sh` - LLM API 테스트 (실행 권한 부여됨)

### 문서
- `README.md` - 프로젝트 전체 문서 (1000+ 줄)

---

## 기술 정보

### FRP (Fast Reverse Proxy)
- **버전**: v0.65.0 (2024-09-25 릴리스)
- **GitHub**: https://github.com/fatedier/frp
- **다운로드 URL**: https://github.com/fatedier/frp/releases/download/v0.65.0/frp_0.65.0_linux_amd64.tar.gz
- **아키텍처**: x86_64 (amd64)

### 네트워크 정보
- **miniPC IP**: 192.168.50.196 (내부), 110.13.119.7 (공인)
- **LLM 서버 IP**: 172.21.113.31
- **LLM API 포트**: 4000
- **FRP 제어 포트**: 7000
- **FRP HTTP 포트**: 8081

### 보안
- 인증 토큰: deasea!1
- HTTP 통신 (현재)
- 향후 HTTPS(8443) 적용 예정

---

## 결정 사항

1. **FRP 사용 이유**: SSH/VPN 불가능한 폐쇄망 환경에서 역방향 터널링 필요
2. **포트 선택**: 7000(제어), 8081(HTTP) - 방화벽 정책 고려
3. **인증 방식**: 토큰 기반, 향후 OAuth2/JWT 검토
4. **설정 형식**: TOML (FRP v0.52.0+부터 INI 대신 TOML 권장)
5. **로그 관리**: systemd journal + /var/log/frp/ (7일 보관)

---

## 다음 단계 (실제 배포)

### miniPC에서 실행
```bash
cd ~/frps
sudo bash scripts/install-frps.sh
```

### 사무실 LLM 서버에서 실행
```bash
cd /path/to/frps
sudo bash scripts/install-frpc.sh
```

### 연결 테스트 (miniPC 또는 집 PC에서)
```bash
cd ~/frps
bash scripts/test-frp.sh
bash scripts/test-llm-api.sh
```

### LLM API 호출 예시 (집 PC에서)
```bash
# 모델 목록 조회
curl -H "Host: llm.local" http://110.13.119.7:8081/v1/models

# Chat Completion
curl -H "Host: llm.local" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer sk-Dwgun2yU_YQkounRcLEuGA" \
     -d '{
       "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
       "messages": [{"role": "user", "content": "Hello!"}],
       "max_tokens": 100
     }' \
     http://110.13.119.7:8081/v1/chat/completions
```

---

## 테스트 방법

### 1. FRP 서버 상태 확인 (miniPC)
```bash
sudo systemctl status frps
sudo journalctl -u frps -f
```

### 2. FRP 클라이언트 상태 확인 (사무실)
```bash
sudo systemctl status frpc
sudo journalctl -u frpc -f
```

### 3. 포트 확인
```bash
# miniPC에서 실행
sudo netstat -tlnp | grep -E '7000|8081'
```

### 4. 자동 테스트 스크립트 실행
```bash
bash scripts/test-frp.sh        # 연결 테스트
bash scripts/test-llm-api.sh    # LLM API 테스트
```

---

## 참고 자료
- [FRP GitHub](https://github.com/fatedier/frp)
- [FRP 공식 문서](https://github.com/fatedier/frp/blob/dev/README.md)
- `.github/project-goal.md` - 프로젝트 목표 문서
- `.github/development-environment.md` - 개발 환경 정보
- `README.md` - 프로젝트 전체 문서

---

## 결과

### 성과
- ✅ FRP 기반 역방향 프록시 환경 완전 구축
- ✅ 자동 설치/배포 시스템 구현
- ✅ 테스트 자동화 스크립트 제공
- ✅ 상세한 문서화 완료
- ✅ systemd 서비스 자동 관리

### 배포 준비 완료
- miniPC에서 `install-frps.sh` 실행 준비 완료
- 사무실 서버에서 `install-frpc.sh` 실행 준비 완료
- 테스트 스크립트로 즉시 검증 가능

### 향후 개선 사항
1. HTTPS 적용 (8443 포트)
2. OAuth2/JWT 인증 강화
3. Cloudflare Tunnel 연동
4. Rate Limiting 구현
5. 모니터링 대시보드 추가

