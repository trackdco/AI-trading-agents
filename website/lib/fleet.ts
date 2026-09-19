import { formatPrice } from "./services";
import { guidePrice, conditionRange, sizes, type JobId, type SizeId } from "./pricing";

/**
 * The fleet page's own content. Prices live in lib/pricing.ts and are read from
 * there, never retyped, so a price change in one place changes this page too.
 */

/** Every price below comes through here, so none of them is retyped. */
const at = (job: JobId, size: SizeId) => {
  const g = guidePrice(job, size, 3);
  return g.price === null ? "quoted" : formatPrice(g.price);
};

/** The sizes a business picks from. Bikes are not fleet work; trucks are, and they are quoted. */
export type FleetSizeId = Exclude<SizeId, "bike"> | "truck";

export const fleetSizes: { id: FleetSizeId; label: string; eg: string }[] = [
  ...sizes.filter((s) => s.id !== "bike").map((s) => ({ id: s.id as FleetSizeId, label: s.label, eg: s.eg })),
  // Pat does prime movers and tippers, but there is no published rate for them,
  // so the estimator says "quoted" rather than inventing one.
  { id: "truck", label: "Truck", eg: "Prime mover, tipper, rigid" },
];

/** Who the page is for. Each one is a real shape a two-person van can actually serve. */
export const fleetSegments: { name: string; line: string }[] = [
  {
    name: "Trades, subbies and small builders",
    line: "Your utes are the biggest advertisement the business owns, and they live under site dust. We come to the yard and work along the line.",
  },
  {
    name: "Transport and civil",
    line: "Prime movers, tippers and rigids. Trucks are quoted over the phone rather than off a price list, because no two are the same job.",
  },
  {
    name: "Real estate agencies",
    line: "Agent cars wear out on the inside first. The whole team's cars done in the office car park in one visit.",
  },
  {
    name: "Offices with pool cars",
    line: "Pool cars and the executive bays done where they already park, so nobody loses a car for a day at a shop.",
  },
  {
    name: "Owner-operator mini-fleets",
    line: "A work ute, a partner's SUV and the good car at one address, invoiced to the business. Two vehicles is a fleet here.",
  },
  {
    name: "Hire cars, chauffeur and wedding operators",
    line: "The car is the product. An interior detail between jobs, a full detail before the season.",
  },
  {
    name: "Rideshare drivers",
    line: "An interior detail is what a rating is made of. Priced by the car, the same as anyone else pays.",
  },
  {
    name: "Car yards and independent dealers",
    line: "Per car, not per yard. One trade-in corrected properly before it is photographed.",
  },
];

/** What actually happens, in order. This is a real sequence, so it is numbered. */
export const fleetProcess: { step: string; detail: string }[] = [
  {
    step: "Send the numbers",
    detail:
      "Use the estimator, or ring us and describe the fleet. Photos of the worst two interiors help more than a paragraph about them.",
  },
  {
    step: "We quote it per vehicle",
    detail:
      "The same per-car prices, itemised by size, with the condition allowance on any interiors and full details priced in up front so there is nothing to argue about on the day.",
  },
  {
    step: "We give you dates",
    detail:
      "How many days your fleet needs and which days we have open. Real dates, worked out against your actual numbers, rather than a figure that sounds good on a page.",
  },
  {
    step: "Two of us arrive with everything",
    detail:
      "You supply the outdoor tap, the 240V power point and access to the vehicles. Nobody needs to stand over us. Payment is due on completion, by card or bank transfer.",
  },
];

/** The gate. Worth answering before a booking, not on the morning. */
export const fleetSiteNeeds = [
  "An outdoor tap we can run a hose from.",
  "A standard 240V power point within reach of where the vehicles park.",
  "Access to the vehicles, and somewhere for the van to sit while we work.",
  "For correction or coating: a garage or covered space, out of sun, wind and dust, one vehicle at a time.",
  "In a basement or shared car park: the building's okay for a contractor to work on vehicles down there.",
];

/** For the accounts people. Every row is sourced from lib/site.ts or /terms/. */
export const fleetPaperwork: { term: string; detail: string }[] = [
  { term: "Business", detail: "Imperium Detailing. ABN 81 254 863 265." },
  {
    term: "Insurance",
    detail: "Fully insured, and we guarantee the finish we hand back. If something is not right, tell us within a couple of days and we come back and fix it.",
  },
  { term: "Coatings", detail: "A separate written warranty, set out on the warranty page." },
  { term: "Payment", detail: "Due on completion, by card or bank transfer, once you have seen the result. No card fees." },
  { term: "Travel", detail: "No call-out fee and no travel fee anywhere in the ACT or Queanbeyan." },
  { term: "Weather", detail: "If the forecast makes the day unworkable we move it, at no charge." },
  { term: "Hours", detail: "Every day, 8:30am to 5:30pm. Book at least a day ahead. Same-day is sometimes possible by phone." },
];

