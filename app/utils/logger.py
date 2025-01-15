import os
import logging
import yaml

class LogManager:
    def __init__(self, app):
        self.app = app
        self.log_path = self._get_log_path()
        self._setup_logging()

    def _get_log_path(self):
        """获取日志路径配置"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'config', 
            'app.yaml'
        )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config['log_path']
        except Exception as e:
            print(f"Warning: Failed to load log path config: {e}")
            return 'logs'  # 默认路径

    def _setup_logging(self):
        """设置日志"""
        # 确保日志目录存在
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            self.log_path
        )
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 设置日志处理器
        log_file = os.path.join(log_dir, 'supernova.log')
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        
        # 添加到应用日志处理器
        self.app.logger.addHandler(handler)
