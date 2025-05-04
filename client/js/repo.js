// js/repo.js
// Handles file explorer, editor, working tree, staging, and commit UI logic

const repoId = new URLSearchParams(window.location.search).get('repo_id');
let selectedFileId = null;
let userId = 1; // TODO: Replace with real user session

async function loadFileList() {
    const res = await apiGet(`/api/repos/${repoId}/files`);
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';
    res.forEach(f => {
        const li = document.createElement('li');
        li.className = 'file-list-item';
        li.textContent = f.filename;
        li.onclick = () => selectFile(f.id, f.filename);
        fileList.appendChild(li);
    });
}

async function selectFile(fileId, filename) {
    selectedFileId = fileId;
    const res = await apiGet(`/api/file/${fileId}`);
    const editor = document.getElementById('fileEditor');
    editor.value = res.content || '';
    editor.disabled = false;
    document.getElementById('saveBtn').disabled = false;
    document.getElementById('saveBtn').onclick = () => saveFile(fileId, filename);
    // Highlight selected file
    document.querySelectorAll('.file-list-item').forEach(el => el.classList.remove('active'));
    [...document.getElementById('fileList').children].find(li => li.textContent === filename).classList.add('active');
}

async function saveFile(fileId, filename) {
    const content = document.getElementById('fileEditor').value;
    await apiPut(`/api/file/${fileId}`, { content, user_id: userId });
    await updateWorkingTree();
}

async function updateWorkingTree() {
    // Fetch working tree files for this user/repo
    const res = await apiGet(`/api/working-tree?user_id=${userId}&repo_id=${repoId}`);
    const list = document.getElementById('workingTreeList');
    list.innerHTML = '';
    res.forEach(f => {
        const li = document.createElement('li');
        li.textContent = f.file_path;
        const btn = document.createElement('button');
        btn.textContent = 'Add';
        btn.onclick = () => stageFile(f.file_path);
        li.appendChild(btn);
        list.appendChild(li);
    });
    await updateStaging();
}

async function stageFile(filePath) {
    await apiPost('/api/stage', { user_id: userId, repo_id: repoId, file_path: filePath });
    await updateWorkingTree();
}

async function updateStaging() {
    // Fetch staging area files for this user/repo
    const res = await apiGet(`/api/staging?user_id=${userId}&repo_id=${repoId}`);
    const list = document.getElementById('stagingList');
    list.innerHTML = '';
    res.forEach(f => {
        const li = document.createElement('li');
        li.textContent = f.file_path;
        list.appendChild(li);
    });
    document.getElementById('commitBtn').disabled = res.length === 0;
    await updateCommitted();
}

async function commitFiles() {
    await apiPost('/api/commit', { user_id: userId, repo_id: repoId });
    await updateWorkingTree();
}

async function updateCommitted() {
    // Fetch recently committed files (for demo, just show staged files as committed)
    const res = await apiGet(`/api/committed?user_id=${userId}&repo_id=${repoId}`);
    const list = document.getElementById('committedList');
    list.innerHTML = '';
    res.forEach(f => {
        const li = document.createElement('li');
        li.textContent = f.file_path;
        list.appendChild(li);
    });
}

document.getElementById('saveBtn').onclick = () => {
    if (selectedFileId) saveFile(selectedFileId);
};
document.getElementById('commitBtn').onclick = commitFiles;

// Initial load
loadFileList();
updateWorkingTree();