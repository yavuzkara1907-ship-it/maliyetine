# -*- coding: utf-8 -*-
"""Icerik tabanli veri surumu testleri."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import veri_surumu


class VeriSurumuTesti(unittest.TestCase):
    def _hazirla(self, kok: Path, fiyat: int = 1000):
        veri = kok / "veri"
        (veri / "gecmis").mkdir(parents=True, exist_ok=True)
        (veri / "csv").mkdir(exist_ok=True)
        (veri / "ornek.json").write_text(json.dumps({
            "guncelleme_tarihi": "2026-08-20",
            "kalemler": {"a": {
                "genel_medyan": fiyat,
                "guncelleme_tarihi": "2026-08-20",
            }},
        }), encoding="utf-8")
        (veri / "gecmis" / "ornek.json").write_text("{}", encoding="utf-8")
        (veri / "csv" / "ornek.csv").write_text("a,b\n", encoding="utf-8")
        return veri

    def test_ayni_icerik_ayni_surumu_uretir(self):
        with TemporaryDirectory() as d:
            kok = Path(d)
            veri = self._hazirla(kok)
            a = veri_surumu.manifest_uret(veri, {"ornek": {}}, kok)
            b = veri_surumu.manifest_uret(veri, {"ornek": {}}, kok)
            self.assertEqual(a["dataset_surumu"], b["dataset_surumu"])
            self.assertTrue(a["dataset_surumu"].startswith("2026-08-20-"))

    def test_guncel_json_degisince_surum_degisir(self):
        with TemporaryDirectory() as d:
            kok = Path(d)
            veri = self._hazirla(kok)
            once = veri_surumu.manifest_uret(veri, {"ornek": {}}, kok)
            self._hazirla(kok, fiyat=1200)
            sonra = veri_surumu.manifest_uret(veri, {"ornek": {}}, kok)
            self.assertNotEqual(once["dataset_surumu"], sonra["dataset_surumu"])

    def test_manifest_sonradan_degisikligi_yakalar(self):
        with TemporaryDirectory() as d:
            kok = Path(d)
            veri = self._hazirla(kok)
            manifest = veri_surumu.manifest_uret(veri, {"ornek": {}}, kok)
            self.assertEqual(veri_surumu.manifest_hatalari(manifest, kok), [])
            (veri / "csv" / "ornek.csv").write_text("degisti", encoding="utf-8")
            self.assertEqual(
                veri_surumu.manifest_hatalari(manifest, kok),
                ["ornek/guncel_csv: SHA-256 manifestten farkli"],
            )


if __name__ == "__main__":
    unittest.main()
