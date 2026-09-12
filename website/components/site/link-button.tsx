import Link from "next/link";
import type { ReactNode } from "react";

type Props = {
  href: string;
  children: ReactNode;
  variant?: "primary" | "ghost";
  className?: string;
  external?: boolean;
};

const base =
  "inline-flex min-h-[52px] whitespace-nowrap items-center justify-center rounded-lg px-6 text-base font-semibold no-underline transition-colors duration-150 active:scale-[0.985]";
const variants = {
  primary: "bg-accent text-accent-foreground hover:bg-[#5aa6f0]",
  ghost: "border border-border text-foreground hover:border-secondary-foreground/50",
};

export function LinkButton({ href, children, variant = "primary", className = "", external }: Props) {
  const cls = `${base} ${variants[variant]} ${className}`;
  if (external || href.startsWith("tel:") || href.startsWith("sms:") || href.startsWith("mailto:") || href.startsWith("http")) {
    return (
      <a href={href} className={cls}>
        {children}
      </a>
    );
  }
  return (
    <Link href={href} className={cls}>
      {children}
    </Link>
  );
}
