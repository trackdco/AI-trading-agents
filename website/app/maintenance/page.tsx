import type { Metadata } from "next";
import { og } from "@/lib/seo";
import Link from "next/link";
import { site, prices, smsHref, telHref } from "@/lib/site";
import { formatPrice, type Faq as FaqItem } from "@/lib/services";
import { LoopVideo } from "@/components/site/loop-video";
import { Picture } from "@/components/site/picture";
import { Faq } from "@/components/site/faq";
import { LinkButton } from "@/components/site/link-button";
import { QuoteCta } from "@/components/site/quote-cta";
import { Booking } from "@/components/site/booking";
import { Breadcrumbs } from "@/components/site/breadcrumbs";

export const metadata: Metadata = {
  title: "Maintenance Plans Canberra from $90",
  description:
    "Monthly car maintenance in Canberra. Exterior from $90 a month, inside and out from $150. A coating-safe hand wash at your place, monthly or fortnightly.",
  alternates: { canonical: "/maintenance/" }, openGraph: og("/maintenance/"),
};

const plans = [
  {
    every: "Exterior, monthly",
    who: "The outside kept the way we left it. The cheapest way onto a schedule, and enough for a car that lives in a garage and carries nobody but you.",
    price: `From ${formatPrice(prices.maintenanceExterior)} a month`,
    note: "Quoted for your car",
  },
  {
    every: "Inside and out, monthly",
    who: "The exterior visit plus the interior reset. Most cars that carry people every day sit here, and it is the rhythm we recommend for coated cars.",
    price: `From ${formatPrice(prices.maintenanceMonthly)} a month`,
    note: "Quoted for your car",
  },
  {
    every: "Every 2 weeks",
    who: "Daily drivers that live on the street, dark colours that show every mark, cars that carry kids or dogs. It never looks washed. It looks detailed.",
    price: "Quote on request",
    note: "Text us the car",
  },
];

// Split so the two prices mean something: the first list is the $90 visit, the
// second is what the extra $60 buys.
const outside = [
  "Pre-rinse and snow foam, so grit lifts off before anything touches the paint",
  "Two-bucket, pH-neutral hand wash with clean mitts, never a brush",
  "Wheels, tyres and arches cleaned, tyres dressed",
  "Door jambs and exterior glass",
  "Bonded contamination checked and spot-treated",
  "Protection topped up: a coating booster on coated cars, a sealant on the rest",
  "A quick note on anything we notice: stone chips, swirl marks, coating health",
];

const inside = [
  "Interior vacuum, front and back",
  "Dash, console and door cards wiped down",
  "Interior glass",
];

const faq: FaqItem[] = [
  {
    q: "Does the car need a full detail first?",
    a: "Usually, unless we've detailed it in the last few months. A plan keeps a finish; it doesn't chase one. We start with a full detail so every visit after that is maintenance, not recovery.",
  },
  {
    q: "How is it priced?",
    a: "The exterior plan starts at $90 a month and inside and out starts at $150, quoted for your car from its size, colour and how it's used. Fortnightly visits are quoted on request. It's the same number every month, and the number you're quoted is the number you pay.",
  },
  {
    q: "What's the difference between the $90 plan and the $150 one?",
    a: "The $90 plan is the outside: snow foam, a two-bucket hand wash, wheels and arches, glass, and the protection topped up. The $150 plan is that visit plus the interior reset, so the vacuum, the dash, console and door cards, and the inside of the glass. Both are the same two people, the same month, at your place.",
  },
  {
    q: "Do I need to be home?",
    a: "No. As long as we can reach a tap, a power point and the car, we can do the visit while you're at work and text you when it's done.",
  },
  {
    q: "Is it only for ceramic-coated cars?",
    a: "No. Coated cars get the most out of it, because the coating gets washed the way the warranty asks and topped up as it needs. But any car we've detailed can go on a plan.",
  },
  {
    q: "Can I change how often you come?",
    a: "Yes. Start monthly and move to fortnightly as the seasons change, or the other way. Winter grit and spring pollen usually call for closer visits.",
  },
];

