# 프로젝트 컨텍스트

## 프로젝트 개요
- **이름**: Fast Reverse Proxy Server (FRPS)
- **목표**: 회사 내부망 LLM 서버를 외부에서 안전하게 호출하기 위한 FRP 기반 역방향 프록시 환경 구축
- **타입**: 인프라/네트워크 프로젝트
- **언어**: Bash (스크립트), TOML (설정)
- **위치**: /home/lisyoen/frps (miniPC)
- **저장소**: https://github.com/lisyoen/frps

## 개발 환경
- **개발 머신**: miniPC (Ubuntu Linux, 192.168.50.196)
- **개발 도구**: VSCode + GitHub Copilot
- **버전 관리**: Git + GitHub
- **배포 대상**: 
  - miniPC (FRP 서버)
  - 사무실 LLM 서버 (FRP 클라이언트)

## 프로젝트 목표
회사 폐쇄망 환경에서 외부 접근이 불가능한 LLM 서버를 집에서 안전하게 사용하기 위한 역방향 프록시 시스템 구축

### 핵심 요구사항
1. **역방향 터널링**: 사무실 → 집 방향의 아웃바운드 연결
2. **LLM API 중계**: miniPC를 통한 외부 접근 제공
3. **자동화**: 설치/배포/관리의 완전 자동화
4. **안정성**: systemd 기반 자동 재시작 및 로그 관리

## 시스템 아키텍처

### 네트워크 구성
```
[회사 내부망]                [인터넷]              [집]
┌─────────────────┐                        ┌──────────────────┐
│ LLM 서버         │                        │ miniPC           │
│ 172.21.113.31   │                        │ 192.168.50.196   │
│ Port: 4000      │                        │ (110.13.119.7)   │
│                 │                        │ Port: 7000,8081  │
│ frpc (client)   │─── Outbound 연결 ────→│ frps (server)    │
└─────────────────┘                        └─────────┬────────┘
                                                     │
                                                     ↓
                                            ┌──────────────────┐
                                            │ 집 PC            │
                                            │ HTTP Client      │
                                            │ curl/Postman     │
                                            └──────────────────┘
```

### 역할 분담
| 구성 요소 | 호스트 | 역할 | 소프트웨어 |
|-----------|--------|------|------------|
| **Server** | miniPC (집) | FRP 서버, 외부 접속 중계 | frps v0.65.0 |
| **Client** | LLM 서버 (회사) | FRP 클라이언트, 역방향 연결 | frpc v0.65.0 |
| **User** | 집 PC | HTTP 요청 발신 | curl, Postman 등 |

## LLM 서버 환경

### 회사 LLM 서버 (Spark)

### 회사 LLM 서버 (Spark)
- **GPU**: DGX Spark
- **내부 IP**: 172.21.113.31
- **API 포트**: 4000
- **모델**: Qwen/Qwen3-Coder-30B-A3B-Instruct
- **용도**: 실 업무 코드 작성, 테스트 및 코드 보조
- **특징**: 30B 파라미터 기반, 코드 생성 특화 모델
- **API 스택**: LiteLLM → vLLM

### API 연결 정보
```yaml
provider: openai
model: Qwen/Qwen3-Coder-30B-A3B-Instruct
apiKey: sk-Dwgun2yU_YQkounRcLEuGA
apiBase: http://172.21.113.31:4000/v1
```

### FRP를 통한 외부 접근
```bash
# 집에서 LLM API 호출
curl -H "Host: llm.local" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer sk-Dwgun2yU_YQkounRcLEuGA" \
     -d '{
       "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
       "messages": [{"role": "user", "content": "Hello!"}]
     }' \
     http://110.13.119.7:8081/v1/chat/completions
```

## 기술 스택

### FRP (Fast Reverse Proxy)
- **버전**: v0.65.0 (2024-09-25 릴리스)
- **GitHub**: https://github.com/fatedier/frp
- **언어**: Go
- **라이선스**: Apache 2.0
- **기능**: TCP/UDP/HTTP/HTTPS 역방향 프록시

### 설정 형식
- **파일 형식**: TOML (v0.52.0+부터 INI 대신 권장)
- **서버 설정**: `/etc/frp/frps.toml`
- **클라이언트 설정**: `/etc/frp/frpc.toml`

### 시스템 관리
- **서비스 관리**: systemd
- **로그 관리**: journald + /var/log/frp/
- **자동 재시작**: systemd Restart=on-failure

## 프로젝트 구조

```
frps/
├── README.md              # 프로젝트 전체 문서
├── configs/
│   ├── frps.toml         # FRP 서버 설정 (miniPC)
│   └── frpc.toml         # FRP 클라이언트 설정 (사무실)
├── scripts/
│   ├── install-frps.sh   # FRP 서버 자동 설치
│   ├── install-frpc.sh   # FRP 클라이언트 자동 설치
│   ├── test-frp.sh       # 연결 테스트
│   └── test-llm-api.sh   # LLM API 테스트
└── .github/
    ├── project-goal.md           # 프로젝트 목표
    ├── project-context.md        # 프로젝트 컨텍스트 (이 파일)
    ├── development-environment.md # 개발 환경 정보
    ├── current-session.md        # 현재 세션
    ├── session-manager.md        # 세션 관리
    └── sessions/                 # 세션 기록
```

## 네트워크 설정

### 포트 구성
- **7000**: FRP 제어 포트 (frpc ↔ frps 통신)
- **8081**: HTTP 프록시 포트 (외부 → LLM API)
- **4000**: LLM API 원본 포트 (내부망 전용)

