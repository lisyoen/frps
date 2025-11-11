# Tunnel Client

HTTP 터널 클라이언트 - 회사 내부망에서 집의 터널 서버로 역방향 연결

## 개요

이 클라이언트는 회사 내부망에서 실행되어:
1. 회사 프록시를 통해 집의 터널 서버(MiniPC)에 연결
2. 커맨드 채널로 영구 연결 유지
3. NEW_CONN 메시지 수신 시 데이터 채널 생성
4. 내부 LLM 서버와 외부 사용자를 relay

## 아키텍처

```
MainPC (집)                     MiniPC (집)                     SubPC (회사)                    LLM (회사)
    |                               |                               |                               |
    | HTTP Request                  |                               |                               |
    |------------------------------>|                               |                               |
    |                               | NEW_CONN (client_ip)          |                               |
    |                               |------------------------------>|                               |
    |                               |                               | Data Channel (with 'T')       |
    |                               |<------------------------------|                               |
    |                               |                               | Connect to LLM                |
    |                               |                               |------------------------------>|
    |                               | <====== Bidirectional Relay =============================>  |
```

## 설치

### 1. Python 가상환경 생성

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

## 설정

`config.yaml` 파일을 수정:

### 개발 환경 (MainPC)
```yaml
tunnel_server:
  host: 192.168.50.196  # MiniPC 로컬 IP
  command_port: 8089
  data_port: 8091

proxy:
  enabled: false         # 프록시 없이 직접 연결

target_server:
  host: 192.168.50.196  # 테스트용 (MiniPC의 mock 서버)
  port: 4000
```

### 운영 환경 (SubPC)
```yaml
tunnel_server:
  host: 110.13.119.7    # MiniPC 공인 IP
  command_port: 8089
  data_port: 8091

proxy:
  enabled: true          # 회사 프록시 사용
  host: 30.30.30.27
  port: 8080

target_server:
  host: 172.21.113.31   # 회사 LLM 서버
  port: 4000
```

## 실행

```bash
# 가상환경 활성화
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux

# 클라이언트 실행
python tunnel_client.py
```

## 테스트

### 로컬 테스트 (MainPC + MiniPC)
```bash
# 1. MiniPC에서 터널 서버 실행 (이미 실행 중)
# ssh lisyoen@192.168.50.196
# cd tunnel-server
# python tunnel_server.py

# 2. MainPC에서 클라이언트 실행
python tunnel_client.py

# 3. MainPC에서 HTTP 요청 전송
curl http://192.168.50.196:8091/test
```

### 프록시 시뮬레이션
```bash
# test_client.py로 프록시 포함 시나리오 테스트
python test_client.py
```

## 프로토콜

### 커맨드 채널 (8089)
- **연결**: 터널 서버에 영구 연결
- **READY 메시지**: `READY target_host:port\n` (예: `READY 172.21.113.31:4000\n`)
- **NEW_CONN 메시지**: `NEW_CONN client_ip\n` (예: `NEW_CONN 192.168.50.102\n`)
- **ERROR 메시지**: `ERROR message\n`

### 데이터 채널 (8091)
- **연결**: NEW_CONN 수신 시마다 새 연결 생성
- **첫 바이트**: `T` (터널 식별자)
- **이후**: 양방향 TCP relay

## 로그

- **파일**: `client.log`
- **레벨**: DEBUG, INFO, WARNING, ERROR
- **컬러**: 콘솔 출력 시 컬러 로그

## 통계

60초마다 연결 통계 출력:
- 활성 커맨드 채널
- 처리된 연결 수
- 전송/수신 바이트

## 문제 해결

### 프록시 연결 실패
- 프록시 주소/포트 확인
- 프록시 인증 필요 여부 확인

### 터널 서버 연결 실패
- 터널 서버가 실행 중인지 확인
- 방화벽 설정 확인
- 포트 포워딩 확인 (공인 IP 사용 시)

### LLM 서버 연결 실패
- LLM 서버가 실행 중인지 확인
- 내부 네트워크 접근 권한 확인
- 호스트/포트 확인

## Windows 서비스 등록

운영 환경에서는 Windows 서비스로 등록하여 자동 실행:

```powershell
# NSSM을 사용한 서비스 등록
nssm install TunnelClient "D:\path\to\venv\Scripts\python.exe" "D:\path\to\tunnel_client.py"
nssm set TunnelClient AppDirectory "D:\path\to\tunnel-client"
nssm start TunnelClient
```

## 라이선스

MIT License

## 문의

- 작성자: 이창연
- 이메일: lisyoen@gmail.com
