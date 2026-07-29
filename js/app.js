/**
 * Main Application Orchestrator
 * Fetches JSON analysis payload, renders components & triggers animations
 */

document.addEventListener('DOMContentLoaded', () => {
  // Start Neural Loading Sequence
  initLoader(async () => {
    try {
      // Fetch analysis payload
      const response = await fetch('data/analysis.json');
      const data = await response.json();

      // Render Dashboard Content
      populateData(data);
      renderCharts(data);
      
      // Init Animations & Canvas DSP
      initWaveform();
      initSpectrogram();
      initCounters();
      animateGauge(data.system.confidenceScore);
      startTerminal();

    } catch (err) {
      console.error("Failed to load neural data payload:", err);
    }
  });
});

function populateData(data) {
  // 1. Render Acoustics Key-Values
  const acousticsGrid = document.getElementById('acoustics-grid');
  if (acousticsGrid) {
    acousticsGrid.innerHTML = Object.entries(data.acoustics)
      .filter(([_, val]) => typeof val === 'string')
      .map(([key, value]) => `
        <div class="acoustic-item">
          <span class="label">${key.toUpperCase()}</span>
          <span class="val">${value}</span>
        </div>
      `).join('');
  }

  // 2. Render Genres Badges
  const genresContainer = document.getElementById('genres-container');
  if (genresContainer) {
    genresContainer.innerHTML = data.genres.map(g => `
      <span class="genre-tag">${g.name} <strong>${g.weight}%</strong></span>
    `).join('');
  }

  // 3. Render Strengths & Weaknesses
  const strengthsList = document.getElementById('strengths-list');
  if (strengthsList) {
    strengthsList.innerHTML = data.strengths.map(s => `<li>${s}</li>`).join('');
  }

  const weaknessesList = document.getElementById('weaknesses-list');
  if (weaknessesList) {
    weaknessesList.innerHTML = data.weaknesses.map(w => `<li>${w}</li>`).join('');
  }

  // 4. Render AI Report (In Vietnamese)
  const reportBox = document.getElementById('ai-report-box');
  if (reportBox) {
    reportBox.innerHTML = `
      <div>
        <div class="report-section-title">TỔNG QUAN TÍN HIỆU (SUMMARY)</div>
        <p>${data.aiReport.summary}</p>
      </div>
      <div>
        <div class="report-section-title">CHẨN ĐOÁN KỸ THUẬT DSP (TECHNICAL DIAGNOSIS)</div>
        <p>${data.aiReport.technicalDiagnosis}</p>
      </div>
      <div>
        <div class="report-section-title">KHUYẾN NGHỊ CHIẾN LƯỢC (STRATEGIC RECOMMENDATION)</div>
        <p>${data.aiReport.strategicRecommendation}</p>
      </div>
    `;
  }
}
