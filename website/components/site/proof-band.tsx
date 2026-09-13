import { Counter } from "@/components/site/counter";
import { site } from "@/lib/site";

// The four numbers a careful owner asks about, big enough to read from across the room.
const stats = [
  { value: 400, suffix: "+", label: "cars detailed in the last year" },
  { value: 4.9, decimals: 1, label: "stars across Google reviews" },
  { value: site.stats.reviewCount, label: "reviews, every one from a real customer" },
  { value: site.stats.warrantyYears, suffix: " yr", label: "written warranty on ceramic coatings" },
];

export function ProofBand() {
  return (
    <section aria-label="Proof" className="relative border-y border-border bg-card/40">
      <div className="container-x mx-auto grid max-w-6xl grid-cols-2 gap-x-6 gap-y-10 py-12 md:grid-cols-4 md:py-16">
        {stats.map((s, i) => (
          <div key={s.label} data-reveal="up" style={{ transitionDelay: `${i * 60}ms` }}>
            <Counter value={s.value} decimals={s.decimals} suffix={s.suffix} className="display-caps block text-[clamp(3rem,6.5vw,5.6rem)] leading-none text-foreground" />
            <p className="mt-3 max-w-[18ch] text-[15px] text-muted-foreground">{s.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
