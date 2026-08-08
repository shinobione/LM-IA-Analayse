(() => {
  'use strict';

  let installed = false;
  let originalPopulate = null;

  function boot() {
    if (installed) return true;
    const swot = document.querySelector('.swot-row');
    const report = document.querySelector('.report-row');
    if (!swot || !report || typeof window.populateData !== 'function') return false;

    installed = true;
    installLayout(swot, report);
    originalPopulate = window.populateData;
    window.populateData = function patchedPopulateData(data, isReal) {
      originalPopulate(data, isReal);
      renderHumanInsights(data, isReal);
    };
    renderWaitingState();
    window.lucide?.createIcons?.();
    return true;
  }

  function installLayout(swot, report) {
    swot.classList.add('human-insights-row');
    swot.innerHTML = `
      <div class="glass-card human-insight-card col-span-6">
        <div class="human-card-head">
          <div><span class="human-kicker">LECTURE RAPIDE</span><h3><i data-lucide="sparkles"></i> Ce que le morceau dégage</h3></div>
          <span class="human-note">interprétation du signal</span>
        </div>
        <div id="human-character" class="human-insight-list"></div>
      </div>
      <div class="glass-card human-insight-card col-span-6">
        <div class="human-card-head">
          <div><span class="human-kicker">ÉCOUTE CRITIQUE</span><h3><i data-lucide="headphones"></i> À vérifier à l’écoute</h3></div>
          <span class="human-note">actions utiles, pas des doublons</span>
        </div>
        <div id="human-listening-checks" class="human-insight-list"></div>
      </div>`;

    const existingReportCard = report.querySelector(':scope > .glass-card:not(.terminal-card)');
    const terminalCard = report.querySelector('.terminal-card');

    if (existingReportCard) {
      existingReportCard.className = 'glass-card col-span-8 human-production-card';
      existingReportCard.innerHTML = `
        <div class="human-card-head production-head">
          <div><span class="human-kicker">SYNTHÈSE</span><h3><i data-lucide="audio-waveform"></i> Lecture production</h3></div>
          <span class="human-note">ce que ça implique pour le morceau</span>
        </div>
        <div id="human-production-read" class="production-read"></div>`;
    }

    if (terminalCard) {
      const terminalOutput = terminalCard.querySelector('#terminal-output');
      terminalCard.className = 'glass-card col-span-4 human-tech-card';
      terminalCard.innerHTML = '';
      const details = document.createElement('details');
      details.className = 'human-tech-details';
      details.innerHTML = `
        <summary>
          <span><i data-lucide="terminal-square"></i><strong>Journal technique</strong></span>
          <small>Afficher seulement si besoin</small>
        </summary>`;
      if (terminalOutput) details.appendChild(terminalOutput);
      terminalCard.appendChild(details);
    }
  }

  function renderWaitingState() {
    const character = document.getElementById('human-character');
    const checks = document.getElementById('human-listening-checks');
    const production = document.getElementById('human-production-read');
    if (character) character.innerHTML = waiting('Le caractère du morceau apparaîtra ici après l’analyse express.');
    if (checks) checks.innerHTML = waiting('Les vérifications utiles seront proposées uniquement si le signal le justifie.');
    if (production) production.innerHTML = waiting('LMNotebook résumera ici la sensation générale du mix et les priorités d’écoute.');
  }

  function renderHumanInsights(data, isReal) {
    if (!isReal || !data?.raw) return renderWaitingState();

    const amplitude = data.raw.amplitude || {};
    const stereo = data.raw.stereo || {};
    const rhythm = data.raw.rhythm || {};
    const key = data.raw.key || {};
    const spectral = data.raw.spectral || {};

    const characterItems = buildCharacter(amplitude, stereo, rhythm, key, spectral);
    const checks = buildChecks(amplitude, stereo, rhythm, key, spectral);
    const production = buildProduction(amplitude, stereo, rhythm, key, spectral, data);

    const characterEl = document.getElementById('human-character');
    const checksEl = document.getElementById('human-listening-checks');
    const productionEl = document.getElementById('human-production-read');

    if (characterEl) characterEl.innerHTML = characterItems.map(item => insightItem(item.icon, item.title, item.text)).join('');
    if (checksEl) checksEl.innerHTML = checks.map(item => checkItem(item.level, item.title, item.text)).join('');
    if (productionEl) productionEl.innerHTML = production;
    window.lucide?.createIcons?.();
  }

  function buildCharacter(a, s, r, k, sp) {
    const bpm = num(r.bpm);
    const crest = num(a.crestDb);
    const width = num(s.width);
    const centroid = num(sp.centroid);
    const flatness = num(sp.flatness);

    const pace = bpm >= 155 ? ['Très mobile', 'Le morceau donne une sensation de vitesse nette et d’urgence.']
      : bpm >= 125 ? ['Énergique', 'Le mouvement rythmique est soutenu, avec une vraie sensation d’élan.']
      : bpm >= 95 ? ['En mouvement', 'Le groove reste actif sans donner une impression de course permanente.']
      : ['Posé', 'Le tempo laisse davantage d’espace au groove, aux voix et aux textures.'];

    const dynamics = crest >= 14 ? ['Très respirant', 'Les écarts entre corps du son et transitoires sont marqués : le mix garde beaucoup de respiration.']
      : crest >= 9 ? ['Contrôlé mais vivant', 'La dynamique reste lisible : suffisamment tenue, sans écraser complètement les impacts.']
      : ['Dense', 'Le signal paraît serré et compact, avec moins d’écart entre niveau moyen et impacts.'];

    const space = width >= .35 ? ['Large', 'L’image stéréo donne une vraie sensation d’ouverture autour du centre.']
      : width >= .15 ? ['Centrée mais ouverte', 'Le centre reste solide, avec assez de côté pour donner de l’espace.']
      : ['Très centrée', 'La masse du morceau reste proche du centre, avec peu d’éléments latéraux.'];

    const tone = centroid >= 6500 ? ['Claire / brillante', 'Le haut du spectre ressort fortement et apporte beaucoup de présence.']
      : centroid >= 3500 ? ['Équilibrée', 'Le centre de gravité spectral reste polyvalent, sans excès évident vers le sombre ou le brillant.']
      : ['Sombre / chaude', 'Le morceau privilégie le bas et le médium plutôt qu’une forte brillance.'];

    const texture = flatness >= .35 ? ['Texturée', 'Le spectre comporte une part notable de matière diffuse / bruitée, pas seulement des composantes tonales.']
      : ['Définie', 'Le contenu spectral reste plutôt structuré et tonal que diffus ou bruité.'];

    return [
      { icon:'gauge', title: pace[0], text: pace[1] },
      { icon:'activity', title: dynamics[0], text: dynamics[1] },
      { icon:'move-horizontal', title: space[0], text: space[1] },
      { icon:'sun-medium', title: tone[0], text: tone[1] },
      { icon:'waves', title: texture[0], text: texture[1] },
    ];
  }

  function buildChecks(a, s, r, k, sp) {
    const out = [];
    const peak = num(a.peakDb);
    const crest = num(a.crestDb);
    const clipping = num(a.clippingPercent);
    const correlation = num(s.correlation);
    const width = num(s.width);
    const balance = Math.abs(num(s.balance));
    const centroid = num(sp.centroid);
    const tempoConf = num(r.confidence);
    const keyConf = num(k.confidence);

    if (clipping > .005 || peak > -.8) out.push({ level:'warn', title:'Garde un œil sur les crêtes', text:'Le signal laisse peu de marge en haut. Vérifie le limiter et les crêtes inter-sample avant export final.' });
    if (crest < 7.5) out.push({ level:'warn', title:'Réécoute le punch', text:'Le mix semble très dense. Surveille surtout la frappe kick/snare et la lisibilité des attaques à volume faible.' });
    if (correlation < .25) out.push({ level:'warn', title:'Fais un passage en mono', text:'L’ouverture stéréo peut devenir fragile lors d’une réduction mono. Contrôle les éléments qui disparaissent ou changent de niveau.' });
    if (balance > .12) out.push({ level:'warn', title:'Contrôle le centre de gravité', text:'La balance gauche/droite paraît sensible. Vérifie casque + enceintes pour t’assurer qu’elle est volontaire.' });
    if (width < .08) out.push({ level:'info', title:'Décide si ce centre très compact est voulu', text:'Le morceau est très recentré. Ça peut être efficace, mais écoute si pads, doubles ou ambiances gagneraient à respirer davantage.' });
    if (centroid > 7000) out.push({ level:'info', title:'Teste la fatigue dans le haut', text:'Le haut du spectre est très présent. Vérifie les sifflantes, hats et textures brillantes sur écouteurs agressifs.' });
    if (centroid < 2500) out.push({ level:'info', title:'Vérifie la lisibilité sur petits systèmes', text:'Le morceau est plutôt sombre. Contrôle que voix, snare et éléments de définition restent lisibles sur téléphone / laptop.' });
    if (tempoConf < .55) out.push({ level:'info', title:'Ne prends pas le BPM pour parole d’évangile', text:'Le rythme est moins évident pour le détecteur. Si le tempo doit servir à un grid ou à du sync, confirme-le à l’oreille.' });
    if (keyConf < .45) out.push({ level:'info', title:'Tonalité à considérer comme indicative', text:'La couleur tonale est ambiguë. Évite de baser une décision harmonique importante uniquement sur cette estimation.' });

    if (!out.length) out.push({ level:'good', title:'Rien de prioritaire dans le scan navigateur', text:'Aucun drapeau évident ne ressort ici. La meilleure suite est une écoute comparative avec 1 ou 2 références proches, à volume égal.' });
    return out.slice(0, 4);
  }

  function buildProduction(a, s, r, k, sp, data) {
    const bpm = num(r.bpm);
    const crest = num(a.crestDb);
    const centroid = num(sp.centroid);
    const width = num(s.width);
    const tempoConf = Math.round(num(r.confidence) * 100);
    const keyConf = Math.round(num(k.confidence) * 100);

    const energyWord = bpm >= 150 ? 'nerveux et très mobile' : bpm >= 120 ? 'énergique et entraînant' : bpm >= 90 ? 'groovy et mesuré' : 'posé et spacieux';
    const dynWord = crest >= 14 ? 'très aéré' : crest >= 9 ? 'équilibré entre contrôle et respiration' : 'dense et fortement tenu';
    const toneWord = centroid >= 6500 ? 'brillant et très présent' : centroid >= 3500 ? 'plutôt équilibré' : 'sombre et centré sur le bas-médium';
    const spaceWord = width >= .35 ? 'large' : width >= .15 ? 'modérément ouvert' : 'très centré';

    const trust = tempoConf >= 75 && keyConf >= 60
      ? 'Les estimations rythmiques et tonales sont suffisamment stables pour servir de repère.'
      : tempoConf < 55 && keyConf < 45
        ? 'Le morceau résiste un peu aux estimations automatiques : garde le BPM et la tonalité comme indications, pas comme vérités absolues.'
        : tempoConf < 55
          ? 'Le tempo mérite une vérification manuelle si tu comptes l’utiliser pour un grid précis.'
          : 'La tonalité est la partie la moins certaine de cette lecture ; le rythme est plus fiable.';

    const priority = pickPriority(a, s, r, k, sp);

    return `
      <div class="production-lead">
        <span class="production-label">Impression générale</span>
        <p>Le morceau paraît <strong>${escapeHtml(energyWord)}</strong>, avec un mix <strong>${escapeHtml(dynWord)}</strong>, une couleur <strong>${escapeHtml(toneWord)}</strong> et une image stéréo <strong>${escapeHtml(spaceWord)}</strong>.</p>
      </div>
      <div class="production-grid">
        <div class="production-note"><span>Confiance de lecture</span><p>${escapeHtml(trust)}</p></div>
        <div class="production-note priority"><span>Écoute prioritaire</span><p>${escapeHtml(priority)}</p></div>
      </div>
      <div class="production-foot">Les mesures chiffrées restent disponibles plus haut ; ici LMNotebook ne garde que ce qui aide à décider quoi écouter ensuite.</div>`;
  }

  function pickPriority(a, s, r, k, sp) {
    const clipping = num(a.clippingPercent);
    const peak = num(a.peakDb);
    const crest = num(a.crestDb);
    const correlation = num(s.correlation);
    const centroid = num(sp.centroid);
    if (clipping > .005 || peak > -.8) return 'Commence par les crêtes et le limiteur : c’est le point qui peut le plus vite créer un problème à l’export.';
    if (correlation < .25) return 'Commence par un contrôle mono : c’est là que l’équilibre risque le plus de bouger.';
    if (crest < 7.5) return 'Commence par le punch à faible volume : kick, snare et attaques doivent rester lisibles malgré la densité.';
    if (centroid > 7000) return 'Commence par une écoute sur un système brillant pour vérifier la fatigue dans les aigus.';
    if (centroid < 2500) return 'Commence par un téléphone ou un laptop pour vérifier que le morceau garde assez de définition.';
    return 'Commence par une comparaison A/B à volume égal avec une référence proche : équilibre tonal, punch et image stéréo sont les trois choses à juger.';
  }

  function insightItem(icon, title, text) {
    return `<div class="human-insight-item"><div class="human-icon"><i data-lucide="${icon}"></i></div><div><strong>${escapeHtml(title)}</strong><p>${escapeHtml(text)}</p></div></div>`;
  }

  function checkItem(level, title, text) {
    const icon = level === 'warn' ? 'triangle-alert' : level === 'good' ? 'circle-check' : 'ear';
    return `<div class="human-check ${level}"><i data-lucide="${icon}"></i><div><strong>${escapeHtml(title)}</strong><p>${escapeHtml(text)}</p></div></div>`;
  }

  function waiting(text) {
    return `<div class="human-waiting"><i data-lucide="circle-dashed"></i><span>${escapeHtml(text)}</span></div>`;
  }

  function num(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n : 0;
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[ch]));
  }

  const timer = setInterval(() => {
    if (boot()) clearInterval(timer);
  }, 30);
  window.setTimeout(() => clearInterval(timer), 8000);
})();
