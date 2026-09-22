# Canberra to Coast Fencing

One-page lead-generation site for Damian Rubino-Fuchs, Canberra to Coast Fencing (ABN 44 686 184 703).
Static HTML, no build step. Upload this folder as-is to Vercel, Netlify, Cloudflare Pages or any host.

## Before it goes live

1. **Turn the quote form on.** Open `index.html`, find the `SITE` object near the bottom and paste a
   Web3Forms access key into `formAccessKey` (free, from web3forms.com). With no key the form still
   works: it opens a pre-filled text message to Damian instead of emailing him, and the thank-you
   message says so honestly rather than promising a call.
2. **Google review links.** In the same `SITE` object, set `googleReviewsUrl` to the business's
   Google profile link (looks like `https://g.page/r/xxxx/`) and `googleWriteReviewUrl` to the same
   link with `/review` on the end. The "Write a review" button stays hidden until both are real
   links, so remove the `hidden` attribute on `#writeReview` once they are set.
3. **Check the prices with Damian.** The price guide uses `PRICES` in `index.html`:
   $95 to $135 a metre for 1.8 m, $80 to $115 for 1.5 m, $110 to $155 for 2.1 m, plus $15 to $25 a
   metre to remove an old fence, $450 to $650 for a single gate and $900 to $1,300 for a double.
   These are typical Canberra 2026 figures, not Damian's own numbers. Change them or remove the
   section. The same figures appear in the hero line and the first FAQ answer.
4. **Confirm the trust claims:** "Fully insured", "5.0 Google rating", "20+ five-star reviews".
5. **Domain.** canberratocoast.net is currently on Wix. Point the domain at the new host and cancel
   the Wix plan.
6. **Google Business Profile.** Add this site as the website. That matters more for leads than the
   site itself.

## Files

- `index.html` - the whole page, styles and scripts inline (GSAP loads from cdnjs for the animations;
  the page still works and shows everything if that fails to load)
- `fonts/` - Big Shoulders Display and Hanken Grotesk, self-hosted
- `*.webp` - Damian's own job photos, full size and 800px versions
- `gate-*.webp` - the same gate photo recoloured into all 12 Colorbond colours (1100px and 700px).
  Made from `images/11.webp` by `tools/mask.py` (marks just the fence and gate) then `tools/recolour.py`
  (keeps the real shadows, ribs and sun glare, swaps the colour). Re-run those two if the photo changes.
- `logo-720.png`, `mark-240.png` - logo cut out from the supplied image
- `icon-*.png`, `share.jpg` - favicon, app icon and social share image

## What the page does

Hero with a real job photo, trust strip, four service tiles with from-prices, a price guide
calculator, photo gallery with a lightbox, a Colorbond colour picker that recolours a drawn fence,
a "what's in every fence" explainer, reasons to pick Damian, real Google reviews, three-step
process, suburb list, FAQ, quote form, and a sticky call/text/quote bar on phones.
