/* =====================================================================
   MAIN.JS – ZACHOWANIE STRONY
   ---------------------------------------------------------------------
   Bez bibliotek. Każdy blok działa tylko wtedy, gdy na stronie jest
   odpowiedni element – można go spokojnie zostawić na każdej podstronie.
   ===================================================================== */
(function () {
  'use strict';

  var DNI_KROTKO = ['Nd', 'Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'Sb'];
  var MIESIACE = ['Styczeń', 'Luty', 'Marzec', 'Kwiecień', 'Maj', 'Czerwiec', 'Lipiec',
    'Sierpień', 'Wrzesień', 'Październik', 'Listopad', 'Grudzień'];
  var MIESIACE_DOP = ['stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca', 'lipca',
    'sierpnia', 'września', 'października', 'listopada', 'grudnia'];
  var GODZINA = 3600 * 1000;

  function dwa(n) { return String(n).padStart(2, '0'); }
  function kluczDnia(d) { return d.getFullYear() + '-' + dwa(d.getMonth() + 1) + '-' + dwa(d.getDate()); }
  function zKlucza(k) { var c = k.split('-'); return new Date(+c[0], +c[1] - 1, +c[2]); }
  function tekst(s) { var el = document.createElement('span'); el.textContent = s == null ? '' : s; return el.innerHTML; }

  /* ---------------------------------------------------------------
     MENU MOBILNE
     --------------------------------------------------------------- */
  var przycisk = document.querySelector('.menu-przycisk');
  var menu = document.getElementById('menu');
  if (przycisk && menu) {
    var ustawMenu = function (otwarte) {
      menu.classList.toggle('otwarte', otwarte);
      document.body.classList.toggle('menu-otwarte', otwarte);   // tło się nie przewija
      przycisk.setAttribute('aria-expanded', otwarte);
    };
    przycisk.addEventListener('click', function () {
      ustawMenu(!menu.classList.contains('otwarte'));
    });
    menu.addEventListener('click', function (e) {
      if (e.target.closest('a')) ustawMenu(false);                // np. kotwica na tej samej stronie
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && menu.classList.contains('otwarte')) {
        ustawMenu(false);
        przycisk.focus();
      }
    });
  }

  /* ---------------------------------------------------------------
     ZAPOWIEDŹ MECZU – plakat z FB/IG na kilka sekund
       • znika sam po N sekundach (pasek pokazuje, ile zostało),
       • zamyka się kliknięciem, krzyżykiem albo klawiszem Esc,
       • najechanie myszą / fokus wstrzymuje odliczanie,
       • domyślnie tylko raz na wizytę (nie po każdym odświeżeniu).
     --------------------------------------------------------------- */
  var zapowiedz = document.querySelector('[data-zapowiedz]');
  if (zapowiedz) {
    var kluczPamieci = 'zapowiedz-' + zapowiedz.dataset.klucz;
    var juzWidziana = false;
    try { juzWidziana = zapowiedz.dataset.raz === '1' && sessionStorage.getItem(kluczPamieci) === '1'; } catch (e) {}
    if (!juzWidziana) {
      var sekundy = Number(zapowiedz.dataset.sekundy) || 3;
      var poprzedniFokus = document.activeElement;
      var pozostalo = sekundy * 1000, start = 0, odliczanie = null;
      var zamknij = function () {
        if (zapowiedz.hidden || zapowiedz.classList.contains('znika')) return;
        clearTimeout(odliczanie);
        document.removeEventListener('keydown', naKlawisz);
        zapowiedz.classList.add('znika');
        setTimeout(function () {
          zapowiedz.hidden = true;
          if (poprzedniFokus && poprzedniFokus.focus) poprzedniFokus.focus();
        }, 300);
        try { sessionStorage.setItem(kluczPamieci, '1'); } catch (e) {}
      };
      var wznow = function () { start = Date.now(); odliczanie = setTimeout(zamknij, pozostalo); };
      var wstrzymaj = function () { clearTimeout(odliczanie); pozostalo -= Date.now() - start; };
      var naKlawisz = function (e) { if (e.key === 'Escape') zamknij(); };

      zapowiedz.style.setProperty('--czas', sekundy + 's');
      zapowiedz.hidden = false;
      zapowiedz.querySelector('.zapowiedz__zamknij').focus({ preventScroll: true });
      wznow();
      // Wstrzymujemy tylko nad samym plakatem – tło zajmuje cały ekran, więc mysz i tak tam jest
      var ramka = zapowiedz.querySelector('.zapowiedz__ramka');
      ramka.addEventListener('mouseenter', wstrzymaj);
      ramka.addEventListener('mouseleave', wznow);
      zapowiedz.addEventListener('click', function (e) {
        // klik w tło lub krzyżyk zamyka; link „Zobacz post” działa normalnie
        if (e.target === zapowiedz || e.target.closest('[data-zapowiedz-zamknij]') || e.target.classList.contains('zapowiedz__img')) zamknij();
      });
      document.addEventListener('keydown', naKlawisz);
    }
  }

  /* ---------------------------------------------------------------
     GÓRNA BELKA – wybór meczu i licznik
     Strona zawiera kilka „kandydatów” (ostatni wynik + najbliższe mecze).
     Wybieramy właściwy wg aktualnego czasu:
       • do 48 h po meczu – wynik (chyba że kolejny mecz jest w ciągu 24 h),
       • potem – licznik do najbliższego meczu,
       • w trakcie meczu – „Mecz trwa”.
     --------------------------------------------------------------- */
  var belka = document.querySelector('[data-belka]');
  if (belka) {
    var szablony = Array.prototype.slice.call(belka.querySelectorAll('template'));
    var zegar = null;

    function koniecMeczu(t) {
      var start = Date.parse(t.dataset.start);
      if (t.dataset.godzina === '1') return start + 2.5 * GODZINA;
      return zKlucza(t.dataset.start.slice(0, 10)).getTime() + 24 * GODZINA; // koniec dnia
    }

    function wybierz() {
      var teraz = Date.now();
      var rozegrany = szablony.filter(function (t) { return t.dataset.rozegrany === '1'; })[0];
      var kolejny = szablony.filter(function (t) {
        return t.dataset.rozegrany !== '1' && teraz < koniecMeczu(t);
      })[0];
      if (rozegrany && teraz < Date.parse(rozegrany.dataset.start) + 48 * GODZINA &&
          !(kolejny && Date.parse(kolejny.dataset.start) - teraz < 24 * GODZINA)) {
        return rozegrany;
      }
      return kolejny || rozegrany || null;
    }

    function pokaz() {
      var t = wybierz();
      Array.prototype.slice.call(belka.children).forEach(function (el) {
        if (el.tagName !== 'TEMPLATE') el.remove();
      });
      if (!t) return;
      belka.appendChild(t.content.cloneNode(true));
      var licznik = belka.querySelector('[data-licznik]');
      clearInterval(zegar);
      if (!licznik) return;
      var start = Date.parse(t.dataset.start);
      var maGodzine = t.dataset.godzina === '1';

      function tik() {
        var teraz = Date.now();
        if (teraz >= koniecMeczu(t)) { pokaz(); return; }
        if (!maGodzine) {
          var dni = Math.round((zKlucza(t.dataset.start.slice(0, 10)) - zKlucza(kluczDnia(new Date()))) / (24 * GODZINA));
          licznik.innerHTML = dni <= 0 ? '<span class="belka__status">Dziś</span>'
            : '<span>' + dni + '<small>' + (dni === 1 ? 'DZIEŃ' : 'DNI') + '</small></span>';
          return;
        }
        var roznica = start - teraz;
        if (roznica <= 0) { licznik.innerHTML = '<span class="belka__status">Mecz trwa</span>'; return; }
        var s = Math.floor(roznica / 1000);
        licznik.querySelector('[data-j=d]').firstChild.textContent = Math.floor(s / 86400);
        licznik.querySelector('[data-j=h]').firstChild.textContent = dwa(Math.floor(s % 86400 / 3600));
        licznik.querySelector('[data-j=m]').firstChild.textContent = dwa(Math.floor(s % 3600 / 60));
        licznik.querySelector('[data-j=s]').firstChild.textContent = dwa(s % 60);
      }
      tik();
      zegar = setInterval(tik, 1000);
    }
    pokaz();
  }

  /* ---------------------------------------------------------------
     FILTRY MECZÓW – działają na wszystkie karty w obszarze [data-filtrowanie]
     --------------------------------------------------------------- */
  /* ---------------------------------------------------------------
     LICZNIK WYŚWIETLEŃ (stopka) – każde wczytanie strony dolicza 1.
     Gdy serwis nie odpowie, licznik po prostu się nie pokazuje.
     --------------------------------------------------------------- */
  var wysw = document.querySelector('[data-wyswietlenia]');
  if (wysw && window.fetch && location.protocol.indexOf('http') === 0) {
    // Liczymy tylko WEJŚCIE na stronę: przejście z podstrony na podstronę (ten sam adres w „skąd”)
    // tylko odczytuje licznik, bez zwiększania. Nic nie zapisujemy w przeglądarce.
    var wewnetrzne = false;
    try { wewnetrzne = !!document.referrer && new URL(document.referrer).host === location.host; } catch (e) {}
    fetch('https://abacus.jasoncameron.dev/' + (wewnetrzne ? 'get/' : 'hit/') + wysw.dataset.wyswietlenia)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d || typeof d.value !== 'number') return;
        wysw.querySelector('[data-wyswietlenia-liczba]').textContent = d.value.toLocaleString('pl-PL');
        wysw.title = 'Odwiedziny strony';
        wysw.hidden = false;
      })
      .catch(function () {});
  }

  /* ---------------------------------------------------------------
     KAFEL „POZNAJ NAS!”: przy każdym wejściu losowa zawodniczka z kadry
     --------------------------------------------------------------- */
  document.querySelectorAll('img[data-losowe]').forEach(function (obraz) {
    var lista = [];
    try { lista = JSON.parse(obraz.dataset.losowe); } catch (e) {}
    if (lista.length > 1) obraz.src = lista[Math.floor(Math.random() * lista.length)];
  });

  /* ---------------------------------------------------------------
     „NASZA KADRA” na stronie głównej: 3 losowe zawodniczki
     (CSS pokazuje tylko 3 pierwsze karty – tasujemy ich kolejność)
     --------------------------------------------------------------- */
  document.querySelectorAll('[data-losowa-kadra]').forEach(function (rzad) {
    var karty = Array.prototype.slice.call(rzad.children);
    for (var i = karty.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1)), tmp = karty[i]; karty[i] = karty[j]; karty[j] = tmp;
    }
    karty.forEach(function (k) { rzad.appendChild(k); });
  });

  /* ---------------------------------------------------------------
     KARUZELA MECZÓW (telefon): zaczyna od najbliższego meczu,
     a nie od najstarszego wyniku
     --------------------------------------------------------------- */
  document.querySelectorAll('.mecze:not(.mecze--siatka)').forEach(function (rzad) {
    var cel = rzad.querySelector('.mecz--najblizszy');
    if (!cel || rzad.scrollWidth <= rzad.clientWidth + 4) return;
    var start = rzad.children[0].getBoundingClientRect().left;   // gdzie stoi pierwsza karta
    rzad.scrollLeft = cel.getBoundingClientRect().left - start;
  });

  document.querySelectorAll('.filtry').forEach(function (grupa) {
    var przyciski = grupa.querySelectorAll('[data-klucz]');
    if (!przyciski.length) return;
    var lista = grupa.closest('[data-filtrowanie]') || grupa.parentElement;
    var stan = {};
    przyciski.forEach(function (b) {
      if (b.getAttribute('aria-pressed') === 'true') stan[b.dataset.klucz] = b.dataset.wartosc;
      b.addEventListener('click', function () {
        stan[b.dataset.klucz] = b.dataset.wartosc;
        przyciski.forEach(function (x) {
          if (x.dataset.klucz === b.dataset.klucz) x.setAttribute('aria-pressed', x === b);
        });
        lista.querySelectorAll('.mecz').forEach(function (m) {
          m.hidden = Object.keys(stan).some(function (k) {
            return stan[k] !== 'wszystkie' && m.dataset[k] !== stan[k];
          });
        });
      });
    });
  });

  /* ---------------------------------------------------------------
     KADRA – filtr pozycji i dotknięcie karty (telefon)
     --------------------------------------------------------------- */
  document.querySelectorAll('[data-pozycja].filtr').forEach(function (b, _, wszystkie) {
    b.addEventListener('click', function () {
      wszystkie.forEach(function (x) { x.setAttribute('aria-pressed', x === b); });
      document.querySelectorAll('.zawodniczka').forEach(function (z) {
        z.hidden = b.dataset.pozycja !== 'wszystkie' && z.dataset.pozycja !== b.dataset.pozycja;
      });
    });
  });
  document.querySelectorAll('.zawodniczka').forEach(function (k) {
    k.addEventListener('click', function () { k.classList.toggle('pokaz'); });
    k.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); k.classList.toggle('pokaz'); }
    });
  });

  /* ---------------------------------------------------------------
     KALENDARIUM – miesiąc dzień po dniu
     --------------------------------------------------------------- */
  var kal = document.querySelector('[data-kalendarium]');
  var kalDane = document.getElementById('kalendarium-dane');
  if (kal && kalDane) {
    var dane = JSON.parse(kalDane.textContent);
    var dzis = new Date();
    var dzisKlucz = kluczDnia(dzis);
    var widok = new Date(dzis.getFullYear(), dzis.getMonth(), 1);
    var typy = { mecz: true, trening: true, wydarzenie: true };
    var siatka = kal.querySelector('.kal__siatka');
    var lista = kal.querySelector('.kal__lista');
    var tytul = kal.querySelector('.kal__miesiac');

    function zdarzeniaMiesiaca() {
      var rok = widok.getFullYear(), mies = widok.getMonth();
      var wynik = dane.zdarzenia.filter(function (z) {
        var d = zKlucza(z.d);
        return d.getFullYear() === rok && d.getMonth() === mies && typy[z.typ];
      });
      // Treningi powtarzają się co tydzień w okresie sezonu (bez dni wolnych)
      if (typy.trening && dane.sezon_od && dane.sezon_do) {
        var dniMies = new Date(rok, mies + 1, 0).getDate();
        for (var dzien = 1; dzien <= dniMies; dzien++) {
          var d = new Date(rok, mies, dzien), k = kluczDnia(d);
          if (k < dane.sezon_od || k > dane.sezon_do || dane.wolne.indexOf(k) >= 0) continue;
          dane.treningi.forEach(function (t) {
            if ((t.dzien + 1) % 7 === d.getDay()) {
              wynik.push({ d: k, g: t.od + '–' + t.do, typ: 'trening', t: t.t, m: t.m });
            }
          });
        }
      }
      return wynik.sort(function (a, b) { return (a.d + (a.g || '')).localeCompare(b.d + (b.g || '')); });
    }

    function rysuj() {
      var zdarzenia = zdarzeniaMiesiaca();
      var poDniu = {};
      zdarzenia.forEach(function (z) { (poDniu[z.d] = poDniu[z.d] || []).push(z); });
      tytul.textContent = MIESIACE[widok.getMonth()] + ' ' + widok.getFullYear();

      var html = ['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'Sb', 'Nd'].map(function (d) {
        return '<div class="kal__dzien-tyg" aria-hidden="true">' + d + '</div>';
      }).join('');
      var przesuniecie = (widok.getDay() + 6) % 7;
      for (var i = 0; i < przesuniecie; i++) html += '<div class="kal__dzien kal__dzien--pusty"></div>';
      var dniMies = new Date(widok.getFullYear(), widok.getMonth() + 1, 0).getDate();
      for (var dzien = 1; dzien <= dniMies; dzien++) {
        var k = kluczDnia(new Date(widok.getFullYear(), widok.getMonth(), dzien));
        var z = poDniu[k] || [];
        var kropki = z.map(function (x) { return '<span class="kal__kropka typ-' + x.typ + '"></span>'; }).join('');
        var opis = dzien + ' ' + MIESIACE_DOP[widok.getMonth()] + (z.length ? ': ' + z.map(function (x) { return x.t; }).join(', ') : ', brak wydarzeń');
        html += '<button type="button" class="kal__dzien' + (k === dzisKlucz ? ' kal__dzien--dzis' : '') +
          '" data-dzien="' + k + '" aria-label="' + tekst(opis) + '"' + (z.length ? '' : ' tabindex="-1"') + '>' +
          dzien + '<span class="kal__kropki">' + kropki + '</span></button>';
      }
      siatka.innerHTML = html;

      lista.innerHTML = zdarzenia.length ? zdarzenia.map(function (z) {
        var d = zKlucza(z.d);
        return '<li class="kal__wpis kal__wpis--' + z.typ + (z.d === dzisKlucz ? ' kal__wpis--dzis' : '') + '" data-wpis="' + z.d + '">' +
          '<div class="kal__wpis-data">' + d.getDate() + '<small>' + DNI_KROTKO[d.getDay()] + '</small></div>' +
          '<div><strong>' + tekst(z.t) + (z.w ? ' (wyjazd)' : '') + '</strong><span>' +
          tekst([z.g, z.m].filter(Boolean).join(' · ')) + '</span></div></li>';
      }).join('') : '<li class="pusto">Brak wydarzeń w tym miesiącu.</li>';
    }

    kal.addEventListener('click', function (e) {
      var nav = e.target.closest('[data-kal]');
      if (nav) {
        widok.setMonth(widok.getMonth() + (nav.dataset.kal === 'nastepny' ? 1 : -1));
        rysuj();
        return;
      }
      var typ = e.target.closest('[data-typ]');
      if (typ) {
        typy[typ.dataset.typ] = !typy[typ.dataset.typ];
        typ.setAttribute('aria-pressed', typy[typ.dataset.typ]);
        rysuj();
        return;
      }
      var dzien = e.target.closest('[data-dzien]');
      if (dzien) {
        siatka.querySelectorAll('.kal__dzien--wybrany').forEach(function (x) { x.classList.remove('kal__dzien--wybrany'); });
        dzien.classList.add('kal__dzien--wybrany');
        var wpis = lista.querySelector('[data-wpis="' + dzien.dataset.dzien + '"]');
        if (wpis) wpis.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
    rysuj();
  }

  /* ---------------------------------------------------------------
     GALERIA – powiększanie zdjęć
     --------------------------------------------------------------- */
  var okno = document.querySelector('[data-lightbox-okno]');
  var linki = Array.prototype.slice.call(document.querySelectorAll('[data-lightbox]'));
  if (okno && linki.length && okno.showModal) {
    var obraz = okno.querySelector('img');
    var biezacy = 0;
    function otworz(i) {
      biezacy = (i + linki.length) % linki.length;
      obraz.src = linki[biezacy].href;
      obraz.alt = linki[biezacy].querySelector('img').alt;
      if (!okno.open) okno.showModal();
    }
    linki.forEach(function (a, i) {
      a.addEventListener('click', function (e) { e.preventDefault(); otworz(i); });
    });
    okno.addEventListener('click', function (e) {
      if (e.target.closest('[data-lightbox-zamknij]') || e.target === okno) okno.close();
      var krok = e.target.closest('[data-lightbox-krok]');
      if (krok) otworz(biezacy + Number(krok.dataset.lightboxKrok));
    });
    okno.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') otworz(biezacy + 1);
      if (e.key === 'ArrowLeft') otworz(biezacy - 1);
    });
  }

  /* ---------------------------------------------------------------
     FORMULARZ GOOGLE – wczytywany dopiero po kliknięciu
     (szybsza strona i brak cookies Google bez zgody)
     --------------------------------------------------------------- */
  document.querySelectorAll('[data-formularz]').forEach(function (b) {
    b.addEventListener('click', function () {
      var ramka = document.querySelector('[data-formularz-ramka]');
      if (!ramka || ramka.querySelector('iframe')) return;
      var iframe = document.createElement('iframe');
      iframe.src = b.dataset.formularz;
      iframe.title = 'Formularz zapisu';
      iframe.loading = 'lazy';
      ramka.appendChild(iframe);
      b.hidden = true;
      iframe.focus();
    });
  });

  /* ---------------------------------------------------------------
     POJAWIANIE SIĘ SEKCJI PRZY PRZEWIJANIU
     --------------------------------------------------------------- */
  var sekcje = document.querySelectorAll('.pojaw');
  if ('IntersectionObserver' in window) {
    var obserwator = new IntersectionObserver(function (wpisy) {
      wpisy.forEach(function (w) {
        if (w.isIntersecting) { w.target.classList.add('widoczne'); obserwator.unobserve(w.target); }
      });
    }, { threshold: 0.12 });
    sekcje.forEach(function (el) { obserwator.observe(el); });
  } else {
    sekcje.forEach(function (el) { el.classList.add('widoczne'); });
  }
})();


