// The generating step redirects to Rick Astley's official music video without collecting user data.
const form = document.querySelector('#generator-form');
const button = document.querySelector('#generate');
const amounts = document.querySelector('#amounts');
const panel = document.querySelector('#progress-panel');
const status = document.querySelector('#status');
const progress = document.querySelector('#progress');
const percentage = document.querySelector('#percentage');
const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
let running = false;

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (running) return;
  running = true;
  button.disabled = true;
  amounts.disabled = true;
  button.firstChild.textContent = 'Preparing your drop ';
  panel.hidden = false;
  const steps = [
    ['Checking drop availability…', 18, 900],
    ['Preparing your reward…', 43, 1000],
    ['Connecting to the generator…', 76, 1100],
    ['Generating Robux…', 100, 450],
  ];
  for (const [message, value, delay] of steps) {
    status.textContent = message;
    progress.value = value;
    percentage.textContent = value + '%';
    await wait(delay);
  }
  window.location.assign('https://www.youtube.com/watch?v=dQw4w9WgXcQ&autoplay=1');
});
