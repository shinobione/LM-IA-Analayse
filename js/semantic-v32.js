(() => {
  'use strict';

  // Historical global name kept for compatibility with the existing semantic client.
  // V3.2 owns role-aware genre dimensions; V3.3 extends the same helper with
  // structure intelligence (terminality + contextual section-role priors).
  const VERSION = '3.3';
  const DIMENSIONS_VERSION = '3.2';

  function contextFromDimensions(dimensions, analysis = {}) {
    if (!dimensions || typeof dimensions !== 'object') return null;
    const style = dimensions.style?.primary && typeof dimensions.style.primary === 'object'
      ? dimensions.style.primary
      : null;
    const tradition = dimensions.tradition?.primary && typeof dimensions.tradition.primary === 'object'
      ? dimensions.tradition.primary
      : null;
    const form = dimensions.form?.primary && typeof dimensions.form.primary === 'object'
      ? dimensions.form.primary
      : null;
    const familyLabel = String(dimensions.family?.label || style?.family || '').trim();
    const styleLabel = String(style?.label || '').trim();
    const traditionLabel = String(tradition?.label || '').trim();
    const formLabel = String(form?.label || '').trim();
    const region = String(dimensions.region?.label || style?.region || tradition?.region || '').trim();
    const unknown = Boolean(dimensions.unknown);

    if (!styleLabel && !familyLabel) return null;

    const context = {
      family: arrangementFamily(familyLabel, styleLabel),
      broadFamily: familyLabel || 'Général',
      display: unknown ? 'Hybride / incertain' : (styleLabel || familyLabel || 'Style non déterminé'),
      primary: styleLabel,
      primaryStyle: styleLabel,
      tradition: traditionLabel,
      form: formLabel,
      region,
      unknown,
      dimensionsVersion: String(dimensions.version || DIMENSIONS_VERSION),
      structureVersion: VERSION,
      source: 'neural-v3.2-dimensions',
    };
    context.grammar = arrangementGrammar(context);
    context.rawPrimary = String(analysis?.ensemble?.primary?.label || analysis?.primary?.label || '').trim();
    return context;
  }

  function arrangementFamily(broadFamily, label) {
    const family = normalize(broadFamily);
    const style = normalize(label);
    if (/hip.?hop|\brap\b/.test(family)) return 'hip-hop';
    if (/r&b|soul|funk/.test(family)) return 'r&b';
    if (/electronic|\bedm\b/.test(family)) return 'edm';
    if (family === 'pop') return 'pop';
    if (/rock|metal/.test(family)) return 'rock';
    if (!broadFamily || family === 'general') {
      if (/hip.?hop|\brap\b|trap|drill|boom bap|phonk/.test(style)) return 'hip-hop';
      if (/r&b|\brnb\b|soul|neo soul/.test(style)) return 'r&b';
      if (/dubstep|\bedm\b|house|techno|trance|drum.?and.?bass|\bdnb\b|future bass|electronic/.test(style)) return 'edm';
      if (/\bpop\b|synthpop|electropop/.test(style)) return 'pop';
      if (/rock|metal|punk/.test(style)) return 'rock';
    }
    return 'general';
  }

  function arrangementGrammar(genre = {}) {
    const text = normalize([
      genre.primaryStyle,
      genre.primary,
      genre.display,
      genre.tradition,
      genre.form,
      genre.broadFamily,
    ].filter(Boolean).join(' '));

    if (/vietnamese bolero|nhac vang|nhac tru tinh|sentimental ballad|asian ballad|\bballad\b|fado|french chanson/.test(text)) {
      return 'sentimental-song';
    }
    if (/dubstep|hardstyle|drum.?and.?bass|\bdnb\b|jungle|house|techno|trance|future bass|\bedm\b|electronic/.test(text)) {
      return 'electronic-drop';
    }
    if (/hip.?hop|\brap\b|trap|drill|phonk|boom bap|g-funk|grime/.test(text)) {
      return 'hip-hop';
    }
    if (/r&b|\brnb\b|neo soul|soul|quiet storm|new jack swing/.test(text)) {
      return 'rnb-song';
    }
    if (/\bpop\b|synth.?pop|electropop|city pop|j-pop|k-pop/.test(text)) {
      return 'pop-song';
    }
    if (/rock|metal|punk|shoegaze|post-rock/.test(text)) {
      return 'rock-song';
    }
    return 'general';
  }

  function applySectionGrammar(base, context = {}) {
    if (!base || typeof base !== 'object') return base;
    const section = context.section || {};
    const genre = context.genre || {};
    const grammar = genre.grammar || arrangementGrammar(genre);
    const lyrics = section.lyrics || {};
    const sections = Array.isArray(context.sections) ? context.sections : [];
    const index = Number.isFinite(Number(context.index)) ? Number(context.index) : 0;
    const isLast = sections.length > 0 && index === sections.length - 1;
    const v = stem(section, 'vocals');
    const d = stem(section, 'drums');
    const b = stem(section, 'bass');
    const o = stem(section, 'other');
    const energy = unitPercent(section.energy);
    const duration = Math.max(0, Number(section.duration || (Number(section.end || 0) - Number(section.start || 0)) || 0));
    const position = clamp(Number(context.position ?? 0), 0, 1);
    const repeat = clamp(Number(context.repeat ?? section.fusion_repeat_strength ?? section.repeat_strength ?? 0), 0, 1);
    const hook = clamp(Number(section.fusion_hook_score || 0) / 100, 0, 1);
    const lyricDensity = clamp(Number(lyrics.density || 0), 0, 1);
    const lyricHook = clamp(Number(lyrics.hook_score || 0), 0, 1);

    // V3.2 style grammar remains the first layer.
    if (grammar === 'sentimental-song') {
      base.Drop *= 0.12;
      base.Interlude += 0.20 * (1 - v)
        + 0.13 * o
        + 0.08 * (1 - lyricDensity)
        + 0.06 * ((duration >= 6 && duration <= 36) ? 1 : 0)
        + 0.05 * ((position >= 0.18 && position <= 0.86) ? 1 : 0);
      base.Bridge += 0.07 * (1 - repeat) + 0.04 * (position > 0.45 ? 1 : 0);
      base.Instrumental += 0.07 * (1 - v) + 0.03 * o;
      base.Verse += 0.035 * v;
    } else if (grammar === 'electronic-drop') {
      base.Drop += 0.10 * d + 0.08 * b + 0.04 * (1 - v);
      base.Interlude += 0.04 * (1 - v) + 0.02 * o;
    } else if (grammar === 'hip-hop' || grammar === 'rnb-song') {
      base.Interlude += 0.07 * (1 - v) + 0.04 * o;
    } else if (grammar === 'pop-song' || grammar === 'rock-song') {
      base.Interlude += 0.06 * (1 - v) + 0.04 * o;
      base.Drop *= 0.72;
    }

    // V3.3 role intelligence. These are soft priors: section audio still wins.
    // Verse: vocal + lyrical density + low hook/repetition is stronger evidence
    // than simply being a long section.
    if (v >= 0.42 && lyricDensity >= 0.10 && lyricHook < 0.58) {
      base.Verse += 0.07 * v + 0.06 * lyricDensity + 0.04 * (1 - repeat);
    }
    if (v < 0.20 && lyricDensity < 0.06) base.Verse *= 0.66;

    // Pre-Chorus is a connective role: short-ish, vocal, non-terminal and most
    // plausible before a larger/repeating section. Final or very long blocks
    // should almost never become Pre-Chorus on emission evidence alone.
    if (duration < 5 || duration > 30) base['Pre-Chorus'] *= 0.62;
    if (position > 0.84 || isLast) base['Pre-Chorus'] *= 0.34;
    if (repeat > 0.68) base['Pre-Chorus'] *= 0.72;

    // Bridge: prefer a unique late-middle contrast; penalize early/repeating
    // sections so "different" does not automatically mean Bridge.
    if (position < 0.34) base.Bridge *= 0.56;
    if (repeat > 0.62) base.Bridge *= 0.58;
    if (position >= 0.45 && position <= 0.88 && repeat < 0.34) {
      base.Bridge += 0.055 * (1 - repeat) + 0.025 * Math.abs(o - d);
    }

    // Terminality: a last section that begins late and loses vocals/lyrics,
    // recurrence or energy is a coda/outro, not a mid-song interlude. Preserve
    // final choruses and final EDM drops by reducing the Outro boost when hook
    // evidence remains strong.
    if (isLast) {
      const prev = sections[index - 1] || null;
      const prevEnergy = prev ? unitPercent(prev.energy) : energy;
      const energyDrop = clamp(prevEnergy - energy, 0, 1);
      const late = clamp((position - 0.58) / 0.30, 0, 1);
      const terminalCue = clamp(
        0.30
        + 0.22 * late
        + 0.15 * (1 - v)
        + 0.09 * (1 - lyricDensity)
        + 0.08 * (1 - repeat)
        + 0.12 * energyDrop,
        0,
        1,
      );
      const activeHook = clamp(0.42 * v + 0.22 * lyricDensity + 0.20 * repeat + 0.16 * Math.max(hook, lyricHook), 0, 1);
      const outroReliability = terminalCue * (1 - 0.48 * activeHook);
      base.Outro += 0.20 + 0.40 * outroReliability;

      if (position >= 0.68 && (v < 0.50 || lyricDensity < 0.18)) {
        base.Interlude *= 0.38;
        base.Instrumental *= 0.72;
        base.Bridge *= 0.62;
      }

      // A genuine final refrain should stay a refrain. Do not force an Outro
      // merely because it is last in the boundary list.
      if (activeHook >= 0.62) base.Chorus += 0.10 * activeHook;

      // Electronic tracks may legitimately end on a drop; no emission penalty
      // is applied to Drop here for electronic-drop grammar.
      if (grammar !== 'electronic-drop' && position >= 0.68) base.Drop *= 0.78;
    }

    return base;
  }

  function applyContextGrammar(score, current = {}, prev = null, next = null, genre = {}) {
    if (!score || typeof score !== 'object') return score;
    const grammar = genre.grammar || arrangementGrammar(genre);
    const v = stem(current, 'vocals');
    const o = stem(current, 'other');
    const d = stem(current, 'drums');
    const lyricDensity = clamp(Number(current.lyrics?.density || 0), 0, 1);
    const duration = Math.max(0, Number(current.duration || (Number(current.end || 0) - Number(current.start || 0)) || 0));

    if (grammar === 'sentimental-song') {
      if (v < 0.34 && (o > 0.45 || lyricDensity < 0.15)) {
        score.Interlude += 0.16 + 0.08 * o + 0.04 * (1 - d);
        score.Drop *= 0.42;
      }

      if (prev && next) {
        const prevV = stem(prev, 'vocals');
        const nextV = stem(next, 'vocals');
        if (v + 0.18 < Math.min(prevV, nextV)) {
          score.Interlude += 0.14;
          score.Bridge += 0.05;
        }
      }
    }

    // V3.3 connective-role check. A Pre-Chorus should lead into a section with
    // stronger hook/repetition/energy evidence; without a next section it is
    // structurally implausible.
    if (!next) {
      score['Pre-Chorus'] *= 0.28;
    } else {
      const currentEnergy = unitPercent(current.energy);
      const nextEnergy = unitPercent(next.energy);
      const rise = clamp(nextEnergy - currentEnergy, 0, 1);
      const nextRepeat = sectionRepeat(next);
      const nextHook = clamp(Number(next.fusion_hook_score || 0) / 100, 0, 1);
      const connectorFit = clamp(0.45 * rise + 0.30 * nextRepeat + 0.25 * nextHook, 0, 1);
      if (duration >= 5 && duration <= 28 && v >= 0.30) score['Pre-Chorus'] += 0.10 * connectorFit;
      if (connectorFit < 0.18) score['Pre-Chorus'] *= 0.78;
    }

    return score;
  }

  function transitionAdjustment(a, b, genre = {}, i = 0, n = 1) {
    const grammar = genre.grammar || arrangementGrammar(genre);
    let value = 0;

    if (grammar === 'sentimental-song') {
      if (b === 'Drop') value -= 0.78;
      if (b === 'Interlude') {
        value += 0.08;
        if (a === 'Chorus') value += 0.22;
        if (a === 'Verse') value += 0.08;
        if (a === 'Instrumental') value += 0.12;
        if (i > 1 && i < n - 1) value += 0.08;
      }
      if (a === 'Interlude' && ['Verse', 'Chorus', 'Bridge', 'Outro'].includes(b)) value += 0.20;
    }
    if (grammar === 'electronic-drop') {
      if (b === 'Drop') value += 0.10;
      if (a === 'Drop' && b === 'Drop') value += 0.04;
    }
    if ((grammar === 'pop-song' || grammar === 'rock-song') && b === 'Drop') value -= 0.22;

    // V3.3 sequence-aware terminal roles.
    if (i === n - 1) {
      if (b === 'Outro') {
        value += grammar === 'electronic-drop' ? 0.16 : 0.42;
        if (['Chorus', 'Bridge', 'Interlude', 'Instrumental'].includes(a)) value += 0.12;
      }
      if (b === 'Interlude') value -= grammar === 'electronic-drop' ? 0.06 : 0.28;
      if (b === 'Pre-Chorus') value -= 0.62;
      if (b === 'Bridge') value -= 0.18;
      if (grammar !== 'electronic-drop' && b === 'Drop') value -= 0.26;
    }

    // Bridges are predominantly middle/late-song contrast roles. Keep the door
    // open, but make an early Bridge pay a structural penalty.
    if (b === 'Bridge' && n > 3 && i < Math.floor(n * 0.34)) value -= 0.20;

    return value;
  }

  function dimensionRows(genre = {}) {
    const rows = [];
    if (genre.primaryStyle || genre.primary) rows.push({ label: 'Style', value: genre.primaryStyle || genre.primary });
    if (genre.tradition) rows.push({ label: 'Tradition', value: genre.tradition });
    if (genre.form) rows.push({ label: 'Forme', value: genre.form });
    if (genre.broadFamily) rows.push({ label: 'Famille', value: genre.broadFamily });
    if (genre.region) rows.push({ label: 'Région', value: genre.region });
    return rows;
  }

  function stem(section, name) {
    return clamp(Number(section?.stem_activity?.[name]?.score || 0) / 100, 0, 1);
  }

  function sectionRepeat(section) {
    return clamp(Math.max(Number(section?.fusion_repeat_strength || 0), Number(section?.repeat_strength || 0)), 0, 1);
  }

  function unitPercent(value) {
    const number = Number(value || 0);
    return clamp(number > 1 ? number / 100 : number, 0, 1);
  }

  function normalize(value) {
    return String(value || '')
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[’']/g, "'");
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, Number(value) || 0));
  }

  window.LMNSemanticV32 = Object.freeze({
    version: VERSION,
    dimensionsVersion: DIMENSIONS_VERSION,
    contextFromDimensions,
    arrangementGrammar,
    arrangementFamily,
    applySectionGrammar,
    applyContextGrammar,
    transitionAdjustment,
    dimensionRows,
  });
})();
