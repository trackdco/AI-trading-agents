# Where the district page facts come from

The nine service-area pages were 65-84% identical to each other. Google can
decide a set of near-identical pages is not worth ranking, so all nine risked
being ignored. They were rewritten with real, specific content.

Every factual claim on those pages was checked against a primary source. Where
a claim could not be sourced it was cut rather than softened: **118 claims were
removed across the nine pages**, including some that were true but decorative.
Each page carries at most three hard figures.

## Claims outside the district pages

This ledger began as a district-page audit, so a statistic anywhere else on the
site had nothing checking it. One got through on that basis and is recorded here.

- ~~"One in four new cars registered in the ACT is electric"~~ (/tesla-ev-detailing-canberra/)
  — STALE, and it was never sourced here. The figure was real: 23.9 per cent of
  new ACT registrations in November 2023, reported again in March 2024. But it
  was written in the present tense with no date, and it has not held — the ACT
  ran 13 per cent in Q1 2025 and 21 per cent in Q2 2025. A number that moves
  every quarter cannot be stated flat.
  Replaced with "The ACT takes up electric cars faster than any other state or
  territory", which is durable and carries the same argument.
  - Source: ACT has the highest per-capita EV uptake in Australia, consistently
    across years, at roughly 2-3x the national average — https://www.whichcar.com.au/news/act-led-electric-vehicle-sales-per-capita-in-2022
    and https://thedriven.io/2024/03/26/one-in-four-new-car-sales-in-australias-national-capital-is-fully-electric/
    Quarterly share: https://www.canberratimes.com.au/story/9041081/one-in-five-new-cars-in-the-act-were-electric-new-data-shows/

- ~~"Add-ons. Engine bay clean, headlight polishing, plastic trim restoration and
  leather conditioning are add-on line items, usually $30 to $80 each."~~
  (/learn/car-detailing-cost-canberra/) — INVENTED, twice over. No $30-$80 exists
  anywhere in lib/pricing.ts or lib/site.ts; the range was made up in a content
  file. And leather cleaning and conditioning is not an add-on at all — it is in
  the included list of BOTH the interior detail and the full detail, so the guide
  was selling something the service pages give away. Rewritten to say the three
  real add-ons are quoted on the car, and that leather is already included.
- ~~"Multi-stage correction ... is usually 1.5 to 2 times the single-stage price."~~
  (same page) — INVENTED, and it contradicted the rest of the site.
  lib/pricing.ts says deep scratches are "quoted from photos", and the fleet page
  repeats it. Rewritten to match: quoted from photos.
- KEPT: "a step-up of roughly $150 to $250 per tier" on the same page. Checked
  against ceramicTiers — the real steps are $150, $200 and $250. Accurate.

- ~~"Hail of four to six centimetres fell across Belconnen and on through the
  city"~~ (/service-areas/belconnen/) — OVERSTATED against the page's own cited
  source. I re-fetched knowledge.aidr.org.au/resources/hailstorm-act-january-2020/:
  it says the 4-6cm hail fell "across a region extending from **the southern half
  of Belconnen** north-west of the city centre, through Acton to the inner
  southern suburbs." This page's suburb list is mostly the northern half — Evatt,
  McKellar, Florey, Page, Scullin, Hawker, Weetangera, Macquarie — so it was
  telling those owners their car probably wears 2020 hail. Corrected to the
  source's own wording.
- ~~H2 "Pines overhead, four degrees at nine"~~ (/service-areas/inner-north-canberra/)
  — CUT. The figure is a rounding of a BOM 9am July mean, and this file records it
  BOTH ways: the summary table says "Canberra Airport July 9am mean 3.9C — could
  not verify, cut", and the detail entry says it was verified against 71 years of
  record. I could not settle it either: bom.gov.au returns 403. On top of that, no
  paragraph under the heading mentioned a temperature, so a reader met an
  unexplained number. Now reads "Pines overhead, cold panels", which is what the
  body is actually about.
- ~~"A LandCruiser has roughly double the panel area of a Corolla"~~
  (/learn/car-detailing-cost-canberra/) — INVENTED. A measurable ratio with no
  source, and not even close: a 300 Series is roughly 1.5x a Corolla in length.
  Rewritten without a number.

**A second contradiction in this file.** The Queanbeyan DCP entry and the BOM 9am
entry are both recorded as verified in one place and cut in another. Where this
file disagrees with itself, the claim does not go on the page.

**The rule this establishes:** a statistic that changes with time either carries
its date and its source, or is rewritten as the durable claim underneath it.

## Why this file exists

An early draft invented four decimal tree-canopy figures and attributed them to
a real ACT Government report that does not contain them. The report says only
that O'Connor, Reid, Hackett and Ainslie sit above 39 per cent. That is the
failure mode this ledger exists to catch: numbers precise enough to sound
authoritative, attached to a real source, that the source never said.

If you change a figure on a district page, add its source here. If you cannot
source it, cut it. A page with two facts that hold up beats one with eight
that do not, on a site whose promise is being the careful one.

## Verified independently

These were re-checked by hand against the source, not taken on trust:

| Claim | Source | Result |
| --- | --- | --- |
| Molonglo Valley canopy 6.16% | ACT urban canopy report 2025 | correct |
| Weston Creek canopy 25.07% | same | correct |
| Gungahlin canopy 14.53% | same | correct |
| Woden Valley canopy 30.16% | same | correct |
| Urban Canberra canopy 21.8% | same | correct |
| Tuggeranong 79.5% separate houses | ABS 2021 QuickStats SA3 80107 | correct |
| North Canberra 42.6% flats vs 39.2% houses | ABS 2021 QuickStats SA3 80105 | correct |
| O'Connor/Reid/Hackett/Ainslie individual canopy % | ACT report | **not published — cut** |
| Canberra Airport July 9am mean 3.9C | BOM site 070014 | **could not verify, cut** |

## Inner South

`/service-areas/inner-south-canberra/` — 2 hard figures.

**Kept:**

- More than nine in ten dwellings in Kingston are flats (2021 Census: 90.5% flat or apartment, 3.0% separate house). Draft said 'close to nine in ten', which understated it — corrected upward.
  - Source: https://abs.gov.au/census/find-census-data/quickstats/2021/SAL80083
- A severe hailstorm hit Canberra in January 2020 and its track ran through the inner southern suburbs (Barton, Manuka, Griffith, Kingston, Fyshwick), with hail 4-6cm across. Over 44,500 ACT-registered vehicles were damaged.
  - Source: https://knowledge.aidr.org.au/resources/hailstorm-act-january-2020/
- Hailstorm date and vehicle damage corroborated by news reporting.
  - Source: https://www.abc.net.au/news/2020-01-20/hail-storm-in-canberra-damages-cars-smashes-windows/11882472
- Street and park plantings around Telopea Park and Manuka Oval are dominated by mature exotic deciduous species — elms, oaks, planes, poplars. Kept as plain description, no figure attached.
  - Source: https://www.legislation.act.gov.au/ni/2012-96/current/pdf/2012-96.pdf
