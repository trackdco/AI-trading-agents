import Link from "next/link";
import { site } from "@/lib/site";

type Crumb = { href: string; label: string };

// The trail above a page title, with the matching BreadcrumbList for search engines.
export function Breadcrumbs({ items }: { items: Crumb[] }) {
  const ld = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: `${site.url}/` },
      ...items.map((c, i) => ({ "@type": "ListItem", position: i + 2, name: c.label, item: `${site.url}${c.href}` })),
    ],
  };
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }} />
      <nav aria-label="Breadcrumb" className="text-[15px] text-muted-foreground">
        <ol className="m-0 flex list-none flex-wrap gap-x-2 gap-y-1 p-0">
          <li>
            <Link href="/" className="underline underline-offset-4 hover:text-foreground">
              Home
            </Link>
          </li>
          {items.map((c, i) => (
            <li key={c.href} className="flex gap-2">
              <span aria-hidden="true">/</span>
              {i === items.length - 1 ? (
                <span aria-current="page" className="text-secondary-foreground">
                  {c.label}
                </span>
              ) : (
                <Link href={c.href} className="underline underline-offset-4 hover:text-foreground">
                  {c.label}
                </Link>
              )}
            </li>
          ))}
        </ol>
      </nav>
    </>
  );
}
