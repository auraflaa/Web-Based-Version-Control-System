const API_BASE = 'http://localhost:5000';

class APIError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
    }
}

async function handleResponse(response) {
    const data = await response.json();
    if (!response.ok) {
        throw new APIError(data.error || 'Unknown error occurred', response.status);
    }
    return data;
}

async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        return await handleResponse(response);
    } catch (error) {
        if (error instanceof APIError) {
            throw error;
        }
        throw new APIError('Network error occurred', 0);
    }
}

// Repository operations
export async function listRepositories() {
    return await fetchAPI('/api/repos');
}

export async function createRepository(name, description = '') {
    return await fetchAPI('/api/repos', {
        method: 'POST',
        body: JSON.stringify({ name, description })
    });
}

export async function getRepository(repoId) {
    return await fetchAPI(`/api/repos/${repoId}`);
}

// Branch operations
export async function listBranches(repoId) {
    return await fetchAPI(`/api/repos/${repoId}/branches`);
}

export async function createBranch(repoId, name, fromBranch = 'main') {
    return await fetchAPI(`/api/repos/${repoId}/branches`, {
        method: 'POST',
        body: JSON.stringify({ name, from_branch: fromBranch })
    });
}

// Commit operations
export async function listCommits(repoId, branch = 'main') {
    return await fetchAPI(`/api/repos/${repoId}/commits?branch=${branch}`);
}

export async function commit(repoId, message, files, branch = 'main') {
    const formData = new FormData();
    formData.append('message', message);
    formData.append('branch', branch);
    files.forEach(file => formData.append('files', file));

    return await fetch(`${API_BASE}/api/repos/${repoId}/commits`, {
        method: 'POST',
        body: formData
    }).then(handleResponse);
}

// File operations
export async function listFiles(repoId, path = '', branch = 'main') {
    return await fetchAPI(`/api/repos/${repoId}/files?path=${path}&branch=${branch}`);
}

export async function getFile(repoId, path, branch = 'main') {
    return await fetchAPI(`/api/repos/${repoId}/files/${path}?branch=${branch}`);
}

export async function createFile(repoId, filename, content = '') {
    return await fetchAPI(`/api/repos/${repoId}/files`, {
        method: 'POST',
        body: JSON.stringify({ filename, content })
    });
}

export async function deleteFile(repoId, filename) {
    return await fetchAPI(`/api/repos/${repoId}/files/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
    });
}

export async function updateFile(repoId, filename, content) {
    return await fetchAPI(`/api/repos/${repoId}/files/${encodeURIComponent(filename)}`, {
        method: 'PUT',
        body: JSON.stringify({ content })
    });
}

// Graph operations
export async function getCommitGraph(repoId) {
    return await fetchAPI(`/api/repos/${repoId}/graph`);
}

// Error handling helper
export function showError(error) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = error.message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    } else {
        console.error(error);
    }
}

export function logout() {
    localStorage.removeItem('userId');
    window.location.href = 'dashboard.html';
}

