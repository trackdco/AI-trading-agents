import type { Metadata } from "next";
import Link from "next/link";
import { site, smsHref, telHref } from "@/lib/site";
import type { Faq as FaqItem } from "@/lib/services";
import { Picture } from "@/components/site/picture";
import { Faq } from "@/components/site/faq";
import { LinkButton } from "@/components/site/link-button";
import { Booking } from "@/components/site/booking";

export const metadata: Metadata = {
  title: "Car Maintenance Plans Canberra (Mobile)",
  description:
    "A regular maintenance plan from Imperium Detailing: we come back every 2, 4 or 8 weeks for a coating-safe hand wash and interior reset, at your home or work across Canberra and Queanbeyan.",
  alternates: { canonical: "/maintenance/" },
};

const rhythms = [
  {
    every: "Every 2 weeks",
    who: "Daily drivers that live on the street, dark colours that show every mark, cars that carry kids or dogs.",
    note: "It never looks washed. It looks detailed.",
  },
  {
    every: "Every 4 weeks",
    who: "Most cars. Garaged overnight, driven daily, and you want it to stay the way we left it.",
    note: "The rhythm we recommend for coated cars.",
  },
  {
    every: "Every 8 weeks",
    who: "Weekend and second cars, low kilometres, mostly under cover.",
    note: "Enough to keep a coating clean and working.",
  },
];

const visit = [
  "Pre-rinse and snow foam, so grit lifts off before anything touches the paint",
  "Two-bucket, pH-neutral hand wash with clean mitts, never a brush",
  "Wheels, tyres and arches cleaned, tyres dressed",
  "Door jambs, and glass inside and out",
  "Interior vacuum, with the dash, console and door cards wiped down",
  "Bonded contamination checked and spot-treated",
  "Protection topped up: a coating booster on coated cars, a sealant on the rest",
  "A quick note on anything we notice: stone chips, swirl marks, coating health",
];

const faq: FaqItem[] = [
  {
    q: "Does the car need a full detail first?",
    a: "Usually, unless we've detailed it in the last few months. A plan keeps a finish; it doesn't chase one. We start with a full detail so every visit after that is maintenance, not recovery.",
  },
  {
    q: "How is it priced?",
    a: "One fixed price per visit, quoted for your car from its size, colour and how it's used. It's the same number every visit, and the number you're quoted is the number you pay.",
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
    a: "Yes. Start on one rhythm and move to another as the seasons change. Winter grit and spring pollen usually call for closer visits; a garaged summer needs fewer.",
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
          <p className="m-0 text-[15px] text-muted-foreground">Every 2, 4 or 8 weeks. One fixed price per visit.</p>
          <h1 className="display-caps mt-3 text-5xl md:text-7xl">Detailed once. Kept that way.</h1>
          <p className="mt-6 max-w-[60ch] text-lg text-secondary-foreground">
            A maintenance plan is us coming back on a schedule: a proper hand wash, the interior reset, the protection topped up. The car never slides back to needing a full detail, and a coated car gets the life it was promised.
          </p>
          <p className="mt-4 max-w-[60ch] text-muted-foreground">
            {"For daily drivers that live outside, dark cars that show every wash mark, family cars, and anyone who'd rather spend Saturday morning on something other than a bucket."}
          </p>
          <div className="mt-7 flex flex-col gap-3 sm:flex-row">
            <LinkButton href={sms}>Text us your car</LinkButton>
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
          <h2 className="display-caps text-3xl md:text-5xl">Pick a rhythm.</h2>
          <p className="mt-4 max-w-[58ch] text-lg text-muted-foreground">{"We'll suggest one when we quote. You can change it any time."}</p>
          <div className="mt-8 grid gap-px overflow-hidden rounded-lg border border-border bg-border">
            {rhythms.map((r) => (
              <div key={r.every} className="grid gap-3 bg-background p-5 md:grid-cols-12 md:items-baseline md:p-6">
                <h3 className="display-caps m-0 text-3xl md:col-span-3">{r.every}</h3>
                <p className="m-0 text-[15px] text-secondary-foreground md:col-span-6">{r.who}</p>
                <p className="m-0 text-[15px] text-muted-foreground md:col-span-3 md:text-right">{r.note}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto grid max-w-6xl gap-12 py-14 md:grid-cols-12 md:py-20">
          <div className="md:col-span-7">
            <h2 className="display-caps text-3xl md:text-5xl">What a visit covers</h2>
            <ul className="mt-6 grid max-w-[64ch] list-none gap-2.5 p-0 text-[17px] text-secondary-foreground">
              {visit.map((t) => (
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