/* Nazwa naszej drużyny (tabela, mecze): na komputerze Facebook, na telefonie Instagram */
(function () {
  if (!window.matchMedia || !matchMedia('(hover: none) and (pointer: coarse)').matches) return;
  document.querySelectorAll('a[data-telefon]').forEach(function (a) { a.href = a.getAttribute('data-telefon'); });
})();

/* Adresy e-mail: w kodzie strony są zakodowane (ochrona przed botami) – tu składamy prawdziwe */
(function () {
  function dekoduj(s) { try { return atob(s).split('').reverse().join(''); } catch (e) { return ''; } }
  document.querySelectorAll('[data-mail]').forEach(function (el) {
    var adres = dekoduj(el.getAttribute('data-mail'));
    if (!adres) return;
    if (el.tagName === 'A') {
      var q = el.getAttribute('data-mail-q');
      el.href = 'mailto:' + adres + (q ? '?' + q : '');
    } else {
      el.textContent = adres;
    }
  });
})();

/* Statystyki odwiedzin (bez ciasteczek, nic nie zapisujemy w przeglądarce):
   liczniki na serwisie Abacus – wyświetlenia każdej podstrony, wejścia, źródła i urządzenia w danym miesiącu.
   Podgląd: volleykobylka.pl/statystyki.html */
