(() => {
  'use strict';

  const NS = window.SonicTraceCatalog = window.SonicTraceCatalog || {};
  const VERSION = 'v3.3.1';

  const FAMILIES = Object.freeze([
    { id:'vietnamese-asian', label:'Vietnamese / Asian', rx:/(vietnam|nhac\s*vang|nhac\s*tru\s*tinh|v[\s-]?pop|asian\s*ballad)/i },
    { id:'hip-hop-trap', label:'Hip-Hop / Trap', rx:/(hip[\s-]?hop|\brap\b|trap|drill|boom[\s-]?bap|phonk|g[\s-]?funk|grime)/i },
    { id:'bass-dubstep', label:'Bass / Dubstep', rx:/(dubstep|bass\s*music|brostep|drum\s*(?:and|&)\s*bass|\bdnb\b)/i },
    { id:'rnb-soul', label:'R&B / Soul', rx:/(r\s*&\s*b|\brnb\b|rhythm\s*(?:and|&)\s*blues|neo[\s-]?soul|\bsoul\b|quiet\s*storm)/i },
    { id:'pop-electronic-pop', label:'Pop / Electronic Pop', rx:/(electro[\s-]?pop|electronic\s*pop|synth[\s-]?pop|dance\s*pop|alt(?:ernative)?\s*pop|city\s*pop|\bpop\b)/i },
    { id:'electronic', label:'Electronic', rx:/(electronic|electronica|\bedm\b|house|techno|trance|garage|synthwave|ambient|idm|glitch)/i },
    { id:'reggae-dancehall', label:'Reggae / Dancehall', rx:/(reggae|dancehall|ragga|dub|ska)/i },
    { id:'lofi-chillhop', label:'Lo-fi / Chillhop', rx:/(lo[\s-]?fi|chill[\s-]?hop)/i },
    { id:'rock-alternative', label:'Rock / Alternative', rx:/(rock|metal|punk|shoegaze|post[\s-]?rock)/i },
    { id:'folk-world', label:'Folk / World', rx:/(folk|world|fado|afrobeat|highlife|zouk|traditional)/i },
    { id:'latin', label:'Latin', rx:/(latin|reggaeton|salsa|cumbia|bachata|tango|samba|bossa\s*nova)/i },
    { id:'jazz-classical', label:'Jazz / Classical / Screen', rx:/(jazz|classical|neo[\s-]?classical|soundtrack|score|cinematic)/i },
  ]);

  function normalize(value) {
    return String(value || '')
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[_/]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function score(item, fallback = 0.55) {
    const value = Number(item?.evidence_score ?? item?.ensemble_score ?? item?.score ?? item?.value ?? (Number(item?.percent) / 100));
    if (!Number.isFinite(value)) return fallback;
    return Math.max(0, Math.min(1, value > 1 ? value / 100 : value));
  }

  function genreAnalysis(track) {
    return track?.neural?.genreAnalysis
      || track?.neural?.genre_analysis
      || track?.semantic?.genreAnalysis
      || null;
  }

  function dimensions(track) {
    return genreAnalysis(track)?.dimensions || track?.semantic?.genreDimensions || null;
  }

  function familyDefinition(label) {
    const text = normalize(label);
    return FAMILIES.find(item => item.rx.test(text)) || null;
  }

  function primaryFamily(track) {
    const dims = dimensions(track);
    const dimensionFamily = normalize(dims?.family?.label || '');
    if (dimensionFamily) {
      const known = familyDefinition(dimensionFamily);
      if (known) return { ...known, score:score(dims?.family?.evidence, 0.88), source:'v3-dimensions' };
      return {
        id:`genre-${dimensionFamily.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}`,
        label:dimensionFamily,
        score:score(dims?.family?.evidence, 0.78),
        source:'v3-dimensions',
      };
    }

    // Legacy catalog entries do not have dimensions yet. Do NOT aggregate every
    // secondary label: use the first recognized high-ranked Neural label so a
    // weak Neo Soul/Pop resemblance cannot hijack a stronger Vietnamese result.
    const neural = Array.isArray(track?.neural?.genres) ? track.neural.genres.slice(0, 5) : [];
    for (let index = 0; index < neural.length; index++) {
      const label = normalize(neural[index]?.label ?? neural[index]?.name ?? neural[index]);
      const known = familyDefinition(label);
      if (known) return { ...known, score:score(neural[index], Math.max(0.25, 0.62 - index * 0.08)), source:'legacy-primary-evidence' };
    }

    const declared = track?.declared?.GENRE ?? track?.declared?.Genre ?? track?.declared?.genre ?? '';
    for (const label of String(declared).split(/[,;|]+/).map(x => x.trim()).filter(Boolean)) {
      const known = familyDefinition(label);
      if (known) return { ...known, score:0.38, source:'declared-fallback' };
    }
    return { id:'unclassified', label:'Non classé', score:0.15, source:'unclassified' };
  }

  function evidenceLabels(track) {
    const dims = dimensions(track);
    const labels = [];
    const push = value => { const text = String(value || '').trim(); if (text && !labels.includes(text)) labels.push(text); };
    push(dims?.style?.primary?.label);
    push(dims?.tradition?.primary?.label);
    push(dims?.form?.primary?.label);
    (track?.neural?.genres || []).slice(0, 4).forEach(item => push(item?.label ?? item?.name));
    return labels.slice(0, 4);
  }

  function analyze(tracks) {
    const groups = new Map();
    const assignments = {};

    (tracks || []).filter(Boolean).forEach(track => {
      const family = primaryFamily(track);
      let group = groups.get(family.id);
      if (!group) {
        group = { id:family.id, label:family.label, trackIds:[], count:0, weight:0, topLabels:[], sources:[] };
        groups.set(family.id, group);
      }
      group.trackIds.push(track.id);
      group.count += 1;
      group.weight += family.score;
      if (!group.sources.includes(family.source)) group.sources.push(family.source);
      evidenceLabels(track).forEach(label => { if (!group.topLabels.includes(label)) group.topLabels.push(label); });
      assignments[track.id] = [{ id:family.id, score:family.score, source:family.source }];
    });

    const output = [...groups.values()]
      .map(group => ({ ...group, weight:Number(group.weight.toFixed(3)), topLabels:group.topLabels.slice(0, 4) }))
      .sort((a, b) => b.count - a.count || b.weight - a.weight || a.label.localeCompare(b.label, 'fr'));
    return { count:output.length, groups:output, assignments, version:VERSION };
  }

  async function persistLatestDimensions(event) {
    const saved = event?.detail?.track;
    const analysis = NS.capture?.analyze?.neural?.genre_analysis;
    if (!saved?.id || !analysis?.dimensions || !NS.memory?.importCatalog) return;
    try {
      const track = typeof structuredClone === 'function' ? structuredClone(saved) : JSON.parse(JSON.stringify(saved));
      track.neural = track.neural || {};
      track.semantic = track.semantic || {};
      track.neural.genreAnalysis = analysis;
      track.semantic.genreAnalysis = analysis;
      track.semantic.genreDimensions = analysis.dimensions;
      track.semantic.genreFamily = analysis.dimensions?.family?.label || track.semantic.genreFamily || 'general';
      track.catalogAnalysisVersion = VERSION;
      await NS.memory.importCatalog({ schema:'sonictrace.catalog.export.v1', tracks:[track], projects:[] });
    } catch (error) {
      console.warn('[SonicTrace Catalog V3] dimension persistence failed:', error);
    }
  }

  function installOverride() {
    if (!NS.styleFamilies?.analyze) return false;
    if (NS.styleFamilies.analyze?.__sonictraceV3Accuracy) return true;
    analyze.__sonictraceV3Accuracy = true;
    NS.styleFamilies.analyze = analyze;
    document.documentElement.dataset.sonictraceCatalogTaxonomy = VERSION;
    return true;
  }

  const timer = window.setInterval(() => {
    if (installOverride()) window.clearInterval(timer);
  }, 40);
  window.setTimeout(() => window.clearInterval(timer), 12000);

  document.addEventListener('sonictrace:catalog-track-saved', persistLatestDimensions);
  document.addEventListener('sonictrace:catalog-imported', installOverride);

  NS.catalogAccuracy = { version:VERSION, analyze, primaryFamily, dimensions };
})();