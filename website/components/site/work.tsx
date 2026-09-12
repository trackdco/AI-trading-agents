"use client";

import { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Picture } from "@/components/site/picture";
import { BeadingVideo } from "@/components/site/beading-video";
import { site } from "@/lib/site";

gsap.registerPlugin(useGSAP, ScrollTrigger);

// Every photo is shot on a phone in portrait. On desktop the gallery pins and scrolls
// sideways, one big frame after another; on phones it's a two-up grid.
const frames = [
  { name: "mclaren-650s", alt: "White McLaren 650S after a full detail in a Canberra driveway", title: "McLaren 650S", sub: "Full detail" },
  { name: "correction-suv", alt: "Black SUV with corrected, mirror-finish paint", title: "Nissan Patrol", sub: "Paint correction" },
  { name: "huracan-driveway", alt: "Lamborghini Huracán after an exterior detail", title: "Lamborghini Huracán", sub: "Exterior detail" },
  { name: "lambo-interior", alt: "Detailed leather interior of a Lamborghini", title: "Huracán interior", sub: "Interior detail" },
  { name: "m4-clean-front", alt: "Green BMW M4, freshly washed and glossy", title: "BMW M4 Competition", sub: "Full detail" },
];

const tile = "zoom-media relative shrink-0 overflow-hidden rounded-xl bg-card aspect-[4/5] lg:h-[62vh] lg:w-auto lg:aspect-[4/5]";
const media = "absolute inset-0 h-full w-full object-cover";

export function Work() {
  const root = useRef<HTMLElement>(null);
  const pin = useRef<HTMLDivElement>(null);
  const track = useRef<HTMLDivElement>(null);
  const bar = useRef<HTMLSpanElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(min-width: 1024px) and (prefers-reduced-motion: no-preference)", () => {
        const t = track.current;
        const p = pin.current;
        if (!t || !p) return;
        const distance = () => t.scrollWidth - window.innerWidth;
        gsap.to(t, {
          x: () => -distance(),
          ease: "none",
          scrollTrigger: {
            trigger: p,
            start: "top top",
            end: () => `+=${distance()}`,
            pin: true,
            scrub: 0.8,
            anticipatePin: 1,
            invalidateOnRefresh: true,
            onUpdate: (self) => {
              if (bar.current) bar.current.style.transform = `scaleX(${self.progress})`;
            },
          },
        });
      });
    },
    { scope: root },
  );

  return (
    <section ref={root} id="work" aria-labelledby="work-heading" className="border-t border-border">
      <div ref={pin} className="relative lg:flex lg:h-svh lg:items-center lg:overflow-hidden">
        {/* How far through the gallery you are. */}
        <div aria-hidden="true" className="absolute bottom-8 left-[clamp(1rem,4vw,3.5rem)] hidden h-px w-48 bg-border lg:block">
          <span ref={bar} className="block h-full w-full origin-left bg-accent" style={{ transform: "scaleX(0)" }} />
        </div>
        <div ref={track} className="container-x mx-auto grid max-w-6xl grid-cols-2 gap-3 py-16 lg:mx-0 lg:flex lg:max-w-none lg:items-center lg:gap-6 lg:py-0 lg:pr-[8vw]">
          <div className="col-span-2 mb-6 lg:mb-0 lg:w-[34vw] lg:shrink-0 lg:pr-10">
            <h2 id="work-heading" className="display-caps text-[clamp(2.6rem,6.4vw,5.8rem)]" data-reveal="lines">
              Finishes that speak for themselves.
            </h2>
            <p className="mt-6 max-w-[40ch] text-lg text-muted-foreground" data-reveal="up">
              Real cars, real driveways, photographed on the day. Every vehicle leaves with a finish we&apos;d put our name on, because we do.
            </p>
            <p className="mt-6 hidden text-sm text-muted-foreground lg:block" data-reveal="up">
              Keep scrolling to move through the work.
            </p>
          </div>

          <figure className={`${tile} m-0`}>
            <BeadingVideo className={media} />
            <figcaption className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-background/90 to-transparent p-5 pt-14">
              <span className="display-caps block text-2xl">Water beading</span>
              <span className="text-sm text-secondary-foreground">Ceramic coating</span>
            </figcaption>
          </figure>

          {frames.map((f) => (
            <figure key={f.name} className={`${tile} m-0`}>
              <Picture name={f.name} alt={f.alt} sizes="(min-width: 1024px) 50vh, 50vw" className={media} />
              <figcaption className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-background/90 to-transparent p-5 pt-14">
                <span className="display-caps block text-2xl">{f.title}</span>
                <span className="text-sm text-secondary-foreground">{f.sub}</span>
              </figcaption>
            </figure>
          ))}

          <a
            href={site.instagram}
            rel="noopener"
            className="col-span-2 flex min-h-[140px] items-center justify-center rounded-xl border border-border bg-card/40 p-6 text-center no-underline transition-colors hover:border-secondary-foreground/40 lg:h-[62vh] lg:w-[28vw] lg:shrink-0"
          >
            <span>
              <span className="display-caps block text-3xl text-foreground">More on Instagram</span>
              <span className="mt-2 block text-[15px] text-muted-foreground">{site.instagramHandle}</span>
            </span>
          </a>
        </div>
      </div>
    </section>
  );
}
