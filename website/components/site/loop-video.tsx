"use client";

import { useEffect, useRef } from "react";
import { useSpin, hintPillClass } from "@/lib/use-spin";

type Props = {
  base: string;
  poster: string;
  label: string;
  className?: string;
  /** Set when there is no WebM next to the MP4, so the browser skips a dead request. */
  webm?: boolean;
  /** One lap around the car: people can drag it to turn the car themselves. */
  spin?: boolean;
};

// A silent loop that plays only while on screen, and never for people who asked for
// reduced motion (they get the poster). `base` is the path without extension; WebM
// is offered first with MP4 as the fallback.
export function LoopVideo({ base, poster, label, className = "", webm = true, spin = false }: Props) {
  const ref = useRef<HTMLVideoElement>(null);
  const turn = useSpin(ref, spin);
  const { clear } = turn;

  useEffect(() => {
    const v = ref.current;
    if (!v) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) v.play().catch(() => {});
        else v.pause();
      },
      { threshold: 0.25 },
    );
    io.observe(v);
    return () => {
      io.disconnect();
      clear();
    };
  }, [clear]);

  const video = (
    <video
      ref={ref}
      muted
      loop
      playsInline
      preload="metadata"
      poster={poster}
      aria-label={label}
      {...turn.handlers}
      className={`${className} ${turn.className}`}
    >
      {webm && <source src={`${base}.webm`} type="video/webm" />}
      <source src={`${base}.mp4`} type="video/mp4" />
    </video>
  );

  if (!spin) return video;

  return (
    <div className="relative">
      {video}
      {!turn.dragged && <span className={hintPillClass}>Drag to turn the car</span>}
    </div>
  );
}