(function () {
  if (!window.fetch || location.protocol.indexOf('http') !== 0 || navigator.webdriver) return;
  var strona = location.pathname.replace(/^\/+|\.html$/g, '') || 'start';
  if (strona === 'statystyki') return;
  var ns = 'volleykobylka-pl';
  var d = new Date(), mies = d.getFullYear() + ('0' + (d.getMonth() + 1)).slice(-2);
  var klucz = strona.toLowerCase().replace(/[^a-z0-9-]+/g, '_').slice(0, 44);
  var hity = ['s-' + klucz + '-' + mies, 'wszystko-' + mies];
  var skad = '', wewn = false;
  try { var r = new URL(document.referrer); wewn = r.host === location.host; skad = r.host.toLowerCase(); } catch (e) {}
  if (!wewn) {
    var zrodlo = !skad ? 'bezposrednio'
      : /google\./.test(skad) ? 'google'
      : /(facebook|fb)\.(com|me)|messenger/.test(skad) ? 'facebook'
      : /instagram/.test(skad) ? 'instagram'
      : /bing\.|duckduckgo|yahoo|ecosia|brave/.test(skad) ? 'inne-wyszukiwarki'
      : 'inne-strony';
    var tel = window.matchMedia && matchMedia('(pointer: coarse)').matches;
    hity.push('wejscia-' + mies, 'zrodlo-' + zrodlo + '-' + mies, 'urz-' + (tel ? 'telefon' : 'komputer') + '-' + mies);
  }
  hity.forEach(function (k) {
    fetch('https://abacus.jasoncameron.dev/hit/' + ns + '/' + k, { keepalive: true }).catch(function () {});
  });
})();

