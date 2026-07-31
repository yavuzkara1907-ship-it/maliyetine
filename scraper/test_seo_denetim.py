# -*- coding: utf-8 -*-
"""Uretilen SITENIN tamamina karsi calisan SEO/GEO denetimi.

NEDEN AYRI BIR TEST DOSYASI: diger testler tek tek fonksiyonlari
dogruluyor. Bu dosya URETILMIS SITEYE bakiyor - cunku bu projede
bulunan en sinsi hatalar birim testlerinden gecen ama SAYFA
SEVIYESINDE ortaya cikan hatalardi:

  - FAQ semasi kalem sayfalarinda gorunur icerikle eslesiyordu ama
    HUB sayfalarinda 14 soru yalnizca JSON-LD'de duruyordu (Google'in
    yapilandirilmis veri politikasi ihlali). Bir sayfa tipinde
    duzeltip hepsinde duzeldigini varsaymak.
  - `/rehber/` sitemap'te vardi ama hicbir sayfadan link almiyordu.
  - Baslik hiyerarsisinde h1 -> h3 atlamasi.

Bu testler gercek dosyalari okur; site uretilmemisse atlanir.
"""

from __future__ import annotations

import json

import re
import unittest
from pathlib import Path

import sayfa_uret

SITE = Path(__file__).parent.parent


def _sayfalar() -> list[Path]:
    return sorted(SITE.glob("**/index.html"))


def _oku(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _govde(h: str) -> str:
    return re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)


