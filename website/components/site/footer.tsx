import Link from "next/link";
import { site, telHref } from "@/lib/site";
import { services } from "@/lib/services";
import { areas } from "@/lib/areas";
import { articles } from "@/lib/articles";

const col = "flex flex-col gap-2.5 text-[15px]";
const link = "text-secondary-foreground no-underline hover:text-foreground";

export function Footer() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="container-x mx-auto grid max-w-6xl gap-12 py-16 md:grid-cols-12">
        <div className="md:col-span-4">
          <img src="/brand/logo-full-dark-320.png" width={375} height={320} alt="Imperium Detailing" className="h-28 w-auto" />
          <p className="mt-5 max-w-xs text-[15px] text-muted-foreground">
            Premium mobile detailing, ceramic coatings and paint correction across {site.area}. We come to your driveway or office car park.
          </p>
          <div className="mt-5 flex flex-col gap-2 text-[15px]">
            <a href={telHref} className={link}>
              {site.phoneDisplay}
            </a>
            <a href={`mailto:${site.email}`} className={`${link} break-all`}>
              {site.email}
            </a>
            <a href={site.instagram} className={link} rel="noopener">
              Instagram {site.instagramHandle}
            </a>
            <span className="text-muted-foreground">Canberra, ACT · {site.hours}</span>
          </div>
        </div>

        <div className="md:col-span-2">
          <h2 className="mb-4 text-sm font-semibold text-foreground">Services</h2>
          <div className={col}>
            {services.map((s) => (
              <Link key={s.slug} href={`/services/${s.slug}/`} className={link}>
                {s.name}
              </Link>
            ))}
            <Link href="/services/" className={link}>
              All services and prices
            </Link>
          </div>
        </div>

        <div className="md:col-span-3">
          <h2 className="mb-4 text-sm font-semibold text-foreground">Areas we serve</h2>
          <div className={`${col} sm:grid sm:grid-cols-2`}>
            {areas.map((a) => (
              <Link key={a.slug} href={`/service-areas/${a.slug}/`} className={link}>
                {a.name}
              </Link>
            ))}
          </div>
        </div>

        <div className="md:col-span-3">
          <h2 className="mb-4 text-sm font-semibold text-foreground">More</h2>
          <div className={col}>
            <Link href="/reviews/" className={link}>
              Reviews
            </Link>
            {articles.map((a) => (
              <Link key={a.slug} href={`/learn/${a.slug}/`} className={link}>
                {a.h1}
              </Link>
            ))}
            <Link href="/book/" className={link}>
              Get a quote
            </Link>
            <Link href="/warranty/" className={link}>
              Coating warranty
            </Link>
            <Link href="/privacy/" className={link}>
              Privacy
            </Link>
            <Link href="/terms/" className={link}>
              Terms
            </Link>
          </div>
        </div>
      </div>
      <div className="container-x mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 border-t border-border py-6 text-sm text-muted-foreground">
        <span>© {new Date().getFullYear()} Imperium Detailing. All rights reserved.</span>
        <span>Showroom finish. Every time.</span>
      </div>
    </footer>
  );
}
