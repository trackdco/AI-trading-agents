"use client";

import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { site, smsHref, telHref, prices } from "@/lib/site";

gsap.registerPlugin(useGSAP);

type PlayState = "playing" | "ended" | "blocked" | "reduced";

export function Hero() {
  const root = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [state, setState] = useState<PlayState>("playing");
  const [reduce, setReduce] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const wide = window.matchMedia("(min-width: 900px)").matches;
    setReduce(reduced);

    // Pick the size for this screen; WebM first, MP4 as the fallback.
    const base = wide ? "/media/opening-1080" : "/media/opening-720";
    while (video.firstChild) video.removeChild(video.firstChild);
    for (const [ext, type] of [["webm", "video/webm"], ["mp4", "video/mp4"]] as const) {
      const s = document.createElement("source");
      s.src = `${base}.${ext}`;
      s.type = type;
      video.appendChild(s);
    }
    video.load();

    const onEnded = () => setState("ended");
    video.addEventListener("ended", onEnded);

    if (reduced) {
      setState("reduced");
    } else {
      video.play().then(() => setState("playing")).catch(() => setState("blocked"));
    }
    return () => video.removeEventListener("ended", onEnded);
  }, []);

  const replay = () => {
    const v = videoRef.current;
    if (!v) return;
    v.currentTime = 0;
    v.play().then(() => setState("playing")).catch(() => setState("blocked"));
  };

  // One orchestrated load sequence. gsap.from means the page is at rest without it.
  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const tl = gsap.timeline({ defaults: { ease: "expo.out" } });
      tl.from(".hero-panel", { opacity: 0, duration: 0.9, ease: "power2.out" }, 0.1)
        .from(".hero-line > span", { yPercent: 112, duration: 1.05, stagger: 0.14 }, 0.25)
        .from(".hero-sub", { opacity: 0, y: 14, duration: 0.6 }, 0.95)
        .from(".hero-cta", { opacity: 0, y: 14, duration: 0.6 }, 1.1)
        .from(".hero-note", { opacity: 0, y: 14, duration: 0.6 }, 1.2);
    },
    { scope: root },
  );

  const playLabel = state === "ended" ? "Play again" : state === "blocked" || state === "reduced" ? "Play the clip" : null;

  return (
    <section ref={root} aria-label="Imperium Detailing" className="relative">
      <div className="container-x relative mx-auto grid min-h-[calc(100svh-72px)] max-w-6xl items-end pb-8 md:min-h-[calc(84vh-72px)] md:grid-cols-12 md:items-center md:gap-10 md:py-8">
        {/* Video: a tall panel on desktop, the full background on phones. */}
        <div className="hero-panel absolute inset-0 md:relative md:col-span-5 md:col-start-8 md:order-2 md:justify-self-end md:aspect-[9/16] md:h-[min(74vh,760px)] md:w-auto">
          <video
            ref={videoRef}
            muted
            playsInline
            preload="auto"
            poster="/media/opening-poster.jpg"
            aria-label="Washing and drying a green BMW M4 in a Canberra driveway, ending on an Imperium Detailing towel"
            className="absolute inset-0 h-full w-full object-cover bg-card md:static md:rounded-md"
          >
            <source src="/media/opening-720.mp4" type="video/mp4" />
          </video>
          {playLabel && (
            <button
              type="button"
              onClick={replay}
              className="absolute right-4 top-4 z-10 text-sm text-secondary-foreground underline underline-offset-4 hover:text-foreground md:left-0 md:right-0 md:top-auto md:-bottom-10 md:mx-auto md:w-max"
            >
              {playLabel}
            </button>
          )}
          {/* Phone-only scrim so the text reads over the footage. */}
          <div
            aria-hidden="true"
            className="absolute inset-0 md:hidden"
            style={{ background: "linear-gradient(to top, rgba(5,6,8,.94) 0%, rgba(5,6,8,.62) 42%, rgba(5,6,8,.18) 72%, rgba(5,6,8,0) 100%)" }}
          />
        </div>

        <div className="relative z-10 pt-[52vh] md:col-span-7 md:col-start-1 md:order-1 md:pt-0">
          <h1 className="display">
            <span className="hero-line block overflow-hidden pb-[.08em] -mb-[.08em] text-2xl md:text-[clamp(1.9rem,3.4vw,3.4rem)] font-bold">
              <span className="inline-block will-change-transform">Not the cheapest detailer in Canberra.</span>
            </span>
            <span className="hero-line block overflow-hidden pb-[.08em] -mb-[.08em] text-[clamp(2.9rem,13.5vw,4.4rem)] md:text-[clamp(3.4rem,8.4vw,8.4rem)]">
              <span className="inline-block will-change-transform">The most careful one.</span>
            </span>
          </h1>
          <p className="hero-sub mt-5 max-w-[34rem] text-base text-muted-foreground md:mt-7 md:text-lg">
            Ceramic coating from <b className="font-medium text-foreground">${prices.ceramic}</b>. Paint correction from{" "}
            <b className="font-medium text-foreground">${prices.correction}</b>. Full detail from{" "}
            <b className="font-medium text-foreground">${prices.full}</b>. We come to your driveway or office car park, anywhere in {site.area}.
          </p>
          <div className="hero-cta mt-6 flex flex-col gap-3 sm:flex-row md:mt-7">
            <a
              href={smsHref()}
              className="inline-flex min-h-[52px] items-center justify-center rounded-lg bg-accent px-6 text-base font-semibold text-accent-foreground no-underline hover:bg-[#5aa6f0]"
            >
              Text us your car
            </a>
            <a
              href={telHref}
              className="inline-flex min-h-[52px] items-center justify-center rounded-lg border border-border px-6 text-base font-semibold text-foreground no-underline hover:border-secondary-foreground/50"
            >
              Call {site.phoneDisplay}
            </a>
          </div>
          <p className="hero-note mt-4 text-[15px] text-muted-foreground">{site.quotePromise}</p>
        </div>
      </div>
    </section>
  );
}
