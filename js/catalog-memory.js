(() => {
  'use strict';
  const NS = window.SonicTraceCatalog = window.SonicTraceCatalog || {};
  const DB = 'sonictrace-catalog', VERSION = 1, TRACKS = 'tracks', PROJECTS = 'projects';
  const capture = NS.capture = NS.capture || { selectedFile:null, dsp:null, analyze:null, fusion:null, completedAt:null };
  let dbPromise, fetchWrapped = false, analyzerWrapped = false;

  function boot() {
    openDb().catch(error => console.error('[SonicTrace Catalog] IndexedDB:', error));
    wrapFetch(); trackFile(); wrapAnalyzer(); observeFullAnalysis();
  }

  function trackFile() {
    const attach = () => {
      const input = document.getElementById('audio-file-input');
      if (!input || input.dataset.stCatalogTracked) return false;
      input.dataset.stCatalogTracked = '1';
      input.addEventListener('change', () => reset(input.files?.[0] || null));
      document.getElementById('drop-zone')?.addEventListener('drop', event => {
        const file = event.dataTransfer?.files?.[0]; if (file) reset(file);
      });
      capture.selectedFile = input.files?.[0] || null;
      return true;
    };
    if (attach()) return;
    const observer = new MutationObserver(() => { if (attach()) observer.disconnect(); });
    observer.observe(document.documentElement, { childList:true, subtree:true });
  }

  function reset(file) {
    capture.selectedFile = file; capture.dsp = capture.analyze = capture.fusion = capture.completedAt = null;
    NS.currentSnapshot = null;
    document.dispatchEvent(new CustomEvent('sonictrace:catalog-capture-reset'));
  }

  function wrapFetch() {
    if (fetchWrapped || window.fetch?.__stCatalog) return;
    const nativeFetch = window.fetch.bind(window);
    const wrapped = async (...args) => {
      const response = await nativeFetch(...args);
      try {
        const request = args[0], url = typeof request === 'string' ? request : request?.url || '';
        const method = String(args[1]?.method || request?.method || 'GET').toUpperCase();
        if (response.ok && method === 'POST' && /\/api\/(analyze|fusion)(?:\?|$)/.test(url)) {
          const payload = await response.clone().json();
          if (/\/api\/analyze(?:\?|$)/.test(url)) capture.analyze = payload;
          if (/\/api\/fusion(?:\?|$)/.test(url)) capture.fusion = payload;
        }
      } catch (error) { console.warn('[SonicTrace Catalog] API capture:', error); }
      return response;
    };
    wrapped.__stCatalog = true; window.fetch = wrapped; fetchWrapped = true;
  }

  function wrapAnalyzer() {
    const attempt = () => {
      if (analyzerWrapped) return true;
      try {
        if (typeof LMNAudioAnalyzer === 'undefined' || !LMNAudioAnalyzer.prototype?.analyze) return false;
        const original = LMNAudioAnalyzer.prototype.analyze;
        if (original.__stCatalog) { analyzerWrapped = true; return true; }
        const wrapped = async function(file, onProgress) {
          const result = await original.call(this, file, onProgress);
          capture.selectedFile = file || capture.selectedFile; capture.dsp = clone(result);
          document.dispatchEvent(new CustomEvent('sonictrace:dsp-captured', { detail:{ result:capture.dsp } }));
          return result;
        };
        wrapped.__stCatalog = true; LMNAudioAnalyzer.prototype.analyze = wrapped; analyzerWrapped = true; return true;
      } catch (_) { return false; }
    };
    if (attempt()) return;
    const timer = setInterval(() => { if (attempt()) clearInterval(timer); }, 80);
    setTimeout(() => clearInterval(timer), 12000);
  }

  function observeFullAnalysis() {
    let signature = '';
    const inspect = () => {
      const root = document.getElementById('v2-semantic-results');
      if (!root || root.classList.contains('hidden') || !root.textContent.trim()) return;
      const file = currentFile();
      const next = `${file?.name || ''}|${capture.analyze?.neural?.embedding?.vector?.length || 0}|${capture.fusion?.fusion?.sections?.length || 0}`;
      if (!next || next === signature) return;
      signature = next; capture.completedAt = new Date().toISOString();
      const ready = Boolean(capture.analyze?.neural?.embedding?.vector?.length && capture.fusion?.fusion?.sections?.length);
      document.dispatchEvent(new CustomEvent('sonictrace:full-analysis-ready', { detail:{ ready, fileName:file?.name || 'morceau' } }));
    };
    new MutationObserver(inspect).observe(document.documentElement, { childList:true, subtree:true, attributes:true, attributeFilter:['class'] });
  }

  function currentFile() { return capture.selectedFile || document.getElementById('audio-file-input')?.files?.[0] || null; }

  async function buildCurrentSnapshot() {
    const analyze = capture.analyze || {}, fusionPayload = capture.fusion || {}, neural = analyze.neural || {}, fusion = fusionPayload.fusion || {};
    const embedding = neural.embedding || {}, vector = Array.isArray(embedding.vector) ? embedding.vector.map(Number).filter(Number.isFinite) : [];
    const declared = clone(window.LMNSemanticDeclaredMetadata || {}), dsp = capture.dsp || domDsp(), file = currentFile();
    const filename = file?.name || analyze.file?.name || fusionPayload.file?.name || dsp?.file?.name || 'Untitled';
    const track = {
      schema:'sonictrace.catalog.track.v1', id:'', trackId:null, localOnly:true, fingerprint:'', createdAt:new Date().toISOString(), updatedAt:new Date().toISOString(),
      title:cleanTitle(declared.TITLE || filename.replace(/\.[^.]+$/, '')), filename, year:declared.YEAR || '', declared,
      file:compactFile(file, analyze.file, dsp?.file), dsp:compactDsp(dsp), mastering:clone(analyze.mastering || {}),
      neural:{ model:neural.engine?.model || embedding.model || '', genres:rank(neural.genres,8), moods:rank(neural.moods,8), instruments:rank(neural.instruments,10), traits:traits(neural.traits), embedding:{ model:embedding.model || neural.engine?.model || '', dimension:Number(embedding.dimension || vector.length || 0), vector } },
      structure:structure(fusion), semantic:semantic(fusion, neural, declared), concordance:concordance(declared, neural, dsp),
      compute:{ neural:clone(neural.engine || {}), fusion:clone(fusionPayload.compute || {}) },
      privacy:{ audioStored:false, note:'No WAV/MP3 bytes are persisted in the SonicTrace catalog.' },
    };
    track.fingerprint = fingerprint(track);
    track.trackId = studioTrackId();
    track.localOnly = !track.trackId;
    track.id = track.trackId || `local-${track.fingerprint}`;
    NS.currentSnapshot = track; return track;
  }

  function compactFile(file={}, backend={}, dsp={}) { return { name:file?.name || backend?.name || dsp?.name || '', sizeBytes:num(file?.size ?? dsp?.sizeBytes), type:file?.type || dsp?.type || '', durationSeconds:num(backend?.duration_seconds ?? dsp?.durationSeconds), sampleRateHz:num(backend?.sample_rate_hz ?? dsp?.sampleRate), channels:num(backend?.channels ?? dsp?.channels), codec:backend?.codec || dsp?.format || '', bitrateKbps:num(backend?.bit_rate_kbps), format:backend?.format || dsp?.format || '' }; }
  function compactDsp(dsp={}) { const raw=dsp.raw||{}, a=dsp.acoustics||{}; return { source:dsp.source || 'browser-dsp', confidence:num(dsp.system?.confidenceScore), bpm:num(raw.rhythm?.bpm ?? parse(a.tempo)), tempoConfidence:num(raw.rhythm?.confidence), key:raw.key ? { tonic:raw.key.tonic||'', mode:raw.key.mode||'', camelot:raw.key.camelot||a.camelot||'', confidence:num(raw.key.confidence), label:[raw.key.tonic,raw.key.mode].filter(Boolean).join(' ') || a.key || '' } : { label:a.key||'', camelot:a.camelot||'' }, rmsDbfs:num(raw.amplitude?.rmsDb ?? parse(a.rms)), peakDbfs:num(raw.amplitude?.peakDb ?? parse(a.peak)), crestDb:num(raw.amplitude?.crestDb ?? parse(a.crestFactor)), clippingPercent:num(raw.amplitude?.clippingPercent ?? parse(a.clipping)), stereoWidth:num(raw.stereo?.width), stereoCorrelation:num(raw.stereo?.correlation ?? parse(a.stereoCorrelation)), spectralCentroidHz:num(raw.spectral?.centroid ?? parse(a.spectralCentroid)), spectralRolloffHz:num(raw.spectral?.rolloff ?? parse(a.spectralRolloff)), spectralFlatness:num(raw.spectral?.flatness ?? parse(a.spectralFlatness)), spectralFlux:num(raw.spectral?.flux ?? parse(a.spectralFlux)), dna:clone(dsp.dna||{}), descriptors:(dsp.genres||[]).slice(0,8).map(x=>({name:x.name,weight:num(x.weight)})) }; }
  function domDsp() { const text=id=>document.getElementById(id)?.textContent?.trim()||''; return { source:'browser-dsp-dom-fallback', file:{name:currentFile()?.name||''}, acoustics:{tempo:text('metric-tempo'),key:text('metric-key'),rms:text('metric-rms'),peak:text('metric-peak'),crestFactor:text('metric-crest')} }; }
  function rank(items,n) { return (Array.isArray(items)?items:[]).slice(0,n).map(x=>({label:String(x?.label||x?.name||''),score:num(x?.score),percent:num(x?.percent)})).filter(x=>x.label); }
  function traits(value={}) { return Object.fromEntries(Object.entries(value||{}).map(([k,v])=>[k,{value:num(v?.value),percent:num(v?.percent),positive_label:v?.positive_label||'',negative_label:v?.negative_label||''}])); }
  function structure(f={}) { return { engine:clone(f.engine||{}), summary:clone(f.summary||{}), hooks:clone((f.hooks||[]).slice(0,6)), climax:clone(f.climax||{}), sections:(f.sections||[]).map(s=>({ start:num(s.start),end:num(s.end),duration:num(s.duration),type:s.fusion_type||s.type||'',label:s.fusion_label||s.label||'',confidence:num(s.fusion_confidence ?? s.label_confidence),energy:num(s.energy),rhythmic:num(s.rhythmic),brightness:num(s.brightness),repeatGroup:s.fusion_repeat_group||s.repeat_group||null,repeatCount:s.fusion_repeat_count||s.repeat_count||null,key:clone(s.key||{}),stemActivity:clone(s.stem_activity||{}) })) }; }
  function semantic(f,n,d) { return { genreFamily:inferFamily(n), topGenres:rank(n.genres,5), topMoods:rank(n.moods,5), topInstruments:rank(n.instruments,6), arrangementSummary:clone(f.summary?.labels || {}), declaredTitle:d.TITLE||'', themes:d.THEMES||'', language:d.LANGUAGE||'', era:d.ERA||'', stylePrompt:d.STYLE_PROMPT||'' }; }
  function inferFamily(n={}) { const t=(n.genres||[]).slice(0,5).map(x=>String(x.label||'').toLowerCase()).join(' '); if(/hip.?hop|rap|trap|drill/.test(t))return'hip-hop';if(/r&b|rnb|soul/.test(t))return'r&b';if(/house|techno|edm|electronic|dnb|dubstep/.test(t))return'electronic';if(/pop/.test(t))return'pop';if(/rock|metal|punk/.test(t))return'rock';if(/ambient|lo-fi/.test(t))return'ambient';return'general'; }

  function concordance(d={}, n={}, dsp={}) {
    const parts=[]; const add=(name,score,detail)=>{if(Number.isFinite(score))parts.push({name,score:clamp(score,0,1),detail});};
    if(d.GENRE) add('genre', tokenAgreement(d.GENRE,(n.genres||[]).map(x=>x.label).join(' ')), `${d.GENRE}`);
    if(d.MOOD) add('mood', tokenAgreement(d.MOOD,(n.moods||[]).map(x=>x.label).join(' ')), `${d.MOOD}`);
    const de=declaredEnergy(d.ENERGY), ne=traitValue(n.traits?.energy); if(de!=null && ne!=null)add('energy',1-Math.abs(de-ne),`déclaré ${Math.round(de*100)}% ↔ Neural ${Math.round(ne*100)}%`);
    const dbpm=parse(d.BPM), mbpm=num(dsp?.raw?.rhythm?.bpm ?? parse(dsp?.acoustics?.tempo)); if(dbpm!=null&&mbpm!=null)add('bpm',Math.max(0,1-effectiveBpmDelta(dbpm,mbpm)/24),`${dbpm} ↔ ${mbpm}`);
    if(d.STYLE_PROMPT) add('style', tokenAgreement(d.STYLE_PROMPT,[...(n.genres||[]),...(n.moods||[]),...(n.instruments||[])].map(x=>x.label).join(' ')), 'STYLE_PROMPT ↔ Neural');
    const weights={genre:.28,mood:.24,energy:.18,bpm:.12,style:.18}; let total=0,used=0; for(const p of parts){const w=weights[p.name]||1;total+=p.score*w;used+=w;}
    const score=used?total/used:null; return { score, percent:score==null?null:Math.round(score*100), components:parts };
  }
  function tokenAgreement(a,b) { const A=tokens(a),B=tokens(b); if(!A.size||!B.size)return 0; let hit=0; A.forEach(x=>{if(B.has(x))hit++;}); return hit/A.size; }
  function tokens(s) { const stop=new Set(['music','with','and','the','track','style','song']); return new Set(normalize(s).split(' ').filter(x=>x.length>=3&&!stop.has(x))); }
  function declaredEnergy(v) { if(v==null||v==='')return null; const n=parse(v); if(n!=null)return clamp(n>1?n/100:n,0,1); const r=normalize(v); if(/very high|extreme|maximum|intense/.test(r))return .9;if(/high|fort|eleve/.test(r))return .78;if(/medium|mid|moderate|moyen/.test(r))return .55;if(/low|soft|calm|faible/.test(r))return .28;return null; }
  function traitValue(v) { const n=num(v?.value ?? (v?.percent!=null?Number(v.percent)/100:null)); return n==null?null:clamp(n>1?n/100:n,0,1); }
  function effectiveBpmDelta(a,b) { return Math.min(Math.abs(a-b),Math.abs(a*2-b),Math.abs(a-b*2),Math.abs(a*.5-b),Math.abs(a-b*.5)); }

  function fingerprint(track) { const basis=[Math.round(Number(track.file?.durationSeconds||0)*10),(track.neural?.embedding?.vector||[]).slice(0,96).map(v=>Number(v).toFixed(4)).join(','),normalize(track.title)].join('|'); let h=2166136261; for(let i=0;i<basis.length;i++){h^=basis.charCodeAt(i);h=Math.imul(h,16777619);} return `st-${(h>>>0).toString(16).padStart(8,'0')}`; }
  function studioTrackId() { const context=window.SonicTraceStudioContext?.trackId || new URLSearchParams(location.search).get('trackId') || new URLSearchParams(location.search).get('track_id') || ''; return /^[a-z0-9][a-z0-9-]{0,119}$/.test(String(context)) ? String(context) : null; }

  function openDb() { if(dbPromise)return dbPromise; dbPromise=new Promise((resolve,reject)=>{const request=indexedDB.open(DB,VERSION);request.onupgradeneeded=()=>{const db=request.result;if(!db.objectStoreNames.contains(TRACKS)){const s=db.createObjectStore(TRACKS,{keyPath:'id'});s.createIndex('title','title');s.createIndex('updatedAt','updatedAt');}if(!db.objectStoreNames.contains(PROJECTS)){const s=db.createObjectStore(PROJECTS,{keyPath:'id'});s.createIndex('updatedAt','updatedAt');}};request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error||new Error('IndexedDB open failed'));}); return dbPromise; }
  async function tx(store,mode,action) { const db=await openDb(); return new Promise((resolve,reject)=>{const t=db.transaction(store,mode),s=t.objectStore(store),r=action(s);let value;r.onsuccess=()=>{value=r.result;};r.onerror=()=>reject(r.error||new Error('IndexedDB request failed'));t.oncomplete=()=>resolve(value);t.onerror=()=>reject(t.error||new Error('IndexedDB transaction failed'));}); }
  const put=(s,v)=>tx(s,'readwrite',o=>o.put(v)), get=(s,k)=>tx(s,'readonly',o=>o.get(k)), all=s=>tx(s,'readonly',o=>o.getAll()), remove=(s,k)=>tx(s,'readwrite',o=>o.delete(k)), clear=s=>tx(s,'readwrite',o=>o.clear());
  async function saveCurrentTrack(){const track=await buildCurrentSnapshot();if(!track.neural.embedding.vector.length)throw new Error('Embedding Neural absent : relance une Analyse complète avec Neural actif.');const existing=await getTrack(track.id);if(existing?.createdAt)track.createdAt=existing.createdAt;track.updatedAt=new Date().toISOString();await put(TRACKS,track);document.dispatchEvent(new CustomEvent('sonictrace:catalog-track-saved',{detail:{track,updated:Boolean(existing)}}));return{track,updated:Boolean(existing)};}
  const getTrack=id=>get(TRACKS,id); async function getTracks(){return(await all(TRACKS)).sort((a,b)=>String(b.updatedAt||'').localeCompare(String(a.updatedAt||'')));}
  async function deleteTrack(id){await remove(TRACKS,id);document.dispatchEvent(new CustomEvent('sonictrace:catalog-track-deleted',{detail:{id}}));}
  async function clearTracks(){await clear(TRACKS);document.dispatchEvent(new CustomEvent('sonictrace:catalog-cleared'));}
  async function saveProject(project){const now=new Date().toISOString(),clean={...clone(project),id:project.id||`project-${Date.now().toString(36)}`,createdAt:project.createdAt||now,updatedAt:now};await put(PROJECTS,clean);document.dispatchEvent(new CustomEvent('sonictrace:catalog-project-saved',{detail:{project:clean}}));return clean;}
  async function getProjects(){return(await all(PROJECTS)).sort((a,b)=>String(b.updatedAt||'').localeCompare(String(a.updatedAt||'')));}
  async function exportCatalog(){return{schema:'sonictrace.catalog.export.v1',exportedAt:new Date().toISOString(),tracks:await getTracks(),projects:await getProjects()};}
  async function importCatalog(payload){if(!payload||!Array.isArray(payload.tracks))throw new Error('Fichier catalogue invalide.');for(const t of payload.tracks)if(t?.id&&t?.neural?.embedding)await put(TRACKS,t);for(const p of Array.isArray(payload.projects)?payload.projects:[])if(p?.id)await put(PROJECTS,p);document.dispatchEvent(new CustomEvent('sonictrace:catalog-imported'));}

  function clone(v){if(v==null)return v;try{return structuredClone(v);}catch(_){return JSON.parse(JSON.stringify(v));}}
  function cleanTitle(v){return String(v||'Untitled').replace(/[_-]+/g,' ').replace(/\s+/g,' ').trim();}
  function normalize(v){return String(v||'').toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();}
  function parse(v){if(v==null||v==='')return null;const m=String(v).replace(',','.').match(/-?\d+(?:\.\d+)?/);return m?num(m[0]):null;}
  function num(v){if(v==null||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;}
  function clamp(v,min,max){return Math.max(min,Math.min(max,Number(v)||0));}

  NS.memory={openDb,buildCurrentSnapshot,saveCurrentTrack,getTrack,getTracks,deleteTrack,clearTracks,saveProject,getProjects,exportCatalog,importCatalog};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
