import { site, prices } from "@/lib/site";
import { services } from "@/lib/services";
import { areas } from "@/lib/areas";

// One business entity for search engines, with the rating and offers attached.
export function JsonLd() {
  const data = {
    "@context": "https://schema.org",
    "@type": ["AutoDetailing", "LocalBusiness"],
    "@id": `${site.url}/#business`,
    name: site.name,
    url: site.url,
    telephone: site.phoneE164,
    email: site.email,
    image: `${site.url}/brand/og-image.jpg`,
    logo: `${site.url}/brand/logo-full-dark-640.png`,
    description:
      "Premium mobile car detailing in Canberra and Queanbeyan: ceramic coatings, paint correction, full, interior and exterior details at your home or workplace.",
    priceRange: "$110 - $2500",
    address: {
      "@type": "PostalAddress",
      addressLocality: site.address.locality,
      addressRegion: site.address.region,
      postalCode: site.address.postcode,
      addressCountry: site.address.country,
    },
    areaServed: areas.map((a) => ({ "@type": "Place", name: `${a.name}, ${a.slug === "queanbeyan" ? "NSW" : "ACT"}` })),
    openingHoursSpecification: [
      {
        "@type": "OpeningHoursSpecification",
        dayOfWeek: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        opens: "08:30",
        closes: "17:30",
      },
    ],
    sameAs: [site.instagram],
    aggregateRating: {
      "@type": "AggregateRating",
      ratingValue: site.stats.rating,
      reviewCount: site.stats.reviewCount,
      bestRating: "5",
    },
    makesOffer: [
      ...services.map((s) => ({
        "@type": "Offer",
        name: s.name,
        url: `${site.url}/services/${s.slug}/`,
        priceCurrency: "AUD",
        price: s.priceFrom,
        priceSpecification: { "@type": "PriceSpecification", minPrice: s.priceFrom, priceCurrency: "AUD" },
      })),
      {
        "@type": "Offer",
        name: "Maintenance plan",
        url: `${site.url}/maintenance/`,
        priceCurrency: "AUD",
        price: prices.maintenanceMonthly,
        priceSpecification: { "@type": "UnitPriceSpecification", minPrice: prices.maintenanceMonthly, priceCurrency: "AUD", unitText: "month" },
      },
    ],
  };
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }} />;
}
