import type { ReactNode } from "react";

type Props = {
  id?: string;
  title: string;
  intro?: ReactNode;
  as?: "h1" | "h2";
  size?: "lg" | "xl";
};

// Left-aligned section opener: one big uppercase heading that rises out of a mask, an
// optional intro, no labels above it.
export function SectionHeading({ id, title, intro, as = "h2", size = "lg" }: Props) {
  const Tag = as;
  const cls = size === "xl" ? "display-caps text-[clamp(3rem,8vw,7.4rem)]" : "display-caps text-[clamp(2.6rem,6.4vw,5.8rem)]";
  return (
    <div className="mb-10 max-w-4xl md:mb-14">
      <Tag id={id} className={cls} data-reveal="lines">
        {title}
      </Tag>
      {intro && (
        <p className="mt-6 max-w-[58ch] text-lg text-muted-foreground" data-reveal="up">
          {intro}
        </p>
      )}
    </div>
  );
}
