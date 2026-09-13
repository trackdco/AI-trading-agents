"use client";

import { useCallback, useRef, useState } from "react";

/**
 * Turns a one-lap orbit clip into a turntable: dragging across the full width of
 * the video scrubs one full lap, so the car follows the finger. Let go and it
 * holds where you left it for a beat, then carries on turning by itself.
 *
 * Encode orbit clips with dense keyframes or the scrub feels sticky:
 * -g 15 -keyint_min 15 -sc_threshold 0
 */
export function useSpin(ref: React.RefObject<HTMLVideoElement | null>, enabled: boolean) {
  const [dragged, setDragged] = useState(false);
  const drag = useRef<{ id: number; x: number; from: number } | null>(null);
  const resume = useRef(0);

  const onPointerDown = (e: React.PointerEvent<HTMLVideoElement>) => {
    const v = ref.current;
    if (!enabled || !v || !Number.isFinite(v.duration)) return;
    window.clearTimeout(resume.current);
    v.pause();
    drag.current = { id: e.pointerId, x: e.clientX, from: v.currentTime };
    // Capture can be refused if the pointer is already gone; the drag still works.
    try {
      v.setPointerCapture(e.pointerId);
    } catch {}
    setDragged(true);
  };

  const onPointerMove = (e: React.PointerEvent<HTMLVideoElement>) => {
    const v = ref.current;
    const d = drag.current;
    if (!v || !d || d.id !== e.pointerId) return;
    const width = v.clientWidth || 1;
    const turns = (d.x - e.clientX) / width;
    const t = (d.from + turns * v.duration) % v.duration;
    v.currentTime = t < 0 ? t + v.duration : t;
  };

  const onPointerUp = (e: React.PointerEvent<HTMLVideoElement>) => {
    const v = ref.current;
    if (!v || drag.current?.id !== e.pointerId) return;
    drag.current = null;
    if (v.hasPointerCapture(e.pointerId)) v.releasePointerCapture(e.pointerId);
    resume.current = window.setTimeout(() => void v.play().catch(() => {}), 1400);
  };

  // Stable, because callers put it in an effect's dependency list: a fresh
  // identity every render would re-run that effect mid-drag and restart the clip.
  const clear = useCallback(() => window.clearTimeout(resume.current), []);

  return {
    dragged,
    clear,
    /** Spread onto the <video>. No-ops entirely when `enabled` is false. */
    handlers: enabled
      ? { onPointerDown, onPointerMove, onPointerUp, onPointerCancel: onPointerUp }
      : {},
    className: enabled ? "cursor-grab touch-pan-y active:cursor-grabbing" : "",
  };
}

/** The nudge that tells people the car can be turned. Hidden once they've tried it. */
export const spinHintClass =
  "pointer-events-none absolute right-4 top-4 rounded-full border border-border bg-background/80 px-4 py-2 text-sm text-muted-foreground backdrop-blur";
