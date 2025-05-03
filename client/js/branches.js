// branches.js
import { fetchData } from './api.js';

document.addEventListener("DOMContentLoaded", async () => {
  const branchList = document.getElementById("branch-list");
  const branches = await fetchData("branches"); // Get branches from the API

  if (branches) {
    branches.forEach(branch => {
      const branchItem = document.createElement("li");
      branchItem.textContent = branch.name;
      branchList.appendChild(branchItem);
    });
  } else {
    branchList.innerHTML = "<p>No branches found.</p>";
  }
});

