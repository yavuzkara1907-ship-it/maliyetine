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


if __name__ == "__main__":
    unittest.main()
