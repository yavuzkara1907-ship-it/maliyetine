# -*- coding: utf-8 -*-
"""Senaryo sayfasi testleri - ince/kopya icerik kirmizi cizgisi."""
import hashlib
import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import sayfa_uret as su
import senaryo


DUGUN = {
    "guncelleme_tarihi": "2026-08-05",
    "kalemler": {
        "gelinlik": {"genel_medyan": 9000, "toplam_urun": 20,
                     "segmentler": {"dusuk": {"medyan": 5000}, "orta": {"medyan": 9000},
                                    "luks": {"medyan": 15000}}},
        "salon-yemekli": {"genel_medyan": 1000, "toplam_urun": 11,
                          "segmentler": {"dusuk": {"medyan": 700}, "orta": {"medyan": 1000},
                                         "luks": {"medyan": 2000}}},
    },
}


class OlcekSenaryosuTesti(unittest.TestCase):

    def test_olcek_toplami_dogru_carpilir(self):
        """Kisi basi kalem olcekle carpilmali. Tahmini kalemler de toplama
        girdigi icin beklenen deger gercek hesapla karsilastiriliyor."""
        conf = su.VERTIKALLER["dugun"]
        for olcek in (100, 200, 300):
            s = next(x for x in senaryo.OLCEK_SENARYOLARI["dugun"] if x["olcek"] == olcek)
            html = senaryo.olcek_sayfasi("dugun", s, DUGUN, "2026-08-05")
            self.assertIsNotNone(html)
            beklenen, _ = su.ornek_toplam_hesapla(
                conf, DUGUN["kalemler"], olcek=olcek, segment="orta")
            self.assertIn(su._para(beklenen), html)
            # Kisi basi bilesen olcekle dogru orantili artmali
            self.assertIn(su._para(1000 * olcek), html)

    def test_her_olcek_farkli_rakam_uretir(self):
        """Ayni metnin sayi degistirilmis kopyasi olmamali - ama rakam
        gercekten farkli olmali; ayni cikarsa sayfalar ince icerik olur."""
        rakamlar = set()
        for s in senaryo.OLCEK_SENARYOLARI["dugun"]:
            html = senaryo.olcek_sayfasi("dugun", s, DUGUN, "2026-08-05")
            m = re.search(r'<strong>([\d.]+ TL)</strong>', html)
            rakamlar.add(m.group(1))
        self.assertEqual(len(rakamlar), 3)

    def test_kisi_basi_sabit_kirilimi_tutarli(self):
        s = senaryo.OLCEK_SENARYOLARI["dugun"][0]  # 100 kisilik
        html = senaryo.olcek_sayfasi("dugun", s, DUGUN, "2026-08-05")
        self.assertIn(su._para(100_000), html)  # kisi basi toplam
        self.assertIn(su._para(9000), html)     # sabit kalem

    def test_gercek_olcum_yoksa_sayfa_uretilmez(self):
        """Yalnizca tahmini kalemlerle sayfa uretmek yaniltici olur:
        tahminler sabit oldugu icin her senaryoda AYNI rakam cikar."""
        s = senaryo.OLCEK_SENARYOLARI["dugun"][0]
        self.assertIsNone(senaryo.olcek_sayfasi("dugun", s, {"kalemler": {}}, "2026-08-05"))
        tek_kalem = {"kalemler": {"gelinlik": {"segmentler": {"orta": {"medyan": 9000}}}}}
        self.assertIsNone(senaryo.olcek_sayfasi("dugun", s, tek_kalem, "2026-08-05"))


class GrupSenaryosuTesti(unittest.TestCase):

    def test_yetersiz_kalemde_sayfa_uretilmez(self):
        """3'ten az kalemle 'grup butcesi' sayfasi ince icerik olur."""
        s = senaryo.GRUP_SENARYOLARI["ev-kurma"][0]
        veri = {"kalemler": {"buzdolabi": {"segmentler": {"orta": {"medyan": 30000}}}}}
        self.assertIsNone(senaryo.grup_sayfasi("ev-kurma", s, veri, "2026-08-05"))

    def test_gercek_veriyle_uretilenler_benzersiz(self):
        """Uretilmis sayfalarin govdesi birbirinin kopyasi olmamali."""
        govdeler = []
        for v, slug in senaryo.tum_slugler():
            p = su.SITE_KOK / su.VERTIKALLER[v]["yol"] / slug / "index.html"
            if p.exists():
                govdeler.append(hashlib.md5(p.read_text(encoding="utf-8").encode()).hexdigest())
        self.assertTrue(govdeler, "senaryo sayfasi uretilmemis")
        self.assertEqual(len(set(govdeler)), len(govdeler), "kopya sayfa var")

    def test_uretilen_sayfalarda_faq_ve_breadcrumb(self):
        for v, slug in senaryo.tum_slugler():
            p = su.SITE_KOK / su.VERTIKALLER[v]["yol"] / slug / "index.html"
            if not p.exists():
                continue
            h = p.read_text(encoding="utf-8")
            graf = json.loads(
                re.search(r'<script type="application/ld\+json">(.*?)</script>', h, re.S).group(1)
            )["@graph"]
            tipler = {g["@type"] for g in graf}
            self.assertIn("FAQPage", tipler, slug)
            self.assertIn("BreadcrumbList", tipler, slug)
