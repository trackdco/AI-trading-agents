import type { Metadata } from "next";
import Link from "next/link";
import { areas } from "@/lib/areas";
import { SectionHeading } from "@/components/site/section-heading";
import { CtaBand } from "@/components/site/cta-band";

export const metadata: Metadata = {
  title: "Mobile Detailing Service Areas Canberra",
  description: "Fully mobile car detailing across nine Canberra districts and Queanbeyan: no shop, no call-out fee. We come to your driveway, car park or workplace.",
  alternates: { canonical: "/service-areas/" },
};

export default function AreasPage() {
  return (
    <>
      <section className="container-x mx-auto max-w-6xl py-14 md:py-20">
        <SectionHeading
          as="h1"
          size="xl"
          title="Nine districts. One mobile van."
          intro="No shop to drop your car at. We turn up at your driveway, apartment car park or workplace with the van, the water and the power. No travel fee anywhere in the ACT or Queanbeyan: the price you're quoted is the price you pay."
        />
        <ul className="m-0 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
          {areas.map((a) => (
            <li key={a.slug}>
              <Link href={`/service-areas/${a.slug}/`} className="block h-full rounded-lg border border-border bg-card p-6 no-underline transition-colors hover:border-secondary-foreground/40">
                <h2 className="display text-3xl">{a.name}</h2>
                <p className="mt-2 text-[15px] text-muted-foreground">{a.blurb}</p>
                <p className="mt-3 text-sm text-secondary-foreground">{a.suburbs.slice(0, 5).join(", ")}{a.suburbs.length > 5 ? " and more" : ""}</p>
              </Link>
            </li>
          ))}
        </ul>
        <p className="mt-8 max-w-[64ch] text-[15px] text-muted-foreground">
          Not on the list? If you're anywhere between Gungahlin and Tuggeranong, out to Weston Creek or across the border to Queanbeyan and Googong, we'll come to you. Text us your suburb and we'll confirm.
        </p>
      </section>
      <CtaBand />
    </>
  );
}
