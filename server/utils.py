from flask import request, jsonify, current_app
from functools import wraps
import logging
from logger import get_logger, metrics

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API errors."""
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code

    def to_dict(self):
        rv = dict()
        rv['message'] = self.args[0]
        rv['status'] = 'error'
        return rv

class Pagination:
    """Helper class for pagination."""
    def __init__(self, query, page, per_page):
        self.query = query
        self.page = page
        self.per_page = per_page
        self.total = query.count()
        self.items = query.limit(per_page).offset((page - 1) * per_page).all()

    @property
    def pages(self):
        """Calculate total number of pages."""
        return max(1, (self.total + self.per_page - 1) // self.per_page)
        
    @property
    def has_prev(self):
        """Check if there is a previous page."""
        return self.page > 1
        
    @property
    def has_next(self):
        """Check if there is a next page."""
        return self.page < self.pages
        
    def get_next_page(self):
        """Get next page number."""
        return self.page + 1 if self.has_next else None
        
    def get_prev_page(self):
        """Get previous page number."""
        return self.page - 1 if self.has_prev else None
        
    def to_dict(self):
        """Convert pagination object to dictionary."""
        return {
            'items': [item.to_dict() if hasattr(item, 'to_dict') else dict(item) for item in self.items],
            'page': self.page,
            'per_page': self.per_page,
            'total': self.total,
            'pages': self.pages,
            'has_next': self.has_next,
            'has_prev': self.has_prev,
            'next_page': self.get_next_page(),
            'prev_page': self.get_prev_page()
        }

def handle_api_error(error):
    """Global error handler for API errors."""
    response = jsonify({
        'success': False,
        'error': str(error)
    })
    if hasattr(error, 'status_code'):
        response.status_code = error.status_code
    else:
        response.status_code = 500
    return response

def validate_params(*required_params):
    """Decorator to validate required parameters in request."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            if not data:
                raise APIError("No JSON data provided")
            
            missing = [param for param in required_params if param not in data]
            if missing:
                raise APIError(f"Missing required parameters: {', '.join(missing)}")
                
            return f(*args, **kwargs)
        return wrapper
    return decorator

def error_handler(f):
    """Decorator to handle API errors."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            logger.warning(f"API Error: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), e.status_code
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'An unexpected error occurred'
            }), 500
    return wrapper

def get_pagination_params():
    """Get pagination parameters from request."""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(
            int(request.args.get('per_page', current_app.config.get('DEFAULT_PAGE_SIZE', 50))),
            current_app.config.get('MAX_PAGE_SIZE', 100)  # Maximum items per page
        )
        return max(1, page), max(1, per_page)
    except (TypeError, ValueError):
        raise APIError("Invalid pagination parameters")

def validate_file_size(size):
    max_size = current_app.config.get('MAX_FILE_SIZE', 10 * 1024 * 1024)  # Default 10MB
    if size > max_size:
        raise APIError(f"File size exceeds maximum limit of {max_size} bytes")