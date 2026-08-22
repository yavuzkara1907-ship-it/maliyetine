# -*- coding: utf-8 -*-
"""rehber.py testleri - yazilarin rakamlari VERIDEN gelmeli, elle yazilmamali."""
import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import rehber


DUGUN_VERI = {
    "vertikal": "dugun",
    "guncelleme_tarihi": "2026-08-15",
    "kalemler": {
        "gelinlik": {"genel_medyan": 9000, "toplam_urun": 20,
                     "segmentler": {"orta": {"medyan": 9000}, "dusuk": {"medyan": 5000},
                                    "luks": {"medyan": 15000}}},
        "salon-yemekli": {"genel_medyan": 1000, "toplam_urun": 11,
                          "segmentler": {"orta": {"medyan": 1000}, "dusuk": {"medyan": 700},
                                         "luks": {"medyan": 2000}}},
        "salon-kokteyl": {"genel_medyan": 500, "toplam_urun": 10,
                          "segmentler": {"orta": {"medyan": 500}, "dusuk": {"medyan": 300},
                                         "luks": {"medyan": 900}}},
    },
}

KEDI_VERI = {
    "vertikal": "kedi",
    "guncelleme_tarihi": "2026-08-20",
    "kalemler": {
        "kedi-yatagi": {
            "segmentler": {"dusuk": {"medyan": 3000}, "orta": {"medyan": 5000},
                            "luks": {"medyan": 8000}},
        },
        "kedi-kumu": {
            "segmentler": {"dusuk": {"medyan": 100}, "orta": {"medyan": 200},
                            "luks": {"medyan": 400}},
        },
        "kedi-mamasi": {
            "segmentler": {"dusuk": {"medyan": 500}, "orta": {"medyan": 800},
                            "luks": {"medyan": 1500}},
        },
    },
}


