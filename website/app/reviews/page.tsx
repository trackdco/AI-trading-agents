import type { Metadata } from "next";
import { reviews } from "@/lib/reviews";
import { site } from "@/lib/site";
import { SectionHeading } from "@/components/site/section-heading";
import { CtaBand } from "@/components/site/cta-band";

export const metadata: Metadata = {
  title: "Customer Reviews",
  description: `${site.stats.rating} stars across ${site.stats.reviewCount} reviews. What Canberra owners say about Imperium Detailing's ceramic coatings, paint correction and full details.`,
  alternates: { canonical: "/reviews/" },
};

const Stars = () => (
  <span aria-hidden="true" className="flex gap-0.5 text-accent">
    {Array.from({ length: 5 }).map((_, i) => (
      <svg key={i} width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2.3l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 17.1l-5.8 3.1 1.1-6.5-4.7-4.6 6.5-.9z" />
      </svg>
    ))}
  </span>
);

export default function ReviewsPage() {
  return (
    <>
      <section className="container-x mx-auto max-w-6xl py-14 md:py-20">
        <SectionHeading
          as="h1"
          size="xl"
          title="What Canberra owners say."
          intro={
            <>
              {site.stats.rating} stars across {site.stats.reviewCount} reviews. Every review here is from a real customer.{" "}
              <a href={site.googleReviewsUrl} rel="noopener" className="text-foreground underline underline-offset-4">
                Read them on Google
              </a>
              .
            </>
          }
        />
        <ul className="m-0 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
          {reviews.map((r, i) => (
            <li key={`${r.name}-${i}`} className="rounded-lg border border-border bg-card p-6">
              <Stars />
              <span className="sr-only">Five stars.</span>
              <blockquote className="m-0 mt-3">
                <p className="m-0 text-[15px] text-secondary-foreground">{r.quote}</p>
                <footer className="mt-4 text-sm">
                  <cite className="not-italic font-semibold text-foreground">{r.name}</cite>
                  <span className="text-muted-foreground"> · {r.time}</span>
                </footer>
              </blockquote>
            </li>
          ))}
        </ul>
      </section>
      <CtaBand title="Join them." />
    </>
  );
}
