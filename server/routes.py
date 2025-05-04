import os
from flask import Blueprint, request, jsonify, send_file, current_app
from models import db, WorkingTree, StagingArea, File, User, Repository, Branch, Commit
from datetime import datetime
from vcs import repo_manager, VCSError

api = Blueprint('api', __name__)

REPO_BASE = os.path.join(os.getcwd(), 'repos')

def get_repo_path(repo_id):
    return os.path.join(REPO_BASE, str(repo_id), 'files')

@api.route('/api/repos/<int:repo_id>/files', methods=['GET'])
def list_files(repo_id):
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
        
    path = request.args.get('path', '')
    
    repository = Repository.query.filter_by(id=repo_id, user_id=user_id).first()
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
        
    try:
        repo_path = os.path.join(current_app.config['REPO_BASE'], str(repo_id), 'files')
        if path:
            repo_path = os.path.join(repo_path, path)
            
        if not os.path.exists(repo_path):
            return jsonify([])
            
        files = []
        for item in os.listdir(repo_path):
            item_path = os.path.join(repo_path, item)
            files.append({
                'name': item,
                'type': 'dir' if os.path.isdir(item_path) else 'file',
                'path': os.path.join(path, item) if path else item
            })
            
        return jsonify(files)
        
    except Exception as e:
        return jsonify({'error': 'Failed to list files'}), 500

@api.route('/api/repos/<int:repo_id>/files', methods=['POST'])
def create_file():
    data = request.get_json()
    user_id = data.get('user_id')
    filename = data.get('filename')
    content = data.get('content', '')

    if not user_id or not filename:
        return jsonify({'error': 'user_id and filename are required'}), 400

    try:
        # Create file in filesystem
        repo_path = os.path.join(current_app.config['REPO_BASE'], str(repo_id), 'files')
        os.makedirs(repo_path, exist_ok=True)
        file_path = os.path.join(repo_path, filename)

        # Create file entry in database
        file = File(filename=filename, repo_id=repo_id)
        db.session.add(file)
        db.session.flush()

        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Add to working tree
        wt = WorkingTree(
            user_id=user_id,
            repo_id=repo_id,
            file_path=filename,
            status='new',
            last_modified=datetime.now()
        )
        db.session.add(wt)
        db.session.commit()

        return jsonify({
            'id': file.id,
            'filename': file.filename,
            'created_at': file.created_at.isoformat()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/api/repos/<int:repo_id>/files/<path:filename>', methods=['DELETE'])
def delete_file(repo_id, filename):
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    try:
        # Delete from filesystem
        repo_path = os.path.join(current_app.config['REPO_BASE'], str(repo_id), 'files')
        file_path = os.path.join(repo_path, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Add to working tree as deleted
        wt = WorkingTree(
            user_id=user_id,
            repo_id=repo_id,
            file_path=filename,
            status='deleted',
            last_modified=datetime.now()
        )
        db.session.add(wt)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/api/file/<int:file_id>', methods=['GET'])
def get_file_by_id(file_id):
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
    user_id = data.get('user_id')
    repo_id = data.get('repo_id')
    message = data.get('message', 'No commit message')

    if not user_id or not repo_id:
        return jsonify({'error': 'user_id and repo_id are required'}), 400

    try:
        # Get current branch for repo
        branch = Branch.query.filter_by(
            repository_id=repo_id,
            user_id=user_id
        ).first()

        if not branch:
            return jsonify({'error': 'No branch found for repository'}), 404

        # Get files from staging area
        staged_files = StagingArea.query.filter_by(
            user_id=user_id,
            repo_id=repo_id
        ).all()

        if not staged_files:
            return jsonify({'error': 'No files staged for commit'}), 400

        # Create commit record
        commit_hash = str(uuid.uuid4())[:8]
        commit = Commit(
            commit_hash=commit_hash,
            message=message,
            branch_id=branch.id,
            user_id=user_id,
            timestamp=datetime.now()
        )
        db.session.add(commit)
        db.session.flush()

        # Update branch head
        branch.head_commit_id = commit.id

        # Store committed files
        repo_path = os.path.join(current_app.config['REPO_BASE'], str(repo_id), 'files')
        for staged in staged_files:
            file_path = os.path.join(repo_path, staged.file_path)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Get or create file record
                file = File.query.filter_by(
                    filename=staged.file_path,
                    repo_id=repo_id
                ).first()
                
                if not file:
                    file = File(
                        filename=staged.file_path,
                        repo_id=repo_id
                    )
                    db.session.add(file)
                    db.session.flush()

                # Create commit_files record
                commit_file = CommitFiles(
                    commit_id=commit.id,
                    file_id=file.id,
                    content=content
                )
                db.session.add(commit_file)

        # Clear staging area
        StagingArea.query.filter_by(user_id=user_id, repo_id=repo_id).delete()
        
        db.session.commit()
        
        return jsonify({
            'commit_hash': commit_hash,
            'message': message,
            'timestamp': commit.timestamp.isoformat()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/api/login', methods=['POST'])
def api_login():
    print('LOGIN ENDPOINT HIT')  # Debug print
    data = request.json
    print('LOGIN REQUEST DATA:', data)  # Debug print
    email = data.get('username')
    password = data.get('password')
    try:
        print(f"Received login attempt for email: {email}")
        if not email or not password:
            print("Missing username or password in request data")
            return jsonify({'success': False, 'error': 'Username and password are required.'}), 400
        user = User.query.filter_by(email=email, password=password).first()
        print('USER FOUND:', user)  # Debug print
        if user:
            print(f"User {user.email} authenticated successfully")
            return jsonify({'success': True, 'user_id': user.id, 'name': user.name})
        else:
            print("Authentication failed: Incorrect email or password")
            return jsonify({'success': False, 'error': 'Incorrect email or password.'}), 401
    except Exception as e:
        import traceback
        print('LOGIN ERROR:', traceback.format_exc())
        return jsonify({'success': False, 'error': f'Server error: {str(e)}', 'traceback': traceback.format_exc()}), 500

@api.route('/api/dbtest', methods=['GET'])
def db_test():
    try:
        users = User.query.all()
        print('DB TEST USERS:', users)
        return jsonify({'success': True, 'user_count': len(users)})
    except Exception as e:
        import traceback
        print('DB TEST ERROR:', traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)})

@api.route('/api/repos', methods=['GET'])
def list_repositories():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
        
    repositories = Repository.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': repo.id,
        'name': repo.name,
        'created_at': repo.created_at.isoformat()
    } for repo in repositories])

