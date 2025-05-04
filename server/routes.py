import os
from flask import Blueprint, request, jsonify, send_file
from models import db, WorkingTree, StagingArea, File
from datetime import datetime

api = Blueprint('api', __name__)

REPO_BASE = os.path.join(os.getcwd(), 'repos')

def get_repo_path(repo_id):
    return os.path.join(REPO_BASE, str(repo_id), 'files')

@api.route('/api/repos/<int:repo_id>/files', methods=['GET'])
def list_files(repo_id):
    files = File.query.filter_by(repo_id=repo_id).all()
    return jsonify([{'id': f.id, 'filename': f.filename} for f in files])

@api.route('/api/file/<int:file_id>', methods=['GET'])
def get_file(file_id):
    file = File.query.get(file_id)
    if not file:
        return jsonify({'error': 'File not found'}), 404
    repo_path = get_repo_path(file.repo_id)
    file_path = os.path.join(repo_path, file.filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File content not found'}), 404
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return jsonify({'id': file.id, 'filename': file.filename, 'content': content})

@api.route('/api/file/<int:file_id>', methods=['PUT'])
def save_file(file_id):
    file = File.query.get(file_id)
    if not file:
        return jsonify({'error': 'File not found'}), 404
    data = request.json
    content = data.get('content', '')
    repo_path = get_repo_path(file.repo_id)
    os.makedirs(repo_path, exist_ok=True)
    file_path = os.path.join(repo_path, file.filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    # Add to working tree as modified
    wt = WorkingTree(user_id=data.get('user_id'), repo_id=file.repo_id, file_path=file.filename, status='modified', last_modified=datetime.now())
    db.session.add(wt)
    db.session.commit()
    return jsonify({'success': True})

@api.route('/api/working-tree', methods=['POST'])
def add_working_tree():
    data = request.json
    wt = WorkingTree(user_id=data['user_id'], repo_id=data['repo_id'], file_path=data['file_path'], status=data.get('status', 'modified'), last_modified=datetime.now())
    db.session.add(wt)
    db.session.commit()
    return jsonify({'success': True})

@api.route('/api/stage', methods=['POST'])
def stage_file():
    data = request.json
    # Remove from working tree
    WorkingTree.query.filter_by(user_id=data['user_id'], repo_id=data['repo_id'], file_path=data['file_path']).delete()
    # Add to staging area
    sa = StagingArea(user_id=data['user_id'], repo_id=data['repo_id'], file_path=data['file_path'], staged_at=datetime.now())
    db.session.add(sa)
    db.session.commit()
    return jsonify({'success': True})

@api.route('/api/commit', methods=['POST'])
def commit_files():
    data = request.json
    # Here you would create a commit, move staged files to committed, and clear staging
    StagingArea.query.filter_by(user_id=data['user_id'], repo_id=data['repo_id']).delete()
    db.session.commit()
    return jsonify({'success': True})

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
    from flask_bcrypt import generate_password_hash
    data = request.get_json()
    hashed_password = generate_password_hash(data['password']).decode('utf-8')
    new_user = User(name=data['name'], email=data['email'], password=hashed_password)
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


