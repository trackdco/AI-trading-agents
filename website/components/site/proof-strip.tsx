import { site } from "@/lib/site";

export function ProofStrip() {
  return (
    <section aria-label="Proof" className="border-y border-border bg-card/40">
      <div className="container-x mx-auto max-w-6xl py-7">
        <p className="m-0 max-w-[70ch] text-[17px] text-muted-foreground">
          <b className="font-medium text-foreground">{site.stats.cars} cars</b> detailed in the last year.{" "}
          <a href={site.googleReviewsUrl} rel="noopener" className="font-medium text-foreground underline decoration-border underline-offset-4 hover:decoration-foreground">
            {site.stats.rating} stars across {site.stats.reviewCount} reviews
          </a>
          . Ceramic coatings come with a written warranty of up to {site.stats.warrantyYears} years, and we're fully insured.
        </p>
      </div>
    </section>
  );
}
