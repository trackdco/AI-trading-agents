import { prices } from "./site";

export type SizeId = "sedan" | "suv" | "large" | "bike";
export type JobId = "full" | "exterior" | "interior" | "correction" | "ceramic" | "maintenance";
export type Tier = 3 | 5 | 7;

export const sizes: { id: SizeId; label: string; eg: string }[] = [
  { id: "sedan", label: "Hatch or sedan", eg: "Corolla, Model 3, 3 Series" },
  { id: "suv", label: "SUV or ute", eg: "RAV4, Model Y, Ranger" },
  { id: "large", label: "4WD, van or 8-seater", eg: "LandCruiser, Patrol, Carnival" },
  { id: "bike", label: "Motorbike", eg: "Any make, any size" },
];

export const jobs: { id: JobId; label: string; slug: string; note: string }[] = [
  { id: "full", label: "Full detail", slug: "/services/full-car-detail-canberra/", note: "Inside and out in one visit: decontamination wash, sealant, steam, extraction, leather and trim. About 3 hours for a sedan." },
  { id: "exterior", label: "Exterior detail", slug: "/services/exterior-car-detailing-canberra/", note: "Two-bucket hand wash, chemical decontamination, spray sealant, wheels, tyres and glass. About an hour." },
  { id: "interior", label: "Interior detail", slug: "/services/interior-car-detailing-canberra/", note: "Vacuum, steam, hot-water extraction, leather and trim conditioned. About 1.5 hours for a tidy interior." },
  { id: "correction", label: "Paint correction", slug: "/services/paint-correction-canberra/", note: "Single-stage machine correction for swirl marks and haze. Deep scratches need a multi-stage job, quoted from photos." },
  { id: "ceramic", label: "Ceramic coating", slug: "/services/ceramic-coating-canberra/", note: "Decontamination, a single-stage polish, then the coating. Around 5 hours on site; leave the car undercover for 24 hours after." },
  { id: "maintenance", label: "Maintenance plan", slug: "/maintenance/", note: "A monthly visit: coating-safe hand wash, interior reset, protection topped up. Fortnightly visits are quoted on request." },
];

// Real prices by vehicle size, in AUD. null means it's quoted for the vehicle.
const table: Record<Exclude<JobId, "ceramic">, Record<SizeId, number | null>> = {
  full: { sedan: prices.full, suv: 250, large: 270, bike: 135 },
  exterior: { sedan: prices.exterior, suv: 120, large: 140, bike: null },
  interior: { sedan: prices.interior, suv: 165, large: 170, bike: null },
  correction: { sedan: prices.correction, suv: 497, large: 547, bike: null },
  maintenance: { sedan: prices.maintenanceMonthly, suv: null, large: null, bike: null },
};

// Ceramic tiers by warranty length. Bike coatings skip the correction stage.
export const ceramicTiers: Record<SizeId, Record<Tier, number>> = {
  sedan: { 3: prices.ceramic, 5: 1197, 7: 1347 },
  suv: { 3: 1097, 5: 1297, 7: 1447 },
  large: { 3: 1147, 5: 1347, 7: 1597 },
  bike: { 3: 245, 5: 325, 7: 400 },
};
export const tiers: Tier[] = [3, 5, 7];

// Full and interior details carry a condition range, agreed on the day before work starts.
export const conditionRange = 75;

export type Guide = { price: number | null; suffix: string; why: string; cta: string };

const quoted = (why: string): Guide => ({ price: null, suffix: "", why, cta: "Get it quoted by text" });

export function guidePrice(job: JobId, size: SizeId, tier: Tier = 3): Guide {
  const lock = "Lock it in by text";
  if (job === "ceramic") {
    const p = ceramicTiers[size][tier];
    return size === "bike"
      ? { price: p, suffix: "", why: `${tier}-year written warranty on the tank and panels. No correction stage on a bike.`, cta: lock }
      : { price: p, suffix: "", why: `${tier}-year written warranty. Prep, polish and coating by the same two people.`, cta: lock };
  }
  if (size === "bike" && job !== "full") {
    return quoted(`On a bike, this is part of the full detail from $${table.full.bike}. Text us the bike and we'll sort the rest.`);
  }
  const p = table[job][size];
  if (job === "maintenance") {
    return p === null
      ? quoted("Monthly plans for larger vehicles are quoted for the vehicle. Text us the model and how it's used.")
      : { price: p, suffix: " a month", why: "One fixed price every month, quoted for your car.", cta: lock };
  }
  if (p === null) return quoted("Text us the vehicle and we'll quote it the same day.");
  if (job === "correction") {
    return { price: p, suffix: "", why: "Single-stage correction, then a sealant. Coating it afterwards is the most common package we do.", cta: lock };
  }
  if (job === "full" || job === "interior") {
    return {
      price: p,
      suffix: "",
      why: `Mobile anywhere in Canberra and Queanbeyan, no call-out fee. Condition can add up to $${conditionRange}, and we tell you before we start, never after.`,
      cta: lock,
    };
  }
  return { price: p, suffix: "", why: "Mobile anywhere in Canberra and Queanbeyan, no call-out fee. The number you're quoted is the number you pay.", cta: lock };
}
