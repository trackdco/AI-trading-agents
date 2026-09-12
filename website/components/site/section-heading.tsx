import type { ReactNode } from "react";

type Props = {
  id?: string;
  title: string;
  intro?: ReactNode;
  as?: "h1" | "h2";
  size?: "lg" | "xl";
};

// Left-aligned section opener: one heading, an optional intro, no labels above it.
export function SectionHeading({ id, title, intro, as = "h2", size = "lg" }: Props) {
  const Tag = as;
  const cls = size === "xl" ? "display text-5xl md:text-7xl" : "display text-4xl md:text-6xl";
  return (
    <div className="mb-10 max-w-3xl md:mb-14">
      <Tag id={id} className={cls}>
        {title}
      </Tag>
      {intro && <p className="mt-5 max-w-[60ch] text-lg text-muted-foreground">{intro}</p>}
    </div>
  );
}
