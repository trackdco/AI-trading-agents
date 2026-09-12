"use client";

import { usePathname } from "next/navigation";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { SplitText } from "gsap/SplitText";

gsap.registerPlugin(useGSAP, ScrollTrigger, SplitText);

// One place for every scroll-linked effect. Any element can opt in with an attribute:
//   data-reveal="lines"  headline lines slide up out of a mask
//   data-reveal="up"     fades and rises a touch
//   data-reveal="img"    wipes in from the top while the image settles from a slight zoom
//   data-parallax="-8"   drifts by that percent as you scroll past
//   data-draw            a rule that draws from left to right
export function ScrollFx() {
  const pathname = usePathname();

  useGSAP(
    () => {
      const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const reveals = gsap.utils.toArray<HTMLElement>("[data-reveal]");
      if (reduce) {
        gsap.set(reveals, { opacity: 1, visibility: "visible" });
        return;
      }

      const splits: SplitText[] = [];
      const once = (el: Element, start: string) => ({ trigger: el, start, once: true });

      reveals.forEach((el) => {
        const kind = el.dataset.reveal;
        if (kind === "lines") {
          const split = SplitText.create(el, { type: "lines", mask: "lines", linesClass: "reveal-line" });
          splits.push(split);
          gsap.set(el, { visibility: "visible" });
          gsap.from(split.lines, { yPercent: 110, duration: 1.1, ease: "expo.out", stagger: 0.08, scrollTrigger: once(el, "top 88%") });
        } else if (kind === "img") {
          gsap.set(el, { opacity: 1 });
          gsap.from(el, { clipPath: "inset(0 0 100% 0)", duration: 1.15, ease: "expo.inOut", scrollTrigger: once(el, "top 86%") });
          const media = el.querySelector("img, video");
          if (media) gsap.from(media, { scale: 1.16, duration: 1.5, ease: "expo.out", scrollTrigger: once(el, "top 86%") });
        } else {
          gsap.fromTo(el, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.85, ease: "power2.out", scrollTrigger: once(el, "top 90%") });
        }
      });

      gsap.utils.toArray<HTMLElement>("[data-parallax]").forEach((el) => {
        gsap.to(el, {
          yPercent: Number(el.dataset.parallax ?? -8),
          ease: "none",
          scrollTrigger: { trigger: el.parentElement ?? el, scrub: 0.6 },
        });
      });

      gsap.utils.toArray<HTMLElement>("[data-draw]").forEach((el) => {
        gsap.from(el, { scaleX: 0, transformOrigin: "left center", duration: 1.3, ease: "power3.inOut", scrollTrigger: once(el, "top 85%") });
      });

      document.fonts?.ready.then(() => ScrollTrigger.refresh());
      return () => splits.forEach((s) => s.revert());
    },
    { dependencies: [pathname] },
  );

  return null;
}
