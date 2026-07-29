/**
 * LMNotebook Loader Engine
 * Handles step-by-step neural audio loading sequence
 */

const LOADING_STEPS = [
  "Connecting Spotify API...",
  "Connecting SoundCloud API...",
  "Loading Neural Models...",
  "Extracting Audio Embeddings...",
  "Spectral Analysis...",
  "BPM Detection...",
  "Emotion Recognition...",
  "Genre Classification...",
  "Similarity Clustering...",
  "Generating Report..."
];

function initLoader(onComplete) {
  const statusEl = document.getElementById('loader-status');
  const barEl = document.getElementById('loader-progress-bar');
  const percentEl = document.getElementById('loader-percent');
  const loaderScreen = document.getElementById('loader-screen');

  let currentStep = 0;
  const totalSteps = LOADING_STEPS.length;

  const interval = setInterval(() => {
    if (currentStep < totalSteps) {
      statusEl.textContent = LOADING_STEPS[currentStep];
      const progress = Math.round(((currentStep + 1) / totalSteps) * 100);
      barEl.style.width = `${progress}%`;
      percentEl.textContent = `${progress}%`;
      currentStep++;
    } else {
      clearInterval(interval);
      gsap.to(loaderScreen, {
        opacity: 0,
        duration: 0.8,
        onComplete: () => {
          loaderScreen.style.display = 'none';
          document.getElementById('app').classList.remove('hidden');
          if (onComplete) onComplete();
        }
      });
    }
  }, 350);
}
