"use client";

import { useRef, useState } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { imageSrc, imageSrcSet } from "@/components/site/picture";

gsap.registerPlugin(useGSAP, ScrollTrigger);

type Props = { before: string; after: string; beforeAlt: string; afterAlt: string; className?: string };

// Before on the left, after on the right, a handle you drag between them. The control is a
// real range input laid over the photos, so fingers, mice and keyboards all work, and the
// handle gives one small nudge the first time it scrolls into view so people know to drag.
export function CompareSlider({ before, after, beforeAlt, afterAlt, className = "" }: Props) {
  const root = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState(50);
  const touched = useRef(false);

  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const state = { v: 50 };
      gsap.to(state, {
        v: 34,
        duration: 0.7,
        yoyo: true,
        repeat: 1,
        ease: "power2.inOut",
        scrollTrigger: { trigger: root.current, start: "top 70%", once: true },
        onUpdate: () => {
          if (!touched.current) setPos(state.v);
        },
      });
    },
    { scope: root },
  );

  return (
    <div
      ref={root}
      className={`panel-glow relative aspect-[4/5] select-none overflow-hidden rounded-xl bg-card focus-within:ring-2 focus-within:ring-ring ${className}`}
    >
      <img
        src={imageSrc(before, 960)}
        srcSet={imageSrcSet(before)}
        sizes="(min-width: 768px) 42vw, 100vw"
        alt={beforeAlt}
        draggable={false}
        className="absolute inset-0 h-full w-full object-cover"
      />
      <img
        src={imageSrc(after, 960)}
        srcSet={imageSrcSet(after)}
        sizes="(min-width: 768px) 42vw, 100vw"
        alt={afterAlt}
        draggable={false}
        className="absolute inset-0 h-full w-full object-cover"
        style={{ clipPath: `inset(0 0 0 ${pos}%)` }}
      />

      <div aria-hidden="true" className="pointer-events-none absolute inset-y-0 w-px bg-white/90" style={{ left: `${pos}%` }}>
        <span className="absolute left-1/2 top-1/2 flex h-11 w-11 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/40 bg-background/80 text-foreground shadow-lg backdrop-blur">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 6l-6 6 6 6M15 6l6 6-6 6" />
          </svg>
        </span>
      </div>
      <span aria-hidden="true" className="pointer-events-none absolute left-3 top-3 rounded-full bg-background/70 px-3 py-1 text-xs font-medium text-foreground backdrop-blur">
        Before
      </span>
      <span aria-hidden="true" className="pointer-events-none absolute right-3 top-3 rounded-full bg-background/70 px-3 py-1 text-xs font-medium text-foreground backdrop-blur">
        After
      </span>

      <input
        type="range"
        min={0}
        max={100}
        value={Math.round(pos)}
        onChange={(e) => setPos(Number(e.target.value))}
        onPointerDown={() => {
          touched.current = true;
        }}
        aria-label="Drag to compare the paint before and after correction"
        className="absolute inset-0 m-0 h-full w-full cursor-ew-resize opacity-0 [touch-action:pan-y]"
      />
    </div>
  );
}
