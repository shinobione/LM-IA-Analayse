(() => {
  'use strict';

  const VERSION = '3.2';

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
      dimensionsVersion: String(dimensions.version || VERSION),
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
    if (!broadFamily || family === 'general' || family === 'general') {
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

    // Song traditions where section identity is normally verse/chorus/bridge/
    // instrumental/interlude rather than an EDM-style drop. This is a grammar
    // prior only: strong audio evidence can still win, but the burden is higher.
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
    const v = stem(section, 'vocals');
    const d = stem(section, 'drums');
    const b = stem(section, 'bass');
    const o = stem(section, 'other');
    const duration = Math.max(0, Number(section.duration || (Number(section.end || 0) - Number(section.start || 0)) || 0));
    const position = Number(context.position ?? 0);
    const repeat = Number(context.repeat ?? section.fusion_repeat_strength ?? section.repeat_strength ?? 0);
    const lyricDensity = clamp(Number(lyrics.density || 0), 0, 1);

    if (grammar === 'sentimental-song') {
      // A Bolero/ballad/chanson can have a strong instrumental lift, but calling
      // it a Drop requires exceptional evidence. Prefer Interlude/Bridge when
      // vocals recede and the arrangement opens up.
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

    return base;
  }

  function applyContextGrammar(score, current = {}, prev = null, next = null, genre = {}) {
    if (!score || typeof score !== 'object') return score;
    const grammar = genre.grammar || arrangementGrammar(genre);
    if (grammar !== 'sentimental-song') return score;

    const v = stem(current, 'vocals');
    const o = stem(current, 'other');
    const d = stem(current, 'drums');
    const lyricDensity = clamp(Number(current.lyrics?.density || 0), 0, 1);
    const positionSignal = Number(current.start || 0);

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

    if (positionSignal > 0 && Number(current.duration || 0) <= 40) {
      score.Interlude += 0.02;
    }
    return score;
  }

  function transitionAdjustment(a, b, genre = {}, i = 0, n = 1) {
    const grammar = genre.grammar || arrangementGrammar(genre);
    if (grammar === 'sentimental-song') {
      if (b === 'Drop') return -0.78;
      if (b === 'Interlude') {
        let value = 0.08;
        if (a === 'Chorus') value += 0.22;
        if (a === 'Verse') value += 0.08;
        if (a === 'Instrumental') value += 0.12;
        if (i > 1 && i < n - 1) value += 0.08;
        return value;
      }
      if (a === 'Interlude' && ['Verse', 'Chorus', 'Bridge', 'Outro'].includes(b)) return 0.20;
    }
    if (grammar === 'electronic-drop') {
      if (b === 'Drop') return 0.10;
      if (a === 'Drop' && b === 'Drop') return 0.04;
    }
    if ((grammar === 'pop-song' || grammar === 'rock-song') && b === 'Drop') return -0.22;
    return 0;
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
    contextFromDimensions,
    arrangementGrammar,
    arrangementFamily,
    applySectionGrammar,
    applyContextGrammar,
    transitionAdjustment,
    dimensionRows,
  });
})();
