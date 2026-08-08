(() => {
  'use strict';

  const DEFAULT_API = 'http://127.0.0.1:8000';
  const LOCAL_UI = 'http://127.0.0.1:8008';
  let selectedFile = null;
  let apiBase = DEFAULT_API;
  let connected = false;
  let neuralReady = false;
  let neuralModel = null;
  let stemsReady = false;
  let stemsNodeLabel = null;

  document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('audio-file-input');
    const dropZone = document.getElementById('drop-zone');
    const connectBtn = document.getElementById('v2-connect-btn');
    const deepBtn = document.getElementById('deep-analyze-audio-btn');
    const apiInput = document.getElementById('v2-api-url');

    if (!connectBtn || !deepBtn || !apiInput) return;
    const stemsBtn = ensureStemsButton(deepBtn);
    apiInput.value = DEFAULT_API;

    input?.addEventListener('change', () => {
      if (input.files?.[0]) {
        selectedFile = input.files[0];
        syncActionButtons(deepBtn, stemsBtn);
      }
    });

    dropZone?.addEventListener('drop', event => {
      const file = event.dataTransfer?.files?.[0];
      if (file) {
        selectedFile = file;
        syncActionButtons(deepBtn, stemsBtn);
      }
    });

    connectBtn.addEventListener('click', async () => {
      apiBase = normalizeBase(apiInput.value || DEFAULT_API);
      await testConnection();
      syncActionButtons(deepBtn, stemsBtn);
    });

    deepBtn.addEventListener('click', runDeepScan);
    stemsBtn.addEventListener('click', runStemsScan);

    if (isLocalRuntimePage()) {
      setV2Status('V2 CONNECTING', 'Runtime local détecté • connexion automatique au moteur Deep Audio V2…');
      window.setTimeout(async () => {
        apiBase = DEFAULT_API;
        await testConnection();
        syncActionButtons(deepBtn, stemsBtn);
      }, 350);
    } else if (isGitHubPages()) {
      setV2Status('V2 LOCAL', 'Le Deep Scan V2 s’utilise depuis la page locale ouverte automatiquement par LMNotebook_START.cmd.');
    }
  });

  function ensureStemsButton(deepBtn) {
    let button = document.getElementById('stems-analyze-audio-btn');
    if (button) return button;
    button = document.createElement('button');
    button.id = 'stems-analyze-audio-btn';
    button.className = 'secondary-btn stems-btn';
    button.type = 'button';
    button.disabled = true;
    button.innerHTML = '<i data-lucide="split"></i> Stems V2-D';
    deepBtn.insertAdjacentElement('afterend', button);
    window.lucide?.createIcons?.();
    return button;
  }

  function normalizeBase(value) {
    return String(value).trim().replace(/\/+$/, '');
  }

  function isLocalRuntimePage() {
    return ['127.0.0.1', 'localhost'].includes(location.hostname) && location.port === '8008';
  }

  function isGitHubPages() {
    return location.hostname.endsWith('github.io');
  }

  function isLoopbackApi() {
    return apiBase.startsWith('http://127.0.0.1') || apiBase.startsWith('http://localhost');
  }

  function syncActionButtons(deepBtn, stemsBtn) {
    if (deepBtn) deepBtn.disabled = !(selectedFile && connected);
    if (stemsBtn) stemsBtn.disabled = !(selectedFile && connected && stemsReady);
  }

  async function testConnection() {
    setV2Status('CONNECTING', 'Connexion au nœud Deep Audio V2…');
    const deepBtn = document.getElementById('deep-analyze-audio-btn');
    const stemsBtn = document.getElementById('stems-analyze-audio-btn');
    try {
      const healthResponse = await fetch(`${apiBase}/api/health`, { method: 'GET', cache: 'no-store' });
      if (!healthResponse.ok) throw new Error(`HTTP ${healthResponse.status}`);
      const health = await healthResponse.json();

      let cluster = null;
      try {
        const clusterResponse = await fetch(`${apiBase}/api/cluster`, { method: 'GET', cache: 'no-store' });
        if (clusterResponse.ok) cluster = await clusterResponse.json();
      } catch (_) {}

      connected = true;
      neuralReady = Boolean(health.neural?.ready);
      neuralModel = health.neural?.model_id || null;
      const workers = cluster?.workers || [];
      const stemWorker = workers.find(worker => worker.online && worker.stems?.ready);
      stemsReady = Boolean(health.stems?.ready || stemWorker);
      stemsNodeLabel = stemWorker?.node_name || (health.stems?.ready ? health.node_name : null);

      renderV2Health(health, cluster);
      const layers = [neuralReady ? 'NEURAL' : null, stemsReady ? 'STEMS' : null].filter(Boolean).join(' + ');
      setV2Status(
        layers ? `V2 + ${layers}` : (health.status === 'ok' ? 'V2 ONLINE' : 'V2 DEGRADED'),
        stemsReady
          ? `${health.node_name || 'Deep Audio node'} • Neural CUDA ${neuralReady ? 'READY' : 'WAIT'} • Demucs routable vers ${stemsNodeLabel}`
          : (neuralReady
            ? `${health.node_name || 'Deep Audio node'} • CUDA ${health.neural?.cuda_runtime || 'READY'} • ${health.neural?.device_name || 'GPU'}`
            : `${health.node_name || 'Deep Audio node'} • V2-A active • GPU layers en attente`)
      );
    } catch (error) {
      connected = false;
      neuralReady = false;
      stemsReady = false;
      stemsNodeLabel = null;
      renderV2Offline(error);
      setV2Status('V2 OFFLINE', explainConnectionError(error), true);
    }
    syncActionButtons(deepBtn, stemsBtn);
  }

  async function runDeepScan() {
    if (!selectedFile || !connected) return;
    const deepBtn = document.getElementById('deep-analyze-audio-btn');
    const stemsBtn = document.getElementById('stems-analyze-audio-btn');
    const v1Btn = document.getElementById('analyze-audio-btn');
    setBusy(true, deepBtn, stemsBtn, v1Btn);

    setV2Status(
      neuralReady ? 'NEURAL SCAN' : 'DEEP SCAN',
      neuralReady
        ? `V2-A + CLAP CUDA • ${neuralModel || 'modèle neural'} • analyse mastering + compréhension musicale…`
        : 'Upload temporaire vers le nœud V2 • FFmpeg / BS.1770 / EBU R128…'
    );
    setDeepProgress(12);

    try {
      const form = new FormData();
      form.append('file', selectedFile, selectedFile.name);
      setDeepProgress(28);
      const response = await fetch(`${apiBase}/api/analyze?neural=true`, { method: 'POST', body: form });
      setDeepProgress(86);
      if (!response.ok) throw new Error(await responseError(response));

      const result = await response.json();
      setDeepProgress(100);
      renderV2Result(result);
      if (result.neural) {
        neuralReady = true;
        setV2Status('V2 NEURAL', `${selectedFile.name} • Mastering + Neural Music Understanding terminés`);
      } else {
        const warning = result.warnings?.[0];
        setV2Status('V2 MEASURED', `${selectedFile.name} • Mastering terminé${warning ? ' • Neural indisponible' : ''}`);
      }
    } catch (error) {
      setDeepProgress(0);
      setV2Status('V2 ERROR', error.message || 'Deep Scan failed', true);
    } finally {
      setBusy(false, deepBtn, stemsBtn, v1Btn);
      syncActionButtons(deepBtn, stemsBtn);
    }
  }

  async function runStemsScan() {
    if (!selectedFile || !connected || !stemsReady) return;
    const deepBtn = document.getElementById('deep-analyze-audio-btn');
    const stemsBtn = document.getElementById('stems-analyze-audio-btn');
    const v1Btn = document.getElementById('analyze-audio-btn');
    setBusy(true, deepBtn, stemsBtn, v1Btn);

    setV2Status('STEM SPLIT', `Demucs htdemucs • routage GPU vers ${stemsNodeLabel || 'meilleur nœud'} • première exécution = téléchargement possible du modèle…`);
    setDeepProgress(8);

    try {
      const form = new FormData();
      form.append('file', selectedFile, selectedFile.name);
      setDeepProgress(18);
      const response = await fetch(`${apiBase}/api/stems`, { method: 'POST', body: form });
      setDeepProgress(90);
      if (!response.ok) throw new Error(await responseError(response));

      const result = await response.json();
      setDeepProgress(100);
      renderStemsResult(result);
      const node = result.compute?.node_name || result.separation?.device || 'GPU';
      setV2Status('V2-D STEMS', `${selectedFile.name} • 4 stems séparés et mesurés sur ${node}`);
      await testConnection();
    } catch (error) {
      setDeepProgress(0);
      setV2Status('STEMS ERROR', error.message || 'Stem separation failed', true);
    } finally {
      setBusy(false, deepBtn, stemsBtn, v1Btn);
      syncActionButtons(deepBtn, stemsBtn);
    }
  }

  function setBusy(busy, ...buttons) {
    buttons.filter(Boolean).forEach(button => { button.disabled = busy; });
  }

  async function responseError(response) {
    try {
      const payload = await response.json();
      return payload.detail || `HTTP ${response.status}`;
    } catch (_) {
      return `HTTP ${response.status}`;
    }
  }

  function renderV2Health(health, cluster) {
    const panel = document.getElementById('v2-node-grid');
    if (!panel) return;
    const localGpus = health.gpus || [];
    const workers = cluster?.workers || [];
    const workerGpus = workers.flatMap(worker => worker.gpus || []);
    const neural = health.neural || {};
    const localStems = health.stems || {};
    const stemWorker = workers.find(worker => worker.online && worker.stems?.ready);
    const cards = [
      metric('Node', health.node_name || '—', health.node_role || 'backend'),
      metric('FFmpeg', health.ffmpeg?.ffmpeg && health.ffmpeg?.ffprobe ? 'READY' : 'MISSING', 'V2-A mastering'),
      metric('Local GPUs', String(localGpus.length), localGpus.map(g => `${g.name} • ${g.memory_total_gb} GB`).join(' / ') || 'CPU mode'),
      metric('Neural CUDA', neural.ready ? 'READY' : 'WAIT', neural.ready ? `${neural.device_name || 'GPU'} • Torch ${neural.torch_version || '—'}` : (neural.error || 'V2-A reste active')),
      metric('LAN Worker GPUs', String(workerGpus.length), workerGpus.map(g => `${g.name} • ${g.memory_total_gb} GB`).join(' / ') || 'Aucun worker connecté'),
      metric('Stems V2-D', (localStems.ready || stemWorker) ? 'READY' : 'WAIT', stemWorker ? `${stemWorker.node_name} • ${stemWorker.gpus?.[0]?.name || 'GPU'} • ${stemWorker.latency_ms ?? '—'} ms` : (localStems.ready ? `${health.node_name} • local fallback` : (localStems.error || 'Demucs non installé'))),
    ];
    panel.innerHTML = cards.join('');
  }

  function renderV2Offline(error) {
    const panel = document.getElementById('v2-node-grid');
    if (!panel) return;
    panel.innerHTML = metric('Deep Audio API', 'OFFLINE', explainConnectionError(error));
  }

  function renderV2Result(result) {
    const section = document.getElementById('v2-results');
    const grid = document.getElementById('v2-results-grid');
    const provenance = document.getElementById('v2-provenance');
    if (!section || !grid) return;

    const loud = result.mastering?.loudness || {};
    const levels = result.mastering?.levels || {};
    const file = result.file || {};
    const gpu = result.engine?.gpu_snapshot?.[0];
    grid.innerHTML = [
      metric('Integrated Loudness', format(loud.integrated_lufs, ' LUFS'), 'MEASURED • BS.1770 / EBU R128'),
      metric('True Peak', format(loud.true_peak_dbtp, ' dBTP'), 'MEASURED'),
      metric('Loudness Range', format(loud.loudness_range_lu, ' LU'), 'MEASURED • LRA'),
      metric('Mean Volume', format(levels.mean_volume_db, ' dB'), 'FFmpeg volumedetect'),
      metric('Max Volume', format(levels.max_volume_db, ' dB'), 'FFmpeg volumedetect'),
      metric('Codec', String(file.codec || '—').toUpperCase(), `${file.sample_rate_hz || '—'} Hz • ${file.channels || '—'} ch`),
      metric('Bitrate', file.bit_rate_kbps != null ? `${file.bit_rate_kbps} kb/s` : '—', file.format || 'container'),
      metric('Compute Node', result.engine?.node_name || '—', gpu ? `${gpu.name} • ${gpu.memory_total_gb} GB` : 'CPU / GPU idle'),
    ].join('');

    if (provenance) {
      const warning = result.warnings?.[0];
      provenance.textContent = warning ? `MEASURED = backend DSP réel. ${warning}` : 'MEASURED = backend DSP réel. Le fichier temporaire est supprimé après analyse.';
    }
    section.classList.remove('hidden');
    if (result.neural) renderNeuralResult(result.neural);
    else hideNeuralResult();
  }

  function ensureNeuralSection() {
    let section = document.getElementById('v2-neural-results');
    if (section) return section;
    section = document.createElement('section');
    section.id = 'v2-neural-results';
    section.className = 'glass-card v2-neural-results hidden';
    section.innerHTML = `
      <div class="v2-results-header">
        <div class="v2-results-title"><i data-lucide="brain-circuit"></i> Neural Music Understanding V2-B</div>
        <div class="v2-provenance">NEURAL = CLAP zero-shot • scores relatifs au jeu de candidats, pas métriques Spotify.</div>
      </div>
      <div id="v2-neural-columns" class="v2-neural-columns"></div>
      <div id="v2-traits-grid" class="v2-traits-grid"></div>
      <div id="v2-neural-engine" class="v2-neural-engine"></div>`;
    document.getElementById('v2-results')?.insertAdjacentElement('afterend', section);
    window.lucide?.createIcons?.();
    return section;
  }

  function hideNeuralResult() {
    document.getElementById('v2-neural-results')?.classList.add('hidden');
  }

  function renderNeuralResult(neural) {
    const section = ensureNeuralSection();
    const columns = document.getElementById('v2-neural-columns');
    const traitsGrid = document.getElementById('v2-traits-grid');
    const engine = document.getElementById('v2-neural-engine');
    if (!columns || !traitsGrid || !engine) return;

    columns.innerHTML = [
      neuralGroup('Genres / styles', neural.genres || []),
      neuralGroup('Mood / émotion', neural.moods || []),
      neuralGroup('Instrumentation', neural.instruments || []),
    ].join('');

    const traitLabels = { electronic: 'Electronic', vocal: 'Vocal', energy: 'Energy', brightness: 'Brightness', danceability: 'Danceability', aggression: 'Aggression', space: 'Atmosphere' };
    traitsGrid.innerHTML = Object.entries(neural.traits || {}).map(([key, data]) => metric(traitLabels[key] || key, `${Number(data.percent || 0).toFixed(0)}%`, 'NEURAL • relative axis')).join('');

    const info = neural.engine || {};
    const embedding = neural.embedding || {};
    engine.innerHTML = [
      `<span>MODEL: ${escapeHtml(info.model || 'CLAP')}</span>`,
      `<span>DEVICE: ${escapeHtml(info.device_name || info.device || '—')}</span>`,
      `<span>CUDA: ${escapeHtml(info.cuda_runtime || '—')}</span>`,
      `<span>SEGMENTS: ${escapeHtml(info.segment_count ?? '—')} × ${escapeHtml(info.segment_seconds ?? '—')}s</span>`,
      `<span>EMBEDDING: ${escapeHtml(embedding.dimension || '—')}D</span>`,
      `<span>VRAM RESERVED: ${escapeHtml(info.gpu_memory_reserved_mb ?? '—')} MB</span>`,
    ].join('');
    section.classList.remove('hidden');
  }

  function ensureStemsSection() {
    let section = document.getElementById('v2-stems-results');
    if (section) return section;
    section = document.createElement('section');
    section.id = 'v2-stems-results';
    section.className = 'glass-card v2-stems-results hidden';
    section.innerHTML = `
      <div class="v2-results-header">
        <div class="v2-results-title"><i data-lucide="split"></i> Source Separation V2-D — Demucs</div>
        <div id="v2-stems-provenance" class="v2-provenance"></div>
      </div>
      <div id="v2-stems-grid" class="v2-stems-grid"></div>
      <div id="v2-stems-engine" class="v2-neural-engine"></div>`;
    const neural = document.getElementById('v2-neural-results');
    const anchor = neural || document.getElementById('v2-results');
    anchor?.insertAdjacentElement('afterend', section);
    window.lucide?.createIcons?.();
    return section;
  }

  function renderStemsResult(result) {
    const section = ensureStemsSection();
    const grid = document.getElementById('v2-stems-grid');
    const engine = document.getElementById('v2-stems-engine');
    const provenance = document.getElementById('v2-stems-provenance');
    if (!grid || !engine || !provenance) return;

    const separation = result.separation || {};
    const stems = separation.stems || [];
    grid.innerHTML = stems.map(stem => {
      const loud = stem.loudness || {};
      const levels = stem.levels || {};
      const energy = Number(stem.relative_energy_percent || 0);
      return `<article class="v2-stem-card">
        <div class="v2-stem-head"><strong>${escapeHtml(stem.name || 'stem')}</strong><span>${energy.toFixed(1)}% énergie relative</span></div>
        <div class="v2-stem-energy"><i style="width:${clamp(energy, 0, 100)}%"></i></div>
        <div class="v2-stem-metrics">
          <span><small>LUFS</small><b>${format(loud.integrated_lufs, '')}</b></span>
          <span><small>TRUE PEAK</small><b>${format(loud.true_peak_dbtp, ' dBTP')}</b></span>
          <span><small>MEAN</small><b>${format(levels.mean_volume_db, ' dB')}</b></span>
          <span><small>LRA</small><b>${format(loud.loudness_range_lu, ' LU')}</b></span>
        </div>
      </article>`;
    }).join('');

    const route = result.compute?.route || 'unknown';
    provenance.textContent = `DEMUCS GPU • ${stems.length} stems • ${route} • fichiers intermédiaires supprimés après mesures.`;
    engine.innerHTML = [
      `<span>MODEL: ${escapeHtml(separation.model || 'htdemucs')}</span>`,
      `<span>NODE: ${escapeHtml(result.compute?.node_name || '—')}</span>`,
      `<span>DEVICE: ${escapeHtml(separation.device || 'cuda')}</span>`,
      `<span>ROUTE: ${escapeHtml(route)}</span>`,
      `<span>TIME: ${escapeHtml(separation.elapsed_seconds ?? '—')} s</span>`,
      `<span>POLICY: ${escapeHtml(result.routing?.selected_reason || 'best GPU fit')}</span>`,
    ].join('');
    section.classList.remove('hidden');
  }

  function neuralGroup(title, items) {
    const rows = items.slice(0, 6).map(item => {
      const percent = clamp(Number(item.percent || 0), 0, 100);
      return `<div class="v2-neural-row"><span class="v2-neural-label" title="${escapeHtml(item.label || '')}">${escapeHtml(item.label || '—')}</span><strong class="v2-neural-score">${percent.toFixed(1)}%</strong><div class="v2-neural-bar"><i style="width:${percent.toFixed(1)}%"></i></div></div>`;
    }).join('');
    return `<div class="v2-neural-group"><h4>${escapeHtml(title)}</h4><div class="v2-neural-list">${rows || '<span class="v2-status-text">Aucune donnée.</span>'}</div></div>`;
  }

  function metric(label, value, sub) {
    return `<div class="v2-metric"><span>${escapeHtml(label)}</span><strong title="${escapeHtml(value)}">${escapeHtml(value)}</strong><small title="${escapeHtml(sub || '')}">${escapeHtml(sub || '')}</small></div>`;
  }

  function format(value, suffix) {
    return value == null ? '—' : `${Number(value).toFixed(2)}${suffix}`;
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, Number.isFinite(value) ? value : min));
  }

  function setDeepProgress(value) {
    const fill = document.getElementById('v2-progress-fill');
    if (fill) fill.style.width = `${clamp(Number(value) || 0, 0, 100)}%`;
  }

  function setV2Status(tag, message, error = false) {
    const tagEl = document.getElementById('v2-status-tag');
    const textEl = document.getElementById('v2-status-text');
    if (tagEl) {
      tagEl.textContent = tag;
      tagEl.classList.toggle('error', error);
    }
    if (textEl) textEl.textContent = message;
  }

  function explainConnectionError(error) {
    const message = error?.message || String(error || 'Connection failed');
    if (isGitHubPages() && isLoopbackApi()) return `Tu es sur GitHub Pages. Pour le Deep Scan local, utilise ${LOCAL_UI}. ${message}`;
    if (isLocalRuntimePage()) return `${message}. Relance LMNotebook_START.cmd, qui vérifie l'API avant d'ouvrir la page.`;
    if (location.protocol === 'https:' && apiBase.startsWith('http://')) return `HTTPS page → HTTP API potentiellement bloquée par le navigateur. ${message}`;
    return `${message}. Vérifie que le runtime LMNotebook est lancé.`;
  }

  function escapeHtml(value) {
    return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
  }
})();