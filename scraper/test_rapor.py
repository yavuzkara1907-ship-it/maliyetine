# -*- coding: utf-8 -*-
"""Maliyet raporu ve Google disi dagitim ciktisi testleri."""

from __future__ import annotations

import json
import unittest
import xml.etree.ElementTree as ET

import rapor
import sayfa_uret as su


class RaporTesti(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.veri = rapor.rapor_verisi()

    def test_envanter_ve_endeksler_kanonik_veriden_gelir(self):
        self.assertEqual(
            self.veri["envanter"]["fiyat_serisi"],
            sum(len(json.loads((su.SITE_KOK / "veri" / f"{v}.json").read_text())["kalemler"])
                for v in su.VERTIKALLER),
        )
        self.assertEqual(len(self.veri["endeksler"]), len(su.VERTIKALLER))

    def test_rapor_tum_endeksleri_ve_paylasim_yollarini_tasir(self):
        sayfa = rapor.rapor_html(self.veri)
        for o in self.veri["endeksler"]:
            self.assertIn(o["ad"], sayfa)
            self.assertIn(su._para(o["toplam"]), sayfa)
        for ifade in ("WhatsApp", "LinkedIn", "RSS ile takip edin", "Alıntıyı kopyala"):
            self.assertIn(ifade, sayfa)
        self.assertIn('aria-current="page"', sayfa)

    def test_degisimler_yalniz_guclu_kaynak_esigini_gecer(self):
        for aday in self.veri["degisimler"]:
            conf = su.VERTIKALLER[aday["vertikal"]]
            self.assertTrue(aday["kaynak_sayisi"] >= 2 or conf.get("liste_fiyati"))

    def test_rss_gecerli_xml_ve_surume_ozgu_guid_tasir(self):
        kok = ET.fromstring(rapor.rss_xml(self.veri))
        self.assertEqual(kok.tag, "rss")
        guid = kok.findtext("./channel/item/guid")
        self.assertIn(self.veri["dataset_surumu"] or self.veri["tarih"], guid)

    def test_makine_ozeti_tarih_ve_kapsam_tasir(self):
        veri = rapor.rapor_json(self.veri)
        self.assertEqual(veri["son_veri"], self.veri["tarih"])
        self.assertEqual(len(veri["endeksler"]), len(su.VERTIKALLER))
        self.assertTrue(all(x["kapsam"] and x["son_veri"] for x in veri["endeksler"]))


if __name__ == "__main__":
    unittest.main()
