# -*- coding: utf-8 -*-
"""
motor.py icin dogrulama testleri (v0.1)

Bu ortamdan gercek hedef sitelere network erisimi yok (proxy policy
engelliyor) - o yuzden sahte HTML fixture'lari ile motorun cikarim
mantigini, robots.txt kapisini ve saglik kontrolunu dogruluyoruz.
Gercek kaynaklara karsi calistirmak Yavuz'un yerelinde yapilmali.

Calistirma:
  python -m unittest test_motor.py -v
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import requests
from bs4 import BeautifulSoup

import motor


# ----------------------------------------------------------
# Sahte HTML fixture'lari
# ----------------------------------------------------------
JSON_LD_HTML = """
<html><body>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "itemListElement": [
    {"@type": "Product", "name": "Gelinlik A", "offers": {"@type": "Offer", "price": "12000"}},
    {"@type": "Product", "name": "Gelinlik B", "offers": {"@type": "Offer", "price": "8500.50"}}
  ]
}
</script>
<script type="application/ld+json">
{"@context": "https://schema.org", "@type": "Product", "name": "Gelinlik C", "offers": [{"price": 25000}]}
</script>
</body></html>
"""

MICRODATA_HTML = """
<html><body>
<div itemscope itemtype="https://schema.org/Product">
  <span itemprop="name">Gelinlik D</span>
  <span itemprop="price" content="15000.00">15.000,00 TL</span>
</div>
<div itemscope itemtype="https://schema.org/Product">
  <span itemprop="name">Gelinlik E</span>
  <span itemprop="price" content="9000.00">9.000,00 TL</span>
</div>
</body></html>
"""

OG_META_HTML = """
<html><head>
<meta property="og:title" content="Gelinlik F">
<meta property="product:price:amount" content="18000">
</head><body></body></html>
"""

CSS_HTML = """
<html><body>
<div class="product-card">
  <h3 class="product-name">Gelinlik G</h3>
  <span class="price">22.500,00 TL</span>
</div>
<div class="product-card">
  <h3 class="product-name">Gelinlik H</h3>
  <span class="price">7.000,00 TL</span>
</div>
</body></html>
"""

BOS_HTML = "<html><body><p>Urun yok</p></body></html>"

# Gercek Atasay/Trendyol HTML'inden alinmis kucultulmus urun karti
# ornekleri (2026-07-24, sayfa_tani.py ile teshis edildi) - kaynaklar.yaml
# icindeki css_secicileri degerlerinin gercekten calistigini kilitler.
ATASAY_URUN_KARTI_HTML = """
<div class="js-product-wrapper product-item" data-pk="47008">
<div class="product-item__body">resim vb.</div>
<div class="product-item__info">
<div class="product-item__name">
      Sarı Altın Ajda Çift Alyans
    </div>
<div class="product-item__price">
<div class="flex price-least">
<pz-price>19710</pz-price>  'den başlayan fiyatlarla
          </div>
