(() => {
  'use strict';

  const VERSION = '3.5.3-diagnostic';
  const TARGET = '/api/analyze';
  const originalFetch = window.fetch.bind(window);
  let latestPayload = null;
  let renderTimer = null;

  function requestUrl(input) {
    if (typeof input === 'string') return input;
    if (input && typeof input.url === 'string') return input.url;
    return String(input || '');
  }

  function isNeuralAnalyze(url) {
    const text = String(url || '');
    return text.includes(TARGET) && /[?&]neural=true(?:&|$)/.test(text);
  }

  window.fetch = async function sonicTraceDiagnosticFetch(...args) {
    const response = await originalFetch(...args);
    const url = requestUrl(args[0]);
    if (isNeuralAnalyze(url) && response && response.ok && typeof response.clone === 'function') {
      response.clone().json().then(payload => {
        latestPayload = payload;
        scheduleRender();
      }).catch(error => {
        console.warn('[SonicTrace] Neural diagnostic payload capture failed:', error);
      });
    }
    return response;
  };

  function scheduleRender() {
    if (renderTimer) clearTimeout(renderTimer);
    const attempts = [0, 120, 450, 1000];
    attempts.forEach(delay => window.setTimeout(render, delay));
    renderTimer = window.setTimeout(() => { renderTimer = null; }, 1100);
  }

  function neuralFromPayload(payload) {
    if (!payload || typeof payload !== 'object') return {};
    return payload.neural && typeof payload.neural === 'object' ? payload.neural : {};
  }

  function scoreOf(row, preferred) {
    if (!row || typeof row !== 'object') return 0;
    for (const key of preferred) {
      const value = Number(row[key]);
      if (Number.isFinite(value)) return value;
    }
    return 0;
  }

  function percent(value) {
    const number = Number(value || 0);
    return `${Math.round(number * 1000) / 10}%`;
  }

  function styleList(rows, mode) {
    const source = Array.isArray(rows) ? rows.slice(0, 6) : [];
    if (!source.length) return '<span class="diag-empty">aucune donnée</span>';
    return source.map(row => {
      const label = esc(row?.label || '—');
      const score = mode === 'ensemble'
        ? (Number.isFinite(Number(row?.ensemble_percent)) ? `${Math.round(Number(row.ensemble_percent) * 10) / 10}%` : percent(scoreOf(row, ['ensemble_score'])))
        : percent(scoreOf(row, ['similarity', 'score']));
      const family = row?.family ? ` <small>${esc(row.family)}</small>` : '';
      return `<span><b>${label}</b> ${score}${family}</span>`;
    }).join('');
  }

  function labelOf(value) {
    if (!value || typeof value !== 'object') return '';
    if (String(value.label || '') === 'Unknown / hybrid' && value.candidate && typeof value.candidate === 'object') {
      return `Unknown / hybrid → ${String(value.candidate.label || '—')}`;
    }
    return String(value.label || '');
  }

  function render() {
    if (!latestPayload) return;
    const contexts = document.querySelectorAll('.semantic-context');
    const context = contexts.length ? contexts[contexts.length - 1] : null;
    if (!context) return;

    const neural = neuralFromPayload(latestPayload);
    const analysis = neural.genre_analysis && typeof neural.genre_analysis === 'object' ? neural.genre_analysis : {};
    const ensemble = analysis.ensemble && typeof analysis.ensemble === 'object' ? analysis.ensemble : {};
    const dimensions = analysis.dimensions && typeof analysis.dimensions === 'object' ? analysis.dimensions : {};
    const coherence = dimensions.coherence && typeof dimensions.coherence === 'object' ? dimensions.coherence : {};
    const cluster = coherence.family_cluster && typeof coherence.family_cluster === 'object' ? coherence.family_cluster : {};
    const style = dimensions.style && typeof dimensions.style === 'object' ? dimensions.style : {};
    const tradition = dimensions.tradition && typeof dimensions.tradition === 'object' ? dimensions.tradition : {};
    const form = dimensions.form && typeof dimensions.form === 'object' ? dimensions.form : {};

    let panel = context.querySelector('[data-sonictrace-neural-diagnostic]');
    if (!panel) {
      panel = document.createElement('section');
      panel.dataset.sonictraceNeuralDiagnostic = VERSION;
      panel.className = 'sonictrace-neural-diagnostic';
      context.appendChild(panel);
    }

    const rawPrimary = labelOf(analysis.primary);
    const ensemblePrimary = labelOf(ensemble.primary);
    const resolvedStyle = String(style.primary?.label || '—');
    const resolvedFamily = String(dimensions.family?.label || coherence.resolved_family || '—');
    const clusterPercent = Number.isFinite(Number(cluster.percent)) ? `${cluster.percent}%` : percent(cluster.score);
    const clusterMargin = Number.isFinite(Number(cluster.margin)) ? percent(cluster.margin) : '—';
    const runner = cluster.runner_up_family ? `${cluster.runner_up_family} (${percent(cluster.runner_up_score)})` : '—';
    const labels = Array.isArray(cluster.supporting_labels) ? cluster.supporting_labels.join(' · ') : '—';
    const roles = Array.isArray(cluster.roles) ? cluster.roles.join(' · ') : '—';
    const expertFamily = ensemble.expert_top_family
      ? `${ensemble.expert_top_family} (${percent(ensemble.expert_top_family_score)})`
      : '—';

    panel.innerHTML = `
      <style>
        .sonictrace-neural-diagnostic{margin-top:18px;padding:14px;border:1px solid rgba(38,229,206,.26);border-radius:12px;background:rgba(4,18,22,.7);font-size:12px;line-height:1.45}
        .sonictrace-neural-diagnostic h4{margin:0 0 4px;color:#5ff5df;font-size:13px;text-transform:uppercase;letter-spacing:.08em}
        .sonictrace-neural-diagnostic>p{margin:0 0 12px;color:#8ca0a8}
        .diag-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
        .diag-card{padding:10px;border:1px solid rgba(130,164,173,.16);border-radius:9px;background:rgba(5,13,16,.55);min-width:0}
        .diag-card strong{display:block;color:#dbe9ec;margin-bottom:6px;font-size:11px;text-transform:uppercase;letter-spacing:.05em}
        .diag-card>span,.diag-list span{display:block;color:#b6c8cd;margin:3px 0;overflow-wrap:anywhere}
        .diag-list b{color:#eef8fa}.diag-list small{color:#6f858d}.diag-empty{color:#6f858d!important}
        .diag-wide{grid-column:1/-1}.diag-kv b{color:#5ff5df}.diag-warn{color:#ffcd70!important}
        @media(max-width:760px){.diag-grid{grid-template-columns:1fr}.diag-wide{grid-column:auto}}
      </style>
      <h4>Diagnostic Neural ${VERSION}</h4>
      <p>Lecture seule · payload réel du scan · aucune metadata TXT utilisée pour modifier l’inférence.</p>
      <div class="diag-grid">
        <div class="diag-card diag-list"><strong>1 · CLAP brut</strong>${styleList(analysis.styles, 'raw')}</div>
        <div class="diag-card diag-list"><strong>2 · Ensemble CLAP + Discogs</strong>${styleList(ensemble.styles, 'ensemble')}</div>
        <div class="diag-card diag-wide diag-kv">
          <strong>3 · Family cluster V3.5.2</strong>
          <span>Statut <b>${esc(cluster.status || '—')}</b> · famille <b>${esc(cluster.family || '—')}</b> · score <b>${esc(clusterPercent)}</b> · marge <b>${esc(clusterMargin)}</b></span>
          <span>Runner-up ${esc(runner)}</span>
          <span>Labels soutien : ${esc(labels)}</span>
          <span>Rôles : ${esc(roles)} · labels comptés ${esc(cluster.label_count ?? '—')} · eligible ${esc(cluster.eligible ?? '—')}</span>
        </div>
        <div class="diag-card diag-kv">
          <strong>4 · Décision</strong>
          <span>Primary analysis <b>${esc(rawPrimary || '—')}</b></span>
          <span>Primary ensemble <b>${esc(ensemblePrimary || '—')}</b></span>
          <span>Décision ensemble <b>${esc(ensemble.decision || '—')}</b></span>
          <span>Style dimensions <b>${esc(resolvedStyle)}</b></span>
          <span>Famille dimensions <b>${esc(resolvedFamily)}</b></span>
        </div>
        <div class="diag-card diag-kv">
          <strong>5 · Contexte / expert / versions</strong>
          <span>Tradition <b>${esc(tradition.primary?.label || '—')}</b> · forme <b>${esc(form.primary?.label || '—')}</b></span>
          <span>Discogs famille #1 <b>${esc(expertFamily)}</b></span>
          <span>Neural engine <b>${esc(neural.engine?.analysis_version || '—')}</b> · ensemble <b>${esc(ensemble.version || '—')}</b></span>
          <span>dimensions <b>${esc(dimensions.version || '—')}</b> · coherence <b>${esc(coherence.version || '—')}</b></span>
        </div>
      </div>`;
  }

  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  }

  const observer = new MutationObserver(() => {
    if (latestPayload) scheduleRender();
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });

  window.LMNNeuralDiagnostics = Object.freeze({
    version: VERSION,
    render,
    getPayload: () => latestPayload,
  });

  document.documentElement.dataset.sonictraceNeuralDiagnostic = VERSION;
})();
