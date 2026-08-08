/**
 * LMNotebook local DSP bootstrap loader.
 */

const LOADING_STEPS = [
  'Booting local audio engine…',
  'Checking Web Audio API…',
  'Loading FFT / chroma modules…',
  'Preparing waveform renderer…',
  'Preparing DSP charts…',
  'Local analyzer ready.'
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
    link.href = 'css/semantic.css?v=2';
    link.dataset.lmnSemantic = '1';
    document.head.appendChild(link);
  }

  if (!document.querySelector('script[data-lmn-semantic-bootstrap]')) {
    const script = document.createElement('script');
    script.src = 'js/semantic-bootstrap.js?v=2';
    script.dataset.lmnSemanticBootstrap = '1';
    document.head.appendChild(script);
  }
}

loadFusionAssets();
loadSemanticAssets();

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
