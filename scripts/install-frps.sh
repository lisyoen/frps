#!/bin/bash
# FRP Server Installation Script (MiniPC)
# This script downloads, installs, and configures frps as a systemd service

set -e  # Exit on error

# Configuration
FRP_VERSION="0.65.0"
FRP_ARCH="amd64"
FRP_DIR="/opt/frp"
CONFIG_DIR="/etc/frp"
SERVICE_NAME="frps"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== FRP Server Installation ===${NC}"
echo "Version: v${FRP_VERSION}"
echo "Architecture: ${FRP_ARCH}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

# Create directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p ${FRP_DIR}
mkdir -p ${CONFIG_DIR}
mkdir -p /var/log/frp

# Download FRP
echo -e "${YELLOW}Downloading FRP v${FRP_VERSION}...${NC}"
cd /tmp
DOWNLOAD_URL="https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_${FRP_ARCH}.tar.gz"
echo "URL: ${DOWNLOAD_URL}"

if [ -f "frp_${FRP_VERSION}_linux_${FRP_ARCH}.tar.gz" ]; then
    echo "Archive already exists, skipping download"
else
    wget -q --show-progress ${DOWNLOAD_URL} || {
        echo -e "${RED}Error: Failed to download FRP${NC}"
        exit 1
    }
fi

# Extract
echo -e "${YELLOW}Extracting...${NC}"
tar -xzf frp_${FRP_VERSION}_linux_${FRP_ARCH}.tar.gz

# Install binary
echo -e "${YELLOW}Installing frps binary...${NC}"
cd frp_${FRP_VERSION}_linux_${FRP_ARCH}
cp frps ${FRP_DIR}/
chmod +x ${FRP_DIR}/frps

# Copy configuration if provided
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_SOURCE="${SCRIPT_DIR}/../configs/frps.toml"

if [ -f "${CONFIG_SOURCE}" ]; then
    echo -e "${YELLOW}Installing configuration from repository...${NC}"
    cp "${CONFIG_SOURCE}" ${CONFIG_DIR}/
    echo -e "${GREEN}✓ Configuration installed${NC}"
    echo -e "${YELLOW}⚠️  Please review and update if needed:${NC}"
    echo -e "${YELLOW}   - ${CONFIG_DIR}/frps.toml${NC}"
    echo -e "${YELLOW}   - Change auth.token for production use${NC}"
else
    echo -e "${YELLOW}Creating default configuration...${NC}"
    cat > ${CONFIG_DIR}/frps.toml << 'EOF'
bindAddr = "0.0.0.0"
bindPort = 7000
auth.token = "CHANGE_ME_TO_SECURE_TOKEN"
vhostHTTPPort = 8081
log.level = "info"
log.maxDays = 7
transport.heartbeatTimeout = 90
EOF
    echo -e "${RED}⚠️  WARNING: Please configure ${CONFIG_DIR}/frps.toml${NC}"
fi

# Create systemd service
echo -e "${YELLOW}Creating systemd service...${NC}"
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=FRP Server Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Restart=on-failure
RestartSec=5s
ExecStart=${FRP_DIR}/frps -c ${CONFIG_DIR}/frps.toml
StandardOutput=append:/var/log/frp/frps.log
StandardError=append:/var/log/frp/frps.log

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo -e "${YELLOW}Reloading systemd...${NC}"
systemctl daemon-reload

# Enable and start service
echo -e "${YELLOW}Enabling and starting service...${NC}"
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME}

# Check status
sleep 2
if systemctl is-active --quiet ${SERVICE_NAME}; then
    echo -e "${GREEN}✓ FRP Server installed and running successfully!${NC}"
    echo ""
    echo "Service status:"
    systemctl status ${SERVICE_NAME} --no-pager -l
    echo ""
    echo -e "${GREEN}Commands:${NC}"
    echo "  Start:   sudo systemctl start ${SERVICE_NAME}"
    echo "  Stop:    sudo systemctl stop ${SERVICE_NAME}"
    echo "  Restart: sudo systemctl restart ${SERVICE_NAME}"
    echo "  Status:  sudo systemctl status ${SERVICE_NAME}"
    echo "  Logs:    sudo journalctl -u ${SERVICE_NAME} -f"
    echo ""
    echo -e "${GREEN}Configuration:${NC}"
    echo "  Config:  ${CONFIG_DIR}/frps.toml"
    echo "  Binary:  ${FRP_DIR}/frps"
    echo "  Log:     /var/log/frp/frps.log"
    echo ""
    echo -e "${GREEN}Network:${NC}"
    echo "  Control Port: 7000"
    echo "  HTTP Port:    8081"
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo "Check logs: sudo journalctl -u ${SERVICE_NAME} -n 50"
    exit 1
fi

# Cleanup
echo -e "${YELLOW}Cleaning up...${NC}"
cd /tmp
rm -rf frp_${FRP_VERSION}_linux_${FRP_ARCH}

echo -e "${GREEN}=== Installation Complete ===${NC}"
