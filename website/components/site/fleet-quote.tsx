"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import gsap from "gsap";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { site, smsHref, telHref } from "@/lib/site";
import { formatPrice } from "@/lib/services";
import { jobs, tiers, ceramicTiers, guidePrice, conditionRange, type JobId, type SizeId, type Tier } from "@/lib/pricing";
import { fleetSizes, type FleetSizeId } from "@/lib/fleet";
import { track } from "@/lib/track";

type Counts = Record<FleetSizeId, number>;
type Group = { service: JobId; tier: Tier; counts: Counts };
type Status = "idle" | "sending" | "sent" | "fallback" | "error";

const EMPTY: Counts = { sedan: 0, suv: 0, large: 0, truck: 0 };
const MAX_PER_SIZE = 15;
const MAX_GROUPS = 3;

const newGroup = (service: JobId = "exterior"): Group => ({ service, tier: 3, counts: { ...EMPTY } });

// Same chip as the price guide, so the two widgets read as one family.
const chip = (on: boolean) =>
  `flex cursor-pointer flex-col rounded-lg border px-4 py-3 text-left transition-[border-color,background-color,transform] duration-200 active:scale-[0.985] has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-ring ${
    on ? "border-accent bg-accent/10 text-foreground" : "border-border text-secondary-foreground hover:border-secondary-foreground/50"
  }`;

// Matched to the Input component beside it: same radius, same fill, same padding.
// They sit in one grid, so a different corner and a different ground read as a bug.
const selectClass =
  "flex h-11 w-full rounded-lg border border-input bg-transparent px-2.5 text-base text-foreground outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 dark:bg-input/30";

const stepBtn =
  "flex h-11 w-11 shrink-0 items-center justify-center rounded-md border border-border text-xl leading-none text-foreground transition-colors hover:border-secondary-foreground/50 aria-disabled:opacity-35";

/**
 * A truck has no published rate and the maintenance plan only has one for a
 * sedan, so both come back null and are counted as "quoted" instead of being
 * extrapolated from a price that was never set for them.
 */
function unitPrice(service: JobId, size: FleetSizeId, tier: Tier): number | null {
  if (size === "truck") return null;
  if (service === "ceramic") return ceramicTiers[size as SizeId][tier];
  return guidePrice(service, size as SizeId, tier).price;
}

const accessOptions = [
  "Yes, both",
  "It's a basement or shared car park, I'll need to check with the building",
  "Not sure, I'll find out",
  "No tap, no power, or I don't know where they are",
];
const whenOptions = ["As soon as you can fit us in", "In the next 2 to 4 weeks", "Setting up something regular", "Pricing it up for a budget"];

