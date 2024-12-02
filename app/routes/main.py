from flask import Blueprint, render_template, current_app, flash, redirect, url_for, request

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """主页"""
    return render_template('index.html')

@bp.route('/services')
def services():
    """服务管理页面 - 显示所有主机的服务"""
    try:
        # 获取所有主机信息
        hosts = current_app.supervisor_service.get_hosts()
        
        # 如果没有指定host_id，默认使用第一个主机
        host_id = request.args.get('host_id')
        if not host_id and hosts:
            host_id = hosts[0]['id']
            
        return render_template('services.html', hosts=hosts, default_host_id=host_id)
    except Exception as e:
        current_app.logger.error(f"Error loading services page: {str(e)}")
        flash('Error loading services page', 'error')
        return redirect(url_for('main.index'))

@bp.route('/hosts')
def hosts():
    """主机管理页面"""
    return render_template('hosts.html')

@bp.route('/logs')
def logs():
    """日志查看页面"""
    try:
        # 获取所有主机信息
        hosts = current_app.supervisor_service.get_hosts()
        return render_template('logs.html', hosts=hosts)
    except Exception as e:
        current_app.logger.error(f"Error loading logs page: {str(e)}")
        flash('Error loading logs page', 'error')
        return redirect(url_for('main.index'))