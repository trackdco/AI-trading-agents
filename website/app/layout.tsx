import type { Metadata } from "next";
import { Big_Shoulders, Instrument_Sans } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/site/header";
import { Footer } from "@/components/site/footer";
import { JsonLd } from "@/components/site/json-ld";
import { Analytics } from "@/components/site/analytics";
import { site } from "@/lib/site";

// Google folded "Big Shoulders Display" into the variable "Big Shoulders" family;
// the opsz axis gives the display cut automatically at headline sizes.
const display = Big_Shoulders({
  subsets: ["latin"],
  weight: "variable",
  axes: ["opsz"],
  variable: "--font-big-shoulders",
  display: "swap",
});

const sans = Instrument_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-instrument",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title: {
    default: "Mobile Car Detailing Canberra | Ceramic Coating & Paint Correction · Imperium Detailing",
    template: "%s · Imperium Detailing",
  },
  description:
    "Canberra's premium mobile car detailing. Ceramic coatings from $997, paint correction from $397, full details from $225. We come to you across Canberra and Queanbeyan.",
  openGraph: {
    type: "website",
    locale: "en_AU",
    siteName: site.name,
    images: [{ url: "/brand/og-image.jpg", width: 1200, height: 630, alt: "Imperium Detailing" }],
  },
  twitter: { card: "summary_large_image" },
  icons: {
    icon: [
      { url: "/brand/favicon-32.png", sizes: "32x32", type: "image/png" },
      { url: "/brand/icon-192.png", sizes: "192x192", type: "image/png" },
    ],
    apple: "/brand/apple-touch-icon.png",
    shortcut: "/brand/favicon.ico",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en-AU" className={`${display.variable} ${sans.variable} dark h-full`}>
      <body className="flex min-h-full flex-col">
        <Header />
        <main id="content" className="flex-1">
          {children}
        </main>
        <Footer />
        <JsonLd />
        <Analytics />
      </body>
    </html>
  );
}
