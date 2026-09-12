import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { services, getService, formatPrice } from "@/lib/services";
import { site, smsHref, telHref } from "@/lib/site";
import { Picture } from "@/components/site/picture";
import { LoopVideo } from "@/components/site/loop-video";
import { BeforeAfter } from "@/components/site/before-after";
import { Faq } from "@/components/site/faq";
import { LinkButton } from "@/components/site/link-button";
import { Booking } from "@/components/site/booking";
import { Breadcrumbs } from "@/components/site/breadcrumbs";
import { articles } from "@/lib/articles";

type Params = { slug: string };

export function generateStaticParams(): Params[] {
  return services.map((s) => ({ slug: s.slug }));
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { slug } = await params;
  const s = getService(slug);
  if (!s) return {};
  return { title: s.title, description: s.description, alternates: { canonical: `/services/${s.slug}/` } };
}

export default async function ServicePage({ params }: { params: Promise<Params> }) {
  const { slug } = await params;
  const s = getService(slug);
  if (!s) notFound();
  const related = s.related.map(getService).filter(Boolean);

  const faqLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: s.faq.map((f) => ({ "@type": "Question", name: f.q, acceptedAnswer: { "@type": "Answer", text: f.a } })),
  };
  const serviceLd = {
    "@context": "https://schema.org",
    "@type": "Service",
    name: s.name,
    serviceType: s.name,
    description: s.description,
    url: `${site.url}/services/${s.slug}/`,
    provider: { "@id": `${site.url}/#business` },
    areaServed: "Canberra and Queanbeyan",
    offers: { "@type": "Offer", priceCurrency: "AUD", price: s.priceFrom, priceSpecification: { "@type": "PriceSpecification", minPrice: s.priceFrom, priceCurrency: "AUD" } },
  };
  const reading = {
    "ceramic-coating-canberra": ["dealer-paint-protection-vs-ceramic-coating", "ceramic-coating-vs-paint-correction"],
    "paint-correction-canberra": ["ceramic-coating-vs-paint-correction", "car-detailing-cost-canberra"],
  }[s.slug] ?? ["car-detailing-cost-canberra"];
  const guides = reading.map((slug) => articles.find((a) => a.slug === slug)).filter((a) => a !== undefined);
  const more =
    s.slug === "ceramic-coating-canberra"
      ? [{ href: "/tesla-ev-detailing-canberra/", label: "Tesla and EV detailing" }, { href: "/warranty/", label: "The coating warranty" }]
      : [{ href: "/maintenance/", label: "Maintenance plans" }, { href: "/service-areas/", label: "Where we go" }];

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqLd) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(serviceLd) }} />

      <section className="container-x mx-auto grid max-w-6xl gap-10 py-14 md:grid-cols-12 md:items-center md:py-20">
        <div className="md:col-span-7">
          <Breadcrumbs items={[{ href: "/services/", label: "Services" }, { href: `/services/${s.slug}/`, label: s.name }]} />
          <p className="m-0 mt-4 text-[15px] text-muted-foreground">
            From <b className="font-medium text-foreground">{formatPrice(s.priceFrom)}</b> · {s.duration}
          </p>
          <h1 className="display-caps mt-3 text-5xl md:text-7xl">{s.h1}</h1>
          <p className="mt-6 max-w-[60ch] text-lg text-secondary-foreground">{s.intro}</p>
          <p className="mt-4 max-w-[60ch] text-muted-foreground">{s.forWho}</p>
          <div className="mt-7 flex flex-col gap-3 sm:flex-row">
            <LinkButton href={smsHref(`Hi Imperium, I'd like a quote for a ${s.name.toLowerCase()}.\nCar: \nSuburb: `)}>Text us your car</LinkButton>
            <LinkButton href={telHref} variant="ghost">
              Call {site.phoneDisplay}
            </LinkButton>
          </div>
          <p className="mt-4 text-[15px] text-muted-foreground">{site.quotePromise}</p>
        </div>
        <div className="md:col-span-5">
          {s.video ? (
            <LoopVideo base={s.video.base} poster={s.video.poster} label={s.imageAlt} className="panel-glow aspect-[4/5] w-full rounded-xl bg-card object-cover" />
          ) : (
            <Picture name={s.image} alt={s.imageAlt} sizes="(min-width: 768px) 40vw, 100vw" priority className="panel-glow aspect-[4/5] w-full rounded-xl object-cover" />
          )}
        </div>
      </section>

      {s.compare && <BeforeAfter {...s.compare} title="Swirls in. Gloss out." />}

      <section className="border-t border-border">
        <div className="container-x mx-auto grid max-w-6xl gap-12 py-14 md:grid-cols-12 md:py-20">
          <div className="md:col-span-7">
            <h2 className="display-caps text-3xl md:text-5xl">How we do it</h2>
            <div className="mt-6 grid max-w-[64ch] gap-4 text-[17px] text-secondary-foreground">
              {s.why.map((p) => (
                <p key={p.slice(0, 40)} className="m-0">
                  {p}
                </p>
              ))}
            </div>
          </div>
          <aside className="md:col-span-5">
            <div className="rounded-lg border border-border bg-card p-6">
              <h2 className="text-lg font-semibold">Every job, every time</h2>
              <ul className="mt-4 grid list-none gap-2.5 p-0 text-[15px] text-secondary-foreground">
                {s.included.map((i) => (
                  <li key={i} className="flex gap-3">
                    <span aria-hidden="true" className="mt-[.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                    {i}
                  </li>
                ))}
              </ul>
            </div>
            <div className="mt-4 rounded-lg border border-border p-6">
              <h2 className="text-lg font-semibold">On the day, we need</h2>
              <ul className="mt-4 grid list-none gap-2.5 p-0 text-[15px] text-muted-foreground">
                {s.needs.map((n) => (
                  <li key={n}>{n}</li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      </section>

      <section className="border-t border-border">
        <div className="container-x mx-auto max-w-6xl py-14 md:py-20">
          <Faq items={s.faq} />
          <div className="mt-12 grid gap-6 border-t border-border pt-8 md:grid-cols-2">
            <div>
              <h2 className="text-lg font-semibold">Keep reading</h2>
              <ul className="m-0 mt-3 grid list-none gap-2 p-0 text-[15px]">
                {guides.map((g) => (
                  <li key={g.slug}>
                    <Link href={`/learn/${g.slug}/`} className="link-slide text-secondary-foreground no-underline hover:text-foreground">
                      {g.h1}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h2 className="text-lg font-semibold">Also useful</h2>
              <ul className="m-0 mt-3 grid list-none gap-2 p-0 text-[15px]">
                {more.map((m) => (
                  <li key={m.href}>
                    <Link href={m.href} className="link-slide text-secondary-foreground no-underline hover:text-foreground">
                      {m.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          {related.length > 0 && (
            <p className="mt-10 text-[15px] text-muted-foreground">
              Also see:{" "}
              {related.map((r, i) => (
                <span key={r!.slug}>
                  <Link href={`/services/${r!.slug}/`} className="text-foreground underline underline-offset-4">
                    {r!.name}
                  </Link>
                  {i < related.length - 1 ? " and " : ""}
                </span>
              ))}
              .
            </p>
          )}
        </div>
      </section>

      <Booking title={`Book a ${s.name.toLowerCase()}.`} defaultService={s.name} />
    </>
  );
}
