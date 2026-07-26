# -*- coding: utf-8 -*-
"""sayfa_uret.py testleri - agregali veriden dogru rakamlarin hesaplandigini
ve veri yokken UYDURULMUS bir rakam gostermedigini dogrular (KIRMIZI CIZGI)."""

import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import sayfa_uret


GELINLIK_VERISI = {
    "genel_medyan": 5000,
    "kaynak_sayisi": 2,
    "capraz_dogrulama_uyarisi": None,
    "segmentler": {
        "dusuk": {"min": 2000, "medyan": 3000, "max": 4000, "urun_sayisi": 10},
        "orta": {"min": 4001, "medyan": 5000, "max": 7000, "urun_sayisi": 12},
        "luks": {"min": 7001, "medyan": 15000, "max": 30000, "urun_sayisi": 5},
    },
}

SALON_YEMEKLI_VERISI = {
    "genel_medyan": 1000,
    "kaynak_sayisi": 1,
    "capraz_dogrulama_uyarisi": None,
    "segmentler": {
        "orta": {"min": 1000, "medyan": 1100, "max": 1500, "urun_sayisi": 6},
    },
}


DUGUN = sayfa_uret.VERTIKALLER["dugun"]
EV_KURMA = sayfa_uret.VERTIKALLER["ev-kurma"]


class KalemDegerTestleri(unittest.TestCase):
    def test_veri_yoksa_none_doner(self):
        self.assertIsNone(sayfa_uret.kalem_deger(None, "orta"))

    def test_segment_varsa_medyanini_doner(self):
        self.assertEqual(sayfa_uret.kalem_deger(GELINLIK_VERISI, "luks"), 15000)

    def test_segment_yoksa_genel_medyana_duser(self):
        veri = {"genel_medyan": 999, "segmentler": {}}
        self.assertEqual(sayfa_uret.kalem_deger(veri, "luks"), 999)


class OrnekToplamHesaplaTestleri(unittest.TestCase):
    # DUGUN_KALEMLERI_TAHMINI (Yavuz'un 2026-07-24 talimatiyla eklenen genel
    # piyasa arastirmasi degerleri) davetli_sayisi=100, segment="orta" icin.
    # yemek-ikram KASITLI YOK: bilgi_amacli, hicbir senaryoda toplanmaz.
    # taki-altin da YOK: 2026-07-25'te tahminiden gercek kaynaga tasindi
    # (Atasay altin bilezik). Kalan 6 tahmini kalem:
    # 2026-07-26: fotografci, organizasyon, kuafor-makyaj ve gelin-arabasi
    # da gercek kaynaga (dugun.com Istanbul tablolari) tasindi. Kalan 2
    # tahmini kalem: orkestra-dj + nikah-islemleri
    TAHMINI_TOPLAM_100_ORTA = 25000 + 3500  # 28500

    def test_sabit_ve_kisi_basi_kalemler_dogru_toplanir(self):
        kalemler = {"gelinlik": GELINLIK_VERISI, "salon-yemekli": SALON_YEMEKLI_VERISI}
        toplam, detaylar = sayfa_uret.ornek_toplam_hesapla(DUGUN, kalemler, olcek=100, segment="orta")
        # gelinlik: 5000 (sabit, gercek) + salon-yemekli: 1100*100=110000
        # + tahmini kalemlerin toplami (her zaman dahil olur).
        self.assertEqual(toplam, 5000 + 110000 + self.TAHMINI_TOPLAM_100_ORTA)
        gelinlik_satir = next(d for d in detaylar if d["id"] == "gelinlik")
        self.assertTrue(gelinlik_satir["veri_var"])
        self.assertFalse(gelinlik_satir["tahmini_mi"])
        self.assertEqual(gelinlik_satir["satir_toplam"], 5000)

    def test_gercek_kaynagi_olmayan_kalem_kendi_basina_toplama_katilmaz(self):
        toplam, detaylar = sayfa_uret.ornek_toplam_hesapla(DUGUN, {}, olcek=100, segment="orta")
        gercek_detaylar = [d for d in detaylar if d["id"] in {t["id"] for t in sayfa_uret.DUGUN_KALEMLERI}]
        self.assertTrue(all(not d["veri_var"] for d in gercek_detaylar))
        self.assertEqual(len(gercek_detaylar), len(sayfa_uret.DUGUN_KALEMLERI))
        # Ama tahmini kalemler HER ZAMAN dahil olur (veri_var=True, tahmini_mi=True).
        tahmini_detaylar = [d for d in detaylar if d["id"] not in {t["id"] for t in sayfa_uret.DUGUN_KALEMLERI}]
        self.assertEqual(len(tahmini_detaylar), len(sayfa_uret.DUGUN_KALEMLERI_TAHMINI))
        self.assertTrue(all(d["veri_var"] and d["tahmini_mi"] for d in tahmini_detaylar))
        self.assertEqual(toplam, self.TAHMINI_TOPLAM_100_ORTA)

    def test_tahmini_kalem_segmentine_gore_dogru_deger_verir(self):
        _, detaylar = sayfa_uret.ornek_toplam_hesapla(DUGUN, {}, olcek=1, segment="luks")
        orkestra = next(d for d in detaylar if d["id"] == "orkestra-dj")
        self.assertEqual(orkestra["birim_fiyat"], 80000)
        self.assertTrue(orkestra["tahmini_mi"])


