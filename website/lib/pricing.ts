import { prices } from "./site";

export type SizeId = "sedan" | "suv" | "large";
export type JobId = "exterior" | "interior" | "full" | "correction" | "ceramic" | "maintenance";
export type Tier = 3 | 5 | 7;

export const sizes: { id: SizeId; label: string; eg: string }[] = [
  { id: "sedan", label: "Hatch or sedan", eg: "Corolla, Model 3, 3 Series" },
  { id: "suv", label: "SUV or ute", eg: "RAV4, Model Y, Ranger" },
  { id: "large", label: "4WD, van or 8-seater", eg: "LandCruiser, Patrol, Carnival" },
];

export const jobs: { id: JobId; label: string; slug: string; note: string }[] = [
  { id: "full", label: "Full detail", slug: "/services/full-car-detail-canberra/", note: "Inside and out in one visit: decontamination wash, sealant, steam, extraction, leather and trim. About 2.5 hours for a sedan." },
  { id: "exterior", label: "Exterior detail", slug: "/services/exterior-car-detailing-canberra/", note: "Two-bucket hand wash, chemical decontamination, spray sealant, wheels, tyres and glass. About 1.5 to 2 hours." },
  { id: "interior", label: "Interior detail", slug: "/services/interior-car-detailing-canberra/", note: "Vacuum, steam, hot-water extraction, leather and trim conditioned. Heavy pet hair or stains take longer and cost more." },
  { id: "correction", label: "Paint correction", slug: "/services/paint-correction-canberra/", note: "Single-stage machine correction for swirl marks and haze. Deep scratches need a multi-stage job, usually 1.5 to 2 times this." },
  { id: "ceramic", label: "Ceramic coating", slug: "/services/ceramic-coating-canberra/", note: "Decontamination, a single-stage polish, then the coating, with a written warranty. Leave the car undercover for 24 hours after." },
  { id: "maintenance", label: "Maintenance plan", slug: "/maintenance/", note: "A monthly visit: coating-safe hand wash, interior reset, protection topped up. Fortnightly visits are quoted on request." },
];

// Real from-prices by size, in AUD. null means we quote it from photos of the car.
const table: Record<JobId, Record<SizeId, number | null>> = {
  exterior: { sedan: prices.exterior, suv: 125, large: 140 },
  interior: { sedan: prices.interior, suv: 155, large: 170 },
  full: { sedan: prices.full, suv: 250, large: 270 },
  correction: { sedan: prices.correction, suv: null, large: null },
  ceramic: { sedan: prices.ceramic, suv: null, large: null },
  maintenance: { sedan: prices.maintenanceMonthly, suv: null, large: null },
};

// Ceramic tiers for a hatch or sedan; SUV, ute and 4WD tiers sit above these.
export const ceramicTiers: { years: Tier; price: number }[] = [
  { years: 3, price: prices.ceramic },
  { years: 5, price: 1197 },
  { years: 7, price: 1347 },
];

export type Guide = { price: number | null; suffix: string; why: string };

export function guidePrice(job: JobId, size: SizeId, tier: Tier = 3): Guide {
  if (job === "ceramic") {
    if (size !== "sedan") return { price: null, suffix: "", why: "SUV, ute and 4WD coatings sit above the sedan tiers. Text us the car and we'll quote it the same day." };
    const t = ceramicTiers.find((c) => c.years === tier) ?? ceramicTiers[0];
    return { price: t.price, suffix: "", why: `${t.years}-year written warranty. Prep, polish and coating by the same two people.` };
  }
  if (job === "maintenance") {
    const p = table.maintenance[size];
    return p === null
      ? { price: null, suffix: "", why: "Monthly plans for larger cars are quoted for the car. Text us the model and how it's used." }
      : { price: p, suffix: " a month", why: "One fixed price every month, quoted for your car." };
  }
  if (job === "correction") {
    const p = table.correction[size];
    return p === null
      ? { price: null, suffix: "", why: "Correction on larger cars is quoted from two photos of the paint in sunlight." }
      : { price: p, suffix: "", why: "Single-stage correction, then a sealant. Coating it afterwards is the most common package we do." };
  }
  const p = table[job][size];
  return { price: p, suffix: "", why: "Mobile anywhere in Canberra and Queanbeyan, no call-out fee. The number you're quoted is the number you pay." };
}
