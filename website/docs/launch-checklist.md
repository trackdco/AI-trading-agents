# Launch checklist

Tick every line before the domain points at the new site. Lines marked "needs Pat" can't be done from the code.

## Domain and hosting

- [ ] Deploy to Vercel from the `website` folder. Build command `next build`, output `out`.
- [ ] Point `imperiumdetailing.com.au` and `www` at Vercel (needs Pat, domain registrar login).
- [ ] Confirm HTTPS works on both, and that `http://` and the non-www version redirect to `https://www.`.
- [ ] Open `/sitemap.xml` and `/robots.txt` on the live domain.
- [ ] Set `NEXT_PUBLIC_FORM_ENDPOINT` to the LeadConnector webhook (needs Pat).
- [ ] Set `NEXT_PUBLIC_META_PIXEL_ID` if the pixel exists (needs Pat).

## Content truth check (needs Pat)

- [ ] Prices in the guide match what you charge, including the $75 condition range on full and interior details.
- [ ] Every "what's included" list matches what you actually do on the day.
- [ ] Opening hours: every day, 8:30am to 5:30pm.
- [ ] Review count and rating match Google.
- [ ] Warranty page matches the warranty document you hand over.
- [ ] Not offered: PPF, window tinting, rim repairs. Trucks by phone. Boats never.

## Lead flow

- [ ] Send the quote form from a phone and from a laptop. Confirm the lead lands in the CRM and an automatic text goes back.
- [ ] Tap every "Text us" button on a phone. The message should open with the job, price and blanks for car and suburb.
- [ ] Tap "Call". It should dial 0426 661 820.
- [ ] Open `/book/?service=Ceramic%20coating` and confirm the service is pre-picked.
- [ ] Check the Google review link opens the review box: https://g.page/r/CSwRG2iKFelCEBM/review

## Tracking

- [ ] Google Ads: create conversion actions for `contact_call`, `contact_text` and `generate_lead`, then fire each once and confirm they show.
- [ ] Meta: confirm `Contact` and `Lead` events appear in Events Manager after the pixel ID is set.
- [ ] Google Search Console: add the property, submit `/sitemap.xml`.
- [ ] Google Business Profile: website link points at the new domain.

## SEO

- [ ] Every page has a unique title under 60 characters and a description under 160 (checked, all 30 pages).
- [ ] One H1 per page, no heading jumps (checked).
- [ ] All images have alt text and dimensions (checked).
- [ ] Breadcrumb, Service, FAQ, Article and LocalBusiness data validate at https://search.google.com/test/rich-results on the live domain.
- [ ] Old URLs from the previous site redirect to the matching new pages (needs the old URL list).

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
- [ ] Add the ABN to the footer (needs Pat).

## Launch day

- [ ] Deploy, then open every page in the footer once on a phone.
- [ ] Clear Safari history on your own phone so you're not looking at a cached copy.
- [ ] Post the new site link on Instagram and update the bio link.

## First 30 days

- [ ] Check Search Console for crawl errors after one week.
- [ ] Compare leads per week with the old site.
- [ ] Add three to six recent Instagram post codes to the strip.
- [ ] Add a photo of the two of you and a short "who's doing the work" block.
