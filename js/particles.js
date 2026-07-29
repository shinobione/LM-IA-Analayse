/**
 * Interactive Neural Particles Background Engine
 */

document.addEventListener('DOMContentLoaded', () => {
  if (window.tsParticles) {
    tsParticles.load('tsparticles', {
      fpsLimit: 60,
      particles: {
        number: {
          value: 65,
          density: { enable: true, value_area: 900 }
        },
        color: { value: ["#1db954", "#00f0ff", "#ffffff"] },
        shape: { type: "circle" },
        opacity: {
          value: 0.3,
          random: true
        },
        size: {
          value: { min: 1, max: 3 }
        },
        links: {
          enable: true,
          distance: 140,
          color: "#1db954",
          opacity: 0.12,
          width: 1
        },
        move: {
          enable: true,
          speed: 0.8,
          direction: "none",
          random: true,
          straight: false,
          outModes: { default: "bounce" }
        }
      },
      interactivity: {
        detectsOn: "window",
        events: {
          onHover: {
            enable: true,
            mode: "grab"
          }
        },
        modes: {
          grab: {
            distance: 180,
            links: { opacity: 0.35 }
          }
        }
      },
      detectRetina: true
    });
  }
});
