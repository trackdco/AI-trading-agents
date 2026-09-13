"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { detailSteps, type StepId } from "@/lib/detail-steps";
import type { CarScene } from "@/components/site/car-scene";
import { SectionHeading } from "@/components/site/section-heading";

const icons: Record<StepId, React.ReactNode> = {
  foam: (
    <>
      <circle cx="8.5" cy="8.5" r="3.3" />
      <circle cx="15.8" cy="6.9" r="2.1" />
      <circle cx="14.2" cy="14.6" r="4.2" />
    </>
  ),
  wash: (
    <>
      <path d="M4.5 8.5h9a3 3 0 0 1 3 3v1a3 3 0 0 1-3 3h-9a1.5 1.5 0 0 1-1.5-1.5v-4A1.5 1.5 0 0 1 4.5 8.5Z" />
      <path d="M19 9.5c1.3 1.4 1.3 4.6 0 6" />
    </>
  ),
  clay: (
    <>
      <rect x="4.5" y="5.5" width="15" height="6.4" rx="2.6" />
      <circle cx="8" cy="17" r="1" />
      <circle cx="12.4" cy="18.4" r="1" />
      <circle cx="16.6" cy="16.4" r="1" />
    </>
  ),
  iron: (
    <>
      <path d="M12 2.6c3.3 4.1 5 6.7 5 8.9a5 5 0 0 1-10 0c0-2.2 1.7-4.8 5-8.9Z" />
      <path d="M8.4 18.8v2.6M12 19.6v2M15.6 18.8v2.6" />
    </>
  ),
  coat: (
    <>
      <path d="M12 2.8 19 5.4v5.1c0 4.4-2.9 8-7 9.1-4.1-1.1-7-4.7-7-9.1V5.4l7-2.6Z" />
      <circle cx="12" cy="10.4" r="2.2" />
    </>
  ),
};

