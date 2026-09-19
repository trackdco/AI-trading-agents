declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
    fbq?: (...args: unknown[]) => void;
  }
}

// One call for every conversion signal. Google Ads and Meta get it if they're loaded; nothing breaks if not.
export function track(name: string, params: Record<string, string | number> = {}) {
  try {
    window.gtag?.("event", name, params);
  } catch {}
  try {
    if (name === "generate_lead") window.fbq?.("track", "Lead", params);
    else if (name.startsWith("contact")) window.fbq?.("track", "Contact", params);
    else window.fbq?.("trackCustom", name, params);
  } catch {}
}
