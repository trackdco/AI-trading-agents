import { prices } from "./site";

export type Faq = { q: string; a: string };

export type Service = {
  slug: string;
  name: string;
  short: string;
  title: string;
  description: string;
  h1: string;
  priceFrom: number;
  duration: string;
  image: string;
  imageAlt: string;
  intro: string;
  forWho: string;
  why: string[];
  included: string[];
  needs: string[];
  faq: Faq[];
  related: string[];
};

const water = "Access to water: an outdoor tap we can hook a hose to.";
const power = "Access to power: a standard 240V power point within reach.";
const garage =
  "An enclosed garage or covered workspace. Correction and coating work has to be done out of direct sun, wind and dust.";

export const services: Service[] = [
  {
    slug: "ceramic-coating-canberra",
    name: "Ceramic coating",
    short: "Ceramic",
    title: "Ceramic Coating Canberra (Mobile)",
    description:
      "Multi-layer Si02 ceramic coating applied at your home, with a written 3, 5 or 7-year warranty. Prep, polish and coating by the same two people, from $997.",
    h1: "Ceramic coating for Canberra conditions",
    priceFrom: prices.ceramic,
    duration: "A full day. Leave the car undercover for 24 hours after.",
    image: "beading-poster",
    imageAlt: "Water beading tightly on a freshly ceramic-coated white car",
    intro:
      "A ceramic coating is a semi-permanent glass-like layer that bonds to your car's clear coat and protects it from UV, frost, tree sap, bird droppings, industrial fallout and wash marring. It's the highest level of paint protection we offer, and once it's on, it stays on.",
    forWho:
      "For owners of new cars, weekend cars, black or dark-coloured cars that scratch easily, and anyone tired of waxing every three months to keep the paint looking sharp.",
    why: [
      "Canberra is one of the harder Australian environments for paint. Sub-zero winter mornings freeze whatever is sitting on the clear coat and burn it in. Summer sun oxidises pigment and fades colour. Autumn drops sap and pollen onto anything parked under a gum tree.",
      "The coating itself is a liquid-applied Si02 (silica) resin. Once cured it forms a hard, hydrophobic layer chemically bonded to the paint. Water beads tightly and rolls off, dust doesn't cling, and contaminants like bird droppings, sap and bug remains sit on top of the coating instead of etching into the paint.",
      "Prep is where a coating is made or broken. We start with a full decontamination wash, then chemically strip iron, tar and any residual sealants. On new or lightly used cars we do a single-stage machine polish to remove wash marring and level the surface before anything is applied.",
      "The coating is applied panel by panel, wiped off in the correct window and left to cure. We recommend leaving the car undercover for 24 hours and out of rain for 48. That's the only real inconvenience.",
      "You get a written warranty against loss of gloss and hydrophobics, optional annual inspections, and a coating-safe wash guide so you don't accidentally kill it with the wrong products. Applied by us, not a factory subcontractor.",
    ],
    included: [
      "Full decontamination wash and chemical strip",
      "Iron, tar and sealant removal",
      "Single-stage polish and paint prep on new or near-new paint",
      "IPA wipe-down before coating",
      "Multi-layer Si02 ceramic coating",
      "Wheel-face coating (optional)",
      "Glass hydrophobic coating (optional)",
      "Written 3, 5 or 7-year warranty",
      "Coating-safe wash guide and product recommendations",
      "Annual inspection (optional, no extra cost)",
    ],
    needs: [water, power, garage],
    faq: [
      {
        q: "How long does a ceramic coating last?",
        a: "Our coatings carry a 3, 5 or 7-year warranty depending on the tier you choose. Real-world durability in Canberra depends on how you wash the car: coatings degrade fastest at automatic car washes with spinning brushes, and last longest with a proper two-bucket hand wash.",
      },
      {
        q: "Do I still need to wash a coated car?",
        a: "Yes, but far less often and much more easily. A coated car sheds dirt and water instead of holding it, so a normal wash takes half the time and light dust often blows off in the rain. What the coating removes is the need to wax, polish or reseal.",
      },
      {
        q: "Do I need paint correction before coating?",
        a: "If your car has visible swirls, scratches or holograms, yes. A coating locks in whatever the paint looks like underneath, defects and all. On new or near-new cars we do a single-stage polish and prep, which is included. On older paint we'll quote paint correction first.",
      },
    ],
    related: ["paint-correction-canberra", "full-car-detail-canberra"],
  },
  {
    slug: "paint-correction-canberra",
    name: "Paint correction",
    short: "Correction",
    title: "Paint Correction Canberra",
    description:
      "Multi-stage machine polishing that removes swirls, scratches, oxidation and water spots from the clear coat. Measured with a paint depth gauge, inspected under LED. From $397.",
    h1: "Paint correction. Swirls, scratches, gone.",
    priceFrom: prices.correction,
    duration: "Half a day to a full day, depending on stages.",
    image: "correction-suv",
    imageAlt: "Black SUV with corrected, mirror-finish paint in a covered workspace",
    intro:
      "Paint correction is a multi-stage machine polish that removes defects inside your clear coat, instead of hiding them under a glaze. Swirls, wash marring, scratches, oxidation and water spots come out. True gloss and clarity go back in.",
    forWho:
      "For owners of used cars with tired paint, black or dark cars that show every mark, and anyone booking a ceramic coating who wants the paint locked in at its best.",
    why: [
      "Most \"scratches\" on a car aren't scratches. They're swirl marks and wash marring from rough sponges, dirty microfibres and automatic car washes dragging grit across the clear coat. Under bright light they look like fine cobwebs radiating out from the reflection.",
      "We start with a full decontamination wash so we're never polishing over grit. Then we measure paint thickness at multiple points on every panel with a digital gauge. That tells us how much clear coat we're working with and where we can and can't be aggressive.",
      "A single-stage correction uses one polish to clean up light swirls and restore gloss. A two-stage correction uses a compound first to cut deeper defects out, then a finishing polish to bring gloss back. A three-stage adds a heavier cut for paint that has been neglected for years.",
      "Between passes we wipe the paint with an isopropyl solution to strip out polish oils, so we see the true corrected finish, not a filled-in one. When we're done the paint is inspected under the same LED, photographed, and either handed back or protected.",
      "You get an honest assessment before we start, including what will and won't come out, a written record of paint thickness readings, and paint that looks visibly deeper, wetter and more reflective than when we arrived.",
    ],
    included: [
      "Decontamination wash and clay before polishing",
      "Digital paint thickness measurement",
      "LED inspection and defect map",
      "1, 2 or 3-stage machine correction",
      "Swirl, hologram and wash marring removal",
      "Light-to-moderate scratch removal (clear-coat depth)",
      "Oxidation and water spot removal",
      "IPA wipe-down between stages",
      "Before and after inspection photos",
      "Sealant or ceramic-coating prep to finish",
    ],
    needs: [water, power, garage],
    faq: [
      {
        q: "How many stages does my car need?",
        a: "We inspect the paint under strong LED and a paint depth gauge before we quote. Light swirls and holograms usually clear with a single-stage polish. Deeper wash marring, buffer trails or scratches you can catch with a fingernail edge need a 2 or 3-stage correction.",
      },
      {
        q: "Can you remove every scratch?",
        a: "No, and any detailer promising that isn't being straight with you. Correction removes defects within the clear coat. Scratches that have cut through the clear into the base coat need touch-up paint or panel work, not polishing. We'll tell you which is which before we start.",
      },
      {
        q: "Is machine polishing safe for my paint?",
        a: "Not when it's done properly is the wrong answer; yes, when it's done properly. We measure paint thickness before and after each pass, use the least aggressive pad and compound that will work, and stop well before we'd risk the clear coat.",
      },
    ],
    related: ["ceramic-coating-canberra", "exterior-car-detailing-canberra"],
  },
  {
    slug: "full-car-detail-canberra",
    name: "Full detail",
    short: "Full detail",
    title: "Full Car Detailing Canberra (Mobile)",
    description:
      "A complete inside-and-out reset: decontamination wash, machine-applied protection, and a top-to-bottom interior clean, in your driveway. From $225.",
    h1: "Full car detailing, anywhere in Canberra",
    priceFrom: prices.full,
    duration: "About 2.5 hours for a sedan; 2.5 to 4 hours for SUVs, utes and 4WDs.",
    image: "m4-foam-pov",
    imageAlt: "Foam gun in hand, a green BMW M4 covered in snow foam in a Canberra driveway",
    intro:
      "A full detail is a complete inside-and-out reset for your car: a proper decontamination wash, a machine-applied protection layer on the paint, and a top-to-bottom interior clean. It's the service to book if you want the car looking and feeling close to new again.",
    forWho:
      "For daily drivers, family cars and weekend cars that haven't had proper attention in six months or more, and for anyone about to sell, trade or hand back a lease.",
    why: [
      "Canberra is hard on paint. Frost overnight, grit on the arterials, iron dust from the brakes, tree sap in spring and pollen through summer all bond to the clear coat and dull the finish. A regular wash only touches the surface. A full detail strips it back and puts protection on top.",
      "On the outside we start with a pre-wash foam to lift loose grit, then a two-bucket hand wash with pH-neutral shampoo. Wheels, arches, tyres and door shuts are washed separately with their own mitts. Once clean, we chemically decontaminate the paint, clay bar every panel, and seal it.",
      "Inside we pull the mats, vacuum everything including under the seats and in the boot, then steam-clean the touch points: steering wheel, gear shifter, door cards, cupholders and console. Carpets and cloth seats get shampooed. Leather is cleaned and conditioned.",
      "We turn up in an unmarked van, work on your driveway or in your car park, and clean up after ourselves. You get a car that looks like it did on the showroom floor, without losing a Saturday driving it somewhere and waiting around.",
    ],
    included: [
      "Pre-wash snow foam and two-bucket hand wash",
      "Wheels, arches, tyres and door shuts detailed",
      "Iron and tar chemical decontamination",
      "Clay bar treatment on all painted panels",
      "Paint sealant or spray coating for 3 to 6 months of protection",
      "Full interior vacuum including boot and under seats",
      "Steam clean of all touch points and console",
      "Leather clean and condition, or fabric shampoo",
      "Interior and exterior glass, streak-free",
      "Tyre dressing and matte plastic dressing",
    ],
    needs: [water, power],
    faq: [
      {
        q: "Do I need to supply anything?",
        a: "No, we work with what you have on site. We need access to an outdoor tap and a standard 240V power point within reach of the car. If you don't have water or power available, let us know when you book and we can talk through the options.",
      },
      {
        q: "How long does a full detail take?",
        a: "Around 2.5 hours for a sedan or hatch. Larger SUVs, utes and 4WDs typically take 2.5 to 4 hours. We'll give you a realistic time window when we quote so you can plan your day.",
      },
      {
        q: "Do I need to be home?",
        a: "No. As long as we can access the car, a tap and a power point, you can leave us to it. We'll send a photo when we're finished and take payment by card or transfer once you're happy with the result.",
      },
    ],
    related: ["interior-car-detailing-canberra", "exterior-car-detailing-canberra"],
  },
  {
    slug: "interior-car-detailing-canberra",
    name: "Interior detail",
    short: "Interior",
    title: "Interior Car Detailing Canberra",
    description:
      "Deep clean of seats, carpets, roof lining, boot, leather and every touch point, with hot-water extraction and steam. Kid mess, pet hair and odours handled at the source. From $140.",
    h1: "Interior detailing that actually gets the kid mess out",
    priceFrom: prices.interior,
    duration: "About 1.5 hours for a tidy interior; longer for heavy stains or pet hair.",
    image: "lambo-interior",
    imageAlt: "Detailed leather interior of a Lamborghini, seats and stitching spotless",
    intro:
      "An interior detail is a deep clean of everything inside your car: seats, carpets, roof lining, boot, plastics, leather, glass and all the little touch points that pick up grime. It's the service for a car that's been through school runs, weekend sport and long trips.",
    forWho:
      "For parents, tradies, dog owners, anyone about to sell privately, and drivers who've bought a used car and want it reset before it becomes properly theirs.",
    why: [
      "Kids' cars have a specific list of problems: crushed sultanas in the seat crease, spilled Milo on the carpet, a booster seat that hasn't moved in two years, and something in the boot that smells but you can't quite locate. That's exactly what this service is for.",
      "We start by dry-vacuuming the entire interior, including the headliner, air vents, seatbelt wells and the slot between the seat and the console where coins and Lego live. Then we hit the hard surfaces with steam: dashboard, doors, console, cupholders.",
      "Fabric seats and carpets get a hot-water extraction. We pre-treat stained areas, agitate with a soft brush, then extract with a purpose-built machine that pulls the dirty water back out of the weave. That's how you get proper stain removal rather than a surface wipe.",
      "Odours get treated at the source. If it's a spilled drink, we extract the padding. If it's a general \"kid car\" smell, we steam-clean the vents and headliner where odour clings. We finish with a light neutral deodoriser, never a heavy perfume.",
      "You get the car back looking like the day you drove it home, with the child seats put back where you had them.",
    ],
    included: [
      "Full vacuum: seats, carpets, boot, headliner and vents",
      "Steam clean of dashboard, console and all touch points",
      "Hot-water extraction of cloth seats and carpets",
      "Stain treatment (food, drink, ink, organic)",
      "Pet hair removal from seats and carpet",
      "Leather clean and condition",
      "Roof lining spot clean",
      "Door shuts, seals and seatbelt clean",
      "Interior glass, streak-free",
      "Light neutral deodorise, no heavy perfume",
    ],
    needs: [water, power],
    faq: [
      {
        q: "Can you get stains and pet hair out?",
        a: "Most of the time, yes. We use hot-water extraction for cloth and carpet, dedicated enzyme cleaners for organic stains like milk, vomit and food, and rubber pet-hair tools that pull embedded fur out of the weave. If a stain is truly permanent, we'll tell you before we start.",
      },
      {
        q: "Will the car smell like air freshener afterwards?",
        a: "No. We use low-odour cleaners and finish with a light neutral scent, no fake cherry or pine. The car should smell clean, not like an air freshener. If you'd prefer no scent at all, just say so.",
      },
      {
        q: "Are the products safe around child seats and pets?",
        a: "Yes. Everything we use inside is water-based, non-toxic once dry, and safe for child seats, baby capsules and pet beds. Steam cleaning also kills bacteria and dust mites without adding chemicals to the fabric.",
      },
    ],
    related: ["full-car-detail-canberra", "exterior-car-detailing-canberra"],
  },
  {
    slug: "exterior-car-detailing-canberra",
    name: "Exterior detail",
    short: "Exterior",
    title: "Exterior Car Detailing Canberra",
    description:
      "Proper wash and chemical decontamination of paint, wheels, glass and trim, finished with a spray coating or sealant that protects for months. From $110.",
    h1: "Exterior detailing and paint protection",
    priceFrom: prices.exterior,
    duration: "About 1.5 to 2 hours.",
    image: "m4-rinse",
    imageAlt: "Rinsing a green BMW M4, water sheeting off the bonnet",
    intro:
      "An exterior detail is a proper wash and decontamination of the outside of your car: paint, wheels, glass, plastic trim and tyres, finished with a spray coating or sealant that shields the paint for months, not days.",
    forWho:
      "For daily drivers coming out of a Canberra winter, weekend cars stored between drives, and anyone who wants their paint protected before a ceramic coating becomes worth it.",
    why: [
      "Canberra paint takes a beating between May and September. Frost burns tree sap into the clear coat, salted mountain roads throw grit onto the sills, and iron dust from the brake pads bonds to the panels every time you drive. By spring, the paint feels gritty under your hand.",
      "We start with a pre-wash snow foam that clings to the panels and lifts loose grit before anything touches the paint. Wheels, arches and tyres are washed first with their own mitt so we're not dragging brake dust across the bodywork.",
      "Once the car is visually clean, we chemically decontaminate. An iron remover turns purple as it dissolves bonded brake dust. A tar remover takes bitumen off the lower panels. If needed, we clay bar the whole car to pull out embedded contamination.",
      "The car is dried with plush microfibres and a filtered air blower, then we apply a spray-on Si02 coating or a paint sealant depending on how long you want protection to last. Tyres get a satin dressing. Glass gets polished and sealed.",
    ],
    included: [
      "Pre-wash snow foam and rinse",
      "Wheels, arches and tyres washed separately",
      "Two-bucket hand wash with pH-neutral shampoo",
      "Iron and tar chemical decontamination",
      "Clay bar treatment as needed",
      "Filtered air-blow drying, no water spots",
      "Spray-on Si02 coating or paint sealant",
      "Glass polish and hydrophobic sealant",
      "Satin tyre dressing",
      "Door shuts, fuel flap and sills detailed",
    ],
    needs: [water, power],
    faq: [
      {
        q: "Isn't this just a car wash?",
        a: "No. A regular wash cleans loose dirt off the surface. An exterior detail chemically strips bonded contamination that a wash can't touch, then puts a protection layer on top. You'll feel the difference running a hand over the paint.",
      },
      {
        q: "How often should I book one?",
        a: "For most Canberra daily drivers, every 4 to 6 months. If you park outside under trees or drive a lot on country roads, closer to every 3 months. Between details, a normal wash is enough while the protection layer is still active.",
      },
      {
        q: "Will it remove swirl marks?",
        a: "An exterior detail cleans and protects but doesn't correct paint defects. Swirls, wash marring and light scratches need paint correction. If your paint has visible defects, we'll flag it on inspection and give you a price.",
      },
    ],
    related: ["full-car-detail-canberra", "ceramic-coating-canberra"],
  },
];

export const getService = (slug: string) => services.find((s) => s.slug === slug);

export const coreServices = services.filter((s) =>
  ["ceramic-coating-canberra", "paint-correction-canberra", "full-car-detail-canberra"].includes(s.slug),
);

export const formatPrice = (n: number) => `$${n.toLocaleString("en-AU")}`;
