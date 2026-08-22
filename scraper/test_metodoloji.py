# -*- coding: utf-8 -*-
"""Metodoloji sayfalari canli veriyle ayni gercegi anlatmali."""

import json
import re
import unittest

import metodoloji
import sayfa_uret as su


class MetodolojiTestleri(unittest.TestCase):
    def test_tum_sayilar_kanonik_jsonla_ayni(self):
        for vertikal in su.VERTIKALLER:
            veri = json.loads((su.SITE_KOK / "veri" / f"{vertikal}.json").read_text())
            ozet = metodoloji.metodoloji_ozeti(vertikal)
            html = metodoloji.metodoloji_html(vertikal)
            self.assertEqual(ozet["seri"], len(veri["kalemler"]))
            self.assertIn(f'<dd>{ozet["seri"]}</dd>', html, vertikal)
            self.assertIn(f'<dd>{ozet["kaynak"]}</dd>', html, vertikal)
            self.assertIn(f'<dd>{ozet["cok"]}</dd>', html, vertikal)

    def test_eski_kopya_sablonlari_yok(self):
        yasaklar = (
            "42 kalemin hepsi", "bir öğrencinin bebek", "bir öğrencinin kedi",
            "bir öğrencinin köpek", "İki komodin ya da üç halı",
            "ikinci kaynak eklendiğinde", "Veri ayda bir",
        )
        for vertikal in su.VERTIKALLER:
            html = metodoloji.metodoloji_html(vertikal)
            for yasak in yasaklar:
                self.assertNotIn(yasak, html, f"{vertikal}: {yasak}")

    def test_dugunde_yalniz_gercek_tahminler_yazilir(self):
        html = metodoloji.metodoloji_html("dugun")
        self.assertIn("Orkestra / DJ", html)
        self.assertIn("Nikah İşlemleri", html)
        for artik_gercek in ("Fotoğraf ve Video", "Kuaför ve Makyaj",
                             "Gelin Arabası", "Organizasyon / Süsleme"):
            self.assertNotRegex(
                html,
                rf"{re.escape(artik_gercek)}[^<]*(?:tahmin|sürekli.*yok)",
            )

    def test_guncelleme_politikasi_iki_kez(self):
        for vertikal in su.VERTIKALLER:
            html = metodoloji.metodoloji_html(vertikal)
            self.assertIn("ayın <strong>5'i ve 20'sinde</strong>", html)
            self.assertIn('"@type": "WebPage"', html)
            self.assertIn('"@type": "FAQPage"', html)

    def test_paylasim_karti_vertikale_ozel(self):
        for vertikal in su.VERTIKALLER:
            html = metodoloji.metodoloji_html(vertikal)
            self.assertIn('property="og:title"', html)
            self.assertIn(f'/assets/og/{vertikal}-metodoloji.png', html)
            self.assertIn('name="twitter:card"', html)


if __name__ == "__main__":
    unittest.main()
