#!/usr/bin/env python3
"""
HTTP Tunnel Client

회사 내부망에서 집의 터널 서버로 역방향 연결하여
외부에서 내부 LLM 서버 접근을 가능하게 하는 클라이언트

작동 방식:
1. 커맨드 채널 (8089): 터널 서버와 영구 연결, NEW_CONN 메시지 수신
2. 데이터 채널 (8091): NEW_CONN마다 새 연결 생성, LLM 서버와 relay
3. HTTP CONNECT 프록시: 회사 프록시를 통해 터널 서버 접근
"""

import asyncio
import socket
import struct
import yaml
import logging
import colorlog
from typing import Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """클라이언트 설정"""
    tunnel_host: str
    command_port: int
    data_port: int
    proxy_enabled: bool
    proxy_host: str
    proxy_port: int
    target_host: str
    target_port: int
    log_level: str
    log_file: str
    log_console: bool
    reconnect_enabled: bool
    reconnect_delay: int
    reconnect_max_attempts: int
    stats_enabled: bool
    stats_interval: int


class TunnelClient:
    """터널 클라이언트 메인 클래스"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = self._setup_logging()
        self.command_channel: Optional[asyncio.StreamWriter] = None
        self.running = False
        self.stats = {
            'connections': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
        }
        
    def _setup_logging(self) -> logging.Logger:
        """로깅 설정"""
        logger = logging.getLogger('TunnelClient')
        logger.setLevel(getattr(logging, self.config.log_level))
        
        # 파일 핸들러
        file_handler = logging.FileHandler(self.config.log_file, encoding='utf-8')
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        )
        logger.addHandler(file_handler)
        
        # 콘솔 핸들러 (컬러)
        if self.config.log_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                colorlog.ColoredFormatter(
                    '%(log_color)s%(asctime)s [%(levelname)s] %(message)s',
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    }
                )
            )
            logger.addHandler(console_handler)
        
        return logger
    
    async def _connect_through_proxy(
        self, 
        target_host: str, 
        target_port: int
    ) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """HTTP CONNECT 프록시를 통한 연결
        
        Args:
            target_host: 대상 호스트
            target_port: 대상 포트
            
        Returns:
            (reader, writer) 튜플
        """
        self.logger.info(
            f"프록시 연결: {self.config.proxy_host}:{self.config.proxy_port}"
        )
        
        # 1. 프록시 서버에 연결
        reader, writer = await asyncio.open_connection(
            self.config.proxy_host, 
            self.config.proxy_port
        )
        
        # 2. HTTP CONNECT 요청 전송
        connect_request = (
            f"CONNECT {target_host}:{target_port} HTTP/1.1\r\n"
            f"Host: {target_host}:{target_port}\r\n"
            f"\r\n"
        )
        writer.write(connect_request.encode())
        await writer.drain()
        
        self.logger.debug(f"CONNECT 요청 전송: {target_host}:{target_port}")
        
        # 3. 프록시 응답 읽기
        response_line = await reader.readline()
        response = response_line.decode().strip()
        
        self.logger.debug(f"프록시 응답: {response}")
        
        if "200" not in response:
            writer.close()
            await writer.wait_closed()
            raise Exception(f"프록시 연결 실패: {response}")
        
        # 4. 헤더 읽기 (빈 줄까지)
        while True:
            header = await reader.readline()
            if header == b'\r\n' or header == b'\n':
                break
        
        self.logger.info(f"프록시 터널 설정 완료: {target_host}:{target_port}")
        return reader, writer
    
    async def _connect_to_tunnel_server(
        self, 
        port: int
    ) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """터널 서버에 연결
        
        Args:
            port: 연결할 포트 (커맨드 채널 또는 데이터 채널)
            
        Returns:
            (reader, writer) 튜플
        """
        if self.config.proxy_enabled:
            return await self._connect_through_proxy(
                self.config.tunnel_host, 
                port
            )
        else:
            self.logger.info(
                f"터널 서버 직접 연결: {self.config.tunnel_host}:{port}"
            )
            return await asyncio.open_connection(
                self.config.tunnel_host, 
                port
            )
    
    async def _connect_to_target_server(
        self
    ) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """대상 서버(LLM)에 연결
        
        Returns:
            (reader, writer) 튜플
        """
        self.logger.info(
            f"대상 서버 연결: {self.config.target_host}:{self.config.target_port}"
        )
        return await asyncio.open_connection(
            self.config.target_host, 
            self.config.target_port
        )
    
    async def _relay_data(
        self, 
        reader: asyncio.StreamReader, 
        writer: asyncio.StreamWriter,
        direction: str
    ):
        """단방향 데이터 relay
        
        Args:
            reader: 소스 reader
            writer: 대상 writer
            direction: 방향 표시 (로깅용)
        """
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                
                writer.write(data)
                await writer.drain()
                
                if direction == "client->target":
                    self.stats['bytes_sent'] += len(data)
                else:
                    self.stats['bytes_received'] += len(data)
                
                self.logger.debug(f"{direction}: {len(data)} bytes")
        except Exception as e:
            self.logger.debug(f"Relay 종료 ({direction}): {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
    
    async def _handle_data_channel(self, client_ip: str):
        """데이터 채널 처리
        
        NEW_CONN 메시지 수신 시 호출됨
        1. 터널 서버의 데이터 채널에 연결
        2. 첫 바이트로 'T' 전송 (터널 식별)
        3. 대상 서버(LLM)에 연결
        4. 양방향 relay
        
        Args:
            client_ip: 클라이언트 IP (매칭용)
        """
        tunnel_reader = None
        tunnel_writer = None
        target_reader = None
        target_writer = None
        
        try:
            # 1. 터널 서버 데이터 채널에 연결
            self.logger.info(f"데이터 채널 연결 시작: {client_ip}")
            tunnel_reader, tunnel_writer = await self._connect_to_tunnel_server(
                self.config.data_port
            )
            
            # 2. 첫 바이트 'T' 전송 (터널 식별자)
            tunnel_writer.write(b'T')
            await tunnel_writer.drain()
            self.logger.debug("터널 식별자 전송: T")
            
            # 3. 대상 서버(LLM)에 연결
            target_reader, target_writer = await self._connect_to_target_server()
            
            self.logger.info(f"데이터 채널 relay 시작: {client_ip}")
            self.stats['connections'] += 1
            
            # 4. 양방향 relay
            await asyncio.gather(
                self._relay_data(tunnel_reader, target_writer, "client->target"),
                self._relay_data(target_reader, tunnel_writer, "target->client")
            )
            
            self.logger.info(f"데이터 채널 종료: {client_ip}")
            
        except Exception as e:
            self.logger.error(f"데이터 채널 에러 ({client_ip}): {e}")
        finally:
            # 모든 연결 종료
            for writer in [tunnel_writer, target_writer]:
                if writer:
                    try:
                        writer.close()
                        await writer.wait_closed()
                    except:
                        pass
    
    async def _handle_command_channel(self):
        """커맨드 채널 처리
        
        1. 터널 서버에 영구 연결
        2. READY 메시지 전송
        3. NEW_CONN 메시지 수신 대기
        4. NEW_CONN 수신 시 데이터 채널 생성
        """
        try:
            # 1. 커맨드 채널 연결
            self.logger.info("커맨드 채널 연결 중...")
            reader, writer = await self._connect_to_tunnel_server(
                self.config.command_port
            )
            self.command_channel = writer
            
            # 2. READY 메시지 전송
            target = f"{self.config.target_host}:{self.config.target_port}"
            ready_msg = f"READY {target}\n"
            writer.write(ready_msg.encode())
            await writer.drain()
            
            self.logger.info(f"커맨드 채널 연결 완료, READY 전송: {target}")
            
            # 3. NEW_CONN 메시지 수신 루프
            while self.running:
                line = await reader.readline()
                if not line:
                    self.logger.warning("커맨드 채널 종료됨")
                    break
                
                message = line.decode().strip()
                self.logger.debug(f"커맨드 수신: {message}")
                
                # NEW_CONN 메시지 파싱
                if message.startswith("NEW_CONN "):
                    client_ip = message.split()[1]
                    self.logger.info(f"NEW_CONN 수신: {client_ip}")
                    
                    # 비동기로 데이터 채널 처리
                    asyncio.create_task(self._handle_data_channel(client_ip))
                
                # ERROR 메시지 처리
                elif message.startswith("ERROR "):
                    error_msg = message[6:]
                    self.logger.error(f"서버 에러: {error_msg}")
                
        except Exception as e:
            self.logger.error(f"커맨드 채널 에러: {e}")
        finally:
            if self.command_channel:
                try:
                    self.command_channel.close()
                    await self.command_channel.wait_closed()
                except:
                    pass
                self.command_channel = None
    
    async def _print_stats(self):
        """통계 출력 (주기적)"""
        while self.running:
            await asyncio.sleep(self.config.stats_interval)
            if self.stats['connections'] > 0:
                self.logger.info(
                    f"통계 - 연결: {self.stats['connections']}, "
                    f"송신: {self.stats['bytes_sent']} bytes, "
                    f"수신: {self.stats['bytes_received']} bytes"
                )
    
    async def run(self):
        """클라이언트 실행"""
        self.running = True
        self.logger.info("=== 터널 클라이언트 시작 ===")
        self.logger.info(f"터널 서버: {self.config.tunnel_host}")
        self.logger.info(f"대상 서버: {self.config.target_host}:{self.config.target_port}")
        self.logger.info(f"프록시: {'사용' if self.config.proxy_enabled else '사용 안함'}")
        
        attempt = 0
        max_attempts = self.config.reconnect_max_attempts
        
        while self.running:
            try:
                # 재연결 시도 제한 확인
                if max_attempts > 0 and attempt >= max_attempts:
                    self.logger.error(f"최대 재연결 시도 횟수 초과: {max_attempts}")
                    break
                
                if attempt > 0:
                    self.logger.info(
                        f"재연결 시도 {attempt}/{max_attempts if max_attempts > 0 else '∞'}"
                    )
                
                attempt += 1
                
                # 통계 출력 태스크 시작
                stats_task = None
                if self.config.stats_enabled:
                    stats_task = asyncio.create_task(self._print_stats())
                
                # 커맨드 채널 실행
                await self._handle_command_channel()
                
                # 통계 태스크 종료
                if stats_task:
                    stats_task.cancel()
                    try:
                        await stats_task
                    except asyncio.CancelledError:
                        pass
                
                # 재연결 대기
                if self.running and self.config.reconnect_enabled:
                    self.logger.info(
                        f"{self.config.reconnect_delay}초 후 재연결..."
                    )
                    await asyncio.sleep(self.config.reconnect_delay)
                else:
                    break
                    
            except KeyboardInterrupt:
                self.logger.info("사용자 중단 (Ctrl+C)")
                break
            except Exception as e:
                self.logger.error(f"예외 발생: {e}")
                if self.running and self.config.reconnect_enabled:
                    await asyncio.sleep(self.config.reconnect_delay)
                else:
                    break
        
        self.running = False
        self.logger.info("=== 터널 클라이언트 종료 ===")
    
    def stop(self):
        """클라이언트 중지"""
        self.running = False
        if self.command_channel:
            try:
                self.command_channel.close()
            except:
                pass


def load_config(config_path: str = "config.yaml") -> Config:
    """설정 파일 로드
    
    Args:
        config_path: 설정 파일 경로
        
    Returns:
        Config 객체
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    return Config(
        tunnel_host=data['tunnel_server']['host'],
        command_port=data['tunnel_server']['command_port'],
        data_port=data['tunnel_server']['data_port'],
        proxy_enabled=data['proxy']['enabled'],
        proxy_host=data['proxy']['host'],
        proxy_port=data['proxy']['port'],
        target_host=data['target_server']['host'],
        target_port=data['target_server']['port'],
        log_level=data['logging']['level'],
        log_file=data['logging']['file'],
        log_console=data['logging']['console'],
        reconnect_enabled=data['reconnect']['enabled'],
        reconnect_delay=data['reconnect']['delay'],
        reconnect_max_attempts=data['reconnect']['max_attempts'],
        stats_enabled=data['stats']['enabled'],
        stats_interval=data['stats']['interval'],
    )


async def main():
    """메인 진입점"""
    # 설정 로드
    config = load_config()
    
    # 클라이언트 생성 및 실행
    client = TunnelClient(config)
    
    try:
        await client.run()
    except KeyboardInterrupt:
        print("\n프로그램 종료 중...")
        client.stop()


if __name__ == "__main__":
    asyncio.run(main())
