# -*- coding: utf-8 -*-
"""
maliyetine.com - Statik Sayfa Ureteci (v0.2)

/veri/{vertikal}.json'daki (agrega.py ciktisi) GERCEK sayilari statik
HTML'e gomer - GEO icin sart: AI botlarinin cogu (GPTBot vb.) JavaScript
calistirmaz, bu yuzden cevap bloğundaki rakam sayfa kaynagi HTML'inde
(fetch ile degil) bulunmak zorunda. Hesaplayici (JS, etkilesimli) bu
kisitlamaya tabi degil - ama endeks sayfasi (GEO'nun hedefi) build-time'da
uretilir.

v0.2: vertikal-agnostik. Her vertikal VERTIKALLER sozlugunde tanimlanir
(kalem listesi, basliklar, olcek alani); yeni vertikal eklemek = bir
sozluk girdisi, kod degil.

Aylik otomasyonda sirasi: motor.py -> agrega.py -> sayfa_uret.py -> commit.

Kullanim:
  python sayfa_uret.py --vertikal dugun
  python sayfa_uret.py --vertikal ev-kurma
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).parent
SITE_KOK = BASE_DIR.parent

# NOT: assets/js/{vertikal}-kalemler.js ile ayni liste (kasitli kucuk
# tekrar - iki dosya arasinda build araci olmadan paylasmak, "basit tut"
# ilkesine gore mevcut kod hacmine deger katmiyor; liste kisa ve nadiren
# degisiyor).
DUGUN_KALEMLERI = [
    {"id": "gelinlik", "ad": "Gelinlik", "birim": "sabit"},
    {"id": "damatlik", "ad": "Damatlık / Takım Elbise", "birim": "sabit"},
    {"id": "alyans", "ad": "Alyans", "birim": "sabit"},
    {"id": "gelin-ayakkabisi", "ad": "Gelin Ayakkabısı, Duvak, Aksesuar", "birim": "sabit"},
    {"id": "nikah-sekeri", "ad": "Nikah Şekeri", "birim": "sabit"},
    {"id": "davetiye", "ad": "Davetiye", "birim": "sabit"},
    # 2026-07-25: tahminiden GERCEK kaynaga tasindi (Atasay altin bilezik,
    # 24 urun). Onceki tahmin orta 40.000 TL idi, gercek olcum ~81.000 -
    # tahmin DUSUKTU. Kalem adi bilincli olarak DARALTILDI: dugunde
    # takilan TOPLAM altin olculemez (davetli/gelenek degiskeni), ama bir
    # bilezigin fiyati olculebilir.
    {"id": "taki-altin", "ad": "Takı — Altın Bilezik (1 adet)", "birim": "sabit"},
    # Salon iki TANIMLI varyant (bkz. kaynaklar.yaml salon-yemekli /
    # salon-kokteyl). Ikisi de tabloda fiyatiyla GORUNUR ama toplama
    # yalnizca "varsayilan_dahil" olan girer - aksi halde ayni salon iki
    # kez sayilir. yemek_dahil=True olan varyant secildiginde ayri
    # "yemek-ikram" tahmini kalemi de cift sayim olur, o yuzden onun
    # varsayilan_dahil'i False.
    {
        "id": "salon-yemekli", "ad": "Düğün Salonu — yemekli (menü dahil)",
        "birim": "kisi_basi", "secim_grubu": "salon", "yemek_dahil": True,
        "varsayilan_dahil": True,
    },
    {
        "id": "salon-kokteyl", "ad": "Düğün Salonu — kokteyl (yemeksiz)",
        "birim": "kisi_basi", "secim_grubu": "salon", "yemek_dahil": False,
        "varsayilan_dahil": False,
    },
    # 2026-07-25: tahmini listeden GERCEK kaynaga tasindi (deger artik
    # ayni mekanin yemekli/kokteyl fiyat farkindan OLCULUYOR, bkz.
    # kaynaklar.yaml fark modu). Onceki tahmin 700 TL/kisi idi, gercek
    # olcum 410 TL - 1.7 kat sapma.
    #
    # AMA TOPLAMA HIC GIRMEZ (bilgi_amacli): "kokteyl + menu bedeli"
    # tanim geregi "yemekli" fiyatina esit olmali (fark = yemekli -
    # kokteyl), yani ayri kalem olarak toplamak ayni sayiya dolambacli
    # yoldan gitmek olur. Ustelik esitlik pratikte BOZULUYOR: her kalem
    # BAGIMSIZ segmentleniyor, "orta segment yemekli mekan" ile "orta
    # segment kokteyl mekan" ayni mekanlar degil - uc ayri alt kumenin
    # medyani toplaninca %24 tutarsizlik cikiyor. Bu yuzden deger
    # yalnizca REFERANS olarak gosterilir: "yemekli secmek kisi basi
    # yaklasik bu kadar ekler".
    {
        "id": "yemek-ikram", "ad": "Yemek / İkram (mekanın menü bedeli)",
        "birim": "kisi_basi", "bilgi_amacli": True,
    },
    # 2026-07-26: dort hizmet kalemi tahminiden GERCEK kaynaga tasindi
    # (dugun.com il bazli fiyat tablolari, Istanbul satiri).
    #
    # `tek_deger`: bu kalemlerde SEGMENT KIRILIMI YOK - kaynak tek bir
    # Istanbul rakami veriyor, uc ayri fiyat bandi degil. Ekonomik/orta/ust
    # secildiginde ayni rakam kullanilir ve sayfada bu ACIKCA yazilir.
    # Neden 27 ilin tamamini alip persentille segmentlemedik: cografi fark
    # fiyat segmenti DEGILDIR - "ekonomik fotografci" ucuz bir il demek
    # olmaz. Salon kalemindeki "ne olctugu belirsiz" hatasini tekrarlamamak
    # icin tek ve tanimli bir olcum tercih edildi.
    {"id": "fotografci", "ad": "Fotoğraf ve Video", "birim": "sabit", "tek_deger": True},
    {"id": "organizasyon", "ad": "Organizasyon / Süsleme", "birim": "sabit", "tek_deger": True},
    {"id": "kuafor-makyaj", "ad": "Kuaför ve Makyaj", "birim": "sabit", "tek_deger": True},
    {"id": "gelin-arabasi", "ad": "Gelin Arabası", "birim": "sabit", "tek_deger": True},
]

# Henuz kazima kaynagi olmayan kalemler. Yavuz'un acik talimatiyla
# (2026-07-24) genel piyasa arastirmasindan (WebSearch, birden fazla
# ilan/fiyat sitesi) turetilmis TEK SEFERLIK tahmini degerler - motor.py'nin
# surekli kazidigi, tarihli/orneklemli "gercek kaynak" ile AYNI SEY DEGIL.
# Sayfada HER ZAMAN ayri "Tahmini" etiketiyle gosterilir (bkz. sayfa_uret,
# metodoloji sayfasindaki aciklama). arastirma_tarihi elle tekrar
# arastirilip gozden gecirilmedikce SABIT kalir, motor.py gibi otomatik
# guncellenmez.
DUGUN_KALEMLERI_TAHMINI = [
    {
        "id": "orkestra-dj", "ad": "Orkestra / DJ", "birim": "sabit",
        "tahmini": {"dusuk": 5000, "orta": 25000, "luks": 80000},
        "kaynak_notu": "Düğün orkestra/DJ kiralama fiyat araştırması.",
        "arastirma_tarihi": "2026-07-24",
    },
    {
        "id": "nikah-islemleri", "ad": "Nikah İşlemleri (resmi harçlar)", "birim": "sabit",
        "tahmini": {"dusuk": 1500, "orta": 3500, "luks": 8000},
        "kaynak_notu": "Belediye nikah/evlendirme dairesi harç ücreti araştırması (2026 tarifeleri).",
        "arastirma_tarihi": "2026-07-24",
    },
]

# Ev kurma vertikali TAMAMEN urun bazli - her kalem tek bir fiziksel urun,
# hepsi gercek kazima kaynagindan (Trendyol) geliyor. Tahmini kalem YOK.
EV_KURMA_KALEMLERI = [
    {"id": "buzdolabi", "ad": "Buzdolabı", "birim": "sabit", "grup": "Beyaz eşya"},
    {"id": "camasir-makinesi", "ad": "Çamaşır Makinesi", "birim": "sabit", "grup": "Beyaz eşya"},
    {"id": "kurutma-makinesi", "ad": "Kurutma Makinesi", "birim": "sabit", "grup": "Beyaz eşya"},
    {"id": "bulasik-makinesi", "ad": "Bulaşık Makinesi", "birim": "sabit", "grup": "Beyaz eşya"},
    {"id": "firin-ocak", "ad": "Ankastre Fırın / Ocak Seti", "birim": "sabit", "grup": "Beyaz eşya"},
    {"id": "davlumbaz", "ad": "Davlumbaz", "birim": "sabit", "grup": "Beyaz eşya"},
    {"id": "mikrodalga", "ad": "Mikrodalga Fırın", "birim": "sabit", "grup": "Beyaz eşya"},
    {"id": "klima", "ad": "Klima", "birim": "sabit", "grup": "Beyaz eşya"},

    {"id": "koltuk-takimi", "ad": "Koltuk Takımı", "birim": "sabit", "grup": "Mobilya"},
    {"id": "yemek-masasi", "ad": "Yemek Odası Takımı", "birim": "sabit", "grup": "Mobilya"},
    {"id": "tv-unitesi", "ad": "TV Ünitesi", "birim": "sabit", "grup": "Mobilya"},
    {"id": "sehpa", "ad": "Orta Sehpa", "birim": "sabit", "grup": "Mobilya"},
    {"id": "konsol", "ad": "Konsol", "birim": "sabit", "grup": "Mobilya"},
    {"id": "yatak", "ad": "Çift Kişilik Yatak", "birim": "sabit", "grup": "Yatak odası"},
    {"id": "karyola", "ad": "Karyola / Baza", "birim": "sabit", "grup": "Yatak odası"},
    {"id": "gardirop", "ad": "Gardırop", "birim": "sabit", "grup": "Yatak odası"},
    {"id": "komodin", "ad": "Komodin", "birim": "sabit", "grup": "Yatak odası"},
    {"id": "sifonyer", "ad": "Şifonyer", "birim": "sabit", "grup": "Yatak odası"},
    {"id": "boy-aynasi", "ad": "Boy Aynası", "birim": "sabit", "grup": "Yatak odası"},

    {"id": "televizyon", "ad": "Televizyon (4K)", "birim": "sabit", "grup": "Elektronik"},
    {"id": "supurge", "ad": "Robot Süpürge", "birim": "sabit", "grup": "Elektronik"},
    {"id": "dikey-supurge", "ad": "Dikey Süpürge", "birim": "sabit", "grup": "Elektronik"},

    {"id": "airfryer", "ad": "Airfryer", "birim": "sabit", "grup": "Küçük ev aleti"},
    {"id": "kahve-makinesi", "ad": "Kahve Makinesi", "birim": "sabit", "grup": "Küçük ev aleti"},
    {"id": "su-isitici", "ad": "Su Isıtıcı (Kettle)", "birim": "sabit", "grup": "Küçük ev aleti"},
    {"id": "tost-makinesi", "ad": "Tost Makinesi", "birim": "sabit", "grup": "Küçük ev aleti"},
    {"id": "blender", "ad": "Blender", "birim": "sabit", "grup": "Küçük ev aleti"},
    {"id": "mutfak-robotu", "ad": "Mutfak Robotu / Doğrayıcı", "birim": "sabit", "grup": "Küçük ev aleti"},
    {"id": "utu", "ad": "Ütü", "birim": "sabit", "grup": "Küçük ev aleti"},
    {"id": "sac-kurutma-makinesi", "ad": "Saç Kurutma Makinesi", "birim": "sabit", "grup": "Küçük ev aleti"},

    {"id": "tencere-seti", "ad": "Tencere Seti", "birim": "sabit", "grup": "Mutfak"},
    {"id": "tava-seti", "ad": "Tava Seti", "birim": "sabit", "grup": "Mutfak"},
    {"id": "catal-kasik-bicak-takimi", "ad": "Çatal-Kaşık-Bıçak Takımı", "birim": "sabit", "grup": "Mutfak"},
    {"id": "yemek-takimi", "ad": "Yemek Takımı", "birim": "sabit", "grup": "Mutfak"},
    {"id": "kahvalti-takimi", "ad": "Kahvaltı Takımı", "birim": "sabit", "grup": "Mutfak"},
    {"id": "bardak-takimi", "ad": "Bardak Takımı", "birim": "sabit", "grup": "Mutfak"},

    {"id": "nevresim-takimi", "ad": "Nevresim Takımı", "birim": "sabit", "grup": "Tekstil"},
    {"id": "havlu-takimi", "ad": "Havlu Takımı", "birim": "sabit", "grup": "Tekstil"},
    {"id": "bornoz", "ad": "Bornoz", "birim": "sabit", "grup": "Tekstil"},
    {"id": "perde", "ad": "Perde", "birim": "sabit", "grup": "Tekstil"},
    {"id": "hali", "ad": "Halı", "birim": "sabit", "grup": "Tekstil"},
    {"id": "aydinlatma", "ad": "Avize / Aydınlatma", "birim": "sabit", "grup": "Tekstil"},
]

# 0 km arac vertikali (2026-07-25). Kalemler NET TANIMLI tutuldu: tum
# modellerin ham medyani YANILTICI olurdu (listede Porsche ile Fiat esit
# agirlikta, medyan ~3.2M cikiyor ama gercekte alinan arac 1.5-2M bandinda
# - liste agirligi satis agirligi DEGIL). Bkz. kaynaklar.yaml.
ARAC_KALEMLERI = [
    {
        "id": "en-ucuz-sifir-arac",
        "ad": "En ucuz sıfır araç (marka giriş fiyatı)",
        "birim": "sabit",
    },
    # 24 markanin model fiyat listeleri. TOPLAMA GIRMEZ (bilgi_amacli):
    # birbirinin alternatifi, toplamak anlamsiz sayi uretir.
    {"id": "togg", "ad": "Togg", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "renault", "ad": "Renault", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "chery", "ad": "Chery", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "dacia", "ad": "Dacia", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "citroen", "ad": "Citroen", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "opel", "ad": "Opel", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "peugeot", "ad": "Peugeot", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "ford", "ad": "Ford", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "hyundai", "ad": "Hyundai", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "kia", "ad": "Kia", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "skoda", "ad": "Skoda", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "seat", "ad": "Seat", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "honda", "ad": "Honda", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "toyota", "ad": "Toyota", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "fiat", "ad": "Fiat", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "volkswagen", "ad": "Volkswagen", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "nissan", "ad": "Nissan", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "mg", "ad": "MG", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "bmw", "ad": "BMW", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "mercedes", "ad": "Mercedes", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "byd", "ad": "BYD", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "tesla", "ad": "Tesla", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "suzuki", "ad": "Suzuki", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
    {"id": "cupra", "ad": "Cupra", "birim": "sabit", "grup": "Marka bazlı fiyatlar", "bilgi_amacli": True},
]


# Okul vertikali (2026-07-26) - 4. vertikal, tamamen urun bazli.
# Agustos-Eylul arama zirvesine yetismek icin acildi.
#
# `varsayilan_dahil: False` olanlar: tablet, calisma masasi ve sandalyesi
# HER YIL alinmaz - bir kez alinip yillarca kullanilir. Yillik okul
# masrafi sorusuna cevap veren toplam bunlari ICERMEZ; kullanici
# hesaplayicidan isterse ekler. Aksi halde "okul masrafi 60.000 TL" gibi
# yaniltici bir rakam cikardi.
OKUL_KALEMLERI = [
    {"id": "okul-cantasi", "ad": "Okul Çantası", "birim": "sabit", "grup": "Çanta ve beslenme"},
    {"id": "beslenme-cantasi", "ad": "Beslenme Çantası", "birim": "sabit", "grup": "Çanta ve beslenme"},
    {"id": "matara", "ad": "Suluk / Matara", "birim": "sabit", "grup": "Çanta ve beslenme"},
    {"id": "kalem-kutusu", "ad": "Kalem Kutusu", "birim": "sabit", "grup": "Kırtasiye"},
    {"id": "defter", "ad": "Defter", "birim": "sabit", "grup": "Kırtasiye"},
    {"id": "kalem", "ad": "Kalem", "birim": "sabit", "grup": "Kırtasiye"},
    {"id": "boya-seti", "ad": "Boya Seti", "birim": "sabit", "grup": "Kırtasiye"},
    {"id": "resim-malzemeleri", "ad": "Resim ve Sanat Malzemeleri", "birim": "sabit", "grup": "Kırtasiye"},
    {"id": "ders-kitabi", "ad": "Ders ve Yardımcı Kitap", "birim": "sabit", "grup": "Kitap"},
    {"id": "sozluk", "ad": "Sözlük", "birim": "sabit", "grup": "Kitap"},
    {"id": "ayakkabi", "ad": "Spor Ayakkabı", "birim": "sabit", "grup": "Giyim"},
    {"id": "tablet", "ad": "Tablet", "birim": "sabit", "grup": "Teknoloji", "varsayilan_dahil": False},
    {"id": "calisma-masasi", "ad": "Çalışma Masası", "birim": "sabit", "grup": "Çalışma alanı", "varsayilan_dahil": False},
    {"id": "calisma-sandalyesi", "ad": "Çalışma Sandalyesi", "birim": "sabit", "grup": "Çalışma alanı", "varsayilan_dahil": False},
]


# Bebek vertikali (2026-07-26) - 5. vertikal.
#
# `varsayilan_dahil: False` -> bebek bezi. NEDEN: bez SARF malzemesi,
# aylik tekrarliyor; digerleri tek seferlik kurulum. Ikisini tek toplama
# katmak "bebek maliyeti 45.000 TL" gibi ne oldugu belirsiz bir rakam
# uretirdi. Toplam = tek seferlik hazirlik; bez ayrica gosteriliyor.
BEBEK_KALEMLERI = [
    {"id": "bebek-arabasi", "ad": "Bebek Arabası", "birim": "sabit", "grup": "Uyku ve taşıma"},
    {"id": "besik", "ad": "Beşik", "birim": "sabit", "grup": "Uyku ve taşıma"},
    {"id": "park-yatak", "ad": "Park Yatak / Oyun Parkı", "birim": "sabit", "grup": "Uyku ve taşıma"},
    {"id": "oto-koltugu", "ad": "Oto Koltuğu", "birim": "sabit", "grup": "Uyku ve taşıma"},
    {"id": "mama-sandalyesi", "ad": "Mama Sandalyesi", "birim": "sabit", "grup": "Beslenme"},
    {"id": "biberon-seti", "ad": "Biberon Seti", "birim": "sabit", "grup": "Beslenme"},
    {"id": "gogus-pompasi", "ad": "Göğüs Pompası", "birim": "sabit", "grup": "Beslenme"},
    {"id": "bebek-kuveti", "ad": "Bebek Küveti", "birim": "sabit", "grup": "Bakım"},
    {"id": "zibin-seti", "ad": "Zıbın / Body Seti", "birim": "sabit", "grup": "Tekstil"},
    {"id": "uyku-tulumu", "ad": "Uyku Tulumu", "birim": "sabit", "grup": "Tekstil"},
    {"id": "bebek-bezi", "ad": "Bebek Bezi (aylık)", "birim": "sabit", "grup": "Aylık sarf",
     "varsayilan_dahil": False},
]

VERTIKALLER = {
    "dugun": {
        "ad": "Düğün",
        "yol": "dugun",
        "kalemler": DUGUN_KALEMLERI,
        "tahmini_kalemler": DUGUN_KALEMLERI_TAHMINI,
        "baslik": "2026'da İstanbul'da Düğün Kaça Mal Olur?",
        "soru": "2026'da İstanbul'da düğün kaça mal olur?",
        "sayfa_basligi": "2026'da Düğün Kaça Mal Olur? | Maliyeti Ne?",
        "meta_aciklama": (
            "Gelinlik, damatlık, alyans, salon ve daha fazlası: gerçek fiyat "
            "verisinden derlenmiş, aylık güncellenen düğün maliyeti endeksi."
        ),
        "dataset_ad": "Maliyeti Ne? Düğün Maliyeti Endeksi",
        "dataset_aciklama": (
            "Türkiye'de düğün kalemlerinin gerçek e-ticaret ve ilan verisinden "
            "derlenen aylık fiyat endeksi."
        ),
        # kisi_basi kalemleri carpan olcegi (davetli sayisi)
        "olcek_varsayilan": 150,
        "ornek_ifade": "{olcek} kişilik, orta segment bir düğünün",
        # Ana sayfada "... X TL tutuyor" kalibiyla kullanilir, o yuzden
        # YALIN hal (endeks sayfasindaki genitifli ifade orada "tutmasi
        # bekleniyor" ile kullaniliyor).
        "anasayfa_ifade": "{olcek} kişilik, orta segment bir düğün",
        "kart_alt": "{olcek} kişilik, orta segment",
        "hesaplayici_daveti": "Kendi davetli sayınız ve segmentinizle hesaplayın →",
        "kapsam_yer": "İstanbul, Türkiye",
        "keywords": [
            "düğün maliyeti", "düğün fiyatları 2026", "gelinlik fiyatları",
            "düğün salonu kişi başı fiyat", "alyans fiyatları",
            "damatlık fiyatları", "İstanbul düğün maliyeti",
            "düğün bütçesi hesaplama",
        ],
        # FAQPage'e veriden GERCEK sayilarla ek soru uretilecek kalemler.
        # Arama/AI tarafinda ayri ayri sorulan, verisi saglam olanlar.
        "one_cikan_kalemler": [
            "salon-yemekli", "gelinlik", "damatlik", "alyans", "taki-altin",
        ],
        "dahil_olanlar": [
            "Gelinlik, damatlık, alyans ve ölçülebilen temel ürün kalemleri.",
            "Yemekli düğün salonu için kişi başı mekan/menü bedeli.",
            "Kaynak bulunamayan hizmet kalemleri için açıkça etiketlenmiş tahmini kalemler.",
        ],
        "dahil_olmayanlar": [
            "Balayı, ayrı tatil vertikaliyle ele alınacak.",
            "Davetlilerin taktığı toplam altın; bunun yerine ölçülebilir bir bilezik fiyatı izlenir.",
            "Şehir dışı ulaşım, konaklama ve kişiye özel ekstra talepler.",
        ],
        "segment_aciklama": (
            "Ekonomik segment düşük fiyat bandını, orta segment piyasadaki ortalama "
            "bütçeyi, lüks segment ise üst fiyat bandını gösterir. Hizmetlerde "
            "aynı mekanın tüm seçenekleri aynı kapsamı sunmayabilir; bu yüzden "
            "toplam senaryoda yemekli salon ayrı, kokteyl salon ayrı değerlendirilir."
        ),
        "kalem_sayfalari": [
            {
                "id": "gelinlik",
                "slug": "gelinlik-fiyatlari",
                "baslik": "2026'da Gelinlik Fiyatları Ne Kadar?",
                "soru": "2026'da gelinlik fiyatları ne kadar?",
                "aciklama": (
                    "Gelinlik fiyatı hazır giyim, gelinlik evi ve ikinci el segmentleri "
                    "karıştırılmadan izlenmesi gereken bir kalemdir."
                ),
            },
            {
                "id": "damatlik",
                "slug": "damatlik-fiyatlari",
                "baslik": "2026'da Damatlık Fiyatları Ne Kadar?",
                "soru": "2026'da damatlık fiyatları ne kadar?",
                "aciklama": (
                    "Damatlık verisi takım elbise ve smokin fiyatlarını birlikte "
                    "okutur; marka segment farkı yüksek olabilir."
                ),
            },
            {
                "id": "alyans",
                "slug": "alyans-fiyatlari",
                "baslik": "2026'da Alyans Fiyatları Ne Kadar?",
                "soru": "2026'da alyans fiyatları ne kadar?",
                "aciklama": (
                    "Alyans fiyatı ayar, gram ve marka farkından hızlı etkilenir; "
                    "bu yüzden kaynaklar arası fark ayrıca izlenir."
                ),
            },
            {
                "id": "salon-yemekli",
                "slug": "dugun-salonu-fiyatlari",
                "baslik": "Düğün Salonu Kişi Başı Fiyatları 2026",
                "soru": "2026'da düğün salonu kişi başı fiyatı ne kadar?",
                "aciklama": (
                    "Yemekli salon fiyatı menü dahil kişi başı bedeldir. Kokteyl "
                    "seçeneği ayrı ölçülür; ikisi aynı toplamda birlikte sayılmaz."
                ),
            },
        ],
    },
    "ev-kurma": {
        "ad": "Ev Kurma",
        "yol": "ev-kurma",
        "kalemler": EV_KURMA_KALEMLERI,
        "tahmini_kalemler": [],
        "baslik": "2026'da Sıfırdan Ev Kurmak Kaça Mal Olur?",
        "soru": "2026'da sıfırdan ev kurmak kaça mal olur?",
        "sayfa_basligi": "2026'da Ev Kurmak Kaça Mal Olur? | Maliyeti Ne?",
        "meta_aciklama": (
            "Gerçek e-ticaret verisinden derlenmiş, aylık güncellenen ev kurma "
            "maliyeti endeksi. Beyaz eşya, mobilya, mutfak, tekstil — 42 kalem, "
            "kaynak ve tarihiyle."
        ),
        "dataset_ad": "Maliyeti Ne? Ev Kurma Maliyeti Endeksi",
        "dataset_aciklama": (
            "Türkiye'de sıfırdan ev kurmak için gereken beyaz eşya, mobilya, "
            "mutfak ve tekstil kalemlerinin gerçek e-ticaret verisinden derlenen "
            "aylık fiyat endeksi."
        ),
        "olcek_varsayilan": 1,
        "ornek_ifade": (
            "sıfırdan, orta segment bir evi eşyalandırmanın "
            "(beyaz eşya + mobilya + mutfak + tekstil)"
        ),
        "anasayfa_ifade": "sıfırdan bir evi eşyalandırmak (orta segment)",
        "kart_alt": "orta segment, tüm eşya",
        "hesaplayici_daveti": "Kendi eşya listenizle ve segmentinizle hesaplayın →",
        "kapsam_yer": "Türkiye",
        "keywords": [
            "ev kurma maliyeti", "evlilik eşya listesi fiyatları",
            "beyaz eşya fiyatları 2026", "mobilya fiyatları",
            "sıfırdan ev eşyası maliyeti", "çeyiz maliyeti",
            "buzdolabı fiyatları", "çamaşır makinesi fiyatları",
        ],
        "one_cikan_kalemler": [
            "buzdolabi", "camasir-makinesi", "koltuk-takimi", "televizyon",
            "yatak", "gardirop",
        ],
        "dahil_olanlar": [
            "Beyaz eşya, mobilya, yatak odası, elektronik, küçük ev aleti, mutfak ve tekstil kalemleri.",
            "Her kalemden bir adet veya bir standart takım varsayımı.",
            "Gerçek e-ticaret kategori verisinden derlenen ekonomik, orta ve lüks segment fiyatları.",
        ],
        "dahil_olmayanlar": [
            "Konut satın alma veya kira bedeli.",
            "Tadilat, işçilik, nakliye, montaj ve kurulum hizmetleri.",
            "Temizlik malzemesi, sarf ürünleri ve kişisel zevke göre değişen dekorasyon parçaları.",
        ],
        "segment_aciklama": (
            "Ekonomik segment temel işlevi karşılayan alt fiyat bandını, orta segment "
            "ev kurma bütçesinde beklenen ortalama fiyatı, lüks segment ise daha yüksek "
            "marka/kapasite bandını gösterir. Ev kurma endeksinde tüm kalemler sabit "
            "birimli ürün olduğu için davetli sayısı gibi ek çarpan kullanılmaz."
        ),
        "kalem_sayfalari": [
            {
                "id": "buzdolabi",
                "slug": "buzdolabi-fiyatlari",
                "baslik": "2026'da Buzdolabı Fiyatları Ne Kadar?",
                "soru": "2026'da buzdolabı fiyatları ne kadar?",
                "aciklama": (
                    "Buzdolabı ev kurma bütçesinin ana beyaz eşya kalemlerinden biridir; "
                    "kapasite ve enerji sınıfı fiyat bandını belirgin değiştirir."
                ),
            },
            {
                "id": "camasir-makinesi",
                "slug": "camasir-makinesi-fiyatlari",
                "baslik": "2026'da Çamaşır Makinesi Fiyatları Ne Kadar?",
                "soru": "2026'da çamaşır makinesi fiyatları ne kadar?",
                "aciklama": (
                    "Çamaşır makinesi fiyatları kapasite, kurutma özelliği ve enerji "
                    "sınıfına göre ayrışır."
                ),
            },
            {
                "id": "koltuk-takimi",
                "slug": "koltuk-takimi-fiyatlari",
                "baslik": "2026'da Koltuk Takımı Fiyatları Ne Kadar?",
                "soru": "2026'da koltuk takımı fiyatları ne kadar?",
                "aciklama": (
                    "Koltuk takımı ev kurma bütçesinde mobilya grubunun en büyük "
                    "kalemlerinden biridir; takım içeriği fiyatı doğrudan etkiler."
                ),
            },
            {
                "id": "gardirop",
                "slug": "gardirop-fiyatlari",
                "baslik": "2026'da Gardırop Fiyatları Ne Kadar?",
                "soru": "2026'da gardırop fiyatları ne kadar?",
                "aciklama": (
                    "Gardırop fiyatları kapak sayısı, ölçü ve malzeme kalitesine göre "
                    "geniş bir aralıkta değişir."
                ),
            },
            {
                "id": "televizyon",
                "slug": "televizyon-fiyatlari",
                "baslik": "2026'da Televizyon Fiyatları Ne Kadar?",
                "soru": "2026'da televizyon fiyatları ne kadar?",
                "aciklama": (
                    "Televizyon fiyatlarında ekran boyutu, panel türü ve akıllı TV "
                    "özellikleri fiyat bandını belirler."
                ),
            },
        ],
    },
    "okul": {
        "ad": "Okul",
        "yol": "okul",
        "kalemler": OKUL_KALEMLERI,
        "tahmini_kalemler": [],
        "baslik": "2026'da Okul Masrafı Ne Kadar?",
        "soru": "2026'da bir öğrencinin okul masrafı ne kadar?",
        "sayfa_basligi": "Okul Masrafı 2026: Ne Kadar Tutuyor? | Maliyeti Ne?",
        "meta_aciklama": (
            "Çanta, kırtasiye, kitap, ayakkabı: bir öğrencinin okul masrafı "
            "kalem kalem. Gerçek fiyat verisinden, aylık güncellenen endeks."
        ),
        "dataset_ad": "Maliyeti Ne? Okul Masrafı Endeksi",
        "dataset_aciklama": (
            "Türkiye'de bir öğrencinin okul alışverişi kalemlerinin gerçek "
            "e-ticaret verisinden derlenen aylık fiyat endeksi."
        ),
        "olcek_varsayilan": 1,
        "ornek_ifade": "bir öğrencinin okul masrafının",
        "anasayfa_ifade": "bir öğrencinin okul masrafı",
        "kart_alt": "bir öğrenci, yıllık",
        "hesaplayici_daveti": "Kendi listenizi seçip hesaplayın →",
        "dahil_olanlar": [
            "Okul çantası, beslenme çantası ve suluk.",
            "Kırtasiye: kalem kutusu, defter, kalem, boya ve resim malzemeleri.",
            "Ders ve yardımcı kitaplar, sözlük.",
            "Spor ayakkabı.",
        ],
        "dahil_olmayanlar": [
            "Okul kayıt ücreti, bağış ve özel okul taksiti.",
            "Servis ve yemek ücreti — bunlar okula ve şehre göre çok değişiyor.",
            "Kurs, etüt ve özel ders.",
            "Okul forması ve önlük — kategori bazlı ölçülebilir bir kaynak bulunamadı.",
            "Tablet, çalışma masası ve sandalyesi varsayılan toplamda yok: "
            "her yıl değil, bir kez alınıyor. Hesaplayıcıdan ekleyebilirsiniz.",
        ],
        "segment_aciklama": (
            "Ekonomik segment temel ihtiyacı karşılayan alt fiyat bandını, orta "
            "segment yaygın tercih edilen ürünleri, üst segment ise marka ve "
            "kapasite olarak daha yüksek bandı gösterir. Rakamlar tek öğrenci "
            "içindir; iki çocuklu bir ailede tutar yaklaşık iki katına çıkar."
        ),
        "kalem_sayfalari": [
            {
                "id": "okul-cantasi",
                "slug": "okul-cantasi-fiyatlari",
                "baslik": "2026'da Okul Çantası Fiyatları Ne Kadar?",
                "soru": "2026'da okul çantası fiyatları ne kadar?",
                "aciklama": (
                    "Okul çantası fiyatı sırt desteği, hacim ve markaya göre "
                    "ayrışır; ilkokul ve lise modelleri farklı bantlardadır."
                ),
            },
        ],
    },
    "bebek": {
        "ad": "Bebek",
        "yol": "bebek",
        "kalemler": BEBEK_KALEMLERI,
        "tahmini_kalemler": [],
        "baslik": "2026'da Bebek Hazırlığı Kaça Mal Olur?",
        "soru": "2026'da bebek hazırlığı kaça mal olur?",
        "sayfa_basligi": "Bebek Maliyeti 2026: Ne Kadar Tutuyor? | Maliyeti Ne?",
        "meta_aciklama": (
            "Bebek arabası, beşik, oto koltuğu, biberon: yeni doğan hazırlığı "
            "kalem kalem. Gerçek fiyat verisinden, ayda iki kez ölçülen endeks."
        ),
        "dataset_ad": "Maliyeti Ne? Bebek Hazırlığı Endeksi",
        "dataset_aciklama": (
            "Türkiye'de yeni doğan bebek hazırlığı kalemlerinin gerçek "
            "e-ticaret verisinden derlenen fiyat endeksi."
        ),
        "olcek_varsayilan": 1,
        "ornek_ifade": "bebek hazırlığının",
        "anasayfa_ifade": "bebek hazırlığı",
        "kart_alt": "tek seferlik hazırlık",
        "hesaplayici_daveti": "Kendi listenizi seçip hesaplayın →",
        "dahil_olanlar": [
            "Uyku ve taşıma: bebek arabası, beşik, park yatak, oto koltuğu.",
            "Beslenme: mama sandalyesi, biberon seti, göğüs pompası.",
            "Bakım ve tekstil: küvet, zıbın seti, uyku tulumu.",
        ],
        "dahil_olmayanlar": [
            "Doğum masrafı, hastane ve doktor ücretleri.",
            "Bebek bezi ve mama gibi aylık sarf giderleri varsayılan toplamda "
            "yok — tek seferlik hazırlıkla karıştırmamak için ayrı gösteriliyor.",
            "Bebek odası mobilyası (dolap, komodin) — ev kurma endeksinde.",
            "Kreş, bakıcı ve sağlık sigortası.",
            "Biberon sterilizatörü — ölçmeyi denedik, kaynakta sterilizatör "
            "ile temizleme sıvısı ve kurutma ünitesi birbirine karışıyor; "
            "güvenilir bir örneklem kuramadığımız için kapsam dışı bıraktık.",
        ],
        "segment_aciklama": (
            "Ekonomik segment temel ihtiyacı karşılayan alt fiyat bandını, orta "
            "segment yaygın tercih edilen ürünleri, üst segment ise marka ve "
            "özellik olarak daha yüksek bandı gösterir. Rakamlar tek bebek "
            "içindir ve ikinci el ya da devralınan eşyayı kapsamaz."
        ),
        "kalem_sayfalari": [
            {
                "id": "bebek-arabasi",
                "slug": "bebek-arabasi-fiyatlari",
                "baslik": "2026'da Bebek Arabası Fiyatları Ne Kadar?",
                "soru": "2026'da bebek arabası fiyatları ne kadar?",
                "aciklama": (
                    "Bebek arabası fiyatı travel sistem (oto koltuğu dahil) olup "
                    "olmamasına, katlanma mekanizmasına ve markaya göre ayrışır."
                ),
            },
        ],
    },
    "arac": {
        "ad": "0 km Araç",
        "yol": "arac",
        "kalemler": ARAC_KALEMLERI,
        "tahmini_kalemler": [],
        "baslik": "2026'da Sıfır Araba Kaça Alınır?",
        "soru": "2026'da en ucuz sıfır araba kaça alınır?",
        "sayfa_basligi": "Sıfır Araba Fiyatları 2026 | Maliyeti Ne?",
        "meta_aciklama": (
            "Sıfır araba fiyatları 2026: markaların giriş fiyatları ve marka "
            "bazlı model listeleri, kaynak ve derleme tarihiyle."
        ),
        "dataset_ad": "Maliyeti Ne? 0 km Araç Fiyat Endeksi",
        "dataset_aciklama": (
            "Türkiye'de satılan sıfır kilometre otomobillerin marka giriş "
            "fiyatları ve marka bazlı model fiyatlarından derlenen aylık endeks."
        ),
        # Bu vertikalde kalemler TOPLANMAZ (marka kalemleri bilgi_amacli),
        # "toplam" = marka giris fiyatlarinin medyani.
        "olcek_varsayilan": 1,
        "ornek_ifade": "bir markanın en ucuz sıfır aracının ortalama fiyatının",
        "anasayfa_ifade": "bir markanın en ucuz sıfır aracı ortalama",
        "kart_alt": "24 marka giriş fiyatı",
        # 2026-07-25: Yavuz'un onerisiyle hesaplayici EKLENDI. Ilk tasarimda
        # "kalemler birbirinin alternatifi, toplama hesabi anlamsiz" diye
        # atlanmisti - dogruydu ama EKSIK dusunulmustu: asil deger arac
        # fiyatinin UZERINE binen maliyetlerde (MTV, noter/tescil harci,
        # plaka, trafik sigortasi, kasko). Etiket fiyati aracin gercek
        # maliyeti degil ve bu toplami kimse tek yerde vermiyor.
        "hizli_hesap": False,
        "hesaplayici_daveti": (
            "Yola çıkarma maliyetini hesaplayın (MTV, noter, sigorta dahil) →"
        ),
        "kapsam_yer": "Türkiye",
        # Sifir aracta fiyat, ureticinin ilan ettigi TEK liste fiyatidir -
        # ayni model her bayide ayni. Bu yuzden "cok kaynak" kurali burada
        # anlamsiz: ikinci bir kaynak ayni sayiyi tekrarlar. Tek kaynak
        # uyarisi gosterilmiyor (aksi halde olmayan bir eksiklik ima eder).
        "liste_fiyati": True,
        "keywords": [
            "sıfır araba fiyatları", "sıfır otomobil fiyatları 2026",
            "en ucuz sıfır araba", "0 km araç fiyatları",
            "sıfır araç fiyat listesi", "Tesla fiyatları", "BYD fiyatları",
        ],
        "one_cikan_kalemler": ["en-ucuz-sifir-arac", "fiat", "renault", "togg", "dacia", "hyundai"],
        "segment_aciklama": (
            "Ekonomik segment markaların giriş seviyesi (en ucuz) modellerinin "
            "alt bandını, orta segment tipik giriş fiyatını, lüks segment ise "
            "premium markaların giriş modellerini gösterir. Marka bazlı "
            "kalemlerde segmentler o markanın kendi model yelpazesi içindeki "
            "dağılımı yansıtır — markalar arası kıyas için değil, marka içi "
            "aralığı görmek içindir."
        ),
        "dahil_olanlar": [
            "Markaların Türkiye'de satılan sıfır kilometre modellerinin liste fiyatları.",
            "Marka giriş fiyatı: her markanın en ucuz modelinin anahtar teslim fiyatı.",
            "Marka bazlı model listeleri (donanım/motor seçeneğine göre ayrı satırlar).",
        ],
        "dahil_olmayanlar": [
            "Trafik sigortası, kasko, MTV ve tescil masrafları.",
            "Bayi kampanyaları, kredi/taksit farkları ve opsiyonel donanım paketleri.",
            "İkinci el araç fiyatları — bu endeks yalnızca sıfır kilometre araçları kapsar.",
            "Yakıt, bakım, lastik gibi kullanım giderleri.",
        ],
        "kalem_sayfalari": [
            {
                "id": "en-ucuz-sifir-arac",
                "slug": "en-ucuz-sifir-araba",
                "baslik": "En Ucuz Sıfır Araba Fiyatları 2026",
                "soru": "2026'da en ucuz sıfır araba kaça alınır?",
                "aciklama": "Her markanın giriş seviyesi (en ucuz) modelinin fiyatı. Tüm modellerin ortalaması değil.",
            },
            {
                "id": "fiat",
                "slug": "fiat-fiyatlari",
                "baslik": "Fiat Fiyatları 2026",
                "soru": "2026'da Fiat fiyatları ne kadar?",
                "aciklama": "Fiat model fiyatları donanım ve motor seçeneğine göre değişir.",
            },
            {
                "id": "renault",
                "slug": "renault-fiyatlari",
                "baslik": "Renault Fiyatları 2026",
                "soru": "2026'da Renault fiyatları ne kadar?",
                "aciklama": "Renault model fiyatları donanım ve motor seçeneğine göre değişir.",
            },
            {
                "id": "togg",
                "slug": "togg-fiyatlari",
                "baslik": "Togg Fiyatları 2026",
                "soru": "2026'da Togg fiyatları ne kadar?",
                "aciklama": "Togg model fiyatları batarya menzili ve donanım paketine göre değişir.",
            },
            {
                "id": "dacia",
                "slug": "dacia-fiyatlari",
                "baslik": "Dacia Fiyatları 2026",
                "soru": "2026'da Dacia fiyatları ne kadar?",
                "aciklama": "Dacia model fiyatları donanım seviyesine göre değişir.",
            },
            {
                "id": "hyundai",
                "slug": "hyundai-fiyatlari",
                "baslik": "Hyundai Fiyatları 2026",
                "soru": "2026'da Hyundai fiyatları ne kadar?",
                "aciklama": "Hyundai model fiyatları motor ve donanım seçeneğine göre geniş bir aralıkta değişir.",
            },
            {
                "id": "toyota",
                "slug": "toyota-fiyatlari",
                "baslik": "Toyota Fiyatları 2026",
                "soru": "2026'da Toyota fiyatları ne kadar?",
                "aciklama": "Toyota model fiyatları hibrit/benzinli seçeneğe ve donanıma göre değişir.",
            },
            {
                "id": "volkswagen",
                "slug": "volkswagen-fiyatlari",
                "baslik": "Volkswagen Fiyatları 2026",
                "soru": "2026'da Volkswagen fiyatları ne kadar?",
                "aciklama": "Volkswagen model fiyatları motor ve donanım paketine göre değişir.",
            },
        ],
    },
}

# --- Ek kalem sayfalari -----------------------------------------------------
# Her kalem icin ayri bir landing sayfasi ("2026'da X fiyatlari ne kadar?").
# Uzun kuyruk aramalarinin tamami buradan geliyor: kimse "ev kurma maliyeti"
# aramadan once "camasir makinesi fiyatlari" ariyor.
#
# PROGRAMMATIC SEO KIRMIZI CIZGISI (bkz. CLAUDE.md): sayfalar toplu
# uretiliyor ama INCE/TEKRARLI DEGIL. Sayfanin govdesi zaten kaleme ozgu
# gercek olculmus veriden geliyor (fiyat tablosu, segment kirilimi, orneklem,
# SSS, kaynak linkleri). Asagidaki not ise ELLE yaziliyor ve her kalemde
# gercekten farkli bir bilgi veriyor - sablon cumle uretilmiyor. Yeni kalem
# eklerken bu kurala uyulmali; not yazilamiyorsa sayfa acilmaz.
KALEM_SAYFA_NOTLARI = {
    # -- dugun --
    "taki-altin": "Altın bilezik fiyatı gram altına bağlı olarak ay içinde bile değişir; bu yüzden endeksin en oynak kalemidir.",
    "salon-kokteyl": "Kokteyl düzeninde mekan bedeli menü içermez; yemek ayrı bir kalem olarak bütçeye eklenir.",
    "davetiye": "Davetiye adet fiyatı kağıt cinsi ve baskı tekniğine göre ayrışır; toplam tutar davetli sayısıyla çarpılır.",
    "gelin-ayakkabisi": "Gelin ayakkabısı fiyatı topuk yüksekliği ve malzemeden çok markaya göre ayrışır.",
    "yemek-ikram": "Mekanın yemekli ve kokteyl fiyatı arasındaki fark, o mekanda menünün kişi başı bedelini verir.",
    # -- bebek --
    "bebek-arabasi": "Bebek arabası fiyatı travel sistem (oto koltuğu dahil) olup olmamasına, çift yönlü kullanıma ve katlanma mekanizmasına göre ayrışır.",
    "mama-sandalyesi": "Mama sandalyesi fiyatı yükseklik ayarına, katlanabilirliğe ve masaya takılan/ayaklı tipine göre değişir.",
    "besik": "Beşik fiyatı sallanır/sabit oluşuna ve anne yanı (yan açılır) modeline göre değişir.",
    "park-yatak": "Park yatak fiyatı kat sayısına, oyun parkına dönüşüp dönüşmediğine göre ayrışır.",
    "oto-koltugu": "Oto koltuğu fiyatı ağırlık grubuna (0+, I, II-III) ve ISOFIX bağlantısına göre değişir; güvenlik sertifikası olmayan ürün alınmamalı.",
    "biberon-seti": "Biberon seti fiyatı parça sayısına ve cam/PP malzemesine göre ayrışır.",
    "gogus-pompasi": "Göğüs pompası fiyatı manuel, elektrikli ve giyilebilir tipler arasında büyük fark gösterir.",
    "bebek-kuveti": "Bebek küveti fiyatı katlanabilir olup olmamasına ve destek aparatına göre ayrışır.",
    "zibin-seti": "Zıbın ve body seti fiyatı parça sayısına ve pamuk kalitesine göre değişir; bedenler hızlı geçildiği için çok sayıda alınır.",
    "uyku-tulumu": "Uyku tulumu fiyatı mevsime (tog değeri) ve bedene göre ayrışır.",
    "bebek-bezi": "Bebek bezi aylık tekrarlayan bir giderdir; fiyat paket adedine ve bedene göre değişir. Tek seferlik hazırlık toplamına dahil edilmez.",
    # -- ev kurma: beyaz esya --
    "bulasik-makinesi": "Bulaşık makinesi fiyatı kişilik kapasitesi, kurutma tipi ve enerji sınıfına göre ayrışır.",
    "kurutma-makinesi": "Kurutma makinesinde ısı pompalı modeller elektrik gideri düşük olduğu için üst fiyat bandını oluşturur.",
    "firin-ocak": "Ankastre fırın ve ocak çoğu zaman set olarak alınır; tekil fiyatlar set fiyatının altında kalır.",
    "davlumbaz": "Davlumbaz fiyatı emiş gücü (m³/saat) ve bacalı/bacasız oluşuna göre değişir.",
    "mikrodalga": "Mikrodalga fırında hacim ve ızgara özelliği fiyatı belirleyen iki ana etkendir.",
    "klima": "Klima fiyatı BTU değerine göre ayrışır; montaj bedeli bu rakama dahil değildir.",
    # -- ev kurma: mobilya --
    "yemek-masasi": "Yemek masası takımı fiyatı sandalye sayısına ve masanın açılır olup olmamasına göre değişir.",
    "sehpa": "Sehpa fiyatı orta sehpa, zigon takım veya yan sehpa oluşuna göre geniş bir bantta dağılır.",
    "konsol": "Konsol fiyatı genişlik ve çekmece sayısına göre ayrışır; ayna dahil setler üst banttadır.",
    "tv-unitesi": "TV ünitesi fiyatı uzunluk ve dolaplı/duvara asılır oluşuna göre değişir.",
    # -- ev kurma: yatak odasi --
    "yatak": "Yatak fiyatı yay tipi (yaylı, visco, hibrit) ve ölçüye göre ayrışır; baza ve başlık ayrı kalemlerdir.",
    "karyola": "Karyola fiyatı baza tipine (sandıklı/sandıksız) ve başlık dahil olup olmamasına göre değişir.",
    "komodin": "Komodin genelde çift alınır; buradaki fiyat tek adet içindir.",
    "sifonyer": "Şifonyer fiyatı çekmece sayısı ve aynalı olup olmamasına göre ayrışır.",
    "boy-aynasi": "Boy aynası fiyatı çerçeve malzemesi ve ölçüsüne göre değişir.",
    # -- ev kurma: kucuk ev aleti --
    "supurge": "Robot süpürgede paspas özelliği ve otomatik boşaltma istasyonu fiyatı belirgin yükseltir.",
    "dikey-supurge": "Dikey süpürgede şarjlı modeller kablolulardan pahalı; batarya süresi fiyatın ana belirleyicisi.",
    "airfryer": "Airfryer fiyatı hazne litresi ve çift hazneli olup olmamasına göre ayrışır.",
    "kahve-makinesi": "Kahve makinesi fiyatı Türk kahvesi, filtre ve espresso tiplerine göre çok farklı bantlarda dağılır.",
    "su-isitici": "Su ısıtıcıda cam gövdeli ve sıcaklık ayarlı modeller üst fiyat bandını oluşturur.",
    "tost-makinesi": "Tost makinesinde çıkarılabilir plakalı ve ızgara özellikli modeller daha pahalıdır.",
    "blender": "Blender fiyatı el blenderı ile sürahi tipi arasında büyük fark gösterir; set halinde satılanlar üst banttadır.",
    "mutfak-robotu": "Mutfak robotu fiyatı motor gücü ve hamur yoğurma kapasitesine göre ayrışır.",
    "utu": "Ütüde buhar kazanlı modeller normal buharlı ütülerin belirgin üzerindedir.",
    "sac-kurutma-makinesi": "Saç kurutma makinesi fiyatı motor tipine (AC/DC, dijital) göre ayrışır.",
    # -- ev kurma: mutfak --
    "tencere-seti": "Tencere seti fiyatı parça sayısına ve malzemeye (granit, çelik, döküm) göre ayrışır.",
    "tava-seti": "Tava setinde yapışmaz kaplama cinsi ve indüksiyon uyumu fiyatı belirler.",
    "yemek-takimi": "Yemek takımı fiyatı kişilik sayısına ve porselen/stoneware ayrımına göre değişir.",
    "kahvalti-takimi": "Kahvaltı takımı fiyatı parça sayısına göre ayrışır; 6 ve 12 kişilik setler ayrı bantlardadır.",
    "bardak-takimi": "Bardak takımı fiyatı cam cinsine ve adet sayısına göre değişir.",
    "catal-kasik-bicak-takimi": "Çatal kaşık bıçak takımı fiyatı çelik kalitesi (18/10) ve kişilik sayısına göre ayrışır.",
    # -- okul --
    "beslenme-cantasi": "Beslenme çantası fiyatı ısı yalıtımı ve hacme göre ayrışır; suluk bölmeli modeller üst banttadır.",
    "matara": "Suluk fiyatı malzemeye (çelik, tritan, alüminyum) ve litreye göre değişir.",
    "kalem-kutusu": "Kalem kutusu fiyatı tek/çift bölmeli oluşuna ve dolu satılıp satılmadığına göre ayrışır.",
    "defter": "Defter fiyatı yaprak sayısı, kapak cinsi ve spiralli olup olmamasına göre değişir; toplu alımda birim fiyat düşer.",
    "kalem": "Kalem fiyatı kurşun, tükenmez ve jel tipleri arasında geniş bir bantta dağılır; setler tekil fiyatın altında kalır.",
    "boya-seti": "Boya seti fiyatı renk sayısına ve türüne (kuru, pastel, sulu) göre ayrışır.",
    "resim-malzemeleri": "Resim malzemeleri fiyatı defter, fırça ve tuval gibi farklı ürünleri kapsadığı için geniş dağılır.",
    "ders-kitabi": "Devlet okullarında ders kitapları ücretsiz dağıtılır; buradaki fiyat yardımcı kaynak ve test kitapları içindir.",
    "sozluk": "Sözlük fiyatı Türkçe, İngilizce ve ansiklopedik baskılar arasında değişir.",
    "ayakkabi": "Spor ayakkabı fiyatı markaya göre belirgin ayrışır; kategori çocuk bedeniyle sınırlı değildir.",
    "tablet": "Tablet fiyatı ekran boyutu, depolama ve kalem desteğine göre ayrışır.",
    "calisma-masasi": "Çalışma masası fiyatı genişlik ve raflı/çekmeceli oluşuna göre değişir.",
    "calisma-sandalyesi": "Çalışma sandalyesi fiyatı bel desteği ve ayarlanabilirlik özelliklerine göre ayrışır.",
    # -- ev kurma: tekstil --
    "nevresim-takimi": "Nevresim takımı fiyatı kumaş cinsine (ranforce, pamuk saten) ve tek/çift kişilik oluşuna göre ayrışır.",
    "havlu-takimi": "Havlu takımı fiyatı gramaj ve parça sayısına göre değişir.",
    "bornoz": "Bornoz fiyatı kumaş cinsine (havlu, pamuk) ve beden aralığına göre ayrışır.",
    "perde": "Perde fiyatı metrekare üzerinden değişir; buradaki rakam hazır perde içindir, ısmarlama dikim ayrı hesaplanır.",
    "hali": "Halı fiyatı ölçüye göre ayrışır; buradaki rakam salon ölçüsü hazır halı içindir.",
    "aydinlatma": "Aydınlatma fiyatı avize, sarkıt ve spot arasında geniş bir bantta dağılır; montaj dahil değildir.",
}

# Bir kalemin kendi sayfasini hak etmesi icin gereken asgari orneklem.
# Bunun altinda sayfa ACILMAZ - 3 urunden "X fiyatlari" sayfasi yapmak hem
# okuyucuyu yaniltir hem ince icerik olur.
KALEM_SAYFASI_ASGARI_URUN = 8

# Zaten ACIK bir sayfa, orneklem bu sayinin altina dusmedikce kapanmaz.
# NEDEN HISTEREZIS: orneklem ay ay dalgalaniyor (9 -> 7 -> 10). Tek esikle
# calisirsak ayni sayfa acilip kapaniyor; her kapanista canli bir URL
# bayatliyor ve sitemap'ten dusuyor. Acmak icin 8, kapatmak icin 5 =
# sinirdaki kalemler istikrarli kaliyor.
KALEM_SAYFASI_KAPATMA_ESIGI = 5


def _slugify_kalem(kalem_id: str) -> str:
    return f"{kalem_id}-fiyatlari"


def _ek_kalem_sayfalari(conf: dict, kalem_verisi: dict) -> list[dict]:
    """KALEM_SAYFA_NOTLARI'ndaki kalemler icin sayfa girdisi uretir.

    Elle tanimlanmis `kalem_sayfalari` girdileri onceliklidir - ayni kalem
    icin ikinci bir girdi uretilmez.
    """
    mevcut = {s["id"] for s in conf.get("kalem_sayfalari", [])}
    uretilen = []
    for kalem in conf["kalemler"]:
        kid = kalem["id"]
        if kid in mevcut or kid not in KALEM_SAYFA_NOTLARI:
            continue
        veri = kalem_verisi.get(kid) or {}
        if not veri.get("genel_medyan"):
            continue
        urun = veri.get("toplam_urun") or 0
        # Sayfa daha once acildiysa histerezis esigi gecerli (bkz. yukarisi).
        zaten_var = (SITE_KOK / conf["yol"] / _slugify_kalem(kid) / "index.html").exists()
        esik = KALEM_SAYFASI_KAPATMA_ESIGI if zaten_var else KALEM_SAYFASI_ASGARI_URUN
        if urun < esik:
            continue
        ad = kalem["ad"]
        uretilen.append({
            "id": kid,
            "slug": _slugify_kalem(kid),
            "baslik": f"2026'da {ad} Fiyatları Ne Kadar?",
            "soru": f"2026'da {ad.lower()} fiyatları ne kadar?",
            "aciklama": KALEM_SAYFA_NOTLARI[kid],
        })
    return uretilen


# Ana sayfa endeks kartinda gosterilecek en fazla kalem linki.
ANASAYFA_KART_LINK_SINIRI = 8


# Footer'daki GLOBAL endeks listesi.
# NEDEN: vertikal sayfalarinin menusu ve footer'i yalnizca KENDI
# vertikalini gosteriyordu; olculdu, 85 sayfadan diger endekslere hicbir
# link yoktu. Kullanici dugun kalem sayfasindayken ev-kurmaya ancak ana
# sayfaya donup gidebiliyordu - hem gezinme hem ic link akisi kaybi.
TUM_ENDEKS_LINKLERI = "".join(
    f'\n      <a href="/{c["yol"]}/">{c["ad"]}</a>' for c in VERTIKALLER.values()
)

SEGMENT_ANAHTARI = {"ekonomik": "dusuk", "orta": "orta", "luks": "luks"}
SEGMENT_ETIKETLERI = {"dusuk": "Ekonomik", "orta": "Orta", "luks": "Üst"}

ORNEK_SEGMENT = "orta"


def vertikal_conf(vertikal: str) -> dict:
    if vertikal not in VERTIKALLER:
        raise ValueError(
            f"Bilinmeyen vertikal: {vertikal}. Tanimlilar: {', '.join(VERTIKALLER)}"
        )
    return VERTIKALLER[vertikal]


def kalem_sayfalarini_genislet(veri_kok: Path | None = None) -> dict[str, int]:
    """VERTIKALLER'deki `kalem_sayfalari` listelerini veriden genisletir.

    Neden calisma aninda ve modul yuklenirken DEGIL: hangi kalemin kendi
    sayfasini hak ettigi o AYKI olcume bagli (bkz. KALEM_SAYFASI_ASGARI_URUN).
    Orneklem dusen bir kalem icin yeni sayfa acilmaz; zaten acilmis sayfa ise
    elle tanimli listede olmadigi surece sessizce sitemap disinda kalir.

    main() bastan cagirir, boylece sitemap ve ana sayfa da genisletilmis
    listeyi gorur. Idempotent - iki kez cagrilmasi girdiyi tekrarlamaz.
    """
    kok = veri_kok or SITE_KOK / "veri"
    eklenen: dict[str, int] = {}
    for vertikal, conf in VERTIKALLER.items():
        dosya = kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        try:
            kalem_verisi = json.loads(dosya.read_text(encoding="utf-8")).get("kalemler", {})
        except (json.JSONDecodeError, OSError):
            continue
        yeni = _ek_kalem_sayfalari(conf, kalem_verisi)
        if yeni:
            conf.setdefault("kalem_sayfalari", []).extend(yeni)
            eklenen[vertikal] = len(yeni)
    return eklenen


def _kisa_kalem_adi(ad: str) -> str:
    """Kart etiketi icin kisa kalem adi.

    "Düğün Salonu — yemekli (menü dahil)" -> "Düğün Salonu (yemekli)"
    Varyant bilgisi ATILMAZ: salon iki varyanta bolundugu icin varyanti
    dusuren kisaltma iki ayri sayfayi ayni etiketle gosteriyordu.
    """
    if "—" not in ad:
        return ad.split("(")[0].strip()
    ana, varyant = ad.split("—", 1)
    varyant = varyant.split("(")[0].strip()
    return f"{ana.strip()} ({varyant})" if varyant else ana.strip()



# Google SERP'te baslik ~60 karakterden sonra kesiliyor. Sablon uzun kalem
# adlarinda tasiyordu ("2026'da Yemek / Ikram (mekanin menu bedeli)
# Fiyatlari Ne Kadar? | Maliyeti Ne?" = 78). H1 tam kalir, yalnizca
# <title> kisalir - sayfadaki baslik bilgi kaybetmesin.
SEO_TITLE_SINIRI = 60
MARKA_SONEKI = " | Maliyeti Ne?"


def _seo_title(kalem_adi: str, yil: str = "2026") -> str:
    """60 karaktere sigan <title>. Sirayla kisaltir, son care ad + marka."""
    kisa = _kisa_kalem_adi(kalem_adi)
    adaylar = [
        f"{yil}'da {kisa} Fiyatları Ne Kadar?",
        f"{kisa} Fiyatları {yil}",
        f"{kisa} Fiyatları",
        kisa,
    ]
    for a in adaylar:
        if len(a) + len(MARKA_SONEKI) <= SEO_TITLE_SINIRI:
            return a + MARKA_SONEKI
    return adaylar[-1] + MARKA_SONEKI



def _breadcrumb_html(conf: dict, kalem_adi: str) -> str:
    """Gorunur kirinti navigasyonu.

    BreadcrumbList schema zaten vardi ama HTML'de karsiligi YOKTU. Google
    yalnizca yapilandirilmis veriye guvenmiyor; SERP'te kirinti gostermesi
    icin sayfada da gorunur olmasi isine yariyor. Ayrica derin sayfadan
    ust kategoriye tek tikla donus - kullanici icin de faydali.
    """
    return (
        '  <nav class="kirinti" aria-label="Sayfa yolu">\n'
        '    <a href="/">Ana sayfa</a> <span aria-hidden="true">›</span> '
        f'<a href="/{conf["yol"]}/">{conf["ad"]}</a> '
        f'<span aria-hidden="true">›</span> <span>{kalem_adi}</span>\n'
        "  </nav>\n"
    )



# --- Fiyat grafigi (SVG) -----------------------------------------------
# NEDEN: sitede HIC gorsel yoktu - <img> etiketi bile. Uc kazanc:
# (1) sayfa kalite sinyali, (2) paylasildiginda goze carpma,
# (3) fiyat dagiliminin tabloya gore anlik okunmasi.
# HARICI DOSYA YOK: SVG sayfaya gomulu, ek istek acmiyor ve veriyle
# birlikte kendiliginden guncelleniyor. Renkler CSS degiskenlerinden
# geliyor, karanlik modda da dogru gorunuyor.
GRAFIK_GENISLIK = 620
GRAFIK_YUKSEKLIK = 190


def _segment_grafigi(degerler: dict, birim_notu: str = "") -> str:
    """Ekonomik/orta/ust segment karsilastirma cubuk grafigi.

    Veri eksikse (segmentlerden biri yoksa) BOS doner - yarim grafik
    cizmek yaniltici olur.
    """
    sira = [("dusuk", "Ekonomik"), ("orta", "Orta"), ("luks", "Üst")]
    veri = [(ad, degerler.get(k)) for k, ad in sira]
    if not all(d for _, d in veri):
        return ""
    en_buyuk = max(d for _, d in veri)
    if not en_buyuk:
        return ""

    sol, ust, cubuk_y, aralik = 88, 22, 30, 52
    cubuk_alan = GRAFIK_GENISLIK - sol - 96
    parcalar = []
    for i, (ad, deger) in enumerate(veri):
        y = ust + i * aralik
        genislik = max(3, round(cubuk_alan * deger / en_buyuk))
        parcalar.append(
            f'<text x="{sol - 10}" y="{y + 19}" text-anchor="end" class="g-etiket">{ad}</text>'
            f'<rect x="{sol}" y="{y}" width="{genislik}" height="{cubuk_y}" rx="4" class="g-cubuk g-{i}"/>'
            f'<text x="{sol + genislik + 10}" y="{y + 19}" class="g-deger">{_para(deger)}</text>'
        )
    kat = veri[2][1] / veri[0][1] if veri[0][1] else 0
    alt = (f'<text x="{sol}" y="{ust + 3 * aralik + 6}" class="g-alt">'
           f'Üst segment, ekonomiğin {kat:.1f} katı{birim_notu}</text>') if kat else ""
    return (
        f'  <figure class="fiyat-grafik">\n'
        f'    <svg viewBox="0 0 {GRAFIK_GENISLIK} {GRAFIK_YUKSEKLIK}" '
        f'role="img" aria-label="Segmentlere göre fiyat karşılaştırması: '
        + ", ".join(f"{ad} {_para(d)}" for ad, d in veri) + '">\n'
        f'      {"".join(parcalar)}{alt}\n'
        f'    </svg>\n'
        f'  </figure>\n'
    )



def _hizli_hesap_katsayilari(veri_kok: Path | None = None) -> dict:
    """Ana sayfa hesaplayicisi icin vertikal/segment katsayilari.

    NEDEN KATSAYI: ana sayfaya dort vertikalin kalem listesini birden
    yuklemek (4 ayri JS dosyasi + 4 JSON fetch) agir olurdu. Toplam her
    olcekte LINEER oldugu icin iki noktadan (olcek=1 ve 2) sabit ve
    kisi-basi bilesenleri cikariliyor: toplam = sabit + kisi_basi * olcek.
    50/80/100/150/200/300 olceklerinde gercek hesapla BIREBIR ayni sonucu
    verdigi dogrulandi (testle kilitli) - yani ana sayfadaki rakam endeks
    sayfasindakiyle ayni.

    Arac disarida: orada "segment" marka giris fiyatlarinin persentili,
    gercek bir "ekonomik arac" degil - segment secimiyle sunmak yaniltici.
    """
    kok = veri_kok or SITE_KOK / "veri"
    cikti = {}
    for vertikal, conf in VERTIKALLER.items():
        if not conf.get("hesaplayici_var", True) or not conf.get("hizli_hesap", True):
            continue
        dosya = kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        try:
            kalemler = json.loads(dosya.read_text(encoding="utf-8")).get("kalemler") or {}
        except (json.JSONDecodeError, OSError):
            continue
        segmentler = {}
        for seg in ("ekonomik", "orta", "luks"):
            t1, _ = ornek_toplam_hesapla(conf, kalemler, olcek=1, segment=seg)
            t2, _ = ornek_toplam_hesapla(conf, kalemler, olcek=2, segment=seg)
            if not t1:
                continue
            kisi = t2 - t1
            segmentler[seg] = {"sabit": t1 - kisi, "kisi_basi": kisi}
        if len(segmentler) == 3:
            cikti[vertikal] = {
                "ad": conf["ad"],
                "yol": conf["yol"],
                "olcek_var": any(k.get("birim") == "kisi_basi" for k in conf["kalemler"]),
                "segmentler": segmentler,
            }
    return cikti


HIZLI_HESAP_JS_GOVDE = """
(function () {
  var VERI = __VERI__;
  var bicim = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
  var secim = document.getElementById("hh-vertikal");
  var olcekSatir = document.getElementById("hh-olcek-satir");
  var olcek = document.getElementById("hh-olcek");
  var sonuc = document.getElementById("hh-sonuc");
  var alt = document.getElementById("hh-alt");
  if (!secim || !sonuc) return;
  function segment() {
    var s = document.querySelector('input[name="hh-seg"]:checked');
    return s ? s.value : "orta";
  }
  function hesapla() {
    var v = VERI[secim.value];
    if (!v) return;
    var seg = v.segmentler[segment()];
    olcekSatir.hidden = !v.olcek_var;
    var n = v.olcek_var ? Math.max(0, parseInt(olcek.value, 10) || 0) : 1;
    var toplam = seg.sabit + seg.kisi_basi * n;
    sonuc.textContent = bicim.format(Math.round(toplam)) + " TL";
    alt.innerHTML = (v.olcek_var ? n + " kişilik · " : "") +
      "ölçülen güncel fiyatlarla · " +
      '<a href="/' + v.yol + '/hesaplayici/">kalem kalem hesaplayın →</a>';
  }
  secim.addEventListener("change", hesapla);
  olcek.addEventListener("input", hesapla);
  document.getElementById("hh-segment").addEventListener("change", hesapla);
  hesapla();
})();
"""


def _hizli_hesap_js(hizli: dict) -> str:
    """JS f-string DISINDA uretiliyor: JS'in susli parantezleri ana sayfa
    sablonunun f-string'iyle catisiyor."""
    govde = HIZLI_HESAP_JS_GOVDE.replace("__VERI__", json.dumps(hizli, ensure_ascii=False))
    return "<script>" + govde + "</script>\n"



