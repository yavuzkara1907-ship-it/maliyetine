import unittest

import arac_maliyetleri as am


class AracMaliyetleriTesti(unittest.TestCase):
    def test_resmi_2026_mtv_tutarlari(self):
        self.assertEqual(am.hesapla(2_000_000, 1300, ["mtv"])["ek_toplam"], 6902)
        self.assertEqual(am.hesapla(2_000_000, 1600, ["mtv"])["ek_toplam"], 12028)
        self.assertEqual(am.hesapla(2_000_000, 1800, ["mtv"])["ek_toplam"], 21251)
        self.assertEqual(am.hesapla(2_000_000, 2000, ["mtv"])["ek_toplam"], 33474)

    def test_ilk_tescil_harci_uydurma_sabit_ucret_eklemez(self):
        sonuc = am.hesapla(3_000_000, 1600, ["noter_tescil"])
        self.assertEqual(sonuc["ek_toplam"], 6000)
        self.assertIn("dahil değildir", sonuc["detaylar"][0]["not"])

    def test_js_python_kaynak_verisinden_uretilir(self):
        metin = am.javascript_metni()
        self.assertIn('"tutar": 21251', metin)
        self.assertIn("OTOMATIK URETILIR", metin)
        self.assertNotIn("sabit_ucret", metin)
        self.assertEqual(am.JS_CIKTI.read_text(encoding="utf-8"), metin)

    def test_hesaplayici_secimleri_ortak_sozlesmeden_kurulur(self):
        sayfa = (am.SITE_KOK / "arac" / "hesaplayici" / "index.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('<select id="motor-cc"></select>', sayfa)
        self.assertIn("ARAC_EK_MALIYETLER.mtv.kademeler", sayfa)
        self.assertNotIn("Noter + ilk tescil harcı", sayfa)

    def test_statistik_metodoloji_eski_tarifeyi_tasimaz(self):
        metodoloji = (am.SITE_KOK / "arac" / "metodoloji" / "index.html").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("6.903 TL", metodoloji)
        self.assertNotIn("21.252 TL", metodoloji)
        self.assertNotIn("sabit noter ücreti", metodoloji)


if __name__ == "__main__":
    unittest.main()
