/* Imperium Detailing — timesheets.

   One page, three possible places to keep the data, picked at startup:

     sheets    a Google Apps Script web app writing to a Google Sheet. This is
               the real one: any phone can open the URL, no accounts, and the
               hours land in a spreadsheet Pat can read and fix.
     artifact  the claude.ai artifact store, when the page is published there.
     local     this phone only. The fallback, so the page is never a dead end.

   Everything above the Store is identical whichever one is in use. */

(() => {
  'use strict';

  /* ================================================================ config ==
     Shared with log.html, so it lives in config.js and is only typed once. */
  const CFG = window.IMP || {};
  const ENDPOINT = CFG.ENDPOINT || '';
  const STAFF_CODE = CFG.STAFF_CODE || '0000';
  const ADMIN_CODE = CFG.ADMIN_CODE || '1906';
  const DEFAULT_RATE = CFG.DEFAULT_RATE || 27;
  const DEFAULT_CREW = CFG.DEFAULT_CREW || [];
  const POLL_MS = CFG.POLL_MS || 20000;   // how often a sheet-backed page re-reads

  const $ = id => document.getElementById(id);
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ================================================================= state == */
  let store = null;
  let mode = 'local';
  let staff = [];
  let shifts = [];
  let settings = {};
  let me = null;
  let weekOffset = 0;
  let busy = false;
  let editingId = null;
  let backMinutes = 0;                  // how far back a shift should start
  let role = null;                      // 'staff' or 'admin', set at the gate
  let entry = '';                       // digits typed into the keypad
  let linkOk = true;                    // is the shared timesheet answering?
  const isAdmin = () => role === 'admin';

  /* =============================================================== helpers == */
  const pad = n => String(n).padStart(2, '0');
  const uid = () => 's' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);

  function hms(ms) {
    const s = Math.max(0, Math.floor(ms / 1000));
    return `${Math.floor(s / 3600)}:${pad(Math.floor(s / 60) % 60)}:${pad(s % 60)}`;
  }
  /* A day nobody clocked is stored as a plain number of hours, because there
     are no real times to keep. It still carries a start and end covering the
     same span, so a total is right even from a sheet that has not been updated
     to hold the hours column. */
  const loggedHours = sh => {
    const h = Number(sh.hours);
    if (Number.isFinite(h) && h > 0) return h;
    /* A sheet deployed before the hours column existed drops that field, so the
       same thing is readable from the times: these start at exactly local
       midnight, which no real clock-on ever does. */
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
  function hm(h) {
    const t = Math.round(h * 60);
    return `${Math.floor(t / 60)}:${pad(t % 60)}`;
  }
  const money = n => '$' + n.toLocaleString('en-AU', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const clock = d => d.toLocaleTimeString('en-AU', { hour: 'numeric', minute: '2-digit' });
  const dayKey = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

  function dayLabel(key) {
    const [y, m, d] = key.split('-').map(Number);
    const today = dayKey(new Date());
    const yest = dayKey(new Date(Date.now() - 864e5));
    if (key === today) return 'Today';
    if (key === yest) return 'Yesterday';
    return new Date(y, m - 1, d).toLocaleDateString('en-AU', { weekday: 'short', day: 'numeric', month: 'short' });
  }

  // Pay weeks run Wednesday to Tuesday. The rule lives in config.js so this
  // page and log.html cannot end up disagreeing about which week a shift is in.
  const weekStart = (offset = 0) => CFG.weekStart(offset);

  const esc = s => String(s).replace(/[&<>"']/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  function toast(msg, bad) {
    const box = $('status');
    box.innerHTML = '';
    if (!msg) return;
    const el = document.createElement('div');
    el.className = 'note' + (bad ? ' bad' : '');
    el.textContent = msg;
    box.appendChild(el);
  }

  /* The browser's own confirm() is blocked inside an embedded viewer: the call
     just returns false, so the delete silently never ran. Asking in the page
     works everywhere and matches the rest of the app. */
  let askDone = null;
  function ask(title, body, yes) {
    return new Promise(resolve => {
      $('askTitle').textContent = title;
      $('askBody').textContent = body || '';
      $('askBody').hidden = !body;
      $('askYes').textContent = yes || 'Delete';
      askDone = resolve;
      $('askDlg').showModal();
    });
  }
  function closeAsk(answer) {
    const done = askDone;
    askDone = null;
    $('askDlg').close();
    if (done) done(answer);
  }

  /* ================================================================ stores ==
     Each adapter exposes the same five calls, so nothing below this block ever
     needs to know where the data actually lives. */

  function localStore() {
    const KEY = 'imp.hours.v1';
    const read = () => {
      try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch { return {}; }
    };
    const write = s => {
      try { localStorage.setItem(KEY, JSON.stringify(s)); } catch {}
    };
    let cb = () => {};
    const push = () => cb({ staff, shifts, settings });
    return {
      mode: 'local',
      note: 'Hours are saved on this phone only.',
      async init() {
        const s = read();
        staff = s.staff || [];
        shifts = s.shifts || [];
        settings = s.settings || {};
      },
      subscribe(fn) { cb = fn; push(); },
      async save() { write({ staff, shifts, settings }); push(); },
    };
  }

  function sheetsStore(url) {
    let cb = () => {};
    let timer = null;

    /* Sent as text/plain on purpose: that keeps it a "simple" cross-origin
       request, so the browser skips the preflight Apps Script cannot answer.

       The reply is deliberately ignored. A POST to a web app answers with a 302
       to a one-shot script.googleusercontent.com URL, and re-requesting that can
       land on a Google error page even though the write went through — measured
       against the live endpoint. So the write is fire-and-forget and `save`
       below confirms it by re-reading. The sheet is the truth, not the reply. */
    async function post(body) {
      try {
        await fetch(url, { method: 'POST', body: JSON.stringify(body) });
      } catch {
        /* A network failure still shows up as the change not landing. */
      }
    }
    async function pull() {
      try {
        const res = await fetch(url + '?action=load&t=' + Date.now());
        if (!res.ok) throw new Error('http ' + res.status);
        const out = await res.json();
        staff = out.staff || [];
        shifts = out.shifts || [];
        settings = out.settings || {};
        linkOk = true;
      } catch (err) {
        linkOk = false;
        throw err;
      }
      cb({ staff, shifts, settings });
    }
    return {
      mode: 'sheets',
      note: 'Hours sync to the shared timesheet.',
      async init() { await pull(); },
      subscribe(fn) {
        cb = fn;
        cb({ staff, shifts, settings });
        clearInterval(timer);
        // Re-read on a timer, and immediately whenever the phone comes back to
        // the page — that is when somebody is actually about to look at it.
        timer = setInterval(() => pull().catch(render), POLL_MS);
        document.addEventListener('visibilitychange', () => {
          if (!document.hidden) pull().catch(render);
        });
      },
      async save(change) {
        if (!change) return;
        await post(change.kind === 'settings'
          ? { action: 'settings', value: settings }
          : { action: change.remove ? 'remove' : 'upsert', kind: change.kind, value: change.value });

        // Re-read, which both confirms the write and picks up whatever the other
        // phones have done since.
        await pull();

        if (change.kind === 'settings') return;
        const list = change.kind === 'staff' ? staff : shifts;
        const there = list.some(x => String(x.id) === String(change.value.id));
        if (there === !!change.remove) throw new Error('write did not land');
      },
    };
  }

  function artifactStore(db) {
    let cb = () => {};
    const push = () => cb({ staff, shifts, settings });
    return {
      mode: 'artifact',
      note: 'Hours sync to everyone signed in to this workspace.',
      async init() {
        const onErr = () => toast('Lost the live connection. Pull down to reload.', true);
        db.collection('staff').onSnapshot(s => {
          staff = s.docs.map(d => ({ id: d.id, ...d.data() }))
            .sort((a, b) => String(a.name).localeCompare(String(b.name)));
          push();
        }, onErr);
        db.collection('shifts').orderBy('start', 'desc').limit(500).onSnapshot(s => {
          shifts = s.docs.map(d => ({ id: d.id, ...d.data() }));
          push();
        }, onErr);
        db.doc('config/settings').onSnapshot(d => {
          settings = d.exists ? d.data() : {};
          push();
        }, onErr);
      },
      subscribe(fn) { cb = fn; push(); },
      /* The shared adapters replace the whole state; this one writes only what
         actually moved, because the store is per-document. */
      async save(change) {
        if (!change) return;
        if (change.kind === 'settings') return db.doc('config/settings').set(settings);
        const { id, ...body } = change.value;
        const ref = db.doc(`${change.kind === 'staff' ? 'staff' : 'shifts'}/${id}`);
        return change.remove ? ref.delete() : ref.set(body);
      },
    };
  }

  async function pickStore() {
    /* The artifact viewer is sandboxed and cannot reach Google at all, so
       trying the sheet from there only produces a confusing half-state: the app
       looks fine and the spreadsheet never changes. Check for it first, use the
       artifact's own store, and let the banner call it a preview. */
    try {
      const db = typeof claude !== 'undefined' && claude.use ? await claude.use('db') : null;
      if (db) { const s = artifactStore(db); await s.init(); return s; }
    } catch {}

    if (ENDPOINT) {
      const s = sheetsStore(ENDPOINT);
      for (let i = 0; i < 3; i++) {
        try { await s.init(); return s; } catch {}
        await new Promise(r => setTimeout(r, 500 * (i + 1)));
      }
      /* Stay pointed at the sheet rather than quietly starting a second,
         private timesheet on this phone: two records of the same week is worse
         than one that says it is offline. The banner says so, and the poll
         keeps trying. */
      linkOk = false;
      return s;
    }

    const s = localStore();
    await s.init();
    return s;
  }

  /* Writes go through here so a failure always says something useful and the
     button can never be double-tapped into two shifts. */
  async function commit(change) {
    if (busy) return;
    busy = true;
    render();
    try {
      await store.save(change);
      toast('');
    } catch {
      toast('That didn’t save. Check your signal and try again.', true);
    } finally {
      busy = false;
      render();
    }
  }

  /* =============================================================== actions == */
  const myOpen = () => shifts.find(s => s.staffId === me && !s.end) || null;
  const rateOf = id => {
    const s = staff.find(x => x.id === id);
    return s && Number.isFinite(Number(s.rate)) ? Number(s.rate) : 0;
  };

  function startShift() {
    if (!me) return openWho();
    if (myOpen()) return;
    const person = staff.find(s => s.id === me);
    const shift = {
      id: uid(),
      staffId: me,
      staffName: person ? person.name : 'Unknown',
      start: new Date(Date.now() - backMinutes * 60000).toISOString(),
      end: null,
      job: $('jobIn').value.trim(),
    };
    shifts.unshift(shift);
    $('jobIn').value = '';
    backMinutes = 0;
    $('backChips').hidden = true;
    commit({ kind: 'shift', value: shift });
  }

  function finishShift() {
    const open = myOpen();
    if (!open) return;
    open.end = new Date().toISOString();
    commit({ kind: 'shift', value: open });
  }

  function addStaff() {
    if (!isAdmin()) return;
    const name = $('newName').value.trim();
    if (!name) return $('newName').focus();
    const raw = parseFloat($('newRate').value);
    const person = { id: uid(), name, rate: Number.isFinite(raw) ? raw : DEFAULT_RATE };
    staff.push(person);
    staff.sort((a, b) => String(a.name).localeCompare(String(b.name)));
    $('newName').value = '';
    $('newRate').value = '';
    commit({ kind: 'staff', value: person });
  }

  async function removeStaff(id) {
    if (!isAdmin()) return;
    const s = staff.find(x => x.id === id);
    if (!s) return;
    const yes = await ask(`Take ${s.name} off the crew?`,
      'Their past shifts stay on the timesheet.', 'Remove');
    if (!yes) return;
    staff = staff.filter(x => x.id !== id);
    if (me === id) setMe(null);
    commit({ kind: 'staff', value: s, remove: true });
  }

  async function deleteShift(id) {
    if (!isAdmin()) return;
    const s = shifts.find(x => x.id === id);
    if (!s) return;
    const at = new Date(s.start);
    const yes = await ask('Delete this shift?',
      `${s.staffName || 'Unknown'}, ${dayLabel(dayKey(at))} at ${clock(at)}. It can’t be undone.`);
    if (!yes) return;
    shifts = shifts.filter(x => x.id !== id);
    commit({ kind: 'shift', value: s, remove: true });
  }

  /* ============================================================== who am I == */
  function setMe(id) {
    me = id;
    try { id ? localStorage.setItem('imp.me', id) : localStorage.removeItem('imp.me'); } catch {}
    render();
  }
  function openWho() {
    $('whoList').innerHTML = staff.length
      ? staff.map(s => `<button type="button" data-me="${s.id}" aria-pressed="${s.id === me}">${esc(s.name)}</button>`).join('')
      : '<p style="grid-column:1/-1;margin:0;color:var(--muted);font-size:14px">Nobody on the crew yet. Add names under Admin.</p>';
    $('whoDlg').showModal();
  }

  /* ============================================================ backdating == */
  function applyBack(mins) {
    backMinutes = mins;
    for (const c of $('backChips').querySelectorAll('.chip')) {
      c.setAttribute('aria-pressed', String(Number(c.dataset.back) === mins));
    }
    render();
  }
  function openTimePick() {
    const d = new Date();
    $('tTime').value = `${pad(d.getHours())}:${pad(d.getMinutes())}`;
    $('timeDlg').showModal();
  }
  function saveTimePick() {
    const v = $('tTime').value;
    if (!v) return;
    const [h, m] = v.split(':').map(Number);
    const started = new Date();
    started.setHours(h, m, 0, 0);
    // A time later than now can only mean yesterday evening.
    if (started > new Date()) started.setDate(started.getDate() - 1);
    $('timeDlg').close();
    applyBack(Math.max(0, Math.round((Date.now() - started.getTime()) / 60000)));
  }

  /* ============================================================ edit shift == */
  function openEdit(id) {
    if (!isAdmin()) return;
    editingId = id;
    const sh = id ? shifts.find(s => s.id === id) : null;
    $('editTitle').textContent = sh ? 'Edit shift' : 'Add a past shift';
    $('eWho').innerHTML = staff.map(s => `<option value="${s.id}">${esc(s.name)}</option>`).join('');
    $('eErr').hidden = true;

    const start = sh ? new Date(sh.start) : new Date();
    const end = sh && sh.end ? new Date(sh.end) : null;
    $('eWho').value = sh ? sh.staffId : (me || (staff[0] && staff[0].id) || '');
    $('eDate').value = dayKey(start);
    $('eStart').value = `${pad(start.getHours())}:${pad(start.getMinutes())}`;
    $('eEnd').value = end ? `${pad(end.getHours())}:${pad(end.getMinutes())}` : '';
    $('eJob').value = sh ? (sh.job || '') : '';

    // A day that was logged as a number has no real times to edit, so it gets
    // the number instead. Editing it keeps it that way.
    const logged = sh ? loggedHours(sh) : 0;
    $('eTimes').hidden = !!logged;
    $('eHoursWrap').hidden = !logged;
    $('eHours').value = logged ? String(Number(logged.toFixed(2))) : '';

    $('editDlg').showModal();
  }

  function saveEdit() {
    const staffId = $('eWho').value;
    const date = $('eDate').value;
    const st = $('eStart').value;
    const en = $('eEnd').value;
    const err = m => { const p = $('eErr'); p.textContent = m; p.hidden = false; };

    if (!staffId) return err('Pick who worked it.');

    if (!$('eHoursWrap').hidden) {
      if (!date) return err('A shift needs a date.');
      const h = parseFloat($('eHours').value);
      if (!Number.isFinite(h) || h <= 0) return err('How many hours were worked?');
      if (h > 20) return err('That is over 20 hours. Check the number.');
      const who = staff.find(s => s.id === staffId);
      const logged = CFG.dayShift({
        id: editingId || uid(),
        staffId,
        staffName: who ? who.name : 'Unknown',
        date,
        hours: h,
        job: $('eJob').value.trim(),
      });
      const at = shifts.findIndex(s => s.id === logged.id);
      if (at >= 0) shifts[at] = logged; else shifts.unshift(logged);
      shifts.sort((a, b) => Date.parse(b.start) - Date.parse(a.start));
      $('editDlg').close();
      return commit({ kind: 'shift', value: logged });
    }

    if (!date || !st) return err('A shift needs a date and a start time.');

    const start = new Date(`${date}T${st}`);
    let end = en ? new Date(`${date}T${en}`) : null;
    // A finish before the start means the shift ran past midnight.
    if (end && end <= start) end = new Date(end.getTime() + 864e5);
    if (end && end - start > 20 * 3600000) return err('That shift is over 20 hours. Check the times.');

    const person = staff.find(s => s.id === staffId);
    const value = {
      id: editingId || uid(),
      staffId,
      staffName: person ? person.name : 'Unknown',
      start: start.toISOString(),
      end: end ? end.toISOString() : null,
      job: $('eJob').value.trim(),
      hours: '',
    };
    const i = shifts.findIndex(s => s.id === value.id);
    if (i >= 0) shifts[i] = value; else shifts.unshift(value);
    shifts.sort((a, b) => Date.parse(b.start) - Date.parse(a.start));
    $('editDlg').close();
    commit({ kind: 'shift', value });
  }

  /* ================================================================= gate === */
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

    sub.textContent = 'That code isn\u2019t right.';
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

  /* ================================================================== CSV === */
  const weekShifts = (from, to) => shifts
    .filter(s => { const t = Date.parse(s.start); return t >= from.getTime() && t < to.getTime(); })
    .slice().sort((a, b) => Date.parse(a.start) - Date.parse(b.start));

  async function exportCsv() {
    const from = weekStart(weekOffset), to = new Date(from.getTime() + 7 * 864e5);
    const rows = weekShifts(from, to);
    if (!rows.length) return toast('No shifts in that week to export.', true);

    const cell = v => `"${String(v == null ? '' : v).replace(/"/g, '""')}"`;
    const now = Date.now();
    const lines = [['Date', 'Who', 'Start', 'Finish', 'Hours', 'Rate', 'Pay', 'Job'].map(cell).join(',')];
    for (const s of rows) {
      const h = hoursOf(s, now), rate = rateOf(s.staffId), d = new Date(s.start);
      lines.push([
        d.toLocaleDateString('en-AU'), s.staffName || '',
        loggedHours(s) ? 'logged' : clock(d),
        loggedHours(s) ? 'logged' : s.end ? clock(new Date(s.end)) : 'still on',
        h.toFixed(2), rate ? rate.toFixed(2) : '', rate ? (h * rate).toFixed(2) : '', s.job || '',
      ].map(cell).join(','));
    }
    const csv = lines.join('\r\n');
    const filename = `imperium-hours-${dayKey(from)}.csv`;

    // In the artifact viewer a plain download link is inert, so ask the host.
    try {
      const dl = typeof claude !== 'undefined' && claude.use ? await claude.use('downloads') : null;
      if (dl) { await dl.save({ filename, data: csv }); return toast(`Saved ${filename}.`); }
    } catch { return toast('The download was cancelled.', true); }

    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast(`Saved ${filename}.`);
  }

  /* =============================================================== render === */
  function render() {
    const now = Date.now();
    const open = myOpen();
    const person = staff.find(s => s.id === me);

    $('whoName').textContent = person ? person.name : 'Who are you?';

    const card = $('clock');
    card.toggleAttribute('data-running', !!open);
    $('stateLabel').textContent = open ? 'On the clock' : 'Not clocked on';
    $('startFields').hidden = !!open;
    $('backdate').hidden = !!open || !me;

    if (open) {
      $('since').textContent = `Started ${clock(new Date(open.start))}` + (open.job ? ` · ${open.job}` : '');
    } else if (!staff.length) {
      $('since').textContent = 'Add the crew under Admin to get started.';
    } else if (!me) {
      $('since').textContent = 'Pick your name to get started.';
    } else if (backMinutes > 0) {
      const from = new Date(now - backMinutes * 60000);
      $('since').textContent = `Will count from ${clock(from)}.`;
    } else {
      $('since').textContent = 'Ready when you are.';
    }

    const btn = $('mainBtn');
    btn.textContent = open ? 'Finish shift' : 'Start shift';
    btn.classList.toggle('stop', !!open);
    btn.disabled = busy || (!open && !staff.length);

    tick();

    const today = dayKey(new Date());
    const wkFrom = weekStart(0).getTime();
    let tH = 0, wH = 0;
    for (const s of shifts) {
      if (me && s.staffId !== me) continue;
      const t = Date.parse(s.start);
      if (dayKey(new Date(t)) === today) tH += hoursOf(s, now);
      if (t >= wkFrom) wH += hoursOf(s, now);
    }
    $('kToday').textContent = me ? 'Your today' : 'Today, all';
    $('kWeek').textContent = me ? 'Your week' : 'Week, all';
    $('sToday').innerHTML = hm(tH) + '<small>h</small>';
    $('sWeek').innerHTML = hm(wH) + '<small>h</small>';
    $('sOn').textContent = shifts.filter(s => !s.end).length;
    $('shiftScope').textContent = shifts.length ? 'Everyone, newest first' : '';

    /* Where the hours are going, said out loud whenever it is not the sheet. */
    const link = $('linkNote');
    if (mode === 'sheets' && !linkOk) {
      link.hidden = false;
      link.dataset.tone = 'bad';
      link.innerHTML = '<b>Not connected to the timesheet.</b> Nothing is saving. Tap to try again.';
    } else if (mode === 'artifact') {
      link.hidden = false;
      link.dataset.tone = 'warn';
      link.innerHTML = '<b>Preview.</b> Hours here do not reach the Google Sheet \u2014 open the real link for that.';
    } else if (mode === 'local') {
      link.hidden = false;
      link.dataset.tone = 'warn';
      link.innerHTML = '<b>This phone only.</b> Hours are not shared with anyone else.';
    } else {
      link.hidden = true;
    }

    $('storeNote').textContent = store ? store.note : '';

    // Everything that changes the record is admin-only. The crew can clock on
    // and off, and read the list, and that is the whole of it.
    $('adminBox').hidden = !isAdmin();
    $('roleNote').textContent = isAdmin() ? 'Signed in as admin.' : 'Signed in as crew.';

    renderShifts(now);
    renderWeek(now);
    renderStaff();
  }

  function renderShifts(now) {
    const host = $('shifts');
    if (!shifts.length) {
      host.innerHTML = '<div class="empty">No shifts yet. Start one above and it turns up here.</div>';
      return;
    }
    const byDay = new Map();
    for (const s of shifts) {
      const k = dayKey(new Date(s.start));
      if (!byDay.has(k)) byDay.set(k, []);
      byDay.get(k).push(s);
    }
    const out = [];
    for (const [k, list] of [...byDay.entries()].sort((a, b) => b[0].localeCompare(a[0])).slice(0, 21)) {
      const total = list.reduce((n, s) => n + hoursOf(s, now), 0);
      out.push(`<div class="day"><div class="date"><span>${dayLabel(k)}</span><b>${hm(total)} h</b></div>` +
        list.slice().sort((a, b) => Date.parse(b.start) - Date.parse(a.start)).map(s => {
          const st = new Date(s.start);
          const times = loggedHours(s) ? 'Hours logged, no times'
            : s.end ? `${clock(st)} – ${clock(new Date(s.end))}`
            : `${clock(st)} – still on`;
          return `<div class="row"${s.end ? '' : ' data-open'}>
            <div class="main">
              <div class="person">${esc(s.staffName || 'Unknown')}</div>
              <div class="times tnum">${times}</div>
              ${s.job ? `<div class="job">${esc(s.job)}</div>` : ''}
            </div>
            <div class="dur tnum">${hm(hoursOf(s, now))}</div>
            ${isAdmin() ? `<div class="acts">
              <button class="btn-2" data-edit="${s.id}" type="button">Edit</button>
              <button class="btn-2 danger" data-del="${s.id}" type="button">Delete</button>
            </div>` : ''}
          </div>`;
        }).join('') + '</div>');
    }
    host.innerHTML = out.join('');
  }

  function renderWeek(now) {
    const from = weekStart(weekOffset), to = new Date(from.getTime() + 7 * 864e5);
    const rows = weekShifts(from, to);
    const per = new Map();
    for (const s of rows) {
      const k = s.staffId || 'unknown';
      const cur = per.get(k) || { name: s.staffName || 'Unknown', h: 0 };
      cur.h += hoursOf(s, now);
      per.set(k, cur);
    }
    const fmt = t => t.toLocaleDateString('en-AU', { weekday: 'short', day: 'numeric', month: 'short' });
    const label = `${fmt(from)} – ${fmt(new Date(to.getTime() - 864e5))}`;
    const host = $('weekTotals');
    if (!per.size) {
      host.innerHTML = `<div class="empty">Nothing logged ${weekOffset === 0 ? 'this pay week' : 'that pay week'} (${label}).</div>`;
      return;
    }
    let totH = 0, totP = 0;
    const body = [...per.entries()].map(([id, v]) => {
      const rate = rateOf(id);
      totH += v.h; totP += v.h * rate;
      return `<div class="who-row"><b>${esc(v.name)}</b>
        <span class="hrs tnum">${hm(v.h)}</span>
        <span class="pay tnum">${rate ? money(v.h * rate) : '—'}</span></div>`;
    }).join('');
    host.innerHTML = `<div class="who-row" style="border-bottom-color:var(--line-2)">
        <b style="color:var(--muted)">${label}</b>
        <span class="hrs tnum">${hm(totH)}</span>
        <span class="pay tnum">${totP ? money(totP) : '—'}</span>
      </div>` + body;
  }

  function renderStaff() {
    $('staffList').innerHTML = staff.length
      ? staff.map(s => `<div class="staff-row"><b>${esc(s.name)}</b>
          <span class="rate tnum">${rateOf(s.id) ? money(rateOf(s.id)) + '/h' : 'no rate'}</span>
          <button class="btn-2 danger" data-rmstaff="${s.id}" type="button">Remove</button></div>`).join('')
      : '<div class="empty">Nobody on the crew yet. Add a name below.</div>';
  }

  /* The only thing on a timer is the readout. It never writes. */
  function tick() {
    const open = myOpen();
    $('elapsed').textContent = open ? hms(Date.now() - Date.parse(open.start)) : '0:00:00';
  }

  /* ================================================================ wiring == */
  $('mainBtn').addEventListener('click', () => (myOpen() ? finishShift() : startShift()));
  $('whoBtn').addEventListener('click', openWho);
  $('whoCancel').addEventListener('click', () => $('whoDlg').close());
  $('addStaff').addEventListener('click', addStaff);
  $('newName').addEventListener('keydown', e => { if (e.key === 'Enter') addStaff(); });
  $('manualBtn').addEventListener('click', () => openEdit(null));
  $('eCancel').addEventListener('click', () => $('editDlg').close());
  $('eSave').addEventListener('click', saveEdit);
  $('tCancel').addEventListener('click', () => $('timeDlg').close());
  $('tSave').addEventListener('click', saveTimePick);
  $('csvBtn').addEventListener('click', exportCsv);
  $('askYes').addEventListener('click', () => closeAsk(true));
  $('askNo').addEventListener('click', () => closeAsk(false));
  // Esc counts as "no".
  $('askDlg').addEventListener('close', () => closeAsk(false));

  $('linkNote').addEventListener('click', async () => {
    if (mode !== 'sheets' || linkOk) return;
    toast('Reconnecting\u2026');
    try { await store.init(); toast(''); } catch { toast('Still can\u2019t reach the timesheet.', true); }
    render();
  });
  $('prevWeek').addEventListener('click', () => { weekOffset--; render(); });
  $('nextWeek').addEventListener('click', () => { weekOffset = Math.min(0, weekOffset + 1); render(); });

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
  $('signOut').addEventListener('click', () => setRole(null));

  $('backLink').addEventListener('click', () => {
    const chips = $('backChips');
    chips.hidden = !chips.hidden;
    if (!chips.hidden) applyBack(backMinutes);
  });

  // One delegated listener rather than rebinding every row on each render.
  document.addEventListener('click', e => {
    const t = e.target.closest('[data-edit],[data-del],[data-rmstaff],[data-me],[data-back]');
    if (!t) return;
    if (t.dataset.edit) openEdit(t.dataset.edit);
    else if (t.dataset.del) deleteShift(t.dataset.del);
    else if (t.dataset.rmstaff) removeStaff(t.dataset.rmstaff);
    else if (t.dataset.me) { setMe(t.dataset.me); $('whoDlg').close(); }
    else if (t.dataset.back !== undefined) {
      const m = Number(t.dataset.back);
      if (m === -1) openTimePick(); else applyBack(m);
    }
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
    if (!reduced) document.documentElement.classList.add('anim');
    setInterval(tick, 1000);

    store = await pickStore();
    mode = store.mode;

    // The crew Pat named, so nobody has to set the app up before using it. Only
    // for the stores this page owns — the artifact store is seeded server-side.
    if (mode !== 'artifact' && linkOk && !staff.length) {
      staff = DEFAULT_CREW.map(name => ({ id: uid(), name, rate: DEFAULT_RATE }))
        .sort((a, b) => a.name.localeCompare(b.name));
      for (const person of staff) {
        try { await store.save({ kind: 'staff', value: person }); } catch {}
      }
    }

    // "Pick a time" only makes sense once the chips exist; add it here so the
    // markup stays declarative.
    const chips = $('backChips');
    if (chips && !chips.querySelector('[data-back="-1"]')) {
      const b = document.createElement('button');
      b.className = 'chip';
      b.type = 'button';
      b.dataset.back = '-1';
      b.textContent = 'Pick a time';
      chips.appendChild(b);
    }

    store.subscribe(() => {
      if (me && !staff.some(s => s.id === me)) setMe(null);
      render();
    });
    render();
  })();
})();
