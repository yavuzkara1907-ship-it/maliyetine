# -*- coding: utf-8 -*-
"""CSV disa aktarim testleri - alintilanabilirlik bu dosyaya bagli."""
import csv
import json
import unittest
from datetime import date
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import veri_disa_aktar as vd


ORNEK = {
    "guncelleme_tarihi": "2026-08-05",
    "kalemler": {
        "buzdolabi": {
            "genel_medyan": 29000, "toplam_urun": 53,
            "birim_fiyatlari": {"kg": {"genel_medyan": 245.5, "eslesen_urun": 11}},
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

    def test_satir_dikey_tarihi_yerine_kalem_olcum_tarihini_kullanir(self):
        """Hedefli yenileme tum dikeyde ayni gun olcum yapilmis gibi gorunmemeli."""
        veri = json.loads(json.dumps(ORNEK))
        veri["guncelleme_tarihi"] = "2026-08-22"
        veri["kalemler"]["buzdolabi"]["guncelleme_tarihi"] = "2026-08-20"
        satir = dict(zip(vd.BASLIKLAR, vd._satirlar("ev-kurma", veri)[0]))
        self.assertEqual(satir["olcum_tarihi"], "2026-08-20")

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

    def test_olcum_turu_csvde_acik(self):
        satir = dict(zip(vd.BASLIKLAR, vd._satirlar("ev-kurma", ORNEK)[0]))
        self.assertEqual(satir["olcum_turu"], "kalem_fiyati")

        bebek = {
            "guncelleme_tarihi": "2026-08-20",
            "kalemler": {"bebek-bezi": ORNEK["kalemler"]["buzdolabi"]},
        }
        paket = dict(zip(vd.BASLIKLAR, vd._satirlar("bebek", bebek)[0]))
        self.assertEqual(paket["olcum_turu"], "paket_fiyati")

    def test_normalize_birim_fiyati_csvde_acik(self):
        satir = dict(zip(vd.BASLIKLAR, vd._satirlar("ev-kurma", ORNEK)[0]))
        self.assertEqual(satir["tl_kg"], 245.5)
        self.assertEqual(satir["kg_urun_sayisi"], 11)
        self.assertEqual(satir["tl_litre"], "")

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

    def test_tarihli_arsiv_ayni_tarihte_yeniden_yazilmaz(self):
        with TemporaryDirectory() as d:
            kok = Path(d) / "veri"; kok.mkdir()
            (kok / "ev-kurma.json").write_text(json.dumps(ORNEK), encoding="utf-8")
            cikti = Path(d) / "csv"; cikti.mkdir()
            arsiv = cikti / "ev-kurma-2026-08-05.csv"
            arsiv.write_text("yayindaki-degismez-surum", encoding="utf-8")
            vd.disa_aktar(veri_kok=kok, cikti_kok=cikti)
            self.assertEqual(arsiv.read_text(encoding="utf-8"), "yayindaki-degismez-surum")
            self.assertIn("buzdolabi", (cikti / "ev-kurma.csv").read_text(encoding="utf-8"))

    def test_bugunun_arsivi_hedefli_yeniden_olcumde_guncellenir(self):
        with TemporaryDirectory() as d:
            bugun = date.today().isoformat()
            veri = json.loads(json.dumps(ORNEK))
            veri["guncelleme_tarihi"] = bugun
            veri["kalemler"]["buzdolabi"]["guncelleme_tarihi"] = bugun
            kok = Path(d) / "veri"
            kok.mkdir()
            (kok / "ev-kurma.json").write_text(
                json.dumps(veri, ensure_ascii=False), encoding="utf-8"
            )
            cikti = Path(d) / "csv"
            cikti.mkdir()
            arsiv = cikti / f"ev-kurma-{bugun}.csv"
            arsiv.write_text("eski-ayni-gun", encoding="utf-8")
            vd.disa_aktar(veri_kok=kok, cikti_kok=cikti)
            self.assertNotEqual(
                arsiv.read_text(encoding="utf-8"), "eski-ayni-gun"
            )
            self.assertIn("buzdolabi", arsiv.read_text(encoding="utf-8"))

    def test_veri_yoksa_dosya_uretilmez(self):
        with TemporaryDirectory() as d:
            self.assertEqual(vd.disa_aktar(veri_kok=Path(d), cikti_kok=Path(d) / "c"), {})

    def test_veri_sayfasi_datacatalog_ve_lisans(self):
        sayfa = vd.veri_sayfasi(
            {"ev-kurma": {"kalem": 42, "tarih": "2026-08-05",
                           "dosya": "/veri/csv/ev-kurma.csv",
                           "arsiv": "/veri/csv/ev-kurma-2026-08-05.csv"}},
            manifest={"dataset_surumu": "2026-08-05-abcdef1234567890"},
        )
        blok = sayfa.split('<script type="application/ld+json">')[1].split("</script>")[0]
        graf = json.loads(blok)["@graph"]
        self.assertEqual(graf[0]["@type"], "DataCatalog")
        self.assertIn("creativecommons", graf[0]["license"])
        self.assertIn("ölçüm tarihini", sayfa)
        self.assertIn("ücretsiz kalır", sayfa)
        self.assertIn("sürümlenmiş sorgu API'si", sayfa)
        self.assertIn("aynı dosyayı yeniden satmaz", sayfa)
        self.assertIn("2026-08-05-abcdef1234567890", sayfa)
        self.assertIn("/veri/qa.json", sayfa)

    def test_ai_haritasi_veri_araclarini_formul_diye_gostermez(self):
        ozet = {"ev-kurma": {"kalem": 1, "tarih": "2026-08-05",
                              "dosya": "/veri/csv/ev-kurma.csv"}}
        llms = vd.llms_txt(ozet, "2026-08-05")
        ai = vd.ai_txt(ozet, "2026-08-05")
        self.assertIn("Bütçem Yeter mi?", llms)
        self.assertIn("İki tür araç vardır", llms)
        import hesaplayicilar as hc
        formul = len(hc.HESAPLAYICILAR)
        veri = len(hc.tum_hesaplayicilar()) - formul
        self.assertIn(f"{formul} formül/mevzuat", ai)
        self.assertIn(f"{veri} güncel veriye dayalı", ai)

    def test_llms_hesaplayici_dosyasi_henuz_yokken_de_tam_listeyi_verir(self):
        """AI haritasi build adimi sirasina bagli olmamali."""
        ozet = {"ev-kurma": {"kalem": 1, "tarih": "2026-08-05",
                              "dosya": "/veri/csv/ev-kurma.csv"}}
        llms = vd.llms_txt(ozet, "2026-08-05")
        import hesaplayicilar as hc
        for hesap in hc.tum_hesaplayicilar():
            self.assertIn(f"/{hc.HESAP_KOK}/{hesap['slug']}/", llms)

    def test_ai_haritasi_build_gununu_olcum_tarihi_diye_yazmaz(self):
        ozet = {
            "dugun": {"tarih": "2026-08-05"},
            "ev-kurma": {"tarih": "2026-08-20"},
        }
        self.assertEqual(vd.son_olcum_tarihi(ozet), "2026-08-20")


if __name__ == "__main__":
    unittest.main()
