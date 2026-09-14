"use client";

import { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Picture } from "@/components/site/picture";
import { LoopVideo } from "@/components/site/loop-video";
import { site } from "@/lib/site";

gsap.registerPlugin(useGSAP, ScrollTrigger);

// Every photo is shot on a phone in portrait. On desktop the gallery pins and scrolls
// sideways, one big frame after another; on phones it's a two-up grid.
//
// A tile is a photo unless it carries `video`, in which case it's a silent loop
// with the same frame and caption. Ordinary cars are deliberately mixed in with
// the supercars: the price guide quotes on a Corolla or a RAV4, so the gallery
// should show one.
type Frame = { name: string; alt: string; title: string; sub: string; video?: { base: string; poster: string } };

const frames: Frame[] = [
  {
    name: "beading",
    alt: "Water beading and sliding off a ceramic-coated panel",
    title: "Water beading",
    sub: "Ceramic coating",
    video: { base: "/media/beading-720", poster: "/media/beading-poster.webp" },
  },
  { name: "mclaren-650s", alt: "White McLaren 650S after a full detail in a Canberra driveway", title: "McLaren 650S", sub: "Full detail" },
  {
    name: "x6",
    alt: "Black BMW X6 finished in a driveway: the flank, the boot, the red leather interior and the wheels",
    title: "BMW X6",
    sub: "Full detail",
    video: { base: "/media/x6-detail-360", poster: "/media/x6-detail-poster.webp" },
  },
  {
    name: "r8",
    alt: "Black Audi R8 detailed on a driveway: snow foam, the wash, the wheels and the finished car",
    title: "Audi R8",
    sub: "Full detail",
    video: { base: "/media/r8-detail-720", poster: "/media/r8-detail-poster.webp" },
  },
  {
    name: "m3-gtr",
    alt: "A black BMW M3 CS and a black Nissan GT-R, finished and parked together",
    title: "M3 CS and GT-R",
    sub: "Recent work",
    video: { base: "/media/m3-gtr-720", poster: "/media/m3-gtr-poster.webp" },
  },
  {
    name: "m3-comp",
    alt: "White BMW M3 Competition, snow foamed and then finished, parked beside a red Audi R8",
    title: "BMW M3 Competition",
    sub: "Full detail",
    video: { base: "/media/m3-comp-720", poster: "/media/m3-comp-poster.webp" },
  },
  { name: "huracan-driveway", alt: "Lamborghini Huracán after an exterior detail", title: "Lamborghini Huracán", sub: "Exterior detail" },
  { name: "lambo-interior", alt: "Detailed leather interior of a Lamborghini", title: "Huracán interior", sub: "Interior detail" },
  {
    // The hero at the top of this page is the same car, the same wash. Pointing at
    // the 720 cut rather than the 1080 one means a phone, which the hero also gives
    // 720, fetches nothing extra for this tile.
    name: "m4-hero",
    alt: "Washing and drying a green BMW M4 in a Canberra driveway, ending on an Imperium Detailing towel",
    title: "BMW M4 Competition",
    sub: "Full detail",
    video: { base: "/media/hero-720", poster: "/media/hero-poster.webp" },
  },
];

const tile =
  "zoom-media relative shrink-0 overflow-hidden rounded-xl bg-card aspect-[4/5] lg:h-[62vh] lg:w-auto lg:aspect-[4/5] lg:motion-reduce:h-auto lg:motion-reduce:w-full";
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
      <div
        ref={pin}
        // The horizontal scroll is the only thing that ever moves the track, and GSAP
        // gates it behind prefers-reduced-motion: no-preference. Without this, a
        // desktop visitor with Reduce Motion on saw two of the six photos and had
        // no way to reach the rest. Under Reduce Motion it becomes a plain grid.
        className="relative lg:flex lg:h-svh lg:items-center lg:overflow-hidden lg:motion-reduce:block lg:motion-reduce:h-auto lg:motion-reduce:overflow-visible"
      >
        {/* How far through the gallery you are. */}
        <div aria-hidden="true" className="absolute bottom-8 left-[clamp(1rem,4vw,3.5rem)] hidden h-px w-48 bg-border lg:block lg:motion-reduce:hidden">
          <span ref={bar} className="block h-full w-full origin-left bg-accent" style={{ transform: "scaleX(0)" }} />
        </div>
        <div
          ref={track}
          className="container-x mx-auto grid max-w-6xl grid-cols-2 gap-3 py-16 lg:mx-0 lg:flex lg:max-w-none lg:items-center lg:gap-6 lg:py-0 lg:pr-[8vw] lg:motion-reduce:mx-auto lg:motion-reduce:grid lg:motion-reduce:max-w-6xl lg:motion-reduce:grid-cols-3 lg:motion-reduce:gap-4 lg:motion-reduce:py-16 lg:motion-reduce:pr-0"
        >
          <div className="col-span-2 mb-6 lg:mb-0 lg:w-[34vw] lg:shrink-0 lg:pr-10 lg:motion-reduce:col-span-3 lg:motion-reduce:mb-6 lg:motion-reduce:w-full lg:motion-reduce:pr-0">
            <h2 id="work-heading" className="display-caps text-[clamp(2.6rem,6.4vw,5.8rem)]" data-reveal="lines">
              Finishes that speak for themselves.
            </h2>
            <p className="mt-6 max-w-[40ch] text-lg text-muted-foreground" data-reveal="up">
              Real cars, real driveways, photographed on the day. Every vehicle leaves with a finish we&apos;d put our name on, because we do.
            </p>
            <p className="mt-6 hidden text-sm text-muted-foreground lg:block lg:motion-reduce:hidden" data-reveal="up">
              Keep scrolling to move through the work.
            </p>
          </div>

          {frames.map((f) => (
            <figure key={f.name} className={`${tile} m-0`}>
              {f.video ? (
                <LoopVideo base={f.video.base} poster={f.video.poster} label={f.alt} className={media} />
              ) : (
                <Picture name={f.name} alt={f.alt} sizes="(min-width: 1024px) 50vh, 50vw" className={media} />
              )}
              <figcaption className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-background/90 to-transparent p-5 pt-14">
                <span className="display-caps block text-2xl">{f.title}</span>
                <span className="text-sm text-secondary-foreground">{f.sub}</span>
              </figcaption>
            </figure>
          ))}

          <a
            href={site.instagram}
            rel="noopener"
            className="col-span-2 flex min-h-[140px] items-center justify-center rounded-xl border border-border bg-card/40 p-6 text-center no-underline transition-colors hover:border-secondary-foreground/40 lg:h-[62vh] lg:w-[28vw] lg:shrink-0 lg:motion-reduce:col-span-3 lg:motion-reduce:h-auto lg:motion-reduce:w-full"
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
