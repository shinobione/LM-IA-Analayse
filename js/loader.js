/**
 * LMNotebook local DSP bootstrap loader.
 */

const LOADING_STEPS = [
  'Initialisation du moteur audio local…',
  'Vérification Web Audio API…',
  'Chargement FFT / chroma…',
  'Préparation de la waveform…',
  'Préparation des visualisations…',
  'Interface d’analyse prête.'
];

function loadFusionAssets() {
  if (!document.querySelector('link[data-lmn-fusion]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'css/fusion.css';
    link.dataset.lmnFusion = '1';
    document.head.appendChild(link);
  }
  if (!document.querySelector('script[data-lmn-fusion]')) {
    const script = document.createElement('script');
    script.src = 'js/fusion-client.js';
    script.dataset.lmnFusion = '1';
    document.head.appendChild(script);
  }
}

function loadSemanticAssets() {
  if (!document.querySelector('link[data-lmn-semantic]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet'; link.href = 'css/semantic.css?v=4'; link.dataset.lmnSemantic = '1'; document.head.appendChild(link);
  }
  if (!document.querySelector('link[data-lmn-semantic-human]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet'; link.href = 'css/semantic-human.css?v=4'; link.dataset.lmnSemanticHuman = '1'; document.head.appendChild(link);
  }
  if (!document.querySelector('script[data-lmn-semantic-bootstrap]')) {
    const script = document.createElement('script');
    script.src = 'js/semantic-bootstrap.js?v=4'; script.dataset.lmnSemanticBootstrap = '1'; document.head.appendChild(script);
  }
  if (!document.querySelector('script[data-lmn-semantic-metadata]')) {
    const script = document.createElement('script');
    script.src = 'js/semantic-metadata.js?v=4'; script.dataset.lmnSemanticMetadata = '1'; document.head.appendChild(script);
  }
  if (!document.querySelector('script[data-lmn-semantic-human-ui]')) {
    const script = document.createElement('script');
    script.src = 'js/semantic-human-ui.js?v=4'; script.dataset.lmnSemanticHumanUi = '1'; document.head.appendChild(script);
  }
}

function loadUnifiedAnalysisAssets() {
  if (!document.querySelector('link[data-lmn-unified-analysis]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet'; link.href = 'css/unified-analysis.css?v=2'; link.dataset.lmnUnifiedAnalysis = '1'; document.head.appendChild(link);
  }
  if (!document.querySelector('script[data-lmn-unified-analysis]')) {
    const script = document.createElement('script');
    script.src = 'js/unified-analysis.js?v=2'; script.dataset.lmnUnifiedAnalysis = '1'; document.head.appendChild(script);
  }
}

function loadHumanInsightAssets() {
  if (!document.querySelector('link[data-lmn-human-insights]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet'; link.href = 'css/human-insights.css?v=1'; link.dataset.lmnHumanInsights = '1'; document.head.appendChild(link);
  }
  if (!document.querySelector('script[data-lmn-human-insights]')) {
    const script = document.createElement('script');
    script.src = 'js/human-insights.js?v=1'; script.dataset.lmnHumanInsights = '1'; document.head.appendChild(script);
  }
}

function loadReadabilityOverhaulAssets() {
  if (!document.querySelector('link[data-sonictrace-readability]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet'; link.href = 'css/readability-overhaul.css?v=5'; link.dataset.sonictraceReadability = '1'; document.head.appendChild(link);
  }
  if (!document.querySelector('script[data-sonictrace-readability]')) {
    const script = document.createElement('script');
    script.src = 'js/readability-overhaul.js?v=7'; script.dataset.sonictraceReadability = '1'; document.head.appendChild(script);
  }
}

function loadCatalogIntelligenceAssets() {
  if (!document.querySelector('link[data-sonictrace-catalog]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet'; link.href = 'css/catalog.css?v=2'; link.dataset.sonictraceCatalog = '1'; document.head.appendChild(link);
  }
  if (!document.querySelector('link[data-sonictrace-style-families]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet'; link.href = 'css/catalog-style-families.css?v=2'; link.dataset.sonictraceStyleFamilies = '1'; document.head.appendChild(link);
  }
  if (!document.querySelector('link[data-sonictrace-family-language]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet'; link.href = 'css/catalog-family-language-build05.css?v=1'; link.dataset.sonictraceFamilyLanguage = '1'; document.head.appendChild(link);
  }
  const assets = [
    ['js/catalog-memory.js?v=1', 'memory'],
    ['js/catalog-similarity.js?v=2', 'similarity'],
    ['js/catalog-ui.js?v=2', 'ui'],
    ['js/catalog-style-families.js?v=2', 'styleFamilies'],
    ['js/catalog-style-families-build04.js?v=1', 'styleFamiliesBuild04'],
    ['js/catalog-family-language-build05.js?v=1', 'familyLanguageBuild05'],
  ];
  const loadNext = index => {
    if (index >= assets.length) return;
    const [src, name] = assets[index];
    const attrName = `data-sonictrace-catalog-${name.replace(/[A-Z]/g, letter => `-${letter.toLowerCase()}`)}`;
    const existing = document.querySelector(`script[${attrName}]`);
    if (existing) {
      if (existing.dataset.loaded === '1') loadNext(index + 1);
      else existing.addEventListener('load', () => loadNext(index + 1), { once:true });
      return;
    }
    const script = document.createElement('script');
    script.src = src; script.async = false;
    script.setAttribute(attrName, '1');
    script.addEventListener('load', () => { script.dataset.loaded = '1'; loadNext(index + 1); }, { once:true });
    script.addEventListener('error', () => console.error(`[SonicTrace] Catalog asset failed to load: ${src}`), { once:true });
    document.head.appendChild(script);
  };
  loadNext(0);
}

loadFusionAssets();
loadSemanticAssets();
loadUnifiedAnalysisAssets();
loadHumanInsightAssets();
loadReadabilityOverhaulAssets();
loadCatalogIntelligenceAssets();

function initLoader(onComplete) {
  const statusEl = document.getElementById('loader-status');
  const barEl = document.getElementById('loader-progress-bar');
  const percentEl = document.getElementById('loader-percent');
  const loaderScreen = document.getElementById('loader-screen');
  let currentStep = 0;
  const totalSteps = LOADING_STEPS.length;
  const interval = setInterval(() => {
    if (currentStep < totalSteps) {
      if (statusEl) statusEl.textContent = LOADING_STEPS[currentStep];
      const progress = Math.round(((currentStep + 1) / totalSteps) * 100);
      if (barEl) barEl.style.width = `${progress}%`;
      if (percentEl) percentEl.textContent = `${progress}%`;
      currentStep++;
      return;
    }
    clearInterval(interval);
    const finish = () => {
      if (loaderScreen) loaderScreen.style.display = 'none';
      document.getElementById('app')?.classList.remove('hidden');
      if (onComplete) onComplete();
    };
    if (window.gsap && loaderScreen) gsap.to(loaderScreen, { opacity:0, duration:0.35, onComplete:finish });
    else finish();
  }, 120);
}
