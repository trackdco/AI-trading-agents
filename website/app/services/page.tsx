import type { Metadata } from "next";
import Link from "next/link";
import { services, formatPrice } from "@/lib/services";
import { Picture } from "@/components/site/picture";
import { SectionHeading } from "@/components/site/section-heading";
import { CtaBand } from "@/components/site/cta-band";

export const metadata: Metadata = {
  title: "Services and Prices",
  description:
    "Every Imperium Detailing service with real from-prices: full detail from $225, interior from $140, exterior from $110, paint correction from $397, ceramic coating from $997.",
  alternates: { canonical: "/services/" },
};

export default function ServicesPage() {
  return (
    <>
      <section className="container-x mx-auto max-w-6xl py-14 md:py-20">
        <SectionHeading as="h1" size="xl" title="Five services. Real prices." intro="Mobile across Canberra and Queanbeyan for the same price. The number you're quoted is the number you pay." />
        <div className="grid gap-px overflow-hidden rounded-lg border border-border bg-border">
          {services.map((s) => (
            <Link key={s.slug} href={`/services/${s.slug}/`} className="grid gap-5 bg-background p-5 no-underline transition-colors hover:bg-card md:grid-cols-12 md:items-center md:p-6">
              <div className="md:col-span-3">
                <Picture name={s.image} alt={s.imageAlt} sizes="(min-width: 768px) 25vw, 100vw" className="aspect-[4/3] w-full rounded-md object-cover" />
              </div>
              <div className="md:col-span-6">
                <h2 className="display-caps text-3xl">{s.name}</h2>
                <p className="mt-2 text-[15px] text-muted-foreground">{s.description}</p>
              </div>
              <div className="md:col-span-3 md:text-right">
                <span className="text-sm text-muted-foreground">from</span>
                <span className="display-caps block text-4xl">{formatPrice(s.priceFrom)}</span>
                <span className="mt-1 block text-sm text-muted-foreground">{s.duration}</span>
              </div>
            </Link>
          ))}
        </div>
        <Link href="/maintenance/" className="mt-4 grid gap-4 rounded-lg border border-border p-5 no-underline transition-colors hover:bg-card md:grid-cols-12 md:items-center md:p-6">
          <div className="md:col-span-9">
            <h2 className="display-caps text-3xl">Maintenance plans</h2>
            <p className="mt-2 text-[15px] text-muted-foreground">
              Already detailed? We come back every 2, 4 or 8 weeks and keep it that way. One fixed price per visit, quoted for your car.
            </p>
          </div>
          <div className="text-[15px] font-semibold text-foreground md:col-span-3 md:text-right">How the plans work</div>
        </Link>
      </section>
      <CtaBand title="Not sure which one your car needs?" />
    </>
  );
}
