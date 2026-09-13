import type { Metadata } from "next";
import { Booking } from "@/components/site/booking";

export const metadata: Metadata = {
  title: "Get a Quote",
  description: "Tell us the car and your suburb and we'll text back a fixed quote and the next available days. Mobile detailing across Canberra and Queanbeyan.",
  alternates: { canonical: "/book/" },
};

export default function BookPage() {
  return <Booking title="Get a quote." headingAs="h1" />;
}
