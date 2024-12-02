from typing import Optional
from flask import Flask
from flask_bootstrap import Bootstrap5  # 修改为正确的导入
from .utils.error_handler import setup_error_handlers
from .utils.logger import LogManager
from .utils.backup import ConfigBackup
from .utils.monitor import HostMonitor
from .services.supervisor_service import SupervisorService

def create_app(config_name: Optional[str] = None) -> Flask:
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 使用 Bootstrap5
    bootstrap = Bootstrap5(app)
    
    # 配置
    app.config.update(
        SECRET_KEY='your-secret-key',
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max-size
        JSON_AS_ASCII=False,
        TEMPLATES_AUTO_RELOAD=True,
        BOOTSTRAP_SERVE_LOCAL=True
    )
    
    # 初始化日志管理
    log_manager = LogManager(app)
    
    # 初始化配置备份
    config_backup = ConfigBackup(app)
    
    # 初始化Supervisor服务
    supervisor_service = SupervisorService()
    
    # 初始化主机监控
    host_monitor = HostMonitor(app, supervisor_service)
    host_monitor.start_monitoring()
    
    # 设置错误处理
    setup_error_handlers(app)
    
    # 注册蓝图
    with app.app_context():
        from .routes import api, main
        app.register_blueprint(api.bp)
        app.register_blueprint(main.bp)
    
    # 添加到应用上下文
    app.config_backup = config_backup
    app.host_monitor = host_monitor
    app.supervisor_service = supervisor_service
    
    return app