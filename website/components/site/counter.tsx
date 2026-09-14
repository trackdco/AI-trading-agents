"use client";

import { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(useGSAP, ScrollTrigger);

type Props = { value: number; decimals?: number; prefix?: string; suffix?: string; className?: string };

// A number that counts up the first time it scrolls into view. Renders the final
// value in the HTML so it reads correctly without JavaScript.
export function Counter({ value, decimals = 0, prefix = "", suffix = "", className = "" }: Props) {
  const ref = useRef<HTMLSpanElement>(null);
  const format = (n: number) => `${prefix}${n.toFixed(decimals)}${suffix}`;

  useGSAP(() => {
    const el = ref.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const state = { n: 0 };
    gsap.to(state, {
      n: value,
      duration: 1.6,
      ease: "power3.out",
      scrollTrigger: { trigger: el, start: "top 90%", once: true },
      onUpdate: () => {
        el.textContent = format(state.n);
      },
    });
  });

  return (
    <span ref={ref} className={`tabular-nums ${className}`}>
      {format(value)}
    </span>
  );
}
