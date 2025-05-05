import { requireAuth, showError, syncRepository, logout } from './api.js';

let currentRepoId = null;
let currentSection = 'overview';

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
        
        const response = await fetch(`/api/repos/${currentRepoId}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load repository');
        }
        
        // Update repository name
        document.getElementById('repoName').textContent = data.name;
        document.title = `${data.name} - Git GUI`;
        
        // Load repository stats
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
        const commitsResponse = await fetch(`/api/repos/${currentRepoId}/commits`);
        const commitsData = await commitsResponse.json();
        document.getElementById('commitCount').textContent = commitsData.total || 0;
        
        // Load branch count
        const branchesResponse = await fetch(`/api/repos/${currentRepoId}/branches`);
        const branchesData = await branchesResponse.json();
        document.getElementById('branchCount').textContent = branchesData.total || 0;
        
        // Load file count
        const filesResponse = await fetch(`/api/repos/${currentRepoId}/files`);
        const filesData = await filesResponse.json();
        document.getElementById('fileCount').textContent = filesData.length || 0;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all items
            navItems.forEach(i => i.classList.remove('active'));
            
            // Add active class to clicked item
            item.classList.add('active');
            
            // Get section name and load it
            const section = item.dataset.section;
            loadSection(section);
        });
    });
}

async function loadSection(section) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
    
    // Show selected section
    const sectionElement = document.getElementById(section);
    if (sectionElement) {
        sectionElement.style.display = 'block';
    }
    
    // Load section content if needed
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
    }
    
    currentSection = section;
}

async function loadFiles() {
    const filesSection = document.getElementById('files');
    filesSection.innerHTML = '<div class="loading">Loading files...</div>';
    
    try {
        const response = await fetch(`/api/repos/${currentRepoId}/files`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load files');
        }
        
        // Render files section (to be implemented)
        filesSection.innerHTML = '<h2>Files content here</h2>';
    } catch (error) {
        filesSection.innerHTML = `<div class="error-message">${error.message}</div>`;
    }
}

async function loadCommits() {
    const commitsSection = document.getElementById('commits');
    commitsSection.innerHTML = '<div class="loading">Loading commits...</div>';
    
    try {
        const response = await fetch(`/api/repos/${currentRepoId}/commits`);
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
        const response = await fetch(`/api/repos/${currentRepoId}/branches`);
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
        const response = await fetch(`/api/repos/${currentRepoId}/graph`);
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

// Make functions global for onclick handlers
window.sync = async () => {
    try {
        const userId = localStorage.getItem('userId');
        const result = await syncRepository(currentRepoId, userId);
        
        if (result.success) {
            // Reload repository data after sync
            await loadRepository();
        } else {
            throw new Error(result.error || 'Failed to sync repository');
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