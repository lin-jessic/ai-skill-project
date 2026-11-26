/* Offline shell only. NEVER cache uploads, API requests or private reports. */
const CACHE = 'openshop-life-shell-v31';
const ASSETS = ['/', '/assets/styles.css', '/assets/app.js', '/manifest.webmanifest', '/assets/icons/icon-192.png', '/assets/icons/icon-512.png'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)));
  self.skipWaiting();
});
self.addEventListener('activate', event => {
  event.waitUntil(Promise.all([caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))),self.clients.claim()]));
});
self.addEventListener('fetch', event => {
  const req=event.request, url=new URL(req.url);
  if (req.method !== 'GET' || url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return;
  if (req.mode === 'navigate') {
    event.respondWith(fetch(req).catch(() => caches.match('/')));
    return;
  }
  if (ASSETS.includes(url.pathname)) {
    event.respondWith(caches.match(req).then(cached => cached || fetch(req)));
  }
});
