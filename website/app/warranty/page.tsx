import type { Metadata } from "next";
import Link from "next/link";
import { site } from "@/lib/site";
import { CtaBand } from "@/components/site/cta-band";

export const metadata: Metadata = {
  title: "Ceramic Coating Warranty",
  description: "What Imperium Detailing's written 3, 5 and 7-year ceramic coating warranty covers, what keeps it valid, and how to make a claim.",
  alternates: { canonical: "/warranty/" },
};

const P = ({ children }: { children: React.ReactNode }) => <p className="mt-4 max-w-[64ch] text-[17px] text-secondary-foreground">{children}</p>;
const H = ({ children }: { children: React.ReactNode }) => <h2 className="display-caps mt-12 text-3xl md:text-4xl">{children}</h2>;

export default function WarrantyPage() {
  return (
    <>
      <section className="container-x mx-auto max-w-6xl py-14 md:py-20">
        <h1 className="display-caps max-w-4xl text-5xl md:text-7xl">Coating warranty, in writing.</h1>
        <P>
          Every ceramic coating we apply comes with a written warranty: 3, 5 or 7 years depending on the tier you choose. The full terms are handed to you with the car and match what's on this page. Local competitors don't publish theirs. We do.
        </P>

        <H>What's covered</H>
        <P>Loss of gloss and loss of hydrophobic behaviour (water beading and sheeting) on coated panels, where the coating has been maintained as described below. If the coating fails within the warranty period under those conditions, we re-prep and re-apply the affected panels at no charge.</P>

        <H>What keeps it valid</H>
        <ul className="mt-4 grid max-w-[64ch] list-none gap-2.5 p-0 text-[17px] text-secondary-foreground">
          {[
            "Hand washing with a pH-neutral shampoo and the two-bucket method described in the wash guide we give you.",
            "No automatic car washes with spinning brushes: they abrade the coating and are the fastest way to end its life.",
            "No abrasive polishes, cutting compounds or clay on the coated panels other than by us.",
            "Bird droppings, sap and bug remains removed within a few days rather than left to bake on.",
            "Keeping the car undercover for 24 hours and out of rain for 48 hours after application, as advised on the day.",
          ].map((t) => (
            <li key={t} className="flex gap-3">
              <span aria-hidden="true" className="mt-[.6em] h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              {t}
            </li>
          ))}
        </ul>

        <H>What isn't covered</H>
        <P>Damage from accidents, stone chips, scratches through the coating, paint failure underneath it, improper washing, chemical spills, or work on the coated panels by anyone else. Coatings protect against the environment; they are not a substitute for paint protection film against impact, and they do not protect against hail.</P>

        <H>Annual inspection</H>
        <P>An optional annual check is included at no extra cost. We inspect the coating, decontaminate the panels and top up the hydrophobic layer if needed. It's the easiest way to get the full life out of the coating.</P>

        <H>How to claim</H>
        <P>
          Text or call {site.phoneDisplay}, or email {site.email}, with your name, the car and a couple of photos. We'll book an inspection at your place, confirm what's happened and, if it's covered, re-apply the affected panels. Your rights under the Australian Consumer Law sit alongside this warranty, not beneath it.
        </P>

        <p className="mt-10 text-[15px] text-muted-foreground">
          See also{" "}
          <Link href="/services/ceramic-coating-canberra/" className="underline underline-offset-4">
            ceramic coating
          </Link>{" "}
          and our{" "}
          <Link href="/terms/" className="underline underline-offset-4">
            terms
          </Link>
          .
        </p>
      </section>
      <CtaBand title="Ready to protect the paint properly?" />
    </>
  );
}