export function FleetQuote() {
  const [groups, setGroups] = useState<Group[]>([newGroup()]);
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const firstStep = useRef<HTMLInputElement>(null);
  const fallbackRef = useRef<HTMLDivElement>(null);

  const setGroup = (i: number, patch: Partial<Group>) => setGroups((gs) => gs.map((g, n) => (n === i ? { ...g, ...patch } : g)));
  const setCount = (i: number, size: FleetSizeId, raw: number) => {
    // A cleared input gives NaN and a pasted value can be anything, so clamp both.
    const n = Number.isFinite(raw) ? Math.min(MAX_PER_SIZE, Math.max(0, Math.floor(raw))) : 0;
    if (n > 0) setError("");
    setGroups((gs) => gs.map((g, k) => (k === i ? { ...g, counts: { ...g.counts, [size]: n } } : g)));
  };

  // --- the maths. Every figure comes out of lib/pricing.ts; none is typed here.
  const lines = groups.map((g) => {
    const meta = jobs.find((j) => j.id === g.service)!;
    const parts = fleetSizes
      .filter((s) => g.counts[s.id] > 0)
      .map((s) => ({ size: s, n: g.counts[s.id], each: unitPrice(g.service, s.id, g.tier) }));
    const total = parts.reduce((sum, p) => sum + (p.each === null ? 0 : p.each * p.n), 0);
    const quoted = parts.reduce((sum, p) => sum + (p.each === null ? p.n : 0), 0);
    const count = parts.reduce((sum, p) => sum + p.n, 0);
    return { g, meta, parts, total, quoted, count, monthly: g.service === "maintenance" };
  });

  const totalVehicles = lines.reduce((s, l) => s + l.count, 0);
  const oneOff = lines.filter((l) => !l.monthly).reduce((s, l) => s + l.total, 0);
  const monthly = lines.filter((l) => l.monthly).reduce((s, l) => s + l.total, 0);
  const quotedVehicles = lines.reduce((s, l) => s + l.quoted, 0);
  // The condition allowance only ever applies to full and interior details.
  const conditionVehicles = lines
    .filter((l) => l.g.service === "full" || l.g.service === "interior")
    .reduce((s, l) => s + l.parts.reduce((n, p) => n + (p.each === null ? 0 : p.n), 0), 0);
  const conditionCeiling = conditionVehicles * conditionRange;

  // The headline rolls to its new value, like the price guide's does.
  const [shown, setShown] = useState(0);
  const last = useRef(0);
  useEffect(() => {
    if (oneOff === last.current) return;
    const o = { v: last.current };
    last.current = oneOff;
    const instant = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const tween = gsap.to(o, { v: oneOff, duration: instant ? 0 : 0.5, ease: "expo.out", onUpdate: () => setShown(Math.round(o.v)) });
    return () => {
      tween.kill();
    };
  }, [oneOff]);

  useEffect(() => {
    if (status === "fallback" || status === "error") fallbackRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [status]);

  const fleetLines = lines
    .filter((l) => l.count > 0)
    .map((l) => {
      const bits = l.parts.map((p) => `${p.n} x ${p.size.label}${p.each === null ? " (quoted)" : ""}`).join(", ");
      const tier = l.g.service === "ceramic" ? ` (${l.g.tier}-year)` : "";
      return `${l.meta.label}${tier}: ${bits}`;
    })
    .join("\n");

  const estimateLine = [
    oneOff > 0 ? `Guide total ${formatPrice(oneOff)}` : "",
    monthly > 0 ? `${formatPrice(monthly)} a month` : "",
    quotedVehicles > 0 ? `${quotedVehicles} vehicle${quotedVehicles === 1 ? "" : "s"} quoted separately` : "",
    conditionCeiling > 0 ? `condition up to ${formatPrice(conditionCeiling)}` : "",
  ]
    .filter(Boolean)
    .join(", ");

  const compose = (data: FormData) =>
    [
      "Hi Imperium, we'd like a fleet quote.",
      `Business: ${data.get("business")}`,
      `Vehicles:\n${fleetLines}`,
      `Estimate: ${estimateLine}`,
      `Where they park: ${data.get("suburb")}`,
      `Tap and power: ${data.get("access")}`,
      `When: ${data.get("when")}`,
      `Contact: ${data.get("name")}`,
      `Phone: ${data.get("phone")}`,
      data.get("email") ? `Email: ${data.get("email")}` : "",
      data.get("notes") ? `Notes: ${data.get("notes")}` : "",
    ]
      .filter(Boolean)
      .join("\n");

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);
    if (data.get("company")) return; // honeypot
    if (totalVehicles === 0) {
      setError("Tell us how many vehicles and we'll price it.");
      firstStep.current?.focus();
      return;
    }
    setError("");
    const text = compose(data);
    setMessage(text);

    if (site.formEndpoint && site.formAccessKey) {
      setStatus("sending");
      try {
        const payload: Record<string, string> = {};
        for (const [k, v] of data.entries()) payload[k] = String(v);
        delete payload.company;
        // The chips are real radio inputs, so FormData sweeps up service_0 and
        // tier_0. Those are machine noise in an inbox; the readable version is
        // composed below from state instead.
        for (const k of Object.keys(payload)) if (/^(qty|service|tier)_\d+$/.test(k)) delete payload[k];
        payload.fleet = fleetLines;
        payload.estimate = estimateLine;
        payload.access_key = site.formAccessKey;
        payload.subject = `Fleet quote: ${totalVehicles} vehicles in ${data.get("suburb")} — ${data.get("business")}`;
        payload.from_name = `${data.get("business")} — ${site.name} website`;
        const email = String(data.get("email") ?? "");
        if (email) payload.replyto = email;

        const giveUp = new AbortController();
        const timer = window.setTimeout(() => giveUp.abort(), 12000);
        const res = await fetch(site.formEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify(payload),
          signal: giveUp.signal,
        }).finally(() => window.clearTimeout(timer));
        const body = await res.json().catch(() => null);
        if (!res.ok || (body && body.success === false)) throw new Error(body?.message ?? String(res.status));
        track("generate_lead", { method: "fleet_form", vehicles: totalVehicles, value: oneOff });
        setStatus("sent");
        form.reset();
        // The steppers are controlled, so form.reset() cannot clear them.
        setGroups([newGroup()]);
      } catch {
        setStatus("error");
      }
      return;
    }

    setStatus("fallback");
    if (/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
      track("generate_lead", { method: "sms", vehicles: totalVehicles });
      // assign() rather than setting location.href: this handler closes over the
      // derived totals, so the compiler treats it as reactive and rejects the write.
      window.location.assign(smsHref(text));
    }
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2200);
    } catch {
      /* clipboard unavailable: the text is on screen to select */
    }
  };

  if (status === "sent") {
    return (
      <div className="rounded-lg border border-border bg-card p-6" role="status">
        <h3 className="text-xl font-semibold">{"Got it. We'll come back with the numbers."}</h3>
        <p className="mt-2 text-muted-foreground">
          {site.quotePromise} You&apos;ll get the price per vehicle, how many days the fleet needs and the dates we have open. It comes from{" "}
          {site.phoneDisplay}, so save the number.
        </p>
      </div>
    );
  }

  const summary = totalVehicles === 0 ? "No vehicles yet" : `${totalVehicles} vehicle${totalVehicles === 1 ? "" : "s"}`;

  return (
    <form onSubmit={onSubmit} className="container-x mx-auto grid max-w-6xl gap-12 py-14 md:grid-cols-12 md:py-20">
      <div className="md:col-span-7">
        <h2 className="display-caps text-3xl md:text-5xl">Price your fleet, then send it with your business details</h2>
        <div className="mt-6 grid max-w-[64ch] gap-4 text-[17px] text-secondary-foreground">
          <p className="m-0">
            Add your vehicles by size and pick the service. The total adds up on screen, so nobody has to ring you to find out the number.
          </p>
          <p className="m-0">
            Four utes on an exterior detail and two sedans on a full detail is two lines. Add a second service if the fleet needs different work.
          </p>
        </div>

        {groups.map((g, i) => {
          const covered = g.service === "correction" || g.service === "ceramic";
          return (
            <div key={i} className={`mt-8 ${i > 0 ? "border-t border-border pt-8" : ""}`}>
              <div className="flex items-baseline justify-between gap-4">
                <h3 className="text-sm font-semibold text-foreground">{i === 0 ? "The service" : `Service ${i + 1}`}</h3>
                {i > 0 && (
                  <button
                    type="button"
                    onClick={() => setGroups((gs) => gs.filter((_, n) => n !== i))}
                    className="min-h-[44px] text-[15px] text-muted-foreground underline underline-offset-4 hover:text-foreground"
                  >
                    Remove this service
                  </button>
                )}
              </div>

              <fieldset className="m-0 mt-3 min-w-0 border-0 p-0">
                <legend className="sr-only">{i === 0 ? "Which service?" : `Which service for group ${i + 1}?`}</legend>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {jobs.map((j) => (
                    <label key={j.id} className={chip(g.service === j.id)}>
                      <input
                        type="radio"
                        name={`service_${i}`}
                        value={j.id}
                        checked={g.service === j.id}
                        onChange={() => setGroup(i, { service: j.id })}
                        className="sr-only"
                      />
                      <span className="text-[15px] font-semibold">{j.label}</span>
                    </label>
                  ))}
                </div>
              </fieldset>

              {g.service === "ceramic" && (
                <fieldset className="m-0 mt-4 min-w-0 border-0 p-0">
                  <legend className="mb-2 text-sm font-semibold text-foreground">Warranty</legend>
                  <div className="grid gap-2 sm:grid-cols-3">
                    {tiers.map((t) => (
                      <label key={t} className={chip(g.tier === t)}>
                        <input
                          type="radio"
                          name={`tier_${i}`}
                          value={t}
                          checked={g.tier === t}
                          onChange={() => setGroup(i, { tier: t })}
                          className="sr-only"
                        />
                        <span className="text-[15px] font-semibold">{t} years</span>
                        <span className="mt-0.5 text-xs text-muted-foreground">from {formatPrice(ceramicTiers.sedan[t])}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>
              )}

              <fieldset className="m-0 mt-5 min-w-0 border-0 p-0">
                <legend className="mb-3 text-sm font-semibold text-foreground">How many of each{i > 0 ? ` (group ${i + 1})` : ""}</legend>
                <div className="grid gap-3 sm:grid-cols-2">
                  {fleetSizes.map((s, si) => {
                    const n = g.counts[s.id];
                    const each = unitPrice(g.service, s.id, g.tier);
                    return (
                      <div key={s.id} className="flex items-center justify-between gap-3 rounded-lg border border-border px-4 py-3">
                        <span className="min-w-0">
                          <span className="block text-[15px] font-semibold text-foreground">{s.label}</span>
                          <span className="block text-xs text-muted-foreground">
                            {each === null
                              ? `${s.eg} — quoted`
                              : `${s.eg} — ${formatPrice(each)} ${g.service === "maintenance" ? "each a month" : "each"}`}
                          </span>
                        </span>
                        <span className="flex shrink-0 items-center gap-1.5">
                          <button
                            type="button"
                            className={stepBtn}
                            // aria-disabled, not disabled: a keyboard user stepping this
                            // down to zero would otherwise lose focus to <body>.
                            aria-disabled={n === 0}
                            onClick={() => n > 0 && setCount(i, s.id, n - 1)}
                            aria-label={`One fewer ${s.label}`}
                          >
                            &minus;
                          </button>
                          <input
                            ref={i === 0 && si === 0 ? firstStep : undefined}
                            type="number"
                            inputMode="numeric"
                            min={0}
                            max={MAX_PER_SIZE}
                            value={n}
                            onChange={(e) => setCount(i, s.id, e.currentTarget.valueAsNumber)}
                            aria-label={`How many ${s.label}`}
                            className="h-11 w-14 rounded-md border border-input bg-background text-center text-base tabular-nums text-foreground outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                          />
                          <button
                            type="button"
                            className={stepBtn}
                            aria-disabled={n >= MAX_PER_SIZE}
                            onClick={() => n < MAX_PER_SIZE && setCount(i, s.id, n + 1)}
                            aria-label={`One more ${s.label}`}
                          >
                            +
                          </button>
                        </span>
                      </div>
                    );
                  })}
                </div>
              </fieldset>

              {covered && (
                <p className="mt-3 max-w-[64ch] text-[15px] text-muted-foreground">
                  Needs a garage or covered space for the day, one vehicle at a time. A fleet parked outside in a yard can&apos;t be corrected or
                  coated there.
                </p>
              )}
            </div>
          );
        })}

        {groups.length < MAX_GROUPS ? (
          <button
            type="button"
            onClick={() => setGroups((gs) => [...gs, newGroup()])}
            className="mt-6 inline-flex min-h-[44px] items-center rounded-md border border-border px-4 text-[15px] font-semibold text-foreground hover:border-secondary-foreground/50"
          >
            Add a different service for the rest of the fleet
          </button>
        ) : (
          <p className="mt-6 text-[15px] text-muted-foreground">
            More than three services is a phone call. Ring{" "}
            <a href={telHref} className="text-foreground underline underline-offset-4">
              {site.phoneDisplay}
            </a>
            .
          </p>
        )}

        {error && (
          <p role="alert" className="mt-6 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-[15px]">
            {error}
          </p>
        )}

        {/* On a phone the panel is a long way down, so the running number is repeated here. */}
        <p aria-hidden="true" className="mt-8 rounded-lg border border-border bg-card px-4 py-3 text-[15px] text-secondary-foreground md:hidden">
          {summary}
          {oneOff > 0 && <span className="text-foreground"> · from {formatPrice(oneOff)}</span>}
          {monthly > 0 && <span className="text-foreground"> · {formatPrice(monthly)} a month</span>}
        </p>

        <h3 className="mt-10 text-sm font-semibold text-foreground">Your business</h3>
        <div className="mt-3 grid gap-5 sm:grid-cols-2">
          <div className="grid gap-2">
            <Label htmlFor="fq-business">Business name</Label>
            <Input id="fq-business" name="business" required placeholder="Canberra Electrical Pty Ltd" autoComplete="organization" className="h-11 text-base" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="fq-name">Your name</Label>
            <Input id="fq-name" name="name" required placeholder="Alex Smith" autoComplete="name" className="h-11 text-base" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="fq-phone">Best number to text</Label>
            <Input id="fq-phone" name="phone" type="tel" required placeholder="0400 000 000" autoComplete="tel" inputMode="tel" className="h-11 text-base" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="fq-email">Email (optional)</Label>
            <Input id="fq-email" name="email" type="email" placeholder="you@business.com.au" autoComplete="email" className="h-11 text-base" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="fq-suburb">Where will the vehicles be parked?</Label>
            <Input id="fq-suburb" name="suburb" required placeholder="Yard in Hume, or the office car park in Braddon" autoComplete="address-level2" className="h-11 text-base" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="fq-when">When do you need it done?</Label>
            <select id="fq-when" name="when" required className={selectClass} defaultValue="">
              <option value="" disabled>
                Choose one
              </option>
              {whenOptions.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </div>
          <div className="grid gap-2 sm:col-span-2">
            <Label htmlFor="fq-access">Is there an outdoor tap and a 240V power point where they park?</Label>
            <select id="fq-access" name="access" required className={selectClass} defaultValue="" aria-describedby="fq-access-note">
              <option value="" disabled>
                Choose one
              </option>
              {accessOptions.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
            <p id="fq-access-note" className="m-0 text-sm text-muted-foreground">
              Water and power are the two things we can&apos;t bring. If you&apos;re not sure, say so and send it anyway — we&apos;ll work it out with
              you before anyone books a day.
            </p>
          </div>
          <div className="grid gap-2 sm:col-span-2">
            <Label htmlFor="fq-notes">Anything else we should know? (optional)</Label>
            <p id="fq-notes-help" className="m-0 text-sm text-muted-foreground">
              Photos of the worst two interiors help more than a description. Also worth mentioning: trays, canopies, roof racks or van shelving,
              signwriting and wraps, preferred days, whether we&apos;ll need keys, and any motorbikes or trucks in the mix.
            </p>
            <Textarea id="fq-notes" name="notes" rows={3} aria-describedby="fq-notes-help" className="text-base" />
          </div>
          <div className="hidden" aria-hidden="true">
            <label htmlFor="fq-company">Company</label>
            <input id="fq-company" name="company" tabIndex={-1} autoComplete="off" />
            {/* Web3Forms runs its own trap on a field with this exact name. */}
            <input type="checkbox" name="botcheck" tabIndex={-1} autoComplete="off" />
          </div>
        </div>
      </div>

      <aside className="md:col-span-5">
        <div className="panel-glow rounded-xl border border-border bg-card p-6 md:sticky md:top-24 md:p-8">
          <p className="m-0 text-sm text-muted-foreground">
            {summary}
            {lines.filter((l) => l.count > 0).length > 1 && `, ${lines.filter((l) => l.count > 0).length} services`}
          </p>
          <p className="m-0 mt-2 flex items-baseline gap-2">
            {oneOff > 0 && <span className="text-sm text-muted-foreground">from</span>}
            <span aria-hidden="true" className="display-caps text-6xl tabular-nums md:text-7xl">
              {oneOff > 0 ? formatPrice(shown) : monthly > 0 ? `${formatPrice(monthly)}/mo` : quotedVehicles > 0 ? "Quoted" : "—"}
            </span>
            {/* The visible figure has four branches; this has to say the same
                thing, or a truck-only fleet is announced as "from $0". */}
            <span className="sr-only" aria-live="polite" aria-atomic="true">
              {summary}
              {oneOff > 0 && `, from ${formatPrice(oneOff)}`}
              {monthly > 0 && `, ${formatPrice(monthly)} a month`}
              {oneOff === 0 && monthly === 0 && quotedVehicles > 0 && ", quoted for you"}
              {totalVehicles === 0 && ", no price yet"}
            </span>
          </p>

          {lines.some((l) => l.count > 0) && (
            <ul className="m-0 mt-5 grid list-none gap-2 border-t border-border p-0 pt-5 text-[15px] text-secondary-foreground">
              {lines
                .filter((l) => l.count > 0)
                .map((l, i) => (
                  <li key={i} className="flex justify-between gap-4">
                    <span>
                      {l.meta.label}
                      {l.g.service === "ceramic" && ` (${l.g.tier}yr)`}
                      <span className="block text-xs text-muted-foreground">{l.parts.map((p) => `${p.n} × ${p.size.label}`).join(", ")}</span>
                    </span>
                    <span className="shrink-0 text-right tabular-nums text-foreground">
                      {l.total > 0 ? `${formatPrice(l.total)}${l.monthly ? "/mo" : ""}` : "quoted"}
                      {l.total > 0 && l.quoted > 0 && (
                        <span className="block text-xs font-normal text-muted-foreground">+ {l.quoted} quoted</span>
                      )}
                    </span>
                  </li>
                ))}
            </ul>
          )}

          <div className="mt-5 grid gap-2 border-t border-border pt-5 text-[15px] text-muted-foreground">
            {quotedVehicles > 0 && (
              <p className="m-0">
                {quotedVehicles} vehicle{quotedVehicles === 1 ? "" : "s"} quoted for you rather than off the list. Trucks and monthly plans on larger
                vehicles are priced for the vehicle.
              </p>
            )}
            {conditionCeiling > 0 && (
              <p className="m-0">
                Condition can add up to {formatPrice(conditionCeiling)} across the {conditionVehicles} interior and full{" "}
                {conditionVehicles === 1 ? "detail" : "details"}, agreed with you before we start. Worst case {formatPrice(oneOff + conditionCeiling)}
                {quotedVehicles > 0 ? ", plus whatever the quoted vehicles come to" : ""}.
              </p>
            )}
            <p className="m-0">This is a guide at our published per-car prices. Nothing is booked and nothing is charged until we confirm it with you.</p>
            <p className="m-0">
              No volume discount, and no business mark-up. We come back with the price per vehicle, how many days it takes and the dates we have open.
            </p>
          </div>

          <div className="mt-6 flex flex-col gap-3">
            <button
              type="submit"
              disabled={status === "sending"}
              className="lift inline-flex min-h-[52px] items-center justify-center rounded-lg bg-accent px-6 text-base font-semibold text-accent-foreground hover:bg-[#5aa6f0] disabled:opacity-60"
            >
              {status === "sending" ? "Sending…" : totalVehicles > 0 ? `Send these ${totalVehicles} vehicles` : "Send the fleet through"}
            </button>
            <a
              href={smsHref(`Hi Imperium, we'd like a fleet quote.\nBusiness: \nVehicles: \nWhere they park: `)}
              className="lift inline-flex min-h-[52px] items-center justify-center rounded-lg border border-border px-6 text-base font-semibold text-foreground no-underline hover:border-secondary-foreground/50"
            >
              Text the numbers instead
            </a>
            <a
              href={telHref}
              className="lift inline-flex min-h-[52px] items-center justify-center rounded-lg border border-border px-6 text-base font-semibold text-foreground no-underline hover:border-secondary-foreground/50"
            >
              Call {site.phoneDisplay}
            </a>
          </div>

          <p className="m-0 mt-4 text-sm text-muted-foreground">
            {site.quotePromise} By sending this you agree to our{" "}
            <a href="/privacy/" className="underline underline-offset-4">
              privacy policy
            </a>
            .
          </p>

          {status === "error" && (
            <p role="alert" className="m-0 mt-4 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-[15px]">
              {"That didn't send. Call or text "}
              {site.phoneDisplay}
              {" and we'll sort it straight away."}
            </p>
          )}

          {(status === "fallback" || status === "error") && (
            <div ref={fallbackRef} role="status" className="mt-4 rounded-lg border border-border bg-background p-5">
              <h3 className="text-lg font-semibold">Send this to us as a text</h3>
              <p className="mt-1 text-[15px] text-muted-foreground">
                {"On a phone your messages app should have opened with the details filled in. If it didn't, copy them and text "}
                {site.phoneDisplay}
                {", or email "}
                <a href={`mailto:${site.email}?subject=Fleet%20quote&body=${encodeURIComponent(message)}`} className="underline underline-offset-4">
                  {site.email}
                </a>
                .
              </p>
              <pre className="mt-3 whitespace-pre-wrap rounded-md bg-card p-3 text-sm text-secondary-foreground">{message}</pre>
              <div className="mt-3 flex flex-wrap gap-3">
                <a href={smsHref(message)} className="inline-flex min-h-[44px] items-center rounded-md bg-accent px-4 text-[15px] font-semibold text-accent-foreground no-underline">
                  Open in messages
                </a>
                <button type="button" onClick={copy} className="inline-flex min-h-[44px] items-center rounded-md border border-border px-4 text-[15px] font-semibold">
                  {copied ? "Copied" : "Copy details"}
                </button>
              </div>
            </div>
          )}
        </div>
      </aside>
    </form>
  );
}