export default function MaintenancePage() {
  const faqLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faq.map((f) => ({ "@type": "Question", name: f.q, acceptedAnswer: { "@type": "Answer", text: f.a } })),
  };
  const sms = smsHref("Hi Imperium, I'd like a quote for a maintenance plan.\nCar: \nSuburb: \nHow often: ");

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqLd) }} />

      <section className="container-x mx-auto grid max-w-6xl gap-10 py-14 md:grid-cols-12 md:items-center md:py-20">
        <div className="md:col-span-7">
          <Breadcrumbs items={[{ href: "/services/", label: "Services" }, { href: "/maintenance/", label: "Maintenance plans" }]} />
          <p className="m-0 mt-4 text-[15px] text-muted-foreground">
            Exterior from <b className="font-medium text-foreground">{formatPrice(prices.maintenanceExterior)}</b> a month. Inside and out from{" "}
            <b className="font-medium text-foreground">{formatPrice(prices.maintenanceMonthly)}</b>. Fortnightly quoted on request.
          </p>
          <h1 className="display-caps mt-3 text-5xl md:text-7xl">Detailed once. Kept that way.</h1>
          <p className="mt-6 max-w-[60ch] text-lg text-secondary-foreground">
            A maintenance plan is us coming back on a schedule: a proper hand wash, the interior reset, the protection topped up. The car never slides back to needing a full detail, and a coated car gets the life it was promised.
          </p>
          <p className="mt-4 max-w-[60ch] text-muted-foreground">
            {"For daily drivers that live outside, dark cars that show every wash mark, family cars, and anyone who'd rather spend Saturday morning on something other than a bucket."}
          </p>
          <div className="mt-7 flex flex-col gap-3 sm:flex-row">
            <QuoteCta sms={sms} />
            <LinkButton href={telHref} variant="ghost">
              Call {site.phoneDisplay}
            </LinkButton>
          </div>
          <p className="mt-4 text-[15px] text-muted-foreground">{site.quotePromise}</p>
        </div>
        <div className="md:col-span-5">
          <Picture
            name="m4-mitt"
            alt="A wash mitt on the bonnet of a BMW M4 during a maintenance wash"
            sizes="(min-width: 768px) 40vw, 100vw"
            priority
            className="panel-glow aspect-[4/5] w-full rounded-xl object-cover"
          />
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto max-w-6xl py-14 md:py-20">
          <h2 className="display-caps text-3xl md:text-5xl">Pick a plan.</h2>
          <p className="mt-4 max-w-[58ch] text-lg text-muted-foreground">{"We'll suggest one when we quote. You can change it any time."}</p>
          <div className="mt-8 grid gap-px overflow-hidden rounded-lg border border-border bg-border">
            {plans.map((r) => (
              <div key={r.every} className="grid gap-3 bg-background p-5 md:grid-cols-12 md:items-center md:p-6">
                <h3 className="display-caps m-0 text-3xl md:col-span-3">{r.every}</h3>
                <p className="m-0 text-[15px] text-secondary-foreground md:col-span-6">{r.who}</p>
                <div className="md:col-span-3 md:text-right">
                  <span className="display-caps block text-2xl">{r.price}</span>
                  <span className="mt-1 block text-sm text-muted-foreground">{r.note}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto grid max-w-6xl gap-12 py-14 md:grid-cols-12 md:py-20">
          <div className="md:col-span-7">
            <h2 className="display-caps text-3xl md:text-5xl">What a visit covers</h2>
            <h3 className="mt-6 text-lg font-semibold">
              Every visit, from {formatPrice(prices.maintenanceExterior)} a month
            </h3>
            <ul className="mt-4 grid max-w-[64ch] list-none gap-2.5 p-0 text-[17px] text-secondary-foreground">
              {outside.map((t) => (
                <li key={t} className="flex gap-3">
                  <span aria-hidden="true" className="mt-[.6em] h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                  {t}
                </li>
              ))}
            </ul>
            <h3 className="mt-8 text-lg font-semibold">
              Inside and out adds, from {formatPrice(prices.maintenanceMonthly)} a month
            </h3>
            <ul className="mt-4 grid max-w-[64ch] list-none gap-2.5 p-0 text-[17px] text-secondary-foreground">
              {inside.map((t) => (
                <li key={t} className="flex gap-3">
                  <span aria-hidden="true" className="mt-[.6em] h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                  {t}
                </li>
              ))}
            </ul>
          </div>
          <aside className="md:col-span-5">
            <div className="rounded-lg border border-border bg-card p-6">
              <h2 className="text-lg font-semibold">Why not a car wash?</h2>
              <p className="mt-3 text-[15px] text-secondary-foreground">
                Spinning brushes are the fastest way to put swirl marks back into corrected paint, and they void a coating warranty. A plan is the same two people and the same method as the day it was detailed, on your driveway.
              </p>
            </div>
            <div className="mt-4 rounded-lg border border-border p-6">
              <h2 className="text-lg font-semibold">On the day, we need</h2>
              <ul className="mt-4 grid list-none gap-2.5 p-0 text-[15px] text-muted-foreground">
                <li>Access to water: an outdoor tap we can hook a hose to.</li>
                <li>Access to power: a standard 240V power point within reach.</li>
                <li>Somewhere to park the car that we can walk around.</li>
              </ul>
            </div>
          </aside>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto grid max-w-6xl items-center gap-10 py-14 md:grid-cols-12 md:py-20">
          <div className="md:col-span-5">
            <LoopVideo
              base="/media/maintenance-wash-720"
              poster="/media/maintenance-wash-poster.webp"
              label="A monthly maintenance wash on a work ute: snow foam, a hand wash with a mitt, the wheels, then dried by hand"
              className="panel-glow aspect-[4/5] w-full rounded-xl bg-card object-cover"
            />
          </div>
          <div className="md:col-span-7">
            <h2 className="display-caps text-3xl md:text-5xl">One visit, start to finish.</h2>
            <p className="mt-5 max-w-[56ch] text-lg text-secondary-foreground">
              Snow foam first so the grit lifts off, then a hand wash with a clean mitt, the wheels and arches, and a hand dry. No brushes touch the
              paint. That is the whole visit, and it looks the same every month.
            </p>
            <p className="mt-4 max-w-[56ch] text-muted-foreground">
              This one is a work ute on a monthly exterior plan. The exterior maintenance plan starts at{" "}
              <b className="font-medium text-foreground">{formatPrice(prices.maintenanceExterior)} a month</b>, quoted for your vehicle.
            </p>
            <div className="mt-7 flex flex-col gap-3 sm:flex-row">
              <QuoteCta sms={sms} />
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto max-w-6xl py-14 md:py-20">
          <Faq items={faq} />
          <p className="mt-10 text-[15px] text-muted-foreground">
            Also see:{" "}
            <Link href="/services/ceramic-coating-canberra/" className="text-foreground underline underline-offset-4">
              Ceramic coating
            </Link>{" "}
            and the{" "}
            <Link href="/warranty/" className="text-foreground underline underline-offset-4">
              coating warranty
            </Link>
            .
          </p>
        </div>
      </section>

      <Booking title="Start a maintenance plan." defaultService="Regular maintenance plan" />
    </>
  );
}
