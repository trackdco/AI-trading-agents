type Props = { items: string[]; className?: string; duration?: number };

// A slow strip of service names separated by the logo mark. The moving copy is
// hidden from assistive tech; a plain list carries the same words for it.
export function Marquee({ items, className = "", duration = 42 }: Props) {
  const row = [...items, ...items];
  return (
    <div className={`marquee relative overflow-hidden ${className}`}>
      <ul className="sr-only">
        {items.map((t) => (
          <li key={t}>{t}</li>
        ))}
      </ul>
      <div aria-hidden="true" className="marquee-track flex w-max items-center" style={{ ["--marquee-duration" as string]: `${duration}s` }}>
        {row.map((t, i) => (
          <span key={i} className="display-caps flex items-center gap-8 pr-8 text-[clamp(1.4rem,2.4vw,2rem)] text-secondary-foreground/80">
            {t}
            <img src="/brand/logo-mark-96.webp" width={26} height={16} alt="" className="h-4 w-auto opacity-50" />
          </span>
        ))}
      </div>
    </div>
  );
}
