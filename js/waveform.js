/**
 * Waveform & spectrogram renderer.
 * Falls back to a subtle demo state until a real file has been analysed.
 */

function initWaveform() {
  const demo = Array.from({ length: 120 }, (_, i) => 0.12 + Math.abs(Math.sin(i * 0.19)) * 0.32);
  renderWaveform(demo, true);
}

function renderWaveform(peaks, isDemo = false) {
  const svg = document.getElementById('svg-waveform');
  if (!svg || !Array.isArray(peaks) || !peaks.length) return;

  const width = 1000;
  const mid = 60;
  const maxAmp = 48;
  const top = [];
  const bottom = [];

  peaks.forEach((value, i) => {
    const x = peaks.length === 1 ? 0 : (i / (peaks.length - 1)) * width;
    const amp = Math.max(1.5, Math.min(1, value) * maxAmp);
    top.push(`${x.toFixed(2)},${(mid - amp).toFixed(2)}`);
    bottom.push(`${x.toFixed(2)},${(mid + amp).toFixed(2)}`);
  });

  const polygon = [...top, ...bottom.reverse()].join(' ');
  svg.innerHTML = `
    <line x1="0" y1="60" x2="1000" y2="60" stroke="rgba(255,255,255,.08)" stroke-width="1" />
    <polygon points="${polygon}" fill="${isDemo ? 'rgba(29,185,84,.15)' : 'rgba(29,185,84,.28)'}" stroke="#1db954" stroke-width="1.3" />
  `;
}

function initSpectrogram() {
  const canvas = document.getElementById('spectrogramCanvas');
  if (!canvas) return;
  resizeSpectrogramCanvas(canvas);
  drawSpectrogram(canvas, createDemoSpectrogram());
  window.addEventListener('resize', () => {
    resizeSpectrogramCanvas(canvas);
    if (window.__LMN_LAST_SPECTROGRAM__) drawSpectrogram(canvas, window.__LMN_LAST_SPECTROGRAM__);
  });
}

function resizeSpectrogramCanvas(canvas) {
  const parent = canvas.parentElement;
  if (!parent) return;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(parent.clientWidth * ratio));
  canvas.height = Math.max(1, Math.floor(parent.clientHeight * ratio));
}

function renderSpectrogram(matrix) {
  const canvas = document.getElementById('spectrogramCanvas');
  if (!canvas || !Array.isArray(matrix) || !matrix.length) return;
  window.__LMN_LAST_SPECTROGRAM__ = matrix;
  resizeSpectrogramCanvas(canvas);
  drawSpectrogram(canvas, matrix);
}

function drawSpectrogram(canvas, matrix) {
  const ctx = canvas.getContext('2d');
  const cols = matrix.length;
  const rows = matrix[0]?.length || 0;
  if (!rows) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#050608';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const cellW = canvas.width / cols;
  const cellH = canvas.height / rows;

  for (let x = 0; x < cols; x++) {
    for (let y = 0; y < rows; y++) {
      const energy = Math.max(0, Math.min(1, matrix[x][y] || 0));
      const hue = 164 + energy * 35;
      const light = 8 + energy * 54;
      ctx.fillStyle = `hsl(${hue} 88% ${light}% / ${0.28 + energy * 0.72})`;
      ctx.fillRect(
        x * cellW,
        canvas.height - (y + 1) * cellH,
        Math.ceil(cellW) + 0.5,
        Math.ceil(cellH) + 0.5
      );
    }
  }
}

function createDemoSpectrogram() {
  return Array.from({ length: 48 }, (_, x) =>
    Array.from({ length: 32 }, (_, y) => {
      const ridge = Math.exp(-Math.pow((y - 8 - 3 * Math.sin(x * 0.22)) / 4.5, 2));
      const harmonic = Math.exp(-Math.pow((y - 18 - 2 * Math.cos(x * 0.14)) / 6, 2)) * 0.45;
      return Math.min(1, (ridge + harmonic) * (0.45 + 0.25 * Math.sin(x * 0.31) ** 2));
    })
  );
}

window.renderWaveform = renderWaveform;
window.renderSpectrogram = renderSpectrogram;
