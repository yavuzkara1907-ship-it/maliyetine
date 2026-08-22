# -*- coding: utf-8 -*-
"""Urun miktari ve beyaz esya niteligi normalizasyon testleri."""

import unittest

import urun_normalizasyonu as un


class MiktarAyristirmaTestleri(unittest.TestCase):
    def test_kg_gram_ve_ondalik(self):
        self.assertEqual(un.miktarlari_ayristir("Kedi maması 1,5 kg"), {"kg": 1.5})
        self.assertEqual(un.miktarlari_ayristir("Yavru mama 1500 gr"), {"kg": 1.5})

    def test_coklu_paket_toplam_miktari_verir(self):
        self.assertEqual(un.miktarlari_ayristir("Yaş mama 12 x 85 g"), {"kg": 1.02})
        self.assertEqual(un.miktarlari_ayristir("Ped 2 paket 40 adet"), {"adet": 80.0})

    def test_adet_yazimlari(self):
        self.assertEqual(un.miktarlari_ayristir("Bebek bezi 120 adet"), {"adet": 120.0})
        self.assertEqual(un.miktarlari_ayristir("Ekonomik paket 40'lı"), {"adet": 40.0})

    def test_promosyon_miktarlari_toplanir(self):
        self.assertEqual(un.miktarlari_ayristir("Köpek maması 15 kg + 2 kg"), {"kg": 17.0})
        self.assertEqual(un.miktarlari_ayristir("Kedi maması 5+2 kg hediyeli"), {"kg": 7.0})

    def test_agirlik_araligi_paket_miktari_sayilmaz(self):
        self.assertEqual(un.miktarlari_ayristir("1-10 kg köpekler için mama"), {})

    def test_kumda_kg_ve_litre_birbirine_cevrilmez(self):
        self.assertEqual(
            un.miktarlari_ayristir("Kedi kumu 10 litre 8,5 kg"),
            {"kg": 8.5, "litre": 10.0},
        )


class BirimFiyatTestleri(unittest.TestCase):
    def test_yalnizca_sozlesmeli_kalemde_ozet_uretilir(self):
        urunler = [{"isim": "Mama 2 kg", "fiyat": 600}]
        self.assertEqual(un.birim_fiyat_ozeti("koltuk", urunler), {})
        self.assertEqual(un.birim_fiyat_ozeti("kedi-mamasi", urunler)["kg"]["genel_medyan"], 300)

    def test_eslesmeyen_urun_oranda_gorunur(self):
        urunler = [
            {"isim": "Mama 2 kg", "fiyat": 600},
            {"isim": "Gramajı yazmayan mama", "fiyat": 500},
        ]
        ozet = un.birim_fiyat_ozeti("kedi-mamasi", urunler)["kg"]
        self.assertEqual(ozet["eslesen_urun"], 1)
        self.assertEqual(ozet["toplam_urun"], 2)
        self.assertEqual(ozet["eslesme_orani"], 0.5)

    def test_kg_mamaya_ek_adetli_urun_karismaz(self):
        urunler = [{"isim": "Kuru mama 2 kg + 2 adet yaş mama", "fiyat": 900}]
        self.assertEqual(un.birim_fiyat_ozeti("kedi-mamasi", urunler), {})

    def test_kaynaklar_ham_urunleri_karistirmadan_birlesir(self):
        kayitlar = [
            {"site": "a", "birim_fiyatlari": {"kg": {
                "genel_medyan": 200, "eslesen_urun": 10, "toplam_urun": 12,
                "segmentler": {}, "ornek_urunler": [],
            }}},
            {"site": "b", "birim_fiyatlari": {"kg": {
                "genel_medyan": 400, "eslesen_urun": 4, "toplam_urun": 8,
                "segmentler": {}, "ornek_urunler": [],
            }}},
        ]
        ozet = un.birim_fiyatlarini_birlestir(kayitlar)["kg"]
        self.assertEqual(ozet["genel_medyan"], 300)
        self.assertEqual(ozet["eslesen_urun"], 14)
        self.assertEqual(ozet["toplam_urun"], 20)
        self.assertEqual(ozet["kaynak_sayisi"], 2)


class FirinOzellikTestleri(unittest.TestCase):
    def test_acikca_yazilan_nitelikler_ayristirilir(self):
        n = un.firin_ozelliklerini_ayristir(
            "Bosch HSG7361B1 Ankastre Fırın 71 L A+ Enerji Sınıfı Buhar Destekli"
        )
        self.assertEqual(n["marka"], "Bosch")
        self.assertEqual(n["model"], "HSG7361B1")
        self.assertEqual(n["urun_turu"], "ankastre-firin")
        self.assertEqual(n["kapasite_litre"], 71)
        self.assertEqual(n["enerji_sinifi"], "A+")
        self.assertIn("buhar-destekli", n["ozellikler"])

    def test_urun_turleri_birbirinden_ayrilir(self):
        self.assertEqual(
            un.firin_ozelliklerini_ayristir("Beko 3'lü Ankastre Set")["urun_turu"],
            "ankastre-set",
        )
        self.assertEqual(
            un.firin_ozelliklerini_ayristir("Vestel Ocaklı Fırın")["urun_turu"],
            "ocakli-firin",
        )

    def test_model_ve_enerji_sinifi_tahmin_edilmez(self):
        n = un.firin_ozelliklerini_ayristir("Ankastre fırın siyah")
        self.assertNotIn("model", n)
        self.assertNotIn("enerji_sinifi", n)

    def test_pilot_baska_kaleme_yayilmaz(self):
        self.assertEqual(
            un.firin_ozellik_ozeti("buzdolabi", [{"isim": "Bosch 70 L", "fiyat": 10000}]),
            {},
        )


