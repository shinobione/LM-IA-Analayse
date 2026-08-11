(() => {
  'use strict';

  const BRAND = 'SonicTrace Audio Intelligence';
  const RELEASE = Object.freeze({ version: 'V2-E', build: '06', display: 'V2-E · BUILD 06' });
  let scheduled = false;

  const exactTextMap = new Map([
    ['LMNotebook Neural Audio Analyzer', BRAND],
    ['HYBRID ANALYSIS ENGINE', 'MOTEUR D’ANALYSE AUDIO'],
    ['BROWSER DSP V1', 'ANALYSE LOCALE'],
    ['DEEP AUDIO V2', 'ANALYSE AVANCÉE'],
    ['Browser analysis pipeline', 'État de l’analyse'],
    ['Deep Audio V2 node', 'Moteur avancé'],
    ['Deep Mastering V2 — Reference Measurements', 'Mastering & niveau'],
    ['Measured Sonic DNA', 'Profil sonore'],
    ['Waveform & Spectrogram', 'Forme d’onde & spectre'],
    ['Spectral Energy Distribution', 'Répartition fréquentielle'],
    ['Dynamic Energy Progression', 'Évolution de l’énergie'],
    ['Source Separation V2-D — Demucs', 'Répartition des sources'],
    ['Song Anatomy V2-C', 'Structure du morceau'],
    ['Song Understanding Fusion V2-C×V2-D', 'Vue d’ensemble du morceau'],
    ['Song Understanding Fusion V2-CxV2-D', 'Vue d’ensemble du morceau'],
    ['Semantic Arrangement V2-CD.1', 'Paroles & contexte'],
    ['Final Arrangement', 'Déroulé du morceau'],
    ['Arrangement Evidence', 'Pourquoi cette lecture ?'],
    ['Lyrics / Neural Context', 'Paroles & style'],
    ['Declared Intent (TXT)', 'Infos du fichier texte'],
    ['DSP Strengths', 'Ce qui fonctionne'],
    ['Technical Watchpoints', 'À surveiller'],
    ['Automatic Technical Report', 'Lecture production'],
    ['Export JSON', 'Exporter'],
    ['Connect', 'Connecter'],
  ]);

  const buttonMap = [
    [/Scan DSP V1/i, 'Analyse express', 'st-action-fast'],
    [/Deep Scan V2/i, 'Analyse complète', 'st-action-full'],
    [/Stems V2-D/i, 'Séparer les sources', 'st-action-tool'],
    [/Song Anatomy V2-C/i, 'Structure du morceau', 'st-action-tool'],
    [/Fusion V2-C/i, 'Vue d’ensemble', 'st-action-tool'],
    [/Semantic Arrangement V2-CD\.1/i, 'Paroles & contexte', 'st-action-tool'],
  ];

  function txt(el) {
    return (el?.textContent || '').replace(/\s+/g, ' ').trim();
  }

  function installReleaseLabel() {
    document.documentElement.dataset.sonictraceRelease = 'v2-e-build-06';
    document.querySelectorAll('.brand-identity').forEach(identity => {
      const copy = identity.querySelector('.brand-title')?.parentElement;
      if (!copy) return;
      let label = copy.querySelector('.brand-release');
      if (!label) {
        label = document.createElement('span');
        label.className = 'brand-release';
        copy.appendChild(label);
      }
      label.textContent = RELEASE.display;
      label.title = `${BRAND} ${RELEASE.version} Build ${RELEASE.build}`;
      label.setAttribute('aria-label', `${BRAND} version ${RELEASE.version}, build ${RELEASE.build}`);
    });
  }

  function retitle() {
    document.title = 'SonicTrace — Audio Intelligence';

    document.querySelectorAll('h1,h2,h3,h4,.brand-title,.card-header,.card-header-flex h3,.v2-results-title,.fusion-title,.semantic-title,.anatomy-title').forEach(el => {
      const current = txt(el);
      if (exactTextMap.has(current)) el.textContent = exactTextMap.get(current);
    });

    document.querySelectorAll('.brand-title').forEach(el => { el.textContent = BRAND; });
    document.querySelectorAll('.brand-subtitle').forEach(el => {
      el.textContent = 'Analyse musicale locale • GPU • structure • paroles';
    });
    installReleaseLabel();

    document.querySelectorAll('.artist-name').forEach(el => {
      if (/hybrid analysis engine/i.test(txt(el))) el.textContent = 'MOTEUR D’ANALYSE AUDIO';
    });

    document.querySelectorAll('.platform-badge').forEach(el => {
      const current = txt(el);
      if (/browser dsp v1/i.test(current)) el.textContent = 'ANALYSE LOCALE';
      if (/deep audio v2/i.test(current)) el.textContent = 'ANALYSE AVANCÉE';
    });
  }

  function simplifyActions() {
    const buttons = Array.from(document.querySelectorAll('button'));
    const tools = [];

    buttons.forEach(btn => {
      const label = txt(btn);
      buttonMap.forEach(([rx, replacement, cls]) => {
        if (rx.test(label)) {
          btn.textContent = replacement;
          btn.classList.add('st-action', cls);
        }
      });
      if (btn.classList.contains('st-action-tool')) tools.push(btn);
    });

    const actionRoot = document.querySelector('.analysis-actions');
    if (!actionRoot) return;

    const unifiedExpert = document.querySelector('#unified-analysis-shell .unified-expert-buttons');
    if (unifiedExpert) {
      tools.forEach(btn => {
        if (!unifiedExpert.contains(btn)) unifiedExpert.appendChild(btn);
      });
      actionRoot.querySelector('.st-toolbox')?.remove();
      return;
    }

    if (!tools.length || actionRoot.querySelector('.st-toolbox')) return;

    const details = document.createElement('details');
    details.className = 'st-toolbox';
    details.innerHTML = '<summary>Outils avancés</summary><div class="st-toolbox-body"></div>';
    actionRoot.appendChild(details);
    const body = details.querySelector('.st-toolbox-body');
    tools.forEach(btn => body.appendChild(btn));
  }

  function hideRedundantMicrocopy() {
    const patterns = [
      /V1 reste 100% locale/i,
      /Les couches V2/i,
      /MEASURED =/i,
      /signal-derived/i,
      /heuristic/i,
      /policy:/i,
      /algo:/i,
      /engine:/i,
      /source declared/i,
      /clique sur une section/i,
    ];

    document.querySelectorAll('p,small,.analysis-disclaimer,.v2-provenance,.fusion-provenance,.semantic-provenance,.anatomy-provenance,.mono-dim').forEach(el => {
      if (patterns.some(rx => rx.test(txt(el)))) el.classList.add('st-micro-hidden');
    });
  }

  function markReadableZones() {
    document.body.classList.add('sonictrace-readable');
    document.querySelectorAll('.glass-card').forEach(el => el.classList.add('st-card'));
    document.querySelectorAll('.metric-card').forEach(el => el.classList.add('st-metric'));
    document.querySelectorAll('.terminal-body,#terminal-output').forEach(el => el.classList.add('st-terminal'));
    document.querySelectorAll('.human-insight-item,.human-check,.production-note,.production-lead').forEach(el => el.classList.add('st-human-copy'));
  }

  function polish() {
    scheduled = false;
    retitle();
    simplifyActions();
    hideRedundantMicrocopy();
    markReadableZones();
    window.lucide?.createIcons?.();
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(polish);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', schedule, { once: true });
  } else {
    schedule();
  }

  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
})();