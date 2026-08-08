(() => {
  'use strict';

  const DEFAULT_API = 'http://127.0.0.1:8000';
  const LOCAL_UI = 'http://127.0.0.1:8008';
  let selectedFile = null;
  let apiBase = DEFAULT_API;
  let connected = false;

  document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('audio-file-input');
    const dropZone = document.getElementById('drop-zone');
    const connectBtn = document.getElementById('v2-connect-btn');
    const deepBtn = document.getElementById('deep-analyze-audio-btn');
    const apiInput = document.getElementById('v2-api-url');

    if (!connectBtn || !deepBtn || !apiInput) return;
    apiInput.value = DEFAULT_API;

    input?.addEventListener('change', () => {
      if (input.files?.[0]) {
        selectedFile = input.files[0];
        syncDeepButton(deepBtn);
      }
    });

    dropZone?.addEventListener('drop', event => {
      const file = event.dataTransfer?.files?.[0];
      if (file) {
        selectedFile = file;
        syncDeepButton(deepBtn);
      }
    });

    connectBtn.addEventListener('click', async () => {
      apiBase = normalizeBase(apiInput.value || DEFAULT_API);
      await testConnection();
      syncDeepButton(deepBtn);
    });

    deepBtn.addEventListener('click', runDeepScan);

    if (isLocalRuntimePage()) {
      setV2Status('V2 CONNECTING', 'Runtime local détecté • connexion automatique au moteur Deep Audio V2…');
      window.setTimeout(async () => {
        apiBase = DEFAULT_API;
        await testConnection();
        syncDeepButton(deepBtn);
      }, 350);
    } else if (isGitHubPages()) {
      setV2Status(
        'V2 LOCAL',
        'Le Deep Scan V2 s’utilise depuis la page locale ouverte automatiquement par LMNotebook_START.cmd.'
      );
    }
  });

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

  function syncDeepButton(button) {
    button.disabled = !(selectedFile && connected);
  }

  async function testConnection() {
    setV2Status('CONNECTING', 'Connexion au nœud Deep Audio V2…');
    const deepBtn = document.getElementById('deep-analyze-audio-btn');
    try {
      const healthResponse = await fetch(`${apiBase}/api/health`, { method: 'GET', cache: 'no-store' });
      if (!healthResponse.ok) throw new Error(`HTTP ${healthResponse.status}`);
      const health = await healthResponse.json();

      let cluster = null;
      try {
        const clusterResponse = await fetch(`${apiBase}/api/cluster`, { method: 'GET', cache: 'no-store' });
        if (clusterResponse.ok) cluster = await clusterResponse.json();
      } catch (_) {
        // Cluster details are optional for a single-node V2-A deployment.
      }

      connected = true;
      renderV2Health(health, cluster);
      setV2Status(
        health.status === 'ok' ? 'V2 ONLINE' : 'V2 DEGRADED',
        `${health.node_name || 'Deep Audio node'} • ${health.gpus?.length || 0} GPU locale(s) détectée(s)`
      );
    } catch (error) {
      connected = false;
      renderV2Offline(error);
      setV2Status('V2 OFFLINE', explainConnectionError(error), true);
    }
    if (deepBtn) syncDeepButton(deepBtn);
  }

  async function runDeepScan() {
    if (!selectedFile || !connected) return;
    const deepBtn = document.getElementById('deep-analyze-audio-btn');
    const v1Btn = document.getElementById('analyze-audio-btn');
    if (deepBtn) deepBtn.disabled = true;
    if (v1Btn) v1Btn.disabled = true;

    setV2Status('DEEP SCAN', 'Upload temporaire vers le nœud V2 • FFmpeg / BS.1770 / EBU R128…');
    setDeepProgress(12);

    try {
      const form = new FormData();
      form.append('file', selectedFile, selectedFile.name);
      setDeepProgress(28);

      const response = await fetch(`${apiBase}/api/analyze`, {
        method: 'POST',
        body: form,
      });
      setDeepProgress(82);

      if (!response.ok) {
        let detail = `HTTP ${response.status}`;
        try {
          const payload = await response.json();
          detail = payload.detail || detail;
        } catch (_) {}
        throw new Error(detail);
      }

      const result = await response.json();
      setDeepProgress(100);
      renderV2Result(result);
      setV2Status('V2 MEASURED', `${selectedFile.name} • Deep Mastering Scan terminé`);
    } catch (error) {
      setDeepProgress(0);
      setV2Status('V2 ERROR', error.message || 'Deep Scan failed', true);
    } finally {
      if (deepBtn) deepBtn.disabled = false;
      if (v1Btn) v1Btn.disabled = false;
    }
  }

  function renderV2Health(health, cluster) {
    const panel = document.getElementById('v2-node-grid');
    if (!panel) return;
    const localGpus = health.gpus || [];
    const workers = cluster?.workers || [];
    const workerGpus = workers.flatMap(worker => worker.gpus || []);
    const cards = [
      metric('Node', health.node_name || '—', health.node_role || 'backend'),
      metric('FFmpeg', health.ffmpeg?.ffmpeg && health.ffmpeg?.ffprobe ? 'READY' : 'MISSING', 'V2-A mastering'),
      metric('Local GPUs', String(localGpus.length), localGpus.map(g => `${g.name} • ${g.memory_total_gb} GB`).join(' / ') || 'CPU mode'),
      metric('LAN Worker GPUs', String(workerGpus.length), workerGpus.map(g => `${g.name} • ${g.memory_total_gb} GB`).join(' / ') || 'Aucun worker connecté'),
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
      provenance.textContent = 'MEASURED = backend DSP réel. Le fichier temporaire est supprimé après analyse. Les couches Neural / Stems seront ajoutées sur les GPU locaux.';
    }
    section.classList.remove('hidden');
  }

  function metric(label, value, sub) {
    return `<div class="v2-metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(sub || '')}</small></div>`;
  }

  function format(value, suffix) {
    return value == null ? '—' : `${Number(value).toFixed(2)}${suffix}`;
  }

  function setDeepProgress(value) {
    const fill = document.getElementById('v2-progress-fill');
    if (fill) fill.style.width = `${Math.max(0, Math.min(100, Number(value) || 0))}%`;
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
    if (isGitHubPages() && isLoopbackApi()) {
      return `Tu es sur GitHub Pages. Pour le Deep Scan local, utilise ${LOCAL_UI}, ouvert automatiquement par LMNotebook_START.cmd. ${message}`;
    }
    if (isLocalRuntimePage()) {
      return `${message}. Le moteur local n'a pas répondu ; relance LMNotebook_START.cmd, qui vérifiera désormais l'API avant d'ouvrir la page.`;
    }
    if (location.protocol === 'https:' && apiBase.startsWith('http://')) {
      return `HTTPS page → HTTP API potentiellement bloquée par le navigateur. Utilise un endpoint HTTPS/tunnel. ${message}`;
    }
    return `${message}. Vérifie que le runtime LMNotebook est lancé.`;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }
})();
