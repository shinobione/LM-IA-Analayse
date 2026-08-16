(() => {
  'use strict';

  const REQUIRED_HELPER_VERSION = '3.3';

  async function loadOptionalHelper() {
    if (window.LMNSemanticV32?.version === REQUIRED_HELPER_VERSION) return true;
    try {
      const response = await fetch('js/semantic-v32.js?v=3.3', { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const source = await response.text();
      (0, eval)(`${source}\n//# sourceURL=semantic-v32.js?v=3.3`);
      return window.LMNSemanticV32?.version === REQUIRED_HELPER_VERSION;
    } catch (error) {
      console.error('[SonicTrace] Semantic V3.3 structure helper failed to load:', error);
      return false;
    }
  }

  async function bootSemantic() {
    // V3.2.1 established that helper availability must be independent from
    // client/button creation. V3.3 keeps the same invariant and additionally
    // verifies the helper version so an already-open/stale V3.2 page cannot
    // silently claim the V3.3 structure policy.
    const helperReady = await loadOptionalHelper();

    if (document.getElementById('semantic-arrangement-btn')) {
      if (!helperReady) {
        console.error('[SonicTrace] Semantic client exists but V3.3 structure helper is unavailable; V3.3 interpretation is not active.');
      }
      return;
    }

    try {
      const response = await fetch('js/semantic-client.js?v=3.2.1', { cache: 'no-store' });
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
        (0, eval)(`${source}\n//# sourceURL=semantic-client.js?v=3.2.1`);
      } finally {
        if (domAlreadyReady) document.addEventListener = originalAddEventListener;
      }
    } catch (error) {
      console.error('[LMNotebook] Semantic bootstrap failed:', error);
    }
  }

  bootSemantic();
})();
