import type { Metadata } from "next";
import { og } from "@/lib/seo";
import Link from "next/link";
import { notFound } from "next/navigation";
import { articles, getArticle } from "@/lib/articles";
import { site } from "@/lib/site";
import { services, formatPrice } from "@/lib/services";
import { Faq } from "@/components/site/faq";
import { CtaBand } from "@/components/site/cta-band";
import { Breadcrumbs } from "@/components/site/breadcrumbs";

type Params = { slug: string };

export function generateStaticParams(): Params[] {
  return articles.map((a) => ({ slug: a.slug }));
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { slug } = await params;
  const a = getArticle(slug);
  if (!a) return {};
  return {
    title: a.title,
    description: a.description,
    alternates: { canonical: `/learn/${a.slug}/` },
    openGraph: og(`/learn/${a.slug}/`, { type: "article", publishedTime: a.published, modifiedTime: a.updated }),
  };
}

export default async function ArticlePage({ params }: { params: Promise<Params> }) {
  const { slug } = await params;
  const a = getArticle(slug);
  if (!a) notFound();

  const url = `${site.url}/learn/${a.slug}/`;
  const ld = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: a.h1,
    description: a.description,
    // Without these a guide has no age, and Google has nothing to freshen it on.
    datePublished: a.published,
    dateModified: a.updated,
    mainEntityOfPage: { "@type": "WebPage", "@id": url },
    image: `${site.url}/brand/og-image.jpg`,
    author: { "@type": "Organization", name: site.name, url: site.url },
    publisher: {
      "@type": "Organization",
      name: site.name,
      url: site.url,
      logo: { "@type": "ImageObject", url: `${site.url}/brand/logo-full-dark-640.png` },
    },
  };

  // The guides render a FAQ accordion but never told Google it was one, so three
  // pages of real questions and answers were invisible to rich results.
  const faqLd = a.faq?.length
    ? {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        mainEntity: a.faq.map((f) => ({ "@type": "Question", name: f.q, acceptedAnswer: { "@type": "Answer", text: f.a } })),
      }
    : null;

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }} />
      {faqLd && <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqLd) }} />}
      <article className="container-x mx-auto max-w-6xl py-14 md:py-20">
        <Breadcrumbs items={[{ href: "/learn/", label: "Guides" }, { href: `/learn/${a.slug}/`, label: a.title }]} />
        <h1 className="display-caps mt-3 max-w-4xl text-5xl md:text-7xl">{a.h1}</h1>
        <p className="mt-6 max-w-[62ch] text-lg text-secondary-foreground">{a.intro}</p>
        <p className="mt-4 text-sm text-muted-foreground">
          Last updated{" "}
          <time dateTime={a.updated}>
            {new Date(a.updated).toLocaleDateString("en-AU", { day: "numeric", month: "long", year: "numeric" })}
          </time>
        </p>

        <div className="mt-10 grid gap-10 md:grid-cols-12">
          <div className="grid gap-10 md:col-span-8">
            {a.sections.map((s) => (
              <section key={s.h}>
                <h2 className="display-caps text-3xl md:text-4xl">{s.h}</h2>
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
