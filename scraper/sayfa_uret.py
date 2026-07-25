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
        "hesaplayici_daveti": "Kendi davetli sayınız ve segmentinizle hesaplayın →",
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
        "hesaplayici_daveti": "Kendi eşya listenizle ve segmentinizle hesaplayın →",
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
    """Kac AYRI SITE'den veri geldigini doner.

    kalem basina "kaynak_sayisi"nin toplami DEGIL: ayni site (or. Trendyol)
    20 kalemi de beslediginde bu toplam 20 cikar ve okuyucuya 20 farkli
    kaynak izlenimi verir. COK KAYNAK KURALI'nin olctugu sey site
    cesitliligi, o yuzden benzersiz site sayilir.
    """
    siteler = set()
    for kalem_id in kalem_idleri:
        for kaynak in kalemler.get(kalem_id, {}).get("kaynaklar", []):
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
        degerler = {
            seg: kalem_deger(veri, seg) for seg in ("dusuk", "orta", "luks")
        }
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

    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "FAQPage",
                "mainEntity": [{
                    "@type": "Question",
                    "name": conf["soru"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": cevap_metni.replace("<strong>", "").replace("</strong>", ""),
                    },
                }],
            },
            {
                "@type": "Dataset",
                "name": conf["dataset_ad"],
                "description": conf["dataset_aciklama"],
                "dateModified": guncelleme_tarihi or bugun,
                "creator": {"@type": "Organization", "name": "Maliyetine.com.tr"},
            },
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


if __name__ == "__main__":
    main()