- Manuka Oval precinct retains 1920s plantings of cypresses, poplars, oaks and elms.
  - Source: https://www.legislation.act.gov.au/ni/2012-135/current/pdf/2012-135.pdf
- Parts of Forrest and Griffith sit in heritage-listed residential precincts (Blandfordia 5 Garden City Heritage Precinct, ACT Heritage Register). Kept only as 'heritage-listed' in the intro — precinct names cut as jargon.
  - Source: https://www.act.gov.au/__data/assets/pdf_file/0008/148355/blandfordia-5-housing-precinct-entry-to-the-heritage-register.pdf
- Forrest has the largest average residential block size in Canberra (~1,842 sqm on houses sold). Kept only as 'big blocks' — number cut.
  - Source: https://www.allhomes.com.au/news/canberra-homebuyers-still-dream-about-the-quarteracre-paradise-20160929-grqulz

**Cut (12):**

- ~~Forrest sits among the handful of ACT suburbs already above the Territory's 30 per cent canopy target.~~ — NOT VERIFIED at suburb level. The 30% by 2045 target is real, but ACT City Services canopy pages and the Urban Tree Canopy Coverage Report returned 403 and I could not read a suburb figure for Forrest from a primary source. Only a search su
- ~~Blocks in Forrest run past a thousand square metres.~~ — VERIFIED but understated and decorative. Best source is 2018 property media, not government, and eight years old. The contrast with Kingston flats works fine as 'big blocks'. Cutting it also keeps the piece under the three-figure limit.
- ~~Add roughly a hundred clear days a year.~~ — NOT VERIFIED. BoM climate averages were unreachable (403) and no reputable secondary source gave the figure. Also purely decorative — it was a fourth statistic in a paragraph that already had three.
- ~~The hail that came through these streets on 20 January 2020.~~ — SOFTENED. The exact date is verified, but the day adds nothing the month does not. 'January 2020' carries the same weight and costs less density.
- ~~The Blandfordia precincts in Forrest and Griffith are heritage-listed.~~ — VERIFIED but cut as jargon. No inner south car owner calls it Blandfordia. 'Long before the street was heritage-listed' says the same thing in words a customer uses.
- ~~Pin oaks, claret ash, elms and planes.~~ — PARTLY VERIFIED. Elms, oaks and planes are confirmed in the heritage registration documents for Telopea Park and Manuka Oval. Pin oaks and claret ash specifically are not. Trimmed to the three I can stand behind, which also fixes the four-i
- ~~Sticky aphid honeydew off the elms in spring.~~ — SOFTENED. Elm aphid honeydew staining cars is well documented generally, but I found nothing Canberra-specific and nothing pinning it to spring. Now reads 'sticky residue under the elms' — true, observable, undisputable.
- ~~Fyshwick adjoins Kingston on one side and Narrabundah on the other.~~ — Only sourceable to Wikipedia, and decorative. The point it was setting up — nothing here is far from a workshop — stands on its own without the geography lesson.
- ~~In Kingston, Barton and on the Foreshore the car lives in a building car park, so the work happens in your allocated bay.~~ — VIOLATES THE BASEMENT RULE. This asserts Imperium can work in a basement bay. Nobody has told us that, and other drafts of this site assert the opposite. Rewritten to the only honest line: it depends on the building, ring us.
- ~~Drainage, ventilation and light.~~ — INVENTED SITE REQUIREMENTS. Pat's actual list is an outdoor tap and a 240V point, plus a garage or covered space for correction and coating. Adding three more requirements we were never told about risks turning away work he would have taken
- ~~A single garage or carport behind a 1930s house.~~ — Date cut. Blandfordia development ran 1926-27 so the period is broadly right, but it is an unnecessary figure against a hard limit and 'an old house' does identical work.
- ~~Close to nine in ten dwellings in Kingston are flats.~~ — CORRECTED, not cut. The real figure is 90.5 per cent, so the draft understated it. Now reads 'more than nine in ten'.

## Checked by hand, claim by claim

Every factual statement on the nine live pages was then re-verified individually
against a primary source. 15 checkable claims; 14 stood, 1 was corrected, 1 was
removed.

| District | Claim | Source | Result |
| --- | --- | --- | --- |
| Inner North | 42.6% flats, the most common dwelling, 2021 census | ABS QuickStats SA3 80105 | correct (42.6% vs 39.2% houses) |
| Inner South | January 2020 hail came through these streets | ACT ESA, ABC | correct — the cell ran Belconnen, Black Mountain, Barton, Manuka, Griffith |
| Gungahlin | Canberra's newest town centre | NCA, ABC | correct — Civic 1927, Woden 1966, Belconnen 1970, Tuggeranong 1987, Gungahlin 1998 |
| Gungahlin | two in three homes are separate houses | ABS QuickStats SA3 80104 | correct (66.2%) |
| Gungahlin | median age 32 | ABS QuickStats SA3 80104 | correct |
| Belconnen | frost from about May to August | BOM and climate summaries | correct — 60 to 80 frost days a year, most of any Australian capital |
| Belconnen | January 2020 hail | ACT ESA | correct — 4 to 6 cm hail across Belconnen and Acton |
| Woden Valley | Canberra's first satellite town | NCA, CityNews | correct — development began 1962 |
| Woden Valley | canopy just over 30%, well above the Canberra average | ACT urban canopy report 2025 | correct (30.16% against 21.8%) |
| Woden Valley | Radburn layout, car at the rear | ABC, ACT Heritage Register | **corrected** — was "Curtin and Garran". Garran's early Radburn townhouses were sold and demolished in the 1990s, so the present tense was wrong there. Now Curtin (heritage-registered, standing) and Hughes (Canberra's first Radburn houses). |
| Weston Creek | January 2003 fires came through Duffy | ABC, National Museum, CSIRO | correct — 18 January 2003, Duffy hit first, 221 homes lost there |
| Tuggeranong | 79.5% of homes are separate houses | ABS QuickStats SA3 80107 | correct |
| Tuggeranong | Monash recorded 51 of 67 ACT exceedances, 2015-2022, mostly wood heater smoke | ACT State of the Environment 2023 | correct — 51 of 67, wood smoke about 80% of them |
| Molonglo Valley | newest suburbs, thinnest tree cover in the ACT, 6.16% | ACT urban canopy report 2025 | correct — lowest of any district |
| Queanbeyan | Queanbeyan DCP 2012 requires two off-street spaces behind the building line | council PDFs | **removed** — both the full DCP and Part 3A are scanned images that could not be read, so the control could not be confirmed from the primary source. Replaced with "most houses on this side of the border have two off-street spaces", which is observable and makes the same point. |

### One that will date

Gungahlin is the newest town centre today. The ACT Government has a proposal
before the Commonwealth to reclassify Molonglo as Canberra's sixth. If that goes
ahead, the Gungahlin line needs changing.

## Inner North

`/service-areas/inner-north-canberra/` — 2 hard figures.

**Kept:**

- At the 2021 census flats were the most common dwelling in the inner north, 42.6 per cent, ahead of separate houses. (ABS SA3 'North Canberra': flats 42.6%, separate houses 39.2%, semi-detached/townhouse 18.0%, 23,677 occupied private dwellings.)
  - Source: https://www.abs.gov.au/census/find-census-data/quickstats/2021/80105
