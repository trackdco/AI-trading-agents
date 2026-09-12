import type { MetadataRoute } from "next";
import { site } from "@/lib/site";
import { services } from "@/lib/services";
import { areas } from "@/lib/areas";
import { articles } from "@/lib/articles";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const page = (path: string, priority: number): MetadataRoute.Sitemap[number] => ({
    url: `${site.url}${path}`,
    lastModified: now,
    changeFrequency: "monthly",
    priority,
  });
  return [
    page("/", 1),
    page("/services/", 0.9),
    ...services.map((s) => page(`/services/${s.slug}/`, 0.9)),
    page("/maintenance/", 0.7),
    page("/car-detailing-canberra/", 0.7),
    page("/service-areas/", 0.7),
    ...areas.map((a) => page(`/service-areas/${a.slug}/`, 0.6)),
    page("/learn/", 0.6),
    ...articles.map((a) => page(`/learn/${a.slug}/`, 0.6)),
    page("/reviews/", 0.7),
    page("/book/", 0.8),
    page("/warranty/", 0.5),
    page("/privacy/", 0.2),
    page("/terms/", 0.2),
  ];
}
