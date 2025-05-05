// API client for version control system
const API_BASE = 'http://127.0.0.1:5000/api';
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

// Error class for API errors
class APIError extends Error {
    constructor(message, status) {
        super(message);
        this.name = 'APIError';
        this.status = status;
    }
}

// Generic API request function
export async function fetchAPI(endpoint, options = {}) {
    try {
        const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
        console.log(`Making ${options.method || 'GET'} request to:`, url);
        
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...options.headers
            },
            mode: 'cors'
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new APIError(data.error || 'API request failed', response.status);
        }
        
        return data;
    } catch (error) {
        console.error(`API Error:`, error);
        throw error;
    }
}

// Authentication
export async function login(email, password) {
    return await fetchAPI('/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
    });
}

export async function register(name, email, password) {
    return await fetchAPI('/register', {
        method: 'POST',
        body: JSON.stringify({ name, email, password })
    });
}

export async function logout() {
    localStorage.removeItem('userId');
    localStorage.removeItem('userName');
    window.location.href = 'dashboard.html';
}

// Repository operations
export async function listRepositories(userId) {
    return await fetchAPI(`/repos?user_id=${userId}`);
}

export async function createRepository(name, userId) {
    return await fetchAPI('/repos', {
        method: 'POST',
        body: JSON.stringify({ name, user_id: userId })
    });
}

export async function syncRepository(repoId, userId) {
    return await fetchAPI(`/repos/${repoId}/sync`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId })
    });
}

// File operations
export async function listFiles(repoId, path = '') {
    return await fetchAPI(`/repos/${repoId}/files?path=${encodeURIComponent(path)}`);
}

export async function getFileContent(repoId, filePath) {
    return await fetchAPI(`/repos/${repoId}/files/${encodeURIComponent(filePath)}`);
}

export async function createFile(repoId, path, content, message) {
    return await fetchAPI(`/repos/${repoId}/files`, {
        method: 'POST',
        body: JSON.stringify({ path, content, message })
    });
}

export async function updateFile(repoId, filePath, content, message) {
    return await fetchAPI(`/repos/${repoId}/files/${encodeURIComponent(filePath)}`, {
        method: 'PUT',
        body: JSON.stringify({ content, message })
    });
}

export async function deleteFile(repoId, filePath, message) {
    return await fetchAPI(`/repos/${repoId}/files/${encodeURIComponent(filePath)}`, {
        method: 'DELETE',
        body: JSON.stringify({ message })
    });
}

// Working tree and staging operations
export async function stageFile(repoId, filePath) {
    return await fetchAPI(`/repos/${repoId}/stage`, {
        method: 'POST',
        body: JSON.stringify({ file_path: filePath })
    });
}

export async function unstageFile(repoId, filePath) {
    return await fetchAPI(`/repos/${repoId}/unstage`, {
        method: 'POST',
        body: JSON.stringify({ file_path: filePath })
    });
}

export async function commit(repoId, message) {
    return await fetchAPI(`/repos/${repoId}/commit`, {
        method: 'POST',
        body: JSON.stringify({ message })
    });
}

// Error display utility
export function showError(error, errorDiv = 'error-message') {
    const element = document.getElementById(errorDiv);
    if (element) {
        element.textContent = error.message || 'An unexpected error occurred';
        element.style.display = 'block';
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    } else {
        console.error(error);
    }
}

// Authentication check utility
export function requireAuth() {
    const userId = localStorage.getItem('userId');
    const userName = localStorage.getItem('userName');
    
    if (!userId || !userName) {
        window.location.href = 'dashboard.html';
        return false;
    }
    return true;
}

