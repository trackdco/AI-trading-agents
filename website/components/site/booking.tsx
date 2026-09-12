import { BookingForm } from "@/components/site/booking-form";
import { SectionHeading } from "@/components/site/section-heading";
import { site, telHref } from "@/lib/site";

type Props = { title?: string; headingAs?: "h1" | "h2"; defaultService?: string };

export function Booking({ title = "Book your detail.", headingAs = "h2", defaultService }: Props) {
  return (
    <section id="book" className="border-t border-border py-16 md:py-24">
      <div className="container-x mx-auto grid max-w-6xl gap-12 md:grid-cols-12">
        <div className="md:col-span-5">
          <SectionHeading as={headingAs} title={title} intro="Tell us about the car and we'll come back with availability and a fixed quote." />
          <ul className="m-0 grid list-none gap-3 p-0 text-[15px] text-secondary-foreground">
            <li>Free, no-obligation quote</li>
            <li>Mobile service across Canberra and Queanbeyan, no call-out fee</li>
            <li>Fully insured and finish-guaranteed</li>
            <li>
              Prefer to talk?{" "}
              <a href={telHref} className="text-foreground underline underline-offset-4">
                {site.phoneDisplay}
              </a>
              , {site.hours}
            </li>
          </ul>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 md:col-span-7 md:p-8">
          <BookingForm defaultService={defaultService} />
        </div>
      </div>
    </section>
  );
}
