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
        "id": "fotografci", "ad": "Fotoğraf ve Video", "birim": "sabit",
        "tahmini": {"dusuk": 20000, "orta": 45000, "luks": 100000},
        "kaynak_notu": "Düğün fotoğraf/video paket fiyat araştırması.",
        "arastirma_tarihi": "2026-07-24",
    },
    {
        "id": "orkestra-dj", "ad": "Orkestra / DJ", "birim": "sabit",
        "tahmini": {"dusuk": 5000, "orta": 25000, "luks": 80000},
        "kaynak_notu": "Düğün orkestra/DJ kiralama fiyat araştırması.",
        "arastirma_tarihi": "2026-07-24",
    },
    {
        "id": "gelin-arabasi", "ad": "Gelin Arabası", "birim": "sabit",
        "tahmini": {"dusuk": 800, "orta": 3000, "luks": 8000},
        "kaynak_notu": "Gelin arabası kiralama fiyat araştırması.",
        "arastirma_tarihi": "2026-07-24",
    },
    {
        "id": "kuafor-makyaj", "ad": "Kuaför ve Makyaj", "birim": "sabit",
        "tahmini": {"dusuk": 1000, "orta": 5000, "luks": 15000},
        "kaynak_notu": "Gelin saçı ve makyajı fiyat araştırması.",
        "arastirma_tarihi": "2026-07-24",
    },
    {
        "id": "organizasyon", "ad": "Organizasyon / Süsleme", "birim": "sabit",
        "tahmini": {"dusuk": 15000, "orta": 40000, "luks": 150000},
        "kaynak_notu": "Düğün organizasyon/dekorasyon fiyat araştırması.",
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

VERTIKALLER = {
    "dugun": {
        "ad": "Düğün",
        "yol": "dugun",
        "kalemler": DUGUN_KALEMLERI,
        "tahmini_kalemler": DUGUN_KALEMLERI_TAHMINI,
        "baslik": "2026'da İstanbul'da Düğün Kaça Mal Olur?",
        "soru": "2026'da İstanbul'da düğün kaça mal olur?",
        "sayfa_basligi": "2026'da Düğün Kaça Mal Olur? | Maliyetine.com.tr",
        "meta_aciklama": (
            "Gerçek e-ticaret ve ilan verisinden derlenmiş, aylık güncellenen düğün "
            "maliyeti endeksi. Gelinlik, damatlık, alyans, salon ve daha fazlası — "
            "kaynak ve tarihiyle."
        ),
        "dataset_ad": "Maliyetine Düğün Maliyeti Endeksi",
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
            "Ekonomik segment düşük fiyat bandını, orta segment piyasadaki medyan "
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
                "baslik": "2026'da Düğün Salonu Kişi Başı Fiyatları Ne Kadar?",
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
        "sayfa_basligi": "2026'da Ev Kurmak Kaça Mal Olur? | Maliyetine.com.tr",
        "meta_aciklama": (
            "Gerçek e-ticaret verisinden derlenmiş, aylık güncellenen ev kurma "
            "maliyeti endeksi. Beyaz eşya, mobilya, mutfak, tekstil — 42 kalem, "
            "kaynak ve tarihiyle."
        ),
        "dataset_ad": "Maliyetine Ev Kurma Maliyeti Endeksi",
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
            "ev kurma bütçesinde beklenen medyan fiyatı, lüks segment ise daha yüksek "
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
}

SEGMENT_ANAHTARI = {"ekonomik": "dusuk", "orta": "orta", "luks": "luks"}
SEGMENT_ETIKETLERI = {"dusuk": "Ekonomik", "orta": "Orta", "luks": "Lüks"}

ORNEK_SEGMENT = "orta"


def vertikal_conf(vertikal: str) -> dict:
    if vertikal not in VERTIKALLER:
        raise ValueError(
            f"Bilinmeyen vertikal: {vertikal}. Tanimlilar: {', '.join(VERTIKALLER)}"
        )
    return VERTIKALLER[vertikal]


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
    segmentler = (kalem_verisi or {}).get("segmentler") or {}
    return {
        seg: (segmentler.get(seg) or {}).get("medyan")
        for seg in ("dusuk", "orta", "luks")
    }


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
                    f"Maliyetine'ye göre {tanim['ad']}{birim} "
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


def _tek_kaynak_uyarisi_html(conf: dict, siteler: set[str]) -> str:
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
            f"Maliyetine'ye göre {guncelleme_tarihi or bugun} itibarıyla "
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

    guncelleme_etiketi = (
        f'<span class="guncelleme-etiketi">Güncelleme: {guncelleme_tarihi}</span>'
        if guncelleme_tarihi
        else '<span class="guncelleme-etiketi">Henüz güncellenmedi</span>'
    )

    sayfa_url = f"{SITE_KOK_URL}/{yol}/"
    kurum = {
        "@type": "Organization",
        "@id": f"{SITE_KOK_URL}/#kurum",
        "name": "Maliyetine.com.tr",
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
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">maliyet<span>ine</span>.com.tr</a>
    <nav class="ust-menu">
      <a href="/{yol}/hesaplayici/">Hesaplayıcı</a>
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

  <p><a href="/{yol}/hesaplayici/">{conf["hesaplayici_daveti"]}</a></p>

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
    <div>© 2026 Maliyetine.com.tr</div>
    <nav>
      <a href="/{yol}/hesaplayici/">Hesaplayıcı</a>
      <a href="/{yol}/metodoloji/">Metodoloji</a>
    </nav>
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
        "<table>\n<thead><tr><th>Segment</th><th class=\"sayi\">Medyan fiyat</th></tr></thead>\n"
        "<tbody>\n" + "\n".join(satirlar) + "\n</tbody>\n</table>"
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
    birim = " kişi başı" if tanim["birim"] == "kisi_basi" else ""

    if orta:
        cevap = (
            f"Maliyetine'ye göre {guncelleme_tarihi} itibarıyla {tanim['ad']} "
            f"orta segment medyan fiyatı {birim} <strong>{_para(orta)}</strong>. "
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

    kurum = {
        "@type": "Organization",
        "@id": f"{SITE_KOK_URL}/#kurum",
        "name": "Maliyetine.com.tr",
        "url": SITE_KOK_URL,
        "description": "Türkiye için canlı, doğrulanabilir maliyet endeksi.",
    }
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
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": sayfa["soru"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": cevap.replace("<strong>", "").replace("</strong>", ""),
                        },
                    },
                    {
                        "@type": "Question",
                        "name": "Bu fiyatlar nasıl hesaplandı?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": (
                                "Fiyatlar gerçek kaynaklardan aylık olarak derlenir; "
                                "ürünler düşük, orta ve lüks segmentlere ayrılır."
                            ),
                        },
                    },
                ],
            },
        ],
    }

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{sayfa["baslik"]} | Maliyetine.com.tr</title>
<meta name="description" content="{sayfa["soru"].capitalize()} Güncel fiyat aralığı, segmentler, kaynak ve derleme tarihiyle.">
<link rel="canonical" href="{sayfa_url}">
<link rel="stylesheet" href="/assets/css/style.css">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">maliyet<span>ine</span>.com.tr</a>
    <nav class="ust-menu">
      <a href="/{conf["yol"]}/">Endeks</a>
      <a href="/{conf["yol"]}/hesaplayici/">Hesaplayıcı</a>
      <a href="/{conf["yol"]}/metodoloji/">Metodoloji</a>
    </nav>
  </div>
