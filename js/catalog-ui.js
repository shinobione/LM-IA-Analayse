(() => {
  'use strict';

  const NS = window.SonicTraceCatalog = window.SonicTraceCatalog || {};
  let tracks = [];
  let analysis = null;
  let selectedTrackId = null;
  let projectSelection = new Set();
  let projectResult = null;
  let booted = false;
  let renderScheduled = false;

  async function boot() {
    if (booted) return;
    if (!NS.memory || !NS.similarity) { window.setTimeout(boot, 80); return; }
    const main = document.querySelector('.dashboard-grid');
    const header = document.querySelector('.top-header');
    if (!main || !header) { window.setTimeout(boot, 80); return; }
    booted = true;
    ensureNavigation(header); ensureCatalogView(main); bindGlobalEvents();
    await refreshCatalog(); renderCurrentSaveState();
  }

  function ensureNavigation(header) {
    if (document.getElementById('sonictrace-mode-nav')) return;
    const nav = document.createElement('nav');
    nav.id = 'sonictrace-mode-nav'; nav.className = 'st-mode-nav'; nav.setAttribute('aria-label', 'Navigation SonicTrace');
    nav.innerHTML = `
      <button type="button" class="st-mode-btn active" data-st-view="analysis"><i data-lucide="audio-waveform"></i><span>Analyse</span></button>
      <button type="button" class="st-mode-btn" data-st-view="catalog"><i data-lucide="library-big"></i><span>Catalogue</span><b id="st-catalog-count">0</b></button>`;
    header.insertAdjacentElement('afterend', nav);
    nav.querySelectorAll('[data-st-view]').forEach(button => button.addEventListener('click', () => setView(button.dataset.stView)));
    window.lucide?.createIcons?.();
  }

  function setView(view) {
    const catalog = view === 'catalog';
    document.body.classList.toggle('st-catalog-mode', catalog);
    document.querySelectorAll('#sonictrace-mode-nav [data-st-view]').forEach(button => button.classList.toggle('active', button.dataset.stView === (catalog ? 'catalog' : 'analysis')));
    if (catalog) { refreshCatalog(); document.getElementById('sonictrace-catalog-view')?.scrollIntoView({ behavior:'smooth', block:'start' }); }
  }

  function ensureCatalogView(main) {
    if (document.getElementById('sonictrace-catalog-view')) return;
    const section = document.createElement('section');
    section.id = 'sonictrace-catalog-view'; section.className = 'st-catalog-view glass-card';
    section.innerHTML = `
      <div class="st-catalog-head">
        <div><span class="st-kicker">V2-E · CATALOG INTELLIGENCE</span><h2>Catalogue — <b id="st-catalog-title-count">0</b> titres</h2><p>Une mémoire locale de ton univers sonore. Les fichiers audio ne sont jamais conservés.</p></div>
        <div class="st-catalog-head-actions"><button id="st-export-catalog" type="button" class="secondary-btn"><i data-lucide="download"></i> Exporter</button><button id="st-import-catalog-btn" type="button" class="secondary-btn"><i data-lucide="upload"></i> Importer</button><input id="st-import-catalog" class="st-hidden-input" type="file" accept="application/json,.json" /></div>
      </div>
      <div id="st-catalog-stats" class="st-catalog-stats"></div>
      <div class="st-catalog-layout">
        <article class="st-map-panel"><div class="st-panel-head"><div><strong>Carte sonore</strong><span>projection 2D des embeddings CLAP</span></div><small>Clique un titre pour révéler ses voisins</small></div><div id="st-catalog-map" class="st-catalog-map"></div><div id="st-cluster-legend" class="st-cluster-legend"></div></article>
        <aside class="st-track-panel"><div class="st-panel-head"><div><strong>Morceaux</strong><span>sélection Album / EP possible</span></div><button id="st-clear-selection" type="button" class="st-text-btn">vider</button></div><div id="st-track-list" class="st-track-list"></div></aside>
      </div>
      <div class="st-catalog-lower"><article id="st-neighbor-panel" class="st-intelligence-panel"></article><article id="st-insights-panel" class="st-intelligence-panel"></article></div>
      <article class="st-project-panel"><div class="st-panel-head"><div><strong>Intelligence Album / EP</strong><span id="st-project-selection-label">Sélectionne au moins 2 morceaux</span></div><button id="st-analyze-project" type="button" class="primary-btn" disabled><i data-lucide="list-music"></i> Analyser la sélection</button></div><div id="st-project-result" class="st-project-result"></div></article>
      <div id="st-catalog-toast" class="st-catalog-toast" role="status" aria-live="polite"></div>`;
    main.appendChild(section);
    section.querySelector('#st-export-catalog')?.addEventListener('click', exportCatalogFile);
    section.querySelector('#st-import-catalog-btn')?.addEventListener('click', () => section.querySelector('#st-import-catalog')?.click());
    section.querySelector('#st-import-catalog')?.addEventListener('change', importCatalogFile);
    section.querySelector('#st-clear-selection')?.addEventListener('click', () => { projectSelection.clear(); projectResult = null; renderCatalog(); });
    section.querySelector('#st-analyze-project')?.addEventListener('click', analyzeProjectSelection);
    window.lucide?.createIcons?.();
  }

  function bindGlobalEvents() {
    document.addEventListener('sonictrace:full-analysis-ready', event => renderCurrentSaveState(Boolean(event.detail?.ready)));
    document.addEventListener('sonictrace:catalog-capture-reset', () => document.getElementById('st-save-to-catalog')?.remove());
    ['sonictrace:catalog-track-saved','sonictrace:catalog-track-deleted','sonictrace:catalog-cleared','sonictrace:catalog-imported'].forEach(name => document.addEventListener(name, () => refreshCatalog()));
    document.addEventListener('sonictrace:catalog-track-saved', event => { selectedTrackId = event.detail?.track?.id || selectedTrackId; toast(event.detail?.updated ? 'Morceau mis à jour dans le catalogue.' : 'Morceau ajouté au catalogue.'); });
  }

  async function renderCurrentSaveState(explicitReady) {
    const capture = NS.capture || {};
    const ready = explicitReady ?? Boolean(capture.analyze?.neural?.embedding?.vector?.length && capture.fusion?.fusion?.sections?.length);
    if (!ready) return;
    const anchor = document.getElementById('v2-semantic-results') || document.getElementById('v2-fusion-results');
    if (!anchor || anchor.classList.contains('hidden')) return;
    let card = document.getElementById('st-save-to-catalog');
    if (!card) { card = document.createElement('section'); card.id = 'st-save-to-catalog'; card.className = 'st-save-card glass-card'; anchor.insertAdjacentElement('afterend', card); }
    let snapshot = null; try { snapshot = await NS.memory.buildCurrentSnapshot(); } catch (_) {}
    const title = snapshot?.title || capture.selectedFile?.name?.replace(/\.[^.]+$/, '') || 'Ce morceau';
    const dimension = snapshot?.neural?.embedding?.dimension || capture.analyze?.neural?.embedding?.dimension || 0;
    const concordance = snapshot?.concordance?.percent;
    const existing = snapshot?.id ? tracks.find(track => track.id === snapshot.id) : null;
    card.innerHTML = `
      <div class="st-save-copy"><span class="st-kicker">V2-E · MÉMOIRE DU CATALOGUE</span><h3>${esc(title)} peut maintenant rejoindre ton catalogue.</h3><p>DSP, mastering, Neural, structure, résumé sémantique, TXT et embedding ${dimension || '—'}D seront conservés localement. <b>Pas le WAV/MP3.</b></p><div class="st-save-meta"><span><i data-lucide="brain-circuit"></i> embedding ${dimension || '—'}D</span>${Number.isFinite(concordance) ? `<span><i data-lucide="scan-search"></i> concordance artistique ${concordance}%</span>` : ''}<span><i data-lucide="hard-drive"></i> IndexedDB locale</span></div></div>
      <button id="st-save-current-track" type="button" class="primary-btn"><i data-lucide="library-big"></i> ${existing ? 'Mettre à jour dans le catalogue' : 'Ajouter ce morceau au catalogue'}</button>`;
    card.querySelector('#st-save-current-track')?.addEventListener('click', saveCurrentTrack); window.lucide?.createIcons?.();
  }

  async function saveCurrentTrack() {
    const button = document.getElementById('st-save-current-track'); if (!button) return;
    const old = button.innerHTML; button.disabled = true; button.innerHTML = '<i data-lucide="loader-circle"></i> Enregistrement…'; window.lucide?.createIcons?.();
    try { const result = await NS.memory.saveCurrentTrack(); selectedTrackId = result.track?.id || selectedTrackId; await refreshCatalog(); await renderCurrentSaveState(true); }
    catch (error) { toast(error.message || 'Impossible d’ajouter ce morceau.', true); button.disabled = false; button.innerHTML = old; window.lucide?.createIcons?.(); }
  }

  async function refreshCatalog() {
    if (!NS.memory || !NS.similarity) return;
    try {
      tracks = await NS.memory.getTracks(); analysis = NS.similarity.analyzeCatalog(tracks);
      if (selectedTrackId && !tracks.some(track => track.id === selectedTrackId)) selectedTrackId = null;
      if (!selectedTrackId && tracks[0]) selectedTrackId = tracks[0].id;
      projectSelection = new Set([...projectSelection].filter(id => tracks.some(track => track.id === id))); projectResult = null;
      scheduleRender(); const count = tracks.length;
      const navCount = document.getElementById('st-catalog-count'), titleCount = document.getElementById('st-catalog-title-count');
      if (navCount) navCount.textContent = count; if (titleCount) titleCount.textContent = count;
    } catch (error) { console.error('[SonicTrace Catalog] refresh failed:', error); }
  }

  function scheduleRender() { if (renderScheduled) return; renderScheduled = true; requestAnimationFrame(() => { renderScheduled = false; renderCatalog(); }); }
  function renderCatalog() { if (!document.getElementById('sonictrace-catalog-view')) return; renderStats(); renderMap(); renderTrackList(); renderNeighbors(); renderInsights(); renderProjectControls(); window.lucide?.createIcons?.(); }

  function renderStats() {
    const root = document.getElementById('st-catalog-stats'); if (!root) return;
    const values = tracks.map(track => Number(track?.concordance?.percent)).filter(Number.isFinite); const mean = values.length ? Math.round(values.reduce((a,b)=>a+b,0)/values.length) : null;
    root.innerHTML = [stat('Titres mémorisés',tracks.length,'analyses structurées'),stat('Familles sonores',analysis?.clusters?.count||0,tracks.length>=3?'clusters naturels':'à partir de quelques titres'),stat('Doublons potentiels',analysis?.insights?.redundantPairs?.length||0,'similarité ≥ 92%'),stat('Outliers',analysis?.insights?.outliers?.length||0,'hors familles principales'),stat('Concordance moyenne',mean==null?'—':`${mean}%`,'déclaré vs entendu')].join('');
  }

  function renderMap() {
    const root=document.getElementById('st-catalog-map'),legend=document.getElementById('st-cluster-legend'); if(!root||!legend)return;
    if(!tracks.length){root.innerHTML=emptyState('La carte se construira à mesure que tu ajoutes des morceaux analysés.','map');legend.innerHTML='';return;}
    const points=analysis?.projection||[], selected=tracks.find(track=>track.id===selectedTrackId), neighbors=selected?NS.similarity.nearest(selected,tracks,8):[], neighborIds=new Map(neighbors.map(item=>[item.track.id,item.percent]));
    const width=1000,height=570,pad=58,toX=v=>pad+((v+1)/2)*(width-pad*2),toY=v=>pad+((1-(v+1)/2))*(height-pad*2);
    const lines=selected?neighbors.slice(0,5).map(item=>{const a=points.find(p=>p.id===selected.id),b=points.find(p=>p.id===item.track.id);return(!a||!b)?'':`<line x1="${toX(a.x)}" y1="${toY(a.y)}" x2="${toX(b.x)}" y2="${toY(b.y)}" class="st-map-link" style="--link-strength:${(item.percent/100).toFixed(2)}" />`;}).join(''):'';
    root.innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Carte 2D du catalogue sonore"><defs><filter id="stMapGlow"><feGaussianBlur stdDeviation="5" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><g class="st-map-grid">${[1,2,3,4].map(i=>`<line x1="${i*width/5}" y1="30" x2="${i*width/5}" y2="${height-30}"/><line x1="30" y1="${i*height/5}" x2="${width-30}" y2="${i*height/5}"/>`).join('')}</g><g class="st-map-links">${lines}</g>${points.map(point=>{const track=tracks.find(item=>item.id===point.id),cluster=analysis?.clusters?.assignments?.[point.id]??0,isSelected=point.id===selectedTrackId,neighbor=neighborIds.get(point.id);return`<g class="st-map-point ${isSelected?'selected':''} ${neighbor?'neighbor':''}" data-track-id="${attr(point.id)}" transform="translate(${toX(point.x)} ${toY(point.y)})" style="--cluster:${cluster}"><circle r="${isSelected?15:neighbor?11:8}"/><text x="${isSelected?20:14}" y="4">${esc(shortTitle(track?.title||'Track',24))}${neighbor?` · ${neighbor}%`:''}</text></g>`;}).join('')}</svg>`;
    root.querySelectorAll('[data-track-id]').forEach(point=>point.addEventListener('click',()=>{selectedTrackId=point.dataset.trackId;renderCatalog();}));
    legend.innerHTML=(analysis?.clusters?.groups||[]).map(group=>`<button type="button" data-cluster-id="${group.id}"><i style="--cluster:${group.id}"></i><span>${esc(group.label)}</span><b>${group.trackIds.length}</b></button>`).join('');
    legend.querySelectorAll('[data-cluster-id]').forEach(button=>button.addEventListener('click',()=>{const group=analysis.clusters.groups.find(item=>String(item.id)===button.dataset.clusterId);if(group?.trackIds?.[0])selectedTrackId=group.trackIds[0];renderCatalog();}));
  }

  function renderTrackList() {
    const root=document.getElementById('st-track-list'); if(!root)return;
    if(!tracks.length){root.innerHTML=emptyState('Aucun titre pour l’instant. Termine une Analyse complète puis ajoute le morceau.','library');return;}
    root.innerHTML=tracks.map(track=>{const clusterId=analysis?.clusters?.assignments?.[track.id]??0,genre=track?.neural?.genres?.[0]?.label||track?.declared?.GENRE||'—',mood=track?.neural?.moods?.[0]?.label||track?.declared?.MOOD||'—',bpm=track?.dsp?.bpm,selected=selectedTrackId===track.id,checked=projectSelection.has(track.id);return`<div class="st-track-row ${selected?'active':''}" data-track-row="${attr(track.id)}"><button type="button" class="st-track-main" data-select-track="${attr(track.id)}"><i class="st-cluster-dot" style="--cluster:${clusterId}"></i><span><strong>${esc(track.title||'Untitled')}</strong><small>${esc(genre)} • ${esc(mood)}${Number.isFinite(Number(bpm))?` • ${Number(bpm).toFixed(0)} BPM`:''}</small></span>${Number.isFinite(Number(track?.concordance?.percent))?`<em>${Math.round(track.concordance.percent)}%</em>`:''}</button><label class="st-project-check" title="Inclure dans le projet Album / EP"><input type="checkbox" data-project-track="${attr(track.id)}" ${checked?'checked':''}/><span></span></label></div>`;}).join('');
    root.querySelectorAll('[data-select-track]').forEach(button=>button.addEventListener('click',()=>{selectedTrackId=button.dataset.selectTrack;renderCatalog();}));
    root.querySelectorAll('[data-project-track]').forEach(input=>input.addEventListener('change',()=>{if(input.checked)projectSelection.add(input.dataset.projectTrack);else projectSelection.delete(input.dataset.projectTrack);projectResult=null;renderProjectControls();renderTrackList();}));
  }

  function renderNeighbors() {
    const root=document.getElementById('st-neighbor-panel');if(!root)return;const selected=tracks.find(track=>track.id===selectedTrackId);
    if(!selected){root.innerHTML=panelEmpty('Similarité musicale','Ajoute plusieurs titres pour voir leurs voisins expliqués.');return;}
    const neighbors=NS.similarity.nearest(selected,tracks,5);
    root.innerHTML=`<div class="st-panel-head"><div><strong>Voisins de ${esc(selected.title)}</strong><span>score hybride embedding + audio + structure</span></div></div><div class="st-neighbor-list">${neighbors.length?neighbors.map((item,index)=>`<button type="button" class="st-neighbor-row" data-neighbor-id="${attr(item.track.id)}"><b>${index+1}</b><span><strong>${esc(item.track.title)}</strong><small>${item.reasons.map(esc).join(' • ')}</small></span><em>${item.percent}%</em></button>`).join(''):'<p class="st-empty-copy">Il faut au moins deux morceaux dans le catalogue.</p>'}</div>`;
    root.querySelectorAll('[data-neighbor-id]').forEach(button=>button.addEventListener('click',()=>{selectedTrackId=button.dataset.neighborId;renderCatalog();}));
  }

  function renderInsights() {
    const root=document.getElementById('st-insights-panel');if(!root)return;const insights=analysis?.insights||{};
    if(tracks.length<3){root.innerHTML=panelEmpty('Lecture du catalogue','Les familles, outliers et morceaux-ponts deviennent pertinents dès que le catalogue grandit.');return;}
    const title=id=>tracks.find(track=>track.id===id)?.title||'Track', redundancies=(insights.redundantPairs||[]).slice(0,3),outliers=(insights.outliers||[]).slice(0,3),bridges=(insights.bridges||[]).slice(0,3);
    root.innerHTML=`<div class="st-panel-head"><div><strong>Lecture du catalogue</strong><span>familles • redondances • outliers • ponts</span></div></div><div class="st-insight-groups"><section><h4>Familles sonores</h4>${(analysis?.clusters?.groups||[]).map(group=>`<p><i style="--cluster:${group.id}"></i><b>${esc(group.label)}</b><span>${group.trackIds.length} titre${group.trackIds.length>1?'s':''}</span></p>`).join('')||'<small>—</small>'}</section><section><h4>Très proches</h4>${redundancies.length?redundancies.map(pair=>`<p><b>${esc(title(pair.a))} ↔ ${esc(title(pair.b))}</b><span>${pair.percent}% • potentiellement redondants</span></p>`).join(''):'<small>Aucune paire ≥ 92%.</small>'}</section><section><h4>Outliers</h4>${outliers.length?outliers.map(item=>`<p><b>${esc(title(item.id))}</b><span>voisinage ${item.neighborhoodPercent}% • identité à part</span></p>`).join(''):'<small>Aucun outlier net.</small>'}</section><section><h4>Morceaux-ponts</h4>${bridges.length?bridges.map(item=>`<p><b>${esc(title(item.id))}</b><span>relie ${item.clusterCount} familles • ${item.bridgePercent}%</span></p>`).join(''):'<small>Aucun pont net pour l’instant.</small>'}</section></div>`;
  }

  function renderProjectControls() {
    const label=document.getElementById('st-project-selection-label'),button=document.getElementById('st-analyze-project'),root=document.getElementById('st-project-result'),count=projectSelection.size;
    if(label)label.textContent=count?`${count} morceau${count>1?'x':''} sélectionné${count>1?'s':''}`:'Sélectionne au moins 2 morceaux';if(button)button.disabled=count<2;if(!root)return;
    if(projectResult)renderProjectResult(root,projectResult);else root.innerHTML=count>=2?'<p class="st-project-placeholder">La sélection est prête : lance l’analyse pour mesurer sa cohérence et proposer un ordre.</p>':'<p class="st-project-placeholder">Coche les morceaux à comparer dans la liste ou sur ton projet.</p>';
  }

  async function analyzeProjectSelection(){const selected=[...projectSelection].map(id=>tracks.find(track=>track.id===id)).filter(Boolean);projectResult=NS.similarity.analyzeProject(selected);renderProjectControls();}
  function renderProjectResult(root,result){const outlierNames=result.outliers.map(item=>tracks.find(track=>track.id===item.id)?.title).filter(Boolean);root.innerHTML=`<div class="st-project-score"><span>Cohérence sonore</span><strong>${result.coherencePercent}%</strong><i><b style="width:${result.coherencePercent}%"></b></i></div><div class="st-project-copy">${result.summary.map(text=>`<p>${esc(text)}</p>`).join('')}</div>${outlierNames.length?`<div class="st-project-warning"><i data-lucide="orbit"></i><span><strong>À vérifier</strong>${esc(outlierNames.join(', '))} s’éloigne${outlierNames.length>1?'nt':''} de l’identité générale.</span></div>`:''}<div class="st-sequence-list"><div class="st-sequence-head"><strong>Proposition d’ordre</strong><span>énergie • similarité • BPM • tonalité • structure</span></div>${result.ordered.map((item,index)=>`<div class="st-sequence-row"><b>${index+1}</b><span><strong>${esc(item.track.title)}</strong><small>${esc(item.role)} • ${item.transition.map(esc).join(' • ')}</small></span><em>${Math.round(NS.similarity.trackEnergy(item.track)*100)}% E</em></div>`).join('')}</div><div class="st-project-save-row"><input id="st-project-name" type="text" maxlength="80" placeholder="Nom du projet / album"/><button id="st-save-project" type="button" class="secondary-btn"><i data-lucide="save"></i> Sauvegarder le projet</button></div>`;root.querySelector('#st-save-project')?.addEventListener('click',saveProject);window.lucide?.createIcons?.();}
  async function saveProject(){if(!projectResult)return;const input=document.getElementById('st-project-name'),name=input?.value?.trim()||`Projet ${new Date().toLocaleDateString('fr-FR')}`;try{await NS.memory.saveProject({name,trackIds:projectResult.ordered.map(item=>item.track.id),coherencePercent:projectResult.coherencePercent,outlierIds:projectResult.outliers.map(item=>item.id),bridge:projectResult.bridge,sequencing:projectResult.ordered.map((item,index)=>({position:index+1,trackId:item.track.id,role:item.role,transition:item.transition}))});toast(`Projet « ${name} » sauvegardé localement.`);}catch(error){toast(error.message||'Impossible de sauvegarder le projet.',true);}}

  async function exportCatalogFile(){try{const payload=await NS.memory.exportCatalog(),blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`sonictrace-catalog-${new Date().toISOString().slice(0,10)}.json`;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Catalogue exporté en JSON.');}catch(error){toast(error.message||'Export impossible.',true);}}
  async function importCatalogFile(event){const file=event.target.files?.[0];if(!file)return;try{const payload=JSON.parse(await file.text());await NS.memory.importCatalog(payload);await refreshCatalog();toast(`${payload.tracks?.length||0} titres importés / mis à jour.`);}catch(error){toast(error.message||'Import impossible.',true);}finally{event.target.value='';}}
  function toast(message,error=false){const root=document.getElementById('st-catalog-toast');if(!root)return;root.textContent=message;root.classList.toggle('error',error);root.classList.add('show');clearTimeout(toast._timer);toast._timer=setTimeout(()=>root.classList.remove('show'),3200);}
  function stat(label,value,sub){return`<div><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(sub)}</small></div>`;}
  function emptyState(text,icon){return`<div class="st-empty-state"><i data-lucide="${icon}"></i><p>${esc(text)}</p></div>`;}
  function panelEmpty(title,text){return`<div class="st-panel-head"><div><strong>${esc(title)}</strong></div></div><p class="st-empty-copy">${esc(text)}</p>`;}
  function shortTitle(value,max){const text=String(value||'');return text.length>max?`${text.slice(0,max-1)}…`:text;}
  function attr(value){return esc(value).replace(/`/g,'&#96;');}
  function esc(value){return String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));}

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