@api.route('/api/repos', methods=['POST'])
def create_repository():
    data = request.get_json()
    if not data or 'name' not in data or 'user_id' not in data:
        return jsonify({'error': 'name and user_id are required'}), 400
        
    name = data['name'].strip()
    user_id = data['user_id']
    
    # Validate repository name
    if not name or len(name) > 255:
        return jsonify({'error': 'Invalid repository name'}), 400
        
    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    # Check if repository name already exists for this user
    existing_repo = Repository.query.filter_by(name=name, user_id=user_id).first()
    if existing_repo:
        return jsonify({'error': 'Repository with this name already exists'}), 409
        
    try:
        # Create database entry
        repository = Repository(name=name, user_id=user_id)
        db.session.add(repository)
        db.session.flush()  # Get the ID without committing
        
        # Create physical repository
        repo_manager.create_repository(repository.id)
        
        # Create default branch
        branch = Branch(
            branch_name='main',
            repository_id=repository.id,
            user_id=user_id
        )
        db.session.add(branch)
        
        # Commit the transaction
        db.session.commit()
        
        return jsonify({
            'id': repository.id,
            'name': repository.name,
            'created_at': repository.created_at.isoformat()
        }), 201
        
    except VCSError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create repository'}), 500

@api.route('/api/repos/<int:repo_id>', methods=['GET'])
def get_repository(repo_id):
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
        
    repository = Repository.query.filter_by(id=repo_id, user_id=user_id).first()
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
        
    return jsonify({
        'id': repository.id,
        'name': repository.name,
        'created_at': repository.created_at.isoformat()
    })

@api.route('/api/repos/<int:repo_id>/branches', methods=['GET'])
def list_branches(repo_id):
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
        
    repository = Repository.query.filter_by(id=repo_id, user_id=user_id).first()
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
        
    branches = Branch.query.filter_by(repository_id=repo_id).all()
    return jsonify([{
        'id': branch.id,
        'name': branch.branch_name,
        'head_commit_id': branch.head_commit_id
    } for branch in branches])

