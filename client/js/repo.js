import { requireAuth, showError, syncRepository, logout } from './api.js';

let currentRepoId = null;
let currentSection = 'overview';

// Utility to get JWT token from localStorage
function getAuthToken() {
    return localStorage.getItem('token');
}

// Patch fetch to add Authorization header for /repos/ API calls
async function authFetch(url, options = {}) {
    const token = getAuthToken();
    if (token && url.startsWith('/api/repos')) {
        options.headers = options.headers || {};
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    return fetch(url, options);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth()) return;
    
    // Display user name
    const userName = localStorage.getItem('userName');
    document.getElementById('userName').textContent = userName;
    
    // Get repository ID from URL
    const params = new URLSearchParams(window.location.search);
    currentRepoId = params.get('id');
    
    if (!currentRepoId) {
        window.location.href = 'repos.html';
        return;
    }
    
    // Load repository data
    await loadRepository();
    
    // Setup navigation
    setupNavigation();
    
    // Load initial section
    loadSection(currentSection);
});

async function loadRepository() {
    const loading = document.getElementById('loading');
    try {
        loading.style.display = 'block';
        // Use the correct API endpoint for repo details
        const response = await authFetch(`/api/repos/${currentRepoId}`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || data.message || 'Failed to load repository');
        }
        document.getElementById('repoName').textContent = data.name;
        document.title = `${data.name} - Git GUI`;
        await loadStats();
        loading.style.display = 'none';
    } catch (error) {
        loading.style.display = 'none';
        showError(error);
    }
}

async function loadStats() {
    try {
        // Load commit count
        const commitsResponse = await authFetch(`/api/repos/${currentRepoId}/commits`);
        const commitsData = await commitsResponse.json();
        document.getElementById('commitCount').textContent = commitsData.total || 0;
        
        // Load branch count
        const branchesResponse = await authFetch(`/api/repos/${currentRepoId}/branches`);
        const branchesData = await branchesResponse.json();
        document.getElementById('branchCount').textContent = branchesData.total || 0;
        
        // Load file count
        const filesResponse = await authFetch(`/api/repos/${currentRepoId}/files`);
        const filesData = await filesResponse.json();
        document.getElementById('fileCount').textContent = filesData.length || 0;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Add navigation and section loading for working tree and staging area
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            const section = item.dataset.section;
            loadSection(section);
        });
    });
}

async function loadSection(section) {
    document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
    const sectionElement = document.getElementById(section);
    if (sectionElement) {
        sectionElement.style.display = 'block';
    }
    switch (section) {
        case 'files':
            await loadFiles();
            break;
        case 'commits':
            await loadCommits();
            break;
        case 'branches':
            await loadBranches();
            break;
        case 'graph':
            await loadGraph();
            break;
        case 'working-tree':
            await loadWorkingTree();
            break;
        case 'staging-area':
            await loadStagingArea();
            break;
    }
    currentSection = section;
}

async function loadFiles() {
    const filesSection = document.getElementById('files');
    filesSection.innerHTML = `<div class="files-header">
        <h2 style="display:inline-block;">Files</h2>
        <button id="addFileBtn" class="action-btn primary-btn" style="float:right; margin-left:1em;">Add File</button>
    </div>
    <ul class="file-list"></ul>`;
    try {
        const response = await authFetch(`/api/repos/${currentRepoId}/files`);
        const data = await response.json();
        const fileList = filesSection.querySelector('.file-list');
        fileList.innerHTML = '';
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load files');
        }
        if (data.length === 0) {
            fileList.innerHTML = '<li>No files found.</li>';
        } else {
            for (const file of data) {
                fileList.innerHTML += `<li><span class="filename">${file.name}</span> <button class="edit-file-btn" data-filename="${file.name}">Edit</button></li>`;
            }
        }
        document.getElementById('addFileBtn').onclick = showAddFileModal;
        filesSection.querySelectorAll('.edit-file-btn').forEach(btn => {
            btn.onclick = () => showEditFileModal(btn.dataset.filename);
        });
    } catch (error) {
        filesSection.innerHTML = `<div class="error-message">${error.message}</div>`;
    }
}

function showAddFileModal() {
    const filesSection = document.getElementById('files');
    filesSection.innerHTML += `
        <div class="modal active" id="addFileModal">
            <div class="modal-content">
                <h2>Add New File</h2>
                <form id="addFileForm">
                    <input type="text" id="newFileName" placeholder="Filename" required />
                    <textarea id="newFileContent" placeholder="File content" rows="6"></textarea>
                    <div class="modal-actions">
                        <button type="button" onclick="document.getElementById('addFileModal').remove()">Cancel</button>
                        <button type="submit">Add</button>
                    </div>
                </form>
            </div>
        </div>`;
    document.getElementById('addFileForm').onsubmit = async (e) => {
        e.preventDefault();
        const name = document.getElementById('newFileName').value;
        const content = document.getElementById('newFileContent').value;
        await addOrEditFile(name, content);
        document.getElementById('addFileModal').remove();
        await loadFiles();
    };
}

function showEditFileModal(filename) {
    authFetch(`/api/repos/${currentRepoId}/files/${filename}`)
        .then(res => res.json())
        .then(data => {
            const filesSection = document.getElementById('files');
            filesSection.innerHTML += `
                <div class="modal active" id="editFileModal">
                    <div class="modal-content">
                        <h2>Edit File: ${filename}</h2>
                        <form id="editFileForm">
                            <textarea id="editFileContent" rows="10">${data.content || ''}</textarea>
                            <div class="modal-actions">
                                <button type="button" onclick="document.getElementById('editFileModal').remove()">Cancel</button>
                                <button type="submit">Save</button>
                            </div>
                        </form>
                    </div>
                </div>`;
            document.getElementById('editFileForm').onsubmit = async (e) => {
                e.preventDefault();
                const content = document.getElementById('editFileContent').value;
                await addOrEditFile(filename, content);
                document.getElementById('editFileModal').remove();
                await loadFiles();
            };
        });
}

