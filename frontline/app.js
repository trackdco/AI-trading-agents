/* Frontline Systems — landing page behaviour.
   Everything here is an enhancement. With JavaScript off the page still reads,
   the FAQ still opens, every log row is still in the DOM with its tier stated in
   words, and the form still submits to the fallback below. */

(() => {
  'use strict';

  /* --------------------------------------------------------------- config --
     Where the enquiry form posts. Leave FORM_KEY empty and the form falls back
     to composing an email, so it is never a dead end. When the Make.com scenario
     is live, put its webhook URL in FORM_ENDPOINT and set FORM_KEY to anything
     non-empty. See README.md. */
  const FORM_ENDPOINT = 'https://api.web3forms.com/submit';
  const FORM_KEY = '';
  const EMAIL = 'patrick@frontlinesystems.com.au';

  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ------------------------------------------------------------ the hero --
     The page's one orchestrated moment, played once on load: the headline rises
     line by line, the handset lights, the notification drops onto the lock
     screen and the phone kicks as if it had just buzzed. The class is added from
     here rather than sitting in the markup so that a reader with JavaScript off,
     or with reduced motion on, simply gets the finished state. */
  const phone = document.getElementById('phone');
  if (!reduced) {
    document.documentElement.classList.add('anim');
    if (phone) {
      // Matches the note-card's 1320ms delay plus its 520ms drop.
      setTimeout(() => phone.classList.add('kick'), 1780);
    }
  }

  /* ---------------------------------------------------------- the device --
     The Imperium screenshot scrolls inside the handset as the handset travels
     up the viewport, so the reader scrolls a real 32-page site without leaving
     this one. Driven off scroll rather than a loop: a loop would move while
     nobody is looking, and this way the gesture is theirs. */
  const device = document.getElementById('device');
  if (device && !reduced) {
    const reel = device.querySelector('.reel');
    const screen = device.querySelector('.screen');
    let visible = false;
    let queued = false;

    function frame() {
      queued = false;
      const box = device.getBoundingClientRect();
      const travel = reel.offsetHeight - screen.clientHeight;
      if (travel <= 0) return;
      // 0 when the device first enters from below, 1 when it has fully left.
      const t = (innerHeight - box.top) / (innerHeight + box.height);
      const y = Math.min(1, Math.max(0, t)) * travel;
      reel.style.transform = `translate3d(0, ${-y.toFixed(1)}px, 0)`;
    }
    function onScroll() {
      if (visible && !queued) { queued = true; requestAnimationFrame(frame); }
    }
    new IntersectionObserver(([e]) => {
      visible = e.isIntersecting;
      if (visible) frame();
    }, { rootMargin: '100px' }).observe(device);
    addEventListener('scroll', onScroll, { passive: true });
    addEventListener('resize', onScroll, { passive: true });
    if (reel.complete) frame(); else reel.addEventListener('load', frame);
  }

  /* ------------------------------------------------------------ the log --
     Tapping a tier relights the log. The point of the control is that the page
     never has to describe what a tier includes in the abstract — you can see
     which messages stop firing when you drop a tier. */
  const log = document.getElementById('log');
  if (log) {
    const RANK = { starter: 0, business: 1, complete: 2 };
    const rows = [...log.querySelectorAll('li')];
    const buttons = [...log.querySelectorAll('.tiers button')];

    function play() {
      if (reduced) return;
      log.removeAttribute('data-playing');
      // Force a reflow so re-adding the attribute restarts the animation.
      void log.offsetWidth;
      log.setAttribute('data-playing', '');
    }

    function show(tier) {
      log.dataset.tier = tier;
      let i = 0;
      for (const row of rows) {
        const live = RANK[row.dataset.min] <= RANK[tier];
        row.dataset.live = String(live);
        // Stagger index counts only live rows, so the reveal never leaves gaps.
        if (live) row.style.setProperty('--i', i++);
      }
      for (const b of buttons) {
        b.setAttribute('aria-pressed', String(b.dataset.tier === tier));
      }
    }

    buttons.forEach(b => b.addEventListener('click', () => {
      show(b.dataset.tier);
      play();
    }));

    const replay = document.getElementById('replay');
    if (replay) {
      replay.addEventListener('click', play);
      if (reduced) replay.hidden = true;
    }

    // One orchestrated moment, the first time the panel is reached, and nothing
    // else on the page moves on scroll.
    if (!reduced) {
      log.setAttribute('data-animate', '');
      const io = new IntersectionObserver(([e]) => {
        if (!e.isIntersecting) return;
        io.disconnect();
        play();
      }, { threshold: 0.15 });
      io.observe(log);
    }
  }

  /* ---------------------------------------------------------- sticky bar --
     Repeats the primary action once the hero's copy has scrolled away, and gets
     out of the way while the form is on screen so it can never sit on top of the
     last field with the keyboard up. */
  const sticky = document.getElementById('sticky');
  const hero = document.querySelector('.hero');
  const start = document.getElementById('start');
  if (sticky && hero && start) {
    const link = sticky.querySelector('a');
    let pastHero = false;
    let atForm = false;

    function sync() {
      const show = pastHero && !atForm;
      sticky.toggleAttribute('data-show', show);
      sticky.setAttribute('aria-hidden', String(!show));
      link.tabIndex = show ? 0 : -1;
    }

    new IntersectionObserver(([e]) => {
      pastHero = !e.isIntersecting;
      sync();
    }, { threshold: 0 }).observe(hero);

    new IntersectionObserver(([e]) => {
      atForm = e.isIntersecting;
      sync();
    }, { threshold: 0 }).observe(start);
  }

  /* ---------------------------------------------------------------- form -- */
  const form = document.getElementById('enq');
  if (!form) return;
  const sent = document.getElementById('sent');
  const submit = form.querySelector('button[type="submit"]');

  // 04xxxxxxxx, +61 4xxxxxxxx, and any spacing people actually type.
  function normaliseMobile(raw) {
    let d = raw.replace(/[\s()-]/g, '');
    if (d.startsWith('+61')) d = '0' + d.slice(3);
    else if (d.startsWith('61') && d.length === 11) d = '0' + d.slice(2);
    return /^04\d{8}$/.test(d) ? d : null;
  }

  const checks = {
    'f-name': v => v.trim().length > 1,
    'f-mobile': v => normaliseMobile(v) !== null,
    'f-trade': v => v.trim().length > 1,
    'f-suburb': v => v.trim().length > 1,
    'f-site': v => v !== '',
    'f-want': v => v.trim().length > 2,
  };

  function mark(id, ok) {
    const el = document.getElementById(id);
    const field = el.closest('.field');
    field.toggleAttribute('data-invalid', !ok);
    el.setAttribute('aria-invalid', String(!ok));
    // Only point at the error message while there is one to read.
    if (ok) el.removeAttribute('aria-describedby');
    else el.setAttribute('aria-describedby', 'e-' + id.slice(2));
    return ok;
  }

  // Clear an error the moment the field becomes valid, rather than on submit.
  for (const id of Object.keys(checks)) {
    const el = document.getElementById(id);
    const revalidate = () => {
      if (el.closest('.field').hasAttribute('data-invalid')) mark(id, checks[id](el.value));
    };
    el.addEventListener('input', revalidate);
    el.addEventListener('change', revalidate);
  }

  form.addEventListener('submit', async ev => {
    ev.preventDefault();

    let firstBad = null;
    for (const [id, test] of Object.entries(checks)) {
      const ok = mark(id, test(document.getElementById(id).value));
      if (!ok && !firstBad) firstBad = id;
    }
    if (firstBad) {
      const el = document.getElementById(firstBad);
      el.focus({ preventScroll: true });
      el.scrollIntoView({ block: 'center', behavior: reduced ? 'auto' : 'smooth' });
      return;
    }

    const v = id => document.getElementById(id).value.trim();
    const body = [
      `Name: ${v('f-name')}`,
      `Mobile: ${normaliseMobile(v('f-mobile'))}`,
      `Trade: ${v('f-trade')}`,
      `Suburb: ${v('f-suburb')}`,
      `Website now: ${v('f-site')}`,
      '',
      v('f-want'),
    ].join('\n');

    // No endpoint configured yet: hand the whole enquiry to their mail app rather
    // than pretending it sent.
    if (!FORM_KEY) {
      location.href = `mailto:${EMAIL}?subject=${encodeURIComponent(
        'Website enquiry — ' + v('f-trade') + ', ' + v('f-suburb'))}&body=${encodeURIComponent(body)}`;
      return;
    }

    submit.disabled = true;
    const was = submit.textContent;
    submit.textContent = 'Sending…';
    try {
      const res = await fetch(FORM_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({
          access_key: FORM_KEY,
          subject: `Website enquiry — ${v('f-trade')}, ${v('f-suburb')}`,
          from_name: v('f-name'),
          name: v('f-name'),
          mobile: normaliseMobile(v('f-mobile')),
          trade: v('f-trade'),
          suburb: v('f-suburb'),
          website: v('f-site'),
          want: v('f-want'),
        }),
      });
      if (!res.ok) throw new Error(String(res.status));
      form.hidden = true;
      sent.hidden = false;
      sent.setAttribute('tabindex', '-1');
      sent.focus({ preventScroll: true });
      sent.scrollIntoView({ block: 'center', behavior: reduced ? 'auto' : 'smooth' });
    } catch {
      submit.disabled = false;
      submit.textContent = was;
      // Never swallow it. If the send failed, say so and give them the other way.
      const note = form.querySelector('.form-note');
      note.innerHTML = `That didn&rsquo;t send &mdash; something&rsquo;s wrong at my end, not yours. ` +
        `Please email <a href="mailto:${EMAIL}">${EMAIL}</a> and I&rsquo;ll sort it.`;
    }
  });
})();