/* Strona statystyk – odczyt liczników (tylko „get”, nic nie dolicza) */
(function () {
  var box = document.querySelector('[data-statystyki]');
  if (!box || !window.fetch) return;
  var strony = JSON.parse(box.getAttribute('data-statystyki'));
  var ns = 'volleykobylka-pl', sel = box.querySelector('[data-st-miesiac]');
  var nazwyMies = ['styczeń','luty','marzec','kwiecień','maj','czerwiec','lipiec','sierpień','wrzesień','październik','listopad','grudzień'];
  var d = new Date();
  for (var i = 0; i < 12; i++) {
    var m = new Date(d.getFullYear(), d.getMonth() - i, 1);
    if (m < new Date(2026, 10, 1)) break;
    var o = document.createElement('option');
    o.value = m.getFullYear() + ('0' + (m.getMonth() + 1)).slice(-2);
    o.textContent = nazwyMies[m.getMonth()] + ' ' + m.getFullYear();
    sel.appendChild(o);
  }
  function get(k) {
    return fetch('https://abacus.jasoncameron.dev/get/' + ns + '/' + k)
      .then(function (r) { return r.ok ? r.json() : { value: 0 }; })
      .then(function (j) { return j.value || 0; }).catch(function () { return 0; });
  }
  function lista(el, wiersze) {
    var max = Math.max.apply(null, wiersze.map(function (w) { return w[1]; }).concat([1]));
    el.innerHTML = wiersze.filter(function (w) { return w[1] > 0; }).sort(function (a, b) { return b[1] - a[1]; })
      .map(function (w) {
        return '<div class="st-wiersz"><span class="st-nazwa">' + w[0] + '</span><span class="st-pasek"><i style="width:' +
          Math.round(w[1] / max * 100) + '%"></i></span><b>' + w[1].toLocaleString('pl-PL') + '</b></div>';
      }).join('') || '<p class="pusto">Brak danych w tym miesiącu.</p>';
  }
  function wczytaj() {
    var mies = sel.value;
    ['wszystko', 'wejscia'].forEach(function (k) {
      get(k + '-' + mies).then(function (v) { box.querySelector('[data-st=' + k + ']').textContent = v.toLocaleString('pl-PL'); });
    });
    ['telefon', 'komputer'].forEach(function (k) {
      get('urz-' + k + '-' + mies).then(function (v) { box.querySelector('[data-st=' + k + ']').textContent = v.toLocaleString('pl-PL'); });
    });
    var zr = [['Google', 'google'], ['Facebook', 'facebook'], ['Instagram', 'instagram'], ['Wpisany adres / zakładka', 'bezposrednio'],
              ['Inne wyszukiwarki', 'inne-wyszukiwarki'], ['Inne strony', 'inne-strony']];
    Promise.all(zr.map(function (z) { return get('zrodlo-' + z[1] + '-' + mies).then(function (v) { return [z[0], v]; }); }))
      .then(function (w) { lista(box.querySelector('[data-st-zrodla]'), w); });
    Promise.all(strony.map(function (s) { return get('s-' + s[1] + '-' + mies).then(function (v) { return [s[0] === 'index.html' ? 'Strona wyboru' : s[0].replace(/\.html$/, ''), v]; }); }))
      .then(function (w) { lista(box.querySelector('[data-st-strony]'), w); });
  }
  sel.addEventListener('change', wczytaj);
  wczytaj();
})();

