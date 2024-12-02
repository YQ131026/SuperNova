import yaml
import os
import logging
from typing import Dict, List, Optional, Any

class ConfigManager:
    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
        self.hosts_file = os.path.join(self.config_dir, 'hosts.yaml')
        self._hosts_cache = None
        self._last_read_time = 0
        
        # 确保配置目录存在
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        # 确保hosts配置文件存在
        if not os.path.exists(self.hosts_file):
            self.save_hosts({})

    def _should_reload_config(self) -> bool:
        """检查是否需要重新加载配置
        
        Returns:
            bool: 是否需要重新加载
        """
        if not os.path.exists(self.hosts_file):
            return True
            
        current_mtime = os.path.getmtime(self.hosts_file)
        return current_mtime > self._last_read_time

    def get_all_hosts(self) -> Dict[str, Dict[str, Any]]:
        """获取所有主机配置
        
        Returns:
            Dict[str, Dict[str, Any]]: 主机ID到主机配置的映射
        """
        try:
            if self._should_reload_config():
                with open(self.hosts_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    self._hosts_cache = config.get('hosts', {})
                    if not isinstance(self._hosts_cache, dict):
                        self._hosts_cache = {}
                    self._last_read_time = os.path.getmtime(self.hosts_file)
                    logging.info(f"Reloaded hosts configuration, found {len(self._hosts_cache)} hosts")
            return self._hosts_cache or {}
        except Exception as e:
            logging.error(f"加载主机配置失败: {str(e)}")
            return {}

    def get_host(self, host_id: str) -> Optional[Dict[str, Any]]:
        """获取指定主机配置
        
        Args:
            host_id: 主机ID
            
        Returns:
            Optional[Dict[str, Any]]: 主机配置，如果不存在则返回 None
        """
        hosts = self.get_all_hosts()
        host = hosts.get(host_id)
        if host:
            return {**host, 'id': host_id}
        return None

    def save_hosts(self, hosts: Dict[str, Dict[str, Any]]) -> bool:
        """保存主机配置
        
        Args:
            hosts: 主机配置字典，键为主机ID
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 验证主机配置
            for host_id, host in hosts.items():
                required_fields = ['ip', 'port', 'username', 'password']
                if not all(field in host for field in required_fields):
                    missing = [field for field in required_fields if field not in host]
                    raise ValueError(f"Host {host_id} missing required fields: {', '.join(missing)}")

            with open(self.hosts_file, 'w', encoding='utf-8') as f:
                yaml.dump({'hosts': hosts}, f, allow_unicode=True)
            
            # 强制下次重新加载配置
            self._hosts_cache = None
            self._last_read_time = 0
            return True
        except Exception as e:
            logging.error(f"保存主机配置失败: {str(e)}")
            return False

    def add_host(self, host_id: str, host: Dict[str, Any]) -> bool:
        """添加主机
        
        Args:
            host_id: 主机ID
            host: 主机配置信息
            
        Returns:
            bool: 是否添加成功
        """
        hosts = self.get_all_hosts()
        if host_id in hosts:
            return False
            
        hosts[host_id] = host
        return self.save_hosts(hosts)

    def update_host(self, host_id: str, host: Dict[str, Any]) -> bool:
        """更新主机
        
        Args:
            host_id: 主机ID
            host: 新的主机配置信息
            
        Returns:
            bool: 是否更新成功
        """
        hosts = self.get_all_hosts()
        if host_id not in hosts:
            return False
            
        hosts[host_id].update(host)
        return self.save_hosts(hosts)

    def delete_host(self, host_id: str) -> bool:
        """删除主机
        
        Args:
            host_id: 主机ID
            
        Returns:
            bool: 是否删除成功
        """
        hosts = self.get_all_hosts()
        if host_id not in hosts:
            return False
            
        del hosts[host_id]
        return self.save_hosts(hosts)
