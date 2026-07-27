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


if __name__ == "__main__":
    unittest.main()
