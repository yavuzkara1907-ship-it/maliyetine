# -*- coding: utf-8 -*-
"""CSV disa aktarim testleri - alintilanabilirlik bu dosyaya bagli."""
import csv
import json
import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import veri_disa_aktar as vd


ORNEK = {
    "guncelleme_tarihi": "2026-08-05",
    "kalemler": {
        "buzdolabi": {
            "genel_medyan": 29000, "toplam_urun": 53,
            "segmentler": {"dusuk": {"medyan": 15196, "min": 6299},
                           "orta": {"medyan": 30552},
                           "luks": {"medyan": 47734, "max": 61990}},
            "kaynaklar": [{"site": "trendyol", "toplam_urun": 25},
                          {"site": "amazon", "toplam_urun": 28},
                          {"site": "bos-kaynak", "toplam_urun": 0}],
        },
    },
}


class CsvTesti(unittest.TestCase):

    def test_bom_var(self):
        """Excel BOM'suz UTF-8'i bozuyor: 'Buzdolabı' -> 'BuzdolabÄ±'."""
        m = vd.csv_metni([["a"] * len(vd.BASLIKLAR)])
        self.assertTrue(m.startswith("﻿"))

    def test_satir_kaynak_ve_tarih_icerir(self):
        """Rakamin dogrulanabilir olmasi icin ikisi de SART."""
        s = vd._satirlar("ev-kurma", ORNEK)
        self.assertEqual(len(s), 1)
        satir = dict(zip(vd.BASLIKLAR, s[0]))
        self.assertEqual(satir["olcum_tarihi"], "2026-08-05")
        self.assertEqual(satir["kaynaklar"], "amazon; trendyol")
        self.assertEqual(satir["kaynak_sayisi"], 2)

    def test_urun_dondurmeyen_kaynak_sayilmaz(self):
        s = vd._satirlar("ev-kurma", ORNEK)
        self.assertNotIn("bos-kaynak", dict(zip(vd.BASLIKLAR, s[0]))["kaynaklar"])

    def test_segment_degerleri_dogru_sutunda(self):
        satir = dict(zip(vd.BASLIKLAR, vd._satirlar("ev-kurma", ORNEK)[0]))
        self.assertEqual(satir["ekonomik_tl"], 15196)
        self.assertEqual(satir["orta_tl"], 30552)
        self.assertEqual(satir["ust_tl"], 47734)
        self.assertEqual(satir["en_dusuk_tl"], 6299)
        self.assertEqual(satir["en_yuksek_tl"], 61990)

    def test_csv_gercekten_ayristirilabilir(self):
        m = vd.csv_metni(vd._satirlar("ev-kurma", ORNEK))
        okunan = list(csv.reader(StringIO(m.lstrip("﻿"))))
        self.assertEqual(okunan[0], vd.BASLIKLAR)
        self.assertEqual(len(okunan), 2)

    def test_hem_sabit_hem_tarihli_dosya(self):
        """Sabit URL linklenebilir, tarihli surum eski yaziyi dogrular."""
        with TemporaryDirectory() as d:
            kok = Path(d) / "veri"; kok.mkdir()
            (kok / "ev-kurma.json").write_text(json.dumps(ORNEK), encoding="utf-8")
            cikti = Path(d) / "csv"
            ozet = vd.disa_aktar(veri_kok=kok, cikti_kok=cikti)
            self.assertIn("ev-kurma", ozet)
            self.assertTrue((cikti / "ev-kurma.csv").exists())
            self.assertTrue((cikti / "ev-kurma-2026-08-05.csv").exists())
            self.assertTrue((cikti / "tum-kalemler.csv").exists())

    def test_veri_yoksa_dosya_uretilmez(self):
        with TemporaryDirectory() as d:
            self.assertEqual(vd.disa_aktar(veri_kok=Path(d), cikti_kok=Path(d) / "c"), {})

    def test_veri_sayfasi_datacatalog_ve_lisans(self):
        sayfa = vd.veri_sayfasi({"ev-kurma": {"kalem": 42, "tarih": "2026-08-05",
                                              "dosya": "/veri/csv/ev-kurma.csv",
                                              "arsiv": "/veri/csv/ev-kurma-2026-08-05.csv"}})
        blok = sayfa.split('<script type="application/ld+json">')[1].split("</script>")[0]
        graf = json.loads(blok)["@graph"]
        self.assertEqual(graf[0]["@type"], "DataCatalog")
        self.assertIn("creativecommons", graf[0]["license"])
        self.assertIn("ölçüm tarihini", sayfa)


if __name__ == "__main__":
    unittest.main()
