#!/usr/bin/env python3
"""
HTTP Tunnel Server (MiniPC)

역할: 집(MiniPC)에서 실행되는 터널 서버
- 8089: 커맨드 채널 (SubPC와 영구 연결)
- 8090: 데이터 채널 (HTTP 트래픽, 다중 연결)

작성자: 이창연
작성일: 2025-11-12
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Tuple, Optional
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("Warning: PyYAML not installed. Using default config.")

try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


class TunnelServer:
    """HTTP 터널 서버 메인 클래스"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = self._setup_logger()
        
        # 클라이언트 대기 큐: client_ip → (reader, writer, first_byte)
        self.pending_clients: Dict[str, Tuple[asyncio.StreamReader, asyncio.StreamWriter, bytes]] = {}
        
        # 터널 대기 큐: client_ip → (tunnel_reader, tunnel_writer)
        # SubPC가 터널 연결을 먼저 만들고 READY를 보내는 경우를 처리
        self.pending_tunnels: Dict[str, Tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {}
        
        # 커맨드 채널 (SubPC 연결)
        self.command_writer: Optional[asyncio.StreamWriter] = None
        
        # 서버 인스턴스
        self.command_server = None
        self.data_server = None
        
        # 통계
        self.stats = {
            'total_connections': 0,
            'active_tunnels': 0,
            'bytes_transferred': 0
        }
    
    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger('TunnelServer')
        logger.setLevel(getattr(logging, self.config['logging']['level']))
        
        if COLORLOG_AVAILABLE and self.config['logging']['colored']:
            handler = colorlog.StreamHandler()
            handler.setFormatter(colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            ))
        else:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
        
        logger.addHandler(handler)
        
        # 파일 로깅 (설정된 경우)
        if self.config['logging']['file']:
            file_handler = logging.FileHandler(self.config['logging']['file'])
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            logger.addHandler(file_handler)
        
        return logger
    
    async def handle_command_channel(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        8089 포트: 커맨드 채널 핸들러
        SubPC와 영구 연결 유지, READY/ERROR 메시지 수신
        """
        addr = writer.get_extra_info('peername')
        self.logger.info(f"커맨드 채널 연결됨: {addr}")
        
        self.command_writer = writer
        
        try:
            while True:
                # 줄 단위로 읽기 (\n 구분)
                line = await reader.readline()
                if not line:
                    self.logger.warning("커맨드 채널 종료됨 (EOF)")
                    break
                
                message = line.decode('utf-8').strip()
                self.logger.debug(f"커맨드 수신: {message}")
                
                # 메시지 파싱
                parts = message.split()
                if len(parts) < 2:
                    self.logger.warning(f"잘못된 커맨드 형식: {message}")
                    continue
                
                cmd = parts[0]
                client_ip = parts[1]
                
                if cmd == "READY":
                    await self._handle_ready(client_ip)
                elif cmd == "ERROR":
                    error_msg = ' '.join(parts[2:]) if len(parts) > 2 else "Unknown error"
                    await self._handle_error(client_ip, error_msg)
                else:
                    self.logger.warning(f"알 수 없는 커맨드: {cmd}")
        
        except asyncio.CancelledError:
            self.logger.info("커맨드 채널 취소됨")
        except Exception as e:
            self.logger.error(f"커맨드 채널 에러: {e}", exc_info=True)
        finally:
            self.command_writer = None
            writer.close()
            await writer.wait_closed()
            self.logger.info("커맨드 채널 종료")
    
    async def _handle_ready(self, client_ip: str):
        """READY 메시지 처리: SubPC가 터널 준비 완료"""
        self.logger.info(f"READY 수신: {client_ip}")
        
        # 클라이언트가 아직 대기 중인 경우 (일반적인 경우)
        if client_ip in self.pending_clients:
            self.logger.debug(f"클라이언트 대기 중: {client_ip}")
            # 다음 터널 연결을 기다림 (pending_tunnels에 추가될 것)
            return
        
        # 터널이 먼저 연결된 경우 (드물지만 가능)
        if client_ip in self.pending_tunnels:
            self.logger.warning(f"READY: 터널이 클라이언트보다 먼저 도착 ({client_ip})")
            # 이미 터널이 대기 중이므로, 클라이언트 연결 대기
            return
        
        self.logger.warning(f"READY: 대기 중인 클라이언트 없음 ({client_ip})")
    
    async def _handle_error(self, client_ip: str, error_msg: str):
        """ERROR 메시지 처리: SubPC 연결 실패"""
        if client_ip not in self.pending_clients:
            self.logger.warning(f"ERROR: 대기 중인 클라이언트 없음 ({client_ip})")
            return
        
        self.logger.error(f"SubPC 에러 ({client_ip}): {error_msg}")
        
        # 클라이언트에게 502 Bad Gateway 응답
        _, writer, _ = self.pending_clients.pop(client_ip)
        try:
            writer.write(b"HTTP/1.1 502 Bad Gateway\r\n")
            writer.write(b"Content-Type: text/plain\r\n")
            writer.write(b"\r\n")
            writer.write(f"Tunnel error: {error_msg}\n".encode('utf-8'))
            await writer.drain()
        except Exception as e:
            self.logger.error(f"에러 응답 전송 실패: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def handle_data_channel(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        8090 포트: 데이터 채널 핸들러
        클라이언트 또는 SubPC 터널 연결 수락
        """
        addr = writer.get_extra_info('peername')
        client_ip = addr[0]
        
        self.stats['total_connections'] += 1
        self.logger.info(f"데이터 채널 연결됨: {addr}")
        
        # TODO: 클라이언트와 SubPC 터널을 구분하는 로직 필요
        # 현재는 간단하게 IP로 구분 (추후 핸드셰이크 추가)
        
        # 임시: 첫 바이트를 peek하여 HTTP 요청인지 확인
        # HTTP 요청이면 클라이언트, 아니면 SubPC 터널
        try:
            first_byte = await asyncio.wait_for(reader.read(1), timeout=1.0)
            if not first_byte:
                writer.close()
                await writer.wait_closed()
                return
            
            # 데이터 되돌리기 (Python asyncio는 unread 불가, 임시 버퍼 사용)
            # TODO: 더 나은 방법 찾기
            
            # HTTP 메서드 체크 (G=GET, P=POST, H=HEAD, etc.)
            if first_byte in b'GPHPDO':  # GET, POST, HEAD, PUT, DELETE, OPTIONS
                self.logger.debug(f"HTTP 요청 감지: {client_ip}")
                await self._handle_client_request(reader, writer, client_ip, first_byte)
            elif first_byte == b'T':  # 터널 식별자
                self.logger.debug(f"SubPC 터널 연결 감지: {client_ip}")
                # 'T'는 식별자이므로 relay에 포함하지 않음 (빈 바이트)
                await self._handle_tunnel_connection(reader, writer, client_ip, b'')
            else:
                self.logger.warning(f"알 수 없는 연결: {client_ip}, first_byte={first_byte}")
                writer.close()
                await writer.wait_closed()
        
        except asyncio.TimeoutError:
            self.logger.warning(f"연결 타임아웃: {addr}")
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            self.logger.error(f"데이터 채널 에러: {e}", exc_info=True)
            writer.close()
            await writer.wait_closed()
    
    async def _handle_client_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                                     client_ip: str, first_byte: bytes):
        """클라이언트 HTTP 요청 처리"""
        self.logger.info(f"클라이언트 요청 처리: {client_ip}")
        
        # 클라이언트 대기 큐에 추가
        self.pending_clients[client_ip] = (reader, writer, first_byte)
        
        # SubPC에게 NEW_CONN 전송
        if not self.command_writer:
            self.logger.error("커맨드 채널 없음! SubPC가 연결되지 않았습니다.")
            writer.write(b"HTTP/1.1 503 Service Unavailable\r\n\r\nTunnel not ready\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            del self.pending_clients[client_ip]
            return
        
        target_host = self.config['default_target']['host']
        target_port = self.config['default_target']['port']
        
        new_conn_msg = f"NEW_CONN {client_ip} {target_host}:{target_port}\n"
        self.logger.debug(f"전송: {new_conn_msg.strip()}")
        
        try:
            self.command_writer.write(new_conn_msg.encode('utf-8'))
            await self.command_writer.drain()
        except Exception as e:
            self.logger.error(f"NEW_CONN 전송 실패: {e}")
            writer.write(b"HTTP/1.1 503 Service Unavailable\r\n\r\nTunnel error\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            del self.pending_clients[client_ip]
            return
        
        # SubPC 터널 연결 대기 (타임아웃)
        # _handle_tunnel_connection에서 매칭하여 relay 시작
        # 여기서는 대기하지 않고 종료 (비동기 처리)
    
    async def _handle_tunnel_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                                       client_ip: str, first_byte: bytes):
        """SubPC 터널 연결 처리"""
        self.logger.info(f"SubPC 터널 연결: {client_ip}")
        
        # pending_clients에서 매칭
        if client_ip not in self.pending_clients:
            self.logger.warning(f"터널: 대기 중인 클라이언트 없음 ({client_ip})")
            # 터널을 pending_tunnels에 추가 (드문 경우)
            self.pending_tunnels[client_ip] = (reader, writer)
            # 5초 후 정리
            await asyncio.sleep(self.config['timeouts']['pending_timeout'])
            if client_ip in self.pending_tunnels:
                self.logger.error(f"터널 타임아웃 (클라이언트 없음): {client_ip}")
                del self.pending_tunnels[client_ip]
                writer.close()
                await writer.wait_closed()
            return
        
        # 클라이언트 매칭
        client_reader, client_writer, first_byte_client = self.pending_clients.pop(client_ip)
        
        self.logger.info(f"✓ 터널 매칭 성공: {client_ip}")
        self.stats['active_tunnels'] += 1
        
        # 양방향 relay 시작
        try:
            await self._relay_bidirectional(
                client_reader, client_writer, first_byte_client,
                reader, writer, first_byte,
                client_ip
            )
        except Exception as e:
            self.logger.error(f"Relay 에러: {e}", exc_info=True)
        finally:
            self.stats['active_tunnels'] -= 1
            self.logger.info(f"터널 종료: {client_ip}")
    
    async def _relay_bidirectional(self,
                                   client_reader: asyncio.StreamReader,
                                   client_writer: asyncio.StreamWriter,
                                   client_first_byte: bytes,
                                   tunnel_reader: asyncio.StreamReader,
                                   tunnel_writer: asyncio.StreamWriter,
                                   tunnel_first_byte: bytes,
                                   client_ip: str):
        """양방향 TCP Relay"""
        self.logger.debug(f"Relay 시작: {client_ip}")
        
        async def forward(src_reader, src_writer, dst_writer, direction: str, first_byte: bytes = b''):
            """단방향 데이터 전달"""
            total_bytes = 0
            try:
                # 첫 바이트 전송 (이미 읽은 데이터)
                if first_byte:
                    dst_writer.write(first_byte)
                    await dst_writer.drain()
                    total_bytes += len(first_byte)
                
                # 데이터 relay
                while True:
                    data = await src_reader.read(8192)
                    if not data:
                        self.logger.debug(f"{direction} EOF: {client_ip}")
                        break
                    
                    dst_writer.write(data)
                    await dst_writer.drain()
                    total_bytes += len(data)
                
                self.logger.debug(f"{direction} 완료: {client_ip}, {total_bytes} bytes")
            except asyncio.CancelledError:
                self.logger.debug(f"{direction} 취소됨: {client_ip}")
                raise
            except Exception as e:
                self.logger.error(f"{direction} 에러: {e}")
            finally:
                try:
                    dst_writer.close()
                    await dst_writer.wait_closed()
                except:
                    pass
            
            return total_bytes
        
        # 양방향 동시 실행
        try:
            results = await asyncio.gather(
                forward(client_reader, client_writer, tunnel_writer, "Client→Tunnel", client_first_byte),
                forward(tunnel_reader, tunnel_writer, client_writer, "Tunnel→Client", tunnel_first_byte),
                return_exceptions=True
            )
            
            # 통계 업데이트
            for result in results:
                if isinstance(result, int):
                    self.stats['bytes_transferred'] += result
        
        except Exception as e:
            self.logger.error(f"Relay 에러: {e}", exc_info=True)
        finally:
            # 양쪽 소켓 정리
            for writer in [client_writer, tunnel_writer]:
                try:
                    writer.close()
                    await writer.wait_closed()
                except:
                    pass
    
    async def start(self):
        """서버 시작"""
        bind_addr = self.config['server']['bind_address']
        cmd_port = self.config['server']['command_port']
        data_port = self.config['server']['data_port']
        
        self.logger.info("="*60)
        self.logger.info("HTTP Tunnel Server 시작")
        self.logger.info(f"커맨드 채널: {bind_addr}:{cmd_port}")
        self.logger.info(f"데이터 채널: {bind_addr}:{data_port}")
        self.logger.info("="*60)
        
        # 커맨드 채널 서버
        self.command_server = await asyncio.start_server(
            self.handle_command_channel,
            bind_addr,
            cmd_port
        )
        self.logger.info(f"✓ 커맨드 채널 LISTEN: {cmd_port}")
        
        # 데이터 채널 서버
        self.data_server = await asyncio.start_server(
            self.handle_data_channel,
            bind_addr,
            data_port
        )
        self.logger.info(f"✓ 데이터 채널 LISTEN: {data_port}")
        
        # 서버 실행
        async with self.command_server, self.data_server:
            await asyncio.gather(
                self.command_server.serve_forever(),
                self.data_server.serve_forever()
            )
    
    async def stop(self):
        """서버 정지"""
        self.logger.info("서버 정지 중...")
        
        if self.command_server:
            self.command_server.close()
            await self.command_server.wait_closed()
        
        if self.data_server:
            self.data_server.close()
            await self.data_server.wait_closed()
        
        self.logger.info("서버 정지 완료")


def load_config(config_path: str = 'config.yaml') -> dict:
    """설정 파일 로드"""
    config_file = Path(config_path)
    
    if not config_file.exists():
        print(f"Warning: Config file not found: {config_path}")
        print("Using default configuration")
        return get_default_config()
    
    if not YAML_AVAILABLE:
        print("Warning: PyYAML not installed. Using default config.")
        return get_default_config()
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        print("Using default configuration")
        return get_default_config()


def get_default_config() -> dict:
    """기본 설정 반환"""
    return {
        'server': {
            'command_port': 8089,
            'data_port': 8090,
            'bind_address': '0.0.0.0'
        },
        'timeouts': {
            'pending_timeout': 5,
            'relay_timeout': 30
        },
        'logging': {
            'level': 'INFO',
            'file': None,
            'colored': True
        },
        'default_target': {
            'host': '172.21.113.31',
            'port': 4000
        }
    }


async def main():
    """메인 엔트리포인트"""
    config = load_config()
    server = TunnelServer(config)
    
    # 시그널 핸들러 등록
    loop = asyncio.get_running_loop()
    
    def signal_handler():
        print("\nShutdown signal received...")
        asyncio.create_task(server.stop())
        loop.stop()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received")
    finally:
        await server.stop()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
