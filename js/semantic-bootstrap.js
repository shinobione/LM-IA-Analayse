(() => {
  'use strict';

  async function loadOptionalHelper() {
    try {
      const response = await fetch('js/semantic-v32.js?v=3.2', { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const source = await response.text();
      (0, eval)(`${source}\n//# sourceURL=semantic-v32.js?v=3.2`);
    } catch (error) {
      // V3.2 is additive. If the helper cannot load, the existing semantic
      // client still boots with its V3.1-safe behaviour instead of failing.
      console.warn('[SonicTrace] Semantic V3.2 helper unavailable; using base semantic client:', error);
    }
  }

  async function bootSemantic() {
    if (document.getElementById('semantic-arrangement-btn')) return;

    try {
      await loadOptionalHelper();
      const response = await fetch('js/semantic-client.js?v=3.2', { cache: 'no-store' });
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
        (0, eval)(`${source}\n//# sourceURL=semantic-client.js?v=3.2`);
      } finally {
        if (domAlreadyReady) document.addEventListener = originalAddEventListener;
      }
    } catch (error) {
      console.error('[LMNotebook] Semantic bootstrap failed:', error);
    }
  }

  bootSemantic();
})();
