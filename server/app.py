from flask import Flask, jsonify, render_template_string, request, redirect, send_from_directory
import mysql.connector
from vcs import VersionControlSystem
import os
from models import db, User
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://root:Pritam@127.0.0.1/codehub"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bcrypt = Bcrypt(app)

with app.app_context():
    db.init_app(app)
    db.create_all()

vcs = VersionControlSystem()

@app.route('/')
def index():
    client_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'client'))
    return send_from_directory(client_dir, 'index.html')

@app.route('/client/<path:filename>')
def serve_client(filename):
    client_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'client'))
    return send_from_directory(client_dir, filename)

@app.route('/api/status', methods=['GET'])
def api_status():
    # Example: Replace with real VCS logic
    status = vcs.status() if hasattr(vcs, 'status') else {}
    # Parse status string to dict for demo (replace with real dict in production)
    branch, head, staged, untracked = '-', '-', [], []
    if isinstance(status, str):
        lines = status.split('\n')
        for line in lines:
            if line.startswith('On branch:'):
                branch = line.split(':',1)[1].strip()
            elif line.startswith('HEAD:'):
                head = line.split(':',1)[1].strip()
            elif line.startswith('Staged files:'):
                staged = [f.strip() for f in line.split(':',1)[1].split(',') if f.strip() and 'None' not in f]
    return jsonify({
        'branch': branch,
        'head': head,
        'staged': staged,
        'untracked': untracked
    })

@app.route('/api/commits', methods=['GET'])
def api_commits():
    # Example: Replace with real VCS logic
    if hasattr(vcs, 'repositories') and vcs.current_repo:
        commits = vcs.repositories[vcs.current_repo]['commits']
        return jsonify([{
            'hash': c['hash'],
            'branch': c['branch'],
            'timestamp': c['timestamp'],
            'message': c['message']
        } for c in reversed(commits)])
    return jsonify([])

@app.route('/api/branches', methods=['GET'])
def api_branches():
    # Example: Replace with real VCS logic
    if hasattr(vcs, 'repositories') and vcs.current_repo:
        repo = vcs.repositories[vcs.current_repo]
        branches = repo['branches']
        current = repo['current_branch']
        return jsonify([{'name': b, 'active': (b == current)} for b in branches])
    return jsonify([])

@app.route('/api/branch', methods=['POST'])
def api_branch():
    data = request.json
    name = data.get('name')
    delete = data.get('delete', False)
    if delete:
        result = vcs.branch(name, delete=True)
    else:
        result = vcs.branch(name)
    return jsonify({'result': result})

@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    data = request.json
    branch = data.get('branch')
    result = vcs.checkout(branch)
    return jsonify({'result': result})

@app.route('/api/files', methods=['GET', 'POST'])
def api_files():
    if request.method == 'GET':
        if hasattr(vcs, 'repositories') and vcs.current_repo:
            files = vcs.repositories[vcs.current_repo]['files']
            return jsonify([{'name': f} for f in files])
        return jsonify([])
    else:
        data = request.json
        name = data.get('name')
        content = data.get('content', '')
        # Add or update file in VCS (simulate add)
        vcs.add(name, content)
        return jsonify({'result': 'File added/updated.'})

@app.route('/api/files/<filename>', methods=['GET'])
def api_file_view(filename):
    # Example: Replace with real VCS logic
    content = vcs.cat(filename)
    return jsonify({'data': content})

@app.route('/api/add', methods=['POST'])
def api_add():
    data = request.json
    name = data.get('name')
    result = vcs.add(name)
    return jsonify({'result': result})

@app.route('/api/commit', methods=['POST'])
def api_commit():
    data = request.json
    message = data.get('message')
    result = vcs.commit(message)
    return jsonify({'result': result})

@app.route('/api/stash', methods=['POST'])
def api_stash():
    result = vcs.stash_save()
    return jsonify({'result': result})

@app.route('/api/merge', methods=['POST'])
def api_merge():
    data = request.json
    branch = data.get('branch')
    result = vcs.merge(branch)
    return jsonify({'result': result})

@app.route('/api/reset', methods=['POST'])
def api_reset():
    data = request.json
    mode = data.get('mode', 'soft')
    steps = int(data.get('steps', 1))
    result = vcs.reset(mode, steps)
    return jsonify({'result': result})

@app.route('/api/revert', methods=['POST'])
def api_revert():
    data = request.json
    hash_ = data.get('hash')
    result = vcs.revert(hash_)
    return jsonify({'result': result})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('username')
    password = data.get('password')
    try:
        user = User.query.filter_by(email=email).first()
        if user is None:
            print(f"Login failed: user with email {email} not found")
        elif not bcrypt.check_password_hash(user.password, password):
            print(f"Login failed: password mismatch for user {email}")
        if user and bcrypt.check_password_hash(user.password, password):
            return jsonify({'success': True, 'user_id': user.id, 'name': user.name})
        else:
            return jsonify({'success': False, 'error': 'Incorrect email or password.'}), 401
    except Exception as e:
        # Log the error for debugging
        import traceback
        print('LOGIN ERROR:', traceback.format_exc())
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/api/test', methods=['GET'])
def api_test():
    print("Test route accessed")
    return jsonify({'success': True, 'message': 'Test route is working'})

if __name__ == '__main__':
    app.run(debug=True)