def _arama_verisi(veri_kok: Path | None = None) -> list[dict]:
    """Site ici arama icin kalem dizini.

    NEDEN ARAMA, NEDEN CHAT DEGIL: kullanicinin gercek ihtiyaci "bana
    buzdolabi bul" - yani dogru sayfaya ulasmak. Bunu bir sohbet botuyla
    yapmak ISE YARAMAZ, hatta zararli: bot rakam uydurursa ("buzdolabi
    25.000") sitenin tum degeri olan "fiyat uydurmuyoruz" iddiasi coker.
    Arama ise YALNIZCA olctugumuz kalemleri doner; uydurabilecegi bir sey
    yok, her sonuc gercek bir sayfaya gidiyor.
    """
    kok = veri_kok or SITE_KOK / "veri"
    kayitlar = []
    for vertikal, conf in VERTIKALLER.items():
        dosya = kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        try:
            kalemler = json.loads(dosya.read_text(encoding="utf-8")).get("kalemler") or {}
        except (json.JSONDecodeError, OSError):
            continue
        sayfalar = {s["id"]: s["slug"] for s in conf.get("kalem_sayfalari", [])}
        for t in conf["kalemler"]:
            veri = kalemler.get(t["id"])
            if not veri or not veri.get("genel_medyan"):
                continue
            slug = sayfalar.get(t["id"])
            kayitlar.append({
                "ad": _kisa_kalem_adi(t["ad"]),
                "grup": t.get("grup") or conf["ad"],
                "fiyat": kalem_deger(veri, "orta") or veri["genel_medyan"],
                # Kalem sayfasi yoksa endekse gonder - kirik link olmasin.
                "yol": f"/{conf['yol']}/{slug}/" if slug else f"/{conf['yol']}/",
                "endeks": conf["ad"],
            })
    return sorted(kayitlar, key=lambda x: x["ad"])


