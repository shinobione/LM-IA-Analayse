import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../js/semantic-client.js', import.meta.url), 'utf8');
const context = {
  window: {},
  document: { addEventListener() {} },
  console,
};
vm.createContext(context);
vm.runInContext(source, context, { filename: 'semantic-client.js' });

const api = context.window.LMNSemanticGenreContext;
assert.ok(api?.inferGenre, 'semantic genre test hook must expose inferGenre');

const screenshotCase = {
  neural: {
    genres: [
      { label: 'Nhạc Vàng', score: 0.69 },
      { label: 'Vietnamese Pop Ballad', score: 0.63 },
      { label: 'Vietnamese Bolero', score: 0.51 },
      { label: 'Neo Soul', score: 0.48 },
    ],
    genre_analysis: {
      primary: {
        label: 'Vietnamese Bolero',
        family: 'Vietnamese / Asian',
        score: 0.51,
      },
      ensemble: {
        status: 'ready',
        primary: {
          label: 'Vietnamese Bolero',
          family: 'Vietnamese / Asian',
          ensemble_score: 0.74,
        },
      },
    },
  },
};

const structured = api.inferGenre(screenshotCase);
assert.equal(structured.display, 'Vietnamese Bolero');
assert.equal(structured.broadFamily, 'Vietnamese / Asian');
assert.equal(structured.family, 'general');
assert.notEqual(structured.family, 'r&b');
assert.equal(structured.source, 'neural-v3.1-structured');

const legacy = api.inferGenre({
  neural: {
    genres: screenshotCase.neural.genres,
  },
});
assert.equal(legacy.display, 'Nhạc Vàng');
assert.equal(legacy.broadFamily, 'Vietnamese / Asian');
assert.equal(legacy.family, 'general');
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

const unknownVietnamese = api.inferGenre({
  neural: {
    genres: screenshotCase.neural.genres,
    genre_analysis: {
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
    },
  },
});
assert.equal(unknownVietnamese.display, 'Hybride / incertain');
assert.equal(unknownVietnamese.broadFamily, 'Vietnamese / Asian');
assert.equal(unknownVietnamese.family, 'general');

console.log('Semantic V3.1 genre authority regression: PASS');