import os
import hashlib
import json
import shutil
from datetime import datetime
import threading
import sys

# Platform-specific imports for file locking
if os.name == 'nt':
    import msvcrt
else:
    import fcntl

def sanitize_path(base, user_path):
    """Sanitize and validate a user-supplied file path to prevent directory traversal."""
    abs_base = os.path.abspath(base)
    abs_path = os.path.abspath(os.path.join(base, user_path))
    if not abs_path.startswith(abs_base):
        raise ValueError("Invalid file path: directory traversal detected.")
    return abs_path

class FileLock:
    """Context manager for file-based locking."""
    def __init__(self, lockfile):
        self.lockfile = lockfile
        self.handle = None

    def __enter__(self):
        self.handle = open(self.lockfile, 'a+')
        if os.name == 'nt':
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            fcntl.flock(self.handle, fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handle:
            if os.name == 'nt':
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self.handle, fcntl.LOCK_UN)
            self.handle.close()

class GitRepository:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.objects_path = os.path.join(repo_path, 'objects')
        self.refs_path = os.path.join(repo_path, 'refs')
        self.head_file = os.path.join(repo_path, 'HEAD')
        self.config_file = os.path.join(repo_path, 'config')
        self.files_path = os.path.join(repo_path, 'files')
        self.lockfile = os.path.join(repo_path, '.vcs.lock')

    @staticmethod
    def init(repo_path):
        """Initialize a new Git repository."""
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
        
        os.makedirs(repo_path)
        os.makedirs(os.path.join(repo_path, 'objects'))
        os.makedirs(os.path.join(repo_path, 'refs', 'heads'))
        os.makedirs(os.path.join(repo_path, 'refs', 'tags'))
        os.makedirs(os.path.join(repo_path, 'files'))
        
        # Initialize HEAD to point to master branch
        with open(os.path.join(repo_path, 'HEAD'), 'w') as f:
            f.write('ref: refs/heads/master')
        
        # Create empty config file
        with open(os.path.join(repo_path, 'config'), 'w') as f:
            json.dump({}, f)
        
        return GitRepository(repo_path)

    def create_branch(self, branch_name, start_point='HEAD'):
        """Create a new branch pointing to start_point."""
        if start_point == 'HEAD':
            with open(self.head_file, 'r') as f:
                ref = f.read().strip()
                if ref.startswith('ref: '):
                    ref = ref[5:]
                start_point = self.get_ref(ref)
        
        branch_path = os.path.join(self.refs_path, 'heads', branch_name)
        with open(branch_path, 'w') as f:
            f.write(start_point)

    def checkout(self, branch_name):
        """Switch to a different branch."""
        branch_path = os.path.join(self.refs_path, 'heads', branch_name)
        if not os.path.exists(branch_path):
            raise ValueError(f"Branch {branch_name} does not exist")
        
        # Update HEAD to point to new branch
        with open(self.head_file, 'w') as f:
            f.write(f'ref: refs/heads/{branch_name}')
        
        # Get commit hash
        commit_hash = self.get_ref(f'refs/heads/{branch_name}')
        if commit_hash:
            self._restore_commit_files(commit_hash)

    def commit(self, message, files):
        """Create a new commit with the given files and snapshot the repo folder."""
        with FileLock(self.lockfile):
            parent = self.get_current_commit()
            # --- Snapshot current repo folder ---
            if parent:
                parent_folder = f"{self.repo_path}_{parent}"
                if not os.path.exists(parent_folder):
                    shutil.copytree(self.repo_path, parent_folder, dirs_exist_ok=True)
            # --- Create new commit as before ---
            tree_hash = self._create_tree(files)
            commit = {
                'tree': tree_hash,
                'parent': parent,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
            commit_hash = self._save_object('commit', json.dumps(commit))
            current_ref = self._get_current_ref()
            self.update_ref(current_ref, commit_hash)
            return commit_hash

    def revert_to_commit(self, commit_hash):
        """Revert the repo to a previous commit by restoring the corresponding folder."""
        parent_folder = f"{self.repo_path}_{commit_hash}"
        if not os.path.exists(parent_folder):
            raise ValueError(f"Snapshot for commit {commit_hash} does not exist.")
        # Remove current repo folder contents except snapshots and lock
        for item in os.listdir(self.repo_path):
            item_path = os.path.join(self.repo_path, item)
            if not item.startswith('.') and not item.endswith('.lock'):
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                elif os.path.isfile(item_path):
                    os.remove(item_path)
        # Copy snapshot back
        for item in os.listdir(parent_folder):
            s = os.path.join(parent_folder, item)
            d = os.path.join(self.repo_path, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

    def list_files(self):
        """List all files in the working directory."""
        files = []
        for root, _, filenames in os.walk(self.files_path):
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), self.files_path)
                files.append({
                    'name': rel_path,
                    'type': 'file'
                })
        return files

    def get_file_content(self, file_path):
        """Get the content of a file."""
        abs_path = sanitize_path(self.files_path, file_path)
        if not os.path.exists(abs_path):
            return None
        with open(abs_path, 'r') as f:
            return f.read()

    def write_file(self, file_path, content):
        """Write content to a file."""
        abs_path = sanitize_path(self.files_path, file_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with FileLock(self.lockfile):
            with open(abs_path, 'w') as f:
                f.write(content)

    def delete_file(self, file_path):
        """Delete a file."""
        abs_path = sanitize_path(self.files_path, file_path)
        with FileLock(self.lockfile):
            if os.path.exists(abs_path):
                os.remove(abs_path)

    def sync(self):
        """Sync working directory with current commit."""
        commit_hash = self.get_current_commit()
        if commit_hash:
            self._restore_commit_files(commit_hash)

    def list_commits(self):
        """List all commits in the repository (simple linear history)."""
        commits = []
        # Start from HEAD
        commit_hash = self.get_current_commit()
        seen = set()
        while commit_hash and commit_hash not in seen:
            seen.add(commit_hash)
            obj = self._load_object(commit_hash)
            if not obj:
                break
            obj_type, data = obj
            if obj_type != 'commit':
                break
            commit = json.loads(data)
            commits.append({
                'hash': commit_hash,
                'message': commit.get('message', ''),
                'timestamp': commit.get('timestamp', ''),
                'parent': commit.get('parent', None)
            })
            commit_hash = commit.get('parent', None)
        return commits[::-1]  # Oldest first

    def get_commit_graph(self):
        """Return a simple commit graph (linear for now)."""
        # For now, just return the list of commits as nodes and edges
        commits = self.list_commits()
        nodes = [{'id': c['hash'], 'label': c['message']} for c in commits]
        edges = []
        for c in commits:
            if c['parent']:
                edges.append({'from': c['parent'], 'to': c['hash']})
        return {'nodes': nodes, 'edges': edges}

    # Helper methods
    def _save_object(self, obj_type, data):
        """Save an object to the repository and return its hash."""
        content = f"{obj_type} {data}".encode()
        sha1 = hashlib.sha1(content).hexdigest()
        
        path = os.path.join(self.objects_path, sha1[:2], sha1[2:])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'wb') as f:
            f.write(content)
        
        return sha1

    def _load_object(self, obj_hash):
        """Load an object from the repository."""
        path = os.path.join(self.objects_path, obj_hash[:2], obj_hash[2:])
        if not os.path.exists(path):
            return None
        
        with open(path, 'rb') as f:
            content = f.read()
        
        space_index = content.index(b' ')
        obj_type = content[:space_index].decode()
        data = content[space_index + 1:].decode()
        
        return obj_type, data

    def _create_tree(self, files):
        """Create a tree object from a list of files."""
        tree = {}
        for file_data in files:
            name = file_data['name']
            content = file_data['content']
            
            # Save file content as blob
            blob_hash = self._save_object('blob', content)
            tree[name] = blob_hash
        
        # Save tree object
        return self._save_object('tree', json.dumps(tree))

    def _restore_commit_files(self, commit_hash):
        """Restore files from a commit to the working directory."""
        obj_type, data = self._load_object(commit_hash)
        if obj_type != 'commit':
            raise ValueError('Not a commit object')
        
        commit = json.loads(data)
        tree_hash = commit['tree']
        
        # Clear working directory
        if os.path.exists(self.files_path):
            shutil.rmtree(self.files_path)
        os.makedirs(self.files_path)
        
        # Load tree
        _, tree_data = self._load_object(tree_hash)
        tree = json.loads(tree_data)
        
        # Restore files
        for name, blob_hash in tree.items():
            _, content = self._load_object(blob_hash)
            file_path = os.path.join(self.files_path, name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)

    def get_ref(self, ref_name):
        """Get the commit hash that a ref points to."""
        ref_path = os.path.join(self.repo_path, ref_name)
        if not os.path.exists(ref_path):
            return None
        with open(ref_path, 'r') as f:
            return f.read().strip()

    def update_ref(self, ref_name, commit_hash):
        """Update a ref to point to a commit."""
        ref_path = os.path.join(self.repo_path, ref_name)
        os.makedirs(os.path.dirname(ref_path), exist_ok=True)
        with open(ref_path, 'w') as f:
            f.write(commit_hash)

    def get_current_commit(self):
        """Get the commit hash of HEAD."""
        ref = self._get_current_ref()
        return self.get_ref(ref)

    def _get_current_ref(self):
        """Get the ref that HEAD points to."""
        with open(self.head_file, 'r') as f:
            ref = f.read().strip()
            if ref.startswith('ref: '):
                return ref[5:]
            return ref
