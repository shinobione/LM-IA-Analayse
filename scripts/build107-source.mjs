import assert from 'node:assert/strict';
export const sourceCommit = '7dfe8d341ef1a0573ddda4eb66801d01986780dd';
export const sourceCommitPath = 'js/catalog-similarity.js';
// Reconstruct the extraction from committed pre-Build107 source, not a second solver.
export function extractKernel(source) {
  source = source.replaceAll('\r\n', '\n');
  const functions = ['normalize', 'dot', 'powerComponent'].map(name => {
    const start = source.indexOf(`  function ${name}(`);
    assert.ok(start >= 0, `Missing pinned function ${name}`);
    let end = source.indexOf('{', start) + 1, depth = 1;
    while (depth && end < source.length) { const c = source[end++]; if (c === '{') depth++; if (c === '}') depth--; }
    assert.equal(depth, 0);
    return source.slice(start, end).replace(/^  /gm, '').replace(/^function /, 'export function ');
  });
  return '// SonicTrace-owned catalog projection numerical kernel. Edit only in LM-IA-Analayse.\n' + functions.join('\n\n') + '\n';
}
