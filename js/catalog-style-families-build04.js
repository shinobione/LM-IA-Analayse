(() => {
  'use strict';

  const NS = window.SonicTraceCatalog = window.SonicTraceCatalog || {};
  let timer = 0;
  let running = false;
  let observer = null;

  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({
      '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#039;'
    })[char]);
  }

  function setText(node, value) {
    if (node && node.textContent !== value) node.textContent = value;
  }

  function statByLabel(root, label) {
    return [...root.children].find(card => card.querySelector('span')?.textContent?.trim().toLowerCase() === label.toLowerCase()) || null;
  }

  function acousticStat(root) {
    return root.querySelector('[data-acoustic-zones="true"]')
      || statByLabel(root, 'Zones acoustiques')
      || [...root.children].find(card => !card.matches('[data-st-style-families-stat]') && card.querySelector('span')?.textContent?.trim().toLowerCase() === 'familles sonores')
      || null;
  }

  function renderStats(result) {
    const root = document.getElementById('st-catalog-stats');
    if (!root) return false;

    const acoustic = acousticStat(root);
    if (acoustic) {
      setText(acoustic.querySelector('span'), 'Zones acoustiques');
      setText(acoustic.querySelector('small'), 'voisinages de proximité CLAP');
      acoustic.dataset.acousticZones = 'true';
    }

    let styleStat = root.querySelector('[data-st-style-families-stat]');
    if (!styleStat) {
      styleStat = document.createElement('div');
      styleStat.dataset.stStyleFamiliesStat = 'true';
      styleStat.innerHTML = '<span>Familles sonores</span><strong>0</strong><small>genres Neural consolidés</small>';
      if (acoustic?.nextSibling) root.insertBefore(styleStat, acoustic.nextSibling);
      else root.appendChild(styleStat);
    }
    setText(styleStat.querySelector('span'), 'Familles sonores');
    setText(styleStat.querySelector('strong'), String(result.count));
    setText(styleStat.querySelector('small'), 'genres Neural consolidés');
    return true;
  }

  function renderPanel(result, tracks) {
    const catalog = document.getElementById('sonictrace-catalog-view');
    const layout = catalog?.querySelector('.st-catalog-layout');
    if (!catalog || !layout) return false;

    let panel = document.getElementById('st-style-family-panel');
    if (!panel) {
      panel = document.createElement('article');
      panel.id = 'st-style-family-panel';
      panel.className = 'st-style-family-panel';
      layout.insertAdjacentElement('beforebegin', panel);
    }

    const trackById = new Map((tracks || []).map(track => [track.id, track]));
    const signature = JSON.stringify(result.groups.map(group => [group.id, group.count, group.weight, group.trackIds]));
    if (panel.dataset.familySignature === signature) {
      setText(panel.querySelector('.st-style-family-head strong'), 'Familles sonores');
      setText(panel.querySelector('.st-style-family-head span'), 'Genres Neural consolidés — distincts des zones acoustiques CLAP');
      return true;
    }

    panel.innerHTML = `
      <div class="st-style-family-head">
        <div><strong>Familles sonores</strong><span>Genres Neural consolidés — distincts des zones acoustiques CLAP</span></div>
        <b>${result.count}</b>
      </div>
      <div class="st-style-family-grid">
        ${result.groups.length ? result.groups.map((group, index) => {
          const names = group.trackIds.slice(0, 5).map(id => trackById.get(id)?.title).filter(Boolean);
          const evidence = group.topLabels.slice(0, 4).join(' · ');
          return `<section class="st-style-family-card" style="--style-index:${index}">
            <div><i></i><strong>${esc(group.label)}</strong><b>${group.count}</b></div>
            <small>${esc(evidence || 'genre Neural')}</small>
            <p>${esc(names.join(' · ') || '—')}${group.trackIds.length > names.length ? ` · +${group.trackIds.length - names.length}` : ''}</p>
          </section>`;
        }).join('') : '<p class="st-style-family-empty">Aucune famille sonore exploitable dans les genres Neural mémorisés.</p>'}
      </div>`;
    panel.dataset.familySignature = signature;
    return true;
  }

  function zoneName(index) {
    return String.fromCharCode(65 + Math.max(0, Math.min(25, index)));
  }

  function relabelLegend() {
    document.querySelectorAll('#st-cluster-legend button').forEach((button, index) => {
      const span = button.querySelector('span');
      if (!span) return;
      const raw = span.dataset.rawAcousticLabel
        || span.textContent.trim().replace(/^Zone acoustique\s+(?:\d+|[A-Z])(?:\s*·\s*.*)?$/i, '')
        || span.textContent.trim();
      span.dataset.rawAcousticLabel = raw;
      const name = zoneName(index);
      button.dataset.acousticZone = name;
      setText(span, `Zone acoustique ${name}`);
    });
  }

  async function refresh() {
    if (running || !NS.memory?.getTracks || !NS.styleFamilies?.analyze) return;
    running = true;
    try {
      const tracks = await NS.memory.getTracks();
      const result = NS.styleFamilies.analyze(tracks);
      NS.styleFamilies.current = result;
      renderStats(result);
      renderPanel(result, tracks);
      relabelLegend();
      document.documentElement.dataset.sonictraceStyleFamilies = String(result.count);
    } catch (error) {
      console.error('[SonicTrace Build 04/05] durable style-family render failed:', error);
    } finally {
      running = false;
    }
  }

  function schedule(delay = 0) {
    window.clearTimeout(timer);
    timer = window.setTimeout(refresh, delay);
  }

  function installObserver() {
    if (observer || !document.documentElement) return;
    observer = new MutationObserver(records => {
      const relevant = records.some(record => {
        const target = record.target instanceof Element ? record.target : record.target?.parentElement;
        if (target?.id === 'st-catalog-stats' || target?.id === 'st-cluster-legend') return true;
        return [...record.addedNodes].some(node => node instanceof Element && (
          node.id === 'sonictrace-catalog-view'
          || node.id === 'st-catalog-stats'
          || node.id === 'st-cluster-legend'
          || node.querySelector?.('#st-catalog-stats,#st-cluster-legend')
        ));
      });
      if (relevant) schedule(0);
    });
    observer.observe(document.documentElement, { childList:true, subtree:true });
  }

  ['sonictrace:catalog-track-saved','sonictrace:catalog-track-deleted','sonictrace:catalog-cleared','sonictrace:catalog-imported']
    .forEach(name => document.addEventListener(name, () => schedule(10)));
  document.addEventListener('click', event => {
    if (event.target.closest?.('[data-st-view="catalog"]')) schedule(40);
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { installObserver(); schedule(120); }, { once:true });
  } else {
    installObserver();
    schedule(120);
  }
})();
