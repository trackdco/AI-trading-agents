import Link from "next/link";
import { CoverFlowCarousel, type CarouselItem } from "@/components/ui/3-d-coverflow-carousel";
import { services, formatPrice } from "@/lib/services";
import { imageSrc, imageSrcSet } from "@/components/site/picture";
import { SectionHeading } from "@/components/site/section-heading";

const lines: Record<string, string> = {
  "ceramic-coating-canberra": "Written 3, 5 or 7-year warranty",
  "paint-correction-canberra": "Measured, corrected, photographed",
  "full-car-detail-canberra": "Inside and out, in your driveway",
  "interior-car-detailing-canberra": "Steam and extraction, no perfume",
  "exterior-car-detailing-canberra": "Decontaminated, then sealed",
};

const items: CarouselItem[] = services.map((s) => ({
  tag: `From ${formatPrice(s.priceFrom)}`,
  titleLine1: s.name,
  titleLine2: lines[s.slug],
  desc: s.forWho,
  img: imageSrc(s.image, 480),
  imgSrcSet: imageSrcSet(s.image),
  imgAlt: s.imageAlt,
  ctaText: "See what's included",
  ctaUrl: `/services/${s.slug}/`,
}));

export function ServicesCoverflow() {
  return (
    <section id="services" className="py-16 md:py-24">
      <div className="container-x mx-auto max-w-6xl">
        <SectionHeading
          title="What we do, and what it costs."
          intro="Real from-prices. The number you're quoted is the number you pay, anywhere in Canberra and Queanbeyan, with no call-out fee. Swipe or use the arrows."
        />
      </div>
      <CoverFlowCarousel items={items} autoplayDelay={6000} />
      <div className="container-x mx-auto mt-8 max-w-6xl">
        <Link href="/services/" className="text-[15px] text-secondary-foreground underline underline-offset-4 hover:text-foreground">
          Compare all five services and prices
        </Link>
      </div>
    </section>
  );
}
