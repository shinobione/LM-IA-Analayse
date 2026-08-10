(() => {
  'use strict';

  const NS = window.SonicTraceCatalog = window.SonicTraceCatalog || {};
  const FAMILY_PALETTE = Object.freeze({
    'hip-hop-trap': '#55e2b2',
    'bass-dubstep': '#4caeff',
    'genre-synthwave': '#9b6cff',
    'rnb-soul': '#d85bd4',
    'pop-electronic-pop': '#ff667f',
    'electronic': '#2dd6d2',
    'reggae-dancehall': '#f2c85b',
    'lofi-chillhop': '#82cb79',
    'rock-alternative': '#ff9f5f',
    'unclassified': '#82979e',
  });

  let timer = 0;
  let running = false;
  let observer = null;

  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({
      '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#039;'
    })[char]);
  }

  function stableFallbackColor(id) {
    const value = String(id || 'unclassified');
    let hash = 0;
    for (let i = 0; i < value.length; i++) hash = ((hash << 5) - hash + value.charCodeAt(i)) | 0;
    const hue = ((Math.abs(hash) % 280) + 35) % 360;
    return `hsl(${hue} 70% 62%)`;
  }

  function colorFor(id) {
    return FAMILY_PALETTE[id] || stableFallbackColor(id);
  }

  function primaryFamily(trackId, result) {
    return result?.assignments?.[trackId]?.[0]?.id || 'unclassified';
  }

  function familyLabel(id, result) {
    return result?.groups?.find(group => group.id === id)?.label || (id === 'unclassified' ? 'Non classé' : id);
  }

  function setText(node, value) {
    if (node && node.textContent !== value) node.textContent = value;
  }

  function statByLabel(root, labels) {
    const accepted = labels.map(label => label.toLowerCase());
    return [...root.children].find(card => accepted.includes(card.querySelector('span')?.textContent?.trim().toLowerCase())) || null;
  }

  function patchStats(result) {
    const root = document.getElementById('st-catalog-stats');
    if (!root) return;

    const acoustic = statByLabel(root, ['Familles sonores', 'Zones acoustiques']);
    if (acoustic && !acoustic.matches('[data-st-style-families-stat]')) {
      setText(acoustic.querySelector('span'), 'Zones acoustiques');
      setText(acoustic.querySelector('small'), 'voisinages de proximité CLAP');
      acoustic.dataset.acousticZones = 'true';
    }

    const families = root.querySelector('[data-st-style-families-stat]');
    if (families) {
      setText(families.querySelector('span'), 'Familles sonores');
      setText(families.querySelector('strong'), String(result?.count || 0));
      setText(families.querySelector('small'), 'genres Neural consolidés');
    }

    const outliers = statByLabel(root, ['Outliers']);
    if (outliers) setText(outliers.querySelector('small'), 'hors voisinages principaux');
  }

  function patchFamilyPanel(result) {
    const panel = document.getElementById('st-style-family-panel');
    if (!panel) return;
    setText(panel.querySelector('.st-style-family-head strong'), 'Familles sonores');
    setText(panel.querySelector('.st-style-family-head span'), 'Couleur canonique par univers sonore • issue des genres Neural mémorisés');

    const cards = [...panel.querySelectorAll('.st-style-family-card')];
    cards.forEach((card, index) => {
      const group = result?.groups?.[index];
      if (!group) return;
      card.dataset.familyId = group.id;
      card.style.setProperty('--family-color', colorFor(group.id));
      const dot = card.querySelector('i');
      if (dot) {
        dot.dataset.familyId = group.id;
        dot.style.setProperty('--family-color', colorFor(group.id));
      }
    });
  }

  function patchMap(result) {
    const mapPanel = document.querySelector('.st-map-panel');
    const head = mapPanel?.querySelector('.st-panel-head');
    if (head) {
      setText(head.querySelector('span'), 'Position = proximité CLAP • couleur = famille sonore');
      setText(head.querySelector('small'), 'Zones acoustiques = voisinages, pas genres');
    }

    document.querySelectorAll('#st-catalog-map [data-track-id]').forEach(point => {
      const trackId = point.dataset.trackId;
      const familyId = primaryFamily(trackId, result);
      point.dataset.familyId = familyId;
      point.style.setProperty('--family-color', colorFor(familyId));
      point.setAttribute('aria-label', `${point.textContent?.trim() || 'Morceau'} • ${familyLabel(familyId, result)}`);
    });
  }

  function patchTrackList(result) {
    document.querySelectorAll('#st-track-list [data-track-row]').forEach(row => {
      const familyId = primaryFamily(row.dataset.trackRow, result);
      row.dataset.familyId = familyId;
      const dot = row.querySelector('.st-cluster-dot');
      if (!dot) return;
      dot.dataset.familyId = familyId;
      dot.style.setProperty('--family-color', colorFor(familyId));
      dot.title = familyLabel(familyId, result);
    });
  }

  function zoneName(index) {
    return String.fromCharCode(65 + Math.max(0, Math.min(25, index)));
  }

  function patchAcousticLegend() {
    document.querySelectorAll('#st-cluster-legend button').forEach((button, index) => {
      const span = button.querySelector('span');
      const count = Number(button.querySelector('b')?.textContent || 0);
      const name = zoneName(index);
      button.dataset.acousticZone = name;
      button.title = `Zone acoustique ${name} • cluster de proximité CLAP • ${count} titre${count > 1 ? 's' : ''}`;
      setText(span, `Zone acoustique ${name}`);
      const dot = button.querySelector('i');
      if (dot) dot.removeAttribute('style');
    });
  }

  function patchInsights(result) {
    const root = document.getElementById('st-insights-panel');
    if (!root) return;
    const head = root.querySelector('.st-panel-head span');
    setText(head, 'familles sonores • redondances • outliers • ponts acoustiques');

    const sections = [...root.querySelectorAll('.st-insight-groups > section')];
    const families = sections[0];
    if (families) {
      setText(families.querySelector('h4'), 'Familles sonores');
      const items = result?.groups || [];
      const html = items.length
        ? `<h4>Familles sonores</h4>${items.map(group => `<p><i class="st-family-dot" data-family-id="${esc(group.id)}" style="--family-color:${esc(colorFor(group.id))}"></i><b>${esc(group.label)}</b><span>${group.count} titre${group.count > 1 ? 's' : ''}</span></p>`).join('')}`
        : '<h4>Familles sonores</h4><small>—</small>';
      if (families.innerHTML !== html) families.innerHTML = html;
    }

    const bridges = sections[3];
    bridges?.querySelectorAll('span').forEach(span => {
      const next = span.textContent.replace(/relie\s+(\d+)\s+familles/i, 'relie $1 zones acoustiques');
      setText(span, next);
    });
  }

  function applyVisualLanguage() {
    if (running) return;
    const result = NS.styleFamilies?.current;
    if (!result) return;
    running = true;
    try {
      patchStats(result);
      patchFamilyPanel(result);
      patchMap(result);
      patchTrackList(result);
      patchAcousticLegend();
      patchInsights(result);
      document.documentElement.dataset.sonictraceFamilyLanguage = 'build05';
      NS.familyVisualLanguage = { colorFor, primaryFamily: trackId => primaryFamily(trackId, result), palette:FAMILY_PALETTE };
    } catch (error) {
      console.error('[SonicTrace Build 05] family visual language failed:', error);
    } finally {
      running = false;
    }
  }

  function schedule(delay = 0) {
    window.clearTimeout(timer);
    timer = window.setTimeout(applyVisualLanguage, delay);
  }

  function relevantTarget(target) {
    const element = target instanceof Element ? target : target?.parentElement;
    return Boolean(element?.closest?.('#st-catalog-stats,#st-style-family-panel,#st-catalog-map,#st-track-list,#st-cluster-legend,#st-insights-panel,.st-map-panel'));
  }

  function installObserver() {
    if (observer || !document.documentElement) return;
    observer = new MutationObserver(records => {
      if (records.some(record => relevantTarget(record.target) || [...record.addedNodes].some(node => node instanceof Element && relevantTarget(node)))) schedule(0);
    });
    observer.observe(document.documentElement, { childList:true, subtree:true });
  }

  ['sonictrace:catalog-track-saved','sonictrace:catalog-track-deleted','sonictrace:catalog-cleared','sonictrace:catalog-imported']
    .forEach(name => document.addEventListener(name, () => schedule(30)));
  document.addEventListener('click', event => {
    if (event.target.closest?.('[data-st-view="catalog"],[data-track-id],[data-select-track],[data-cluster-id]')) schedule(30);
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { installObserver(); schedule(220); }, { once:true });
  } else {
    installObserver();
    schedule(220);
  }
})();
