// Optional modules (studio/modules.py): the heavy parts — the text check and upscaling — that are not in the program until
// the user asks. Where one would be used the page offers it; this file asks, installs with a progress window, and says when done.
import { api, post, html, modal, toast, confirmBox, runJob, setProgress } from './lib.js';

export const listModules = () => api('/api/modules');

/** Offers a module that is missing and installs it when the user agrees. Resolves true when it is installed at the end. */
export async function offerModule(id) {
  let found;
  try { found = (await listModules()).modules.find((m) => m.id === id); }
  catch (err) { toast(err.message, 'error'); return false; }
  if (!found) return false;
  if (found.installed) return true;
  if (!found.canInstall) { toast('Модулі встановлюються лише в портативну версію', 'error'); return false; }
  const ok = await confirmBox({
    title: `Встановити «${found.title}»?`,
    text: `${found.about} Завантаження з інтернету: ${found.size}. ${found.needs}`,
    confirm: 'Встановити',
  });
  return ok ? installModule(found) : false;
}

/** Installs a module (from the internet, or from a ZIP picked in the Windows dialog) with a window that shows the progress. */
export async function installModule(m, fromFile = false) {
  let start;
  try { start = await post(`/api/modules/${m.id}/${fromFile ? 'install-from-file' : 'install'}`, {}); }
  catch (err) { toast(err.message, 'error', 8000); return false; }
  if (start.cancelled) return false;
  const box = modal({
    title: `Встановлюю «${m.title}»`,
    sub: 'Це може тривати. Вікно не закривайте — воно саме закриється, коли все буде готово.',
    dismissible: false,
    body: html`<div class="stack">
      <div class="row"><span id="mod-step" class="grow">Підготовка…</span><span id="mod-pct" class="mono faint">0%</span></div>
      <div class="progress"><i id="mod-bar"></i></div>
      <div class="faint" id="mod-detail" style="font-size: var(--fs)"></div>
    </div>`,
  });
  const q = (sel) => box.el.querySelector(sel);
  try {
    await runJob(Promise.resolve(start), (j) => {
      const bar = q('#mod-bar');
      if (!bar) return;
      const percent = Number(j.percent) || 0;
      setProgress(bar, percent);
      q('#mod-step').textContent = j.step;
      q('#mod-pct').textContent = `${Math.round(percent)}%`;
      q('#mod-detail').textContent = j.detail || '';
    }, 1000);
    box.close();
    toast(`«${m.title}» встановлено`, 'success', 5000);
    return true;
  } catch (err) {
    box.close();
    toast(err.message, 'error', 10000);
    return false;
  }
}
