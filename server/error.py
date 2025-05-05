from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES

class APIError(Exception):
    """Base exception for API errors"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['success'] = False
        rv['error'] = self.message
        rv['status'] = HTTP_STATUS_CODES.get(self.status_code, 'unknown error')
        return rv

def init_error_handlers(app):
    """Initialize error handlers for the Flask app"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle bad request errors"""
        return jsonify({
            'success': False,
            'error': str(error),
            'status': 'Bad Request'
        }), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        """Handle unauthorized errors"""
        return jsonify({
            'success': False,
            'error': 'Unauthorized access',
            'status': 'Unauthorized'
        }), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle forbidden errors"""
        return jsonify({
            'success': False,
            'error': 'Forbidden access',
            'status': 'Forbidden'
        }), 403

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle not found errors"""
        return jsonify({
            'success': False,
            'error': 'Resource not found',
            'status': 'Not Found'
        }), 404

    @app.errorhandler(405)
    def method_not_allowed_error(error):
        """Handle method not allowed errors"""
        return jsonify({
            'success': False,
            'error': 'Method not allowed',
            'status': 'Method Not Allowed'
        }), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle internal server errors"""
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'status': 'Internal Server Error'
        }), 500

def success_response(data=None, message=None, status_code=200):
    """Create a success response"""
    response = {
        'success': True,
        'status': HTTP_STATUS_CODES.get(status_code, 'unknown status')
    }
    
    if data is not None:
        response['data'] = data
    if message is not None:
        response['message'] = message
        
    return jsonify(response), status_code

def error_response(message, status_code=400, payload=None):
    """Create an error response"""
    raise APIError(message, status_code, payload)