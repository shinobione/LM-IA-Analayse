(() => {
  'use strict';

  const REQUIRED_HELPER_VERSION = '3.3';
  const ASSET_REVISION = '3.3.1';

  async function loadOptionalHelper() {
    if (window.LMNSemanticV32?.version === REQUIRED_HELPER_VERSION) return true;
    try {
      const response = await fetch(`js/semantic-v32.js?v=${ASSET_REVISION}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const source = await response.text();
      (0, eval)(`${source}\n//# sourceURL=semantic-v32.js?v=${ASSET_REVISION}`);
      return window.LMNSemanticV32?.version === REQUIRED_HELPER_VERSION;
    } catch (error) {
      console.error('[SonicTrace] Semantic V3.3 structure helper failed to load:', error);
      return false;
    }
  }

  async function bootSemantic() {
    // Helper availability is independent from client/button creation. We verify
    // the V3.3 helper before accepting any existing semantic UI, so a stale tab
    // cannot silently claim a newer structure policy.
    const helperReady = await loadOptionalHelper();

    if (document.getElementById('semantic-arrangement-btn')) {
      if (!helperReady) {
        console.error('[SonicTrace] Semantic client exists but V3.3 structure helper is unavailable; V3.3 interpretation is not active.');
      }
      document.documentElement.dataset.sonictraceSemanticHelper = helperReady ? REQUIRED_HELPER_VERSION : 'missing';
      return;
    }

    try {
      const response = await fetch(`js/semantic-client.js?v=${ASSET_REVISION}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const source = await response.text();

      const originalAddEventListener = document.addEventListener.bind(document);
      const domAlreadyReady = document.readyState !== 'loading';

      if (domAlreadyReady) {
        document.addEventListener = function patchedAddEventListener(type, listener, options) {
          if (type === 'DOMContentLoaded') {
            queueMicrotask(() => listener.call(document, new Event('DOMContentLoaded')));
            return;
          }
          return originalAddEventListener(type, listener, options);
        };
      }

      try {
        (0, eval)(`${source}\n//# sourceURL=semantic-client.js?v=${ASSET_REVISION}`);
      } finally {
        if (domAlreadyReady) document.addEventListener = originalAddEventListener;
      }
      document.documentElement.dataset.sonictraceSemanticHelper = helperReady ? REQUIRED_HELPER_VERSION : 'missing';
      document.documentElement.dataset.sonictraceSemanticClient = ASSET_REVISION;
    } catch (error) {
      console.error('[LMNotebook] Semantic bootstrap failed:', error);
    }
  }

  bootSemantic();
})();