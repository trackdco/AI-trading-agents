import type { Metadata } from "next";
import { og } from "@/lib/seo";
import Link from "next/link";
import { notFound } from "next/navigation";
import { areas, getArea } from "@/lib/areas";
import { getService, services, formatPrice } from "@/lib/services";
import { site } from "@/lib/site";
import { Booking } from "@/components/site/booking";
import { Breadcrumbs } from "@/components/site/breadcrumbs";

type Params = { slug: string };

export function generateStaticParams(): Params[] {
  return areas.map((a) => ({ slug: a.slug }));
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { slug } = await params;
  const a = getArea(slug);
  if (!a) return {};
  return {
    title: `Mobile Car Detailing ${a.name}`,
    description: `Mobile detailing, ceramic coating and paint correction in ${a.name}: ${a.suburbs.slice(0, 3).join(", ")} and nearby. We come to you, no call-out fee.`,
    alternates: { canonical: `/service-areas/${a.slug}/` }, openGraph: og(`/service-areas/${a.slug}/`),
  };
}

export default async function AreaPage({ params }: { params: Promise<Params> }) {
  const { slug } = await params;
  const a = getArea(slug);
  if (!a) notFound();
  const best = getService(a.bestForSlug);

  return (
    <>
      <section className="container-x mx-auto max-w-6xl py-14 md:py-20">
        <Breadcrumbs items={[{ href: "/service-areas/", label: "Areas we serve" }, { href: `/service-areas/${a.slug}/`, label: a.name }]} />
        <h1 className="display-caps mt-3 text-5xl md:text-7xl">Mobile car detailing in {a.name}.</h1>
        {a.intro.map((t, i) => (
          <p key={i} className={`max-w-[62ch] text-secondary-foreground ${i === 0 ? "mt-6 text-lg" : "mt-4"}`}>
            {t}
          </p>
        ))}
        <p className="mt-4 max-w-[62ch] text-muted-foreground">{site.quotePromise}</p>

        {/* The substance of the page. Nine near-identical pages is how a set of
            location pages gets ignored, and this is what makes each its own. */}
        <div className="mt-12 grid gap-x-10 gap-y-10 md:grid-cols-3">
          {a.sections.map((sec) => (
            <section key={sec.h}>
              <h2 className="display-caps text-2xl md:text-[1.75rem]">{sec.h}</h2>
              {sec.p.map((t, i) => (
                <p key={i} className="mt-3 text-[15px] leading-relaxed text-secondary-foreground">
                  {t}
                </p>
              ))}
            </section>
          ))}
        </div>

        <div className="mt-10 grid gap-8 md:grid-cols-12">
          <div className="md:col-span-7">
            <h2 className="text-lg font-semibold">Suburbs we cover in {a.name}</h2>
            <ul className="mt-3 flex list-none flex-wrap gap-2 p-0">
              {a.suburbs.map((s) => (
                <li key={s} className="rounded-md border border-border px-3 py-1.5 text-[15px] text-secondary-foreground">
                  {s}
                </li>
              ))}
            </ul>
          </div>
          <div className="md:col-span-5">
            {best && (
              <Link href={`/services/${best.slug}/`} className="block rounded-lg border border-border bg-card p-6 no-underline hover:border-secondary-foreground/40">
                <p className="m-0 text-sm text-muted-foreground">Most booked in {a.name}</p>
                <h2 className="display-caps mt-1 text-3xl">{best.name}</h2>
                <p className="mt-2 text-[15px] text-muted-foreground">{best.description}</p>
                <p className="mt-3 text-[15px] text-foreground">From {formatPrice(best.priceFrom)}</p>
              </Link>
            )}
          </div>
        </div>

        <div className="mt-12">
          <h2 className="text-lg font-semibold">Every service, at your door</h2>
          <ul className="mt-3 grid list-none gap-2 p-0 sm:grid-cols-2 lg:grid-cols-3">
            {services.map((s) => (
              <li key={s.slug}>
                <Link href={`/services/${s.slug}/`} className="flex items-center justify-between rounded-md border border-border px-4 py-3 text-[15px] no-underline hover:bg-card">
                  <span className="text-foreground">{s.name}</span>
                  <span className="text-muted-foreground">from {formatPrice(s.priceFrom)}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </section>
      <Booking title={`Book a detail in ${a.name}.`} />
    </>
  );
}
