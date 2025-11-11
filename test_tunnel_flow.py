#!/usr/bin/env python3
"""
전체 터널 흐름 테스트
MainPC → MiniPC → MainPC Ollama
"""

import requests
import json
import time

def test_tunnel_flow():
    """터널을 통한 LLM API 호출 테스트"""
    print("=" * 60)
    print("터널 흐름 테스트")
    print("=" * 60)
    print("흐름: MainPC → MiniPC:8091 → 터널 → MainPC Ollama")
    print()
    
    # MiniPC 터널 서버로 요청
    url = "http://192.168.50.196:8091/v1/chat/completions"
    
    payload = {
        "model": "qwen3-coder:30b",
        "messages": [
            {"role": "user", "content": "Hello! This is a tunnel test. Please respond briefly."}
        ],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    print(f"요청 URL: {url}")
    print(f"모델: {payload['model']}")
    print(f"메시지: {payload['messages'][0]['content']}")
    print()
    
    try:
        print("요청 전송 중...")
        start_time = time.time()
        
        response = requests.post(url, json=payload, timeout=60)
        
        elapsed = time.time() - start_time
        
        print(f"\n응답 상태: {response.status_code}")
        print(f"응답 시간: {elapsed:.2f}초")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 터널 테스트 성공!")
            print(f"\n응답 내용:")
            print(f"  모델: {data.get('model', 'N/A')}")
            content = data['choices'][0]['message']['content']
            print(f"  메시지: {content}")
            print(f"  토큰: {data.get('usage', {})}")
            print()
            print("=" * 60)
            print("전체 흐름 검증 완료!")
            print("MainPC → MiniPC:8091 → 터널 클라이언트 → Ollama")
            print("=" * 60)
        else:
            print(f"\n❌ 실패!")
            print(f"응답: {response.text}")
    
    except requests.exceptions.Timeout:
        print(f"\n❌ 타임아웃!")
        print(f"60초 내에 응답 없음")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 연결 실패!")
        print(f"MiniPC 터널 서버가 실행 중인지 확인하세요")
    except Exception as e:
        print(f"\n❌ 에러: {e}")

if __name__ == "__main__":
    print("\n잠시 대기 중... (터널 클라이언트 초기화)")
    time.sleep(2)
    test_tunnel_flow()
