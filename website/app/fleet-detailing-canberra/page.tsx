import type { Metadata } from "next";
import { og } from "@/lib/seo";
import Link from "next/link";
import { site, prices, telHref, smsHref } from "@/lib/site";
import { formatPrice } from "@/lib/services";
import { guidePrice, ceramicTiers, conditionRange, type JobId, type SizeId } from "@/lib/pricing";
import { fleetSegments, fleetProcess, fleetSiteNeeds, fleetPaperwork, fleetFaq } from "@/lib/fleet";
import { Faq } from "@/components/site/faq";
import { Picture } from "@/components/site/picture";
import { LinkButton } from "@/components/site/link-button";
import { Breadcrumbs } from "@/components/site/breadcrumbs";
import { FleetQuote } from "@/components/site/fleet-quote";

export const metadata: Metadata = {
  title: "Fleet Detailing Canberra",
  description:
    "Mobile fleet detailing for Canberra businesses. Utes, vans, pool cars and trucks done at your yard. Same price per vehicle, no call-out fee.",
  alternates: { canonical: "/fleet-detailing-canberra/" },
  openGraph: og("/fleet-detailing-canberra/", {
    title: "Fleet Detailing Canberra",
    description: "Utes, vans, pool cars and trucks detailed at your yard. Same price per vehicle a private customer pays.",
  }),
};

const COLS: { id: SizeId; label: string; eg: string }[] = [
  { id: "sedan", label: "Hatch or sedan", eg: "Corolla, Model 3, 3 Series" },
  { id: "suv", label: "SUV or ute", eg: "RAV4, Model Y, Ranger" },
  { id: "large", label: "4WD, van or 8-seater", eg: "LandCruiser, Patrol, Carnival" },
];

const ROWS: { job: JobId; label: string; note: string; href?: string }[] = [
  { job: "exterior", label: "Exterior detail", note: "About an hour", href: "/services/exterior-car-detailing-canberra/" },
  { job: "interior", label: "Interior detail", note: "About an hour and a half", href: "/services/interior-car-detailing-canberra/" },
  { job: "full", label: "Full detail", note: "About three hours on a sedan", href: "/services/full-car-detail-canberra/" },
  { job: "correction", label: "Paint correction", note: "Single stage, covered space", href: "/services/paint-correction-canberra/" },
  { job: "ceramic", label: "Ceramic coating", note: "3-year, rises with the warranty", href: "/services/ceramic-coating-canberra/" },
  { job: "maintenance", label: "Maintenance plan", note: "Per month, per vehicle", href: "/maintenance/" },
];

/** Every price on this page comes through here, so none of them is typed twice. */
const price = (job: JobId, size: SizeId) => {
  const g = guidePrice(job, size, 3);
  return g.price === null ? "quoted" : formatPrice(g.price);
};

const cell = (job: JobId, size: SizeId) => {
  const g = guidePrice(job, size, 3);
  if (g.price === null) return "Quoted";
  // The plan's price is a floor for a sedan, not a flat sedan rate.
  return `${job === "maintenance" ? "From " : ""}${formatPrice(g.price)}${g.suffix}`;
};

const P = ({ children }: { children: React.ReactNode }) => <p className="m-0">{children}</p>;