SALON_KOKTEYL_VERISI = {
    "genel_medyan": 550,
    "kaynak_sayisi": 1,
    "capraz_dogrulama_uyarisi": None,
    "kaynaklar": [{"site": "dugunbuketi"}],
    "segmentler": {
        "orta": {"min": 600, "medyan": 800, "max": 990, "urun_sayisi": 3},
    },
}


class CiftSayimKorumasiTestleri(unittest.TestCase):
    """Salon iki varyantli (yemekli/kokteyl) ve "yemekli" menu dahil kisi
    basi fiyattir. Endeks sayfasinin varsayilan senaryosunda yalnizca BIR
    varyant ve yemekli ile cakisan "yemek-ikram" HARIC toplanmali - aksi
    halde ayni salon iki kez, ayni yemek iki kez sayilir."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.veri_dosyasi = Path(self.tmp.name) / "dugun.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_secilmeyen_salon_varyanti_toplama_girmez(self):
        kalemler = {
            "salon-yemekli": SALON_YEMEKLI_VERISI,
            "salon-kokteyl": SALON_KOKTEYL_VERISI,
        }
        toplam, detaylar = sayfa_uret.ornek_toplam_hesapla(DUGUN, kalemler, olcek=100, segment="orta")
        yemekli = next(d for d in detaylar if d["id"] == "salon-yemekli")
        kokteyl = next(d for d in detaylar if d["id"] == "salon-kokteyl")
        # Ikisi de tabloda GORUNUR (fiyati var)...
        self.assertTrue(yemekli["veri_var"] and kokteyl["veri_var"])
        # ...ama toplama yalnizca yemekli girer.
        self.assertTrue(yemekli["toplama_dahil"])
        self.assertFalse(kokteyl["toplama_dahil"])
        self.assertEqual(toplam, 1100 * 100 + self.__class__._tahmini())

    @staticmethod
    def _tahmini():
        # OrnekToplamHesaplaTestleri.TAHMINI_TOPLAM_100_ORTA ile ayni deger
        # (taki-altin ve yemek-ikram artik tahmini degil).
        return 25000 + 3500  # 28500

    def test_yemek_kalemi_varsayilan_senaryoda_toplama_girmez(self):
        # yemek-ikram 2026-07-25'te tahminiden GERCEK kaynaga tasindi -
        # artik degeri kazinan veriden gelir (ayni mekanin yemekli/kokteyl
        # farki). Veri VARKEN tabloda gorunur ama varsayilan senaryoda
        # (yemekli salon secili) toplama girmez.
        kalemler = {
            "yemek-ikram": {
                "genel_medyan": 250, "kaynak_sayisi": 1,
                "capraz_dogrulama_uyarisi": None,
                "kaynaklar": [{"site": "dugunbuketi"}],
                "segmentler": {"orta": {"min": 200, "medyan": 250, "max": 920, "urun_sayisi": 5}},
            }
        }
        toplam, detaylar = sayfa_uret.ornek_toplam_hesapla(DUGUN, kalemler, olcek=100, segment="orta")
        yemek = next(d for d in detaylar if d["id"] == "yemek-ikram")
        self.assertTrue(yemek["veri_var"])          # tabloda gorunur
        self.assertFalse(yemek["tahmini_mi"])       # artik TAHMINI DEGIL
        self.assertFalse(yemek["toplama_dahil"])    # ama toplamda degil
        self.assertEqual(toplam, self._tahmini())   # yemek 250*100 EKLENMEDI

    def test_bilgi_amacli_kalem_HICBIR_senaryoda_toplanmaz(self):
        # yemek-ikram olculmus bir deger tasir ama toplama girmez:
        # "kokteyl + menu bedeli" tanim geregi "yemekli"ye esit olmali
        # (fark = yemekli - kokteyl), ayri kalem olarak toplamak ayni
        # sayiya dolambacli yoldan gitmektir. Ustelik segmentler bagimsiz
        # hesaplandigi icin esitlik pratikte bozuluyor (%24).
        yemek_verisi = {
            "genel_medyan": 400, "kaynak_sayisi": 1,
            "capraz_dogrulama_uyarisi": None,
            "kaynaklar": [{"site": "dugunbuketi"}],
            "segmentler": {"orta": {"min": 400, "medyan": 410, "max": 500, "urun_sayisi": 3}},
        }
        for kalemler in ({"yemek-ikram": yemek_verisi},
                         {"yemek-ikram": yemek_verisi, "salon-kokteyl": SALON_KOKTEYL_VERISI}):
            toplam, detaylar = sayfa_uret.ornek_toplam_hesapla(
                DUGUN, kalemler, olcek=100, segment="orta"
            )
            yemek = next(d for d in detaylar if d["id"] == "yemek-ikram")
            self.assertTrue(yemek["veri_var"])        # degeri var, tabloda gorunur
            self.assertFalse(yemek["toplama_dahil"])  # ama ASLA toplanmaz
            self.assertEqual(toplam, self._tahmini())

    def test_bilgi_amacli_kalem_tabloda_acikca_isaretlenir(self):
        agregali = {
            "vertikal": "dugun", "guncelleme_tarihi": "2026-07-25",
            "kalemler": {"yemek-ikram": {
                "genel_medyan": 400, "kaynak_sayisi": 1, "segmentler": {},
                "capraz_dogrulama_uyarisi": None, "kaynaklar": [{"site": "dugunbuketi"}],
            }},
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")
        html = sayfa_uret.sayfa_uret("dugun", self.veri_dosyasi)
        self.assertIn("Bilgi amaçlı — toplamda değil", html)

    def test_yemek_kalemi_artik_tahmini_listede_degil(self):
        # KIRMIZI CIZGI kurali: gercek kaynak bulununca kalem tahmini
        # listeden CIKARILIR. Ikisinde birden bulunmasi cift sayima ve
        # "Tahmini" etiketinin yanlis gorunmesine yol acar.
        tahmini_idler = {t["id"] for t in DUGUN["tahmini_kalemler"]}
        gercek_idler = {t["id"] for t in DUGUN["kalemler"]}
        self.assertIn("yemek-ikram", gercek_idler)
        self.assertNotIn("yemek-ikram", tahmini_idler)
        self.assertEqual(tahmini_idler & gercek_idler, set())

    def test_kirilim_ornek_toplamla_TUTAR(self):
        # Regresyon: "gercek X TL + tahmini Y TL" kirilimi, gosterilen
        # toplamla aritmetik olarak tutmali. Toplama girmeyen kalemler
        # kirilimda da sayilmamali - yoksa okuyucu rakamlari toplayip
        # farkli bir sonuca ulasir ve guven zedelenir.
        agregali = {
            "vertikal": "dugun", "guncelleme_tarihi": "2026-07-25",
            "kalemler": {
                "salon-yemekli": SALON_YEMEKLI_VERISI,
                "salon-kokteyl": SALON_KOKTEYL_VERISI,
                "gelinlik": GELINLIK_VERISI,
            },
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")
        html = sayfa_uret.sayfa_uret("dugun", self.veri_dosyasi)

        conf = DUGUN
        olcek = conf["olcek_varsayilan"]
        toplam, detaylar = sayfa_uret.ornek_toplam_hesapla(
            conf, agregali["kalemler"], olcek, sayfa_uret.ORNEK_SEGMENT
        )
        dahil = [d for d in detaylar if d["veri_var"] and d.get("toplama_dahil", True)]
        gercek = sum(d["satir_toplam"] for d in dahil if not d["tahmini_mi"])
        tahmini = sum(d["satir_toplam"] for d in dahil if d["tahmini_mi"])
        self.assertEqual(gercek + tahmini, toplam)
        # Uc rakamin hepsi sayfada gorunmeli.
        for n in (toplam, gercek, tahmini):
            self.assertIn(sayfa_uret._para(n), html)

    def test_toplama_girmeyen_satir_tabloda_isaretlenir(self):
        agregali = {
            "vertikal": "dugun", "guncelleme_tarihi": "2026-07-25",
            "kalemler": {
                "salon-yemekli": SALON_YEMEKLI_VERISI,
                "salon-kokteyl": SALON_KOKTEYL_VERISI,
            },
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")
        html = sayfa_uret.sayfa_uret("dugun", self.veri_dosyasi)
        self.assertIn("Toplamda değil", html)


class IcerikSeoTestleri(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.veri_dosyasi = Path(self.tmp.name) / "ev-kurma.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_endeks_sayfasinda_gorunur_icerik_bloklari_var(self):
        agregali = {
            "vertikal": "ev-kurma",
            "guncelleme_tarihi": "2026-07-25",
            "kalemler": {"buzdolabi": BUZDOLABI_VERISI},
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")
        html = sayfa_uret.sayfa_uret("ev-kurma", self.veri_dosyasi)
        self.assertIn("Bu rakama neler dahil?", html)
        self.assertIn("Bu rakama neler dahil değil?", html)
        self.assertIn("En yüksek maliyet kalemleri", html)
        self.assertIn("Segmentler nasıl okunmalı?", html)
        self.assertIn("/ev-kurma/buzdolabi-fiyatlari/", html)

    def test_tabloda_eksik_segment_genel_medyana_dusmez(self):
        televizyon = {
            "genel_medyan": 46499,
            "kaynak_sayisi": 1,
            "toplam_urun": 4,
            "guncelleme_tarihi": "2026-07-25",
            "kaynaklar": [{"site": "trendyol", "toplam_urun": 4, "genel_medyan": 46499}],
            "segmentler": {
                "dusuk": {"medyan": 33999},
                "orta": {"medyan": 87499},
            },
        }
        html = sayfa_uret._kalem_satirlari_html(EV_KURMA, {"televizyon": televizyon})
        televizyon_satiri = next(
            satir for satir in html.splitlines() if "Televizyon (4K)" in satir
        )
        self.assertIn("87.499 TL", televizyon_satiri)
        self.assertIn('<td class="sayi">—</td>', televizyon_satiri)
        self.assertNotIn("46.499 TL</td></tr>", html)

    def test_kalem_sayfasi_uretilir(self):
        agregali = {
            "vertikal": "ev-kurma",
            "guncelleme_tarihi": "2026-07-25",
            "kalemler": {"buzdolabi": BUZDOLABI_VERISI},
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")
        html = sayfa_uret.kalem_sayfasi_uret(
            "ev-kurma", "buzdolabi-fiyatlari", self.veri_dosyasi
        )
        self.assertIn("2026'da Buzdolabı Fiyatları Ne Kadar?", html)
        self.assertIn("orta segment ortalama fiyatı", html)
        self.assertIn("28.930 TL", html)
        self.assertIn("/ev-kurma/hesaplayici/", html)

    def test_sitemap_kalem_sayfalarini_icerir(self):
        sitemap = sayfa_uret.sitemap_uret()
        self.assertIn("https://maliyetine.com.tr/dugun/gelinlik-fiyatlari/", sitemap)
        self.assertIn("https://maliyetine.com.tr/ev-kurma/buzdolabi-fiyatlari/", sitemap)


class SayfaUretTestleri(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.veri_dosyasi = Path(self.tmp.name) / "dugun.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_gercek_kaynak_hic_yoksa_tahmini_oldugu_acikca_belirtilir(self):
        # DUGUN_KALEMLERI_TAHMINI statik oldugu icin veri dosyasi olmasa
        # bile artik BIR rakam gosterilir (Yavuz'un 2026-07-24 talimatiyla) -
        # ama KIRMIZI CIZGI korunmali: bu rakamin TAMAMEN genel piyasa
        # arastirmasina dayandigi ve HICBIR kaleminin gercek/kazinan bir
        # kaynaktan gelmedigi metinde ACIKCA belirtilmeli, "bağımsız
        # kaynaktan derlenen" gibi guven veren bir ifade KULLANILMAMALI.
        html = sayfa_uret.sayfa_uret("dugun", self.veri_dosyasi)
        self.assertIn("TAMAMEN genel piyasa araştırmasına dayanıyor", html)
        self.assertNotIn("bağımsız kaynaktan derlenen", html)
        self.assertIn("Henüz güncellenmedi", html)

    def test_tum_gercek_kaynaklar_0_urun_donduyse_tahmini_oldugu_belirtilir(self):
        # Regresyon: kalemler sozlugu BOS DEGIL (kaynaklar calisti,
        # kaynak_sayisi>0) ama hepsi 0 urun dondugu icin genel_medyan=null
        # olabilir (ör. sandbox'ta network engeli). Bu durumda "gercek
        # kaynaktan geldi" izlenimi UYDURULMAMALI - sadece tahmini
        # kalemlerin toplami gosterilmeli, acikca isaretlenerek.
        agregali = {
            "vertikal": "dugun",
            "guncelleme_tarihi": "2026-07-24",
            "kalemler": {
                "gelinlik": {"genel_medyan": None, "kaynak_sayisi": 3, "segmentler": {}, "capraz_dogrulama_uyarisi": None},
                "damatlik": {"genel_medyan": None, "kaynak_sayisi": 5, "segmentler": {}, "capraz_dogrulama_uyarisi": None},
            },
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")

        html = sayfa_uret.sayfa_uret("dugun", self.veri_dosyasi)
        self.assertIn("TAMAMEN genel piyasa araştırmasına dayanıyor", html)
        self.assertNotIn("bağımsız kaynaktan derlenen", html)

    def test_gercek_veri_varsa_gercek_ve_tahmini_kismi_ayri_belirtilir(self):
        agregali = {
            "vertikal": "dugun",
            "guncelleme_tarihi": "2026-07-24",
            "kalemler": {"gelinlik": GELINLIK_VERISI, "salon-yemekli": SALON_YEMEKLI_VERISI},
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")

        html = sayfa_uret.sayfa_uret("dugun", self.veri_dosyasi)
        self.assertIn("Güncelleme: 2026-07-24", html)
        gercek_kismi = 5000 + 1100 * DUGUN["olcek_varsayilan"]
        self.assertIn(sayfa_uret._para(gercek_kismi), html)
        self.assertIn("bağımsız kaynaktan derlenen", html)
        self.assertIn("genel piyasa araştırmasına dayanır", html)
        self.assertIn('"@type": "FAQPage"', html)
        self.assertIn('"@type": "Dataset"', html)

    def test_capraz_dogrulama_uyarisi_sayfada_gorunur(self):
        uyarili_alyans = {
            "genel_medyan": 10000,
            "kaynak_sayisi": 2,
            "capraz_dogrulama_uyarisi": {"fark_yuzdesi": 351.0, "medyanlar": {"atasay": 19405, "trendyol": 4298}},
            "segmentler": {},
        }
        agregali = {
            "vertikal": "dugun", "guncelleme_tarihi": "2026-07-24",
            "kalemler": {"gelinlik": GELINLIK_VERISI},
        }
        # alyans kalemi DUGUN_KALEMLERI listesinde degil (bu test sadece
        # uyari render fonksiyonunu dogrudan kontrol ediyor).
        html_uyari = sayfa_uret._capraz_dogrulama_uyarilari_html(DUGUN, {"alyans": uyarili_alyans})
        self.assertIn("%351", html_uyari)
        self.assertIn("Alyans", html_uyari)

        html_uyarisiz = sayfa_uret._capraz_dogrulama_uyarilari_html(DUGUN, {"gelinlik": GELINLIK_VERISI})
        self.assertEqual(html_uyarisiz, "")


class EkSorularTestleri(unittest.TestCase):
    def test_eksik_segment_genel_medyani_segment_gibi_yazmaz(self):
        # Regresyon: one_cikan_kalemler FAQ metni, kalem_deger() fallback'ini
        # kullanirsa eksik "luks" segment yerine genel medyani "luks" diye
        # yazabilir. FAQ'ta yalnizca gercekten var olan segmentler soylenmeli.
        televizyon = {
            "genel_medyan": 46499,
            "kaynak_sayisi": 1,
            "toplam_urun": 4,
            "guncelleme_tarihi": "2026-07-25",
            "segmentler": {
                "dusuk": {"medyan": 33999},
                "orta": {"medyan": 87499},
            },
        }
        sorular = sayfa_uret.ek_sorular_uret(
            EV_KURMA, {"televizyon": televizyon}, EV_KURMA["olcek_varsayilan"]
        )
        televizyon_cevabi = next(
            s["acceptedAnswer"]["text"]
            for s in sorular
            if s["name"].startswith("Televizyon")
        )
        self.assertIn("orta segmentte 87.499 TL", televizyon_cevabi)
        self.assertNotIn("lüks segmentte", televizyon_cevabi)
        self.assertNotIn("46.499 TL", televizyon_cevabi)


BUZDOLABI_VERISI = {
    "genel_medyan": 28860,
    "kaynak_sayisi": 1,
    "capraz_dogrulama_uyarisi": None,
    "kaynaklar": [{"site": "trendyol", "tarih": "2026-07-25", "toplam_urun": 25}],
    "segmentler": {
        "dusuk": {"min": 6388, "medyan": 8829, "max": 15699, "urun_sayisi": 7},
        "orta": {"min": 18589, "medyan": 28930, "max": 36199, "urun_sayisi": 12},
        "luks": {"min": 37898, "medyan": 43299, "max": 62860, "urun_sayisi": 6},
    },
}


class BagimsizSitelerTestleri(unittest.TestCase):
    """Regresyon: "kac bagimsiz kaynak" ifadesi kalem basina kaynak_sayisi'nin
    TOPLAMI degil, BENZERSIZ SITE sayisi olmali. Ayni site 42 kalemi de
    besliyorsa bu "42 bagimsiz kaynak" DEGILDIR - okuyucuya 42 farkli site
    izlenimi vermek COK KAYNAK KURALI'ni yanlis temsil eder."""

    def test_ayni_site_birden_cok_kalemde_tekrar_sayilmaz(self):
        kalemler = {
            "buzdolabi": {"kaynaklar": [{"site": "trendyol"}]},
            "camasir-makinesi": {"kaynaklar": [{"site": "trendyol"}]},
            "gardirop": {"kaynaklar": [{"site": "trendyol"}]},
        }
        siteler = sayfa_uret.bagimsiz_siteler(kalemler, set(kalemler))
        self.assertEqual(siteler, {"trendyol"})

    def test_farkli_siteler_ayri_sayilir(self):
        kalemler = {
            "damatlik": {"kaynaklar": [{"site": "trendyol"}, {"site": "vakko"}]},
            "alyans": {"kaynaklar": [{"site": "atasay"}]},
        }
        siteler = sayfa_uret.bagimsiz_siteler(kalemler, set(kalemler))
        self.assertEqual(siteler, {"trendyol", "vakko", "atasay"})

    def test_kapsam_disi_kalemin_sitesi_sayilmaz(self):
        kalemler = {
            "gelinlik": {"kaynaklar": [{"site": "trendyol"}]},
            "salon": {"kaynaklar": [{"site": "dugunbuketi"}]},
        }
        siteler = sayfa_uret.bagimsiz_siteler(kalemler, {"gelinlik"})
        self.assertEqual(siteler, {"trendyol"})

    def test_urun_dondurmeyen_kaynak_sayilmaz(self):
        kalemler = {
            "gelinlik": {
                "kaynaklar": [
                    {"site": "akakce", "toplam_urun": 0, "genel_medyan": None},
                    {"site": "trendyol", "toplam_urun": 21, "genel_medyan": 8999},
                ]
            }
        }
        siteler = sayfa_uret.bagimsiz_siteler(kalemler, {"gelinlik"})
        self.assertEqual(siteler, {"trendyol"})


