# -*- coding: utf-8 -*-
"""Uretilmis yayin paketinin QA kapisi entegrasyon testi."""

import unittest
from datetime import date

import qa


class QaKapisiTesti(unittest.TestCase):
    def test_yayindaki_paket_kritik_hatasiz(self):
        rapor = qa.rapor_uret(bugun=date(2026, 8, 22))
        self.assertEqual(
            rapor["kritik_hatalar"], [],
            "Yayin paketi QA kapisindan gecemedi",
        )
        self.assertEqual(rapor["durum"], "gecti")
        self.assertEqual(
            rapor["ozet"]["fiyat_serisi"],
            sum(len((qa._json_oku(qa.SITE_KOK / "veri" / f"{v}.json").get("kalemler") or {}))
                for v in qa.su.VERTIKALLER),
        )


if __name__ == "__main__":
    unittest.main()
