# Launch checklist

Tick every line before the domain points at the new site. Lines marked "needs Pat" can't be done from the code.

## Domain and hosting

- [ ] Deploy to Vercel from the `website` folder. Build command `next build`, output `out`.
- [ ] Point `imperiumdetailing.com.au` and `www` at Vercel (needs Pat, domain registrar login).
- [ ] Confirm HTTPS works on both, and that `http://` and the non-www version redirect to `https://www.`.
- [ ] Open `/sitemap.xml` and `/robots.txt` on the live domain.
- [ ] Nothing to set for the quote form: it posts to Web3Forms and the access key lives in `lib/site.ts`, because a Web3Forms key is public by design. `NEXT_PUBLIC_FORM_ENDPOINT` and `NEXT_PUBLIC_FORM_ACCESS_KEY` only need setting if the form ever moves.
- [x] Meta pixel: not needed. Pat confirmed on 2026-09-14 that he does not run Meta ads.
      `components/site/analytics.tsx` already skips the whole script when the ID is empty,
      so nothing loads and nothing breaks. Set `NEXT_PUBLIC_META_PIXEL_ID` if that changes.

## Content truth check (needs Pat)

- [ ] Prices in the guide match what you charge, including the $75 condition range on full and interior details.
- [ ] Every "what's included" list matches what you actually do on the day.
- [ ] Opening hours: every day, 8:30am to 5:30pm.
- [ ] Review count and rating match Google.
- [ ] Warranty page matches the warranty document you hand over.
- [ ] Not offered: window tinting and rim repairs. PPF is not FITTED, but film someone else fitted is coated over. Trucks are done, quoted by phone. Boats never.

## Lead flow

- [ ] **Send one real quote from the live site, from a phone and from a laptop, and confirm the email arrives.** This is the single most important line on this page and it has never been tested end to end — the sandbox blocks Web3Forms, so it could not be verified from here. Do the fleet form too: `/fleet-detailing-canberra/`.
- [ ] Tap every "Text us" button on a phone. The message should open with the job, price and blanks for car and suburb.
- [ ] Tap "Call". It should dial 0426 661 820.
- [ ] Open `/book/?service=Ceramic%20coating` and confirm the service is pre-picked.
- [ ] On `/fleet-detailing-canberra/`, count a few vehicles into the estimator and send it. Confirm the email lists the vehicles by size and the guide total.
- [ ] Check the Google review link opens the review box: https://g.page/r/CSwRG2iKFelCEBM/review

## Tracking

- [ ] Google Ads: create conversion actions for `contact_call`, `contact_text` and `generate_lead`, then fire each once and confirm they show.
- [x] Meta: nothing to do, no pixel. See the note under Domain and hosting.
- [ ] Google Search Console: add the property, submit `/sitemap.xml`.
- [ ] Google Business Profile: website link points at the new domain.

## SEO

- [ ] Every page has a unique title under 60 characters and a description between 70 and 160 (checked, all 31 pages).
- [ ] One H1 per page, no heading jumps (checked).
- [ ] All images have alt text and dimensions (checked).
- [ ] Breadcrumb, Service, FAQ, Article and LocalBusiness data validate at https://search.google.com/test/rich-results on the live domain.
- [x] Old URLs from the previous site redirect to the matching new pages. Checked against the live sitemap at imperiumdetailing.com.au on 2026-09-13: all 26 URLs it lists either exist on the new site or already have a redirect in `vercel.json`. `/contact-us` was the only gap — it is from an older iteration, already 404s live, and is still indexed, so it now redirects to `/book/`.
- [ ] **`imperiumdetailing.org`: optional, and parked.** Registry lookup on 2026-09-14: registrar
      Automattic (WordPress.com), registered 2024-12-25, transferred 2025-06-02, **expires 2026-12-25**,
      status `client transfer prohibited`, nameservers on Google Cloud DNS. So it is still Pat's; what was
      cancelled is the site, not the registration, and the DNS zone lives in a Google account rather than at
      the registrar. Pat cannot get into the WordPress.com account, so this is parked rather than open.
      If he ever does get in, forwarding it to `https://www.imperiumdetailing.com.au/` hands Google the
      credit for the pages it still has indexed there. If not, it lapses in December and the only thing
      worth deciding is whether to re-register it purely to hold the brand name.
- [ ] **Check `management@imperiumdetailing.org` is not in use anywhere.** It was published on the `.org`
      site. When that domain lapses the mailbox dies with it. The new site uses the Gmail address, so this
      is about anything outside the site: Google Business Profile, invoices, Square, ad accounts.
- [ ] **`imperiumdetailing.square.site` is NOT Pat's and is still live** (HTTP 200, checked 2026-09-14; it
      renders in the browser only, so its content could not be read from the sandbox). Pat should open it
      and decide: if someone else is trading under the name, that is a business problem rather than a code
      one. If it is a dormant page nobody runs, outranking it is enough.

## Speed

- [ ] Run PageSpeed Insights on the live home page and a service page. Aim for 75+ on mobile, 90+ on desktop.
- [ ] Confirm `/media/` and `/images/` responses carry `Cache-Control: public, max-age=604800`.
- [ ] Hero video plays on iPhone Safari with the sound off and loops.

## Mobile

- [ ] iPhone Safari and Android Chrome: the Text and Call bar shows after scrolling, hides at the quote form, and never covers a button.
- [ ] The chat bubble does not appear on phones (it is desktop-only on purpose).
- [ ] No sideways scrolling on any page at 360px (checked).
- [ ] The price guide scrolls to the answer when you pick a job.

## Accessibility

- [ ] Zero axe violations on all pages (checked).
- [ ] Tab through the home page: every button and link shows a focus ring, and the carousel arrows work from the keyboard.
- [ ] Turn on "Reduce motion" on a phone: no curtain, no marquee, no reveals, everything still readable.

## Legal

- [ ] Privacy policy matches what the form and the pixel actually collect.
- [ ] Terms match the warranty and the condition-based price range.
- [x] ABN in the footer.

## Launch day

- [ ] Deploy, then open every page in the footer once on a phone.
- [ ] Clear Safari history on your own phone so you're not looking at a cached copy.
- [ ] Post the new site link on Instagram and update the bio link.

## First 30 days

- [ ] Check Search Console for crawl errors after one week.
- [ ] Compare leads per week with the old site.
- [x] Eight Instagram post codes in the strip, each opened to confirm it loads.
- [ ] Add a photo of the two of you and a short "who's doing the work" block.
