/**
 * Chart.js visualizations driven by real analysis results.
 */

let radarChartInstance, spectralChartInstance, timelineChartInstance;

function destroyChart(instance) {
  if (instance && typeof instance.destroy === 'function') instance.destroy();
}

function renderCharts(data) {
  if (!window.Chart || !data) return;
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";

  const dna = data.dna || {
    energy: data.acoustics?.energy || 0.5,
    rhythm: data.acoustics?.danceability || 0.5,
    brightness: 0.5,
    dynamics: 0.5,
    stereoWidth: 0.5,
    tonality: 0.5
  };

  const radarCanvas = document.getElementById('radarChart');
  if (radarCanvas) {
    destroyChart(radarChartInstance);
    radarChartInstance = new Chart(radarCanvas.getContext('2d'), {
      type: 'radar',
      data: {
        labels: ['Energy', 'Rhythm', 'Brightness', 'Dynamics', 'Stereo Width', 'Tonality'],
        datasets: [{
          label: 'DSP Feature Vector',
          data: [dna.energy, dna.rhythm, dna.brightness, dna.dynamics, dna.stereoWidth, dna.tonality].map(v => Math.round(v * 100)),
          backgroundColor: 'rgba(29, 185, 84, 0.18)',
          borderColor: '#1db954',
          pointBackgroundColor: '#00f0ff',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 650 },
        scales: {
          r: {
            min: 0,
            max: 100,
            angleLines: { color: 'rgba(255,255,255,0.08)' },
            grid: { color: 'rgba(255,255,255,0.08)' },
            pointLabels: { color: '#cbd5e1', font: { size: 11 } },
            ticks: { display: false }
          }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  const spectralCanvas = document.getElementById('spectralChart');
  if (spectralCanvas) {
    destroyChart(spectralChartInstance);
    const fallbackBands = [
      { name: 'sub', value: 7 }, { name: 'bass', value: 19 }, { name: 'lowMid', value: 18 },
      { name: 'mid', value: 28 }, { name: 'presence', value: 21 }, { name: 'air', value: 7 }
    ];
    const bands = data.spectralBands || fallbackBands;
    const nice = { sub: 'Sub <60', bass: 'Bass 60–250', lowMid: 'Low-mid 250–500', mid: 'Mid 500–2k', presence: 'Presence 2–6k', air: 'Air 6–16k' };
    spectralChartInstance = new Chart(spectralCanvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: bands.map(b => nice[b.name] || b.name),
        datasets: [{
          label: 'Spectral energy share',
          data: bands.map(b => b.value),
          backgroundColor: 'rgba(0, 240, 255, 0.38)',
          borderColor: '#00f0ff',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { callback: v => `${v}%` } },
          x: { grid: { display: false } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  const timelineCanvas = document.getElementById('timelineChart');
  if (timelineCanvas) {
    destroyChart(timelineChartInstance);
    const timeline = data.emotionalTimeline || [];
    timelineChartInstance = new Chart(timelineCanvas.getContext('2d'), {
      type: 'line',
      data: {
        labels: timeline.map(item => item.phase),
        datasets: [{
          label: 'Relative section energy',
          data: timeline.map(item => item.intensity),
          borderColor: '#00f0ff',
          backgroundColor: 'rgba(0, 240, 255, 0.08)',
          fill: true,
          tension: 0.35,
          pointRadius: 3,
          pointBackgroundColor: '#1db954'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' } },
          x: { grid: { display: false } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }
}

window.renderCharts = renderCharts;
