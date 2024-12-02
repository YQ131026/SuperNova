from flask import Blueprint, render_template, request, redirect, url_for, current_app, make_response
from http import HTTPStatus

bp = Blueprint('views', __name__)

def add_security_headers(response):
    """添加安全响应头"""
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https:; img-src 'self' data:;"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

@bp.route('/')
def index():
    """主页 - 主机列表"""
    response = make_response(render_template('hosts.html'))
    return add_security_headers(response)

@bp.route('/services')
def services():
    """服务管理页面"""
    host_id = request.args.get('host_id')
    if not host_id:
        return redirect(url_for('views.index'))
        
    try:
        host = current_app.supervisor_service.get_host(host_id)
        if not host:
            return redirect(url_for('views.index'))
            
        response = make_response(render_template('services.html'))
        return add_security_headers(response)
    except Exception as e:
        current_app.logger.error(f"Error loading services page: {str(e)}")
        return redirect(url_for('views.index'))