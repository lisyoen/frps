#!/usr/bin/env python3
"""
터널 클라이언트 테스트 스크립트

로컬 네트워크에서 MainPC → MiniPC 연결 테스트
"""

import asyncio
import socket
import sys


async def test_command_channel():
    """커맨드 채널 테스트"""
    print("\n" + "="*60)
    print("커맨드 채널 테스트")
    print("="*60)
    
    try:
        # 연결
        reader, writer = await asyncio.open_connection('192.168.50.196', 8089)
        print("✓ 커맨드 채널 연결 성공")
        
        # READY 메시지 전송
        ready_msg = "READY 192.168.50.102:9999\n"
        writer.write(ready_msg.encode())
        await writer.drain()
        print(f"✓ READY 메시지 전송: {ready_msg.strip()}")
        
        # 응답 대기 (5초)
        try:
            response = await asyncio.wait_for(reader.readline(), timeout=5.0)
            if response:
                print(f"✓ 서버 응답: {response.decode().strip()}")
        except asyncio.TimeoutError:
            print("  (응답 없음 - 정상, NEW_CONN 대기 중)")
        
        # 연결 종료
        writer.close()
        await writer.wait_closed()
        print("✓ 커맨드 채널 종료")
        
        return True
        
    except Exception as e:
        print(f"✗ 커맨드 채널 테스트 실패: {e}")
        return False


async def test_data_channel():
    """데이터 채널 테스트"""
    print("\n" + "="*60)
    print("데이터 채널 테스트")
    print("="*60)
    
    try:
        # 연결
        reader, writer = await asyncio.open_connection('192.168.50.196', 8091)
        print("✓ 데이터 채널 연결 성공")
        
        # HTTP 요청 전송 (클라이언트로 식별)
        http_request = b"GET /test HTTP/1.1\r\nHost: test\r\n\r\n"
        writer.write(http_request)
        await writer.drain()
        print("✓ HTTP 요청 전송")
        
        # 응답 읽기
        response = await asyncio.wait_for(reader.read(1024), timeout=5.0)
        print(f"✓ 응답 수신: {response[:100]}")
        
        # 503 에러 확인 (터널 클라이언트 없음)
        if b'503' in response:
            print("✓ 503 에러 확인 (터널 없음, 정상)")
        
        # 연결 종료
        writer.close()
        await writer.wait_closed()
        print("✓ 데이터 채널 종료")
        
        return True
        
    except Exception as e:
        print(f"✗ 데이터 채널 테스트 실패: {e}")
        return False


async def test_tunnel_identifier():
    """터널 식별자 테스트 (첫 바이트 'T')"""
    print("\n" + "="*60)
    print("터널 식별자 테스트")
    print("="*60)
    
    try:
        # 연결
        reader, writer = await asyncio.open_connection('192.168.50.196', 8091)
        print("✓ 데이터 채널 연결 성공")
        
        # 첫 바이트 'T' 전송 (터널)
        writer.write(b'T')
        await writer.drain()
        print("✓ 터널 식별자 전송: T")
        
        # 대기 (서버가 대상 서버 연결 시도)
        await asyncio.sleep(2)
        
        # 연결이 유지되는지 확인
        try:
            writer.write(b'test data')
            await writer.drain()
            print("✓ 터널 연결 유지 중")
        except:
            print("  (대상 서버 없음, 연결 종료됨 - 정상)")
        
        # 연결 종료
        writer.close()
        await writer.wait_closed()
        print("✓ 터널 종료")
        
        return True
        
    except Exception as e:
        print(f"✗ 터널 식별자 테스트 실패: {e}")
        return False


def check_ports():
    """포트 상태 확인"""
    print("\n" + "="*60)
    print("포트 상태 확인")
    print("="*60)
    
    host = '192.168.50.196'
    ports = {
        8089: '커맨드 채널',
        8091: '데이터 채널',
    }
    
    all_ok = True
    for port, name in ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✓ {name} (포트 {port}): LISTEN")
        else:
            print(f"✗ {name} (포트 {port}): CLOSED")
            all_ok = False
    
    return all_ok


async def main():
    """메인 테스트"""
    print("\n터널 클라이언트 테스트 시작")
    print("대상: MiniPC (192.168.50.196)")
    
    # 1. 포트 확인
    if not check_ports():
        print("\n⚠️  터널 서버가 실행 중이지 않습니다.")
        print("MiniPC에서 터널 서버를 먼저 실행하세요:")
        print("  cd tunnel-server")
        print("  python tunnel_server.py")
        return
    
    # 2. 커맨드 채널 테스트
    await test_command_channel()
    
    # 3. 데이터 채널 테스트
    await test_data_channel()
    
    # 4. 터널 식별자 테스트
    await test_tunnel_identifier()
    
    print("\n" + "="*60)
    print("테스트 완료")
    print("="*60)
    print("\n다음 단계:")
    print("1. tunnel_client.py 실행:")
    print("   python tunnel_client.py")
    print("2. 다른 터미널에서 HTTP 요청:")
    print("   curl http://192.168.50.196:8091/test")


if __name__ == "__main__":
    asyncio.run(main())
