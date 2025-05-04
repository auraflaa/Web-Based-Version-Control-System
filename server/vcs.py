import uuid
import time

class Commit:
    def __init__(self, message, files, parent=None):
        self.id = str(uuid.uuid4())[:8]  # Commit ID as a string
        self.message = str(message)  # Ensure message is a string
        self.files = {filename: str(content) for filename, content in files.items()}  # Files as {filename: content} with content as strings
        self.parent = parent  # Parent commit (linked list)
        self.timestamp = str(time.time())  # Timestamp as a string for uniformity

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "files": {filename: str(content) for filename, content in self.files.items()},  # Ensure all file content is in string format
            "parent": self.parent.id if self.parent else None,
            "timestamp": self.timestamp,
        }

class VersionControlSystem:
    def __init__(self):
        self.repositories = {}  # repo_name: {branches, commits, etc.}
        self.current_repo = None
        self.staging_area = {}
        self.stash = []
        self.head = None
        self.current_branch = None
        self.branch_stack = []

    def init(self, repo_name='repo'):
        if repo_name in self.repositories:
            return f"Repository '{repo_name}' already exists."
        self.repositories[repo_name] = {
            'branches': {'main': None},
            'commits': [],
            'files': {},
            'current_branch': 'main',
            'head': None,
            'staging_area': {},
            'stash': []
        }
        self.current_repo = repo_name
        self.current_branch = 'main'
        self.head = None
        return f"Initialized empty repository '{repo_name}' with main branch."

    def clone(self, repo_name):
        if repo_name not in self.repositories:
            return f"Repository '{repo_name}' does not exist."
        clone_name = repo_name + '_clone'
        import copy
        self.repositories[clone_name] = copy.deepcopy(self.repositories[repo_name])
        return f"Cloned repository as '{clone_name}'."

    def add(self, filename, content=''):
        if not self.current_repo:
            return "No repository initialized. Run 'init' first."
        self.repositories[self.current_repo]['staging_area'][filename] = content
        return f"Added '{filename}' to staging area."

    def commit(self, message):
        if not self.current_repo:
            return "No repository initialized. Run 'init' first."
        staging = self.repositories[self.current_repo]['staging_area']
        if not staging:
            return "Nothing to commit. Staging area is empty."
        import uuid, time
        commit_hash = str(uuid.uuid4())[:8]
        commit = {
            'hash': commit_hash,
            'message': message,
            'files': staging.copy(),
            'parent': self.repositories[self.current_repo]['head'],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'branch': self.repositories[self.current_repo]['current_branch']
        }
        self.repositories[self.current_repo]['commits'].append(commit)
        self.repositories[self.current_repo]['head'] = commit_hash
        self.repositories[self.current_repo]['branches'][self.repositories[self.current_repo]['current_branch']] = commit_hash
        self.repositories[self.current_repo]['files'].update(staging)
        self.repositories[self.current_repo]['staging_area'] = {}
        return f"Committed as {commit_hash}: {message}"

    def branch(self, name=None, delete=False):
        if not self.current_repo:
            return "No repository initialized. Run 'init' first."
        branches = self.repositories[self.current_repo]['branches']
        if name is None:
            return 'Branches:\n' + '\n'.join(branches.keys())
        if delete:
            if name == 'main':
                return "Cannot delete main branch."
            if name not in branches:
                return f"Branch '{name}' does not exist."
            del branches[name]
            return f"Deleted branch '{name}'."
        if name in branches:
            return f"Branch '{name}' already exists."
        branches[name] = self.repositories[self.current_repo]['head']
        return f"Created branch '{name}'."

    def checkout(self, name):
        if not self.current_repo:
            return "No repository initialized. Run 'init' first."
        branches = self.repositories[self.current_repo]['branches']
        if name not in branches:
            return f"Branch '{name}' does not exist."
        self.repositories[self.current_repo]['current_branch'] = name
        self.current_branch = name
        self.head = branches[name]
        return f"Switched to branch '{name}'."

    def merge(self, source):
        if not self.current_repo:
            return "No repository initialized. Run 'init' first."
        repo = self.repositories[self.current_repo]
        branches = repo['branches']
        if source not in branches:
            return f"Branch '{source}' does not exist."
        target = repo['current_branch']
        if source == target:
            return "Cannot merge a branch into itself."
        # Simple merge: just combine files (no conflict detection for now)
        source_commit_hash = branches[source]
        target_commit_hash = branches[target]
        source_commit = next((c for c in repo['commits'] if c['hash'] == source_commit_hash), None)
        target_commit = next((c for c in repo['commits'] if c['hash'] == target_commit_hash), None)
        merged_files = {}
        if target_commit:
            merged_files.update(target_commit['files'])
        if source_commit:
            merged_files.update(source_commit['files'])
        # Create merge commit
        import uuid, time
        commit_hash = str(uuid.uuid4())[:8]
        commit = {
            'hash': commit_hash,
            'message': f"Merge branch '{source}' into '{target}'",
            'files': merged_files,
            'parent': target_commit_hash,
            'merge_parent': source_commit_hash,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'branch': target
        }
        repo['commits'].append(commit)
        repo['head'] = commit_hash
        branches[target] = commit_hash
        repo['files'].update(merged_files)
        return f"Merged branch '{source}' into '{target}'."

    def log(self):
        if not self.current_repo:
            return "No repository initialized. Run 'init' first."
        commits = self.repositories[self.current_repo]['commits']
        if not commits:
            return "No commits yet."
        log_lines = [f"{c['hash']} {c['timestamp']} [{c['branch']}] - {c['message']}" for c in reversed(commits)]
        return '\n'.join(log_lines)

    def stash_save(self):
        if not self.current_repo:
            return "No repository initialized. Run 'init' first."
        staging = self.repositories[self.current_repo]['staging_area']
        if not staging:
            return "Nothing to stash."
        self.repositories[self.current_repo]['stash'].append(staging.copy())
        self.repositories[self.current_repo]['staging_area'] = {}
        return "Stashed changes."

    def stash_list(self):
        if not self.current_repo:
            return "No repository initialized. Run 'init' first."
        stash = self.repositories[self.current_repo]['stash']
        if not stash:
            return "No stashes."
        return '\n'.join([f"stash@{{{i}}}: {list(s.keys())}" for i, s in enumerate(stash)])

    def stash_apply(self, idx=0):
        if not self.current_repo:
            return "No repository initialized. Run 'init' first."
        stash = self.repositories[self.current_repo]['stash']
        if not stash:
            return "No stashes."
        try:
            changes = stash.pop(idx)
            self.repositories[self.current_repo]['staging_area'].update(changes)
            return f"Applied stash@{{{idx}}}."
        except IndexError:
            return f"No stash at index {idx}."

    def reset(self, mode='soft', steps=1):
        if not self.current_repo:
            return "No repository initialized. Run 'init' first."
        repo = self.repositories[self.current_repo]
        commits = repo['commits']
        if len(commits) < steps:
            return "Not enough commits to reset."
        if mode == 'soft':
            repo['head'] = commits[-steps-1]['hash'] if len(commits) > steps else None
            return f"Soft reset HEAD~{steps}."
        elif mode == 'mixed':
            repo['head'] = commits[-steps-1]['hash'] if len(commits) > steps else None
            repo['staging_area'] = {}
            return f"Mixed reset HEAD~{steps}."
        elif mode == 'hard':
            repo['head'] = commits[-steps-1]['hash'] if len(commits) > steps else None
            repo['staging_area'] = {}
            repo['commits'] = commits[:-steps]
            return f"Hard reset HEAD~{steps}."
        else:
            return "Unknown reset mode."

    def revert(self, commit_hash):
        if not self.current_repo:
            return "No repository initialized. Run 'init' first."
        repo = self.repositories[self.current_repo]
        commit = next((c for c in repo['commits'] if c['hash'] == commit_hash), None)
        if not commit:
            return f"Commit {commit_hash} not found."
        # Inverse commit: remove files added in this commit
        inverse_files = {k: '' for k in commit['files'].keys()}
        import uuid, time
        new_hash = str(uuid.uuid4())[:8]
        revert_commit = {
            'hash': new_hash,
            'message': f"Revert commit {commit_hash}",
            'files': inverse_files,
            'parent': repo['head'],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'branch': repo['current_branch']
        }
        repo['commits'].append(revert_commit)
        repo['head'] = new_hash
        repo['files'].update(inverse_files)
        return f"Reverted commit {commit_hash}."

    def status(self):
        if not self.current_repo:
            return "No repository initialized. Run 'init' first."
        repo = self.repositories[self.current_repo]
        branch = repo['current_branch']
        head = repo['head']
        staged = list(repo['staging_area'].keys())
        return f"On branch: {branch}\nHEAD: {head}\nStaged files: {', '.join(staged) if staged else 'None'}"

    def cat(self, filename):
        if not self.current_repo:
            return "No repository initialized. Run 'init' first."
        repo = self.repositories[self.current_repo]
        content = repo['files'].get(filename)
        if content is None:
            return f"File '{filename}' not found."
        return f"{filename}:\n{content}"

    def get_prompt(self):
        if not self.current_repo:
            return {'repo': None, 'branch': None}
        repo = self.repositories[self.current_repo]
        return {'repo': self.current_repo, 'branch': repo['current_branch']}
