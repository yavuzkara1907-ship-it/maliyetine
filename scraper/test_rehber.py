# -*- coding: utf-8 -*-
"""rehber.py testleri - yazilarin rakamlari VERIDEN gelmeli, elle yazilmamali."""
import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import rehber


DUGUN_VERI = {
    "vertikal": "dugun",
    "guncelleme_tarihi": "2026-08-15",
    "kalemler": {
        "gelinlik": {"genel_medyan": 9000, "toplam_urun": 20,
                     "segmentler": {"orta": {"medyan": 9000}, "dusuk": {"medyan": 5000},
                                    "luks": {"medyan": 15000}}},
        "salon-yemekli": {"genel_medyan": 1000, "toplam_urun": 11,
                          "segmentler": {"orta": {"medyan": 1000}, "dusuk": {"medyan": 700},
                                         "luks": {"medyan": 2000}}},
        "salon-kokteyl": {"genel_medyan": 500, "toplam_urun": 10,
                          "segmentler": {"orta": {"medyan": 500}, "dusuk": {"medyan": 300},
                                         "luks": {"medyan": 900}}},
    },
}


class RehberTesti(unittest.TestCase):

    def test_veri_yoksa_sayfa_URETILMEZ(self):
        """Bos/rakamsiz bir blog yazisi yayinlamak guven kaybi."""
        for r in rehber.REHBERLER:
            self.assertIsNone(rehber.rehber_uret(r, {}), r["slug"])

    def test_rakamlar_veriden_gelir(self):
        r = next(x for x in rehber.REHBERLER if x["slug"] == "yemekli-mi-kokteyl-mi")
        html = rehber.rehber_uret(r, {"dugun": DUGUN_VERI})
        self.assertIsNotNone(html)
        self.assertIn("1.000 TL", html)   # yemekli
        self.assertIn("500 TL", html)     # kokteyl
        self.assertIn("75.000 TL", html)  # 150 kisilik fark: (1000-500)*150

    def test_jsonld_gecerli_ve_article(self):
        r = next(x for x in rehber.REHBERLER if x["slug"] == "yemekli-mi-kokteyl-mi")
        html = rehber.rehber_uret(r, {"dugun": DUGUN_VERI})
        bloklar = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        self.assertTrue(bloklar)
        graf = json.loads(bloklar[0])["@graph"]
        self.assertEqual(graf[0]["@type"], "Article")
        self.assertEqual(graf[1]["@type"], "BreadcrumbList")

    def test_diger_rehberlere_ic_link_verir(self):
        r = next(x for x in rehber.REHBERLER if x["slug"] == "yemekli-mi-kokteyl-mi")
        html = rehber.rehber_uret(r, {"dugun": DUGUN_VERI})
        self.assertIn("/rehber/150-kisilik-dugun-maliyeti/", html)
        # kendine link vermemeli
        self.assertNotIn('href="/rehber/yemekli-mi-kokteyl-mi/"', html)

    def test_yazilan_dosyalar_ve_dizin(self):
        with TemporaryDirectory() as d:
            veri_kok = Path(d) / "veri"
            veri_kok.mkdir()
            (veri_kok / "dugun.json").write_text(json.dumps(DUGUN_VERI), encoding="utf-8")
            hedef = Path(d) / "rehber"
            yazilan = rehber.rehberleri_yaz(veri_kok=veri_kok, hedef_kok=hedef)
            slugler = {r["slug"] for r in yazilan}
            # Sadece dugun verisi var -> ev-kurma ve arac rehberleri yazilmamali
            self.assertIn("yemekli-mi-kokteyl-mi", slugler)
            self.assertNotIn("sifirdan-ev-kurma-listesi", slugler)
            self.assertTrue((hedef / "index.html").exists())
            dizin = (hedef / "index.html").read_text()
            self.assertNotIn("sifirdan-ev-kurma-listesi", dizin)

    def test_yapay_zeka_klise_kaliplari_yok(self):
        """Yavuz'un talimati: 'yapay zeka gibi degil, gercekci'."""
        html = rehber.rehber_uret(
            next(x for x in rehber.REHBERLER if x["slug"] == "yemekli-mi-kokteyl-mi"),
            {"dugun": DUGUN_VERI})
        for kalip in ["Unutmayın ki", "Sonuç olarak", "Peki ya", "Kısacası",
                      "bu yazıda", "ele alacağız", "Umarız"]:
            self.assertNotIn(kalip.lower(), html.lower(), f"klise kalip: {kalip}")


if __name__ == "__main__":
    unittest.main()


class GrupYuzdesiTesti(unittest.TestCase):
    """Varsayilan-kapali kalemler grup yuzdelerini sismemeli."""

    def test_okul_grup_toplami_yillik_toplami_asmaz(self):
        import sayfa_uret as su
        conf = su.VERTIKALLER["okul"]
        veri = {k["id"]: {"genel_medyan": 1000, "toplam_urun": 20,
                          "segmentler": {"orta": {"medyan": 1000},
                                         "dusuk": {"medyan": 500},
                                         "luks": {"medyan": 2000}}}
                for k in conf["kalemler"]}
        html = rehber.rehber_uret(
            next(r for r in rehber.REHBERLER if r["slug"] == "okul-masrafi-ne-kadar"),
            {"okul": {"kalemler": veri, "guncelleme_tarihi": "2026-08-01"}})
        self.assertIsNotNone(html)
        yuzdeler = [int(x) for x in re.findall(r'class="sayi">%(\d+)</td>', html)]
        self.assertTrue(yuzdeler, "grup tablosu uretilmedi")
        self.assertLessEqual(sum(yuzdeler), 101, f"grup yuzdeleri %100'u asiyor: {yuzdeler}")

    def test_tek_seferlik_kalemler_gruplarda_yok(self):
        import sayfa_uret as su
        conf = su.VERTIKALLER["okul"]
        veri = {k["id"]: {"genel_medyan": 1000, "toplam_urun": 20,
                          "segmentler": {"orta": {"medyan": 1000}}}
                for k in conf["kalemler"]}
        html = rehber.rehber_uret(
            next(r for r in rehber.REHBERLER if r["slug"] == "okul-masrafi-ne-kadar"),
            {"okul": {"kalemler": veri, "guncelleme_tarihi": "2026-08-01"}})
        # Teknoloji ve Calisma alani gruplari toplam tablosunda OLMAMALI
        tablo = re.search(r'<h2>Para nereye gidiyor\?</h2>(.*?)</table>', html, re.S).group(1)
        self.assertNotIn("Teknoloji", tablo)
        self.assertNotIn("Çalışma alanı", tablo)
