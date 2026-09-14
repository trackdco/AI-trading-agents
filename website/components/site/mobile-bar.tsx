"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { site, smsHref, telHref } from "@/lib/site";

// Phones only: Text and Call pinned to the bottom once the hero has scrolled away.
// It steps aside while the quote form or the footer's own buttons are on screen.
export function MobileBar() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [covered, setCovered] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 320);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const targets = ["#book", "#footer-cta"].map((s) => document.querySelector(s)).filter((el): el is Element => el !== null);
    // The observer reports each target as soon as it is observed, so a route change resets the state.
    const visible = new Set<Element>();
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) visible.add(e.target);
          else visible.delete(e.target);
        }
        setCovered(visible.size > 0);
      },
      { threshold: 0.1 },
    );
    targets.forEach((t) => io.observe(t));
    return () => io.disconnect();
  }, [pathname]);

  const show = scrolled && !covered;
  const btn = "inline-flex min-h-[48px] items-center justify-center rounded-lg text-[15px] font-semibold no-underline active:scale-[0.985]";

  return (
    <>
      <div aria-hidden="true" className="h-[70px] md:hidden" />
      <div
        id="phone-bar"
        inert={!show}
        className={`fixed inset-x-0 bottom-0 z-40 border-t border-border bg-background/95 transition-transform duration-300 ease-out motion-reduce:transition-none md:hidden ${
          show ? "translate-y-0" : "translate-y-full"
        }`}
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <div className="container-x grid grid-cols-2 gap-3 py-2.5">
          <a href={smsHref()} className={`${btn} bg-accent text-accent-foreground`}>
            Text us your car
          </a>
          <a href={telHref} className={`${btn} border border-border text-foreground`}>
            Call {site.phoneDisplay}
          </a>
        </div>
      </div>
    </>
  );
}