ARAMA_JS_GOVDE = """
(function () {
  var VERI = __VERI__;
  var kutu = document.getElementById("kalem-ara");
  var liste = document.getElementById("arama-sonuc");
  if (!kutu || !liste) return;
  var bicim = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
  function sadelestir(s) {
    return s.toLocaleLowerCase("tr")
      .replace(/ı/g, "i").replace(/ş/g, "s").replace(/ğ/g, "g")
      .replace(/ü/g, "u").replace(/ö/g, "o").replace(/ç/g, "c");
  }
  var dizin = VERI.map(function (k) {
    return { k: k, a: sadelestir(k.ad + " " + k.grup + " " + k.endeks) };
  });
  function ara() {
    var q = sadelestir(kutu.value.trim());
    if (q.length < 2) { liste.innerHTML = ""; liste.hidden = true; return; }
    var bulunan = dizin.filter(function (x) { return x.a.indexOf(q) !== -1; }).slice(0, 8);
    if (!bulunan.length) {
      liste.innerHTML = '<li class="arama-bos">Bu isimde ölçtüğümüz bir kalem yok.' +
        ' <a href="/veri/">Tüm kalemlere bakın</a></li>';
      liste.hidden = false; return;
    }
    liste.innerHTML = bulunan.map(function (x) {
      return '<li><a href="' + x.k.yol + '"><span>' + x.k.ad + '</span>' +
        '<span class="arama-fiyat">' + bicim.format(x.k.fiyat) + ' TL</span></a>' +
        '<span class="arama-grup">' + x.k.endeks + '</span></li>';
    }).join("");
    liste.hidden = false;
  }
  kutu.addEventListener("input", ara);
  kutu.addEventListener("focus", ara);
})();
"""


