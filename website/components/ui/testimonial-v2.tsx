"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";

// Scrolling testimonial columns. Adapted for Imperium Detailing: fed with real
// reviews, brand colours, an initials disc when there's no photo, and the
// marquee stops for people who've asked for reduced motion.

export interface Testimonial {
  text: string;
  name: string;
  role: string;
  image?: string;
}

const initials = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((n) => n[0]?.toUpperCase() ?? "")
    .join("");

const Avatar = ({ name, image }: { name: string; image?: string }) =>
  image ? (
    <img width={40} height={40} src={image} alt="" className="h-10 w-10 rounded-full object-cover ring-2 ring-border" />
  ) : (
    <span
      aria-hidden="true"
      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/20 text-sm font-semibold text-accent ring-2 ring-border"
    >
      {initials(name)}
    </span>
  );

const Card = ({ text, name, role, image }: Testimonial) => (
  <blockquote className="m-0 p-0">
    <p className="m-0 leading-relaxed text-secondary-foreground">{text}</p>
    <footer className="mt-6 flex items-center gap-3">
      <Avatar name={name} image={image} />
      <div className="flex flex-col">
        <cite className="not-italic font-semibold leading-5 tracking-tight text-foreground">{name}</cite>
        <span className="mt-0.5 text-sm leading-5 text-muted-foreground">{role}</span>
      </div>
    </footer>
  </blockquote>
);

const cardClass =
  "w-full max-w-xs rounded-2xl border border-border bg-card p-7 shadow-lg shadow-black/30 cursor-default select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-ring/60";

const TestimonialsColumn = (props: { className?: string; testimonials: Testimonial[]; duration?: number }) => {
  const reduce = useReducedMotion();

  if (reduce) {
    return (
      <div className={props.className}>
        <ul className="m-0 flex list-none flex-col gap-6 p-0">
          {props.testimonials.map((t, i) => (
            <li key={i} className={cardClass}>
              <Card {...t} />
            </li>
          ))}
        </ul>
      </div>
    );
  }

  return (
    <div className={props.className}>
      <motion.ul
        animate={{ translateY: "-50%" }}
        transition={{ duration: props.duration || 10, repeat: Infinity, ease: "linear", repeatType: "loop" }}
        className="m-0 flex list-none flex-col gap-6 p-0 pb-6"
      >
        {[
          ...new Array(2).fill(0).map((_, index) => (
            <React.Fragment key={index}>
              {props.testimonials.map((t, i) => (
                <motion.li
                  key={`${index}-${i}`}
                  aria-hidden={index === 1 ? "true" : "false"}
                  tabIndex={index === 1 ? -1 : 0}
                  whileHover={{ scale: 1.03, y: -8, transition: { type: "spring", stiffness: 400, damping: 17 } }}
                  whileFocus={{ scale: 1.03, y: -8, transition: { type: "spring", stiffness: 400, damping: 17 } }}
                  className={cardClass}
                >
                  <Card {...t} />
                </motion.li>
              ))}
            </React.Fragment>
          )),
        ]}
      </motion.ul>
    </div>
  );
};

export interface TestimonialsMarqueeProps {
  testimonials: Testimonial[];
  heading?: string;
  intro?: string;
  columns?: 2 | 3;
  maxHeight?: number;
}

export function TestimonialsMarquee({
  testimonials,
  heading = "Trusted by Canberra's most particular owners.",
  intro,
  columns = 3,
  maxHeight = 680,
}: TestimonialsMarqueeProps) {
  const cols: Testimonial[][] = Array.from({ length: columns }, () => []);
  testimonials.forEach((t, i) => cols[i % columns].push(t));
  const durations = [26, 32, 29];

  return (
    <section aria-labelledby="testimonials-heading" className="relative overflow-hidden bg-transparent py-16 md:py-24">
      <div className="container-x z-10 mx-auto w-full max-w-6xl">
        <div className="mb-12 max-w-4xl">
          <h2 id="testimonials-heading" className="display-caps text-[clamp(2.6rem,6.4vw,5.8rem)]" data-reveal="lines">
            {heading}
          </h2>
          {intro && (
            <p className="mt-6 max-w-[58ch] text-lg text-muted-foreground" data-reveal="up">
              {intro}
            </p>
          )}
        </div>

        <div
          className="mask-fade-y flex justify-center gap-6 overflow-hidden"
          style={{ maxHeight: `${maxHeight}px` }}
          role="region"
          aria-label="Customer reviews"
        >
          {cols.map((c, i) => (
            <TestimonialsColumn
              key={i}
              testimonials={c}
              duration={durations[i % durations.length]}
              className={i === 0 ? "" : i === 1 ? "hidden md:block" : "hidden lg:block"}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

export default TestimonialsMarquee;
