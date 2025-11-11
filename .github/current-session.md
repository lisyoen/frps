# Current Session

**세션 ID**: session-20251112-002-tunnel-client-impl

**상태**: ✅ 완료

**작업**: MainPC 터널 클라이언트 구현 및 통합 테스트 성공

**상세**: `.github/sessions/session-20251112-002-tunnel-client-impl.md` 참조

---

## 개발 및 운영 환경

### 개발 환경 (현재, ✅ 완료)
- **개발 서버**: MiniPC (Ubuntu/Linux Mint 22, 192.168.50.196, 집)
  - tunnel-server 개발 및 운영 중 ✅
- **개발 클라이언트**: MainPC (Windows 11, 192.168.50.102, 집)
  - tunnel-client 개발 및 테스트 완료 ✅
- **테스트 LLM**: MainPC Ollama (localhost:11434/v1)
  - 모델: qwen3-coder:30b ✅

### 운영 환경 (개발 완료 후)
- **운영 서버**: MiniPC (systemd 서비스로 자동 실행)
- **운영 클라이언트**: SubPC (Windows 11, 회사 내부망, Windows 서비스)

---

## 완료된 작업 ✅

### 터널 서버 (session-20251112-001)
- ✅ MiniPC에서 asyncio 기반 HTTP 터널 서버 구현
- ✅ 커맨드 채널 (8089), 데이터 채널 (8091)
- ✅ 로컬 테스트 성공

### 터널 클라이언트 (session-20251112-002)
- ✅ MainPC에서 터널 클라이언트 구현
- ✅ HTTP CONNECT 프록시 지원
- ✅ 커맨드/데이터 채널 관리
- ✅ 양방향 TCP relay
- ✅ **통합 테스트 성공**: MainPC → MiniPC → MainPC Ollama

---

## 다음 단계

### 1단계: SubPC 배포 (회사)
- [ ] SubPC에 코드 배포 (git pull)
- [ ] config.yaml 수정 (proxy.enabled=true)
- [ ] 회사 프록시 경유 테스트
- [ ] 회사 LLM 서버 (172.21.113.31:4000) 연결

### 2단계: 서비스 등록
- [ ] MiniPC: systemd 서비스 등록
- [ ] SubPC: Windows 서비스 등록

### 3단계: 운영 환경 구성
- [ ] 포트 포워딩 설정
- [ ] 방화벽 설정
- [ ] 모니터링 설정

---

## 최근 세션 목록

**session-20251112-002**: MainPC 터널 클라이언트 구현 (✅ 완료)  
**session-20251112-001**: MiniPC 터널 서버 구현 (✅ 완료)  
**session-20251111-005**: HTTP 터널 프로토콜 설계 (✅ 완료)  
**session-20251111-004**: FRP WebSocket 전환 시도 (❌ 중단, DPI 차단)  
**session-20251111-003**: MiniPC FRP 서버 설치 (✅ 완료)

