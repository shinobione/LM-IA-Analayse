import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../js/semantic-v32.js', import.meta.url), 'utf8');
const context = { window:{}, console };
vm.createContext(context);
vm.runInContext(source, context, { filename:'semantic-v32.js' });
const helper = context.window.LMNSemanticV32;

assert.equal(helper?.version, '3.4', 'V3.4 helper must be active');

const LABELS = ['Intro','Verse','Pre-Chorus','Chorus','Bridge','Interlude','Drop','Instrumental','Outro'];
const base = () => Object.fromEntries(LABELS.map(label => [label, 0.30]));
const genre = (primaryStyle, broadFamily, grammar = null) => {
  const value = {
    primaryStyle,
    primary:primaryStyle,
    display:primaryStyle,
    broadFamily,
    tradition:'',
    form:'',
    region:'',
    unknown:false,
  };
  value.grammar = grammar || helper.arrangementGrammar(value);
  return value;
};
const section = (overrides = {}) => ({
  start:30,
  end:54,
  duration:24,
  energy:65,
  fusion_repeat_strength:0.20,
  fusion_hook_score:20,
  stem_activity:{
    vocals:{score:50}, drums:{score:60}, bass:{score:55}, other:{score:50},
  },
  lyrics:{density:0.25, hook_score:0.20, line_count:4, repeated_ratio:0.10},
  ...overrides,
});

// Specific style must beat a broad hybrid family. Phonk/Trap remains hip-hop
// even when Electronic is present as a secondary/broad influence.
assert.equal(helper.arrangementGrammar(genre('Phonk', 'Electronic / Hip-Hop')), 'hip-hop');
assert.equal(helper.arrangementGrammar(genre('Trap', 'Electronic / Hip-Hop')), 'hip-hop');
assert.equal(helper.arrangementGrammar(genre('Dubstep', 'Electronic')), 'electronic-drop');
assert.equal(helper.arrangementGrammar(genre('Alternative R&B', 'R&B / Soul / Funk')), 'rnb-song');
assert.equal(helper.arrangementGrammar(genre('Synth-pop', 'Pop')), 'pop-song');

const boomBap = genre('Boom Bap', 'Hip-Hop / Rap');
const rapVerse = section({
  energy:72,
  fusion_repeat_strength:0.15,
  fusion_hook_score:20,
  stem_activity:{ vocals:{score:90}, drums:{score:80}, bass:{score:70}, other:{score:50} },
  lyrics:{ density:0.70, hook_score:0.15, line_count:10, repeated_ratio:0.05 },
});
const rapVerseScores = helper.applySectionGrammar(base(), {
  section:rapVerse, sections:[rapVerse, section()], index:0, position:0.25, repeat:0.15, genre:boomBap,
});
helper.applyContextGrammar(rapVerseScores, rapVerse, null, section(), boomBap);
assert.ok(rapVerseScores.Verse > rapVerseScores.Chorus, `dense low-hook rap should prefer Verse (${rapVerseScores.Verse} vs ${rapVerseScores.Chorus})`);
assert.ok(rapVerseScores.Verse > rapVerseScores.Drop, `dense rap vocals must not become Drop (${rapVerseScores.Verse} vs ${rapVerseScores.Drop})`);

const trap = genre('Trap', 'Hip-Hop / Rap');
const trapImpact = section({
  energy:94,
  fusion_repeat_strength:0.25,
  fusion_hook_score:35,
  stem_activity:{ vocals:{score:8}, drums:{score:96}, bass:{score:92}, other:{score:65} },
  lyrics:{ density:0.05, hook_score:0.10, line_count:0, repeated_ratio:0.05 },
});
const trapScores = helper.applySectionGrammar(base(), {
  section:trapImpact, sections:[section({energy:50}), trapImpact, section()], index:1, position:0.48, repeat:0.25, genre:trap,
});
helper.applyContextGrammar(trapScores, trapImpact, section({energy:50}), section({energy:72}), trap);
assert.ok(trapScores.Drop > trapScores.Verse, `real Trap impact section should retain a Drop path (${trapScores.Drop} vs ${trapScores.Verse})`);

