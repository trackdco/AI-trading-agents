import type { Metadata } from "next";
import { og } from "@/lib/seo";
import { reviews } from "@/lib/reviews";
import { site } from "@/lib/site";
import { SectionHeading } from "@/components/site/section-heading";
import { LinkButton } from "@/components/site/link-button";
import { CtaBand } from "@/components/site/cta-band";

export const metadata: Metadata = {
  title: "Customer Reviews",
  description: `${site.stats.rating} stars across ${site.stats.reviewCount} reviews. What Canberra owners say about Imperium Detailing's ceramic coatings, paint correction and full details.`,
  alternates: { canonical: "/reviews/" }, openGraph: og("/reviews/"),
};

export default function ReviewsPage() {
  return (
    <>
      <section className="container-x mx-auto max-w-6xl py-14 md:py-20">
        <SectionHeading
          as="h1"
          size="xl"
          title="What Canberra owners say."
          intro={`${site.stats.rating} stars across ${site.stats.reviewCount} reviews. Every review here is from a real customer.`}
        />
        <div className="-mt-4 mb-10 md:-mt-6 md:mb-14" data-reveal="up">
          <div className="flex flex-col gap-3 sm:flex-row">
            <LinkButton href={site.googleWriteReviewUrl} newTab>
              Write a review on Google
            </LinkButton>
            <LinkButton href={site.googleReviewsUrl} variant="ghost" newTab>
              Read them on Google
            </LinkButton>
          </div>
          <p className="mt-4 max-w-[52ch] text-[15px] text-muted-foreground">
            {"Had your car done by us? A review takes a minute, and it's what keeps a small business booked."}
          </p>
          <p className="mt-2 max-w-[52ch] text-[15px] text-muted-foreground">
            Pulled from Google in September 2026, so the times below are counted from then.
          </p>
        </div>
        <ul className="m-0 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
          {reviews.map((r, i) => (
            <li key={`${r.name}-${i}`} className="rounded-lg border border-border bg-card p-6">
              <blockquote className="m-0">
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
