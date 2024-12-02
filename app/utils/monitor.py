from typing import Dict, Any, Optional
import asyncio
import threading
import time
from datetime import datetime
from flask import Flask
from ..services.supervisor_service import SupervisorService

class HostMonitor:
    def __init__(self, app: Flask, supervisor_service: SupervisorService) -> None:
        self.app: Flask = app
        self.supervisor_service: SupervisorService = supervisor_service
        self.monitoring: bool = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.host_status: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def start_monitoring(self) -> None:
        """启动监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self) -> None:
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()

    async def _check_host_async(self, host_id: str, host_config: Dict[str, Any]) -> None:
        """异步检查单个主机状态
        
        Args:
            host_id: 主机ID
            host_config: 主机配置信息
        """
        try:
            status = await asyncio.to_thread(
                self.supervisor_service.check_connection,
                host_config
            )
            self._update_host_status(host_id, status)
        except Exception as e:
            self.app.logger.error(f"Error checking host {host_id}: {e}")
            self._update_host_status(host_id, False)

    def _monitor_loop(self) -> None:
        """监控循环"""
        while self.monitoring:
            with self.app.app_context():
                hosts = self.supervisor_service.config_manager.get_all_hosts()
                
                # 创建异步任务列表
                async def check_all_hosts():
                    tasks = [
                        self._check_host_async(host_id, host_config)
                        for host_id, host_config in hosts.items()
                    ]
                    await asyncio.gather(*tasks)

                # 运行异步任务
                asyncio.run(check_all_hosts())
            
            time.sleep(60)  # 每分钟检查一次

    def _update_host_status(self, host_id: str, status: bool) -> None:
        """更新主机状态
        
        Args:
            host_id: 主机ID
            status: 主机状态
        """
        with self._lock:
            now = datetime.now()
            prev_status = self.host_status.get(host_id, {}).get('status')
            
            self.host_status[host_id] = {
                'status': status,
                'last_check': now,
                'last_change': now if status != prev_status else 
                              self.host_status.get(host_id, {}).get('last_change', now)
            }

            # 如果状态发生变化，记录日志
            if status != prev_status:
                self.app.logger.info(
                    f"Host {host_id} status changed to: {'online' if status else 'offline'}"
                )

    def get_host_status(self, host_id: str) -> Dict[str, Any]:
        """获取主机状态
        
        Args:
            host_id: 主机ID
            
        Returns:
            Dict[str, Any]: 主机状态信息
        """
        with self._lock:
            return self.host_status.get(host_id, {
                'status': False,
                'last_check': None,
                'last_change': None
            })

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有主机状态
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有主机的状态信息
        """
        with self._lock:
            return self.host_status.copy()