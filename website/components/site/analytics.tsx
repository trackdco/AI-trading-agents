"use client";

import { useEffect, useState } from "react";
import Script from "next/script";
import { site } from "@/lib/site";
import { track } from "@/lib/track";

// Google Ads tag (existing), Meta Pixel (when an ID is set), and the chat widget.
// The widget loads last, only on screens wide enough that it doesn't sit on the phone bar.
// Every call and text link on the site reports a contact event, tagged with the section it came from.
export function Analytics() {
  const [wide, setWide] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 768px)");
    const update = () => setWide(mq.matches);
    update();
    mq.addEventListener("change", update);

    const onClick = (e: MouseEvent) => {
      const a = (e.target as Element | null)?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (!a) return;
      const href = a.getAttribute("href") || "";
      const section = a.closest("[id]")?.id || "page";
      if (href.startsWith("tel:")) track("contact_call", { section });
      else if (href.startsWith("sms:")) track("contact_text", { section });
    };
    document.addEventListener("click", onClick, { capture: true, passive: true });
    return () => {
      mq.removeEventListener("change", update);
      document.removeEventListener("click", onClick, { capture: true });
    };
  }, []);

  return (
    <>
      {site.googleAdsId && (
        <>
          <Script src={`https://www.googletagmanager.com/gtag/js?id=${site.googleAdsId}`} strategy="afterInteractive" />
          <Script id="gtag-init" strategy="afterInteractive">
            {`window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${site.googleAdsId}');`}
          </Script>
        </>
      )}
      {site.metaPixelId && (
        <Script id="meta-pixel" strategy="afterInteractive">
          {`!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','${site.metaPixelId}');fbq('track','PageView');`}
        </Script>
      )}
      {site.chatWidgetId && wide && (
        <Script
          src="https://widgets.leadconnectorhq.com/loader.js"
          strategy="lazyOnload"
          data-resources-url="https://widgets.leadconnectorhq.com/chat-widget/loader.js"
          data-widget-id={site.chatWidgetId}
        />
      )}
    </>
  );
}
