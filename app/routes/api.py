from flask import Blueprint, jsonify, request, current_app
from http import HTTPStatus

bp = Blueprint('api', __name__, url_prefix='/api')

def make_api_response(data=None, message=None, error=None, status_code=HTTPStatus.OK):
    """创建统一的 API 响应
    
    Args:
        data: 响应数据
        message: 成功消息
        error: 错误消息
        status_code: HTTP 状态码
    """
    response = {
        'success': error is None,
        'data': data or {},
        'message': message,
        'error': error
    }
    return jsonify(response), status_code

def sanitize_host_info(host: dict) -> dict:
    """清理主机信息，移除敏感数据
    
    Args:
        host: 主机信息字典
        
    Returns:
        dict: 清理后的主机信息
    """
    return {
        'id': host['id'],
        'name': host['name'],
        'ip': host['ip'],
        'port': host['port'],
        'username': host['username'],
        'status': host['status']
    }

@bp.errorhandler(Exception)
def handle_api_error(error):
    """API 错误处理器"""
    return make_api_response(
        error=str(error),
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR
    )

@bp.route('/hosts', methods=['GET'])
def get_hosts():
    """获取所有主机列表"""
    try:
        hosts = current_app.supervisor_service.get_hosts()
        return make_api_response(
            data={'hosts': hosts},
            message='Successfully retrieved hosts'
        )
    except Exception as e:
        error_msg = f"Failed to get hosts: {str(e)}"
        current_app.logger.error(error_msg)
        return make_api_response(
            error=error_msg,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@bp.route('/hosts', methods=['POST'])
def add_host():
    """添加新主机"""
    try:
        data = request.get_json()
        if not data:
            return make_api_response(
                error='Missing request body',
                status_code=HTTPStatus.BAD_REQUEST
            )
            
        required_fields = ['name', 'ip', 'port', 'username', 'password']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return make_api_response(
                error=f'Missing required fields: {", ".join(missing_fields)}',
                status_code=HTTPStatus.BAD_REQUEST
            )
            
        # 生成主机ID
        host_id = f"{data['ip']}_{data['port']}"
        
        # 添加主机到配置
        success = current_app.supervisor_service.add_host(host_id, {
            'name': data['name'],
            'ip': data['ip'],
            'port': int(data['port']),
            'username': data['username'],
            'password': data['password']
        })
        
        if success:
            return make_api_response(
                message='Host added successfully',
                data={'host_id': host_id}
            )
        else:
            return make_api_response(
                error='Failed to add host',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        return make_api_response(
            error=str(e),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@bp.route('/hosts/<host_id>', methods=['DELETE'])
def delete_host(host_id):
    """删除主机"""
    try:
        success = current_app.supervisor_service.delete_host(host_id)
        if success:
            return make_api_response(
                message='Host deleted successfully'
            )
        else:
            return make_api_response(
                error='Failed to delete host',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        return make_api_response(
            error=str(e),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@bp.route('/hosts/<host_id>', methods=['GET'])
def get_host(host_id):
    """获取指定主机信息"""
    try:
        host = current_app.supervisor_service.get_host(host_id)
        if not host:
            return make_api_response(
                error=f'Host {host_id} not found',
                status_code=HTTPStatus.NOT_FOUND
            )
            
        # 清理敏感信息并返回
        host_info = sanitize_host_info(host)
        return make_api_response(
            data={'host': host_info},
            message='Successfully retrieved host information'
        )
    except Exception as e:
        error_msg = f"Failed to get host {host_id}: {str(e)}"
        current_app.logger.error(error_msg)
        return make_api_response(
            error=error_msg,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@bp.route('/processes', methods=['GET'])
def get_processes():
    """获取指定主机的进程列表"""
    host_id = request.args.get('host_id')
    current_app.logger.debug(f"Received request for processes with host_id: {host_id}")
    
    if not host_id:
        return make_api_response(
            error="Missing host_id parameter",
            status_code=HTTPStatus.BAD_REQUEST
        )

    try:
        supervisor_service = current_app.supervisor_service
        host = supervisor_service.get_host(host_id)
        
        if not host:
            current_app.logger.error(f"Host not found: {host_id}")
            return make_api_response(
                error="Host not found",
                status_code=HTTPStatus.NOT_FOUND
            )

        processes = supervisor_service.get_processes(host_id)
        current_app.logger.debug(f"Retrieved processes for host {host_id}: {processes}")
        
        # 确保返回的是列表
        if not isinstance(processes, list):
            current_app.logger.error(f"Invalid processes data type: {type(processes)}")
            processes = list(processes) if processes else []
        
        return make_api_response(
            data={'processes': processes},
            message='Successfully retrieved processes'
        )
        
    except Exception as e:
        error_msg = f"Error getting processes: {str(e)}"
        current_app.logger.error(error_msg)
        return make_api_response(
            error=error_msg,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@bp.route('/processes/<process_name>/<action>', methods=['POST'])
def control_process(process_name, action):
    """控制进程状态"""
    try:
        host_id = request.json.get('host_id')
        if not host_id:
            return make_api_response(
                error='Host ID is required',
                status_code=HTTPStatus.BAD_REQUEST
            )
            
        if action not in ['start', 'stop', 'restart']:
            return make_api_response(
                error=f'Invalid action: {action}',
                status_code=HTTPStatus.BAD_REQUEST
            )
            
        success = current_app.supervisor_service.control_process(host_id, process_name, action)
        if success:
            return make_api_response(
                message=f'Successfully {action}ed process {process_name}'
            )
        else:
            return make_api_response(
                error=f'Failed to {action} process {process_name}',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        error_msg = f"Failed to {action} process {process_name}: {str(e)}"
        current_app.logger.error(error_msg)
        return make_api_response(
            error=error_msg,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@bp.route('/processes/<process_name>/log', methods=['GET'])
def get_process_log(process_name):
    """获取进程日志"""
    try:
        host_id = request.args.get('host_id')
        if not host_id:
            return make_api_response(
                error='Host ID is required',
                status_code=HTTPStatus.BAD_REQUEST
            )
            
        log_type = request.args.get('type', 'stdout')
        if log_type not in ['stdout', 'stderr']:
            return make_api_response(
                error=f'Invalid log type: {log_type}',
                status_code=HTTPStatus.BAD_REQUEST
            )
            
        log = current_app.supervisor_service.get_process_log(host_id, process_name, log_type)
        return make_api_response(
            data={'log': log},
            message=f'Successfully retrieved {log_type} log for process {process_name}'
        )
    except Exception as e:
        error_msg = f"Failed to get log for process {process_name}: {str(e)}"
        current_app.logger.error(error_msg)
        return make_api_response(
            error=error_msg,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@bp.route('/logs/<process_name>', methods=['GET'])
def get_logs(process_name):
    """获取进程日志"""
    host_id = request.args.get('host_id')
    log_type = request.args.get('type', 'stdout')  # 默认获取标准输出
    
    if not host_id:
        return make_api_response(
            error="Missing host_id parameter",
            status_code=HTTPStatus.BAD_REQUEST
        )
        
    try:
        supervisor_service = current_app.supervisor_service
        host = supervisor_service.get_host(host_id)
        
        if not host:
            return make_api_response(
                error="Host not found",
                status_code=HTTPStatus.NOT_FOUND
            )
            
        # 获取日志内容
        log_content = supervisor_service.get_process_log(host_id, process_name, log_type)
        
        return make_api_response(
            data={
                'content': log_content,
                'process': process_name,
                'type': log_type
            },
            message='Successfully retrieved logs'
        )
        
    except Exception as e:
        error_msg = f"Failed to get logs: {str(e)}"
        current_app.logger.error(error_msg)
        return make_api_response(
            error=error_msg,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )