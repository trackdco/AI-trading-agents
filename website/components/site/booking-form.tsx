"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { site, smsHref, telHref } from "@/lib/site";
import { track } from "@/lib/track";

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

// Matched to the Input component beside it: same radius, same fill, same padding.
// They sit in one grid, so a different corner and a different ground read as a bug.
const selectClass =
  "flex h-11 w-full rounded-lg border border-input bg-transparent px-2.5 text-base text-foreground outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 dark:bg-input/30";

export function BookingForm({ compact = false, defaultService = "" }: { compact?: boolean; defaultService?: string }) {
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");
  const [copied, setCopied] = useState(false);
  const serviceRef = useRef<HTMLSelectElement>(null);
  const fallbackRef = useRef<HTMLDivElement>(null);

  // The fallback panel appends below the submit button, so on a laptop it can
  // land off-screen and read as "nothing happened". Bring it into view.
  useEffect(() => {
    if (status === "fallback" || status === "error") fallbackRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [status]);

  // A link can pre-pick the service: /book/?service=Ceramic%20coating
  useEffect(() => {
    const wanted = new URLSearchParams(window.location.search).get("service");
    if (wanted && serviceRef.current && serviceOptions.includes(wanted)) serviceRef.current.value = wanted;
  }, []);

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

    if (site.formEndpoint && site.formAccessKey) {
      setStatus("sending");
      try {
        const payload: Record<string, string> = {};
        for (const [k, v] of data.entries()) payload[k] = String(v);
        delete payload.company; // our own honeypot, never worth mailing on
        payload.access_key = site.formAccessKey;
        // What Pat sees in his inbox before he opens anything.
        payload.subject = `Quote request: ${data.get("service")} in ${data.get("suburb")}`;
        payload.from_name = `${data.get("name")} — ${site.name} website`;
        const email = String(data.get("email") ?? "");
        if (email) payload.replyto = email; // so he can just hit reply

        // A dead network otherwise leaves the button on "Sending…" for ever, so
        // give up after twelve seconds and show them the text-us way out.
        const giveUp = new AbortController();
        const timer = window.setTimeout(() => giveUp.abort(), 12000);
        const res = await fetch(site.formEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify(payload),
          signal: giveUp.signal,
        }).finally(() => window.clearTimeout(timer));
        // Web3Forms answers 200 with {success:false} for a rejected send, so the
        // status code alone is not enough to call it delivered.
        const body = await res.json().catch(() => null);
        if (!res.ok || (body && body.success === false)) throw new Error(body?.message ?? String(res.status));
        track("generate_lead", { method: "form", service: String(data.get("service")) });
        setStatus("sent");
        form.reset();
      } catch {
        // Say plainly that it did not send, and still hand them the text-and-email
        // way out rather than a dead end they have to retype their way through.
        setStatus("error");
      }
      return;
    }

    // No endpoint configured: hand the composed message to their messaging app.
    // Only a phone actually opens one, so only count it as a lead there.
    setStatus("fallback");
    if (/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
      track("generate_lead", { method: "sms", service: String(data.get("service")) });
      window.location.href = smsHref(text);
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
        <h3 className="text-xl font-semibold">{"Done. We'll text you shortly."}</h3>
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
          <select id="bf-service" ref={serviceRef} name="service" required className={selectClass} defaultValue={defaultService}>
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
          {/* Web3Forms runs its own trap on a field with this exact name. */}
          <input type="checkbox" name="botcheck" tabIndex={-1} autoComplete="off" />
        </div>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <button
          type="submit"
          disabled={status === "sending"}
          className="lift inline-flex min-h-[52px] items-center justify-center rounded-lg bg-accent px-6 text-base font-semibold text-accent-foreground hover:bg-[#5aa6f0] disabled:opacity-60"
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
          {"That didn't send. Call or text "}
          {site.phoneDisplay}
          {" and we'll sort it straight away."}
        </p>
      )}

      {(status === "fallback" || status === "error") && (
        <div ref={fallbackRef} role="status" className="rounded-lg border border-border bg-card p-5">
          <h3 className="text-lg font-semibold">Send this to us as a text</h3>
          <p className="mt-1 text-[15px] text-muted-foreground">
            {"On a phone, your messages app should have opened with the details filled in. If it didn't, copy them and text "}
            {site.phoneDisplay}
            {", or email "}
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
              {copied ? "Copied" : "Copy details"}
            </button>
          </div>
        </div>
      )}
    </form>
  );
}