def _arama_js(kayitlar: list[dict]) -> str:
    return "<script>" + ARAMA_JS_GOVDE.replace(
        "__VERI__", json.dumps(kayitlar, ensure_ascii=False)
    ) + "</script>\n"


def _para(n: int) -> str:
    return f"{n:,.0f}".replace(",", ".") + " TL"


def bagimsiz_siteler(kalemler: dict, kalem_idleri: set[str]) -> set[str]:
    """Kac AYRI ve o ay veri donduren SITE'den fiyat geldigini doner.

    kalem basina "kaynak_sayisi"nin toplami DEGIL: ayni site (or. Trendyol)
    20 kalemi de beslediginde bu toplam 20 cikar ve okuyucuya 20 farkli
    kaynak izlenimi verir. COK KAYNAK KURALI'nin olctugu sey site
    cesitliligi, o yuzden benzersiz site sayilir. 0 urun donduren aday
    kaynaklar ise "calisan kaynak" gibi gosterilmez.
    """
    siteler = set()
    for kalem_id in kalem_idleri:
        for kaynak in kalemler.get(kalem_id, {}).get("kaynaklar", []):
            if kaynak.get("toplam_urun") == 0:
                continue
            if "genel_medyan" in kaynak and kaynak.get("genel_medyan") is None:
                continue
            siteler.add(kaynak["site"])
    return siteler


def kalem_deger(kalem_verisi: dict | None, segment_anahtari: str) -> int | None:
    if not kalem_verisi:
        return None
    seg = kalem_verisi.get("segmentler", {}).get(segment_anahtari)
    if seg:
        return seg["medyan"]
    return kalem_verisi.get("genel_medyan")


def ornek_toplam_hesapla(conf: dict, kalemler: dict, olcek: int, segment: str) -> tuple[int, list[dict]]:
    seg_anahtari = SEGMENT_ANAHTARI[segment]
    toplam = 0
    detaylar = []
    for tanim in conf["kalemler"]:
        veri = kalemler.get(tanim["id"])
        deger = kalem_deger(veri, seg_anahtari)
        if deger is None:
            detaylar.append({**tanim, "veri_var": False, "tahmini_mi": False})
            continue
        carpan = olcek if tanim["birim"] == "kisi_basi" else 1
        satir_toplam = round(deger * carpan)
        # bilgi_amacli kalemler HICBIR senaryoda toplanmaz (bkz. yemek-ikram).
        dahil = tanim.get("varsayilan_dahil", True) and not tanim.get("bilgi_amacli")
        if dahil:
            toplam += satir_toplam
        detaylar.append({
            **tanim, "veri_var": True, "tahmini_mi": False,
            "birim_fiyat": deger, "satir_toplam": satir_toplam,
            "toplama_dahil": dahil,
        })

    for tanim in conf["tahmini_kalemler"]:
        deger = tanim["tahmini"][seg_anahtari]
        carpan = olcek if tanim["birim"] == "kisi_basi" else 1
        satir_toplam = round(deger * carpan)
        dahil = tanim.get("varsayilan_dahil", True)
        if dahil:
            toplam += satir_toplam
        detaylar.append({
            "id": tanim["id"], "ad": tanim["ad"], "birim": tanim["birim"],
            "veri_var": True, "tahmini_mi": True,
            "birim_fiyat": deger, "satir_toplam": satir_toplam,
            "toplama_dahil": dahil,
            "kaynak_notu": tanim["kaynak_notu"], "arastirma_tarihi": tanim["arastirma_tarihi"],
        })
    return toplam, detaylar


def _kalem_satirlari_html(conf: dict, kalemler: dict) -> str:
    satirlar = []
    onceki_grup = None
    for tanim in conf["kalemler"]:
        grup = tanim.get("grup")
        if grup and grup != onceki_grup:
            satirlar.append(f'<tr class="grup-satiri"><td colspan="5">{grup}</td></tr>')
            onceki_grup = grup
        veri = kalemler.get(tanim["id"])
        if not veri:
            satirlar.append(
                f'<tr><td>{tanim["ad"]}</td>'
                '<td class="sayi">—</td><td class="sayi">—</td><td class="sayi">—</td>'
                '<td class="sayi">Veri yok</td></tr>'
            )
            continue
        degerler = segment_degerleri(veri)
        # Toplama girmeyen satir (salon'un secilmeyen varyanti) fiyat
        # referansi olarak gosterilir ama toplamda olmadigi belirtilir -
        # aksi halde tablodaki satirlari toplayan okuyucu farkli bir
        # sonuca ulasir ve bu guveni zedeler.
        if tanim.get("bilgi_amacli"):
            not_etiketi = ' <span class="tahmini-etiket">Bilgi amaçlı — toplamda değil</span>'
        elif not tanim.get("varsayilan_dahil", True):
            not_etiketi = ' <span class="tahmini-etiket">Toplamda değil</span>'
        elif tanim.get("tek_deger"):
            # Kaynak tek bir Istanbul rakami veriyor, uc fiyat bandi degil.
            # Uc sutunda ayni sayiyi gorup "segment farki yok mu?" diye
            # soran okuyucuya cevabi satirin kendisi versin.
            not_etiketi = ' <span class="tahmini-etiket">Tek ölçüm — segment kırılımı yok</span>'
        else:
            not_etiketi = ""
        satirlar.append(
            f'<tr><td>{tanim["ad"]}{not_etiketi}</td>'
            f'<td class="sayi">{_para(degerler["dusuk"]) if degerler["dusuk"] else "—"}</td>'
            f'<td class="sayi">{_para(degerler["orta"]) if degerler["orta"] else "—"}</td>'
            f'<td class="sayi">{_para(degerler["luks"]) if degerler["luks"] else "—"}</td>'
            f'<td class="sayi">{veri.get("kaynak_sayisi", 0)}</td></tr>'
        )
    for tanim in conf["tahmini_kalemler"]:
        t = tanim["tahmini"]
        not_etiketi = (
            "" if tanim.get("varsayilan_dahil", True)
            else ' <span class="tahmini-etiket">Toplamda değil</span>'
        )
        satirlar.append(
            f'<tr><td>{tanim["ad"]} <span class="tahmini-etiket" title="{tanim["kaynak_notu"]}">Tahmini</span>{not_etiketi}</td>'
            f'<td class="sayi">{_para(t["dusuk"])}</td>'
            f'<td class="sayi">{_para(t["orta"])}</td>'
            f'<td class="sayi">{_para(t["luks"])}</td>'
            f'<td class="sayi">Tahmini</td></tr>'
        )
    return "\n".join(satirlar)


def segment_degerleri(kalem_verisi: dict | None) -> dict[str, int | None]:
    """Segment tablolari icin yalnizca gercek segment medyanlarini doner.

    kalem_deger() toplam/cevap hesaplarinda genel medyana kontrollu fallback
    yapar. Tablo ve SEO metninde ise eksik segmenti "luks" ya da "ekonomik"
    gibi gostermek yaniltici olur; bu yuzden burada fallback YOK.
    """
    # SEGMENT TUTARSIZSA hicbiri gosterilmez: agrega.py, segmentler
    # kaynaklar arasinda bagimsiz hesaplandigi icin siralanmanin
    # bozulabildigi kalemleri isaretliyor ("orta segment, ustten pahali").
    # Boyle bir tabloyu yayinlamak okuyucuyu yaniltir - yalnizca genel
    # ortalama gosterilir ve nedeni yazilir.
    if (kalem_verisi or {}).get("segment_tutarsiz"):
        return {"dusuk": None, "orta": None, "luks": None}
    segmentler = (kalem_verisi or {}).get("segmentler") or {}
    return {
        seg: (segmentler.get(seg) or {}).get("medyan")
        for seg in ("dusuk", "orta", "luks")
    }



def _segment_tutarsiz_notu(kalem_verisi: dict | None) -> str:
    """Segment kirilimi gizlendiginde NEDENINI yazar.

    Tabloyu sessizce gizlemek "veri eksik" izlenimi verir; asil sebep
    olcum yonteminin siniri ve bunu soylemek guveni artiriyor.
    """
    if not (kalem_verisi or {}).get("segment_tutarsiz"):
        return ""
    return (
        '    <div class="uyari-kutu">\n'
        "      <strong>Bu kalemde segment kırılımı gösterilmiyor.</strong> "
        "Kaynaklardan birinin örneklemi küçük olduğu için üst segment yalnızca "
        "tek kaynaktan hesaplanıyor ve sıralama tutarsız çıkıyor (orta segment, "
        "üst segmentten pahalı görünüyor). Yanlış bir tablo göstermektense "
        "yalnızca genel ortalamayı veriyoruz; örneklem büyüdüğünde kırılım "
        "kendiliğinden geri gelecek.\n"
        "    </div>\n"
    )


def _liste_html(maddeler: list[str]) -> str:
    return "<ul>" + "\n".join(f"<li>{madde}</li>" for madde in maddeler) + "</ul>"


def _en_pahali_kalemler_html(detaylar: list[dict], adet: int = 5) -> str:
    adaylar = [
        d for d in detaylar
        if d.get("veri_var") and d.get("toplama_dahil", True)
    ]
    adaylar = sorted(adaylar, key=lambda d: d["satir_toplam"], reverse=True)[:adet]
    if not adaylar:
        return ""
    satirlar = []
    for d in adaylar:
        etiket = ' <span class="tahmini-etiket">Tahmini</span>' if d.get("tahmini_mi") else ""
        satirlar.append(
            f"<li><strong>{d['ad']}:</strong> {_para(d['satir_toplam'])}{etiket}</li>"
        )
    return "<ol>" + "\n".join(satirlar) + "</ol>"


def _kalem_sayfa_haritasi(conf: dict) -> dict[str, dict]:
    return {s["id"]: s for s in conf.get("kalem_sayfalari", [])}


def _kalem_sayfa_linkleri_html(conf: dict, kalemler: dict) -> str:
    linkler = []
    for sayfa in conf.get("kalem_sayfalari", []):
        veri = kalemler.get(sayfa["id"])
        if not kalem_deger(veri, SEGMENT_ANAHTARI[ORNEK_SEGMENT]):
            continue
        linkler.append(
            f'<li><a href="/{conf["yol"]}/{sayfa["slug"]}/">{sayfa["baslik"].replace(" Ne Kadar?", "")}</a></li>'
        )
    if not linkler:
        return ""
    return "<ul>" + "\n".join(linkler) + "</ul>"


def _icerik_seo_bloklari_html(conf: dict, kalemler: dict, detaylar: list[dict]) -> str:
    dahil = _liste_html(conf.get("dahil_olanlar", []))
    haric = _liste_html(conf.get("dahil_olmayanlar", []))
    en_pahali = _en_pahali_kalemler_html(detaylar)
    kalem_linkleri = _kalem_sayfa_linkleri_html(conf, kalemler)
    if kalem_linkleri:
        kalem_linkleri = (
            '<section class="icerik-bolumu">\n'
            "  <h2>İlgili fiyat sayfaları</h2>\n"
            f"  {kalem_linkleri}\n"
            "</section>"
        )
    kalem_linkleri = _senaryo_linkleri_html(conf) + kalem_linkleri
    return f"""
  <section class="icerik-bolumu">
    <h2>Bu rakama neler dahil?</h2>
    <p>Bu endeks, kullanıcının bütçe çıkarırken tek tek görmek isteyeceği ana kalemleri kapsar.</p>
    {dahil}
  </section>

  <section class="icerik-bolumu">
    <h2>Bu rakama neler dahil değil?</h2>
    <p>Aşağıdaki kalemler kapsam dışında tutulur; çünkü ölçüm yöntemi ya ayrı bir vertikal gerektirir ya da kişiye göre çok değişir.</p>
    {haric}
  </section>

  <section class="icerik-bolumu">
    <h2>En yüksek maliyet kalemleri</h2>
    <p>Orta segment varsayılan senaryoda bütçeyi en çok etkileyen kalemler şunlardır:</p>
    {en_pahali}
  </section>

  <section class="icerik-bolumu">
    <h2>Segmentler nasıl okunmalı?</h2>
    <p>{conf["segment_aciklama"]}</p>
  </section>

  {kalem_linkleri}
"""


