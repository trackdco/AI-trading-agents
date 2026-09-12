"use client";

import { useState, type FormEvent } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { site, smsHref, telHref } from "@/lib/site";

// The playbook's four qualifying questions plus contact details.
const serviceOptions = [
  "Full detail",
  "Interior detail",
  "Exterior detail",
  "Paint correction",
  "Ceramic coating",
  "Regular maintenance plan",
  "Not sure, recommend something",
];
const whenOptions = ["As soon as possible", "In the next 1 to 2 weeks", "In the next 3 to 4 weeks", "Just researching prices"];

type Status = "idle" | "sending" | "sent" | "fallback" | "error";

const selectClass =
  "flex h-11 w-full rounded-md border border-input bg-background px-3 text-base text-foreground outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50";

export function BookingForm({ compact = false }: { compact?: boolean }) {
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");

  const compose = (data: FormData) =>
    [
      "Hi Imperium, I'd like a quote.",
      `Service: ${data.get("service")}`,
      `Car: ${data.get("vehicle")}`,
      `Suburb: ${data.get("suburb")}`,
      `When: ${data.get("when")}`,
      `Name: ${data.get("name")}`,
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
    const text = compose(data);
    setMessage(text);

    if (site.formEndpoint) {
      setStatus("sending");
      try {
        const res = await fetch(site.formEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify(Object.fromEntries(data.entries())),
        });
        if (!res.ok) throw new Error(String(res.status));
        setStatus("sent");
        form.reset();
      } catch {
        setStatus("error");
      }
      return;
    }

    // No form endpoint configured yet: hand the composed message to their messaging app.
    setStatus("fallback");
    if (/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) window.location.href = smsHref(text);
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message);
    } catch {
      /* clipboard unavailable: the text is on screen to select */
    }
  };

  if (status === "sent") {
    return (
      <div className="rounded-lg border border-border bg-card p-6" role="status">
        <h3 className="text-xl font-semibold">Done. We'll text you shortly.</h3>
        <p className="mt-2 text-muted-foreground">
          {site.quotePromise} It will come from {site.phoneDisplay}, so save the number.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="grid gap-5" noValidate={false}>
      <div className={`grid gap-5 ${compact ? "" : "sm:grid-cols-2"}`}>
        <div className="grid gap-2">
          <Label htmlFor="bf-service">Which service?</Label>
          <select id="bf-service" name="service" required className={selectClass} defaultValue="">
            <option value="" disabled>
              Choose one
            </option>
            {serviceOptions.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        </div>
        <div className="grid gap-2">
          <Label htmlFor="bf-when">When do you want it done?</Label>
          <select id="bf-when" name="when" required className={selectClass} defaultValue="">
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
        <div className="grid gap-2">
          <Label htmlFor="bf-vehicle">Your car (make, model, year)</Label>
          <Input id="bf-vehicle" name="vehicle" required placeholder="BMW M4 Competition, 2023" autoComplete="off" className="h-11 text-base" />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="bf-suburb">Your suburb</Label>
          <Input id="bf-suburb" name="suburb" required placeholder="Gungahlin" autoComplete="address-level2" className="h-11 text-base" />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="bf-name">Your name</Label>
          <Input id="bf-name" name="name" required placeholder="Alex Smith" autoComplete="name" className="h-11 text-base" />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="bf-phone">Mobile number</Label>
          <Input id="bf-phone" name="phone" type="tel" required placeholder="0400 000 000" autoComplete="tel" className="h-11 text-base" />
        </div>
        <div className={`grid gap-2 ${compact ? "" : "sm:col-span-2"}`}>
          <Label htmlFor="bf-email">Email (optional)</Label>
          <Input id="bf-email" name="email" type="email" placeholder="you@example.com" autoComplete="email" className="h-11 text-base" />
        </div>
        <div className={`grid gap-2 ${compact ? "" : "sm:col-span-2"}`}>
          <Label htmlFor="bf-notes">Anything we should know? (optional)</Label>
          <Textarea id="bf-notes" name="notes" rows={3} placeholder="Paint condition, swirl marks, pet hair, preferred days" className="text-base" />
        </div>
        <div className="hidden" aria-hidden="true">
          <label htmlFor="bf-company">Company</label>
          <input id="bf-company" name="company" tabIndex={-1} autoComplete="off" />
        </div>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <button
          type="submit"
          disabled={status === "sending"}
          className="inline-flex min-h-[52px] items-center justify-center rounded-lg bg-accent px-6 text-base font-semibold text-accent-foreground hover:bg-[#5aa6f0] disabled:opacity-60"
        >
          {status === "sending" ? "Sending…" : "Request my quote"}
        </button>
        <span className="text-[15px] text-muted-foreground">
          Or call{" "}
          <a href={telHref} className="text-foreground underline underline-offset-4">
            {site.phoneDisplay}
          </a>
        </span>
      </div>
      <p className="m-0 text-sm text-muted-foreground">
        {site.quotePromise} By sending this you agree to our{" "}
        <a href="/privacy/" className="underline underline-offset-4">
          privacy policy
        </a>
        .
      </p>

      {status === "error" && (
        <p role="alert" className="m-0 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-[15px]">
          That didn't send. Call or text {site.phoneDisplay} and we'll sort it straight away.
        </p>
      )}

      {status === "fallback" && (
        <div role="status" className="rounded-lg border border-border bg-card p-5">
          <h3 className="text-lg font-semibold">Send this to us as a text</h3>
          <p className="mt-1 text-[15px] text-muted-foreground">
            On a phone, your messages app should have opened with the details filled in. If it didn't, copy them and text {site.phoneDisplay}, or email{" "}
            <a href={`mailto:${site.email}?subject=Quote%20request&body=${encodeURIComponent(message)}`} className="underline underline-offset-4">
              {site.email}
            </a>
            .
          </p>
          <pre className="mt-3 whitespace-pre-wrap rounded-md bg-background p-3 text-sm text-secondary-foreground">{message}</pre>
          <div className="mt-3 flex flex-wrap gap-3">
            <a href={smsHref(message)} className="inline-flex min-h-[44px] items-center rounded-md bg-accent px-4 text-[15px] font-semibold text-accent-foreground no-underline">
              Open in messages
            </a>
            <button type="button" onClick={copy} className="inline-flex min-h-[44px] items-center rounded-md border border-border px-4 text-[15px] font-semibold">
              Copy details
            </button>
          </div>
        </div>
      )}
    </form>
  );
}
