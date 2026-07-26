# -*- coding: utf-8 -*-
"""Asistan testleri - KIRMIZI CIZGI: uydurma cevap URETEMEZ."""
import json
import re
import unittest

import asistan
import sayfa_uret as su


class AsistanVerisiTesti(unittest.TestCase):

    def setUp(self):
        self.v = asistan.asistan_verisi()

    def test_yalnizca_olculmus_kalemler(self):
        self.assertTrue(self.v["kalemler"])
        for k in self.v["kalemler"]:
            self.assertTrue(k["orta"], k["ad"])
            self.assertTrue(k["kaynak"] >= 1, k["ad"])
            self.assertTrue(k["tarih"], k["ad"])

    def test_her_kalem_var_olan_sayfaya_baglanir(self):
        for k in self.v["kalemler"]:
            self.assertTrue((su.SITE_KOK / k["yol"].strip("/") / "index.html").exists(),
                            f'{k["ad"]} -> {k["yol"]}')

    def test_fiyatlar_endeks_verisiyle_ayni(self):
        """Asistan farkli rakam soylerse guven biter."""
        veri = json.loads(
            (su.SITE_KOK / "veri" / "ev-kurma.json").read_text(encoding="utf-8"))["kalemler"]
        k = next(x for x in self.v["kalemler"] if x["ad"] == "Buzdolabı")
        self.assertEqual(k["orta"], su.kalem_deger(veri["buzdolabi"], "orta"))

    def test_hesap_katsayilari_gercek_hesapla_ayni(self):
        for vert, h in self.v["hesaplar"].items():
            conf = su.VERTIKALLER[vert]
            km = json.loads(
                (su.SITE_KOK / "veri" / f"{vert}.json").read_text(encoding="utf-8"))["kalemler"]
            for seg, kat in h["segmentler"].items():
                for olcek in (1, 80, 200):
                    gercek, _ = su.ornek_toplam_hesapla(conf, km, olcek=olcek, segment=seg)
                    self.assertEqual(kat["sabit"] + kat["kisi"] * olcek, gercek,
                                     f"{vert}/{seg}/{olcek}")

    def test_segment_tutarsiz_kalem_isaretli(self):
        """Tutarsiz kalemde asistan da segment SOYLEMEMELI."""
        veri = json.loads(
            (su.SITE_KOK / "veri" / "ev-kurma.json").read_text(encoding="utf-8"))["kalemler"]
        tutarsiz = {k for k, x in veri.items() if x.get("segment_tutarsiz")}
        if not tutarsiz:
            self.skipTest("su an tutarsiz kalem yok")
        adlar = {su._kisa_kalem_adi(t["ad"]) for t in su.VERTIKALLER["ev-kurma"]["kalemler"]
                 if t["id"] in tutarsiz}
        for k in self.v["kalemler"]:
            if k["ad"] in adlar:
                self.assertTrue(k["segmentsiz"], k["ad"])


class AsistanJsTesti(unittest.TestCase):

    def setUp(self):
        self.js = asistan.asistan_js(asistan.asistan_verisi())

    def test_dil_modeli_veya_disari_istek_YOK(self):
        """Halusinasyon 'dikkatli prompt' meselesi degil: model yok ki
        uydursun. Disari istek de yok - veri gomulu."""
        for yasak in ["fetch(", "XMLHttpRequest", "openai", "api.", "eval("]:
            self.assertNotIn(yasak, self.js, f"asistan disari cikiyor: {yasak}")

    def test_eslesmeyen_soruya_uydurma_yok(self):
        self.assertIn("Bunu ölçmüyorum", self.js)
        self.assertIn("tahmin yürütmüyorum", self.js)

    def test_gomulu_veri_gecerli_json(self):
        ham = self.js.split("var D = ", 1)[1].split(";\n", 1)[0]
        d = json.loads(ham)
        self.assertEqual(set(d), {"kalemler", "hesaplar", "gruplar", "kapsam_disi", "yontem"})

    def test_her_kalem_cevabinda_kaynak_ve_tarih_var(self):
        """Rakam verip kaynagini soylememek bu sitenin yapmayacagi sey."""
        self.assertIn("üründen, ", self.js)
        self.assertIn("as-kaynak", self.js)


if __name__ == "__main__":
    unittest.main()
