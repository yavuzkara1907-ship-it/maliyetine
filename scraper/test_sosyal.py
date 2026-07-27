# -*- coding: utf-8 -*-
"""sosyal.py testleri.

Bu modulun asil isi PAYLASMAK degil, PAYLASMAMAK: uc kapinin gercekten
kapattigini dogrulamak. Sosyal medya, abartma basincinin en yuksek oldugu
mecra - bir kez orneklem gurultusunu "fiyat %40 dustu" diye atarsak
sitenin tum guven iddiasi coker.

Degisim gonderileri gercek veriyle henuz test edilemiyor (ilk
karsilastirilabilir olcum 5 Agustos), o yuzden gecmis sentetik uretiliyor.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sosyal


def _gecmis_yaz(kok: Path, vertikal: str, kalem_id: str, seri: list[dict],
                aylik_degisim: float | None):
    kok.mkdir(parents=True, exist_ok=True)
    kayit = {"seri": seri, "ilk": seri[0], "son": seri[-1]}
    if aylik_degisim is not None:
        kayit["aylik_degisim_yuzde"] = aylik_degisim
    (kok / f"{vertikal}.json").write_text(json.dumps({
        "vertikal": vertikal, "olcumler": [s["tarih"] for s in seri],
        "kalemler": {kalem_id: kayit}, "ozet": {},
    }, ensure_ascii=False), encoding="utf-8")


class KapilarTesti(unittest.TestCase):
    """Uc kapi: yeterli aralik, orneklem kararliligi, anlamli buyukluk."""

    def setUp(self):
        self.gecici = tempfile.TemporaryDirectory()
        self.kok = Path(self.gecici.name)
        self.addCleanup(self.gecici.cleanup)

    def _seri(self, t1, t2, m1, m2, u1, u2):
        return [{"tarih": t1, "medyan": m1, "urun": u1, "kaynak": 2},
                {"tarih": t2, "medyan": m2, "urun": u2, "kaynak": 2}]

    def test_gercek_degisim_paylasilir(self):
        _gecmis_yaz(self.kok, "bebek", "besik",
                    self._seri("2026-08-05", "2026-08-20", 4000, 4300, 45, 44), 7.5)
        g = sosyal.degisim_adaylari(self.kok)
        self.assertEqual(len(g), 1)
        metin = g[0]["metin"]
        self.assertIn("Beşik", metin)          # ham id degil, insan adi
        self.assertIn("besik", g[0]["kalem_id"])
        self.assertIn("%7.5", metin)
        self.assertIn("44 üründen", metin)     # orneklem her zaman gorunur
        self.assertIn("2026-08-20", metin)     # tarih her zaman gorunur

    def test_kapi1_yakin_olcumler_paylasilmaz(self):
        """24->25 Temmuz testinde "nikah sekeri %40 dustu" cikmisti; gercek
        bir dusus degil, kategori sayfasinda LISTELENEN urunlerin degismesi."""
        _gecmis_yaz(self.kok, "bebek", "besik",
                    self._seri("2026-08-05", "2026-08-06", 4000, 2400, 45, 45), -40.0)
        self.assertEqual(sosyal.degisim_adaylari(self.kok), [])

    def test_kapi2_orneklem_oynadiysa_paylasilmaz(self):
        """Urun sayisi 20'den 45'e ciktiysa medyandaki oynama FIYATTAN degil
        olculen kumeden geliyor olabilir - hangisi oldugunu ayirt edemiyoruz,
        o yuzden susuyoruz."""
        _gecmis_yaz(self.kok, "bebek", "besik",
                    self._seri("2026-08-05", "2026-08-20", 4000, 6000, 20, 45), 50.0)
        self.assertEqual(sosyal.degisim_adaylari(self.kok), [])

    def test_kapi3_kucuk_degisim_paylasilmaz(self):
        _gecmis_yaz(self.kok, "bebek", "besik",
                    self._seri("2026-08-05", "2026-08-20", 4000, 4060, 45, 45), 1.5)
        self.assertEqual(sosyal.degisim_adaylari(self.kok), [])

    def test_soylenecek_sey_yoksa_bos_doner(self):
        """Bos liste hata degil, tasarlanan davranis. Kod bu durumda
        uydurma bir gonderi URETEMEZ."""
        self.assertEqual(sosyal.gonderiler(self.kok, self.kok), [])

    def test_gonderi_sayisi_sinirli(self):
        """Bir olcumde 40 kalem degistiyse 40 tweet atmak spam'dir."""
        kok = self.kok
        kalemler = {}
        for i, kid in enumerate(["besik", "bebek-arabasi", "oto-koltugu",
                                 "mama-sandalyesi", "park-yatak"]):
            kalemler[kid] = {
                "seri": self._seri("2026-08-05", "2026-08-20", 4000, 4000 + 400 * (i + 1), 45, 45),
                "aylik_degisim_yuzde": 10.0 + i,
            }
            kalemler[kid]["ilk"] = kalemler[kid]["seri"][0]
            kalemler[kid]["son"] = kalemler[kid]["seri"][-1]
        (kok / "bebek.json").write_text(json.dumps(
            {"vertikal": "bebek", "kalemler": kalemler}, ensure_ascii=False), encoding="utf-8")
        secilen = sosyal.gonderiler(kok, kok)
        self.assertEqual(len(secilen), sosyal.EN_FAZLA_GONDERI)
        # En buyuk degisim once gelir
        self.assertGreaterEqual(secilen[0]["onem"], secilen[-1]["onem"])

    def test_tanimsiz_kalem_ham_id_ile_paylasilmaz(self):
        """Senaryo sayfalarinda tam bu hata yasandi: tabloda kalem adi
        yerine ham id ("orkestra-dj") gorunuyordu."""
        _gecmis_yaz(self.kok, "bebek", "boyle-bir-kalem-yok",
                    self._seri("2026-08-05", "2026-08-20", 4000, 4400, 45, 45), 10.0)
        self.assertEqual(sosyal.degisim_adaylari(self.kok), [])

    def test_karakter_siniri(self):
        _gecmis_yaz(self.kok, "bebek", "mama-sandalyesi",
                    self._seri("2026-08-05", "2026-08-20", 1664, 1900, 60, 59), 14.2)
        for g in sosyal.gonderiler(self.kok, self.kok):
            self.assertLessEqual(len(g["tam_metin"]), sosyal.AZAMI_KARAKTER)


