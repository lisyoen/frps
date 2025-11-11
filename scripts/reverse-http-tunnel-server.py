#!/usr/bin/env python3
"""
Reverse HTTP Tunnel Server (Spark에서 실행)
회사 Spark에서 실행하여 MiniPC의 HTTP 요청을 회사 LLM(172.21.113.31:4000)으로 프록시
"""
from flask import Flask, request, Response
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# 회사 LLM 서버 설정 (Spark 내부망)
LLM_HOST = "172.21.113.31"
LLM_PORT = 4000
LLM_BASE_URL = f"http://{LLM_HOST}:{LLM_PORT}"

@app.route('/health', methods=['GET'])
def health():
    """터널 서버 상태 확인"""
    return {
        "status": "ok",
        "tunnel": "reverse-http-tunnel-server",
        "location": "Spark (회사)",
        "target": LLM_BASE_URL
    }

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    """MiniPC의 요청을 회사 LLM 서버로 프록시"""
    url = f"{LLM_BASE_URL}/{path}"
    
    app.logger.info(f"Proxy: {request.method} {url}")
    
    try:
        # 회사 LLM 서버로 요청 전달
        resp = requests.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers if k.lower() != 'host'},
            data=request.get_data(),
            params=request.args,
            allow_redirects=False,
            timeout=120  # LLM 응답 대기 시간
        )
        
        # LLM 응답을 MiniPC로 전달
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(k, v) for k, v in resp.raw.headers.items() if k.lower() not in excluded_headers]
        
        return Response(
            resp.content,
            status=resp.status_code,
            headers=headers
        )
    
    except requests.exceptions.Timeout:
        app.logger.error(f"LLM timeout: {url}")
        return {"error": "LLM request timeout"}, 504
    
    except Exception as e:
        app.logger.error(f"Proxy error: {e}")
        return {"error": str(e)}, 502

@app.route('/')
def root():
    """루트 경로"""
    return {
        "service": "Reverse HTTP Tunnel Server",
        "location": "Spark (Company)",
        "target": LLM_BASE_URL,
        "endpoints": {
            "health": "/health",
            "proxy": "/*"
        }
    }

if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("=" * 60)
    print("Reverse HTTP Tunnel Server (Spark)")
    print("=" * 60)
    print(f"Listening: 0.0.0.0:8090")
    print(f"Local IP: {local_ip}")
    print(f"Target: {LLM_BASE_URL}")
    print(f"Access from MiniPC: http://{local_ip}:8090")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=8090,
        debug=False,
        threaded=True
    )
