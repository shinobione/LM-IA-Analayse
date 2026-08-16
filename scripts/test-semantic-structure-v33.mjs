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
const helper = context.window.LMNSemanticV32;
assert.equal(helper?.version, '3.3', 'structure helper must expose V3.3');
assert.ok(api?.scoreSection, 'semantic test hook must expose scoreSection');
assert.ok(api?.transition, 'semantic test hook must expose transition');

const sentimental = {
  family: 'general',
  broadFamily: 'Vietnamese / Asian',
  display: 'Vietnamese Bolero',
  primary: 'Vietnamese Bolero',
  primaryStyle: 'Vietnamese Bolero',
  tradition: 'Nhạc Vàng',
  form: 'Sentimental Ballad',
  region: 'Vietnam',
  unknown: false,
  grammar: 'sentimental-song',
};

function section(overrides = {}) {
  return {
    start: 0,
    end: 30,
    duration: 30,
    energy: 60,
    rhythmic: 60,
    fusion_repeat_strength: 0.20,
    fusion_repeat_count: 1,
    fusion_hook_score: 20,
    fusion_type: 'Instrumental',
    fusion_confidence: 0.60,
    stem_activity: {
      vocals: { score: 10 },
      drums: { score: 55 },
      bass: { score: 45 },
      other: { score: 80 },
    },
    lyrics: {
      line_count: 0,
      density: 0,
      repeated_ratio: 0,
      hook_score: 0,
    },
    ...overrides,
  };
}

const first = section({
  start: 0,
  end: 54,
  duration: 54,
  energy: 58,
  fusion_type: 'Intro',
  stem_activity: {
    vocals: { score: 8 }, drums: { score: 48 }, bass: { score: 40 }, other: { score: 88 },
  },
});
const middle = section({
  start: 80,
  end: 96,
  duration: 16,
  energy: 78,
  rhythmic: 82,
  fusion_type: 'Instrumental',
  stem_activity: {
    vocals: { score: 7 }, drums: { score: 80 }, bass: { score: 58 }, other: { score: 92 },
  },
});
const terminalCoda = section({
  start: 177,
  end: 233,
  duration: 56,
  energy: 42,
  rhythmic: 55,
  fusion_repeat_strength: 0.10,
  fusion_hook_score: 8,
  fusion_type: 'Instrumental',
  fusion_confidence: 0.58,
  stem_activity: {
    vocals: { score: 6 }, drums: { score: 46 }, bass: { score: 38 }, other: { score: 93 },
  },
});
const boleroSections = [first, middle, terminalCoda];
const lyrics = { mode: 'timed' };

const middleScores = api.scoreSection(middle, 1, boleroSections, sentimental, lyrics);
assert.ok(middleScores.Interlude > middleScores.Outro, `mid-song instrumental should remain Interlude-like (${middleScores.Interlude} vs Outro ${middleScores.Outro})`);
assert.ok(middleScores.Interlude > middleScores.Drop, `Bolero mid-song instrumental must not regress to Drop (${middleScores.Interlude} vs ${middleScores.Drop})`);

const terminalScores = api.scoreSection(terminalCoda, 2, boleroSections, sentimental, lyrics);
assert.ok(terminalScores.Outro > terminalScores.Interlude, `terminal Bolero coda should prefer Outro (${terminalScores.Outro}) over Interlude (${terminalScores.Interlude})`);
assert.ok(terminalScores.Outro > terminalScores.Instrumental, `terminal Bolero coda should prefer semantic Outro (${terminalScores.Outro}) over generic Instrumental (${terminalScores.Instrumental})`);

const finalChorus = section({
  start: 180,
  end: 220,
  duration: 40,
  energy: 90,
  rhythmic: 84,
  fusion_repeat_strength: 0.90,
  fusion_repeat_count: 3,
  fusion_hook_score: 92,
  fusion_type: 'Chorus',
  fusion_confidence: 0.88,
  stem_activity: {
    vocals: { score: 88 }, drums: { score: 82 }, bass: { score: 66 }, other: { score: 58 },
  },
  lyrics: {
    line_count: 8,
    density: 0.72,
    repeated_ratio: 0.82,
    hook_score: 0.90,
  },
});
const chorusSections = [first, middle, finalChorus];
const chorusScores = api.scoreSection(finalChorus, 2, chorusSections, sentimental, lyrics);
assert.ok(chorusScores.Chorus > chorusScores.Outro, `a genuine final chorus must remain Chorus (${chorusScores.Chorus} vs Outro ${chorusScores.Outro})`);

const electronic = {
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
const finalDrop = section({
  start: 170,
  end: 205,
  duration: 35,
  energy: 96,
  rhythmic: 95,
  fusion_repeat_strength: 0.45,
  fusion_hook_score: 88,
  fusion_type: 'Drop',
  fusion_confidence: 0.90,
  stem_activity: {
    vocals: { score: 4 }, drums: { score: 97 }, bass: { score: 94 }, other: { score: 72 },
  },
});
const edmSections = [first, middle, finalDrop];
const dropScores = api.scoreSection(finalDrop, 2, edmSections, electronic, lyrics);
assert.ok(dropScores.Drop > dropScores.Outro, `electronic terminal Drop must remain viable (${dropScores.Drop} vs Outro ${dropScores.Outro})`);

const finalOutroTransition = api.transition('Interlude', 'Outro', sentimental, 9, 10);
const finalInterludeTransition = api.transition('Interlude', 'Interlude', sentimental, 9, 10);
const finalPreTransition = api.transition('Verse', 'Pre-Chorus', sentimental, 9, 10);
assert.ok(finalOutroTransition > finalInterludeTransition, 'terminal sequence should favor Outro over another Interlude');
assert.ok(finalOutroTransition > finalPreTransition, 'terminal sequence should reject a dangling Pre-Chorus');

const edmFinalDropTransition = api.transition('Chorus', 'Drop', electronic, 9, 10);
const sentimentalFinalDropTransition = api.transition('Chorus', 'Drop', sentimental, 9, 10);
assert.ok(edmFinalDropTransition > sentimentalFinalDropTransition, 'V3.3 must preserve stronger terminal Drop paths for electronic grammar');

const earlyBridgeTransition = api.transition('Verse', 'Bridge', sentimental, 1, 10);
const lateBridgeTransition = api.transition('Chorus', 'Bridge', sentimental, 6, 10);
assert.ok(lateBridgeTransition > earlyBridgeTransition, 'Bridge should be structurally more plausible mid/late than very early');

console.log('Semantic V3.3 structure intelligence regression: PASS');
