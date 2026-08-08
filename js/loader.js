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
    link.rel = 'stylesheet';
    link.href = 'css/semantic.css?v=4';
    link.dataset.lmnSemantic = '1';
    document.head.appendChild(link);
  }

  if (!document.querySelector('link[data-lmn-semantic-human]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'css/semantic-human.css?v=4';
    link.dataset.lmnSemanticHuman = '1';
    document.head.appendChild(link);
  }

  if (!document.querySelector('script[data-lmn-semantic-bootstrap]')) {
    const script = document.createElement('script');
    script.src = 'js/semantic-bootstrap.js?v=4';
    script.dataset.lmnSemanticBootstrap = '1';
    document.head.appendChild(script);
  }

  if (!document.querySelector('script[data-lmn-semantic-metadata]')) {
    const script = document.createElement('script');
    script.src = 'js/semantic-metadata.js?v=4';
    script.dataset.lmnSemanticMetadata = '1';
    document.head.appendChild(script);
  }

  if (!document.querySelector('script[data-lmn-semantic-human-ui]')) {
    const script = document.createElement('script');
    script.src = 'js/semantic-human-ui.js?v=4';
    script.dataset.lmnSemanticHumanUi = '1';
    document.head.appendChild(script);
  }
}

function loadUnifiedAnalysisAssets() {
  if (!document.querySelector('link[data-lmn-unified-analysis]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'css/unified-analysis.css?v=1';
    link.dataset.lmnUnifiedAnalysis = '1';
    document.head.appendChild(link);
  }

  if (!document.querySelector('script[data-lmn-unified-analysis]')) {
    const script = document.createElement('script');
    script.src = 'js/unified-analysis.js?v=1';
    script.dataset.lmnUnifiedAnalysis = '1';
    document.head.appendChild(script);
  }
}

function loadHumanInsightAssets() {
  if (!document.querySelector('link[data-lmn-human-insights]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'css/human-insights.css?v=1';
    link.dataset.lmnHumanInsights = '1';
    document.head.appendChild(link);
  }

  if (!document.querySelector('script[data-lmn-human-insights]')) {
    const script = document.createElement('script');
    script.src = 'js/human-insights.js?v=1';
    script.dataset.lmnHumanInsights = '1';
    document.head.appendChild(script);
  }
}

loadFusionAssets();
loadSemanticAssets();
loadUnifiedAnalysisAssets();
loadHumanInsightAssets();

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

    if (window.gsap && loaderScreen) {
      gsap.to(loaderScreen, { opacity: 0, duration: 0.35, onComplete: finish });
    } else {
      finish();
    }
  }, 120);
}
