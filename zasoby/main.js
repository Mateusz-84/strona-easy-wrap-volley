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
    fetch('https://abacus.jasoncameron.dev/hit/' + wysw.dataset.wyswietlenia)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d || typeof d.value !== 'number') return;
        wysw.querySelector('[data-wyswietlenia-liczba]').textContent = d.value.toLocaleString('pl-PL');
        wysw.title = 'Wyświetlenia strony';
        wysw.hidden = false;
      })
      .catch(function () {});
  }

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
        return '<div class="kal__dzien-tyg" role="columnheader">' + d + '</div>';
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
