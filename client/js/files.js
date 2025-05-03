import { fetchData } from './api.js';

document.addEventListener("DOMContentLoaded", async () => {
  const fileList = document.getElementById("file-list");
  const files = await fetchData("files"); // Get files from the API

  if (files) {
    files.forEach(file => {
      const fileItem = document.createElement("li");
      fileItem.textContent = file.name;
      fileList.appendChild(fileItem);
    });
  } else {
    fileList.innerHTML = "<p>No files found.</p>";
  }
});

