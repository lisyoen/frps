# Fast Reverse Proxy server — Project Goal
## 1. 프로젝트 개요
- **원본 리포지토리:** [https://github.com/lisyoen/frps](https://github.com/lisyoen/frps)  
- **개발환경:** `.github/개발환경_20251025.prompt.txt`

---

## 2. 프로젝트 목표

### 2.1 목적
본 프로젝트는 **회사 내부망의 LLM 서버를 외부(집)에서 안전하게 호출**할 수 있도록
역방향 HTTP 프록시 환경을 구축하는 것을 목표로 한다.  
회사는 외부에서 직접 접근할 수 없는 폐쇄망 구조이며, outbound 트래픽만 허용되어 있기 때문에
표준 SSH 터널이나 VPN 방식은 사용할 수 없다.

이를 해결하기 위해 **FRP(Fast Reverse Proxy)** 기반의 역방향 터널링을 구현하여,
사무실 LLM 서버가 집의 MiniPC로 아웃바운드 연결을 맺고,
MiniPC를 중계점으로 외부에서 LLM API 호출을 가능하게 만든다.

---

### 2.2 개발 및 운영 환경

#### 개발 환경 (개발 중)
- **개발 서버**: MiniPC (Ubuntu/Linux Mint 22, 192.168.50.196, 집)
  - 역할: HTTP 터널 서버 (tunnel-server)
  - 공인 IP: 110.13.119.7
  - 포트 포워딩: 8089, 8091
- **개발 클라이언트**: MainPC (Windows 11 Pro, 192.168.50.102, 집)
  - 역할: 터널 클라이언트 개발 및 테스트
  - 회사 프록시 시뮬레이션
  - Git 작업

#### 운영 환경 (개발 완료 후)
- **운영 서버**: MiniPC (Ubuntu/Linux Mint 22, 192.168.50.196, 집)
  - 역할: HTTP 터널 서버 (항상 실행)
  - 공인 IP: 110.13.119.7
  - systemd 서비스 등록
- **운영 클라이언트**: SubPC (Windows 11, 회사 내부망)
  - 역할: 터널 클라이언트 (항상 실행)
  - 회사 프록시 경유 (30.30.30.27:8080)
  - Windows 서비스 등록
  - LLM 서버 프록시 (172.21.113.31:4000)

---

### 2.3 시스템 구성 요약

| 구분 | 역할 | 비고 |
|------|------|------|
| **사무실 LLM 서버** | FRP 클라이언트(`frpc`) 실행, MiniPC로 역방향 연결 | GPU DGX Spark 기반 |
| **MiniPC (집)** | FRP 서버(`frps`) 구동, 외부 접속 중계 | 공개 포트 (제어, HTTP) |
| **집 PC** | HTTP 요청을 통해 MiniPC를 통해 LLM API 호출 | 개발·테스트 환경 |

---

### 2.4 LLM 서버 사양
- **GPU:** DGX Spark  
- **LLM Endpoint:** 172.21.xxx.xxx (보안상 마스킹)
- **모델:** Qwen3-Coder-30B-A3B-Instruct  
- **용도:** 실 업무 코드 작성, 테스트 및 코드 보조  
- **특징:** 30B 파라미터 기반, 코드 생성 특화 모델  

> API 연결 정보 (보안을 위해 마스킹됨)  
> provider: `openai`  
> model: `Qwen/Qwen3-Coder-30B-A3B-Instruct`  
> apiKey: `YOUR_API_KEY` (실제 키로 변경)
> apiBase: `http://YOUR_LLM_SERVER_IP:YOUR_LLM_PORT/v1`

---

### 2.5 기술 목표
1. **역방향 HTTP 프록시 구축**
   - 사무실 LLM 서버 → MiniPC 방향의 아웃바운드 연결(제어 포트)
   - MiniPC → 집 PC 방향의 HTTP 응답(HTTP 포트)
2. **LLM API 중계**
   - MiniPC의 HTTP 포트를 통해 LLM API를 외부에서 접근 가능하도록 제공
   - 실제 호출 예:  
     ```bash
     curl -i http://<MiniPC공인IP>:<HTTP포트>/v1/chat/completions \
       -H "Content-Type: application/json" \
       -H "Host: llm.local" \
       -d '{"model":"YOUR_MODEL","messages":[{"role":"user","content":"ping"}]}'
     ```
3. **보안 통신**
   - 인증 토큰 기반 통신 제어 (강력한 토큰 사용 권장)
   - 향후 HTTPS(8443) 적용 및 접근 제어 프록시 추가 예정
4. **운영 자동화**
   - `frps`, `frpc` 모두 systemd 서비스로 등록하여 자동 재시작 및 모니터링 구성
5. **지속적 점검**
   - 로그 수집 및 서비스 상태 모니터링으로 안정성 확보

---

### 2.6 기대효과
- 회사 내부 LLM 자원을 외부에서도 안전하게 활용 가능
- SSH/VPN 없이 HTTP 기반 터널링을 통한 빠른 접근
- 코드 테스트 및 AI 개발 효율 향상
- LLM 인프라 활용 범위 확대 및 자원 재사용 극대화

---

### 2.7 향후 계획
- HTTPS 기반 암호화 적용
- 토큰 인증 강화를 위한 OAuth2 / JWT 도입 검토
- MiniPC → Cloudflare Tunnel 연동으로 DDNS 불필요화
- 자동 복구 모듈(systemd + health check script) 추가

---

**작성자:** 이창연  
**작성일:** 2025-11-11  
