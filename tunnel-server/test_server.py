#!/usr/bin/env python3
"""
터널 서버 테스트 스크립트

간단한 더미 클라이언트로 서버 동작 확인
"""

import asyncio
import socket

async def test_command_channel():
    """커맨드 채널 연결 테스트"""
    print("=" * 60)
    print("커맨드 채널 테스트")
    print("=" * 60)
    
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', 8089)
        print("✓ 커맨드 채널 연결 성공")
        
        # READY 메시지 전송
        test_ip = "192.168.50.100"
        writer.write(f"READY {test_ip}\n".encode('utf-8'))
        await writer.drain()
        print(f"✓ READY 메시지 전송: {test_ip}")
        
        # 연결 유지 (실제로는 계속 유지)
        await asyncio.sleep(2)
        
        writer.close()
        await writer.wait_closed()
        print("✓ 커맨드 채널 종료")
    
    except Exception as e:
        print(f"✗ 커맨드 채널 에러: {e}")

async def test_data_channel():
    """데이터 채널 연결 테스트"""
    print("\n" + "=" * 60)
    print("데이터 채널 테스트")
    print("=" * 60)
    
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', 8091)
        print("✓ 데이터 채널 연결 성공")
        
        # HTTP 요청 시뮬레이션
        http_request = b"GET /test HTTP/1.1\r\nHost: test.local\r\n\r\n"
        writer.write(http_request)
        await writer.drain()
        print("✓ HTTP 요청 전송")
        
        # 응답 대기 (타임아웃)
        try:
            response = await asyncio.wait_for(reader.read(1024), timeout=3.0)
            print(f"✓ 응답 수신: {response[:100]}")
        except asyncio.TimeoutError:
            print("✗ 응답 타임아웃 (정상 - SubPC 없음)")
        
        writer.close()
        await writer.wait_closed()
        print("✓ 데이터 채널 종료")
    
    except Exception as e:
        print(f"✗ 데이터 채널 에러: {e}")

async def test_ports():
    """포트 LISTEN 상태 확인"""
    print("\n" + "=" * 60)
    print("포트 상태 확인")
    print("=" * 60)
    
    for port, name in [(8089, "커맨드 채널"), (8091, "데이터 채널")]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            print(f"✓ {name} (포트 {port}): LISTEN")
        else:
            print(f"✗ {name} (포트 {port}): CLOSED")

async def main():
    """메인 테스트"""
    print("\n터널 서버 테스트 시작\n")
    
    # 포트 확인
    await test_ports()
    
    # 커맨드 채널 테스트
    await test_command_channel()
    
    # 데이터 채널 테스트
    await test_data_channel()
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(main())
