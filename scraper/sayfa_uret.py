# -*- coding: utf-8 -*-
"""
maliyetine.com - Statik Sayfa Ureteci (v0.2)

/veri/{vertikal}.json'daki (agrega.py ciktisi) GERCEK sayilari statik
HTML'e gomer - GEO icin sart: AI botlarinin cogu (GPTBot vb.) JavaScript
calistirmaz, bu yuzden cevap bloğundaki rakam sayfa kaynagi HTML'inde
(fetch ile degil) bulunmak zorunda. Hesaplayici (JS, etkilesimli) bu
kisitlamaya tabi degil - ama endeks sayfasi (GEO'nun hedefi) build-time'da
uretilir.

v0.2: vertikal-agnostik hale getirildi (once sadece "dugun" hardcoded'di).
Yeni bir vertikal eklemek icin VERTIKAL_KONFIG'e bir girdi eklemek yeterli.

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

# NOT: assets/js/dugun-kalemler.js ile ayni liste (kasitli kucuk
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
    {"id": "salon", "ad": "Düğün Salonu", "birim": "kisi_basi"},
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
        "id": "taki-altin", "ad": "Takı ve Altın", "birim": "sabit",
        "tahmini": {"dusuk": 15000, "orta": 40000, "luks": 90000},
        "kaynak_notu": "Gram altın ~6.140 TL (24 Temmuz 2026) baz alınarak tipik hediye takı seti bütçesi.",
        "arastirma_tarihi": "2026-07-24",
    },
    {
        "id": "yemek-ikram", "ad": "Yemek / İkram (salona dahil değilse)", "birim": "kisi_basi",
        "tahmini": {"dusuk": 400, "orta": 700, "luks": 2000},
        "kaynak_notu": "Kişi başı düğün catering fiyat araştırması.",
        "arastirma_tarihi": "2026-07-24",
    },
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

# Ev kurma vertikali - tamamen urun bazli, "tahmini" kalem YOK (bkz.
# CLAUDE.md "EV KURMA VERTIKALI" bolumu - ChatGPT'nin uydurma rakamlari
# kasitli olarak KULLANILMADI, hepsi icin gercek Trendyol kaynagi
# arandi). Siralama assets/js/ev-kurma-kalemler.js ile ayni.
EV_KURMA_KALEMLERI = [
    {"id": "buzdolabi", "ad": "Buzdolabı", "birim": "sabit"},
    {"id": "camasir-makinesi", "ad": "Çamaşır Makinesi", "birim": "sabit"},
    {"id": "bulasik-makinesi", "ad": "Bulaşık Makinesi", "birim": "sabit"},
    {"id": "firin-ocak", "ad": "Fırın / Ocak (Ankastre Set)", "birim": "sabit"},
    {"id": "mikrodalga", "ad": "Mikrodalga Fırın", "birim": "sabit"},
    {"id": "davlumbaz", "ad": "Davlumbaz", "birim": "sabit"},
    {"id": "kurutma-makinesi", "ad": "Kurutma Makinesi", "birim": "sabit"},
    {"id": "klima", "ad": "Klima", "birim": "sabit"},
    {"id": "koltuk-takimi", "ad": "Koltuk Takımı", "birim": "sabit"},
    {"id": "yemek-masasi", "ad": "Yemek Masası Takımı", "birim": "sabit"},
    {"id": "yatak", "ad": "Çift Kişilik Yatak", "birim": "sabit"},
    {"id": "gardirop", "ad": "Gardırop", "birim": "sabit"},
    {"id": "tv-unitesi", "ad": "TV Ünitesi", "birim": "sabit"},
    {"id": "karyola", "ad": "Karyola", "birim": "sabit"},
    {"id": "komodin", "ad": "Komodin", "birim": "sabit"},
    {"id": "sifonyer", "ad": "Şifonyer", "birim": "sabit"},
    {"id": "boy-aynasi", "ad": "Boy Aynası", "birim": "sabit"},
    {"id": "sehpa", "ad": "Orta Sehpa", "birim": "sabit"},
    {"id": "konsol", "ad": "Konsol", "birim": "sabit"},
    {"id": "supurge", "ad": "Robot Süpürge", "birim": "sabit"},
    {"id": "dikey-supurge", "ad": "Dikey Süpürge", "birim": "sabit"},
    {"id": "airfryer", "ad": "Airfryer", "birim": "sabit"},
    {"id": "kahve-makinesi", "ad": "Kahve Makinesi", "birim": "sabit"},
    {"id": "su-isitici", "ad": "Su Isıtıcı (Kettle)", "birim": "sabit"},
    {"id": "tost-makinesi", "ad": "Tost Makinesi", "birim": "sabit"},
    {"id": "blender", "ad": "Blender", "birim": "sabit"},
    {"id": "mutfak-robotu", "ad": "Mutfak Robotu (Doğrayıcı)", "birim": "sabit"},
    {"id": "utu", "ad": "Ütü", "birim": "sabit"},
    {"id": "sac-kurutma-makinesi", "ad": "Saç Kurutma Makinesi", "birim": "sabit"},
    {"id": "televizyon", "ad": "Televizyon (4K)", "birim": "sabit"},
    {"id": "perde", "ad": "Perde", "birim": "sabit"},
    {"id": "aydinlatma", "ad": "Aydınlatma (Avize)", "birim": "sabit"},
    {"id": "nevresim-takimi", "ad": "Nevresim Takımı", "birim": "sabit"},
    {"id": "tencere-seti", "ad": "Tencere Seti", "birim": "sabit"},
    {"id": "tava-seti", "ad": "Tava Seti", "birim": "sabit"},
    {"id": "catal-kasik-bicak-takimi", "ad": "Çatal-Kaşık-Bıçak Takımı", "birim": "sabit"},
    {"id": "yemek-takimi", "ad": "Yemek Takımı", "birim": "sabit"},
    {"id": "kahvalti-takimi", "ad": "Kahvaltı Takımı", "birim": "sabit"},
    {"id": "bardak-takimi", "ad": "Bardak Takımı", "birim": "sabit"},
    {"id": "havlu-takimi", "ad": "Havlu Takımı", "birim": "sabit"},
    {"id": "bornoz", "ad": "Bornoz", "birim": "sabit"},
    {"id": "hali", "ad": "Halı", "birim": "sabit"},
]

EV_KURMA_KALEMLERI_TAHMINI: list[dict] = []

SEGMENT_ANAHTARI = {"ekonomik": "dusuk", "orta": "orta", "luks": "luks"}
SEGMENT_ETIKETLERI = {"dusuk": "Ekonomik", "orta": "Orta", "luks": "Lüks"}

VERTIKAL_KONFIG = {
    "dugun": {
        "kalemler": DUGUN_KALEMLERI,
        "kalemler_tahmini": DUGUN_KALEMLERI_TAHMINI,
        "meta_title": "2026'da Düğün Kaça Mal Olur? | Maliyetine.com.tr",
        "meta_aciklama": "Gerçek e-ticaret ve ilan verisinden derlenmiş, aylık güncellenen düğün maliyeti endeksi. Gelinlik, damatlık, alyans, salon ve daha fazlası — kaynak ve tarihiyle.",
        "canonical_yol": "/dugun/",
        "hesaplayici_yolu": "/dugun/hesaplayici/",
        "metodoloji_yolu": "/dugun/metodoloji/",
        "nav_ad": "Düğün",
        "h1": "2026'da İstanbul'da Düğün Kaça Mal Olur?",
        "soru": "2026'da İstanbul'da düğün kaça mal olur?",
        "dataset_adi": "Maliyetine Düğün Maliyeti Endeksi",
        "dataset_aciklama": "Türkiye'de düğün kalemlerinin gerçek e-ticaret ve ilan verisinden derlenen aylık fiyat endeksi.",
        "ornek_davetli_sayisi": 150,
        "ornek_segment": "orta",
        "konu_tam": "150 kişilik, orta segment bir düğünün",
        "konu_yalin": "150 kişilik, orta segment bir düğün",
        "tahmini_paragraf": (
            '<p><span class="tahmini-etiket">Tahmini</span> etiketli kalemler henüz '
            "kazınan bir kaynağa dayanmıyor — genel piyasa araştırmasından "
            "alınmıştır, diğerleri gerçek/tarihli kaynaklardan derlenir. "
            '<a href="/dugun/metodoloji/">Fark ne, bakın.</a></p>'
        ),
        "hesaplayici_link_metni": "Kendi davetli sayınız ve segmentinizle hesaplayın →",
    },
    "ev-kurma": {
        "kalemler": EV_KURMA_KALEMLERI,
        "kalemler_tahmini": EV_KURMA_KALEMLERI_TAHMINI,
        "meta_title": "2026'da Sıfırdan Ev Kurmak Kaça Mal Olur? | Maliyetine.com.tr",
        "meta_aciklama": "Gerçek e-ticaret verisinden derlenmiş, aylık güncellenen ev kurma maliyeti endeksi. Beyaz eşya, mobilya, küçük ev aletleri ve daha fazlası — kaynak ve tarihiyle.",
        "canonical_yol": "/ev-kurma/",
        "hesaplayici_yolu": "/ev-kurma/hesaplayici/",
        "metodoloji_yolu": "/ev-kurma/metodoloji/",
        "nav_ad": "Ev Kurma",
        "h1": "2026'da Sıfırdan Ev Kurmak Kaça Mal Olur?",
        "soru": "2026'da sıfırdan ev kurmak kaça mal olur?",
        "dataset_adi": "Maliyetine Ev Kurma Maliyeti Endeksi",
        "dataset_aciklama": "Türkiye'de sıfırdan ev kurarken alınan beyaz eşya, mobilya ve küçük ev aletlerinin gerçek e-ticaret verisinden derlenen aylık fiyat endeksi.",
        "ornek_davetli_sayisi": 1,
        "ornek_segment": "orta",
        "konu_tam": "sıfırdan, orta segment bir evi eşyalandırmanın (beyaz eşya + mobilya + küçük ev aletleri)",
        "konu_yalin": "Sıfırdan, orta segment bir evi eşyalandırmak",
        "tahmini_paragraf": (
            '<p class="uyari-kutu">Bu vertikaldeki tüm kalemler şu an <strong>tek kaynaktan</strong> '
            "(Trendyol) derleniyor — ÇOK KAYNAK KURALI henüz karşılanmıyor, ikinci "
            'bağımsız kaynak aranıyor. <a href="/ev-kurma/metodoloji/">Metodolojiye bakın.</a></p>'
        ),
        "hesaplayici_link_metni": "Kendi eşya listenizle ve segmentinizle hesaplayın →",
    },
}


def _para(n: int) -> str:
    return f"{n:,.0f}".replace(",", ".") + " TL"


def kalem_deger(kalem_verisi: dict | None, segment_anahtari: str) -> int | None:
    if not kalem_verisi:
        return None
    seg = kalem_verisi.get("segmentler", {}).get(segment_anahtari)
    if seg:
        return seg["medyan"]
    return kalem_verisi.get("genel_medyan")


def ornek_toplam_hesapla(
    kalemler: dict,
    davetli_sayisi: int,
    segment: str,
    kalem_tanimlari: list[dict] = DUGUN_KALEMLERI,
    kalem_tanimlari_tahmini: list[dict] = DUGUN_KALEMLERI_TAHMINI,
) -> tuple[int, list[dict]]:
    seg_anahtari = SEGMENT_ANAHTARI[segment]
    toplam = 0
    detaylar = []
    for tanim in kalem_tanimlari:
        veri = kalemler.get(tanim["id"])
        deger = kalem_deger(veri, seg_anahtari)
        if deger is None:
            detaylar.append({**tanim, "veri_var": False, "tahmini_mi": False})
            continue
        carpan = davetli_sayisi if tanim["birim"] == "kisi_basi" else 1
        satir_toplam = round(deger * carpan)
        toplam += satir_toplam
        detaylar.append({**tanim, "veri_var": True, "tahmini_mi": False, "birim_fiyat": deger, "satir_toplam": satir_toplam})

    for tanim in kalem_tanimlari_tahmini:
        deger = tanim["tahmini"][seg_anahtari]
        carpan = davetli_sayisi if tanim["birim"] == "kisi_basi" else 1
        satir_toplam = round(deger * carpan)
        toplam += satir_toplam
        detaylar.append({
            "id": tanim["id"], "ad": tanim["ad"], "birim": tanim["birim"],
            "veri_var": True, "tahmini_mi": True,
            "birim_fiyat": deger, "satir_toplam": satir_toplam,
            "kaynak_notu": tanim["kaynak_notu"], "arastirma_tarihi": tanim["arastirma_tarihi"],
        })
    return toplam, detaylar


def _kalem_satirlari_html(
    kalemler: dict,
    kalem_tanimlari: list[dict] = DUGUN_KALEMLERI,
    kalem_tanimlari_tahmini: list[dict] = DUGUN_KALEMLERI_TAHMINI,
) -> str:
    satirlar = []
    for tanim in kalem_tanimlari:
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
        satirlar.append(
            f'<tr><td>{tanim["ad"]}</td>'
            f'<td class="sayi">{_para(degerler["dusuk"]) if degerler["dusuk"] else "—"}</td>'
            f'<td class="sayi">{_para(degerler["orta"]) if degerler["orta"] else "—"}</td>'
            f'<td class="sayi">{_para(degerler["luks"]) if degerler["luks"] else "—"}</td>'
            f'<td class="sayi">{veri.get("kaynak_sayisi", 0)}</td></tr>'
        )
    for tanim in kalem_tanimlari_tahmini:
        t = tanim["tahmini"]
        satirlar.append(
            f'<tr><td>{tanim["ad"]} <span class="tahmini-etiket" title="{tanim["kaynak_notu"]}">Tahmini</span></td>'
            f'<td class="sayi">{_para(t["dusuk"])}</td>'
            f'<td class="sayi">{_para(t["orta"])}</td>'
            f'<td class="sayi">{_para(t["luks"])}</td>'
            f'<td class="sayi">Tahmini</td></tr>'
        )
    return "\n".join(satirlar)


def _capraz_dogrulama_uyarilari_html(
    kalemler: dict,
    kalem_tanimlari: list[dict] = DUGUN_KALEMLERI,
    metodoloji_yolu: str = "/dugun/metodoloji/",
) -> str:
    uyarilar = []
    ad_haritasi = {t["id"]: t["ad"] for t in kalem_tanimlari}
    for kalem_id, veri in kalemler.items():
        uyari = veri.get("capraz_dogrulama_uyarisi")
        if uyari:
            ad = ad_haritasi.get(kalem_id, kalem_id)
            uyarilar.append(
                f"<li><strong>{ad}:</strong> kaynaklar arası fark %{uyari['fark_yuzdesi']:.0f} "
                "— farklı segment/marka aralığını yansıtıyor olabilir, "
                f'<a href="{metodoloji_yolu}">metodolojiye bakın</a>.</li>'
            )
    if not uyarilar:
        return ""
    return (
        '<div class="uyari-kutu"><strong>Çapraz doğrulama notu:</strong>'
        "<ul>" + "\n".join(uyarilar) + "</ul></div>"
    )


def sayfa_uret(veri_dosyasi: Path, vertikal: str = "dugun") -> str:
    konfig = VERTIKAL_KONFIG[vertikal]
    kalem_tanimlari = konfig["kalemler"]
    kalem_tanimlari_tahmini = konfig["kalemler_tahmini"]

    if veri_dosyasi.exists():
        agregali = json.loads(veri_dosyasi.read_text(encoding="utf-8"))
    else:
        agregali = {"vertikal": vertikal, "guncelleme_tarihi": None, "kalemler": {}}

    kalemler = agregali.get("kalemler", {})
    guncelleme_tarihi = agregali.get("guncelleme_tarihi")
    bugun = date.today().isoformat()

    ornek_davetli_sayisi = konfig["ornek_davetli_sayisi"]
    ornek_toplam, ornek_detaylar = ornek_toplam_hesapla(
        kalemler, ornek_davetli_sayisi, konfig["ornek_segment"], kalem_tanimlari, kalem_tanimlari_tahmini
    )
    kapsanan_detaylar = [d for d in ornek_detaylar if d["veri_var"]]
    gercek_detaylar = [d for d in kapsanan_detaylar if not d["tahmini_mi"]]
    tahmini_detaylar = [d for d in kapsanan_detaylar if d["tahmini_mi"]]
    gercek_toplam = sum(d["satir_toplam"] for d in gercek_detaylar)
    tahmini_toplam = sum(d["satir_toplam"] for d in tahmini_detaylar)

    # "kalemler" dolu ama HEPSI genel_medyan=null (ör. o ay tum kaynaklar
    # 0 urun dondu) olabilir - bu durumda "0 TL" gibi yaniltici bir cevap
    # UYDURMAMAK icin gercek kapsanan kalem olup olmadigina bakiliyor,
    # sadece kalemler sozlugunun bos olmadigina degil. Tahmini kalemler
    # varsa her zaman deger urettigi icin bu ayrim "gercek kaynak var mi"
    # sorusuna indirgeniyor - cevap metni buna gore GERCEK ile TAHMINI
    # kismi ACIKCA ayirir, karistirmaz.
    if gercek_detaylar:
        kapsanan_idler = {d["id"] for d in gercek_detaylar}
        kaynak_sayisi_toplam = sum(
            v.get("kaynak_sayisi", 0) for k, v in kalemler.items() if k in kapsanan_idler
        )
        if tahmini_detaylar:
            govde = (
                f"Bunun {_para(gercek_toplam)} tutarı {len(gercek_detaylar)} kalem için "
                f"{kaynak_sayisi_toplam} bağımsız kaynaktan derlenen güncel fiyatlara, "
                f"{_para(tahmini_toplam)} tutarı ise henüz kazınan bir kaynağı olmayan "
                f"{len(tahmini_detaylar)} kalem için genel piyasa araştırmasına dayanır."
            )
        else:
            govde = (
                f"Bu rakamın tamamı {len(gercek_detaylar)} kalem için "
                f"{kaynak_sayisi_toplam} bağımsız kaynaktan derlenen güncel fiyatlara dayanır."
            )
        cevap_metni = (
            f"Maliyetine'ye göre {guncelleme_tarihi or bugun} itibarıyla "
            f"{konfig['konu_tam']} <strong>{_para(ornek_toplam)}</strong> tutması bekleniyor. {govde}"
        )
        cevap_disable = ""
    elif tahmini_detaylar:
        cevap_metni = (
            f"{konfig['konu_yalin']} için kalem kalem toplam yaklaşık <strong>{_para(ornek_toplam)}</strong> "
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
                    "name": konfig["soru"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": cevap_metni.replace("<strong>", "").replace("</strong>", ""),
                    },
                }],
            },
            {
                "@type": "Dataset",
                "name": konfig["dataset_adi"],
                "description": konfig["dataset_aciklama"],
                "dateModified": guncelleme_tarihi or bugun,
                "creator": {"@type": "Organization", "name": "Maliyetine.com.tr"},
            },
        ],
    }

    tahmini_paragraf = konfig.get("tahmini_paragraf", "") if kalem_tanimlari_tahmini or vertikal == "ev-kurma" else ""

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{konfig["meta_title"]}</title>
<meta name="description" content="{konfig["meta_aciklama"]}">
<link rel="canonical" href="https://maliyetine.com.tr{konfig["canonical_yol"]}">
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
      <a href="{konfig["hesaplayici_yolu"]}">Hesaplayıcı</a>
      <a href="{konfig["metodoloji_yolu"]}">Metodoloji</a>
    </nav>
  </div>
</header>

<main class="kapsayici">

  {guncelleme_etiketi}
  <h1>{konfig["h1"]}</h1>

  <div class="cevap-blok"{cevap_disable}>
    {cevap_metni}
  </div>

  <p><a href="{konfig["hesaplayici_yolu"]}">{konfig["hesaplayici_link_metni"]}</a></p>

  <h2>Kalem kalem fiyatlar</h2>
  {tahmini_paragraf}
  <table>
    <thead>
      <tr><th>Kalem</th><th class="sayi">Ekonomik</th><th class="sayi">Orta</th><th class="sayi">Lüks</th><th class="sayi">Kaynak</th></tr>
    </thead>
    <tbody>
      {_kalem_satirlari_html(kalemler, kalem_tanimlari, kalem_tanimlari_tahmini)}
    </tbody>
  </table>

  {_capraz_dogrulama_uyarilari_html(kalemler, kalem_tanimlari, konfig["metodoloji_yolu"])}

  <p>Yöntem, kaynaklar ve örneklem büyüklükleri için
    <a href="{konfig["metodoloji_yolu"]}">metodoloji sayfasına</a> bakın.</p>

</main>

<footer>
  <div class="kapsayici">
    <div>© 2026 Maliyetine.com.tr</div>
    <nav>
      <a href="{konfig["hesaplayici_yolu"]}">Hesaplayıcı</a>
      <a href="{konfig["metodoloji_yolu"]}">Metodoloji</a>
    </nav>
  </div>
</footer>

</body>
</html>
"""


def main():
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument("--vertikal", default="dugun", choices=sorted(VERTIKAL_KONFIG))
    ayristirici.add_argument("--veri", type=Path, default=None)
    ayristirici.add_argument("--hedef", type=Path, default=None)
    args = ayristirici.parse_args()

    veri_dosyasi = args.veri or (SITE_KOK / "veri" / f"{args.vertikal}.json")
    hedef = args.hedef or (SITE_KOK / args.vertikal / "index.html")

    html = sayfa_uret(veri_dosyasi, args.vertikal)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(html, encoding="utf-8")
    print(f"[{args.vertikal}] sayfa uretildi: {hedef}")


if __name__ == "__main__":
    main()
