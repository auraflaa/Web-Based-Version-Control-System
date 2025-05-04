// js/repo.js
// Handles file explorer, editor, working tree, staging, and commit UI logic

const repoId = new URLSearchParams(window.location.search).get('repo_id');
const userId = localStorage.getItem('userId') || 1; // Fallback for testing

async function loadFileList() {
    const res = await fetchAPI(`/api/repos/${repoId}/files?user_id=${userId}`);
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';
    
    res.forEach(f => {
        const li = document.createElement('li');
        li.className = 'file-list-item';
        
        const nameSpan = document.createElement('span');
        nameSpan.textContent = f.name;
        nameSpan.onclick = () => selectFile(f.name);
        
        const actions = document.createElement('div');
        actions.className = 'file-actions';
        
        const editBtn = document.createElement('button');
        editBtn.textContent = 'Edit';
        editBtn.onclick = () => selectFile(f.name);
        
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete';
        deleteBtn.className = 'delete-btn';
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            deleteFile(f.name);
        };
        
        actions.appendChild(editBtn);
        actions.appendChild(deleteBtn);
        
        li.appendChild(nameSpan);
        li.appendChild(actions);
        fileList.appendChild(li);
    });
}

async function createFile() {
    const nameInput = document.getElementById('newFileName');
    const filename = nameInput.value.trim();
    
    if (!filename) {
        alert('Please enter a file name');
        return;
    }
    
    try {
        await fetchAPI(`/api/repos/${repoId}/files`, {
            method: 'POST',
            body: JSON.stringify({
                filename,
                content: '',
                user_id: userId
            })
        });
        
        nameInput.value = '';
        await loadFileList();
        await updateWorkingTree();
        
    } catch (error) {
        showError(error);
    }
}

async function deleteFile(filename) {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) {
        return;
    }
    
    try {
        await fetchAPI(`/api/repos/${repoId}/files/${encodeURIComponent(filename)}?user_id=${userId}`, {
            method: 'DELETE'
        });
        
        await loadFileList();
        await updateWorkingTree();
        
        // Clear editor if deleted file was selected
        const editor = document.getElementById('fileEditor');
        if (editor.dataset.filename === filename) {
            editor.value = '';
            editor.disabled = true;
            document.getElementById('saveBtn').disabled = true;
            delete editor.dataset.filename;
        }
        
    } catch (error) {
        showError(error);
    }
}

async function selectFile(filename) {
    try {
        const response = await fetchAPI(`/api/repos/${repoId}/files/${encodeURIComponent(filename)}?user_id=${userId}`);
        const editor = document.getElementById('fileEditor');
        editor.value = response.content || '';
        editor.disabled = false;
        editor.dataset.filename = filename;
        document.getElementById('saveBtn').disabled = false;
        
        // Highlight selected file
        document.querySelectorAll('.file-list-item').forEach(el => {
            if (el.querySelector('span').textContent === filename) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });
        
    } catch (error) {
        showError(error);
    }
}

async function saveFile() {
    const editor = document.getElementById('fileEditor');
    const filename = editor.dataset.filename;
    if (!filename) return;
    
    try {
        await fetchAPI(`/api/repos/${repoId}/files/${encodeURIComponent(filename)}`, {
            method: 'PUT',
            body: JSON.stringify({
                content: editor.value,
                user_id: userId
            })
        });
        
        await updateWorkingTree();
        
    } catch (error) {
        showError(error);
    }
}

async function updateWorkingTree() {
    try {
        const res = await fetchAPI(`/api/working-tree?user_id=${userId}&repo_id=${repoId}`);
        const list = document.getElementById('workingTreeList');
        list.innerHTML = '';
        
        res.forEach(f => {
            const li = document.createElement('li');
            li.textContent = `${f.file_path} (${f.status})`;
            
            const stageBtn = document.createElement('button');
            stageBtn.textContent = 'Stage';
            stageBtn.onclick = () => stageFile(f.file_path);
            
            li.appendChild(stageBtn);
            list.appendChild(li);
        });
        
        await updateStaging();
        
    } catch (error) {
        showError(error);
    }
}

async function stageFile(filePath) {
    try {
        await fetchAPI('/api/stage', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                repo_id: repoId,
                file_path: filePath
            })
        });
        
        await updateWorkingTree();
        
    } catch (error) {
        showError(error);
    }
}

async function updateStaging() {
    try {
        const res = await fetchAPI(`/api/staging?user_id=${userId}&repo_id=${repoId}`);
        const list = document.getElementById('stagingList');
        list.innerHTML = '';
        
        res.forEach(f => {
            const li = document.createElement('li');
            li.textContent = f.file_path;
            list.appendChild(li);
        });
        
        document.getElementById('commitBtn').disabled = res.length === 0;
        
    } catch (error) {
        showError(error);
    }
}

async function commitFiles() {
    const message = prompt('Enter commit message:');
    if (!message) return;
    
    try {
        await fetchAPI('/api/commit', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                repo_id: repoId,
                message
            })
        });
        
        await updateWorkingTree();
        
    } catch (error) {
        showError(error);
    }
}

// Event listeners
document.getElementById('saveBtn').onclick = saveFile;
document.getElementById('commitBtn').onclick = commitFiles;

// Initial load
loadFileList();
updateWorkingTree();