/* Plansza meczu: w trakcie meczu pasek „Na żywo” z wynikiem na żywo i transmisją;
   po meczu (do czasu aktualizacji strony) informacja, że wynik pojawi się wkrótce */
(function () {
  var hero = document.querySelector('.hero[data-start]');
  if (!hero) return;
  var start = new Date(hero.getAttribute('data-start'));
  if (isNaN(start)) return;
  var pasek = hero.querySelector('.hero__na-zywo'), tekst = pasek && pasek.querySelector('[data-na-zywo-tekst]');
  var etykieta = hero.querySelector('.hero__etykieta'), pierwotna = etykieta ? etykieta.textContent : '';
  function stan() {
    var min = (Date.now() - start.getTime()) / 60000;
    var trwa = min >= -5 && min < 150, po = min >= 150 && min < 360;
    hero.classList.toggle('hero--na-zywo', trwa);
    if (pasek) {
      pasek.hidden = !(trwa || po);
      tekst.textContent = trwa ? 'Mecz trwa – na żywo' : 'Mecz zakończony – wynik pojawi się tu wkrótce';
      pasek.querySelectorAll('a').forEach(function (a) { a.hidden = !trwa; });
    }
    if (etykieta) etykieta.textContent = trwa ? '● Na żywo' : pierwotna;
  }
  stan();
  setInterval(stan, 30000);
})();


/* „Skopiuj adres kalendarza” (subskrypcja terminarza) */
(function () {
  document.querySelectorAll('[data-kopiuj]').forEach(function (b) {
    b.addEventListener('click', function () {
      var t = b.getAttribute('data-kopiuj'), stary = b.textContent;
      function ok() { b.textContent = 'Skopiowano ✓'; setTimeout(function () { b.textContent = stary; }, 2000); }
      if (navigator.clipboard) navigator.clipboard.writeText(t).then(ok, function () { prompt('Adres kalendarza:', t); });
      else prompt('Adres kalendarza:', t);
    });
  });
})();

/* „Poznaj nas” na stronie głównej: losowa odpowiedź zawodniczki (inna przy każdej wizycie i po kliknięciu) */
(function () {
  var box = document.querySelector('[data-ciekawostki]');
  if (!box) return;
  var w = JSON.parse(box.getAttribute('data-ciekawostki')), ost = -1;
  function pokaz() {
    if (!w.length) return;
    var i; do { i = Math.floor(Math.random() * w.length); } while (w.length > 1 && i === ost);
    ost = i; var x = w[i];
    box.querySelector('.ciek__q').textContent = x.q;
    box.querySelector('.ciek__a').textContent = '„' + x.a + '”';
    var k = box.querySelector('.ciek__kto'); k.textContent = x.k + ' – poznaj ją →'; k.href = x.u;
    var f = box.querySelector('.ciek__foto'); if (x.f) { f.src = x.f; f.hidden = false; } else f.hidden = true;
  }
  pokaz();
  box.querySelector('.ciek__inne').addEventListener('click', pokaz);
})();

/* =====================================================================
   ŚWIĄTECZNE LOGO – w czasie świąt herb KS Volley i logo Akademii
   dostają tematyczny dodatek (czapka Mikołaja, kotylion, znicz,
   czapeczka sylwestrowa z fajerwerkami, pisanki).
   Data liczona wg czasu polskiego, Wielkanoc wyliczana co roku sama.
   Podgląd dowolnego święta: dopisz do adresu ?swieto=bn | nowyrok |
   wielkanoc | zaduszki | niepodleglosc  (albo ?swieto=brak).
   ===================================================================== */
