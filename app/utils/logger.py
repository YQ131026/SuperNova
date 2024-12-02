import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime

class LogManager:
    def __init__(self, app):
        self.app = app
        self.log_dir = os.path.join(app.root_path, '..', 'logs')
        self.ensure_log_directory()
        self.setup_app_logger()
        self.setup_access_logger()
        self.setup_error_logger()

    def ensure_log_directory(self):
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def setup_app_logger(self):
        """设置应用日志"""
        app_log = os.path.join(self.log_dir, 'app.log')
        handler = RotatingFileHandler(
            app_log,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        handler.setFormatter(self.get_formatter())
        self.app.logger.addHandler(handler)
        self.app.logger.setLevel(logging.INFO)

    def setup_access_logger(self):
        """设置访问日志"""
        access_log = os.path.join(self.log_dir, 'access.log')
        handler = TimedRotatingFileHandler(
            access_log,
            when='midnight',
            interval=1,
            backupCount=30
        )
        handler.setFormatter(self.get_formatter())
        logger = logging.getLogger('werkzeug')
        logger.addHandler(handler)

    def setup_error_logger(self):
        """设置错误日志"""
        error_log = os.path.join(self.log_dir, 'error.log')
        handler = RotatingFileHandler(
            error_log,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        handler.setFormatter(self.get_formatter())
        handler.setLevel(logging.ERROR)
        self.app.logger.addHandler(handler)

    def get_formatter(self):
        """获取日志格式化器"""
        return logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )

def log_supervisor_action(app, host_id, action, service_name, success, error=None):
    """记录Supervisor操作日志"""
    with app.app_context():
        message = f"Host {host_id} - {action} {service_name} - {'Success' if success else 'Failed'}"
        if error:
            message += f" - Error: {error}"
        if success:
            app.logger.info(message)
        else:
            app.logger.error(message)
