/**
 * Chart.js Visualizations (Radar, Similarity Map, Timeline)
 */

let radarChartInstance, similarityChartInstance, timelineChartInstance;

function renderCharts(data) {
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";

  // 1. Radar Chart (Sonic DNA)
  const radarCtx = document.getElementById('radarChart').getContext('2d');
  radarChartInstance = new Chart(radarCtx, {
    type: 'radar',
    data: {
      labels: ['Energy', 'Danceability', 'Valence', 'Acousticness', 'Speechiness', 'Instrumentalness'],
      datasets: [{
        label: 'Audio Feature Vector',
        data: [
          data.acoustics.energy * 100,
          data.acoustics.danceability * 100,
          data.acoustics.valence * 100,
          data.acoustics.acousticness * 100,
          data.acoustics.speechiness * 100,
          data.acoustics.instrumentalness * 100
        ],
        backgroundColor: 'rgba(29, 185, 84, 0.2)',
        borderColor: '#1db954',
        pointBackgroundColor: '#00f0ff',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          angleLines: { color: 'rgba(255,255,255,0.08)' },
          grid: { color: 'rgba(255,255,255,0.08)' },
          pointLabels: { color: '#cbd5e1', font: { size: 11 } },
          ticks: { display: false }
        }
      },
      plugins: { legend: { display: false } }
    }
  });

  // 2. Similarity Clustering Scatter Map
  const simCtx = document.getElementById('similarityChart').getContext('2d');
  const scatterPoints = Array.from({ length: 40 }, () => ({
    x: (Math.random() - 0.5) * 10,
    y: (Math.random() - 0.5) * 10
  }));

  similarityChartInstance = new Chart(simCtx, {
    type: 'scatter',
    data: {
      datasets: [
        {
          label: 'SHINOBIWAN Tracks',
          data: [
            { x: 1.2, y: 2.3 }, { x: 1.8, y: 2.9 }, { x: 2.1, y: 1.9 },
            { x: -1.5, y: -2.1 }, { x: -0.9, y: -1.8 }
          ],
          backgroundColor: '#1db954',
          pointRadius: 7
        },
        {
          label: 'Latent Cluster References',
          data: scatterPoints,
          backgroundColor: 'rgba(255, 255, 255, 0.2)',
          pointRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' } }
      },
      plugins: { legend: { display: false } }
    }
  });

  // 3. Emotional Timeline
  const timeCtx = document.getElementById('timelineChart').getContext('2d');
  timelineChartInstance = new Chart(timeCtx, {
    type: 'line',
    data: {
      labels: data.emotionalTimeline.map(item => item.phase),
      datasets: [{
        label: 'Emotional Intensity',
        data: data.emotionalTimeline.map(item => item.intensity),
        borderColor: '#00f0ff',
        backgroundColor: 'rgba(0, 240, 255, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 5,
        pointBackgroundColor: '#7000ff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, max: 100 },
        x: { grid: { display: false } }
      },
      plugins: { legend: { display: false } }
    }
  });
}
