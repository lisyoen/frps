# Session: FRP 역방향 프록시 구축

**세션 ID**: session-20251111-001-frp-setup  
**생성일**: 2025-11-11  
**상태**: 진행 중 🔄

---

## 작업 목적
회사 내부망의 LLM 서버(172.21.113.31:4000)를 외부(집)에서 안전하게 호출할 수 있도록 Fast Reverse Proxy (FRP) 환경 구축

### 시스템 구성
- **사무실 LLM 서버**: frpc 클라이언트 실행 → miniPC로 아웃바운드 연결
- **miniPC (집)**: frps 서버 실행 → 외부 접속 중계 (포트 7000, 8081)
- **집 PC**: HTTP 요청으로 miniPC를 통해 LLM API 호출

---

## 작업 계획

### 1단계: FRP 바이너리 다운로드 및 설치
- [ ] GitHub releases에서 최신 frp 버전 확인
- [ ] miniPC용 Linux 바이너리 다운로드
- [ ] 사무실 서버용 바이너리 준비 (추후)

### 2단계: FRP 서버 설정 (miniPC)
- [ ] frps.ini 설정 파일 작성
  - bind_port: 7000 (제어 포트)
  - vhost_http_port: 8081 (HTTP 포트)
  - authentication_token: deasea!1

### 3단계: FRP 클라이언트 설정 (사무실)
- [ ] frpc.ini 설정 파일 작성
  - server_addr: miniPC 공인 IP
  - server_port: 7000
  - LLM API 엔드포인트: 172.21.113.31:4000

### 4단계: systemd 서비스 등록
- [ ] frps.service 파일 작성 (miniPC)
- [ ] frpc.service 파일 작성 (사무실)
- [ ] 자동 시작 및 재시작 설정

### 5단계: 배포 자동화
- [ ] 설치 스크립트 작성 (install-frps.sh)
- [ ] 설치 스크립트 작성 (install-frpc.sh)

### 6단계: 테스트 및 검증
- [ ] 연결 테스트 스크립트 작성
- [ ] LLM API 호출 테스트 (curl)

### 7단계: 문서화
- [ ] README.md 업데이트 (설치/설정/사용 방법)

---

## 진행 상황

### 2025-11-11

#### 초기 설정
- 프로젝트 목표 확인 ✅
- 세션 생성 ✅
- TODO 리스트 작성 ✅

#### 다음 단계
- FRP 최신 버전 확인 및 다운로드 URL 준비

---

## 기술 정보

### FRP (Fast Reverse Proxy)
- **GitHub**: https://github.com/fatedier/frp
- **문서**: https://github.com/fatedier/frp/blob/dev/README.md
- **아키텍처**: Client-Server 역방향 터널링

### 네트워크 정보
- **miniPC IP**: 192.168.50.196 (내부), 110.13.119.7 (공인)
- **LLM 서버 IP**: 172.21.113.31
- **LLM API 포트**: 4000
- **FRP 제어 포트**: 7000
- **FRP HTTP 포트**: 8081

### 보안
- 인증 토큰: deasea!1
- 향후 HTTPS(8443) 적용 예정

---

## 결정 사항

1. **FRP 사용 이유**: SSH/VPN 불가능한 폐쇄망 환경에서 역방향 터널링 필요
2. **포트 선택**: 7000(제어), 8081(HTTP) - 방화벽 정책 고려
3. **인증 방식**: 토큰 기반, 향후 OAuth2/JWT 검토

---

## 문제점 및 해결

*작업 중 발생하는 문제점과 해결 방법 기록*

---

## 참고 자료
- [FRP GitHub](https://github.com/fatedier/frp)
- `.github/project-goal.md` - 프로젝트 목표 문서
- `.github/development-environment.md` - 개발 환경 정보
