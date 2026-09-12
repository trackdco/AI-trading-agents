// One place for every business fact the site shows. Change it here, it changes everywhere.
export const site = {
  name: "Imperium Detailing",
  legalName: "Imperium Detailing",
  url: "https://www.imperiumdetailing.com.au",
  tagline: "Not the cheapest detailer in Canberra. The most careful one.",
  phoneDisplay: "0426 661 820",
  phoneE164: "+61426661820",
  email: "imperiumdetailingmanagement@gmail.com",
  instagram: "https://www.instagram.com/imperiumdetailing_/",
  instagramHandle: "@imperiumdetailing_",
  address: { locality: "Canberra", region: "ACT", postcode: "2600", country: "AU" },
  area: "Canberra and Queanbeyan",
  hours: "7 days a week, by appointment",
  // The response promise shown next to every call to action. Keep it true.
  quotePromise: "You'll have a quote back within a few hours, 7 days a week.",
  stats: { cars: "400+", rating: "4.9", reviewCount: 45, warrantyYears: 7 },
  // Google Business Profile: where the reviews are read, and the direct "write a review" link.
  googleReviewsUrl: "https://www.google.com/maps/search/Imperium+Detailing+Canberra",
  googleWriteReviewUrl: "https://g.page/r/CSwRG2iKFelCEBM/review",
  // Integrations. Set these in .env.local (see README); empty means "not loaded".
  formEndpoint: process.env.NEXT_PUBLIC_FORM_ENDPOINT ?? "",
  metaPixelId: process.env.NEXT_PUBLIC_META_PIXEL_ID ?? "",
  googleAdsId: process.env.NEXT_PUBLIC_GOOGLE_ADS_ID ?? "AW-17065776345",
  chatWidgetId: process.env.NEXT_PUBLIC_CHAT_WIDGET_ID ?? "6a43315455ef5e64138101d7",
};

export const prices = {
  exterior: 110,
  interior: 140,
  full: 225,
  correction: 397,
  ceramic: 997,
  /** Maintenance plan, per month. Fortnightly visits are quoted per car. */
  maintenanceMonthly: 150,
};

export const defaultSmsBody = "Hi Imperium, I'd like a quote.\nCar: \nSuburb: \nService: ";

export const smsHref = (body: string = defaultSmsBody) =>
  `sms:${site.phoneE164}?&body=${encodeURIComponent(body)}`;

export const telHref = `tel:${site.phoneE164}`;

export const nav = [
  { href: "/services/", label: "Services" },
  { href: "/#work", label: "Our work" },
  { href: "/service-areas/", label: "Areas" },
  { href: "/reviews/", label: "Reviews" },
  { href: "/learn/", label: "Guides" },
];
