# -*- coding: utf-8 -*-
"""gecmis.py testleri - zaman serisi ve orneklem gurultusu korumasi."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import gecmis


def kayit(kalem, site, tarih, medyan, urun=10):
    return kalem, site, tarih, {
        "kalem": kalem, "site": site, "tarih": tarih, "saglikli": True,
        "toplam_urun": urun, "genel_medyan": medyan, "segmentler": {},
    }


class GecmisTestleri(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.kok = Path(self.tmp.name)
        (self.kok / "dugun").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _yaz(self, *kayitlar):
        for kalem, site, tarih, veri in kayitlar:
            (self.kok / "dugun" / f"{kalem}_{site}_{tarih}.json").write_text(
                json.dumps(veri, ensure_ascii=False), encoding="utf-8")

    def test_aylik_aralikta_degisim_hesaplanir(self):
        self._yaz(kayit("gelinlik", "trendyol", "2026-07-25", 10000),
                  kayit("gelinlik", "trendyol", "2026-08-25", 11000))
        g = gecmis.vertikal_gecmisi("dugun", self.kok)
        k = g["kalemler"]["gelinlik"]
        self.assertEqual(k["degisim_yuzde"], 10.0)
        self.assertEqual(k["gun_araligi"], 31)
        self.assertEqual(len(k["seri"]), 2)

    def test_COK_YAKIN_olcumler_karsilastirilmaz(self):
        """Regresyon: 24->25 Temmuz testinde 'nikah sekeri %40 dustu'
        cikmisti - gercek fiyat dususu degil, bir gunde listelenen
        urunlerin degismesi (orneklem gurultusu). Boyle bir rakami
        yayinlamak KIRMIZI CIZGI ihlali olurdu."""
        self._yaz(kayit("nikah-sekeri", "trendyol", "2026-07-24", 489),
                  kayit("nikah-sekeri", "trendyol", "2026-07-25", 294))
        g = gecmis.vertikal_gecmisi("dugun", self.kok)
        k = g["kalemler"]["nikah-sekeri"]
        self.assertIsNone(k.get("degisim_yuzde"))
        self.assertEqual(len(k["seri"]), 2)          # seri yine de tutulur
        self.assertEqual(g["ozet"]["karsilastirilabilir"], 0)

    def test_ayni_tarihte_cok_kaynak_medyan_of_medyan(self):
        self._yaz(kayit("alyans", "atasay", "2026-07-25", 20000),
                  kayit("alyans", "trendyol", "2026-07-25", 4000))
        g = gecmis.vertikal_gecmisi("dugun", self.kok)
        n = g["kalemler"]["alyans"]["son"]
        self.assertEqual(n["medyan"], 12000)   # medyan([20000, 4000])
        self.assertEqual(n["kaynak"], 2)
        self.assertEqual(n["urun"], 20)

    def test_sifir_urunlu_ve_saglıksiz_kayit_seriye_girmez(self):
        _, _, _, bos = kayit("davetiye", "trendyol", "2026-07-25", None, urun=0)
        _, _, _, hasta = kayit("davetiye", "cimri", "2026-08-25", 100)
        hasta["saglikli"] = False
        self._yaz(("davetiye", "trendyol", "2026-07-25", bos),
                  ("davetiye", "cimri", "2026-08-25", hasta))
        g = gecmis.vertikal_gecmisi("dugun", self.kok)
        self.assertNotIn("davetiye", g["kalemler"])

    def test_ozet_artan_azalan_sayar(self):
        self._yaz(kayit("a", "s", "2026-07-01", 100), kayit("a", "s", "2026-08-01", 110),
                  kayit("b", "s", "2026-07-01", 100), kayit("b", "s", "2026-08-01", 90),
                  kayit("c", "s", "2026-07-01", 100), kayit("c", "s", "2026-08-01", 100))
        o = gecmis.vertikal_gecmisi("dugun", self.kok)["ozet"]
        self.assertEqual((o["artan"], o["azalan"], o["sabit"]), (1, 1, 1))
        self.assertEqual(o["medyan_degisim_yuzde"], 0.0)

    def test_tek_olcum_varsa_degisim_yok(self):
        self._yaz(kayit("gelinlik", "trendyol", "2026-07-25", 10000))
        k = gecmis.vertikal_gecmisi("dugun", self.kok)["kalemler"]["gelinlik"]
        self.assertIsNone(k.get("degisim_yuzde"))
        self.assertEqual(k["ilk"], k["son"])

    def test_kalem_sirasi_deterministik(self):
        self._yaz(kayit("z-kalem", "site", "2026-07-25", 200),
                  kayit("a-kalem", "site", "2026-07-25", 100))
        g = gecmis.vertikal_gecmisi("dugun", self.kok)
        self.assertEqual(list(g["kalemler"]), ["a-kalem", "z-kalem"])

    def test_aktif_envanter_filtresi_eski_seriyi_yayinlamaz(self):
        self._yaz(kayit("salon", "site", "2026-07-25", 500),
                  kayit("salon-yemekli", "site", "2026-08-20", 1200))
        g = gecmis.vertikal_gecmisi(
            "dugun", self.kok, aktif_kalemler={"salon-yemekli"}
        )
        self.assertEqual(set(g["kalemler"]), {"salon-yemekli"})
