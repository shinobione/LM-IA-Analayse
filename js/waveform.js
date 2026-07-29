/**
 * SVG Animated Waveform & HTML5 Canvas Realtime Spectrogram Simulation
 */

function initWaveform() {
  const svg = document.getElementById('svg-waveform');
  if (!svg) return;

  const pointsCount = 120;
  let pathD = "M 0 60 ";

  for (let i = 0; i <= pointsCount; i++) {
    const x = (i / pointsCount) * 1000;
    const height = Math.random() * 45 + 5;
    const y = i % 2 === 0 ? 60 - height : 60 + height;
    pathD += `L ${x} ${y} `;
  }

  svg.innerHTML = `
    <path d="${pathD}" fill="none" stroke="#1db954" stroke-width="2" stroke-linecap="round" />
  `;

  // Continuous micro-animation
  gsap.to(svg.querySelector('path'), {
    strokeWidth: 2.5,
    duration: 1.5,
    yoyo: true,
    repeat: -1,
    ease: "sine.inOut"
  });
}

function initSpectrogram() {
  const canvas = document.getElementById('spectrogramCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight;
  }
  resize();

  const cols = 80;
  const rows = 24;

  function render() {
    ctx.fillStyle = "rgba(4, 5, 7, 0.4)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const cellWidth = canvas.width / cols;
    const cellHeight = canvas.height / rows;

    for (let i = 0; i < cols; i++) {
      for (let j = 0; j < rows; j++) {
        const energy = Math.sin(i * 0.1 + Date.now() * 0.003) * Math.cos(j * 0.2) * 0.5 + 0.5;
        if (Math.random() > 0.4) {
          const green = Math.floor(energy * 255);
          const blue = Math.floor((1 - energy) * 200);
          ctx.fillStyle = `rgba(29, ${green}, ${blue}, ${energy * 0.7})`;
          ctx.fillRect(i * cellWidth, j * cellHeight, cellWidth - 1, cellHeight - 1);
        }
      }
    }
    requestAnimationFrame(render);
  }

  render();
}
