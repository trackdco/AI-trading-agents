import type { Faq as FaqItem } from "@/lib/services";

// Native disclosure: works without JavaScript, keyboard-accessible by default.
export function Faq({ items, title = "Common questions" }: { items: FaqItem[]; title?: string }) {
  return (
    <div>
      <h2 className="display-caps text-3xl md:text-5xl">{title}</h2>
      <div className="mt-6 border-t border-border">
        {items.map((f) => (
          <details key={f.q} className="group border-b border-border">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 py-4 text-lg font-medium marker:content-none [&::-webkit-details-marker]:hidden">
              {f.q}
              <span aria-hidden="true" className="text-2xl text-muted-foreground transition-transform group-open:rotate-45">
                +
              </span>
            </summary>
            <p className="m-0 max-w-[68ch] pb-5 text-[15px] text-muted-foreground">{f.a}</p>
          </details>
        ))}
      </div>
    </div>
  );
}
