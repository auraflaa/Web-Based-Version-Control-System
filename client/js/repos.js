import { listRepositories, createRepository, logout, requireAuth, showError } from './api.js';

// Check authentication on page load
document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth()) return;
    
    // Display user name
    const userName = localStorage.getItem('userName');
    document.getElementById('userName').textContent = (userName && userName !== 'undefined') ? userName : '';
    
    // Load repositories
    await loadRepositories();
});

async function loadRepositories() {
    const loading = document.getElementById('loading');
    const repoList = document.getElementById('repoList');
    const userId = localStorage.getItem('userId');

    try {
        loading.style.display = 'block';
        repoList.innerHTML = '';
        
        const response = await listRepositories(userId);
        
        if (response.success) {
            loading.style.display = 'none';
            
            if (response.data.items.length === 0) {
                repoList.innerHTML = '<p class="no-repos">No repositories yet. Create your first repository!</p>';
                return;
            }
            
            response.data.items.forEach(repo => {
                const card = createRepoCard(repo);
                repoList.appendChild(card);
            });
        } else {
            throw new Error(response.error || 'Failed to load repositories');
        }
    } catch (error) {
        loading.style.display = 'none';
        showError(error);
    }
}

function createRepoCard(repo) {
    const card = document.createElement('div');
    card.className = 'repo-card';
    
    const createdDate = new Date(repo.created_at);
    const formattedDate = createdDate.toLocaleDateString();
    
    card.innerHTML = `
        <div class="repo-name">${repo.name}</div>
        <div class="repo-meta">Created on ${formattedDate}</div>
        <div class="repo-actions">
            <button class="open-btn" onclick="openRepo(${repo.id})">Open</button>
            <button class="delete-btn" onclick="deleteRepo(${repo.id})">Delete</button>
        </div>
    `;
    
    return card;
}

// Make these functions global for onclick handlers
window.showCreateRepoModal = () => {
    document.getElementById('createRepoModal').classList.add('active');
    document.getElementById('repoName').focus();
};

window.hideCreateRepoModal = () => {
    document.getElementById('createRepoModal').classList.remove('active');
    document.getElementById('createRepoForm').reset();
};

window.createRepository = async (event) => {
    event.preventDefault();
    
    const nameInput = document.getElementById('repoName');
    const name = nameInput.value.trim();
    const userId = localStorage.getItem('userId');
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    
    try {
        submitButton.disabled = true;
        const result = await createRepository(name, userId);
        
        if (result.success) {
            hideCreateRepoModal();
            await loadRepositories();
        } else {
            showError({ message: result.error || 'Failed to create repository' });
        }
    } catch (error) {
        showError(error);
    } finally {
        submitButton.disabled = false;
    }
};

window.openRepo = (repoId) => {
    window.location.href = `repo.html?id=${repoId}`;
};

window.deleteRepo = async (repoId) => {
    if (!confirm('Are you sure you want to delete this repository? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/repos/${repoId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            await loadRepositories();
        } else {
            const data = await response.json();
            throw new Error(data.error || 'Failed to delete repository');
        }
    } catch (error) {
        showError(error);
    }
};

// Make logout function global for onclick handler
window.logout = logout;