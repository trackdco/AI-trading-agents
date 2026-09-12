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
    title: "Car Detailing Cost in Canberra (2026)",
    description:
      "Real Canberra detailing prices: what a full detail, interior, exterior, paint correction and ceramic coating actually cost, and what moves the price.",
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
    title: "Ceramic Coating vs Paint Correction",
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
  {
    slug: "dealer-paint-protection-vs-ceramic-coating",
    title: "Dealer Paint Protection vs Ceramic",
    description:
      "What the dealer's paint protection package usually is, what a real ceramic coating is, and the questions to ask before you sign for either.",
    h1: "Dealer paint protection vs a ceramic coating",
    intro:
      "The car is nearly yours, and the finance manager has one more thing: paint protection, often well over a thousand dollars, sometimes rolled into the loan. Here's what that usually buys, what a ceramic coating from a detailer buys, and how to tell the difference before you sign.",
    sections: [
      {
        h: "What the dealer package usually is",
        p: [
          "Most dealer paint protection is a sealant or a thin coating applied in the dealership's wash bay or by a subcontractor, in an hour or two, on a car that has come straight off a truck. There is rarely any decontamination and almost never any paint correction, so whatever transport marring and wash marks are already in the clear coat get sealed in.",
          "The warranty is the part worth reading. Many are long on years and short on cover: they often require paid annual inspections or reapplications to stay valid, exclude the things that actually damage paint, and pay out only when the product itself has visibly failed.",
          "None of this makes the product useless. It makes it expensive for what it is, and the price is usually negotiable, which tells you something about the margin.",
        ],
      },
      {
        h: "What a ceramic coating from a detailer is",
        p: [
          "A proper coating is mostly preparation. The car is washed and chemically stripped of iron, tar and any old sealant, then machine polished so the surface is level and clear before anything goes on. The coating is applied panel by panel, wiped in the right window, and left to cure.",
          "You get a written warranty you can read before you pay, a wash guide so you don't undo the work, and the same two people who did the job answering the phone afterwards. Our tiers and prices are on the ceramic coating page.",
        ],
      },
      {
        h: "Questions to ask before you sign",
        list: [
          "Who applies it, and where? A trained detailer in a booth, or whoever is free in the wash bay?",
          "What preparation is done first? If the answer is a wash, the marks under it stay.",
          "Can I read the warranty terms now, not after delivery?",
          "What do I have to pay for each year to keep the warranty valid?",
          "What does it exclude? Bird droppings, sap, wash marks and fallout are what paint actually suffers from.",
          "What happens to the price if I say no? If it drops by half, you have your answer.",
          "Can it be removed from the contract entirely? It's an optional extra, and the manufacturer's paint warranty doesn't depend on it.",
        ],
      },
      {
        h: "If you already paid for it",
        p: [
          "It isn't wasted, but it isn't a base for a coating either. A ceramic coating bonds to bare clear coat, so the dealer product has to come off first. If you want the real thing, we strip it as part of the standard prep, correct the paint and coat it.",
        ],
      },
      {
        h: "What we'd do with a new car",
        p: [
          "Book it in the first few weeks, before the first automatic wash. A light single-stage correction removes what the transporter and the dealer prep left behind, then a 5 or 7-year coating goes on while the paint is as good as it will ever be. In Canberra that also means it's protected before its first frost and its first pollen season.",
        ],
      },
    ],
    faq: [
      {
        q: "Is dealer paint protection worth it?",
        a: "Rarely at the price offered. You're paying a dealership margin for a product applied without correction, on warranty terms that usually require ongoing paid visits. The same money, or less, buys a properly prepared ceramic coating with a warranty you can read first.",
      },
      {
        q: "Can you put a ceramic coating over dealer paint protection?",
        a: "Not over it. A coating has to bond to the clear coat, so we strip the dealer product during prep, correct the paint and apply the coating to a clean surface. It's the same prep every coating gets.",
      },
      {
        q: "Will saying no affect my new-car warranty?",
        a: "No. The manufacturer's paint warranty stands on its own. Paint protection is an optional add-on sold by the dealership, and declining it changes nothing about the car's factory cover.",
      },
      {
        q: "When should a new car be coated?",
        a: "Within the first few weeks is ideal, before wash marks build up. If the car has already done a few months, it just means a little more correction before the coating goes on.",
      },
    ],
  },
];

export const getArticle = (slug: string) => articles.find((a) => a.slug === slug);
