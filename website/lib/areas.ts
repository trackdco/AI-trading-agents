export type Area = {
  slug: string;
  name: string;
  blurb: string;
  suburbs: string[];
  bestFor: string;
  bestForSlug: string;
};

// Nine districts, one mobile van. Copy carried over from the current site.
export const areas: Area[] = [
  {
    slug: "inner-north-canberra",
    name: "Inner North",
    blurb: "Apartment and townhouse living. No driveway, no problem: we detail at your building or workplace.",
    suburbs: ["Braddon", "Dickson", "Lyneham", "O'Connor", "Ainslie", "Turner", "Watson", "Downer", "Hackett", "Campbell", "Reid"],
    bestFor: "Full detail",
    bestForSlug: "full-car-detail-canberra",
  },
  {
    slug: "inner-south-canberra",
    name: "Inner South",
    blurb: "Prestige and near-new vehicles. Ceramic coating and paint correction, at your door.",
    suburbs: ["Kingston", "Manuka", "Griffith", "Narrabundah", "Red Hill", "Forrest", "Deakin", "Yarralumla", "Barton"],
    bestFor: "Ceramic coating",
    bestForSlug: "ceramic-coating-canberra",
  },
  {
    slug: "gungahlin",
    name: "Gungahlin",
    blurb: "Family SUVs and school-run cars. Interior deep cleans in your own driveway.",
    suburbs: ["Gungahlin", "Harrison", "Franklin", "Crace", "Casey", "Amaroo", "Ngunnawal", "Nicholls", "Palmerston", "Forde", "Bonner", "Moncrieff", "Throsby", "Taylor", "Jacka"],
    bestFor: "Interior detail",
    bestForSlug: "interior-car-detailing-canberra",
  },
  {
    slug: "belconnen",
    name: "Belconnen",
    blurb: "The biggest district we cover. Everything from a quick exterior refresh to a full family-car detail.",
    suburbs: ["Belconnen", "Bruce", "Kaleen", "Giralang", "Evatt", "McKellar", "Florey", "Page", "Scullin", "Hawker", "Weetangera", "Macquarie", "Cook", "Aranda", "Higgins", "Holt", "Latham", "Macgregor", "Dunlop", "Fraser", "Charnwood", "Flynn", "Melba", "Spence", "Lawson"],
    bestFor: "Full detail",
    bestForSlug: "full-car-detail-canberra",
  },
  {
    slug: "woden-valley",
    name: "Woden Valley",
    blurb: "Established suburbs, long-term residents. Regular maintenance details on a schedule.",
    suburbs: ["Phillip", "Curtin", "Hughes", "Garran", "Lyons", "Chifley", "Pearce", "Torrens", "Mawson", "Farrer", "Isaacs", "O'Malley"],
    bestFor: "Exterior detail",
    bestForSlug: "exterior-car-detailing-canberra",
  },
  {
    slug: "weston-creek",
    name: "Weston Creek",
    blurb: "Leafy streets are hard on paint. Sap, pollen and bird mess removed and sealed against.",
    suburbs: ["Weston", "Holder", "Duffy", "Rivett", "Chapman", "Fisher", "Waramanga", "Stirling"],
    bestFor: "Exterior detail",
    bestForSlug: "exterior-car-detailing-canberra",
  },
  {
    slug: "tuggeranong",
    name: "Tuggeranong",
    blurb: "Deep south, furthest from city detailers. The mobile advantage is sharpest down here.",
    suburbs: ["Greenway", "Wanniassa", "Kambah", "Monash", "Oxley", "Gowrie", "Fadden", "Macarthur", "Chisholm", "Richardson", "Gilmore", "Isabella Plains", "Bonython", "Calwell", "Theodore", "Conder", "Banks", "Gordon"],
    bestFor: "Full detail",
    bestForSlug: "full-car-detail-canberra",
  },
  {
    slug: "molonglo-valley",
    name: "Molonglo Valley",
    blurb: "Brand-new estates, brand-new cars. Ceramic coating from day one protects new paint properly.",
    suburbs: ["Wright", "Coombs", "Denman Prospect", "Whitlam"],
    bestFor: "Ceramic coating",
    bestForSlug: "ceramic-coating-canberra",
  },
  {
    slug: "queanbeyan",
    name: "Queanbeyan",
    blurb: "Cross-border coverage. Work utes and tradie vehicles alongside family cars.",
    suburbs: ["Queanbeyan", "Queanbeyan East", "Queanbeyan West", "Karabar", "Crestwood", "Jerrabomberra", "Googong", "Greenleigh"],
    bestFor: "Paint correction",
    bestForSlug: "paint-correction-canberra",
  },
];

export const getArea = (slug: string) => areas.find((a) => a.slug === slug);