class RehberTesti(unittest.TestCase):

    def test_veri_yoksa_sayfa_URETILMEZ(self):
        """Bos/rakamsiz bir blog yazisi yayinlamak guven kaybi."""
        for r in rehber.REHBERLER:
            if r.get("kaynak_tipi") == "resmi":
                continue
            self.assertIsNone(rehber.rehber_uret(r, {}), r["slug"])

    def test_resmi_kaynakli_rehber_veri_istemeden_kaynak_gosterir(self):
        """Bazi rehberler fiyat olcumu degil, resmi kaynak okuma rehberi.

        Bunlar veri yokken de uretilebilir; ama kaynaklari gorunur olmak
        zorunda. Aksi halde "olcum yok" istisnasi kapi araligi olur.
        """
        r = next(x for x in rehber.REHBERLER
                 if x["slug"] == "kredi-karti-puanlari-nerede-gecer")
        html = rehber.rehber_uret(r, {})
        self.assertIsNotNone(html)
        self.assertIn("Bonus resmi marka listesi", html)
        self.assertIn("ParafPara resmi tanıtım sayfası", html)
        self.assertIn('"@type": "FAQPage"', html)
        self.assertNotIn("tarihli ölçümlerden", html)

    def test_rakamlar_veriden_gelir(self):
        r = next(x for x in rehber.REHBERLER if x["slug"] == "yemekli-mi-kokteyl-mi")
        html = rehber.rehber_uret(r, {"dugun": DUGUN_VERI})
        self.assertIsNotNone(html)
        self.assertIn("1.000 TL", html)   # yemekli
        self.assertIn("500 TL", html)     # kokteyl
        self.assertIn("75.000 TL", html)  # 150 kisilik fark: (1000-500)*150

    def test_evcil_rehberi_paket_fiyatini_ayliklastirmaz(self):
        r = next(x for x in rehber.REHBERLER if x["slug"] == "aylik-kedi-masrafi")
        html = rehber.rehber_uret(r, {"kedi": KEDI_VERI})
        self.assertIsNotNone(html)
        self.assertIn("1.000 TL", html)       # birer paket mama + kum
        self.assertNotIn("12.000 TL", html)   # paket toplami 12 ile carpilamaz
        self.assertNotRegex(html, r"ayda\s+1\.000 TL")
        self.assertNotRegex(html, r"yılda\s+12\.000 TL")
        cevap = re.search(r'<p class="cevap-blok">(.*?)</p>', html, re.S).group(1)
        self.assertNotIn("5.000 TL", cevap)  # tek seferlik yatak ayliga karismaz

    def test_veriden_uretilen_sss_gorunur_ve_schema_ile_ayni(self):
        r = next(x for x in rehber.REHBERLER if x["slug"] == "aylik-kedi-masrafi")
        html = rehber.rehber_uret(r, {"kedi": KEDI_VERI})
        self.assertIn("2026'da aylık kedi masrafı ne kadar?", html)
        graf = json.loads(
            re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1)
        )["@graph"]
        faq = next(x for x in graf if x["@type"] == "FAQPage")
        self.assertIn("1.000 TL", faq["mainEntity"][0]["acceptedAnswer"]["text"])

    def test_jsonld_gecerli_ve_article(self):
        r = next(x for x in rehber.REHBERLER if x["slug"] == "yemekli-mi-kokteyl-mi")
        html = rehber.rehber_uret(r, {"dugun": DUGUN_VERI})
        bloklar = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        self.assertTrue(bloklar)
        graf = json.loads(bloklar[0])["@graph"]
        self.assertEqual(graf[0]["@type"], "Article")
        self.assertEqual(graf[1]["@type"], "BreadcrumbList")

    def test_diger_rehberlere_ic_link_verir(self):
        r = next(x for x in rehber.REHBERLER if x["slug"] == "yemekli-mi-kokteyl-mi")
        html = rehber.rehber_uret(r, {"dugun": DUGUN_VERI})
        self.assertIn("/rehber/150-kisilik-dugun-maliyeti/", html)
        # kendine link vermemeli
        self.assertNotIn('href="/rehber/yemekli-mi-kokteyl-mi/"', html)

    def test_yazilan_dosyalar_ve_dizin(self):
        with TemporaryDirectory() as d:
            veri_kok = Path(d) / "veri"
            veri_kok.mkdir()
            (veri_kok / "dugun.json").write_text(json.dumps(DUGUN_VERI), encoding="utf-8")
            hedef = Path(d) / "rehber"
            yazilan = rehber.rehberleri_yaz(veri_kok=veri_kok, hedef_kok=hedef)
            slugler = {r["slug"] for r in yazilan}
            # Sadece dugun verisi var -> ev-kurma ve arac rehberleri yazilmamali
            self.assertIn("yemekli-mi-kokteyl-mi", slugler)
            self.assertNotIn("sifirdan-ev-kurma-listesi", slugler)
            self.assertTrue((hedef / "index.html").exists())
            dizin = (hedef / "index.html").read_text()
            self.assertNotIn("sifirdan-ev-kurma-listesi", dizin)

    def test_yapay_zeka_klise_kaliplari_yok(self):
        """Yavuz'un talimati: 'yapay zeka gibi degil, gercekci'."""
        html = rehber.rehber_uret(
            next(x for x in rehber.REHBERLER if x["slug"] == "yemekli-mi-kokteyl-mi"),
            {"dugun": DUGUN_VERI})
        for kalip in ["Unutmayın ki", "Sonuç olarak", "Peki ya", "Kısacası",
                      "bu yazıda", "ele alacağız", "Umarız"]:
            self.assertNotIn(kalip.lower(), html.lower(), f"klise kalip: {kalip}")


    def test_basliklarda_rakam_gomulu_degil(self):
        """Rakam metne gomulmez - veri degisince baslik yalana doner.

        Bu testi yazmaya sebep olan gercek hata (2026-07-31): damatlik
        yazisinin basligi "3 Bin Liralik da Var, 165 Bin Liralik da"
        idi. Ikisi de o anki olcumden geliyordu; bir sonraki olcumde
        min/max degisince baslik sessizce yanlis olacakti - govdedeki
        rakam guncellenirken baslik donmus kalir.
        """
        import re
        # "150 kisilik", "45 kalemde", "2026" gibi SABIT kavramlar serbest;
        # yasak olan olculen para tutari (bin/milyon/TL ile birlikte).
        para = re.compile(r"\d[\d.,]*\s*(bin|milyon|tl|₺)", re.I)
        for r in rehber.REHBERLER:
            for alan in ("baslik", "seo_baslik", "meta"):
                metin = r[alan]
                self.assertIsNone(
                    para.search(metin),
                    "{}/{} icinde gomulu para tutari var: {!r}".format(
                        r["slug"], alan, metin))

