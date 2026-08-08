(() => {
  'use strict';

  const API = 'http://127.0.0.1:8000';
  let selectedFile = null;
  let fusionReady = false;
  let latestResult = null;

  function initFusionClient() {
    const input = document.getElementById('audio-file-input');
    const deepBtn = document.getElementById('deep-analyze-audio-btn');
    if (!input || !deepBtn || document.getElementById('fusion-analyze-audio-btn')) return;

    const button = ensureButton(deepBtn);
    selectedFile = input.files?.[0] || null;

    input.addEventListener('change', () => {
      selectedFile = input.files?.[0] || null;
      syncButton(button);
    });

    document.getElementById('drop-zone')?.addEventListener('drop', event => {
      selectedFile = event.dataTransfer?.files?.[0] || selectedFile;
      syncButton(button);
    });

    button.addEventListener('click', () => runFusion(button));
    syncButton(button);
    window.setTimeout(() => refreshCapability(button), 450);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFusionClient, { once: true });
  } else {
    initFusionClient();
  }

  function ensureButton(deepBtn) {
    let button = document.getElementById('fusion-analyze-audio-btn');
    if (button) return button;

    button = document.createElement('button');
    button.id = 'fusion-analyze-audio-btn';
    button.className = 'primary-btn fusion-btn';
    button.type = 'button';
    button.disabled = true;
    button.innerHTML = '<i data-lucide="combine"></i> Fusion V2-C×V2-D';

    const anatomy = document.getElementById('anatomy-analyze-audio-btn');
    const stems = document.getElementById('stems-analyze-audio-btn');
    (anatomy || stems || deepBtn).insertAdjacentElement('afterend', button);
    window.lucide?.createIcons?.();
    return button;
  }

  async function refreshCapability(button) {
    try {
      const response = await fetch(`${API}/api/fusion/status`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      fusionReady = Boolean(payload.ready);
      if (!fusionReady && payload.error) {
        button.title = payload.error;
      } else {
        const selected = payload.selected_stems_node || {};
        button.title = selected.name || selected.node_name
          ? `V2-C local + V2-D sur ${selected.name || selected.node_name}`
          : 'V2-C local + V2-D routé automatiquement';
      }
    } catch (_) {
      fusionReady = false;
    }
    syncButton(button);
  }

  function syncButton(button) {
    if (button) button.disabled = !(selectedFile && fusionReady);
  }

  async function runFusion(button) {
    if (!selectedFile || !fusionReady) return;

    const peerButtons = [
      document.getElementById('analyze-audio-btn'),
      document.getElementById('deep-analyze-audio-btn'),
      document.getElementById('stems-analyze-audio-btn'),
      document.getElementById('anatomy-analyze-audio-btn'),
    ].filter(Boolean);

    setBusy(true, button, ...peerButtons);
    setV2Status(
      'V2-CD FUSION',
      '3060: structure/harmonie • 3070 Ti: Demucs + activité temporelle • fusion des preuves en cours…'
    );
    setProgress(8);

    try {
      const form = new FormData();
      form.append('file', selectedFile, selectedFile.name);
      setProgress(18);

      const response = await fetch(`${API}/api/fusion`, {
        method: 'POST',
        body: form,
      });
      if (!response.ok) throw new Error(await responseError(response));

      setProgress(94);
      const result = await response.json();
      latestResult = result;
      renderFusion(result);
      setProgress(100);

      const fusion = result.fusion || {};
      const summary = fusion.summary || {};
      const route = result.compute?.stems_route || '—';
      const node = result.compute?.stems_node || 'worker';
      setV2Status(
        'V2-CD FUSED',
        `${selectedFile.name} • ${summary.section_count || 0} sections relabellisées • stems ${route} sur ${node}`
      );
    } catch (error) {
      setProgress(0);
      setV2Status('V2-CD ERROR', error.message || 'Fusion failed', true);
    } finally {
      setBusy(false, button, ...peerButtons);
      syncButton(button);
    }
  }

  function ensureSection() {
    let section = document.getElementById('v2-fusion-results');
    if (section) return section;

    section = document.createElement('section');
    section.id = 'v2-fusion-results';
    section.className = 'glass-card fusion-results hidden';
    section.innerHTML = `
      <div class="fusion-header">
        <div>
          <div class="fusion-title"><i data-lucide="combine"></i> Song Understanding Fusion V2-C×V2-D</div>
          <div class="fusion-subtitle">Structure + harmonie + répétitions + activité temporelle des stems</div>
        </div>
        <div id="fusion-route" class="fusion-route"></div>
      </div>

      <div id="fusion-summary" class="fusion-summary"></div>

      <div class="fusion-panel fusion-arrangement-panel">
        <div class="fusion-panel-head">
          <strong>Fused Arrangement</strong>
          <span>clique une section : label + confiance + preuves</span>
        </div>
        <div id="fusion-timeline" class="fusion-timeline"></div>
        <div id="fusion-detail" class="fusion-detail"></div>
      </div>

      <div class="fusion-grid">
        <div class="fusion-panel">
          <div class="fusion-panel-head">
            <strong>Stem Activity by Section</strong>
            <span>normalisé dans le morceau</span>
          </div>
          <div id="fusion-stem-map" class="fusion-stem-map"></div>
        </div>
        <div class="fusion-panel">
          <div class="fusion-panel-head">
            <strong>Fused Recurrence</strong>
            <span>V2-C similarity + profils des stems</span>
          </div>
          <div id="fusion-similarity" class="fusion-similarity"></div>
        </div>
      </div>

      <div class="fusion-grid">
        <div class="fusion-panel">
          <div class="fusion-panel-head">
            <strong>Hook Candidates</strong>
            <span>récurrence + vocals + drums + énergie</span>
          </div>
          <div id="fusion-hooks" class="fusion-hooks"></div>
        </div>
        <div class="fusion-panel">
          <div class="fusion-panel-head">
            <strong>Label Evidence</strong>
            <span>pourquoi Intro / Verse / Chorus / etc.</span>
          </div>
          <div id="fusion-evidence-list" class="fusion-evidence-list"></div>
        </div>
      </div>

      <div id="fusion-engine" class="fusion-engine"></div>
    `;

    const anatomy = document.getElementById('v2-anatomy-results');
    const stems = document.getElementById('v2-stems-results');
    const anchor = anatomy || stems || document.getElementById('v2-neural-results') || document.getElementById('v2-results');
    anchor?.insertAdjacentElement('beforebegin', section);
    window.lucide?.createIcons?.();
    return section;
  }

  function renderFusion(result) {
    const container = ensureSection();
    const fusion = result.fusion || {};
    const sections = fusion.sections || [];
    const summary = fusion.summary || {};
    const duration = Number(result.file?.duration_seconds || sections.at(-1)?.end || 1);
    const climax = fusion.climax || {};
    const route = result.compute || {};

    const routeEl = document.getElementById('fusion-route');
    if (routeEl) {
      const fallback = route.stems_route === 'local-fallback';
      routeEl.className = `fusion-route ${fallback ? 'fallback' : 'worker'}`;
      routeEl.innerHTML = `
        <span>${esc(route.stems_route || '—')}</span>
        <strong>${esc(route.stems_device || 'GPU ?')}</strong>
        <small>${esc(route.stems_node || 'node ?')} • ${Number(route.stems_elapsed_seconds || 0).toFixed(1)} s</small>
      `;
    }

    const summaryEl = document.getElementById('fusion-summary');
    if (summaryEl) {
      const labels = Object.entries(summary.labels || {})
        .filter(([, count]) => Number(count) > 0)
        .map(([name, count]) => `${name}×${count}`)
        .join(' • ') || 'labels en attente';
      summaryEl.innerHTML = [
        summaryMetric('Sections', summary.section_count ?? sections.length, labels),
        summaryMetric('Repeat Groups', summary.fusion_repeat_group_count || 0, 'V2-C + profils stems'),
        summaryMetric('Hooks', summary.hook_candidate_count || 0, 'fusion salience'),
        summaryMetric('Climax', climax.time != null ? fmtTime(climax.time) : '—', climax.label || '—'),
        summaryMetric('Stems Route', route.stems_route || '—', route.stems_node || '—'),
        summaryMetric('Compute', '2 GPUs', `${route.coordinator || '3060'} + ${route.stems_device || 'worker'}`),
      ].join('');
    }

    renderTimeline(sections, duration, climax);
    renderStemMap(sections);
    renderSimilarity(fusion.section_similarity || [], sections);
    renderHooks(fusion.hooks || []);
    renderEvidenceList(sections);

    const engine = document.getElementById('fusion-engine');
    if (engine) {
      const info = fusion.engine || {};
      engine.innerHTML = [
        `<span>ENGINE: ${esc(info.name || 'Song Understanding Fusion')}</span>`,
        `<span>VERSION: ${esc(info.version || result.fusion_schema_version || '2.4')}</span>`,
        `<span>MODE: ${esc(info.mode || 'V2-C x V2-D')}</span>`,
        `<span>STEMS: ${esc(route.stems_route || '—')} / ${esc(route.stems_device || '—')}</span>`,
        `<span>BOUNDARIES: V2-C</span>`,
        `<span>LABELS: evidence fusion inference</span>`,
      ].join('');
    }

    container.classList.remove('hidden');
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function renderTimeline(sections, duration, climax) {
    const timeline = document.getElementById('fusion-timeline');
    if (!timeline) return;

    timeline.innerHTML = sections.map((section, index) => {
      const width = clamp((Number(section.duration || 0) / duration) * 100, 1.3, 100);
      const confidence = pct(section.fusion_confidence);
      const repeat = section.fusion_repeat_group ? `R${section.fusion_repeat_group}` : '';
      const isClimax = Number(climax.section_index) === index;
      return `
        <button
          class="fusion-section type-${slug(section.fusion_type || 'section')} ${isClimax ? 'is-climax' : ''}"
          data-fusion-section="${index}"
          style="flex-basis:${width}%"
          title="${esc(section.fusion_label || 'Section')} • ${confidence} confidence"
        >
          <strong>${esc(section.fusion_label || section.original_label || `Section ${index + 1}`)}</strong>
          <small>${fmtTime(section.start)} · ${confidence}</small>
          <span>${repeat}${isClimax ? `${repeat ? ' • ' : ''}CLIMAX` : ''}</span>
        </button>`;
    }).join('');

    timeline.querySelectorAll('[data-fusion-section]').forEach(button => {
      button.addEventListener('click', () => {
        timeline.querySelectorAll('.active').forEach(el => el.classList.remove('active'));
        button.classList.add('active');
        renderDetail(sections[Number(button.dataset.fusionSection)]);
      });
    });

    if (sections[0]) {
      timeline.querySelector('[data-fusion-section="0"]')?.classList.add('active');
      renderDetail(sections[0]);
    }
  }

  function renderDetail(section) {
    const detail = document.getElementById('fusion-detail');
    if (!detail || !section) return;
    const activity = section.stem_activity || {};
    const alternatives = (section.fusion_alternatives || [])
      .map(item => `${item.type} ${(Number(item.score || 0) * 100).toFixed(0)}%`)
      .join(' • ');

    detail.innerHTML = `
      <div class="fusion-detail-main">
        <div class="fusion-detail-label">
          <span>FUSED LABEL</span>
          <strong>${esc(section.fusion_label || '—')}</strong>
          <b>${pct(section.fusion_confidence)}</b>
        </div>
        <div class="fusion-detail-meta">
          <span>${fmtTime(section.start)} → ${fmtTime(section.end)}</span>
          <span>V2-C: ${esc(section.original_label || '—')}</span>
          <span>${section.fusion_repeat_group ? `R${section.fusion_repeat_group} ×${section.fusion_repeat_count}` : 'unique'}</span>
          <span>alt: ${esc(alternatives || '—')}</span>
        </div>
        <div class="fusion-evidence-chips">
          ${(section.evidence || []).map(item => `<i>${esc(item)}</i>`).join('')}
        </div>
      </div>
      <div class="fusion-stem-bars">
        ${stemBar('Vocals', activity.vocals)}
        ${stemBar('Drums', activity.drums)}
        ${stemBar('Bass', activity.bass)}
        ${stemBar('Other', activity.other)}
      </div>
    `;
  }

  function renderStemMap(sections) {
    const el = document.getElementById('fusion-stem-map');
    if (!el) return;
    el.innerHTML = `
      <div class="fusion-stem-map-head">
        <span>SECTION</span><span>VOCALS</span><span>DRUMS</span><span>BASS</span><span>OTHER</span>
      </div>
      ${sections.map(section => {
        const a = section.stem_activity || {};
        return `<div class="fusion-stem-row">
          <strong>${esc(section.fusion_label || section.original_label || 'Section')}</strong>
          ${miniActivity(a.vocals)}
          ${miniActivity(a.drums)}
          ${miniActivity(a.bass)}
          ${miniActivity(a.other)}
        </div>`;
      }).join('')}
    `;
  }

  function renderSimilarity(matrix, sections) {
    const el = document.getElementById('fusion-similarity');
    if (!el) return;
    const n = matrix.length;
    if (!n) {
      el.innerHTML = '<span class="fusion-empty">Aucune matrice disponible.</span>';
      return;
    }
    el.style.setProperty('--fusion-sim-size', n);
    el.innerHTML = matrix.flatMap((row, r) => row.map((value, c) => {
      const v = clamp(Number(value || 0), 0, 1);
      const title = `${sections[r]?.fusion_label || r + 1} ↔ ${sections[c]?.fusion_label || c + 1}: ${(v * 100).toFixed(0)}%`;
      return `<i style="opacity:${(0.10 + v * 0.90).toFixed(2)}" title="${esc(title)}"></i>`;
    })).join('');
  }

  function renderHooks(hooks) {
    const el = document.getElementById('fusion-hooks');
    if (!el) return;
    el.innerHTML = hooks.length
      ? hooks.map((hook, index) => `
          <article>
            <div><strong>HOOK ${index + 1}</strong><b>${Number(hook.score || 0).toFixed(0)}%</b></div>
            <span>${esc(hook.label || 'Section')} • ${fmtTime(hook.start)} → ${fmtTime(hook.end)}</span>
            <small>${(hook.evidence || []).map(esc).join(' • ')}</small>
          </article>
        `).join('')
      : '<span class="fusion-empty">Aucun hook fusion suffisamment saillant.</span>';
  }

  function renderEvidenceList(sections) {
    const el = document.getElementById('fusion-evidence-list');
    if (!el) return;
    el.innerHTML = sections.map(section => `
      <div class="fusion-evidence-row">
        <div>
          <strong>${esc(section.fusion_label || 'Section')}</strong>
          <span>${pct(section.fusion_confidence)} • ${fmtTime(section.start)}–${fmtTime(section.end)}</span>
        </div>
        <p>${(section.evidence || []).map(esc).join(' • ')}</p>
      </div>
    `).join('');
  }

  function summaryMetric(label, value, sub) {
    return `<div class="fusion-summary-card"><span>${esc(label)}</span><strong>${esc(String(value ?? '—'))}</strong><small>${esc(sub || '')}</small></div>`;
  }

  function stemBar(label, data = {}) {
    const score = clamp(Number(data.score || 0), 0, 100);
    return `<div class="fusion-stem-bar">
      <div><span>${label}</span><b>${score.toFixed(0)}%</b><small>${Number(data.dbfs ?? -120).toFixed(1)} dBFS</small></div>
      <i><em style="width:${score}%"></em></i>
    </div>`;
  }

  function miniActivity(data = {}) {
    const score = clamp(Number(data.score || 0), 0, 100);
    return `<span class="fusion-mini-activity" title="${score.toFixed(0)}% • ${Number(data.dbfs ?? -120).toFixed(1)} dBFS">
      <i><em style="width:${score}%"></em></i><b>${score.toFixed(0)}</b>
    </span>`;
  }

  function setBusy(busy, ...buttons) {
    buttons.filter(Boolean).forEach(button => {
      button.disabled = busy || (button.id === 'fusion-analyze-audio-btn' && !(selectedFile && fusionReady));
      if (button.id === 'fusion-analyze-audio-btn') {
        button.classList.toggle('is-running', busy);
        button.innerHTML = busy
          ? '<i data-lucide="loader-circle"></i> Fusion en cours…'
          : '<i data-lucide="combine"></i> Fusion V2-C×V2-D';
      }
    });
    window.lucide?.createIcons?.();
  }

  function setV2Status(tag, text, error = false) {
    const tagEl = document.getElementById('v2-status-tag');
    const textEl = document.getElementById('v2-status-text');
    if (tagEl) {
      tagEl.textContent = tag;
      tagEl.classList.toggle('error', error);
    }
    if (textEl) textEl.textContent = text;
  }

  function setProgress(value) {
    const fill = document.getElementById('v2-progress-fill');
    if (fill) fill.style.width = `${clamp(Number(value || 0), 0, 100)}%`;
  }

  async function responseError(response) {
    try {
      const body = await response.json();
      return body.detail || body.error || `HTTP ${response.status}`;
    } catch (_) {
      return `HTTP ${response.status}`;
    }
  }

  function pct(value) {
    const n = Number(value || 0);
    return `${Math.round(n <= 1 ? n * 100 : n)}%`;
  }

  function fmtTime(seconds) {
    const s = Math.max(0, Number(seconds || 0));
    const minutes = Math.floor(s / 60);
    const rest = Math.floor(s % 60);
    return `${minutes}:${String(rest).padStart(2, '0')}`;
  }

  function slug(value) {
    return String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function esc(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  window.LMNotebookFusion = {
    getLatest: () => latestResult,
    refresh: () => refreshCapability(document.getElementById('fusion-analyze-audio-btn')),
  };
})();
