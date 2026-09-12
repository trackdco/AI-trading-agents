"use client";

import { usePathname } from "next/navigation";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { SplitText } from "gsap/SplitText";

gsap.registerPlugin(useGSAP, ScrollTrigger, SplitText);
ScrollTrigger.config({ ignoreMobileResize: true });

// One place for every scroll-linked effect. Any element can opt in with an attribute:
//   data-reveal="lines"  headline lines slide up out of a mask
//   data-reveal="up"     fades and rises a touch
//   data-reveal="img"    fades in while the image settles from a slight zoom
//   data-parallax="-8"   drifts by that percent as you scroll past
//   data-draw            a rule that draws from left to right
export function ScrollFx() {
  const pathname = usePathname();

  useGSAP(
    (_context, contextSafe) => {
      const reduce = window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;
      const reveals = gsap.utils.toArray<HTMLElement>("[data-reveal]");
      if (reduce) {
        gsap.set(reveals, { opacity: 1, visibility: "visible" });
        return;
      }

      const splits: SplitText[] = [];
      const once = (el: Element, start: string) => ({
        trigger: el,
        start,
        once: true,
      });

      // Splitting headlines and wiring triggers is layout work; it waits for the first idle
      // moment so the page paints and hydrates first. contextSafe keeps the tweens in this
      // hook's context, so they're reverted on the next route.
      const setup = contextSafe!(() => {
        reveals.forEach((el) => {
          const kind = el.dataset.reveal;
          if (kind === "lines") {
            const split = SplitText.create(el, {
              type: "lines",
              mask: "lines",
              linesClass: "reveal-line",
            });
            splits.push(split);
            gsap.set(el, { visibility: "visible" });
            gsap.from(split.lines, {
              yPercent: 110,
              duration: 0.9,
              ease: "expo.out",
              stagger: 0.07,
              scrollTrigger: once(el, "top 88%"),
            });
          } else if (kind === "img") {
            gsap.fromTo(
              el,
              { opacity: 0 },
              {
                opacity: 1,
                duration: 0.7,
                ease: "power2.out",
                scrollTrigger: once(el, "top 88%"),
              },
            );
            const media = el.querySelector("img, video");
            if (media)
              gsap.from(media, {
                scale: 1.06,
                duration: 1.1,
                ease: "expo.out",
                scrollTrigger: once(el, "top 88%"),
              });
          } else {
            gsap.fromTo(
              el,
              { opacity: 0, y: 14 },
              {
                opacity: 1,
                y: 0,
                duration: 0.7,
                ease: "expo.out",
                scrollTrigger: once(el, "top 92%"),
              },
            );
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
          gsap.from(el, {
            scaleX: 0,
            transformOrigin: "left center",
            duration: 1.0,
            ease: "power3.inOut",
            scrollTrigger: once(el, "top 85%"),
          });
        });

        document.fonts?.ready.then(() => ScrollTrigger.refresh());
      });

      const idle = typeof window.requestIdleCallback === "function";
      const id = idle
        ? window.requestIdleCallback(setup, { timeout: 300 })
        : window.setTimeout(setup, 60);
      return () => {
        if (idle) window.cancelIdleCallback(id);
        else window.clearTimeout(id);
        splits.forEach((s) => s.revert());
      };
    },
    { dependencies: [pathname] },
  );

  return null;
}
