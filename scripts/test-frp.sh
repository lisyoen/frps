#!/bin/bash
# FRP Service Test Script
# Tests FRP server/client connection and LLM API accessibility

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MINIPC_IP="110.13.119.7"
FRP_CONTROL_PORT="7000"
FRP_HTTP_PORT="8081"
LLM_API_ENDPOINT="http://${MINIPC_IP}:${FRP_HTTP_PORT}/v1"

echo -e "${GREEN}=== FRP Service Test ===${NC}"
echo ""

# Test 1: Check if frps service is running (on miniPC)
echo -e "${YELLOW}[1/5] Checking FRP Server status...${NC}"
if systemctl is-active --quiet frps 2>/dev/null; then
    echo -e "${GREEN}✓ FRP Server (frps) is running${NC}"
else
    echo -e "${RED}✗ FRP Server (frps) is not running${NC}"
    echo "  Run: sudo systemctl start frps"
fi
echo ""

# Test 2: Check if frpc service is running (on office server)
echo -e "${YELLOW}[2/5] Checking FRP Client status...${NC}"
if systemctl is-active --quiet frpc 2>/dev/null; then
    echo -e "${GREEN}✓ FRP Client (frpc) is running${NC}"
else
    echo -e "${YELLOW}⚠ FRP Client (frpc) status cannot be checked (might be on different machine)${NC}"
    echo "  On office server, run: sudo systemctl status frpc"
fi
echo ""

# Test 3: Check FRP control port connectivity
echo -e "${YELLOW}[3/5] Testing FRP Control Port (${MINIPC_IP}:${FRP_CONTROL_PORT})...${NC}"
if timeout 5 bash -c "echo > /dev/tcp/${MINIPC_IP}/${FRP_CONTROL_PORT}" 2>/dev/null; then
    echo -e "${GREEN}✓ FRP Control Port is accessible${NC}"
else
    echo -e "${RED}✗ Cannot connect to FRP Control Port${NC}"
    echo "  Check: 1) frps is running, 2) port 7000 is open, 3) firewall rules"
fi
echo ""

# Test 4: Check FRP HTTP port connectivity
echo -e "${YELLOW}[4/5] Testing FRP HTTP Port (${MINIPC_IP}:${FRP_HTTP_PORT})...${NC}"
if timeout 5 bash -c "echo > /dev/tcp/${MINIPC_IP}/${FRP_HTTP_PORT}" 2>/dev/null; then
    echo -e "${GREEN}✓ FRP HTTP Port is accessible${NC}"
else
    echo -e "${RED}✗ Cannot connect to FRP HTTP Port${NC}"
    echo "  Check: 1) frps is running, 2) vhostHTTPPort is configured, 3) firewall rules"
fi
echo ""

# Test 5: Test LLM API through FRP
echo -e "${YELLOW}[5/5] Testing LLM API through FRP...${NC}"
echo "Endpoint: ${LLM_API_ENDPOINT}/models"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" -H "Host: llm.local" -H "Content-Type: application/json" \
    --connect-timeout 10 --max-time 30 \
    "${LLM_API_ENDPOINT}/models" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ LLM API is accessible through FRP!${NC}"
    echo ""
    echo "Response:"
    echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
elif [ "$HTTP_CODE" = "000" ]; then
    echo -e "${RED}✗ Connection failed${NC}"
    echo "  Possible causes:"
    echo "  1) frpc is not running on office server"
    echo "  2) LLM API (172.21.113.31:4000) is not accessible from office server"
    echo "  3) Network connectivity issue"
else
    echo -e "${YELLOW}⚠ Received HTTP ${HTTP_CODE}${NC}"
    echo "Response: $BODY"
fi
echo ""

# Summary
echo -e "${GREEN}=== Test Complete ===${NC}"
echo ""
echo "Quick commands:"
echo "  View frps logs: sudo journalctl -u frps -f"
echo "  View frpc logs: sudo journalctl -u frpc -f"
echo "  Test with curl: curl -H 'Host: llm.local' http://${MINIPC_IP}:${FRP_HTTP_PORT}/v1/models"
echo ""
