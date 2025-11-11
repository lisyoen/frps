# Development Environment

## Hosts

### DESKTOP-HOME (MainPC, 회사 업무용)
- **Role**: Development PC (회사 개발용)
- **OS**: Windows 11 Pro 10.0.26100
- **IP**: 192.168.50.102/24
- **MAC**: 9C-6B-00-8D-95-70
- **Gateway**: 192.168.50.1 (ASUS RT-AX53U)
- **Public IP**: 110.13.119.7
- **Location**: Home network

### MiniPC (Linux)
- **Role**: Development Server
- **OS**: Linux (Ubuntu-based)
- **IP**: 192.168.50.196/24 (Local), 110.13.119.7 (Public)
- **MAC**: 68-1d-ef-4e-2c-ad
- **Gateway**: 192.168.50.1
- **Open Ports**: 22, 80, 3000, 3389, 5432, 8080, 8088, 8500, 8888
- **Current Access**: Remote connection from DESKTOP-HOME (HomePC)
- **Location**: Home network
- **Docker Networks**: 
  - br-2756b4ad2294: 172.18.0.1/16
  - docker0: 172.17.0.1/16

### Office LLM Server (Spark - DGX)
- **Role**: Company LLM Server
- **OS**: Linux (Ubuntu-based)
- **Architecture**: ARM64 (aarch64)
- **Hostname**: spark-9ea9
- **IP**: 172.21.113.31 (internal)
- **LLM Port**: 4000 (Qwen3-Coder-30B)
- **Network Restrictions**:
  - ❌ **Outbound ping blocked**: Cannot ping external IPs
  - ❌ **Outbound connections restricted**: Limited external access
  - ⚠️ **FRP connection issue**: Cannot connect to home MiniPC (110.13.119.7:7000)
  - ℹ️ Requires network policy review or VPN/proxy setup

### DESKTOP-OLDWIN1 (win-backup)
- **Role**: Backup/Secondary PC
- **OS**: Windows 10 Pro 10.0.19045
- **CPU**: AMD Ryzen 5 2600 (6 cores, 12 threads)
- **Memory**: 8GB
- **GPU**: NVIDIA GeForce GTX 1060 3GB
- **Disks**: C: 133GB/223GB, E: 1400GB/1863GB

## Runtime Environments

### DESKTOP-HOME (win-dev)
- **Node.js**: 22.20.0
- **Python**: 3.11.8
- **Git**: 2.50.1
- **SSH**: 9.5
- **Paths**:
  - Python: `C:\Users\lisyo\AppData\Local\Programs\Python\Python311\`
  - Git: `C:\Program Files\Git\cmd`
  - Node.js: `C:\Program Files\nodejs\`
  - npm: `C:\Users\lisyo\AppData\Roaming\npm`

### MiniPC (Linux)
- **Node.js**: 20.19.1 (via nvm)
- **Python**: 3.12.3
- **Docker**: 26.1.3
- **Docker Compose**: 2.36.2
- **Git**: 2.43.0
- **npm**: 10.8.2
- **pip**: 24.0
- **Git Config**:
  - User: Changyeon Lee
  - Email: lisyoen@gmail.com
- **Paths**:
  - Node: `/home/lisyoen/.nvm/versions/node/v20.19.1/bin`
  - Python: `/usr/bin/python3`
  - Docker Root: `/var/lib/docker` (overlay2)

## Development Tools Configuration

### Common Paths
- **GRADLE_HOME**: `~/.gradle`
- **MAVEN_HOME**: `~/.m2`
- **CARGO_HOME**: `~/.cargo`
- **RUSTUP_HOME**: `~/.rustup`

### MiniPC Specific
- **npm prefix**: `/home/lisyoen/.nvm/versions/node/v20.19.1`
- **npm cache**: `/home/lisyoen/.npm`
- **npm registry**: https://registry.npmjs.org/
- **pip cache**: `/home/lisyoen/.cache/pip`

## Network

### Router
- **Model**: ASUS RT-AX53U
- **IP**: 192.168.50.1
- **MAC**: 08-bf-b8-e5-ac-60
- **DNS**: Gateway mode

### LAN Devices (192.168.50.0/24)
- **Gateway**: 192.168.50.1 (RT-AX53U-AC60)
- **DESKTOP-HOME**: 192.168.50.102
- **MiniPC**: 192.168.50.196
- **LG TV**: 192.168.50.250
- **iPhone**: 192.168.50.160
- **Total Devices**: 15

### Security Notes
- **NetBIOS**: Open on 192.168.50.102 (port 139)
- **SMB**: Open on 192.168.50.102 (port 445)
- **RDP**: Open on 192.168.50.196 (port 3389)

## LLM Configuration

### OpenAI API
- **API Key**: Configured in environment variables
- **Base URL**: https://api.openai.com/v1
- **Model**: gpt-4o
- **Status**: Active and ready for API calls

---

## HTTP Tunnel Development Plan

### Development Environment (개발 중)
**목적**: 집에서 tunnel-client 개발 및 로컬 테스트

**구성**:
- **Server**: MiniPC (192.168.50.196)
  - tunnel-server 구동 (ports 8089, 8091)
  - systemd 서비스 등록 예정
  
- **Client Development**: DESKTOP-HOME (HomePC, 192.168.50.102, Windows 11)
  - tunnel-client.py 개발 (Python)
  - Git 작업
  - MiniPC와 직접 연결 테스트 (프록시 없이)
  - HTTP CONNECT 프록시 시뮬레이션

**개발 절차**:
1. HomePC에서 tunnel-client.py 작성
2. HomePC → MiniPC (192.168.50.196:8089, 8091) 직접 연결
3. 로컬 네트워크에서 end-to-end 테스트
4. 프록시 시뮬레이션 코드 추가 (use_proxy 플래그)

### Production Environment (개발 완료 후)
**목적**: 회사 내부망 LLM 서버를 집에서 안전하게 호출

**구성**:
- **Server**: MiniPC (공인 IP: 110.13.119.7)
  - tunnel-server 운영 (systemd 서비스)
  - 포트 포워딩: 8089, 8091
  
- **Client**: SubPC (회사 내부망, 항상 켜둠)
  - tunnel-client 운영 (Windows 서비스)
  - 회사 프록시(30.30.30.27:8080) 경유
  - MiniPC:8089 커맨드 채널 영구 연결
  - LLM 서버(172.21.113.31:4000) 프록시
  
- **User**: HomePC (집)
  - http://110.13.119.7:8091/v1/chat/completions 호출
  - MiniPC를 통해 회사 LLM 접근

**운영 시나리오**:
```
HomePC (집)
    ↓ HTTP
MiniPC:8091 (집, 공인 IP)
    ↓ 터널 (8089 커맨드, 8091 데이터)
SubPC (회사, 프록시 경유)
    ↓ HTTP
LLM Server (172.21.113.31:4000, 회사 내부망)
```