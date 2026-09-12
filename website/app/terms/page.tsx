import type { Metadata } from "next";
import Link from "next/link";
import { site } from "@/lib/site";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "The plain-English terms for booking a mobile detail, paint correction or ceramic coating with Imperium Detailing.",
  alternates: { canonical: "/terms/" },
};

const P = ({ children }: { children: React.ReactNode }) => <p className="mt-4 max-w-[64ch] text-[17px] text-secondary-foreground">{children}</p>;
const H = ({ children }: { children: React.ReactNode }) => <h2 className="display mt-10 text-3xl md:text-4xl">{children}</h2>;

export default function TermsPage() {
  return (
    <section className="container-x mx-auto max-w-6xl py-14 md:py-20">
      <h1 className="display max-w-4xl text-5xl md:text-7xl">Terms, in plain English.</h1>
      <P>These are the terms that apply when you book Imperium Detailing. They're short because the way we work is simple.</P>

      <H>Quotes and prices</H>
      <P>Our from-prices are genuine minimums for the service on a standard sedan or hatch in normal condition. Your quote is fixed once we've seen the car, either in photos or in person. If a car turns out to be in genuinely extreme condition, we'll tell you before we start and agree any adjustment with you. No surprise invoices.</P>

      <H>Bookings and access</H>
      <P>We work at your home, apartment car park or workplace. You need to give us access to the car, an outdoor tap and a standard 240V power point. Paint correction and ceramic coating also need an enclosed garage or covered space out of direct sun, wind and dust. If those aren't available on the day, we may need to reschedule.</P>

      <H>Weather</H>
      <P>Rain, frost and extreme heat affect what we can do safely and well. If the forecast makes the job unworkable we'll contact you as early as we can to move it, and there's no charge for a weather reschedule.</P>

      <H>Payment</H>
      <P>Payment is due on completion, by card or bank transfer, once you've seen the result. There are no card fees and no travel fees anywhere in the ACT or Queanbeyan.</P>

      <H>Our workmanship</H>
      <P>We're fully insured and we guarantee the finish we hand back. If something isn't right, tell us within a couple of days and we'll come back and fix it. Ceramic coatings carry a separate written warranty, explained on the <Link href="/warranty/" className="underline underline-offset-4">warranty page</Link>.</P>

      <H>What we can't promise</H>
      <P>We tell you before we start what will and won't come out. Scratches through the clear coat, deep etching, existing paint failure and mechanical faults are outside what detailing can fix, and we'll say so rather than guess.</P>

      <H>Contact</H>
      <P>Questions about these terms: {site.phoneDisplay} or {site.email}. Your rights under the Australian Consumer Law apply in addition to anything here.</P>
    </section>
  );
}
