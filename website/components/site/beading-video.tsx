"use client";

import { useEffect, useRef } from "react";

// The hydrophobic beading loop: plays only while on screen, never with reduced motion.
export function BeadingVideo({ className = "" }: { className?: string }) {
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
    <video
      ref={ref}
      muted
      loop
      playsInline
      preload="metadata"
      poster="/media/beading-poster.jpg"
      aria-label="Water beading and sliding off a ceramic-coated panel"
      className={className}
    >
      <source src="/media/beading-720.webm" type="video/webm" />
      <source src="/media/beading-720.mp4" type="video/mp4" />
    </video>
  );
}
