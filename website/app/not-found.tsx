import Link from "next/link";
import { site, telHref } from "@/lib/site";

export default function NotFound() {
  return (
    <section className="container-x mx-auto max-w-6xl py-20 md:py-32">
      <h1 className="display-caps text-5xl md:text-7xl">That page isn't here.</h1>
      <p className="mt-5 max-w-[52ch] text-lg text-muted-foreground">
        The link may be old. Everything is one step from the{" "}
        <Link href="/" className="text-foreground underline underline-offset-4">
          home page
        </Link>
        , or call{" "}
        <a href={telHref} className="text-foreground underline underline-offset-4">
          {site.phoneDisplay}
        </a>
        .
      </p>
    </section>
  );
}
