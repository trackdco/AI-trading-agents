# Frontline Systems — landing page

One static page. No build step, no framework, no npm install. Open `index.html`
and it works; drag the folder onto any host and it works there too.

    index.html          the page
    privacy/index.html  privacy policy
    styles.css          all styling, tokens at the top
    app.js              tier switcher, sticky bar, form
    assets/             logo, favicons, fonts, the Imperium reel, share card
    assets/trace-logo.py  regenerates the logo SVGs from logo-orig.png

First load is about **85 KB** over the wire, and 62 KB of that is the two fonts.
`imperium-reel.webp` (172 KB) is lazy-loaded well below the fold.

## The look

Deep charcoal, navy as structure, hi-vis as the only thing that acts — a night
job site rather than another dark SaaS page. Two fixed layers do the lighting: a
soft navy key light and a fine grain at 3.5% on overlay. The grain is what stops
a dark page reading flat; remove it and the whole thing goes plastic.

Hi-vis is rationed hard. It is the primary button, the rail on the one log row
the business rests on, the tick marks, and nothing else. The two non-recommended
pricing tiers deliberately carry the same words on a lighter button, so the solid
yellow always means "this one".

Two handsets carry the argument. The hero one is built in CSS and plays the
product happening — lock screen, 7:42, the notification dropping in, one kick.
The second, in the proof section, runs a real screenshot of
imperiumdetailing.com.au that scrolls as the page scrolls.

Regenerating that reel: serve a production build of the Imperium site locally and
run `scratchpad/imperium/fl-reel.mjs`. It captures band by band on purpose — that
site pauses its videos off-screen, so a single full-page grab catches them as
black holes, and every off-box request has to be blocked or the sandbox proxy's
TLS retries take the browser down.

---

## Before this goes live

Four things need a decision or an action. Nothing on the page is untrue as it
stands, but three of these change what it is allowed to say.

### 1. The form does not fire the automation yet

`app.js` has `FORM_KEY = ''`, so the form currently composes an email instead of
posting anywhere. That is honest today: the page says *"I'll text and email you
about your enquiry"* and does not claim a live demo.

The moment Make.com and ClickSend are wired up, two things change together:

1. In `app.js`, set `FORM_ENDPOINT` to the Make webhook URL and `FORM_KEY` to any
   non-empty string.
2. Only then, change the form section's opening lines to the demo version:

   > **Send this and watch what happens on your own phone.**
   > This form runs on the exact system I'm selling. Fill it in and my phone
   > buzzes, and yours gets a reply. That's the product — try it before you pay
   > for it.

   and change the success panel heading to *"Sent. My phone just buzzed. Check
   yours — your reply's on its way."*

**Do not make change 2 without change 1.** This is the one page whose entire
argument is that every claim on it is checkable, and the form is where a sceptic
checks.

### 2. "Frontline Systems" is not a registered business name

ABN Lookup on 14 Sep 2026 shows ABN 21 468 745 370 as **PENDERGAST, PATRICK
CHARLES**, individual/sole trader, active from 4 Sep 2025, ACT 2617, not
registered for GST, **with no registered business names**.

Trading under a name that isn't your own legal name generally requires an ASIC
business name registration. The footer is worded to be true either way — it says
"Patrick Pendergast, sole trader" and never claims a registered business name —
but the registration is worth doing, and it applies to *Imperium Detailing* too.

### 3. The GST line

The page states "not registered for GST, so the prices are the total." True as at
14 Sep 2026. It lives in exactly two places — the pricing section and the footer.
Change both the day you register.

### 4. There is no photo of Pat

The "I'm Pat" section reads fine without one, but a real photo in that section is
worth more than anything else you could add to this page. A plain one, on the
job, in the van, works better than a studio portrait. Drop it in
`assets/pat.jpg` and add it to that section.

---

## The claims on this page, and where they came from

Everything checkable was verified on 14 Sep 2026 against the primary source:

| Claim | Source |
| --- | --- |
| ABN, entity name, GST status | [ABN Lookup](https://abr.business.gov.au/ABN/View?abn=21468745370) |
| Sender ID Register mandatory 1 Jul 2026; unregistered IDs labelled "Unverified" | [ACMA](https://www.acma.gov.au/sms-sender-id-register) |
| A .com.au holder may not rent, lease or sub-licence; a developer registering for you must list *you* as registrant | [auDA](https://www.auda.org.au/au-domain-names/policies-and-compliance/au-licensing-rules/monetisation-and-new-au-licensing-rules) |
| Automated messages must identify the sender and offer a working opt-out | [ACMA, Spam Act](https://www.acma.gov.au/avoid-sending-spam) |

The Imperium figures (32 pages, 33,597 words, 2 calculators, 13 clips, 28 photos,
72 structured-data blocks) were counted from a fresh production build on
14 Sep 2026, not estimated. **Re-count them before publishing if that site has
changed** — they are the exact numbers a sceptic will check, and being wrong on
one costs more than all six are worth.

There are no testimonials, client names, case studies or performance statistics
anywhere on this page, because Frontline has none yet. Don't add any that aren't
real.

---

## Deploying

The domain `frontlinesystems.com.au` already resolves (Cloudflare) and currently
returns 404, so it is free to point wherever you like.

**Vercel** — `vercel.json` is already here (clean URLs, week-long cache on
`/assets`, no cache on HTML). Import the folder, add the domain, done.

**Anything else** — it is plain static files. Upload the folder. The only server
requirement is that `/privacy/` serves `privacy/index.html`.

After it is live: take down or redirect `plug-the-leaks.lovable.app`. It still
sells a different offer (an HVAC AI receptionist) to a different audience, and
two live pitches from one business undercuts both.

---

## Reusing this as a client template

This is also the template for the $897 and $1,897 builds. To rebuild it as a
client's site:

1. Copy the folder.
2. Change the token values at the top of `styles.css`. That is the whole
   palette. The `theme-factory` skill in `.claude/skills/` has ten ready-made
   colour and font pairings — use a different one per client so no two builds
   look like the same site recoloured.
3. Swap the two font files in `assets/fonts/` and the two `@font-face` rules.
4. Replace the copy. Keep the structure: mechanism, ownership, running costs,
   proof, price, exclusions, fit, limits, who you are, objections, form.
5. Point `FORM_ENDPOINT` at *their* Make webhook, on *their* account.

The parts worth keeping every time are the ones that cost nothing and build
trust: published prices, a stated list of what is excluded, a section that turns
the wrong customers away, and a limits section that says what the thing cannot do.
