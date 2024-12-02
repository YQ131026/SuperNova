from typing import Dict, List, Any, Optional
import logging
import os
import urllib.parse
import xmlrpc.client
import time
import base64
from ..utils.config import ConfigManager

# 添加 AuthTransport 类定义
class AuthTransport(xmlrpc.client.Transport):
    """用于处理 XML-RPC 认证的传输类"""
    def __init__(self, username: str, password: str, timeout: int = 10):
        super().__init__()
        self.username = username
        self.password = password
        self.timeout = timeout
        self.auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        self._cached_connections = {}

    def _get_host_key(self, host) -> str:
        """获取主机的唯一标识符"""
        if isinstance(host, str):
            return host
        elif isinstance(host, dict):
            return f"{host['ip']}:{host['port']}"
        raise ValueError(f"Unsupported host format: {type(host)}")

    def make_connection(self, host):
        """创建或获取缓存的HTTP连接"""
        try:
            host_key = self._get_host_key(host)
            
            if host_key not in self._cached_connections:
                conn = super().make_connection(host_key)
                if hasattr(conn, 'timeout'):
                    conn.timeout = self.timeout
                self._cached_connections[host_key] = conn
                
            return self._cached_connections[host_key]
        except Exception as e:
            raise ConnectionError(f"Failed to create connection: {str(e)}")

    def send_request(self, host, handler, request_body, verbose=False):
        """发送请求并添加认证头"""
        connection = self.make_connection(host)
        
        connection.putrequest("POST", handler)
        connection.putheader('Authorization', f'Basic {self.auth}')
        connection.putheader('Content-Type', 'text/xml')
        connection.putheader('Content-Length', str(len(request_body)))
        connection.endheaders(request_body)
        
        return connection

    def close(self):
        """关闭所有缓存的连接"""
        for conn in self._cached_connections.values():
            if hasattr(conn, 'close'):
                conn.close()
        self._cached_connections.clear()
        super().close()

