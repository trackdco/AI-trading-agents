"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { nav, site, telHref } from "@/lib/site";

export function Header() {
  const [open, setOpen] = useState(false);
  const toggle = useRef<HTMLButtonElement>(null);
  // "/#work" in the menu left it open over the section it had just scrolled to.
  // usePathname() ignores the hash so the effect above never ran; the router
  // navigates by pushState so there is no hashchange and no load; and an onClick
  // prop fires on a plain anchor here but not on a next/link Link. A native
  // listener in the capture phase sees the click before any of that.
  const menu = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = menu.current;
    if (!el) return;
    const onClick = (e: MouseEvent) => {
      if ((e.target as Element | null)?.closest("a")) setOpen(false);
    };
    el.addEventListener("click", onClick, true);
    return () => el.removeEventListener("click", onClick, true);
  }, []);
  const pathname = usePathname();

  const [solid, setSolid] = useState(false);
  const [tucked, setTucked] = useState(false);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  // Escape is how anyone expects to back out of an open menu, and without it a
  // keyboard user has to tab through every link to get out of one.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      setOpen(false);
      toggle.current?.focus();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  // Clear over the hero, solid once you scroll. On phones it tucks away while you scroll
  // down and returns the moment you scroll up, so the screen is all page.
  useEffect(() => {
    let last = window.scrollY;
    const phone = window.matchMedia("(max-width: 767px)");
    const onScroll = () => {
      const y = window.scrollY;
      setSolid(y > 24);
      if (phone.matches) {
        if (y > 140 && y > last + 4) setTucked(true);
        else if (y < last - 4 || y <= 140) setTucked(false);
      } else setTucked(false);
      last = y;
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`sticky top-0 z-50 border-b transition-[background-color,border-color,backdrop-filter,transform] duration-500 motion-reduce:transition-none ${
        solid || open ? "border-border bg-background/85 backdrop-blur-md" : "border-transparent bg-transparent"
      } ${tucked && !open ? "-translate-y-full" : "translate-y-0"}`}
    >
      <a
        href="#content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:z-[60] focus:rounded-md focus:bg-accent focus:px-3 focus:py-2 focus:text-accent-foreground"
      >
        Skip to content
      </a>
      <div className="container-x mx-auto flex h-[72px] max-w-6xl items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-3 no-underline" aria-label="Imperium Detailing, home">
          <img src="/brand/logo-mark-96.webp" width={59} height={36} alt="" className="h-9 w-auto" />
          <span className="display text-xl tracking-wide text-foreground">Imperium Detailing</span>
        </Link>

        <nav aria-label="Primary" className="hidden items-center gap-7 lg:flex">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="link-slide text-[15px] text-secondary-foreground no-underline transition-colors hover:text-foreground"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-5 lg:flex">
          <a href={telHref} className="text-[15px] text-secondary-foreground no-underline hover:text-foreground">
            {site.phoneDisplay}
          </a>
          <Link
            href="/book/"
            className="lift inline-flex h-11 items-center rounded-full bg-accent px-5 text-[15px] font-semibold text-accent-foreground no-underline hover:bg-[#5aa6f0]"
          >
            Get a quote
          </Link>
        </div>

        <button
          ref={toggle}
          type="button"
          className="inline-flex h-11 w-11 items-center justify-center rounded-md border border-border text-foreground lg:hidden"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          aria-controls="mobile-menu"
          onClick={() => setOpen((v) => !v)}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            {open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
          </svg>
        </button>
      </div>

      <div ref={menu} id="mobile-menu" hidden={!open} className="border-t border-border bg-background lg:hidden">
        {/* Closing on a pathname change misses "/#work", which only moves the
            hash — so the menu stayed open over the section it had just
            scrolled to. Any tap inside the menu closes it. */}
        <nav aria-label="Mobile" className="container-x flex flex-col py-2">
          {nav.map((item) => (
            <Link key={item.href} href={item.href} className="border-b border-border py-4 text-lg text-foreground no-underline">
              {item.label}
            </Link>
          ))}
          <a href={telHref} className="border-b border-border py-4 text-lg text-foreground no-underline">
            Call {site.phoneDisplay}
          </a>
          <Link
            href="/book/"
           
            className="my-4 inline-flex min-h-[52px] items-center justify-center rounded-lg bg-accent text-base font-semibold text-accent-foreground no-underline"
          >
            Get a quote
          </Link>
        </nav>
      </div>
    </header>
  );
}
