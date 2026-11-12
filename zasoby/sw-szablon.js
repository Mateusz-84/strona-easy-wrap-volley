/* Service worker Volley Kobyłka – strona działa także bez internetu.
   Strony: najpierw internet (zawsze świeże dane), bez sieci – ostatnia zapisana wersja.
   CSS, JS, zdjęcia: z pamięci od razu, w tle odświeżane.
   Plik powstaje przy budowaniu strony (build.py) z zasoby/sw-szablon.js. */
var WERSJA = '__WERSJA__';
var PAMIEC = 'volley-' + WERSJA;
var NA_START = ['./', './__START__', './terminarz.html', './druzyny.html',
  './zasoby/style.css?v=__ZASOB_V__', './zasoby/main.js?v=__ZASOB_V__', './zasoby/fonty.css?v=__ZASOB_V__',
  './img/favicon-192.png'];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(PAMIEC).then(function (c) {
    return Promise.all(NA_START.map(function (u) { return c.add(u).catch(function () {}); }));
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (klucze) {
    return Promise.all(klucze.filter(function (k) { return k.indexOf('volley-') === 0 && k !== PAMIEC; })
      .map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener('fetch', function (e) {
  var r = e.request;
  if (r.method !== 'GET') return;
  var url = new URL(r.url);
  if (url.origin !== self.location.origin) return;           // statystyki, wyniki na żywo, mapy – bez zmian
  if (/\.(ics)$/.test(url.pathname) || url.pathname.indexOf('statystyki') !== -1) return;

  if (r.mode === 'navigate' || (r.headers.get('accept') || '').indexOf('text/html') !== -1) {
    e.respondWith(fetch(r).then(function (odp) {
      if (odp && odp.ok) { var kopia = odp.clone(); caches.open(PAMIEC).then(function (c) { c.put(r, kopia); }); }
      return odp;
    }).catch(function () {
      return caches.match(r, { ignoreSearch: true }).then(function (z) {
        return z || caches.match('./__START__') || caches.match('./terminarz.html');
      });
    }));
    return;
  }

  e.respondWith(caches.open(PAMIEC).then(function (c) {
    return c.match(r).then(function (zapisane) {
      var siec = fetch(r).then(function (odp) {
        if (odp && odp.ok && odp.type === 'basic') c.put(r, odp.clone());
        return odp;
      }).catch(function () { return zapisane; });
      return zapisane || siec;
    });
  }));
});
