# -*- coding: utf-8 -*-
"""Kalici exact-query fiyat gozlemi sayfalari testleri."""

import html
import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import fiyat_gozlemleri as fg


def _veri(urunler_a=None, urunler_b=None):
    return {
        "guncelleme_tarihi": "2026-08-22",
        "kalemler": {
            "buzdolabi": {
                "genel_medyan": 40000,
                "toplam_urun": 60,
                "kaynak_sayisi": 2,
                "guncelleme_tarihi": "2026-08-22",
                "kaynaklar": [
                    {"site": "amazon", "tarih": "2026-08-22", "toplam_urun": 30,
                     "ornek_urunler": urunler_a or []},
                    {"site": "trendyol", "tarih": "2026-08-22", "toplam_urun": 30,
                     "ornek_urunler": urunler_b or []},
                ],
            }
        },
    }


class FiyatGozlemiTesti(unittest.TestCase):

    def _yaz(self, kok: Path, veri: dict):
        (kok / "ev-kurma.json").write_text(
            json.dumps(veri, ensure_ascii=False), encoding="utf-8"
        )

    def test_ayni_urun_iki_kaynakta_tek_url_olur(self):
        with TemporaryDirectory() as d:
            kok = Path(d)
            self._yaz(kok, _veri(
                [{"isim": "Arçelik 123 Buzdolabı", "fiyat": 41000}],
                [{"isim": "Arçelik 123 Buzdolabı", "fiyat": 43000}],
            ))
            e = fg.envanter_uret(kok, kok / "yok.json")
        self.assertEqual(e["gozlem_sayfasi"], 1)
        self.assertEqual(len(e["gozlemler"][0]["olcumler"]), 2)
        self.assertEqual(e["gozlemler"][0]["slug"].count("/"), 0)

    def test_bos_ve_gecersiz_fiyat_sayfa_acmaz(self):
        with TemporaryDirectory() as d:
            kok = Path(d)
            self._yaz(kok, _veri([
                {"isim": "", "fiyat": 20000},
                {"isim": "Gerçek ürün", "fiyat": 0},
                {"isim": "Fiyatsız ürün", "fiyat": None},
            ]))
            e = fg.envanter_uret(kok, kok / "yok.json")
        self.assertEqual(e["gozlem_sayfasi"], 0)

    def test_onceki_url_urun_yeni_kosuda_yokken_korunur(self):
        with TemporaryDirectory() as d:
            kok = Path(d)
            envanter = kok / "envanter.json"
            self._yaz(kok, _veri(
                [{"isim": "Kalıcı Model 42", "fiyat": 42000}], []
            ))
            ilk = fg.envanter_uret(kok, envanter)
            envanter.write_text(json.dumps(ilk, ensure_ascii=False), encoding="utf-8")
            ilk_slug = ilk["gozlemler"][0]["slug"]
            self._yaz(kok, _veri([], []))
            ikinci = fg.envanter_uret(kok, envanter)
        self.assertEqual(ikinci["gozlem_sayfasi"], 1)
        self.assertEqual(ikinci["gozlemler"][0]["slug"], ilk_slug)
        self.assertFalse(ikinci["gozlemler"][0]["bu_kosuda_goruldu"])

    def test_sayfa_fiyati_kaynagi_tarihi_ve_gorunur_faqyi_tasir(self):
        with TemporaryDirectory() as d:
            kok = Path(d)
            uzun = "Arçelik Çok Uzun ve Ayırt Edici Model Adı 123 Buzdolabı"
            self._yaz(kok, _veri(
                [{"isim": uzun, "fiyat": 41000}],
                [{"isim": uzun, "fiyat": 43000}],
            ))
            kayit = fg.envanter_uret(kok, kok / "yok.json")["gozlemler"][0]
            sayfa = fg.gozlem_sayfasi(kayit, [kayit])
        baslik = html.unescape(re.search(r"<title>(.*?)</title>", sayfa).group(1))
        self.assertLessEqual(len(baslik), 62)
        self.assertIn("42.000 TL", sayfa)
        self.assertIn("Amazon", sayfa)
        self.assertIn("Trendyol", sayfa)
        self.assertIn("2026-08-22", sayfa)
        self.assertIn('"FAQPage"', sayfa)
        self.assertGreaterEqual(sayfa.count(f"{uzun} fiyatı ne kadar?"), 2)

    def test_canli_envanter_sitemap_ve_html_birebir(self):
        envanter = json.loads(fg.ENVANTER_DOSYASI.read_text(encoding="utf-8"))
        yollar = fg.sitemap_yollari()
        self.assertEqual(envanter["gozlem_sayfasi"], len(envanter["gozlemler"]))
        self.assertEqual(
            len(yollar),
            1 + len(envanter["vertikaller"]) + envanter["gozlem_sayfasi"],
        )
        for yol in yollar:
            self.assertTrue((fg.SITE_KOK / yol / "index.html").exists(), yol)


if __name__ == "__main__":
    unittest.main()