class OzetTesti(unittest.TestCase):
    def setUp(self):
        self.gecici = tempfile.TemporaryDirectory()
        self.kok = Path(self.gecici.name)
        self.addCleanup(self.gecici.cleanup)

    def test_veri_yoksa_ozet_uretilmez(self):
        self.assertIsNone(sosyal.olcum_ozeti("bebek", self.kok))

    def test_rakamsiz_ozet_uretilmez(self):
        """Tum segmentler bossa (o ay hicbir kaynak urun dondurmedi) "0 TL"
        gibi guvenilir gorunen bir gonderi ATILMAZ."""
        (self.kok / "bebek.json").write_text(json.dumps({
            "kalemler": {"besik": {"segmentler": {}, "kaynaklar": []}},
        }), encoding="utf-8")
        self.assertIsNone(sosyal.olcum_ozeti("bebek", self.kok))

    def test_toplama_girmeyen_kalem_ozete_katilmaz(self):
        """bebek-bezi sarf malzemesi, tek seferlik hazirlik toplamina
        girmiyor - sosyal gonderide de girmemeli, aksi halde sitedekiyle
        farkli bir rakam paylasilmis olur."""
        (self.kok / "bebek.json").write_text(json.dumps({
            "olcum_tarihi": "2026-08-20",
            "kalemler": {
                "besik": {"segmentler": {"orta": {"medyan": 4315}},
                          "kaynaklar": [{"site": "trendyol", "toplam_urun": 20}]},
                "bebek-arabasi": {"segmentler": {"orta": {"medyan": 7110}},
                                  "kaynaklar": [{"site": "amazon", "toplam_urun": 42}]},
                "oto-koltugu": {"segmentler": {"orta": {"medyan": 9608}},
                                "kaynaklar": [{"site": "trendyol", "toplam_urun": 24}]},
                "bebek-bezi": {"segmentler": {"orta": {"medyan": 565}},
                               "kaynaklar": [{"site": "amazon", "toplam_urun": 44}]},
            },
        }), encoding="utf-8")
        ozet = sosyal.olcum_ozeti("bebek", self.kok)
        self.assertIn("21.033 TL", ozet["metin"])   # 4315+7110+9608, bez YOK
        self.assertNotIn("21.598", ozet["metin"])


class KirmiziCizgiTesti(unittest.TestCase):
    """Metin URETILMIYOR, veriden KURULUYOR."""

    def test_dil_modeli_veya_disari_istek_yok(self):
        kaynak = Path(sosyal.__file__).read_text(encoding="utf-8")
        # Metin uretim yolunda hicbir LLM/uretim cagrisi olmamali.
        for yasak in ("openai", "anthropic", "generate", "completion", "eval("):
            self.assertNotIn(yasak, kaynak.lower(), f"yasak ifade: {yasak}")

    def test_gonderme_anahtar_yoksa_atlanir(self):
        import os
        for a in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET",
                  "BLUESKY_HANDLE", "BLUESKY_SIFRE"):
            os.environ.pop(a, None)
        self.assertFalse(sosyal.x_gonder("deneme"))
        self.assertFalse(sosyal.bluesky_gonder("deneme"))

    def test_esik_gecmis_ile_ayni(self):
        """Aralik esigi iki yerde ayri tanimlanirsa biri guncellenip digeri
        kalir. Tek kaynak: gecmis.ASGARI_GUN_ARALIGI."""
        import gecmis
        kaynak = Path(sosyal.__file__).read_text(encoding="utf-8")
        self.assertIn("gecmis.ASGARI_GUN_ARALIGI", kaynak)
        self.assertGreater(gecmis.ASGARI_GUN_ARALIGI, 0)


if __name__ == "__main__":
    unittest.main()


class RotasyonTesti(unittest.TestCase):
    def test_ay_bazli_deterministik(self):
        """Ayni ay iki kez calistirilirsa ayni vertikal secilir - yani ard
        arda calistirma yeni bir gonderi uretmez."""
        import datetime
        a = sosyal.ozet_vertikali_sec(datetime.date(2026, 8, 5))
        b = sosyal.ozet_vertikali_sec(datetime.date(2026, 8, 20))
        self.assertEqual(a, b)

    def test_aylar_arasi_donusumlu(self):
        import datetime
        secimler = {sosyal.ozet_vertikali_sec(datetime.date(2026, ay, 5))
                    for ay in range(1, 13)}
        self.assertGreater(len(secimler), 1, "rotasyon calismiyor")

    def test_secilen_vertikal_gercekten_var(self):
        import sayfa_uret as su
        self.assertIn(sosyal.ozet_vertikali_sec(), su.VERTIKALLER)
