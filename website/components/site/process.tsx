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
    <section id="how" className="border-t border-border py-16 md:py-24">
      <div className="container-x mx-auto max-w-6xl">
        <SectionHeading title="We come to you." intro="No shop to drop the car at. Your driveway, your apartment car park or your workplace, anywhere in Canberra and Queanbeyan, for the same price." />
        <ol className="m-0 grid list-none gap-8 p-0 md:grid-cols-3">
          {steps.map((s) => (
            <li key={s.n} className="border-t border-border pt-5">
              <span className="display block text-4xl text-muted-foreground">{s.n}</span>
              <h3 className="mt-3 text-xl font-semibold">{s.h}</h3>
              <p className="mt-2 text-[15px] text-muted-foreground">{s.p}</p>
            </li>
          ))}
        </ol>

        <div className="mt-14">
          <h3 className="text-xl font-semibold">Nine districts, one van.</h3>
          <ul className="mt-4 flex list-none flex-wrap gap-2 p-0">
            {areas.map((a) => (
              <li key={a.slug}>
                <Link
                  href={`/service-areas/${a.slug}/`}
                  className="inline-flex min-h-[44px] items-center rounded-md border border-border px-4 text-[15px] text-secondary-foreground no-underline hover:border-secondary-foreground/50 hover:text-foreground"
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
