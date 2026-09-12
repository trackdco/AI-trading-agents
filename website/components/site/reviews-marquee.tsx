import Link from "next/link";
import { TestimonialsMarquee } from "@/components/ui/testimonial-v2";
import { reviews } from "@/lib/reviews";
import { site } from "@/lib/site";

export function ReviewsMarquee() {
  const items = reviews.map((r) => ({ text: r.quote, name: r.name, role: r.time }));
  return (
    <div id="reviews" className="border-t border-border">
      <TestimonialsMarquee
        testimonials={items}
        heading="Trusted by Canberra's most particular owners."
        intro={`${site.stats.rating} stars across ${site.stats.reviewCount} reviews. Every one is from a real customer, in their own words.`}
      />
      <div className="container-x mx-auto -mt-6 max-w-6xl pb-16 md:pb-20">
        <Link href="/reviews/" className="text-[15px] text-secondary-foreground underline underline-offset-4 hover:text-foreground">
          Read all {site.stats.reviewCount} reviews
        </Link>
      </div>
    </div>
  );
}
