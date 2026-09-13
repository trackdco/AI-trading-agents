"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { detailSteps, type DetailStep, type StepId } from "@/lib/detail-steps";
import { SectionHeading } from "@/components/site/section-heading";
import { useSpin, hintPillClass } from "@/lib/use-spin";
import { WashWipe } from "@/components/site/wash-wipe";

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

// One step's media. Only mounted once its button has been used, so nothing loads
// for a step nobody opened. The poster sits under the video at all times, which
// covers a slow load, a failed load, and reduced motion with the same markup.
function StepMedia({ step, active, reduced }: { step: DetailStep; active: boolean; reduced: boolean }) {
  const ref = useRef<HTMLVideoElement>(null);
  const [broken, setBroken] = useState(false);

  const spinnable = Boolean(step.spin && step.video && !broken && !reduced);
  const spin = useSpin(ref, spinnable);
  const { clear } = spin;

  useEffect(() => {
    const v = ref.current;
    if (!v || reduced) return;
    if (active) void v.play().catch(() => {});
    else v.pause();
    return clear;
  }, [active, reduced, clear]);

  return (
    <div
      aria-hidden={!active}
      // The steps are stacked, so the ones behind have to stop taking pointers or
      // whichever was opened last would swallow every drag meant for the front one.
      className={`absolute inset-0 transition-opacity duration-[250ms] ease-out motion-reduce:transition-none ${
        active ? "opacity-100" : "pointer-events-none opacity-0"
      }`}
    >
      {step.widget === "wash" ? (
        <WashWipe live={active} reduced={reduced} />
      ) : (
        <img src={step.poster} alt="" loading="lazy" decoding="async" className="absolute inset-0 h-full w-full object-cover" />
      )}
      {step.video && !broken && !reduced && (
        <video
          ref={ref}
          muted
          loop
          playsInline
          preload="metadata"
          poster={step.poster}
          aria-label={step.alt}
          onError={() => setBroken(true)}
          {...spin.handlers}
          className={`absolute inset-0 h-full w-full object-cover ${spin.className}`}
        >
          <source src={step.video} type="video/mp4" />
        </video>
      )}
      {spinnable && !spin.dragged && <span className={hintPillClass}>Drag to turn the car</span>}
      {!step.video && !step.widget && (
        <span className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full border border-border bg-background/80 px-4 py-2 text-sm text-muted-foreground backdrop-blur">
          Footage coming soon
        </span>
      )}
    </div>
  );
}

export function DetailSteps() {
  const [active, setActive] = useState<StepId>(detailSteps[0].id);
  // A step's media is created the first time it is opened, and kept from then on.
  const [opened, setOpened] = useState<StepId[]>([detailSteps[0].id]);
  const [reduced, setReduced] = useState(false);

  const railRef = useRef<HTMLDivElement>(null);
  const [pill, setPill] = useState<{ left: number; width: number } | null>(null);

  const step = detailSteps.find((s) => s.id === active)!;

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  const open = useCallback((id: StepId) => {
    setActive(id);
    setOpened((prev) => (prev.includes(id) ? prev : [...prev, id]));
  }, []);

  // The sliding marker behind the buttons, measured so it holds at any text size.
  const movePill = useCallback(() => {
    const btn = railRef.current?.querySelector<HTMLButtonElement>(`[data-step="${active}"]`);
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

  const onKeyDown = (e: React.KeyboardEvent) => {
    const i = detailSteps.findIndex((s) => s.id === active);
    let next = -1;
    if (e.key === "ArrowRight") next = (i + 1) % detailSteps.length;
    else if (e.key === "ArrowLeft") next = (i - 1 + detailSteps.length) % detailSteps.length;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = detailSteps.length - 1;
    if (next < 0) return;
    e.preventDefault();
    open(detailSteps[next].id);
    railRef.current?.querySelector<HTMLButtonElement>(`[data-step="${detailSteps[next].id}"]`)?.focus();
  };

  return (
    <section id="in-a-detail" className="border-t border-border py-20 md:py-28">
      <div className="container-x mx-auto max-w-6xl">
        <SectionHeading
          title="What's included in a detail."
          intro="Five stages, in the order they happen. Pick one to see it on the car. Most of it is invisible by the time you get the keys back, which is exactly why people think a detail is just a wash."
        />
      </div>

      {/* Buttons: one row on a laptop, a scrolling strip on a phone. Never five stacked blocks. */}
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
                id={`step-tab-${s.id}`}
                data-step={s.id}
                aria-selected={on}
                aria-controls="step-panel"
                tabIndex={on ? 0 : -1}
                onClick={() => open(s.id)}
                className={`relative z-10 flex min-h-[52px] flex-1 shrink-0 snap-start items-center justify-center gap-2.5 whitespace-nowrap rounded-full px-4 text-[15px] font-semibold transition-colors duration-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring sm:px-5 ${
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

      {/* The stage. Its 16:9 box is reserved up front, so the page never jumps while it loads. */}
      <div className="container-x mx-auto mt-6 max-w-5xl md:mt-8">
        <div
          id="step-panel"
          role="tabpanel"
          aria-labelledby={`step-tab-${active}`}
          className="relative aspect-video w-full overflow-hidden rounded-2xl border border-border bg-[#0a0e14]"
        >
          {detailSteps
            .filter((s) => opened.includes(s.id))
            .map((s) => (
              <StepMedia key={s.id} step={s} active={s.id === active} reduced={reduced} />
            ))}
        </div>

        <p key={step.id} className="price-in mt-5 max-w-[70ch] text-[17px] text-secondary-foreground">
          <b className="font-semibold text-foreground">{step.label}.</b> {step.short}
        </p>
      </div>
    </section>
  );
}
