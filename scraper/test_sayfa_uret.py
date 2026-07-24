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


DUGUN = sayfa_uret.VERTIKALLER["dugun"]
EV_KURMA = sayfa_uret.VERTIKALLER["ev-kurma"]


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
        toplam, detaylar = sayfa_uret.ornek_toplam_hesapla(DUGUN, kalemler, olcek=100, segment="orta")
        # gelinlik: 5000 (sabit, gercek) + salon: 800*100=80000 (gercek)
        # + tahmini kalemlerin toplami (her zaman dahil olur).
        self.assertEqual(toplam, 5000 + 80000 + self.TAHMINI_TOPLAM_100_ORTA)
        gelinlik_satir = next(d for d in detaylar if d["id"] == "gelinlik")
        self.assertTrue(gelinlik_satir["veri_var"])
        self.assertFalse(gelinlik_satir["tahmini_mi"])
        self.assertEqual(gelinlik_satir["satir_toplam"], 5000)

    def test_gercek_kaynagi_olmayan_kalem_kendi_basina_toplama_katilmaz(self):
        toplam, detaylar = sayfa_uret.ornek_toplam_hesapla(DUGUN, {}, olcek=100, segment="orta")
        gercek_detaylar = [d for d in detaylar if d["id"] in {t["id"] for t in sayfa_uret.DUGUN_KALEMLERI}]
        self.assertTrue(all(not d["veri_var"] for d in gercek_detaylar))
        self.assertEqual(len(gercek_detaylar), len(sayfa_uret.DUGUN_KALEMLERI))
        # Ama tahmini kalemler HER ZAMAN dahil olur (veri_var=True, tahmini_mi=True).
        tahmini_detaylar = [d for d in detaylar if d["id"] not in {t["id"] for t in sayfa_uret.DUGUN_KALEMLERI}]
        self.assertEqual(len(tahmini_detaylar), len(sayfa_uret.DUGUN_KALEMLERI_TAHMINI))
        self.assertTrue(all(d["veri_var"] and d["tahmini_mi"] for d in tahmini_detaylar))
        self.assertEqual(toplam, self.TAHMINI_TOPLAM_100_ORTA)

    def test_tahmini_kalem_segmentine_gore_dogru_deger_verir(self):
        _, detaylar = sayfa_uret.ornek_toplam_hesapla(DUGUN, {}, olcek=1, segment="luks")
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
        html = sayfa_uret.sayfa_uret("dugun", self.veri_dosyasi)
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

        html = sayfa_uret.sayfa_uret("dugun", self.veri_dosyasi)
        self.assertIn("TAMAMEN genel piyasa araştırmasına dayanıyor", html)
        self.assertNotIn("bağımsız kaynaktan derlenen", html)

    def test_gercek_veri_varsa_gercek_ve_tahmini_kismi_ayri_belirtilir(self):
        agregali = {
            "vertikal": "dugun",
            "guncelleme_tarihi": "2026-07-24",
            "kalemler": {"gelinlik": GELINLIK_VERISI, "salon": SALON_VERISI},
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")

        html = sayfa_uret.sayfa_uret("dugun", self.veri_dosyasi)
        self.assertIn("Güncelleme: 2026-07-24", html)
        gercek_kismi = 5000 + 800 * DUGUN["olcek_varsayilan"]
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
        html_uyari = sayfa_uret._capraz_dogrulama_uyarilari_html(DUGUN, {"alyans": uyarili_alyans})
        self.assertIn("%351", html_uyari)
        self.assertIn("Alyans", html_uyari)

        html_uyarisiz = sayfa_uret._capraz_dogrulama_uyarilari_html(DUGUN, {"gelinlik": GELINLIK_VERISI})
        self.assertEqual(html_uyarisiz, "")


BUZDOLABI_VERISI = {
    "genel_medyan": 28860,
    "kaynak_sayisi": 1,
    "capraz_dogrulama_uyarisi": None,
    "kaynaklar": [{"site": "trendyol", "tarih": "2026-07-25", "toplam_urun": 25}],
    "segmentler": {
        "dusuk": {"min": 6388, "medyan": 8829, "max": 15699, "urun_sayisi": 7},
        "orta": {"min": 18589, "medyan": 28930, "max": 36199, "urun_sayisi": 12},
        "luks": {"min": 37898, "medyan": 43299, "max": 62860, "urun_sayisi": 6},
    },
}


class BagimsizSitelerTestleri(unittest.TestCase):
    """Regresyon: "kac bagimsiz kaynak" ifadesi kalem basina kaynak_sayisi'nin
    TOPLAMI degil, BENZERSIZ SITE sayisi olmali. Ayni site 42 kalemi de
    besliyorsa bu "42 bagimsiz kaynak" DEGILDIR - okuyucuya 42 farkli site
    izlenimi vermek COK KAYNAK KURALI'ni yanlis temsil eder."""

    def test_ayni_site_birden_cok_kalemde_tekrar_sayilmaz(self):
        kalemler = {
            "buzdolabi": {"kaynaklar": [{"site": "trendyol"}]},
            "camasir-makinesi": {"kaynaklar": [{"site": "trendyol"}]},
            "gardirop": {"kaynaklar": [{"site": "trendyol"}]},
        }
        siteler = sayfa_uret.bagimsiz_siteler(kalemler, set(kalemler))
        self.assertEqual(siteler, {"trendyol"})

    def test_farkli_siteler_ayri_sayilir(self):
        kalemler = {
            "damatlik": {"kaynaklar": [{"site": "trendyol"}, {"site": "vakko"}]},
            "alyans": {"kaynaklar": [{"site": "atasay"}]},
        }
        siteler = sayfa_uret.bagimsiz_siteler(kalemler, set(kalemler))
        self.assertEqual(siteler, {"trendyol", "vakko", "atasay"})

    def test_kapsam_disi_kalemin_sitesi_sayilmaz(self):
        kalemler = {
            "gelinlik": {"kaynaklar": [{"site": "trendyol"}]},
            "salon": {"kaynaklar": [{"site": "dugunbuketi"}]},
        }
        siteler = sayfa_uret.bagimsiz_siteler(kalemler, {"gelinlik"})
        self.assertEqual(siteler, {"trendyol"})


class TekKaynakUyarisiTestleri(unittest.TestCase):
    def test_tek_site_varsa_uyari_gosterilir(self):
        html = sayfa_uret._tek_kaynak_uyarisi_html(EV_KURMA, {"trendyol"})
        self.assertIn("Tek kaynak uyarısı", html)
        self.assertIn("Trendyol", html)

    def test_birden_cok_site_varsa_uyari_gosterilmez(self):
        html = sayfa_uret._tek_kaynak_uyarisi_html(DUGUN, {"trendyol", "vakko"})
        self.assertEqual(html, "")

    def test_hic_site_yoksa_uyari_gosterilmez(self):
        self.assertEqual(sayfa_uret._tek_kaynak_uyarisi_html(DUGUN, set()), "")


class EvKurmaVertikaliTestleri(unittest.TestCase):
    """Ev kurma vertikalinde HIC tahmini kalem yok - hepsi gercek kaynakli.
    Bu, KIRMIZI CIZGI acisindan dugun'den farkli bir kod yolu (tahmini
    bloklarinin hic devreye girmemesi) oldugu icin ayrica kilitleniyor."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.veri_dosyasi = Path(self.tmp.name) / "ev-kurma.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_tahmini_kalem_tanimli_degil(self):
        self.assertEqual(EV_KURMA["tahmini_kalemler"], [])

    def test_veri_yoksa_rakam_UYDURULMAZ(self):
        # Tahmini kalem olmadigi icin, veri de yoksa gosterilecek hicbir
        # dogrulanmis rakam yok - "0 TL" gibi guven veren bir sayi
        # UYDURULMAMALI.
        html = sayfa_uret.sayfa_uret("ev-kurma", self.veri_dosyasi)
        self.assertIn("Veri toplama süreci devam ediyor", html)
        self.assertNotIn("bağımsız kaynaktan derlenen", html)
        # Cevap blogunda hicbir para rakami olmamali.
        cevap = html.split('class="cevap-blok"')[1].split("</div>")[0]
        self.assertNotIn("TL", cevap)

    def test_gercek_veri_varsa_tamami_kaynakli_denir(self):
        agregali = {
            "vertikal": "ev-kurma",
            "guncelleme_tarihi": "2026-07-25",
            "kalemler": {"buzdolabi": BUZDOLABI_VERISI},
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")

        html = sayfa_uret.sayfa_uret("ev-kurma", self.veri_dosyasi)
        self.assertIn("Güncelleme: 2026-07-25", html)
        self.assertIn(sayfa_uret._para(28930), html)
        self.assertIn("bağımsız kaynaktan derlenen", html)
        # Tahmini kalem olmadigi icin "tahmini kismi" cumlesi HIC kurulmamali.
        self.assertNotIn("genel piyasa araştırmasına dayanır", html)
        self.assertIn("tamamı</strong> gerçek", html)
        # Tek site besliyor: "1 bağımsız kaynak" denmeli, kalem sayisi degil.
        self.assertIn("1 bağımsız kaynaktan derlenen", html)
        self.assertIn("Tek kaynak uyarısı", html)

    def test_kalem_gruplari_tabloda_basliklanir(self):
        agregali = {
            "vertikal": "ev-kurma", "guncelleme_tarihi": "2026-07-25",
            "kalemler": {"buzdolabi": BUZDOLABI_VERISI},
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")
        html = sayfa_uret.sayfa_uret("ev-kurma", self.veri_dosyasi)
        self.assertIn('<tr class="grup-satiri"><td colspan="5">Beyaz eşya</td></tr>', html)
        self.assertIn("Mutfak", html)

    def test_linkler_ve_kanonik_url_vertikale_gore_uretilir(self):
        html = sayfa_uret.sayfa_uret("ev-kurma", self.veri_dosyasi)
        self.assertIn('href="https://maliyetine.com.tr/ev-kurma/"', html)
        self.assertIn('href="/ev-kurma/hesaplayici/"', html)
        self.assertIn('href="/ev-kurma/metodoloji/"', html)
        self.assertNotIn("/dugun/", html)

    def test_bilinmeyen_vertikal_hata_verir(self):
        with self.assertRaises(ValueError):
            sayfa_uret.sayfa_uret("olmayan-vertikal")


if __name__ == "__main__":
    unittest.main()
