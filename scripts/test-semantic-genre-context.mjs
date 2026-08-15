import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const helperSource = fs.readFileSync(new URL('../js/semantic-v32.js', import.meta.url), 'utf8');
const clientSource = fs.readFileSync(new URL('../js/semantic-client.js', import.meta.url), 'utf8');
const context = {
  window: {},
  document: { addEventListener() {} },
  console,
};
vm.createContext(context);
vm.runInContext(helperSource, context, { filename: 'semantic-v32.js' });
vm.runInContext(clientSource, context, { filename: 'semantic-client.js' });

const api = context.window.LMNSemanticGenreContext;
const v32 = context.window.LMNSemanticV32;
assert.ok(api?.inferGenre, 'semantic genre test hook must expose inferGenre');
assert.ok(api?.scoreSection, 'V3.2 tests need scoreSection');
assert.ok(api?.transition, 'V3.2 tests need transition');
assert.ok(v32?.arrangementGrammar, 'V3.2 helper must expose arrangementGrammar');
assert.ok(api.labels.includes('Interlude'), 'V3.2 semantic labels must include Interlude');

const screenshotCase = {
  neural: {
    genres: [
      { label: 'Nhạc Vàng', score: 0.69 },
      { label: 'Vietnamese Pop Ballad', score: 0.63 },
      { label: 'Vietnamese Bolero', score: 0.51 },
      { label: 'Neo Soul', score: 0.48 },
    ],
    genre_analysis: {
      version: '3.2',
      primary: {
        label: 'Nhạc Vàng',
        family: 'Vietnamese / Asian',
        score: 0.69,
      },
      ensemble: {
        status: 'ready',
        primary: {
          label: 'Nhạc Vàng',
          family: 'Vietnamese / Asian',
          ensemble_score: 0.69,
        },
      },
      dimensions: {
        version: '3.2',
        unknown: false,
        family: { label: 'Vietnamese / Asian' },
        style: {
          primary: {
            label: 'Vietnamese Bolero',
            family: 'Vietnamese / Asian',
            region: 'Vietnam',
            evidence_score: 0.51,
          },
        },
        tradition: {
          primary: {
            label: 'Nhạc Vàng',
            family: 'Vietnamese / Asian',
            region: 'Vietnam',
            evidence_score: 0.69,
          },
        },
        form: {
          primary: {
            label: 'Sentimental Ballad',
            source_label: 'Vietnamese Pop Ballad',
            evidence_score: 0.63,
          },
        },
        region: { label: 'Vietnam' },
      },
    },
  },
};

const structured = api.inferGenre(screenshotCase);
assert.equal(structured.display, 'Vietnamese Bolero');
assert.equal(structured.primaryStyle, 'Vietnamese Bolero');
assert.equal(structured.tradition, 'Nhạc Vàng');
assert.equal(structured.form, 'Sentimental Ballad');
assert.equal(structured.region, 'Vietnam');
assert.equal(structured.broadFamily, 'Vietnamese / Asian');
assert.equal(structured.family, 'general');
assert.equal(structured.grammar, 'sentimental-song');
assert.notEqual(structured.family, 'r&b');
assert.equal(structured.source, 'neural-v3.2-dimensions');
assert.equal(structured.rawPrimary, 'Nhạc Vàng');

const legacy = api.inferGenre({
  neural: {
    genres: screenshotCase.neural.genres,
  },
});
assert.equal(legacy.display, 'Nhạc Vàng');
assert.equal(legacy.broadFamily, 'Vietnamese / Asian');
assert.equal(legacy.family, 'general');
assert.equal(legacy.grammar, 'sentimental-song');
assert.notEqual(legacy.family, 'r&b');
assert.equal(legacy.source, 'legacy-top-label-only');

const rnb = api.inferGenre({
  neural: {
    genres: [
      { label: 'Contemporary R&B', score: 0.81 },
      { label: 'Pop Ballad', score: 0.52 },
    ],
  },
});
assert.equal(rnb.display, 'Contemporary R&B');
assert.equal(rnb.family, 'r&b');
assert.equal(rnb.grammar, 'rnb-song');

