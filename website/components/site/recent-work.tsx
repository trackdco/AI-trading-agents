import { site } from "@/lib/site";
import { posts, recentJobs, postUrl } from "@/lib/instagram";
import { SectionHeading } from "@/components/site/section-heading";
import { Marquee } from "@/components/site/marquee";

// The latest posts, straight from Instagram, and a strip of recent jobs.
// Each embed sits over a plain card, so a blocked frame still shows a link to the post.
export function RecentWork() {
  const strip = recentJobs.map((j) => [j.car, j.service, j.suburb].filter(Boolean).join(", "));
  return (
    <section id="recent-work" className="border-t border-border py-20 md:py-28">
      <div className="container-x mx-auto max-w-6xl">
        <SectionHeading title="Fresh off the driveway." intro="What we posted last. Every car here is a real job, shot on the day, nothing staged." />
      </div>
      {strip.length > 0 && (
        <div className="border-y border-border py-3">
          <Marquee items={strip} duration={60} />
        </div>
      )}
      <div className="container-x mx-auto mt-10 max-w-6xl md:mt-14">
        <ul className="m-0 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
          {posts.map((p) => {
            const label = [p.car, p.service, p.suburb].filter(Boolean).join(", ");
            return (
              <li key={p.code} className="relative h-[560px] max-w-[400px] overflow-hidden rounded-xl border border-border bg-card">
                <a href={postUrl(p)} target="_blank" rel="noopener" className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-6 text-center no-underline">
                  <img src="/brand/logo-mark-96.png" width={59} height={36} alt="" className="h-9 w-auto opacity-70" />
                  <span className="text-[15px] font-semibold text-foreground">{label || "Watch this one on Instagram"}</span>
                  <span className="text-sm text-muted-foreground">{site.instagramHandle}</span>
                </a>
                <iframe
                  src={`https://www.instagram.com/${p.kind}/${p.code}/embed/`}
                  title={label ? `Instagram post: ${label}` : "Instagram post from Imperium Detailing"}
                  loading="lazy"
                  scrolling="no"
                  allowFullScreen
                  className="absolute inset-0 h-full w-full border-0"
                />
              </li>
            );
          })}
        </ul>
        <div className="mt-8 flex flex-wrap items-center gap-x-8 gap-y-3">
          <a href={site.instagram} target="_blank" rel="noopener" className="inline-flex min-h-[48px] items-center rounded-lg border border-border px-5 text-[15px] font-semibold text-foreground no-underline hover:border-secondary-foreground/50">
            Follow {site.instagramHandle}
          </a>
          <span className="text-[15px] text-muted-foreground">Stories go up most days we work.</span>
        </div>
      </div>
    </section>
  );
}
