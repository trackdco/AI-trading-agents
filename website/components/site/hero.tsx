"use client";

import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { site, smsHref, telHref, prices } from "@/lib/site";
import { services } from "@/lib/services";
import { Marquee } from "@/components/site/marquee";

gsap.registerPlugin(useGSAP);

type PlayState = "playing" | "ended" | "blocked" | "reduced";

export function Hero() {
  const root = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [state, setState] = useState<PlayState>("playing");

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const wide = window.matchMedia("(min-width: 900px)").matches;

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
    if (reduced) setState("reduced");
    else video.play().then(() => setState("playing")).catch(() => setState("blocked"));
    return () => video.removeEventListener("ended", onEnded);
  }, []);

  const replay = () => {
    const v = videoRef.current;
    if (!v) return;
    v.currentTime = 0;
    v.play().then(() => setState("playing")).catch(() => setState("blocked"));
  };

  // The one orchestrated moment: waits for the intro curtain, then lines rise out of
  // their masks while the panel settles into place.
  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const tl = gsap.timeline({ paused: true, defaults: { ease: "expo.out" } });
      tl.from(".hero-panel", { opacity: 0, y: 40, scale: 0.97, duration: 1.3, ease: "expo.out" }, 0)
        .from(".hero-line > span", { yPercent: 110, duration: 1.15, stagger: 0.11 }, 0.15)
        .from(".hero-sub", { opacity: 0, y: 16, duration: 0.7 }, 0.85)
        .from(".hero-cta > *", { opacity: 0, y: 16, duration: 0.7, stagger: 0.08 }, 0.95)
        .from(".hero-note", { opacity: 0, duration: 0.6 }, 1.15)
        .from(".hero-strip", { opacity: 0, duration: 0.8 }, 1.2);
      if (document.documentElement.dataset.intro === "done") tl.play();
      else window.addEventListener("intro:done", () => tl.play(), { once: true });
    },
    { scope: root },
  );

  const playLabel = state === "ended" ? "Play again" : state === "blocked" || state === "reduced" ? "Play the clip" : null;
  const strip = [...services.map((s) => s.name), "Mobile across Canberra and Queanbeyan", "No call-out fee"];

  return (
    <section ref={root} aria-label="Imperium Detailing" className="relative overflow-hidden">
      {/* Full-bleed backdrop: a blurred frame of the footage, so the header floats over it. */}
      <div aria-hidden="true" className="absolute inset-x-0 -top-[72px] bottom-0 -z-10">
        <img src="/media/opening-poster.jpg" alt="" className="h-full w-full scale-125 object-cover opacity-40 blur-3xl saturate-125" />
        <div className="absolute inset-0 bg-[radial-gradient(60%_50%_at_70%_40%,rgba(31,111,196,0.22),transparent_70%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(to_bottom,rgba(5,6,8,0.55),rgba(5,6,8,0.15)_35%,rgba(5,6,8,0.6)_75%,#050608_100%)]" />
      </div>

      <div className="container-x relative mx-auto grid min-h-[calc(100svh-72px)] max-w-6xl items-end pb-10 md:min-h-[calc(92vh-72px)] md:grid-cols-12 md:items-center md:pb-0 md:pt-6">
        {/* Video: a glowing portrait panel on desktop, the full background on phones. */}
        <div className="hero-panel absolute inset-0 md:relative md:col-span-5 md:col-start-8 md:row-start-1 md:aspect-[9/16] md:h-[min(76vh,780px)] md:w-auto md:justify-self-end">
          <video
            ref={videoRef}
            muted
            playsInline
            preload="auto"
            poster="/media/opening-poster.jpg"
            aria-label="Washing and drying a green BMW M4 in a Canberra driveway, ending on an Imperium Detailing towel"
            className="panel-glow absolute inset-0 h-full w-full bg-card object-cover md:static md:rounded-xl"
          >
            <source src="/media/opening-720.mp4" type="video/mp4" />
          </video>
          {playLabel && (
            <button
              type="button"
              onClick={replay}
              className="absolute right-4 top-4 z-10 rounded-full border border-white/20 bg-background/60 px-4 py-2 text-sm text-foreground backdrop-blur hover:bg-background/80"
            >
              {playLabel}
            </button>
          )}
          <div
            aria-hidden="true"
            className="absolute inset-0 md:hidden"
            style={{ background: "linear-gradient(to top, rgba(5,6,8,.96) 0%, rgba(5,6,8,.66) 40%, rgba(5,6,8,.2) 70%, rgba(5,6,8,0) 100%)" }}
          />
        </div>

        {/* Copy: sits on top of the panel's inner edge on desktop. */}
        <div className="relative z-10 pt-[54vh] md:col-span-8 md:col-start-1 md:row-start-1 md:pt-0">
          <h1 className="display-caps text-[clamp(2.5rem,5.7vw,6.1rem)]">
            <span className="hero-line block overflow-x-visible overflow-y-clip pb-[.06em] -mb-[.06em] text-secondary-foreground">
              <span className="inline-block whitespace-nowrap will-change-transform">Not the cheapest</span>
            </span>
            <span className="hero-line block overflow-x-visible overflow-y-clip pb-[.06em] -mb-[.06em] text-secondary-foreground">
              <span className="inline-block whitespace-nowrap will-change-transform">detailer in Canberra.</span>
            </span>
            <span className="hero-line block overflow-x-visible overflow-y-clip pb-[.06em] -mb-[.06em]">
              <span className="inline-block whitespace-nowrap will-change-transform">The most careful one.</span>
            </span>
          </h1>
          <p className="hero-sub mt-6 max-w-[32rem] text-base text-secondary-foreground md:mt-8 md:text-lg">
            Ceramic coating from <b className="font-semibold text-foreground">${prices.ceramic}</b>. Paint correction from{" "}
            <b className="font-semibold text-foreground">${prices.correction}</b>. Full detail from{" "}
            <b className="font-semibold text-foreground">${prices.full}</b>. We come to your driveway or office car park, anywhere in {site.area}.
          </p>
          <div className="hero-cta mt-7 flex flex-col gap-3 sm:flex-row md:mt-8">
            <a
              href={smsHref()}
              className="inline-flex min-h-[54px] items-center justify-center rounded-full bg-accent px-7 text-base font-semibold text-accent-foreground no-underline shadow-[0_0_40px_rgba(58,143,224,0.35)] transition-[transform,box-shadow] duration-300 hover:-translate-y-0.5 hover:shadow-[0_0_60px_rgba(58,143,224,0.5)]"
            >
              Text us your car
            </a>
            <a
              href={telHref}
              className="inline-flex min-h-[54px] items-center justify-center rounded-full border border-white/20 bg-background/40 px-7 text-base font-semibold text-foreground no-underline backdrop-blur transition-colors hover:border-white/50"
            >
              Call {site.phoneDisplay}
            </a>
          </div>
          <p className="hero-note mt-4 text-[15px] text-muted-foreground">{site.quotePromise}</p>
        </div>
      </div>

      <div className="hero-strip relative border-t border-white/10 py-4">
        <Marquee items={strip} />
      </div>
    </section>
  );
}