export default function FleetPage() {
  const faqLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: fleetFaq.map((f) => ({ "@type": "Question", name: f.q, acceptedAnswer: { "@type": "Answer", text: f.a } })),
  };
  // Only the three services this page actually sells to a fleet. Correction and
  // coating stay as Offers on their own service pages so the two don't compete.
  const serviceLd = {
    "@context": "https://schema.org",
    "@type": "Service",
    name: "Fleet detailing",
    serviceType: "Fleet and commercial vehicle detailing",
    provider: { "@id": `${site.url}/#business` },
    areaServed: { "@type": "AdministrativeArea", name: "Canberra, ACT and Queanbeyan, NSW" },
    url: `${site.url}/fleet-detailing-canberra/`,
    description:
      "Mobile detailing for businesses with more than one vehicle, at your yard, depot or office car park across Canberra and Queanbeyan.",
    hasOfferCatalog: {
      "@type": "OfferCatalog",
      name: "Fleet detailing per vehicle",
      itemListElement: ROWS.filter((r) => ["exterior", "interior", "full"].includes(r.job)).flatMap((r) =>
        COLS.map((c) => {
          const g = guidePrice(r.job, c.id, 3);
          return {
            "@type": "Offer",
            name: `${r.label} — ${c.label}`,
            priceCurrency: "AUD",
            price: g.price,
            priceSpecification: { "@type": "PriceSpecification", minPrice: g.price, priceCurrency: "AUD" },
          };
        }),
      ),
    },
  };

  const sms = smsHref("Hi Imperium, we'd like a fleet quote.\nBusiness: \nVehicles: \nWhere they park: ");

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqLd) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(serviceLd) }} />

      <section className="container-x mx-auto grid max-w-6xl gap-10 py-14 md:grid-cols-12 md:items-center md:py-20">
        <div className="md:col-span-7">
          <Breadcrumbs items={[{ href: "/services/", label: "Services" }, { href: "/fleet-detailing-canberra/", label: "Fleet detailing" }]} />
          <p className="m-0 mt-4 text-[15px] text-muted-foreground">Detailing, not a bulk wash. Same price per vehicle. No call-out fee.</p>
          <h1 className="display-caps mt-3 text-5xl md:text-7xl">Fleet detailing in Canberra and Queanbeyan.</h1>
          <p className="mt-6 max-w-[60ch] text-lg text-secondary-foreground">
            Detailing for businesses with more than one vehicle, done at your yard, your depot or the office car park. Every vehicle is priced by its
            size, the same as it would be for a private customer, with no call-out fee anywhere in the ACT or Queanbeyan.
          </p>
          <p className="mt-4 max-w-[60ch] text-muted-foreground">
            Put your vehicles into the estimator and the total is on screen before you send anything.
          </p>
          <div className="mt-7 flex flex-col gap-3 sm:flex-row">
            <LinkButton href="#book">Price your fleet</LinkButton>
            <LinkButton href={telHref} variant="ghost">
              Call {site.phoneDisplay}
            </LinkButton>
          </div>
          <p className="mt-4 text-[15px] text-muted-foreground">{site.quotePromise}</p>
        </div>
        <div className="md:col-span-5">
          <Picture
            name="fleet-lineup"
            alt="A line of white prime movers parked up after detailing"
            priority
            sizes="(min-width: 768px) 40vw, 100vw"
            className="panel-glow aspect-[4/5] w-full rounded-xl bg-card object-cover"
          />
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto max-w-6xl py-14 md:py-20">
          <h2 className="display-caps text-3xl md:text-5xl">Who we do commercial work for in Canberra</h2>
          <ul className="m-0 mt-8 grid list-none gap-x-10 gap-y-6 p-0 md:grid-cols-2">
            {fleetSegments.map((s) => (
              <li key={s.name} className="border-t border-border pt-4">
                <h3 className="text-[17px] font-semibold text-foreground">{s.name}</h3>
                <p className="m-0 mt-1.5 max-w-[52ch] text-[15px] text-muted-foreground">{s.line}</p>
              </li>
            ))}
          </ul>

          {/* The three photos further down this page are all trucks. Most fleet
              work is dual cabs, so the page should show one. */}
          <div className="mt-12 grid gap-4 sm:grid-cols-3">
            {[
              { name: "hilux-sr5", alt: "Grey Toyota HiLux SR5 dual cab, washed and dried, on a driveway", title: "Toyota HiLux SR5", kind: "Dual cab" },
              { name: "ranger-wildtrak", alt: "Silver Ford Ranger Wildtrak dual cab, finished, in a workshop shed", title: "Ford Ranger Wildtrak", kind: "Dual cab" },
              { name: "rav4-hybrid", alt: "Black Toyota RAV4 Hybrid, washed and dried, outside a shed", title: "Toyota RAV4 Hybrid", kind: "Pool car" },
            ].map((f) => (
              <figure key={f.name} className="zoom-media relative m-0 aspect-[4/5] overflow-hidden rounded-xl bg-card">
                <Picture name={f.name} alt={f.alt} sizes="(min-width: 640px) 30vw, 100vw" className="absolute inset-0 h-full w-full object-cover" />
                <figcaption className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-background/90 to-transparent p-5 pt-14">
                  <span className="display-caps block text-2xl">{f.title}</span>
                  <span className="text-sm text-secondary-foreground">{f.kind}</span>
                </figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto max-w-6xl py-14 md:py-20">
          <h2 className="display-caps text-3xl md:text-5xl">Fleet prices in Canberra: the same per car a private customer pays</h2>
          <p className="mt-6 max-w-[64ch] text-[17px] text-secondary-foreground">
            There is no fleet rate here, and no bulk discount. A ute in a line of six is priced the same as a ute on a driveway in Chifley, because it
            is the same work. Two people, one van, and car six takes the same hours as car one. We would rather you read that here than find it out on
            the phone. Nothing is marked up because you are a business either.
          </p>

          <div
            tabIndex={0}
            role="region"
            aria-label="Fleet prices by service and vehicle size"
            className="-mx-4 mt-8 overflow-x-auto px-4 focus-visible:outline-2 focus-visible:outline-ring"
          >
            <table className="w-full min-w-[42rem] border-collapse text-[15px]">
              <caption className="sr-only">Price per vehicle by service and vehicle size, in Australian dollars</caption>
              <thead>
                <tr>
                  <th scope="col" className="border-b border-border py-3 pr-4 text-left font-semibold">
                    Per vehicle
                  </th>
                  {COLS.map((c) => (
                    <th key={c.id} scope="col" className="border-b border-border px-4 py-3 text-right font-semibold">
                      {c.label}
                      <span className="block text-xs font-normal text-muted-foreground">{c.eg}</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ROWS.map((r) => (
                  <tr key={r.job}>
                    <th scope="row" className="border-b border-border py-3 pr-4 text-left font-normal">
                      {r.href ? (
                        <Link href={r.href} className="font-semibold text-foreground underline underline-offset-4">
                          {r.label}
                        </Link>
                      ) : (
                        <span className="font-semibold text-foreground">{r.label}</span>
                      )}
                      <span className="block text-xs text-muted-foreground">{r.note}</span>
                    </th>
                    {COLS.map((c) => (
                      <td key={c.id} className="border-b border-border px-4 py-3 text-right tabular-nums text-secondary-foreground">
                        {cell(r.job, c.id)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-8 grid max-w-[64ch] gap-4 text-[17px] text-secondary-foreground">
            <P>
              Ceramic coating rises with the warranty you pick. On a hatch or sedan it is {formatPrice(ceramicTiers.sedan[3])},{" "}
              {formatPrice(ceramicTiers.sedan[5])} or {formatPrice(ceramicTiers.sedan[7])} for three, five or seven years. On an SUV or ute,{" "}
              {formatPrice(ceramicTiers.suv[3])}, {formatPrice(ceramicTiers.suv[5])} or {formatPrice(ceramicTiers.suv[7])}. On a 4WD, van or
              8-seater, {formatPrice(ceramicTiers.large[3])}, {formatPrice(ceramicTiers.large[5])} or {formatPrice(ceramicTiers.large[7])}.
            </P>
            <P>
              Paint correction is priced for a single-stage machine correction, which is what takes swirl marks and haze out. Deeper scratches need a
              multi-stage job and we quote that from photos rather than off this table.
            </P>
            <P>
              Full and interior details can carry up to {formatPrice(conditionRange)} a vehicle for condition. On a work fleet, assume that is live.
              It is agreed with you before we start and never added afterwards, and across a run of vehicles we would rather price it from photos up
              front than have that conversation eight times in your car park.
            </P>
            <P>
              A motorbike full detail is {price("full", "bike")}. Trucks we quote over the phone, because a prime mover, a tipper and a rigid are not the same job and
              none of them comes off a price list.
            </P>
            <P>
              What is not on the invoice: a call-out fee anywhere in the ACT or Queanbeyan, a travel fee, a card fee, or a charge for water and power.
              The tap and the power point are yours, so that part comes off your supply.
            </P>
          </div>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto max-w-6xl py-14 md:py-20">
          <h2 className="display-caps text-3xl md:text-5xl">Two vehicles is a fleet here</h2>
          <div className="mt-6 grid max-w-[64ch] gap-4 text-[17px] text-secondary-foreground">
            <P>
              Two utes for a sparky. A work ute, a partner&apos;s SUV and the good car parked at one house and invoiced to the business. Three cars in
              the staff bays behind an agency in Kingston. That is a normal day for us and it books the way a single car does.
            </P>
            <P>
              Small is not a compromise, it is the good version of this work. Everything sits at one address, so no part of the day goes on driving
              between suburbs, and one person can usually approve it without a purchase order.
            </P>
            <P>
              If you want to try us on one vehicle before you hand over the rest, do that. One vehicle costs what it costs, {price("exterior", "suv")} for an
              exterior detail on a ute or {price("full", "suv")} for a full detail, and nothing about the price changes when you come back with the other
              five.
            </P>
          </div>
        </div>
      </section>

      <section id="book" className="border-t border-border">
        <FleetQuote />
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto grid max-w-6xl gap-12 py-14 md:grid-cols-12 md:py-20">
          <div className="md:col-span-7">
            <h2 className="display-caps text-3xl md:text-5xl">What your site needs: an outdoor tap and a 240V power point</h2>
            <div className="mt-6 grid max-w-[64ch] gap-4 text-[17px] text-secondary-foreground">
              <P>
                You supply two things: an outdoor tap we can run a hose from, and a standard 240V power point within reach. We bring everything else,
                including the machines, the chemicals and the towels. There is no shop and no drop-off, so the vehicles never leave your site and
                nobody on your payroll spends a morning ferrying cars to a wash bay and back.
              </P>
              <P>
                A basement or a shared car park works on the same two things plus one more: the building has to be happy for a contractor to work on
                vehicles down there. Your facilities manager can normally answer that in one call. It is worth asking before the booking rather than on
                the morning.
              </P>
              <P>
                If the yard has neither a tap nor a power point, say so on the form. Most fleets get around it by having us come to whichever address
                does have both, whether that is head office, a workshop or somebody&apos;s place. We would rather tell you that on the phone than turn
                up and find out.
              </P>
            </div>
          </div>
          <aside className="md:col-span-5">
            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="text-lg font-semibold">Before you book</h3>
              <ul className="mt-4 grid list-none gap-2.5 p-0 text-[15px] text-secondary-foreground">
                {fleetSiteNeeds.map((n) => (
                  <li key={n} className="flex gap-3">
                    <span aria-hidden="true" className="mt-[.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                    {n}
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto grid max-w-6xl gap-12 py-14 md:grid-cols-12 md:items-center md:py-20">
          <div className="md:col-span-7">
            <h2 className="display-caps text-3xl md:text-5xl">Ute, van and truck fleets: trades, transport and site vehicles</h2>
            <div className="mt-6 grid max-w-[64ch] gap-4 text-[17px] text-secondary-foreground">
              <P>
                A signwritten ute is the biggest advertisement most trades businesses own, and it spends its life under site dust. An exterior detail
                is about an hour a vehicle and takes the dust and road film off the graphics as well as the paint.
              </P>
              <P>
                Utes are priced as an SUV: {price("exterior", "suv")} for an exterior detail, {price("interior", "suv")} for an interior, {price("full", "suv")} for a
                full detail. Vans, 4WDs and 8-seaters are the large price, at {price("exterior", "large")}, {price("interior", "large")} and{" "}
                {price("full", "large")}. Trays,
                canopies, roof racks and fitted-out van shelving are more work than an empty tub, so tell us what is on the vehicle and we will price
                it before the day rather than on it.
              </P>
              <P>
                Trucks are their own thing. Prime movers, tippers and rigids all get quoted over the phone, because the size, the height and how dirty
                it has got are what decide the job, not a line on a price list.
              </P>
              <P>
                The practical version is that we come to the yard, not the site, on a day the whole line-up is parked up. We work along the line and
                the vehicles stay where they are. A yard in Hume or Mitchell costs the same to get to as a car park in Braddon, because there is no
                travel fee anywhere in the ACT.
              </P>
              <P>
                Interiors on a work fleet are their own job. Site dust, servo food, dog hair, and a cab that doubles as an office. That is exactly what
                the up-to-{formatPrice(conditionRange)} condition allowance exists for. Send photos of the worst two with your enquiry and we will
                price it in before the day.
              </P>
            </div>
          </div>
          <div className="md:col-span-5">
            <Picture
              name="fleet-tipper"
              alt="A white tipper truck cleaned down outside a workshop"
              sizes="(min-width: 768px) 40vw, 100vw"
              className="aspect-[4/5] w-full rounded-xl bg-card object-cover"
            />
          </div>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto max-w-6xl py-14 md:py-20">
          <h2 className="display-caps text-3xl md:text-5xl">Agent cars, pool cars and company cars</h2>
          <div className="mt-6 grid max-w-[64ch] gap-4 text-[17px] text-secondary-foreground">
            <P>
              An agent puts buyers in the passenger seat every weekend, which makes the inside of the car part of the listing. Agent cars wear out on
              the interior long before the paint gives up, so the repeat purchase here is an interior detail, at {price("interior", "sedan")} for a hatch or
              sedan and {price("interior", "suv")} for an SUV, with a full detail before a campaign.
            </P>
            <P>
              The shape that works is the office car park. Several cars done in one visit, no travel between them, and nobody loses a car for a day at
              a shop. Staff bays in Kingston, Manuka, Braddon, Barton, Phillip, Belconnen and Gungahlin are all inside the no-call-out-fee area, so a
              visit to any of them costs the same.
            </P>
            <P>
              If the pool cars are electric, the{" "}
              <Link href="/tesla-ev-detailing-canberra/" className="text-foreground underline underline-offset-4">
                EV detailing page
              </Link>{" "}
              covers what changes: soft paint, cameras and sensors, light interiors. The prices are the same as any other car of that size.
            </P>
            <P>
              One note on leased and salary-packaged cars, because an office manager often ends up arranging these for staff. A hand-back detail is
              priced the same as any other detail, by size. What your novated lease does or does not cover is a question for your leasing company, not
              for us, and we will not pretend to know.
            </P>
          </div>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto max-w-6xl py-14 md:py-20">
          <h2 className="display-caps text-3xl md:text-5xl">Car yards: per car, not per yard</h2>
          <div className="mt-6 grid max-w-[64ch] gap-4 text-[17px] text-secondary-foreground">
            <P>We are not a lot-washing service and we will not pretend to be one. What we are useful for is the single car that has to photograph properly.</P>
            <P>
              One dark trade-in corrected so the paint holds a reflection instead of throwing haze across every photo is {price("correction", "sedan")} on a hatch
              or sedan, {price("correction", "suv")} on an SUV or ute and {price("correction", "large")} on a 4WD or van, done at your yard. That is a single-stage
              correction; a car that needs more than that gets quoted from photos first. A full detail on an individual unit before it goes up is{" "}
              {price("full", "sedan")} to {price("full", "large")} by size.
            </P>
            <P>
              Two constraints before you ask. Correction and coating need covered space for the day, so if every car on the lot sits in the open we
              cannot do that work there. And it is per vehicle at card prices. If what you need is twenty units presented quickly at a trade rate, we
              are the wrong supplier, and we would rather say so now than waste a fortnight of your time.
            </P>
          </div>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto grid max-w-6xl gap-12 py-14 md:grid-cols-12 md:items-center md:py-20">
          <div className="md:col-span-7">
            <h2 className="display-caps text-3xl md:text-5xl">Correcting, coating and keeping a fleet that way</h2>
            <div className="mt-6 grid max-w-[64ch] gap-4 text-[17px] text-secondary-foreground">
              <P>
                Paint correction and ceramic coating are both per vehicle, both need a garage or covered space out of direct sun, wind and dust, and
                both are done one vehicle at a time. A fleet parked outside in a yard cannot be corrected or coated there, and a coated vehicle wants
                to stay undercover for 24 hours after the coating goes on.
              </P>
              <P>
                Before a fleet spends that, be honest about how the vehicles get washed, because we will be. The{" "}
                <Link href="/warranty/" className="text-foreground underline underline-offset-4">
                  written warranty
                </Link>{" "}
                asks for a pH-neutral, two-bucket hand wash and specifically excludes automatic washes with spinning brushes. If your drivers put the
                utes through the brush wash at the servo every second Friday, the coating will not last and the warranty will not cover the result. In
                that case regular details, or a plan where we do the washing, is the better spend, and we will say so.
              </P>
              <P>
                Keeping them that way is a different product. A maintenance plan is us coming back on a schedule. The exterior plan starts at{" "}
                {price("maintenance", "sedan")} a month for a hatch or sedan and inside and out starts at {formatPrice(prices.maintenanceMonthly)}, with larger vehicles quoted for
                the vehicle. What a visit covers is set out on the{" "}
                <Link href="/maintenance/" className="text-foreground underline underline-offset-4">
                  maintenance plans page
                </Link>
                , including why most vehicles start with a full detail so every visit after that is maintenance rather than recovery.
              </P>
            </div>
          </div>
          <div className="md:col-span-5">
            <Picture
              name="fleet-prime-mover"
              alt="A white prime mover washed down, standing on wet concrete at night"
              sizes="(min-width: 768px) 40vw, 100vw"
              className="aspect-[4/5] w-full rounded-xl bg-card object-cover"
            />
          </div>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto max-w-6xl py-14 md:py-20">
          <h2 className="display-caps text-3xl md:text-5xl">How a fleet booking runs</h2>
          <ol className="m-0 mt-8 grid list-none gap-6 p-0 md:grid-cols-2">
            {fleetProcess.map((s, i) => (
              <li key={s.step} className="flex gap-4 border-t border-border pt-4">
                <span aria-hidden="true" className="display-caps shrink-0 text-2xl leading-none text-accent">
                  {i + 1}
                </span>
                <span>
                  <h3 className="text-[17px] font-semibold text-foreground">{s.step}</h3>
                  <p className="m-0 mt-1.5 max-w-[52ch] text-[15px] text-muted-foreground">{s.detail}</p>
                </span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto max-w-6xl py-14 md:py-20">
          <h2 className="display-caps text-3xl md:text-5xl">What we don&apos;t do</h2>
          <div className="mt-6 grid max-w-[64ch] gap-4 text-[17px] text-secondary-foreground">
            <P>We do not fit paint protection film, we do not tint windows and we do not repair rims. If PPF is already on a vehicle, we will ceramic coat over it.</P>
            <P>
              We are not a bulk wash service. An exterior detail is an hour of hand work on one vehicle, not a pass through a machine. If what the fleet needs is a cheap weekly wash, that is a different product at a different price and we are not trying to match
              it.
            </P>
            <P>
              We are not a panel supplier. Prequalification, service level agreements and fifty-vehicle arrangements are more than two people and one
              van can hold. One team, one depot, or one office with a handful of vehicles is the right size for us.
            </P>
            <P>
              We will not promise a fleet finished overnight. There are two of us and one van, and those days are shared with every other customer.
              Send your numbers and you will get real dates rather than a figure that sounds good on a page.
            </P>
            <P>A garden tap and one power point will not service a bus yard.</P>
          </div>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto grid max-w-6xl gap-12 py-14 md:grid-cols-12 md:py-20">
          <div className="md:col-span-5">
            <h2 className="display-caps text-3xl md:text-5xl">For your accounts people</h2>
            <div className="mt-6 grid gap-4 text-[17px] text-secondary-foreground">
              <P>
                Other businesses trust us with their vehicles. We have not asked them for permission to use their names, so you will not find a wall
                of client logos here.
              </P>
              <P>
                What we can show you is the work: {site.stats.cars} cars detailed in the last year, and {site.stats.rating} from{" "}
                {site.stats.reviewCount}{" "}
                <Link href="/reviews/" className="text-foreground underline underline-offset-4">
                  Google reviews
                </Link>
                , which are there to be read rather than taken on trust.
              </P>
              <P>
                If your site needs paperwork before we come through the gate, ask when you enquire and we will tell you exactly what we can send. Our
                full{" "}
                <Link href="/terms/" className="text-foreground underline underline-offset-4">
                  terms
                </Link>{" "}
                cover access, weather and workmanship.
              </P>
            </div>
          </div>
          <div className="md:col-span-7">
            <dl className="m-0 grid gap-0">
              {fleetPaperwork.map((r) => (
                <div key={r.term} className="grid gap-1 border-b border-border py-4 sm:grid-cols-4 sm:gap-4">
                  <dt className="text-[15px] font-semibold text-foreground">{r.term}</dt>
                  <dd className="m-0 text-[15px] text-muted-foreground sm:col-span-3">{r.detail}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto max-w-6xl py-14 md:py-20">
          <h2 className="display-caps text-3xl md:text-5xl">Where we come, at no call-out fee</h2>
          <div className="mt-6 grid max-w-[64ch] gap-4 text-[17px] text-secondary-foreground">
            <P>
              There is no call-out fee and no travel fee anywhere in the ACT or in Queanbeyan NSW. A depot in Hume costs the same to get to as an
              office car park in Braddon.
            </P>
            <P>
              We cover eight ACT districts —{" "}
              <Link href="/service-areas/inner-north-canberra/" className="text-foreground underline underline-offset-4">
                Inner North
              </Link>
              ,{" "}
              <Link href="/service-areas/inner-south-canberra/" className="text-foreground underline underline-offset-4">
                Inner South
              </Link>
              ,{" "}
              <Link href="/service-areas/gungahlin/" className="text-foreground underline underline-offset-4">
                Gungahlin
              </Link>
              ,{" "}
              <Link href="/service-areas/belconnen/" className="text-foreground underline underline-offset-4">
                Belconnen
              </Link>
              ,{" "}
              <Link href="/service-areas/woden-valley/" className="text-foreground underline underline-offset-4">
                Woden Valley
              </Link>
              ,{" "}
              <Link href="/service-areas/weston-creek/" className="text-foreground underline underline-offset-4">
                Weston Creek
              </Link>
              ,{" "}
              <Link href="/service-areas/tuggeranong/" className="text-foreground underline underline-offset-4">
                Tuggeranong
              </Link>{" "}
              and{" "}
              <Link href="/service-areas/molonglo-valley/" className="text-foreground underline underline-offset-4">
                Molonglo Valley
              </Link>{" "}
              — plus{" "}
              <Link href="/service-areas/queanbeyan/" className="text-foreground underline underline-offset-4">
                Queanbeyan
              </Link>{" "}
              across the border.{" "}
              <Link href="/service-areas/" className="text-foreground underline underline-offset-4">
                Nine service areas
              </Link>{" "}
              in total. If your yard sits outside them, ring us and we will tell you honestly whether we can get there.
            </P>
          </div>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto max-w-6xl py-14 md:py-20">
          <Faq items={fleetFaq} title="Fleet detailing questions we get asked" />
          <p className="mt-10 text-[15px] text-muted-foreground">
            Also see:{" "}
            <Link href="/learn/car-detailing-cost-canberra/" className="text-foreground underline underline-offset-4">
              what car detailing costs in Canberra
            </Link>
            , or text the numbers straight to{" "}
            <a href={sms} className="text-foreground underline underline-offset-4">
              {site.phoneDisplay}
            </a>
            . Four utes exterior, two sedans full detail, Braddon, is enough for us to price it.
          </p>
        </div>
      </section>

      {/* Not <CtaBand>: its button is "Text us your car" with a one-car message
          template, which is the wrong ask at the bottom of a fleet page. */}
      <section className="border-t border-border bg-card/40 py-14 md:py-20">
        <div className="container-x mx-auto flex max-w-6xl flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="display-caps text-4xl md:text-6xl">Send us the fleet.</h2>
            <p className="mt-4 max-w-[52ch] text-muted-foreground">
              Tell us what the fleet is made of and where it parks. We come back with the price per vehicle, how many days it takes, and the dates we
              have open.
            </p>
          </div>
          <div className="flex shrink-0 flex-col gap-3 sm:flex-row">
            <LinkButton href="#book">Price your fleet</LinkButton>
            <LinkButton href={sms} variant="ghost">
              Text the numbers
            </LinkButton>
          </div>
        </div>
      </section>
    </>
  );
}
