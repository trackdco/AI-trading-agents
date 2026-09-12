"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import gsap from "gsap";
import { site, smsHref, telHref } from "@/lib/site";
import { formatPrice } from "@/lib/services";
import { sizes, jobs, ceramicTiers, guidePrice, type JobId, type SizeId, type Tier } from "@/lib/pricing";
import { SectionHeading } from "@/components/site/section-heading";

const chip = (on: boolean) =>
  `flex cursor-pointer flex-col rounded-lg border px-4 py-3 text-left transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-ring ${
    on ? "border-accent bg-accent/10 text-foreground" : "border-border text-secondary-foreground hover:border-secondary-foreground/50"
  }`;

// Pick the car and the job, get the real from-price, take it to a text message.
export function PriceGuide({ title = "Your price in ten seconds." }: { title?: string }) {
  const [size, setSize] = useState<SizeId>("sedan");
  const [job, setJob] = useState<JobId>("full");
  const [tier, setTier] = useState<Tier>(3);

  const guide = guidePrice(job, size, tier);
  const jobMeta = jobs.find((j) => j.id === job)!;
  const sizeMeta = sizes.find((s) => s.id === size)!;

  // The number rolls to its new value instead of snapping (or snaps, for reduced motion).
  const [display, setDisplay] = useState(guide.price ?? 0);
  const last = useRef(guide.price ?? 0);
  useEffect(() => {
    const target = guide.price;
    if (target === null || target === last.current) return;
    const o = { v: last.current };
    last.current = target;
    const instant = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const tween = gsap.to(o, { v: target, duration: instant ? 0 : 0.5, ease: "expo.out", onUpdate: () => setDisplay(Math.round(o.v)) });
    return () => {
      tween.kill();
    };
  }, [guide.price]);

  const label = jobMeta.label.toLowerCase();
  const sms =
    guide.price === null
      ? smsHref(`Hi Imperium, I'd like a quote for a ${label} on my ${sizeMeta.label.toLowerCase()}.\nCar: \nSuburb: `)
      : smsHref(`Hi Imperium, I'd like to lock in a ${label} for my ${sizeMeta.label.toLowerCase()}. Guide price ${formatPrice(guide.price)}${guide.suffix}.\nCar: \nSuburb: `);

  return (
    <section id="price-guide" className="border-t border-border py-20 md:py-28">
      <div className="container-x mx-auto max-w-6xl">
        <SectionHeading title={title} intro="Pick the car and the job. That's the number, not a hook to get you on the phone." />
        <div className="grid gap-8 md:grid-cols-12 md:gap-12">
          <div className="grid gap-8 md:col-span-7">
            <fieldset className="m-0 min-w-0 border-0 p-0">
              <legend className="mb-3 text-sm font-semibold text-foreground">Your car</legend>
              <div className="grid gap-2 sm:grid-cols-3">
                {sizes.map((s) => (
                  <label key={s.id} className={chip(size === s.id)}>
                    <input type="radio" name="pg-size" value={s.id} checked={size === s.id} onChange={() => setSize(s.id)} className="sr-only" />
                    <span className="text-[15px] font-semibold">{s.label}</span>
                    <span className="mt-0.5 text-xs text-muted-foreground">{s.eg}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <fieldset className="m-0 min-w-0 border-0 p-0">
              <legend className="mb-3 text-sm font-semibold text-foreground">The job</legend>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {jobs.map((j) => (
                  <label key={j.id} className={chip(job === j.id)}>
                    <input type="radio" name="pg-job" value={j.id} checked={job === j.id} onChange={() => setJob(j.id)} className="sr-only" />
                    <span className="text-[15px] font-semibold">{j.label}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            {job === "ceramic" && (
              <fieldset className="m-0 min-w-0 border-0 p-0">
                <legend className="mb-3 text-sm font-semibold text-foreground">Warranty</legend>
                <div className="grid gap-2 sm:grid-cols-3">
                  {ceramicTiers.map((t) => (
                    <label key={t.years} className={chip(tier === t.years)}>
                      <input type="radio" name="pg-tier" value={t.years} checked={tier === t.years} onChange={() => setTier(t.years)} className="sr-only" />
                      <span className="text-[15px] font-semibold">{t.years} years</span>
                    </label>
                  ))}
                </div>
              </fieldset>
            )}
          </div>

          <div className="md:col-span-5">
            <div className="panel-glow rounded-xl border border-border bg-card p-6 md:sticky md:top-24 md:p-8">
              <p className="m-0 text-sm text-muted-foreground">
                {jobMeta.label}, {sizeMeta.label.toLowerCase()}
              </p>
              {guide.price === null ? (
                <p className="display-caps m-0 mt-2 text-4xl md:text-5xl">Quoted for your car</p>
              ) : (
                <p className="m-0 mt-2 flex items-baseline gap-2">
                  <span className="text-sm text-muted-foreground">from</span>
                  <span aria-hidden="true" className="display-caps text-6xl tabular-nums md:text-7xl">
                    {formatPrice(display)}
                  </span>
                  {guide.suffix && <span className="text-lg text-muted-foreground">{guide.suffix.trim()}</span>}
                  <span className="sr-only" aria-live="polite">
                    From {formatPrice(guide.price)}
                    {guide.suffix}
                  </span>
                </p>
              )}
              <p className="mt-4 text-[15px] text-secondary-foreground">{guide.why}</p>
              <p className="mt-2 text-[15px] text-muted-foreground">{jobMeta.note}</p>
              <div className="mt-6 flex flex-col gap-3">
                <a href={sms} className="inline-flex min-h-[52px] items-center justify-center rounded-lg bg-accent px-6 text-base font-semibold text-accent-foreground no-underline hover:bg-[#5aa6f0]">
                  {guide.price === null ? "Get it quoted by text" : "Lock it in by text"}
                </a>
                <a href={telHref} className="inline-flex min-h-[52px] items-center justify-center rounded-lg border border-border px-6 text-base font-semibold text-foreground no-underline hover:border-secondary-foreground/50">
                  Call {site.phoneDisplay}
                </a>
              </div>
              <p className="mt-4 text-sm text-muted-foreground">
                {site.quotePromise}{" "}
                <Link href={jobMeta.slug} className="text-foreground underline underline-offset-4">
                  What&apos;s included
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
