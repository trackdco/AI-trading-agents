/* Imperium Clock — the shell, cached.

   The whole point of the offline queue is a dead spot behind a garage, and a
   queue is no use if the page that holds it cannot load there. This caches
   the app's own files so a tap on the home-screen icon always opens something.

   Only this origin is touched. Every request to the Google Sheet goes straight
   to the network, always — a cached timesheet would be a lie.

   Vercel serves this folder with cleanUrls, so "index.html" redirects to "/".
   A redirected response cannot be served for a navigation, so the page is
   cached under "./", which is also the manifest's start_url. */

const CACHE = 'imperium-clock-v1';
const SHELL = [
  './',
  'app.js',
  'config.js',
  'tokens.css',
  'fonts.css',
  'fonts/bigshoulders-8a3351.woff2',
  'fonts/instrumentsans-f587e7.woff2',
  'logo.webp',
  'icon-180.png',
  'icon-192.png',
  'icon-512.png',
  'manifest.webmanifest',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

const SHELL_PATHS = new Set(SHELL.map(p => new URL(p, self.location.href).pathname));

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;         // the Sheet is never cached
  if (req.mode !== 'navigate' && !SHELL_PATHS.has(url.pathname)) return;   // only the shell, ever

  if (req.mode === 'navigate') {
    // Network first so updates roll out, the cached shell when there is none.
    e.respondWith(fetch(req).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put('./', copy));
      return res;
    }).catch(() => caches.match('./')));
    return;
  }

  // Everything else: serve what is cached, refresh it in the background.
  e.respondWith(caches.match(req).then(hit => {
    const refetch = fetch(req).then(res => {
      if (res.ok) caches.open(CACHE).then(c => c.put(req, res.clone()));
      return res;
    }).catch(() => hit);
    return hit || refetch;
  }));
});