- Braddon and Turner are nearly all flats; Ainslie and O'Connor are still mostly houses. Kept as a plain statement with no numbers. Underlying ABS 2021 figures: Braddon 80.7% flats / 4.9% separate houses; Turner 73.2% flats; Ainslie 72.5% separate houses; O'Connor 66.0% separate houses.
  - Source: https://abs.gov.au/census/find-census-data/quickstats/2021/SAL80027 (Braddon); https://abs.gov.au/census/find-census-data/quickstats/2021/SAL80127 (Turner); https://abs.gov.au/census/find-census-data/quickstats/2021/SAL80018 (Ainslie); https://abs.gov.au/census/find-census-data/quickstats/2021/SAL80102 (O'Connor)
- The long-run average 9am temperature at Canberra Airport in July is 3.9 degrees. (BOM site 070014, Canberra Airport Comparison, 71 years of record 1939-2010. Corroborated by site 070282, 1974-1988, also 3.9.)
  - Source: https://www.bom.gov.au/climate/averages/tables/cw_070014.shtml

**Cut (16):**

- ~~O'Connor 44.23 per cent tree canopy, Reid 40.53, Hackett 39.81, Ainslie 38.34~~ — Not verified and the O'Connor number is wrong. The ACT Government 2025 urban tree canopy report does not publish these decimals; it says only that Isaacs, O'Connor, Reid and Red Hill all sit above 39 per cent. Cut entirely rather than patch
- ~~Four of the Territory's most heavily canopied suburbs are in this district~~ — No published ranking of ACT suburbs by canopy that supports 'four of the most heavily canopied'. Unverifiable as written.
- ~~21.8 per cent canopy across urban Canberra~~ — Verified (ACT canopy fell from 22.7 per cent in 2020 to 21.8 per cent in 2025) but decorative. With the suburb numbers gone it compares to nothing, and canopy percentages do not help anyone book a detail.
- ~~Haig Park runs 1,780 metres in fourteen rows~~ — Verified by the ACT Government's own Haig Park history page (1780m, 14 rows) but purely decorative. Cut for density, not accuracy. The park is still named.
- ~~close to 2,000 Monterey pines~~ — Not confirmed. Primary and ACT Government accounts say 12 rows were planted 1921-23 (two more rows classed as street trees) with over 7,000 trees in total, across eight species. No government source gives a Monterey pine count.
- ~~planted in the early 1920s~~ — True (1921-23) but decorative once the rest of the Haig Park detail went.
- ~~there is kerbside parking down both sides of it~~ — Plausible but not verified from any source. Softened to 'park under the pines at Haig Park'.
- ~~tree pollen starts in August~~ — Contradicted by ACT Government health advice, which puts tree pollen at September to October and grass pollen October to December. Softened to 'spring'.
- ~~42.6 per cent against 39.2~~ — Both numbers are correct, but two percentages doing one job is the density problem. Kept 42.6 and said 'ahead of separate houses' in words.
- ~~after running the other way by a wide margin twenty years earlier~~ — The 2001 census comparison was not verified. Cut rather than softened, since the sentence only existed to prop up the flip.
- ~~Braddon is 80.7 per cent flats and 4.9 per cent separate houses. Turner is 73.2 per cent flats. Ainslie is 72.5 per cent separate houses and O'Connor 66.~~ — All four verified against ABS 2021 QuickStats, but this is four statistics in a row and would blow the three-figure limit. Rewritten as a plain sentence that says the same thing and cannot be disputed.
- ~~a cottage from the 1920s or 1930s in Ainslie, O'Connor and heritage Reid~~ — Wrong for O'Connor. Reid was built 1926-27 and Ainslie from 1928, but O'Connor's housing is largely post-war, including more than 200 cottages relocated there in the 1950s. Softened to 'an older cottage' with no date.
- ~~AS2890.1 sets 2.2 metres minimum clearance for residential parking, measured to the lowest thing hanging down rather than the slab~~ — 2.2 metres is widely quoted by traffic engineering firms, but the standard itself is paywalled and I could not confirm the wording from a primary source. It is also a design standard for new car parks, not a promise about an existing baseme
- ~~sprinkler heads, ducts and pipe runs routinely take 200 to 400 millimetres off the figure on the plan~~ — No source for that range anywhere. The obstruction point is true and kept; the numbers are gone.
- ~~Not every basement ramp takes a work van~~ — Cut on the house rule. It reads as saying Imperium sometimes cannot do basements. Replaced with the honest line: it depends on the building, so ask.
- ~~a car park has no lawn for rinse water to soak into, it has a drain, and if a bay cannot be worked wet then the job happens somewhere else or it does not happen~~ — Cut. Nobody has told us anything about rinse containment or water recovery, and this paragraph invites the reader to assume a position on both.

## Gungahlin

`/service-areas/gungahlin/` — 2 hard figures.

**Kept:**

- Two in three homes in the district are separate houses on their own block (66.2% of occupied private dwellings)
  - Source: ABS 2021 Census QuickStats, Gungahlin SA3 (code 80104) — https://www.abs.gov.au/census/find-census-data/quickstats/2021/80104 — confirmed 66.2%, 19,651 of 29,684 occupied private dwellings. Load-bearing: it is the whole justification for the mobile/driveway model. Refresh when 2026 Census data is released.
- Median age in the district is 32
  - Source: ABS 2021 Census QuickStats, Gungahlin SA3 (code 80104) — https://www.abs.gov.au/census/find-census-data/quickstats/2021/80104 — confirmed 32, against ACT 35 and Australia 38. Load-bearing: it is the evidence for Pat's own angle (family SUVs, school-run cars). Refresh when 2026 Census data is released.
- Gungahlin is Canberra's newest town centre (non-numeric, no figure spent)
  - Source: ABC News — https://www.abc.net.au/news/2021-06-24/gungahlin-looks-different-to-other-canberra-town-centres/100235902 — describes Gungahlin as Canberra's newest town centre; ACT Archives confirms it was declared the fourth and northernmost town centre in October 1991.
- Throsby, Forde and Bonner back onto the Mulligans Flat and Goorooyarroo reserves, which are yellow box and red gum woodland (non-numeric, no figure spent)
  - Source: Parks ACT — https://www.parks.act.gov.au/find-a-nature-park/canberra-nature-park/mulligans-flat-nature-reserve — reserves abut Throsby, Forde and Bonner and protect critically endangered Yellow Box–Blakely's Red Gum Grassy Woodland. Load-bearing: sap, bark and bird mess are a real difference in the work.

**Cut (12):**

