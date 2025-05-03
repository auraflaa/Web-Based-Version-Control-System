// api.js

const API_URL = "https://your-api-endpoint.com"; // Replace with your API base URL

// Helper function to fetch data from API
async function fetchData(endpoint) {
  try {
    const response = await fetch(`${API_URL}/${endpoint}`);
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch data:", error);
    return null;
  }
}
async function getCommits() {
  const data = await fetchData('/api/commits');
  return data;  // Adjust data structure as needed
}

// Function to fetch branches data
async function getBranches() {
  const data = await fetchData('/api/branches');
  return data;  // Adjust data structure as needed
}

// Function to fetch files data
async function getFiles() {
  const data = await fetchData('/api/files');
  return data;  // Adjust data structure as needed
}

// Function to fetch graph data (for graph visualization)
async function getGraphData() {
  const data = await fetchData('/api/graph-data');
  return data;  // Adjust data structure as needed
}

// Export functions for use in other files
export { getCommits, getBranches, getFiles, getGraphData };

