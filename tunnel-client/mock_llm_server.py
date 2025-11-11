#!/usr/bin/env python3
"""
Mock LLM 서버 (테스트용)

로컬 테스트를 위한 간단한 HTTP 서버
실제 LLM API 형식으로 응답
"""

import asyncio
import json
from datetime import datetime


async def handle_client(reader, writer):
    """클라이언트 요청 처리"""
    try:
        # HTTP 헤더 읽기
        headers = []
        while True:
            line = await reader.readline()
            if line == b'\r\n':
                break
            headers.append(line.decode().strip())
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 요청 수신:")
        for header in headers[:3]:
            print(f"  {header}")
        
        # Content-Length 확인
        content_length = 0
        for header in headers:
            if header.lower().startswith('content-length:'):
                content_length = int(header.split(':')[1].strip())
        
        # 본문 읽기
        if content_length > 0:
            body = await reader.read(content_length)
            print(f"  Body: {body.decode()[:100]}...")
        
        # LLM API 응답 생성
        response_data = {
            "id": "chatcmpl-test-123",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": "mock-llm",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello from mock LLM server! This is a test response."
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
        
        response_body = json.dumps(response_data, ensure_ascii=False).encode()
        
        # HTTP 응답 전송
        response_headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            f"Content-Length: {len(response_body)}\r\n"
            "\r\n"
        )
        
        writer.write(response_headers.encode())
        writer.write(response_body)
        await writer.drain()
        
        print(f"  응답 전송: 200 OK ({len(response_body)} bytes)")
        
    except Exception as e:
        print(f"  에러: {e}")
    finally:
        writer.close()
        await writer.wait_closed()


async def main():
    """메인 서버"""
    server = await asyncio.start_server(
        handle_client,
        '0.0.0.0',
        4000
    )
    
    print("=== Mock LLM 서버 시작 ===")
    print("포트: 4000")
    print("Ctrl+C로 종료")
    print()
    
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n서버 종료")
