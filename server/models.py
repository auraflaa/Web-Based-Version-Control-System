# server/models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    repositories = db.relationship('Repository', backref='owner', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }

class Repository(db.Model):
    __tablename__ = 'repositories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    branches = db.relationship('Branch', backref='repository', lazy=True)
    working_trees = db.relationship('WorkingTree', backref='repository', lazy=True)
    staging_areas = db.relationship('StagingArea', backref='repository', lazy=True)

class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    branch_name = db.Column(db.String(100), nullable=False)
    head_commit_id = db.Column(db.Integer, db.ForeignKey('commits.id'))
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class Commit(db.Model):
    __tablename__ = 'commits'
    id = db.Column(db.Integer, primary_key=True)
    commit_hash = db.Column(db.String(40), nullable=False)
    message = db.Column(db.Text)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    merge_status = db.Column(db.String(50), default=None)

class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    repo_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)

class CommitFiles(db.Model):
    __tablename__ = 'commit_files'
    commit_id = db.Column(db.Integer, db.ForeignKey('commits.id'), primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), primary_key=True)
    content = db.Column(db.Text, nullable=False)
    
    commit = db.relationship('Commit', backref=db.backref('files', lazy=True))
    file = db.relationship('File', backref=db.backref('commits', lazy=True))

class WorkingTree(db.Model):
    __tablename__ = 'working_tree'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    repo_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    last_modified = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class StagingArea(db.Model):
    __tablename__ = 'staging_area'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    repo_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    staged_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
