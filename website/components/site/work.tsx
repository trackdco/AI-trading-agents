import { Picture } from "@/components/site/picture";
import { BeadingVideo } from "@/components/site/beading-video";
import { SectionHeading } from "@/components/site/section-heading";

// Every photo is shot on a phone in portrait, so the gallery embraces that:
// six 4:5 tiles, three across on desktop and two on a phone. The beading video
// sits in the top row so the one moving tile is the first thing the eye lands on.
const tile = "relative m-0 aspect-[4/5] overflow-hidden rounded-md bg-card";
const media = "absolute inset-0 h-full w-full object-cover";
const cap = "absolute bottom-3 left-3 rounded-md bg-background/75 px-2.5 py-1 text-xs text-secondary-foreground backdrop-blur";

const photos = [
  { name: "mclaren-650s", alt: "White McLaren 650S after a full detail in a Canberra driveway", caption: "Full detail, McLaren 650S" },
  { name: "correction-suv", alt: "Black SUV with corrected, mirror-finish paint", caption: "Paint correction" },
  { name: "huracan-driveway", alt: "Lamborghini Huracán after an exterior detail", caption: "Exterior detail, Huracán" },
  { name: "lambo-interior", alt: "Detailed leather interior of a Lamborghini", caption: "Interior detail" },
  { name: "m4-clean-front", alt: "Green BMW M4, freshly washed and glossy", caption: "Full detail, BMW M4" },
];

export function Work() {
  const [first, ...rest] = photos;
  return (
    <section id="work" className="border-t border-border py-16 md:py-24">
      <div className="container-x mx-auto max-w-6xl">
        <SectionHeading
          title="Finishes that speak for themselves."
          intro="Real cars, real driveways, photographed on the day. Every vehicle leaves with a finish we'd put our name on, because we do."
        />
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-4">
          <figure className={tile}>
            <Picture name={first.name} alt={first.alt} sizes="(min-width: 768px) 33vw, 50vw" className={media} />
            <figcaption className={cap}>{first.caption}</figcaption>
          </figure>
          <figure className={tile}>
            <BeadingVideo className={media} />
            <figcaption className={cap}>Ceramic coating, water beading</figcaption>
          </figure>
          {rest.map((p) => (
            <figure key={p.name} className={tile}>
              <Picture name={p.name} alt={p.alt} sizes="(min-width: 768px) 33vw, 50vw" className={media} />
              <figcaption className={cap}>{p.caption}</figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
