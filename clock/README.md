# Imperium Clock

The rebuild of the timesheet. One page, three tabs, no build step, no framework.

    index.html            the whole app — clock, timesheet, admin
    app.js                everything it does
    config.js             the endpoint, the codes, the rates, the pay week
    tokens.css            the palette and type scale
    fonts.css, fonts/     the two typefaces, served from here rather than Google
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

### Works with no signal

Every change is applied on the phone, written to a queue, and sent when there is
service. The queue survives the app being closed.

This is the one thing that matters most in a driveway behind a garage. Under the
old build a save in a dead spot simply failed, and the natural response — tap
Start again — created a double. Here the clock is right immediately, the strip
at the top says how many changes are waiting, and they go up the moment there
are bars.

Because an Apps Script POST can answer with what looks like an error **even when
the write succeeded**, nothing trusts the reply: after every send the sheet is
re-read and the row is looked for. The sheet is the truth.

### The two codes

| Code | Who | What they get |
| --- | --- | --- |
| **0000** | The crew | Clock, Timesheet. Their name, their hours, the shift list. |
| **1906** | Admin | All of that, plus the Admin tab: pay, crew, rates, edit, delete, CSV. |

On 0000 the Admin tab is not rendered at all, and the checks are on the actions
as well as the buttons. **It is still a lid, not a lock** — both codes are in
the page. The link is the real key; only give it to people who should have it.

Change them in `config.js`.

### Things worth knowing

- Pay weeks run **Wednesday to Tuesday**.
- Times come from each phone's own clock, so keep phones on automatic time.
- A finish earlier than the start is read as a shift that ran past midnight.
- Anything over 20 hours is rejected as a typo.
- Delete asks first, in a panel drawn by the page — never the browser's own
  pop-up, which an embedded viewer blocks and silently answers "no".

---

## Putting it up

Plain static files, so any host works. On Vercel: **Add New → Project** → import
the repo → set **Root Directory** to `clock` → Deploy. `vercel.json` already
sets `noindex`.

Then send the crew the link and one line:

> **iPhone:** open in Safari → Share → *Add to Home Screen*.
> **Android:** open in Chrome → ⋮ → *Add to Home screen*.

It opens full screen with the Imperium mark, and remembers who they are.
