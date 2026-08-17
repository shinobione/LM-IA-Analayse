(() => {
  'use strict';

  const REQUIRED_HELPER_VERSION = '3.4';
  const ASSET_REVISION = '3.4.0';
  const DIAGNOSTIC_REVISION = '3.5.3.1';

  async function loadDiagnosticProbe() {
    if (window.LMNNeuralDiagnostics?.version === '3.5.3.1-diagnostic') return true;
    try {
      const response = await fetch(`js/neural-diagnostics-v353.js?v=${DIAGNOSTIC_REVISION}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const source = await response.text();
      (0, eval)(`${source}\n//# sourceURL=neural-diagnostics-v353.js?v=${DIAGNOSTIC_REVISION}`);
      return window.LMNNeuralDiagnostics?.version === '3.5.3.1-diagnostic';
    } catch (error) {
      console.error('[SonicTrace] Neural V3.5.3.1 diagnostic probe failed to load:', error);
      return false;
    }
  }

  async function loadOptionalHelper() {
    if (window.LMNSemanticV32?.version === REQUIRED_HELPER_VERSION) return true;
    try {
      const response = await fetch(`js/semantic-v32.js?v=${ASSET_REVISION}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const source = await response.text();
      (0, eval)(`${source}\n//# sourceURL=semantic-v32.js?v=${ASSET_REVISION}`);
      return window.LMNSemanticV32?.version === REQUIRED_HELPER_VERSION;
    } catch (error) {
      console.error('[SonicTrace] Semantic V3.4 generalization helper failed to load:', error);
      return false;
    }
  }

  async function bootSemantic() {
    const diagnosticReady = await loadDiagnosticProbe();
    const helperReady = await loadOptionalHelper();

    document.documentElement.dataset.sonictraceNeuralDiagnostic = diagnosticReady ? '3.5.3.1' : 'missing';

    if (document.getElementById('semantic-arrangement-btn')) {
      if (!helperReady) {
        console.error('[SonicTrace] Semantic client exists but V3.4 structure helper is unavailable; V3.4 interpretation is not active.');
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
