import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from models import db
from routes import api
from vcs import repo_manager

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Ensure the database directory exists
    db_dir = os.path.join(os.path.dirname(__file__), '..', 'database')
    os.makedirs(db_dir, exist_ok=True)
    
    # Configuration
    # MySQL connection string: mysql+pymysql://username:password@host:port/dbname
    mysql_user = 'root'
    mysql_password = 'Pritam'
    mysql_host = '127.0.0.1'
    mysql_port = 3306
    mysql_db = 'codehub'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['REPO_BASE'] = os.path.join(os.path.dirname(__file__), 'repos')
    
    # Ensure repository directory exists
    os.makedirs(app.config['REPO_BASE'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize repository manager
    # repo_manager.init_app(app)  # Removed, not needed
    
    # Register blueprints
    app.register_blueprint(api)
    
    # Serve static files in development
    @app.route('/')
    def serve_index():
        return send_from_directory('../client', 'index.html')
        
    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory('../client', path)
        
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Resource not found'}, 404
        
    @app.errorhandler(500)
    def server_error(e):
        return {'error': 'Internal server error'}, 500
        
    return app

def init_database(app):
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    app = create_app()
    init_database(app)
    app.run(debug=True)
