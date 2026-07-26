# -*- coding: utf-8 -*-
"""agrega.py testleri - motor.py'nin site-basina JSON ciktilarini tek bir
endeks JSON'una dogru birlestirdigini dogrular."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import agrega


def _kayit_yaz(klasor: Path, kalem: str, site: str, tarih: str, **ust_yaz):
    klasor.mkdir(parents=True, exist_ok=True)
    veri = {
        "site": site,
        "kaynak_adlari": [f"{site.title()} - {kalem.title()}"],
        "kalem": kalem,
        "vertikal": "dugun",
        "tarih": tarih,
        "toplam_urun": 10,
        "saglikli": True,
        "kullanilan_katmanlar": ["json-ld"],
        "genel_medyan": 1000,
        "segmentler": {
            "dusuk": {"min": 500, "medyan": 700, "max": 900, "urun_sayisi": 3},
            "orta": {"min": 950, "medyan": 1100, "max": 1300, "urun_sayisi": 4},
            "luks": {"min": 1400, "medyan": 1800, "max": 2500, "urun_sayisi": 3},
        },
    }
    veri.update(ust_yaz)
    dosya = klasor / f"{kalem}_{site}_{tarih}.json"
    dosya.write_text(json.dumps(veri, ensure_ascii=False), encoding="utf-8")
    return veri


class KaynakOkumaTestleri(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.veri_kok = Path(self.tmp.name)
        self.vertikal_klasoru = self.veri_kok / "dugun"

    def tearDown(self):
        self.tmp.cleanup()

    def test_olmayan_klasor_bos_liste_doner(self):
        self.assertEqual(agrega.kaynak_dosyalarini_oku(self.veri_kok / "yok"), [])

    def test_capraz_dogrulama_dosyasi_atlanir(self):
        _kayit_yaz(self.vertikal_klasoru, "gelinlik", "trendyol", "2026-07-24")
        rapor = self.vertikal_klasoru / "gelinlik_capraz-dogrulama_2026-07-24.json"
        rapor.write_text(json.dumps({"kalem": "gelinlik"}), encoding="utf-8")

        kayitlar = agrega.kaynak_dosyalarini_oku(self.vertikal_klasoru)
        self.assertEqual(len(kayitlar), 1)
        self.assertEqual(kayitlar[0]["site"], "trendyol")

    def test_bozuk_json_sessizce_atlanir(self):
        self.vertikal_klasoru.mkdir(parents=True)
        (self.vertikal_klasoru / "bozuk.json").write_text("{ gecersiz", encoding="utf-8")
        self.assertEqual(agrega.kaynak_dosyalarini_oku(self.vertikal_klasoru), [])


class EnGuncelSecimTestleri(unittest.TestCase):
    def test_sagliksiz_kayit_disarida_birakilir(self):
        kayitlar = [
            {"kalem": "gelinlik", "site": "trendyol", "tarih": "2026-07-24", "saglikli": False},
        ]
        self.assertEqual(agrega.en_guncel_kayitlari_sec(kayitlar), [])

    def test_ayni_kaynagin_en_guncel_tarihli_versiyonu_kazanir(self):
        eski = {"kalem": "gelinlik", "site": "trendyol", "tarih": "2026-06-01", "saglikli": True, "toplam_urun": 5}
        yeni = {"kalem": "gelinlik", "site": "trendyol", "tarih": "2026-07-24", "saglikli": True, "toplam_urun": 23}
        sonuc = agrega.en_guncel_kayitlari_sec([eski, yeni])
        self.assertEqual(len(sonuc), 1)
        self.assertEqual(sonuc[0]["toplam_urun"], 23)

    def test_farkli_kaynaklar_ayri_ayri_tutulur(self):
        a = {"kalem": "gelinlik", "site": "trendyol", "tarih": "2026-07-24", "saglikli": True}
        b = {"kalem": "gelinlik", "site": "beymen", "tarih": "2026-07-24", "saglikli": True}
        sonuc = agrega.en_guncel_kayitlari_sec([a, b])
        self.assertEqual(len(sonuc), 2)


class KalemBirlestirTestleri(unittest.TestCase):
    def test_tek_kaynak_dogrudan_gecer(self):
        kayit = {
            "site": "trendyol", "kaynak_adlari": ["Trendyol - Gelinlik"], "tarih": "2026-07-24",
            "toplam_urun": 23, "genel_medyan": 5000,
            "segmentler": {"orta": {"min": 4000, "medyan": 5000, "max": 6000, "urun_sayisi": 23}},
        }
        ozet = agrega.kalem_birlestir([kayit])
        self.assertEqual(ozet["segmentler"]["orta"]["medyan"], 5000)
        self.assertEqual(ozet["segmentler"]["orta"]["kaynak_sayisi"], 1)
        self.assertEqual(ozet["kaynak_sayisi"], 1)
        self.assertEqual(ozet["genel_medyan"], 5000)
        self.assertNotIn("dusuk", ozet["segmentler"])

    def test_iki_kaynak_medyan_of_medyan(self):
        # COK KAYNAK KURALI: ham fiyatlar karistirilmiyor, her kaynagin
        # KENDI medyani alinip onlarin medyani hesaplaniyor.
        atasay = {
            "site": "atasay", "kaynak_adlari": ["Atasay - Alyans"], "tarih": "2026-07-24",
            "toplam_urun": 24, "genel_medyan": 19405,
            "segmentler": {"orta": {"min": 15000, "medyan": 19405, "max": 25000, "urun_sayisi": 24}},
        }
        trendyol = {
            "site": "trendyol", "kaynak_adlari": ["Trendyol - Alyans"], "tarih": "2026-07-24",
            "toplam_urun": 4, "genel_medyan": 4298,
            "segmentler": {"orta": {"min": 3000, "medyan": 4298, "max": 5000, "urun_sayisi": 4}},
        }
        ozet = agrega.kalem_birlestir([atasay, trendyol])
        # medyan([19405, 4298]) -> ortalamalari (cift sayida eleman)
        self.assertEqual(ozet["segmentler"]["orta"]["medyan"], round((19405 + 4298) / 2))
        self.assertEqual(ozet["segmentler"]["orta"]["min"], 3000)
        self.assertEqual(ozet["segmentler"]["orta"]["max"], 25000)
        self.assertEqual(ozet["segmentler"]["orta"]["urun_sayisi"], 28)
        self.assertEqual(ozet["segmentler"]["orta"]["kaynak_sayisi"], 2)
        self.assertEqual(ozet["kaynak_sayisi"], 2)
        self.assertEqual(len(ozet["kaynaklar"]), 2)

    def test_sifir_urunlu_kaynak_SAYILMAZ_ve_LISTELENMEZ(self):
        """Regresyon (2026-07-25): birakilmis/bozulmus kaynaklarin eski
        0-urunlu snapshot'lari diskte kaliyor ve kaynak_sayisi'na
        katiliyordu. Dugun/gelinlik'te 6 kaynak listeliyken gerceginde
        yalnizca 1'i (trendyol) urun donduruyordu; vertikal genelinde
        "10 bagimsiz kaynak" deniyordu, gercek 5'ti - COK KAYNAK KURALI
        iki kat sisik gorunuyordu. 0-urunlu kaynak ne medyana ne segmente
        katki yapar; sayilmasi da listelenmesi de yaniltici."""
        calisan = {
            "site": "trendyol", "kaynak_adlari": ["Trendyol - Gelinlik"],
            "tarih": "2026-07-25", "toplam_urun": 21, "genel_medyan": 8999,
            "segmentler": {"orta": {"min": 5000, "medyan": 8999, "max": 12000, "urun_sayisi": 21}},
        }
        birakilmis = {
            "site": "akakce", "kaynak_adlari": ["Akakce - Gelinlik"],
            "tarih": "2026-07-24", "toplam_urun": 0, "genel_medyan": None,
            "segmentler": {},
        }
        bos_ama_tarihi_yeni = {
            "site": "cimri", "kaynak_adlari": ["Cimri - Gelinlik"],
            "tarih": "2026-07-25", "toplam_urun": 0, "genel_medyan": None,
            "segmentler": {},
        }
        ozet = agrega.kalem_birlestir([calisan, birakilmis, bos_ama_tarihi_yeni])
        self.assertEqual(ozet["kaynak_sayisi"], 1)
        self.assertEqual([k["site"] for k in ozet["kaynaklar"]], ["trendyol"])
        # Rakamlar etkilenmemeli: medyan ve toplam urun dogru kalmali.
        self.assertEqual(ozet["genel_medyan"], 8999)
        self.assertEqual(ozet["toplam_urun"], 21)

    def test_tum_kaynaklar_bossa_kaynak_sayisi_sifir(self):
        # Bu durumda "veri yok" denmeli, sahte bir kaynak sayisi degil.
        bos = {
            "site": "akakce", "kaynak_adlari": ["A"], "tarih": "2026-07-24",
            "toplam_urun": 0, "genel_medyan": None, "segmentler": {},
        }
        ozet = agrega.kalem_birlestir([bos])
        self.assertEqual(ozet["kaynak_sayisi"], 0)
        self.assertEqual(ozet["kaynaklar"], [])
        self.assertIsNone(ozet["genel_medyan"])

    def test_guncelleme_tarihi_en_yeniyi_alir(self):
        eski = {
            "site": "a", "kaynak_adlari": ["A"], "tarih": "2026-06-01",
            "toplam_urun": 5, "genel_medyan": 1000, "segmentler": {},
        }
        yeni = {
            "site": "b", "kaynak_adlari": ["B"], "tarih": "2026-07-24",
            "toplam_urun": 5, "genel_medyan": 1000, "segmentler": {},
        }
        ozet = agrega.kalem_birlestir([eski, yeni])
        self.assertEqual(ozet["guncelleme_tarihi"], "2026-07-24")


class VertikalAgregaliTestleri(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.veri_kok = Path(self.tmp.name)
        self.vertikal_klasoru = self.veri_kok / "dugun"

    def tearDown(self):
        self.tmp.cleanup()

    def test_bos_veri_klasoru_bos_kalemler_doner(self):
        sonuc = agrega.vertikal_agregali("dugun", self.veri_kok)
        self.assertEqual(sonuc["kalemler"], {})
        self.assertIsNone(sonuc["guncelleme_tarihi"])

    def test_capraz_dogrulama_uyarisi_ilgili_kaleme_eklenir(self):
        # Sema motor.py'nin GERCEK capraz_dogrula() ciktisiyla birebir ayni
        # olmali (2026-07-25, Yavuz'un yerelinde gercek veriyle bulunan bug):
        # "site_medyanlari" (medyanlar DEGIL) ve "fark_orani" (oran, 0-1+
        # araliginda - "fark_yuzdesi" DEGIL, zaten yuzde degil).
        _kayit_yaz(self.vertikal_klasoru, "alyans", "atasay", "2026-07-24")
        _kayit_yaz(self.vertikal_klasoru, "alyans", "trendyol", "2026-07-24")
        _kayit_yaz(self.vertikal_klasoru, "gelinlik", "trendyol", "2026-07-24")
        rapor = self.vertikal_klasoru / "alyans_capraz-dogrulama_2026-07-24.json"
        rapor.write_text(json.dumps({
            "vertikal": "dugun", "kalem": "alyans", "tarih": "2026-07-24",
            "site_medyanlari": {"atasay": 19405, "trendyol": 4298},
            "fark_orani": 3.51, "esik_orani": 0.3, "uyari": True,
        }), encoding="utf-8")

        sonuc = agrega.vertikal_agregali("dugun", self.veri_kok)
        uyari = sonuc["kalemler"]["alyans"]["capraz_dogrulama_uyarisi"]
        self.assertIsNotNone(uyari)
        self.assertEqual(uyari["fark_yuzdesi"], 351.0)
        self.assertEqual(uyari["medyanlar"], {"atasay": 19405, "trendyol": 4298})
        self.assertIsNone(sonuc["kalemler"]["gelinlik"]["capraz_dogrulama_uyarisi"])

    def test_uyari_false_olan_rapor_yoksayilir(self):
        # motor.py, esigi asmayan kalemler icin de bir rapor dosyasi yazar
        # (bkz. capraz_dogrula() motor.py) - "uyari": false. Bu YANLISLIKLA
        # gercek bir uyariymis gibi agregali veriye eklenmemeli (2026-07-25
        # bug'inin bir parcasi olarak bulundu).
        _kayit_yaz(self.vertikal_klasoru, "salon", "dugunbuketi", "2026-07-24")
        _kayit_yaz(self.vertikal_klasoru, "salon", "trendyol", "2026-07-24")
        rapor = self.vertikal_klasoru / "salon_capraz-dogrulama_2026-07-24.json"
        rapor.write_text(json.dumps({
            "vertikal": "dugun", "kalem": "salon", "tarih": "2026-07-24",
            "site_medyanlari": {"dugunbuketi": 1000, "trendyol": 1100},
            "fark_orani": 0.1, "esik_orani": 0.3, "uyari": False,
        }), encoding="utf-8")

        sonuc = agrega.vertikal_agregali("dugun", self.veri_kok)
        self.assertIsNone(sonuc["kalemler"]["salon"]["capraz_dogrulama_uyarisi"])

    def test_karantina_klasoru_dahil_edilmez(self):
        # karantina alt klasordedir (vertikal klasorunun kendisi degil),
        # bu yuzden glob zaten sadece dogrudan iceriği tarar - guvenlik testi.
        _kayit_yaz(self.vertikal_klasoru, "gelinlik", "trendyol", "2026-07-24")
        karantina = self.veri_kok / "karantina"
        _kayit_yaz(karantina, "gelinlik", "supheli-site", "2026-07-24")

        sonuc = agrega.vertikal_agregali("dugun", self.veri_kok)
        siteler = {k["site"] for k in sonuc["kalemler"]["gelinlik"]["kaynaklar"]}
        self.assertEqual(siteler, {"trendyol"})


class YazTestleri(unittest.TestCase):
    def test_dosya_dogru_konuma_yazilir(self):
        with TemporaryDirectory() as veri_kok_str, TemporaryDirectory() as site_veri_kok_str:
            veri_kok = Path(veri_kok_str)
            site_veri_kok = Path(site_veri_kok_str)
            _kayit_yaz(veri_kok / "dugun", "gelinlik", "trendyol", "2026-07-24")

            hedef = agrega.yaz("dugun", veri_kok, site_veri_kok)

            self.assertEqual(hedef, site_veri_kok / "dugun.json")
            self.assertTrue(hedef.exists())
            veri = json.loads(hedef.read_text(encoding="utf-8"))
            self.assertEqual(veri["vertikal"], "dugun")
            self.assertIn("gelinlik", veri["kalemler"])


if __name__ == "__main__":
    unittest.main()


class SegmentTutarliligiTesti(unittest.TestCase):
    """Segmentler kaynaklar arasinda BAGIMSIZ hesaplandigi icin siralanma
    bozulabiliyor - bu tespit edilmezse 'orta segment ustten pahali' gibi
    bir tablo yayinlanir."""

    def _kayit(self, site, segmentler, urun):
        return {"site": site, "kaynak_adlari": [site], "tarih": "2026-08-05",
                "toplam_urun": urun, "genel_medyan": 1000, "saglikli": True,
                "segmentler": {
                    ad: {"min": v, "medyan": v, "max": v, "urun_sayisi": 5}
                    for ad, v in segmentler.items()
                }}

    def test_ust_segment_ortadan_ucuzsa_isaretlenir(self):
        """Gercek vaka (blender, 2026-07-26): bir kaynagin orneklemi
        kucuk oldugu icin ust segmenti hic olusmamis."""
        birlesik = agrega.kalem_birlestir([
            self._kayit("amazon", {"dusuk": 1399, "orta": 2389, "luks": 4762}, 47),
            self._kayit("trendyol", {"dusuk": 2749, "orta": 8659}, 8),  # luks YOK
        ])
        self.assertTrue(birlesik.get("segment_tutarsiz"))

    def test_duzgun_siralamada_isaret_yok(self):
        birlesik = agrega.kalem_birlestir([
            self._kayit("a", {"dusuk": 100, "orta": 200, "luks": 300}, 20),
            self._kayit("b", {"dusuk": 120, "orta": 220, "luks": 320}, 20),
        ])
        self.assertNotIn("segment_tutarsiz", birlesik)

    def test_eksik_segment_tek_basina_tutarsizlik_degil(self):
        """Bazi kalemlerde yalnizca bir segment var - bu bozukluk degil."""
        birlesik = agrega.kalem_birlestir([self._kayit("a", {"orta": 500}, 1)])
        self.assertNotIn("segment_tutarsiz", birlesik)