class TekKaynakUyarisiTestleri(unittest.TestCase):
    def test_tek_site_varsa_uyari_gosterilir(self):
        html = sayfa_uret._tek_kaynak_uyarisi_html(EV_KURMA, {"trendyol"})
        self.assertIn("Tek kaynak uyarısı", html)
        self.assertIn("Trendyol", html)

    def test_birden_cok_site_varsa_uyari_gosterilmez(self):
        html = sayfa_uret._tek_kaynak_uyarisi_html(DUGUN, {"trendyol", "vakko"})
        self.assertEqual(html, "")

    def test_hic_site_yoksa_uyari_gosterilmez(self):
        self.assertEqual(sayfa_uret._tek_kaynak_uyarisi_html(DUGUN, set()), "")


class EvKurmaVertikaliTestleri(unittest.TestCase):
    """Ev kurma vertikalinde HIC tahmini kalem yok - hepsi gercek kaynakli.
    Bu, KIRMIZI CIZGI acisindan dugun'den farkli bir kod yolu (tahmini
    bloklarinin hic devreye girmemesi) oldugu icin ayrica kilitleniyor."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.veri_dosyasi = Path(self.tmp.name) / "ev-kurma.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_tahmini_kalem_tanimli_degil(self):
        self.assertEqual(EV_KURMA["tahmini_kalemler"], [])

    def test_veri_yoksa_rakam_UYDURULMAZ(self):
        # Tahmini kalem olmadigi icin, veri de yoksa gosterilecek hicbir
        # dogrulanmis rakam yok - "0 TL" gibi guven veren bir sayi
        # UYDURULMAMALI.
        html = sayfa_uret.sayfa_uret("ev-kurma", self.veri_dosyasi)
        self.assertIn("Veri toplama süreci devam ediyor", html)
        self.assertNotIn("bağımsız kaynaktan derlenen", html)
        # Cevap blogunda hicbir para rakami olmamali.
        cevap = html.split('class="cevap-blok"')[1].split("</div>")[0]
        self.assertNotIn("TL", cevap)

    def test_gercek_veri_varsa_tamami_kaynakli_denir(self):
        agregali = {
            "vertikal": "ev-kurma",
            "guncelleme_tarihi": "2026-07-25",
            "kalemler": {"buzdolabi": BUZDOLABI_VERISI},
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")

        html = sayfa_uret.sayfa_uret("ev-kurma", self.veri_dosyasi)
        self.assertIn("Güncelleme: 2026-07-25", html)
        self.assertIn(sayfa_uret._para(28930), html)
        self.assertIn("bağımsız kaynaktan derlenen", html)
        # Tahmini kalem olmadigi icin "tahmini kismi" cumlesi HIC kurulmamali.
        self.assertNotIn("genel piyasa araştırmasına dayanır", html)
        self.assertIn("tamamı</strong> gerçek", html)
        # Tek site besliyor: "1 bağımsız kaynak" denmeli, kalem sayisi degil.
        self.assertIn("1 bağımsız kaynaktan derlenen", html)
        self.assertIn("Tek kaynak uyarısı", html)

    def test_kalem_gruplari_tabloda_basliklanir(self):
        agregali = {
            "vertikal": "ev-kurma", "guncelleme_tarihi": "2026-07-25",
            "kalemler": {"buzdolabi": BUZDOLABI_VERISI},
        }
        self.veri_dosyasi.write_text(json.dumps(agregali, ensure_ascii=False), encoding="utf-8")
        html = sayfa_uret.sayfa_uret("ev-kurma", self.veri_dosyasi)
        self.assertIn('<tr class="grup-satiri"><td colspan="5">Beyaz eşya</td></tr>', html)
        self.assertIn("Mutfak", html)

    def test_linkler_ve_kanonik_url_vertikale_gore_uretilir(self):
        html = sayfa_uret.sayfa_uret("ev-kurma", self.veri_dosyasi)
        self.assertIn('href="https://maliyetine.com.tr/ev-kurma/"', html)
        self.assertIn('href="/ev-kurma/hesaplayici/"', html)
        self.assertIn('href="/ev-kurma/metodoloji/"', html)
        self.assertNotIn("/dugun/", html)

    def test_bilinmeyen_vertikal_hata_verir(self):
        with self.assertRaises(ValueError):
            sayfa_uret.sayfa_uret("olmayan-vertikal")


if __name__ == "__main__":
    unittest.main()


class AnasayfaTestleri(unittest.TestCase):
    """Ana sayfa GEO'nun ilk temas noktasi. Onceki hali elle yazilmisti ve
    HIC RAKAM ICERMIYORDU. Artik build-time'da uretiliyor - ama veri yoksa
    rakam UYDURMAMALI (KIRMIZI CIZGI)."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.veri_kok = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _yaz(self, vertikal, kalemler, tarih="2026-07-25"):
        (self.veri_kok / f"{vertikal}.json").write_text(
            json.dumps({"vertikal": vertikal, "guncelleme_tarihi": tarih,
                        "kalemler": kalemler}, ensure_ascii=False),
            encoding="utf-8",
        )

    def test_veri_yoksa_rakam_UYDURULMAZ(self):
        html = sayfa_uret.anasayfa_uret(self.veri_kok)
        self.assertIn("Veri toplama süreci devam ediyor", html)
        cevap = html.split('class="cevap-blok"')[1].split("</div>")[0]
        self.assertNotIn("TL", cevap)

    def test_gercek_veri_varsa_rakam_cevap_blogunda_gorunur(self):
        self._yaz("dugun", {"gelinlik": GELINLIK_VERISI,
                            "salon-yemekli": SALON_YEMEKLI_VERISI})
        html = sayfa_uret.anasayfa_uret(self.veri_kok)
        beklenen = 5000 + 1100 * DUGUN["olcek_varsayilan"] + 28500
        self.assertIn(sayfa_uret._para(beklenen), html)
        self.assertIn("Güncelleme: 2026-07-25", html)

    def test_kalem_sayfalarina_ic_link_verir(self):
        # Yetim sayfa riskini azaltir: sitemap tek basina zayif sinyal.
        self._yaz("dugun", {"gelinlik": GELINLIK_VERISI})
        html = sayfa_uret.anasayfa_uret(self.veri_kok)
        for slug in ("gelinlik-fiyatlari", "damatlik-fiyatlari",
                     "alyans-fiyatlari", "dugun-salonu-fiyatlari"):
            self.assertIn(f'href="/dugun/{slug}/"', html)

    def test_schema_org_dogru_tipleri_icerir(self):
        self._yaz("dugun", {"gelinlik": GELINLIK_VERISI})
        html = sayfa_uret.anasayfa_uret(self.veri_kok)
        blok = re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                          html, re.S)[0]
        tipler = {n.get("@type") for n in json.loads(blok)["@graph"]}
        self.assertEqual(tipler, {"Organization", "WebSite", "ItemList", "FAQPage"})

    def test_verisi_olmayan_vertikal_yakinda_olarak_gosterilir(self):
        # ev-kurma verisi YOK -> rakam gosterilmemeli, kart "Yakinda"
        # olmali; ama dugun verisi varsa o normal gorunmeli.
        self._yaz("dugun", {"gelinlik": GELINLIK_VERISI})
        html = sayfa_uret.anasayfa_uret(self.veri_kok)
        self.assertIn("Düğün maliyeti", html)
        self.assertNotIn('href="/ev-kurma/"', html)

    def test_tahmini_kalemi_olmayan_vertikal_tamami_gercek_der(self):
        self._yaz("ev-kurma", {"buzdolabi": BUZDOLABI_VERISI})
        html = sayfa_uret.anasayfa_uret(self.veri_kok)
        self.assertIn("tamamı gerçek kaynaklı", html)