def _capraz_dogrulama_uyarilari_html(conf: dict, kalemler: dict) -> str:
    uyarilar = []
    ad_haritasi = {t["id"]: t["ad"] for t in conf["kalemler"]}
    yol = conf["yol"]
    for kalem_id, veri in kalemler.items():
        uyari = veri.get("capraz_dogrulama_uyarisi")
        if uyari:
            ad = ad_haritasi.get(kalem_id, kalem_id)
            uyarilar.append(
                f"<li><strong>{ad}:</strong> kaynaklar arası fark %{uyari['fark_yuzdesi']:.0f} "
                "— farklı segment/marka aralığını yansıtıyor olabilir, "
                f'<a href="/{yol}/metodoloji/">metodolojiye bakın</a>.</li>'
            )
    if not uyarilar:
        return ""
    return (
        '<div class="uyari-kutu"><strong>Çapraz doğrulama notu:</strong>'
        "<ul>" + "\n".join(uyarilar) + "</ul></div>"
    )


SITE_KOK_URL = "https://maliyetine.com.tr"


def ek_sorular_uret(conf: dict, kalemler: dict, olcek: int) -> list[dict]:
    """Veriden GERCEK sayilarla ek soru/cevap ciftleri uretir (GEO icin).

    Neden: FAQPage'de tek soru olmasi kapsami daraltiyor. "X fiyatlari ne
    kadar?" tipi sorgular AI motorlarinda ve aramada ayri ayri soruluyor.
    Cevaplar UYDURULMAZ - yalnizca verisi olan kalemler icin uretilir,
    segment kirilimi gercek medyanlardan gelir.
    """
    sorular = []
    ad_haritasi = {t["id"]: t for t in conf["kalemler"]}
    for kalem_id in conf.get("one_cikan_kalemler", []):
        tanim = ad_haritasi.get(kalem_id)
        veri = kalemler.get(kalem_id)
        if not (tanim and veri):
            continue
        segmentler = veri.get("segmentler") or {}
        degerler = {
            s: (segmentler.get(s) or {}).get("medyan")
            for s in ("dusuk", "orta", "luks")
        }
        if degerler["orta"] is None:
            continue
        birim = " (kişi başı)" if tanim["birim"] == "kisi_basi" else ""
        parcalar = [
            f"{SEGMENT_ETIKETLERI[s].lower()} segmentte {_para(degerler[s])}"
            for s in ("dusuk", "orta", "luks") if degerler[s] is not None
        ]
        kaynak_sayisi = (
            len(bagimsiz_siteler({kalem_id: veri}, {kalem_id}))
            or veri.get("kaynak_sayisi", 0)
        )
        urun_sayisi = veri.get("toplam_urun")
        dayanak = f"{kaynak_sayisi} bağımsız kaynaktan"
        if urun_sayisi:
            dayanak += f", {urun_sayisi} ürün üzerinden"
        sorular.append({
            "@type": "Question",
            "name": f"{tanim['ad']} fiyatları 2026'da ne kadar?{birim}".strip(),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": (
                    f"Maliyeti Ne? verilerine göre {tanim['ad']}{birim} "
                    + ", ".join(parcalar)
                    + f". Bu rakamlar {dayanak} derlendi "
                      f"(derleme tarihi: {veri.get('guncelleme_tarihi', '—')})."
                ),
            },
        })
    return sorular


def _grup_toplamlari(conf: dict, kalemler: dict, segment_anahtari: str) -> list[dict]:
    """Gruplu vertikallerde (ev-kurma) grup basina toplam soru/cevabi."""
    gruplar: dict[str, int] = {}
    for tanim in conf["kalemler"]:
        grup = tanim.get("grup")
        deger = kalem_deger(kalemler.get(tanim["id"]), segment_anahtari)
        if grup and deger:
            gruplar[grup] = gruplar.get(grup, 0) + round(deger)
    return [
        {
            "@type": "Question",
            "name": f"{grup} için ne kadar bütçe gerekir?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": (
                    f"Orta segmentte {grup.lower()} kalemlerinin toplamı "
                    f"{_para(tutar)}. Kalem kalem döküm maliyetine.com.tr"
                    f"/{conf['yol']}/ adresinde."
                ),
            },
        }
        for grup, tutar in gruplar.items()
    ]


# Kaynak sitelerin gorunur adi ve urun sayfasi linki. Kalem sayfalarinda
# "Nereden alabilirsiniz" bolumu bunlari kullanir.
#
# GELIR MODELI NOTU: su an duz link. Affiliate programlarina (Trendyol
# Ortaklik, vb.) kabul alindiginda takip parametresi YALNIZCA buraya
# eklenecek - sayfa sablonlarina dokunmaya gerek kalmayacak. rel=
# degeri de o zaman "sponsored" olmali (Google zorunlu tutuyor).
# Kalem sayfasindaki "Nereden bakabilirsiniz" linkleri.
#
# AFFILIATE HAZIRLIGI: bir siteyle ortaklik anlasmasi yapildiginda
# yalnizca buraya `takip` parametresi eklenir; sablonlara dokunulmaz.
# `takip` dolu olan link otomatik olarak rel="sponsored" aliyor (Google'in
# ucretli/komisyonlu baglanti icin zorunlu tuttugu isaret) ve sayfada
# gorunur bir aciklama cikiyor.
#
# NEDEN BOYLE: bu sitenin tum degeri bagimsiz olcum iddiasinda. Komisyonlu
# link koyup bunu SOYLEMEMEK hem yasal sorun (reklam aciklama
# yukumlulugu) hem de guven kaybi. Fiyat siralamasi ve olcum komisyondan
# ETKILENMIYOR - link yalnizca "nereden bakabilirsiniz" bilgisi; sirayi
# komisyon degil kaynak sayisi belirliyor.
KAYNAK_SITELERI = {
    "trendyol": {"ad": "Trendyol", "rel": "nofollow"},
    "amazon": {"ad": "Amazon", "rel": "nofollow"},
    "madamecoco": {"ad": "Madame Coco", "rel": "nofollow"},
    "dugun-com": {"ad": "Düğün.com", "rel": "nofollow"},
    "karaca": {"ad": "Karaca", "rel": "nofollow"},
    "englishhome": {"ad": "English Home", "rel": "nofollow"},
    "atasay": {"ad": "Atasay", "rel": "nofollow"},
    "beymen": {"ad": "Beymen", "rel": "nofollow"},
    "vakko": {"ad": "Vakko", "rel": "nofollow"},
    "boyner": {"ad": "Boyner", "rel": "nofollow"},
    "ramsey": {"ad": "Ramsey", "rel": "nofollow"},
    "cimri": {"ad": "Cimri", "rel": "nofollow"},
    "dugunbuketi": {"ad": "DüğünBuketi", "rel": "nofollow"},
    "donanimhaber": {"ad": "DonanımHaber", "rel": "nofollow"},
}


def _kaynak_linkleri_yukle():
    """kaynaklar.yaml'dan (vertikal, kalem) -> [(site, url)] haritasi.

    Kalem sayfasinda "bu urunleri nerede bulursunuz" linki vermek icin.
    Kullaniciyi bos birakmak hem kotu deneyim hem de gelir modelini
    (affiliate) bastan imkansiz kiliyordu.
    """
    try:
        import yaml
        veri = yaml.safe_load((BASE_DIR / "kaynaklar.yaml").read_text(encoding="utf-8"))
    except Exception:
        return {}
    harita = {}
    for k in veri.get("kaynaklar", []):
        if not k.get("aktif", True):
            continue
        anahtar = (k.get("vertikal"), k.get("kalem"))
        harita.setdefault(anahtar, [])
        site = k.get("site")
        if not any(s == site for s, _ in harita[anahtar]):
            harita[anahtar].append((site, k.get("url")))
    return harita


_KAYNAK_LINKLERI = None


def kalem_kaynak_linkleri(vertikal: str, kalem_id: str):
    global _KAYNAK_LINKLERI
    if _KAYNAK_LINKLERI is None:
        _KAYNAK_LINKLERI = _kaynak_linkleri_yukle()
    return _KAYNAK_LINKLERI.get((vertikal, kalem_id), [])


def _nereden_alinir_html(vertikal: str, kalem_id: str, kalem_adi: str) -> str:
    linkler = kalem_kaynak_linkleri(vertikal, kalem_id)
    if not linkler:
        return ""
    parcalar = []
    for site, url in linkler:
        bilgi = KAYNAK_SITELERI.get(site, {"ad": site.capitalize(), "rel": "nofollow"})
        takip = bilgi.get("takip")
        if takip:
            url = url + ("&" if "?" in url else "?") + takip
        rel = "sponsored" if takip else bilgi["rel"]
        parcalar.append(
            f'<a href="{url}" rel="{rel} noopener" target="_blank">'
            f'{bilgi["ad"]}</a>'
        )
    # Komisyonlu link varsa ACIKCA soylenir: hem yasal aciklama
    # yukumlulugu hem guven. Sirayi komisyon degil kaynak sayisi
    # belirliyor ve olcum bundan etkilenmiyor - bunu da yaziyoruz.
    sponsor_notu = ""
    if any(KAYNAK_SITELERI.get(site, {}).get("takip") for site, _ in linkler):
        sponsor_notu = (
            '    <p class="sonuc-alt-metin"><strong>Açıklama:</strong> bu '
            "bağlantıların bazıları ortaklık (affiliate) bağlantısıdır; "
            "üzerinden alışveriş yapılırsa siteye komisyon kalabilir. "
            "Ölçtüğümüz fiyatlar ve kaynak sıralaması bundan etkilenmez — "
            "hangi sitenin listeleneceğini komisyon değil, o kalemi "
            "gerçekten ölçebildiğimiz kaynaklar belirler.</p>\n"
        )
    return (
        '  <section class="icerik-bolumu">\n'
        "    <h2>Nereden bakabilirsiniz?</h2>\n"
        f"    <p>{kalem_adi} fiyatlarını derlediğimiz kaynaklar: "
        + " · ".join(parcalar)
        + "</p>\n"
        + sponsor_notu
        + '    <p class="sonuc-alt-metin">Bu bağlantılar fiyatı derlediğimiz '
        "kategori sayfalarına gider. Fiyatlar sayfamızdaki derleme tarihinden "
        "sonra değişmiş olabilir.</p>\n"
        "  </section>\n"
    )


def _kunye_html(conf: dict, kalem_verisi: dict | None, tarih: str) -> str:
    """Sayfa altinda TEK SATIR kunye.

    Onceden burada "Kaynaklar ve yontem" diye ayri bir bolum vardi ve
    hangi siteden kac urun cekildigini tek tek listeliyordu. Yavuz'un
    tespiti: kullanici araba/urun fiyati ogrenmeye geliyor, bizim is
    yapma seklimizi okumaya degil. Seffaflik icin gereken bilgi (kac
    urun, ne zaman, yontem linki) tek satira sigar.
    """
    v = kalem_verisi or {}
    urun = v.get("toplam_urun")
    parca = []
    if urun:
        parca.append(f"{urun} üründen derlendi")
    parca.append(tarih)
    return (
        '  <p class="kunye">' + " · ".join(parca)
        + f' · <a href="/{conf["yol"]}/metodoloji/">Yöntem</a></p>\n'
    )


def _fiyat_gecmisi_html(vertikal: str, kalem_id: str, gecmis_kok: Path | None = None) -> str:
    """Kalem sayfasinda fiyat gecmisi bolumu.

    Veri kaynagi: /veri/gecmis/{vertikal}.json (gecmis.py uretir).
    Yeterince uzak iki olcum yoksa (bkz. gecmis.ASGARI_GUN_ARALIGI) bolum
    HIC RENDER EDILMEZ - bos bir "gecmis" basligi gostermek, veri varmis
    izlenimi verir. 5 Agustos'taki ikinci olcumde kendiliginden acilir.

    NEDEN DEGERLI: zaman serisi bu projenin kopyalanamaz varligi. "Gelinlik
    fiyatlari son X ayda %Y artti" cumlesini kurabilen tek kaynak olmak hem
    dogal baglanti hem AI alintisi getiriyor.
    """
    kok = gecmis_kok or SITE_KOK / "veri" / "gecmis"
    dosya = kok / f"{vertikal}.json"
    if not dosya.exists():
        return ""
    try:
        veri = json.loads(dosya.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""
    kayit = (veri.get("kalemler") or {}).get(kalem_id) or {}
    seri = kayit.get("seri") or []
    degisim = kayit.get("degisim_yuzde")
    if degisim is None or len(seri) < 2:
        # Kendi serimiz henuz yok (ilk karsilastirma 5 Agustos'ta).
        # Bolumu bos birakmak yerine RESMI seriyi gosteriyoruz - okuyucu
        # "bu kalem ne kadar zamlandi" sorusuna bugun de cevap alsin.
        # KIRMIZI CIZGI: bu bizim olcumumuz DEGIL, ayri ve kaynak adiyla.
        return _resmi_gecmis_html(vertikal)

    yon = "arttı" if degisim > 0 else ("azaldı" if degisim < 0 else "değişmedi")
    ilk, son = seri[0], seri[-1]
    satirlar = "".join(
        f'<tr><td>{n["tarih"]}</td><td class="sayi">{_para(n["medyan"])}</td>'
        f'<td class="sayi">{n["urun"]}</td></tr>'
        for n in seri
    )
    ozet = (
        f'{ilk["tarih"]} tarihinden {son["tarih"]} tarihine kadar ortalama fiyat '
        f'{_para(ilk["medyan"])} → {_para(son["medyan"])}, yani '
        f'<strong>%{abs(degisim):.1f} {yon}</strong>.'
    )
    return (
        '  <section class="icerik-bolumu">\n'
        "    <h2>Fiyat geçmişi</h2>\n"
        f"    <p>{ozet}</p>\n"
        '    <div class="tablo-sarmal"><table>\n'
        "      <thead><tr><th>Ölçüm tarihi</th><th>Ortalama</th><th>Örneklem</th></tr></thead>\n"
        f"      <tbody>{satirlar}</tbody>\n"
        "    </table></div>\n"
        "  </section>\n"
    )



def _resmi_gecmis_html(vertikal: str, veri_kok: Path | None = None) -> str:
    """Kendi zaman serimiz olusana kadar RESMI (TUFE) referans.

    Kendi olcumumuz 2026 Temmuz'da basladi; "Ocak'tan bu yana ne oldu?"
    sorusuna ancak resmi endeksle cevap verilebiliyor. Veri yoksa bos
    doner - uydurma rakam yazilmaz.
    """
    dosya = (veri_kok or SITE_KOK / "veri") / "enflasyon.json"
    if not dosya.exists():
        return ""
    try:
        e = json.loads(dosya.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""
    ilgili = [
        g for g in (e.get("gruplar") or {}).values()
        if vertikal in (g.get("vertikaller") or [g.get("vertikal")])
    ]
    olcumler = e.get("olcumler") or []
    if not ilgili or len(olcumler) < 2:
        return ""
    satirlar = "".join(
        f'<tr><td>{g["ad"]}</td><td class="sayi">%{g["degisim_yuzde"]:+.1f}</td></tr>'
        for g in ilgili
    )
    return (
        '  <section class="icerik-bolumu">\n'
        "    <h2>Fiyat geçmişi</h2>\n"
        "    <p>Kendi ölçümümüz yeni başladı; ilk karşılaştırmalı rakamlar "
        "bir sonraki ölçümde burada görünecek. O zamana kadar resmî veriye "
        "bakabilirsiniz: TÜİK'in tüketici fiyat endeksinde bu kalemi "
        f"kapsayan gruplar {olcumler[0]} — {olcumler[-1]} arasında şöyle "
        "değişti.</p>\n"
        '    <div class="tablo-sarmal"><table>\n'
        '      <thead><tr><th>TÜİK grubu</th><th class="sayi">Değişim</th></tr></thead>\n'
        f"      <tbody>{satirlar}</tbody>\n"
        "    </table></div>\n"
        '    <p class="sonuc-alt-metin">Bu bir <strong>endeks</strong> değişimi; '
        "bizim TL cinsinden ölçtüğümüz fiyatlarla aynı şey değil. "
        "Kaynak: TCMB EVDS, TÜİK Tüketici Fiyat Endeksi (2025=100).</p>\n"
        "  </section>\n"
    )


def _tek_kaynak_uyarisi_html(conf: dict, siteler: set[str]) -> str:
    # Liste fiyatli vertikallerde (0 km arac) tek kaynak bir eksiklik
    # DEGIL: fiyati uretici belirliyor, ikinci kaynak ayni sayiyi verir.
    if conf.get("liste_fiyati"):
        return ""
    """COK KAYNAK KURALI karsilanmadiginda bunu GIZLEME - sayfada soyle.

    Tek kaynak, o sitenin fiyat politikasini yansitir, piyasayi degil
    (bkz. CLAUDE.md). Okuyucunun bunu bilmesi gerekir.
    """
    if len(siteler) != 1:
        return ""
    site = next(iter(siteler)).capitalize()
    return (
        '<div class="uyari-kutu"><strong>Tek kaynak uyarısı:</strong> '
        f"Bu endeksteki fiyatların tamamı şu an tek bir kaynaktan "
        f"(<strong>{site}</strong>) derleniyor. Tek kaynak, o sitenin fiyat "
        "politikasını yansıtır — piyasanın tamamını değil. İkinci bağımsız "
        "kaynak eklenene kadar bu rakamları bir <em>gösterge</em> olarak "
        f'okuyun. <a href="/{conf["yol"]}/metodoloji/">Neden önemli, bakın.</a>'
        "</div>"
    )


def _tahmini_aciklama_html(conf: dict) -> str:
    if not conf["tahmini_kalemler"]:
        return (
            "<p>Bu endeksteki kalemlerin <strong>tamamı</strong> gerçek, tarihli "
            "kaynaklardan derlenmiştir — tahmini kalem yoktur. "
            f'<a href="/{conf["yol"]}/metodoloji/">Yöntemi görün.</a></p>'
        )
    return (
        '<p><span class="tahmini-etiket">Tahmini</span> etiketli kalemler henüz\n'
        "    kazınan bir kaynağa dayanmıyor — genel piyasa araştırmasından\n"
        "    alınmıştır, diğerleri gerçek/tarihli kaynaklardan derlenir.\n"
        f'    <a href="/{conf["yol"]}/metodoloji/">Fark ne, bakın.</a></p>'
    )


def sayfa_uret(vertikal: str = "dugun", veri_dosyasi: Path | None = None) -> str:
    conf = vertikal_conf(vertikal)
    if veri_dosyasi is None:
        veri_dosyasi = SITE_KOK / "veri" / f"{vertikal}.json"

    if veri_dosyasi.exists():
        agregali = json.loads(veri_dosyasi.read_text(encoding="utf-8"))
    else:
        agregali = {"vertikal": vertikal, "guncelleme_tarihi": None, "kalemler": {}}

    kalemler = agregali.get("kalemler", {})
    guncelleme_tarihi = agregali.get("guncelleme_tarihi")
    bugun = date.today().isoformat()
    yol = conf["yol"]
    olcek = conf["olcek_varsayilan"]

    ornek_toplam, ornek_detaylar = ornek_toplam_hesapla(conf, kalemler, olcek, ORNEK_SEGMENT)
    # Sadece TOPLAMA GIREN kalemler sayilir - salon'un secilmeyen varyanti
    # ve yemekli salonla cift sayim olacak "yemek-ikram" tabloda gorunur
    # ama toplama dahil degil; cevap metnindeki kirilim (gercek X TL +
    # tahmini Y TL) ornek_toplam ile TUTMAK zorunda.
    kapsanan_detaylar = [
        d for d in ornek_detaylar if d["veri_var"] and d.get("toplama_dahil", True)
    ]
    gercek_detaylar = [d for d in kapsanan_detaylar if not d["tahmini_mi"]]
    tahmini_detaylar = [d for d in kapsanan_detaylar if d["tahmini_mi"]]
    gercek_toplam = sum(d["satir_toplam"] for d in gercek_detaylar)
    tahmini_toplam = sum(d["satir_toplam"] for d in tahmini_detaylar)
    ornek_ifade = conf["ornek_ifade"].format(olcek=olcek)

    # "kalemler" dolu ama HEPSI genel_medyan=null (ör. o ay tum kaynaklar
    # 0 urun dondu) olabilir - bu durumda "0 TL" gibi yaniltici bir cevap
    # UYDURMAMAK icin gercek kapsanan kalem olup olmadigina bakiliyor,
    # sadece kalemler sozlugunun bos olmadigina degil. Tahmini kalemler
    # her zaman deger urettigi icin bu ayrim "gercek kaynak var mi"
    # sorusuna indirgeniyor - cevap metni buna gore GERCEK ile TAHMINI
    # kismi ACIKCA ayirir, karistirmaz.
    kullanilan_siteler: set[str] = set()
    if gercek_detaylar:
        kapsanan_idler = {d["id"] for d in gercek_detaylar}
        kullanilan_siteler = bagimsiz_siteler(kalemler, kapsanan_idler)
        site_sayisi = len(kullanilan_siteler)
        cevap_metni = (
            f"Maliyeti Ne? verilerine göre {guncelleme_tarihi or bugun} itibarıyla "
            f"{ornek_ifade} <strong>{_para(ornek_toplam)}</strong> tutması bekleniyor. "
        )
        if tahmini_detaylar:
            cevap_metni += (
                f"Bunun {_para(gercek_toplam)} tutarı {len(gercek_detaylar)} kalem için "
                f"{site_sayisi} bağımsız kaynaktan derlenen güncel fiyatlara, "
                f"{_para(tahmini_toplam)} tutarı ise henüz kazınan bir kaynağı olmayan "
                f"{len(tahmini_detaylar)} kalem için genel piyasa araştırmasına dayanır."
            )
        else:
            cevap_metni += (
                f"Bu rakamın tamamı {len(gercek_detaylar)} kalem için "
                f"{site_sayisi} bağımsız kaynaktan derlenen güncel fiyatlara dayanır."
            )
        cevap_disable = ""
    elif tahmini_detaylar:
        cevap_metni = (
            f"{ornek_ifade} kalem kalem toplamı yaklaşık "
            f"<strong>{_para(ornek_toplam)}</strong> "
            "— ancak bu rakam şu an TAMAMEN genel piyasa araştırmasına dayanıyor, "
            "hiçbir kalem henüz kazınan/tarihli bir kaynaktan doğrulanmadı. Gerçek "
            "veri toplandıkça bu sayı kaynaklı rakamlarla güncellenecek."
        )
        cevap_disable = ' style="color:#7a4a06"'
    else:
        ornek_toplam = None
        cevap_metni = (
            "Veri toplama süreci devam ediyor — bu sayfa aylık güncellenen "
            "gerçek fiyat verisiyle otomatik olarak dolacak. Şu an "
            "gösterilecek doğrulanmış bir rakam yok."
        )
        cevap_disable = ' style="color:#7a4a06"'

    # Hesaplayicisi olmayan vertikalde (arac) o linkler gosterilmez -
    # aksi halde sitemap ve menude 404 olusur.
    _h_var = conf.get("hesaplayici_var", True)
    hesaplayici_menu = (
        f'<a href="/{yol}/hesaplayici/">Hesaplayıcı</a>' if _h_var else ""
    )
    hesaplayici_link = (
        f'<a href="/{yol}/hesaplayici/">{conf["hesaplayici_daveti"]}</a>'
        if _h_var else
        f'<a href="/{yol}/metodoloji/">{conf["hesaplayici_daveti"]}</a>'
    )

    guncelleme_etiketi = (
        f'<span class="guncelleme-etiketi">Güncelleme: {guncelleme_tarihi}</span>'
        if guncelleme_tarihi
        else '<span class="guncelleme-etiketi">Henüz güncellenmedi</span>'
    )

    sayfa_url = f"{SITE_KOK_URL}/{yol}/"
    kurum = {
        "@type": "Organization",
        "@id": f"{SITE_KOK_URL}/#kurum",
        "name": "Maliyeti Ne?",
        "url": SITE_KOK_URL,
        "description": "Türkiye için canlı, doğrulanabilir maliyet endeksi.",
    }

    sorular = [{
        "@type": "Question",
        "name": conf["soru"],
        "acceptedAnswer": {
            "@type": "Answer",
            "text": cevap_metni.replace("<strong>", "").replace("</strong>", ""),
        },
    }]
    sorular += ek_sorular_uret(conf, kalemler, olcek)
    sorular += _grup_toplamlari(conf, kalemler, SEGMENT_ANAHTARI[ORNEK_SEGMENT])

    # Dataset: Google Dataset Search'un aradigi alanlar dolduruluyor.
    # "distribution" asil veri dosyasini (agrega.py ciktisi) isaret ediyor -
    # veriyi gercekten indirilebilir kilmak hem seffaflik hem kesfedilebilirlik.
    dataset = {
        "@type": "Dataset",
        "name": conf["dataset_ad"],
        "description": conf["dataset_aciklama"],
        "url": sayfa_url,
        "dateModified": guncelleme_tarihi or bugun,
        "creator": kurum,
        "publisher": kurum,
        "keywords": conf.get("keywords", []),
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "isAccessibleForFree": True,
        "inLanguage": "tr-TR",
        "spatialCoverage": {
            "@type": "Place",
            "name": conf.get("kapsam_yer", "Türkiye"),
        },
        "temporalCoverage": f"{guncelleme_tarihi or bugun}/..",
        "distribution": [{
            "@type": "DataDownload",
            "encodingFormat": "application/json",
            "contentUrl": f"{SITE_KOK_URL}/veri/{vertikal}.json",
        }],
        "measurementTechnique": (
            "Gerçek e-ticaret ve sektör platformlarından robots.txt kurallarına "
            "uygun aylık kazıma; kaynak başına medyan alınıp kaynaklar arası "
            "medyan-of-medyan hesaplanır, persentil bazlı segmentlenir."
        ),
        "variableMeasured": [
            {
                "@type": "PropertyValue",
                "name": t["ad"],
                "unitText": "TRY",
                **({"value": kalem_deger(kalemler[t["id"]], SEGMENT_ANAHTARI[ORNEK_SEGMENT])}
                   if kalemler.get(t["id"])
                   and kalem_deger(kalemler[t["id"]], SEGMENT_ANAHTARI[ORNEK_SEGMENT])
                   else {}),
            }
            for t in conf["kalemler"]
        ],
    }

    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            kurum,
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Ana sayfa",
                     "item": SITE_KOK_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": conf["ad"],
                     "item": sayfa_url},
                ],
            },
            {"@type": "FAQPage", "mainEntity": sorular},
            dataset,
        ],
    }

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{conf["sayfa_basligi"]}</title>
<meta name="description" content="{conf["meta_aciklama"]}">
<link rel="canonical" href="https://maliyetine.com.tr/{yol}/">
<link rel="stylesheet" href="/assets/css/style.css">
<meta property="og:title" content="{conf["baslik"]}">
<meta property="og:description" content="{conf["meta_aciklama"]}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://maliyetine.com.tr/{yol}/">
<meta property="og:site_name" content="Maliyeti Ne?">
<meta property="og:image" content="https://maliyetine.com.tr/assets/og-gorsel.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">Maliyeti <span>Ne?</span></a>
    <nav class="ust-menu">
      {hesaplayici_menu}
      <a href="/{yol}/metodoloji/">Metodoloji</a>
    </nav>
  </div>