@api.route('/api/repos/<int:repo_id>/branches', methods=['POST'])
def create_branch(repo_id):
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
        
    if 'name' not in data:
        return jsonify({'error': 'Branch name is required'}), 400
        
    repository = Repository.query.filter_by(id=repo_id, user_id=user_id).first()
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
        
    branch_name = data['name'].strip()
    if not branch_name or len(branch_name) > 100:
        return jsonify({'error': 'Invalid branch name'}), 400
        
    # Check if branch already exists
    existing_branch = Branch.query.filter_by(
        repository_id=repo_id,
        branch_name=branch_name
    ).first()
    if existing_branch:
        return jsonify({'error': 'Branch already exists'}), 409
        
    try:
        branch = Branch(
            branch_name=branch_name,
            repository_id=repo_id,
            user_id=user_id,
            head_commit_id=data.get('start_point')  # Optional
        )
        db.session.add(branch)
        db.session.commit()
        
        return jsonify({
            'id': branch.id,
            'name': branch.branch_name,
            'head_commit_id': branch.head_commit_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create branch'}), 500

@api.route('/api/repos/<int:repo_id>/commits', methods=['GET'])
def list_commits(repo_id):
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
        
    repository = Repository.query.filter_by(id=repo_id, user_id=user_id).first()
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
        
    commits = Commit.query.join(Branch).filter(
        Branch.repository_id == repo_id
    ).order_by(Commit.timestamp.desc()).all()
    
    return jsonify([{
        'id': commit.id,
        'hash': commit.commit_hash,
        'message': commit.message,
        'timestamp': commit.timestamp.isoformat(),
        'branch_id': commit.branch_id,
        'merge_status': commit.merge_status
    } for commit in commits])

@api.route('/api/repos/<int:repo_id>/files/<path:filename>', methods=['GET'])
def get_file_content(repo_id, filename):
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    try:
        repo_path = os.path.join(current_app.config['REPO_BASE'], str(repo_id), 'files')
        file_path = os.path.join(repo_path, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return jsonify({
            'filename': filename,
            'content': content
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/api/repos/<int:repo_id>/files/<path:filename>', methods=['PUT'])
def update_file_content(repo_id, filename):
    data = request.get_json()
    user_id = data.get('user_id')
    content = data.get('content')

    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    try:
        repo_path = os.path.join(current_app.config['REPO_BASE'], str(repo_id), 'files')
        file_path = os.path.join(repo_path, filename)

        if not os.path.exists(repo_path):
            os.makedirs(repo_path, exist_ok=True)

        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Add to working tree as modified
        existing_wt = WorkingTree.query.filter_by(
            user_id=user_id,
            repo_id=repo_id,
            file_path=filename
        ).first()

        if existing_wt:
            existing_wt.status = 'modified'
            existing_wt.last_modified = datetime.now()
        else:
            wt = WorkingTree(
                user_id=user_id,
                repo_id=repo_id,
                file_path=filename,
                status='modified',
                last_modified=datetime.now()
            )
            db.session.add(wt)

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/api/working-tree', methods=['GET'])
def get_working_tree():
    user_id = request.args.get('user_id', type=int)
    repo_id = request.args.get('repo_id', type=int)

    if not user_id or not repo_id:
        return jsonify({'error': 'user_id and repo_id are required'}), 400

    working_tree = WorkingTree.query.filter_by(
        user_id=user_id,
        repo_id=repo_id
    ).all()

    return jsonify([{
        'file_path': wt.file_path,
        'status': wt.status,
        'last_modified': wt.last_modified.isoformat()
    } for wt in working_tree])

@api.route('/api/staging', methods=['GET'])
def get_staging():
    user_id = request.args.get('user_id', type=int)
    repo_id = request.args.get('repo_id', type=int)

    if not user_id or not repo_id:
        return jsonify({'error': 'user_id and repo_id are required'}), 400

    staging = StagingArea.query.filter_by(
        user_id=user_id,
        repo_id=repo_id
    ).all()

    return jsonify([{
        'file_path': s.file_path,
        'staged_at': s.staged_at.isoformat()
    } for s in staging])

# server/routes.py

from flask import Blueprint, jsonify, request
from models import db, User, Commit
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


