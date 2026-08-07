/**
 * Local DSP console + confidence gauge helper.
 */

const TERMINAL_LOGS = [
  '[SYSTEM] LMNotebook Local Audio DSP v1.0 ready',
  '[INPUT] Accepted formats: MP3 / WAV',
  '[PRIVACY] Audio remains inside the browser session',
  '[DSP] PCM amplitude, RMS, peak, crest factor, clipping',
  '[RHYTHM] Tempo estimation via onset-envelope autocorrelation',
  '[TONAL] Chroma extraction + major/minor key profile matching',
  '[SPECTRAL] FFT centroid, roll-off, flatness, flux and band energy',
  '[STEREO] Mid/Side width, channel balance and L/R correlation',
  '[VISUAL] Real waveform, spectrogram and section-energy timeline',
  '[V2] Neural genre, stems, lyrics, chords and BS.1770 LUFS planned'
];

function startTerminal() {
  const outputEl = document.getElementById('terminal-output');
  if (!outputEl) return;
  outputEl.innerHTML = '';
  let lineIndex = 0;

  function printLine() {
    if (lineIndex >= TERMINAL_LOGS.length) return;
    const line = document.createElement('div');
    line.className = 'terminal-line';
    const prompt = document.createElement('span');
    prompt.className = 'prompt';
    prompt.textContent = '>';
    line.appendChild(prompt);
    line.appendChild(document.createTextNode(` ${TERMINAL_LOGS[lineIndex]}`));
    outputEl.appendChild(line);
    outputEl.scrollTop = outputEl.scrollHeight;
    lineIndex++;
    setTimeout(printLine, 110);
  }

  printLine();
}

function animateGauge(percentage) {
  const gaugeFill = document.getElementById('gauge-fill');
  const confidenceVal = document.getElementById('confidence-val');
  if (!gaugeFill || !confidenceVal) return;
  const target = Math.max(0, Math.min(100, Number(percentage) || 0));

  if (window.gsap) {
    const obj = { val: parseFloat(confidenceVal.textContent) || 0 };
    gsap.to(obj, {
      val: target,
      duration: 0.8,
      ease: 'power2.out',
      onUpdate: () => {
        gaugeFill.setAttribute('stroke-dasharray', `${obj.val.toFixed(1)}, 100`);
        confidenceVal.textContent = `${obj.val.toFixed(1)}%`;
      }
    });
  } else {
    gaugeFill.setAttribute('stroke-dasharray', `${target.toFixed(1)}, 100`);
    confidenceVal.textContent = `${target.toFixed(1)}%`;
  }
}
