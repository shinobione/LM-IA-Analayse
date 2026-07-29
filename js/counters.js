/**
 * Smooth Animated Number Counters and Gauge Controller
 */

function initCounters() {
  const counters = document.querySelectorAll('.counter');
  
  counters.forEach(counter => {
    const target = +counter.getAttribute('data-target');
    const obj = { val: 0 };

    gsap.to(obj, {
      val: target,
      duration: 2,
      ease: "power2.out",
      onUpdate: () => {
        counter.textContent = Math.round(obj.val);
      }
    });
  });
}

function animateGauge(percentage) {
  const gaugeFill = document.getElementById('gauge-fill');
  const confidenceVal = document.getElementById('confidence-val');
  if (!gaugeFill || !confidenceVal) return;

  let obj = { val: 0 };
  gsap.to(obj, {
    val: percentage,
    duration: 2.2,
    ease: "power3.out",
    onUpdate: () => {
      gaugeFill.setAttribute('stroke-dasharray', `${obj.val.toFixed(1)}, 100`);
      confidenceVal.textContent = `${obj.val.toFixed(1)}%`;
    }
  });
}
