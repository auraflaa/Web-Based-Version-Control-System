from flask import Blueprint, request, jsonify, send_file
from .models import db, User, Repository, Branch, Commit, File, CommitFiles, WorkingTree, StagingArea
from .error import success_response, error_response, APIError
from .utils import validate_params, error_handler, get_pagination_params, Pagination
from .vcs import GitRepository
import os
from datetime import datetime
import zipfile
import io
from functools import wraps
import jwt
from datetime import timedelta
from .configs import SECRET_KEY
import traceback

api = Blueprint('api', __name__)

def debug_log(msg):
    print(f'[DEBUG ROUTES] {msg}')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split()[1]  # Remove 'Bearer' prefix
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401
        except Exception as e:
            return jsonify({'message': f'Authentication error: {str(e)}'}), 401
        if not current_user:
            return jsonify({'message': 'User not found'}), 404
        return f(current_user, *args, **kwargs)
    return decorated

@api.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400
    user = User(
        name=data['name'],
        email=data['email'],
        password=data['password']
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

@api.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user or user.password != data['password']:
        return jsonify({'message': 'Invalid credentials'}), 401
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }, SECRET_KEY, algorithm="HS256")
    return jsonify({'token': token})

@api.route('/api/register', methods=['POST'])
@error_handler
def api_register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    if not name or not email or not password:
        raise APIError('Missing required fields', status_code=400)
    if User.query.filter_by(email=email).first():
        raise APIError('Email already exists', status_code=400)
    user = User(name=name, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'data': {'user_id': user.id, 'name': user.name}}), 201

@api.route('/api/login', methods=['POST'])
@error_handler
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise APIError('Missing email or password', status_code=400)
    user = User.query.filter_by(email=email).first()
    if not user or user.password != password:
        raise APIError('Invalid credentials', status_code=401)
    return jsonify({'success': True, 'data': {'user_id': user.id, 'name': user.name}})

@api.route('/repos', methods=['GET'])
@token_required
def list_repos(current_user):
    repos = Repository.query.filter_by(user_id=current_user.id).all()
    return jsonify([repo.to_dict() for repo in repos])

@api.route('/repos', methods=['POST'])
@token_required
def create_repo(current_user):
    import traceback
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    if not name:
        print('[DEBUG] Missing repository name')
        return jsonify({'success': False, 'error': 'Missing repository name'}), 400
    # Prevent duplicate repo names for the same user
    existing = Repository.query.filter_by(user_id=current_user.id, name=name).first()
    if existing:
        return jsonify({'success': False, 'error': 'Repository name already exists'}), 400
    try:
        print(f'[DEBUG] Creating repo: name={name}, description={description}, user_id={current_user.id}')
        repo = Repository(
            name=name,
            description=description,
            user_id=current_user.id
        )
        db.session.add(repo)
        db.session.commit()
        print(f'[DEBUG] Repo created in DB with id={repo.id}')
        repo_path = os.path.join('repos', str(repo.id))
        GitRepository.init(repo_path)
        print(f'[DEBUG] Repo folder initialized at {repo_path}')
        return jsonify({'success': True, 'data': repo.to_dict()}), 201
    except Exception as e:
        print('[ERROR] Exception during repo creation:', e)
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/api/repos', methods=['GET'])
def api_list_repos():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Missing user_id'}), 400
    repos = Repository.query.filter_by(user_id=user_id).all()
    items = [repo.to_dict() for repo in repos]
    return jsonify({'success': True, 'data': {'items': items}})

@api.route('/api/repos', methods=['POST'])
def api_create_repo():
    import traceback
    data = request.get_json()
    name = data.get('name')
    user_id = data.get('user_id')
    description = data.get('description', '')
    if not name or not user_id or str(user_id) == 'undefined' or not str(user_id).isdigit():
        print(f'[DEBUG] Invalid user_id received: {user_id}')
        return jsonify({'success': False, 'error': 'Missing or invalid name or user_id'}), 400
    user_id = int(user_id)
    try:
        print(f'[DEBUG] Creating repo: name={name}, description={description}, user_id={user_id}')
        repo = Repository(name=name, user_id=user_id, description=description)
        db.session.add(repo)
        db.session.commit()
        print(f'[DEBUG] Repo created in DB with id={repo.id}')
        repo_path = os.path.join('repos', str(repo.id))
        GitRepository.init(repo_path)
        print(f'[DEBUG] Repo folder initialized at {repo_path}')
        return jsonify({'success': True, 'data': repo.to_dict()}), 201
    except Exception as e:
        print('[ERROR] Exception during repo creation:', e)
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/api/repos/<int:repo_id>', methods=['DELETE'])
def api_delete_repo(repo_id):
    repo = Repository.query.get_or_404(repo_id)
    db.session.delete(repo)
    db.session.commit()
    repo_path = os.path.join('repos', str(repo.id))
    if os.path.exists(repo_path):
        import shutil
        shutil.rmtree(repo_path)
    return jsonify({'success': True})

