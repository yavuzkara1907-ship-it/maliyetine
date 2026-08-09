# -*- coding: utf-8 -*-
"""hesaplayicilar.py testleri.

En kritik iki sey:
  1. Her hesaplayici KAYNAK tasiyor. Kaynaksiz bir vergi hesabi
     yayinlamak, rakiplerin yaptigi seydir (nekadar.com.tr ve
     maliyeti.com.tr hic kaynak vermiyor) ve bizim tek farkimiz bu.
  2. Sayfada uydurma rakam olmamasi: gorunen her TL tutari ya kullanici
     girdisinden ya resmi parametreden gelmeli.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import hesaplayicilar as hc

JS_KOK = hc.SITE_KOK / "assets" / "js"


class TanimTesti(unittest.TestCase):
    def test_her_hesaplayici_kaynak_tasiyor(self):
        """Kaynaksiz vergi hesabi yayinlamak yok - tek farkimiz bu."""
        for h in hc.HESAPLAYICILAR:
            self.assertTrue(h.get("kaynaklar"), f"{h['id']}: kaynak yok")
            for k in h["kaynaklar"]:
                self.assertGreater(len(k), 10, f"{h['id']}: kaynak cok kisa: {k}")

    # Her hesaplayici UC tipten birine girer ve tipi kaynak bicimini
    # belirler. Bu ayrim projenin can damari: bir hesabin cevabi nereden
    # geliyor sorusunun uc mesru cevabi var, dorduncusu (uydurma) yok.
    MEVZUAT = {"kdv", "maas", "kidem", "tapu", "issizlik", "kira", "izin",
               "mesai", "freelancer"}
    SAF_MATEMATIK = {"kredi", "yuzde", "bilesik-faiz", "birikim",
                     "hisse-maliyet", "kar-zarar", "temettu", "kart-borcu",
                     # lot: cekirdek hesap saf aritmetik (butce / fiyat, tam
                     # sayiya yuvarlama). Komisyon KULLANICIDAN aliniyor ve
                     # bos birakilabiliyor - sabit bir oran GOMULMUYOR, o
                     # yuzden mevzuat/olculen veri sinifina girmiyor.
                     "lot"}
    # RPM resmi olarak yayinlanmiyor - kullanicidan alinir, aralik gosterilir
    KULLANICI_PARAMETRESI = {"icerik", "website"}
    OLCULEN_VERI = {"alim-gucu"}         # parametresi bizim cektigimiz TUFE

    def test_her_hesaplayici_bir_tipe_giriyor(self):
        """Siniflandirilmamis hesaplayici olmasin - yenisi eklenirken
        kaynagin nereden gelecegine karar verilmis olmali."""
        tanimli = self.MEVZUAT | self.SAF_MATEMATIK | self.KULLANICI_PARAMETRESI | self.OLCULEN_VERI
        for h in hc.tum_hesaplayicilar():
            self.assertIn(h["id"], tanimli, f"{h['id']} siniflandirilmamis")

    def test_mevzuata_bagli_hesaplarda_resmi_atif_var(self):
        """Vergi/tazminat hesaplarinda kanun ya da teblig adi gecmek
        ZORUNDA; 'internetten baktim' seviyesinde kaynak kabul edilmez."""
        for h in hc.HESAPLAYICILAR:
            if h["id"] not in self.MEVZUAT:
                continue
            metin = " ".join(h["kaynaklar"])
            self.assertTrue(
                any(x in metin for x in ("Kanun", "Tebliğ", "Bakanlığı", "BKK")),
                f"{h['id']}: resmi atif yok -> {metin}",
            )

    def test_mevzuata_dayanmayan_hesapta_yanlis_resmi_iddia_yok(self):
        """Kredi, yuzde ve YouTube hesaplari mevzuata dayanmiyor; onlara
        teblig atfi yazmak YANLIS BIR GUVEN iddiasi olurdu."""
        for h in hc.HESAPLAYICILAR:
            if h["id"] not in (self.SAF_MATEMATIK | self.KULLANICI_PARAMETRESI):
                continue
            metin = " ".join(h["kaynaklar"])
            for yasak in ("Tebliğ", "Resmî Gazete", "Kanunu"):
                self.assertNotIn(yasak, metin, f"{h['id']}: yanlis resmi atif")

    def test_kullanici_parametreli_hesap_belirsizligi_ACIKCA_soyluyor(self):
        """EN ONEMLI YENI KURAL. YouTube gelirinin tamami RPM'e bagli ve
        RPM resmi olarak yayinlanmiyor. Rakipler oraya uydurma bir sabit
        koyup TEK RAKAM basiyor. Biz uyduramayiz - o yuzden sayfa hem
        parametrenin bizden gelmedigini soylemek hem tek sayi yerine
        ARALIK gostermek ZORUNDA."""
        for h in hc.HESAPLAYICILAR:
            if h["id"] not in self.KULLANICI_PARAMETRESI:
                continue
            metin = (h["ozet"] + " ".join(h["kaynaklar"])).lower()
            self.assertTrue(
                "yayınlanmıyor" in metin or "varsayılmaz" in metin,
                f"{h['id']}: parametrenin kaynaksiz oldugu soylenmemis",
            )
            self.assertIn("duyarlilik", h["js"].lower(),
                          f"{h['id']}: tek sayi yerine aralik gosterilmeli")

    def test_slug_ve_id_benzersiz(self):
        sluglar = [h["slug"] for h in hc.HESAPLAYICILAR]
        idler = [h["id"] for h in hc.HESAPLAYICILAR]
        self.assertEqual(len(sluglar), len(set(sluglar)))
        self.assertEqual(len(idler), len(set(idler)))

    def test_her_hesaplayicida_en_az_3_sss(self):
        """SSS gorunur HTML'de ve schema'da - GEO'nun calistigi yer."""
        for h in hc.HESAPLAYICILAR:
            self.assertGreaterEqual(len(h["sss"]), 3, f"{h['id']}: SSS az")

    def test_sss_cevaplari_dolgu_kalip_icermiyor(self):
        """rehber.py'deki ayni kural: yapay zeka kokan dolgu kaliplari."""
        yasak = ("unutmayın ki", "sonuç olarak", "kısacası", "peki ya",
                 "oldukça önemli", "detaylı bir şekilde")
        for h in hc.HESAPLAYICILAR:
            for soru, cevap in h["sss"]:
                for k in yasak:
                    self.assertNotIn(k, cevap.lower(), f"{h['id']}: dolgu kalip '{k}'")

    def test_mtv_hesaplayicisi_YOK(self):
        """Elimizdeki dogrulanmis MTV kademeleri 1800 cc'ye kadar. 2.0
        motorlu araca yanlis rakam vermek yerine kalemi acmiyoruz -
        eksik vergi tarifesi yayinlamak, hic yayinlamamaktan kotu.
        Bu test o karari kilitliyor: MTV eklenecekse kademeler once
        tam olarak dogrulanmali."""
        self.assertNotIn("mtv", [h["id"] for h in hc.HESAPLAYICILAR])


