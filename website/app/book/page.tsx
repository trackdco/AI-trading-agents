import type { Metadata } from "next";
import { Booking } from "@/components/site/booking";

export const metadata: Metadata = {
  title: "Get a Quote",
  description: "Tell us about your car and suburb and we'll come back with availability and a fixed quote. Mobile detailing, ceramic coating and paint correction across Canberra and Queanbeyan.",
  alternates: { canonical: "/book/" },
};

export default function BookPage() {
  return <Booking title="Get a quote." headingAs="h1" />;
}
