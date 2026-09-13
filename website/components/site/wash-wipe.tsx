"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { hintPillClass } from "@/lib/use-spin";

const NATURAL_W = 1400;
const NATURAL_H = 806;
const ASPECT = NATURAL_W / NATURAL_H;

/** A mitt this wide on a laptop; a thumb needs more, so phones get a bigger one. */
const RADIUS_DESKTOP = 20;
const RADIUS_PHONE = 30;

/** How long the car sits wiped before the foam creeps back, and how long that takes. */
const REST_MS = 3200;
const REFOAM_MS = 1100;

// Every path below is a plain double-quoted literal on purpose. The artifact
// preview rewriter only patches those, so a URL assembled inside a template
// literal resolves to nothing when the site is served from a sub-path.
type Source = { w: number; webp: string; jpg: string };

const FOAM: Source[] = [
  { w: 480, webp: "/images/wash-foam-480.webp", jpg: "/images/wash-foam-480.jpg" },
  { w: 960, webp: "/images/wash-foam-960.webp", jpg: "/images/wash-foam-960.jpg" },
  { w: 1400, webp: "/images/wash-foam-1400.webp", jpg: "/images/wash-foam-1400.jpg" },
];

const CLEAN: Source[] = [
  { w: 480, webp: "/images/wash-clean-480.webp", jpg: "/images/wash-clean-480.jpg" },
  { w: 960, webp: "/images/wash-clean-960.webp", jpg: "/images/wash-clean-960.jpg" },
  { w: 1400, webp: "/images/wash-clean-1400.webp", jpg: "/images/wash-clean-1400.jpg" },
];

// Joining already-patched literals is safe; writing the whole set as one string
// would not be, because only the first path in it would get rewritten.
const srcSet = (list: Source[]) => list.map((s) => `${s.webp} ${s.w}w`).join(", ");
const SIZES = "(min-width: 1024px) 1024px, 100vw";

const pick = (list: Source[], cssWidth: number, dpr: number) => {
  const need = cssWidth * dpr;
  return list.find((s) => s.w >= need) ?? list[list.length - 1];
};

// WebP first, JPEG if the browser refuses it. Rejects only when both fail, which
// is what drops the whole widget back to the static picture.
function load(src: Source): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const attempt = (url: string, onFail: () => void) => {
      const img = new Image();
      img.decoding = "async";
      img.onload = () => resolve(img);
      img.onerror = onFail;
      img.src = url;
    };
    attempt(src.webp, () => attempt(src.jpg, () => reject(new Error("wash images failed"))));
  });
}

// The clean car under the canvas is an <img> with object-cover, so the foam has
// to be drawn the same way or the two layers drift apart and the wipe reveals
// the wrong part of the car.
function coverRect(iw: number, ih: number, bw: number, bh: number) {
  const scale = Math.max(bw / iw, bh / ih);
  const dw = iw * scale;
  const dh = ih * scale;
  return { dx: (bw - dw) / 2, dy: (bh - dh) / 2, dw, dh };
}

type Engine = {
  ctx: CanvasRenderingContext2D;
  /** Offscreen record of everything wiped so far, so the foam can fade back in. */
  mask: HTMLCanvasElement;
  mctx: CanvasRenderingContext2D;
  foam: HTMLImageElement;
  w: number;
  h: number;
  dpr: number;
  radius: number;
  /** How much of the mask is currently applied. 1 while wiping, ramps to 0 as foam returns. */
  strength: number;
  last: { x: number; y: number } | null;
  pointer: number | null;
  rest: number;
  raf: number;
};

// A soft round mitt rather than a hard disc, so the wiped edge feathers into the
// foam instead of looking cut out with scissors.
function stamp(ctx: CanvasRenderingContext2D, x: number, y: number, r: number) {
  const g = ctx.createRadialGradient(x, y, r * 0.45, x, y, r);
  g.addColorStop(0, "rgba(0,0,0,1)");
  g.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fill();
}

// Pointer events arrive far apart during a fast swipe. Stamping along the line
// between two samples is what stops the trail breaking up into dots.
function stroke(ctx: CanvasRenderingContext2D, from: { x: number; y: number }, to: { x: number; y: number }, r: number) {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const steps = Math.max(1, Math.ceil(Math.hypot(dx, dy) / Math.max(r / 4, 1)));
  for (let i = 1; i <= steps; i++) stamp(ctx, from.x + (dx * i) / steps, from.y + (dy * i) / steps, r);
}

// Redraw from scratch: full foam, then the mask punched out of it at `strength`.
// Only used for the fade back, because wiping stamps straight onto the canvas.
function render(e: Engine) {
  const { ctx, foam, mask, w, h } = e;
  const r = coverRect(foam.naturalWidth, foam.naturalHeight, w, h);
  ctx.globalCompositeOperation = "source-over";
  ctx.globalAlpha = 1;
  ctx.clearRect(0, 0, w, h);
  ctx.drawImage(foam, r.dx, r.dy, r.dw, r.dh);
  if (e.strength > 0) {
    ctx.globalCompositeOperation = "destination-out";
    ctx.globalAlpha = e.strength;
    ctx.drawImage(mask, 0, 0, w, h);
    ctx.globalCompositeOperation = "source-over";
    ctx.globalAlpha = 1;
  }
}

