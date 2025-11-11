#!/usr/bin/env python3
"""
Simple HTTP Tunnel Server
miniPC에서 실행하여 Spark의 HTTP 요청을 LLM(172.21.113.31:4000)으로 프록시
"""
from flask import Flask, request, Response
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# LLM 서버 설정
LLM_HOST = "172.21.113.31"
LLM_PORT = 4000
LLM_BASE_URL = f"http://{LLM_HOST}:{LLM_PORT}"

@app.route('/health', methods=['GET'])
def health():
    """터널 서버 상태 확인"""
    return {
        "status": "ok",
        "tunnel": "http-tunnel-server",
        "target": LLM_BASE_URL
    }

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    """모든 요청을 LLM 서버로 프록시"""
    url = f"{LLM_BASE_URL}/{path}"
    
    app.logger.info(f"Proxy: {request.method} {url}")
    
    try:
        # LLM 서버로 요청 전달
        resp = requests.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers if k.lower() != 'host'},
            data=request.get_data(),
            params=request.args,
            allow_redirects=False,
            timeout=120  # LLM 응답 대기 시간
        )
        
        # LLM 응답을 클라이언트로 전달
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
        "service": "HTTP Tunnel Server",
        "target": LLM_BASE_URL,
        "endpoints": {
            "health": "/health",
            "proxy": "/*"
        }
    }

if __name__ == '__main__':
    print("=" * 60)
    print("HTTP Tunnel Server")
    print("=" * 60)
    print(f"Listening: 0.0.0.0:8088")
    print(f"Target: {LLM_BASE_URL}")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=8088,
        debug=False,
        threaded=True
    )
