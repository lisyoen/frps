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