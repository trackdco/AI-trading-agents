import type { Metadata } from "next";
import { Hero } from "@/components/site/hero";
import { ProofBand } from "@/components/site/proof-band";
import { ServicesCoverflow } from "@/components/site/services-coverflow";
import { Work } from "@/components/site/work";
import { Process } from "@/components/site/process";
import { ReviewsMarquee } from "@/components/site/reviews-marquee";
import { Booking } from "@/components/site/booking";

export const metadata: Metadata = {
  alternates: { canonical: "/" },
};

export default function HomePage() {
  return (
    <>
      <Hero />
      <ProofBand />
      <ServicesCoverflow />
      <Work />
      <Process />
      <ReviewsMarquee />
      <Booking />
    </>
  );
}
