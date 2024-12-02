from flask import jsonify, render_template, request, make_response
import logging

def setup_error_handlers(app):
    def handle_error(error, status_code=500):
        logging.error(f"Error: {error}")
        if request_wants_json():
            response = jsonify({
                'success': False,
                'error': 'Error',
                'message': str(error)
            })
            response.status_code = status_code
            return response
        return render_template('errors/500.html'), status_code

    @app.errorhandler(400)
    def bad_request_error(error):
        return handle_error(error, 400)

    @app.errorhandler(404)
    def not_found_error(error):
        return handle_error(error, 404)

    @app.errorhandler(500)
    def internal_error(error):
        return handle_error(error, 500)

    @app.errorhandler(Exception)
    def handle_exception(error):
        return handle_error(error, 500)

def request_wants_json():
    """检查请求是否期望JSON响应"""
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > request.accept_mimetypes['text/html']