# -*- coding: utf-8 -*-
"""Rakipten uyarlanan marka/kategori/degisim kesif yuzeyi testleri."""

import html
import json
import re
import unittest

import kesif_yuzeyi as ky


class KesifYuzeyiTesti(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.fiyat = json.loads(ky.fg.ENVANTER_DOSYASI.read_text(encoding="utf-8"))
        cls.gozlemler = cls.fiyat["gozlemler"]

    def test_markalar_buyuk_kucuk_harfle_bolunmez_ve_sahte_ad_acmaz(self):
        gruplar = ky.marka_gruplari(self.gozlemler)
        self.assertIn("bosch", gruplar)
        self.assertGreaterEqual(len(gruplar["bosch"]["urunler"]), 2)
        for yasak in ky.SAHTE_MARKA_BASLANGICLARI:
            self.assertNotIn(yasak, gruplar)

    def test_kategori_sayfasi_gercek_urunleri_ve_siniri_tasir(self):
        grup = ky.kategori_gruplari(self.gozlemler)["buzdolabi"]
        sayfa = ky._kategori_sayfasi(grup)
        self.assertIn(f"{len(grup['urunler'])} kaynak gözlemi", sayfa)
        self.assertIn("tüm pazarın eksiksiz ürün kataloğu değildir", sayfa)
        self.assertIn('/fiyat/', sayfa)

    def test_arac_karsilastirmalari_esigi_gecer_ve_yollari_benzersizdir(self):
        karsilastirmalar = ky.arac_karsilastirmalari(self.gozlemler)
        self.assertGreaterEqual(len(karsilastirmalar), 200)
        self.assertEqual(len(karsilastirmalar), len({x["slug"] for x in karsilastirmalar}))
        for kayit in karsilastirmalar:
            self.assertGreaterEqual(len(kayit["a"]), ky.ARAC_KARSILASTIRMA_ESIGI)
            self.assertGreaterEqual(len(kayit["b"]), ky.ARAC_KARSILASTIRMA_ESIGI)

    def test_karsilastirma_niyeti_cevaplanir_ve_siniri_aciklar(self):
        kayit = ky.arac_karsilastirmalari(self.gozlemler)[0]
        sayfa = ky._karsilastirma_sayfasi(kayit)
        self.assertIn("Ölçülen liste fiyatlarında en ucuz model", sayfa)
        self.assertIn("sıfır araç fiyat karşılaştırması", sayfa)
        self.assertNotRegex(sayfa, r"\b(?:mı|mi|mu|mü)\?")
        self.assertIn("Karar sınırı", sayfa)
        self.assertIn("ikinci el değeri", sayfa)
        baslik = html.unescape(re.search(r"<title>(.*?)</title>", sayfa).group(1))
        self.assertLessEqual(len(baslik), 65)

    def test_7_ve_30_gunluk_degisimler_tarihsel_seriden_gelir(self):
        seriler = ky._tarihsel_seriler()
        yedi = ky._degisimler(seriler, 7)
        otuz = ky._degisimler(seriler, 30)
        self.assertGreater(len(yedi), 20)
        self.assertGreater(len(otuz), 20)
        for x in yedi + otuz:
            self.assertNotEqual(x["once"]["tarih"], x["son"]["tarih"])
            self.assertGreater(x["gun_araligi"], 0)

    def test_canli_envanter_sitemap_ve_html_birebir(self):
        envanter = json.loads(ky.ENVANTER_DOSYASI.read_text(encoding="utf-8"))
        yollar = ky.sitemap_yollari()
        self.assertEqual(envanter["toplam_sayfa"], len(yollar))
        self.assertEqual(len(yollar), len(set(yollar)))
        for yol in yollar:
            self.assertTrue((ky.SITE_KOK / yol / "index.html").exists(), yol)


if __name__ == "__main__":
    unittest.main()
