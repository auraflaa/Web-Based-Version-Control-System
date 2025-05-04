// js/dashboard.js
// Optimized: Modular functions for each panel, minimal global state, and clear API usage

document.addEventListener('DOMContentLoaded', () => {
    loadRepoStatus();
    loadCommitHistory();
    loadBranches();
    loadFileExplorer();
});

// Utility: Fetch helper
async function apiGet(url) {
    const res = await fetch(url);
    return res.json();
}
async function apiPost(url, data) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return res.json();
}

// 1. Repository Status Panel
async function loadRepoStatus() {
    const statusDiv = document.getElementById('statusDetails');
    statusDiv.textContent = 'Loading...';
    try {
        const status = await apiGet('/api/status');
        statusDiv.innerHTML = `
            <b>Current Branch:</b> ${status.branch || '-'}<br>
            <b>HEAD:</b> ${status.head || '-'}<br>
            <b>Staged Files:</b> ${status.staged && status.staged.length ? status.staged.join(', ') : 'None'}<br>
            <b>Untracked:</b> ${status.untracked && status.untracked.length ? status.untracked.join(', ') : 'None'}
        `;
    } catch (e) {
        statusDiv.textContent = 'Failed to load status.';
    }
}

// 2. Commit History Panel
async function loadCommitHistory() {
    const commitDiv = document.getElementById('commitList');
    commitDiv.textContent = 'Loading...';
    try {
        const commits = await apiGet('/api/commits');
        if (!commits.length) {
            commitDiv.textContent = 'No commits yet.';
            return;
        }
        commitDiv.innerHTML = commits.map(c => `
            <div class="commit-item">
                <b>${c.hash}</b> [${c.branch}]<br>
                <span>${c.timestamp}</span><br>
                <i>${c.message}</i>
            </div>
        `).join('<hr>');
    } catch (e) {
        commitDiv.textContent = 'Failed to load commits.';
    }
}

// 3. Branch Management Panel
async function loadBranches() {
    const branchDiv = document.getElementById('branchList');
    branchDiv.textContent = 'Loading...';
    try {
        const branches = await apiGet('/api/branches');
        branchDiv.innerHTML = branches.map(b => `
            <div class="branch-item">
                <b>${b.name}</b> ${b.active ? '(current)' : ''}
                <button onclick="switchBranch('${b.name}')">Switch</button>
                ${b.name !== 'main' ? `<button onclick="deleteBranch('${b.name}')">Delete</button>` : ''}
            </div>
        `).join('');
        branchDiv.innerHTML += `
            <input id="newBranchName" placeholder="New branch name" />
            <button onclick="createBranch()">Create Branch</button>
        `;
    } catch (e) {
        branchDiv.textContent = 'Failed to load branches.';
    }
}
window.switchBranch = async function(name) {
    await apiPost('/api/checkout', { branch: name });
    loadRepoStatus();
    loadBranches();
    loadCommitHistory();
};
window.deleteBranch = async function(name) {
    await apiPost('/api/branch', { name, delete: true });
    loadBranches();
};
window.createBranch = async function() {
    const name = document.getElementById('newBranchName').value.trim();
    if (!name) return;
    await apiPost('/api/branch', { name });
    loadBranches();
};

// 4. File Explorer Panel
async function loadFileExplorer() {
    const fileDiv = document.getElementById('fileList');
    fileDiv.textContent = 'Loading...';
    try {
        const files = await apiGet('/api/files');
        if (!files.length) {
            fileDiv.textContent = 'No files.';
            return;
        }
        fileDiv.innerHTML = files.map(f => `
            <div class="file-item">
                <b>${f.name}</b>
                <button onclick="viewFile('${f.name}')">View</button>
                <button onclick="editFile('${f.name}')">Edit</button>
                <button onclick="stageFile('${f.name}')">Stage</button>
            </div>
        `).join('');
        fileDiv.innerHTML += `
            <input id="newFileName" placeholder="New file name" />
            <button onclick="addFile()">Add File</button>
        `;
    } catch (e) {
        fileDiv.textContent = 'Failed to load files.';
    }
}
window.viewFile = async function(name) {
    const content = await apiGet(`/api/files/${encodeURIComponent(name)}`);
    alert(`File: ${name}\n\n${content.data || ''}`);
};
window.editFile = async function(name) {
    const newContent = prompt('Edit file content:');
    if (newContent !== null) {
        await apiPost(`/api/files`, { name, content: newContent });
        loadFileExplorer();
    }
};
window.stageFile = async function(name) {
    await apiPost('/api/add', { name });
    loadRepoStatus();
};
window.addFile = async function() {
    const name = document.getElementById('newFileName').value.trim();
    if (!name) return;
    await apiPost('/api/files', { name, content: '' });
    loadFileExplorer();
};

// 5. Actions Panel
window.commitChanges = async function() {
    const msg = prompt('Commit message:');
    if (!msg) return;
    await apiPost('/api/commit', { message: msg });
    loadRepoStatus();
    loadCommitHistory();
};
window.stashChanges = async function() {
    await apiPost('/api/stash', {});
    loadRepoStatus();
};
window.mergeBranch = async function() {
    const branch = prompt('Merge branch:');
    if (!branch) return;
    await apiPost('/api/merge', { branch });
    loadRepoStatus();
    loadCommitHistory();
};
window.resetChanges = async function() {
    const mode = prompt('Reset mode (soft/mixed/hard):', 'soft');
    const steps = prompt('How many commits to reset?', '1');
    await apiPost('/api/reset', { mode, steps: parseInt(steps) });
    loadRepoStatus();
    loadCommitHistory();
};
window.revertCommit = async function() {
    const hash = prompt('Commit hash to revert:');
    if (!hash) return;
    await apiPost('/api/revert', { hash });
    loadRepoStatus();
    loadCommitHistory();
};