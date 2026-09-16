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
  Edit or delete any of them.
- **Admin.** Hours and pay per person per week, with previous/next week. Add or
  remove crew and set rates. Add a shift nobody clocked. Download the week as CSV.

### The admin PIN

Under Admin you can set a 4-digit PIN. After that, opening Admin asks for it, so
the crew can still clock on and off but won't be poking at pay figures.

**It is a lid, not a lock.** Anyone with the link can open the page, and the
hours live in a Google Sheet that the web app reads without a password. Treat the
link as the actual key and only give it to people who should have it. If you need
real access control, that's a different build with proper logins.

---

## Things worth knowing

- Times come from each phone's own clock, so keep phones on automatic time.
- Payroll weeks run **Monday to Sunday**, the Australian convention.
- A finish time earlier than the start is read as a shift that ran past midnight.
- Anything over 20 hours is rejected as a typo.
- The Sheet is the record. If something looks wrong, fix it in the Sheet or with
  *Edit* on the shift — both end up in the same place.
