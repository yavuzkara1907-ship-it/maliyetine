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
    # DUGUN_KALEMLERI_TAHMINI (Yavuz'un 2026-07-24 talimatiyla eklenen genel
    # piyasa arastirmasi degerleri) davetli_sayisi=100, segment="orta" icin.
    TAHMINI_TOPLAM_100_ORTA = 40000 + 700 * 100 + 45000 + 25000 + 3000 + 5000 + 40000 + 3500  # 231500

    def test_sabit_ve_kisi_basi_kalemler_dogru_toplanir(self):
        kalemler = {"gelinlik": GELINLIK_VERISI, "salon": SALON_VERISI}
        toplam, detaylar = sayfa_uret.ornek_toplam_hesapla(kalemler, davetli_sayisi=100, segment="orta")
        # gelinlik: 5000 (sabit, gercek) + salon: 800*100=80000 (gercek)
        # + tahmini kalemlerin toplami (her zaman dahil olur).
        self.assertEqual(toplam, 5000 + 80000 + self.TAHMINI_TOPLAM_100_ORTA)
        gelinlik_satir = next(d for d in detaylar if d["id"] == "gelinlik")
        self.assertTrue(gelinlik_satir["veri_var"])
        self.assertFalse(gelinlik_satir["tahmini_mi"])
        self.assertEqual(gelinlik_satir["satir_toplam"], 5000)

    def test_gercek_kaynagi_olmayan_kalem_kendi_basina_toplama_katilmaz(self):
        toplam, detaylar = sayfa_uret.ornek_toplam_hesapla({}, davetli_sayisi=100, segment="orta")
        gercek_detaylar = [d for d in detaylar if d["id"] in {t["id"] for t in sayfa_uret.DUGUN_KALEMLERI}]
        self.assertTrue(all(not d["veri_var"] for d in gercek_detaylar))
        self.assertEqual(len(gercek_detaylar), len(sayfa_uret.DUGUN_KALEMLERI))
        # Ama tahmini kalemler HER ZAMAN dahil olur (veri_var=True, tahmini_mi=True).
        tahmini_detaylar = [d for d in detaylar if d["id"] not in {t["id"] for t in sayfa_uret.DUGUN_KALEMLERI}]
        self.assertEqual(len(tahmini_detaylar), len(sayfa_uret.DUGUN_KALEMLERI_TAHMINI))
        self.assertTrue(all(d["veri_var"] and d["tahmini_mi"] for d in tahmini_detaylar))
        self.assertEqual(toplam, self.TAHMINI_TOPLAM_100_ORTA)

    def test_tahmini_kalem_segmentine_gore_dogru_deger_verir(self):
        _, detaylar = sayfa_uret.ornek_toplam_hesapla({}, davetli_sayisi=1, segment="luks")
        fotografci = next(d for d in detaylar if d["id"] == "fotografci")
        self.assertEqual(fotografci["birim_fiyat"], 100000)
        self.assertTrue(fotografci["tahmini_mi"])


class SayfaUretTestleri(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.veri_dosyasi = Path(self.tmp.name) / "dugun.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_gercek_kaynak_hic_yoksa_tahmini_oldugu_acikca_belirtilir(self):
        # DUGUN_KALEMLERI_TAHMINI statik oldugu icin veri dosyasi olmasa
        # bile artik BIR rakam gosterilir (Yavuz'un 2026-07-24 talimatiyla) -
        # ama KIRMIZI CIZGI korunmali: bu rakamin TAMAMEN genel piyasa
        # arastirmasina dayandigi ve HICBIR kaleminin gercek/kazinan bir
        # kaynaktan gelmedigi metinde ACIKCA belirtilmeli, "bağımsız
        # kaynaktan derlenen" gibi guven veren bir ifade KULLANILMAMALI.
        html = sayfa_uret.sayfa_uret(self.veri_dosyasi)
        self.assertIn("TAMAMEN genel piyasa araştırmasına dayanıyor", html)
        self.assertNotIn("bağımsız kaynaktan derlenen", html)
        self.assertIn("Henüz güncellenmedi", html)

    def test_tum_gercek_kaynaklar_0_urun_donduyse_tahmini_oldugu_belirtilir(self):
        # Regresyon: kalemler sozlugu BOS DEGIL (kaynaklar calisti,
        # kaynak_sayisi>0) ama hepsi 0 urun dondugu icin genel_medyan=null
        # olabilir (ör. sandbox'ta network engeli). Bu durumda "gercek
        # kaynaktan geldi" izlenimi UYDURULMAMALI - sadece tahmini
        # kalemlerin toplami gosterilmeli, acikca isaretlenerek.
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
        self.assertIn("TAMAMEN genel piyasa araştırmasına dayanıyor", html)
        self.assertNotIn("bağımsız kaynaktan derlenen", html)

    def test_gercek_veri_varsa_gercek_ve_tahmini_kismi_ayri_belirtilir(self):
        agregali = {
            "vertikal": "dugun",
            "guncelleme_tarihi": "2026-07-24",
            "kalemler": {"gelinlik": GELINLIK_VERISI, "salon": SALON_VERISI},
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")

        html = sayfa_uret.sayfa_uret(self.veri_dosyasi)
        self.assertIn("Güncelleme: 2026-07-24", html)
        gercek_kismi = 5000 + 800 * sayfa_uret.ORNEK_DAVETLI_SAYISI
        self.assertIn(sayfa_uret._para(gercek_kismi), html)
        self.assertIn("bağımsız kaynaktan derlenen", html)
        self.assertIn("genel piyasa araştırmasına dayanır", html)
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
