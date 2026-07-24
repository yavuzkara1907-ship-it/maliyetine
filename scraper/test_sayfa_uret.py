# -*- coding: utf-8 -*-
"""sayfa_uret.py testleri - agregali veriden dogru rakamlarin hesaplandigini
ve veri yokken UYDURULMUS bir rakam gostermedigini dogrular (KIRMIZI CIZGI)."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import sayfa_uret


GELINLIK_VERISI = {
    "genel_medyan": 5000,
    "kaynak_sayisi": 2,
    "capraz_dogrulama_uyarisi": None,
    "segmentler": {
        "dusuk": {"min": 2000, "medyan": 3000, "max": 4000, "urun_sayisi": 10},
        "orta": {"min": 4001, "medyan": 5000, "max": 7000, "urun_sayisi": 12},
        "luks": {"min": 7001, "medyan": 15000, "max": 30000, "urun_sayisi": 5},
    },
}

SALON_VERISI = {
    "genel_medyan": 800,
    "kaynak_sayisi": 1,
    "capraz_dogrulama_uyarisi": None,
    "segmentler": {
        "orta": {"min": 601, "medyan": 800, "max": 1200, "urun_sayisi": 4},
    },
}


class KalemDegerTestleri(unittest.TestCase):
    def test_veri_yoksa_none_doner(self):
        self.assertIsNone(sayfa_uret.kalem_deger(None, "orta"))

    def test_segment_varsa_medyanini_doner(self):
        self.assertEqual(sayfa_uret.kalem_deger(GELINLIK_VERISI, "luks"), 15000)

    def test_segment_yoksa_genel_medyana_duser(self):
        veri = {"genel_medyan": 999, "segmentler": {}}
        self.assertEqual(sayfa_uret.kalem_deger(veri, "luks"), 999)


class OrnekToplamHesaplaTestleri(unittest.TestCase):
    def test_sabit_ve_kisi_basi_kalemler_dogru_toplanir(self):
        kalemler = {"gelinlik": GELINLIK_VERISI, "salon": SALON_VERISI}
        toplam, detaylar = sayfa_uret.ornek_toplam_hesapla(kalemler, davetli_sayisi=100, segment="orta")
        # gelinlik: 5000 (sabit) + salon: 800*100=80000 -> geriye kalan kalemler veri yok
        self.assertEqual(toplam, 5000 + 80000)
        gelinlik_satir = next(d for d in detaylar if d["id"] == "gelinlik")
        self.assertTrue(gelinlik_satir["veri_var"])
        self.assertEqual(gelinlik_satir["satir_toplam"], 5000)

    def test_veri_olmayan_kalem_toplama_katilmaz(self):
        toplam, detaylar = sayfa_uret.ornek_toplam_hesapla({}, davetli_sayisi=100, segment="orta")
        self.assertEqual(toplam, 0)
        self.assertTrue(all(not d["veri_var"] for d in detaylar))
        self.assertEqual(len(detaylar), len(sayfa_uret.DUGUN_KALEMLERI))


class SayfaUretTestleri(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.veri_dosyasi = Path(self.tmp.name) / "dugun.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_veri_dosyasi_yoksa_uydurma_rakam_gostermez(self):
        html = sayfa_uret.sayfa_uret(self.veri_dosyasi)
        self.assertIn("Veri toplama süreci devam ediyor", html)
        self.assertIn("Henüz güncellenmedi", html)
        # Hicbir TL rakami "uydurulmus" bir cevap metninde gorunmemeli -
        # sadece tablo "-" gostermeli.
        self.assertNotIn("kişilik, orta segment bir düğünün", html)

    def test_tum_kaynaklar_0_urun_donduyse_uydurma_rakam_gostermez(self):
        # Regresyon: kalemler sozlugu BOS DEGIL (kaynaklar calisti,
        # kaynak_sayisi>0) ama hepsi 0 urun dondugu icin genel_medyan=null
        # olabilir (ör. sandbox'ta network engeli). Bu durumda "0 TL"
        # gibi yaniltici, guvenilir gorunen bir cevap metni UYDURULMAMALI.
        agregali = {
            "vertikal": "dugun",
            "guncelleme_tarihi": "2026-07-24",
            "kalemler": {
                "gelinlik": {"genel_medyan": None, "kaynak_sayisi": 3, "segmentler": {}, "capraz_dogrulama_uyarisi": None},
                "damatlik": {"genel_medyan": None, "kaynak_sayisi": 5, "segmentler": {}, "capraz_dogrulama_uyarisi": None},
            },
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")

        html = sayfa_uret.sayfa_uret(self.veri_dosyasi)
        self.assertIn("Veri toplama süreci devam ediyor", html)
        self.assertNotIn("0 TL", html)
        self.assertNotIn("kişilik, orta segment bir düğünün", html)

    def test_gercek_veri_varsa_hesaplanan_rakam_gorunur(self):
        agregali = {
            "vertikal": "dugun",
            "guncelleme_tarihi": "2026-07-24",
            "kalemler": {"gelinlik": GELINLIK_VERISI, "salon": SALON_VERISI},
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")

        html = sayfa_uret.sayfa_uret(self.veri_dosyasi)
        self.assertIn("Güncelleme: 2026-07-24", html)
        beklenen_toplam = 5000 + 800 * sayfa_uret.ORNEK_DAVETLI_SAYISI
        self.assertIn(sayfa_uret._para(beklenen_toplam), html)
        self.assertIn('"@type": "FAQPage"', html)
        self.assertIn('"@type": "Dataset"', html)

    def test_capraz_dogrulama_uyarisi_sayfada_gorunur(self):
        uyarili_alyans = {
            "genel_medyan": 10000,
            "kaynak_sayisi": 2,
            "capraz_dogrulama_uyarisi": {"fark_yuzdesi": 351.0, "medyanlar": {"atasay": 19405, "trendyol": 4298}},
            "segmentler": {},
        }
        agregali = {
            "vertikal": "dugun", "guncelleme_tarihi": "2026-07-24",
            "kalemler": {"gelinlik": GELINLIK_VERISI},
        }
        # alyans kalemi DUGUN_KALEMLERI listesinde degil (bu test sadece
        # uyari render fonksiyonunu dogrudan kontrol ediyor).
        html_uyari = sayfa_uret._capraz_dogrulama_uyarilari_html({"alyans": uyarili_alyans})
        self.assertIn("%351", html_uyari)
        self.assertIn("Alyans", html_uyari)

        html_uyarisiz = sayfa_uret._capraz_dogrulama_uyarilari_html({"gelinlik": GELINLIK_VERISI})
        self.assertEqual(html_uyarisiz, "")


if __name__ == "__main__":
    unittest.main()
