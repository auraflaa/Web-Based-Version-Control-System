import os
import stat
import errno
import shutil
from flask import Flask, current_app, send_from_directory, redirect
from flask_cors import CORS
from models import db
from routes import api
from vcs import repo_manager
from logger import setup_logging, get_logger, metrics
from utils import APIError, handle_api_error
from decouple import config

# Setup logging
setup_logging()
logger = get_logger('main')

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, static_folder='../client', static_url_path='')
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{config('DB_USER', default='root')}:{config('DB_PASSWORD', default='Pritam')}@{config('DB_HOST', default='localhost')}/{config('DB_NAME', default='codehub')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Set other configuration values
    app.config.setdefault('CORS_ORIGINS', ['http://localhost:5000'])
    app.config.setdefault('DEBUG', True)
    app.config.setdefault('DEVELOPMENT', True)
    app.config.setdefault('TESTING', False)
    app.config.setdefault('REPO_BASE', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'repos'))
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Accept"]
        }
    })
    
    # Initialize extensions
    db.init_app(app)
    
    # Register error handlers
    app.register_error_handler(APIError, handle_api_error)
    
    # Register blueprints
    app.register_blueprint(api)
    
    # Root route handler
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
        
    # Favicon handler
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.static_folder, 'assets'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    # Ensure repository directory exists and is clean
    with app.app_context():
        try:
            db.create_all()
            cleanup_repositories()
        except Exception as e:
            logger.error(f"Error during app initialization: {e}", exc_info=True)
        
    return app

def check_database_health():
    """Check database connection health"""
    try:
        db.session.execute('SELECT 1')
        return {'status': 'connected'}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {'status': 'error', 'message': str(e)}

def check_redis_health():
    """Check Redis connection health"""
    try:
        redis_client.ping()
        return {'status': 'connected'}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {'status': 'error', 'message': str(e)}

def handle_remove_readonly(func, path, exc):
    """Error handler for shutil.rmtree that handles read-only files"""
    excvalue = exc[1]
    if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        func(path)
    else:
        logger.error(f"Failed to remove {path}: {exc}")

def safe_remove_directory(path):
    """Safely remove a directory and all its contents"""
    try:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for d in dirs:
                    try:
                        dirpath = os.path.join(root, d)
                        os.chmod(dirpath, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                    except Exception as e:
                        logger.warning(f"Could not change permissions on directory {dirpath}: {e}")
                for f in files:
                    try:
                        filepath = os.path.join(root, f)
                        os.chmod(filepath, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                    except Exception as e:
                        logger.warning(f"Could not change permissions on file {filepath}: {e}")
            
            try:
                shutil.rmtree(path, onerror=handle_remove_readonly)
            except Exception as e1:
                logger.warning(f"First removal attempt failed: {e1}")
                try:
                    if os.name == 'nt':
                        os.system(f'rmdir /S /Q "{path}"')
                    else:
                        os.system(f'rm -rf "{path}"')
                except Exception as e2:
                    logger.error(f"All removal attempts failed for {path}: {e1}, {e2}")
                    return False
            
            logger.info(f"Successfully removed directory: {path}")
            return True
    except Exception as e:
        logger.error(f"Failed to remove directory {path}: {str(e)}")
        return False

def cleanup_repositories():
    """Clean up orphaned repository directories on startup"""
    from models import Repository, Branch
    
    repo_base = current_app.config['REPO_BASE']
    os.makedirs(repo_base, exist_ok=True)
    logger.info(f"Starting repository cleanup in: {repo_base}")
    
    try:
        db_repos = Repository.query.all()
        db_repo_ids = {str(repo.id) for repo in db_repos}
        logger.info(f"Found repositories in database: {db_repo_ids}")
        
        if os.path.exists(repo_base):
            fs_repo_ids = {d for d in os.listdir(repo_base) 
                          if os.path.isdir(os.path.join(repo_base, d))}
            logger.info(f"Found repository directories: {fs_repo_ids}")
        else:
            fs_repo_ids = set()
            logger.warning("Repository base directory does not exist")
            
        # Clean up orphaned directories
        orphaned = fs_repo_ids - db_repo_ids
        if orphaned:
            logger.info(f"Found orphaned repositories to clean: {orphaned}")
            for repo_id in orphaned:
                repo_path = os.path.join(repo_base, repo_id)
                if os.path.exists(repo_path):
                    safe_remove_directory(repo_path)
        
        # Create missing directories
        missing = db_repo_ids - fs_repo_ids
        if missing:
            logger.info(f"Found missing repositories to create: {missing}")
            for repo_id in missing:
                repo_path = os.path.join(repo_base, str(repo_id))
                if not os.path.exists(repo_path):
                    repo_manager.create_repository(int(repo_id))
                    
        logger.info("Repository cleanup completed")
                    
    except Exception as e:
        logger.error(f"Error during repository cleanup: {str(e)}", exc_info=True)

def validate_repo_structure(repo_path):
    """Validate repository directory structure"""
    required_dirs = ['files', 'objects', 'refs/heads', 'refs/tags']
    return all(os.path.exists(os.path.join(repo_path, d)) for d in required_dirs)

def cleanup_invalid_repository(repo):
    """Clean up an invalid repository"""
    try:
        repo_path = os.path.join(current_app.config['REPO_BASE'], str(repo.id))
        if os.path.exists(repo_path):
            safe_remove_directory(repo_path)
            
        Branch.query.filter_by(repository_id=repo.id).delete()
        db.session.delete(repo)
        db.session.commit()
        logger.info(f"Successfully removed invalid repository {repo.id}")
    except Exception as e:
        logger.error(f"Failed to remove repository {repo.id}: {e}")
        db.session.rollback()

def init_database(app):
    """Initialize database tables"""
    with app.app_context():
        logger.info("Initializing database tables...")
        db.create_all()
        logger.info("Database initialization complete")

if __name__ == '__main__':
    app = create_app()
    init_database(app)
    logger.info("Starting Flask development server...")
    app.run(
        host=app.config.get('HOST', '127.0.0.1'),
        port=app.config.get('PORT', 5000),
        debug=app.config.get('DEBUG', False)
    )