// Fold a partial strength back into the mask itself, so a wipe that interrupts a
// fade carries on from what is actually on screen rather than snapping.
function bake(e: Engine) {
  if (e.strength >= 1) return;
  e.mctx.globalCompositeOperation = "destination-in";
  e.mctx.globalAlpha = e.strength;
  e.mctx.fillStyle = "#000";
  e.mctx.fillRect(0, 0, e.mask.width, e.mask.height);
  e.mctx.globalCompositeOperation = "source-over";
  e.mctx.globalAlpha = 1;
  e.strength = 1;
}

export function WashWipe({ live = true, reduced = false }: { live?: boolean; reduced?: boolean }) {
  const hostRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const cursorRef = useRef<HTMLSpanElement>(null);
  const engineRef = useRef<Engine | null>(null);

  const [near, setNear] = useState(false);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const [touched, setTouched] = useState(false);
  const [peek, setPeek] = useState(false);

  const canvasMode = near && !reduced && !failed;

  const stopTimers = useCallback(() => {
    const e = engineRef.current;
    if (!e) return;
    window.clearTimeout(e.rest);
    cancelAnimationFrame(e.raf);
  }, []);

  // Nothing is built until the section is close to the viewport.
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setNear(true);
          io.disconnect();
        }
      },
      { rootMargin: "200px" },
    );
    io.observe(host);
    return () => io.disconnect();
  }, []);

  // Build the canvas once, and tear it down if the widget ever unmounts.
  useEffect(() => {
    if (!canvasMode) return;
    const host = hostRef.current;
    const canvas = canvasRef.current;
    if (!host || !canvas) return;

    let alive = true;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const cssWidth = host.clientWidth || NATURAL_W;

    load(pick(FOAM, cssWidth, dpr))
      .then((foam) => {
        if (!alive) return;
        const ctx = canvas.getContext("2d");
        const mask = document.createElement("canvas");
        const mctx = mask.getContext("2d");
        if (!ctx || !mctx) throw new Error("no 2d context");

        const w = host.clientWidth;
        const h = host.clientHeight || Math.round(w / ASPECT);
        canvas.width = mask.width = Math.round(w * dpr);
        canvas.height = mask.height = Math.round(h * dpr);
        // Draw in CSS pixels and let the backing store stay at device resolution,
        // which is what keeps the mitt crisp on a retina screen.
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        mctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        const e: Engine = {
          ctx,
          mask,
          mctx,
          foam,
          w,
          h,
          dpr,
          radius: window.innerWidth < 640 ? RADIUS_PHONE : RADIUS_DESKTOP,
          strength: 1,
          last: null,
          pointer: null,
          rest: 0,
          raf: 0,
        };
        engineRef.current = e;
        render(e);
        setReady(true);
      })
      .catch(() => alive && setFailed(true));

    return () => {
      alive = false;
      stopTimers();
      engineRef.current = null;
    };
  }, [canvasMode, stopTimers]);

  // Re-measure on resize: the backing store has to follow the box or everything
  // stretches. Whatever was wiped is dropped, so the car comes back foamed.
  useEffect(() => {
    if (!ready) return;
    const host = hostRef.current;
    const canvas = canvasRef.current;
    if (!host || !canvas) return;

    const ro = new ResizeObserver(() => {
      const e = engineRef.current;
      if (!e || (host.clientWidth === e.w && host.clientHeight === e.h)) return;
      stopTimers();
      e.w = host.clientWidth;
      e.h = host.clientHeight || Math.round(e.w / ASPECT);
      e.radius = window.innerWidth < 640 ? RADIUS_PHONE : RADIUS_DESKTOP;
      canvas.width = e.mask.width = Math.round(e.w * e.dpr);
      canvas.height = e.mask.height = Math.round(e.h * e.dpr);
      e.ctx.setTransform(e.dpr, 0, 0, e.dpr, 0, 0);
      e.mctx.setTransform(e.dpr, 0, 0, e.dpr, 0, 0);
      e.strength = 1;
      e.last = null;
      render(e);
    });
    ro.observe(host);
    return () => ro.disconnect();
  }, [ready, stopTimers]);

  // Leaving the step re-foams the car, so the next person who opens it starts fresh.
  useEffect(() => {
    const e = engineRef.current;
    if (!ready || !e || live) return;
    stopTimers();
    e.mctx.clearRect(0, 0, e.mask.width, e.mask.height);
    e.strength = 1;
    e.last = null;
    e.pointer = null;
    render(e);
  }, [live, ready, stopTimers]);

  const refoam = useCallback(() => {
    const e = engineRef.current;
    if (!e) return;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / REFOAM_MS);
      // Ease out, so the foam floods back quickly then settles.
      e.strength = 1 - (1 - Math.pow(1 - t, 3));
      render(e);
      if (t < 1) e.raf = requestAnimationFrame(tick);
      else {
        e.mctx.clearRect(0, 0, e.mask.width, e.mask.height);
        e.strength = 1;
      }
    };
    e.raf = requestAnimationFrame(tick);
  }, []);

  const restart = useCallback(() => {
    const e = engineRef.current;
    if (!e) return;
    window.clearTimeout(e.rest);
    e.rest = window.setTimeout(refoam, REST_MS);
  }, [refoam]);

  const point = (e: React.PointerEvent<HTMLDivElement>) => {
    const box = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
    return { x: e.clientX - box.left, y: e.clientY - box.top };
  };

  const moveCursor = (x: number, y: number) => {
    const c = cursorRef.current;
    if (c) c.style.transform = `translate3d(${x}px, ${y}px, 0) translate(-50%, -50%)`;
  };

  const onPointerDown = (ev: React.PointerEvent<HTMLDivElement>) => {
    const e = engineRef.current;
    if (!e) return;
    window.clearTimeout(e.rest);
    cancelAnimationFrame(e.raf);
    bake(e);
    e.pointer = ev.pointerId;
    e.last = point(ev);
    // Capture can be refused if the pointer is already gone; the wipe still works.
    try {
      ev.currentTarget.setPointerCapture(ev.pointerId);
    } catch {}
    setTouched(true);
    // A tap with no drag should still take some foam off.
    e.ctx.globalCompositeOperation = "destination-out";
    stamp(e.ctx, e.last.x, e.last.y, e.radius);
    e.ctx.globalCompositeOperation = "source-over";
    e.mctx.globalCompositeOperation = "source-over";
    stamp(e.mctx, e.last.x, e.last.y, e.radius);
  };

  const onPointerMove = (ev: React.PointerEvent<HTMLDivElement>) => {
    const e = engineRef.current;
    if (!e) return;
    const p = point(ev);
    moveCursor(p.x, p.y);
    if (e.pointer !== ev.pointerId || !e.last) return;
    // Wipe the visible canvas directly and mirror it into the mask. Redrawing the
    // whole frame on every move would be the slow way to do the same thing.
    e.ctx.globalCompositeOperation = "destination-out";
    stroke(e.ctx, e.last, p, e.radius);
    e.ctx.globalCompositeOperation = "source-over";
    stroke(e.mctx, e.last, p, e.radius);
    e.last = p;
  };

  const onPointerUp = (ev: React.PointerEvent<HTMLDivElement>) => {
    const e = engineRef.current;
    if (!e || e.pointer !== ev.pointerId) return;
    e.pointer = null;
    e.last = null;
    if (ev.currentTarget.hasPointerCapture?.(ev.pointerId)) ev.currentTarget.releasePointerCapture(ev.pointerId);
    restart();
  };

  // Decorative through and through: the paragraph under the panel carries the
  // message, so none of this is announced or reachable by keyboard.
  return (
    <div
      ref={hostRef}
      aria-hidden="true"
      className="absolute inset-0 overflow-hidden bg-[#0a0e14]"
      style={{ aspectRatio: `${NATURAL_W} / ${NATURAL_H}` }}
    >
      <img
        src={CLEAN[2].webp}
        srcSet={srcSet(CLEAN)}
        sizes={SIZES}
        width={NATURAL_W}
        height={NATURAL_H}
        alt=""
        loading="lazy"
        decoding="async"
        className="absolute inset-0 h-full w-full object-cover"
      />

      {/* Static fallback: reduced motion, or a canvas that never came up. */}
      {!canvasMode && (
        <img
          src={FOAM[2].webp}
          srcSet={srcSet(FOAM)}
          sizes={SIZES}
          width={NATURAL_W}
          height={NATURAL_H}
          alt=""
          loading="lazy"
          decoding="async"
          onPointerDown={() => setPeek(true)}
          onPointerUp={() => setPeek(false)}
          onPointerCancel={() => setPeek(false)}
          onMouseEnter={() => setPeek(true)}
          onMouseLeave={() => setPeek(false)}
          className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-500 motion-reduce:transition-none ${
            peek ? "opacity-0" : "opacity-100"
          }`}
        />
      )}

      {canvasMode && (
        <div
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
          onPointerLeave={() => moveCursor(-999, -999)}
          // pan-y hands vertical swipes back to the page, so the widget never
          // swallows a scroll that started on top of it.
          className="absolute inset-0 touch-pan-y [@media(pointer:fine)]:cursor-none"
        >
          <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />
          <span
            ref={cursorRef}
            className="pointer-events-none absolute left-0 top-0 hidden h-10 w-10 rounded-full border border-accent/70 bg-white/15 [@media(pointer:fine)]:block"
          />
        </div>
      )}

      {canvasMode && ready && !touched && <span className={hintPillClass}>Drag to wash the car</span>}
    </div>
  );
}
