# server/routes.py

from flask import Blueprint, jsonify, request
from models import db, User, Commit
from app import repo
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@main.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    new_user = User(name=data['name'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.to_dict()), 201

@main.route('/commit', methods=['POST'])
def commit_changes():
    message = request.json.get('message', 'No commit message')
    repo.git.add(A=True)  # Stage all changes
    commit = repo.index.commit(message)
    new_commit = Commit(hash=commit.hexsha, message=message, timestamp=datetime.now())
    db.session.add(new_commit)
    db.session.commit()
    return jsonify({'status': 'success', 'commit_hash': commit.hexsha})

@main.route('/merge', methods=['POST'])
def merge_branch():
    source_branch = request.json.get('source_branch')
    target_branch = request.json.get('target_branch')
    repo.git.checkout(target_branch)
    merge_result = repo.git.merge(source_branch)
    return jsonify({'status': 'success', 'merge_result': merge_result})

@main.route('/branch', methods=['POST'])
def create_branch():
    branch_name = request.json.get('branch_name')
    repo.git.branch(branch_name)
    return jsonify({'status': 'success', 'branch_name': branch_name})


