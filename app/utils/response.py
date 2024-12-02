from typing import Any, Tuple
from flask import jsonify, Response

def make_api_response(
    data: Any = None,
    error: str = None,
    message: str = None,
    status_code: int = 200,
    **kwargs
) -> Tuple[Response, int]:
    """创建统一的API响应"""
    response_data = {
        'success': error is None,
        'error': error,
        'message': message,
        'data': data
    }
    
    # 添加任何额外的字段
    response_data.update(kwargs)
    
    return jsonify(response_data), status_code 