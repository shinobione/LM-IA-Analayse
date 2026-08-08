/**
 * Local DSP console + confidence gauge helper.
 */

const TERMINAL_LOGS = [
  '[SYSTEM] LMNotebook local analysis stack ready',
  '[INPUT] MP3 / WAV accepted • TXT/LRC lyrics optional',
  '[PRIVACY] Browser DSP stays local; temporary V2 files are deleted after analysis',
  '[DSP] Level, dynamics, clipping, stereo, FFT and spectral balance active',
  '[RHYTHM] Tempo and onset analysis active',
  '[TONAL] Chroma, key and harmonic tracking active',
  '[V2-A] BS.1770 / EBU R128 loudness, LRA and true peak active',
  '[V2-B] CUDA Neural genre/style, mood, instrumentation and 512D embeddings active',
  '[V2-C] Song Anatomy structure, repetitions, hooks, climax and chord timeline active',
  '[V2-D] Demucs stems routed to the LAN GPU worker with local fallback',
  '[V2-CD] Structure + temporal stem activity fusion active',
  '[V2-CD.1] Semantic arrangement + timestamped lyrics + declared metadata active'
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
