import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { articles, getArticle } from "@/lib/articles";
import { services, formatPrice } from "@/lib/services";
import { Faq } from "@/components/site/faq";
import { CtaBand } from "@/components/site/cta-band";

type Params = { slug: string };

export function generateStaticParams(): Params[] {
  return articles.map((a) => ({ slug: a.slug }));
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { slug } = await params;
  const a = getArticle(slug);
  if (!a) return {};
  return { title: a.title, description: a.description, alternates: { canonical: `/learn/${a.slug}/` } };
}

export default async function ArticlePage({ params }: { params: Promise<Params> }) {
  const { slug } = await params;
  const a = getArticle(slug);
  if (!a) notFound();

  const ld = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: a.h1,
    description: a.description,
    author: { "@type": "Organization", name: "Imperium Detailing" },
    publisher: { "@type": "Organization", name: "Imperium Detailing" },
  };

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }} />
      <article className="container-x mx-auto max-w-6xl py-14 md:py-20">
        <p className="m-0 text-[15px] text-muted-foreground">
          <Link href="/learn/" className="underline underline-offset-4">
            Guides
          </Link>
        </p>
        <h1 className="display mt-3 max-w-4xl text-5xl md:text-7xl">{a.h1}</h1>
        <p className="mt-6 max-w-[62ch] text-lg text-secondary-foreground">{a.intro}</p>

        <div className="mt-10 grid gap-10 md:grid-cols-12">
          <div className="grid gap-10 md:col-span-8">
            {a.sections.map((s) => (
              <section key={s.h}>
                <h2 className="display text-3xl md:text-4xl">{s.h}</h2>
                {s.p?.map((p) => (
                  <p key={p.slice(0, 40)} className="mt-4 max-w-[64ch] text-[17px] text-secondary-foreground">
                    {p}
                  </p>
                ))}
                {s.list && (
                  <ul className="mt-4 grid max-w-[64ch] list-none gap-2.5 p-0 text-[16px] text-secondary-foreground">
                    {s.list.map((li) => (
                      <li key={li} className="flex gap-3">
                        <span aria-hidden="true" className="mt-[.6em] h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                        {li}
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            ))}
            <Faq items={a.faq} title="Questions we get asked" />
          </div>
          <aside className="md:col-span-4">
            <div className="rounded-lg border border-border bg-card p-6 md:sticky md:top-24">
              <h2 className="text-lg font-semibold">Current from-prices</h2>
              <ul className="mt-4 grid list-none gap-2.5 p-0 text-[15px]">
                {services.map((s) => (
                  <li key={s.slug} className="flex items-center justify-between gap-3">
                    <Link href={`/services/${s.slug}/`} className="text-secondary-foreground underline-offset-4 hover:underline">
                      {s.name}
                    </Link>
                    <span className="text-foreground">{formatPrice(s.priceFrom)}</span>
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      </article>
      <CtaBand title="Get a real quote for your car." />
    </>
  );
}
