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

/**
 * A phone decodes video in hardware, but only so many streams at once. The home
 * page gallery is a two-up grid on a phone, so four tiles sit on screen together,
 * and four clips decoding at once is what makes scrolling stutter.
 *
 * So every loop on the page registers here with how much of itself is showing, and
 * only the two most visible ones actually play. The rest sit on their poster frame,
 * which costs nothing. Pausing is what frees the decoder; hiding would not.
 */
const MAX_PLAYING = 2;
const onScreen = new Map<HTMLVideoElement, number>();

function arbitrate() {
  const ranked = [...onScreen.entries()].filter(([, r]) => r > 0.25).sort((a, b) => b[1] - a[1]);
  const wanted = new Set(ranked.slice(0, MAX_PLAYING).map(([el]) => el));
  for (const el of onScreen.keys()) {
    if (wanted.has(el)) {
      if (el.paused) el.play().catch(() => {});
    } else if (!el.paused) {
      el.pause();
    }
  }
}

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
    onScreen.set(v, 0);
    const io = new IntersectionObserver(
      ([entry]) => {
        onScreen.set(v, entry.intersectionRatio);
        arbitrate();
      },
      // Several steps, so the ranking knows which tile is most visible, not just
      // that it crossed one line.
      { threshold: [0, 0.25, 0.5, 0.75, 1] },
    );
    io.observe(v);
    return () => {
      io.disconnect();
      onScreen.delete(v);
      clear();
    };
  }, [clear]);

  const video = (
    <video
      ref={ref}
      muted
      loop
      playsInline
      preload="none"
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