### IP 주소
- **miniPC 내부 IP**: 192.168.50.196
- **miniPC 공인 IP**: 110.13.119.7
- **LLM 서버 IP**: 172.21.113.31 (회사 내부망)

### 보안
- **인증 방식**: Token 기반 (auth.token = "deasea!1")
- **통신 프로토콜**: HTTP (현재), HTTPS (향후 계획)
- **방화벽**: 포트 7000, 8081만 오픈

## 개발 워크플로우

### 개발 환경 (miniPC)
```bash
# 개발 위치
cd /home/lisyoen/frps

# VSCode 실행
code .

# Git 동기화
git pull
git add .
git commit -m "메시지"
git push
```

### 배포 워크플로우

#### 1. miniPC에 FRP 서버 배포
```bash
sudo bash scripts/install-frps.sh
sudo systemctl status frps
sudo journalctl -u frps -f
```

#### 2. 사무실 서버에 FRP 클라이언트 배포
```bash
git clone https://github.com/lisyoen/frps.git
cd frps
sudo bash scripts/install-frpc.sh
sudo systemctl status frpc
sudo journalctl -u frpc -f
```

#### 3. 테스트
```bash
bash scripts/test-frp.sh
bash scripts/test-llm-api.sh
```

## 주요 명령어

### 서비스 관리
```bash
# FRP 서버 (miniPC)
sudo systemctl start frps
sudo systemctl stop frps
sudo systemctl restart frps
sudo systemctl status frps
sudo journalctl -u frps -f

# FRP 클라이언트 (사무실)
sudo systemctl start frpc
sudo systemctl stop frpc
sudo systemctl restart frpc
sudo systemctl status frpc
sudo journalctl -u frpc -f
```

### 네트워크 진단
```bash
# 포트 확인
sudo netstat -tlnp | grep -E '7000|8081'

# 연결 확인
sudo netstat -tnp | grep frp

# 공인 IP 확인
curl ifconfig.me
```

### LLM API 테스트
```bash
# 모델 목록 조회
curl -H "Host: llm.local" http://110.13.119.7:8081/v1/models

# Chat Completion
curl -H "Host: llm.local" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer sk-Dwgun2yU_YQkounRcLEuGA" \
     -d '{"model":"Qwen/Qwen3-Coder-30B-A3B-Instruct","messages":[{"role":"user","content":"ping"}]}' \
     http://110.13.119.7:8081/v1/chat/completions
```

## 주요 의사결정 사항

1. **FRP 선택 이유**
   - SSH/VPN 불가능한 폐쇄망 환경
   - 역방향 터널링으로 outbound 트래픽만 사용
   - 가벼운 Go 기반 바이너리

2. **포트 선택**
   - 7000: 표준적으로 사용되는 FRP 제어 포트
   - 8081: HTTP 서비스에 흔히 사용되는 대체 포트

3. **설정 형식**
   - TOML 사용 (FRP v0.52.0+ 권장 형식)
   - INI보다 구조화되고 타입 안전

4. **자동화 전략**
   - 단일 스크립트로 다운로드부터 서비스 시작까지 완전 자동화
   - systemd 통합으로 운영 안정성 확보

5. **보안 방식**
   - 현재: Token 기반 인증
   - 향후: HTTPS(8443) + OAuth2/JWT 검토

## 코딩 스타일 및 컨벤션

### Bash 스크립트
- `set -e`로 에러 시 즉시 종료
- 색상 출력으로 가독성 향상 (RED, GREEN, YELLOW)
- 진행 상황 명확한 메시지 출력
- 권한 체크 (`$EUID -ne 0`)

### 설정 파일 (TOML)
- 명확한 섹션 구분
- 주석으로 각 설정 설명
- 기본값 명시

### Git 커밋
- 한국어 커밋 메시지
- 상세한 변경 내역 포함
- 다음 단계 명시

## 문제 해결 가이드

### 일반적인 문제
1. **FRP 서버 시작 실패**: 포트 충돌 확인 (`netstat -tlnp`)
2. **클라이언트 연결 실패**: 공인 IP 변경 확인, 토큰 일치 확인
3. **LLM API 호출 실패**: Host 헤더 확인, frpc 로그 확인
4. **로그 파일 증가**: maxDays 설정으로 자동 정리 (7일)

### 디버깅
```bash
# 실시간 로그 모니터링
sudo journalctl -u frps -f
sudo journalctl -u frpc -f

# 최근 50줄 로그
sudo journalctl -u frps -n 50
sudo journalctl -u frpc -n 50

# 서비스 상태 확인
systemctl status frps --no-pager -l
systemctl status frpc --no-pager -l
```

## 향후 개선 계획

### 단기 (1-2개월)
- [ ] HTTPS(8443) 포트 추가
- [ ] Let's Encrypt 인증서 자동 갱신
- [ ] 연결 상태 모니터링 대시보드

### 중기 (3-6개월)
- [ ] OAuth2/JWT 인증 강화
- [ ] Rate Limiting 구현
- [ ] IP 화이트리스트 기능

### 장기 (6개월+)
- [ ] Cloudflare Tunnel 연동
- [ ] 다중 LLM 서버 지원
- [ ] 자동 장애 복구 시스템

## 참고 자료
- [FRP GitHub](https://github.com/fatedier/frp)
- [FRP 공식 문서](https://github.com/fatedier/frp/blob/dev/README.md)
- [프로젝트 목표](project-goal.md)
- [개발 환경 정보](development-environment.md)
- [README.md](../README.md)

---

**작성자**: 이창연 (lisyoen@gmail.com)  
**최종 수정**: 2025-11-11  
**개발 환경**: miniPC + VSCode + GitHub Copilot
