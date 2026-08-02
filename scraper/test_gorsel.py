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

    def test_hesaplayici_varsayilani_endeksle_AYNI(self):
        """Ayni sey icin iki farkli rakam olmamali.

        2026-07-28'de Yavuz bu hata sinifini bildirdi. Hesaplayici
        `varsayilan_dahil: false` bayragini YOK SAYIP her kalemi isaretli
        getiriyordu; endeks sayfasi ise aylik sarf kalemlerini toplamdan
        cikariyordu. Sonuc: bebek 34.829 (endeks) vs 35.394 (hesaplayici),
        kedi 5.267 vs 6.597. Ikisi de "orta segment" diyordu.

        Bebek vertikali yayina gireli beri canlidaydi ve kimse fark
        etmemisti - cunku iki sayfaya ayni anda bakmak gerekiyor.

        ARAC HARIC: oradaki hesaplayici arac fiyatini degil SAHIP OLMA
        maliyetini (MTV, noter, kasko) hesapliyor - farkli sey olcuyor,
        farkli rakam vermesi dogru."""
        import json
        import sayfa_uret as su
        for vertikal, conf in su.VERTIKALLER.items():
            if not conf.get("hesaplayici_var", True) or vertikal == "arac":
                continue
            dosya = SITE / "veri" / f"{vertikal}.json"
            if not dosya.exists():
                continue
            veri = json.loads(dosya.read_text(encoding="utf-8"))
            beklenen, _ = su.ornek_toplam_hesapla(
                conf, veri.get("kalemler") or {},
                conf.get("olcek_varsayilan", 1), "orta")
            s = self._ac(f"/{vertikal}/hesaplayici/")
            s.eval_on_selector("#hesaplayici-form", "f => f.requestSubmit()")
            s.wait_for_timeout(400)
            metin = s.inner_text("#sonuc-toplam-deger")
            s.close()
            bulunan = int(metin.replace(" TL", "").replace(".", ""))
            self.assertEqual(
                bulunan, beklenen,
                f"{vertikal}: hesaplayici {bulunan:,} diyor, endeks {beklenen:,} - "
                f"ayni sey icin iki farkli rakam.".replace(",", "."))

    def test_veri_yuklenmeden_rakam_gosterilmiyor(self):
        """GERCEK BUG (2026-07-28 son denetim): yavas baglantida
        "Hesapla"ya fetch bitmeden basan kullanici GUVENILIR GORUNEN
        YANLIS bir rakam goruyordu.

        Cogu vertikalde "0 TL"; DUGUNDE ISE 28.500 TL - yalnizca
        tahmini kalemlerin toplami, cunku onlarin degeri JS'e gomulu
        ve veri beklemiyor. Ikincisi daha tehlikeli: 0 TL bariz
        yanlisken 28.500 makul goruntyor.

        Bu, projenin her yerde uyguladigi kuralin ihlaliydi: cevabi
        olmayan durumda uydurma sayi gosterme. Artik veri yuklenmeden
        sonuc kutusu ACILMIYOR, bunun yerine acik bir mesaj cikiyor."""
        for vertikal, conf in __import__("sayfa_uret").VERTIKALLER.items():
            if not conf.get("hesaplayici_var", True):
                continue
            dosya = SITE / vertikal / "hesaplayici" / "index.html"
            if not dosya.exists():
                continue
            # ARAC HARIC ve bu DOGRU: arac hesaplayicisi veri CEKMIYOR -
            # MTV, noter ve harclari `arac-ek-maliyetler.js` icindeki
            # resmi sabitlerden aliyor. Beklemesi gereken bir sey yok,
            # sonucu hemen gostermesi dogru davranis.
            if "veriKalemleri" not in dosya.read_text(encoding="utf-8"):
                continue
            yol = f"/{vertikal}/hesaplayici/"
            s = self.tarayici.new_page(viewport={"width": 390, "height": 900})
            try:
                # Veri istegini bilerek dusuruyoruz - yavas/kopuk baglanti
                s.route("**/veri/*.json", lambda r: r.abort())
                s.goto(f"http://127.0.0.1:{self.port}{yol}",
                       wait_until="domcontentloaded")
                s.eval_on_selector("#hesaplayici-form", "f => f.requestSubmit()")
                s.wait_for_timeout(250)
                gizli = s.eval_on_selector("#sonuc-kutu", "e => e.hidden")
                self.assertTrue(
                    gizli, f"{yol}: veri yokken sonuc kutusu ACILIYOR - "
                           f"uydurma rakam gosteriliyor")
            finally:
                s.close()

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


    def test_paylasilan_link_ayni_hesabi_uretiyor(self):
        """Paylasilan sonuc linki ACILDIGINDA ayni rakami vermeli.

        2026-08-02'de eklendi. Ilk yazimda `_urldenUygula()` fetch'ten
        ONCE cagriliyordu; "veri yuklenmeden rakam gosterme" korumasi
        devreye girip paylasilan HER link "veri yuklenemedi" mesajiyla
        aciliyordu. Yani ozellik sessizce hic calismiyordu.
        """
        ctx = self.tarayici.new_context(viewport={"width": 1280, "height": 900})
        try:
            sf = ctx.new_page()
            sf.goto(f"http://127.0.0.1:{self.port}/bebek/hesaplayici/",
                    wait_until="networkidle")
            sf.wait_for_timeout(700)
            sf.click('input[name="segment"][value="luks"]')
            sf.evaluate("document.getElementById('hesaplayici-form').requestSubmit()")
            sf.wait_for_timeout(400)
            beklenen = sf.evaluate(
                "document.getElementById('sonuc-toplam-deger').textContent")
            sf.click("#linki-kopyala")
            sf.wait_for_timeout(300)
            url = sf.url
            self.assertIn("segment=luks", url, "secim URL'e yazilmadi")

            yeni = ctx.new_page()
            yeni.goto(url, wait_until="networkidle")
            yeni.wait_for_timeout(1400)
            self.assertFalse(
                yeni.evaluate("document.getElementById('sonuc-kutu').hidden"),
                "paylasilan link acildiginda sonuc gosterilmedi")
            self.assertEqual(
                beklenen,
                yeni.evaluate("document.getElementById('sonuc-toplam-deger').textContent"),
                "paylasilan link FARKLI rakam uretti")
        finally:
            ctx.close()

if __name__ == "__main__":
    unittest.main()