class SayfaTesti(unittest.TestCase):
    def setUp(self):
        self.sayfalar = {h["slug"]: hc.sayfa_uret(h) for h in hc.tum_hesaplayicilar()}

    def test_json_ld_gecerli_ve_zorunlu_tipleri_iceriyor(self):
        for slug, html in self.sayfalar.items():
            bloklar = re.findall(
                r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
            self.assertTrue(bloklar, f"{slug}: JSON-LD yok")
            veri = json.loads(bloklar[0])
            tipler = {x["@type"] for x in veri["@graph"]}
            for zorunlu in ("WebApplication", "HowTo", "FAQPage", "BreadcrumbList"):
                self.assertIn(zorunlu, tipler, f"{slug}: {zorunlu} yok")

    def test_kaynaklar_sayfada_GORUNUR(self):
        """Schema'ya gomulu olmasi yetmez - kullanici ve AI motoru sayfa
        metnini okuyor. Bu ders daha once SSS'te ogrenildi."""
        for h in hc.tum_hesaplayicilar():
            html = self.sayfalar[h["slug"]]
            for k in h["kaynaklar"]:
                self.assertIn(k, html, f"{h['id']}: kaynak metinde gorunmuyor")

    def test_title_60_karakter_alti(self):
        for slug, html in self.sayfalar.items():
            t = re.search(r"<title>(.*?)</title>", html).group(1)
            self.assertLessEqual(len(t), 65, f"{slug}: title {len(t)} karakter: {t}")

    def test_og_etiketleri_tam(self):
        for slug, html in self.sayfalar.items():
            for e in ("og:image:width", "og:image:height", "og:locale", "og:site_name"):
                self.assertIn(e, html, f"{slug}: {e} yok")

    def test_number_alanlarinda_step_gecerlilik_kisiti_yaratmiyor(self):
        """GERCEK BUG: arac hesaplayicisinda step="50000" yuzunden
        kullanici 1.295.000 gibi gercek bir tutar yazinca HTML5
        validation formu SESSIZCE bloke ediyordu. `step` bir artis
        miktari degil, GECERLILIK KISITI."""
        for slug, html in self.sayfalar.items():
            for adim in re.findall(r'type="number"[^>]*step="([^"]+)"', html):
                self.assertIn(adim, ("1", "0.01", "any"),
                              f"{slug}: step={adim} serbest sayi girisini bloke eder")

    def test_sayfada_uydurma_TL_rakami_yok(self):
        """Gorunen her TL tutari ya kullanici girdisi ornegidir ya resmi
        parametredir. Rakip maliyeti.com.tr tam tersini yapiyor: 6.500.000
        TL gibi rakamlar var, sayfada 'kaynak' kelimesi hic gecmiyor."""
        parametre_metni = (JS_KOK / "resmi-parametreler.js").read_text(encoding="utf-8")
        for h in hc.tum_hesaplayicilar():
            html = self.sayfalar[h["slug"]]
            govde = re.sub(r"<script.*?</script>", "", html, flags=re.S)
            for ham in re.findall(r"([0-9]{1,3}(?:\.[0-9]{3})+(?:,[0-9]+)?) TL", govde):
                sayi = ham.replace(".", "").replace(",", ".")
                # ya resmi parametre dosyasinda ya SSS metninde aciklamali
                self.assertTrue(
                    sayi in parametre_metni or ham in " ".join(
                        c for _, c in h["sss"]) or ham in h["ozet"] or ham in h["meta"],
                    f"{h['id']}: kaynagi belirsiz tutar {ham} TL",
                )

    def test_dizin_tum_hesaplayicilara_link_veriyor(self):
        dizin = hc.dizin_uret()
        for h in hc.tum_hesaplayicilar():
            self.assertIn(f'/{hc.HESAP_KOK}/{h["slug"]}/', dizin)

    def test_olcum_ile_turetme_ayrimi_sayfada_yaziyor(self):
        """Kullanici bu sayfalari olculmus fiyat sanmamali - ikisi ayri
        guven turu. Dizin sayfasi bunu acikca anlatmak zorunda."""
        dizin = hc.dizin_uret()
        self.assertIn("ölçüm değil", dizin.lower().replace("i̇", "i"))

    def test_sitemap_yollari_gercek_dosyalarla_ayni(self):
        yollar = set(hc.sitemap_yollari())
        beklenen = {f"{hc.HESAP_KOK}/"} | {
            f"{hc.HESAP_KOK}/{h['slug']}/" for h in hc.tum_hesaplayicilar()}
        self.assertEqual(yollar, beklenen)

    def test_alim_gucu_VERI_YOKSA_uretilmez(self):
        """rehber.py ile ayni kural: TUFE verisi yoksa uydurma endeksle
        sayfa acmiyoruz, sayfayi hic acmiyoruz. EVDS anahtari tanimli
        degilse enflasyon.json olusmaz."""
        with TemporaryDirectory() as gecici:
            self.assertIsNone(hc.alim_gucu_tanimi(Path(gecici)))
            # ...ve o durumda sitemap'e de girmez
            liste = [h["id"] for h in hc.tum_hesaplayicilar(Path(gecici))]
            self.assertNotIn("alim-gucu", liste)

    def test_alim_gucu_serisi_sayfaya_GOMULU(self):
        """Client-side fetch DEGIL: AI botlarinin cogu JS calistirmiyor.
        Rakip yenibirhesap'i AI motorlari icin gorunmez yapan sey tam
        olarak canli veriyi fetch ile yuklemesi."""
        ag = hc.alim_gucu_tanimi()
        if not ag:
            self.skipTest("TUFE verisi yok")
        html = hc.sayfa_uret(ag)
        self.assertIn("TUFE_SERISI", html)
        self.assertIn(ag["_tufe"]["seri"][0]["tarih"], html)

    def test_opsiyonel_alanda_required_YOK(self):
        """GERCEK BUG (tarayici testi yakaladi): YouTube hesabinda RPM
        alani "bos birakabilirsiniz" diyordu ama required tasidigi icin
        HTML5 validation submit'i SESSIZCE bloke ediyordu - sayfa hic
        sonuc uretmiyordu. Arac hesaplayicisindaki step bug'inin ayni
        sinifi: form nitelikleri gorunum degil GECERLILIK KISITI."""
        for h in hc.tum_hesaplayicilar():
            html = hc.sayfa_uret(h)
            for a in h["alanlar"]:
                if a["tip"] != "number" or a.get("zorunlu", True):
                    continue
                girdi = re.search(rf'<input[^>]*id="{a["id"]}"[^>]*>', html).group(0)
                self.assertNotIn("required", girdi,
                                 f"{h['id']}/{a['id']}: opsiyonel alanda required var")


class ParametreDosyasiTesti(unittest.TestCase):
    """Resmi parametreler JS'te; Python tarafi da onlarin varligini
    dogruluyor ki iki taraf ayrismasin."""

    def test_parametre_dosyasi_her_kumede_kaynak_tasiyor(self):
        metin = (JS_KOK / "resmi-parametreler.js").read_text(encoding="utf-8")
        self.assertIn("gecerli_bitis", metin)
        # Her kaynak alani dolu olmali
        for m in re.finditer(r"kaynak:\s*\"([^\"]*)\"", metin):
            self.assertGreater(len(m.group(1)), 10, f"kisa kaynak: {m.group(1)}")

    def test_kidem_tavani_gecerlilik_penceresi_alti_ay(self):
        """Kidem tavani yilda IKI KEZ degisiyor - dosyadaki en kisa
        omurlu parametre. Penceresi bir yil yazilmissa hata."""
        metin = (JS_KOK / "resmi-parametreler.js").read_text(encoding="utf-8")
        blok = metin[metin.index("kidem_tavani"):metin.index("ihbar:")]
        self.assertIn('gecerli_baslangic: "2026-07-01"', blok)
        self.assertIn('gecerli_bitis: "2026-12-31"', blok)

if __name__ == "__main__":
    unittest.main()
