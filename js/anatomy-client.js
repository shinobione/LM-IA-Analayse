(() => {
  'use strict';

  const API = 'http://127.0.0.1:8000';
  let selectedFile = null;
  let anatomyReady = false;

  document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('audio-file-input');
    const dropZone = document.getElementById('drop-zone');
    const deepBtn = document.getElementById('deep-analyze-audio-btn');
    if (!input || !deepBtn) return;

    const button = ensureButton(deepBtn);
    input.addEventListener('change', () => {
      selectedFile = input.files?.[0] || null;
      syncButton(button);
    });

    dropZone?.addEventListener('drop', event => {
      selectedFile = event.dataTransfer?.files?.[0] || selectedFile;
      syncButton(button);
    });

    button.addEventListener('click', () => runAnatomy(button));
    window.setTimeout(() => refreshCapability(button), 700);
  });

  function ensureButton(deepBtn) {
    let button = document.getElementById('anatomy-analyze-audio-btn');
    if (button) return button;
    button = document.createElement('button');
    button.id = 'anatomy-analyze-audio-btn';
    button.className = 'secondary-btn anatomy-btn';
    button.type = 'button';
    button.disabled = true;
    button.innerHTML = '<i data-lucide="git-branch-plus"></i> Song Anatomy V2-C';

    const stems = document.getElementById('stems-analyze-audio-btn');
    (stems || deepBtn).insertAdjacentElement('afterend', button);
    window.lucide?.createIcons?.();
    return button;
  }

  async function refreshCapability(button) {
    try {
      const response = await fetch(`${API}/api/health`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const health = await response.json();
      anatomyReady = Boolean(health.anatomy?.ready || health.analysis_layers?.v2c_song_anatomy);
    } catch (_) {
      anatomyReady = false;
    }
    syncButton(button);
  }

  function syncButton(button) {
    if (button) button.disabled = !(selectedFile && anatomyReady);
  }

  async function runAnatomy(button) {
    if (!selectedFile || !anatomyReady) return;
    const stemsBtn = document.getElementById('stems-analyze-audio-btn');
    const deepBtn = document.getElementById('deep-analyze-audio-btn');
    const v1Btn = document.getElementById('analyze-audio-btn');

    setBusy(true, button, stemsBtn, deepBtn, v1Btn);
    setV2Status('V2-C ANATOMY', 'Segmentation structurelle • répétitions • hooks • climax • accords • tonalité dans le temps…');
    setProgress(10);

    try {
      const form = new FormData();
      form.append('file', selectedFile, selectedFile.name);
      setProgress(22);

      const response = await fetch(`${API}/api/anatomy`, { method: 'POST', body: form });
      if (!response.ok) throw new Error(await responseError(response));

      setProgress(94);
      const result = await response.json();
      renderAnatomy(result);
      setProgress(100);

      const anatomy = result.anatomy || {};
      const sectionCount = anatomy.summary?.section_count ?? anatomy.sections?.length ?? 0;
      setV2Status(
        'V2-C MEASURED',
        `${selectedFile.name} • ${sectionCount} sections • structure/harmonie analysées sur ${result.compute?.node_name || 'coordinateur'}`
      );
    } catch (error) {
      setProgress(0);
      setV2Status('V2-C ERROR', error.message || 'Song Anatomy failed', true);
    } finally {
      setBusy(false, button, stemsBtn, deepBtn, v1Btn);
      syncButton(button);
    }
  }

  function ensureSection() {
    let section = document.getElementById('v2-anatomy-results');
    if (section) return section;

    section = document.createElement('section');
    section.id = 'v2-anatomy-results';
    section.className = 'glass-card anatomy-results hidden';
    section.innerHTML = `
      <div class="v2-results-header anatomy-header">
        <div>
          <div class="v2-results-title"><i data-lucide="waypoints"></i> Song Anatomy V2-C</div>
          <div class="anatomy-subtitle">Structure musicale • répétitions • hooks • climax • harmonie</div>
        </div>
        <div id="anatomy-provenance" class="v2-provenance"></div>
      </div>

      <div id="anatomy-summary" class="anatomy-summary"></div>

      <div class="anatomy-panel">
        <div class="anatomy-panel-head">
          <strong>Structure Timeline</strong>
          <span>clique une section pour l’inspecter</span>
        </div>
        <div id="anatomy-timeline-wrap" class="anatomy-timeline-wrap">
          <div id="anatomy-timeline" class="anatomy-timeline"></div>
          <div id="anatomy-markers" class="anatomy-markers"></div>
        </div>
        <div id="anatomy-section-detail" class="anatomy-section-detail"></div>
      </div>

      <div class="anatomy-grid-2">
        <div class="anatomy-panel">
          <div class="anatomy-panel-head"><strong>Chord Timeline</strong><span>triades majeures / mineures</span></div>
          <div id="anatomy-chords" class="anatomy-chords"></div>
          <div id="anatomy-harmonic-changes" class="anatomy-harmonic-changes"></div>
        </div>

        <div class="anatomy-panel">
          <div class="anatomy-panel-head"><strong>Structural Recurrence</strong><span>similarité entre sections</span></div>
          <div id="anatomy-similarity" class="anatomy-similarity"></div>
        </div>
      </div>

      <div class="anatomy-grid-2">
        <div class="anatomy-panel">
          <div class="anatomy-panel-head"><strong>Hook Candidates</strong><span>répétition + énergie + saillance rythmique</span></div>
          <div id="anatomy-hooks" class="anatomy-hooks"></div>
        </div>
        <div class="anatomy-panel">
          <div class="anatomy-panel-head"><strong>Section Map</strong><span>clé / énergie / répétition / confiance</span></div>
          <div id="anatomy-section-list" class="anatomy-section-list"></div>
        </div>
      </div>

      <div id="anatomy-engine" class="v2-neural-engine anatomy-engine"></div>`;

    const stems = document.getElementById('v2-stems-results');
    const neural = document.getElementById('v2-neural-results');
    const anchor = stems || neural || document.getElementById('v2-results');
    anchor?.insertAdjacentElement('afterend', section);
    window.lucide?.createIcons?.();
    return section;
  }

  function renderAnatomy(result) {
    const section = ensureSection();
    const anatomy = result.anatomy || {};
    const sections = anatomy.sections || [];
    const duration = Number(anatomy.duration_seconds || result.file?.duration_seconds || 1);
    const summary = anatomy.summary || {};
    const key = anatomy.global_key || {};
    const climax = anatomy.climax || {};
    const hooks = anatomy.hooks || [];

    const summaryEl = document.getElementById('anatomy-summary');
    if (summaryEl) {
      summaryEl.innerHTML = [
        metric('Sections', summary.section_count ?? sections.length, `${summary.repeat_group_count || 0} groupes répétés`),
        metric('Global Key', key.key || '—', `confidence ${pct(key.confidence)}`),
        metric('Tempo', anatomy.tempo_bpm != null ? `${Number(anatomy.tempo_bpm).toFixed(1)} BPM` : '—', 'beat-synchronous grid'),
        metric('Climax', climax.time != null ? fmtTime(climax.time) : '—', climax.section_index != null ? sectionLabel(sections, climax.section_index) : 'impact peak'),
        metric('Hooks', hooks.length, hooks[0] ? `top ${Number(hooks[0].score || 0).toFixed(0)}%` : 'aucun candidat'),
        metric('Chords', summary.chord_change_count ?? Math.max(0, (anatomy.chords || []).length - 1), `${summary.harmonic_change_count || 0} changements tonals`),
      ].join('');
    }

    renderTimeline(sections, duration, climax, hooks);
    renderChords(anatomy.chords || [], anatomy.harmonic_changes || [], duration);
    renderSimilarity(anatomy.section_similarity || [], sections);
    renderHooks(hooks, sections);
    renderSectionList(sections);

    const provenance = document.getElementById('anatomy-provenance');
    if (provenance) {
      provenance.textContent = 'SIGNAL-DERIVED boundaries/chords • labels Intro/Verse/Chorus/etc = inférence structurelle heuristique avec confiance affichée.';
    }

    const engine = document.getElementById('anatomy-engine');
    if (engine) {
      const info = anatomy.engine || {};
      engine.innerHTML = [
        `<span>ENGINE: ${esc(info.name || 'Song Anatomy')}</span>`,
        `<span>ALGO: ${esc(info.algorithm || 'structural DSP')}</span>`,
        `<span>TIME: ${esc(info.elapsed_seconds ?? '—')} s</span>`,
        `<span>SR: ${esc(info.sample_rate_hz ?? '—')} Hz</span>`,
        `<span>NODE: ${esc(result.compute?.node_name || '—')}</span>`,
        `<span>MODE: ${esc(info.label_mode || 'heuristic-structural')}</span>`,
      ].join('');
    }

    section.classList.remove('hidden');
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function renderTimeline(sections, duration, climax, hooks) {
    const timeline = document.getElementById('anatomy-timeline');
    const markers = document.getElementById('anatomy-markers');
    if (!timeline || !markers) return;

    timeline.innerHTML = sections.map((item, index) => {
      const width = clamp((Number(item.duration || 0) / duration) * 100, 1.2, 100);
      const confidence = Math.round(Number(item.label_confidence || 0) * 100);
      const repeat = item.repeat_group ? `R${item.repeat_group}` : '';
      const tooltip = `${item.label || item.type} • ${fmtTime(item.start)}–${fmtTime(item.end)} • énergie ${item.energy}% • ${item.key?.key || 'key ?'} • confiance ${confidence}%`;
      return `<button class="anatomy-section-block type-${slug(item.type || 'section')}" data-section="${index}" style="flex-basis:${width}%" title="${esc(tooltip)}">
        <strong>${esc(item.label || item.type || `Section ${index + 1}`)}</strong>
        <small>${fmtTime(item.start)}</small>
        ${repeat ? `<em>${repeat}</em>` : ''}
      </button>`;
    }).join('');

    markers.innerHTML = [
      climax?.time != null
        ? `<span class="anatomy-marker climax" style="left:${clamp(Number(climax.time) / duration * 100, 0, 100)}%" title="Climax ${fmtTime(climax.time)}"><i></i>CLIMAX</span>`
        : '',
      ...hooks.map((hook, index) => `<span class="anatomy-marker hook" style="left:${clamp(Number(hook.start) / duration * 100, 0, 100)}%" title="Hook ${index + 1} • ${Number(hook.score || 0).toFixed(0)}%"><i></i>H${index + 1}</span>`),
    ].join('');

    timeline.querySelectorAll('[data-section]').forEach(button => {
      button.addEventListener('click', () => {
        timeline.querySelectorAll('.active').forEach(el => el.classList.remove('active'));
        button.classList.add('active');
        renderSectionDetail(sections[Number(button.dataset.section)]);
      });
    });

    if (sections[0]) {
      timeline.querySelector('[data-section="0"]')?.classList.add('active');
      renderSectionDetail(sections[0]);
    }
  }

  function renderSectionDetail(item) {
    const detail = document.getElementById('anatomy-section-detail');
    if (!detail || !item) return;
    detail.innerHTML = [
      `<div><span>SECTION</span><strong>${esc(item.label || item.type || '—')}</strong></div>`,
      `<div><span>TIME</span><strong>${fmtTime(item.start)} → ${fmtTime(item.end)}</strong></div>`,
      `<div><span>ENERGY</span><strong>${Number(item.energy || 0).toFixed(0)}%</strong></div>`,
      `<div><span>RHYTHMIC</span><strong>${Number(item.rhythmic || 0).toFixed(0)}%</strong></div>`,
      `<div><span>BRIGHTNESS</span><strong>${Number(item.brightness || 0).toFixed(0)}%</strong></div>`,
      `<div><span>KEY</span><strong>${esc(item.key?.key || '—')}</strong></div>`,
      `<div><span>REPEAT</span><strong>${item.repeat_group ? `R${item.repeat_group} ×${item.repeat_count}` : 'unique'}</strong></div>`,
      `<div><span>LABEL CONF.</span><strong>${pct(item.label_confidence)}</strong></div>`,
    ].join('');
  }

  function renderChords(chords, harmonicChanges, duration) {
    const strip = document.getElementById('anatomy-chords');
    const changes = document.getElementById('anatomy-harmonic-changes');
    if (!strip || !changes) return;

    strip.innerHTML = chords.map(chord => {
      const width = clamp(((Number(chord.end) - Number(chord.start)) / duration) * 100, 0.8, 100);
      return `<div class="anatomy-chord ${chord.label === 'N' ? 'no-chord' : ''}" style="flex-basis:${width}%" title="${esc(chord.label)} • ${fmtTime(chord.start)}–${fmtTime(chord.end)} • confidence ${pct(chord.confidence)}">
        <strong>${esc(chord.label || 'N')}</strong>
        <small>${fmtTime(chord.start)}</small>
      </div>`;
    }).join('');

    changes.innerHTML = harmonicChanges.length
      ? harmonicChanges.map(change => `<span><b>${fmtTime(change.time)}</b> ${esc(change.from || '?')} → ${esc(change.to || '?')}</span>`).join('')
      : '<span>Aucun changement de centre tonal suffisamment net détecté.</span>';
  }

  function renderSimilarity(matrix, sections) {
    const el = document.getElementById('anatomy-similarity');
    if (!el) return;
    const n = matrix.length;
    if (!n) {
      el.innerHTML = '<span class="anatomy-empty">Aucune matrice.</span>';
      return;
    }

    el.style.setProperty('--sim-size', n);
    el.innerHTML = matrix.flatMap((row, r) => row.map((value, c) => {
      const v = clamp(Number(value || 0), 0, 1);
      const title = `${sectionLabel(sections, r)} ↔ ${sectionLabel(sections, c)} : ${(v * 100).toFixed(0)}%`;
      return `<i style="opacity:${(0.12 + v * 0.88).toFixed(2)}" title="${esc(title)}"></i>`;
    })).join('');
  }

  function renderHooks(hooks, sections) {
    const el = document.getElementById('anatomy-hooks');
    if (!el) return;
    el.innerHTML = hooks.length
      ? hooks.map((hook, index) => `<article class="anatomy-hook-card">
          <div><strong>HOOK ${index + 1}</strong><b>${Number(hook.score || 0).toFixed(0)}%</b></div>
          <span>${fmtTime(hook.start)} → ${fmtTime(hook.end)}</span>
          <small>${esc(sectionLabel(sections, hook.section_index))}</small>
        </article>`).join('')
      : '<span class="anatomy-empty">Aucun hook suffisamment saillant.</span>';
  }

  function renderSectionList(sections) {
    const el = document.getElementById('anatomy-section-list');
    if (!el) return;
    el.innerHTML = sections.map(item => `<div class="anatomy-section-row">
      <strong>${esc(item.label || item.type || 'Section')}</strong>
      <span>${fmtTime(item.start)}–${fmtTime(item.end)}</span>
      <span>${esc(item.key?.key || '—')}</span>
      <span>E ${Number(item.energy || 0).toFixed(0)}%</span>
      <span>${item.repeat_group ? `R${item.repeat_group} ×${item.repeat_count}` : 'unique'}</span>
      <span>conf ${pct(item.label_confidence)}</span>
    </div>`).join('');
  }

  function metric(label, value, sub) {
    return `<div class="v2-metric anatomy-metric"><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(sub || '')}</small></div>`;
  }

  function sectionLabel(sections, index) {
    const item = sections?.[Number(index)];
    return item?.label || item?.type || (index == null ? '—' : `Section ${Number(index) + 1}`);
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

  function setProgress(value) {
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

  function fmtTime(seconds) {
    const total = Math.max(0, Number(seconds) || 0);
    const minutes = Math.floor(total / 60);
    const secs = Math.floor(total % 60);
    return `${minutes}:${String(secs).padStart(2, '0')}`;
  }

  function pct(value) {
    const n = Number(value);
    if (!Number.isFinite(n)) return '—';
    return `${Math.round(n * 100)}%`;
  }

  function slug(value) {
    return String(value || 'section').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, Number.isFinite(value) ? value : min));
  }

  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;',
    })[char]);
  }
})();