if __name__ == "__main__":
    unittest.main()


class GrupYuzdesiTesti(unittest.TestCase):
    """Varsayilan-kapali kalemler grup yuzdelerini sismemeli."""

    def test_okul_grup_toplami_yillik_toplami_asmaz(self):
        import sayfa_uret as su
        conf = su.VERTIKALLER["okul"]
        veri = {k["id"]: {"genel_medyan": 1000, "toplam_urun": 20,
                          "segmentler": {"orta": {"medyan": 1000},
                                         "dusuk": {"medyan": 500},
                                         "luks": {"medyan": 2000}}}
                for k in conf["kalemler"]}
        html = rehber.rehber_uret(
            next(r for r in rehber.REHBERLER if r["slug"] == "okul-masrafi-ne-kadar"),
            {"okul": {"kalemler": veri, "guncelleme_tarihi": "2026-08-01"}})
        self.assertIsNotNone(html)
        yuzdeler = [int(x) for x in re.findall(r'class="sayi">%(\d+)</td>', html)]
        self.assertTrue(yuzdeler, "grup tablosu uretilmedi")
        self.assertLessEqual(sum(yuzdeler), 101, f"grup yuzdeleri %100'u asiyor: {yuzdeler}")

    def test_tek_seferlik_kalemler_gruplarda_yok(self):
        import sayfa_uret as su
        conf = su.VERTIKALLER["okul"]
        veri = {k["id"]: {"genel_medyan": 1000, "toplam_urun": 20,
                          "segmentler": {"orta": {"medyan": 1000}}}
                for k in conf["kalemler"]}
        html = rehber.rehber_uret(
            next(r for r in rehber.REHBERLER if r["slug"] == "okul-masrafi-ne-kadar"),
            {"okul": {"kalemler": veri, "guncelleme_tarihi": "2026-08-01"}})
        # Teknoloji ve Calisma alani gruplari toplam tablosunda OLMAMALI
        tablo = re.search(r'<h2>Para nereye gidiyor\?</h2>(.*?)</table>', html, re.S).group(1)
        self.assertNotIn("Teknoloji", tablo)
        self.assertNotIn("Çalışma alanı", tablo)


class PaketFiyatiIddiaTesti(unittest.TestCase):
    @staticmethod
    def _vertikal_verisi(vertikal: str) -> dict:
        import sayfa_uret as su
        kalemler = {
            k["id"]: {
                "genel_medyan": 1000,
                "toplam_urun": 20,
                "segmentler": {
                    "dusuk": {"medyan": 500},
                    "orta": {"medyan": 1000},
                    "luks": {"medyan": 2000},
                },
            }
            for k in su.VERTIKALLER[vertikal]["kalemler"]
        }
        return {"kalemler": kalemler, "guncelleme_tarihi": "2026-08-20"}

    def test_evcil_ve_bebek_rehberleri_paketi_ayliklastirmiyor(self):
        veri = {
            v: self._vertikal_verisi(v) for v in ("kedi", "kopek", "bebek")
        }
        for slug in (
            "aylik-kedi-masrafi", "aylik-kopek-masrafi",
            "kedi-mi-kopek-mi-masrafli", "bebek-masraflari-ilk-yil",
            "kedi-sahiplenmeden-once", "kopek-sahiplenmeden-once",
            "bebek-alisverisinde-nelere-dikkat",
        ):
            tanim = next(r for r in rehber.REHBERLER if r["slug"] == slug)
            html = rehber.rehber_uret(tanim, veri)
            self.assertIsNotNone(html, slug)
            self.assertNotRegex(html, r"ayda\s+[\d.]+\s+TL", slug)
            self.assertNotRegex(html, r"yılda\s+[\d.]+\s+TL", slug)
            self.assertNotIn("12.000 TL", html, slug)
