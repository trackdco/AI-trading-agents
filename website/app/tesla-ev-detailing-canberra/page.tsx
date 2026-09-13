import type { Metadata } from "next";
import Link from "next/link";
import { site, smsHref, telHref } from "@/lib/site";
import { services, formatPrice, type Faq as FaqItem } from "@/lib/services";
import { LoopVideo } from "@/components/site/loop-video";
import { Faq } from "@/components/site/faq";
import { LinkButton } from "@/components/site/link-button";
import { Booking } from "@/components/site/booking";
import { Breadcrumbs } from "@/components/site/breadcrumbs";

export const metadata: Metadata = {
  title: "Tesla and EV Detailing Canberra",
  description:
    "Tesla and EV detailing in Canberra: soft paint corrected and ceramic coated, cameras kept clear, light interiors cleaned safely. We come to you.",
  alternates: { canonical: "/tesla-ev-detailing-canberra/" },
};

const onTheDay = [
  "Flush door handles and the charge port door cleaned by hand, not blasted",
  "Cameras and sensors cleaned and kept clear of coating, so the driver aids see properly",
  "Glass roof decontaminated and coated with the paint, so rain sheets off it",
  "Aero wheel covers off, wheels cleaned behind them, covers back on",
  "White and light interiors cleaned with pH-neutral product, no dyes, no solvents, tested in a hidden spot first",
  "Frunk lip and seals wiped down. No engine bay to degrease",
];

const faq: FaqItem[] = [
  {
    q: "Is a ceramic coating safe on Tesla paint?",
    a: "Yes, and it's the best protection for it. Tesla's clear coat is soft, so we do a light correction first, then coat it. The coating is harder than the paint and takes the wash marring instead.",
  },
  {
    q: "Can you detail the car while it's charging?",
    a: "We'd rather not. Charge it before or after the visit. Everything else, including the charge port door, gets cleaned as normal.",
  },
  {
    q: "Do you touch the cameras and sensors?",
    a: "We clean them and keep coating off the lenses. Nothing is sprayed into the sensor housings, and nothing is left on the glass that would blur them.",
  },
  {
    q: "What about a white interior?",
    a: "Vegan leather and light fabrics are cleaned with pH-neutral product and no dyes, tested in a hidden spot first. Denim transfer on light seats comes off with the right product and patience, not with a scrub.",
  },
  {
    q: "Which EVs do you work on?",
    a: "All of them. Tesla, BYD, Polestar, Kia, Hyundai, BMW, Mercedes, MG. The paint and the interiors differ; the care doesn't.",
  },
];

export default function EvPage() {
  const faqLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faq.map((f) => ({ "@type": "Question", name: f.q, acceptedAnswer: { "@type": "Answer", text: f.a } })),
  };
  const sms = smsHref("Hi Imperium, I'd like a quote for my EV.\nCar: \nSuburb: \nService: ");

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqLd) }} />

      <section className="container-x mx-auto grid max-w-6xl gap-10 py-14 md:grid-cols-12 md:items-center md:py-20">
        <div className="md:col-span-7">
          <Breadcrumbs items={[{ href: "/services/", label: "Services" }, { href: "/tesla-ev-detailing-canberra/", label: "Tesla and EV detailing" }]} />
          <p className="m-0 mt-4 text-[15px] text-muted-foreground">Soft paint. Glass roof. White seats. We know the car.</p>
          <h1 className="display-caps mt-3 text-5xl md:text-7xl">Tesla and EV detailing in Canberra.</h1>
          <p className="mt-6 max-w-[60ch] text-lg text-secondary-foreground">
            One in four new cars registered in the ACT is electric, and most of them wear paint that marks the first time it meets a brush. This is the detailing an EV actually needs: a careful hand wash, a light correction, and a coating that goes on while the car is still perfect. Done at your home, no call-out fee.
          </p>
          <p className="mt-4 max-w-[60ch] text-muted-foreground">For new Model 3 and Model Y owners, and anyone in a BYD, Polestar, Kia, Hyundai, BMW or Mercedes EV.</p>
          <div className="mt-7 flex flex-col gap-3 sm:flex-row">
            <LinkButton href={sms}>Text us your car</LinkButton>
            <LinkButton href={telHref} variant="ghost">
              Call {site.phoneDisplay}
            </LinkButton>
          </div>
          <p className="mt-4 text-[15px] text-muted-foreground">{site.quotePromise}</p>
        </div>
        <div className="md:col-span-5">
          <LoopVideo base="/media/beading-720" poster="/media/beading-poster.webp" label="Water beading tightly on freshly coated paint" className="panel-glow aspect-[4/5] w-full rounded-xl bg-card object-cover" />
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto grid max-w-6xl gap-12 py-14 md:grid-cols-12 md:py-20">
          <div className="md:col-span-7">
            <h2 className="display-caps text-3xl md:text-5xl">Why EV paint needs more care</h2>
            <div className="mt-6 grid max-w-[64ch] gap-4 text-[17px] text-secondary-foreground">
              <p className="m-0">
                Modern EV paint, Tesla&apos;s in particular, is thin and soft. It swirls under a car-wash brush, marks under a dry towel and shows every mistake in direct sun. The fix isn&apos;t to wash it less. It&apos;s to wash it properly and put something harder than the paint on top of it.
              </p>
              <p className="m-0">
                A single-stage correction removes the marring most EVs collect in their first months, including what the delivery centre left behind. A ceramic coating then takes the hits instead of the clear coat: UV, frost, sap, fallout and the wash itself.
              </p>
              <p className="m-0">
                The best time is the first few weeks, before the first automatic wash. Light correction, then a 5 or 7-year coating with the written warranty on our warranty page. A Model 3 is priced as a sedan and a Model Y as an SUV, like any other car.
              </p>
            </div>
          </div>
          <aside className="md:col-span-5">
            <div className="rounded-lg border border-border bg-card p-6">
              <h2 className="text-lg font-semibold">What&apos;s different on the day</h2>
              <ul className="mt-4 grid list-none gap-2.5 p-0 text-[15px] text-secondary-foreground">
                {onTheDay.map((t) => (
                  <li key={t} className="flex gap-3">
                    <span aria-hidden="true" className="mt-[.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto max-w-6xl py-14 md:py-20">
          <h2 className="display-caps text-3xl md:text-5xl">Same prices as any car</h2>
          <ul className="m-0 mt-8 grid list-none gap-3 p-0 sm:grid-cols-2 lg:grid-cols-3">
            {services.map((s) => (
              <li key={s.slug}>
                <Link href={`/services/${s.slug}/`} className="block h-full rounded-lg border border-border bg-card p-5 no-underline hover:border-secondary-foreground/40">
                  <h3 className="display-caps text-2xl">{s.name}</h3>
                  <p className="mt-2 text-[15px] text-muted-foreground">{s.forWho}</p>
                  <p className="mt-3 text-[15px] text-foreground">From {formatPrice(s.priceFrom)}</p>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto max-w-6xl py-14 md:py-20">
          <Faq items={faq} />
          <p className="mt-10 text-[15px] text-muted-foreground">
            Also see:{" "}
            <Link href="/learn/dealer-paint-protection-vs-ceramic-coating/" className="text-foreground underline underline-offset-4">
              dealer paint protection vs a ceramic coating
            </Link>
            .
          </p>
        </div>
      </section>

      <Booking title="Book your EV in." />
    </>
  );
}
