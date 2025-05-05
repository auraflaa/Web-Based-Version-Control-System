import os
import uuid
import shutil
import time
from flask import Blueprint, request, jsonify, send_file, current_app
from models import db, WorkingTree, StagingArea, File, User, Repository, Branch, Commit, CommitFiles
from datetime import datetime
from vcs import repo_manager, VCSError
from utils import APIError, error_handler, validate_params, get_pagination_params, Pagination
from cache import cache_response, cache_file_content, get_cached_file_content, invalidate_repo_cache
from monitoring import http_requests_total, http_request_duration_seconds
from logger import get_logger
from werkzeug.security import generate_password_hash, check_password_hash

api = Blueprint('api', __name__, url_prefix='/api')
logger = get_logger(__name__)

REPO_BASE = os.path.join(os.getcwd(), 'repos')

def get_repo_path(repo_id):
    return os.path.join(REPO_BASE, str(repo_id), 'files')

@api.before_request
def before_request():
    request.start_time = time.time()

@api.after_request
def after_request(response):
    # Record request duration
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.endpoint
        ).observe(duration)
    
    # Record request metrics
    http_requests_total.labels(
        method=request.method,
        endpoint=request.endpoint,
        status=response.status_code
    ).inc()
    
    return response

@api.route('/register', methods=['POST'])
@error_handler
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not all([name, email, password]):
        raise APIError("Name, email and password are required")
        
    if User.query.filter_by(email=email).first():
        raise APIError("Email already registered", 409)
        
    try:
        user = User.register(name, email, password)
        return jsonify({
            'success': True,
            'user_id': user.id,
            'name': user.name
        }), 201
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        db.session.rollback()
        raise APIError("Registration failed", 500)

@api.route('/login', methods=['POST'])
@error_handler
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        raise APIError("Email and password are required")
        
    try:
        user = User.authenticate(email=email, password=password)
        if user:
            return jsonify({
                'success': True,
                'user_id': user.id,
                'name': user.name
            })
        
        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise APIError("Login failed", 500)

@api.route('/repos', methods=['GET'])
@error_handler
def list_repos():
    user_id = request.args.get('user_id')
    if not user_id:
        raise APIError("User ID is required", 400)
        
    try:
        query = Repository.query.filter_by(user_id=user_id).order_by(Repository.created_at.desc())
        page, per_page = get_pagination_params()
        pagination = Pagination(query, page, per_page)
        
        return jsonify({
            'success': True,
            'data': pagination.to_dict()
        })
    except Exception as e:
        logger.error(f"Failed to list repositories: {e}")
        raise APIError("Failed to list repositories", 500)

