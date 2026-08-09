(() => {
  'use strict';

  const EXPERT_IDS = [
    'analyze-audio-btn',
    'deep-analyze-audio-btn',
    'stems-analyze-audio-btn',
    'anatomy-analyze-audio-btn',
    'fusion-analyze-audio-btn',
    'semantic-arrangement-btn',
  ];

  let booted = false;
  let selectedFile = null;
  let fullBusy = false;

  function boot() {
    if (booted) return;
    const actions = document.querySelector('.analysis-actions');
    const fileInput = document.getElementById('audio-file-input');
    const choose = document.getElementById('choose-audio-btn');
    const semantic = document.getElementById('semantic-arrangement-btn');
    const lyrics = document.getElementById('semantic-lyrics-wrap');
    if (!actions || !fileInput || !choose || !semantic || !lyrics) return false;

    booted = true;
    selectedFile = fileInput.files?.[0] || null;

    const shell = document.createElement('div');
    shell.id = 'unified-analysis-shell';
    shell.className = 'unified-analysis-shell';
    shell.dataset.layout = 'build-02-workflow';
    shell.innerHTML = `
      <div class="unified-intake-row" aria-label="Fichiers d’analyse">
        <div class="unified-intake-slot unified-audio-slot" data-unified-audio-slot>
          <span class="unified-intake-kicker">Audio</span>
        </div>
        <div class="unified-intake-slot unified-lyrics-slot" data-unified-lyrics-slot>
          <span class="unified-intake-kicker">Paroles / contexte</span>
        </div>
      </div>
      <div class="unified-main-row">
        <div class="unified-analysis-kicker">Choisis le niveau d’analyse</div>
        <div class="unified-main-actions">
          <button id="unified-quick-btn" class="unified-btn unified-quick" type="button" disabled>
            <i data-lucide="zap"></i>
            <span><strong>Analyse express</strong><small>Mesures audio locales • quelques secondes</small></span>
          </button>
          <button id="unified-full-btn" class="unified-btn unified-full" type="button" disabled>
            <i data-lucide="sparkles"></i>
            <span><strong>Analyse complète</strong><small>DSP + mastering + Neural + structure + stems + paroles</small></span>
          </button>
        </div>
        <div id="unified-layer-strip" class="unified-layer-strip" aria-live="polite">
          <span data-layer="v1">DSP</span>
          <span data-layer="v2ab">Mastering + Neural</span>
          <span data-layer="v2c">Structure</span>
          <span data-layer="v2d">Stems GPU</span>
          <span data-layer="fusion">Fusion</span>
          <span data-layer="lyrics">Paroles</span>
        </div>
      </div>
      <details id="unified-expert-tools" class="unified-expert-tools">
        <summary><i data-lucide="sliders-horizontal"></i><span>Outils avancés</span><small>Lancer une couche séparément</small></summary>
        <div class="unified-expert-buttons"></div>
      </details>`;

    choose.insertAdjacentElement('afterend', shell);

    const audioSlot = shell.querySelector('[data-unified-audio-slot]');
    const lyricsSlot = shell.querySelector('[data-unified-lyrics-slot]');
    audioSlot?.appendChild(choose);
    lyricsSlot?.appendChild(lyrics);
    lyrics.classList.add('unified-lyrics');

    const expertButtons = shell.querySelector('.unified-expert-buttons');
    EXPERT_IDS.forEach(id => {
      const button = document.getElementById(id);
      if (button) expertButtons.appendChild(button);
    });

    const quickBtn = shell.querySelector('#unified-quick-btn');
    const fullBtn = shell.querySelector('#unified-full-btn');

    quickBtn.addEventListener('click', () => runQuick(quickBtn));
    fullBtn.addEventListener('click', () => runFull(fullBtn));

    fileInput.addEventListener('change', () => {
      selectedFile = fileInput.files?.[0] || null;
      resetLayers();
      syncButtons();
    });

    document.getElementById('drop-zone')?.addEventListener('drop', event => {
      selectedFile = event.dataTransfer?.files?.[0] || selectedFile;
      resetLayers();
      window.setTimeout(syncButtons, 30);
    });

    document.getElementById('semantic-lyrics-input')?.addEventListener('change', syncLyricsLayer);
    document.getElementById('semantic-lyrics-clear')?.addEventListener('click', () => window.setTimeout(syncLyricsLayer, 0));

    const stateObserver = new MutationObserver(syncButtons);
    stateObserver.observe(semantic, { attributes: true, attributeFilter: ['disabled', 'class'] });

    syncLyricsLayer();
    syncButtons();
    window.lucide?.createIcons?.();
    return true;
  }

  function syncButtons() {
    const quick = document.getElementById('unified-quick-btn');
    const full = document.getElementById('unified-full-btn');
    const semantic = document.getElementById('semantic-arrangement-btn');
    const hasFile = Boolean(selectedFile || document.getElementById('audio-file-input')?.files?.[0]);
    if (quick) quick.disabled = !hasFile || fullBusy;
    if (full) {
      const pipelineReady = semantic && !semantic.disabled && !semantic.classList.contains('is-loading');
      full.disabled = !hasFile || !pipelineReady || fullBusy;
      full.title = pipelineReady
        ? 'Lance automatiquement toutes les couches utiles.'
        : 'Le moteur complet sera disponible dès que le runtime avancé sera prêt.';
    }
  }

  async function runQuick(button) {
    if (!selectedFile || typeof window.runAnalysis !== 'function') return;
    setUnifiedBusy(button, true, 'Analyse express en cours…');
    markLayer('v1', 'running');
    try {
      await window.runAnalysis();
      markLayer('v1', 'done');
    } catch (error) {
      markLayer('v1', 'error');
      console.error('[LMNotebook] Unified quick scan failed:', error);
    } finally {
      setUnifiedBusy(button, false);
      syncButtons();
    }
  }

  async function runFull(button) {
    const semantic = document.getElementById('semantic-arrangement-btn');
    if (!selectedFile || !semantic || semantic.disabled || fullBusy) return;

    fullBusy = true;
    resetLayers();
    syncLyricsLayer();
    setUnifiedBusy(button, true, 'Analyse complète en cours…');
    lockQuick(true);

    try {
      markLayer('v1', 'running');
      setUnifiedNote('Étape 1/2 • mesures locales du signal');
      if (typeof window.runAnalysis === 'function') await window.runAnalysis();
      markLayer('v1', 'done');

      ['v2ab', 'v2c', 'v2d', 'fusion'].forEach(name => markLayer(name, 'running'));
      setUnifiedNote('Étape 2/2 • compréhension complète sur les deux GPU');

      semantic.click();
      await waitFor(() => semantic.classList.contains('is-loading'), 5000);
      await waitFor(() => !semantic.classList.contains('is-loading'), 12 * 60 * 1000);

      const status = document.getElementById('v2-status-tag')?.textContent || '';
      const result = document.getElementById('v2-semantic-results');
      if (/ERROR/i.test(status) || !result || result.classList.contains('hidden')) {
        throw new Error(document.getElementById('v2-status-text')?.textContent || 'Analyse complète interrompue.');
      }

      ['v2ab', 'v2c', 'v2d', 'fusion'].forEach(name => markLayer(name, 'done'));
      setUnifiedNote('Analyse complète terminée • lecture musicale prête');
      result.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
      ['v2ab', 'v2c', 'v2d', 'fusion'].forEach(name => {
        const layer = document.querySelector(`[data-layer="${name}"]`);
        if (layer?.classList.contains('is-running')) markLayer(name, 'error');
      });
      setUnifiedNote(error.message || 'L’analyse complète a été interrompue.', true);
      console.error('[LMNotebook] Unified full scan failed:', error);
    } finally {
      fullBusy = false;
      setUnifiedBusy(button, false);
      lockQuick(false);
      syncButtons();
    }
  }

  function setUnifiedBusy(button, busy, text) {
    button.classList.toggle('is-loading', busy);
    if (busy) {
      button.dataset.originalHtml = button.innerHTML;
      button.innerHTML = `<i data-lucide="loader-circle"></i><span><strong>${escapeHtml(text || 'Analyse en cours…')}</strong><small>Tu peux suivre les étapes juste en dessous</small></span>`;
    } else if (button.dataset.originalHtml) {
      button.innerHTML = button.dataset.originalHtml;
      delete button.dataset.originalHtml;
    }
    window.lucide?.createIcons?.();
  }

  function lockQuick(locked) {
    const quick = document.getElementById('unified-quick-btn');
    if (quick) quick.disabled = locked || !selectedFile;
  }

  function markLayer(name, state) {
    const layer = document.querySelector(`[data-layer="${name}"]`);
    if (!layer) return;
    layer.classList.remove('is-running', 'is-done', 'is-error');
    if (state) layer.classList.add(`is-${state}`);
  }

  function resetLayers() {
    document.querySelectorAll('#unified-layer-strip [data-layer]').forEach(layer => {
      layer.classList.remove('is-running', 'is-done', 'is-error');
    });
    syncLyricsLayer();
    setUnifiedNote('Analyse complète = toutes les couches en un clic');
  }

  function syncLyricsLayer() {
    const hasLyrics = Boolean(document.getElementById('semantic-lyrics-input')?.files?.length);
    const layer = document.querySelector('[data-layer="lyrics"]');
    if (!layer) return;
    layer.classList.toggle('is-done', hasLyrics);
    layer.classList.toggle('is-optional', !hasLyrics);
    layer.textContent = hasLyrics ? 'Paroles ✓' : 'Paroles optionnelles';
  }

  function setUnifiedNote(text, error = false) {
    let note = document.getElementById('unified-analysis-note');
    if (!note) {
      note = document.createElement('div');
      note.id = 'unified-analysis-note';
      note.className = 'unified-analysis-note';
      document.getElementById('unified-layer-strip')?.insertAdjacentElement('afterend', note);
    }
    note.textContent = text;
    note.classList.toggle('is-error', error);
  }

  async function waitFor(test, timeout = 5000, interval = 100) {
    const started = Date.now();
    while (Date.now() - started < timeout) {
      if (test()) return true;
      await new Promise(resolve => setTimeout(resolve, interval));
    }
    throw new Error('Le moteur a dépassé le délai de réponse prévu.');
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[ch]));
  }

  const observer = new MutationObserver(() => {
    if (boot()) observer.disconnect();
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
