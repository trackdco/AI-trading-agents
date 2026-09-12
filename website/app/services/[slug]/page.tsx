import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { services, getService, formatPrice } from "@/lib/services";
import { site, smsHref, telHref } from "@/lib/site";
import { Picture } from "@/components/site/picture";
import { Faq } from "@/components/site/faq";
import { LinkButton } from "@/components/site/link-button";
import { Booking } from "@/components/site/booking";

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

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqLd) }} />

      <section className="container-x mx-auto grid max-w-6xl gap-10 py-14 md:grid-cols-12 md:items-center md:py-20">
        <div className="md:col-span-7">
          <p className="m-0 text-[15px] text-muted-foreground">
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
          <Picture name={s.image} alt={s.imageAlt} sizes="(min-width: 768px) 40vw, 100vw" priority className="aspect-[4/5] w-full rounded-md object-cover" />
        </div>
      </section>

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

      <Booking title={`Book a ${s.name.toLowerCase()}.`} />
    </>
  );
}