</div>
</div>
</div>
"""

TRENDYOL_URUN_KARTI_HTML = """
<a class="product-card" href="/x">
<span class="product-brand">Altınyıldız Classics</span>
<span class="product-name"> <!-- -->Erkek Lacivert Slim Fit Dar Kesim Mono Yaka Takım Elbise</span>
<div class="product-card-price">
<span class="price-value" data-testid="price-value">3.239,99 TL</span>
<span class="strikethrough-price" data-testid="strikethrough-price">3.599,99 TL</span>
</div>
</a>
"""


class HeaderRegresyonTestleri(unittest.TestCase):
    """2026-07-24: HEADERS icinde 'Accept-Encoding: ...br' sabitlenmisti -
    urllib3/requests brotli decoder'i kurulu degilse br-sikistirilmis
    yanitlar cozulemeyip r.text cop karakterlere donusuyordu (Yavuz'un
    Ramsey/Atasay/Armut/DugunBuketi testlerinde goruldu - 'CSS secici yok'
    sanilan sorun aslinda hic okunamayan bozuk veriydi). Bir daha
    eklenmesin diye kilitleyen test."""

    def test_accept_encoding_elle_belirtilmemis(self):
        self.assertNotIn(
            "Accept-Encoding", motor.HEADERS,
            "Accept-Encoding elle sabitlenirse brotli decoder kurulu "
            "olmayan ortamlarda r.text cop karakterlere donusebilir - "
            "requests'in kendi otomatik degerine birak.",
        )


class FiyatAyiklaTestleri(unittest.TestCase):
    def test_turkce_bin_ayirici_ve_ondalik(self):
        self.assertEqual(motor.fiyat_ayikla("45.999,00 TL"), 45999.0)

    def test_tl_simgesi(self):
        self.assertEqual(motor.fiyat_ayikla("1.250 ₺"), 1250.0)

    def test_bos_metin(self):
        self.assertIsNone(motor.fiyat_ayikla(""))
        self.assertIsNone(motor.fiyat_ayikla(None))

    def test_rakamsiz_metin(self):
        self.assertIsNone(motor.fiyat_ayikla("Fiyat sorunuz"))


class UcKatmanTestleri(unittest.TestCase):
    def test_json_ld_katmani_itemlist_ve_tekli_urun(self):
        soup = BeautifulSoup(JSON_LD_HTML, "html.parser")
        urunler = motor.json_ld_urunler(soup, min_fiyat=100)
        isimler = {u["isim"] for u in urunler}
        self.assertEqual(isimler, {"Gelinlik A", "Gelinlik B", "Gelinlik C"})
        fiyatlar = {u["isim"]: u["fiyat"] for u in urunler}
        self.assertEqual(fiyatlar["Gelinlik A"], 12000.0)
        self.assertEqual(fiyatlar["Gelinlik B"], 8500.5)
        self.assertEqual(fiyatlar["Gelinlik C"], 25000.0)

    def test_microdata_katmani(self):
        soup = BeautifulSoup(MICRODATA_HTML, "html.parser")
        urunler = motor.microdata_urunler(soup, min_fiyat=100)
        isimler = {u["isim"] for u in urunler}
        self.assertEqual(isimler, {"Gelinlik D", "Gelinlik E"})

    def test_og_meta_yedegi(self):
        soup = BeautifulSoup(OG_META_HTML, "html.parser")
        urunler = motor.microdata_urunler(soup, min_fiyat=100)
        self.assertEqual(len(urunler), 1)
        self.assertEqual(urunler[0]["isim"], "Gelinlik F")
        self.assertEqual(urunler[0]["fiyat"], 18000.0)

    def test_css_katmani_son_care(self):
        soup = BeautifulSoup(CSS_HTML, "html.parser")
        secici = {
            "urun_karti": "div.product-card",
            "isim_secici": "h3.product-name",
            "fiyat_secici": "span.price",
        }
        urunler = motor.css_urunler(soup, secici, min_fiyat=100)
        isimler = {u["isim"] for u in urunler}
        self.assertEqual(isimler, {"Gelinlik G", "Gelinlik H"})

    def test_katman_onceligi_json_ld_kazanir(self):
        # JSON-LD VE css ikisi de ayni sayfada olsa JSON-LD once denenir.
        karisik_html = JSON_LD_HTML.replace("</body>", CSS_HTML.split("<body>")[1])
        soup = BeautifulSoup(karisik_html, "html.parser")
        kaynak = {
            "min_fiyat": 100,
            "css_secicileri": {
                "urun_karti": "div.product-card",
                "isim_secici": "h3.product-name",
                "fiyat_secici": "span.price",
            },
        }
        urunler, katman = motor.uc_katman_cikar(soup, kaynak)
        self.assertEqual(katman, "json-ld")
        isimler = {u["isim"] for u in urunler}
        self.assertIn("Gelinlik A", isimler)
        self.assertNotIn("Gelinlik G", isimler)  # css katmanindan gelen, denenmedi

    def test_hicbir_katman_bulamazsa_bos_doner(self):
        soup = BeautifulSoup(BOS_HTML, "html.parser")
        urunler, katman = motor.uc_katman_cikar(soup, {"min_fiyat": 100, "css_secicileri": None})
        self.assertEqual(urunler, [])
        self.assertEqual(katman, "hicbiri")


class GercekSiteSecicileriTestleri(unittest.TestCase):
    """kaynaklar.yaml'daki css_secicileri degerlerinin, sayfa_tani.py ile
    2026-07-24'te teshis edilen gercek Atasay/Trendyol urun karti HTML'ine
    karsi hala calistigini kilitler - biri yaml'i degistirip secicileri
    bozarsa bu test kirilir."""

    def _yaml_secici(self, ad: str) -> dict:
        import yaml
        dosya = Path(__file__).parent / "kaynaklar.yaml"
        veri = yaml.safe_load(dosya.read_text(encoding="utf-8"))
        for k in veri["kaynaklar"]:
            if k["ad"] == ad:
                return k["css_secicileri"]
        raise AssertionError(f"kaynaklar.yaml'da bulunamadi: {ad}")

    def test_atasay_secicisi_gercek_urun_kartini_dogru_cikarir(self):
        secici = self._yaml_secici("Atasay - Alyans (marka magazasi)")
        soup = BeautifulSoup(ATASAY_URUN_KARTI_HTML, "html.parser")
        urunler = motor.css_urunler(soup, secici, min_fiyat=1000)
        self.assertEqual(urunler, [{"isim": "Sarı Altın Ajda Çift Alyans", "fiyat": 19710.0}])

    def test_trendyol_secicisi_gercek_urun_kartini_dogru_cikarir(self):
        secici = self._yaml_secici("Trendyol - Damatlik")
        soup = BeautifulSoup(TRENDYOL_URUN_KARTI_HTML, "html.parser")
        urunler = motor.css_urunler(soup, secici, min_fiyat=1000)
        self.assertEqual(
            urunler,
            [{"isim": "Erkek Lacivert Slim Fit Dar Kesim Mono Yaka Takım Elbise", "fiyat": 3239.99}],
        )


class AykiriVeSegmentTestleri(unittest.TestCase):
    def test_aykiri_deger_temizligi(self):
        normal = [{"isim": f"u{i}", "fiyat": 1000 + i * 10} for i in range(30)]
        aykiri = [{"isim": "cok-pahali", "fiyat": 999999}]
        temiz = motor.aykiri_temizle(normal + aykiri)
        self.assertNotIn(aykiri[0], temiz)
        self.assertEqual(len(temiz), 30)

    def test_az_veride_aykiri_temizlik_atlanir(self):
        az = [{"isim": f"u{i}", "fiyat": 1000 + i} for i in range(5)]
        self.assertEqual(motor.aykiri_temizle(az), az)

    def test_segmentleme_persentil(self):
        urunler = [{"isim": f"u{i}", "fiyat": (i + 1) * 100} for i in range(20)]
        seg = motor.segmentle(urunler)
        self.assertIn("dusuk", seg)
        self.assertIn("orta", seg)
        self.assertIn("luks", seg)
        toplam = sum(s["urun_sayisi"] for s in seg.values())
        self.assertEqual(toplam, 20)

    def test_bos_liste_segmentleme(self):
        self.assertEqual(motor.segmentle([]), {})


class SaglikKontroluTestleri(unittest.TestCase):
    def test_ilk_calistirmada_her_zaman_saglikli(self):
        saglikli, ortalama = motor.saglik_kontrolu("yeni-kaynak", 3, {})
        self.assertTrue(saglikli)
        self.assertIsNone(ortalama)

    def test_normal_dalgalanma_saglikli(self):
        gecmis = {"kaynak-x": {"urun_sayilari": [200, 190, 210]}}
        saglikli, ortalama = motor.saglik_kontrolu("kaynak-x", 180, gecmis)
        self.assertTrue(saglikli)

    def test_ciddi_dusus_karantina(self):
        gecmis = {"kaynak-x": {"urun_sayilari": [200, 190, 210]}}
        saglikli, ortalama = motor.saglik_kontrolu("kaynak-x", 3, gecmis)
        self.assertFalse(saglikli)
        self.assertAlmostEqual(ortalama, 200.0, delta=0.1)

    def test_gecmis_guncelle_son_12_tutar(self):
        gecmis = {}
        for i in range(15):
            motor.gecmis_guncelle(gecmis, "k", 100 + i)
        self.assertEqual(len(gecmis["k"]["urun_sayilari"]), 12)
        self.assertEqual(gecmis["k"]["urun_sayilari"][-1], 114)


class SahteYanit:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text


class RobotsKapisiTestleri(unittest.TestCase):
    """robots_izin_var artik requests+protego kullaniyor (stdlib
    urllib.robotparser DEGIL - bkz. motor.py'deki ayrintili not: gercek
    Akakce robots.txt'ine karsi test edilirken 3 ayri hata bulundu:
    bot-imzali User-Agent'in 403 alip yanlislikla "hicbir sey kazinamaz"
    sonucuna varmasi, User-agent gruplarinda bos satirin grubu dusurmesi,
    ve "*" joker karakterinin hic desteklenmemesi)."""

    def setUp(self):
        motor._robots_onbellek.clear()

    @patch("motor.requests.get")
    def test_izin_verilen_url(self, sahte_get):
        sahte_get.return_value = SahteYanit(200, "User-agent: *\nAllow: /\n")
        sonuc = motor.robots_izin_var("https://ornek-site.com/kategori")
        self.assertTrue(sonuc)

    @patch("motor.requests.get")
    def test_yasakli_url(self, sahte_get):
        sahte_get.return_value = SahteYanit(200, "User-agent: *\nDisallow: /\n")
        sonuc = motor.robots_izin_var("https://ornek-site.com/yasakli")
        self.assertFalse(sonuc)

    @patch("motor.requests.get")
    def test_joker_karakter_dogru_calisir(self, sahte_get):
        # stdlib robotparser'in KACIRDIGI tam senaryo: "*" ile ozel yol engeli.
        sahte_get.return_value = SahteYanit(
            200, "User-agent: *\nAllow: /\nDisallow: /moda/*\nDisallow: /*?sayfa=*\n"
        )
        self.assertTrue(motor.robots_izin_var("https://ornek-site.com/gelinlik.html"))
        self.assertFalse(motor.robots_izin_var("https://ornek-site.com/moda/x"))
        self.assertFalse(motor.robots_izin_var("https://ornek-site.com/gelinlik.html?sayfa=2"))

    @patch("motor.requests.get")
    def test_coklu_useragent_grubu_bos_satirla_dogru_calisir(self, sahte_get):
        # stdlib robotparser'in KACIRDIGI ikinci senaryo: User-agent
        # satirlari ile kurallar arasinda bos satir olan coklu grup.
        sahte_get.return_value = SahteYanit(
            200,
            "User-agent:*\nUser-agent: Googlebot\n\nAllow: /\nDisallow: /moda/*\n\n"
            "User-agent: AhrefsBot\nDisallow: /\n",
        )
        self.assertTrue(motor.robots_izin_var("https://ornek-site.com/gelinlik.html"))
        self.assertFalse(motor.robots_izin_var("https://ornek-site.com/moda/x"))

    @patch("motor.requests.get")
    def test_403_erisim_yasagi_tum_urlleri_ret_eder(self, sahte_get):
        sahte_get.return_value = SahteYanit(403, "")
        sonuc = motor.robots_izin_var("https://ornek-site.com/x")
        self.assertFalse(sonuc)

    @patch("motor.requests.get")
    def test_404_robots_txt_yoksa_izinli_kabul_edilir(self, sahte_get):
        sahte_get.return_value = SahteYanit(404, "")
        sonuc = motor.robots_izin_var("https://ornek-site.com/x")
        self.assertTrue(sonuc)

    @patch("motor.requests.get")
    def test_5xx_ihtiyatla_ret(self, sahte_get):
        sahte_get.return_value = SahteYanit(503, "")
        sonuc = motor.robots_izin_var("https://ornek-site.com/x")
        self.assertFalse(sonuc)

    @patch("motor.requests.get")
    def test_robots_txt_okunamazsa_ihtiyatla_ret(self, sahte_get):
        sahte_get.side_effect = requests.RequestException("baglanti hatasi")
        sonuc = motor.robots_izin_var("https://erisilemez-site.com/x")
        self.assertFalse(sonuc)

    @patch("motor.requests.get")
    def test_ayni_domain_icin_onbellek_tek_okuma(self, sahte_get):
        sahte_get.return_value = SahteYanit(200, "User-agent: *\nAllow: /\n")
        motor.robots_izin_var("https://ornek-site.com/a")
        motor.robots_izin_var("https://ornek-site.com/b")
        sahte_get.assert_called_once()


class PlaywrightGetirTestleri(unittest.TestCase):
    """getir_playwright() ve kaynak_ham_veri_topla()'nin render_gerekli
    bayragina gore dogru fetch fonksiyonunu secmesini dogrular. Gercek
    bir Chromium bu sandbox'ta calistirilamiyor (tarayici ikili dosyasi
    indirilemiyor - proxy engelli), o yuzden playwright.sync_api sahte
    (mock) nesnelerle test ediliyor."""

    def test_basarili_cekim_sayfa_icerigini_dondurur(self):
        sahte_sayfa = MagicMock()
        sahte_sayfa.content.return_value = "<html>merhaba</html>"
        sahte_tarayici = MagicMock()
        sahte_tarayici.new_page.return_value = sahte_sayfa
        sahte_pw = MagicMock()
        sahte_pw.chromium.launch.return_value = sahte_tarayici

        with patch("playwright.sync_api.sync_playwright") as sahte_sync:
            sahte_sync.return_value.__enter__.return_value = sahte_pw
            sonuc = motor.getir_playwright("https://ornek-site.com/x", deneme=1)

        self.assertEqual(sonuc, "<html>merhaba</html>")
        sahte_tarayici.close.assert_called_once()

    def test_tarayici_kurulu_degilse_none_doner_ve_hata_vermez(self):
        with patch.dict("sys.modules", {"playwright.sync_api": None}):
            sonuc = motor.getir_playwright("https://ornek-site.com/x", deneme=1)
        self.assertIsNone(sonuc)

    @patch("motor.robots_izin_var", return_value=True)
    @patch("motor.getir")
    @patch("motor.getir_playwright")
    def test_render_gerekli_true_ise_playwright_kullanilir(
        self, sahte_pw_getir, sahte_requests_getir, _sahte_robots
    ):
        sahte_pw_getir.return_value = JSON_LD_HTML
        kaynak = {
            "ad": "Render Gerekli Kaynak", "site": "x",
            "url": "https://ornek-site.com/y.html", "sayfa_sayisi": 1,
            "vertikal": "dugun", "kalem": "gelinlik", "min_fiyat": 100,
            "bekleme_sn": 0, "aktif": True, "css_secicileri": None,
            "render_gerekli": True,
        }
        motor.kaynak_ham_veri_topla(kaynak)
        sahte_pw_getir.assert_called_once()
        sahte_requests_getir.assert_not_called()

    @patch("motor.robots_izin_var", return_value=True)
    @patch("motor.getir")
    @patch("motor.getir_playwright")
    def test_render_gerekli_false_ise_requests_kullanilir(
        self, sahte_pw_getir, sahte_requests_getir, _sahte_robots
    ):
        sahte_requests_getir.return_value = JSON_LD_HTML
        kaynak = {
            "ad": "Normal Kaynak", "site": "x",
            "url": "https://ornek-site.com/y.html", "sayfa_sayisi": 1,
            "vertikal": "dugun", "kalem": "gelinlik", "min_fiyat": 100,
            "bekleme_sn": 0, "aktif": True, "css_secicileri": None,
        }
        motor.kaynak_ham_veri_topla(kaynak)
        sahte_requests_getir.assert_called_once()
        sahte_pw_getir.assert_not_called()


class GrupIsleUctanUcaTestleri(unittest.TestCase):
    """robots + HTTP katmanlarini sahteleyip grup_isle'nin uctan uca
    dogru calistigini (dosya yazma, saglik kontrolu, karantina) dogrular."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.cikti_kok = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    @patch("motor.robots_izin_var", return_value=True)
    @patch("motor.getir")
    def test_saglikli_grup_dogru_klasore_yazar(self, sahte_getir, _sahte_robots):
        sahte_getir.return_value = JSON_LD_HTML
        kaynak = {
            "ad": "Test Kaynak",
            "site": "test-site",
            "url": "https://ornek-site.com/gelinlik.html",
            "sayfa_sayisi": 1,
            "vertikal": "dugun",
            "kalem": "gelinlik",
            "min_fiyat": 100,
            "bekleme_sn": 0,
            "aktif": True,
            "css_secicileri": None,
        }
        gecmis = {}
        gruplar = motor.gruplar_halinde_topla([kaynak])
        self.assertEqual(len(gruplar), 1)
        (vertikal, kalem, site), grup = next(iter(gruplar.items()))
        sonuc = motor.grup_isle(vertikal, kalem, site, grup, gecmis, self.cikti_kok)

        self.assertTrue(sonuc["saglikli"])
        self.assertEqual(sonuc["toplam_urun"], 3)
        self.assertEqual(sonuc["kullanilan_katmanlar"], ["json-ld"])
        self.assertIsNotNone(sonuc["genel_medyan"])

        beklenen_dosya = self.cikti_kok / "dugun" / "gelinlik_test-site_" \
            f"{__import__('datetime').date.today().isoformat()}.json"
        self.assertTrue(beklenen_dosya.exists())
        icerik = json.loads(beklenen_dosya.read_text(encoding="utf-8"))
        self.assertEqual(icerik["toplam_urun"], 3)

        self.assertIn("dugun/gelinlik/test-site", gecmis)
        self.assertEqual(gecmis["dugun/gelinlik/test-site"]["urun_sayilari"], [3])

    @patch("motor.robots_izin_var", return_value=True)
    @patch("motor.getir")
    def test_ayni_site_birden_fazla_girdi_birlesir(self, sahte_getir, _sahte_robots):
        # Akakce'nin 5 alt kategorisi gibi: ayni "site" degeriyle 2 yaml
        # girdisi TEK kaynak grubu olarak birlesmeli.
        sahte_getir.return_value = JSON_LD_HTML  # her cagride ayni 3 urunu doner
        ortak = {
            "site": "akakce",
            "sayfa_sayisi": 1,
            "vertikal": "dugun",
            "kalem": "gelinlik",
            "min_fiyat": 100,
            "bekleme_sn": 0,
            "aktif": True,
            "css_secicileri": None,
        }
        kaynaklar = [
            {**ortak, "ad": "Akakce - A", "url": "https://akakce.com/a.html"},
            {**ortak, "ad": "Akakce - B", "url": "https://akakce.com/b.html"},
        ]
        gruplar = motor.gruplar_halinde_topla(kaynaklar)
        self.assertEqual(len(gruplar), 1)  # iki girdi tek gruba dustu
        grup = next(iter(gruplar.values()))
        self.assertEqual(sorted(grup["kaynak_adlari"]), ["Akakce - A", "Akakce - B"])
        self.assertEqual(len(grup["urunler"]), 6)  # 3 urun x 2 girdi

    @patch("motor.robots_izin_var", return_value=True)
    @patch("motor.getir")
    def test_ani_dusus_karantinaya_yazar(self, sahte_getir, _sahte_robots):
        sahte_getir.return_value = JSON_LD_HTML  # bu calistirmada 3 urun donecek
        kaynak = {
            "ad": "Test Kaynak 2",
            "site": "test-site-2",
            "url": "https://ornek-site.com/gelinlik.html",
            "sayfa_sayisi": 1,
            "vertikal": "dugun",
            "kalem": "gelinlik",
            "min_fiyat": 100,
            "bekleme_sn": 0,
            "aktif": True,
            "css_secicileri": None,
        }
        # Gecmiste normalde 200 urun donuyordu -> bu ay 3 urun ciddi dusus.
        gecmis = {"dugun/gelinlik/test-site-2": {"urun_sayilari": [200, 195, 205]}}
        gruplar = motor.gruplar_halinde_topla([kaynak])
        (vertikal, kalem, site), grup = next(iter(gruplar.items()))
        sonuc = motor.grup_isle(vertikal, kalem, site, grup, gecmis, self.cikti_kok)

        self.assertFalse(sonuc["saglikli"])
        karantina_dosyalari = list((self.cikti_kok / "karantina").glob("*.json"))
        self.assertEqual(len(karantina_dosyalari), 1)
        normal_dosyalari = list((self.cikti_kok / "dugun").glob("*.json")) \
            if (self.cikti_kok / "dugun").exists() else []
        self.assertEqual(len(normal_dosyalari), 0)

    @patch("motor.robots_izin_var", return_value=False)
    @patch("motor.getir")
    def test_robots_ret_ederse_hicbir_seyi_kazimaz(self, sahte_getir, _sahte_robots):
        kaynak = {
            "ad": "Yasakli Kaynak",
            "site": "yasakli-site",
            "url": "https://ornek-site.com/yasakli.html",
            "sayfa_sayisi": 1,
            "vertikal": "dugun",
            "kalem": "gelinlik",
            "min_fiyat": 100,
            "bekleme_sn": 0,
            "aktif": True,
            "css_secicileri": None,
        }
        gruplar = motor.gruplar_halinde_topla([kaynak])
        (vertikal, kalem, site), grup = next(iter(gruplar.items()))
        sonuc = motor.grup_isle(vertikal, kalem, site, grup, {}, self.cikti_kok)
        sahte_getir.assert_not_called()
        self.assertEqual(sonuc["toplam_urun"], 0)

    @patch("motor.robots_izin_var", return_value=True)
    @patch("motor.getir")
    def test_pasif_kaynak_atlanir(self, sahte_getir, _sahte_robots):
        kaynak = {"ad": "Pasif", "site": "pasif-site", "url": "https://x.com/y", "aktif": False}
        gruplar = motor.gruplar_halinde_topla([kaynak])
        self.assertEqual(gruplar, {})
        sahte_getir.assert_not_called()


