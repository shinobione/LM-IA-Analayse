// SonicTrace-owned catalog projection numerical kernel. Edit only in LM-IA-Analayse.
export function normalize(vector) {
  const norm = Math.sqrt(vector.reduce((sum, value) => sum + value * value, 0));
  if (!norm) return vector.map(() => 0);
  return vector.map(value => value / norm);
}

export function dot(a, b) {
  let sum = 0;
  for (let i = 0; i < Math.min(a.length, b.length); i++) sum += a[i] * b[i];
  return sum;
}

export function powerComponent(rows, orthogonalTo) {
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
