(() => {
  'use strict';

  let metadata = {};
  let sanitizing = false;

  function boot() {
    const attach = () => {
      const input = document.getElementById('semantic-lyrics-input');
      if (!input || input.dataset.lmnMetadataAttached) return false;
      input.dataset.lmnMetadataAttached = '1';
      input.addEventListener('change', () => handleLyricsFile(input));
      return true;
    };
    if (attach()) return;
    const observer = new MutationObserver(() => {
      if (attach()) observer.disconnect();
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
  }

  async function handleLyricsFile(input) {
    if (sanitizing) return;
    const file = input.files?.[0];
    if (!file) {
      metadata = {};
      window.LMNSemanticDeclaredMetadata = metadata;
      renderPickerHint();
      return;
    }
    try {
      const raw = await file.text();
      const parsed = splitSemanticText(raw);
      metadata = parsed.metadata;
      window.LMNSemanticDeclaredMetadata = metadata;
      renderPickerHint();
      if (!parsed.hasLyricsSeparator) return;
      const cleanFile = new File([parsed.lyrics.trim()], file.name, {
        type: file.type || 'text/plain',
        lastModified: file.lastModified,
      });
      const dt = new DataTransfer();
      dt.items.add(cleanFile);
      sanitizing = true;
      input.files = dt.files;
      input.dispatchEvent(new Event('change', { bubbles: true }));
      sanitizing = false;
    } catch (error) {
      sanitizing = false;
      console.warn('[LMNotebook] Metadata TXT preprocessor failed:', error);
    }
  }

  function splitSemanticText(text) {
    const raw = String(text || '').replace(/\r/g, '');
    const lines = raw.split('\n');
    const separator = lines.findIndex(line => /^\s*LYRICS\s*:\s*$/i.test(line));
    if (separator < 0) return { metadata: {}, lyrics: raw, hasLyricsSeparator: false };
    return {
      metadata: parseMetadata(lines.slice(0, separator)),
      lyrics: lines.slice(separator + 1).join('\n'),
      hasLyricsSeparator: true,
    };
  }

  function parseMetadata(lines) {
    const out = {};
    let current = null;
    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line) continue;
      const match = line.match(/^([A-Z][A-Z0-9 _-]{1,30})\s*:\s*(.*)$/i);
      if (match) {
        const key = match[1].trim().toUpperCase().replace(/[ -]+/g, '_');
        out[key] = match[2].trim();
        current = key;
      } else if (current) {
        out[current] = `${out[current]} ${line}`.trim();
      }
    }
    return out;
  }

  function renderPickerHint() {
    const wrap = document.getElementById('semantic-lyrics-wrap');
    if (!wrap) return;
    let hint = document.getElementById('semantic-metadata-hint');
    if (!hint) {
      hint = document.createElement('div');
      hint.id = 'semantic-metadata-hint';
      hint.style.cssText = 'font:8px JetBrains Mono,monospace;color:#6f8190;margin:4px 0 0 4px;max-width:520px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis';
      wrap.insertAdjacentElement('afterend', hint);
    }
    const keys = Object.keys(metadata);
    hint.textContent = keys.length ? `Declared metadata: ${keys.slice(0, 7).join(' • ')}${keys.length > 7 ? '…' : ''} — séparées des lyrics` : '';
  }

  function enhanceResults() {
    const root = document.getElementById('v2-semantic-results');
    if (!root || !Object.keys(metadata).length) return;
    const context = root.querySelector('.semantic-context');
    if (!context || context.querySelector('#semantic-declared-context')) return;
    const panel = document.createElement('div');
    panel.id = 'semantic-declared-context';
    const declaredGenre = metadata.GENRE || '';
    const neuralLabels = [...context.querySelectorAll('.semantic-context-tags span')].map(el => el.textContent || '');
    const agreement = declaredGenre ? lexicalAgreement(declaredGenre, neuralLabels) : null;
    const bpm = parseFloat(String(metadata.BPM || '').replace(',', '.'));
    const measuredBpm = findVisibleBpm();
    const bpmDisplay = Number.isFinite(bpm)
      ? `${escapeHtml(metadata.BPM)}${Number.isFinite(measuredBpm) ? ` <b>↔ DSP ${measuredBpm.toFixed(1)} BPM (Δ ${Math.abs(measuredBpm - bpm).toFixed(1)})</b>` : ''}`
      : '';
    const tags = [
      ['TITLE', metadata.TITLE], ['TYPE', metadata.TYPE], ['YEAR', metadata.YEAR], ['RELEASE', metadata.RELEASE],
      ['BPM', bpmDisplay, true], ['GENRE', metadata.GENRE], ['MOOD', metadata.MOOD], ['ENERGY', metadata.ENERGY],
      ['LANGUAGE', metadata.LANGUAGE], ['THEMES', metadata.THEMES], ['ERA', metadata.ERA],
    ].filter(([, value]) => value);
    panel.innerHTML = `
      <h4>Declared Intent (TXT)</h4>
      <div class="semantic-context-tags">${tags.map(([key, value, html]) => `<span>${escapeHtml(key)} <b>${html ? value : escapeHtml(value)}</b></span>`).join('')}</div>
      ${agreement == null ? '' : `<div class="semantic-context-stats" style="margin-top:6px"><span>Genre lexical agreement <b>${agreement}%</b></span><span>Source <b>declared vs Neural</b></span></div>`}
      ${metadata.STYLE_PROMPT ? `<details style="margin-top:8px"><summary style="cursor:pointer;font-size:8px;color:#8193a0">Style Prompt déclaré</summary><p>${escapeHtml(metadata.STYLE_PROMPT)}</p></details>` : ''}
      <p><b>Declared only:</b> ces valeurs servent de contexte et de comparaison ; elles ne remplacent jamais DSP, Neural, V2-C ou V2-D.</p>`;
    context.appendChild(panel);
  }

  function lexicalAgreement(declared, neuralLabels) {
    const declaredTokens = tokenSet(declared);
    if (!declaredTokens.size || !neuralLabels.length) return 0;
    const neuralTokens = tokenSet(neuralLabels.join(' '));
    const intersection = [...declaredTokens].filter(token => neuralTokens.has(token)).length;
    return Math.round((intersection / declaredTokens.size) * 100);
  }

  function tokenSet(text) {
    const stop = new Set(['music','introspective','melancholic','ambient','the','and','with']);
    return new Set(String(text || '').toLowerCase().replace(/r&b/g, 'rnb').replace(/[^a-z0-9]+/g, ' ').split(/\s+/).filter(token => token.length >= 3 && !stop.has(token)));
  }

  function findVisibleBpm() {
    const text = document.body?.innerText || '';
    const match = text.match(/\b(\d{2,3}(?:\.\d+)?)\s*BPM\b/i);
    return match ? Number(match[1]) : NaN;
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[ch]));
  }

  const observer = new MutationObserver(() => enhanceResults());
  observer.observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
