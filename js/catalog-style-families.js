(() => {
  'use strict';

  const NS = window.SonicTraceCatalog = window.SonicTraceCatalog || {};
  const STYLE_DEFINITIONS = Object.freeze([
    { id:'hip-hop-trap', label:'Hip-Hop / Trap', rx:/(?:^|\b)(hip[\s-]?hop|rap|trap|drill|boom[\s-]?bap)(?:\b|$)/i },
    { id:'rnb-soul', label:'R&B / Soul', rx:/(?:^|\b)(r\s*&\s*b|rnb|rhythm\s*(?:and|&)\s*blues|neo[\s-]?soul|soul)(?:\b|$)/i },
    { id:'bass-dubstep', label:'Bass / Dubstep', rx:/(?:^|\b)(dubstep|bass\s*music|brostep|grime|drum\s*(?:and|&)\s*bass|dnb)(?:\b|$)/i },
    { id:'pop-electronic-pop', label:'Pop / Electronic Pop', rx:/(?:^|\b)(electro[\s-]?pop|electronic\s*pop|synth[\s-]?pop|dance\s*pop|alt(?:ernative)?\s*pop|pop)(?:\b|$)/i },
    { id:'electronic', label:'Electronic', rx:/(?:^|\b)(electronic|electronica|edm|electro|house|techno|trance|garage)(?:\b|$)/i },
    { id:'reggae-dancehall', label:'Reggae / Dancehall', rx:/(?:^|\b)(reggae|dancehall|ragga)(?:\b|$)/i },
    { id:'lofi-chillhop', label:'Lo-fi / Chillhop', rx:/(?:^|\b)(lo[\s-]?fi|chill[\s-]?hop)(?:\b|$)/i },
    { id:'rock-alternative', label:'Rock / Alternative', rx:/(?:^|\b)(rock|alternative|indie\s*rock|post[\s-]?rock)(?:\b|$)/i },
  ]);

  let refreshTimer = 0;
  let observer = null;

  function normalizedLabel(value) {
    return String(value || '')
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[_/]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function rankingScore(item, fallback = 0.55) {
    const value = Number(item?.score ?? item?.value ?? (Number(item?.percent) / 100));
    if (!Number.isFinite(value)) return fallback;
    return Math.max(0, Math.min(1, value > 1 ? value / 100 : value));
  }

  function declaredGenres(track) {
    const value = track?.declared?.GENRE ?? track?.declared?.Genre ?? track?.declared?.genre;
    if (Array.isArray(value)) return value;
    return String(value || '').split(/[,;|]+/).map(item => item.trim()).filter(Boolean);
  }

  function genreEvidence(track) {
    const neural = Array.isArray(track?.neural?.genres) ? track.neural.genres.slice(0, 6) : [];
    const evidence = neural
      .map((item, index) => ({
        label: normalizedLabel(item?.label ?? item?.name ?? item),
        score: rankingScore(item, Math.max(0.20, 0.58 - index * 0.08)),
        source: 'neural',
        rank: index,
      }))
      .filter(item => item.label);

    if (!evidence.length) {
      declaredGenres(track).slice(0, 4).forEach((label, index) => evidence.push({
        label: normalizedLabel(label),
        score: Math.max(0.18, 0.42 - index * 0.07),
        source: 'declared',
        rank: index,
      }));
    }
    return evidence;
  }

  function definitionFor(label) {
    return STYLE_DEFINITIONS.find(definition => definition.rx.test(label)) || null;
  }

  function analyze(tracks) {
    const valid = (tracks || []).filter(Boolean);
    const groups = new Map(STYLE_DEFINITIONS.map(definition => [definition.id, {
      id: definition.id,
      label: definition.label,
      trackIds: new Set(),
      weight: 0,
      labels: new Map(),
      sources: new Set(),
    }]));
    const unmatched = new Map();
    const assignments = {};

    valid.forEach(track => {
      const perTrack = new Map();
      const evidence = genreEvidence(track);
      evidence.forEach(item => {
        const definition = definitionFor(item.label);
        if (definition) {
          const previous = perTrack.get(definition.id) || 0;
          perTrack.set(definition.id, Math.max(previous, item.score));
          const group = groups.get(definition.id);
          group.labels.set(item.label, (group.labels.get(item.label) || 0) + item.score);
          group.sources.add(item.source);
          return;
        }

        const key = item.label.toLowerCase();
        const fallback = unmatched.get(key) || { label:item.label, trackIds:new Set(), weight:0, labels:new Map(), sources:new Set() };
        fallback.trackIds.add(track.id);
        fallback.weight += item.score;
        fallback.labels.set(item.label, (fallback.labels.get(item.label) || 0) + item.score);
        fallback.sources.add(item.source);
        unmatched.set(key, fallback);
      });

      const ordered = [...perTrack.entries()].sort((a,b) => b[1] - a[1]);
      const accepted = ordered.filter(([, score], index) => index === 0 || score >= 0.22).slice(0, 3);
      assignments[track.id] = accepted.map(([id, score]) => ({ id, score }));
      accepted.forEach(([id, score]) => {
        const group = groups.get(id);
        group.trackIds.add(track.id);
        group.weight += score;
      });
    });

    for (const [key, fallback] of unmatched) {
      if (fallback.trackIds.size < 2 && fallback.weight < 1.15) continue;
      const id = `genre-${key.replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}`;
      groups.set(id, {
        id,
        label: titleCase(fallback.label),
        trackIds: fallback.trackIds,
        weight: fallback.weight,
        labels: fallback.labels,
        sources: fallback.sources,
      });
      fallback.trackIds.forEach(trackId => {
        assignments[trackId] = assignments[trackId] || [];
        assignments[trackId].push({ id, score: Math.min(1, fallback.weight / Math.max(1, fallback.trackIds.size)) });
      });
    }

    const output = [...groups.values()]
      .filter(group => group.trackIds.size > 0)
      .map(group => ({
        id: group.id,
        label: group.label,
        trackIds: [...group.trackIds],
        count: group.trackIds.size,
        weight: Number(group.weight.toFixed(3)),
        topLabels: [...group.labels.entries()].sort((a,b) => b[1] - a[1]).slice(0, 4).map(([label]) => label),
        sources: [...group.sources],
      }))
      .sort((a,b) => b.count - a.count || b.weight - a.weight || a.label.localeCompare(b.label, 'fr'));

    return { count:output.length, groups:output, assignments };
  }

  function titleCase(value) {
    return normalizedLabel(value).replace(/\b\w/g, letter => letter.toUpperCase());
  }

  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#039;' })[char]);
  }

  function findStat(root, label) {
    return [...root.children].find(card => card.querySelector('span')?.textContent?.trim().toLowerCase() === label.toLowerCase()) || null;
  }

  function renderStats(result) {
    const root = document.getElementById('st-catalog-stats');
    if (!root) return;

    const oldFamilies = findStat(root, 'Familles sonores');
    if (oldFamilies) {
      const label = oldFamilies.querySelector('span');
      const note = oldFamilies.querySelector('small');
      if (label) label.textContent = 'Zones acoustiques';
      if (note) note.textContent = 'clusters de proximité CLAP';
      oldFamilies.dataset.acousticZones = 'true';
    }

    let card = root.querySelector('[data-st-style-families-stat]');
    if (!card) {
      card = document.createElement('div');
      card.dataset.stStyleFamiliesStat = 'true';
      card.innerHTML = '<span>Familles stylistiques</span><strong>0</strong><small>genres Neural consolidés</small>';
      if (oldFamilies?.nextSibling) root.insertBefore(card, oldFamilies.nextSibling);
      else root.appendChild(card);
    }
    card.querySelector('strong').textContent = String(result.count);
  }

  function renderStylePanel(result, tracks) {
    const catalog = document.getElementById('sonictrace-catalog-view');
    const layout = catalog?.querySelector('.st-catalog-layout');
    if (!catalog || !layout) return;

    let panel = document.getElementById('st-style-family-panel');
    if (!panel) {
      panel = document.createElement('article');
      panel.id = 'st-style-family-panel';
      panel.className = 'st-style-family-panel';
      layout.insertAdjacentElement('beforebegin', panel);
    }

    const trackById = new Map((tracks || []).map(track => [track.id, track]));
    panel.innerHTML = `
      <div class="st-style-family-head">
        <div><strong>Familles stylistiques</strong><span>Genres Neural consolidés — distincts des zones acoustiques de la carte</span></div>
        <b>${result.count}</b>
      </div>
      <div class="st-style-family-grid">
        ${result.groups.length ? result.groups.map((group, index) => {
          const names = group.trackIds.slice(0, 4).map(id => trackById.get(id)?.title).filter(Boolean);
          const evidence = group.topLabels.slice(0, 3).join(' · ');
          return `<section class="st-style-family-card" style="--style-index:${index}">
            <div><i></i><strong>${esc(group.label)}</strong><b>${group.count}</b></div>
            <small>${esc(evidence || 'genre Neural')}</small>
            <p>${esc(names.join(' · ') || '—')}${group.trackIds.length > names.length ? ` · +${group.trackIds.length - names.length}` : ''}</p>
          </section>`;
        }).join('') : '<p class="st-style-family-empty">Pas encore assez de genres Neural exploitables pour former une famille stylistique.</p>'}
      </div>`;
  }

  function relabelAcousticLegend() {
    document.querySelectorAll('#st-cluster-legend button').forEach((button, index) => {
      const span = button.querySelector('span');
      if (!span) return;
      const raw = span.dataset.rawAcousticLabel || span.textContent.trim().replace(/^Zone acoustique \d+\s*·\s*/i, '');
      span.dataset.rawAcousticLabel = raw;
      const expected = `Zone acoustique ${index + 1} · ${raw}`;
      if (span.textContent !== expected) span.textContent = expected;
    });
  }

  async function refresh() {
    if (!NS.memory?.getTracks) return;
    try {
      const tracks = await NS.memory.getTracks();
      const result = analyze(tracks);
      NS.styleFamilies.current = result;
      renderStats(result);
      renderStylePanel(result, tracks);
      relabelAcousticLegend();
    } catch (error) {
      console.error('[SonicTrace Style Families] refresh failed:', error);
    }
  }

  function scheduleRefresh(delay = 0) {
    window.clearTimeout(refreshTimer);
    refreshTimer = window.setTimeout(refresh, delay);
  }

  function installObserver() {
    if (observer || !document.documentElement) return;
    observer = new MutationObserver(records => {
      if (!records.some(record => [...record.addedNodes].some(node => node instanceof Element && (
        node.id === 'sonictrace-catalog-view'
        || node.id === 'st-catalog-stats'
        || node.id === 'st-cluster-legend'
        || node.querySelector?.('#st-catalog-stats,#st-cluster-legend')
      )))) return;
      scheduleRefresh(0);
    });
    observer.observe(document.documentElement, { childList:true, subtree:true });
  }

  NS.styleFamilies = { analyze, current:{ count:0, groups:[], assignments:{} }, definitions:STYLE_DEFINITIONS };

  ['sonictrace:catalog-track-saved','sonictrace:catalog-track-deleted','sonictrace:catalog-cleared','sonictrace:catalog-imported']
    .forEach(name => document.addEventListener(name, () => scheduleRefresh(20)));
  document.addEventListener('click', event => {
    if (event.target.closest?.('[data-st-view="catalog"]')) scheduleRefresh(60);
  });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => { installObserver(); scheduleRefresh(120); }, { once:true });
  else { installObserver(); scheduleRefresh(120); }
})();
