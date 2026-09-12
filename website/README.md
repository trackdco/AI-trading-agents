# Imperium Detailing — website

Premium mobile car detailing, Canberra and Queanbeyan. Built with Next.js (static export), TypeScript, Tailwind CSS v4 and shadcn/ui, with GSAP for the hero sequence and framer-motion for the reviews marquee.

## Run it

```bash
npm install
npm run dev        # http://localhost:3000
npm run build      # static export into ./out
```

`out/` is a plain folder of HTML, CSS, JS and media. Deploy it to Vercel, Cloudflare Pages, Netlify, or any static host. On Vercel, just import the repo and set the root directory to `website`.

## Where things live

| What | File |
| --- | --- |
| Business facts: phone, email, hours, stats, quote promise | `lib/site.ts` |
| Prices | `lib/site.ts` (`prices`) |
| The five services: copy, inclusions, FAQs, images | `lib/services.ts` |
| Nine districts and their suburbs | `lib/areas.ts` |
| The two guides | `lib/articles.ts` |
| The 45 reviews | `lib/reviews.json` |
| Colour tokens (same as the previous site) | `app/globals.css` |
| Logo, favicons, share image | `public/brand/` |
| Photos (WebP, three sizes each) | `public/images/` + `lib/image-manifest.json` |
| Videos | `public/media/` |

Pages: `/`, `/services/` and five service pages, `/service-areas/` and nine district pages, `/learn/` and two guides, `/reviews/`, `/book/`, `/warranty/`, `/privacy/`, `/terms/`, plus `/car-detailing-canberra/` to keep the old URL alive. `sitemap.xml` and `robots.txt` are generated at build.

## Settings (`.env.local`)

```
NEXT_PUBLIC_FORM_ENDPOINT=      # where the quote form POSTs JSON (LeadConnector webhook, Formspree, etc.)
NEXT_PUBLIC_META_PIXEL_ID=      # Meta Pixel ID; empty = not loaded
NEXT_PUBLIC_GOOGLE_ADS_ID=      # defaults to the existing AW-17065776345
NEXT_PUBLIC_CHAT_WIDGET_ID=     # defaults to the existing LeadConnector chat widget
```

Until `NEXT_PUBLIC_FORM_ENDPOINT` is set, the quote form composes the answers into a text message and opens the visitor's messaging app (on desktop it shows the message with a copy button and your email). Set the endpoint and it posts there instead and shows a thank-you.

## Before launch

1. Replace `public/brand/logo-*.png` with SVG exports of the logo if you have them (sharper at every size).
2. Put your Google Business "write a review" link in `lib/site.ts` (`googleReviewsUrl`).
3. Read `/warranty/` and `/terms/` once and adjust anything that doesn't match how you actually work.
4. Decide the quote promise wording in `lib/site.ts` (`quotePromise`) and keep it.
5. Add new photos: drop JPEGs in the generator's `assets/src`, or resize to 480/960/full-width WebP by hand and add an entry to `lib/image-manifest.json`.

## Adding a photo (by hand)

Save `public/images/<name>-480.webp`, `<name>-960.webp` and `<name>-<fullwidth>.webp`, then add to `lib/image-manifest.json`:

```json
"<name>": { "w": 1600, "h": 1067, "variants": [480, 960, 1600] }
```

Use it with `<Picture name="<name>" alt="..." />`.
