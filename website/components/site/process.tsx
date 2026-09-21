import Link from "next/link";
import { areas } from "@/lib/areas";
import { site } from "@/lib/site";
import { SectionHeading } from "@/components/site/section-heading";
import { LoopVideo } from "@/components/site/loop-video";

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

        {/* The three steps say what happens. This is the middle one happening. */}
        <div className="mt-16 grid items-center gap-8 md:mt-20 md:grid-cols-12" data-reveal="up">
          <div className="md:col-span-5">
            <LoopVideo
              base="/media/m4-wash-720"
              poster="/media/m4-wash-poster.webp"
              label="A BMW M4 washed on site: snow foam and a rinse, a hand wash with a mitt, then dried with an Imperium Detailing towel"
              className="panel-glow aspect-[4/5] w-full rounded-xl bg-card object-cover"
            />
          </div>
          <div className="md:col-span-7">
            <h3 className="display-caps text-3xl">What the wash actually is.</h3>
            <p className="mt-5 max-w-[52ch] text-[17px] text-secondary-foreground">
              Snow foam and a rinse first, so the grit lifts before a mitt ever touches the paint. Then a two-bucket hand wash, panel by panel. Iron
              decon and a clay bar pull out what the wash cannot, a ceramic sealant goes on, and the car is dried by hand. Nothing spins, and nothing
              gets dragged across the clear coat.
            </p>
            <p className="mt-4 max-w-[52ch] text-[15px] text-muted-foreground">
              That is our own drying towel in the clip, and our own gear in the van. All we need from the house is the tap and the power point.
            </p>
          </div>
        </div>

        <div className="mt-20" data-reveal="up">
          <h3 className="display-caps text-3xl">Nine service areas, one van.</h3>
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
          {/* The fleet page had one contextual link into it, from /services/. A
              business owner landing here had no way of knowing the work exists. */}
          <p className="mt-6 max-w-[60ch] text-[15px] text-muted-foreground">
            More than one vehicle?{" "}
            <Link href="/fleet-detailing-canberra/" className="text-foreground underline underline-offset-4">
              Fleet and business detailing
            </Link>{" "}
            is priced per car, at your yard, your depot or the office car park. Utes, vans, pool cars and trucks.
          </p>
        </div>
      </div>
    </section>
  );
}