const unknownVietnamese = api.inferGenre({
  neural: {
    genres: screenshotCase.neural.genres,
    genre_analysis: {
      version: '3.2',
      primary: {
        label: 'Unknown / hybrid',
        candidate: {
          label: 'Vietnamese Bolero',
          family: 'Vietnamese / Asian',
        },
      },
      ensemble: {
        status: 'clap-only',
        primary: {
          label: 'Unknown / hybrid',
          candidate: {
            label: 'Vietnamese Bolero',
            family: 'Vietnamese / Asian',
          },
        },
      },
      dimensions: {
        version: '3.2',
        unknown: true,
        family: { label: 'Vietnamese / Asian' },
        style: { primary: { label: 'Vietnamese Bolero', family: 'Vietnamese / Asian', region: 'Vietnam', authority: 'evidence-only' } },
        tradition: { primary: { label: 'Nhạc Vàng', family: 'Vietnamese / Asian', region: 'Vietnam' } },
        form: { primary: { label: 'Sentimental Ballad' } },
        region: { label: 'Vietnam' },
      },
    },
  },
});
assert.equal(unknownVietnamese.display, 'Hybride / incertain');
assert.equal(unknownVietnamese.primaryStyle, 'Vietnamese Bolero');
assert.equal(unknownVietnamese.broadFamily, 'Vietnamese / Asian');
assert.equal(unknownVietnamese.family, 'general');
assert.equal(unknownVietnamese.grammar, 'sentimental-song');
assert.equal(unknownVietnamese.unknown, true);

const midSection = {
  start: 80,
  end: 96,
  duration: 16,
  energy: 82,
  rhythmic: 84,
  fusion_repeat_strength: 0.18,
  fusion_repeat_count: 1,
  fusion_hook_score: 14,
  fusion_type: 'Instrumental',
  fusion_confidence: 0.58,
  stem_activity: {
    vocals: { score: 8 },
    drums: { score: 86 },
    bass: { score: 74 },
    other: { score: 92 },
  },
  lyrics: {
    line_count: 0,
    density: 0,
    repeated_ratio: 0,
    hook_score: 0,
  },
};
const sections = [
  { ...midSection, start: 0, end: 28, duration: 28, stem_activity: { ...midSection.stem_activity, vocals: { score: 70 } } },
  midSection,
  { ...midSection, start: 96, end: 126, duration: 30, stem_activity: { ...midSection.stem_activity, vocals: { score: 76 } } },
];
const lyrics = { mode: 'timed' };

const sentimentalScores = api.scoreSection(midSection, 1, sections, structured, lyrics);
assert.ok(sentimentalScores.Interlude > sentimentalScores.Drop, `sentimental grammar should prefer Interlude (${sentimentalScores.Interlude}) over Drop (${sentimentalScores.Drop})`);
assert.ok(sentimentalScores.Drop < 0.20, `sentimental Drop score should be strongly suppressed, got ${sentimentalScores.Drop}`);

const edmContext = {
  family: 'edm',
  broadFamily: 'Electronic',
  display: 'Dubstep',
  primary: 'Dubstep',
  primaryStyle: 'Dubstep',
  tradition: '',
  form: '',
  region: '',
  unknown: false,
  grammar: 'electronic-drop',
};
const edmScores = api.scoreSection(midSection, 1, sections, edmContext, lyrics);
assert.ok(edmScores.Drop > sentimentalScores.Drop * 3, 'EDM Drop evidence must remain materially stronger than sentimental-song Drop evidence');

const sentimentalDropTransition = api.transition('Chorus', 'Drop', structured, 4, 10);
const sentimentalInterludeTransition = api.transition('Chorus', 'Interlude', structured, 4, 10);
assert.ok(sentimentalInterludeTransition > sentimentalDropTransition, 'sentimental grammar must prefer Chorus → Interlude over Chorus → Drop');

const edmDropTransition = api.transition('Chorus', 'Drop', edmContext, 4, 10);
assert.ok(edmDropTransition > sentimentalDropTransition, 'electronic grammar must preserve a stronger path to Drop');

console.log('Semantic V3.2 genre dimensions + arrangement grammar regression: PASS');
