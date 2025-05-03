// commits.js
import { getCommits } from './api.js';

document.addEventListener("DOMContentLoaded", async () => {
  const commitList = document.querySelector(".commit-list");
  
  try {
    const commits = await getCommits();
    
    if (commits && commits.length > 0) {
      commitList.innerHTML = commits.map(commit => `
        <div class="commit-item">
          <h3>${commit.message}</h3>
          <p class="commit-hash">${commit.hash}</p>
          <div class="commit-meta">
            <span>${commit.author}</span>
            <span>${commit.date}</span>
          </div>
        </div>
      `).join('');
    } else {
      commitList.innerHTML = '<p>No commits found</p>';
    }
  } catch (error) {
    console.error("Error loading commits:", error);
    commitList.innerHTML = '<p>Error loading commits</p>';
  }
});

