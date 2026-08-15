(() => {
  'use strict';

  async function loadOptionalHelper() {
    if (window.LMNSemanticV32) return true;
    try {
      const response = await fetch('js/semantic-v32.js?v=3.2.1', { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const source = await response.text();
      (0, eval)(`${source}\n//# sourceURL=semantic-v32.js?v=3.2.1`);
      return Boolean(window.LMNSemanticV32);
    } catch (error) {
      console.error('[SonicTrace] Semantic V3.2 helper failed to load:', error);
      return false;
    }
  }

  async function bootSemantic() {
    // V3.2.1: helper availability is independent from client/button creation.
    // The human/unified UI may create the semantic button before this bootstrap
    // runs. Previously that early button made us return before loading V3.2,
    // silently falling back to V3.1 genre authority + generic arrangement.
    const helperReady = await loadOptionalHelper();

    if (document.getElementById('semantic-arrangement-btn')) {
      if (!helperReady) {
        console.error('[SonicTrace] Semantic client exists but V3.2 helper is unavailable; V3.2 interpretation is not active.');
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