const pop = genre('Synth-pop', 'Pop');
const popHook = section({
  energy:86,
  fusion_repeat_strength:0.85,
  fusion_hook_score:90,
  stem_activity:{ vocals:{score:88}, drums:{score:80}, bass:{score:62}, other:{score:60} },
  lyrics:{ density:0.65, hook_score:0.88, line_count:8, repeated_ratio:0.80 },
});
const popScores = helper.applySectionGrammar(base(), {
  section:popHook, sections:[section(), popHook, section()], index:1, position:0.50, repeat:0.85, genre:pop,
});
helper.applyContextGrammar(popScores, popHook, section({energy:70}), section({energy:74}), pop);
assert.ok(popScores.Chorus > popScores.Verse, `repeated vocal Pop hook should prefer Chorus (${popScores.Chorus} vs ${popScores.Verse})`);
assert.ok(popScores.Chorus > popScores.Drop, `Pop hook must not become Drop (${popScores.Chorus} vs ${popScores.Drop})`);

const rnb = genre('Alternative R&B', 'R&B / Soul / Funk');
const rnbVerse = section({
  energy:58,
  fusion_repeat_strength:0.12,
  fusion_hook_score:18,
  stem_activity:{ vocals:{score:85}, drums:{score:55}, bass:{score:58}, other:{score:62} },
  lyrics:{ density:0.72, hook_score:0.15, line_count:10, repeated_ratio:0.08 },
});
const rnbScores = helper.applySectionGrammar(base(), {
  section:rnbVerse, sections:[rnbVerse, section()], index:0, position:0.28, repeat:0.12, genre:rnb,
});
helper.applyContextGrammar(rnbScores, rnbVerse, null, section({energy:70}), rnb);
assert.ok(rnbScores.Verse > rnbScores.Chorus, `low-hook R&B vocal block should prefer Verse (${rnbScores.Verse} vs ${rnbScores.Chorus})`);
assert.ok(rnbScores.Verse > rnbScores.Drop, 'R&B verse must strongly reject Drop');

const edm = genre('Dubstep', 'Electronic');
const edmVocal = section({
  energy:35,
  fusion_repeat_strength:0.18,
  fusion_hook_score:22,
  stem_activity:{ vocals:{score:80}, drums:{score:25}, bass:{score:20}, other:{score:48} },
  lyrics:{ density:0.55, hook_score:0.25, line_count:8, repeated_ratio:0.10 },
});
const edmVocalScores = helper.applySectionGrammar(base(), {
  section:edmVocal, sections:[edmVocal, section()], index:0, position:0.25, repeat:0.18, genre:edm,
});
helper.applyContextGrammar(edmVocalScores, edmVocal, null, section({energy:55}), edm);
assert.ok(edmVocalScores.Drop < 0.30, `low-impact vocal EDM section should suppress Drop (${edmVocalScores.Drop})`);

const edmDrop = section({
  energy:96,
  fusion_repeat_strength:0.35,
  fusion_hook_score:72,
  stem_activity:{ vocals:{score:5}, drums:{score:98}, bass:{score:96}, other:{score:70} },
  lyrics:{ density:0.02, hook_score:0.05, line_count:0, repeated_ratio:0 },
});
const edmDropScores = helper.applySectionGrammar(base(), {
  section:edmDrop, sections:[section({energy:42}), edmDrop, section()], index:1, position:0.50, repeat:0.35, genre:edm,
});
helper.applyContextGrammar(edmDropScores, edmDrop, section({energy:42}), section({energy:70}), edm);
assert.ok(edmDropScores.Drop > edmVocalScores.Drop + 0.30, `real EDM impact must be materially more Drop-like (${edmDropScores.Drop} vs ${edmVocalScores.Drop})`);

const popPreToChorus = helper.transitionAdjustment('Pre-Chorus', 'Chorus', pop, 4, 10);
const popChorusToPre = helper.transitionAdjustment('Chorus', 'Pre-Chorus', pop, 4, 10);
assert.ok(popPreToChorus > popChorusToPre, 'Pop topology should prefer Pre-Chorus → Chorus over Chorus → Pre-Chorus');

const rapVerseToHook = helper.transitionAdjustment('Verse', 'Chorus', boomBap, 4, 10);
const rapVerseToBridge = helper.transitionAdjustment('Verse', 'Bridge', boomBap, 1, 10);
assert.ok(rapVerseToHook > rapVerseToBridge, 'Hip-Hop topology should prefer Verse → Hook/Chorus over an early Bridge');

const edmBuildToDrop = helper.transitionAdjustment('Instrumental', 'Drop', edm, 4, 10);
const popBuildToDrop = helper.transitionAdjustment('Instrumental', 'Drop', pop, 4, 10);
assert.ok(edmBuildToDrop > popBuildToDrop, 'Drop transitions must remain much more plausible in electronic grammar than Pop');

console.log('Semantic V3.4 cross-genre generalization regression: PASS');