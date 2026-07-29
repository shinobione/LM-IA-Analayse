/**
 * AI Console Terminal Output Simulator
 */

const TERMINAL_LOGS = [
  "[SYSTEM] Initializing LMNotebook DSP Kernel v4.8...",
  "[SPOTIFY] Authenticated token for catalog: SHINOBIWAN",
  "[SOUNDCLOUD] Querying track waveforms and play counts...",
  "[NEURAL] Extracting 128-dimension audio embeddings...",
  "[DSP] Performing FFT (Fast Fourier Transform)...",
  "[SPECTRAL] Centroid: 2840 Hz | Flux: 0.042",
  "[METRICS] Integrated Loudness: -7.2 LUFS",
  "[CLUSTERING] Nearest Neighbors calculated (k=15)",
  "[CONFIDENCE] Neural confidence calculated at 98.7%",
  "[REPORT] Vietnamese Natural Language Generation complete.",
  "[STATUS] System Ready. All monitors active."
];

function startTerminal() {
  const outputEl = document.getElementById('terminal-output');
  let lineIndex = 0;

  function printLine() {
    if (lineIndex < TERMINAL_LOGS.length) {
      const line = document.createElement('div');
      line.className = 'terminal-line';
      line.innerHTML = `<span class="prompt">></span> ${TERMINAL_LOGS[lineIndex]}`;
      outputEl.appendChild(line);
      outputEl.scrollTop = outputEl.scrollHeight;
      lineIndex++;
      setTimeout(printLine, Math.random() * 400 + 200);
    }
  }

  printLine();
}
