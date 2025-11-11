#!/usr/bin/env python3
"""
Ollama LLM 서버 테스트 스크립트
MainPC Ollama (localhost:11434/v1)에 직접 연결하여 테스트
"""

import requests
import json

def test_ollama_direct():
    """Ollama 직접 연결 테스트"""
    print("=" * 60)
    print("MainPC Ollama 직접 연결 테스트")
    print("=" * 60)
    
    url = "http://localhost:11434/v1/chat/completions"
    
    payload = {
        "model": "qwen3-coder:30b",
        "messages": [
            {"role": "user", "content": "Hello, this is a test!"}
        ],
        "temperature": 0.7
    }
    
    print(f"\n요청 URL: {url}")
    print(f"모델: {payload['model']}")
    print(f"메시지: {payload['messages'][0]['content']}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\n응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 성공!")
            print(f"\n응답 내용:")
            print(f"  모델: {data.get('model', 'N/A')}")
            print(f"  메시지: {data['choices'][0]['message']['content'][:100]}...")
            print(f"  토큰: {data.get('usage', {})}")
        else:
            print(f"❌ 실패!")
            print(f"응답: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print(f"❌ 연결 실패!")
        print(f"Ollama 서버가 실행 중인지 확인하세요:")
        print(f"  http://localhost:11434")
    except Exception as e:
        print(f"❌ 에러: {e}")

if __name__ == "__main__":
    test_ollama_direct()
