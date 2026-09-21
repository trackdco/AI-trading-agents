/* Crossroads — the little bit of script the site needs.
   Everything that moves is CSS. This file only: turns the header solid once
   the hero has gone by, opens the menu, loads a video when you ask for it,
   and turns a form into an email. */
(() => {
  const root = document.documentElement;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  root.classList.add(reduce ? 'no-motion' : 'has-motion');

  // header: transparent over the hero, solid after it
  const head = document.querySelector('.site-head');
  const sentinel = document.querySelector('#top-sentinel');
  if (head && sentinel && 'IntersectionObserver' in window) {
    new IntersectionObserver(([e]) => {
      head.classList.toggle('is-solid', !e.isIntersecting);
    }, { rootMargin: `-${head.offsetHeight}px 0px 0px 0px` }).observe(sentinel);
  } else if (head) {
    head.classList.add('is-solid');
  }

  // menu
  const btn = document.querySelector('.menu-btn');
  const menu = document.querySelector('#menu');
  if (btn && menu) {
    const setOpen = (open) => {
      menu.hidden = !open;
      btn.setAttribute('aria-expanded', String(open));
      btn.querySelector('.label').textContent = open ? 'Close' : 'Menu';
      document.body.classList.toggle('menu-open', open);
      if (open) menu.querySelector('a')?.focus({ preventScroll: true });
    };
    btn.addEventListener('click', () => setOpen(menu.hidden));
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !menu.hidden) { setOpen(false); btn.focus(); } });
    matchMedia('(min-width: 1000px)').addEventListener('change', (e) => { if (e.matches) setOpen(false); });
    window.addEventListener('pageshow', () => setOpen(false));
  }

  // videos and embeds: nothing from Vimeo, YouTube or Subsplash loads until you tap
  document.addEventListener('click', (e) => {
    const b = e.target.closest('[data-src]');
    if (!b) return;
    let box = b.closest('.video, .embed .frame');
    if (!box && b.closest('.ep')) { box = b.closest('.ep').querySelector('.ep-frame'); box.hidden = false; }
    if (!box) return;
    const f = document.createElement('iframe');
    f.src = b.dataset.src;
    f.title = b.dataset.title || 'Video';
    f.allow = 'autoplay; fullscreen; picture-in-picture; clipboard-write';
    f.setAttribute('allowfullscreen', '');
    f.setAttribute('loading', 'eager');
    box.replaceChildren(f);
    f.focus();
  });

  // forms: build an email from the fields and hand it to the mail app
  document.querySelectorAll('form[data-mailto]').forEach((form) => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const lines = [];
      for (const [k, v] of fd.entries()) {
        if (!String(v).trim() || k.startsWith('_')) continue;
        const el = form.querySelector(`[name="${k}"]`);
        const label = (el?.closest('fieldset')?.querySelector('legend') || el?.closest('label')?.querySelector('span'))?.textContent?.trim() || k;
        lines.push(`${label}: ${v}`);
      }
      const subject = form.dataset.subject || 'Website form';
      const href = `mailto:${form.dataset.mailto}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(lines.join('\n') + '\n')}`;
      const sent = form.querySelector('.sent');
      if (sent) { sent.hidden = false; sent.focus?.(); }
      window.location.href = href;
    });
  });

  // mark the current section in the top nav
  const here = location.pathname;
  document.querySelectorAll('.site-nav a').forEach((a) => {
    const p = new URL(a.href).pathname;
    if (p !== '/' && here.startsWith(p)) a.classList.add('is-here');
    if (p === here) a.setAttribute('aria-current', 'page');
  });
})();