</header>

<main class="kapsayici">
  <span class="guncelleme-etiketi">Güncelleme: {guncelleme_tarihi}</span>
  <h1>{sayfa["baslik"]}</h1>

  <div class="cevap-blok">
    {cevap}
  </div>

  <section class="icerik-bolumu">
    <h2>Fiyat aralığı</h2>
    <p>{sayfa["aciklama"]}</p>
    {_segment_tablosu_html(veri)}
  </section>

  <section class="icerik-bolumu">
    <h2>Bu fiyata ne dahil?</h2>
    <p>Bu sayfa yalnızca <strong>{tanim["ad"]}</strong> kalemini ölçer. Tüm bütçeyi görmek için
      <a href="/{conf["yol"]}/">{conf["ad"]} maliyeti endeksine</a> veya
      <a href="/{conf["yol"]}/hesaplayici/">hesaplayıcıya</a> gidin.</p>
  </section>

  <section class="icerik-bolumu">
    <h2>Kaynaklar ve yöntem</h2>
    {_kaynak_ozeti_html(veri)}
    <p>Segment tanımı, aykırı değer kontrolü ve kaynak ayrımı için
      <a href="/{conf["yol"]}/metodoloji/">metodoloji sayfasına</a> bakın.</p>
  </section>
</main>

<footer>
  <div class="kapsayici">
    <div>© 2026 Maliyetine.com.tr</div>
    <nav>
      <a href="/{conf["yol"]}/">{conf["ad"]} endeksi</a>
      <a href="/{conf["yol"]}/hesaplayici/">Hesaplayıcı</a>
      <a href="/{conf["yol"]}/metodoloji/">Metodoloji</a>
    </nav>
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


