# -*- coding: utf-8 -*-
"""enflasyon.py testleri - resmi TUFE verisi bizim TL fiyatlarimizla karistirilmamali."""
import unittest
from unittest import mock

import enflasyon
import rehber


ORNEK_ITEMS = [
    {"Tarih": "2026-01", "TP_FE25_OKTG01": "115.73", "TP_FE25_OKTG19": "116.00",
     "TP_FE25_OKTG20": "115.00", "TP_FE25_OKTG25": "119.64", "TP_FE25_OKTG22": "118.51"},
    {"Tarih": "2026-06", "TP_FE25_OKTG01": "129.99", "TP_FE25_OKTG19": "130.00",
     "TP_FE25_OKTG20": "121.67", "TP_FE25_OKTG25": "130.78", "TP_FE25_OKTG22": "133.44"},
]


class SayiTesti(unittest.TestCase):
    def test_binlik_ayiraci_virgul(self):
        """EVDS '3,683.83' biciminde doner - binde bir hatasi olmamali."""
        self.assertEqual(enflasyon._sayi("3,683.83"), 3683.83)
        self.assertEqual(enflasyon._sayi("129.99"), 129.99)

    def test_bos_ve_bozuk(self):
        for x in (None, "", "null", "abc"):
            self.assertIsNone(enflasyon._sayi(x))


class DerlemeTesti(unittest.TestCase):
    def test_degisim_dogru_hesaplanir(self):
        with mock.patch.object(enflasyon, "tufe_cek", return_value=ORNEK_ITEMS):
            v = enflasyon.derle(2026)
        self.assertEqual(v["olcumler"], ["2026-01", "2026-06"])
        genel = v["gruplar"]["TP.FE25.OKTG01"]
        self.assertAlmostEqual(genel["degisim_yuzde"], 12.3, places=1)
        self.assertIsNone(genel["vertikal"])

    def test_tek_olcum_grubu_disarida_birakir(self):
        """Degisim hesaplanamayan seri yayinlanmaz."""
        with mock.patch.object(enflasyon, "tufe_cek", return_value=ORNEK_ITEMS[:1]):
            v = enflasyon.derle(2026)
        self.assertEqual(v["gruplar"], {})

    def test_api_bos_donerse_uydurma_veri_yok(self):
        with mock.patch.object(enflasyon, "tufe_cek", return_value=[]):
            v = enflasyon.derle(2026)
        self.assertEqual(v["gruplar"], {})


class RehberEntegrasyonTesti(unittest.TestCase):
    def _veri(self):
        with mock.patch.object(enflasyon, "tufe_cek", return_value=ORNEK_ITEMS):
            return {"enflasyon": enflasyon.derle(2026)}

    def test_tufe_blogu_uretilir_ve_kaynak_belirtilir(self):
        html = rehber._tufe(self._veri(), "dugun")
        self.assertIn("TÜİK", html)
        self.assertIn("TCMB EVDS", html)
        self.assertIn("%12.3", html)

    def test_enflasyon_verisi_yoksa_blok_hic_cikmaz(self):
        self.assertEqual(rehber._tufe({}, "dugun"), "")
        self.assertEqual(rehber._tufe({"enflasyon": {"gruplar": {}}}, "dugun"), "")

    def test_ilgisiz_vertikal_icin_blok_cikmaz(self):
        self.assertEqual(rehber._tufe(self._veri(), "arac"), "")

    def test_tufe_bizim_TL_tutarlarimizla_karistirilmaz(self):
        """Endeks degeri TL gibi sunulmamali."""
        html = rehber._tufe(self._veri(), "dugun")
        self.assertNotIn("115.73 TL", html)
        self.assertIn("TL cinsinden gerçek fiyatları izler", html)


if __name__ == "__main__":
    unittest.main()
