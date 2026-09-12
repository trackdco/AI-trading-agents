import Link from "next/link";
import { areas } from "@/lib/areas";
import { site } from "@/lib/site";
import { SectionHeading } from "@/components/site/section-heading";

// A real sequence, so the numbering carries information.
const steps = [
  {
    n: "1",
    h: "Text us your car and suburb",
    p: `A photo helps. ${site.quotePromise} The quote is fixed once we've seen the car: no surprise invoices.`,
  },
  {
    n: "2",
    h: "We arrive with everything",
    p: "An unmarked van with the gear, the product and the people. You need an outdoor tap and a 240V power point within reach; correction and coating also need a garage or covered space.",
  },
  {
    n: "3",
    h: "Handover",
    p: "We send a photo when we're done, walk you through the finish, and take card or transfer once you're happy. Coated cars leave with a wash guide and a written warranty.",
  },
];

export function Process() {
  return (
    <section id="how" className="relative border-t border-border py-20 md:py-28">
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 bg-[radial-gradient(50%_40%_at_15%_20%,rgba(31,111,196,0.12),transparent_70%)]" />
      <div className="container-x relative mx-auto max-w-6xl">
        <SectionHeading title="We come to you." intro="No shop to drop the car at. Your driveway, your apartment car park or your workplace, anywhere in Canberra and Queanbeyan, for the same price." />
        <div className="relative">
          <span aria-hidden="true" data-draw className="absolute inset-x-0 top-0 block h-px bg-secondary-foreground/40" />
          <ol className="m-0 grid list-none gap-10 p-0 pt-8 md:grid-cols-3 md:gap-8">
            {steps.map((s) => (
              <li key={s.n} data-reveal="up">
                <span className="display-caps block text-[clamp(3.5rem,7vw,6rem)] leading-none text-accent">{s.n}</span>
                <h3 className="mt-4 text-xl font-semibold">{s.h}</h3>
                <p className="mt-3 max-w-[38ch] text-[15px] text-muted-foreground">{s.p}</p>
              </li>
            ))}
          </ol>
        </div>

        <div className="mt-20" data-reveal="up">
          <h3 className="display-caps text-3xl">Nine districts, one van.</h3>
          <ul className="mt-5 flex list-none flex-wrap gap-2 p-0">
            {areas.map((a) => (
              <li key={a.slug}>
                <Link
                  href={`/service-areas/${a.slug}/`}
                  className="inline-flex min-h-[44px] items-center rounded-full border border-border px-5 text-[15px] text-secondary-foreground no-underline transition-colors hover:border-secondary-foreground/60 hover:text-foreground"
                >
                  {a.name}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