def _metin(h: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", _govde(h)))


def _yol(p: Path) -> str:
    return str(p.relative_to(SITE))


class SiteDenetimi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sayfalar = _sayfalar()
        if not cls.sayfalar:
            raise unittest.SkipTest("site henuz uretilmemis")

    # ---------------- EN KRITIK ----------------
    def test_faq_semasindaki_her_soru_sayfada_GORUNUR(self):
        """Google: "FAQ icerigi kullaniciya gorunur olmali." Semaya soru
        koyup sayfada gostermemek politika ihlali - ve AI motorlari da
        sayfa metnini okuyor, yalnizca semaya guvenmek GEO kaybi."""
        for p in self.sayfalar:
            h = _oku(p)
            if '"FAQPage"' not in h:
                continue
            t = _metin(h)
            for blok in re.findall(r'application/ld\+json">(.*?)</script>', h, re.S):
                try:
                    veri = json.loads(blok)
                except json.JSONDecodeError:
                    self.fail(f"{_yol(p)}: JSON-LD parse edilemedi")
                for o in (veri.get("@graph") or [veri]):
                    if o.get("@type") != "FAQPage":
                        continue
                    for q in o.get("mainEntity") or []:
                        ad = q["name"]
                        self.assertIn(
                            ad[:30], t,
                            f"{_yol(p)}: '{ad[:50]}' semada var ama sayfada GORUNMUYOR",
                        )

    def test_yetim_sayfa_yok(self):
        """Sitemap'te olup hicbir sayfadan link almayan sayfa, arama
        motoru icin cikmaz sokak; ic link akisi da almaz."""
        sm = (SITE / "sitemap.xml")
        if not sm.exists():
            self.skipTest("sitemap yok")
        url = {
            u.replace("https://maliyetine.com.tr/", "").strip("/")
            for u in re.findall(r"<loc>(.*?)</loc>", sm.read_text(encoding="utf-8"))
        }
        gelen = set()
        for p in self.sayfalar:
            for href in re.findall(r'href="(/[^"#?]*)"', _oku(p)):
                gelen.add(href.strip("/"))
        yetim = sorted(u for u in url if u and u not in gelen)
        self.assertEqual(yetim, [], f"ic link almayan sayfa(lar): {yetim}")

    def test_baslik_hiyerarsisinde_atlama_yok(self):
        """h1 -> h3 atlamasi hem erisilebilirlik hem icerik ayristirma
        acisindan sorun; Google baslik yapisini icerik hiyerarsisi
        olarak okuyor."""
        for p in self.sayfalar:
            s = [int(m) for m in re.findall(r"<h([1-6])[^>]*>", _govde(_oku(p)))]
            for a, b in zip(s, s[1:]):
                self.assertLessEqual(
                    b, a + 1, f"{_yol(p)}: h{a} -> h{b} atlamasi")

    # ---------------- TEMEL SEO ----------------
    def test_her_sayfada_tek_h1(self):
        for p in self.sayfalar:
            n = len(re.findall(r"<h1[^>]*>", _oku(p)))
            self.assertEqual(n, 1, f"{_yol(p)}: {n} adet h1")

    def test_canonical_kendine_isaret_ediyor(self):
        for p in self.sayfalar:
            m = re.search(r'<link rel="canonical" href="([^"]+)"', _oku(p))
            self.assertIsNotNone(m, f"{_yol(p)}: canonical yok")
            dizin = str(p.parent.relative_to(SITE))
            bek = "https://maliyetine.com.tr/" + ("" if dizin == "." else dizin + "/")
            self.assertEqual(m.group(1), bek, f"{_yol(p)}: canonical yanlis")

    def test_title_ve_description_benzersiz(self):
        for alan, desen in (("title", r"<title>(.*?)</title>"),
                            ("description", r'<meta name="description" content="([^"]*)"')):
            gorulen = {}
            for p in self.sayfalar:
                m = re.search(desen, _oku(p), re.S)
                self.assertIsNotNone(m, f"{_yol(p)}: {alan} yok")
                d = m.group(1).strip()
                self.assertNotIn(d, gorulen,
                                 f"{alan} tekrar: {_yol(p)} = {gorulen.get(d)}")
                gorulen[d] = _yol(p)

    def test_title_60_karakteri_asmiyor(self):
        for p in self.sayfalar:
            t = re.search(r"<title>(.*?)</title>", _oku(p), re.S).group(1).strip()
            self.assertLessEqual(len(t), 62, f"{_yol(p)}: title {len(t)} karakter")

    def test_paylasim_etiketleri_tam(self):
        for p in self.sayfalar:
            h = _oku(p)
            for e in ("og:title", "og:image", "og:image:width", "og:image:height",
                      "og:url", "og:locale", "twitter:card"):
                self.assertIn(e, h, f"{_yol(p)}: {e} yok")

    def test_analitik_her_sayfada(self):
        for p in self.sayfalar:
            self.assertIn("G-JP07XQLV0L", _oku(p), f"{_yol(p)}: analitik yok")

    def test_kirik_ic_link_yok(self):
        for p in self.sayfalar:
            for href in re.findall(r'href="(/[^"#?]*)"', _oku(p)):
                if "'" in href or "+" in href:
                    continue  # JS sablon dizesi
                yol = href.lstrip("/")
                hedef = SITE / ((yol + "index.html") if href.endswith("/") or href == "/" else yol)
                self.assertTrue(hedef.exists(), f"{_yol(p)}: kirik link {href}")

    def test_jenerik_anchor_metni_yok(self):
        """"Buraya tiklayin" hem erisilebilirlik hem SEO acisindan zayif."""
        yasak = {"buraya", "tıkla", "tıklayın", "buraya tıklayın", "link",
                 "daha fazla", "devamı", "oku"}
        for p in self.sayfalar:
            for m in re.finditer(r"<a [^>]*href=[^>]*>(.*?)</a>", _oku(p), re.S):
                a = re.sub(r"<[^>]+>", "", m.group(1)).strip().lower()
                self.assertNotIn(a, yasak, f"{_yol(p)}: jenerik anchor '{a}'")

    # ---------------- GEO ----------------
    def test_endeks_sayfalarinda_cevap_blogu_var(self):
        """GEO'nun kalbi: ilk 40-60 kelimede alintilanabilir cevap."""
        for p in self.sayfalar:
            dizin = str(p.parent.relative_to(SITE))
            # Hesaplayici ve dizin sayfalari haric - onlar arac/liste
            if any(x in dizin for x in ("hesaplayici", "metodoloji")) or dizin in (
                    ".", "rehber", "hesap", "veri", "sss", "hakkimizda", "iletisim"):
                continue
            self.assertIn("cevap-blok", _oku(p), f"{_yol(p)}: cevap blogu yok")

    def test_rakamlar_ham_HTMLde(self):
        """AI motorlarinin cogu JavaScript calistirmiyor. Rakam yalnizca
        JS ile geliyorsa GPTBot/ClaudeBot icin sayfa BOS. Rakip
        yenibirhesap'i gorunmez yapan sey tam olarak bu."""
        for v in ("dugun", "ev-kurma", "okul", "bebek", "arac"):
            p = SITE / v / "index.html"
            if not p.exists():
                continue
            t = _metin(_oku(p))
            self.assertRegex(t, r"[0-9]{1,3}\.[0-9]{3} TL",
                             f"{v}: ham HTML'de TL rakami yok")

    def test_ai_botlari_engellenmiyor(self):
        """Projenin temel stratejisi AI motorlarinda alintilanmak."""
        r = SITE / "robots.txt"
        if not r.exists():
            self.skipTest("robots.txt yok")
        m = r.read_text(encoding="utf-8")
        self.assertNotIn("Disallow: /", m, "robots.txt genel Disallow iceriyor")
        for bot in ("GPTBot", "ClaudeBot", "PerplexityBot"):
            self.assertIn(bot, m, f"{bot} robots.txt'te tanimli degil")
    def test_yayindaki_rakamlar_GUNCEL_veriyle_ayni(self):
        """Yayindaki her toplam, SU ANKI veriden turetilebilir olmali.

        2026-07-28'de Yavuz gercek bir tutarsizlik yakaladi: bir sayfa
        411.670 TL derken digeri 406.375 TL diyordu ve IKISI DE
        "2026-07-26" tarihini gosteriyordu.

        KOK NEDEN - yapisal degil ZAMANSAL: ana sayfa ve endeks sayfasi
        ayni fonksiyondan (`vertikal_ozeti` -> `ornek_toplam_hesapla`)
        beslendigi icin ayni anda uretildiklerinde ayrisamazlar. Ama
        26 Temmuz 23:09'da motor AYNI GUN ikinci kez kostu ve o gunun
        olcumunun uzerine yazdi (gelinlik 8.699 -> 18.172, salon
        1.100 -> 1.000). Sayfalarin bir kismi eski veriyle uretilmis
        halde kalirsa iki farkli rakam ayni tarih etiketiyle yayinda
        durur - kullanici hangisine guvenecegini bilemez.

        Bu test yayindaki rakamlari veriye karsi dogruluyor: veri
        degisip sayfalar yeniden uretilmezse PATLAR.
        """
        for vertikal, conf in sayfa_uret.VERTIKALLER.items():
            dosya = SITE / "veri" / f"{vertikal}.json"
            sayfa = SITE / vertikal / "index.html"
            if not (dosya.exists() and sayfa.exists()):
                continue
            veri = json.loads(dosya.read_text(encoding="utf-8"))
            toplam, _ = sayfa_uret.ornek_toplam_hesapla(
                conf, veri.get("kalemler") or {},
                conf.get("olcek_varsayilan", 1), "orta")
            if not toplam:
                continue
            beklenen = f"{toplam:,}".replace(",", ".")
            self.assertIn(beklenen, _govde(_oku(sayfa)),
                          f"{vertikal}/index.html guncel veriden ({beklenen} TL) "
                          f"farkli bir toplam gosteriyor - sayfa bayat.")
            # Ana sayfa da AYNI rakami gostermek zorunda
            self.assertIn(beklenen, _govde(_oku(SITE / "index.html")),
                          f"ana sayfa {vertikal} icin {beklenen} TL gostermiyor - "
                          f"iki sayfa ayni seye farkli deger veriyor.")

    def test_uretilen_sayfalar_veriden_YENI(self):
        """Sayfa, besledigi veriden eski olamaz.

        Yukaridaki tutarsizligin mekanik kontrolu: veri dosyasi
        sayfadan sonra degismisse sayfa bayattir ve rakam yanlistir."""
        import os
        for vertikal in sayfa_uret.VERTIKALLER:
            veri = SITE / "veri" / f"{vertikal}.json"
            sayfa = SITE / vertikal / "index.html"
            if not (veri.exists() and sayfa.exists()):
                continue
            self.assertGreaterEqual(
                os.path.getmtime(sayfa), os.path.getmtime(veri) - 1,
                f"{vertikal}/index.html verisinden ESKI - yeniden uretilmeli")

    def test_global_menu_her_sayfada_ayni(self):
        """2026-07-27 TASARIM DENETIMI - Yavuz: "google indekslemezse
        hesaplayicilar da kayip. ne headerda var ne sitede gorunur."

        Olculdu: ust menude yalnizca 5 vertikal vardi; 20 hesaplayici,
        8 rehber ve veri merkezi HICBIR sayfanin header'indan
        erisilemiyordu. Ic link, arama motoru icin kesif yolunun
        kendisi - header'da olmayan bolum sitenin uzak kosesinde kalir.

        Bu test menunun her sayfada AYNI oldugunu dogruluyor; elle
        yazilan sayfalar (hesaplayici, metodoloji, hakkimizda) daha once
        eski menude kalmisti."""
        beklenen = None
        for p in self.sayfalar:
            m = re.search(r'<nav class="ust-menu">(.*?)</nav>', _oku(p), re.S)
            self.assertIsNotNone(m, f"{_yol(p)}: ust menu yok")
            ogeler = tuple(re.findall(r">([^<>]+)</a>", m.group(1)))
            if beklenen is None:
                beklenen = ogeler
                self.assertGreaterEqual(len(ogeler), 7,
                                        f"menu cok dar: {ogeler}")
            self.assertEqual(ogeler, beklenen, f"{_yol(p)}: menu farkli")

    def test_hesaplayicilar_ve_rehber_menude(self):
        """Sitenin en genis iki bolumu menude gorunmek ZORUNDA."""
        h = _oku(self.sayfalar[0])
        menu = re.search(r'<nav class="ust-menu">(.*?)</nav>', h, re.S).group(1)
        for beklenen in ('href="/hesap/"', 'href="/rehber/"', 'href="/veri/"'):
            self.assertIn(beklenen, menu, f"menude {beklenen} yok")


    def test_ondalik_ayraci_turkce(self):
        """Uretilen sayfalarda ondalik NOKTAYLA yazilmaz.

        2026-08-01'de bulundu: `{kat:.1f}` dogrudan kullanildigi icin
        107 sayfa "2.1 kat", "28.5 kat" yaziyordu. Ayni cumlede para
        tutari `_para()` ile "29.382 TL" seklinde -- yani noktanin bir
        yerde binlik, bir yerde ondalik ayraci oldugu iki bicim yan
        yana duruyordu. `sayfa_uret._kat()` bunu tek yerden cozuyor.
        """
        desen = re.compile(r"\d+\.\d\s*(kat|×)")
        hatali = []
        for yol in self.sayfalar:
            m = desen.search(_metin(_oku(yol)))
            if m:
                hatali.append("{}: {!r}".format(yol, m.group(0)))
        self.assertEqual([], hatali,
                         "Turkce ondalik ayraci virgul olmali: {}".format(hatali[:5]))

    def test_urun_semasinda_UYDURMA_puan_ve_yorum_YOK(self):
        """aggregateRating / review BILEREK yok - Search Console bunlari
        "eksik alan" diye bildiriyor ama ikisi de istege bagli.

        Doldurmak icin ya olmayan yorumu isaretlememiz ya kendi
        urunumuze kendi puanimizi vermemiz gerekirdi. Ikisi de Google'in
        yapilandirilmis veri politikasina aykiri ve manuel isleme aday;
        birkac yildiz icin alinacak risk degil. Ustelik biz urun
        DEGERLENDIRMIYORUZ, fiyat olcuyoruz.

        `availability` de ayni sebeple yok: hicbir sey satmiyoruz ve
        stok durumu olcmuyoruz. "InStock" dogrulanmamis bir iddiaydi.

        Bu test kararin sessizce bozulmasini engelliyor. Gercekten
        yorum toplamaya baslanirsa once o altyapi kurulur, sonra bu
        test bilerek guncellenir.
        """
        yasak = ("aggregateRating", "reviewCount", "ratingValue", "availability")
        hatali = []
        for yol in self.sayfalar:
            for blok in re.findall(r'application/ld\+json">(.*?)</script>',
                                   _oku(yol), re.S):
                try:
                    d = json.loads(blok)
                except ValueError:
                    continue
                ham = json.dumps(d, ensure_ascii=False)
                for alan in yasak:
                    if '"{}"'.format(alan) in ham:
                        hatali.append("{}: {}".format(yol, alan))
        self.assertEqual([], hatali,
                         "Olcmedigimiz alan semaya girmis: {}".format(hatali[:5]))

if __name__ == "__main__":
    unittest.main()
