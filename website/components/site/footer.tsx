import Link from "next/link";
import { site, smsHref, telHref } from "@/lib/site";
import { services } from "@/lib/services";
import { areas } from "@/lib/areas";
import { articles } from "@/lib/articles";
import { Marquee } from "@/components/site/marquee";

const col = "flex flex-col gap-2.5 text-[15px]";
const link = "link-slide text-secondary-foreground no-underline hover:text-foreground";

export function Footer() {
  return (
    <footer id="site-footer" className="relative overflow-hidden border-t border-border bg-background">
      {/* The closing ask, then the name at a size you can't miss. */}
      <div className="container-x mx-auto flex max-w-6xl flex-col gap-8 pb-4 pt-20 md:flex-row md:items-end md:justify-between md:pt-28">
        <div>
          <h2 className="display-caps text-[clamp(2.6rem,6.4vw,5.8rem)]" data-reveal="lines">
            Ready when you are.
          </h2>
          <p className="mt-5 max-w-[46ch] text-lg text-muted-foreground" data-reveal="up">
            {site.quotePromise}
          </p>
        </div>
        <div id="footer-cta" className="flex shrink-0 flex-col gap-3 sm:flex-row" data-reveal="up">
          <a
            href={smsHref()}
            className="inline-flex min-h-[54px] items-center justify-center rounded-full bg-accent px-7 text-base font-semibold text-accent-foreground no-underline shadow-[0_0_40px_rgba(58,143,224,0.3)] transition-transform duration-300 hover:-translate-y-0.5"
          >
            Text us your car
          </a>
          <a
            href={telHref}
            className="inline-flex min-h-[54px] items-center justify-center rounded-full border border-white/20 px-7 text-base font-semibold text-foreground no-underline transition-colors hover:border-white/50"
          >
            Call {site.phoneDisplay}
          </a>
        </div>
      </div>

      <div aria-hidden="true" className="container-x mx-auto max-w-6xl pt-10 md:pt-16">
        <div className="wordmark-fade display-caps select-none whitespace-nowrap text-[clamp(4rem,13.4vw,12.6rem)] leading-[0.82]">Imperium</div>
      </div>

      <div className="border-y border-border py-3">
        <Marquee items={["Showroom finish. Every time.", "Ceramic coating", "Paint correction", "Full detail", "Canberra and Queanbeyan"]} duration={55} />
      </div>

      <div className="container-x mx-auto grid max-w-6xl gap-12 py-16 md:grid-cols-12">
        <div className="md:col-span-4">
          <img src="/brand/logo-full-dark-320.png" width={375} height={320} alt="Imperium Detailing" className="h-24 w-auto" />
          <p className="mt-5 max-w-xs text-[15px] text-muted-foreground">
            Premium mobile detailing, ceramic coatings and paint correction across {site.area}. We come to your driveway or office car park.
          </p>
          <div className="mt-5 flex flex-col items-start gap-2 text-[15px]">
            <a href={telHref} className={link}>
              {site.phoneDisplay}
            </a>
            <a href={`mailto:${site.email}`} className={`${link} break-all`}>
              {site.email}
            </a>
            <a href={site.instagram} className={link} rel="noopener">
              Instagram {site.instagramHandle}
            </a>
            <span className="text-muted-foreground">Canberra, ACT. {site.hours}</span>
          </div>
        </div>

        <div className="md:col-span-2">
          <h2 className="mb-4 text-sm font-semibold text-foreground">Services</h2>
          <div className={`${col} items-start`}>
            {services.map((s) => (
              <Link key={s.slug} href={`/services/${s.slug}/`} className={link}>
                {s.name}
              </Link>
            ))}
            <Link href="/maintenance/" className={link}>
              Maintenance plans
            </Link>
            <Link href="/services/" className={link}>
              All services and prices
            </Link>
          </div>
        </div>

        <div className="md:col-span-3">
          <h2 className="mb-4 text-sm font-semibold text-foreground">Areas we serve</h2>
          <div className={`${col} items-start sm:grid sm:grid-cols-2`}>
            {areas.map((a) => (
              <Link key={a.slug} href={`/service-areas/${a.slug}/`} className={link}>
                {a.name}
              </Link>
            ))}
          </div>
        </div>

        <div className="md:col-span-3">
          <h2 className="mb-4 text-sm font-semibold text-foreground">More</h2>
          <div className={`${col} items-start`}>
            <Link href="/reviews/" className={link}>
              Reviews
            </Link>
            <a href={site.googleWriteReviewUrl} target="_blank" rel="noopener" className={link}>
              Write a Google review
            </a>
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
