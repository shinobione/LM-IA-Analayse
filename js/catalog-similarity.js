(() => {
  'use strict';

  const NS = window.SonicTraceCatalog = window.SonicTraceCatalog || {};

  const WEIGHTS = {
    embedding: 0.62,
    traits: 0.12,
    labels: 0.08,
    bpm: 0.07,
    key: 0.04,
    structure: 0.05,
    mastering: 0.02,
  };

  function compareTracks(a, b) {
    if (!a || !b) return emptyComparison();
    const components = {
      embedding: embeddingSimilarity(a, b),
      traits: traitSimilarity(a, b),
      labels: labelSimilarity(a, b),
      bpm: bpmSimilarity(a, b),
      key: keySimilarity(a, b),
      structure: structureSimilarity(a, b),
      mastering: masteringSimilarity(a, b),
    };

    let weighted = 0;
    let totalWeight = 0;
    for (const [name, value] of Object.entries(components)) {
      if (!Number.isFinite(value)) continue;
      const weight = WEIGHTS[name] || 0;
      weighted += value * weight;
      totalWeight += weight;
    }

    const score = totalWeight ? clamp(weighted / totalWeight, 0, 1) : 0;
    return {
      score,
      percent: Math.round(score * 100),
      components,
      reasons: explainSimilarity(a, b, components, score),
    };
  }

  function nearest(track, tracks, limit = 6) {
    return (tracks || [])
      .filter(candidate => candidate && candidate.id !== track?.id)
      .map(candidate => ({ track: candidate, ...compareTracks(track, candidate) }))
      .sort((x, y) => y.score - x.score)
      .slice(0, Math.max(0, limit));
  }

  function analyzeCatalog(tracks) {
    const valid = (tracks || []).filter(Boolean);
    const pairwise = pairwiseMatrix(valid);
    const projection = projectTracks(valid);
    const clusters = clusterProjection(valid, projection);
    const insights = catalogInsights(valid, pairwise, clusters);
    return { tracks: valid, pairwise, projection, clusters, insights };
  }

  function pairwiseMatrix(tracks) {
    const matrix = Array.from({ length: tracks.length }, () => Array(tracks.length).fill(0));
    for (let i = 0; i < tracks.length; i++) {
      matrix[i][i] = 1;
      for (let j = i + 1; j < tracks.length; j++) {
        const score = compareTracks(tracks[i], tracks[j]).score;
        matrix[i][j] = score;
        matrix[j][i] = score;
      }
    }
    return matrix;
  }

  function projectTracks(tracks) {
    if (!tracks.length) return [];
    if (tracks.length === 1) return [{ id: tracks[0].id, x: 0, y: 0 }];

    const embeddings = tracks.map(track => normalizedVector(track?.neural?.embedding?.vector));
    const dimension = Math.max(0, ...embeddings.map(v => v.length));
    if (!dimension) return fallbackProjection(tracks);

    const usable = embeddings.map(vector => {
      const out = Array(dimension).fill(0);
      for (let i = 0; i < Math.min(dimension, vector.length); i++) out[i] = vector[i];
      return out;
    });
    const mean = Array(dimension).fill(0);
    usable.forEach(vector => vector.forEach((value, index) => { mean[index] += value / usable.length; }));
    const centered = usable.map(vector => vector.map((value, index) => value - mean[index]));

    const pc1 = powerComponent(centered, null);
    const pc2 = powerComponent(centered, pc1);
    if (!pc1.some(v => Math.abs(v) > 1e-9)) return fallbackProjection(tracks);

    const raw = centered.map((row, index) => ({
      id: tracks[index].id,
      x: dot(row, pc1),
      y: pc2.some(v => Math.abs(v) > 1e-9) ? dot(row, pc2) : index - (tracks.length - 1) / 2,
    }));
    return normalizeProjection(raw);
  }

  function powerComponent(rows, orthogonalTo) {
    if (!rows.length || !rows[0]?.length) return [];
    const dimension = rows[0].length;
    let v = Array.from({ length: dimension }, (_, i) => ((i * 37 + 11) % 101) / 101 - 0.5);
    v = normalize(v);

    for (let iter = 0; iter < 42; iter++) {
      const next = Array(dimension).fill(0);
      for (const row of rows) {
        const scale = dot(row, v);
        for (let i = 0; i < dimension; i++) next[i] += row[i] * scale;
      }
      if (orthogonalTo?.length) {
        const projection = dot(next, orthogonalTo);
        for (let i = 0; i < dimension; i++) next[i] -= projection * orthogonalTo[i];
      }
      const normalized = normalize(next);
      if (!normalized.some(n => Math.abs(n) > 1e-12)) break;
      v = normalized;
    }
    return v;
  }

  function clusterProjection(tracks, projection) {
    const n = tracks.length;
    if (!n) return { count: 0, assignments: {}, groups: [] };
    const k = n < 4 ? 1 : Math.max(2, Math.min(7, Math.round(Math.sqrt(n / 2)) || 2));
    const points = projection.map(p => [p.x, p.y]);
    const centers = deterministicCenters(points, k);
    let assignments = Array(n).fill(0);

    for (let iter = 0; iter < 30; iter++) {
      const next = points.map(point => nearestCenter(point, centers));
      if (iter > 0 && next.every((value, index) => value === assignments[index])) break;
      assignments = next;
      for (let c = 0; c < k; c++) {
        const members = points.filter((_, index) => assignments[index] === c);
        if (!members.length) continue;
        centers[c] = [avg(members.map(p => p[0])), avg(members.map(p => p[1]))];
      }
    }

    const groups = [];
    for (let c = 0; c < k; c++) {
      const indices = assignments.map((cluster, index) => cluster === c ? index : -1).filter(index => index >= 0);
      if (!indices.length) continue;
      const memberTracks = indices.map(index => tracks[index]);
      groups.push({
        id: c,
        label: clusterLabel(memberTracks),
        trackIds: memberTracks.map(track => track.id),
        center: { x: centers[c][0], y: centers[c][1] },
      });
    }

    return {
      count: groups.length,
      assignments: Object.fromEntries(tracks.map((track, index) => [track.id, assignments[index]])),
      groups,
    };
  }

  function catalogInsights(tracks, matrix, clusters) {
    const redundantPairs = [];
    for (let i = 0; i < tracks.length; i++) {
      for (let j = i + 1; j < tracks.length; j++) {
        if (matrix[i][j] >= 0.92) {
          redundantPairs.push({
            a: tracks[i].id,
            b: tracks[j].id,
            percent: Math.round(matrix[i][j] * 100),
          });
        }
      }
    }
    redundantPairs.sort((a, b) => b.percent - a.percent);

    const neighborhood = tracks.map((track, index) => {
      const scores = matrix[index].filter((_, j) => j !== index).sort((a, b) => b - a).slice(0, 3);
      return { id: track.id, score: scores.length ? avg(scores) : 1 };
    });
    const baseline = neighborhood.length > 2 ? avg(neighborhood.map(item => item.score)) : 0;
    const outliers = neighborhood
      .filter(item => tracks.length >= 4 && item.score < Math.min(0.72, baseline - 0.10))
      .sort((a, b) => a.score - b.score)
      .map(item => ({ id: item.id, neighborhoodPercent: Math.round(item.score * 100) }));

    const bridges = [];
    for (let i = 0; i < tracks.length; i++) {
      const own = clusters.assignments[tracks[i].id];
      const foreign = [];
      for (let j = 0; j < tracks.length; j++) {
        if (j === i || matrix[i][j] < 0.73) continue;
        const other = clusters.assignments[tracks[j].id];
        if (other !== own) foreign.push({ cluster: other, score: matrix[i][j] });
      }
      const foreignClusters = new Set(foreign.map(item => item.cluster));
      if (foreignClusters.size >= 1 && foreign.length >= 2) {
        bridges.push({
          id: tracks[i].id,
          clusterCount: foreignClusters.size + 1,
          bridgePercent: Math.round(avg(foreign.map(item => item.score)) * 100),
        });
      }
    }
    bridges.sort((a, b) => b.bridgePercent - a.bridgePercent);

    return {
      redundantPairs: redundantPairs.slice(0, 12),
      outliers: outliers.slice(0, 10),
      bridges: bridges.slice(0, 10),
    };
  }

  function analyzeProject(tracks) {
    const selected = (tracks || []).filter(Boolean);
    if (!selected.length) return null;
    const matrix = pairwiseMatrix(selected);
    const pairScores = [];
    for (let i = 0; i < selected.length; i++) {
      for (let j = i + 1; j < selected.length; j++) pairScores.push(matrix[i][j]);
    }
    const coherence = pairScores.length ? avg(pairScores) : 1;
    const perTrack = selected.map((track, index) => {
      const others = matrix[index].filter((_, j) => j !== index);
      return { track, cohesion: others.length ? avg(others) : 1 };
    });
    const outliers = perTrack
      .filter(item => selected.length >= 4 && item.cohesion < Math.max(0.54, coherence - 0.14))
      .sort((a, b) => a.cohesion - b.cohesion)
      .map(item => ({ id: item.track.id, percent: Math.round(item.cohesion * 100) }));

    const order = sequenceProject(selected, matrix);
    const ordered = order.map((index, position) => ({
      track: selected[index],
      originalIndex: index,
      role: sequenceRole(position, order.length),
      transition: position ? transitionExplanation(selected[order[position - 1]], selected[index]) : ['ouverture du projet'],
    }));

    const bridge = bestProjectBridge(selected, matrix);
    return {
      coherence,
      coherencePercent: Math.round(coherence * 100),
      outliers,
      bridge,
      ordered,
      matrix,
      summary: projectSummary(selected, coherence, outliers, bridge),
    };
  }

  function sequenceProject(tracks, matrix) {
    if (tracks.length <= 1) return tracks.map((_, index) => index);
    const energies = tracks.map(trackEnergy);
    const openings = tracks.map((track, index) => openingScore(track, energies[index]));
    let current = indexOfMax(openings);
    const order = [current];
    const unused = new Set(tracks.map((_, index) => index));
    unused.delete(current);

    while (unused.size) {
      const position = order.length;
      const target = targetEnergy(position, tracks.length);
      let best = null;
      let bestScore = -Infinity;
      for (const candidate of unused) {
        const sim = matrix[current][candidate];
        const energyFit = 1 - Math.abs(energies[candidate] - target);
        const tempoFit = bpmSimilarity(tracks[current], tracks[candidate]);
        const keyFit = keySimilarity(tracks[current], tracks[candidate]);
        const contrast = Math.abs(energies[candidate] - energies[current]);
        const finalBonus = position === tracks.length - 1 ? closingScore(tracks[candidate], energies[candidate]) : 0;
        const score = 0.42 * sim
          + 0.20 * energyFit
          + 0.13 * finiteOr(tempoFit, 0.5)
          + 0.10 * finiteOr(keyFit, 0.5)
          + 0.08 * (position === Math.floor(tracks.length * 0.55) ? contrast : 1 - contrast)
          + 0.07 * finalBonus;
        if (score > bestScore) {
          best = candidate;
          bestScore = score;
        }
      }
      current = best ?? [...unused][0];
      order.push(current);
      unused.delete(current);
    }
    return order;
  }

  function projectSummary(tracks, coherence, outliers, bridge) {
    const sentences = [];
    if (coherence >= 0.82) sentences.push(`${tracks.length} titres forment une identité très cohérente.`);
    else if (coherence >= 0.70) sentences.push(`${tracks.length} titres forment une famille globalement cohérente, avec quelques contrastes utiles.`);
    else sentences.push(`La sélection est volontairement large : plusieurs identités sonores coexistent.`);

    if (outliers.length === 1) sentences.push(`1 titre s’éloigne nettement du centre sonore du projet.`);
    if (outliers.length > 1) sentences.push(`${outliers.length} titres s’éloignent nettement du centre sonore du projet.`);
    if (bridge) sentences.push(`${bridge.title} est le meilleur candidat pour relier deux zones sonores de la sélection.`);
    return sentences;
  }

  function bestProjectBridge(tracks, matrix) {
    if (tracks.length < 3) return null;
    let best = null;
    for (let i = 0; i < tracks.length; i++) {
      const scores = matrix[i].filter((_, j) => j !== i).sort((a, b) => b - a);
      const value = scores.slice(0, Math.min(4, scores.length)).reduce((sum, score) => sum + score, 0) / Math.max(1, Math.min(4, scores.length));
      const spread = scores.length ? scores[0] - scores.at(-1) : 0;
      const bridgeScore = value - spread * 0.12;
      if (!best || bridgeScore > best.score) best = { id: tracks[i].id, title: tracks[i].title, score: bridgeScore };
    }
    return best ? { ...best, percent: Math.round(best.score * 100) } : null;
  }

  function transitionExplanation(a, b) {
    const reasons = [];
    const bpm = bpmSimilarity(a, b);
    const key = keySimilarity(a, b);
    const ea = trackEnergy(a);
    const eb = trackEnergy(b);
    if (Number.isFinite(bpm) && bpm >= 0.85) reasons.push('tempo très proche');
    else if (Number.isFinite(bpm) && bpm >= 0.66) reasons.push('tempo compatible');
    if (Number.isFinite(key) && key >= 0.8) reasons.push('transition harmonique naturelle');
    if (Math.abs(ea - eb) <= 0.12) reasons.push('énergie continue');
    else reasons.push(eb > ea ? 'montée d’énergie' : 'respiration d’énergie');
    const shared = sharedLabels(a?.neural?.moods, b?.neural?.moods, 2);
    if (shared.length) reasons.push(`mood commun : ${shared.join(', ')}`);
    return reasons.slice(0, 3);
  }

  function embeddingSimilarity(a, b) {
    const av = normalizedVector(a?.neural?.embedding?.vector);
    const bv = normalizedVector(b?.neural?.embedding?.vector);
    if (!av.length || av.length !== bv.length) return NaN;
    const cosine = clamp(dot(av, bv), -1, 1);
    return clamp((cosine + 1) / 2, 0, 1);
  }

  function traitSimilarity(a, b) {
    const at = a?.neural?.traits || {};
    const bt = b?.neural?.traits || {};
    const keys = [...new Set([...Object.keys(at), ...Object.keys(bt)])];
    const diffs = [];
    for (const key of keys) {
      const av = traitValue(at[key]);
      const bv = traitValue(bt[key]);
      if (!Number.isFinite(av) || !Number.isFinite(bv)) continue;
      diffs.push(Math.abs(av - bv));
    }
    return diffs.length ? clamp(1 - avg(diffs), 0, 1) : NaN;
  }

  function labelSimilarity(a, b) {
    const genre = weightedLabelOverlap(a?.neural?.genres, b?.neural?.genres);
    const mood = weightedLabelOverlap(a?.neural?.moods, b?.neural?.moods);
    if (!Number.isFinite(genre) && !Number.isFinite(mood)) return NaN;
    if (!Number.isFinite(genre)) return mood;
    if (!Number.isFinite(mood)) return genre;
    return 0.55 * genre + 0.45 * mood;
  }

  function bpmSimilarity(a, b) {
    const av = Number(a?.dsp?.bpm ?? a?.declared?.BPM);
    const bv = Number(b?.dsp?.bpm ?? b?.declared?.BPM);
    if (!Number.isFinite(av) || !Number.isFinite(bv) || av <= 0 || bv <= 0) return NaN;
    const candidates = [bv, bv * 2, bv / 2];
    const deltaRatio = Math.min(...candidates.map(value => Math.abs(av - value) / Math.max(av, value, 1)));
    return clamp(Math.exp(-7.5 * deltaRatio), 0, 1);
  }

  function keySimilarity(a, b) {
    const ak = parseKey(a?.dsp?.key);
    const bk = parseKey(b?.dsp?.key);
    if (!ak || !bk) return NaN;
    if (ak.tonic === bk.tonic && ak.mode === bk.mode) return 1;
    if (ak.tonic === bk.tonic) return 0.84;
    const distance = pitchDistance(ak.pitch, bk.pitch);
    if (distance === 5) return 0.82;
    if (distance === 2 || distance === 3 || distance === 4) return 0.64;
    if (distance === 1) return 0.50;
    return 0.38;
  }

  function structureSimilarity(a, b) {
    const as = a?.structure || {};
    const bs = b?.structure || {};
    const metrics = [];
    const sectionA = Number(as.summary?.section_count ?? as.sections?.length);
    const sectionB = Number(bs.summary?.section_count ?? bs.sections?.length);
    if (Number.isFinite(sectionA) && Number.isFinite(sectionB)) metrics.push(relativeNear(sectionA, sectionB, 5));
    const hookA = Number(as.summary?.hook_candidate_count ?? as.hooks?.length);
    const hookB = Number(bs.summary?.hook_candidate_count ?? bs.hooks?.length);
    if (Number.isFinite(hookA) && Number.isFinite(hookB)) metrics.push(relativeNear(hookA, hookB, 3));
    const labelsA = as.summary?.labels || {};
    const labelsB = bs.summary?.labels || {};
    const labelKeys = [...new Set([...Object.keys(labelsA), ...Object.keys(labelsB)])];
    if (labelKeys.length) {
      const distance = labelKeys.reduce((sum, key) => sum + Math.abs(Number(labelsA[key] || 0) - Number(labelsB[key] || 0)), 0);
      const scale = labelKeys.reduce((sum, key) => sum + Math.max(Number(labelsA[key] || 0), Number(labelsB[key] || 0)), 0) || 1;
      metrics.push(clamp(1 - distance / scale, 0, 1));
    }
    return metrics.length ? avg(metrics) : NaN;
  }

  function masteringSimilarity(a, b) {
    const al = a?.mastering?.loudness || {};
    const bl = b?.mastering?.loudness || {};
    const parts = [];
    const lufsA = Number(al.integrated_lufs);
    const lufsB = Number(bl.integrated_lufs);
    if (Number.isFinite(lufsA) && Number.isFinite(lufsB)) parts.push(clamp(1 - Math.abs(lufsA - lufsB) / 8, 0, 1));
    const lraA = Number(al.loudness_range_lu);
    const lraB = Number(bl.loudness_range_lu);
    if (Number.isFinite(lraA) && Number.isFinite(lraB)) parts.push(clamp(1 - Math.abs(lraA - lraB) / 12, 0, 1));
    return parts.length ? avg(parts) : NaN;
  }

  function explainSimilarity(a, b, components, score) {
    const reasons = [];
    const moods = sharedLabels(a?.neural?.moods, b?.neural?.moods, 2);
    const genres = sharedLabels(a?.neural?.genres, b?.neural?.genres, 2);
    if (moods.length) reasons.push(`ambiance ${moods.join(' / ')} commune`);
    if (genres.length) reasons.push(`${genres.join(' / ')} en commun`);

    const energyA = traitValue(a?.neural?.traits?.energy);
    const energyB = traitValue(b?.neural?.traits?.energy);
    if (Number.isFinite(energyA) && Number.isFinite(energyB)) {
      const delta = energyB - energyA;
      if (Math.abs(delta) <= 0.10) reasons.push('énergie très proche');
      else if (Math.abs(delta) >= 0.24) reasons.push(delta > 0 ? `${b.title || 'ce titre'} est plus énergique` : `${b.title || 'ce titre'} est plus retenu`);
    }

    const vocalA = traitValue(a?.neural?.traits?.vocal);
    const vocalB = traitValue(b?.neural?.traits?.vocal);
    if (Number.isFinite(vocalA) && Number.isFinite(vocalB) && Math.abs(vocalA - vocalB) <= 0.12) reasons.push('présence vocale comparable');

    const spaceA = traitValue(a?.neural?.traits?.space);
    const spaceB = traitValue(b?.neural?.traits?.space);
    if (Number.isFinite(spaceA) && Number.isFinite(spaceB) && Math.abs(spaceA - spaceB) <= 0.13) reasons.push('espace / atmosphère comparable');

    if (Number.isFinite(components.bpm) && components.bpm >= 0.84) reasons.push('tempo voisin');
    if (Number.isFinite(components.key) && components.key >= 0.80) reasons.push('tonalité compatible');
    if (Number.isFinite(components.structure) && components.structure >= 0.80) reasons.push('construction du morceau similaire');
    if (Number.isFinite(components.mastering) && components.mastering >= 0.84) reasons.push('densité de mastering proche');
    if (!reasons.length && score >= 0.75) reasons.push('empreinte Neural globale très proche');
    if (!reasons.length) reasons.push('proximité principalement portée par l’empreinte audio globale');
    return [...new Set(reasons)].slice(0, 4);
  }

  function clusterLabel(tracks) {
    const genre = dominantLabel(tracks.flatMap(track => track?.neural?.genres?.slice(0, 3) || []));
    const mood = dominantLabel(tracks.flatMap(track => track?.neural?.moods?.slice(0, 3) || []));
    if (genre && mood) return `${titleCase(genre)} · ${titleCase(mood)}`;
    return titleCase(genre || mood || 'Famille sonore');
  }

  function dominantLabel(items) {
    const scores = new Map();
    for (const item of items || []) {
      const label = normalizeLabel(item?.label);
      if (!label) continue;
      const weight = rankingScore(item);
      scores.set(label, (scores.get(label) || 0) + Math.max(0.08, weight));
    }
    return [...scores.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || '';
  }

  function weightedLabelOverlap(a, b) {
    const am = labelMap(a);
    const bm = labelMap(b);
    if (!am.size || !bm.size) return NaN;
    const keys = new Set([...am.keys(), ...bm.keys()]);
    let intersection = 0;
    let union = 0;
    for (const key of keys) {
      const av = am.get(key) || 0;
      const bv = bm.get(key) || 0;
      intersection += Math.min(av, bv);
      union += Math.max(av, bv);
    }
    return union ? clamp(intersection / union, 0, 1) : 0;
  }

  function labelMap(items) {
    const map = new Map();
    for (const item of items || []) {
      const label = normalizeLabel(item?.label);
      if (!label) continue;
      map.set(label, Math.max(map.get(label) || 0, rankingScore(item)));
    }
    return map;
  }

  function sharedLabels(a, b, limit = 2) {
    const am = labelMap(a);
    const bm = labelMap(b);
    return [...am.keys()]
      .filter(key => bm.has(key))
      .sort((x, y) => Math.min(bm.get(y), am.get(y)) - Math.min(bm.get(x), am.get(x)))
      .slice(0, limit)
      .map(titleCase);
  }

  function rankingScore(item) {
    const value = Number(item?.score ?? item?.value ?? (Number(item?.percent) / 100));
    return Number.isFinite(value) ? clamp(value > 1 ? value / 100 : value, 0, 1) : 0;
  }

  function trackEnergy(track) {
    const neural = traitValue(track?.neural?.traits?.energy);
    if (Number.isFinite(neural)) return neural;
    const declared = Number(track?.declared?.ENERGY);
    if (Number.isFinite(declared)) return clamp(declared > 1 ? declared / 100 : declared, 0, 1);
    const sections = track?.structure?.sections || [];
    const energies = sections.map(section => Number(section.energy)).filter(Number.isFinite).map(value => value > 1 ? value / 100 : value);
    return energies.length ? clamp(avg(energies), 0, 1) : 0.5;
  }

  function openingScore(track, energy) {
    const sections = track?.structure?.sections || [];
    const first = String(sections[0]?.fusion_type || sections[0]?.type || sections[0]?.label || '').toLowerCase();
    const instrumental = 1 - finiteOr(traitValue(track?.neural?.traits?.vocal), 0.5);
    return 0.36 * (1 - Math.abs(energy - 0.42)) + 0.28 * (/intro/.test(first) ? 1 : 0) + 0.18 * instrumental + 0.18 * (1 - energy);
  }

  function closingScore(track, energy) {
    const sections = track?.structure?.sections || [];
    const last = String(sections.at(-1)?.fusion_type || sections.at(-1)?.type || sections.at(-1)?.label || '').toLowerCase();
    return 0.45 * (/outro/.test(last) ? 1 : 0) + 0.35 * (1 - Math.abs(energy - 0.52)) + 0.20 * finiteOr(traitValue(track?.neural?.traits?.space), 0.5);
  }

  function targetEnergy(position, length) {
    if (length <= 1) return 0.5;
    const t = position / (length - 1);
    if (t < 0.35) return 0.43 + t * 0.95;
    if (t < 0.60) return 0.76 - (t - 0.35) * 0.95;
    if (t < 0.84) return 0.52 + (t - 0.60) * 1.15;
    return 0.80 - (t - 0.84) * 1.7;
  }

  function sequenceRole(position, length) {
    if (length === 1) return 'Pièce centrale';
    if (position === 0) return 'Ouverture';
    if (position === length - 1) return 'Clôture';
    const t = position / (length - 1);
    if (t < 0.28) return 'Montée';
    if (t < 0.43) return 'Premier pic';
    if (t < 0.60) return 'Respiration';
    if (t < 0.78) return 'Relance';
    return 'Dernier pic';
  }

  function parseKey(key) {
    if (!key) return null;
    const label = typeof key === 'string' ? key : (key.label || [key.tonic, key.mode].filter(Boolean).join(' '));
    const normalized = String(label || '').replace(/♯/g, '#').replace(/♭/g, 'b').trim();
    const match = normalized.match(/^([A-Ga-g])([#b]?)(?:\s+|$)(major|minor|maj|min|m)?/i) || normalized.match(/^([A-Ga-g])([#b]?)(m)?$/i);
    if (!match) return null;
    const tonic = `${match[1].toUpperCase()}${match[2] || ''}`;
    const modeText = String(match[3] || '').toLowerCase();
    const mode = modeText === 'm' || modeText.startsWith('min') ? 'minor' : 'major';
    const pitches = { C:0,'C#':1,Db:1,D:2,'D#':3,Eb:3,E:4,F:5,'F#':6,Gb:6,G:7,'G#':8,Ab:8,A:9,'A#':10,Bb:10,B:11 };
    const pitch = pitches[tonic];
    return Number.isFinite(pitch) ? { tonic, mode, pitch } : null;
  }

  function pitchDistance(a, b) {
    const d = Math.abs(a - b) % 12;
    return Math.min(d, 12 - d);
  }

  function traitValue(value) {
    const n = Number(value?.value ?? value?.score ?? (Number(value?.percent) / 100) ?? value);
    if (!Number.isFinite(n)) return NaN;
    return clamp(n > 1 ? n / 100 : n, 0, 1);
  }

  function normalizedVector(vector) {
    if (!Array.isArray(vector)) return [];
    const clean = vector.map(Number).filter(Number.isFinite);
    return normalize(clean);
  }

  function normalize(vector) {
    const norm = Math.sqrt(vector.reduce((sum, value) => sum + value * value, 0));
    if (!norm) return vector.map(() => 0);
    return vector.map(value => value / norm);
  }

  function normalizeProjection(points) {
    const xs = points.map(p => p.x);
    const ys = points.map(p => p.y);
    const xMin = Math.min(...xs); const xMax = Math.max(...xs);
    const yMin = Math.min(...ys); const yMax = Math.max(...ys);
    return points.map(point => ({
      ...point,
      x: xMax === xMin ? 0 : ((point.x - xMin) / (xMax - xMin)) * 2 - 1,
      y: yMax === yMin ? 0 : ((point.y - yMin) / (yMax - yMin)) * 2 - 1,
    }));
  }

  function fallbackProjection(tracks) {
    return tracks.map((track, index) => {
      const angle = (index / Math.max(1, tracks.length)) * Math.PI * 2;
      const radius = 0.45 + ((hashString(track.id || track.title || String(index)) % 50) / 100);
      return { id: track.id, x: Math.cos(angle) * radius, y: Math.sin(angle) * radius };
    });
  }

  function deterministicCenters(points, k) {
    if (!points.length) return [];
    const centers = [points[0].slice()];
    while (centers.length < k) {
      let best = points[0];
      let bestDistance = -1;
      for (const point of points) {
        const d = Math.min(...centers.map(center => squaredDistance(point, center)));
        if (d > bestDistance) { bestDistance = d; best = point; }
      }
      centers.push(best.slice());
    }
    return centers;
  }

  function nearestCenter(point, centers) {
    let best = 0;
    let bestDistance = Infinity;
    centers.forEach((center, index) => {
      const d = squaredDistance(point, center);
      if (d < bestDistance) { bestDistance = d; best = index; }
    });
    return best;
  }

  function squaredDistance(a, b) {
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2;
  }

  function relativeNear(a, b, scale) {
    return clamp(1 - Math.abs(a - b) / Math.max(scale, Math.abs(a), Math.abs(b), 1), 0, 1);
  }

  function normalizeLabel(value) {
    return String(value || '').toLowerCase().replace(/r&b/g, 'rnb').replace(/[^a-z0-9]+/g, ' ').trim();
  }

  function titleCase(value) {
    return String(value || '').replace(/\b\w/g, char => char.toUpperCase());
  }

  function hashString(text) {
    let hash = 2166136261;
    for (const char of String(text || '')) {
      hash ^= char.charCodeAt(0);
      hash = Math.imul(hash, 16777619);
    }
    return hash >>> 0;
  }

  function dot(a, b) {
    let sum = 0;
    for (let i = 0; i < Math.min(a.length, b.length); i++) sum += a[i] * b[i];
    return sum;
  }

  function avg(values) {
    const clean = values.filter(Number.isFinite);
    return clean.length ? clean.reduce((sum, value) => sum + value, 0) / clean.length : NaN;
  }

  function indexOfMax(values) {
    let index = 0;
    for (let i = 1; i < values.length; i++) if (values[i] > values[index]) index = i;
    return index;
  }

  function finiteOr(value, fallback) {
    return Number.isFinite(value) ? value : fallback;
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, Number(value) || 0));
  }

  function emptyComparison() {
    return { score: 0, percent: 0, components: {}, reasons: [] };
  }

  NS.similarity = {
    compareTracks,
    nearest,
    analyzeCatalog,
    pairwiseMatrix,
    projectTracks,
    analyzeProject,
    trackEnergy,
    bpmSimilarity,
    keySimilarity,
  };

  document.dispatchEvent(new CustomEvent('sonictrace:similarity-ready'));
})();
