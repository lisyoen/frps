#!/usr/bin/env python3
"""
HTTP Tunnel Test - Spark에서 실행하여 프록시 경유 HTTP 터널 테스트
"""
import requests
import json

# 회사 프록시
PROXIES = {
    'http': 'http://30.30.30.27:8080',
    'https': 'http://30.30.30.27:8080'
}

# MiniPC HTTP 터널 (실제 실행 포트)
TUNNEL_URL = "http://110.13.119.7:8089"

def test_tunnel():
    print("=" * 60)
    print("HTTP Tunnel Test - 프록시 경유 테스트")
    print("=" * 60)
    
    # 1. 기본 연결 테스트
    print("\n[1] 기본 연결 테스트...")
    try:
        resp = requests.get(
            f"{TUNNEL_URL}/",
            proxies=PROXIES,
            timeout=5
        )
        print(f"✅ 연결 성공: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('Content-Type')}")
        print(f"응답 길이: {len(resp.content)} bytes")
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return
    
    # 2. LLM API 프록시 테스트 (MiniPC에 터널 서버 필요)
    print("\n[2] LLM API 프록시 테스트...")
    print("(MiniPC에 HTTP 터널 서버가 실행 중이어야 합니다)")
    
    llm_payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Say 'HTTP Tunnel Works!'"}
        ]
    }
    
    try:
        resp = requests.post(
            f"{TUNNEL_URL}/v1/chat/completions",
            json=llm_payload,
            proxies=PROXIES,
            timeout=30
        )
        print(f"✅ LLM 응답: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"메시지: {data['choices'][0]['message']['content']}")
    except Exception as e:
        print(f"❌ LLM 요청 실패: {e}")
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)

if __name__ == "__main__":
    test_tunnel()