class EkKalemSayfalariTesti(unittest.TestCase):
    """Kalem sayfalarinin veriden genisletilmesi (uzun kuyruk SEO)."""

    def _conf(self):
        return {
            "ad": "Ev kurma",
            "yol": "ev-kurma",
            "kalemler": [
                {"id": "nevresim-takimi", "ad": "Nevresim Takımı", "birim": "sabit", "grup": "Tekstil"},
                {"id": "hali", "ad": "Halı", "birim": "sabit", "grup": "Tekstil"},
                {"id": "buzdolabi", "ad": "Buzdolabı", "birim": "sabit", "grup": "Beyaz eşya"},
            ],
            "kalem_sayfalari": [{"id": "buzdolabi", "slug": "buzdolabi-fiyatlari",
                                 "baslik": "b", "soru": "s", "aciklama": "a"}],
        }

    def test_asgari_orneklem_altindaki_kaleme_sayfa_acilmaz(self):
        """3 urunden 'X fiyatlari' sayfasi yapmak ince icerik olur."""
        veri = {
            "nevresim-takimi": {"genel_medyan": 950, "toplam_urun": 59},
            "hali": {"genel_medyan": 900, "toplam_urun": 3},
        }
        idler = {s["id"] for s in sayfa_uret._ek_kalem_sayfalari(self._conf(), veri)}
        self.assertIn("nevresim-takimi", idler)
        self.assertNotIn("hali", idler)

    def test_elle_tanimli_sayfa_tekrarlanmaz(self):
        veri = {"buzdolabi": {"genel_medyan": 28860, "toplam_urun": 25}}
        self.assertEqual(sayfa_uret._ek_kalem_sayfalari(self._conf(), veri), [])

    def test_verisi_olmayan_kaleme_sayfa_acilmaz(self):
        veri = {"nevresim-takimi": {"genel_medyan": None, "toplam_urun": 59}}
        self.assertEqual(sayfa_uret._ek_kalem_sayfalari(self._conf(), veri), [])

    def test_not_yazilmamis_kaleme_sayfa_acilmaz(self):
        """KALEM_SAYFA_NOTLARI'nda olmayan kalem = ozgun icerik yok = sayfa yok."""
        conf = self._conf()
        conf["kalemler"].append({"id": "uydurma-kalem", "ad": "Uydurma", "birim": "sabit"})
        veri = {"uydurma-kalem": {"genel_medyan": 100, "toplam_urun": 50}}
        self.assertEqual(sayfa_uret._ek_kalem_sayfalari(conf, veri), [])

    def test_ilgili_kalemler_sinirli_ve_ayni_gruba_oncelikli(self):
        conf = self._conf()
        conf["kalem_sayfalari"] = [
            {"id": f"d{i}", "slug": f"d{i}-fiyatlari"} for i in range(20)
        ] + [{"id": "nevresim-takimi", "slug": "nevresim-takimi-fiyatlari"},
             {"id": "hali", "slug": "hali-fiyatlari"}]
        conf["kalemler"] += [{"id": f"d{i}", "ad": f"D{i}", "birim": "sabit", "grup": "Mutfak"}
                             for i in range(20)]
        html = sayfa_uret._ilgili_kalemler_html(conf, "nevresim-takimi-fiyatlari")
        self.assertLessEqual(html.count("<a "), sayfa_uret.EN_FAZLA_ILGILI_KALEM)
        # Ayni gruptaki (Tekstil) hali one gelmeli
        self.assertIn("hali-fiyatlari", html)


