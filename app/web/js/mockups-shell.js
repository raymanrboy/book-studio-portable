// The listing-mockups window (mockups.html): no sidebar, one page. Keeps the server told the window is open,
// wears Book Studio's theme, and mounts pages/mockups.js.
import { api, TOKEN, toast } from './lib.js';
import { mount } from './pages/mockups.js';

function heartbeat() { api('/api/app/heartbeat', { method: 'POST', body: {} }).catch(() => {}); }
setInterval(heartbeat, 20000);
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') heartbeat(); });
window.addEventListener('pagehide', () => {
  try { navigator.sendBeacon('/api/app/bye', new Blob([JSON.stringify({ t: TOKEN })], { type: 'text/plain' })); } catch {}
});
// A file dropped outside the drop zone must not open in the window.
window.addEventListener('dragover', (e) => e.preventDefault());
window.addEventListener('drop', (e) => e.preventDefault());

function applyTheme(theme) {
  try { localStorage.setItem('bs-theme', theme); } catch {}
  document.documentElement.dataset.theme = theme === 'system'
    ? (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark') : theme;
}

async function boot() {
  heartbeat();
  try {
    const state = await api('/api/mockups/state');
    applyTheme(state.theme || 'dark');
    await mount(document.getElementById('view'), { state });
  } catch (err) {
    toast(err.message, 'error');
  }
}

boot();
