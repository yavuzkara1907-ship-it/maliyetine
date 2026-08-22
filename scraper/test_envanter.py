# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import envanter
import yaml


class EnvanterTesti(unittest.TestCase):
    def test_yalnizca_aktif_kalem_tanimlari_doner(self):
        with TemporaryDirectory() as d:
            yol = Path(d) / "kaynaklar.yaml"
            yol.write_text(
                "kaynaklar:\n"
                "  - {vertikal: dugun, kalem: yeni, aktif: true}\n"
                "  - {vertikal: dugun, kalem: eski, aktif: false}\n"
                "  - {vertikal: okul, kalem: defter, aktif: true}\n",
                encoding="utf-8",
            )
            self.assertEqual(envanter.aktif_kalem_idleri("dugun", yol), {"yeni"})

    def test_ozet_tum_sayaclari_jsondan_hesaplar(self):
        with TemporaryDirectory() as d:
            kok = Path(d)
            (kok / "dugun.json").write_text(json.dumps({
                "guncelleme_tarihi": "2026-08-20",
                "kalemler": {
                    "a": {"kaynaklar": [{"site": "x", "toplam_urun": 3}]},
                    "b": {"kaynaklar": [{"site": "x", "toplam_urun": 2},
                                           {"site": "y", "toplam_urun": 4}]},
                },
            }), encoding="utf-8")
            ozet = envanter.envanter_ozeti(
                kok, {"dugun": {"liste_fiyati": True}, "olmayan": {}}
            )
            self.assertEqual(ozet["fiyat_serisi"], 2)
            self.assertEqual(ozet["kaynak"], 2)
            self.assertEqual(ozet["cok_kaynakli"], 1)
            self.assertEqual(ozet["tek_kaynak"], 1)
            self.assertEqual(ozet["liste_fiyati_tek_kaynak"], 1)
            self.assertEqual(ozet["perakende_hizmet_derinlik_acigi"], 0)
            self.assertEqual(ozet["vertikaller"]["dugun"]["tek_kaynak"], 1)
            self.assertTrue(ozet["vertikaller"]["dugun"]["liste_fiyati"])

    def test_bozuk_veya_bos_kaynak_tanimi_yayini_sessizce_sifirlamaz(self):
        with TemporaryDirectory() as d:
            yol = Path(d) / "kaynaklar.yaml"
            yol.write_text("kaynaklar: [", encoding="utf-8")
            with self.assertRaises(yaml.YAMLError):
                envanter.aktif_kalem_idleri("dugun", yol)

            yol.write_text("kaynaklar: []\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "aktif fiyat serisi"):
                envanter.aktif_kalem_idleri("dugun", yol)


if __name__ == "__main__":
    unittest.main()
