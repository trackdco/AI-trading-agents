import Link from "next/link";
import { TestimonialsMarquee } from "@/components/ui/testimonial-v2";
import { reviews } from "@/lib/reviews";
import { site } from "@/lib/site";

export function ReviewsMarquee() {
  // Fifteen is plenty for three moving columns; the reviews page has all of them.
  const items = reviews.slice(0, 15).map((r) => ({ text: r.quote, name: r.name, role: r.time }));
  return (
    <div id="reviews" className="border-t border-border">
      <TestimonialsMarquee
        testimonials={items}
        heading="Trusted by Canberra's most particular owners."
        intro={`${site.stats.rating} stars across ${site.stats.reviewCount} reviews. Every one is from a real customer, in their own words.`}
      />
      <div className="container-x relative z-10 mx-auto -mt-6 flex max-w-6xl flex-wrap gap-x-8 gap-y-3 pb-16 md:pb-20">
        <Link href="/reviews/" className="inline-flex min-h-[44px] items-center text-[15px] text-secondary-foreground underline underline-offset-4 hover:text-foreground">
          Read all {site.stats.reviewCount} reviews
        </Link>
        <a href={site.googleWriteReviewUrl} target="_blank" rel="noopener" className="inline-flex min-h-[44px] items-center text-[15px] text-secondary-foreground underline underline-offset-4 hover:text-foreground">
          Write a review on Google
        </a>
      </div>
    </div>
  );
}
