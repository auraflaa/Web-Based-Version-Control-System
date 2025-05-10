const API_BASE = '/api';

// Error handler wrapper
async function handleResponse(response) {
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.error || 'API request failed');
    }
    
    return data;
}

// Authentication functions
export async function login(email, password) {
    const response = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    });
    const data = await handleResponse(response);
    // Store JWT token if present
    if (data.token) {
        localStorage.setItem('token', data.token);
    }
    if (data.success && data.data && data.data.user_id && data.data.name) {
        localStorage.setItem('userId', String(data.data.user_id));
        localStorage.setItem('userName', data.data.name);
    } else {
        localStorage.removeItem('userId');
        localStorage.removeItem('userName');
    }
    return data;
}

// Patch for /api/login (if used anywhere)
export async function apiLogin(email, password) {
    const response = await fetch(`${API_BASE}/api/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    });
    const data = await handleResponse(response);
    if (data.token) {
        localStorage.setItem('token', data.token);
    }
    if (data.success && data.data && data.data.user_id && data.data.name) {
        localStorage.setItem('userId', String(data.data.user_id));
        localStorage.setItem('userName', data.data.name);
    } else {
        localStorage.removeItem('userId');
        localStorage.removeItem('userName');
    }
    return data;
}

export async function register(name, email, password) {
    const response = await fetch(`${API_BASE}/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, email, password })
    });
    
    const data = await handleResponse(response);
    
    if (data.success) {
        localStorage.setItem('userId', data.user_id);
        localStorage.setItem('userName', data.name);
    }
    
    return data;
}

export function logout() {
    localStorage.removeItem('userId');
    localStorage.removeItem('userName');
    localStorage.removeItem('token');
    window.location.href = '/dashboard.html';
}

export function requireAuth() {
    const userId = localStorage.getItem('userId');
    if (!userId || userId === 'undefined' || isNaN(Number(userId))) {
        localStorage.removeItem('userId');
        localStorage.removeItem('userName');
        localStorage.removeItem('token');
        window.location.href = '/dashboard.html';
        return false;
    }
    return true;
}

// Repository functions
export async function listRepositories(userId, page = 1, perPage = 10) {
    const response = await fetch(`${API_BASE}/repos?user_id=${userId}&page=${page}&per_page=${perPage}`, {
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
    });
    return handleResponse(response);
}

export async function createRepository(name, userId) {
    if (!userId || userId === 'undefined' || isNaN(Number(userId))) {
        throw new Error('Invalid user ID. Please log in again.');
    }
    const response = await fetch(`${API_BASE}/repos`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ name, user_id: Number(userId) })
    });
    return handleResponse(response);
}

export async function syncRepository(repoId, userId) {
    const response = await fetch(`${API_BASE}/repos/${repoId}/sync`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ user_id: userId })
    });
    return handleResponse(response);
}

// Git operations
export async function createBranch(repoId, branchName, startPoint = 'HEAD') {
    const response = await fetch(`${API_BASE}/repos/${repoId}/branches`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ name: branchName, start_point: startPoint })
    });
    return handleResponse(response);
}

export async function createCommit(repoId, message, files) {
    const response = await fetch(`${API_BASE}/repos/${repoId}/commits`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ message, files })
    });
    return handleResponse(response);
}

export async function switchBranch(repoId, branchName) {
    const response = await fetch(`${API_BASE}/repos/${repoId}/checkout`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ branch: branchName })
    });
    return handleResponse(response);
}

// Error display helper
export function showError(error) {
    const errorElement = document.getElementById('error-message');
    if (errorElement) {
        errorElement.textContent = error.message || String(error);
        errorElement.style.display = 'block';
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 5000);
    } else {
        console.error('Error:', error);
    }
}

