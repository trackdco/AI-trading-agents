import type { Metadata } from "next";
import { site } from "@/lib/site";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "How Imperium Detailing collects, uses and protects the personal information you share when you request a quote or book a detail.",
  alternates: { canonical: "/privacy/" },
};

const P = ({ children }: { children: React.ReactNode }) => <p className="mt-4 max-w-[64ch] text-[17px] text-secondary-foreground">{children}</p>;
const H = ({ children }: { children: React.ReactNode }) => <h2 className="display mt-10 text-3xl md:text-4xl">{children}</h2>;

export default function PrivacyPage() {
  return (
    <section className="container-x mx-auto max-w-6xl py-14 md:py-20">
      <h1 className="display max-w-4xl text-5xl md:text-7xl">Privacy policy.</h1>
      <P>Imperium Detailing ({site.legalName}, Canberra ACT) respects your privacy. This page explains what we collect, why, and what you can do about it. It's written to be read, not to be scrolled past.</P>

      <H>What we collect</H>
      <P>When you request a quote or book a detail we collect the details you give us: your name, phone number, email address if you provide it, your suburb, and information about your car and the work you want done. If you send photos of the car, we keep them with your enquiry.</P>
      <P>Our website uses Google Ads conversion tracking and, where enabled, a Meta pixel and a chat widget. These may set cookies and collect standard usage data such as your IP address, device and the pages you visit, in line with those providers' own policies.</P>

      <H>Why we collect it</H>
      <P>To quote, book and carry out the work; to contact you about your booking; to keep a record of the jobs we've done on your car (useful for coating warranties and follow-up services); and, only if you've agreed, to let you know about seasonal offers. We don't sell your details to anyone.</P>

      <H>Who we share it with</H>
      <P>Only the services that help us run the business: our booking and messaging platform, payment providers, and the advertising and analytics tools named above. Each is bound by its own privacy policy. We share nothing else, unless the law requires it.</P>

      <H>How long we keep it</H>
      <P>Enquiry and booking records are kept while you're a customer and for as long as a coating warranty on your car is active, then deleted or de-identified. You can ask us to delete your details earlier at any time.</P>

      <H>Your choices</H>
      <P>You can ask to see, correct or delete the information we hold about you, or opt out of any marketing, by texting or calling {site.phoneDisplay} or emailing {site.email}. We'll respond within a reasonable time and won't make it difficult.</P>

      <H>Changes</H>
      <P>If this policy changes, the new version will be published here with the date it took effect. This version applies from September 2026.</P>
    </section>
  );
}