export const fleetFaq: { q: string; a: string }[] = [
  {
    q: "Do we get a discount for multiple vehicles?",
    a: `No. The price is the same per vehicle as it would be for a private customer, set by the size of the car: exterior ${at("exterior", "sedan")}, ${at("exterior", "suv")} or ${at("exterior", "large")}, interior ${at("interior", "sedan")}, ${at("interior", "suv")} or ${at("interior", "large")}, full detail ${at("full", "sedan")}, ${at("full", "suv")} or ${at("full", "large")}. Two of us and one van do the same work on car six as on car one, so car six costs what car one did. Nothing is marked up because you are a business either.`,
  },
  {
    q: "What do we need to have on site?",
    a: "An outdoor tap, a 240V power point, and the vehicles accessible. We bring everything else. There is no shop, no drop-off, and no call-out fee anywhere in the ACT or Queanbeyan.",
  },
  {
    q: "Our depot has no tap or no power point. Can you still come?",
    a: "Not as a standard booking. The tap and the power point are the two things we ask you to supply. The way around it is to have us come to whichever address does have both, whether that is head office, a workshop or a yard. Tell us the site and we will tell you straight before you commit to anything.",
  },
  {
    q: "How many vehicles can you do in a day?",
    a: "Work it from the times: about an hour a vehicle for an exterior detail, an hour and a half for an interior, three hours for a full detail on a sedan, and longer on anything bigger. There are two of us working at once, from 8:30am to 5:30pm. Send your numbers and we will come back with the actual days rather than a round figure that suits us."
  },
  {
    q: "Can you work in our basement or office car park?",
    a: "Yes, when there is water, a power point, and the building or body corporate allows the work. All three, not two of the three. The last one is the part that catches people out, so check it with your building manager before we book.",
  },
  {
    q: "Which of our vehicles counts as what size?",
    a: `Hatches and sedans are the sedan price. SUVs and utes are the SUV price. 4WDs, vans and 8-seaters are the large price. A motorbike full detail is ${at("full", "bike")}. Trucks we quote over the phone, because a prime mover and a rigid are not the same job.`,
  },
  {
    q: "Do trays, canopies, roof racks and van shelving cost more?",
    a: "Tell us what is on the vehicle and we will price it on sight before the day. A fitted-out van with shelving is more work than an empty one, and we would rather say that up front than surprise you with it.",
  },
  {
    q: "Can you polish or coat over signwriting and vinyl wrap?",
    a: "Tell us which panels are wrapped when you send the numbers through and we will give you a straight answer for your vehicles. Machine work over vinyl is not the same as machine work over paint, and it is not something to decide in your car park on the morning.",
  },
  {
    q: "How long is each vehicle off the road?",
    a: "About an hour for an exterior detail, about an hour and a half for an interior, and about three hours for a full detail on a sedan. Larger vehicles take longer. We work 8:30am to 5:30pm, every day.",
  },
  {
    q: "Can we book a weekend, when the yard is quiet?",
    a: "Yes. We are open every day, 8:30am to 5:30pm, so a Saturday or Sunday is an ordinary working day for us.",
  },
  {
    q: "Can we try you on one vehicle first?",
    a: `Yes, and we would rather you did. One vehicle is priced exactly the same as it would be for anyone else, so a single ute is ${at("exterior", "suv")} for an exterior detail or ${at("full", "suv")} for a full detail. See the work before you hand over the fleet.`,
  },
  {
    q: `What is the up-to-${formatPrice(conditionRange)} condition charge?`,
    a: `It applies to full and interior details only, it is capped at ${formatPrice(conditionRange)} a vehicle, and it is agreed with you before any work starts, never added afterwards. On a work fleet, assume it is in play. Send photos of the worst two with your enquiry and we will price it in before the day.`,
  },
  {
    q: "When do we pay, and what does it cost to get you out here?",
    a: "Payment is due on completion, by card or bank transfer, once you have seen the result. There are no card fees, and no call-out or travel fees anywhere in the ACT or Queanbeyan. ABN 81 254 863 265, and we are fully insured.",
  },
  {
    q: "Do you do window tinting, paint protection film or rim repairs?",
    a: "No to all three. We will ceramic coat over PPF that somebody else has fitted.",
  },
];