export function DetailSteps() {
  const [active, setActive] = useState<StepId>("foam");
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const [hinted, setHinted] = useState(false);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const railRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<CarScene | null>(null);
  const [pill, setPill] = useState<{ left: number; width: number } | null>(null);

  const step = detailSteps.find((s) => s.id === active)!;

  // The sliding pill behind the buttons: measured, so it works at any text size.
  const movePill = useCallback(() => {
    const rail = railRef.current;
    if (!rail) return;
    const btn = rail.querySelector<HTMLButtonElement>(`[data-step="${active}"]`);
    if (!btn) return;
    setPill({ left: btn.offsetLeft, width: btn.offsetWidth });
    btn.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "smooth" });
  }, [active]);

  useEffect(() => {
    movePill();
    const ro = new ResizeObserver(movePill);
    if (railRef.current) ro.observe(railRef.current);
    return () => ro.disconnect();
  }, [movePill]);

  // three.js is a big download, so it only starts once this section is nearly on
  // screen, and the loop only runs while it's actually in view.
  useEffect(() => {
    const stage = stageRef.current;
    const canvas = canvasRef.current;
    if (!stage || !canvas) return;

    let cancelled = false;
    let started = false;

    const start = async () => {
      started = true;
      try {
        const probe = document.createElement("canvas").getContext("webgl2") ?? document.createElement("canvas").getContext("webgl");
        if (!probe) throw new Error("no webgl");
        const { createCarScene } = await import("@/components/site/car-scene");
        if (cancelled) return;
        sceneRef.current = createCarScene(canvas, {
          reduced: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
          lowPower: window.matchMedia("(max-width: 767px)").matches,
        });
        sceneRef.current.setStep(active);
        setReady(true);
      } catch {
        if (!cancelled) setFailed(true);
      }
    };

    const io = new IntersectionObserver(
      (entries) => {
        const on = entries[0].isIntersecting;
        if (on && !started) void start();
        sceneRef.current?.setActive(on);
      },
      { rootMargin: "200px 0px" },
    );
    io.observe(stage);

    const onVisibility = () => sceneRef.current?.setActive(!document.hidden);
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      cancelled = true;
      io.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
      sceneRef.current?.dispose();
      sceneRef.current = null;
    };
    // Runs once: `active` is only read to set the opening stage.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    sceneRef.current?.setStep(active);
  }, [active]);

  const onKeyDown = (e: React.KeyboardEvent) => {
    const i = detailSteps.findIndex((s) => s.id === active);
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      e.preventDefault();
      const next = (i + (e.key === "ArrowRight" ? 1 : detailSteps.length - 1)) % detailSteps.length;
      setActive(detailSteps[next].id);
      railRef.current?.querySelector<HTMLButtonElement>(`[data-step="${detailSteps[next].id}"]`)?.focus();
    }
  };

  return (
    <section id="in-a-detail" className="border-t border-border py-20 md:py-28">
      <div className="container-x mx-auto max-w-6xl">
        <SectionHeading
          title="What a detail actually is."
          intro="Five stages, in the order they happen. Pick one and watch it play out on the paint. Most of this is invisible by the time you see the car, which is exactly why people think a detail is just a wash."
        />
      </div>

      {/* The toggle rail. Scrolls sideways on a phone, all five fit on a laptop. */}
      <div className="container-x mx-auto max-w-5xl">
        <div
          ref={railRef}
          role="tablist"
          aria-label="Stages of a detail"
          onKeyDown={onKeyDown}
          className="relative flex snap-x snap-mandatory gap-1 overflow-x-auto rounded-full border border-border bg-card/60 p-1.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        >
          {pill && (
            <span
              aria-hidden="true"
              className="pointer-events-none absolute inset-y-1.5 rounded-full bg-accent/15 ring-1 ring-accent/50 transition-[left,width] duration-500 ease-[cubic-bezier(0.2,0.7,0.2,1)] motion-reduce:transition-none"
              style={{ left: pill.left, width: pill.width }}
            />
          )}
          {detailSteps.map((s) => {
            const on = s.id === active;
            return (
              <button
                key={s.id}
                type="button"
                role="tab"
                data-step={s.id}
                aria-selected={on}
                tabIndex={on ? 0 : -1}
                onClick={() => {
                  setActive(s.id);
                  setHinted(true);
                }}
                className={`relative z-10 flex min-h-[52px] flex-1 shrink-0 snap-start items-center justify-center gap-2.5 whitespace-nowrap rounded-full px-4 text-[15px] font-semibold transition-colors duration-300 sm:px-5 ${
                  on ? "text-foreground" : "text-muted-foreground hover:text-secondary-foreground"
                }`}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                  className={`shrink-0 transition-colors duration-300 ${on ? "text-accent" : ""}`}
                >
                  {icons[s.id]}
                </svg>
                {s.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* The car. */}
      <div className="container-x mx-auto mt-6 max-w-5xl md:mt-8">
        <div
          ref={stageRef}
          className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl border border-border bg-[radial-gradient(70%_70%_at_50%_28%,rgba(43,86,142,0.4),rgba(9,13,19,0.9)_72%)] sm:aspect-[16/10] md:aspect-[16/9]"
        >
          <canvas ref={canvasRef} className="absolute inset-0 h-full w-full touch-pan-y" aria-hidden="true" />

          {!ready && !failed && (
            <div className="absolute inset-0 grid place-items-center">
              <span className="text-[15px] text-muted-foreground">Warming up the lights…</span>
            </div>
          )}
          {failed && (
            <div className="absolute inset-0 grid place-items-center px-6 text-center">
              <span className="max-w-[34ch] text-[15px] text-muted-foreground">
                Your browser can&apos;t show the 3D car. The five stages are written out below.
              </span>
            </div>
          )}
          {ready && !hinted && (
            <span className="pointer-events-none absolute right-4 top-4 rounded-full border border-white/15 bg-background/70 px-4 py-2 text-sm text-muted-foreground backdrop-blur">
              Drag to spin it
            </span>
          )}
        </div>
      </div>

      {/* The words. Always here, whether the 3D loads or not. */}
      <div className="container-x mx-auto mt-8 max-w-5xl md:mt-10">
        <div key={step.id} className="price-in grid gap-6 md:grid-cols-12">
          <h3 className="display-caps text-4xl md:col-span-4 md:text-5xl">{step.title}</h3>
          <p className="m-0 max-w-[52ch] text-[17px] text-secondary-foreground md:col-span-4">{step.what}</p>
          <p className="m-0 max-w-[52ch] text-[17px] text-muted-foreground md:col-span-4">{step.why}</p>
        </div>
      </div>
    </section>
  );
}
