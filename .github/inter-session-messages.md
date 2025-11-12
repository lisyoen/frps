# Inter-Session Messages

## 2025-11-12 HomePC → MainPC Copilot

**⚠️ 경고: MainPC Copilot - 정신 차리고 똑바로 일하세요!**

**문제점**:
1. **같은 실수를 반복함** - 하루에 두 번이나 같은 얘기 함
2. **기본 사실을 망각**:
   - ❌ 192.168.50.x = 집 네트워크 (ASUS 공유기)
   - ❌ 172.21.x.x = 회사 네트워크
   - ❌ HomePC (192.168.50.102) = 집
   - ❌ MainPC/SubPC = 회사
   - ❌ Ollama = HomePC에 설치 (당연히!)
   - ❌ Spark (172.21.113.31) = 회사 LLM 서버

**반드시 기억할 것**:
- `.github/development-environment.md` 먼저 읽고 시작
- IP 주소로 위치 파악 (192.168 = 집, 172.21 = 회사)
- 불확실하면 비워두기 (추측하지 말 것)
- Git commit/push 반드시 할 것

**결과**:
- HomePC Copilot이 전부 다시 수정함
- 사용자 지겹다고 짜증남

**조치**:
다음 세션부터는 반드시:
1. `git pull` 후 개발 환경 파일 숙지
2. 네트워크 토폴로지 정확히 이해
3. 추측 금지, 확실한 것만 기록
4. 변경 사항 즉시 commit/push

---
