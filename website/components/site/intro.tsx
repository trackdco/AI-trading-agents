"use client";

import { useEffect, useRef, useState } from "react";
import gsap from "gsap";

// The opening curtain: mark, a rule that draws, then the whole thing lifts to reveal the hero.
// Runs once per tab (sessionStorage); repeat visits skip straight to the page.
export function Intro() {
  const ref = useRef<HTMLDivElement>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    const el = ref.current;
    const root = document.documentElement;
    const finish = () => {
      root.dataset.intro = "done";
      try {
        sessionStorage.setItem("imperium-intro", "1");
      } catch {}
      setDone(true);
      window.dispatchEvent(new Event("intro:done"));
    };
    const skip = root.dataset.intro === "done" || window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (skip || !el) {
      finish();
      return;
    }
    // The hero starts revealing the moment the curtain begins to lift, so nothing waits.
    const tl = gsap.timeline({ onComplete: finish });
    tl.fromTo(".intro-mark", { opacity: 0, scale: 0.96, y: 6 }, { opacity: 1, scale: 1, y: 0, duration: 0.5, ease: "expo.out" }, 0.1)
      .fromTo(".intro-rule", { scaleX: 0 }, { scaleX: 1, duration: 0.6, ease: "power3.inOut" }, 0.25)
      .to(".intro-mark", { opacity: 0, y: -8, duration: 0.25, ease: "power2.in" }, 0.95)
      .add(() => window.dispatchEvent(new Event("intro:lifting")), 1.05)
      .to(el, { yPercent: -100, duration: 0.8, ease: "expo.inOut" }, 1.05);
    return () => {
      tl.kill();
    };
  }, []);

  if (done) return null;
  return (
    <div ref={ref} aria-hidden="true" className="intro fixed inset-0 z-[100] flex items-center justify-center bg-background">
      <div className="intro-mark flex flex-col items-center gap-6 opacity-0">
        <img src="/brand/logo-mark-192.png" width={118} height={72} alt="" className="h-16 w-auto md:h-20" />
        <span className="intro-rule block h-px w-44 origin-left bg-accent/80" />
      </div>
    </div>
  );
}