class FiyatGecmisiTesti(unittest.TestCase):
    """Zaman serisi bolumu - projenin kopyalanamaz varligi."""

    def _yaz(self, tmp, kalemler):
        (tmp / "dugun.json").write_text(
            json.dumps({"vertikal": "dugun", "kalemler": kalemler}, ensure_ascii=False),
            encoding="utf-8")
        return tmp

    def test_yeterli_olcum_yoksa_bolum_hic_render_edilmez(self):
        """Bos bir 'gecmis' basligi veri varmis izlenimi verir."""
        with TemporaryDirectory() as d:
            kok = self._yaz(Path(d), {"gelinlik": {
                "seri": [{"tarih": "2026-07-25", "medyan": 8999, "urun": 21, "kaynak": 1}],
            }})
            self.assertEqual(sayfa_uret._fiyat_gecmisi_html("dugun", "gelinlik", kok), "")

    def test_degisim_yuzdesi_yoksa_render_edilmez(self):
        """gecmis.py, olcumler birbirine cok yakinsa degisim yazmaz."""
        with TemporaryDirectory() as d:
            kok = self._yaz(Path(d), {"gelinlik": {
                "seri": [{"tarih": "2026-07-25", "medyan": 8999, "urun": 21, "kaynak": 1},
                         {"tarih": "2026-07-26", "medyan": 9500, "urun": 21, "kaynak": 1}],
            }})
            self.assertEqual(sayfa_uret._fiyat_gecmisi_html("dugun", "gelinlik", kok), "")

    def test_gercek_seri_ozet_ve_tablo_uretir(self):
        with TemporaryDirectory() as d:
            kok = self._yaz(Path(d), {"gelinlik": {
                "seri": [{"tarih": "2026-07-01", "medyan": 8000, "urun": 20, "kaynak": 1},
                         {"tarih": "2026-08-15", "medyan": 9200, "urun": 22, "kaynak": 1}],
                "degisim_yuzde": 15.0,
            }})
            html = sayfa_uret._fiyat_gecmisi_html("dugun", "gelinlik", kok)
            self.assertIn("Fiyat geçmişi", html)
            self.assertIn("%15.0 arttı", html)
            self.assertIn("8.000 TL", html)
            self.assertIn("9.200 TL", html)

    def test_dusus_dogru_ifade_edilir(self):
        with TemporaryDirectory() as d:
            kok = self._yaz(Path(d), {"gelinlik": {
                "seri": [{"tarih": "2026-07-01", "medyan": 9200, "urun": 20, "kaynak": 1},
                         {"tarih": "2026-08-15", "medyan": 8000, "urun": 22, "kaynak": 1}],
                "degisim_yuzde": -13.0,
            }})
            html = sayfa_uret._fiyat_gecmisi_html("dugun", "gelinlik", kok)
            self.assertIn("azaldı", html)
            self.assertNotIn("-13", html)  # isaret ayri, mutlak deger yazilir

    def test_veri_dosyasi_yoksa_sessizce_bos_doner(self):
        html = sayfa_uret._fiyat_gecmisi_html("dugun", "gelinlik", Path("/olmayan/yol"))
        self.assertEqual(html, "")