class CaprazDogrulamaTestleri(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.cikti_kok = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _sonuc(self, site, kalem, medyan, saglikli=True, vertikal="dugun"):
        return {
            "site": site, "vertikal": vertikal, "kalem": kalem,
            "genel_medyan": medyan, "saglikli": saglikli,
        }

    def test_tek_kaynakta_capraz_dogrulama_yapilmaz(self):
        sonuclar = [self._sonuc("akakce", "gelinlik", 15000)]
        raporlar = motor.capraz_dogrula(sonuclar, self.cikti_kok)
        self.assertEqual(raporlar, [])

    def test_yakin_medyanlar_uyari_uretmez(self):
        sonuclar = [
            self._sonuc("akakce", "gelinlik", 15000),
            self._sonuc("dolap", "gelinlik", 17000),  # %13 fark
        ]
        raporlar = motor.capraz_dogrula(sonuclar, self.cikti_kok)
        self.assertEqual(len(raporlar), 1)
        self.assertFalse(raporlar[0]["uyari"])

    def test_uzak_medyanlar_uyari_uretir(self):
        sonuclar = [
            self._sonuc("akakce", "gelinlik", 10000),
            self._sonuc("dugunbuketi", "gelinlik", 60000),  # %500 fark
        ]
        raporlar = motor.capraz_dogrula(sonuclar, self.cikti_kok)
        self.assertEqual(len(raporlar), 1)
        self.assertTrue(raporlar[0]["uyari"])
        self.assertEqual(raporlar[0]["site_medyanlari"], {"akakce": 10000, "dugunbuketi": 60000})

        dosya = self.cikti_kok / "dugun" / f"gelinlik_capraz-dogrulama_{__import__('datetime').date.today().isoformat()}.json"
        self.assertTrue(dosya.exists())

    def test_saglıksiz_kaynak_karsilastirmaya_dahil_edilmez(self):
        sonuclar = [
            self._sonuc("akakce", "gelinlik", 10000, saglikli=True),
            self._sonuc("dolap", "gelinlik", 500000, saglikli=False),  # karantinada, sayilmamali
        ]
        raporlar = motor.capraz_dogrula(sonuclar, self.cikti_kok)
        self.assertEqual(raporlar, [])  # sadece 1 saglikli kaynak kaldi

    def test_farkli_kalemler_ayri_raporlanir(self):
        sonuclar = [
            self._sonuc("akakce", "gelinlik", 15000),
            self._sonuc("dolap", "gelinlik", 16000),
            self._sonuc("akakce", "alyans", 5000),
            self._sonuc("atasay", "alyans", 5200),
        ]
        raporlar = motor.capraz_dogrula(sonuclar, self.cikti_kok)
        kalemler = {r["kalem"] for r in raporlar}
        self.assertEqual(kalemler, {"gelinlik", "alyans"})


class KaynaklarYamlTestleri(unittest.TestCase):
    """Gercek kaynaklar.yaml dosyasinin gecerli/tutarli oldugunu dogrular."""

    def test_yaml_gecerli_ve_zorunlu_alanlar_var(self):
        import yaml
        dosya = Path(__file__).parent / "kaynaklar.yaml"
        veri = yaml.safe_load(dosya.read_text(encoding="utf-8"))
        kaynaklar = veri["kaynaklar"]
        self.assertGreater(len(kaynaklar), 0)

        zorunlu_alanlar = {"ad", "site", "url", "vertikal", "kalem", "aktif"}
        adlar = set()
        for k in kaynaklar:
            eksik = zorunlu_alanlar - set(k.keys())
            self.assertFalse(eksik, f"{k.get('ad')} eksik alan(lar): {eksik}")
            self.assertNotIn(k["ad"], adlar, f"tekrarli kaynak adi: {k['ad']}")
            adlar.add(k["ad"])
            self.assertTrue(k["url"].startswith("https://"))
            self.assertRegex(k["site"], r"^[a-z0-9-]+$", f"{k['ad']}: site alani slug olmali")

    def test_cok_kaynak_kurali_kapsam_raporu(self):
        """Bilgilendirici: hangi kalemlerin hala tek-kaynakli oldugunu
        gosterir (CLAUDE.md hedefi: kalem basina >=2 site). Test
        basarisiz OLMAZ, sadece stdout'a rapor basar - bircok kalem
        henuz robots.txt dogrulamasi bekledigi icin bu asamada
        zorunlu kilmak erken olur."""
        import yaml
        from collections import defaultdict
        dosya = Path(__file__).parent / "kaynaklar.yaml"
        veri = yaml.safe_load(dosya.read_text(encoding="utf-8"))
        siteler_by_kalem = defaultdict(set)
        aktif_siteler_by_kalem = defaultdict(set)
        for k in veri["kaynaklar"]:
            siteler_by_kalem[(k["vertikal"], k["kalem"])].add(k["site"])
            if k.get("aktif"):
                aktif_siteler_by_kalem[(k["vertikal"], k["kalem"])].add(k["site"])

        for anahtar, siteler in sorted(siteler_by_kalem.items()):
            aktif = aktif_siteler_by_kalem.get(anahtar, set())
            # "aktif" sayisina gore etiketle - toplam tanimli kaynak sayisi
            # degil, cunku pasif/birakilmis kaynaklar gercek kapsamayi
            # yansitmiyor (ör. Akakce Cloudflare yuzunden birakildi).
            if len(aktif) >= 2:
                durum = "OK"
            elif len(aktif) == 1:
                durum = "TEK AKTIF KAYNAK"
            else:
                durum = "AKTIF KAYNAK YOK"
            print(
                f"  [{durum}] {anahtar[0]}/{anahtar[1]}: "
                f"toplam {sorted(siteler)}, aktif {sorted(aktif)}"
            )

    def test_akakce_kaynaklari_sayfalama_yapmiyor(self):
        import yaml
        dosya = Path(__file__).parent / "kaynaklar.yaml"
        veri = yaml.safe_load(dosya.read_text(encoding="utf-8"))
        for k in veri["kaynaklar"]:
            if "akakce.com" in k["url"]:
                self.assertEqual(
                    k.get("sayfa_sayisi", 1), 1,
                    f"{k['ad']}: Akakce robots.txt sayfalamayi yasakliyor, sayfa_sayisi 1 olmali",
                )
                self.assertNotIn("{page}", k["url"])


if __name__ == "__main__":
    unittest.main()
