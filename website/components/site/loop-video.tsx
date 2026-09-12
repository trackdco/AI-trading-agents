"use client";

import { useEffect, useRef } from "react";

type Props = { base: string; poster: string; label: string; className?: string };

// A silent loop that plays only while on screen, and never for people who asked for
// reduced motion (they get the poster). `base` is the path without extension; WebM
// is offered first with MP4 as the fallback.
export function LoopVideo({ base, poster, label, className = "" }: Props) {
  const ref = useRef<HTMLVideoElement>(null);

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
    return () => io.disconnect();
  }, []);

  return (
    <video ref={ref} muted loop playsInline preload="metadata" poster={poster} aria-label={label} className={className}>
      <source src={`${base}.webm`} type="video/webm" />
      <source src={`${base}.mp4`} type="video/mp4" />
    </video>
  );
}