(function () {
  'use strict';

  function dzisWarszawa() {
    try {
      var s = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Warsaw', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
      var c = s.split('-'); return new Date(+c[0], +c[1] - 1, +c[2]);
    } catch (e) { var d = new Date(); return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
  }
  function wielkanoc(r) {            // algorytm Meeusa/Jonesa/Butchera
    var a = r % 19, b = Math.floor(r / 100), c = r % 100, d = Math.floor(b / 4), e = b % 4,
      f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30,
      i = Math.floor(c / 4), k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7, m = Math.floor((a + 11 * h + 22 * l) / 451),
      mies = Math.floor((h + l - 7 * m + 114) / 31), dz = ((h + l - 7 * m + 114) % 31) + 1;
    return new Date(r, mies - 1, dz);
  }
  function wZakresie(d, od, doo) { return d >= od && d <= doo; }

  function ktoreSwieto(d) {
    var r = d.getFullYear(), D = function (m, dz, rr) { return new Date(rr || r, m - 1, dz); };
    var w = wielkanoc(r), wOd = new Date(w), wDo = new Date(w);
    wOd.setDate(w.getDate() - 3); wDo.setDate(w.getDate() + 1);
    if (wZakresie(d, D(12, 20), D(12, 27))) return 'bn';
    if (wZakresie(d, D(12, 31), D(12, 31)) || wZakresie(d, D(1, 1), D(1, 2))) return 'nowyrok';
    if (wZakresie(d, wOd, wDo)) return 'wielkanoc';
    if (wZakresie(d, D(11, 1), D(11, 2))) return 'zaduszki';
    if (wZakresie(d, D(11, 10), D(11, 12))) return 'niepodleglosc';
    return null;
  }

  var dzis = dzisWarszawa();
  var swieto = ktoreSwieto(dzis);
  var wymuszone = (location.search.match(/[?&]swieto=([a-z]+)/) || [])[1];
  if (wymuszone) swieto = wymuszone === 'brak' ? null : wymuszone;
  if (!swieto) return;

  var rokNowy = dzis.getMonth() === 11 ? dzis.getFullYear() + 1 : dzis.getFullYear();
  var PODPIS = {
    bn: 'Wesołych Świąt Bożego Narodzenia!',
    nowyrok: 'Szczęśliwego Nowego Roku ' + rokNowy + '!',
    wielkanoc: 'Wesołych Świąt Wielkanocnych!',
    zaduszki: 'Wszystkich Świętych – pamiętamy',
    niepodleglosc: '11 listopada – Narodowe Święto Niepodległości'
  };

  /* ---------- rysunki (SVG) ---------- */
  var CZAPKA = '<svg viewBox="0 0 100 80" class="sw__ruch sw__ruch--kolys">' +
    '<defs><linearGradient id="swCz" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F0413B"/><stop offset="1" stop-color="#B3161C"/></linearGradient>' +
    '<linearGradient id="swFu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#DCE3EC"/></linearGradient></defs>' +
    '<path d="M12 62 C 18 34 40 10 68 9 C 83 9 93 18 93 33 C 86 26 76 24 69 28 C 75 39 80 50 84 62 Z" fill="url(#swCz)"/>' +
    '<path d="M69 28 C 75 39 80 50 84 62 L 74 62 C 72 50 69 40 64 31 Z" fill="#000" opacity=".14"/>' +
    '<rect x="4" y="55" width="88" height="19" rx="9.5" fill="url(#swFu)"/>' +
    '<g fill="#C9D3DF"><circle cx="16" cy="66" r="2"/><circle cx="31" cy="62" r="1.6"/><circle cx="47" cy="67" r="2"/><circle cx="62" cy="62" r="1.6"/><circle cx="78" cy="67" r="2"/></g>' +
    '<circle cx="92" cy="36" r="9" fill="url(#swFu)"/><circle cx="89" cy="33" r="3" fill="#fff"/></svg>';

  var KOTYLION = (function () {
    var plis = '', i, a;
    for (i = 0; i < 36; i++) { a = i * 10 * Math.PI / 180;
      plis += '<line x1="' + (50 + 26 * Math.cos(a)).toFixed(1) + '" y1="' + (44 + 26 * Math.sin(a)).toFixed(1) +
        '" x2="' + (50 + 41 * Math.cos(a)).toFixed(1) + '" y2="' + (44 + 41 * Math.sin(a)).toFixed(1) + '"/>'; }
    var plis2 = '';
    for (i = 0; i < 24; i++) { a = (i * 15 + 7) * Math.PI / 180;
      plis2 += '<line x1="' + (50 + 9 * Math.cos(a)).toFixed(1) + '" y1="' + (44 + 9 * Math.sin(a)).toFixed(1) +
        '" x2="' + (50 + 25 * Math.cos(a)).toFixed(1) + '" y2="' + (44 + 25 * Math.sin(a)).toFixed(1) + '"/>'; }
    return '<svg viewBox="0 0 100 124" class="sw__ruch sw__ruch--powiew">' +
      '<path d="M44 52 L 24 118 L 33 110 L 39 121 L 56 58 Z" fill="#fff" stroke="#D5DCE5" stroke-width="1"/>' +
      '<path d="M56 52 L 76 118 L 67 110 L 61 121 L 44 58 Z" fill="#DC143C"/>' +
      '<circle cx="50" cy="44" r="42" fill="#fff" stroke="#D5DCE5" stroke-width="1.2"/>' +
      '<g stroke="#D9DFE7" stroke-width="1.1">' + plis + '</g>' +
      '<circle cx="50" cy="44" r="26" fill="#DC143C"/>' +
      '<g stroke="#A50E2B" stroke-width="1.1">' + plis2 + '</g>' +
      '<circle cx="50" cy="44" r="9" fill="#fff"/><circle cx="50" cy="44" r="5" fill="#DC143C"/>' +
      '<circle cx="47.5" cy="41.5" r="1.6" fill="#fff" opacity=".8"/></svg>';
  })();

  var ZNICZ = '<svg viewBox="0 0 60 112">' +
    '<defs><radialGradient id="swPo" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FFC24A" stop-opacity=".75"/><stop offset="1" stop-color="#FFC24A" stop-opacity="0"/></radialGradient>' +
    '<linearGradient id="swSz" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#7E0E17"/><stop offset=".45" stop-color="#D3263A"/><stop offset="1" stop-color="#6A0B13"/></linearGradient>' +
    '<linearGradient id="swPl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFF6C8"/><stop offset=".5" stop-color="#FFB627"/><stop offset="1" stop-color="#F25A12"/></linearGradient>' +
    '<linearGradient id="swZl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#9C7A2B"/><stop offset=".5" stop-color="#F2D27A"/><stop offset="1" stop-color="#8A6A20"/></linearGradient></defs>' +
    '<circle cx="30" cy="34" r="30" fill="url(#swPo)" class="sw__poswiata"/>' +
    '<g class="sw__plomien"><path d="M30 8 C 37 20 40 27 37 34 C 35 39 25 39 23 34 C 20 27 24 19 30 8 Z" fill="url(#swPl)"/>' +
    '<path d="M30 22 C 33 27 34 31 32 34 C 31 36 29 36 28 34 C 27 31 28 27 30 22 Z" fill="#fff" opacity=".85"/></g>' +
    '<rect x="29.2" y="34" width="1.6" height="5" fill="#333"/>' +
    '<path d="M12 40 H48 L 45 104 Q 30 108 15 104 Z" fill="url(#swSz)"/>' +
    '<path d="M18 44 L 21 100" stroke="#fff" stroke-opacity=".35" stroke-width="3" stroke-linecap="round"/>' +
    '<ellipse cx="30" cy="62" rx="9" ry="14" fill="#FFB627" opacity=".35"/>' +
    '<rect x="9" y="36" width="42" height="7" rx="2" fill="url(#swZl)"/>' +
    '<rect x="13" y="102" width="34" height="6" rx="2" fill="url(#swZl)"/></svg>';

  var CZAPECZKA = '<svg viewBox="0 0 64 84" class="sw__ruch sw__ruch--kolys">' +
    '<defs><clipPath id="swSt"><path d="M32 10 L 58 76 Q 32 84 6 76 Z"/></clipPath></defs>' +
    '<path d="M32 10 L 58 76 Q 32 84 6 76 Z" fill="#F4C842"/>' +
    '<g clip-path="url(#swSt)" fill="#13305E"><path d="M0 34 L 64 18 L 64 26 L 0 42 Z"/><path d="M0 54 L 64 38 L 64 46 L 0 62 Z"/><path d="M0 74 L 64 58 L 64 66 L 0 82 Z"/></g>' +
    '<path d="M32 10 L 58 76 Q 32 84 6 76 Z" fill="none" stroke="#C99A16" stroke-width="1.2"/>' +
    '<path d="M5 76 Q 32 86 59 76" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round" stroke-dasharray="1 6"/>' +
    '<g class="sw__iskra"><path d="M32 0 L 35 7 L 42 8 L 36 12 L 38 19 L 32 15 L 26 19 L 28 12 L 22 8 L 29 7 Z" fill="#FFE27A" stroke="#E0A800" stroke-width=".8"/></g></svg>';

  function fajerwerk(kolor, kolor2) {
    var s = '', i, a;
    for (i = 0; i < 12; i++) { a = i * 30 * Math.PI / 180;
      s += '<line x1="' + (50 + 14 * Math.cos(a)).toFixed(1) + '" y1="' + (50 + 14 * Math.sin(a)).toFixed(1) +
        '" x2="' + (50 + 44 * Math.cos(a)).toFixed(1) + '" y2="' + (50 + 44 * Math.sin(a)).toFixed(1) + '"/>' +
        '<circle cx="' + (50 + 47 * Math.cos(a)).toFixed(1) + '" cy="' + (50 + 47 * Math.sin(a)).toFixed(1) + '" r="3"/>'; }
    return '<svg viewBox="0 0 100 100" class="sw__fajerwerk"><g stroke="' + kolor + '" fill="' + kolor2 + '" stroke-width="3.5" stroke-linecap="round">' + s + '</g></svg>';
  }

  var PISANKI = '<svg viewBox="0 0 100 80">' +
    '<defs><clipPath id="swJ1"><ellipse cx="36" cy="44" rx="17" ry="23"/></clipPath><clipPath id="swJ2"><ellipse cx="66" cy="48" rx="15" ry="20"/></clipPath></defs>' +
    '<g transform="rotate(-14 36 44)" class="sw__ruch sw__ruch--jajo">' +
    '<ellipse cx="36" cy="44" rx="17" ry="23" fill="#FFC928"/>' +
    '<g clip-path="url(#swJ1)"><rect x="10" y="36" width="52" height="11" fill="#D7263D"/>' +
    '<path d="M14 36 l5 -6 l5 6 l5 -6 l5 6 l5 -6 l5 6 l5 -6 l5 6" stroke="#2A7A3B" stroke-width="2.4" fill="none"/>' +
    '<path d="M14 47 l5 6 l5 -6 l5 6 l5 -6 l5 6 l5 -6 l5 6 l5 -6" stroke="#2A7A3B" stroke-width="2.4" fill="none"/>' +
    '<g fill="#fff"><circle cx="20" cy="41.5" r="1.8"/><circle cx="30" cy="41.5" r="1.8"/><circle cx="40" cy="41.5" r="1.8"/><circle cx="50" cy="41.5" r="1.8"/></g>' +
    '<g fill="#D7263D"><circle cx="36" cy="26" r="2.2"/><circle cx="36" cy="60" r="2.2"/></g></g>' +
    '<ellipse cx="30" cy="34" rx="4" ry="7" fill="#fff" opacity=".35"/></g>' +
    '<g transform="rotate(12 66 48)" class="sw__ruch sw__ruch--jajo2">' +
    '<ellipse cx="66" cy="48" rx="15" ry="20" fill="#2F7DE1"/>' +
    '<g clip-path="url(#swJ2)"><path d="M48 40 Q 57 34 66 40 T 84 40" stroke="#fff" stroke-width="3" fill="none"/>' +
    '<path d="M48 52 Q 57 46 66 52 T 84 52" stroke="#FFC928" stroke-width="3" fill="none"/>' +
    '<g fill="#fff"><circle cx="58" cy="60" r="1.6"/><circle cx="66" cy="62" r="1.6"/><circle cx="74" cy="60" r="1.6"/><circle cx="66" cy="31" r="1.8"/></g></g>' +
    '<ellipse cx="61" cy="40" rx="3.5" ry="6" fill="#fff" opacity=".35"/></g>' +
    '<g fill="#4CAF50"><path d="M4 78 Q 8 60 12 78 Z"/><path d="M10 78 Q 18 56 20 78 Z" fill="#3E9A45"/><path d="M80 78 Q 86 58 90 78 Z"/><path d="M88 78 Q 94 62 98 78 Z" fill="#3E9A45"/>' +
    '<path d="M2 80 Q 50 70 100 80 Z" fill="#5DBB63"/><path d="M44 80 Q 48 64 52 80 Z" fill="#3E9A45"/></g></svg>';

  /* gdzie co stoi: [lewo, góra, szerokość] w % rozmiaru logo; osobno dla tarczy (herb) i koła (Akademia) */
  var UKLAD = {
    bn: { tarcza: [[50, -19, 64, CZAPKA, 'sw__el--obr18']], kolo: [[44, -17, 62, CZAPKA, 'sw__el--obr18']] },
    niepodleglosc: { tarcza: [[56, 58, 52, KOTYLION]], kolo: [[70, 50, 40, KOTYLION]] },
    zaduszki: { tarcza: [[76, 58, 34, ZNICZ]], kolo: [[80, 44, 30, ZNICZ]] },
    nowyrok: {
      tarcza: [[54, -22, 50, CZAPECZKA, 'sw__el--obr18'], [-38, -6, 46, fajerwerk('#FFD54A', '#FFF3B0')], [92, 30, 40, fajerwerk('#FF5A6E', '#FFC2CB'), 'sw__el--pozniej']],
      kolo: [[58, -24, 40, CZAPECZKA, 'sw__el--obr18'], [-30, -10, 42, fajerwerk('#FFD54A', '#FFF3B0')], [90, 40, 36, fajerwerk('#FF5A6E', '#FFC2CB'), 'sw__el--pozniej']]
    },
    wielkanoc: { tarcza: [[38, 56, 84, PISANKI]], kolo: [[50, 54, 64, PISANKI]] }
  };
  if (!UKLAD[swieto]) return;

  var cele = document.querySelectorAll('.naglowek .logo img, .naglowek .logo > svg, .wybor__logo, .ak-hero__logo');
  Array.prototype.forEach.call(cele, function (el, nr) {
    var src = el.getAttribute('src') || '';
    var kolo = /akademia/i.test(src) || el.classList.contains('wybor__logo--okragle') || el.classList.contains('ak-hero__logo');
    var cs = getComputedStyle(el);
    var opak = document.createElement('span');
    opak.className = 'sw sw--' + swieto + ' sw--' + (kolo ? 'kolo' : 'tarcza');
    if (el.classList.contains('wybor__logo')) opak.className += ' sw--wybor';
    if (el.classList.contains('ak-hero__logo')) opak.className += ' sw--ak-hero';
    if (el.closest('.naglowek')) opak.className += ' sw--naglowek';
    opak.title = PODPIS[swieto] || '';
    ['order', 'justifySelf', 'alignSelf', 'gridColumn', 'gridRow'].forEach(function (w) { if (cs[w]) opak.style[w] = cs[w]; });
    el.parentNode.insertBefore(opak, el);
    opak.appendChild(el);
    var warstwa = document.createElement('span');
    warstwa.className = 'sw__warstwa'; warstwa.setAttribute('aria-hidden', 'true');
    UKLAD[swieto][kolo ? 'kolo' : 'tarcza'].forEach(function (x, i) {
      var s = document.createElement('span');
      s.className = 'sw__el' + (x[4] ? ' ' + x[4] : '');
      s.style.left = x[0] + '%'; s.style.top = x[1] + '%'; s.style.width = x[2] + '%';
      s.style.setProperty('--sw-i', i);
      s.innerHTML = x[3].replace(/id="sw(\w+)"/g, 'id="sw$1' + nr + '"').replace(/url\(#sw(\w+)\)/g, 'url(#sw$1' + nr + ')');
      warstwa.appendChild(s);
    });
    opak.appendChild(warstwa);
  });
  document.documentElement.setAttribute('data-swieto', swieto);
})();

/* =====================================================================
   POWIĘKSZENIE TEKSTU – jeden przycisk w nagłówku (dla słabowidzących)
   Kolejne kliknięcia: 100% → 125% → 150% → z powrotem 100%.
   Wybór zapamiętany w przeglądarce (działa na każdej podstronie).
   ===================================================================== */
(function () {
  'use strict';
  var html = document.documentElement;
  var POZIOMY = ['0', '1', '2'], PROC = { '0': '100%', '1': '125%', '2': '150%' };
  function poziom() { return html.getAttribute('data-czcionka') || '0'; }
  function opisz(b) {
    var p = poziom(), nast = POZIOMY[(POZIOMY.indexOf(p) + 1) % POZIOMY.length];
    b.setAttribute('aria-label', nast === '0'
      ? 'Przywróć zwykły rozmiar tekstu (teraz ' + PROC[p] + ')'
      : 'Powiększ tekst do ' + PROC[nast] + ' (teraz ' + PROC[p] + ')');
    b.title = nast === '0' ? 'Zwykły rozmiar tekstu' : 'Powiększ tekst';
    b.setAttribute('aria-pressed', p === '0' ? 'false' : 'true');
    b.setAttribute('data-poziom', p);
  }
  document.querySelectorAll('.czcionka-przycisk').forEach(function (b) {
    opisz(b);
    b.addEventListener('click', function () {
      var nast = POZIOMY[(POZIOMY.indexOf(poziom()) + 1) % POZIOMY.length];
      if (nast === '0') html.removeAttribute('data-czcionka'); else html.setAttribute('data-czcionka', nast);
      try { if (nast === '0') localStorage.removeItem('czcionka'); else localStorage.setItem('czcionka', nast); } catch (e) {}
      document.querySelectorAll('.czcionka-przycisk').forEach(opisz);
    });
  });
})();

/* =====================================================================
   STRONA JAK APLIKACJA – rejestracja service workera (działanie bez internetu)
   ===================================================================== */
(function () {
  'use strict';
  if (!('serviceWorker' in navigator) || location.protocol !== 'https:') return;
  var skrypt = document.currentScript || document.querySelector('script[src*="zasoby/main.js"]');
  if (!skrypt) return;
  var adres = new URL('../sw.js', skrypt.src);
  window.addEventListener('load', function () {
    navigator.serviceWorker.register(adres.href, { scope: new URL('../', skrypt.src).pathname }).catch(function () {});
  });
})();

/* =====================================================================
   RUCH PRZY PRZEWIJANIU – każdy element strony reaguje na przewijanie:
   wjeżdża, gdy pojawia się na ekranie (kolejno, z małym opóźnieniem),
   chowa się, gdy przewijasz z powrotem w górę, a duże napisy i zdjęcia
   lekko „płyną” (paralaksa). Wyłączone, gdy telefon ma ograniczone animacje.
   ===================================================================== */
(function () {
  'use strict';
  if (!('IntersectionObserver' in window)) return;
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var GRUPY = [
    ['ruch--lewo', 'main .sekcja__tytul, main .plakat__tytul, main .pm__imie, main .przed__tytul, main h2:not(.ukryte), main h3'],
    ['ruch--karta', 'main .mecz, main .zawodniczka, main .news, main .kafel, main .przed__karta, main .ostatni, main .kal-sub, main .pm__fakty > div, main .zapr, main .ciek, main [class*="sponsor"] a, main .sponsor, main .grupa, main .cennik > *, main .fakt'],
    ['ruch--obraz', 'main img, main .pm__zdjecie'],
    ['ruch--wiersz', 'main .tabela tbody tr, main li, main dl > div, main .pm__qa'],
    ['ruch--gora', 'main p, main .btn, main .btn-kal, main .filtry, main .terminarz-pasek, main table, main form, .stopka__kolumny > div, .stopka p']
  ];

  // stare „pojawianie się całych sekcji” zastępuje ruch pojedynczych elementów
  document.querySelectorAll('.pojaw').forEach(function (el) { el.classList.add('widoczne'); });
  var wszystkie = [];
  GRUPY.forEach(function (g) {
    document.querySelectorAll(g[1]).forEach(function (el) {
      if (el.classList.contains('ruch')) return;
      if (el.closest('.hero, .ak-hero, .wybor, .belka, .naglowek, .dolny-pasek, .zapowiedz, .zawodniczka__wiecej, .sw')) return;
      // nie animuj elementu, którego rodzic już jest animowany (np. akapit w karcie)
      var r = el.parentElement;
      while (r && r !== document.body) { if (r.classList.contains('ruch')) return; r = r.parentElement; }
      el.classList.add('ruch', g[0]);
      wszystkie.push(el);
    });
  });
  if (!wszystkie.length) return;
  document.documentElement.classList.add('ruch-gotowy');

  // kolejność „fali”: elementy pojawiające się razem dostają rosnące opóźnienie
  var kolejka = [], zegar = null;
  function pokaz() {
    kolejka.sort(function (a, b) {
      var ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
      return (ra.top - rb.top) || (ra.left - rb.left);
    }).forEach(function (el, i) {
      el.style.setProperty('--ruch-opoznienie', Math.min(i * 70, 420) + 'ms');
      el.classList.add('ruch--widoczny');
    });
    kolejka = []; zegar = null;
  }
  var obs = new IntersectionObserver(function (wpisy) {
    wpisy.forEach(function (w) {
      var el = w.target;
      if (w.isIntersecting) {
        kolejka.push(el);
        if (!zegar) zegar = requestAnimationFrame(pokaz);
      } else if (w.boundingClientRect.top > 0) {
        // element zszedł dołem ekranu (przewijanie w górę) – schowaj, żeby znów wjechał
        el.classList.remove('ruch--widoczny');
        el.style.removeProperty('--ruch-opoznienie');
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -6% 0px' });
  wszystkie.forEach(function (el) { obs.observe(el); });

  // paralaksa dużych napisów, numerów i zdjęć
  var plyn = Array.prototype.slice.call(document.querySelectorAll(
    'main .sekcja__tytul, main .plakat__tytul, main .pm__nr, main .zawodniczka__numer, .hero__postac-img, .ak-hero__logo, main .plakat__tlo'));
  plyn = plyn.filter(function (el) { return !el.closest('.zawodniczka__wiecej'); });
  if (!plyn.length) return;
  var czeka = false;
  function przesun() {
    czeka = false;
    var h = window.innerHeight;
    plyn.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.bottom < -100 || r.top > h + 100) return;
      var srodek = (r.top + r.height / 2 - h / 2) / h;           // -1 … 1
      var sila = el.classList.contains('hero__postac-img') ? -40 : el.matches('.pm__nr, .zawodniczka__numer') ? -60 : -24;
      el.style.setProperty('--plyn', (srodek * sila).toFixed(1) + 'px');
    });
  }
  window.addEventListener('scroll', function () { if (!czeka) { czeka = true; requestAnimationFrame(przesun); } }, { passive: true });
  window.addEventListener('resize', przesun);
  przesun();
})();
