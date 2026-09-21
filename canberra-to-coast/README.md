# Canberra to Coast Fencing

One-page lead-generation site for Damian Rubino-Fuchs, Canberra to Coast Fencing (ABN 44 686 184 703).
Static HTML, no build step. Upload this folder as-is to Vercel, Netlify, Cloudflare Pages or any host.

## Before it goes live

1. **Quote form.** Open `index.html`, find `FORM_ENDPOINT` near the bottom and paste a Formspree or
   Web3Forms endpoint. Until then the form falls back to opening an email to canberratocoast@gmail.com.
2. **Google reviews link.** The "Read all our Google reviews" link is a Google search. Replace it with the
   business's own Google Maps review link.
3. **Confirm with Damian:** "Fully insured" in the trust bar, the review count ("20+"), and that South Coast
   jobs are still on offer.
4. **Domain.** canberratocoast.net is currently on Wix. Point the domain at the new host and cancel the Wix plan.
5. **Google Business Profile.** Add this site as the website, and add the real Facebook page URL if a social
   link is wanted in the footer.

## Files

- `index.html` - the whole page, styles and scripts inline (GSAP loads from cdnjs for the animations)
- `fonts/` - Big Shoulders Display and Hanken Grotesk, self-hosted
- `*.webp` - Damian's own job photos (full size and 800px versions)
- `logo-720.png`, `mark-240.png` - logo cut out from the supplied image
- `icon-*.png`, `share.jpg` - favicon, app icon and social share image
