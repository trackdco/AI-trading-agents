"use client";

import { useEffect, useRef } from "react";
import { usePathname, useRouter } from "next/navigation";
import gsap from "gsap";

declare global {
  interface Window {
    __ART?: string;
    __wipe?: (href: string) => void;
  }
}

const reduced = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// Between pages: the curtain from the opening rises to cover the page, the new page
// loads behind it, then it keeps going up and out. One motion, so the site feels like one place.
export function PageWipe() {
  const ref = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const pathname = usePathname();
  const covered = useRef(false);
  const busy = useRef(false);

  const lift = () => {
    const el = ref.current;
    const root = document.documentElement;
    if (!el) return;
    window.dispatchEvent(new Event("intro:lifting"));
    gsap.to(el, {
      yPercent: -100,
      duration: 0.7,
      ease: "expo.inOut",
      onComplete: () => {
        gsap.set(el, { yPercent: 100 });
        delete root.dataset.wipe;
        covered.current = false;
        busy.current = false;
      },
    });
  };

  const cover = (then: () => void) => {
    const el = ref.current;
    if (!el) return then();
    busy.current = true;
    covered.current = true;
    document.documentElement.dataset.wipe = "1";
    gsap.fromTo(el, { yPercent: 100 }, { yPercent: 0, duration: 0.45, ease: "power3.inOut", onComplete: then });
  };

  // A full page load that a wipe started: the curtain is already down (see the flags script), so lift it.
  useEffect(() => {
    const root = document.documentElement;
    if (root.dataset.wipe !== "1") return;
    if (reduced()) {
      delete root.dataset.wipe;
      return;
    }
    covered.current = true;
    let id = requestAnimationFrame(() => {
      id = requestAnimationFrame(lift);
    });
    return () => cancelAnimationFrame(id);
  }, []);

  // A client-side route change while covered: the new page is in place, lift.
  useEffect(() => {
    if (!covered.current) return;
    const id = requestAnimationFrame(lift);
    return () => cancelAnimationFrame(id);
  }, [pathname]);

  useEffect(() => {
    // Coming back through the browser's page cache, never show a stuck curtain.
    const onShow = (e: PageTransitionEvent) => {
      if (e.persisted && covered.current) lift();
    };
    window.addEventListener("pageshow", onShow);

    // The static preview routes clicks itself and hands the target here.
    window.__wipe = (href) => {
      if (reduced() || busy.current) {
        window.location.assign(href);
        return;
      }
      cover(() => {
        try {
          sessionStorage.setItem("imperium-wipe", "1");
        } catch {}
        window.location.assign(href);
      });
    };

    const onClick = (e: MouseEvent) => {
      if (typeof window.__ART === "string") return;
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const a = (e.target as Element | null)?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (!a || a.target === "_blank" || a.hasAttribute("download")) return;
      const url = new URL(a.href, window.location.href);
      if (url.origin !== window.location.origin || url.pathname === window.location.pathname) return;
      if (reduced()) return;
      e.preventDefault();
      e.stopPropagation();
      if (busy.current) return;
      cover(() => router.push(url.pathname + url.search + url.hash));
    };
    document.addEventListener("click", onClick, true);
    return () => {
      window.removeEventListener("pageshow", onShow);
      document.removeEventListener("click", onClick, true);
      delete window.__wipe;
    };
  }, [router]);

  return (
    <div ref={ref} aria-hidden="true" className="wipe pointer-events-none fixed inset-0 z-[95] bg-background">
      <span className="absolute inset-x-0 top-0 h-px bg-accent/70" />
    </div>
  );
}
