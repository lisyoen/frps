# Session Manager

최근 10개 세션 목록 (최신순):

## 활성/최근 세션

### 1. session-20251111-002-frpc-deploy-at-office ⏸️
- **날짜**: 2025-11-11
- **상태**: 대기 중 ⏸️ (회사 LLM 서버에서 재개 예정)
- **작업**: 회사 LLM 서버에 FRP 클라이언트(frpc) 설치
- **상세**: [session-20251111-002-frpc-deploy-at-office.md](sessions/session-20251111-002-frpc-deploy-at-office.md)
- **목적**: 
  - 회사 LLM 서버에서 Git 클론 후 frpc 설치
  - MiniPC frps와 연결 테스트
  - 집에서 회사 LLM API 접근 확인

### 2. session-20251111-001-frp-setup ✅
- **날짜**: 2025-11-11
- **상태**: 완료 ✅
- **작업**: FRP 역방향 프록시 환경 구축
- **상세**: [session-20251111-001-frp-setup.md](sessions/session-20251111-001-frp-setup.md)
- **결과**: 
  - FRP v0.65.0 서버/클라이언트 설정 완료
  - 자동 설치 스크립트 작성 (install-frps.sh, install-frpc.sh)
  - 테스트 스크립트 작성 (test-frp.sh, test-llm-api.sh)
  - README.md 상세 문서화 완료
  - Git 커밋 및 푸시 완료

---

*오래된 세션은 [work-history.md](work-history.md)로 이동됨*
