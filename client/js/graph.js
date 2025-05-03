//graph.js
import { fetchData } from './api.js';


document.addEventListener("DOMContentLoaded", async () => {
  const graphSVG = document.getElementById("graph-svg");
  const graphData = await fetchData("graph-data"); // Get graph data from the API

  if (graphData) {
    graphData.nodes.forEach(node => {
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", node.x);
      circle.setAttribute("cy", node.y);
      circle.setAttribute("r", 5);
      circle.setAttribute("fill", "blue");
      graphSVG.appendChild(circle);
    });

    graphData.links.forEach(link => {
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", link.startX);
      line.setAttribute("y1", link.startY);
      line.setAttribute("x2", link.endX);
      line.setAttribute("y2", link.endY);
      line.setAttribute("stroke", "black");
      graphSVG.appendChild(line);
    });
  } else {
    graphSVG.innerHTML = "<p>No graph data found.</p>";
  }
});
