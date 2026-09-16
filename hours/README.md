# Imperium Timesheets

Clock on, clock off, see everyone's hours. One page, no build step, no framework.

    index.html            the page
    app.js                everything it does, tokens and config at the top
    apps-script.gs        the Google Sheets backend
    manifest.webmanifest  what makes "Add to Home Screen" open it like an app
    logo.webp, icon-*.png brand assets, copied from the main site

The crew is already in the Sheet — **Lucas, AJ, Nick, Gus, Ananth, all on
$27/hour** — so nobody has to set anything up before using it. Change any of that
under Admin.

---

## Where the hours are kept

The page picks one of three, in this order, at startup:

| | When | What it means |
| --- | --- | --- |
| **Google Sheet** | the page is on a normal web address | **The real one.** Every phone shares one timesheet, no accounts, and the hours land in a spreadsheet you can read and fix. |
| claude.ai artifact | opened as a Claude artifact | A **preview**. The artifact viewer is sandboxed and cannot reach Google at all, so nothing typed there ever reaches the Sheet. |
| This phone only | `ENDPOINT` left empty | Nothing is lost, but nothing is shared. |

The page now says which one it is on, in a strip under the header, whenever it
is not the Sheet. That strip exists because the preview used to look identical
to the real thing while the spreadsheet stayed empty — the app must never be
quiet about where the hours are going.

**So: the Sheet only fills up once the page is hosted at a real address.** Steps
are below.

---

## Sheets setup — **already done**

`ENDPOINT` is filled in and the deployed script was tested against live on
16 Sep 2026: a read returned JSON, a write landed in the sheet, a delete removed
it again, and the five crew names were written into the Staff tab. Nothing
further is needed unless the sheet is ever rebuilt.

One thing that testing turned up, worth knowing before anyone "fixes" it: a POST
to an Apps Script web app answers with a 302 to a one-shot
`script.googleusercontent.com` URL, and following that can produce a Google error
page **even though the write succeeded**. So `post()` deliberately ignores the
reply and `save()` re-reads the sheet to confirm the change landed. The sheet is
the truth, never the response body.

<details>
<summary>How it was set up, if it ever needs rebuilding</summary>

### About five minutes, free, no card

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

</details>

---

## Putting it on the crew's phones

### 1. Give it an address

It's plain static files, so any host works. On Vercel, which already runs the
main site:

1. **vercel.com** → *Add New* → *Project* → import this repository.
2. Set **Root Directory** to `hours`. Leave the framework as *Other*.
3. **Deploy.** You get a link straight away.
4. Optional: *Settings → Domains* → add `hours.imperiumdetailing.com.au`.

`vercel.json` already sets `noindex`, so it never turns up in a search.

Open that link once and the strip under the header disappears — that is the page
telling you it is talking to the Sheet.

### 2. Send the crew the link

One line to send with it:

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

Delete asks first, in a panel drawn by the page. It deliberately does **not**
use the browser's own pop-up: inside an embedded viewer that pop-up is blocked
and simply answers "no", which made Delete look broken.

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
- Pay weeks run **Wednesday to Tuesday**. The admin panel and the CSV both use
  that week, and *Previous week* steps back a whole Wed–Tue block.
- A finish time earlier than the start is read as a shift that ran past midnight.
- Anything over 20 hours is rejected as a typo.
- The Sheet is the record. If something looks wrong, fix it in the Sheet or with
  *Edit* on the shift — both end up in the same place.
