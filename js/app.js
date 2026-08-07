/**
 * LMNotebook Neural Audio — Application Orchestrator
 * Loads demo data, then replaces it with real DSP measurements after upload.
 */

let selectedAudioFile = null;
let lastAnalysisResult = null;
let analyzerInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  initLoader(async () => {
    let demoData = null;
    try {
      const response = await fetch('data/analysis.json');
      demoData = await response.json();
    } catch (err) {
      console.warn('Demo payload unavailable:', err);
    }

    if (demoData) {
      const normalized = normalizeLegacyData(demoData);
      populateData(normalized, false);
      renderCharts(normalized);
    }

    initWaveform();
    initSpectrogram();
    startTerminal();
    setupAudioAnalyzerUI();
    lucide.createIcons();
  });
});

function setupAudioAnalyzerUI() {
  const fileInput = document.getElementById('audio-file-input');
  const chooseBtn = document.getElementById('choose-audio-btn');
  const analyzeBtn = document.getElementById('analyze-audio-btn');
  const exportBtn = document.getElementById('export-json-btn');
  const dropZone = document.getElementById('drop-zone');

  if (!fileInput || !analyzeBtn || !dropZone) return;
  analyzerInstance = new LMNAudioAnalyzer();

  chooseBtn?.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', () => {
    if (fileInput.files?.[0]) setSelectedFile(fileInput.files[0]);
  });

  ['dragenter', 'dragover'].forEach(type => {
    dropZone.addEventListener(type, e => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(type => {
    dropZone.addEventListener(type, e => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
    });
  });

  dropZone.addEventListener('drop', e => {
    const file = e.dataTransfer?.files?.[0];
    if (file) setSelectedFile(file);
  });

  analyzeBtn.addEventListener('click', runAnalysis);
  exportBtn?.addEventListener('click', exportLastAnalysis);
}

function setSelectedFile(file) {
  const ext = (file.name.split('.').pop() || '').toLowerCase();
  if (!['mp3', 'wav'].includes(ext) && !['audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/wave'].includes(file.type)) {
    setStatus(0, 'Format non supporté — MP3 ou WAV uniquement.', true);
    selectedAudioFile = null;
    document.getElementById('analyze-audio-btn').disabled = true;
    return;
  }

  selectedAudioFile = file;
  const nameEl = document.getElementById('selected-file-name');
  if (nameEl) nameEl.textContent = `${file.name} • ${(file.size / 1048576).toFixed(2)} MB`;
  const analyzeBtn = document.getElementById('analyze-audio-btn');
  if (analyzeBtn) analyzeBtn.disabled = false;
  setStatus(0, 'Fichier prêt. Lance le scan DSP.', false);
}

async function runAnalysis() {
  if (!selectedAudioFile || !analyzerInstance) return;
  const analyzeBtn = document.getElementById('analyze-audio-btn');
  const chooseBtn = document.getElementById('choose-audio-btn');
  const exportBtn = document.getElementById('export-json-btn');

  if (analyzeBtn) analyzeBtn.disabled = true;
  if (chooseBtn) chooseBtn.disabled = true;
  if (exportBtn) exportBtn.disabled = true;
  setDataOrigin('ANALYSIS RUNNING', 'Mesures locales Web Audio API + FFT');

  try {
    const result = await analyzerInstance.analyze(selectedAudioFile, (percent, step) => {
      setStatus(percent, step, false);
    });
    lastAnalysisResult = result;
    populateData(result, true);
    renderCharts(result);
    renderWaveform(result.waveformPeaks);
    renderSpectrogram(result.spectrogram);
    animateGauge(result.system.confidenceScore);
    setStatus(100, 'Analyse terminée — données réelles affichées.', false);
    setDataOrigin('REAL LOCAL DSP', `${result.file.name} • ${result.file.duration} • ${result.file.sampleRate} Hz`);
    if (exportBtn) exportBtn.disabled = false;
    lucide.createIcons();
  } catch (err) {
    console.error(err);
    setStatus(0, err.message || 'Échec de l’analyse audio.', true);
    setDataOrigin('ANALYSIS ERROR', 'Le fichier n’a pas pu être traité');
  } finally {
    if (analyzeBtn) analyzeBtn.disabled = false;
    if (chooseBtn) chooseBtn.disabled = false;
  }
}

function populateData(data, isReal) {
  updateTopMetrics(data, isReal);

  const acousticsGrid = document.getElementById('acoustics-grid');
  if (acousticsGrid && data.acoustics) {
    const preferredOrder = [
      'tempo', 'tempoConfidence', 'key', 'camelot', 'keyConfidence',
      'rms', 'peak', 'crestFactor', 'clipping', 'dcOffset', 'zeroCrossingRate',
      'spectralCentroid', 'spectralRolloff', 'spectralFlatness', 'spectralFlux',
      'stereoWidth', 'stereoCorrelation', 'stereoBalance', 'sampleRate', 'channels', 'duration'
    ];
    const entries = preferredOrder
      .filter(key => data.acoustics[key] !== undefined)
      .map(key => [key, data.acoustics[key]]);

    acousticsGrid.innerHTML = entries.map(([key, value]) => `
      <div class="acoustic-item">
        <span class="label">${humanizeKey(key)}</span>
        <span class="val">${escapeHtml(String(value))}</span>
      </div>
    `).join('');
  }

  const genresContainer = document.getElementById('genres-container');
  if (genresContainer) {
    genresContainer.innerHTML = (data.genres || []).map(g => `
      <span class="genre-tag">${escapeHtml(g.name)} <strong>${Math.round(g.weight)}%</strong></span>
    `).join('');
  }

  const strengthsList = document.getElementById('strengths-list');
  if (strengthsList) strengthsList.innerHTML = (data.strengths || []).map(s => `<li>${escapeHtml(s)}</li>`).join('');

  const weaknessesList = document.getElementById('weaknesses-list');
  if (weaknessesList) weaknessesList.innerHTML = (data.weaknesses || []).map(w => `<li>${escapeHtml(w)}</li>`).join('');

  const reportBox = document.getElementById('ai-report-box');
  if (reportBox && data.aiReport) {
    reportBox.innerHTML = `
      <div>
        <div class="report-section-title">SIGNAL SUMMARY</div>
        <p>${escapeHtml(data.aiReport.summary || '')}</p>
      </div>
      <div>
        <div class="report-section-title">DSP DIAGNOSIS</div>
        <p>${escapeHtml(data.aiReport.technicalDiagnosis || '')}</p>
      </div>
      <div>
        <div class="report-section-title">NEXT ANALYSIS LAYER</div>
        <p>${escapeHtml(data.aiReport.strategicRecommendation || '')}</p>
      </div>
    `;
  }

  updateFileTech(data.file, isReal);
  animateGauge(data.system?.confidenceScore || 0);
}

function updateTopMetrics(data, isReal) {
  const a = data.acoustics || {};
  const values = {
    'metric-tempo': a.tempo || '—',
    'metric-key': a.key || '—',
    'metric-rms': a.rms || '—',
    'metric-peak': a.peak || '—',
    'metric-crest': a.crestFactor || a.dynamicRange || '—',
    'metric-stereo': a.stereoWidth || '—',
    'metric-clipping': a.clipping || '—'
  };
  Object.entries(values).forEach(([id, value]) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  });

  document.querySelectorAll('.metric-card').forEach(card => {
    card.classList.toggle('measured', isReal);
  });
}

