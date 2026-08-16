(() => {
  'use strict';

  const NS = window.SonicTraceCatalog = window.SonicTraceCatalog || {};
  let observer = null;
  let scheduled = false;

  function installStyle() {
    if (document.getElementById('st-catalog-maintenance-style')) return;
    const style = document.createElement('style');
    style.id = 'st-catalog-maintenance-style';
    style.textContent = `
      .st-track-row{grid-template-columns:1fr 38px 34px!important}
      .st-track-delete{position:relative;z-index:8;align-self:center;justify-self:center;width:30px;height:30px;border:1px solid rgba(255,105,120,.22);border-radius:9px;background:rgba(255,80,100,.06);color:#9aa8ad;display:grid;place-items:center;cursor:pointer;opacity:.48;transition:.16s ease;pointer-events:auto!important}
      .st-track-row:hover .st-track-delete,.st-track-delete:focus-visible{opacity:1;color:#ff7180;border-color:rgba(255,113,128,.52);background:rgba(255,80,100,.12);outline:none}
      .st-track-delete:hover{transform:scale(1.05)}
      .st-track-delete svg{width:15px;height:15px;pointer-events:none}
      .st-track-delete.is-busy{pointer-events:none!important;opacity:.35}
    `;
    document.head.appendChild(style);
  }

  function trackTitle(row) {
    return row?.querySelector('.st-track-main strong')?.textContent?.trim() || 'ce morceau';
  }

  function onDeleteClick(event) {
    const button = event.currentTarget;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation?.();
    deleteTrack(button);
  }

  function addDeleteButtons() {
    installStyle();
    document.querySelectorAll('#st-track-list [data-track-row]').forEach(row => {
      if (row.querySelector('[data-delete-catalog-track]')) return;
      const id = row.dataset.trackRow;
      if (!id) return;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'st-track-delete';
      button.dataset.deleteCatalogTrack = id;
      button.dataset.directDeleteHandler = '1';
      button.title = `Supprimer ${trackTitle(row)} du catalogue local`;
      button.setAttribute('aria-label', button.title);
      button.innerHTML = '<i data-lucide="trash-2"></i>';
      button.addEventListener('click', onDeleteClick);
      row.appendChild(button);
    });
    window.lucide?.createIcons?.();
  }

  function toast(text, error = false) {
    const root = document.getElementById('st-catalog-toast');
    if (!root) return;
    root.textContent = text;
    root.classList.toggle('error', error);
    root.classList.add('show');
    window.setTimeout(() => root.classList.remove('show'), 2600);
  }

  async function deleteTrack(button) {
    const id = button?.dataset?.deleteCatalogTrack;
    if (!id) {
      toast('Identifiant catalogue introuvable.', true);
      return;
    }
    if (!NS.memory?.deleteTrack) {
      console.error('[SonicTrace Catalog] deleteTrack API unavailable');
      toast('La mémoire du catalogue n’est pas prête. Relance SonicTrace.', true);
      return;
    }
    if (button.dataset.deleteBusy === '1') return;

    const row = button.closest('[data-track-row]');
    const title = trackTitle(row);
    const accepted = window.confirm(
      `Supprimer « ${title} » du catalogue SonicTrace ?\n\n` +
      'Seule l’entrée locale IndexedDB sera supprimée. Aucun fichier audio n’est stocké ni supprimé.'
    );
    if (!accepted) return;

    button.dataset.deleteBusy = '1';
    button.classList.add('is-busy');
    button.disabled = true;
    try {
      await NS.memory.deleteTrack(id);
      toast(`« ${title} » supprimé du catalogue.`);
    } catch (error) {
      console.error('[SonicTrace Catalog] delete failed:', error);
      button.disabled = false;
      button.dataset.deleteBusy = '0';
      button.classList.remove('is-busy');
      toast('Impossible de supprimer cette entrée du catalogue.', true);
    }
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      addDeleteButtons();
    });
  }

  function installObserver() {
    if (observer || !document.documentElement) return;
    observer = new MutationObserver(records => {
      if (records.some(record => {
        const target = record.target instanceof Element ? record.target : record.target?.parentElement;
        return target?.closest?.('#st-track-list') || [...record.addedNodes].some(node => node instanceof Element && (node.id === 'st-track-list' || node.querySelector?.('#st-track-list')));
      })) schedule();
    });
    observer.observe(document.documentElement, { childList:true, subtree:true });
  }

  // Fallback delegation for externally injected rows. Native maintenance buttons
  // own a direct handler so parent propagation rules cannot swallow the action.
  document.addEventListener('click', event => {
    const button = event.target.closest?.('[data-delete-catalog-track]');
    if (!button || button.dataset.directDeleteHandler === '1') return;
    event.preventDefault();
    event.stopPropagation();
    deleteTrack(button);
  });

  ['sonictrace:catalog-track-saved','sonictrace:catalog-track-deleted','sonictrace:catalog-imported','sonictrace:catalog-cleared']
    .forEach(name => document.addEventListener(name, schedule));
  document.addEventListener('click', event => {
    if (event.target.closest?.('[data-st-view="catalog"]')) window.setTimeout(schedule, 30);
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { installObserver(); schedule(); }, { once:true });
  } else {
    installObserver();
    schedule();
  }

  NS.catalogMaintenance = { version:'1.1', refresh: schedule };
})();