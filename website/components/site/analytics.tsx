"use client";

import Script from "next/script";
import { site } from "@/lib/site";

// Google Ads tag (existing), Meta Pixel (when an ID is set), and the chat widget
// (loaded last, after the page is interactive, so it never slows the first paint).
export function Analytics() {
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
      {site.chatWidgetId && (
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
