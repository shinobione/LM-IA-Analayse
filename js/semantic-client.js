(() => {
  'use strict';

  const API = 'http://127.0.0.1:8000';
  const LABELS = ['Intro', 'Verse', 'Pre-Chorus', 'Chorus', 'Bridge', 'Interlude', 'Drop', 'Instrumental', 'Outro'];
  let selectedAudio = null;
  let selectedLyrics = null;
  let semanticReady = false;

  document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('audio-file-input');
    const deepBtn = document.getElementById('deep-analyze-audio-btn');
    if (!input || !deepBtn) return;

    const ui = ensureControls(deepBtn);
    input.addEventListener('change', () => {
      selectedAudio = input.files?.[0] || null;
      sync(ui);
    });
    document.getElementById('drop-zone')?.addEventListener('drop', event => {
      selectedAudio = event.dataTransfer?.files?.[0] || selectedAudio;
      sync(ui);
    });
    ui.lyricsInput.addEventListener('change', () => {
      selectedLyrics = ui.lyricsInput.files?.[0] || null;
      ui.lyricsName.textContent = selectedLyrics ? selectedLyrics.name : 'Lyrics optionnelles';
      ui.lyricsWrap.classList.toggle('has-file', Boolean(selectedLyrics));
      sync(ui);
    });
    ui.clearLyrics.addEventListener('click', () => {
      ui.lyricsInput.value = '';
      selectedLyrics = null;
      ui.lyricsName.textContent = 'Lyrics optionnelles';
      ui.lyricsWrap.classList.remove('has-file');
      sync(ui);
    });
    ui.button.addEventListener('click', () => runSemantic(ui));
    window.setTimeout(() => refreshCapability(ui), 1200);
  });

  function ensureControls(deepBtn) {
    let button = document.getElementById('semantic-arrangement-btn');
    if (button) {
      return {
        button,
        lyricsInput: document.getElementById('semantic-lyrics-input'),
        lyricsName: document.getElementById('semantic-lyrics-name'),
        lyricsWrap: document.getElementById('semantic-lyrics-wrap'),
        clearLyrics: document.getElementById('semantic-lyrics-clear'),
      };
    }

    const fusionBtn = document.getElementById('fusion-analyze-audio-btn');
    button = document.createElement('button');
    button.id = 'semantic-arrangement-btn';
    button.type = 'button';
    button.className = 'primary-btn semantic-btn';
    button.disabled = true;
    button.innerHTML = '<i data-lucide="brain"></i> Semantic Arrangement V2-CD.1';
    (fusionBtn || deepBtn).insertAdjacentElement('afterend', button);

    const wrap = document.createElement('div');
    wrap.id = 'semantic-lyrics-wrap';
    wrap.className = 'semantic-lyrics-wrap';
    wrap.innerHTML = `
      <input id="semantic-lyrics-input" type="file" accept="text/plain,.txt,.lrc" />
      <label for="semantic-lyrics-input" class="semantic-lyrics-label">
        <i data-lucide="captions"></i>
        <span><strong id="semantic-lyrics-name">Lyrics optionnelles</strong><small>TXT/LRC • timestampées = précision max</small></span>
      </label>
      <button id="semantic-lyrics-clear" type="button" class="semantic-lyrics-clear" title="Retirer les lyrics">×</button>`;
    button.insertAdjacentElement('afterend', wrap);
    window.lucide?.createIcons?.();

    return {
      button,
      lyricsInput: wrap.querySelector('#semantic-lyrics-input'),
      lyricsName: wrap.querySelector('#semantic-lyrics-name'),
      lyricsWrap: wrap,
      clearLyrics: wrap.querySelector('#semantic-lyrics-clear'),
    };
  }

  async function refreshCapability(ui) {
    try {
      const response = await fetch(`${API}/api/fusion/status`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      semanticReady = Boolean(payload.ready);
    } catch (_) {
      semanticReady = false;
    }
    sync(ui);
  }

  function sync(ui) {
    if (!ui?.button) return;
    ui.button.disabled = !(selectedAudio && semanticReady);
  }

  async function runSemantic(ui) {
    if (!selectedAudio || !semanticReady) return;
    setBusy(true, ui.button);
    setV2Status('V3.2 SEMANTIC', selectedLyrics
      ? `Fusion + Neural V3.2 + lecture de ${selectedLyrics.name}…`
      : 'Fusion + Neural V3.2 + grammaire d’arrangement…');
    setProgress(8);

    try {
      const lyricsPromise = selectedLyrics ? selectedLyrics.text() : Promise.resolve('');
      const fusionForm = new FormData();
      fusionForm.append('file', selectedAudio, selectedAudio.name);
      const neuralForm = new FormData();
      neuralForm.append('file', selectedAudio, selectedAudio.name);

      setProgress(14);
      const [fusionResponse, neuralResponse, lyricsText] = await Promise.all([
        fetch(`${API}/api/fusion`, { method: 'POST', body: fusionForm }),
        fetch(`${API}/api/analyze?neural=true`, { method: 'POST', body: neuralForm }),
        lyricsPromise,
      ]);

      if (!fusionResponse.ok) throw new Error(`Fusion: ${await responseError(fusionResponse)}`);
      if (!neuralResponse.ok) throw new Error(`Neural: ${await responseError(neuralResponse)}`);
      setProgress(82);

      const fusionPayload = await fusionResponse.json();
      const neuralPayload = await neuralResponse.json();
      const lyrics = parseLyrics(lyricsText || '');
      const semantic = buildSemanticArrangement(fusionPayload, neuralPayload, lyrics);
      renderSemantic(semantic, fusionPayload, lyrics);
      setProgress(100);
      setV2Status('V3.2 SEMANTIC', `${selectedAudio.name} • ${semantic.arrangement.length} blocs finaux • ${semantic.genre.display} • lyrics ${lyrics.mode}`);
    } catch (error) {
      setProgress(0);
      setV2Status('V3.2 ERROR', error.message || 'Semantic Arrangement failed', true);
    } finally {
      setBusy(false, ui.button);
      sync(ui);
    }
  }

  function parseLyrics(text) {
    const raw = String(text || '').replace(/\r/g, '').trim();
    if (!raw) return { mode: 'none', entries: [], blocks: [], repeatedLines: new Map(), coverage: 0 };

    const lines = raw.split('\n');
    const entries = [];
    const plainBlocks = raw.split(/\n\s*\n+/).map(block => block.split('\n').map(x => x.trim()).filter(Boolean)).filter(Boolean);
    let pendingTime = null;
    let timedCount = 0;

    for (const original of lines) {
      const line = original.trim();
      if (!line) continue;
      const inline = line.match(/^\[?(?:(\d{1,2}):)?(\d{1,2}):(\d{2}(?:[.:]\d{1,3})?)\]?\s*(.*)$/);
      const standalone = line.match(/^\[?(\d{1,2}):(\d{2}(?:[.:]\d{1,3})?)\]?\s*(.*)$/);
      let time = null;
      let content = '';
      if (inline && inline[1] != null) {
        time = Number(inline[1]) * 3600 + Number(inline[2]) * 60 + parseSeconds(inline[3]);
        content = inline[4].trim();
      } else if (standalone) {
        time = Number(standalone[1]) * 60 + parseSeconds(standalone[2]);
        content = standalone[3].trim();
      }
      if (time != null && Number.isFinite(time)) {
        pendingTime = time;
        if (content) {
          entries.push({ time, text: content, norm: normalizeLyric(content) });
          pendingTime = null;
          timedCount++;
        }
        continue;
      }
      if (pendingTime != null) {
        entries.push({ time: pendingTime, text: line, norm: normalizeLyric(line) });
        pendingTime = null;
        timedCount++;
      }
    }

    const allTextLines = lines.map(x => x.trim()).filter(x => x && !looksLikeTimestampOnly(x));
    const counts = new Map();
    for (const line of allTextLines) {
      const n = normalizeLyric(stripTimestamp(line));
      if (n.length >= 3) counts.set(n, (counts.get(n) || 0) + 1);
    }
    const repeatedLines = new Map([...counts].filter(([, count]) => count >= 2));
    entries.sort((a, b) => a.time - b.time);

    return {
      mode: timedCount >= Math.max(2, Math.round(allTextLines.length * 0.3)) ? 'timed' : 'plain',
      entries,
      blocks: plainBlocks,
      repeatedLines,
      coverage: allTextLines.length ? timedCount / allTextLines.length : 0,
      lineCount: allTextLines.length,
    };
  }

  function buildSemanticArrangement(fusionPayload, neuralPayload, lyrics) {
    const fusion = fusionPayload.fusion || {};
    const sections = (fusion.sections || []).map((section, index) => ({ ...section, semantic_index: index }));
    const genre = inferGenre(neuralPayload);
    const lyricFeatures = lyricsForSections(sections, lyrics);
    sections.forEach((section, index) => { section.lyrics = lyricFeatures[index]; });

    const candidateScores = sections.map((section, index) => scoreSection(section, index, sections, genre, lyrics));
    applyContextBoosts(candidateScores, sections, genre);
    const sequence = viterbiLabels(candidateScores, sections, genre);
    const semanticSections = sections.map((section, index) => finalizeSection(section, candidateScores[index], sequence[index], genre));
    const merged = mergeAdjacent(semanticSections);

    return {
      version: '2.6-v3.2',
      genre,
      lyrics: {
        mode: lyrics.mode,
        line_count: lyrics.lineCount || 0,
        timed_coverage: Math.round((lyrics.coverage || 0) * 100),
        repeated_line_count: lyrics.repeatedLines?.size || 0,
      },
      sections: semanticSections,
      arrangement: merged,
      summary: countLabels(merged),
      compute: {
        coordinator: fusionPayload.compute?.coordinator || fusionPayload.compute?.node_name || 'RTX3060-PRIMARY',
        stems_node: fusionPayload.compute?.stems_node || '—',
        stems_device: fusionPayload.compute?.stems_device || '—',
        stems_route: fusionPayload.compute?.stems_route || '—',
      },
    };
  }

  function inferGenre(neuralPayload) {
    const neural = neuralPayload?.neural || {};
    const labels = collectNeuralLabels(neural);
    const structured = structuredGenreContext(neural.genre_analysis);
    if (structured) return { ...structured, top: labels.slice(0, 5) };
    const legacy = legacyGenreContext(labels[0]);
    return { ...legacy, top: labels.slice(0, 5) };
  }

  function structuredGenreContext(analysis) {
    if (!analysis || typeof analysis !== 'object') return null;

    const dimensional = window.LMNSemanticV32?.contextFromDimensions?.(analysis.dimensions, analysis);
    if (dimensional) return dimensional;

    const ensemble = analysis.ensemble && typeof analysis.ensemble === 'object' ? analysis.ensemble : null;
    const primary = ensemble?.primary && typeof ensemble.primary === 'object'
      ? ensemble.primary
      : analysis.primary;
    if (!primary || typeof primary !== 'object') return null;

    const rawLabel = String(primary.label || '').trim();
    const unknown = rawLabel.toLowerCase() === 'unknown / hybrid';
    const candidate = unknown && primary.candidate && typeof primary.candidate === 'object'
      ? primary.candidate
      : primary;
    const candidateLabel = String(candidate?.label || '').trim();
    const familyLabel = String(candidate?.family || primary.family || '').trim();
    const broadFamily = familyLabel || broadFamilyFromLabel(candidateLabel || rawLabel);
    const display = unknown
      ? 'Hybride / incertain'
      : (rawLabel || candidateLabel || broadFamily || 'Style non déterminé');

    const context = {
      family: arrangementFamily(broadFamily, candidateLabel || rawLabel),
      broadFamily: broadFamily || 'Général',
      display,
      primary: rawLabel || candidateLabel || '',
      primaryStyle: rawLabel || candidateLabel || '',
      tradition: '',
      form: '',
      region: String(candidate?.region || primary.region || '').trim(),
      unknown,
      source: 'neural-v3.1-structured',
    };
    context.grammar = window.LMNSemanticV32?.arrangementGrammar?.(context) || 'general';
    return context;
  }

  function legacyGenreContext(primary) {
    if (!primary) {
      return {
        family: 'general',
        broadFamily: 'Général',
        display: 'Style non déterminé',
        primary: '',
        primaryStyle: '',
        tradition: '',
        form: '',
        region: '',
        unknown: true,
        grammar: 'general',
        source: 'legacy-empty',
      };
    }
    const label = String(primary.label || '').trim();
    const broadFamily = broadFamilyFromLabel(label);
    const context = {
      family: arrangementFamily(broadFamily, label),
      broadFamily,
      display: label || broadFamily,
      primary: label,
      primaryStyle: label,
      tradition: '',
      form: '',
      region: '',
      unknown: false,
      source: 'legacy-top-label-only',
    };
    context.grammar = window.LMNSemanticV32?.arrangementGrammar?.(context) || 'general';
    return context;
  }

  function broadFamilyFromLabel(label) {
    const text = normalizeGenreText(label);
    if (/vietnam|nhac vang|nhac tru tinh|v-pop|asian ballad/.test(text)) return 'Vietnamese / Asian';
    if (/hip.?hop|\brap\b|trap|drill|boom bap|phonk|g-funk|cloud rap|grime/.test(text)) return 'Hip-Hop / Rap';
    if (/r&b|\brnb\b|soul|funk|new jack swing|quiet storm/.test(text)) return 'R&B / Soul / Funk';
    if (/dubstep|\bedm\b|house|techno|trance|drum.?and.?bass|\bdnb\b|future bass|electronic|synthwave|ambient|jungle|glitch|idm/.test(text)) return 'Electronic';
    if (/reggae|dancehall|dub|lovers rock|ska|soca/.test(text)) return 'Reggae / Caribbean';
    if (/latin|reggaeton|salsa|cumbia|bachata|tango|samba|bossa nova/.test(text)) return 'Latin';
    if (/rock|metal|punk|shoegaze|post-rock/.test(text)) return 'Rock / Metal';
    if (/folk|world|fado|zouk|highlife|afrobeat|indian classical/.test(text)) return 'Folk / World';
    if (/jazz/.test(text)) return 'Jazz';
    if (/classical|neo-classical|soundtrack|score|cinematic/.test(text)) return 'Classical / Screen';
    if (/\bpop\b|synthpop|synth-pop|electropop|city pop|j-pop|k-pop|chanson|europop/.test(text)) return 'Pop';
    return 'Général';
  }

  function arrangementFamily(broadFamily, label) {
    const helper = window.LMNSemanticV32?.arrangementFamily;
    if (typeof helper === 'function') return helper(broadFamily, label);

    const family = normalizeGenreText(broadFamily);
    const style = normalizeGenreText(label);
    if (/hip.?hop|\brap\b/.test(family)) return 'hip-hop';
    if (/r&b|soul|funk/.test(family)) return 'r&b';
    if (/electronic|\bedm\b/.test(family)) return 'edm';
    if (family === 'pop') return 'pop';
    if (/rock|metal/.test(family)) return 'rock';
    if (!broadFamily || family === 'general') {
      if (/hip.?hop|\brap\b|trap|drill|boom bap/.test(style)) return 'hip-hop';
      if (/r&b|\brnb\b|soul|neo soul/.test(style)) return 'r&b';
      if (/dubstep|\bedm\b|house|techno|trance|drum.?and.?bass|\bdnb\b|future bass|electronic/.test(style)) return 'edm';
      if (/\bpop\b|synthpop|electropop/.test(style)) return 'pop';
      if (/rock|metal|punk/.test(style)) return 'rock';
    }
    return 'general';
  }

  function normalizeGenreText(value) {
    return String(value || '')
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[’']/g, "'");
  }

  function collectNeuralLabels(neural) {
    const out = [];
    const visit = value => {
      if (Array.isArray(value)) {
        value.forEach(item => {
          if (item && typeof item === 'object') {
            const label = item.label || item.name || item.text;
            const score = Number(item.score ?? item.confidence ?? item.probability ?? item.percent ?? 0);
            if (label) out.push({ label: String(label), score: score > 1 ? score / 100 : score });
          }
        });
      }
    };
    visit(neural.genres);
    visit(neural.styles);
    visit(neural.genre_style);
    visit(neural.genre_styles);
    if (!out.length) Object.values(neural).forEach(visit);
    const unique = new Map();
    out.forEach(item => {
      const key = item.label.toLowerCase();
      if (!unique.has(key) || unique.get(key).score < item.score) unique.set(key, item);
    });
    return [...unique.values()].sort((a, b) => b.score - a.score);
  }

  function lyricsForSections(sections, lyrics) {
    if (lyrics.mode === 'none') return sections.map(() => emptyLyricFeature());
    if (lyrics.mode === 'timed' && lyrics.entries.length) {
      return sections.map((section, index) => {
        const start = Number(section.start || 0);
        const end = Number(section.end || start);
        const items = lyrics.entries.filter(entry => entry.time >= start && entry.time < end);
        return featureFromLines(items.map(item => item.text), lyrics, section, index);
      });
    }

    const blocks = lyrics.blocks || [];
    return sections.map((section, index) => {
      const mapped = blocks.length ? blocks[Math.min(blocks.length - 1, Math.floor(index * blocks.length / Math.max(sections.length, 1)))] : [];
      return featureFromLines(mapped || [], lyrics, section, index, true);
    });
  }

  function featureFromLines(lines, lyrics, section, index, approximate = false) {
    const norms = lines.map(normalizeLyric).filter(Boolean);
    const repeated = norms.filter(n => (lyrics.repeatedLines?.get(n) || 0) >= 2);
    const unique = new Set(norms);
    const repeatsInside = norms.length - unique.size;
    const duration = Math.max(1, Number(section.duration || (section.end - section.start) || 1));
    const density = Math.min(1, norms.length / Math.max(2, duration / 4));
    const repeatedRatio = norms.length ? repeated.length / norms.length : 0;
    const internalRepeat = norms.length ? repeatsInside / norms.length : 0;
    const hookness = clamp(0.55 * repeatedRatio + 0.25 * internalRepeat + 0.20 * Math.min(1, norms.filter(n => n.split(' ').length <= 8).length / Math.max(1, norms.length)), 0, 1);
    return {
      line_count: norms.length,
      density: round(density, 3),
      repeated_ratio: round(repeatedRatio, 3),
      hook_score: round(hookness, 3),
      approximate,
      sample: lines.slice(0, 2),
    };
  }

  function emptyLyricFeature() {
    return { line_count: 0, density: 0, repeated_ratio: 0, hook_score: 0, approximate: false, sample: [] };
  }

  function scoreSection(section, index, sections, genre, lyrics) {
    const base = Object.fromEntries(LABELS.map(label => [label, 0.08]));
    const sourceType = canonicalType(section.fusion_type || section.type || section.fusion_label || '');
    const sourceConf = Number(section.fusion_confidence || 0.5);
    if (base[sourceType] != null) base[sourceType] += 0.34 + sourceConf * 0.18;

    const v = stem(section, 'vocals');
    const d = stem(section, 'drums');
    const b = stem(section, 'bass');
    const o = stem(section, 'other');
    const energy = Number(section.energy || 0) / 100;
    const rhythm = Number(section.rhythmic || 0) / 100;
    const repeat = Math.max(Number(section.fusion_repeat_strength || 0), Number(section.repeat_strength || 0));
    const repeatCount = Number(section.fusion_repeat_count || section.repeat_count || 1);
    const hook = Number(section.fusion_hook_score || 0) / 100;
    const lyric = section.lyrics || emptyLyricFeature();
    const position = Number(section.start || 0) / Math.max(Number(sections.at(-1)?.end || 1), 1);
    const duration = Number(section.duration || 0);

    base.Chorus += 0.20 * repeat + 0.14 * Math.min(1, repeatCount / 3) + 0.16 * hook + 0.14 * lyric.hook_score + 0.10 * lyric.repeated_ratio + 0.10 * v + 0.08 * d + 0.05 * energy;
    base.Verse += 0.20 * v + 0.15 * lyric.density + 0.08 * (1 - lyric.hook_score) + 0.08 * (1 - repeat) + 0.07 * rhythm + 0.05 * (duration >= 15 && duration <= 45 ? 1 : 0);
    base['Pre-Chorus'] += 0.11 * v + 0.08 * lyric.density + 0.06 * hook + 0.07 * rhythm + 0.08 * (duration >= 6 && duration <= 24 ? 1 : 0);
    base.Bridge += 0.12 * v + 0.13 * (1 - repeat) + 0.12 * (position > 0.45 && position < 0.88 ? 1 : 0) + 0.09 * Math.abs(o - d);
    base.Interlude += 0.18 * (1 - v) + 0.10 * o + 0.07 * (1 - lyric.density) + 0.05 * (1 - repeat) + 0.04 * (duration >= 6 && duration <= 40 ? 1 : 0);
    base.Drop += 0.22 * d + 0.18 * b + 0.16 * energy + 0.10 * rhythm + 0.08 * (1 - v) + 0.06 * hook;
    base.Instrumental += 0.30 * (1 - v) + 0.14 * o + 0.08 * (1 - lyric.density);

    if (index === 0) {
      base.Intro += 0.46 + 0.12 * (1 - v) + 0.08 * (1 - lyric.density);
      if (duration > 45 && (v > 0.45 || lyric.line_count >= 4)) base.Intro -= 0.30;
    } else base.Intro *= 0.15;

    if (index === sections.length - 1) base.Outro += 0.42 + 0.11 * (1 - d) + 0.08 * (1 - energy);
    else base.Outro *= 0.15;

    if (genre.family === 'hip-hop' || genre.family === 'r&b') {
      base.Verse += 0.12 * v + 0.08 * lyric.density;
      base.Chorus += 0.08 * lyric.hook_score;
      base.Drop *= 0.48;
      if (v > 0.6) base.Drop *= 0.6;
    } else if (genre.family === 'edm') {
      base.Drop += 0.14 * d + 0.12 * b + 0.08 * (1 - v);
      base.Instrumental += 0.06 * (1 - v);
    } else if (genre.family === 'pop') {
      base.Chorus += 0.08 * lyric.hook_score + 0.05 * v;
      base.Verse += 0.05 * lyric.density;
    }

    if (lyrics.mode === 'timed') {
      base.Chorus += 0.10 * lyric.repeated_ratio;
      base.Verse += 0.06 * lyric.density * (1 - lyric.repeated_ratio);
    }

    window.LMNSemanticV32?.applySectionGrammar?.(base, {
      section,
      index,
      sections,
      genre,
      lyrics,
      position,
      repeat,
    });

    LABELS.forEach(label => { base[label] = clamp(base[label], 0.001, 1.45); });
    return base;
  }

  function applyContextBoosts(scores, sections, genre) {
    for (let i = 0; i < sections.length; i++) {
      const current = sections[i];
      const next = sections[i + 1];
      const prev = sections[i - 1];
      if (next) {
        const rise = (Number(next.energy || 0) - Number(current.energy || 0)) / 100;
        scores[i]['Pre-Chorus'] += 0.22 * normalizeScore(scores[i + 1].Chorus) + 0.10 * Math.max(0, rise);
      }
      if (prev && next) {
        const contrastPrev = profileDistance(current, prev);
        const contrastNext = profileDistance(current, next);
        if (i > sections.length * 0.4) scores[i].Bridge += 0.10 * Math.min(1, (contrastPrev + contrastNext) / 1.2);
      }
      if (genre.family !== 'edm' && i > 0 && i < sections.length - 1 && stem(current, 'vocals') > 0.55) scores[i].Drop *= 0.72;
      window.LMNSemanticV32?.applyContextGrammar?.(scores[i], current, prev, next, genre);
      LABELS.forEach(label => { scores[i][label] = clamp(scores[i][label], 0.001, 1.45); });
    }
  }

  function viterbiLabels(scores, sections, genre) {
    const n = scores.length;
    if (!n) return [];
    const dp = Array.from({ length: n }, () => Object.fromEntries(LABELS.map(l => [l, -Infinity])));
    const back = Array.from({ length: n }, () => ({}));
    for (const label of LABELS) dp[0][label] = Math.log(Math.max(scores[0][label], 1e-6)) + startPrior(label);

    for (let i = 1; i < n; i++) {
      for (const label of LABELS) {
        const emission = Math.log(Math.max(scores[i][label], 1e-6));
        for (const prev of LABELS) {
          const value = dp[i - 1][prev] + transition(prev, label, genre, i, n) + emission;
          if (value > dp[i][label]) {
            dp[i][label] = value;
            back[i][label] = prev;
          }
        }
      }
    }
    let last = LABELS.reduce((best, label) => dp[n - 1][label] > dp[n - 1][best] ? label : best, LABELS[0]);
    const seq = Array(n);
    seq[n - 1] = last;
    for (let i = n - 1; i > 0; i--) {
      last = back[i][last] || last;
      seq[i - 1] = last;
    }
    return seq;
  }

  function transition(a, b, genre, i, n) {
    const map = {
      Intro: { Verse: 0.35, Chorus: 0.12, Instrumental: 0.15, Interlude: 0.08, 'Pre-Chorus': 0.05 },
      Verse: { 'Pre-Chorus': 0.34, Chorus: 0.30, Verse: 0.10, Bridge: 0.06, Interlude: 0.07, Outro: -0.10 },
      'Pre-Chorus': { Chorus: 0.48, Drop: genre.family === 'edm' ? 0.34 : -0.18, Interlude: -0.04 },
      Chorus: { Verse: 0.30, Bridge: 0.18, Interlude: 0.12, Chorus: 0.06, Outro: 0.16, Drop: genre.family === 'edm' ? 0.12 : -0.16 },
      Bridge: { Chorus: 0.34, Verse: 0.08, Interlude: 0.10, Outro: 0.15 },
      Interlude: { Verse: 0.18, Chorus: 0.20, Bridge: 0.12, Instrumental: 0.10, Outro: 0.14 },
      Drop: { Verse: 0.12, Chorus: 0.18, Bridge: 0.05, Interlude: 0.02, Drop: 0.04, Outro: 0.08 },
      Instrumental: { Verse: 0.14, Chorus: 0.10, Interlude: 0.12, Drop: genre.family === 'edm' ? 0.16 : 0.02, Outro: 0.12 },
      Outro: { Outro: 0.25 },
    };
    let value = a === b ? 0.18 : (map[a]?.[b] ?? -0.08);
    if (b === 'Outro' && i < n - 2) value -= 0.35;
    if (b === 'Intro' && i > 0) value -= 0.75;
    if (genre.family !== 'edm' && b === 'Drop') value -= 0.18;
    value += Number(window.LMNSemanticV32?.transitionAdjustment?.(a, b, genre, i, n) || 0);
    return value;
  }

  function startPrior(label) {
    if (label === 'Intro') return 0.55;
    if (label === 'Verse') return 0.18;
    if (label === 'Instrumental') return 0.05;
    if (label === 'Interlude') return -0.02;
    return -0.15;
  }

  function finalizeSection(section, rawScores, chosen, genre) {
    const ordered = Object.entries(rawScores).sort((a, b) => b[1] - a[1]);
    const chosenScore = rawScores[chosen] || ordered[0][1];
    const second = ordered.find(([name]) => name !== chosen)?.[1] || 0;
    const normalized = clamp(chosenScore / 1.35, 0, 1);
    const confidence = clamp(0.44 + normalized * 0.38 + Math.max(0, chosenScore - second) * 0.20, 0.42, 0.97);
    const evidence = [...(section.evidence || [])];
    const lyric = section.lyrics || emptyLyricFeature();
    if (lyric.line_count) evidence.push(`lyrics ${lyric.line_count} lignes`);
    if (lyric.repeated_ratio >= 0.45) evidence.push(`lyrics répétées ${Math.round(lyric.repeated_ratio * 100)}%`);
    if (lyric.hook_score >= 0.55) evidence.push(`hook textuel ${Math.round(lyric.hook_score * 100)}%`);
    if (genre.family !== 'general') evidence.push(`contexte ${genre.family}`);
    if (genre.grammar === 'sentimental-song') evidence.push('grammaire chanson sentimentale');
    else if (genre.grammar === 'electronic-drop') evidence.push('grammaire électronique / drops');
    return {
      ...section,
      semantic_type: chosen,
      semantic_confidence: round(confidence, 3),
      semantic_score: round(chosenScore, 3),
      semantic_alternatives: ordered.filter(([name]) => name !== chosen).slice(0, 3).map(([type, score]) => ({ type, score: round(score, 3) })),
      semantic_evidence: [...new Set(evidence)].slice(0, 7),
    };
  }

  function mergeAdjacent(sections) {
    const out = [];
    for (const section of sections) {
      const last = out.at(-1);
      if (last && last.semantic_type === section.semantic_type && canMerge(last, section)) {
        last.end = section.end;
        last.duration = Number(last.end) - Number(last.start);
        last.source_sections.push(section.semantic_index);
        last.semantic_confidence = round((Number(last.semantic_confidence) + Number(section.semantic_confidence)) / 2, 3);
        last.semantic_evidence = [...new Set([...last.semantic_evidence, ...section.semantic_evidence])].slice(0, 8);
        last.stem_activity = averageStemActivity(last.stem_activity, section.stem_activity);
        last.lyrics.line_count += section.lyrics?.line_count || 0;
        continue;
      }
      out.push({ ...section, source_sections: [section.semantic_index], lyrics: { ...(section.lyrics || emptyLyricFeature()) } });
    }
    const counts = {};
    out.forEach(item => {
      counts[item.semantic_type] = (counts[item.semantic_type] || 0) + 1;
      item.semantic_label = ['Verse', 'Chorus', 'Pre-Chorus', 'Interlude', 'Drop'].includes(item.semantic_type)
        ? `${item.semantic_type} ${counts[item.semantic_type]}`
        : item.semantic_type;
    });
    return out;
  }

  function canMerge(a, b) {
    const gap = Number(b.start || 0) - Number(a.end || 0);
    const total = Number(b.end || 0) - Number(a.start || 0);
    const sameRepeat = a.fusion_repeat_group && a.fusion_repeat_group === b.fusion_repeat_group;
    return gap < 1.5 && total <= 65 && (sameRepeat || profileDistance(a, b) < 0.42 || a.semantic_type === 'Drop');
  }

  function averageStemActivity(a = {}, b = {}) {
    const out = {};
    ['vocals', 'drums', 'bass', 'other'].forEach(name => {
      out[name] = { ...(a[name] || {}) };
      const av = Number(a[name]?.score || 0);
      const bv = Number(b[name]?.score || 0);
      out[name].score = round((av + bv) / 2, 1);
    });
    return out;
  }

  function renderSemantic(semantic, fusionPayload, lyrics) {
    const root = ensureResults();
    const arrangement = semantic.arrangement;
    const duration = Number(arrangement.at(-1)?.end || 1);
    const genreTop = semantic.genre.top.slice(0, 4).map(x => `${esc(x.label)} ${Math.round((x.score || 0) * 100)}%`).join(' • ') || 'aucun contexte neural';
    const route = semantic.compute.stems_route;
    const genreDisplay = semantic.genre.display || semantic.genre.primary || semantic.genre.broadFamily || semantic.genre.family;
    const genreBadge = semantic.genre.broadFamily || genreDisplay || semantic.genre.family;

    root.innerHTML = `
      <div class="semantic-head">
        <div><div class="semantic-title"><i data-lucide="brain-circuit"></i> Semantic Arrangement V3.2</div>
        <div class="semantic-sub">Neural V3.2 + structure V2-C + stems V2-D + ${lyrics.mode === 'none' ? 'grammaire musicale' : `lyrics ${lyrics.mode}`}</div></div>
        <div class="semantic-badge">${esc(String(genreBadge).toUpperCase())}<span>${esc(route)}</span></div>
      </div>
      <div class="semantic-summary">
        ${summaryCard('FINAL BLOCKS', arrangement.length, `${(fusionPayload.fusion?.sections || []).length} sections source`)}
        ${summaryCard('GENRE CONTEXT', esc(genreDisplay), genreTop)}
        ${summaryCard('LYRICS', esc(semantic.lyrics.mode), `${semantic.lyrics.line_count} lignes • ${semantic.lyrics.repeated_line_count} répétées`)}
        ${summaryCard('TIMED COVERAGE', `${semantic.lyrics.timed_coverage}%`, semantic.lyrics.mode === 'timed' ? 'alignement temporel actif' : 'mapping approximatif / absent')}
        ${summaryCard('STEMS ROUTE', esc(route), esc(semantic.compute.stems_device))}
      </div>
      <div class="semantic-panel">
        <div class="semantic-panel-head"><strong>Final Arrangement</strong><span>séquence optimisée + grammaire V3.2 + merges contextuels</span></div>
        <div class="semantic-timeline">${arrangement.map((item, index) => timelineBlock(item, duration, index)).join('')}</div>
        <div id="semantic-detail" class="semantic-detail"></div>
      </div>
      <div class="semantic-grid">
        <div class="semantic-panel"><div class="semantic-panel-head"><strong>Arrangement Evidence</strong><span>pourquoi ce label</span></div><div class="semantic-evidence-list">${arrangement.map((item, index) => evidenceRow(item, index)).join('')}</div></div>
        <div class="semantic-panel"><div class="semantic-panel-head"><strong>Lyrics / Neural Context</strong><span>dimensions V3.2 + indices Neural</span></div>${contextPanel(semantic)}</div>
      </div>`;

    root.classList.remove('hidden');
    root.querySelectorAll('[data-semantic]').forEach(button => button.addEventListener('click', () => selectSemantic(root, arrangement, Number(button.dataset.semantic))));
    selectSemantic(root, arrangement, 0);
    window.lucide?.createIcons?.();
    root.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function ensureResults() {
    let section = document.getElementById('v2-semantic-results');
    if (section) return section;
    section = document.createElement('section');
    section.id = 'v2-semantic-results';
    section.className = 'glass-card semantic-results hidden';
    const fusion = document.getElementById('v2-fusion-results');
    const anatomy = document.getElementById('v2-anatomy-results');
    (fusion || anatomy || document.getElementById('v2-results'))?.insertAdjacentElement('afterend', section);
    return section;
  }

  function timelineBlock(item, duration, index) {
    const width = clamp((Number(item.duration || 0) / duration) * 100, 2, 100);
    return `<button data-semantic="${index}" class="semantic-block type-${slug(item.semantic_type)}" style="flex-basis:${width}%" title="${esc(item.semantic_label)} • ${pct(item.semantic_confidence)}">
      <strong>${esc(item.semantic_label)}</strong><small>${fmtTime(item.start)} • ${pct(item.semantic_confidence)}</small>
      ${item.source_sections.length > 1 ? `<em>${item.source_sections.length}× merge</em>` : ''}
    </button>`;
  }

  function evidenceRow(item, index) {
    return `<button data-semantic="${index}" class="semantic-evidence-row"><span><strong>${esc(item.semantic_label)}</strong><small>${fmtTime(item.start)}–${fmtTime(item.end)} • ${pct(item.semantic_confidence)}</small></span><p>${item.semantic_evidence.map(esc).join(' • ') || '—'}</p></button>`;
  }

  function selectSemantic(root, arrangement, index) {
    root.querySelectorAll('[data-semantic]').forEach(el => el.classList.toggle('active', Number(el.dataset.semantic) === index));
    const item = arrangement[index];
    const detail = root.querySelector('#semantic-detail');
    if (!item || !detail) return;
    const alt = (item.semantic_alternatives || []).slice(0, 2).map(x => `${x.type} ${Math.round(x.score * 100)}%`).join(' • ');
    detail.innerHTML = `<div class="semantic-detail-copy"><span>SEMANTIC LABEL</span><h3>${esc(item.semantic_label)} <b>${pct(item.semantic_confidence)}</b></h3><p>${fmtTime(item.start)} → ${fmtTime(item.end)} • source V2-CD: ${esc(item.fusion_label || item.original_label || '—')} • alt: ${esc(alt || '—')}</p><div class="semantic-chips">${item.semantic_evidence.map(x => `<span>${esc(x)}</span>`).join('')}</div></div><div class="semantic-stems">${['vocals','drums','bass','other'].map(name => stemBar(name, item.stem_activity?.[name]?.score || 0)).join('')}</div>`;
  }

  function contextPanel(semantic) {
    const top = semantic.genre.top.length ? semantic.genre.top.map(item => `<span>${esc(item.label)} <b>${Math.round((item.score || 0) * 100)}%</b></span>`).join('') : '<span>Aucun label neural exploitable.</span>';
    const dimensions = window.LMNSemanticV32?.dimensionRows?.(semantic.genre) || [];
    const dimensionHtml = dimensions.length
      ? `<h4>Lecture V3.2</h4><div class="semantic-context-stats">${dimensions.map(item => `<span>${esc(item.label)} <b>${esc(item.value)}</b></span>`).join('')}<span>Grammaire <b>${esc(friendlyGrammar(semantic.genre.grammar))}</b></span></div>`
      : '';
    return `<div class="semantic-context">${dimensionHtml}<h4>Neural Genre Context</h4><div class="semantic-context-tags">${top}</div><h4>Lyrics</h4><div class="semantic-context-stats"><span>Mode <b>${esc(semantic.lyrics.mode)}</b></span><span>Lignes <b>${semantic.lyrics.line_count}</b></span><span>Répétées <b>${semantic.lyrics.repeated_line_count}</b></span><span>Coverage <b>${semantic.lyrics.timed_coverage}%</b></span></div><p>Les lyrics servent de preuve supplémentaire ; elles ne remplacent jamais les frontières audio V2-C.</p></div>`;
  }

  function friendlyGrammar(value) {
    const labels = {
      'sentimental-song': 'chanson sentimentale',
      'electronic-drop': 'électronique / drops',
      'hip-hop': 'hip-hop',
      'rnb-song': 'R&B / chanson',
      'pop-song': 'pop',
      'rock-song': 'rock',
      general: 'générale',
    };
    return labels[value] || String(value || 'générale');
  }

  function summaryCard(label, value, sub) { return `<div><span>${label}</span><strong>${value}</strong><small>${sub}</small></div>`; }
  function stemBar(name, score) { return `<div><span>${name}</span><i><b style="width:${clamp(Number(score),0,100)}%"></b></i><strong>${Math.round(Number(score))}%</strong></div>`; }
  function countLabels(items) { const out = {}; items.forEach(x => { out[x.semantic_type] = (out[x.semantic_type] || 0) + 1; }); return out; }
  function canonicalType(value) { const t = String(value || '').toLowerCase(); if (t.includes('pre-chorus') || t.includes('pre chorus')) return 'Pre-Chorus'; if (t.includes('chorus')) return 'Chorus'; if (t.includes('verse')) return 'Verse'; if (t.includes('bridge')) return 'Bridge'; if (t.includes('interlude')) return 'Interlude'; if (t.includes('drop')) return 'Drop'; if (t.includes('intro')) return 'Intro'; if (t.includes('outro')) return 'Outro'; if (t.includes('instrument')) return 'Instrumental'; return 'Instrumental'; }
  function stem(section, name) { return clamp(Number(section.stem_activity?.[name]?.score || 0) / 100, 0, 1); }
  function profileDistance(a, b) { return Math.sqrt(['vocals','drums','bass','other'].reduce((sum, name) => sum + Math.pow(stem(a,name)-stem(b,name),2),0) / 4); }
  function normalizeScore(v) { return clamp(Number(v || 0) / 1.35, 0, 1); }
  function parseSeconds(value) { return Number(String(value).replace(':','.')); }
  function looksLikeTimestampOnly(line) { return /^\[?\d{1,2}:\d{2}(?:[.:]\d{1,3})?\]?$/.test(line.trim()); }
  function stripTimestamp(line) { return String(line).replace(/^\[?(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.:]\d{1,3})?\]?\s*/, ''); }
  function normalizeLyric(line) { return stripTimestamp(String(line || '')).toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9' ]+/g,' ').replace(/\s+/g,' ').trim(); }
  function setBusy(busy, ownButton) { if (ownButton) { ownButton.disabled = busy; ownButton.classList.toggle('is-loading', busy); ownButton.innerHTML = busy ? '<i data-lucide="loader-circle"></i> Semantic scan…' : '<i data-lucide="brain"></i> Semantic Arrangement V3.2'; window.lucide?.createIcons?.(); } }
  function setV2Status(tag, text, error = false) { const tagEl = document.getElementById('v2-status-tag'); const textEl = document.getElementById('v2-status-text'); if (tagEl) { tagEl.textContent = tag; tagEl.classList.toggle('is-error', error); } if (textEl) textEl.textContent = text; }
  function setProgress(value) { const fill = document.getElementById('v2-progress-fill'); if (fill) fill.style.width = `${clamp(value,0,100)}%`; }
  async function responseError(response) { try { const p = await response.json(); return p.detail || p.error || `HTTP ${response.status}`; } catch (_) { return `HTTP ${response.status}`; } }
  function fmtTime(value) { const sec = Math.max(0, Number(value || 0)); const m = Math.floor(sec / 60); const s = Math.floor(sec % 60); return `${m}:${String(s).padStart(2,'0')}`; }
  function pct(value) { return `${Math.round(Number(value || 0) * 100)}%`; }
  function slug(value) { return String(value || '').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,''); }
  function clamp(v,min,max) { return Math.max(min, Math.min(max, Number(v) || 0)); }
  function round(v,n=3) { const p = 10 ** n; return Math.round(Number(v) * p) / p; }
  function esc(value) { return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])); }

  window.LMNSemanticGenreContext = Object.freeze({
    inferGenre,
    structuredGenreContext,
    collectNeuralLabels,
    broadFamilyFromLabel,
    arrangementFamily,
    scoreSection,
    transition,
    labels: [...LABELS],
  });
})();
