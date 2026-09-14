export type Area = {
  slug: string;
  name: string;
  blurb: string;
  /**
   * The page's own copy. These nine pages were 65-84% identical to each other,
   * which is how Google decides a set of pages is not worth ranking. Every fact
   * below was checked against a primary source — ABS census, ACT Government,
   * council planning documents — and anything that could not be sourced was cut
   * rather than softened. See docs/district-sources.md for the ledger.
   */
  intro: string[];
  sections: { h: string; p: string[] }[];
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
    intro: [
      "At the 2021 census, flats were the most common home in the inner north — 42.6 per cent of dwellings, ahead of separate houses. Most come with parking, but it is a numbered bay under a building, not a driveway. So the first question on a job here is not the car. It is where the car sits, and whether a van, a hose and a power point can reach it. Exterior detailing starts at $110, interior at $140.",
    ],
    sections: [
      {
        h: "Braddon is not Ainslie",
        p: [
          "Braddon and Turner are nearly all flats. A short drive out, Ainslie and O'Connor are still mostly houses. The two jobs look nothing alike.",
          "In the older streets we are beside a cottage where the garage went in decades later at the back of the block, down a long narrow drive. The drive decides whether the van gets past the house at all.",
          "In the flats the car is in a numbered bay, and access is the whole question. Ramp clearance first. Then an outdoor tap we can reach with a hose, and a 240V point near the bay rather than three levels up. We bring the rest.",
          "The last one is permission. Some complexes are fine with a detailer in the car park and some are not, so that gets asked before the booking, not on the morning. Water, power and a yes from the building, and we are down there.",
        ],
      },
      {
        h: "Covered space beats a back yard",
        p: [
          "Paint correction from $397 and ceramic coating from $997 both need a garage or covered space for the day. A car park can be a better room for that than a back yard. No wind, no pollen landing on a wet panel, no sun tracking across the bonnet.",
          "The limit is height. Sprinkler heads, ducts and pipe runs hang below the slab, so the clear height is always less than the ceiling looks. We measure the ramp and the lowest point overhead before a coating goes in the diary.",
          "Coating runs from $997 for three years up to $1,597 for seven years on a large 4WD.",
        ],
      },
      {
        h: "Pines overhead, cold panels",
        p: [
          "This is the leafy end of Canberra. Park under the pines at Haig Park, or along the older streets, and needles collect in shuts, cowls and roof rails. Resin marks the flat panels. Spring adds pollen on top. A full detail from $225 takes that back off. The monthly plan, from $90 for the exterior, is what keeps it off.",
          "Cold is the other half of a winter job. Panels are cold, water will not leave the surface and a coating cures slowly. Winter coating work gets a longer booking window, and we will move a day before we cut a cure short.",
          "Two of us, one van, three jobs a day across the inner north. No shop and no drop-off. We do not fit paint protection film, window tinting or rim repairs.",
        ],
      },
    ],
    suburbs: ["Braddon", "Dickson", "Lyneham", "O'Connor", "Ainslie", "Turner", "Watson", "Downer", "Hackett", "Campbell", "Reid"],
    bestFor: "Full detail",
    bestForSlug: "full-car-detail-canberra",
  },
  {
    slug: "inner-south-canberra",
    name: "Inner South",
    blurb: "Prestige and near-new vehicles. Ceramic coating and paint correction, at your door.",
    intro: [
      "More than nine in ten homes in Kingston are flats. Out in Forrest and Red Hill the houses sit on big blocks, and the cover over the car is whatever was built behind the house long before the street was heritage-listed. Paint correction from $397 and ceramic coating from $997 both need a roof over the car for a full day. So around here the site usually decides the booking, not the car.",
    ],
    sections: [
      {
        h: "Car parks and old garages",
        p: [
          "We do work in building car parks. Three things decide it: an outdoor tap we can run a hose from, a 240V point we can reach, and a building manager who is happy to have us down there. Past that it is the van — whether it clears the ramp and can turn at the bottom. Plenty of car parks have no tap at all. No water, no exterior work, and we would rather tell you that on the phone than on the day. Ring us with the building and we settle it before you book.",
          "The older detached streets are a different job. There is a driveway, and usually something at the rear, but rarely a modern double garage. A single garage or carport behind an old house is not getting any wider. Measure the inside of it before you book correction or coating. And tell us if your drive is one of the steep ones on the Red Hill slope.",
        ],
      },
      {
        h: "Leaves, not bark",
        p: [
          "The street trees through Forrest, Griffith and around Telopea Park and Manuka are mostly old exotics. Elms, oaks, planes. That is a different problem from the eucalypt suburbs. Instead of bark and sap all year you get a few heavy weeks of leaf fall, sticky residue under the elms, and wet leaves that will mark clear coat if they sit on a bonnet.",
          "The shade works backwards too. Full cover in February, bare branches in July, so the panels that were protected all summer are the ones taking the frost. And the January 2020 hail came through these streets, not past them.",
          "A coating makes that seasonal mess much easier to get off. It does nothing for etching already in the clear coat, and nothing at all for a dent.",
        ],
      },
      {
        h: "Why mobile in the inner south",
        p: [
          "Nothing around here is far from a workshop, so convenience is a thin reason to book a mobile detailer and we are not going to pretend otherwise. The reason is the day itself. Correction from $397, or a coating from $997 for three years up to $1,597 for a large 4WD on seven, takes the car out of your hands for most of a day plus two trips either end. Mobile, it never leaves the spot it already parks in. Two of us, three jobs a day, no more.",
          "If the car is a daily commuter that parks underground and sits under leaves at the other end, interior from $140 or the monthly plan from $90 is the honest place to start, not a coating.",
          "On site we need an outdoor tap and a 240V point. Correction and coating also need a garage or covered space. We bring the rest.",
        ],
      },
    ],
    suburbs: ["Kingston", "Manuka", "Griffith", "Narrabundah", "Red Hill", "Forrest", "Deakin", "Yarralumla", "Barton"],
    bestFor: "Ceramic coating",
    bestForSlug: "ceramic-coating-canberra",
  },
  {
    slug: "gungahlin",
    name: "Gungahlin",
    blurb: "Family SUVs and school-run cars. Interior deep cleans in your own driveway.",
    intro: [
      "Gungahlin is Canberra's newest town centre, and most of it is still houses on their own block — two in three homes, going by the census. That means a driveway, and a driveway is all we need. Two of us, one van, three jobs a day. Exterior from $110, interior from $140, a full detail from $225. You supply an outdoor tap and a 240V power point. We bring everything else.",
      "Paint correction from $397 and ceramic coating from $997 are the exception. Those need covered space for the day, so tell us what you have before we book.",
    ],
    sections: [
      {
        h: "The driveway is the work site",
        p: [
          "Blocks in the newer streets up north are small. Put a decent house on one and the side of the block is a footpath, so the driveway and whatever sits under the roof line is the whole job. The second car comes off the driveway for the day and stays off.",
          "One car out of a double garage is usually enough room to walk a panel and light it properly, which is what correction wants. An enclosed garage, a carport, or two uncovered spaces are three different jobs. None of them rules you out. They change what we can finish in a day.",
          "If the car lives in a basement bay in the town centre we can work down there, as long as there is a tap, a power point within reach and the complex allows it. Ramp clearance is the other one. Tell us the building and we check all of it before the booking, not on the day.",
        ],
      },
      {
        h: "What lands on the paint here",
        p: [
          "North of the centre the verge trees are young and nothing much hangs over a driveway. What settles on the paint is dust, grit and sun, and the flat panels dull first — bonnet, roof, boot lid.",
          "Throsby, Forde and Bonner back onto the Mulligans Flat and Goorooyarroo reserves. That is yellow box and red gum woodland over the fence line, and it drops sap, bark and bird mess. Same district, opposite problem.",
          "In summer we work to panel temperature rather than the clock, because a hot panel changes flash times. In winter a coating on a cold panel cures slowly, so that work gets a longer window and it has to be under cover. A roof is not an enclosure.",
        ],
      },
      {
        h: "Family cars, done at the house",
        p: [
          "The median age here is 32, and the cars match it. Kids, sport, the weekly shop, something spilled in the boot. The cabin usually needs more work than the paint does, which is why the interior detail starts at $140 and the full detail at $225.",
          "Dropping a car at a workshop costs you most of a day and two runs across the city. Working at the house costs you the driveway. That is the whole argument for doing it this way.",
          "If the car works that hard every week, the monthly plan, from $90, is what keeps a corrected finish from sliding back.",
        ],
      },
    ],
    suburbs: ["Gungahlin", "Harrison", "Franklin", "Crace", "Casey", "Amaroo", "Ngunnawal", "Nicholls", "Palmerston", "Forde", "Bonner", "Moncrieff", "Throsby", "Taylor", "Jacka"],
    bestFor: "Interior detail",
    bestForSlug: "interior-car-detailing-canberra",
  },
  {
    slug: "belconnen",
    name: "Belconnen",
    blurb: "The biggest district we cover. Everything from a quick exterior refresh to a full family-car detail.",
    intro: [
      "Belconnen is the biggest district we cover and the least uniform. An ex-govie on a wide block in Page, a townhouse in Bruce, an apartment over the town centre. We come to the car, which counts for more the further out you live. Exterior details start at $110.",
    ],
    sections: [
      {
        h: "Where we set up",
        p: [
          "Most of this happens on your driveway. We need an outdoor tap and a 240V power point. We bring the rest.",
          "We will not put wheels on the nature strip. That is illegal parking in the ACT, and the verge is where the street trees keep their roots.",
          "Paint correction and ceramic coating need a garage or a covered space, and that is the part worth sorting out early. More than half of households here keep two cars or more, so a single garage is often already full. Townhouse complex or a basement car park, we work in both, as long as there is water, a power point and the complex's permission. Tell us the address and we will confirm it before you book.",
        ],
      },
      {
        h: "The reserves sit between the suburbs",
        p: [
          "Mount Rogers, the Pinnacle, Aranda Bushland. The reserves here sit between the suburbs rather than past them, so plenty of streets back straight onto gums.",
          "Park under those and the car picks up sap, pollen, dust and bird mess, and it keeps picking it up between washes. Most of the time that is an exterior job. A full detail from $225 if the inside has had a season of kids, dogs and bikes as well.",
        ],
      },
      {
        h: "Frost, sun and the 2020 hail",
        p: [
          "Frost sits on anything left out on the driveway from about May to August. Summer runs the other way and the paint bakes dry more often than it gets rinsed. Neither is kind to a clear coat.",
          "Then there was January 2020. Hail of four to six centimetres fell across the southern half of Belconnen and on through Acton to the inner south, and plenty of cars from those streets still wear it. Paint with that history usually wants correction first, from $397, before a ceramic coating from $997 is worth doing.",
          "Two of us, one van, three jobs a day. No shop and no drop-off. We do not fit paint protection film, window tinting or rim repairs, and we will tell you that rather than take the booking.",
        ],
      },
    ],
    suburbs: ["Belconnen", "Bruce", "Kaleen", "Giralang", "Evatt", "McKellar", "Florey", "Page", "Scullin", "Hawker", "Weetangera", "Macquarie", "Cook", "Aranda", "Higgins", "Holt", "Latham", "Macgregor", "Dunlop", "Fraser", "Charnwood", "Flynn", "Melba", "Spence", "Lawson"],
    bestFor: "Full detail",
    bestForSlug: "full-car-detail-canberra",
  },
  {
    slug: "woden-valley",
    name: "Woden Valley",
    blurb: "Established suburbs, long-term residents. Regular maintenance details on a schedule.",
    intro: [
      "Woden Valley was Canberra's first satellite town, and the suburbs here have been lived in a long time. Most of what we pull up to is a brick veneer govvie set back from the kerb, with a driveway long enough to work on. Not all of it, though. Parts of Curtin and Hughes were laid out on Radburn lines, so the car sits at the rear off a service road, on the side the address does not mention. The houses at Swinger Hill in Phillip sit in small groups around shared courts. So the first thing we ask is not what the car is. It is where it sits. An exterior detail starts at $110 and a full one at $225.",
    ],
    sections: [
      {
        h: "The side of the house the address doesn't mention",
        p: [
          "Radburn put the car at the back. In those parts of Curtin and Hughes the street your letterbox faces may have no driveway on it at all, and the car lives off a service road at the rear, in a court shared with neighbours. Swinger Hill is the same idea at higher density: houses grouped around a common court, narrow internal roads, not much room to turn a van. Tell us the street the car actually sits on, and whether anyone needs to get past us during the day. We will not block a neighbour in. A lot of driveways around here are cut into a slope as well, so we work out which way the rinse runs before we start rather than after.",
        ],
      },
      {
        h: "Old gums over the driveway",
        p: [
          "Canopy cover across the district is just over 30 per cent, well above the Canberra average, and plenty of it is big eucalypt that went in when the houses did. The trees are all getting on at once. A car parked under one picks up sap, the black sooty film that comes with it, bark and bird mess, and across a summer that bonds into the clear coat. Taking that off is decontamination work, not a rinse. Winter is the other end of the problem. A frosted panel is not one to start wiping, so in the cold months we let the sun get onto the car first.",
        ],
      },
      {
        h: "Cars that stay put",
        p: [
          "About a third of homes here are owned outright, more than the ACT as a whole. People in Woden stay, and the same car sits in the same driveway under the same tree for years. That is a maintenance job rather than a one-off, which is what the monthly plan, from $90, is for. Paint correction from $397 and ceramic coating from $997 both need dry covered space for the day, and in the rear courts that cover is often shared with a neighbour, so we settle it before booking. From the house we need an outdoor tap and a 240V point. Everything else is in the van. Two of us, three jobs a day at the most.",
        ],
      },
    ],
    suburbs: ["Phillip", "Curtin", "Hughes", "Garran", "Lyons", "Chifley", "Pearce", "Torrens", "Mawson", "Farrer", "Isaacs", "O'Malley"],
    bestFor: "Exterior detail",
    bestForSlug: "exterior-car-detailing-canberra",
  },
  {
    slug: "weston-creek",
    name: "Weston Creek",
    blurb: "Leafy streets are hard on paint. Sap, pollen and bird mess removed and sealed against.",
    intro: [
      "Weston Creek has two kinds of house on it, sometimes on the same street. There are the originals, built together when the district first went up, and there are the ones that replaced what burned when the January 2003 fires came through Duffy and the streets beside it. The difference that matters to us is cover. An open carport and a lock-up garage are not the same job. A full detail starts at $225 either way, but what we can do past that depends on which one is yours.",
    ],
    sections: [
      {
        h: "Cover decides what we can do",
        p: [
          "Paint correction and ceramic coating have to be done under cover, so we ask what you have before booking rather than finding out on the day. It varies house by house here, not suburb by suburb. Past that we need an outdoor tap, a 240V power point, and room on the driveway to walk around the car. The rest is in the van. If you are in a unit and the only space is a basement bay, that works too, provided there is water down there, a power point, and the complex is happy with it. Tell us the building and we will check.",
        ],
      },
      {
        h: "Sap, pollen and bird mess",
        p: [
          "The street trees here are mature and they drop all year. Bark and gum nuts you can sweep off. The sticky film underneath is the problem, because a hose will not move it, and bird mess sits on top of it and bakes in. Grass pollen adds to the load from October to December, off the pastures around Canberra. Left on the paint long enough, all of it etches, and by then washing does not bring it back. That is what paint correction, from $397, is for. It goes before a coating, not after.",
        ],
      },
      {
        h: "Mobile, so the car stays home",
        p: [
          "There is no industrial pocket in this district, so a workshop detail means crossing town and going without the car for the day. We come to you instead. Two of us, one van, three jobs a day at most, and no shop to hurry back to. Ceramic coating runs from $997 for three years up to $1,597 for seven years on a large 4WD, and the monthly plan from $90 after it is what stops your own weekend wash turning back into decontamination work. We do not fit paint protection film, window tinting or rim repairs, so if that is what you are after, we are the wrong van.",
        ],
      },
    ],
    suburbs: ["Weston", "Holder", "Duffy", "Rivett", "Chapman", "Fisher", "Waramanga", "Stirling"],
    bestFor: "Exterior detail",
    bestForSlug: "exterior-car-detailing-canberra",
  },
  {
    slug: "tuggeranong",
    name: "Tuggeranong",
    blurb: "Deep south, furthest from city detailers. The mobile advantage is sharpest down here.",
    intro: [
      "Banks is the last suburb on the map going south. After that it is paddocks, then Namadgi. That distance is the ordinary reason people down this end book a van instead of driving north and leaving the car with someone for a day. The other reason is what sits over the valley every winter. Exterior detail from $110, full detail from $225. Two of us, one van, three cars a day.",
    ],
    sections: [
      {
        h: "Most houses down here have a driveway",
        p: [
          "The housing is mostly 1970s to early-1990s stock, and 79.5 per cent of homes in Tuggeranong are separate houses. A driveway is close to certain, and there is usually room to work around one car.",
          "Cover is the part that varies. Plenty of these blocks have an open carport rather than a garage. Exterior and interior work is fine in the open. Paint correction and ceramic coating are not, so we check what you have before we book anything.",
          "We need an outdoor tap and a 240V power point. We bring the rest. If your car lives in a basement under an apartment block in Greenway, we can work in the bay, as long as there is water and power down there and the complex lets us in. Tell us which one and we will check.",
        ],
      },
      {
        h: "Wood smoke sits in this valley",
        p: [
          "Cold nights put an inversion over the valley and hold the smoke down instead of letting it lift. The ACT's southern air monitor at Monash recorded 51 of the Territory's 67 daily PM2.5 exceedances between 2015 and 2022, most of it wood heater smoke.",
          "It settles on horizontal panels and it works into the cabin. That is why interior detail from $140 is not an afterthought down here. Half the time it is the job that changes how the car feels.",
        ],
      },
      {
        h: "Old gums and a decade of brush washes",
        p: [
          "These streets were planted when the town went in, so the trees are mature eucalypts now. Old enough to drop limbs, shed bark and put gum nuts on whatever is parked underneath. Add a decade of automatic brush washes and you get the swirls and the flat patches under the streetlight.",
          "Paint correction from $397 is what takes that back. A ceramic coating holds the result afterwards, $997 for three years up to $1,597 for seven on a large 4WD. The monthly maintenance plan, from $90, is there so you keep it rather than pay for it twice.",
          "We do not fit paint protection film, window tinting or rim repairs.",
        ],
      },
    ],
    suburbs: ["Greenway", "Wanniassa", "Kambah", "Monash", "Oxley", "Gowrie", "Fadden", "Macarthur", "Chisholm", "Richardson", "Gilmore", "Isabella Plains", "Bonython", "Calwell", "Theodore", "Conder", "Banks", "Gordon"],
    bestFor: "Full detail",
    bestForSlug: "full-car-detail-canberra",
  },
  {
    slug: "molonglo-valley",
    name: "Molonglo Valley",
    blurb: "Brand-new estates, brand-new cars. Ceramic coating from day one protects new paint properly.",
    intro: [
      "Molonglo Valley has the newest suburbs in Canberra and the thinnest tree cover of any district in the ACT, 6.16 per cent at the last count. Most cars here sit on an open driveway with nothing over them. We come to you. Paint correction starts at $397 and ceramic coating at $997.",
    ],
    sections: [
      {
        h: "Sun, and nothing in front of it",
        p: [
          "The street trees went in with the streets. They are still young, and they do not shade a driveway yet. That cuts both ways. There is far less sap, lerp and bird mess here than in the older parts of town, so paint is not getting fouled every week. What you get instead is sun, all day, with nothing in front of it. Flat panels take it first: bonnet, roof, boot lid. Once the clear coat has gone flat, washing is not what brings it back.",
        ],
      },
      {
        h: "Where the van sits",
        p: [
          "Blocks across Molonglo are small and the houses fill them. Some streets load from a rear lane rather than the front, so tell us how yours works. It decides where the van sits.",
          "Paint correction and ceramic coating both need a garage or covered space, and a full day of it, dry and lit. A carport is not enough. There are apartments and terraces out here as well as houses. If your car lives in a basement bay, we can work down there wherever there is a tap, a power point and the complex's okay.",
          "Wherever we end up we need an outdoor tap, a 240V power point and hard standing to work off. We bring the rest. We cover Denman Prospect, Whitlam, Wright and Coombs.",
        ],
      },
      {
        h: "The window where a coating does most",
        p: [
          "A lot of the paint out here has never had a bad year. That changes what a coating is buying. On a car that has been through years of brush washes, the correction has to happen first, and that is a full day before the coating starts. On paint still close to original, the spend goes into the coating instead of into undoing damage. Three years from $997. Seven years on a large 4WD, $1,597.",
          "New is not the same as perfect. Cars come off transport and out of dealer washbays with marks already in them, so we put a light across the panels before quoting, not after.",
          "Parts of the district are still a building site. Earthworks and truck traffic put grit in the air, and it settles and stays. That is what the monthly plan, from $90, is for. Upkeep, not rescue.",
        ],
      },
    ],
    suburbs: ["Wright", "Coombs", "Denman Prospect", "Whitlam"],
    bestFor: "Ceramic coating",
    bestForSlug: "ceramic-coating-canberra",
  },
  {
    slug: "queanbeyan",
    name: "Queanbeyan",
    blurb: "Cross-border coverage. Work utes and tradie vehicles alongside family cars.",
    intro: [
      "Everything here sits on the NSW side of the border: NSW plates, NSW planning rules, and a line the ABS ignores when it counts the whole built-up area as one city. Plenty of people cross it to work, so these are daily cars. Parked outside at home, parked outside all day at the other end. We come to you. Exterior work starts at $110, and all that has to come from the house is an outdoor tap and a 240V power point.",
    ],
    sections: [
      {
        h: "Two off-street spaces, not always covered",
        p: [
          "Most houses on this side of the border have two off-street spaces. So in Karabar, Crestwood, Jerrabomberra and Googong there is nearly always a driveway to work on. What you do not always get is a roof over it. A carport or an open hardstand is fine for an exterior detail, an interior or a full detail.",
          "Paint correction and ceramic coating are the exception. Those need a garage or covered space for the day, out of sun, wind and dust. It is worth settling that before the booking rather than on the morning.",
        ],
      },
      {
        h: "Work utes and the good car",
        p: [
          "Trades are a bigger share of the working population here than across the state — 13.3 per cent of employed people at the last census — and about a quarter of households keep three vehicles or more, well above the NSW rate. Put those together and a driveway in Karabar or Googong often has a work ute on it, a family car, and one the owner actually cares about.",
          "That is three different jobs at one address, and it is the easiest day we get: nothing goes on driving between suburbs, and it is one tap and one power point for the lot. A work ute is priced as an SUV and the good car by its own size, the same as they would be anywhere else.",
        ],
      },
    ],
    suburbs: ["Queanbeyan", "Queanbeyan East", "Queanbeyan West", "Karabar", "Crestwood", "Jerrabomberra", "Googong", "Greenleigh"],
    bestFor: "Paint correction",
    bestForSlug: "paint-correction-canberra",
  },
];

export const getArea = (slug: string) => areas.find((a) => a.slug === slug);
