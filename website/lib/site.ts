// One place for every business fact the site shows. Change it here, it changes everywhere.
export const site = {
  name: "Imperium Detailing",
  legalName: "Imperium Detailing",
  abn: "81 254 863 265",
  url: "https://www.imperiumdetailing.com.au",
  tagline: "Not the cheapest detailer in Canberra. The most careful one.",
  phoneDisplay: "0426 661 820",
  phoneE164: "+61426661820",
  email: "imperiumdetailingmanagement@gmail.com",
  instagram: "https://www.instagram.com/imperiumdetailing_/",
  instagramHandle: "@imperiumdetailing_",
  address: { locality: "Canberra", region: "ACT", postcode: "2600", country: "AU" },
  area: "Canberra and Queanbeyan",
  hours: "Every day, 8:30am to 5:30pm",
  notice: "Book at least a day ahead. Same-day is sometimes possible by phone.",
  notOffered: ["Paint protection film (PPF)", "Window tinting", "Rim repairs"],
  // The response promise shown next to every call to action. Keep it true.
  quotePromise: "You'll have a quote back within a few hours, 7 days a week.",
  stats: { cars: "400+", rating: "4.9", reviewCount: 45, warrantyYears: 7 },
  // Google Business Profile: where the reviews are read, and the direct "write a review" link.
  // The business profile itself, not a Maps search — a search can list competitors
  // alongside Imperium and renders differently on different devices. Same profile
  // ID as the write-a-review link below.
  googleReviewsUrl: "https://g.page/r/CSwRG2iKFelCEBM/",
  googleWriteReviewUrl: "https://g.page/r/CSwRG2iKFelCEBM/review",
  // Integrations. Set these in .env.local (see README); empty means "not loaded".
  // Web3Forms takes the quote form and emails it. Its access key is public by
  // design — it ships inside the page the same way a form action does, and any
  // NEXT_PUBLIC_ value would too — so it lives here rather than in an env var
  // that has to be set again on every host. If it ever attracts spam, turn on
  // domain restriction or hCaptcha in the Web3Forms dashboard.
  formEndpoint: process.env.NEXT_PUBLIC_FORM_ENDPOINT ?? "https://api.web3forms.com/submit",
  formAccessKey: process.env.NEXT_PUBLIC_FORM_ACCESS_KEY ?? "9711fb99-65d5-4280-811a-ff2cb61b6565",
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
  /** Exterior-only maintenance plan, per month. The entry price on the plans page. */
  maintenanceExterior: 90,
  /** Inside-and-out maintenance plan, per month. Fortnightly visits are quoted per car. */
  maintenanceMonthly: 150,
};

/**
 * "a full detail" but "an exterior detail". Every service name the site owns
 * starts with a plain consonant or vowel sound, so the first letter decides it.
 */
export const anA = (noun: string) => `${/^[aeiou]/i.test(noun.trim()) ? "an" : "a"} ${noun}`;

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
