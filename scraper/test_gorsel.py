# -*- coding: utf-8 -*-
"""Gercek tarayicida gorsel/duzen denetimi (Playwright).

NEDEN AYRI VE NEDEN GERCEK TARAYICI: bu projede tasarim hatalari
DAIMA ancak sayfaya bakinca ortaya cikti - CSS'i okuyarak degil:

  - Arac hesaplayicisinda `step="50000"` formu sessizce blokluyordu.
  - YouTube hesabinda opsiyonel alandaki `required` ayni seyi yapti.
  - 2026-07-27: menu 5 ogeden 8'e cikinca 673 px'e ulasti ve
    561-900 px arasindaki HER genislikte sayfa yatay tasti. Mobil
    (390) ve masaustu (1440) test ediliyordu, ARADAKI genislikler
    hic bakilmamisti - tablet, katlanir telefon, kucuk pencere.

DERS: kirilim noktasi "telefon/masaustu" diye degil, ICERIGIN GERCEK
GENISLIGINE gore secilir; ve dogrulama BIRDEN COK genislikte yapilir.

Test yerel bir HTTP sunucusu baslatir. Playwright yoksa atlanir.
"""

from __future__ import annotations

import http.server
import socketserver
import threading
import unittest
from pathlib import Path

SITE = Path(__file__).parent.parent

# Gercek cihaz genislikleri: kucuk telefondan genis masaustune.
# 768 ve 834 BILINCLI - tablet araligi bu projede bir kez korlukten
# atlandi ve her sayfa tasiyordu.
GENISLIKLER = [320, 360, 390, 414, 480, 560, 600, 700, 768, 834, 900, 1024, 1280, 1440]

SAYFALAR = ["/", "/ev-kurma/", "/hesap/", "/hesap/kidem-tazminati-hesaplama/",
            "/rehber/", "/dugun/hesaplayici/", "/veri/", "/sss/",
            "/ev-kurma/buzdolabi-fiyatlari/"]


class _Sunucu(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(SITE), **k)

    def log_message(self, *a):
        pass


class GorselDenetim(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest("playwright kurulu degil")
        if not (SITE / "index.html").exists():
            raise unittest.SkipTest("site uretilmemis")
        cls._httpd = socketserver.TCPServer(("127.0.0.1", 0), _Sunucu)
        cls.port = cls._httpd.server_address[1]
        threading.Thread(target=cls._httpd.serve_forever, daemon=True).start()
        cls._pw = sync_playwright().start()
        cls.tarayici = cls._pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "tarayici"):
            cls.tarayici.close()
            cls._pw.stop()
            cls._httpd.shutdown()

    def _ac(self, yol, genislik=390, tema="light"):
        s = self.tarayici.new_page(viewport={"width": genislik, "height": 900},
                                   color_scheme=tema)
        s.goto(f"http://127.0.0.1:{self.port}{yol}", wait_until="load")
        return s

    def test_hicbir_genislikte_yatay_tasma_yok(self):
        """EN KRITIK: yatay kaydirma mobilde sayfayi kullanilamaz yapar
        ve Google'in mobil kullanilabilirlik sinyallerinden biridir.

        Hiz notu: her genislik icin YENI SAYFA acmak yerine tek sayfayi
        yeniden boyutlandiriyoruz (126 sayfa yuklemesi ~2 dk suruyordu)."""
        s = self.tarayici.new_page(viewport={"width": 390, "height": 900})
        try:
            for yol in SAYFALAR:
                s.goto(f"http://127.0.0.1:{self.port}{yol}", wait_until="load")
                for g in GENISLIKLER:
                    s.set_viewport_size({"width": g, "height": 900})
                    tasma = s.evaluate(
                        "document.documentElement.scrollWidth > window.innerWidth + 1")
                    self.assertFalse(tasma, f"{yol} @ {g}px: yatay tasma")
        finally:
            s.close()

    def test_menu_her_genislikte_tam(self):
        """Menu daralinca oge GIZLENMEMELI - kaydirilabilir olmali."""
        for g in (320, 768, 1440):
            s = self._ac("/", g)
            n = s.eval_on_selector_all(".ust-menu a", "e => e.length")
            s.close()
            self.assertGreaterEqual(n, 7, f"{g}px: menude {n} oge")

    def test_konsol_hatasi_yok(self):
        for yol in SAYFALAR:
            s = self._ac(yol)
            hatalar = []
            s.on("pageerror", lambda e: hatalar.append(str(e)))
            s.on("console", lambda m: hatalar.append(m.text) if m.type == "error" else None)
            s.reload(wait_until="load")
            s.close()
            self.assertEqual(hatalar, [], f"{yol}: konsol hatasi")

    def test_karanlik_modda_da_tasma_yok(self):
        for yol in ("/", "/hesap/"):
            s = self._ac(yol, 390, "dark")
            tasma = s.evaluate(
                "document.documentElement.scrollWidth > window.innerWidth + 1")
            s.close()
            self.assertFalse(tasma, f"{yol} karanlik mod: tasma")

    def test_dokunma_hedefleri_yeterli(self):
        """Kontroller mobilde en az 40 px olmali (WCAG hedef boyutu).

        DIKKAT - ilk yazimda bu test YANLIS olceyordu: `input` ogesinin
        kendi yuksekligine bakiyordu. Bir onay kutusu dogal olarak 18 px'tir;
        asil dokunma hedefi onu SARAN ETIKET'tir. Etiket olculunce
        cogunun 41 px oldugu, yalnizca segment seciminin 23 px kaldigi
        gorundu - gercek sorun oydu ve duzeltildi."""
        for yol in ("/hesap/kidem-tazminati-hesaplama/", "/dugun/hesaplayici/"):
            s = self._ac(yol, 390)
            kucuk = s.evaluate("""() => [...document.querySelectorAll(
                'input, select, button')].map(e => {
                  const hedef = e.closest('label') || e;
                  const r = hedef.getBoundingClientRect();
                  return {ad: e.id || e.name || e.tagName, h: Math.round(r.height)};
                }).filter(x => x.h > 0 && x.h < 40)""")
            s.close()
            self.assertEqual(kucuk, [], f"{yol}: kucuk dokunma hedefi {kucuk}")


if __name__ == "__main__":
    unittest.main()