@api.route('/repos', methods=['POST'])
@error_handler
@validate_params('name', 'user_id')
def create_repo():
    data = request.get_json()
    name = data['name'].strip()
    user_id = data['user_id']
    
    if not name:
        raise APIError("Repository name cannot be empty", 400)
        
    if Repository.query.filter_by(name=name, user_id=user_id).first():
        raise APIError("Repository with this name already exists", 409)
        
    try:
        repo = Repository(name=name, user_id=user_id)
        db.session.add(repo)
        db.session.commit()
        
        # Initialize repository directory
        repo_manager.create_repository(repo.id)
        
        return jsonify({
            'success': True,
            'id': repo.id,
            'name': repo.name,
            'created_at': repo.created_at.isoformat()
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create repository: {e}")
        raise APIError("Failed to create repository", 500)

@api.route('/repos/<int:repo_id>', methods=['GET'])
@error_handler
@cache_response(expire_time=300)
def get_repo(repo_id):
    repository = Repository.query.get_or_404(repo_id)
    return jsonify(repository.to_dict())

@api.route('/repos/<int:repo_id>/sync', methods=['POST'])
@error_handler
@validate_params('user_id')
def sync_repo(repo_id):
    data = request.get_json()
    user_id = data['user_id']
    
    try:
        repository = Repository.query.get_or_404(repo_id)
        if int(user_id) != repository.user_id:
            raise APIError("Unauthorized", 403)
            
        repo_path = os.path.join(current_app.config['REPO_BASE'], str(repo_id))
        if not os.path.exists(repo_path):
            repo_manager.create_repository(repo_id)
                
        return jsonify({
            'success': True,
            'message': f'Repository {repo_id} synchronized successfully'
        })
    except Exception as e:
        logger.error(f"Repository sync failed: {str(e)}")
        raise APIError(f"Failed to sync repository: {str(e)}", 500)

@api.route('/repos/<int:repo_id>/branches', methods=['GET'])
@error_handler
@cache_response(expire_time=300)
def list_branches(repo_id):
    page, per_page = get_pagination_params()
    query = Branch.query.filter_by(repository_id=repo_id)
    pagination = Pagination(query, page, per_page)
    return jsonify(pagination.to_dict())

@api.route('/repos/<int:repo_id>/commits', methods=['GET'])
@error_handler
@cache_response(expire_time=300)
def list_commits(repo_id):
    page, per_page = get_pagination_params()
    branch = request.args.get('branch', 'main')
    
    query = Commit.query.filter_by(
        repository_id=repo_id,
        branch=branch
    ).order_by(Commit.timestamp.desc())
    
    pagination = Pagination(query, page, per_page)
    return jsonify(pagination.to_dict())

@api.route('/repos/<int:repo_id>/files', methods=['GET'])
@error_handler
@cache_response(expire_time=300)
def list_files(repo_id):
    path = request.args.get('path', '')
    repository = Repository.query.get_or_404(repo_id)
    
    try:
        files = repo_manager.list_files(repository.id, path)
        return jsonify(files)
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise APIError("Failed to list files", 500)

@api.route('/repos/<int:repo_id>/files', methods=['POST'])
@error_handler
@validate_params('path', 'content', 'message')
def create_file(repo_id):
    data = request.json
    repository = Repository.query.get_or_404(repo_id)
    
    try:
        file_size = len(data['content'].encode('utf-8'))
        if file_size > current_app.config['MAX_FILE_SIZE']:
            raise APIError("File size exceeds maximum limit")
            
        result = repo_manager.create_file(
            repository.id,
            data['path'],
            data['content'],
            data['message']
        )
        
        # Invalidate cache for this repository
        invalidate_repo_cache(repo_id)
        
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"Failed to create file: {e}")
        raise APIError("Failed to create file", 500)

@api.route('/repos/<int:repo_id>/files/<path:file_path>', methods=['GET'])
@error_handler
def get_file_content(repo_id, file_path):
    repository = Repository.query.get_or_404(repo_id)
    
    # Try to get from cache first
    cached_content = get_cached_file_content(repo_id, file_path)
    if cached_content:
        return jsonify({'content': cached_content})
    
    try:
        content = repo_manager.get_file_content(repository.id, file_path)
        
        # Cache the content
        cache_file_content(repo_id, file_path, content)
        
        return jsonify({'content': content})
    except Exception as e:
        logger.error(f"Failed to get file content: {e}")
        raise APIError("Failed to get file content", 500)

@api.route('/repos/<int:repo_id>/files/<path:file_path>', methods=['PUT'])
@error_handler
@validate_params('content', 'message')
def update_file(repo_id, file_path):
    data = request.json
    repository = Repository.query.get_or_404(repo_id)
    
    try:
        file_size = len(data['content'].encode('utf-8'))
        if file_size > current_app.config['MAX_FILE_SIZE']:
            raise APIError("File size exceeds maximum limit")
            
        result = repo_manager.update_file(
            repository.id,
            file_path,
            data['content'],
            data['message']
        )
        
        # Invalidate cache for this repository
        invalidate_repo_cache(repo_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Failed to update file: {e}")
        raise APIError("Failed to update file", 500)

@api.route('/repos/<int:repo_id>/files/<path:file_path>', methods=['DELETE'])
@error_handler
@validate_params('message')
def delete_file(repo_id, file_path):
    data = request.json
    repository = Repository.query.get_or_404(repo_id)
    
    try:
        result = repo_manager.delete_file(
            repository.id,
            file_path,
            data['message']
        )
        
        # Invalidate cache for this repository
        invalidate_repo_cache(repo_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        raise APIError("Failed to delete file", 500)

@api.route('/repos/<int:repo_id>/download', methods=['GET'])
@error_handler
def download_repository(repo_id):
    repository = Repository.query.get_or_404(repo_id)
    
    try:
        zip_path = repo_manager.create_archive(repository.id)
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f"{repository.name}.zip"
        )
    except Exception as e:
        logger.error(f"Failed to download repository: {e}")
        raise APIError("Failed to download repository", 500)
    finally:
        # Clean up temporary zip file
        if 'zip_path' in locals() and os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary zip file: {e}")

@api.errorhandler(404)
def not_found_error(error):
    return jsonify({'message': 'Resource not found', 'status': 'error'}), 404

@api.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'message': 'Internal server error', 'status': 'error'}), 500


