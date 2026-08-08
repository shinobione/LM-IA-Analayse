(() => {
  'use strict';

  const COPY = {
    '#analyze-audio-btn': ['activity', 'Analyse rapide'],
    '#deep-analyze-audio-btn': ['brain-circuit', 'Analyse avancée'],
    '#stems-analyze-audio-btn': ['split', 'Séparer les stems'],
    '#anatomy-analyze-audio-btn': ['git-branch-plus', 'Découper la structure'],
    '#fusion-analyze-audio-btn': ['combine', 'Fusion structure + stems'],
    '#semantic-arrangement-btn': ['brain', 'Analyser structure + paroles'],
  };

  function setButton(selector, icon, label) {
    const button = document.querySelector(selector);
    if (!button) return;
    if (button.dataset.humanLabel !== label && !button.classList.contains('is-loading')) {
      button.innerHTML = `<i data-lucide="${icon}"></i> ${label}`;
      button.dataset.humanLabel = label;
    }
    if (selector === '#semantic-arrangement-btn') {
      button.classList.add('semantic-main-cta');
      button.title = 'Croise structure, stems, analyse Neural et paroles timestampées.';
    }
  }

  function polishStaticUI() {
    Object.entries(COPY).forEach(([selector, [icon, label]]) => setButton(selector, icon, label));

    setText('.brand-subtitle', 'Analyse audio locale • compréhension musicale • cluster GPU');
    setText('.upload-eyebrow', 'ANALYSE MUSICALE / MOTEUR HYBRIDE');
    setText('.upload-title', 'Analyse le morceau, puis lis sa structure comme une chanson.');
    setText('.upload-description', 'Commence par les mesures audio, puis combine mastering, compréhension Neural, structure, stems GPU et paroles timestampées pour obtenir une lecture musicale complète.');
    setText('.analysis-status-title', 'Analyse locale du fichier');
    setText('.v2-control-title', 'Moteur d’analyse avancée');
    setText('.terminal-title', 'LMNotebook Analysis Console v2.5');

    const badges = document.querySelectorAll('.platform-indicators .platform-badge');
    if (badges[0]) badges[0].lastChild.textContent = ' ANALYSE RAPIDE';
    if (badges[1]) badges[1].lastChild.textContent = ' ANALYSE PROFONDE';

    const connect = document.getElementById('v2-connect-btn');
    if (connect && !connect.dataset.humanLabel) {
      connect.innerHTML = '<i data-lucide="plug-zap"></i> Reconnecter';
      connect.dataset.humanLabel = '1';
    }

    const lyricsWrap = document.getElementById('semantic-lyrics-wrap');
    const lyricsInput = document.getElementById('semantic-lyrics-input');
    const lyricsName = document.getElementById('semantic-lyrics-name');
    const lyricsLabel = lyricsWrap?.querySelector('.semantic-lyrics-label small');
    if (lyricsWrap) lyricsWrap.classList.add('semantic-lyrics-human');
    if (lyricsName && !lyricsInput?.files?.length) lyricsName.textContent = 'Ajouter les paroles (optionnel)';
    if (lyricsLabel) lyricsLabel.textContent = 'TXT/LRC timestampé recommandé';

    window.lucide?.createIcons?.();
  }

  function polishSemanticResults() {
    const root = document.getElementById('v2-semantic-results');
    if (!root || root.classList.contains('hidden')) return;

    root.classList.add('semantic-humanized');
    root.querySelector('.semantic-title')?.replaceChildren(makeTitle());
    setTextWithin(root, '.semantic-sub', 'Structure, style, stems et paroles alignées dans le temps');

    const summary = [...root.querySelectorAll('.semantic-summary > div')];
    const summaryLabels = ['Grandes parties', 'Style dominant détecté', 'Paroles analysées', 'Couverture temporelle', 'Analyse stems via'];
    summary.forEach((card, index) => {
      const label = card.querySelector('span');
      if (label && summaryLabels[index]) label.textContent = summaryLabels[index];
    });

    const panels = root.querySelectorAll('.semantic-panel-head');
    panels.forEach(panel => {
      const strong = panel.querySelector('strong');
      const helper = panel.querySelector('span');
      if (!strong) return;
      const text = strong.textContent.trim();
      if (/Final Arrangement/i.test(text)) {
        strong.textContent = 'Déroulé du morceau';
        if (helper) helper.textContent = 'Clique sur une section pour comprendre son rôle.';
      } else if (/Arrangement Evidence/i.test(text)) {
        strong.textContent = 'Pourquoi cette lecture ?';
        if (helper) helper.textContent = 'Les principaux indices utilisés par le moteur.';
      } else if (/Lyrics \/ Neural Context/i.test(text)) {
        strong.textContent = 'Contexte paroles & style';
        if (helper) helper.textContent = 'Indices textuels et lecture Neural.';
      }
    });

    ensureViewSwitch(root);
    ensureHumanSummary(root);
    humanizeDetail(root);
    humanizeEvidenceRows(root);
    humanizeContext(root);
    humanizeDeclaredIntent(root);
  }

  function makeTitle() {
    const fragment = document.createDocumentFragment();
    const icon = document.createElement('i');
    icon.setAttribute('data-lucide', 'music-2');
    fragment.append(icon, document.createTextNode(' Lecture musicale du morceau'));
    return fragment;
  }

  function ensureViewSwitch(root) {
    if (root.querySelector('.semantic-view-switch')) return;
    const head = root.querySelector('.semantic-head');
    if (!head) return;
    const controls = document.createElement('div');
    controls.className = 'semantic-view-switch';
    controls.innerHTML = '<button type="button" data-sem-view="simple" class="active">Vue simple</button><button type="button" data-sem-view="advanced">Détails</button>';
    head.insertAdjacentElement('afterend', controls);
    root.classList.add('semantic-view-simple');
    controls.addEventListener('click', event => {
      const button = event.target.closest('[data-sem-view]');
      if (!button) return;
      const advanced = button.dataset.semView === 'advanced';
      root.classList.toggle('semantic-view-simple', !advanced);
      root.classList.toggle('semantic-view-advanced', advanced);
      controls.querySelectorAll('button').forEach(item => item.classList.toggle('active', item === button));
    });
  }

  function ensureHumanSummary(root) {
    let box = root.querySelector('.semantic-human-summary');
    if (!box) {
      box = document.createElement('section');
      box.className = 'semantic-human-summary';
      root.querySelector('.semantic-summary')?.insertAdjacentElement('afterend', box);
    }

    const labels = [...root.querySelectorAll('.semantic-timeline .semantic-block strong')].map(el => el.textContent.trim()).filter(Boolean);
    const genre = root.querySelector('.semantic-summary > div:nth-child(2) strong')?.textContent?.trim() || 'style hybride';
    const lyricMode = root.querySelector('.semantic-summary > div:nth-child(3) strong')?.textContent?.trim() || 'sans paroles';
    const choruses = labels.filter(x => /Chorus|Refrain/i.test(x)).length;
    const verses = labels.filter(x => /Verse|Couplet/i.test(x)).length;
    const pre = labels.filter(x => /Pre-Chorus|Pré-refrain/i.test(x)).length;
    const arrangement = labels.slice(0, 8).join(' → ') + (labels.length > 8 ? ' → …' : '');

    const firstSentence = labels.length
      ? `Le moteur retient ${labels.length} grandes parties${verses ? `, dont ${verses} couplet${verses > 1 ? 's' : ''}` : ''}${choruses ? ` et ${choruses} refrain${choruses > 1 ? 's' : ''}` : ''}${pre ? `, avec ${pre} pré-refrain${pre > 1 ? 's' : ''}` : ''}.`
      : 'La structure finale est en cours de préparation.';

    box.innerHTML = `
      <div class="semantic-human-summary-icon"><i data-lucide="sparkles"></i></div>
      <div>
        <span>Résumé de lecture</span>
        <p>${escapeHtml(firstSentence)} Le contexte dominant est <strong>${escapeHtml(genre)}</strong> et les paroles sont analysées en mode <strong>${escapeHtml(lyricMode)}</strong>.</p>
        ${arrangement ? `<small>${escapeHtml(arrangement)}</small>` : ''}
      </div>`;
  }

  function humanizeDetail(root) {
    const detail = root.querySelector('.semantic-detail');
    const copy = detail?.querySelector('.semantic-detail-copy');
    if (!copy) return;
    const label = copy.querySelector(':scope > span');
    if (label) label.textContent = 'Rôle détecté';

    const rawInfo = copy.querySelector(':scope > p');
    if (rawInfo) {
      rawInfo.textContent = rawInfo.textContent
        .replace(/source V2-CD\s*:/i, 'Lecture technique initiale :')
        .replace(/alt\s*:/i, 'Autres lectures possibles :');
    }

    const chips = [...copy.querySelectorAll('.semantic-chips span')];
    let list = copy.querySelector('.semantic-human-reasons');
    if (!list) {
      list = document.createElement('ul');
      list.className = 'semantic-human-reasons';
      copy.querySelector('.semantic-chips')?.insertAdjacentElement('beforebegin', list);
    }
    const reasons = chips.map(chip => humanizeEvidence(chip.textContent)).filter(Boolean).slice(0, 5);
    list.innerHTML = reasons.length
      ? reasons.map(text => `<li>${escapeHtml(text)}</li>`).join('')
      : '<li>Plusieurs indices audio et structurels convergent vers cette lecture.</li>';
  }

  function humanizeEvidenceRows(root) {
    root.querySelectorAll('.semantic-evidence-row p').forEach(paragraph => {
      const raw = paragraph.dataset.rawEvidence || paragraph.textContent;
      paragraph.dataset.rawEvidence = raw;
      const parts = raw.split('•').map(item => humanizeEvidence(item)).filter(Boolean);
      paragraph.textContent = parts.slice(0, 4).join(' ');
    });
  }

  function humanizeEvidence(raw) {
    const text = String(raw || '').trim();
    if (!text) return '';
    let match;
    if ((match = text.match(/vocals? élevés?\s*(\d+)%/i))) return `Les voix dominent clairement la section (${match[1]}%).`;
    if ((match = text.match(/vocals? faibles?\s*(\d+)%/i))) return `La voix reste en retrait (${match[1]}%).`;
    if ((match = text.match(/drums? élevés?\s*(\d+)%/i))) return `La rythmique est très présente (${match[1]}%).`;
    if ((match = text.match(/drums? faibles?\s*(\d+)%/i))) return `La rythmique reste discrète (${match[1]}%).`;
    if ((match = text.match(/bass(?:e)? élevée?\s*(\d+)%/i))) return `La basse porte fortement cette partie (${match[1]}%).`;
    if ((match = text.match(/bass(?:e)? faible\s*(\d+)%/i))) return `La basse reste légère (${match[1]}%).`;
    if ((match = text.match(/instrumental\/other dominant\s*(\d+)%/i))) return `L’instrumental domine l’espace sonore (${match[1]}%).`;
    if ((match = text.match(/répétition\s*([^()]+)\((\d+)%\)/i))) return `Cette partie revient ailleurs dans le morceau avec une forte similarité (${match[2]}%).`;
    if ((match = text.match(/lyrics\s*(\d+)\s*lignes/i))) return `${match[1]} lignes de paroles sont présentes dans cette section.`;
    if ((match = text.match(/lyrics répétées\s*(\d+)%/i))) return `Les paroles sont fortement répétitives (${match[1]}%), un bon indice de refrain ou de hook.`;
    if ((match = text.match(/hook textuel\s*(\d+)%/i))) return `Le texte présente un potentiel de hook élevé (${match[1]}%).`;
    if (/montée vers section suivante/i.test(text)) return 'L’énergie prépare clairement la section suivante.';
    if (/section distincte|nouveauté/i.test(text)) return 'Cette partie contraste avec ce qui l’entoure.';
    if (/contexte\s+hip-hop/i.test(text)) return 'Le contexte hip-hop oriente la lecture vers couplet/refrain plutôt que drop EDM.';
    if (/contexte\s+r&b/i.test(text)) return 'Le contexte R&B favorise une lecture vocale de type couplet/refrain.';
    if (/contexte\s+edm/i.test(text)) return 'Le contexte électronique renforce les lectures de type drop ou instrumental.';
    return text.endsWith('.') ? text : `${text}.`;
  }

  function humanizeContext(root) {
    const context = root.querySelector('.semantic-context');
    if (!context) return;
    context.querySelectorAll('h4').forEach(title => {
      if (/Neural Genre Context/i.test(title.textContent)) title.textContent = 'Style détecté par l’analyse Neural';
      if (/^Lyrics$/i.test(title.textContent)) title.textContent = 'Paroles';
    });
    const note = [...context.querySelectorAll('p')].find(p => /lyrics servent de preuve/i.test(p.textContent));
    if (note) note.textContent = 'Les paroles renforcent la lecture des refrains, hooks et répétitions, sans remplacer les frontières détectées dans l’audio.';
  }

  function humanizeDeclaredIntent(root) {
    const panel = root.querySelector('#semantic-declared-context');
    const data = window.LMNSemanticDeclaredMetadata || {};
    if (!panel || !Object.keys(data).length || panel.dataset.humanized === '1') return;
    panel.dataset.humanized = '1';

    const measuredBpm = findMeasuredBpm();
    const declaredBpm = parseFloat(String(data.BPM || '').replace(',', '.'));
    const bpmComparison = Number.isFinite(declaredBpm) && Number.isFinite(measuredBpm)
      ? `${declaredBpm} BPM déclarés · ${measuredBpm.toFixed(1)} BPM mesurés · écart ${Math.abs(measuredBpm - declaredBpm).toFixed(1)}`
      : (data.BPM || 'Non renseigné');

    panel.innerHTML = `
      <h4>Infos déclarées dans le fichier TXT</h4>
      <div class="declared-core-grid">
        ${declaredField('Titre', data.TITLE)}
        ${declaredField('Type', data.TYPE)}
        ${declaredField('Année', data.YEAR)}
        ${declaredField('Langue', data.LANGUAGE)}
        ${declaredField('BPM', bpmComparison)}
        ${declaredField('Énergie', data.ENERGY)}
      </div>
      ${declaredLong('Genre déclaré', data.GENRE)}
      ${declaredLong('Mood déclaré', data.MOOD)}
      ${declaredLong('Thèmes', data.THEMES)}
      ${declaredLong('Ère / direction', data.ERA)}
      ${data.STYLE_PROMPT ? `<details class="declared-details"><summary>Voir le style prompt déclaré</summary><p>${escapeHtml(data.STYLE_PROMPT)}</p></details>` : ''}
      <p class="declared-note">Ces informations servent de contexte et de comparaison. Elles ne remplacent jamais les mesures DSP, l’analyse Neural, V2-C ou V2-D.</p>`;
  }

  function declaredField(label, value) {
    if (!value) return '';
    return `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
  }

  function declaredLong(label, value) {
    if (!value) return '';
    return `<div class="declared-long"><span>${escapeHtml(label)}</span><p>${escapeHtml(value)}</p></div>`;
  }

  function findMeasuredBpm() {
    const candidates = [document.getElementById('metric-tempo')?.textContent || '', document.body?.innerText || ''];
    for (const text of candidates) {
      const match = String(text).match(/\b(\d{2,3}(?:\.\d+)?)\s*BPM\b/i);
      if (match) return Number(match[1]);
    }
    return NaN;
  }

  function setText(selector, text) {
    const element = document.querySelector(selector);
    if (element && element.textContent !== text) element.textContent = text;
  }

  function setTextWithin(root, selector, text) {
    const element = root.querySelector(selector);
    if (element && element.textContent !== text) element.textContent = text;
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[char]));
  }

  function boot() {
    polishStaticUI();
    polishSemanticResults();
    const observer = new MutationObserver(() => {
      polishStaticUI();
      polishSemanticResults();
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
    window.setInterval(() => {
      polishStaticUI();
      polishSemanticResults();
    }, 1200);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
