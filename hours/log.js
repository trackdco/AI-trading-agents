/* Imperium Detailing — logging a whole day.

   The clock page covers the normal case and the "forgot to press start" case.
   This covers the last one: nobody pressed anything, the van is packed, and all
   that honestly exists is a day and a number of hours. So that is all this page
   asks for. It writes to the same Google Sheet as the clock page, through the
   same shape (config.js dayShift), and the entry counts towards the week like
   any other shift. */

(() => {
  'use strict';

  const CFG = window.IMP || {};
  const ENDPOINT = CFG.ENDPOINT || '';
  const STAFF_CODE = CFG.STAFF_CODE || '0000';
  const ADMIN_CODE = CFG.ADMIN_CODE || '1906';
  const MAX_HOURS = 20;
  const STEP = 0.25;                    // a quarter hour per tap

  const $ = id => document.getElementById(id);

  /* ================================================================= state == */
  let staff = [];
  let shifts = [];
  let me = null;
  let role = null;
  let entry = '';                       // digits typed into the keypad
  let day = null;                       // 'YYYY-MM-DD'
  let hours = 0;
  let busy = false;
  let linkOk = true;
  let lastSaved = null;                 // so one wrong tap can be taken back
  let pickOpen = false;                 // the date field, for anything older

  /* =============================================================== helpers == */
  const pad = n => String(n).padStart(2, '0');
  const uid = () => 's' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  const dayKey = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const esc = s => String(s).replace(/[&<>"']/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const hm = h => {
    const t = Math.round(h * 60);
    return `${Math.floor(t / 60)}:${pad(t % 60)}`;
  };

  // 6.5 reads as "6 hours 30 minutes", which nobody can mistake for half past six.
  function spoken(h) {
    const t = Math.round(h * 60);
    const wh = Math.floor(t / 60), wm = t % 60;
    const bits = [];
    if (wh) bits.push(`${wh} hour${wh === 1 ? '' : 's'}`);
    if (wm) bits.push(`${wm} minutes`);
    return bits.join(' ') || 'nothing yet';
  }

  function dayName(key, long) {
    const [y, m, d] = key.split('-').map(Number);
    const date = new Date(y, m - 1, d);
    const today = dayKey(new Date());
    const yest = dayKey(new Date(Date.now() - 864e5));
    if (key === today) return 'Today';
    if (key === yest) return 'Yesterday';
    return date.toLocaleDateString('en-AU', long
      ? { weekday: 'long', day: 'numeric', month: 'short' }
      : { weekday: 'short' });
  }
  const dayDate = key => {
    const [y, m, d] = key.split('-').map(Number);
    return new Date(y, m - 1, d).toLocaleDateString('en-AU', { day: 'numeric', month: 'short' });
  };

  /* The same reading the clock page does: a day logged as a number carries its
     hours, and a sheet too old to have that column is readable from the times,
     which start at exactly local midnight. */
  const loggedHours = sh => {
    const h = Number(sh.hours);
    if (Number.isFinite(h) && h > 0) return h;
    const a = new Date(sh.start);
    if (sh.end && a.getHours() === 0 && a.getMinutes() === 0 &&
        a.getSeconds() === 0 && a.getMilliseconds() === 0) {
      const span = (Date.parse(sh.end) - a.getTime()) / 3600000;
      if (span > 0) return span;
    }
    return 0;
  };
  function hoursOf(sh, now) {
    const logged = loggedHours(sh);
    if (logged) return logged;
    const a = Date.parse(sh.start);
    const b = sh.end ? Date.parse(sh.end) : now;
    return Number.isFinite(a) && b > a ? (b - a) / 3600000 : 0;
  }

  function toast(msg, kind) {
    const box = $('status');
    box.innerHTML = '';
    if (!msg) return;
    const el = document.createElement('div');
    el.className = 'note' + (kind === 'bad' ? ' bad' : '');
    const text = document.createElement('span');
    text.innerHTML = msg;
    el.appendChild(text);
    if (kind === 'undo') {
      const b = document.createElement('button');
      b.className = 'btn-2';
      b.type = 'button';
      b.textContent = 'Undo';
      b.addEventListener('click', undo);
      el.appendChild(b);
    }
    box.appendChild(el);
  }

  /* ================================================================= sheet ==
     Small on purpose. The clock page owns polling, fallbacks and the admin
     view; this page reads once, writes once, and re-reads to prove it landed. */
  async function pull() {
    if (!ENDPOINT) { linkOk = false; return; }
    try {
      const res = await fetch(ENDPOINT + '?action=load&t=' + Date.now());
      if (!res.ok) throw new Error('http ' + res.status);
      const out = await res.json();
      staff = out.staff || [];
      shifts = out.shifts || [];
      linkOk = true;
    } catch (err) {
      linkOk = false;
      throw err;
    }
  }

  /* Fire and forget, exactly as the clock page does: a POST to an Apps Script
     web app answers with a redirect that can look like an error even when the
     write went through. The sheet is the truth, so `commit` re-reads. */
  async function post(body) {
    try {
      await fetch(ENDPOINT, { method: 'POST', body: JSON.stringify(body) });
    } catch { /* a dead link shows up as the change not landing */ }
  }

  async function commit(shift, remove) {
    if (busy || !ENDPOINT) return false;
    busy = true;
    render();
    let ok = false;
    try {
      await post({ action: remove ? 'remove' : 'upsert', kind: 'shift', value: shift });
      await pull();
      const there = shifts.some(s => String(s.id) === String(shift.id));
      ok = there === !remove;
    } catch { ok = false; }
    busy = false;
    render();
    return ok;
  }

  /* =============================================================== actions == */
  async function save() {
    if (busy || !me || !day || hours <= 0) return;
    const person = staff.find(s => s.id === me);
    const shift = CFG.dayShift({
      id: uid(),
      staffId: me,
      staffName: person ? person.name : 'Unknown',
      date: day,
      hours,
      job: $('note').value.trim(),
    });

    toast('Saving&hellip;');
    if (await commit(shift)) {
      lastSaved = shift;
      toast(`Logged <b>${hm(shift.hours)}</b> for ${esc(dayName(day, true))}.`, 'undo');
      hours = 0;
      $('note').value = '';
      render();
    } else {
      toast('That didn&rsquo;t save. Check your signal and try again.', 'bad');
    }
  }

  async function undo() {
    if (!lastSaved || busy) return;
    const shift = lastSaved;
    toast('Taking it back&hellip;');
    if (await commit(shift, true)) {
      lastSaved = null;
      hours = shift.hours;
      day = dayKey(new Date(shift.start));
      $('note').value = shift.job || '';
      toast('Taken back. Nothing was logged.');
      render();
    } else {
      toast('Couldn&rsquo;t take it back. Ask Pat to delete it.', 'bad');
    }
  }

  function setMe(id) {
    me = id;
    try { id ? localStorage.setItem('imp.me', id) : localStorage.removeItem('imp.me'); } catch {}
    render();
  }

  /* Nothing on this page works until we know who is logging the day, so ask the
     moment both things are true: the code is in, and the crew list has arrived.
     Either can happen first. */
  function maybeAskWho() {
    if (!me && role && staff.length && !$('whoDlg').open) openWho();
  }

  function openWho() {
    $('whoList').innerHTML = staff.length
      ? staff.map(s => `<button type="button" data-me="${s.id}" aria-pressed="${s.id === me}">${esc(s.name)}</button>`).join('')
      : '<p style="grid-column:1/-1;margin:0;color:var(--muted);font-size:14px">The crew list didn&rsquo;t load. Check the connection and reload.</p>';
    $('whoDlg').showModal();
  }

  function setHours(h) {
    hours = Math.min(MAX_HOURS, Math.max(0, Math.round(h / STEP) * STEP));
    render();
  }

  /* ================================================================== gate == */
  function paintDots() {
    const dots = $('dots').children;
    for (let i = 0; i < dots.length; i++) dots[i].toggleAttribute('data-on', i < entry.length);
  }

  function setRole(next) {
    role = next;
    try {
      if (next) localStorage.setItem('imp.role', next);
      else localStorage.removeItem('imp.role');
    } catch {}
    $('gate').hidden = !!next;
    $('app').hidden = !next;
    if (!next) { entry = ''; paintDots(); $('gateSub').textContent = 'Enter your code'; $('gateSub').className = 'gate-sub'; }
    render();
    maybeAskWho();
  }

  function key(k) {
    const sub = $('gateSub');
    if (k === 'clear') { entry = ''; paintDots(); return; }
    if (k === 'back') { entry = entry.slice(0, -1); paintDots(); return; }
    if (entry.length >= 4) return;
    entry += k;
    paintDots();
    if (entry.length < 4) return;

    if (entry === ADMIN_CODE) return setRole('admin');
    if (entry === STAFF_CODE) return setRole('staff');

    sub.textContent = 'That code isn’t right.';
    sub.className = 'gate-sub bad';
    const box = $('gateIn');
    box.setAttribute('data-wrong', '');
    setTimeout(() => {
      box.removeAttribute('data-wrong');
      entry = '';
      paintDots();
      sub.textContent = 'Enter your code';
      sub.className = 'gate-sub';
    }, 620);
  }

  /* =============================================================== render === */
  // A week of buttons covers anything anyone is going to remember; the date
  // field is there for the rest.
  function renderDays() {
    const recent = [];
    for (let i = 0; i < 7; i++) recent.push(dayKey(new Date(Date.now() - i * 864e5)));
    const older = !!day && !recent.includes(day);
    $('days').innerHTML = recent.map(k =>
      `<button type="button" data-day="${k}" aria-pressed="${k === day}">
        <b>${dayName(k)}</b><small>${dayDate(k)}</small></button>`).join('') +
      `<button type="button" data-day="pick" aria-pressed="${older}">
        <b>Another</b><small>day</small></button>`;
    $('pickWrap').hidden = !(older || pickOpen);
  }

  function renderMine() {
    const from = CFG.weekStart(0), to = new Date(from.getTime() + 7 * 864e5);
    const fmt = t => t.toLocaleDateString('en-AU', { weekday: 'short', day: 'numeric', month: 'short' });
    $('weekRange').textContent = `${fmt(from)} – ${fmt(new Date(to.getTime() - 864e5))}`;

    const now = Date.now();
    const mine = shifts
      .filter(s => s.staffId === me)
      .filter(s => { const t = Date.parse(s.start); return t >= from.getTime() && t < to.getTime(); })
      .sort((a, b) => Date.parse(b.start) - Date.parse(a.start));

    const host = $('mine');
    if (!me) { host.innerHTML = '<div class="empty">Pick your name to see your week.</div>'; return; }
    if (!mine.length) { host.innerHTML = '<div class="empty">Nothing this week yet.</div>'; return; }

    let total = 0;
    const rows = mine.map(s => {
      const h = hoursOf(s, now);
      total += h;
      const k = dayKey(new Date(s.start));
      const what = loggedHours(s) ? 'logged' : 'clocked';
      return `<div class="line">
        <div><div class="d">${esc(dayName(k, true))}</div>
        <div class="j">${s.job ? esc(s.job) + ' · ' : ''}${what}</div></div>
        <div class="h tnum">${hm(h)}</div>
      </div>`;
    }).join('');
    host.innerHTML = rows + `<div class="line total">
      <div class="d">Week so far</div><div class="h tnum">${hm(total)}</div></div>`;
  }

  function render() {
    const person = staff.find(s => s.id === me);
    $('whoName').textContent = person ? person.name : 'Who are you?';

    renderDays();

    const big = $('big');
    big.textContent = hm(hours);
    big.classList.toggle('zero', hours <= 0);
    $('dialSub').textContent = hours > 0 ? spoken(hours) : 'Tap a number, then nudge it 15 minutes at a time.';
    $('minus').disabled = hours <= 0;
    $('plus').disabled = hours >= MAX_HOURS;
    for (const c of $('quick').children) {
      c.setAttribute('aria-pressed', String(Number(c.dataset.h) === hours));
    }

    const btn = $('save');
    const ready = !!me && !!day && hours > 0 && linkOk && !busy;
    btn.disabled = !ready;
    const when = dayName(day, true);               // Today | Yesterday | Monday 15 Sep
    btn.textContent = busy ? 'Saving…'
      : !me ? 'Pick your name first'
      : hours <= 0 ? 'How many hours?'
      : `Log ${hm(hours)} for ${when === 'Today' || when === 'Yesterday' ? when.toLowerCase() : when}`;

    const link = $('linkNote');
    if (!ENDPOINT) {
      link.hidden = false;
      link.dataset.tone = 'warn';
      link.innerHTML = '<b>No shared timesheet set up.</b> Nothing logged here will be saved.';
    } else if (!linkOk) {
      link.hidden = false;
      link.dataset.tone = 'bad';
      link.innerHTML = '<b>Not connected to the timesheet.</b> Nothing is saving. Tap to try again.';
    } else {
      link.hidden = true;
    }

    $('storeNote').textContent = linkOk && ENDPOINT ? 'It goes to the shared timesheet.' : '';
    $('roleNote').textContent = role === 'admin' ? 'Signed in as admin.' : 'Signed in as crew.';

    renderMine();
  }

  /* ================================================================ wiring == */
  $('whoBtn').addEventListener('click', openWho);
  $('whoCancel').addEventListener('click', () => $('whoDlg').close());
  $('minus').addEventListener('click', () => setHours(hours - STEP));
  $('plus').addEventListener('click', () => setHours(hours + STEP));
  $('save').addEventListener('click', save);
  $('signOut').addEventListener('click', () => setRole(null));

  $('pickDate').addEventListener('change', e => {
    if (!e.target.value) return;
    day = e.target.value;
    render();
  });

  $('pad').addEventListener('click', e => {
    const b = e.target.closest('[data-k]');
    if (b) key(b.dataset.k);
  });
  addEventListener('keydown', e => {
    if ($('gate').hidden) return;
    if (/^[0-9]$/.test(e.key)) key(e.key);
    else if (e.key === 'Backspace') key('back');
    else if (e.key === 'Escape') key('clear');
  });

  $('linkNote').addEventListener('click', async () => {
    if (linkOk || !ENDPOINT) return;
    toast('Reconnecting&hellip;');
    try { await pull(); toast(''); } catch { toast('Still can&rsquo;t reach the timesheet.', 'bad'); }
    render();
  });

  document.addEventListener('click', e => {
    const t = e.target.closest('[data-me],[data-day],[data-h]');
    if (!t) return;
    if (t.dataset.me) { setMe(t.dataset.me); $('whoDlg').close(); }
    else if (t.dataset.day === 'pick') {
      pickOpen = true;
      render();
      $('pickDate').focus();
      if ($('pickDate').showPicker) { try { $('pickDate').showPicker(); } catch {} }
    } else if (t.dataset.day) { day = t.dataset.day; pickOpen = false; render(); }
    else if (t.dataset.h) { setHours(Number(t.dataset.h)); }
  });

  /* ================================================================== boot == */
  (async () => {
    try {
      me = localStorage.getItem('imp.me');
      const saved = localStorage.getItem('imp.role');
      if (saved === 'staff' || saved === 'admin') role = saved;
    } catch {}
    $('gate').hidden = !!role;
    $('app').hidden = !role;
    paintDots();

    day = dayKey(new Date());
    $('pickDate').max = day;
    render();

    try { await pull(); } catch {}
    if (me && !staff.some(s => s.id === me)) setMe(null);
    render();
    maybeAskWho();
  })();
})();