class SupervisorService:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.logger = logging.getLogger(__name__)

    def get_all_hosts(self) -> List[Dict[str, Any]]:
        """获取所有主机列表
        
        Returns:
            List[Dict[str, Any]]: 主机信息列表，每个主机包含完整的配置信息
        """
        try:
            hosts_config = self.config_manager.get_all_hosts()
            if not hosts_config:
                self.logger.warning("No hosts found in configuration")
                return []
                
            self.logger.info(f"Found {len(hosts_config)} hosts in configuration")
            result = []
            
            for host_id, host in hosts_config.items():
                try:
                    if not isinstance(host, dict):
                        self.logger.error(f"Invalid host configuration for {host_id}: {host}")
                        continue
                        
                    # 验证并转换端口为整数
                    try:
                        port = int(host.get('port', 0))
                        if not (1 <= port <= 65535):
                            self.logger.error(f"Invalid port number for host {host_id}: {port}")
                            continue
                    except (ValueError, TypeError):
                        self.logger.error(f"Invalid port value for host {host_id}: {host.get('port')}")
                        continue

                    # 验证必要字段
                    required_fields = ['ip', 'username', 'password']
                    if not all(field in host for field in required_fields):
                        missing_fields = [field for field in required_fields if field not in host]
                        self.logger.error(f"Missing required fields for host {host_id}: {missing_fields}")
                        continue

                    host_info = {
                        'id': host_id,
                        'name': host.get('name', f"{host['ip']}:{port}"),
                        'ip': host['ip'],
                        'port': port,
                        'username': host['username'],
                        'status': 'connected' if self.check_connection(host) else 'disconnected'
                    }
                    result.append(host_info)
                except Exception as e:
                    self.logger.error(f"Error processing host {host_id}: {str(e)}")
                    continue
                    
            self.logger.info(f"Successfully processed {len(result)} hosts")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get hosts list: {str(e)}")
            return []

    def get_host(self, host_id: str) -> Optional[Dict[str, Any]]:
        """获取指定主机信息
        
        Args:
            host_id: 主机ID
            
        Returns:
            Optional[Dict[str, Any]]: 主机信息，如果不存在则返回 None
        """
        host = self.config_manager.get_host(host_id)
        if not host:
            return None
            
        try:
            # 验证并转换端口为整数
            try:
                port = int(host['port'])
            except (ValueError, TypeError):
                self.logger.error(f"Invalid port for host {host_id}: {host['port']}")
                return None

            return {
                'id': host_id,  
                'name': host.get('name', f"{host['ip']}:{port}"),
                'ip': host['ip'],
                'port': port,
                'username': host['username'],
                'password': host['password'],
                'status': 'connected' if self.check_connection(host) else 'disconnected'
            }
        except Exception as e:
            self.logger.error(f"Error processing host {host_id}: {str(e)}")
            return None

    def _get_supervisor_proxy(self, host: Dict[str, Any]) -> xmlrpc.client.ServerProxy:
        """创建到 Supervisor XML-RPC 服务器的代理连接"""
        try:
            # 提取并验证连接信息
            ip = str(host.get('ip', ''))
            port = int(host.get('port', 0))
            username = str(host.get('username', ''))
            password = str(host.get('password', ''))

            if not all([ip, port, username, password]):
                raise ValueError("Missing required connection information")

            # 构建主机地址字符串
            host_addr = f"{ip}:{port}"
            self.logger.info(f"Creating supervisor proxy for {host_addr}")
            
            # 构建URL
            url = f"http://{host_addr}/RPC2"
            
            # 创建传输对象
            transport = AuthTransport(
                username=username,
                password=password,
                timeout=10
            )
            
            # 创建代理
            proxy = xmlrpc.client.ServerProxy(
                url,
                transport=transport,
                allow_none=True,
                verbose=False
            )
            
            # 验证连接
            try:
                state = proxy.supervisor.getState()
                self.logger.info(f"Successfully connected to supervisor at {host_addr}")
                return proxy
            except xmlrpc.client.ProtocolError as e:
                if e.errcode == 401:
                    raise ConnectionError("Authentication failed - check username and password")
                raise
            except Exception as e:
                raise ConnectionError(f"Failed to verify connection: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Failed to create supervisor proxy for {host.get('ip')}:{host.get('port')}: {str(e)}")
            raise ConnectionError(f"Failed to connect to supervisor: {str(e)}")

    def _get_supervisor(self, host_id: str) -> Optional[xmlrpc.client.ServerProxy]:
        """获取supervisor XML-RPC连接"""
        try:
            host = self.config_manager.get_host(host_id)
            if not host:
                raise ValueError(f"Host {host_id} not found")
            
            # 添加连接重试
            MAX_RETRIES = 3
            RETRY_DELAY = 1
            
            last_error = None
            for attempt in range(MAX_RETRIES):
                try:
                    # 构建标准化的连接信息
                    connection_info = {
                        'ip': str(host.get('ip', '')),
                        'port': int(host.get('port', 0)),
                        'username': str(host.get('username', '')),
                        'password': str(host.get('password', ''))
                    }
                    
                    proxy = self._get_supervisor_proxy(connection_info)
                    if not proxy:
                        raise ConnectionError("Failed to create supervisor proxy")
                        
                    # 验证连接
                    proxy.supervisor.getState()
                    return proxy
                    
                except Exception as e:
                    last_error = str(e)
                    self.logger.warning(f"Connection attempt {attempt + 1}/{MAX_RETRIES} failed: {last_error}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        
            raise ConnectionError(f"Failed to connect after {MAX_RETRIES} attempts. Last error: {last_error}")
            
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            self.logger.error(f"Failed to connect to supervisor at {host_id}: {str(e)}")
            raise ConnectionError(f"Failed to connect to supervisor: {str(e)}")

    def check_connection(self, host: Dict[str, Any]) -> bool:
        """检查与机的连接状态
        
        Args:
            host: 主机配置信息
            
        Returns:
            bool: 连接是否成功
        """
        try:
            # 确保传入的是字典并提取必要信息
            if not isinstance(host, dict):
                self.logger.error("Invalid host configuration: not a dictionary")
                return False
            
            # 直接使用原始主机配置
            try:
                proxy = self._get_supervisor_proxy(host)
                state = proxy.supervisor.getState()
                self.logger.debug(f"Successfully connected to {host.get('ip')}:{host.get('port')}")
                return True
            except Exception as e:
                self.logger.debug(f"Connection test failed for {host.get('ip')}:{host.get('port')}: {str(e)}")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to check host status: {str(e)}")
            return False

    def get_all_processes(self, host_id: str) -> List[Dict[str, Any]]:
        """获取所有进程信息
        
        Args:
            host_id: 主机ID
            
        Returns:
            List[Dict[str, Any]]: 进程信息列表
        """
        host = self.config_manager.get_host(host_id)
        if not host:
            return []

        try:
            proxy = self._get_supervisor_proxy(host)
            processes = proxy.supervisor.getAllProcessInfo()
            
            # 获取每个进程的日志文件路径
            for process in processes:
                try:
                    # 获取进程配置
                    process_config = proxy.supervisor.getProcessInfo(process['name'])
                    stdout_logfile = process_config.get('stdout_logfile', '')
                    stderr_logfile = process_config.get('stderr_logfile', '')
                    
                    # 添加日志文件路径到进程信息中
                    process['stdout_logfile'] = stdout_logfile
                    process['stderr_logfile'] = stderr_logfile
                except Exception as e:
                    self.logger.error(f"Failed to get log file info for process {process['name']}: {str(e)}")
                    process['stdout_logfile'] = ''
                    process['stderr_logfile'] = ''
                    
            return processes
        except xmlrpc.client.Error as e:
            self.logger.error(f"Failed to get process info from {host['ip']}:{host['port']}: {str(e)}")
            return []

    def control_process(self, host_id: str, process_name: str, action: str) -> bool:
        """控制进程状态
        
        Args:
            host_id: 主机ID
            process_name: 进程名称
            action: 控制动作 ('start', 'stop', 'restart')
            
        Returns:
            bool: 操作是否成功
        """
        host = self.config_manager.get_host(host_id)
        if not host:
            return False

        try:
            proxy = self._get_supervisor_proxy(host)
            
            if action == 'start':
                proxy.supervisor.startProcess(process_name)
            elif action == 'stop':
                proxy.supervisor.stopProcess(process_name)
            elif action == 'restart':
                proxy.supervisor.stopProcess(process_name)
                proxy.supervisor.startProcess(process_name)
            else:
                raise ValueError(f"Unknown action: {action}")
                
            return True
        except Exception as e:
            self.logger.error(f"Failed to {action} process {process_name} on {host['ip']}:{host['port']}: {str(e)}")
            return False

    def get_process_log(self, host_id: str, process_name: str, log_type: str = 'stdout') -> str:
        """获取进程日志
        
        Args:
            host_id: 主机ID
            process_name: 进程名称
            log_type: 日志类型 (stdout/stderr)
            
        Returns:
            str: 日志内容
            
        Raises:
            Exception: 获取日志失败时抛出
        """
        try:
            proxy = self._get_supervisor_proxy(self.get_host(host_id))
            if not proxy:
                raise Exception("Failed to connect to supervisor")

            # 获取日志内容
            if log_type == 'stdout':
                offset = 0
                length = 16384  # 读取最后16KB的日志
                log_data = proxy.supervisor.readProcessStdoutLog(process_name, offset, length)
            else:
                offset = 0
                length = 16384
                log_data = proxy.supervisor.readProcessStderrLog(process_name, offset, length)

            return log_data if isinstance(log_data, str) else log_data.decode('utf-8')

        except Exception as e:
            self.logger.error(f"Failed to get {log_type} log for process {process_name}: {str(e)}")
            raise Exception(f"Failed to get process log: {str(e)}")

    def add_host(self, host_id: str, host_data: Dict[str, Any]) -> bool:
        """添加新主机
        
        Args:
            host_id: 主机ID
            host_data: 主机配信息
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 验证必要字段
            required_fields = ['ip', 'port', 'username', 'password']
            if not all(field in host_data for field in required_fields):
                missing = [field for field in required_fields if field not in host_data]
                raise ValueError(f"Missing required fields: {', '.join(missing)}")
                
            # 验证端口
            try:
                port = int(host_data['port'])
                if not (1 <= port <= 65535):
                    raise ValueError(f"Invalid port number: {port}")
                host_data['port'] = port
            except (ValueError, TypeError):
                raise ValueError(f"Invalid port value: {host_data['port']}")
                
            # 获取当前配置
            hosts = self.config_manager.get_all_hosts()
            
            # 检查是否已存在
            if host_id in hosts:
                raise ValueError(f"Host {host_id} already exists")
                
            # 添加新主机
            hosts[host_id] = host_data
            
            # 保存配置
            if not self.config_manager.save_hosts(hosts):
                raise Exception("Failed to save configuration")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add host {host_id}: {str(e)}")
            return False
            
    def delete_host(self, host_id: str) -> bool:
        """删除主机
        
        Args:
            host_id: 主机ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 获取当前配置
            hosts = self.config_manager.get_all_hosts()
            
            # 检查主机是否存在
            if host_id not in hosts:
                raise ValueError(f"Host {host_id} not found")
                
            # 删除主机
            del hosts[host_id]
            
            # 保存配置
            if not self.config_manager.save_hosts(hosts):
                raise Exception("Failed to save configuration")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete host {host_id}: {str(e)}")
            return False

    def check_host_status(self, host: Dict[str, Any]) -> bool:
        """检查主机状态"""
        try:
            # 构建标准化的连接信息
            connection_info = {
                'ip': str(host.get('ip', '')),
                'port': int(host.get('port', 0)),
                'username': str(host.get('username', '')),
                'password': str(host.get('password', ''))
            }

            # 验证必要字段
            if not all(connection_info.values()):
                self.logger.error(f"Missing required connection information for host {connection_info['ip']}")
                return False

            try:
                proxy = self._get_supervisor_proxy(connection_info)
                state = proxy.supervisor.getState()
                self.logger.debug(f"Successfully connected to {connection_info['ip']}:{connection_info['port']}")
                return True
            except Exception as e:
                self.logger.debug(f"Connection test failed: {str(e)}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to check host status: {str(e)}")
            return False

    def get_hosts(self) -> List[Dict[str, Any]]:
        """获取所有主机信息，包括状态"""
        try:
            hosts_config = self.config_manager.get_all_hosts()
            if not hosts_config:
                self.logger.warning("No hosts configured")
                return []
            
            hosts = []
            for host_id, host in hosts_config.items():
                try:
                    # 检查主机状态
                    status = 'connected' if self.check_host_status(host) else 'disconnected'
                    
                    # 构建主机信息
                    host_info = {
                        'id': host_id,
                        'name': host.get('name', ''),
                        'ip': host.get('ip', ''),
                        'port': host.get('port', ''),
                        'username': host.get('username', ''),
                        'status': status,
                        'description': host.get('description', ''),
                        'tags': host.get('tags', [])
                    }
                    hosts.append(host_info)
                    
                except Exception as e:
                    self.logger.error(f"Error processing host {host_id}: {str(e)}")
                    continue
            
            return hosts
            
        except Exception as e:
            self.logger.error(f"Failed to get hosts: {str(e)}")
            return []

    def get_processes(self, host_id: str) -> List[Dict[str, Any]]:
        """获取指定主机的进程列表"""
        try:
            self.logger.debug(f"Getting processes for host {host_id}")
            host = self.get_host(host_id)
            if not host:
                self.logger.error(f"Host not found: {host_id}")
                return []

            proxy = self._get_supervisor_proxy(host)
            if not proxy:
                self.logger.error(f"Failed to get supervisor proxy for host {host_id}")
                return []

            processes = proxy.supervisor.getAllProcessInfo()
            self.logger.debug(f"Raw process info from supervisor: {processes}")
            
            # 确保返回的是列表类型
            if not isinstance(processes, list):
                self.logger.error(f"Unexpected process info type: {type(processes)}")
                processes = list(processes) if processes else []
            
            # 处理进程信息
            formatted_processes = []
            for proc in processes:
                if not isinstance(proc, dict):
                    self.logger.warning(f"Skipping invalid process data: {proc}")
                    continue
                    
                formatted_processes.append({
                    'name': proc.get('name', 'Unknown'),
                    'statename': proc.get('statename', 'Unknown'),
                    'state': proc.get('state', 0),
                    'pid': proc.get('pid', 0),
                    'description': proc.get('description', '')
                })
            
            return formatted_processes

        except Exception as e:
            self.logger.error(f"Error getting processes for host {host_id}: {str(e)}")
            return []

    def control_process(self, host_id: str, process_name: str, action: str) -> bool:
        """控制进程
        
        Args:
            host_id: 主机ID
            process_name: 进程名称
            action: 操作类型 (start/stop/restart)
            
        Returns:
            bool: 操作是否成功
        """
        try:
            host = self.config_manager.get_host(host_id)
            if not host:
                raise ValueError(f"Host {host_id} not found")
                
            server = self._get_supervisor(host_id)
            if not server:
                raise Exception(f"Failed to connect to host {host_id}")
                
            if action == 'start':
                server.supervisor.startProcess(process_name)
            elif action == 'stop':
                server.supervisor.stopProcess(process_name)
            elif action == 'restart':
                try:
                    server.supervisor.stopProcess(process_name)
                except:
                    pass
                server.supervisor.startProcess(process_name)
            else:
                raise ValueError(f"Invalid action: {action}")
                
            return True
        except Exception as e:
            error_msg = f"Failed to {action} process {process_name}: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