async function addOrEditFile(filename, content) {
    // If file exists, use PUT, else use POST
    const files = await authFetch(`/api/repos/${currentRepoId}/files`);
    const fileList = await files.json();
    const exists = fileList.some(f => f.name === filename);
    if (exists) {
        await authFetch(`/api/repos/${currentRepoId}/files/${filename}`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content })
            }
        );
    } else {
        await authFetch(`/api/repos/${currentRepoId}/files`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: filename, content })
            }
        );
    }
}

async function loadCommits() {
    const commitsSection = document.getElementById('commits');
    commitsSection.innerHTML = '<div class="loading">Loading commits...</div>';
    
    try {
        const response = await authFetch(`/api/repos/${currentRepoId}/commits`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load commits');
        }
        
        // Render commits section (to be implemented)
        commitsSection.innerHTML = '<h2>Commits content here</h2>';
    } catch (error) {
        commitsSection.innerHTML = `<div class="error-message">${error.message}</div>`;
    }
}

async function loadBranches() {
    const branchesSection = document.getElementById('branches');
    branchesSection.innerHTML = '<div class="loading">Loading branches...</div>';
    
    try {
        const response = await authFetch(`/api/repos/${currentRepoId}/branches`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load branches');
        }
        
        // Render branches section (to be implemented)
        branchesSection.innerHTML = '<h2>Branches content here</h2>';
    } catch (error) {
        branchesSection.innerHTML = `<div class="error-message">${error.message}</div>`;
    }
}

async function loadGraph() {
    const graphSection = document.getElementById('graph');
    graphSection.innerHTML = '<div class="loading">Loading commit graph...</div>';
    
    try {
        const response = await authFetch(`/api/repos/${currentRepoId}/graph`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load graph');
        }
        
        // Render graph section (to be implemented)
        graphSection.innerHTML = '<h2>Commit graph here</h2>';
    } catch (error) {
        graphSection.innerHTML = `<div class="error-message">${error.message}</div>`;
    }
}

async function loadWorkingTree() {
    const section = document.getElementById('working-tree');
    section.innerHTML = '<div class="loading">Loading working tree...</div>';
    try {
        const response = await authFetch(`/api/repos/${currentRepoId}/working-tree`);
        const files = await response.json();
        let html = `<h2>Working Tree</h2>`;
        if (files.length === 0) {
            html += '<div>No files in working tree.</div>';
        } else {
            html += '<form id="stageForm"><ul class="file-list">';
            for (const file of files) {
                html += `<li><label><input type="checkbox" name="file" value="${file.id}"> ${file.name} <span class="status">[${file.status}]</span></label></li>`;
            }
            html += '</ul><button type="submit">Stage Selected</button></form>';
        }
        section.innerHTML = html;
        const form = document.getElementById('stageForm');
        if (form) {
            form.onsubmit = async (e) => {
                e.preventDefault();
                const fileIds = Array.from(form.querySelectorAll('input[name="file"]:checked')).map(cb => parseInt(cb.value));
                await stageFiles(fileIds);
                await loadWorkingTree();
                await loadStagingArea();
            };
        }
    } catch (error) {
        section.innerHTML = `<div class="error-message">${error.message}</div>`;
    }
}

async function stageFiles(fileIds) {
    await authFetch(`/api/repos/${currentRepoId}/stage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_ids: fileIds })
    });
}

async function loadStagingArea() {
    const section = document.getElementById('staging-area');
    section.innerHTML = '<div class="loading">Loading staging area...</div>';
    try {
        const response = await authFetch(`/api/repos/${currentRepoId}/staging-area`);
        const files = await response.json();
        let html = `<h2>Staging Area</h2>`;
        if (files.length === 0) {
            html += '<div>No files staged.</div>';
        } else {
            html += '<ul class="file-list">';
            for (const file of files) {
                html += `<li>${file.name} <span class="status">[${file.status}]</span></li>`;
            }
            html += '</ul>';
            html += `<form id="commitForm"><input type="text" id="commitMsg" placeholder="Commit message" required><button type="submit">Commit</button></form>`;
        }
        section.innerHTML = html;
        const form = document.getElementById('commitForm');
        if (form) {
            form.onsubmit = async (e) => {
                e.preventDefault();
                const msg = document.getElementById('commitMsg').value;
                await commitStagedFiles(msg);
                await loadStagingArea();
                await loadCommits();
            };
        }
    } catch (error) {
        section.innerHTML = `<div class="error-message">${error.message}</div>`;
    }
}

async function commitStagedFiles(message) {
    // Get staged files
    const response = await authFetch(`/api/repos/${currentRepoId}/staging-area`);
    const files = await response.json();
    const fileList = files.map(f => ({ name: f.name, content: '' })); // You may want to fetch content if needed
    await authFetch(`/api/repos/${currentRepoId}/commits`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, files: fileList })
    });
}

// Make functions global for onclick handlers
window.sync = async () => {
    try {
        // Use the correct API endpoint and method for sync
        const response = await authFetch(`/api/repos/${currentRepoId}/sync`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        if (result.success) {
            await loadRepository();
        } else {
            throw new Error(result.error || result.message || 'Failed to sync repository');
        }
    } catch (error) {
        showError(error);
    }
};

window.download = async () => {
    try {
        window.location.href = `/api/repos/${currentRepoId}/download`;
    } catch (error) {
        showError(error);
    }
};

// Make logout function global for onclick handler
window.logout = logout;