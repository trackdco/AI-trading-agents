import type { NextConfig } from "next";

// Static export: every page is prerendered to HTML, so the site deploys to any
// static host (Vercel, Cloudflare Pages, Netlify, S3) with no server.
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  reactStrictMode: true,
};

export default nextConfig;