@api.route('/repos/<int:repo_id>', methods=['GET'])
@token_required
def get_repo(current_user, repo_id):
    print(f'[DEBUG] GET /repos/{repo_id} called by user_id={current_user.id}')
    repo = Repository.query.get_or_404(repo_id)
    print(f'[DEBUG] Repo found: id={repo.id}, user_id={repo.user_id}')
    if repo.user_id != current_user.id:
        print('[DEBUG] Unauthorized repo access')
        return jsonify({'message': 'Unauthorized'}), 403
    return jsonify(repo.to_dict())

@api.route('/repos/<int:repo_id>', methods=['DELETE'])
@token_required
def delete_repo(current_user, repo_id):
    print(f'[DEBUG] DELETE /repos/{repo_id} called by user_id={current_user.id}')
    repo = Repository.query.get_or_404(repo_id)
    print(f'[DEBUG] Repo found: id={repo.id}, user_id={repo.user_id}')
    if repo.user_id != current_user.id:
        print('[DEBUG] Unauthorized delete attempt')
        return jsonify({'message': 'Unauthorized'}), 403
    db.session.delete(repo)
    db.session.commit()
    repo_path = os.path.join('repos', str(repo.id))
    if os.path.exists(repo_path):
        import shutil
        print(f'[DEBUG] Deleting repo folder: {repo_path}')
        shutil.rmtree(repo_path)
    print('[DEBUG] Repo deleted successfully')
    return jsonify({'success': True})

@api.route('/repos/<int:repo_id>/files', methods=['GET'])
@token_required
def list_files(current_user, repo_id):
    print(f'[DEBUG] GET /repos/{repo_id}/files called by user_id={current_user.id}')
    repo = Repository.query.get_or_404(repo_id)
    print(f'[DEBUG] Repo found: id={repo.id}, user_id={repo.user_id}')
    if repo.user_id != current_user.id:
        print('[DEBUG] Unauthorized file list access')
        return jsonify({'message': 'Unauthorized'}), 403
        
    git_repo = GitRepository(os.path.join('repos', str(repo_id)))
    files = git_repo.list_files()
    print(f'[DEBUG] Files listed: {files}')
    return jsonify(files)

