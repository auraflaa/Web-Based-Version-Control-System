from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    repositories = db.relationship('Repository', backref='owner', lazy=True)
    commits = db.relationship('Commit', backref='author', lazy=True)
    branches = db.relationship('Branch', backref='creator', lazy=True)
    
    @staticmethod
    def register(name, email, password):
        user = User(
            name=name,
            email=email,
            password=password
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def authenticate(email, password):
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            return user
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

class Repository(db.Model):
    __tablename__ = 'repositories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branches = db.relationship('Branch', backref='repository', lazy=True, cascade='all, delete-orphan')
    commits = db.relationship('Commit', backref='repository', lazy=True, cascade='all, delete-orphan')
    files = db.relationship('File', backref='repository', lazy=True, cascade='all, delete-orphan')
    working_tree = db.relationship('WorkingTree', backref='repository', lazy=True, cascade='all, delete-orphan')
    staging_area = db.relationship('StagingArea', backref='repository', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }

class Branch(db.Model):
    __tablename__ = 'branches'
    
    id = db.Column(db.Integer, primary_key=True)
    branch_name = db.Column(db.String(100), nullable=False)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_commit_hash = db.Column(db.String(40))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.branch_name,
            'repository_id': self.repository_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_commit_hash': self.last_commit_hash
        }

class Commit(db.Model):
    __tablename__ = 'commits'
    
    id = db.Column(db.Integer, primary_key=True)
    commit_hash = db.Column(db.String(40), nullable=False, unique=True)
    message = db.Column(db.Text, nullable=False)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    parent_hash = db.Column(db.String(40))
    
    # Relationships
    files = db.relationship('CommitFiles', backref='commit', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'hash': self.commit_hash,
            'message': self.message,
            'repository_id': self.repository_id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
            'parent_hash': self.parent_hash,
            'files': [f.to_dict() for f in self.files]
        }

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    repo_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    commits = db.relationship('CommitFiles', backref='file', lazy=True)
    working_tree = db.relationship('WorkingTree', backref='file', lazy=True)
    staging_area = db.relationship('StagingArea', backref='file', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'repo_id': self.repo_id,
            'created_at': self.created_at.isoformat()
        }

class CommitFiles(db.Model):
    __tablename__ = 'commit_files'
    
    id = db.Column(db.Integer, primary_key=True)
    commit_id = db.Column(db.Integer, db.ForeignKey('commits.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    content = db.Column(db.Text)
    status = db.Column(db.String(20))  # added, modified, deleted
    
    def to_dict(self):
        return {
            'id': self.id,
            'commit_id': self.commit_id,
            'file_id': self.file_id,
            'filename': self.file.filename,
            'content': self.content,
            'status': self.status
        }

class WorkingTree(db.Model):
    __tablename__ = 'working_tree'
    
    id = db.Column(db.Integer, primary_key=True)
    repo_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    content = db.Column(db.Text)
    status = db.Column(db.String(20))  # modified, deleted
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'repo_id': self.repo_id,
            'file_id': self.file_id,
            'filename': self.file.filename,
            'content': self.content,
            'status': self.status,
            'timestamp': self.timestamp.isoformat()
        }

class StagingArea(db.Model):
    __tablename__ = 'staging_area'
    
    id = db.Column(db.Integer, primary_key=True)
    repo_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    content = db.Column(db.Text)
    status = db.Column(db.String(20))  # added, modified, deleted
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'repo_id': self.repo_id,
            'file_id': self.file_id,
            'filename': self.file.filename,
            'content': self.content,
            'status': self.status,
            'timestamp': self.timestamp.isoformat()
        }
