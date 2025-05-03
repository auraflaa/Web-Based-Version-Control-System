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
        self.branches = {
            "main": None  # Main branch starts with no commits
        }
        self.current_branch = "main"
        self.branch_stack = []  # Stack to manage branch switching

    def commit(self, message, files):
        parent = self.branches[self.current_branch]
        new_commit = Commit(str(message), {filename: str(content) for filename, content in files.items()}, parent)  # Ensure files and message are strings
        self.branches[self.current_branch] = new_commit
        return new_commit

    def create_branch(self, name):
        if name in self.branches:
            raise ValueError("Branch already exists.")
        self.branches[name] = self.branches[self.current_branch]

    def switch_branch(self, name):
        if name not in self.branches:
            raise ValueError("Branch does not exist.")
        self.branch_stack.append(self.current_branch)  # Push the current branch to stack
        self.current_branch = name

    def switch_back(self):
        if not self.branch_stack:
            raise ValueError("No previous branch to switch to.")
        self.current_branch = self.branch_stack.pop()  # Pop the previous branch from stack

    def get_latest_commit(self, branch):
        return self.branches.get(branch)

    def merge_branch(self, source_branch):
        if source_branch not in self.branches:
            raise ValueError("Source branch does not exist.")

        target_commit = self.branches[self.current_branch]
        source_commit = self.branches[source_branch]

        # Merge files as strings
        merged_files = {}
        conflicts = []

        all_files = set(target_commit.files.keys()) | set(source_commit.files.keys())

        for file in all_files:
            target_content = target_commit.files.get(file, "")
            source_content = source_commit.files.get(file, "")

            if target_content == source_content:
                merged_files[file] = target_content
            elif target_content and source_content:
                # Conflict
                conflicts.append(file)
                merged_files[file] = (
                    "<<<<<<< HEAD\n" +
                    target_content +
                    "\n=======\n" +
                    source_content +
                    "\n>>>>>>> " + source_branch
                )
            else:
                # One branch has it, the other doesn't
                merged_files[file] = target_content or source_content

        merge_msg = f"Merged branch '{source_branch}' into '{self.current_branch}'"
        merged_commit = Commit(merge_msg, merged_files, parent=target_commit)
        self.branches[self.current_branch] = merged_commit

        return {
            "commit": merged_commit,
            "conflicts": conflicts
        }
