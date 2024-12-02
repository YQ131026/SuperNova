from flask import Flask
from flask_bootstrap import Bootstrap5

def create_app():
    app = Flask(__name__)
    Bootstrap5(app)
    
    # 配置
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-size
    
    # 导入路由模块
    from . import api
    from . import main
    app.register_blueprint(api.bp)
    app.register_blueprint(main.bp)
    
    return app