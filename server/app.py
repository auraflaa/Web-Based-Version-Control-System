from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from server.error import init_error_handlers
from server.models import db
from server.routes import api
from server.cache import cache
from server.monitoring import initialize_monitoring
from server.logger import init_logging

def create_app(config=None):
    app = Flask(__name__)
    
    # Load configuration
    if config:
        app.config.from_object(config)
    else:
        app.config.from_pyfile('configs.py')
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://127.0.0.1:5000", "http://localhost:5000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize extensions
    db.init_app(app)
    initialize_monitoring()
    init_logging("logging_config.yml")
    init_error_handlers(app)
    
    # Register blueprints
    app.register_blueprint(api)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Initialize repos directory if it doesn't exist
        repos_dir = os.path.join(app.root_path, 'repos')
        if not os.path.exists(repos_dir):
            os.makedirs(repos_dir)
    
    @app.route('/')
    def root():
        # Serve dashboard.html as the default page
        return send_from_directory(os.path.join(app.root_path, '../client'), 'dashboard.html')

    @app.route('/<path:filename>')
    def static_files(filename):
        # Serve static files (html, js, css, etc.)
        return send_from_directory(os.path.join(app.root_path, '../client'), filename)

    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
