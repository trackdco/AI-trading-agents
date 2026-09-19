/* Imperium Clock.

   A timesheet for a crew that works in driveways. Three things shaped it:

   1. The dial is the product. Start and Finish are the only two taps that
      matter, so the readout is the biggest thing on the screen and the press of
      Start is the one moment the app allows itself to be theatrical.

   2. Signal is not guaranteed. Every write lands in a queue on the phone first
      and syncs after, so a shift is never lost because the save happened in a
      dead spot behind a garage. The queue survives the app being closed.

   3. Nothing is invented. A day nobody clocked is stored as a number of hours
      with no times, because there weren't any.

   Data lives in the same Google Sheet as the old page — same endpoint, same
   rows — so both can run side by side while Pat decides. */

(() => {
  'use strict';

  /* ================================================================ config == */
  const CFG = window.IMP || {};
  const ENDPOINT = CFG.ENDPOINT || '';
  const STAFF_CODE = CFG.STAFF_CODE || '0000';
  const ADMIN_CODE = CFG.ADMIN_CODE || '1906';
  const DEFAULT_RATE = CFG.DEFAULT_RATE || 27;
  const DEFAULT_CREW = CFG.DEFAULT_CREW || [];
  const POLL_MS = CFG.POLL_MS || 20000;
  const FULL_DAY_H = 8;                 // what the arc treats as a full sweep
  const QUEUE_KEY = 'imp.clock.queue';
  const CACHE_KEY = 'imp.clock.last';    // the last crew list and shifts seen

  const $ = id => document.getElementById(id);
  const SVG = 'http://www.w3.org/2000/svg';
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ================================================================= state == */
  let store = null;
  let mode = 'local';
  let staff = [];
  let shifts = [];
  let me = null;
  let role = null;
  let tab = 'clock';
  let weekOffset = 0;
  let busy = false;
  let editingId = null;
  let backMinutes = 0;
  let entry = '';
  let linkOk = true;
  let queue = [];                       // writes waiting for signal
  let wasRunning = false;               // so the dial only ignites on a change
  let askedWho = false;                 // the name is asked once per unlock

  const isAdmin = () => role === 'admin';

  /* =============================================================== helpers == */
  const pad = n => String(n).padStart(2, '0');
  const uid = () => 's' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  const dayKey = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const esc = s => String(s).replace(/[&<>"']/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const buzz = ms => { try { navigator.vibrate && navigator.vibrate(ms); } catch {} };

  function hms(ms) {
    const s = Math.max(0, Math.floor(ms / 1000));
    return `${Math.floor(s / 3600)}:${pad(Math.floor(s / 60) % 60)}:${pad(s % 60)}`;
  }
  function hm(h) {
    const t = Math.round(h * 60);
    return `${Math.floor(t / 60)}:${pad(t % 60)}`;
  }
  const money = n => '$' + n.toLocaleString('en-AU', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const clock = d => d.toLocaleTimeString('en-AU', { hour: 'numeric', minute: '2-digit' });

  function dayLabel(key, long) {
    const [y, m, d] = key.split('-').map(Number);
    const today = dayKey(new Date());
    const yest = dayKey(CFG.addDays(new Date(), -1));
    if (key === today) return 'Today';
    if (key === yest) return 'Yesterday';
    return new Date(y, m - 1, d).toLocaleDateString('en-AU', long
      ? { weekday: 'long', day: 'numeric', month: 'short' }
      : { weekday: 'short', day: 'numeric', month: 'short' });
  }

  // The pay week rule lives in config.js so nothing can disagree about it.
  const weekStart = (offset = 0) => CFG.weekStart(offset);

  /* A day nobody clocked carries its own number of hours. It also carries a
     start and end spanning the same length from local midnight, so a sheet that
     predates the hours column still totals correctly — and that midnight start,
     which no real clock-on ever has, is how it stays recognisable. */
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

  function toast(msg, kind, action) {
    const box = $('status');
    box.innerHTML = '';
    if (!msg) return;
    const el = document.createElement('div');
    el.className = 'note' + (kind === 'bad' ? ' bad' : '');
    const text = document.createElement('span');
    text.innerHTML = msg;
    el.appendChild(text);
    if (action) {
      const b = document.createElement('button');
      b.className = 'btn';
      b.type = 'button';
      b.textContent = action.label;
      b.addEventListener('click', action.run);
      el.appendChild(b);
    }
    box.appendChild(el);
    // An Undo waits longer than a plain note, but not forever: it must not be
    // sitting there for the next person who picks the phone up.
    if (kind !== 'bad') setTimeout(() => { if (box.firstChild === el) box.innerHTML = ''; }, action ? 12000 : 4200);
  }

  /* ================================================================ stores ==
     Three, picked at startup. Everything above this block is identical
     whichever one is in use. */

  function localStore() {
    const KEY = 'imp.clock.v1';
    const read = () => { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch { return {}; } };
    return {
      mode: 'local',
      note: 'Hours stay on this phone only — no shared timesheet is set up.',
      async init() {
        const s = read();
        staff = s.staff || [];
        shifts = s.shifts || [];
      },
      async save() {
        try { localStorage.setItem(KEY, JSON.stringify({ staff, shifts })); } catch {}
      },
    };
  }

  function artifactStore(db) {
    return {
      mode: 'artifact',
      note: 'Preview only. Nothing here reaches the Google Sheet.',
      async init() {
        db.collection('staff').onSnapshot(s => {
          staff = s.docs.map(d => ({ id: d.id, ...d.data() }))
            .sort((a, b) => String(a.name).localeCompare(String(b.name)));
          render();
          maybeAskWho();
        });
        db.collection('shifts').orderBy('start', 'desc').limit(500).onSnapshot(s => {
          shifts = s.docs.map(d => ({ id: d.id, ...d.data() }));
          render();
        });
      },
      async save(change) {
        if (!change) return;
        const { id, ...body } = change.value;
        const ref = db.doc(`${change.kind === 'staff' ? 'staff' : 'shifts'}/${id}`);
        return change.remove ? ref.delete() : ref.set(body);
      },
    };
  }

  function sheetsStore(url) {
    /* Sent as text/plain on purpose: that keeps it a "simple" cross-origin
       request, so the browser skips the preflight Apps Script cannot answer.

       The reply is ignored. A POST to a web app answers with a 302 to a
       one-shot googleusercontent URL, and following that can land on a Google
       error page even though the write went through — measured against the
       live endpoint. The sheet is the truth, so `flush` re-reads to confirm. */
    async function post(body) {
      return fetch(url, { method: 'POST', body: JSON.stringify(body) });
    }
    /* Raw on purpose: it does not layer the pending queue on top, because
       `flush` has to be able to ask the sheet what is really there. */
    async function fetchAll() {
      try {
        const res = await fetch(url + '?action=load&t=' + Date.now());
        if (!res.ok) throw new Error('http ' + res.status);
        const out = await res.json();
        // doGet answers {ok:false, error} when the script throws. Treating
        // that as an empty sheet would blank the dial mid-shift and let a
        // queued delete "land" against a list that was never read.
        if (!out || out.ok === false || !Array.isArray(out.staff) || !Array.isArray(out.shifts)) {
          throw new Error((out && out.error) || 'bad reply');
        }
        linkOk = true;
        try { localStorage.setItem(CACHE_KEY, JSON.stringify({ staff: out.staff, shifts: out.shifts, at: Date.now() })); } catch {}
        return { staff: out.staff, shifts: out.shifts };
      } catch (err) {
        linkOk = false;
        throw err;
      }
    }
    /* What the sheet said last time. Without this a phone opened behind a
       garage has no names to pick from, and the queue has nothing to hold. */
    function lastSeen() {
      try {
        const c = JSON.parse(localStorage.getItem(CACHE_KEY));
        if (c && Array.isArray(c.staff) && Array.isArray(c.shifts)) return c;
      } catch {}
      return null;
    }
    return {
      mode: 'sheets',
      note: 'Hours sync to the shared Google Sheet.',
      post,
      fetchAll,
      lastSeen,
      async init() { const d = await fetchAll(); staff = d.staff; shifts = d.shifts; },
    };
  }

  async function pickStore() {
    /* The artifact viewer is sandboxed and cannot reach Google at all, so
       trying the sheet from there only produces a confusing half-state where
       the app looks fine and the spreadsheet never changes. Check for it first
       and label it a preview. */
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
         private timesheet on this phone. Start from what the sheet said last
         time, so there are names to pick and a running shift still shows; the
         queue holds anything typed while it is down, and the strip says so. */
      const c = s.lastSeen();
      if (c) { staff = c.staff; shifts = c.shifts; }
      linkOk = false;
      return s;
    }

    const s = localStore();
    await s.init();
    return s;
  }

  /* ================================================================= queue ==
     Why this exists: a driveway behind a garage in Kambah has no bars. Under
     the old build a save in that spot simply failed, and the crew would tap
     Start again and make a double. Here the change is applied on the phone,
     written to the queue, and sent when there is signal — so the clock is never
     wrong and nothing is ever entered twice. */

  const loadQueue = () => { try { queue = JSON.parse(localStorage.getItem(QUEUE_KEY)) || []; } catch { queue = []; } };
  const saveQueue = () => { try { localStorage.setItem(QUEUE_KEY, JSON.stringify(queue)); } catch {} };

  /* A fresh read from the sheet does not know about writes still waiting, so
     they are layered back on top before anything is drawn. */
  function replayQueue() {
    for (const op of queue) {
      const list = op.kind === 'staff' ? staff : shifts;
      const at = list.findIndex(x => String(x.id) === String(op.value.id));
      if (op.remove) { if (at >= 0) list.splice(at, 1); }
      else if (at >= 0) list[at] = op.value;
      else list.unshift(op.value);
    }
    shifts.sort((a, b) => Date.parse(b.start) - Date.parse(a.start));
    staff.sort((a, b) => String(a.name).localeCompare(String(b.name)));
  }

  function enqueue(change) {
    // One pending write per record: a start then a finish on the same shift
    // should send the finished row, not both halves.
    queue = queue.filter(op => !(op.kind === change.kind && String(op.value.id) === String(change.value.id)));
    queue.push(change);
    saveQueue();
  }

  /* Every write bumps this. A poll that started before a write finished must
     not land its older snapshot on top afterwards — the dial would go dark for
     twenty seconds and the crew would tap Start again. */
  let epoch = 0;

  /* Read the sheet, layer anything still waiting on top, draw. */
  async function refresh() {
    if (flushing) return;                // flush is already re-reading
    const at = epoch;
    const d = await store.fetchAll();
    if (at !== epoch) return;            // something was written meanwhile; stale
    staff = d.staff;
    shifts = d.shifts;
    replayQueue();
    render();
    maybeAskWho();
  }

  /* Did this write actually land? Presence of the id is not enough for an
     update — a finish that failed still leaves the start row there — so the
     two fields that decide pay are compared too. */
  function landedOnSheet(op, data) {
    const list = op.kind === 'staff' ? data.staff : data.shifts;
    const row = list.find(x => String(x.id) === String(op.value.id));
    if (op.remove) return !row;
    if (!row) return false;
    if (op.kind === 'staff') return true;
    const same = (a, b) => String(a || '') === String(b || '');
    return same(row.start, op.value.start) && same(row.end, op.value.end);
  }

  let flushing = false;
  async function flush() {
    if (flushing || !queue.length || mode !== 'sheets') return;
    flushing = true;
    try {
      let guard = 0;
      while (queue.length && guard++ < 50) {
        const op = queue[0];
        /* A rejected fetch here is not proof of no signal: the write can have
           landed and the redirect reply been a Google error page the browser
           refused. Either way the sheet is asked, and that read is what decides. */
        try {
          await store.post({ action: op.remove ? 'remove' : 'upsert', kind: op.kind, value: op.value });
        } catch {}
        let data;
        try { data = await store.fetchAll(); } catch { linkOk = false; break; }

        /* Dequeue by identity, never by position. While that POST was in the
           air the crew may have tapped Finish (or Undo), which replaces this op
           in the queue: shifting index 0 would throw the replacement away
           unsent. If the op is gone, it was superseded; move on to what is. */
        const at = queue.indexOf(op);
        if (at < 0) {
          staff = data.staff; shifts = data.shifts; replayQueue();
          continue;
        }
        if (!landedOnSheet(op, data)) { linkOk = false; break; }   // retried next tick

        queue.splice(at, 1);
        saveQueue();
        epoch++;
        staff = data.staff;
        shifts = data.shifts;
        replayQueue();
      }
    } finally {
      flushing = false;
      render();
      maybeAskWho();
    }
  }

  /* Every change goes through here: applied on the phone, queued, then sent. */
  function commit(change) {
    if (!change) return;
    if (mode === 'sheets') {
      enqueue(change);
      epoch++;
      render();
      flush();
    } else {
      Promise.resolve(store.save(change)).catch(() => toast('That didn’t save.', 'bad')).then(render);
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
    if (myOpen() || busy) return;
    const person = staff.find(s => s.id === me);
    const shift = {
      id: uid(),
      staffId: me,
      staffName: person ? person.name : 'Unknown',
      start: new Date(Date.now() - backMinutes * 60000).toISOString(),
      end: null,
      job: $('jobIn').value.trim(),
      hours: '',
    };
    shifts.unshift(shift);
    $('jobIn').value = '';
    backMinutes = 0;
    $('backChips').hidden = true;
    buzz(18);
    commit({ kind: 'shift', value: shift });
  }

  function finishShift() {
    const open = myOpen();
    if (!open || busy) return;
    open.end = new Date().toISOString();
    buzz([12, 40, 12]);
    commit({ kind: 'shift', value: open });
    toast(`Finished. <b>${hm(hoursOf(open, Date.now()))}</b> on the clock.`);
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
    if (!await ask(`Take ${s.name} off the crew?`, 'Their past shifts stay on the timesheet.', 'Remove')) return;
    staff = staff.filter(x => x.id !== id);
    if (me === id) setMe(null);
    commit({ kind: 'staff', value: s, remove: true });
  }

  async function deleteShift(id) {
    if (!isAdmin()) return;
    const s = shifts.find(x => x.id === id);
    if (!s) return;
    const at = new Date(s.start);
    if (!await ask('Delete this shift?',
      `${s.staffName || 'Unknown'}, ${dayLabel(dayKey(at))} at ${clock(at)}. It can’t be undone.`)) return;
    shifts = shifts.filter(x => x.id !== id);
    commit({ kind: 'shift', value: s, remove: true });
  }

  function setMe(id) {
    me = id;
    try { id ? localStorage.setItem('imp.me', id) : localStorage.removeItem('imp.me'); } catch {}
    render();
  }

  function openWho() {
    $('whoList').innerHTML = staff.length
      ? staff.map(s => {
          const open = shifts.find(x => x.staffId === s.id && !x.end);
          return `<button type="button" data-me="${s.id}" aria-pressed="${s.id === me}">${esc(s.name)}` +
            (open ? `<small>on the clock since ${clock(new Date(open.start))}</small>` : '') + '</button>';
        }).join('')
      : '<p style="grid-column:1/-1;margin:0;color:var(--slate);font-size:14px">Nobody on the crew yet. Add names under Admin.</p>';
    $('whoDlg').showModal();
  }

  /* ================================================================== ask == */
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

  /* ========================================================== log a day ==== */
  const MAX_H = 20, STEP = 0.25;
  let dDay = null, dHours = 0, dPickOpen = false;

  function openDay() {
    if (!me) return openWho();
    dDay = dayKey(new Date());
    dHours = 0;
    dPickOpen = false;
    $('dJob').value = '';
    $('pickDate').max = dDay;
    renderDay();
    $('dayDlg').showModal();
  }
  function setDayHours(h) {
    dHours = Math.min(MAX_H, Math.max(0, Math.round(h / STEP) * STEP));
    renderDay();
  }
  function spoken(h) {
    const t = Math.round(h * 60), wh = Math.floor(t / 60), wm = t % 60, bits = [];
    if (wh) bits.push(`${wh} hour${wh === 1 ? '' : 's'}`);
    if (wm) bits.push(`${wm} minutes`);
    return bits.join(' ') || 'nothing yet';
  }
  function renderDay() {
    const recent = [];
    for (let i = 0; i < 7; i++) recent.push(dayKey(CFG.daysAgo(i)));
    const older = !!dDay && !recent.includes(dDay);
    $('days').innerHTML = recent.map(k => {
      const [y, m, d] = k.split('-').map(Number);
      const short = dayLabel(k) === 'Today' || dayLabel(k) === 'Yesterday'
        ? dayLabel(k) : new Date(y, m - 1, d).toLocaleDateString('en-AU', { weekday: 'short' });
      const date = new Date(y, m - 1, d).toLocaleDateString('en-AU', { day: 'numeric', month: 'short' });
      return `<button type="button" data-day="${k}" aria-pressed="${k === dDay}"><b>${short}</b><small>${date}</small></button>`;
    }).join('') + `<button type="button" data-day="pick" aria-pressed="${older}"><b>Another</b><small>day</small></button>`;
    $('pickWrap').hidden = !(older || dPickOpen);

    $('dBig').textContent = hm(dHours);
    $('dBig').classList.toggle('zero', dHours <= 0);
    $('dSub').textContent = dHours > 0 ? spoken(dHours) : 'Tap a number, then nudge it 15 minutes at a time.';
    $('dMinus').disabled = dHours <= 0;
    $('dPlus').disabled = dHours >= MAX_H;
    for (const c of $('dQuick').children) c.setAttribute('aria-pressed', String(Number(c.dataset.h) === dHours));

    const when = dayLabel(dDay, true);
    $('dSave').disabled = dHours <= 0;
    $('dSave').textContent = dHours <= 0 ? 'How many hours?'
      : `Log ${hm(dHours)} for ${when === 'Today' || when === 'Yesterday' ? when.toLowerCase() : when}`;
  }
  function saveDay() {
    if (!me || dHours <= 0) return;
    const person = staff.find(s => s.id === me);
    const shift = CFG.dayShift({
      id: uid(), staffId: me, staffName: person ? person.name : 'Unknown',
      date: dDay, hours: dHours, job: $('dJob').value.trim(),
    });
    shifts.unshift(shift);
    shifts.sort((a, b) => Date.parse(b.start) - Date.parse(a.start));
    $('dayDlg').close();
    buzz(18);
    commit({ kind: 'shift', value: shift });
    toast(`Logged <b>${hm(shift.hours)}</b> for ${esc(dayLabel(dDay, true).toLowerCase())}.`, null, {
      label: 'Undo',
      run: () => {
        shifts = shifts.filter(x => x.id !== shift.id);
        commit({ kind: 'shift', value: shift, remove: true });
        toast('Taken back.');
      },
    });
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

    // A day logged as a number has no real times to edit, so it gets the number.
    const logged = sh ? loggedHours(sh) : 0;
    $('eTimes').hidden = !!logged;
    $('eHoursWrap').hidden = !logged;
    $('eHours').value = logged ? String(Number(logged.toFixed(2))) : '';

    $('editDlg').showModal();
  }

  function saveEdit() {
    const staffId = $('eWho').value;
    const date = $('eDate').value;
    const err = m => { const p = $('eErr'); p.textContent = m; p.hidden = false; };
    if (!staffId) return err('Pick who worked it.');
    const person = staff.find(s => s.id === staffId);

    if (!$('eHoursWrap').hidden) {
      if (!date) return err('A shift needs a date.');
      const h = parseFloat($('eHours').value);
      if (!Number.isFinite(h) || h <= 0) return err('How many hours were worked?');
      if (h > 20) return err('That is over 20 hours. Check the number.');
      const logged = CFG.dayShift({
        id: editingId || uid(), staffId, staffName: person ? person.name : 'Unknown',
        date, hours: h, job: $('eJob').value.trim(),
      });
      const at = shifts.findIndex(s => s.id === logged.id);
      if (at >= 0) shifts[at] = logged; else shifts.unshift(logged);
      shifts.sort((a, b) => Date.parse(b.start) - Date.parse(a.start));
      $('editDlg').close();
      return commit({ kind: 'shift', value: logged });
    }

    const st = $('eStart').value, en = $('eEnd').value;
    if (!date || !st) return err('A shift needs a date and a start time.');
    const start = new Date(`${date}T${st}`);
    let end = en ? new Date(`${date}T${en}`) : null;
    // A finish before the start means the shift ran past midnight.
    if (end && end <= start) end.setDate(end.getDate() + 1);
    if (end && end - start > 20 * 3600000) return err('That shift is over 20 hours. Check the times.');

    const value = {
      id: editingId || uid(), staffId, staffName: person ? person.name : 'Unknown',
      start: start.toISOString(), end: end ? end.toISOString() : null,
      job: $('eJob').value.trim(), hours: '',
    };
    const i = shifts.findIndex(s => s.id === value.id);
    if (i >= 0) shifts[i] = value; else shifts.unshift(value);
    shifts.sort((a, b) => Date.parse(b.start) - Date.parse(a.start));
    $('editDlg').close();
    commit({ kind: 'shift', value });
  }

  /* =================================================================== CSV == */
  const weekShifts = (from, to) => shifts
    .filter(s => { const t = Date.parse(s.start); return t >= from.getTime() && t < to.getTime(); })
    .slice().sort((a, b) => Date.parse(a.start) - Date.parse(b.start));

  async function exportCsv() {
    if (!isAdmin()) return;
    const from = weekStart(weekOffset), to = CFG.weekEnd(weekOffset);
    const rows = weekShifts(from, to);
    if (!rows.length) return toast('No shifts in that week to export.', 'bad');

    const cell = v => `"${String(v == null ? '' : v).replace(/"/g, '""')}"`;
    // A note beginning with = + - @ is a formula to Excel. A leading space
    // keeps it text and is invisible; only the free-text columns need it.
    const text = v => { const s = String(v == null ? '' : v); return /^[=+\-@\t\r]/.test(s) ? ' ' + s : s; };
    const now = Date.now();
    const lines = [['Date', 'Who', 'Start', 'Finish', 'Hours', 'Rate', 'Pay', 'Job'].map(cell).join(',')];
    for (const s of rows) {
      const h = hoursOf(s, now), rate = rateOf(s.staffId), d = new Date(s.start);
      lines.push([
        d.toLocaleDateString('en-AU'), text(s.staffName || ''),
        loggedHours(s) ? 'logged' : clock(d),
        loggedHours(s) ? 'logged' : s.end ? clock(new Date(s.end)) : 'still on',
        h.toFixed(2), rate ? rate.toFixed(2) : '', rate ? (h * rate).toFixed(2) : '', text(s.job || ''),
      ].map(cell).join(','));
    }
    const csv = lines.join('\r\n');
    const filename = `imperium-hours-${dayKey(from)}.csv`;

    // In the artifact viewer a plain download link is inert, so ask the host.
    try {
      const dl = typeof claude !== 'undefined' && claude.use ? await claude.use('downloads') : null;
      if (dl) { await dl.save({ filename, data: csv }); return toast(`Saved ${filename}.`); }
    } catch { return toast('The download was cancelled.', 'bad'); }

    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast(`Saved ${filename}.`);
  }

  /* ================================================================== dial == */
  const ARC_LEN = 2 * Math.PI * 88;
  let tickEls = [];

  function buildDial() {
    const g = $('ticks');
    for (let i = 0; i < 60; i++) {
      const major = i % 5 === 0;
      const l = document.createElementNS(SVG, 'line');
      l.setAttribute('x1', '120'); l.setAttribute('y1', major ? '13' : '16');
      l.setAttribute('x2', '120'); l.setAttribute('y2', major ? '27' : '24');
      l.setAttribute('transform', `rotate(${i * 6} 120 120)`);
      l.setAttribute('class', 'tick' + (major ? ' major' : ''));
      g.appendChild(l);
      tickEls.push(l);
    }
  }

  /* The one piece of motion the app does on its own: on Start the bezel lights
     tick by tick around the face. On Finish it goes out the other way, faster,
     because an exit should never take as long as an arrival. */
  function ignite(on) {
    if (reduced) {
      tickEls.forEach(t => t.classList.toggle('lit', on));
      return;
    }
    const step = on ? 9 : 4;
    tickEls.forEach((t, i) => {
      t.style.transitionDelay = ((on ? i : 59 - i) * step) + 'ms';
      t.classList.toggle('lit', on);
    });
    setTimeout(() => tickEls.forEach(t => { t.style.transitionDelay = ''; }), 60 * step + 400);
  }

  // Each digit is a 0-9 strip behind a one-character window, so a change rolls.
  let readShape = '';
  function setRead(text) {
    const read = $('read');
    const shape = text.replace(/\d/g, '#');
    if (shape !== readShape) {
      readShape = shape;
      // The strips are a picture of a counter; a screen reader gets a label.
      read.innerHTML = '<span class="strips" aria-hidden="true">' + [...text].map(ch => /\d/.test(ch)
        ? '<span class="dg"><span class="roll">' +
          '0123456789'.split('').map(d => `<i>${d}</i>`).join('') + '</span></span>'
        : `<span class="sep">${ch}</span>`).join('') + '</span>';
    }
    const strips = read.querySelectorAll('.dg .roll');
    let i = 0;
    for (const ch of text) if (/\d/.test(ch)) strips[i++].style.setProperty('--n', ch);
  }

  /* The readout is the only thing on a timer, and it never writes anything. */
  function tick() {
    const now = Date.now();
    const open = myOpen();
    const ms = open ? now - Date.parse(open.start) : 0;
    setRead(hms(ms));
    const label = !open ? 'Not on the clock'
      : ms < 60000 ? 'Just started, on the clock'
      : spoken(ms / 3600000) + ' on the clock';
    if ($('read').getAttribute('aria-label') !== label) $('read').setAttribute('aria-label', label);
    const p = Math.min(1, ms / (FULL_DAY_H * 3600000));
    $('arc').setAttribute('stroke-dashoffset', String(ARC_LEN * (1 - p)));
    for (const el of document.querySelectorAll('[data-el]')) {
      const s = shifts.find(x => String(x.id) === el.dataset.el);
      if (s) el.textContent = hm(hoursOf(s, now));
    }
  }

  /* ================================================================= views == */
  function syncTabs() {
    const order = isAdmin() ? ['clock', 'sheet', 'admin'] : ['clock', 'sheet'];
    $('tabs').style.setProperty('--tabs', String(order.length));
    $('tabs').style.setProperty('--tab', String(Math.max(0, order.indexOf(tab))));
    for (const b of $('tabs').children) {
      b.setAttribute('aria-selected', String(b.dataset.tab === tab));
      if (b.dataset.tab === 'admin') b.hidden = !isAdmin();
    }
  }

  function showTab(name) {
    if (name === 'admin' && !isAdmin()) name = 'clock';   // never, whatever is on screen
    if (name === tab) return;
    const cur = $('v-' + tab), next = $('v-' + name);
    tab = name;
    syncTabs();

    cur.setAttribute('data-leaving', '');
    setTimeout(() => {
      cur.hidden = true;
      cur.removeAttribute('data-leaving');
      next.hidden = false;
      next.setAttribute('data-leaving', '');
      scrollTo({ top: 0 });
      requestAnimationFrame(() => requestAnimationFrame(() => next.removeAttribute('data-leaving')));
      render();
    }, reduced ? 0 : 150);
  }

  /* ================================================================ render == */
  function render() {
    const now = Date.now();
    const open = myOpen();
    const person = staff.find(s => s.id === me);

    $('whoName').textContent = person ? person.name : 'Who are you?';

    const running = !!open;
    document.body.toggleAttribute('data-running', running);
    if (running !== wasRunning) { ignite(running); wasRunning = running; }

    $('stateLabel').textContent = running ? 'On the clock' : 'Not on the clock';
    $('jobWrap').hidden = running;
    $('quick').hidden = running || !me;
    if (running) $('backChips').hidden = true;

    if (running) {
      $('since').textContent = `Started ${clock(new Date(open.start))}` + (open.job ? ` · ${open.job}` : '');
    } else if (!staff.length) {
      $('since').textContent = 'Add the crew under Admin to get started.';
    } else if (!me) {
      $('since').textContent = 'Pick your name to get started.';
    } else if (backMinutes > 0) {
      $('since').textContent = `Will count from ${clock(new Date(now - backMinutes * 60000))}.`;
    } else {
      $('since').textContent = 'Ready when you are.';
    }

    const btn = $('mainBtn');
    btn.textContent = running ? 'Finish shift' : 'Start shift';
    btn.classList.toggle('stop', running);
    btn.disabled = busy || (!running && !staff.length);

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
    $('kToday').textContent = me ? 'Today' : 'Today, all';
    $('kWeek').textContent = me ? 'Pay week' : 'Week, all';
    $('sToday').innerHTML = hm(tH) + '<small>h</small>';
    $('sWeek').innerHTML = hm(wH) + '<small>h</small>';
    const onNow = shifts.filter(s => !s.end).length;
    $('sOn').textContent = String(onNow);
    $('stOn').toggleAttribute('data-live', onNow > 0);
    $('shiftScope').textContent = shifts.length ? 'Everyone, newest first' : '';

    /* Who else is working. Rebuilt here; the numbers are refreshed by tick(),
       so the list is not thrown away and rebuilt once a second. */
    const live = shifts.filter(s => !s.end).sort((a, b) => Date.parse(a.start) - Date.parse(b.start));
    const box = $('onNow');
    box.hidden = !live.length;
    if (live.length) {
      box.innerHTML = '<h3 class="sub">On the clock now</h3>' + live.map(s =>
        `<div class="live-row"><span class="pip"></span>
          <b>${esc(s.staffName || 'Unknown')}</b>
          <span class="at">since ${clock(new Date(s.start))}</span>
          <span class="el tnum" data-el="${s.id}">${hm(hoursOf(s, now))}</span>
        </div>`).join('');
    }

    // Where the hours are going, said out loud whenever it is not the sheet.
    const link = $('linkNote');
    const waiting = queue.length;
    if (mode === 'sheets' && !linkOk) {
      link.hidden = false;
      link.dataset.tone = 'bad';
      link.innerHTML = waiting
        ? `<b>No signal.</b> ${waiting} change${waiting === 1 ? '' : 's'} saved on this phone, waiting to sync. Tap to retry.`
        : '<b>No signal.</b> Showing what the timesheet last said. Anything you do is kept and sent later. Tap to retry.';
    } else if (mode === 'sheets' && waiting) {
      link.hidden = false;
      link.dataset.tone = 'warn';
      link.innerHTML = `<b>Syncing.</b> ${waiting} change${waiting === 1 ? '' : 's'} on the way to the sheet.`;
    } else if (mode !== 'sheets') {
      link.hidden = false;
      link.dataset.tone = 'warn';
      link.innerHTML = mode === 'artifact'
        ? '<b>Preview.</b> Hours here do not reach the Google Sheet.'
        : '<b>This phone only.</b> Hours are not shared with anyone else.';
    } else {
      link.hidden = true;
    }
    $('storeNote').textContent = store ? store.note : '';

    syncTabs();

    renderShifts(now);
    if (isAdmin()) { renderWeek(now); renderStaff(); }
  }

  function renderShifts(now) {
    const host = $('shifts');
    if (!shifts.length) {
      host.innerHTML = '<div class="empty">No shifts yet. Start one on the Clock and it turns up here.</div>';
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
              ${s.job ? `<div class="job-note">${esc(s.job)}</div>` : ''}
            </div>
            <div class="dur tnum">${hm(hoursOf(s, now))}</div>
            ${isAdmin() ? `<div class="acts">
              <button class="btn" data-edit="${s.id}" type="button">Edit</button>
              <button class="btn danger" data-del="${s.id}" type="button">Delete</button>
            </div>` : ''}
          </div>`;
        }).join('') + '</div>');
    }
    host.innerHTML = out.join('');
  }

  function renderWeek(now) {
    const from = weekStart(weekOffset), to = CFG.weekEnd(weekOffset);
    const fmt = t => t.toLocaleDateString('en-AU', { weekday: 'short', day: 'numeric', month: 'short' });
    $('weekRange').textContent = `${fmt(from)} – ${fmt(CFG.addDays(to, -1))}`;

    const rows = weekShifts(from, to);
    const per = new Map();
    for (const s of rows) {
      const k = s.staffId || 'unknown';
      const cur = per.get(k) || { name: s.staffName || 'Unknown', h: 0 };
      cur.h += hoursOf(s, now);
      per.set(k, cur);
    }
    const host = $('weekTotals');
    if (!per.size) {
      host.innerHTML = `<div class="empty">Nothing logged ${weekOffset === 0 ? 'this pay week' : 'that pay week'} yet.</div>`;
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
    host.innerHTML = body + `<div class="who-row total"><b>Everyone</b>
      <span class="hrs tnum">${hm(totH)}</span>
      <span class="pay tnum">${totP ? money(totP) : '—'}</span></div>`;
  }

  function renderStaff() {
    $('staffList').innerHTML = staff.length
      ? staff.map(s => `<div class="staff-row"><b>${esc(s.name)}</b>
          <span class="rate tnum">${rateOf(s.id) ? money(rateOf(s.id)) + '/h' : 'no rate'}</span>
          <button class="btn danger" data-rmstaff="${s.id}" type="button">Remove</button></div>`).join('')
      : '<div class="empty">Nobody on the crew yet. Add a name below.</div>';
  }

  /* ================================================================== gate == */
  function paintDots() {
    const dots = $('dots').children;
    for (let i = 0; i < dots.length; i++) dots[i].toggleAttribute('data-on', i < entry.length);
  }

  /* The code is asked for on every launch. It is kept in sessionStorage, which
     survives switching to another app and back but not a fresh open, so the
     lock screen is what the crew see first. A running shift is not touched by
     any of this: it lives in the sheet, and the dial picks it straight back up
     once the right name is chosen. */
  function setRole(next) {
    role = next;
    try {
      if (next) sessionStorage.setItem('imp.role', next);
      else sessionStorage.removeItem('imp.role');
    } catch {}
    $('gate').hidden = !!next;
    $('app').hidden = !next;
    if (!next) {
      askedWho = false;
      entry = ''; paintDots();
      $('gateSub').textContent = 'Enter your code';
      $('gateSub').className = 'gate-sub';
      for (const d of document.querySelectorAll('dialog[open]')) d.close();
      toast('');                            // an Undo must not outlive the person
    }
    if (tab === 'admin' && !isAdmin()) {
      tab = 'clock';
      $('v-admin').hidden = true;
      $('v-clock').hidden = false;
    }
    render();
    if (next) maybeAskWho();
  }

  function key(k) {
    const sub = $('gateSub');
    if (k === 'clear') { entry = ''; paintDots(); return; }
    if (k === 'back') { entry = entry.slice(0, -1); paintDots(); return; }
    if (entry.length >= 4) return;
    entry += k;
    buzz(8);
    paintDots();
    if (entry.length < 4) return;

    if (entry === ADMIN_CODE) return setRole('admin');
    if (entry === STAFF_CODE) return setRole('staff');

    sub.textContent = 'That code isn’t right.';
    sub.className = 'gate-sub bad';
    buzz([30, 60, 30]);
    const box = $('gateIn');
    box.setAttribute('data-wrong', '');
    setTimeout(() => {
      box.removeAttribute('data-wrong');
      entry = ''; paintDots();
      sub.textContent = 'Enter your code';
      sub.className = 'gate-sub';
    }, 620);
  }

  /* Asked once per unlock, whoever was picked last time: phones get handed
     around, and "it stayed as the last person" was the complaint. The last name
     is still highlighted, so the common case is one tap. Waits for the crew
     list if it has not arrived yet. */
  function maybeAskWho() {
    if (askedWho || !role || !staff.length || document.querySelector('dialog[open]')) return;
    askedWho = true;
    openWho();
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
  $('prevWeek').addEventListener('click', () => { weekOffset--; render(); });
  $('nextWeek').addEventListener('click', () => { weekOffset = Math.min(0, weekOffset + 1); render(); });
  $('lockBtn').addEventListener('click', () => setRole(null));

  $('askYes').addEventListener('click', () => closeAsk(true));
  $('askNo').addEventListener('click', () => closeAsk(false));
  $('askDlg').addEventListener('close', () => closeAsk(false));   // Esc means no

  $('dayLink').addEventListener('click', openDay);
  $('dCancel').addEventListener('click', () => $('dayDlg').close());
  $('dSave').addEventListener('click', saveDay);
  $('dMinus').addEventListener('click', () => setDayHours(dHours - STEP));
  $('dPlus').addEventListener('click', () => setDayHours(dHours + STEP));
  $('pickDate').addEventListener('change', e => { if (e.target.value) { dDay = e.target.value; renderDay(); } });

  $('backLink').addEventListener('click', () => {
    const chips = $('backChips');
    chips.hidden = !chips.hidden;
    if (!chips.hidden) applyBack(backMinutes);
  });

  $('tabs').addEventListener('click', e => {
    const b = e.target.closest('[data-tab]');
    if (b) showTab(b.dataset.tab);
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
    if (mode !== 'sheets') return;
    toast('Reconnecting…');
    try { await refresh(); await flush(); toast(''); }
    catch { toast('Still can’t reach the timesheet.', 'bad'); }
    render();
  });

  // One delegated listener rather than rebinding every row on each render.
  document.addEventListener('click', e => {
    const t = e.target.closest('[data-edit],[data-del],[data-rmstaff],[data-me],[data-back],[data-day],[data-h]');
    if (!t) return;
    if (t.dataset.edit) openEdit(t.dataset.edit);
    else if (t.dataset.del) deleteShift(t.dataset.del);
    else if (t.dataset.rmstaff) removeStaff(t.dataset.rmstaff);
    else if (t.dataset.me) { setMe(t.dataset.me); $('whoDlg').close(); }
    else if (t.dataset.back !== undefined) {
      const m = Number(t.dataset.back);
      if (m === -1) openTimePick(); else applyBack(m);
    } else if (t.dataset.day === 'pick') {
      dPickOpen = true; renderDay();
      $('pickDate').focus();
      if ($('pickDate').showPicker) { try { $('pickDate').showPicker(); } catch {} }
    } else if (t.dataset.day) { dDay = t.dataset.day; dPickOpen = false; renderDay(); }
    else if (t.dataset.h) setDayHours(Number(t.dataset.h));
  });

  // Anything that means "there might be signal again" gets a flush.
  addEventListener('online', () => { flush(); });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden || mode !== 'sheets') return;
    refresh().catch(() => render()).then(flush);
  });

  /* =================================================================== boot = */
  (async () => {
    buildDial();
    loadQueue();
    try {
      me = localStorage.getItem('imp.me');
      const saved = sessionStorage.getItem('imp.role');
      if (saved === 'staff' || saved === 'admin') role = saved;
    } catch {}
    $('gate').hidden = !!role;
    $('app').hidden = !role;
    paintDots();
    setRead('0:00:00');
    setInterval(tick, 1000);
    render();                              // so nothing admin-only is tappable while the sheet loads

    // The shell is cached, so the app opens with no signal at all. The queue
    // is no use if the page that holds it cannot load in a dead spot.
    if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});

    store = await pickStore();
    mode = store.mode;
    replayQueue();

    // The crew Pat named, so nobody has to set the app up before using it. Only
    // when the store is actually reachable — seeding into a sheet we cannot see
    // would make five duplicates the moment it came back.
    if (mode === 'local' && !staff.length && DEFAULT_CREW.length) {
      staff = DEFAULT_CREW.map(name => ({ id: uid(), name, rate: DEFAULT_RATE }))
        .sort((a, b) => a.name.localeCompare(b.name));
      await store.save();
    }

    // "Pick a time" only makes sense once the chips exist.
    const chips = $('backChips');
    if (chips && !chips.querySelector('[data-back="-1"]')) {
      const b = document.createElement('button');
      b.className = 'chip';
      b.type = 'button';
      b.dataset.back = '-1';
      b.textContent = 'Pick a time';
      chips.appendChild(b);
    }

    if (me && staff.length && !staff.some(s => s.id === me)) setMe(null);
    render();
    maybeAskWho();
    flush();

    if (mode === 'sheets') {
      setInterval(() => { refresh().catch(() => render()).then(flush); }, POLL_MS);
    }
  })();
})();