@api.route('/repos/<int:repo_id>/files', methods=['POST'])
@token_required
def create_file(current_user, repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
    data = request.get_json()
    file_path = data.get('name')
    content = data.get('content', '')
    if not file_path:
        return jsonify({'message': 'Missing file name'}), 400
    git_repo = GitRepository(os.path.join('repos', str(repo_id)))
    git_repo.write_file(file_path, content)
    # Add to working tree (DB)
    from .models import WorkingTree, File as DBFile
    db_file = DBFile.query.filter_by(filename=file_path, repo_id=repo_id).first()
    if not db_file:
        db_file = DBFile(filename=file_path, repo_id=repo_id)
        db.session.add(db_file)
        db.session.commit()
    # Add/Update working tree entry
    wt = WorkingTree.query.filter_by(repository_id=repo_id, file_id=db_file.id).first()
    if not wt:
        wt = WorkingTree(repository_id=repo_id, file_id=db_file.id)
        db.session.add(wt)
    wt.status = 'added'
    db.session.commit()
    return jsonify({'message': 'File created'})

@api.route('/repos/<int:repo_id>/files/<path:file_path>', methods=['GET'])
@token_required
def get_file(current_user, repo_id, file_path):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
        
    git_repo = GitRepository(os.path.join('repos', str(repo_id)))
    content = git_repo.get_file_content(file_path)
    
    if content is None:
        return jsonify({'message': 'File not found'}), 404
    return jsonify({'content': content})

@api.route('/repos/<int:repo_id>/files/<path:file_path>', methods=['PUT'])
@token_required
def write_file(current_user, repo_id, file_path):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
        
    data = request.get_json()
    git_repo = GitRepository(os.path.join('repos', str(repo_id)))
    git_repo.write_file(file_path, data['content'])
    # Add to working tree (DB)
    from .models import WorkingTree, File as DBFile
    db_file = DBFile.query.filter_by(filename=file_path, repo_id=repo_id).first()
    if not db_file:
        db_file = DBFile(filename=file_path, repo_id=repo_id)
        db.session.add(db_file)
        db.session.commit()
    # Add/Update working tree entry
    wt = WorkingTree.query.filter_by(repository_id=repo_id, file_id=db_file.id).first()
    if not wt:
        wt = WorkingTree(repository_id=repo_id, file_id=db_file.id)
        db.session.add(wt)
    wt.status = 'modified'
    db.session.commit()
    return jsonify({'message': 'File updated'})

@api.route('/repos/<int:repo_id>/files/<path:file_path>', methods=['DELETE'])
@token_required
def delete_file(current_user, repo_id, file_path):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
        
    git_repo = GitRepository(os.path.join('repos', str(repo_id)))
    git_repo.delete_file(file_path)
    
    return jsonify({'message': 'File deleted'})

# --- API proxy endpoints for /api/repos/<int:repo_id>/files (for frontend compatibility) ---
@api.route('/api/repos/<int:repo_id>/files', methods=['GET'])
@token_required
def api_list_files(current_user, repo_id):
    debug_log(f'GET /api/repos/{repo_id}/files called by user_id={current_user.id}')
    try:
        return list_files(current_user, repo_id)
    except Exception as e:
        debug_log(f'Exception in api_list_files: {e}\n{traceback.format_exc()}')
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/api/repos/<int:repo_id>/files', methods=['POST'])
@token_required
def api_create_file(current_user, repo_id):
    debug_log(f'POST /api/repos/{repo_id}/files called by user_id={current_user.id}')
    try:
        return create_file(current_user, repo_id)
    except Exception as e:
        debug_log(f'Exception in api_create_file: {e}\n{traceback.format_exc()}')
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/api/repos/<int:repo_id>/files/<path:file_path>', methods=['GET'])
@token_required
def api_get_file(current_user, repo_id, file_path):
    debug_log(f'GET /api/repos/{repo_id}/files/{file_path} called by user_id={current_user.id}')
    try:
        return get_file(current_user, repo_id, file_path)
    except Exception as e:
        debug_log(f'Exception in api_get_file: {e}\n{traceback.format_exc()}')
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/api/repos/<int:repo_id>/files/<path:file_path>', methods=['PUT'])
@token_required
def api_write_file(current_user, repo_id, file_path):
    debug_log(f'PUT /api/repos/{repo_id}/files/{file_path} called by user_id={current_user.id}')
    try:
        return write_file(current_user, repo_id, file_path)
    except Exception as e:
        debug_log(f'Exception in api_write_file: {e}\n{traceback.format_exc()}')
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/api/repos/<int:repo_id>/files/<path:file_path>', methods=['DELETE'])
@token_required
def api_delete_file(current_user, repo_id, file_path):
    debug_log(f'DELETE /api/repos/{repo_id}/files/{file_path} called by user_id={current_user.id}')
    try:
        return delete_file(current_user, repo_id, file_path)
    except Exception as e:
        debug_log(f'Exception in api_delete_file: {e}\n{traceback.format_exc()}')
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/repos/<int:repo_id>/commits', methods=['POST'])
@token_required
def create_commit(current_user, repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
        
    data = request.get_json()
    git_repo = GitRepository(os.path.join('repos', str(repo_id)))
    
    commit_hash = git_repo.commit(data['message'], data['files'])
    return jsonify({'commit_hash': commit_hash})

@api.route('/repos/<int:repo_id>/commits', methods=['GET'])
@token_required
def get_commits(current_user, repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
    git_repo = GitRepository(os.path.join('repos', str(repo_id)))
    commits = git_repo.list_commits()
    return jsonify(commits)

@api.route('/repos/<int:repo_id>/graph', methods=['GET'])
@token_required
def get_graph(current_user, repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
    git_repo = GitRepository(os.path.join('repos', str(repo_id)))
    graph = git_repo.get_commit_graph() if hasattr(git_repo, 'get_commit_graph') else []
    return jsonify(graph)

@api.route('/repos/<int:repo_id>/branches', methods=['GET'])
@token_required
def list_branches(current_user, repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
        
    branches_dir = os.path.join('repos', str(repo_id), 'refs', 'heads')
    branches = []
    for branch in os.listdir(branches_dir):
        branches.append({'name': branch})
    return jsonify(branches)

@api.route('/repos/<int:repo_id>/branches', methods=['POST'])
@token_required
def create_branch(current_user, repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
        
    data = request.get_json()
    git_repo = GitRepository(os.path.join('repos', str(repo_id)))
    git_repo.create_branch(data['name'], data.get('start_point', 'HEAD'))
    
    return jsonify({'message': 'Branch created'})

@api.route('/repos/<int:repo_id>/checkout', methods=['POST'])
@token_required
def checkout_branch(current_user, repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
        
    data = request.get_json()
    git_repo = GitRepository(os.path.join('repos', str(repo_id)))
    git_repo.checkout(data['branch'])
    
    return jsonify({'message': 'Checked out branch'})

@api.route('/repos/<int:repo_id>/revert', methods=['POST'])
@token_required
def revert_commit(current_user, repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
    data = request.get_json()
    commit_hash = data.get('commit_hash')
    if not commit_hash:
        return jsonify({'message': 'Missing commit_hash'}), 400
    git_repo = GitRepository(os.path.join('repos', str(repo_id)))
    try:
        git_repo.revert_to_commit(commit_hash)
        return jsonify({'message': f'Reverted to commit {commit_hash}'})
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@api.route('/repos/<int:repo_id>/sync', methods=['POST'])
@token_required
def sync_repo(current_user, repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
    git_repo = GitRepository(os.path.join('repos', str(repo_id)))
    try:
        git_repo.sync()
        return jsonify({'success': True, 'message': 'Repository synced'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/repos/<int:repo_id>/download', methods=['GET'])
@token_required
def download_repo(current_user, repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
    repo_path = os.path.join('repos', str(repo_id))
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, repo_path)
                zipf.write(file_path, arcname)
    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name=f'repo_{repo_id}.zip')

@api.route('/repos/<int:repo_id>/working-tree', methods=['GET'])
@token_required
def get_working_tree(current_user, repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
    from .models import WorkingTree, File as DBFile
    entries = WorkingTree.query.filter_by(repository_id=repo_id).all()
    files = []
    for entry in entries:
        db_file = DBFile.query.get(entry.file_id)
        if db_file:
            files.append({
                'id': db_file.id,
                'name': db_file.filename,
                'status': entry.status
            })
    return jsonify(files)

@api.route('/repos/<int:repo_id>/stage', methods=['POST'])
@token_required
def stage_files(current_user, repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
    from .models import WorkingTree, StagingArea, File as DBFile
    data = request.get_json()
    file_ids = data.get('file_ids', [])
    staged = []
    for file_id in file_ids:
        wt = WorkingTree.query.filter_by(repository_id=repo_id, file_id=file_id).first()
        if wt:
            # Move to staging area
            sa = StagingArea.query.filter_by(repository_id=repo_id, file_id=file_id).first()
            if not sa:
                sa = StagingArea(repository_id=repo_id, file_id=file_id)
                db.session.add(sa)
            sa.status = wt.status
            staged.append(file_id)
            db.session.delete(wt)
    db.session.commit()
    return jsonify({'staged': staged})

@api.route('/repos/<int:repo_id>/staging-area', methods=['GET'])
@token_required
def get_staging_area(current_user, repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
    from .models import StagingArea, File as DBFile
    entries = StagingArea.query.filter_by(repository_id=repo_id).all()
    files = []
    for entry in entries:
        db_file = DBFile.query.get(entry.file_id)
        if db_file:
            files.append({
                'id': db_file.id,
                'name': db_file.filename,
                'status': entry.status
            })
    return jsonify(files)