function updateFileTech(file, isReal) {
  const grid = document.getElementById('file-tech-grid');
  if (!grid) return;
  if (!file) {
    grid.innerHTML = `
      <div class="file-tech"><span>Source</span><strong>Demo payload</strong></div>
      <div class="file-tech"><span>Mode</span><strong>Preview</strong></div>
    `;
    return;
  }
  grid.innerHTML = [
    ['File', file.name],
    ['Format', file.format || file.type || '—'],
    ['Duration', file.duration || '—'],
    ['Sample rate', file.sampleRate ? `${file.sampleRate} Hz` : '—'],
    ['Channels', file.channels ?? '—'],
    ['Size', file.sizeMB ? `${file.sizeMB} MB` : '—'],
    ['Origin', isReal ? 'Local browser DSP' : 'Demo'],
    ['Privacy', isReal ? 'File stays on device' : '—']
  ].map(([label, value]) => `
    <div class="file-tech"><span>${escapeHtml(label)}</span><strong title="${escapeHtml(String(value))}">${escapeHtml(String(value))}</strong></div>
  `).join('');
}

function setStatus(percent, text, isError) {
  const fill = document.getElementById('analysis-progress-fill');
  const pct = document.getElementById('analysis-percent');
  const step = document.getElementById('analysis-step');
  const p = Math.max(0, Math.min(100, Number(percent) || 0));
  if (fill) fill.style.width = `${p}%`;
  if (pct) pct.textContent = `${Math.round(p)}%`;
  if (step) {
    step.textContent = text || '';
    step.style.color = isError ? 'var(--danger-red)' : '';
  }
}

function setDataOrigin(tag, description) {
  const tagEl = document.getElementById('data-origin-tag');
  const textEl = document.getElementById('data-origin-text');
  if (tagEl) tagEl.textContent = tag;
  if (textEl) textEl.textContent = description;
}

function exportLastAnalysis() {
  if (!lastAnalysisResult) return;
  const json = JSON.stringify(lastAnalysisResult, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const base = (lastAnalysisResult.file?.name || 'audio-analysis').replace(/\.[^.]+$/, '').replace(/[^a-z0-9_-]+/gi, '-');
  a.href = url;
  a.download = `${base}-LMN-analysis.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function normalizeLegacyData(data) {
  if (data.dna) return data;
  const ac = data.acoustics || {};
  const stereoWidth = parseFloat(ac.stereoWidth) || 100;
  const demo = {
    ...data,
    source: 'demo-payload',
    dna: {
      energy: Number(ac.energy ?? 0.72),
      rhythm: Number(ac.danceability ?? 0.68),
      brightness: 0.58,
      dynamics: 0.52,
      stereoWidth: Math.min(1, stereoWidth / 160),
      tonality: Number(ac.chromaEnergy ?? 0.72)
    },
    spectralBands: [
      { name: 'sub', value: 8 }, { name: 'bass', value: 19 }, { name: 'lowMid', value: 15 },
      { name: 'mid', value: 27 }, { name: 'presence', value: 23 }, { name: 'air', value: 8 }
    ],
    file: null
  };
  setDataOrigin('DEMO DATA', 'Upload un MP3/WAV pour remplacer ces valeurs');
  return demo;
}

function humanizeKey(key) {
  return key
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, s => s.toUpperCase())
    .trim();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}