</header>

<main class="kapsayici">

  {guncelleme_etiketi}
  <h1>{conf["baslik"]}</h1>

  <div class="cevap-blok"{cevap_disable}>
    {cevap_metni}
  </div>

  {_tek_kaynak_uyarisi_html(conf, kullanilan_siteler)}

  <p>{hesaplayici_link}</p>

  <h2>Kalem kalem fiyatlar</h2>
  {_tahmini_aciklama_html(conf)}
  <table>
    <thead>
      <tr><th>Kalem</th><th class="sayi">Ekonomik</th><th class="sayi">Orta</th><th class="sayi">Lüks</th><th class="sayi">Kaynak</th></tr>
    </thead>
    <tbody>
      {_kalem_satirlari_html(conf, kalemler)}
    </tbody>
  </table>

  {_capraz_dogrulama_uyarilari_html(conf, kalemler)}

  {_icerik_seo_bloklari_html(conf, kalemler, ornek_detaylar)}

  <p>Yöntem, kaynaklar ve örneklem büyüklükleri için
    <a href="/{yol}/metodoloji/">metodoloji sayfasına</a> bakın.</p>

</main>

<footer>
  <div class="kapsayici">
    <div>© 2026 Maliyeti Ne? · <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a> · <a href="/sss/">SSS</a> · <a href="/veri/">Veri</a></div>
    <nav>
      {hesaplayici_menu}
      <a href="/{yol}/metodoloji/">Metodoloji</a>
    </nav>
    <nav class="footer-endeksler" aria-label="Tüm endeksler">{TUM_ENDEKS_LINKLERI}</nav>
  </div>
</footer>

</body>
</html>
"""


def _kalem_tanimi(conf: dict, kalem_id: str) -> dict | None:
    for tanim in conf["kalemler"]:
        if tanim["id"] == kalem_id:
            return tanim
    return None


def _segment_tablosu_html(kalem_verisi: dict | None) -> str:
    degerler = segment_degerleri(kalem_verisi)
    satirlar = []
    for seg in ("dusuk", "orta", "luks"):
        deger = degerler[seg]
        satirlar.append(
            f"<tr><td>{SEGMENT_ETIKETLERI[seg]}</td>"
            f'<td class="sayi">{_para(deger) if deger is not None else "—"}</td></tr>'
        )
    return (
        "<table>\n<thead><tr><th>Segment</th><th class=\"sayi\">Ortalama fiyat</th></tr></thead>\n"
        "<tbody>\n" + "\n".join(satirlar) + "\n</tbody>\n</table>"
    )


def _segment_detay_tablosu_html(kalem_verisi: dict | None) -> str:
    """Medyanin yaninda min/max/orneklem de gosterir.

    Neden: tek bir medyan sayisi "bu rakam nereden geldi?" sorusunu
    cevaplamiyor. Aralik ve orneklem buyuklugu hem guven verir hem
    sayfayi zayif icerik (thin content) olmaktan cikarir - kalem
    sayfalari uzun kuyruk aramanin hedefi, Google'in indekslemesi icin
    gercek icerik gerekiyor.
    """
    # Tutarsiz kirilim gosterilmez (bkz. _segment_tutarsiz_notu).
    if (kalem_verisi or {}).get("segment_tutarsiz"):
        return ""
    segmentler = (kalem_verisi or {}).get("segmentler") or {}
    if not segmentler:
        return _segment_tablosu_html(kalem_verisi)
    satirlar = []
    for seg in ("dusuk", "orta", "luks"):
        s = segmentler.get(seg)
        if not s:
            satirlar.append(
                f"<tr><td>{SEGMENT_ETIKETLERI[seg]}</td>"
                '<td class="sayi">—</td><td class="sayi">—</td>'
                '<td class="sayi">—</td><td class="sayi">—</td></tr>'
            )
            continue
        satirlar.append(
            f"<tr><td>{SEGMENT_ETIKETLERI[seg]}</td>"
            f'<td class="sayi">{_para(s["medyan"])}</td>'
            f'<td class="sayi">{_para(s["min"])}</td>'
            f'<td class="sayi">{_para(s["max"])}</td>'
            f'<td class="sayi">{s.get("urun_sayisi", "—")}</td></tr>'
        )
    return (
        "<table>\n<thead><tr><th>Segment</th>"
        '<th class="sayi">Ortalama</th><th class="sayi">En düşük</th>'
        '<th class="sayi">En yüksek</th><th class="sayi">Ürün</th></tr></thead>\n'
        "<tbody>\n" + "\n".join(satirlar) + "\n</tbody>\n</table>"
    )


def kalem_butce_payi(conf: dict, kalemler: dict, kalem_id: str) -> tuple[int, float] | None:
    """Kalemin, vertikalin ornek toplamindaki payi (tutar, yuzde).

    Veriden HESAPLANIR, uydurulmaz. "Gelinlik dugun butcesinin %2'si"
    gibi bir bilgi hem okuyucu icin degerli hem sayfaya gercek icerik
    katiyor.
    """
    olcek = conf["olcek_varsayilan"]
    toplam, detaylar = ornek_toplam_hesapla(conf, kalemler, olcek, ORNEK_SEGMENT)
    satir = next(
        (d for d in detaylar
         if d["id"] == kalem_id and d["veri_var"] and d.get("toplama_dahil", True)),
        None,
    )
    if not satir or not toplam:
        return None
    return satir["satir_toplam"], satir["satir_toplam"] / toplam * 100


# Bir kalem sayfasinin dibinde gosterilecek en fazla ilgili kalem linki.
# NEDEN SINIR VAR: kalem sayfasi sayisi 9'dan 59'a cikinca bu bolum 38 link
# uretiyordu - sayfanin kendi icerigini bastiran, link-farm gorunumlu bir
# blok. Ayni GRUPTAN (Beyaz esya, Tekstil...) kalemleri onceliklendirmek
# hem okunabilir hem konu olarak daha alakali bir ic link sinyali veriyor.
EN_FAZLA_ILGILI_KALEM = 8


def _ilgili_kalemler_html(conf: dict, mevcut_slug: str) -> str:
    sayfalar = conf.get("kalem_sayfalari", [])
    digerleri = [s for s in sayfalar if s["slug"] != mevcut_slug]
    if not digerleri:
        return ""
    tanimlar = {t["id"]: t for t in conf["kalemler"]}
    mevcut_id = next((s["id"] for s in sayfalar if s["slug"] == mevcut_slug), None)
    mevcut_grup = (tanimlar.get(mevcut_id) or {}).get("grup")

    # Once ayni grup, sonra digerleri - ikisi de kendi icinde tanim sirasinda.
    def sira(sayfa):
        return 0 if mevcut_grup and (tanimlar.get(sayfa["id"]) or {}).get("grup") == mevcut_grup else 1

    secilenler = sorted(digerleri, key=sira)[:EN_FAZLA_ILGILI_KALEM]
    ad_haritasi = {t["id"]: t["ad"].split("—")[0].strip() for t in conf["kalemler"]}
    linkler = " · ".join(
        f'<a href="/{conf["yol"]}/{s["slug"]}/">{ad_haritasi.get(s["id"], s["slug"])}</a>'
        for s in secilenler
    )
    return (
        '  <section class="icerik-bolumu">\n'
        f"    <h2>Diğer {conf['ad'].lower()} kalemleri</h2>\n"
        f"    <p>{linkler}</p>\n"
        "  </section>\n"
    )


def _sss_html(sorular: list[dict]) -> str:
    """Schema'daki FAQ'yu sayfada da GORUNUR yapar.

    Google yalnizca yapilandirilmis veriye guvenmez, gorunur icerik
    bekler; ayrica AI motorlari sayfa metnini okuyor.
    """
    bloklar = []
    for q in sorular:
        bloklar.append(
            f"    <h3>{q['name']}</h3>\n"
            f"    <p>{q['acceptedAnswer']['text']}</p>"
        )
    return (
        '  <section class="icerik-bolumu">\n'
        "    <h2>Sık sorulan sorular</h2>\n"
        + "\n".join(bloklar)
        + "\n  </section>\n"
    )


def _kaynak_ozeti_html(kalem_verisi: dict | None) -> str:
    kaynaklar = (kalem_verisi or {}).get("kaynaklar") or []
    if not kaynaklar:
        return "<p>Bu kalem için kaynak listesi henüz yayınlanmadı.</p>"
    satirlar = []
    for kaynak in kaynaklar:
        urun = kaynak.get("toplam_urun", 0)
        tarih = kaynak.get("tarih", "—")
        durum = f"{urun} ürün" if urun else "bu çalıştırmada ürün yok"
        satirlar.append(
            f"<li><strong>{kaynak['site'].capitalize()}:</strong> {durum}, derleme tarihi {tarih}</li>"
        )
    return "<ul class=\"kaynak-listesi\">" + "\n".join(satirlar) + "</ul>"


def _kalem_sayfasi_sec(conf: dict, slug: str) -> dict:
    for sayfa in conf.get("kalem_sayfalari", []):
        if sayfa["slug"] == slug:
            return sayfa
    raise ValueError(f"Bilinmeyen kalem sayfasi: {conf['yol']}/{slug}")


def kalem_sayfasi_uret(
    vertikal: str,
    slug: str,
    veri_dosyasi: Path | None = None,
) -> str:
    conf = vertikal_conf(vertikal)
    sayfa = _kalem_sayfasi_sec(conf, slug)
    tanim = _kalem_tanimi(conf, sayfa["id"])
    if tanim is None:
        raise ValueError(f"Kalem tanimi bulunamadi: {sayfa['id']}")
    if veri_dosyasi is None:
        veri_dosyasi = SITE_KOK / "veri" / f"{vertikal}.json"

    if veri_dosyasi.exists():
        agregali = json.loads(veri_dosyasi.read_text(encoding="utf-8"))
    else:
        agregali = {"vertikal": vertikal, "guncelleme_tarihi": None, "kalemler": {}}

    kalemler = agregali.get("kalemler", {})
    veri = kalemler.get(sayfa["id"])
    bugun = date.today().isoformat()
    guncelleme_tarihi = agregali.get("guncelleme_tarihi") or bugun
    degerler = segment_degerleri(veri)
    orta = degerler["orta"] or kalem_deger(veri, "orta")
    kaynak_sayisi = len(bagimsiz_siteler({sayfa["id"]: veri or {}}, {sayfa["id"]}))
    urun_sayisi = (veri or {}).get("toplam_urun")
    sayfa_url = f"{SITE_KOK_URL}/{conf['yol']}/{sayfa['slug']}/"
    _kh = conf.get("hesaplayici_var", True)
    kalem_hesaplayici_menu = (
        f'<a href="/{conf["yol"]}/hesaplayici/">Hesaplayıcı</a>' if _kh else ""
    )
    kalem_hesaplayici_govde = (
        f'<a href="/{conf["yol"]}/hesaplayici/">hesaplayıcıya</a> gidin.'
        if _kh else "endeks sayfasına gidin."
    )
    birim = " kişi başı" if tanim["birim"] == "kisi_basi" else ""

    if orta:
        cevap = (
            f"Maliyeti Ne? verilerine göre {guncelleme_tarihi} itibarıyla {tanim['ad']} "
            f"{'ortalama fiyatı' if (veri or {}).get('segment_tutarsiz') else 'orta segment ortalama fiyatı'} {birim} <strong>{_para(orta)}</strong>. "
            f"Bu rakam {kaynak_sayisi or (veri or {}).get('kaynak_sayisi', 0)} bağımsız kaynak"
        )
        if urun_sayisi:
            cevap += f" ve {urun_sayisi} ürün üzerinden derlendi."
        else:
            cevap += " üzerinden derlendi."
    else:
        cevap = (
            f"{tanim['ad']} için doğrulanmış fiyat verisi henüz hazır değil. "
            "Kaynaklı veri geldiğinde bu sayfa otomatik güncellenecek."
        )

    # Meta aciklama SERP'te gorunur: GERCEK RAKAM icersin, 160 karakteri
    # asmasin (Google keser).
    if orta:
        meta_aciklama = (
            f"{tanim['ad']} {'ortalama fiyatı' if (veri or {}).get('segment_tutarsiz') else 'orta segment ortalama fiyatı'}{birim} {_para(orta)} "
            f"({guncelleme_tarihi}). Ekonomik, orta ve lüks fiyat aralığı; "
            f"kaynak sayısı ve örneklem büyüklüğüyle."
        )
    else:
        meta_aciklama = (
            f"{tanim['ad']} fiyat verisi hazırlanıyor. Kaynaklı veri geldiğinde "
            "bu sayfa otomatik güncellenecek."
        )
    if len(meta_aciklama) > 158:
        meta_aciklama = meta_aciklama[:155].rsplit(" ", 1)[0] + "…"

    kurum = {
        "@type": "Organization",
        "@id": f"{SITE_KOK_URL}/#kurum",
        "name": "Maliyeti Ne?",
        "url": SITE_KOK_URL,
        "description": "Türkiye için canlı, doğrulanabilir maliyet endeksi.",
    }
    # SSS: hepsi VERIDEN uretiliyor, uydurma cevap yok. Hem schema'ya hem
    # sayfaya (gorunur) konuyor - Google yapilandirilmis veriye tek basina
    # guvenmiyor, AI motorlari da sayfa metnini okuyor.
    sorular = [{
        "@type": "Question",
        "name": sayfa["soru"],
        "acceptedAnswer": {
            "@type": "Answer",
            "text": cevap.replace("<strong>", "").replace("</strong>", ""),
        },
    }]

    pay = kalem_butce_payi(conf, kalemler, sayfa["id"])
    if pay:
        tutar, yuzde = pay
        birim_notu = (
            f" ({conf['olcek_varsayilan']} kişilik hesapla {_para(tutar)})"
            if tanim["birim"] == "kisi_basi" else ""
        )
        sorular.append({
            "@type": "Question",
            "name": f"{tanim['ad']} toplam bütçenin ne kadarı?",
            "acceptedAnswer": {"@type": "Answer", "text": (
                f"Orta segmentte {tanim['ad']}, {conf['ad'].lower()} bütçesinin "
                f"yaklaşık %{yuzde:.0f}'ini oluşturuyor{birim_notu}. "
                f"Kalem kalem tüm döküm {conf['ad'].lower()} endeksi sayfasında."
            )},
        })

    if degerler.get("dusuk") and degerler.get("luks"):
        kat = degerler["luks"] / degerler["dusuk"]
        sorular.append({
            "@type": "Question",
            "name": f"{tanim['ad']} fiyatları arasında ne kadar fark var?",
            "acceptedAnswer": {"@type": "Answer", "text": (
                f"Ekonomik segmentte {_para(degerler['dusuk'])}, lüks segmentte "
                f"{_para(degerler['luks'])} — yaklaşık {kat:.1f} kat fark. "
                "Segmentler persentil bazlı ayrılır: en ucuz çeyrek ekonomik, "
                "ortadaki yarı orta, en pahalı çeyrek lüks kabul edilir."
            )},
        })

    sorular.append({
        "@type": "Question",
        "name": "Fiyatlar ne zaman güncellendi?",
        "acceptedAnswer": {"@type": "Answer", "text": (
            f"Bu sayfadaki fiyatlar {guncelleme_tarihi} tarihinde ölçüldü ve "
            "ayda bir yenilenir."
        )},
    })

    butce_cumlesi = (
        f" — orta segmentte {conf['ad'].lower()} bütçesinin yaklaşık %{pay[1]:.0f}'i."
        if pay else "."
    )

    uyari = (veri or {}).get("capraz_dogrulama_uyarisi")
    if uyari:
        sorular.append({
            "@type": "Question",
            "name": "Kaynaklar arasında neden fark var?",
            "acceptedAnswer": {"@type": "Answer", "text": (
                f"Kaynaklar arası fark %{uyari['fark_yuzdesi']:.0f}. Bu genellikle "
                "farklı segmentlerin (pazaryeri ile marka mağazası) karşılaştırılmasından "
                "kaynaklanır."
            )},
        })

    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            kurum,
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Ana sayfa", "item": SITE_KOK_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": conf["ad"], "item": f"{SITE_KOK_URL}/{conf['yol']}/"},
                    {"@type": "ListItem", "position": 3, "name": tanim["ad"], "item": sayfa_url},
                ],
            },
            {"@type": "FAQPage", "mainEntity": sorular},
        ],
    }

    # Product/AggregateOffer: fiyat araligi olan kalemler icin zengin sonuc
    # adayi. Tek bir urun degil, olculen urun kumesini temsil ediyor -
    # o yuzden AggregateOffer ve lowPrice/highPrice kullaniliyor.
    if orta and degerler.get("dusuk") and degerler.get("luks"):
        json_ld["@graph"].append({
            "@type": "Product",
            "name": f"{tanim['ad']} fiyatları ({guncelleme_tarihi})",
            "description": sayfa["aciklama"],
            "category": conf["ad"],
            "offers": {
                "@type": "AggregateOffer",
                "priceCurrency": "TRY",
                "lowPrice": degerler["dusuk"],
                "highPrice": degerler["luks"],
                "offerCount": urun_sayisi or (veri or {}).get("toplam_urun") or 1,
                "availability": "https://schema.org/InStock",
            },
        })

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_seo_title(tanim["ad"])}</title>
<meta name="description" content="{meta_aciklama}">
<link rel="canonical" href="{sayfa_url}">
<link rel="stylesheet" href="/assets/css/style.css">
<meta property="og:title" content="{sayfa["baslik"]}">
<meta property="og:description" content="{meta_aciklama}">
<meta property="og:type" content="article">
<meta property="og:url" content="{sayfa_url}">
<meta property="og:site_name" content="Maliyeti Ne?">
<meta property="og:image" content="https://maliyetine.com.tr/assets/og-gorsel.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">Maliyeti <span>Ne?</span></a>
    <nav class="ust-menu">
      <a href="/{conf["yol"]}/">Endeks</a>
      {kalem_hesaplayici_menu}
      <a href="/{conf["yol"]}/metodoloji/">Metodoloji</a>
    </nav>
  </div>
</header>

<main class="kapsayici">
{_breadcrumb_html(conf, tanim["ad"])}  <span class="guncelleme-etiketi">Güncelleme: {guncelleme_tarihi}</span>
  <h1>{sayfa["baslik"]}</h1>

  <div class="cevap-blok">
    {cevap}
  </div>

  <section class="icerik-bolumu">
    <h2>Fiyat aralığı ve örneklem</h2>
    <p>{sayfa["aciklama"]}</p>
{_segment_tutarsiz_notu(veri)}
{_segment_grafigi(degerler, " (kişi başı)" if tanim["birim"] == "kisi_basi" else "")}
    {_segment_detay_tablosu_html(veri)}
    <p class="sonuc-alt-metin">Segmentler persentil bazlı ayrılır: en ucuz
      çeyrek ekonomik, ortadaki yarı orta, en pahalı çeyrek lüks. "Ürün"
      sütunu o segmentte kaç ürünün ölçüldüğünü gösterir.</p>
  </section>

  <section class="icerik-bolumu">
    <h2>Bu fiyata ne dahil?</h2>
    <p>Bu sayfa yalnızca <strong>{tanim["ad"]}</strong> kalemini ölçer{butce_cumlesi} Tüm bütçeyi görmek için
      <a href="/{conf["yol"]}/">{conf["ad"]} maliyeti endeksine</a> veya
      {kalem_hesaplayici_govde}</p>
  </section>

{_sss_html(sorular)}
{_fiyat_gecmisi_html(vertikal, sayfa['id'])}{_nereden_alinir_html(vertikal, sayfa['id'], tanim['ad'])}{_kunye_html(conf, veri, guncelleme_tarihi)}{_ilgili_kalemler_html(conf, sayfa["slug"])}</main>

<footer>
  <div class="kapsayici">
    <div>© 2026 Maliyeti Ne? · <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a> · <a href="/sss/">SSS</a> · <a href="/veri/">Veri</a></div>
    <nav>
      <a href="/{conf["yol"]}/">{conf["ad"]} endeksi</a>
      {kalem_hesaplayici_menu}
      <a href="/{conf["yol"]}/metodoloji/">Metodoloji</a>
    </nav>
    <nav class="footer-endeksler" aria-label="Tüm endeksler">{TUM_ENDEKS_LINKLERI}</nav>
  </div>
</footer>

</body>
</html>
"""


