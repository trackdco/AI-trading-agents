import manifest from "@/lib/image-manifest.json";

type ImgMeta = { w: number; h: number; variants: number[] };
const images = manifest as Record<string, ImgMeta>;

type Props = {
  name: string;
  alt: string;
  className?: string;
  sizes?: string;
  priority?: boolean;
};

// Responsive image from the pre-generated WebP set in /public/images.
// Every image ships with width and height so nothing shifts while it loads.
export function Picture({ name, alt, className, sizes = "100vw", priority = false }: Props) {
  const m = images[name];
  if (!m) throw new Error(`Unknown image "${name}" — add it to public/images and lib/image-manifest.json`);
  const largest = m.variants[m.variants.length - 1];
  const srcSet = m.variants.map((w) => `/images/${name}-${w}.webp ${w}w`).join(", ");
  return (
    <img
      src={`/images/${name}-${largest}.webp`}
      srcSet={srcSet}
      sizes={sizes}
      width={m.w}
      height={m.h}
      alt={alt}
      loading={priority ? "eager" : "lazy"}
      decoding="async"
      className={className}
    />
  );
}

export const imageSize = (name: string) => {
  const m = images[name];
  return m ? { width: m.w, height: m.h } : {};
};
export const imageSrc = (name: string, w = 480) => `/images/${name}-${w}.webp`;
export const imageSrcSet = (name: string) => {
  const m = images[name];
  return m ? m.variants.map((w) => `/images/${name}-${w}.webp ${w}w`).join(", ") : undefined;
};