class AracModelTestleri(unittest.TestCase):
    def test_opel_satirlari_model_bazinda_gruplanir_varyant_kaybolmaz(self):
        urunler = [
            {"isim": "Opel Corsa 1.2 100 HP Benzin MT6 Edition", "fiyat": 1535000},
            {"isim": "Opel Corsa Hybrid 1.2 145 e-DCT6 GS", "fiyat": 2119000},
            {"isim": "Yeni Opel Astra 1.5 130 HP Dizel AT8 Edition", "fiyat": 2360000},
            {"isim": "Opel Astra 1.5 130 HP Dizel AT8 GS", "fiyat": 2590000},
            {"isim": "Opel Bilinmeyen 1.2 Paket", "fiyat": 1900000},
        ]
        ozet = un.arac_model_ozeti("opel", urunler)
        self.assertEqual(ozet["toplam_urun"], 5)
        self.assertEqual(ozet["ozellik_eslesen_urun"], 4)
        self.assertEqual(set(ozet["modeller"]), {"corsa", "astra"})
        self.assertEqual(ozet["modeller"]["corsa"]["urun_sayisi"], 2)
        self.assertIn("Edition", ozet["modeller"]["corsa"]["varyantlar"][0]["isim"])

    def test_katalog_disindaki_model_tahmin_edilmez(self):
        self.assertIsNone(un._arac_modelini_bul("opel", "Opel Hayali GS 1.2"))
        self.assertEqual(un._arac_modelini_bul("renault", "Yeni Clio evolution TCe"), "Clio")

    def test_kaynak_aliasi_model_ailesine_baglanir(self):
        self.assertEqual(un._arac_modelini_bul("mercedes", "C 200 4MATIC AMG"), "C-Serisi")
        self.assertEqual(
            un._arac_modelini_bul("mercedes", "Mercedes-AMG C 43 4MATIC Performance"),
            "C-Serisi",
        )
        self.assertEqual(un._arac_modelini_bul("bmw", "BMW i5eDrive40 Edition"), "i5")

    def test_model_varyantlari_agregada_kaynakla_korunur(self):
        ham = un.arac_model_ozeti("opel", [
            {"isim": "Opel Corsa 1.2 MT6 Edition", "fiyat": 1535000},
            {"isim": "Opel Corsa Hybrid e-DCT6 GS", "fiyat": 2119000},
        ])
        birlesik = un.ozellik_ozetlerini_birlestir([
            {"site": "liste", "ozellik_ozeti": ham}
        ])
        varyantlar = birlesik["modeller"]["corsa"]["varyantlar"]
        self.assertEqual(len(varyantlar), 2)
        self.assertEqual(varyantlar[0]["site"], "liste")


class GenisKategoriTestleri(unittest.TestCase):
    def test_oto_ve_outdoor_buzdolabi_ev_tipi_sayilmaz(self):
        for ad in (
            "ICECO 12/24Volt Kompresörlü Outdoor Oto Buzdolabı",
            "Portatif kamp buzdolabı",
        ):
            self.assertEqual(un.genis_kategori_urun_turu("buzdolabi", ad), {})
        self.assertEqual(
            un.genis_kategori_urun_turu("buzdolabi", "Bosch No Frost Buzdolabı"),
            {"urun_turu": "standart"},
        )

    def test_kedi_tuvaleti_alt_turleri_ayrilir(self):
        urunler = [
            {"isim": "Akıllı otomatik kedi tuvaleti", "fiyat": 12000},
            {"isim": "Filtreli kapalı kedi tuvaleti", "fiyat": 1500},
            {"isim": "Açık kum kabı", "fiyat": 400},
        ]
        ozet = un.urun_ozellik_ozeti("kedi-tuvaleti", urunler)
        self.assertEqual(
            set(ozet["urun_turleri"]),
            {"otomatik-tuvalet", "kapali-tuvalet", "acik-tuvalet"},
        )

    def test_kahve_makinesi_tipleri_fiyatla_tahmin_edilmez(self):
        self.assertEqual(
            un.genis_kategori_urun_turu("kahve-makinesi", "Kahve makinesi 49.999 TL"),
            {},
        )
        self.assertEqual(
            un.genis_kategori_urun_turu("kahve-makinesi", "Filtre kahve makinesi"),
            {"urun_turu": "filtre"},
        )


if __name__ == "__main__":
    unittest.main()