def kalem_sayfalari_yaz(vertikal: str, veri_dosyasi: Path | None = None) -> list[Path]:
    conf = vertikal_conf(vertikal)
    yazilanlar = []
    for sayfa in conf.get("kalem_sayfalari", []):
        hedef = SITE_KOK / conf["yol"] / sayfa["slug"] / "index.html"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(kalem_sayfasi_uret(vertikal, sayfa["slug"], veri_dosyasi), encoding="utf-8")
        yazilanlar.append(hedef)
    return yazilanlar


def bayat_kalem_sayfalarini_temizle(vertikal: str) -> list[Path]:
    """Artik uretilmeyen kalem sayfalarini SILER.

    NEDEN GEREKLI: bir kalem sayfasi listeden dustugunde (orneklem
    kapanma esigin altina indi, ya da kalem tanimi degisti) diskteki
    dosya OLDUGU GIBI KALIYORDU. Sonuc: canlida 200 donen, aylar once
    olculmus rakamlari gosteren, sitemap'te olmayan yetim sayfalar.
    2026-07-26'da 6 tane birikmisti (ör. /arac/tesla-fiyatlari/ hala
    07-25 verisini gosteriyordu). Bayat icerik hem okuyucuyu yaniltir
    hem arama motorunda guven kaybettirir.

    Yalnizca `{kalem}-fiyatlari` deseni ve bilinen sabit sayfalar disi
    dizinlere dokunur - hesaplayici/metodoloji asla silinmez.
    """
    conf = vertikal_conf(vertikal)
    gecerli = {s["slug"] for s in conf.get("kalem_sayfalari", [])}
    # SENARYO SAYFALARI KORUNMALI: bunlar kalem sayfasi degil ama ayni
    # dizin duzeninde duruyor ("beyaz-esya-fiyatlari"). Korunmazsa
    # temizleyici onlari "artik uretilmeyen kalem sayfasi" sanip SILIYOR -
    # 2026-07-26'da dugun senaryolari (100/200/300 kisilik) tam olarak
    # boyle silindi ve endeks sayfasindaki linkler kirildi.
    try:
        import senaryo
        gecerli |= {slug for v, slug in senaryo.tum_slugler() if v == vertikal}
    except ImportError:
        pass
    korunan = {"hesaplayici", "metodoloji"}
    kok = SITE_KOK / conf["yol"]
    silinen = []
    if not kok.exists():
        return silinen
    for dizin in sorted(kok.iterdir()):
        if not dizin.is_dir() or dizin.name in korunan or dizin.name in gecerli:
            continue
        sayfa = dizin / "index.html"
        if not sayfa.exists():
            continue
        sayfa.unlink()
        try:
            dizin.rmdir()
        except OSError:
            pass  # icinde baska dosya varsa dizini birak
        silinen.append(dizin)
    return silinen



# --- Genel SSS sayfasi ---------------------------------------------------
# NEDEN AYRI SAYFA: kalem sayfalarindaki SSS o kaleme ozgu. Site geneline
# dair sorular ("veri nereden geliyor", "ne siklikla guncelleniyor",
# "kullanabilir miyim") her sayfada tekrarlanamaz. FAQPage schema ile
# zengin sonuc adayi; ayrica AI motorlari bu tur sayfalari kaynak
# gosterirken tercih ediyor.
#
# CEVAPLAR VERIDEN BESLENIYOR: kalem/kaynak sayilari elle yazilmaz,
# bayatlamasin.
def sss_sorulari(veri_kok: Path | None = None) -> list[dict]:
    kok = veri_kok or SITE_KOK / "veri"
    toplam_kalem = 0
    siteler: set[str] = set()
    tarih = ""
    for vertikal in VERTIKALLER:
        dosya = kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        try:
            veri = json.loads(dosya.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        kalemler = veri.get("kalemler") or {}
        toplam_kalem += len(kalemler)
        tarih = max(tarih, veri.get("guncelleme_tarihi") or "")
        for k in kalemler.values():
            for kaynak in k.get("kaynaklar") or []:
                if (kaynak.get("toplam_urun") or 0) > 0 and kaynak.get("site"):
                    siteler.add(kaynak["site"])

    return [
        {
            "s": "Bu fiyatlar nereden geliyor?",
            "c": (
                f"Gerçek satış sayfalarından. Şu an {toplam_kalem} kalem, "
                f"{len(siteler)} farklı siteden ölçülüyor: e-ticaret siteleri, "
                "marka mağazaları ve sektör platformları. Fiyat tahmin edilmiyor, "
                "yayınlanan listelerden okunuyor. Her kalemin yanında kaç üründen "
                "derlendiği ve hangi tarihte ölçüldüğü yazıyor."
            ),
        },
        {
            "s": "Ne sıklıkla güncelleniyor?",
            "c": (
                "Ayda iki kez, her ayın 5'i ve 20'sinde otomatik olarak. "
                f"Son ölçüm: {tarih}. Her sayfada güncelleme tarihi görünür; "
                "veri değişmediyse tarihi yenilemiyoruz."
            ),
        },
        {
            "s": "\"Ortalama fiyat\" derken neyi kastediyorsunuz?",
            "c": (
                "Aritmetik ortalamayı değil, ortanca değeri. Fiyatları küçükten "
                "büyüğe sıralayıp tam ortadakini alıyoruz. Nedeni: tek bir çok "
                "pahalı ürün aritmetik ortalamayı yukarı çeker ve gerçekte "
                "kimsenin ödemediği bir rakam çıkar."
            ),
        },
        {
            "s": "Ekonomik, orta ve üst segment nasıl belirleniyor?",
            "c": (
                "Yüzdelik dilime göre: en ucuz çeyrek ekonomik, ortadaki yarı "
                "orta, en pahalı çeyrek üst. Bir uyarı: bu rakamlar kategori "
                "listelerinden geliyor, yani \"üst\" piyasanın en pahalısı değil, "
                "yaygın ürünler içindeki üst çeyrek."
            ),
        },
        {
            "s": "Aynı ürün iki sitede farklı fiyatta, hangisi doğru?",
            "c": (
                "İkisi de. Kaynaklar arası fark genelde fiyat politikası değil, "
                "listelerdeki ürün karması farkı: bir sitede markalı ürünler, "
                "diğerinde isimsiz modeller öne çıkabiliyor. Bu yüzden ham "
                "fiyatları karıştırmıyoruz; her kaynağın kendi orta değerini "
                "alıp onların ortasını hesaplıyoruz. Fark %30'u aşarsa sayfada "
                "uyarı olarak gösteriyoruz."
            ),
        },
        {
            "s": "Verileri kullanabilir miyim?",
            "c": (
                "Evet. Tüm veri CSV ve JSON olarak indirilebilir (CC BY 4.0). "
                "Tek ricamız ölçüm tarihini de belirtmeniz — fiyat verisi "
                "tarihsiz olduğunda yanıltıcı hale geliyor."
            ),
        },
        {
            "s": "Neden kira, konut ve işçilik yok?",
            "c": (
                "Çünkü tek bir sayıya sığmıyorlar. Aynı şehirde iki mahalle "
                "arasında kira ikiye katlanabiliyor. Ölçemediğimiz şeye rakam "
                "uydurmaktansa kapsam dışı bırakmayı tercih ediyoruz."
            ),
        },
        {
            "s": "Reklam veriyor musunuz, bağımsız mısınız?",
            "c": (
                "Fiyatlar hiçbir ticari ilişkiden etkilenmiyor: kaynak seçimi ve "
                "ölçüm otomatik, bir markanın ödeme yapması rakamı değiştirmiyor. "
                "Gelir modelimiz ve bağımsızlık beyanımız hakkımızda sayfasında."
            ),
        },
        {
            "s": "Bir hata görürsem ne yapmalıyım?",
            "c": (
                "İletişim sayfasından yazın. Düzeltir ve neyi düzelttiğimizi "
                "yazarız — hatayı sessizce silmiyoruz."
            ),
        },
    ]



def sss_sayfasi_uret(veri_kok: Path | None = None, tarih: str | None = None) -> str:
    tarih = tarih or date.today().isoformat()
    sorular = sss_sorulari(veri_kok)
    url = f"{SITE_KOK_URL}/sss/"
    govde = "".join(
        f'    <h2>{q["s"]}</h2>\n    <p>{q["c"]}</p>\n' for q in sorular
    )
    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q["s"],
                     "acceptedAnswer": {"@type": "Answer", "text": q["c"]}}
                    for q in sorular
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Ana sayfa",
                     "item": SITE_KOK_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Sık sorulan sorular",
                     "item": url},
                ],
            },
        ],
    }
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sık Sorulan Sorular | Maliyeti Ne?</title>
<meta name="description" content="Fiyatlar nereden geliyor, ne sıklıkla güncelleniyor, veriyi kullanabilir miyim? Maliyeti Ne? hakkında sık sorulan sorular ve yanıtları.">
<link rel="canonical" href="{url}">
<link rel="stylesheet" href="/assets/css/style.css">
<meta property="og:title" content="Sık Sorulan Sorular | Maliyeti Ne?">
<meta property="og:description" content="Fiyatlar nereden geliyor, ne sıklıkla güncelleniyor, veriyi kullanabilir miyim?">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE_KOK_URL}/assets/og-gorsel.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">Maliyeti <span>Ne?</span></a>
    <nav class="ust-menu">
      <a href="/dugun/">Düğün</a>
      <a href="/ev-kurma/">Ev Kurma</a>
      <a href="/okul/">Okul</a>
      <a href="/arac/">0 km Araç</a>
    </nav>
  </div>
</header>

<main class="kapsayici">

  <nav class="kirinti" aria-label="Sayfa yolu">
    <a href="/">Ana sayfa</a> <span aria-hidden="true">›</span> <span>Sık sorulan sorular</span>
  </nav>

  <h1>Sık Sorulan Sorular</h1>

  <div class="cevap-blok">
    Fiyatları nereden aldığımız, ne sıklıkla ölçtüğümüz ve veriyi nasıl
    kullanabileceğiniz — hepsi burada. Yöntemin ayrıntısı için her endeksin
    kendi metodoloji sayfası var.
  </div>

  <section class="icerik-bolumu">
{govde}  </section>

  <section class="icerik-bolumu">
    <h2>Başka sorunuz varsa</h2>
    <p>
      <a href="/iletisim/">İletişim sayfasından</a> yazabilirsiniz. Veriyi
      indirmek için <a href="/veri/">veri sayfasına</a>, yöntemin tamamı için
      metodoloji sayfalarına bakabilirsiniz:
      <a href="/dugun/metodoloji/">düğün</a>,
      <a href="/ev-kurma/metodoloji/">ev kurma</a>,
      <a href="/okul/metodoloji/">okul</a>,
      <a href="/arac/metodoloji/">0 km araç</a>.
    </p>
  </section>

</main>

<footer>
  <div class="kapsayici">
    <div>© {tarih[:4]} Maliyeti Ne? · <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a> · <a href="/sss/">SSS</a> · <a href="/veri/">Veri</a></div>
    <nav>
      <a href="/dugun/">Düğün</a>
      <a href="/ev-kurma/">Ev Kurma</a>
      <a href="/okul/">Okul</a>
      <a href="/arac/">0 km Araç</a>
    </nav>
  </div>
</footer>

