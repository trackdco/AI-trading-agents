import type { Faq } from "./services";

export type Section = { h: string; p?: string[]; list?: string[] };

export type Article = {
  slug: string;
  title: string;
  description: string;
  h1: string;
  intro: string;
  sections: Section[];
  faq: Faq[];
};

// The two guides from the current site, kept close to the original wording.
export const articles: Article[] = [
  {
    slug: "car-detailing-cost-canberra",
    title: "How Much Does Car Detailing Cost in Canberra? (2026)",
    description:
      "Real Canberra detailing prices: what a full detail, interior detail, exterior detail, paint correction and ceramic coating actually cost, and what changes the price.",
    h1: "How much does car detailing cost in Canberra?",
    intro:
      "In Canberra in 2026, a mobile exterior detail runs $110 to $140, an interior detail $140 to $170, and a full detail (inside and out) $225 to $270 depending on vehicle size. Paint correction starts at $397 and a 3-year ceramic coating starts at $997. These are real, no-surprise prices, not \"from\" hooks.",
    sections: [
      {
        h: "Pricing by service and vehicle size",
        p: [
          "All prices are AUD for a mobile service with water and power supplied on site. Ceramic coating and paint correction need a covered garage or workspace.",
          "Sedan pricing covers most hatches too. The 4WD and 8-seater bracket includes LandCruiser, Patrol, Ram, LDV and full-size 4WDs. A condition-based adjustment of up to $75 applies to genuinely extreme jobs, and we tell you before we start.",
        ],
        list: [
          "Exterior detail: $110 to $140",
          "Interior detail: $140 to $170",
          "Full detail: $225 to $270",
          "Paint correction: from $397",
          "Ceramic coating: from $997 (3-year tier)",
        ],
      },
      {
        h: "What actually changes the price",
        p: ["Six things move the number up or down, in order of impact."],
        list: [
          "Vehicle size. A LandCruiser has roughly double the panel area of a Corolla and takes noticeably longer. Every price scales with size.",
          "Interior condition. A tidy interior takes about 1.5 hours to deep-clean. Years of pet hair, sand or spilled milk can double that, and stains that need multiple extraction passes cost more product too.",
          "Paint condition. Regular decontamination is priced into every exterior detail. Heavy bonded contamination or oxidation on an unwaxed daily driver may push you into paint-correction territory.",
          "Coating tier. Longer warranties mean more layers, more prep and more time. Expect a step-up of roughly $300 to $500 per tier.",
          "Correction stages. A single-stage correction removes light swirl marks and haze. Multi-stage correction for deep scratches and heavier defects is usually 1.5 to 2 times the single-stage price.",
          "Add-ons. Engine bay clean, headlight polishing, plastic trim restoration and leather conditioning are add-on line items, usually $30 to $80 each.",
        ],
      },
      {
        h: "What isn't extra",
        list: [
          "Travel to your suburb: no call-out fee anywhere in the ACT or Queanbeyan",
          "Water and power: we're fully self-contained",
          "Consumables, product and disposal",
          "Card or transfer payment fees",
        ],
      },
    ],
    faq: [
      {
        q: "What's the cheapest way to keep the car looking good?",
        a: "The exterior detail at $110 for a hatch or sedan. It's a genuine two-bucket hand wash with chemical decontamination, a spray sealant, wheels, tyres and glass, not a hose-and-shampoo touch-up. If your interior is already tidy, it's the most cost-effective way to keep the outside sharp.",
      },
      {
        q: "Why does a full detail cost more than an automatic wash?",
        a: "An automatic wash takes about ten minutes and removes loose surface dirt. A full detail takes hours and includes decontamination, clay bar, an interior deep clean, steam extraction, sealant, wheels, glass and trim. You're paying for hours of manual work and product, and the result lasts months.",
      },
      {
        q: "Do you charge more for a really dirty car?",
        a: "Only if the condition changes the job significantly. A normal-messy family car is priced as-is. Genuinely extreme cases, like years of pet hair matted into the fabric or mould from a leak, we flag on inspection and quote a fair adjustment before starting. No surprise invoices.",
      },
      {
        q: "Is there a travel fee?",
        a: "No. We're mobile everywhere in Canberra and Queanbeyan for the same price. The quote you get is the price you pay.",
      },
    ],
  },
  {
    slug: "ceramic-coating-vs-paint-correction",
    title: "Ceramic Coating vs Paint Correction: Which Do You Need?",
    description:
      "The difference between paint correction and ceramic coating, which order they happen in, and how to tell which one your car needs.",
    h1: "Ceramic coating vs paint correction: which do you need?",
    intro:
      "Paint correction removes existing damage. Ceramic coating prevents future damage. Correction is the fix; coating is the protection. When both are needed, correction happens first. You always fix the paint before you seal it.",
    sections: [
      {
        h: "What each one actually does",
        p: [
          "Both services touch the paint, but they do opposite jobs. Getting them mixed up is the single most expensive mistake we see in Canberra: coating an uncorrected car and locking swirl marks in for years.",
          "Paint correction fixes what's there. Machine polishing with a compound or polish physically removes a microscopic layer of clear coat, and the swirl marks, holograms, water spots and light scratches sitting in it. Nothing is added; a tiny amount is taken away.",
          "Ceramic coating protects corrected paint. A liquid Si02 coating chemically bonds to the clear coat and cures into a hard, hydrophobic layer on top. It repels water, resists chemicals and makes contaminants easier to wash off. It's always applied after correction so the surface is defect-free before it's sealed.",
        ],
      },
      {
        h: "If you need both, the order matters",
        p: ["This is fixed. You do not coat first and correct later."],
        list: [
          "Decontamination wash: strip bonded iron, tar and grime.",
          "Paint correction: machine-polish out swirls, holograms and etching.",
          "Panel wipe: remove polish residue and oils so the coating can bond.",
          "Ceramic coating: applied panel by panel, wiped level, left to cure.",
          "24 to 48 hour cure: the car stays covered, dry and untouched.",
        ],
      },
      {
        h: "Which one do you actually need?",
        list: [
          "Coating with light prep: your car is under 12 months old, hand-washed only, and shows no swirls under direct light. We still run a light correction stage so the surface is perfect before the coating goes on.",
          "Correction then coating: your car is 1 to 5 years old, shows swirl marks or holograms in direct light, and you plan to keep it. This is the most common package we do.",
          "Correction with a sealant: you're preparing the car for sale, or want the finish reset once without committing to long-term coating maintenance.",
          "Full detail first: the paint is heavily faded or has deep scratches through the clear coat. Then an honest conversation about whether correction or a respray is the right next step.",
        ],
      },
    ],
    faq: [
      {
        q: "Can you ceramic coat without correcting first?",
        a: "We always carry out a paint correction stage before applying a coating. Even on a brand-new car we inspect the paint and do at least a light correction to remove wash marring or transport defects. Coating over swirls, holograms or etching just locks that damage in for years.",
      },
      {
        q: "How long does a ceramic coating actually last?",
        a: "It depends on the tier and how the car is used. A 3-year coating lasts around three years on a garaged, hand-washed daily driver, closer to two on a car that lives outside and goes through automatic washes. Longer tiers scale up from there. None of them mean \"never wash the car again\".",
      },
      {
        q: "What can't paint correction remove?",
        a: "Correction removes anything sitting in the clear coat: swirl marks, wash marring, water spots, light scratches you can't feel with a fingernail. Deeper scratches that catch your fingernail have cut through into the base paint. Those need touch-up paint or panel work.",
      },
    ],
  },
];

export const getArticle = (slug: string) => articles.find((a) => a.slug === slug);
