# Imperium Clock

The rebuild of the timesheet. One page, three tabs, no build step, no framework.

    index.html            the whole app — clock, timesheet, admin
    app.js                everything it does
    config.js             the endpoint, the codes, the rates, the pay week, date maths
    tokens.css            the palette and type scale
    fonts.css, fonts/     the two typefaces, served from here rather than Google
    sw.js                 caches the app itself, so it opens with no signal
    apps-script.gs        the Google Sheets backend
    manifest.webmanifest  what makes "Add to Home Screen" open it like an app

**It writes to the same Google Sheet as `../hours`** — same endpoint, same rows.
Both can run at once while you decide which to keep. Nothing has to be moved.

---

## Why it looks like that

The old page was a near-black screen with one bright blue accent. That is the
look every dark app defaults to, which is exactly why it read as generic.

This one is built as an **instrument** instead — the cluster of a good car at
night. The ground is warm graphite rather than blue-black, the bezel is brushed
metal, and time runs in **amber**, because that is the colour of a gauge that is
live. Imperium blue is still there, kept small, doing identity work: the tab
indicator, focus rings, links.

One element is allowed to be bold — the dial — and everything around it is
deliberately quiet. There is exactly **one** piece of motion the app performs on
its own, and it fires on the press of Start: the bezel lights tick by tick
around the face, roughly half a second, then stops. Finishing puts it out the
other way, faster, because an exit should never take as long as an arrival.
Nothing fades up on scroll.

The readout is a row of 0–9 strips behind one-character windows, so a change
rolls the way a mechanical counter does. The window is 0.45em wide because that
is what a tabular digit actually measures in Big Shoulders at weight 700.

---

## What it does

- **Start / Finish.** Two taps, and the dial tells you which state you are in
  from across a driveway.
- **Forgot to press start?** Start the shift 15, 30, 45, 60, 90 or 120 minutes
  ago, or at a time you pick.
- **Log a whole day.** For the evening nobody pressed anything. Pick the day,
  set the hours, save. **No times are recorded**, because there weren't any — it
  shows as *"Hours logged, no times"* and counts towards the week like any other
  shift.
- **On the clock now.** Who else is working, and for how long.
- **Timesheet.** Everyone, newest first, grouped by day with a daily total.
- **Admin.** Hours and pay per person per pay week, previous/next week, the CSV,
  crew and rates, add a past shift, edit or delete anything.

### Works with no signal — all the way from a cold start

Three things make that true, and all three are needed:

1. **The app itself is cached** (`sw.js`), so tapping the icon in a dead spot
   opens the lock screen instead of Safari's "no internet" page.
2. **The phone remembers what the sheet last said** — the crew list and the
   shifts — so there are names to pick and a running shift still shows.
3. **Every change goes into a queue** on the phone and is sent when there is
   service. The queue survives the app being closed.

So: no bars, open the app, unlock, pick your name, tap Start. The dial runs. The
strip at the top says *No signal — showing what the timesheet last said*, and
how many changes are waiting. The moment there are bars they go up.

Under the old build a save in a dead spot simply failed, and the natural
response — tap Start again — created a double.

Two rules keep the queue honest. Because an Apps Script POST can answer with
what looks like an error **even when the write succeeded**, nothing trusts the
reply: after every send the sheet is re-read and the row is checked — its start
*and* finish, not just that it exists. And the queue is emptied by identity,
never by position, so a Finish tapped while the Start is still in the air is
never thrown away.

Only the app's own files are ever cached. The sheet is always read live.

### The lock screen, and who is holding the phone

**Every fresh open starts on the keypad.** The code is kept only for the
session, so switching to Messages and back does not ask again, but opening the
app from the home screen does. A running shift is never touched by any of this:
it lives in the sheet, and the dial picks it straight back up.

**The name is asked once per unlock.** Phones get handed around, so the app
never silently stays as the last person. The last name is highlighted — one tap
for the common case — and the picker says who is already on the clock and since
when. The lock in the header is there for everyone, not just admin.

| Code | Who | What they get |
| --- | --- | --- |
| **0000** | The crew | Clock, Timesheet. Their name, their hours, the shift list. |
| **1906** | Admin | All of that, plus the Admin tab: pay, crew, rates, edit, delete, CSV. |

On 0000 the Admin tab is not in the page at all — not before the sheet loads,
not after — and the checks are on the actions as well as the buttons. **It is
still a lid, not a lock** — both codes are in the page. The link is the real
key; only give it to people who should have it.

Change them in `config.js`.

### Things worth knowing

- Pay weeks run **Wednesday to Tuesday**. Week edges are calendar days, not
  7×24 hours, so the two nights a year Canberra changes clocks never double-count
  or drop a shift.
- Times come from each phone's own clock, so keep phones on automatic time.
- A finish earlier than the start is read as a shift that ran past midnight.
- Anything over 20 hours is rejected as a typo.
- Delete asks first, in a panel drawn by the page — never the browser's own
  pop-up, which an embedded viewer blocks and silently answers "no".
- A job note that starts with `=` is written to the sheet as text, not a
  formula, and the CSV does the same. Nothing typed into the app can run
  anything in the spreadsheet.
- If the same shift is edited from two phones while one of them is offline, the
  last one to reach the sheet wins. Rare, and it is visible on the timesheet.

### After redeploying the Apps Script

`apps-script.gs` now writes every text cell as text. It works fine without
redeploying — this only matters for notes beginning with `=` or that look like
numbers. Extensions → Apps Script → paste the file over → Save → **Deploy →
Manage deployments → edit → New version → Deploy**. The URL stays the same.

---

## Putting it up

Plain static files, so any host works. On Vercel: **Add New → Project** → import
the repo → set **Root Directory** to `clock` → Deploy. `vercel.json` already
sets `noindex`.

Then send the crew the link and one line:

> **iPhone:** open in Safari → Share → *Add to Home Screen*.
> **Android:** open in Chrome → ⋮ → *Add to Home screen*.

It opens full screen with the Imperium mark, on the keypad, and asks who is holding it.