</body>
</html>
"""



def _senaryo_linkleri_html(conf: dict) -> str:
    """Endeks sayfasindan senaryo sayfalarina ic link.

    Senaryo sayfalari gercek arama niyetini hedefliyor ("100 kisilik
    dugun"); endeksten link almazlarsa yetim kalirlar ve sitemap tek
    basina zayif sinyal.
    """
    try:
        import senaryo
    except ImportError:
        return ""
    vertikal = next((v for v, c in VERTIKALLER.items() if c is conf), None)
    if not vertikal:
        return ""
    kayitlar = []
    for grup in (senaryo.OLCEK_SENARYOLARI, senaryo.GRUP_SENARYOLARI):
        for s in grup.get(vertikal, []):
            if (SITE_KOK / conf["yol"] / s["slug"] / "index.html").exists():
                kayitlar.append((s["slug"], s["baslik"]))
    if not kayitlar:
        return ""
    linkler = " · ".join(
        f'<a href="/{conf["yol"]}/{slug}/">{baslik}</a>' for slug, baslik in kayitlar
    )
    return (
        '  <section class="icerik-bolumu">\n'
        "    <h2>Hazır senaryolar</h2>\n"
        f"    <p>{linkler}</p>\n"
        "  </section>\n"
    )


def sitemap_uret() -> str:
    url_kayitlari = [
        ("/", "monthly", "1.0"),
        ("/hakkimizda/", "yearly", "0.6"),
        ("/iletisim/", "yearly", "0.4"),
    ]
    # Veri indirme merkezi - alintilanabilirligin merkezi sayfasi.
    if (SITE_KOK / "veri" / "index.html").exists():
        url_kayitlari.append(("/veri/", "monthly", "0.8"))
    if (SITE_KOK / "sss" / "index.html").exists():
        url_kayitlari.append(("/sss/", "monthly", "0.6"))
    # Senaryo sayfalari (100 kisilik dugun, beyaz esya butcesi...) -
    # gercek arama niyetini hedefliyorlar, oncelik kalem sayfasi kadar.
    try:
        import senaryo
        for vert, slug in senaryo.tum_slugler():
            if (SITE_KOK / VERTIKALLER[vert]["yol"] / slug / "index.html").exists():
                url_kayitlari.append((f"/{VERTIKALLER[vert]['yol']}/{slug}/", "monthly", "0.7"))
    except ImportError:
        pass
    # Rehber (blog) sayfalari - rehber.py uretir, sitemap buradan besleniyor.
    # Import fonksiyon icinde: rehber.py sayfa_uret'i import ediyor, modul
    # seviyesinde karsilikli import olurdu.
    try:
        import rehber
        if (SITE_KOK / "rehber" / "index.html").exists():
            url_kayitlari.append(("/rehber/", "monthly", "0.7"))
            for r in rehber.REHBERLER:
                if (SITE_KOK / "rehber" / r["slug"] / "index.html").exists():
                    url_kayitlari.append((f"/rehber/{r['slug']}/", "monthly", "0.7"))
    except ImportError:
        pass

    for conf in VERTIKALLER.values():
        yol = conf["yol"]
        url_kayitlari.extend([
            (f"/{yol}/", "monthly", "0.9"),
            *([(f"/{yol}/hesaplayici/", "monthly", "0.8")]
              if conf.get("hesaplayici_var", True) else []),
            (f"/{yol}/metodoloji/", "yearly", "0.5"),
        ])
        for sayfa in conf.get("kalem_sayfalari", []):
            url_kayitlari.append((f"/{yol}/{sayfa['slug']}/", "monthly", "0.7"))

    satirlar = ['<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for yol, frekans, oncelik in url_kayitlari:
        # lastmod: sayfanin GERCEK dosya tarihi. Onceden hic yoktu ve
        # arama motoru hangi sayfanin tazelendigini bilemiyordu - ayda
        # iki kez guncellenen bir sitede bu dogrudan tarama butcesi
        # kaybi. Uydurma tarih YAZILMAZ: dosya yoksa alan atlanir.
        dosya = SITE_KOK / yol.strip("/") / "index.html" if yol != "/" else SITE_KOK / "index.html"
        lastmod = ""
        if dosya.exists():
            lastmod = date.fromtimestamp(dosya.stat().st_mtime).isoformat()
        satirlar.append("  <url>")
        satirlar.append(f"    <loc>{SITE_KOK_URL}{yol}</loc>")
        if lastmod:
            satirlar.append(f"    <lastmod>{lastmod}</lastmod>")
        satirlar.extend([
            f"    <changefreq>{frekans}</changefreq>",
            f"    <priority>{oncelik}</priority>",
            "  </url>",
        ])
    satirlar.append("</urlset>")
    return "\n".join(satirlar) + "\n"


def vertikal_ozeti(vertikal: str, veri_kok: Path | None = None) -> dict | None:
    """Bir vertikalin ana sayfada gosterilecek ozeti (toplam, kaynak, tarih).

    Veri yoksa ya da hicbir kalemde gercek deger yoksa None doner -
    ana sayfa o zaman rakam UYDURMAZ, "hazirlaniyor" der.
    """
    conf = vertikal_conf(vertikal)
    dosya = (veri_kok or SITE_KOK / "veri") / f"{vertikal}.json"
    if not dosya.exists():
        return None
    agregali = json.loads(dosya.read_text(encoding="utf-8"))
    kalemler = agregali.get("kalemler", {})
    olcek = conf["olcek_varsayilan"]
    toplam, detaylar = ornek_toplam_hesapla(conf, kalemler, olcek, ORNEK_SEGMENT)
    dahil = [d for d in detaylar if d["veri_var"] and d.get("toplama_dahil", True)]
    gercek = [d for d in dahil if not d["tahmini_mi"]]
    if not gercek:
        return None
    return {
        "vertikal": vertikal,
        "ad": conf["ad"],
        "yol": conf["yol"],
        "soru": conf["soru"],
        "toplam": toplam,
        "gercek_toplam": sum(d["satir_toplam"] for d in gercek),
        "tahmini_toplam": sum(d["satir_toplam"] for d in dahil if d["tahmini_mi"]),
        "gercek_kalem": len(gercek),
        "tahmini_kalem": len([d for d in dahil if d["tahmini_mi"]]),
        "site_sayisi": len(bagimsiz_siteler(kalemler, {d["id"] for d in gercek})),
        "guncelleme_tarihi": agregali.get("guncelleme_tarihi"),
        "ornek_ifade": conf["ornek_ifade"].format(olcek=olcek),
        "anasayfa_ifade": conf.get("anasayfa_ifade", conf["ornek_ifade"]).format(olcek=olcek),
        "kart_alt": conf.get("kart_alt", "").format(olcek=olcek),
        # Ana sayfadaki hizli linkler icin kisa etiket: kalem adinin
        # "—"den onceki kismi ("Düğün Salonu — yemekli (menü dahil)" ->
        # "Düğün Salonu"). kalem_sayfalari girdilerinde kisa bir ad alani
        # yok, uzun basliklar ana sayfa kartinda tasiyor.
        "kalem_sayfalari": [
            {
                **k,
                # Kisa ad em-dash'ten kesiliyor ("Dugun Salonu - yemekli"
                # -> "Dugun Salonu"). AMA salon iki varyanta bolundugu icin
                # iki AYRI sayfa ayni etiketle gorunuyordu. Varyant kismi
                # parantezle korunuyor: "Dugun Salonu (yemekli)".
                "kisa_ad": next(
                    (_kisa_kalem_adi(t["ad"]) for t in conf["kalemler"]
                     if t["id"] == k["id"]),
                    k["slug"].replace("-fiyatlari", "").replace("-", " ").capitalize(),
                ),
            }
            for k in conf.get("kalem_sayfalari", [])
        ],
    }


def anasayfa_uret(veri_kok: Path | None = None) -> str:
    """Ana sayfayi GERCEK rakamlarla build-time'da uretir.

    Neden build-time: ana sayfa GEO'nun ilk temas noktasi. Onceki hali
    elle yazilmisti ve HIC RAKAM ICERMIYORDU - AI motorlari icin
    alintilanabilir bir sey yoktu, kullanici da once bir sayi gormek
    istiyor. Simdi iki endeksin guncel toplami hem cevap blogunda hem
    kartlarda gorunuyor, kalem sayfalarina ic link veriyor.
    """
    bugun = date.today().isoformat()
    ozetler = [o for o in (vertikal_ozeti(v, veri_kok) for v in VERTIKALLER) if o]

    # Rehber linkleri: yalnizca gercekten URETILMIS olanlar. Veri yoksa
    # rehber.py sayfayi yazmiyor - burada da linki verilmemeli, aksi
    # halde ana sayfadan 404'e link cikar.
    # Paylasim aciklamasi: soyut "guvenilir veri" iddiasi yerine
    # olculebilir kanit. X/WhatsApp kartinda gorunen tek cumle bu.
    _og_kalem = sum(len((o.get("kalemler") or {})) for o in [
        json.loads((( veri_kok or SITE_KOK / "veri") / f"{v}.json").read_text(encoding="utf-8"))
        for v in VERTIKALLER
        if (( veri_kok or SITE_KOK / "veri") / f"{v}.json").exists()
    ])
    _og_siteler = set()
    for v in VERTIKALLER:
        d = (veri_kok or SITE_KOK / "veri") / f"{v}.json"
        if not d.exists():
            continue
        for k in (json.loads(d.read_text(encoding="utf-8")).get("kalemler") or {}).values():
            for kay in k.get("kaynaklar") or []:
                if (kay.get("toplam_urun") or 0) > 0 and kay.get("site"):
                    _og_siteler.add(kay["site"])
    og_aciklama = (
        f"{_og_kalem} kalem, {len(_og_siteler)} bağımsız kaynaktan ayda iki kez "
        "ölçülüyor. Her rakamın yanında kaynak ve ölçüm tarihi var."
    ) if _og_kalem else "Gerçek fiyat verisinden derlenmiş maliyet endeksi."

    # Sohbet asistani: cevaplari VERIDEN secen, uydurma yapamayan yapi
    # (bkz. asistan.py - LLM yok, cumleler sabit sablon).
    asistan_blok, asistan_js_kod = "", ""
    try:
        import asistan as _asistan
        _av = _asistan.asistan_verisi(veri_kok)
        if _av["kalemler"]:
            asistan_blok = _asistan.asistan_html(_av)
            asistan_js_kod = _asistan.asistan_js(_av)
    except ImportError:
        pass

    arama_kayitlari = _arama_verisi(veri_kok)
    arama_js = _arama_js(arama_kayitlari) if arama_kayitlari else ""
    hizli = _hizli_hesap_katsayilari(veri_kok)
    hizli_secenekler = "".join(
        f'<option value="{v}">{d["ad"]}</option>' for v, d in hizli.items()
    )
    hizli_hesap_js = _hizli_hesap_js(hizli) if hizli else ""
    rehber_linkleri = ""
    anasayfa_yazi = ""
    try:
        import rehber
        # veri_kok'u AKTAR: aksi halde yazi her zaman canli dosyalari
        # okur, cagirana verilen veri kokunu yok sayar (test bunu yakaladi).
        anasayfa_yazi = rehber.anasayfa_yazisi(rehber._veriler(veri_kok))
        rehber_linkleri = "".join(
            f'<a href="/rehber/{r["slug"]}/">{r["baslik"]}</a>'
            for r in rehber.REHBERLER
            if (SITE_KOK / "rehber" / r["slug"] / "index.html").exists()
        )
    except ImportError:
        pass

    if ozetler:
        cumleler = [
            f"{o['anasayfa_ifade']} <strong>{_para(o['toplam'])}</strong>"
            for o in ozetler
        ]
        tarih = max(o["guncelleme_tarihi"] or bugun for o in ozetler)
        cevap = (
            f"Maliyeti Ne? verilerine göre {tarih} itibarıyla "
            + "; ".join(cumleler)
            + " tutuyor. Rakamlar gerçek e-ticaret ve sektör "
              "platformlarından aylık derlenir; her kalemin yanında kaynak "
              "sayısı ve derleme tarihi görünür."
        )
        cevap_stil = ""
    else:
        cevap = (
            "Veri toplama süreci devam ediyor — bu sayfa aylık güncellenen "
            "gerçek fiyat verisiyle otomatik olarak dolacak."
        )
        cevap_stil = ' style="color:#7a4a06"'
        tarih = bugun

    # Endeks kartlari: verisi olan vertikaller rakamiyla, olmayanlar "Yakinda".
    kartlar = []
    for o in ozetler:
        # Kart basina en fazla ANASAYFA_KART_LINK_SINIRI kalem linki.
        # Sinirsizken ev-kurma karti 42 link uretiyor, digerlerinin uc
        # katina cikip grid'i eziyordu - kartlar yan yana dururken biri
        # ekran boyu uzun, digerleri bir avuc. Kalan kalemlere endeks
        # sayfasindan zaten ulasiliyor.
        gosterilen = o["kalem_sayfalari"][:ANASAYFA_KART_LINK_SINIRI]
        alt_linkler = "".join(
            f'<a href="/{o["yol"]}/{k["slug"]}/">{k["kisa_ad"]}</a>'
            for k in gosterilen
        )
        kalan = len(o["kalem_sayfalari"]) - len(gosterilen)
        if kalan > 0:
            alt_linkler += f'<a href="/{o["yol"]}/" class="kart-link-tum">+{kalan} kalem</a>' 
        kartlar.append(f"""    <div class="vertikal-kart kart">
      <h3><a href="/{o['yol']}/">{o['ad']} maliyeti</a></h3>
      <p class="kart-rakam">{_para(o['toplam'])}</p>
      <p class="kart-alt">{o['kart_alt']} · {o['gercek_kalem']} kalem
        {o['site_sayisi']} bağımsız kaynaktan{", " + str(o['tahmini_kalem']) + " kalem tahmini" if o['tahmini_kalem'] else " (tamamı gerçek kaynaklı)"}</p>
      <p class="kart-linkler">{alt_linkler}</p>
    </div>""")

    # "Yakinda" kartlari SABIT LISTE DEGIL: yayina giren vertikal bu
    # listeden dusmeli. Onceden sabitti ve 0 km arac yayina girdikten
    # sonra da "Yakinda" kartiyla gorunmeye devam ediyordu - ayni endeks
    # sayfada hem gercek rakamla hem "hazirlaniyor" diye iki kez cikti.
    yayindaki = {o["yol"] for o in ozetler}
    for yol, ad in (("ev-tadilati", "Ev tadilatı"), ("tatil", "Tatil")):
        if yol in yayindaki:
            continue
        kartlar.append(f"""    <div class="kart kart-yakinda">
      <h3>{ad} maliyeti <span class="yakinda-etiket">Yakında</span></h3>
      <p>Hazırlanıyor.</p>
    </div>""")

    kurum = {
        "@type": "Organization",
        "@id": f"{SITE_KOK_URL}/#kurum",
        "name": "Maliyeti Ne?",
        "url": SITE_KOK_URL,
        "description": "Türkiye için canlı, doğrulanabilir maliyet endeksi.",
    }
    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            kurum,
            {
                "@type": "WebSite",
                "name": "Maliyeti Ne?",
                "url": SITE_KOK_URL + "/",
                "description": "Türkiye için canlı, doğrulanabilir maliyet endeksi.",
                "inLanguage": "tr-TR",
                "publisher": {"@id": f"{SITE_KOK_URL}/#kurum"},
            },
            {
                "@type": "ItemList",
                "name": "Maliyet endeksleri",
                "itemListElement": [
                    {
                        "@type": "ListItem", "position": i + 1,
                        "name": f"{o['ad']} maliyeti",
                        "url": f"{SITE_KOK_URL}/{o['yol']}/",
                    }
                    for i, o in enumerate(ozetler)
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": o["soru"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": (
                                f"Maliyeti Ne? verilerine göre {o['guncelleme_tarihi'] or bugun} "
                                f"itibarıyla {o['anasayfa_ifade']} "
                                f"{_para(o['toplam'])} tutuyor. "
                                + (
                                    f"Bunun {_para(o['gercek_toplam'])} tutarı "
                                    f"{o['gercek_kalem']} kalem için {o['site_sayisi']} "
                                    f"bağımsız kaynaktan derlenen güncel fiyatlara, "
                                    f"{_para(o['tahmini_toplam'])} tutarı ise henüz "
                                    f"kazınan bir kaynağı olmayan {o['tahmini_kalem']} "
                                    f"kalem için genel piyasa araştırmasına dayanır."
                                    if o["tahmini_kalem"] else
                                    f"Rakamın tamamı {o['gercek_kalem']} kalem için "
                                    f"{o['site_sayisi']} bağımsız kaynaktan derlenen "
                                    f"güncel fiyatlara dayanır."
                                )
                            ),
                        },
                    }
                    for o in ozetler
                ],
            },
        ],
    }

    menu = "".join(f'\n      <a href="/{o["yol"]}/">{o["ad"]}</a>' for o in ozetler)

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026'da Ne Kaça Mal Olur? | Maliyeti Ne?</title>
<meta name="description" content="Düğün ve ev kurma maliyeti: gerçek fiyat verisinden derlenmiş, aylık güncellenen, doğrulanabilir endeks. Kaynak, tarih ve örneklem her rakamın yanında.">
<link rel="canonical" href="{SITE_KOK_URL}/">
<link rel="stylesheet" href="/assets/css/style.css">
<meta property="og:title" content="2026'da ne kaça mal olur? | Maliyeti Ne?">
<meta property="og:description" content="{og_aciklama}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_KOK_URL}/">
<meta property="og:image" content="https://maliyetine.com.tr/assets/og-gorsel.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">Maliyeti <span>Ne?</span></a>
    <nav class="ust-menu">{menu}
    </nav>
  </div>
</header>

<main class="kapsayici">

  <span class="guncelleme-etiketi">Güncelleme: {tarih}</span>
  <h1>2026'da bir şey kaça mal olur?</h1>

  <div class="cevap-blok"{cevap_stil}>
    {cevap}
  </div>

  <section class="kalem-arama">
    <label for="kalem-ara">Bir ürünün fiyatını arayın</label>
    <input type="search" id="kalem-ara" autocomplete="off"
           placeholder="buzdolabı, gelinlik, okul çantası…"
           aria-describedby="arama-not">
    <ul id="arama-sonuc" hidden></ul>
    <p class="sonuc-alt-metin" id="arama-not">Yalnızca ölçtüğümüz kalemler
      çıkar — uydurma sonuç yok.</p>
  </section>

  <section class="hizli-hesap">
    <h2>Kendi hesabınızı yapın</h2>
    <p class="hizli-alt">Ölçtüğümüz güncel fiyatlarla, anında.</p>
    <div class="hizli-form">
      <div class="hizli-satir">
        <label for="hh-vertikal">Ne hesaplayalım?</label>
        <select id="hh-vertikal">{hizli_secenekler}</select>
      </div>
      <div class="hizli-satir" id="hh-olcek-satir">
        <label for="hh-olcek">Davetli sayısı</label>
        <input type="number" id="hh-olcek" min="0" step="1" value="150">
      </div>
      <div class="hizli-satir">
        <label>Bütçe</label>
        <div class="segment-secim" id="hh-segment">
          <label><input type="radio" name="hh-seg" value="ekonomik"> Ekonomik</label>
          <label><input type="radio" name="hh-seg" value="orta" checked> Orta</label>
          <label><input type="radio" name="hh-seg" value="luks"> Üst</label>
        </div>
      </div>
    </div>
    <div class="hizli-sonuc">
      <p class="hizli-sonuc-etiket">Tahmini toplam</p>
      <p class="hizli-sonuc-deger" id="hh-sonuc" aria-live="polite">—</p>
      <p class="hizli-sonuc-alt" id="hh-alt"></p>
    </div>
  </section>

{asistan_blok}
  <h2>Endeksler</h2>

  <div class="kart-grid">
{chr(10).join(kartlar)}
  </div>

  <h2>Rehberler</h2>
  <p class="kart-linkler">{rehber_linkleri}</p>

  <h2>Neden farklı?</h2>
  <p>
    Rakip fiyat listelerinin çoğu tek bir kaynağa dayanır — o sitenin
    kendi fiyat politikasını yansıtır, piyasayı değil. Maliyeti Ne? her
    kalem için mümkün olduğunca çok bağımsız kaynağı (fiyat karşılaştırma
    siteleri, marka mağazaları, sektör platformları) çapraz doğrulayıp
    birleştirir. Kaynaklar arası fark %30'u aşarsa bunu gizlemeyiz, uyarı
    olarak gösteririz. Henüz kazınan bir kaynağı olmayan kalemler
    <span class="tahmini-etiket">Tahmini</span> etiketiyle ayrılır ve
    toplamın ne kadarının gerçek veriden geldiği her zaman belirtilir.
  </p>
  <p>Yöntemin tamamı için
    {" ve ".join(f'<a href="/{o["yol"]}/metodoloji/">{o["ad"].lower()} metodolojisine</a>' for o in ozetler) if ozetler else "metodoloji sayfalarına"}
    bakabilirsiniz.</p>

{anasayfa_yazi}
</main>

<footer>
  <div class="kapsayici">
    <div>© 2026 Maliyeti Ne? · <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a> · <a href="/sss/">SSS</a> · <a href="/veri/">Veri</a></div>
    <nav>{menu}
    </nav>
  </div>
</footer>

{arama_js}{hizli_hesap_js}{asistan_js_kod}</body>
</html>
"""


def main():
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument("--vertikal", default="dugun", choices=sorted(VERTIKALLER))
    ayristirici.add_argument("--veri", type=Path, default=None)
    ayristirici.add_argument("--hedef", type=Path, default=None)
    args = ayristirici.parse_args()

    # Yeterli orneklemi olan kalemlere kendi sayfasini ac. sitemap ve ana
    # sayfa da bu genisletilmis listeyi gormeli, o yuzden en basta.
    eklenen = kalem_sayfalarini_genislet()
    if eklenen:
        print("Ek kalem sayfasi: " + ", ".join(f"{v} +{n}" for v, n in eklenen.items()))

    hedef = args.hedef or SITE_KOK / VERTIKALLER[args.vertikal]["yol"] / "index.html"
    html = sayfa_uret(args.vertikal, args.veri)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(html, encoding="utf-8")
    print(f"Sayfa uretildi: {hedef}")
    for silinen in bayat_kalem_sayfalarini_temizle(args.vertikal):
        print(f"Bayat kalem sayfasi SILINDI: {silinen}")
    for kalem_hedef in kalem_sayfalari_yaz(args.vertikal, args.veri):
        print(f"Kalem sayfasi uretildi: {kalem_hedef}")
    sss = SITE_KOK / "sss" / "index.html"
    sss.parent.mkdir(parents=True, exist_ok=True)
    sss.write_text(sss_sayfasi_uret(), encoding="utf-8")
    print(f"SSS sayfasi uretildi: {sss}")

    sitemap_hedef = SITE_KOK / "sitemap.xml"
    sitemap_hedef.write_text(sitemap_uret(), encoding="utf-8")
    print(f"Sitemap uretildi: {sitemap_hedef}")

    # Ana sayfa TUM vertikallerin verisini okur, yani hangi vertikalle
    # cagirilirsa cagirilsin ayni (dogru) sonucu uretir - sitemap ile ayni
    # desen. Boylece workflow'a ek bir adim eklemek gerekmiyor.
    anasayfa_hedef = SITE_KOK / "index.html"
    anasayfa_hedef.write_text(anasayfa_uret(), encoding="utf-8")
    print(f"Ana sayfa uretildi: {anasayfa_hedef}")


if __name__ == "__main__":
    main()