def sitemap_uret() -> str:
    url_kayitlari = [
        ("/", "monthly", "1.0"),
    ]
    for conf in VERTIKALLER.values():
        yol = conf["yol"]
        url_kayitlari.extend([
            (f"/{yol}/", "monthly", "0.9"),
            (f"/{yol}/hesaplayici/", "monthly", "0.8"),
            (f"/{yol}/metodoloji/", "yearly", "0.5"),
        ])
        for sayfa in conf.get("kalem_sayfalari", []):
            url_kayitlari.append((f"/{yol}/{sayfa['slug']}/", "monthly", "0.7"))

    satirlar = ['<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for yol, frekans, oncelik in url_kayitlari:
        satirlar.extend([
            "  <url>",
            f"    <loc>{SITE_KOK_URL}{yol}</loc>",
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
                "kisa_ad": next(
                    (t["ad"].split("—")[0].strip() for t in conf["kalemler"]
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

    if ozetler:
        cumleler = [
            f"{o['anasayfa_ifade']} <strong>{_para(o['toplam'])}</strong>"
            for o in ozetler
        ]
        tarih = max(o["guncelleme_tarihi"] or bugun for o in ozetler)
        cevap = (
            f"Maliyetine'ye göre {tarih} itibarıyla "
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
        alt_linkler = "".join(
            f'<a href="/{o["yol"]}/{k["slug"]}/">{k["kisa_ad"]}</a>'
            for k in o["kalem_sayfalari"]
        )
        kartlar.append(f"""    <div class="vertikal-kart kart">
      <h3><a href="/{o['yol']}/">{o['ad']} maliyeti</a></h3>
      <p class="kart-rakam">{_para(o['toplam'])}</p>
      <p class="kart-alt">{o['kart_alt']} · {o['gercek_kalem']} kalem
        {o['site_sayisi']} bağımsız kaynaktan{", " + str(o['tahmini_kalem']) + " kalem tahmini" if o['tahmini_kalem'] else " (tamamı gerçek kaynaklı)"}</p>
      <p class="kart-linkler">{alt_linkler}</p>
    </div>""")

    for ad, aciklama in (("Ev tadilatı", "Hazırlanıyor."), ("0 km araç", "Hazırlanıyor.")):
        kartlar.append(f"""    <div class="kart">
      <h3>{ad} maliyeti <span class="yakinda-etiket">Yakında</span></h3>
      <p>{aciklama}</p>
    </div>""")

    kurum = {
        "@type": "Organization",
        "@id": f"{SITE_KOK_URL}/#kurum",
        "name": "Maliyetine.com.tr",
        "url": SITE_KOK_URL,
        "description": "Türkiye için canlı, doğrulanabilir maliyet endeksi.",
    }
    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            kurum,
            {
                "@type": "WebSite",
                "name": "Maliyetine.com.tr",
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
                                f"Maliyetine'ye göre {o['guncelleme_tarihi'] or bugun} "
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
<title>2026'da Ne Kaça Mal Olur? Düğün, Ev Kurma | Maliyetine.com.tr</title>
<meta name="description" content="Düğün ve ev kurma maliyeti: gerçek fiyat verisinden derlenmiş, aylık güncellenen, doğrulanabilir endeks. Kaynak, tarih ve örneklem her rakamın yanında.">
<link rel="canonical" href="{SITE_KOK_URL}/">
<link rel="stylesheet" href="/assets/css/style.css">
<meta property="og:title" content="2026'da ne kaça mal olur? | Maliyetine.com.tr">
<meta property="og:description" content="Gerçek fiyat verisinden derlenmiş, doğrulanabilir maliyet endeksi.">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_KOK_URL}/">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">maliyet<span>ine</span>.com.tr</a>
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

  <h2>Endeksler</h2>

  <div class="kart-grid">
{chr(10).join(kartlar)}
  </div>

  <h2>Neden farklı?</h2>
  <p>
    Rakip fiyat listelerinin çoğu tek bir kaynağa dayanır — o sitenin
    kendi fiyat politikasını yansıtır, piyasayı değil. Maliyetine her
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

</main>

<footer>
  <div class="kapsayici">
    <div>© 2026 Maliyetine.com.tr</div>
    <nav>{menu}
    </nav>
  </div>
</footer>

</body>
</html>
"""


def main():
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument("--vertikal", default="dugun", choices=sorted(VERTIKALLER))
    ayristirici.add_argument("--veri", type=Path, default=None)
    ayristirici.add_argument("--hedef", type=Path, default=None)
    args = ayristirici.parse_args()

    hedef = args.hedef or SITE_KOK / VERTIKALLER[args.vertikal]["yol"] / "index.html"
    html = sayfa_uret(args.vertikal, args.veri)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(html, encoding="utf-8")
    print(f"Sayfa uretildi: {hedef}")
    for kalem_hedef in kalem_sayfalari_yaz(args.vertikal, args.veri):
        print(f"Kalem sayfasi uretildi: {kalem_hedef}")
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