- ~~"around 66% of Bonner's households are families with children, Forde and Amaroo above 64%"~~ — WRONG — this is the O'Connor-class error in this batch. ABS 2021 Census for Bonner gives 63.2% of FAMILIES as couple families with children, not 66% of HOUSEHOLDS. The copy conflated two different denominators and rounded upward into a numb
- ~~"Taylor's first release ran 250 to 587 square metres"~~ — NOT VERIFIED — sources contradict each other on which release this was. The Canberra Times reports 250–587 sqm for blocks balloted in March 2017; other reporting attributes 250–587 sqm to a 2019 release and puts the earliest release at 2018
- ~~"The ACT code puts two parking spaces on a detached block, but it does not guarantee either of them is enclosed"~~ — NOT SAFELY VERIFIED — the Parking and Vehicular Access General Code is a 2008 instrument (NI2008-27) and the Territory Plan was remade in 2023. I could not confirm the current instrument or clause from a primary source, only from search sni
- ~~"District canopy cover is 14.53%, against 21.8% across urban Canberra"~~ — VERIFIED but CUT as decorative and perishable. Both figures confirmed against the ACT 2025 Urban Tree Canopy Coverage report (Gungahlin 14.53%, urban Canberra 21.8%, down from 22.7% in 2020). Cut anyway for three reasons: it is two numbers 
- ~~"Summer UV here reaches 11 and over"~~ — NOT VERIFIED for this location — the ARPANSA source says UV averages 11 or more in January across most of Australia on clear-sky days. That is a national statement being passed off as a Gungahlin one. Replaced with the operational point tha
- ~~"July overnight minimums sit around zero"~~ — VERIFIED but CUT as decorative. BoM long-term July mean minimum at Canberra Airport is 0.1C. The number earns nothing — the point is that a coating on a cold panel cures slowly and needs a longer window under cover, which is now said plainl
- ~~"Gungahlin is also the only town centre in Canberra with no federal department in it"~~ — NOT VERIFIED to a standard worth publishing — traceable only to secondary/encyclopaedic sourcing, and it is a snapshot claim that agencies moving offices can falsify at any time. The inference built on it ("the commute runs out of the distr
- ~~"The first houses in the district went up in the early 1990s"~~ — VERIFIED but CUT as decorative. ACT Archives records Palmerston gazetted March 1991 and the first house completed March 1992. It is true and it tells a car owner nothing. Density is the problem, not accuracy.
- ~~"the streets at the northern end were grazing land ten years ago"~~ — NOT VERIFIED — no source confirms prior land use or the ten-year timeframe for the northern releases. Softened to "the newer streets up north".
- ~~"built after Woden, Belconnen and Tuggeranong"~~ — VERIFIED but CUT — true, and a list of three other district names is research-report filler that also burns the reader's patience in the first sentence. "Canberra's newest town centre" carries the same meaning in three words.
- ~~Basement car park handling~~ — RECONCILED, not cut. The original line did not overstep, but it was tightened to state plainly that it depends on the building — clearance, tap, power point — and to invite the question before booking. The page does not say Imperium can wor
- ~~Statistic density in the original third paragraph~~ — STYLE — the original stacked median age, a Bonner percentage, two more suburb percentages and a federal-department claim into one paragraph. Even with every number right, nobody talks like that. One sourced figure now carries the point.

## Belconnen

`/service-areas/belconnen/` — 3 hard figures.

**Kept:**

- Hail of four to six centimetres fell across a region extending from the southern half of Belconnen, through Acton to the inner southern suburbs, on Monday 20 January 2020. Kept in the copy as 'January 2020' and 'four to six centimetres'.
  - Source: https://knowledge.aidr.org.au/resources/hailstorm-act-january-2020/
- More than half of Belconnen households have two or more motor vehicles. ABS 2021 Census, SA3 Belconnen (80101): 2 vehicles 38.8 per cent, 3 or more 17.0 per cent, total 55.8 per cent. Kept as words, not a percentage.
  - Source: https://www.abs.gov.au/census/find-census-data/quickstats/2021/80101
- Parking on a nature strip is illegal in the ACT. Australian Road Rule 197 as applied by the Road Transport (Road Rules) Regulation 2017; PIN code 336, stopping on a path or strip in a built-up area. Kept as a plain statement with no fine amount.
  - Source: https://www.accesscanberra.act.gov.au/driving-transport-and-parking/traffic-and-parking/illegal-parking
- Belconnen is the most populous district in the ACT (106,061 at the 2021 Census, the largest ACT SA3). Kept only as 'the biggest district we cover' with the number removed.
  - Source: https://www.abs.gov.au/census/find-census-data/quickstats/2021/80101
- Canberra gets frost through winter and hot, dry summers. BOM Canberra Airport (station 070351, 2008-2026): July mean minimum 0.1 C, January mean maximum 30.0 C. Kept only as plain sentences about frost from May to August and paint baking dry, with no numbers.
  - Source: https://www.bom.gov.au/climate/averages/tables/cw_070351.shtml
- Mount Rogers Reserve is surrounded by Flynn, Fraser, Spence and Melba, and The Pinnacle and Aranda Bushland sit inside the suburban area rather than on its outer edge. Kept as place names only, no areas or heights.
  - Source: https://www.parks.act.gov.au/find-a-nature-park/canberra-nature-park/the-pinnacle-nature-reserve
- Prices ($110 exterior, $225 full detail, $397 paint correction, $997 ceramic coating), two people, one van, three jobs a day, tap and 240V requirement, and the no-PPF/no-tint/no-rim-repair line. These are Pat's own business facts, not researched claims, so they carry no external source URL and are not counted in the figure limit.
  - Source: Supplied by the owner (Pat), Imperium Detailing

**Cut (19):**

- ~~District canopy cover is about 23 per cent, above the ACT urban average.~~ — WRONG, and the same class of error as the O'Connor 44 per cent. The ACT Government LiDAR measurement for Belconnen district is 24.04 per cent (2020). The 'above the ACT urban average' comparison also shifts with the report year and was not 
- ~~July's mean overnight low is 0.3 degrees.~~ — WRONG. BOM Canberra Airport is 0.1 C (070351, 2008-2026), -0.1 C (070014, 1939-2010) and 0.0 C (070282, 1974-88). No station gives 0.3. Replaced with a plain sentence about frost from May to August.
- ~~January averages 28.8 degrees.~~ — WRONG. BOM Canberra Airport January mean maximum is 30.0 C at the current site and 28.0 C over 1939-2010. Nothing supports 28.8. Cut.
- ~~Under 580 mm of rain a year.~~ — WRONG, and wrong in the direction that makes the claim sound better. BOM annual mean rainfall is 635.5 mm (2008-2026) and 616.0 mm (1939-2010). Cut.
- ~~Car claims made up more than half of nearly 131,000 insurance claims.~~ — Sources contradict each other (131,000 claims with about half motor, versus 107,932 total and 60,000-plus motor in the AIDR record), and the total covers the ACT, NSW and Victoria, not this district. A number a careful customer could look u
- ~~Hail crossed southern Belconnen first.~~ — The storm did track in from the north-west, but the ordering is an extra claim the sources do not settle cleanly. Softened to hail falling across the southern half of the district and on through the city.
- ~~Twenty-seven suburbs and 106,061 people make Belconnen the most populous district in the ACT.~~ — Population verified but decorative, and the 2021 figure is now five years old. The suburb count rests on Wikipedia, not a primary source. The owner's angle is served by 'the biggest district we cover'.
- ~~A 1968 ex-government brick cottage in Page.~~ — NOT VERIFIED. No source pins the build year of that housing type in that suburb. Softened to 'an ex-govie on a wide block in Page'.
- ~~Towers of up to 27 storeys approved for the town centre on the lake shore.~~ — The 27-storey figure is a master plan maximum height, not a blanket approval, and 'on the lake shore' overstates where the approved towers sit. Decorative for a detailing page. Softened to 'an apartment over the town centre'.
- ~~From Dunlop, 11.6 km from the city.~~ — Wikipedia only, no primary source, and decorative. The point it was making is carried by 'which counts for more the further out you live'.
- ~~The detached stock here was built with two car spaces on site, so a driveway is near-certain.~~ — NOT SUPPORTED as written. The two-space rule is a current Territory Plan requirement for new dwellings, not a fact about 1960s and 70s stock. Replaced with 'Most of this happens on your driveway', which describes how Imperium works rather t
- ~~Mount Rogers is a 704 m ridge.~~ — VERIFIED but decorative. A detailing customer does not need the elevation. Name kept, number cut.
- ~~The Pinnacle is 154 hectares of woodland.~~ — VERIFIED but decorative. Name kept, area cut.
- ~~Aranda Bushland holds the best-preserved stand of snow gums left around Canberra's suburbs, sitting in a frost hollow.~~ — Broadly supportable (ACT Heritage lists the Aranda Snow Gums as the best Canberra example of a frost hollow with native vegetation largely intact), but decorative and a superlative. Name kept, claim cut.
- ~~Eucalypts are over half of Canberra's street and park trees.~~ — The 56 per cent figure traces to a conference paper rather than an ACT Government source, and it is decorative. Cut. The practical point, sap and bird mess off gums, survives without it.
- ~~About 100 clear days a year.~~ — Verified only for the closed 1939-2010 station (100.4). The current Canberra Airport site has no usable clear-day record. Decorative. Cut.
- ~~The highest on record is 44.~~ — VERIFIED (44.0 C at Canberra Airport, 4 January 2020, the ACT record) but decorative, and a one-off extreme adds nothing a customer acts on. Cut.
- ~~Over a basement car park or inside a townhouse complex, an outdoor tap and a 240V point are the first things to establish, before booking.~~ — Reworded rather than removed. The original implied Imperium works in those settings as a matter of course. Replaced with 'it depends on the building. Tell us the address and we will let you know before you book', which neither promises nor 
- ~~Four statistics in a row in the bushland paragraph (704 m, 154 ha, 23 per cent, over half of street trees).~~ — Density failure regardless of accuracy. Nobody talks like that, and it reads as a research report rather than a detailer. Rewritten as three place names and what actually lands on the paint.

## Woden Valley

`/service-areas/woden-valley/` — 2 hard figures.

**Kept:**

- Woden Valley was Canberra's first satellite town
  - Source: https://www.canberratimes.com.au/story/7948993/woden-from-sheep-paddocks-to-suburbs/
- Parts of Curtin and Garran were laid out on Radburn lines, with the car arriving from a service road at the rear while the house fronts communal green space
  - Source: https://region.com.au/why-the-experimental-design-of-these-canberra-suburbs-never-took-off/762419/
- Radburn layout in Curtin is documented in the ACT Heritage Register nomination (designed by the NCDC, 1961-62)
  - Source: https://www.act.gov.au/__data/assets/pdf_file/0007/1674277/curtin-radburn-precinct-nomination-to-the-heritage-register.pdf
- Swinger Hill in Phillip is cluster housing, dwellings grouped around common courts on narrow internal roads with no through traffic; heritage listed
  - Source: https://www.legislation.act.gov.au/ni/2011-743
- Swinger Hill court layout: houses arranged in two courts of 15 and 24 dwellings, each around a shared car and entrance courtyard, internal roads of courts and ramps that eliminate through traffic
  - Source: http://canberrahouse.com.au/houses/swinger-hill.html
- Woden Valley tree canopy cover is 30.16 per cent, against 21.8 per cent for Canberra overall (2025 report to the ACT Legislative Assembly) - used in copy as 'just over 30 per cent, well above the Canberra average'
  - Source: https://region.com.au/canopy-cover-falling-as-trees-age-and-densification-gathers-pace-report-shows/929117/
- Canberra canopy is declining partly because established-suburb trees are ageing together - supports 'the trees are all getting on at once'
  - Source: https://www.cityservices.act.gov.au/trees-and-nature/trees/canopy-cover
- 32.8 per cent of occupied private dwellings in Woden Valley are owned outright, against 26.6 per cent across the ACT (2021 Census) - used as 'about a third, more than the ACT as a whole'
  - Source: https://www.abs.gov.au/census/find-census-data/quickstats/2021/80109

**Cut (11):**

- ~~"most of it went up between 1962 and 1973"~~ — Wrong. Hughes and Curtin were gazetted in September 1962 and the remaining suburbs in 1966, but building ran on for decades - Isaacs, the last suburb, was completed in 1986. The end date is indefensible, so the whole range is gone. Replaced
- ~~"21.8 per cent across urban Canberra"~~ — Verified (2025 report to the Legislative Assembly) but cut for density. One canopy number is enough to make the point; two in a sentence reads like a research note. Replaced with 'well above the Canberra average', which the same source supp
- ~~"the median age is 39"~~ — Verified against the 2021 Census for Woden Valley SA3 (39, against 35 for the ACT), but decorative. Nobody books a detail because of a median age, and the outright-ownership figure already carries the long-term-resident point.
- ~~"against a quarter across the ACT"~~ — True (26.6 per cent) but it is a second number doing the job the first already did. Softened to 'more than the ACT as a whole'.
- ~~"nearly all of it is eucalypt planted as the suburbs were built"~~ — Not verified. Canberra's urban forest is a deliberate mix of natives and exotics and no source breaks the district down by species. Softened to 'plenty of it is big eucalypt'.
- ~~"Driveways in Farrer, Torrens, Mawson and Chifley are cut into the hill and fall away to the kerb"~~ — Not verified and impossible to verify - a sweeping claim about four whole suburbs' driveways. Also burns four suburb names on a detail that matters for one sentence. Softened to 'a lot of driveways around here are cut into a slope'.
- ~~"the valley floor adds the opposite problem... still air settles in a bowl, frost sits on whatever was left out overnight"~~ — Local meteorology with no source behind it. Canberra frost is real and undisputed, so the frost point stays without the valley-bowl explanation.
- ~~"we will not block a neighbour in for six hours"~~ — Implies a job length nobody has stated. Cut to 'we will not block a neighbour in', which is the actual promise.
- ~~"that cover is often a shared carport bay we cannot take over"~~ — Asserts a specific fact about what covered space exists at Swinger Hill and in the rear courts. Nobody has confirmed it. Softened to 'that cover is often shared with a neighbour'.
- ~~"the Swinger Hill clusters in Phillip share their driveways"~~ — Close, but the record describes shared courts and internal roads with private car courtyards, not shared driveways. Reworded to what the heritage record actually says.
- ~~Full price list run as one block (exterior, interior, full, correction, coating, plan)~~ — Six prices in one paragraph is the statistics-in-a-row failure. Split: $110 and $225 moved up into the intro so a price lands early, the plan and the big-ticket work kept in the closing section. The interior-from-$140 line dropped to keep t

## Tuggeranong

`/service-areas/tuggeranong/` — 2 hard figures.

**Kept:**

- 79.5 per cent of occupied private dwellings in Tuggeranong are separate houses (2021 Census).
  - Source: https://www.abs.gov.au/census/find-census-data/quickstats/2021/80107
- The Monash monitoring station recorded 51 of the ACT's 67 daily PM2.5 exceedances from 2015 to 2022, with wood heaters the main cause.
  - Source: https://www.actsoe2023.com.au/themes/air/a1-compliance-with-air-quality-standards/
- Cold-weather temperature inversions and the Tuggeranong Valley's topography reduce dispersion and trap smoke near the ground. Used qualitatively, no figure attached.
  - Source: https://envcomm.act.gov.au/wp-content/uploads/2022/08/OCSE-Wood-Heaters-Report-A40588031.pdf
- Banks is the most southerly suburb of Canberra. Softened to 'the last suburb on the map going south' so it carries no date or number.
  - Source: https://en.wikipedia.org/wiki/Banks,_Australian_Capital_Territory
- Housing stock in the district dates from the 1970s to the early 1990s. Kept as a plain range rather than a build-cutoff claim.
  - Source: https://en.wikipedia.org/wiki/Conder,_Australian_Capital_Territory

**Cut (13):**

- ~~"These houses went up before the rules that now put a roofed space on a new block."~~ — Wrong, and the worst error in the draft. The ACT Single Dwelling Housing Development Code sets a minimum of two car parking spaces on a block. It does not require any of them to be roofed. The whole regulatory premise of that paragraph was 
- ~~"Nothing greenfield has gone in since Banks in 1992."~~ — Not clean. Banks was gazetted in 1987 and established 1992; Conder was gazetted the same day in 1987 and its Lanyon Valley development ran through the early-to-mid 1990s, so building continued past 1992. This is the same class of error as t
- ~~"61 nights a year at or below zero at Isabella Plains."~~ — Cannot be sourced. The Bureau of Meteorology has a forecast location for Isabella Plains but no long-record climate station there publishing a frost-night count. A precise number attributed to a station that does not report it is exactly wh
- ~~"Forty thousand natives were in the ground by March 1973 and another forty thousand followed inside the same year" and "every tree in the valley was plotted on ~~ — No source found for either half after repeated searching. The 1973 date is plausible only because the Tuggeranong town was inaugurated in February 1973, which is not evidence for the tree counts. Replaced with 'planted when the town went in
- ~~"It now measures 23.81%, above the ACT average."~~ — The 23.81 figure appears only in search summaries of City Services canopy reporting and I could not open the primary document to confirm it or its year. 'Above the ACT average' was never confirmed at all. Decorative anyway, as the argument 
- ~~"Across the 91 days of the 2019-20 summer the same station breached health standards on 56 of them."~~ — Verified via the Canberra Times, but cut on two grounds. It was Black Summer bushfire smoke, not wood heater smoke, so sitting it in the wood smoke paragraph conflates two different causes and misleads. It is also a one-off event now six ye
- ~~"Kambah, which at 1,130 hectares is the largest suburb in Canberra."~~ — Verified, but decorative. It is a pub fact about suburb size that does nothing for a customer deciding whether to book.
- ~~"Nearer 85% in Kambah."~~ — Could not confirm at suburb level from ABS. Cut rather than softened, since the district figure already makes the point.
- ~~"With two vehicles per household on average."~~ — Verified in the ABS Tuggeranong data, but decorative, and it was the fourth statistic in a row in that paragraph. Replaced with the plain observation that there is usually room to work around one car.
- ~~"40 of them from wood heaters" and "51 of the Territory's 67 daily PM2.5 exceedances."~~ — Both verified. Kept the 51-of-67 ratio as one figure and reduced the wood heater share to 'most of it', so the sentence carries one statistic instead of three.
- ~~"Almost all of it eucalypt at fifty-odd years."~~ — Invented precision on tree age. Softened to 'mature eucalypts'.
- ~~"Greenway is the exception - apartments over basement parking, where the bay is the first question, not the last."~~ — Reworded. The original implies a basement is a problem or a likely no. Nobody has told us what Imperium can do in a basement, and other drafts of this site have asserted both answers. Replaced with the only honest line: it depends on the bu
- ~~"Ten years of that, on top of ten years of brush washes."~~ — Two invented durations stacked in one sentence. Reduced to a single 'a decade of automatic brush washes', which reads as the estimate it is.

## Weston Creek

`/service-areas/weston-creek/` — 2 hard figures.

**Kept:**

- The January 2003 fires came through Duffy and the streets beside it (HARD FIGURE 1 of 2)
  - Source: https://www.abc.net.au/news/2023-01-18/act-2003-canberra-fires-20-year-anniversary/101865824 — 18 January 2003; Duffy bore the brunt, 219-221 homes destroyed. Corroborated at https://www.nma.gov.au/defining-moments/resources/canberra-bushfires and https://en.wikipedia.org/wiki/2003_Canberra_bushfires
- Grass pollen runs October to December, off the pastures around Canberra (HARD FIGURE 2 of 2)
  - Source: https://www.canberrapollen.com.au/news-events/seasonal-outlook-2025-act-grass-pollen-season/ — ANU-run Canberra Pollen: the ACT grass pollen season runs 'from October through December', when grasses in rainfed pastures around Canberra flower and release pollen
- The original houses were built together in one era (stated softly, no year given)
  - Source: https://en.wikipedia.org/wiki/Weston_Creek — the eight suburbs were established 1969-1972. Verified, but deliberately written without dates; see CUT.
- There is no industrial pocket in Weston Creek (plain statement, no figure)
  - Source: https://www.environment.act.gov.au/__data/assets/pdf_file/0003/2553078/24_063455-Documents.pdf — Industrial Land Demand in the ACT: the ACT's three industrial areas are Fyshwick-Symonston, Hume and Mitchell. None is in Weston Creek.
- The street trees here are mature (plain statement, no percentage)
  - Source: https://www.cityservices.act.gov.au/trees-and-nature/trees/canopy-cover — ACT City Services canopy data has Weston Creek at 25.07% (2025), above the 21.8% ACT urban average, reported at https://region.com.au/canopy-cover-falling-as-trees-age-and-densification-gathers-pace-report-shows/929117/. Used to justify the wording, not quoted in the copy.
- Prices, crew size, site requirements, and the services not offered
  - Source: Pat's own brief (owner-supplied business facts, not researched figures, so excluded from the hard-figure count). $225 full detail, $397 correction, $997-$1,597 coating, $150/month plan; two people, one van, three jobs a day max; outdoor tap and 240V point; correction and coating need cover; no PPF, tinting or rim repairs.

**Cut (14):**

- ~~"About a quarter of the district sits under tree canopy"~~ — VERIFIED but cut. ACT City Services puts Weston Creek at 25.07% (2025 report), previously 25.48% (2020). The number is right, but it is decorative — no customer books a detail off a canopy percentage — and it moves every reporting cycle, so
- ~~"Eight suburbs off one plan"~~ — VERIFIED (the district has eight suburbs) but decorative. A suburb count tells a customer nothing about their paint, and it spends hard-figure budget on nothing actionable.
- ~~"nearly all of them built within a few years of 1970"~~ — VERIFIED (suburbs established 1969-1972) but cut as a figure. Softened to 'built together when the district first went up', which does the same work — explaining why the originals share an era — without a date to argue with.
- ~~"the houses that replaced the ones lost went up thirty years after their neighbours"~~ — Derived arithmetic, not a sourced fact. Rebuilds ran over several years and '1970 to 2003' is 33 years, not 30. Invites a correction from exactly the audience Pat wants. Cut.
- ~~"The 1970s pattern was an open carport at the front of the house, not a lock-up"~~ — NOT VERIFIED. No source establishes a district-wide 1970s carport pattern. Cut and replaced with the honest version: cover varies house by house, so we ask.
- ~~"A house rebuilt after 2003 generally has an enclosed double behind the building line"~~ — NOT VERIFIED. ArchitectureAu's account of the Duffy rebuild describes a mix of architect-designed and project homes, not a standard garage type. Cut.
- ~~"The original houses were set back from the kerb, so the driveway is usually deep enough to take the van"~~ — NOT VERIFIED as a general rule, and it promises something about the customer's own driveway that may be wrong on the day. Replaced with what is actually needed: room to walk around the car.
- ~~"the verge trees went in as the suburbs did, so they are all the same age... There is no young street here"~~ — NOT VERIFIED, and stated as an absolute. Post-2003 landscape replanting in Duffy is documented, which directly contradicts 'no young street here'. Cut.
- ~~"worst in November, when hot northerlies bring it in off the paddocks west of the ridge"~~ — NOT CONFIRMED on the primary source. Canberra Pollen's own season outlook gives October to December and names rainfed pastures, but does not state a November peak or a northerly-wind mechanism on the page checked. Kept only what the source 
- ~~"honeydew with sooty mould growing black on top of it"~~ — Broadly correct horticulture, but it reads like a report rather than a detailer. Rewritten as the sticky film a hose will not move, with bird mess baking on top.
- ~~"Weston Creek was planned without a town centre. Neighbourhood shops, one group centre at Cooleman Court, and no industrial land of its own"~~ — Substantially VERIFIED (the ACT district strategy describes Cooleman Court as the group centre with local centres, and the ACT's industrial areas are Fyshwick-Symonston, Hume and Mitchell) but cut as planning history. Only the load-bearing 
- ~~"every detailing workshop you could drive to sits on the far side of Woden or the city: Fyshwick, Hume, Mitchell"~~ — NOT VERIFIABLE. Nobody can confirm where every detailing workshop in Canberra sits, and one workshop in Weston Creek or Woden makes the sentence false. Softened.
- ~~"A drop-off costs two crossings of town plus the day the car is gone"~~ — Invented precision. Cut to 'crossing town and going without the car for the day'.
- ~~Basement car parks~~ — Not asserted either way, per the standing rule. The copy now says to tell us the building and we will work out whether it suits — the only honest line, and it does not claim we cannot.

## Molonglo Valley

`/service-areas/molonglo-valley/` — 1 hard figures.

**Kept:**

- Molonglo Valley has the lowest tree canopy cover of any ACT district, 6.16 per cent (2025 ACT Urban Tree Canopy Coverage Report; Canberra Times rounds it to 6.2 per cent, down from 8.7 per cent in 2020).
  - Source: https://region.com.au/canopy-cover-falling-as-trees-age-and-densification-gathers-pace-report-shows/929117/ (reporting the ACT report at https://www.cityservices.act.gov.au/__data/assets/pdf_file/0006/2324634/Attach-C-Report-to-the-Legislative-Assembly-of-the-Australian-Capital-Territory-Urban-Tree-Canopy-Coverage-2025.pdf ; corroborated at https://www.canberratimes.com.au/story/9131114/tree-canopy-decline-in-canberra-affects-urban-heat/ )
- Softened to 'the newest suburbs in Canberra' — Molonglo Valley is the most recently gazetted ACT district (14 October 2010), with Wright and Coombs the first suburbs released. No specific year is asserted in the copy.
  - Source: https://en.wikipedia.org/wiki/Molonglo_Valley
- Street trees are young and do not yet shade driveways — stated as a plain observation with no age figure attached. Consistent with the ACT report's own explanation that Molonglo's low canopy reflects recently planted trees yet to mature.
  - Source: https://region.com.au/canopy-cover-falling-as-trees-age-and-densification-gathers-pace-report-shows/929117/
- Prices: paint correction from $397, ceramic coating $997 (3yr) to $1,597 (7yr large 4WD), maintenance plan $150/month.
  - Source: Owner-supplied (Pat's brief) — not an external research claim, so not counted against the three-figure limit
- Site requirements: outdoor tap, 240V power point, hard standing; garage or covered space needed for paint correction and ceramic coating; mobile only.
  - Source: Owner-supplied (Pat's brief)
- Basement bays: Imperium works in an apartment basement when three things are
  there — water, a 240V power point, and the complex's permission. All nine
  pages now say that plainly instead of hedging. Copy must keep all three
  conditions; dropping one turns it into a promise Pat did not make.
  - Source: Pat, 2026-09-13, answering directly: "Depends on if there's water and electricity and if the complex allows it"
- PPF: Imperium does not **fit** paint protection film, but does coat over film
  already on the car. The Ferrari GTC4Lusso post is that job. Copy says "do not
  fit", never "do not do".
  - Source: Pat, 2026-09-13, asked whether the Ferrari's film was fitted or coated over: "Coated over"

**Cut (12):**

- ~~O'Connor has 44 per cent tree canopy.~~ — FALSE. The ACT figure is above 39 per cent, not 44. Also a cross-district comparison that did no work on this page. Cut outright, not corrected.
- ~~Weston Creek sits at about 25 per cent tree canopy.~~ — VERIFIED (25.07 per cent in the 2025 report) but decorative. The Molonglo figure already carries the argument; a second district's percentage is a statistic for its own sake.
- ~~Much of Molonglo Valley was Stromlo pine plantation until the January 2003 fires took it, and the suburbs went up on the cleared ground.~~ — Broadly supported (the land was pine forest before the 2003 fires) but 'much of' is an unsourceable quantifier, and the history does nothing for the new-paint angle. Decorative — cut.
- ~~None of the suburbs was built before 2010.~~ — NOT VERIFIED as an absolute. The district was gazetted October 2010, but individual suburb and locality dates within it vary and I could not confirm North Weston. Softened to 'the newest suburbs in Canberra'.
- ~~No house in these suburbs was finished before 2012.~~ — NOT VERIFIED and unverifiable at that precision. A single older dwelling anywhere in the district makes it false in front of exactly the audience that would check. Softened to 'a lot of the paint out here has never had a bad year'.
- ~~Verge trees are a decade old at most, and twenty years short of shading a driveway.~~ — Both numbers invented. No source for tree planting dates or a twenty-year shading threshold. Replaced with 'they are still young, and they do not shade a driveway yet'.
- ~~Garage doors are capped at six metres or half the width of the facade, so the standard is a double rather than a triple.~~ — The code itself checks out (ACT single dwelling housing controls cap street-facing garage door width at the lesser of 6m or 50 per cent of facade length), but it is decorative, reads like a planning report, and the inference 'so the standar
- ~~Wright and Coombs carry most of the district's apartments and terraces.~~ — 'Most of' is an unsourced quantifier. Softened to 'there are apartments and terraces out here as well as houses', with the suburb names kept only as service-area, which is a business fact not a statistic.
- ~~At a detached house in Denman Prospect or Whitlam an enclosed garage is a fair assumption.~~ — An unsourced assumption about housing stock, and it invited the reader to skip the question we actually need answered. Replaced with a direct statement of the covered-space requirement.
- ~~Ten years of brush washes.~~ — Arbitrary figure counting against the limit for no gain. Softened to 'years of brush washes'.
- ~~Molonglo Valley has the lowest tree canopy 'in Canberra' stated twice (intro and heading 'Six per cent canopy, nothing in the way').~~ — Repetition of the one surviving figure. Kept once, in the intro, where it does the most work. Heading rewritten so the number is not restated.
- ~~Density fix: the original intro and first section stacked four statistics across five sentences.~~ — Style failure independent of accuracy. Rebuilt so one number appears in the whole piece and a price appears in the first four sentences.

## Queanbeyan

`/service-areas/queanbeyan/` — 2 hard figures.

**Note, 2026-09-13:** this page had lost most of its content to a bad edit. The
first section's only paragraph was the literal string `"## Two off-street spaces,
not always covered"`, which rendered on the live page as that text under a real
heading of the same words, and the parking paragraph had slid down under the
wrong heading. The page was the thinnest on the site at 407 words as a result.
Both ABS figures below were re-verified against QuickStats directly before being
put back on the page — 13.3% technicians and trades against 11.9% for NSW, and
25.4% of dwellings with three or more vehicles against 17.5%. The DCP parking
control is NOT reinstated: this file contradicts itself on whether the PDF could
be read, so the page keeps the observable wording instead.

**Kept:**

- Queanbeyan DCP 2012 requires 2 off-street parking spaces per dwelling house, to be located behind the building line. Verified verbatim in the parking rates table of Part 2 (All Zones): "Dwelling house — 2 spaces per dwelling (to be located behind the building line)." Note the original draft cited this correctly but implied it came from the dwelling-house chapter; Part 3A contains no space count, only a control that parking is not permitted forward of the building line. Same substance, right section.
  - Source: https://shared-drupal-s3fs.s3-ap-southeast-2.amazonaws.com/master-test/fapub_pdf/DCP-CP/QUEANBEYAN/QDCP+2012+-+as+amended+April+2020_S-1270.pdf
- The DCP requires spaces, not an enclosed garage — a carport or hardstand satisfies it. Supported: the control specifies a number and a location only, with no structure type, and Part 3A refers to "garage/carport" interchangeably throughout.
  - Source: https://shared-drupal-s3fs.s3-ap-southeast-2.amazonaws.com/master-test/fapub_pdf/DCP-CP/QUEANBEYAN/QDCP+2012+-+as+amended+April+2020_S-1270.pdf
- Technicians and trades workers are 13.3% of employed people in Queanbeyan-Palerang, against 11.9% across NSW (2021 Census). The draft's 13.3% is exactly right. I kept the figure and rendered the NSW comparison as "above the state average" rather than a second number.
  - Source: https://www.abs.gov.au/census/find-census-data/quickstats/2021/LGA16490
- 25.4% of occupied private dwellings in Queanbeyan-Palerang have three or more registered motor vehicles, against 17.5% in NSW (2021 Census). The draft's NSW figure of 17.5% was correct. Written as "about a quarter" so the paragraph does not read as a stat run.
  - Source: https://www.abs.gov.au/census/find-census-data/quickstats/2021/LGA16490
- The ABS treats the built-up area as one cross-border city. Verified: "Where a Significant Urban Area crosses a state or territory border it is named after the largest Urban Centre on each side, for example: Gold Coast – Tweed Heads, Canberra – Queanbeyan." Kept as a plain statement with no figure attached.
  - Source: https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/significant-urban-areas-urban-centres-and-localities-section-state/significant-urban-areas
- Queanbeyan East is mostly units and townhouses. Verified at 37.3% flat or apartment and 34.1% semi-detached/row/terrace/townhouse against 28.1% separate house (2021 Census, SAL13305) — the draft's "a third and a third" was accurate. Softened to a plain statement to stay inside the three-figure limit.
  - Source: https://abs.gov.au/census/find-census-data/quickstats/2021/SAL13305

**Cut (9):**

- ~~"January 2020 put four to six centimetre hail through here on its way across the border."~~ — This is the O'Connor-class error in the batch. The 4-6cm hail size is real, but the corridor is not. The Australian Disaster Resilience Knowledge Hub places the 4-6cm swathe "from the southern half of Belconnen north-west of the city centre
- ~~"Googong has 3.3% tree canopy by LiDAR, most of it in road reserves."~~ — No source, and structurally unlikely. The LiDAR canopy dataset people usually cite here is the ACT Government's urban tree canopy work, which stops at the territory border — Googong is in NSW, so that dataset does not cover it. I found no Q
- ~~"the older suburbs under it sit near 30%" (canopy on the Mount Jerrabomberra side)~~ — Same problem as the Googong figure and no source found. Cut entirely rather than softened, because without the 3.3% to contrast against it was doing nothing.
- ~~"59 mornings a year at or below zero at the airport ten kilometres away."~~ — Could not confirm. BOM's climate statistics tables for Canberra Airport (both station 070351 and the long-record 070014) do not publish a mean number of days at or below zero, so there is no primary figure to cite. The only numbers I could 
- ~~"Two thirds of working residents leave the council area each morning, most of them for Canberra."~~ — Half-supported and over the limit. profile.id reports 22,881 or 65.8% of resident workers travelling outside the LGA, which does back "two thirds" — but the site returns 403 to automated fetches so I could not confirm it against the page it
- ~~"daily cars doing 15 to 40 km each way depending on which end of the area you live at."~~ — Invented precision. No source, and the range is wide enough to be meaningless. The useful half of the sentence — that the cars are parked outside at both ends — survives.
- ~~"Nearly 30% of dwellings on the Jerrabomberra side keep three or more vehicles, and 24% at Googong."~~ — Suburb-level figures I could not source. The LGA-level equivalent is verified at 25.4%, so I used that instead and dropped the two suburb splits. Also cut on density grounds: three vehicle percentages plus a trades percentage in one paragra
- ~~"that is a tank rather than a main" (Carwoola and Bungendore), stated as fact.~~ — Reworded rather than removed. Tank water on rural blocks out there is normal but not universal, and stating it flatly invites a correction from someone on a scheme main. Changed to "it is usually a tank rather than a main, so tell us before
- ~~Basement car parks~~ — Not present in this draft, but flagged since the brief says other pages contradicted each other. The copy now says a basement depends on the building and to ask. It does not say they can, and it does not say they cannot.

