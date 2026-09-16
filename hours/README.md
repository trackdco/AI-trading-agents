# Imperium Timesheets

Clock on, clock off, see everyone's hours. One page, no build step, no framework.

    index.html            the page
    app.js                everything it does, tokens and config at the top
    apps-script.gs        the Google Sheets backend
    manifest.webmanifest  what makes "Add to Home Screen" open it like an app
    logo.webp, icon-*.png brand assets, copied from the main site

The crew is pre-loaded — **Lucas, AJ, Nick, Gus, Ananth, all on $27/hour** — so
nobody has to set anything up before using it. Change any of that under Admin.

---

## Where the hours are kept

The page picks one of three, in this order, at startup:

| | When | What it means |
| --- | --- | --- |
| **Google Sheet** | `ENDPOINT` is filled in at the top of `app.js` | **The real one.** Every phone shares one timesheet, no accounts, and the hours land in a spreadsheet you can read and fix. |
| claude.ai artifact | published as an artifact | Syncs, but only for people signed in to your Claude workspace. Fine for testing, no good for the crew. |
| This phone only | neither of the above | Nothing is lost, but nothing is shared. |

It works out of the box on the third one. **Do the Sheets setup and it becomes
the real thing.**

---

## Sheets setup — about five minutes, free, no card

1. Go to **sheets.new**. Name it *Imperium Hours*.
2. **Extensions → Apps Script**. Delete whatever is in the editor.
3. Paste the whole of `apps-script.gs` in. Save (the disk icon).
4. **Deploy → New deployment**. Click the gear next to "Select type" and choose
   **Web app**.
   - *Execute as*: **Me**
   - *Who has access*: **Anyone**
   - **Deploy**, then approve the permission prompts. Google will warn you the
     app is unverified — it's your own script, so click through *Advanced →
     Go to (project name)*.
5. Copy the **Web app URL**. It ends in `/exec`.
6. Open `app.js`, find `const ENDPOINT = '';` on line 20, and paste the URL
   between the quotes.

Deploy the site again and every phone shares one timesheet. Three tabs appear in
the Sheet on first use — Shifts, Staff, Settings — and you can edit them by hand.

**If you ever change the script**, use *Deploy → Manage deployments → edit →
New version*, or the URL keeps serving the old code.

---

## Putting it on the crew's phones

Host it somewhere first. It's plain static files, so anywhere works. On Vercel:
import the folder, add a domain like `hours.imperiumdetailing.com.au`, done.
`vercel.json` already sets `noindex` so it never turns up in a search.

Then send them the link and one line:

> **iPhone:** open the link in Safari → Share button → *Add to Home Screen*.
> **Android:** open in Chrome → ⋮ menu → *Add to Home screen*.

It opens full screen with the Imperium mark as its icon, and remembers who they
are, so after the first time it's: open, tap **Start shift**.

---

## What it does

- **Big live clock.** Counts while a shift runs; the card lights green.
- **Forgot to press start?** Tap it and pick *15 min ago*, *30*, *45*, *1 hour*,
  *1.5*, *2*, or *Pick a time*. The shift starts in the past, so the hours are
  right even when nobody remembered at the time.
- **Your today / your week / on now.** "On now" is how many are still clocked on.
- **Shifts list.** Everyone, newest first, grouped by day with a daily total.
  Everyone can read it; only admin can change it.
- **Admin only.** Hours and pay per person per week, with previous/next week.
  **Edit or delete any shift.** Add or remove crew and set rates. Add a shift
  nobody clocked. Download the week as CSV.

### The two codes

The page opens on a keypad. There are two codes, set at the top of `app.js`:

| Code | Who | What they can do |
| --- | --- | --- |
| **0000** | The crew | Pick their name, clock on and off, backdate a start, read the shift list. |
| **1906** | Admin | All of that, plus **edit and delete any shift**, add and remove crew, set rates, add a past shift, see hours and pay per person, download the CSV. |

The code is remembered on the phone, so it's asked once. **Sign out** at the
bottom of the page clears it — use that to hand a phone over, or to switch
between crew and admin on your own.

On 0000 there are no Edit or Delete buttons on a shift and no Admin panel at all.
Those checks are on the actions themselves, not just the buttons, so hiding them
is not the only thing stopping a staff member deleting a shift.

**It is a lid, not a lock.** Both codes sit in the page, so anyone who knows how
to view source can read them, and anyone with the link can open the page at all.
It keeps the crew out of the pay figures; it is not security. **The link is the
real key** — only give it to people who should have it. Real access control means
proper accounts and a login server, which is a different build.

To change either code, edit `STAFF_CODE` and `ADMIN_CODE` near the top of
`app.js` and deploy again.

---

## Things worth knowing

- Times come from each phone's own clock, so keep phones on automatic time.
- Payroll weeks run **Monday to Sunday**, the Australian convention.
- A finish time earlier than the start is read as a shift that ran past midnight.
- Anything over 20 hours is rejected as a typo.
- The Sheet is the record. If something looks wrong, fix it in the Sheet or with
  *Edit* on the shift — both end up in the same place.
