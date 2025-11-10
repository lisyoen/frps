#!/bin/bash
# LLM API Test through FRP
# Tests actual LLM inference via the reverse proxy

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
MINIPC_IP="${FRP_SERVER_IP:-localhost}"
FRP_HTTP_PORT="${FRP_HTTP_PORT:-8081}"
LLM_API_ENDPOINT="http://${MINIPC_IP}:${FRP_HTTP_PORT}/v1"
API_KEY="${LLM_API_KEY:-YOUR_API_KEY}"

echo -e "${GREEN}=== LLM API Test ===${NC}"
echo "Endpoint: ${LLM_API_ENDPOINT}"
echo ""

if [ "$API_KEY" = "YOUR_API_KEY" ]; then
    echo -e "${RED}⚠️  WARNING: Please set LLM_API_KEY environment variable${NC}"
    echo "Example: export LLM_API_KEY='your-api-key'"
    echo ""
fi

# Test 1: List models
echo -e "${YELLOW}[1/2] Testing /v1/models...${NC}"
curl -s -H "Host: llm.local" \
    -H "Authorization: Bearer ${API_KEY}" \
    "${LLM_API_ENDPOINT}/models" | jq .
echo ""

# Test 2: Simple chat completion
echo -e "${YELLOW}[2/2] Testing /v1/chat/completions...${NC}"
echo "Sending message: 'ping'"
echo ""

RESPONSE=$(curl -s -H "Host: llm.local" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${API_KEY}" \
    -d '{
        "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "messages": [
            {"role": "user", "content": "ping"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }' \
    "${LLM_API_ENDPOINT}/chat/completions")

if echo "$RESPONSE" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ LLM API is working!${NC}"
    echo ""
    echo "Response:"
    echo "$RESPONSE" | jq '.choices[0].message.content'
else
    echo -e "${RED}✗ LLM API error${NC}"
    echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
fi

echo ""
echo -e "${GREEN}=== Test Complete ===${NC}"
