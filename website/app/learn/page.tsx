import type { Metadata } from "next";
import Link from "next/link";
import { articles } from "@/lib/articles";
import { SectionHeading } from "@/components/site/section-heading";
import { CtaBand } from "@/components/site/cta-band";

export const metadata: Metadata = {
  title: "Detailing Guides and Pricing",
  description: "Straight answers to the questions we get asked most: real Canberra prices, what each service actually does, and how to work out which one your car needs.",
  alternates: { canonical: "/learn/" },
};

export default function LearnPage() {
  return (
    <>
      <section className="container-x mx-auto max-w-6xl py-14 md:py-20">
        <SectionHeading as="h1" size="xl" title="Guides and pricing." intro="Straight answers to the questions we get asked most. Real Canberra prices, what each service actually does, and how to work out which one your car needs." />
        <ul className="m-0 grid list-none gap-4 p-0 md:grid-cols-2">
          {articles.map((a) => (
            <li key={a.slug}>
              <Link href={`/learn/${a.slug}/`} className="block h-full rounded-lg border border-border bg-card p-6 no-underline hover:border-secondary-foreground/40 md:p-8">
                <h2 className="display-caps text-3xl md:text-4xl">{a.h1}</h2>
                <p className="mt-3 text-[15px] text-muted-foreground">{a.description}</p>
                <span className="mt-4 inline-block text-[15px] text-foreground underline underline-offset-4">Read the guide</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
      <CtaBand title="Send a couple of photos. We'll tell you straight." />
    </>
  );
}
