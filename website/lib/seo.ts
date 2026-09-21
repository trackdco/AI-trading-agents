import type { Metadata } from "next";
import { site } from "./site";

/**
 * Next merges metadata per top-level field, so a page that sets `openGraph` to
 * just its own URL REPLACES the layout's object rather than adding to it — and
 * silently loses the share image, the type, the locale and the site name with
 * it. Every page but one was doing that, so no link to this site had a picture
 * on it in a message, a DM or a post. Pages call this instead.
 */
export function og(url: string, extra: Metadata["openGraph"] = {}): Metadata["openGraph"] {
  return {
    type: "website",
    locale: "en_AU",
    siteName: site.name,
    images: [{ url: "/brand/og-image.jpg", width: 1200, height: 630, alt: site.name }],
    url,
    ...extra,
  };
}
