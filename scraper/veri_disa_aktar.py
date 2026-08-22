# -*- coding: utf-8 -*-
"""
Maliyeti Ne? - Veri disa aktarim (CSV) ve veri merkezi sayfasi

NEDEN VAR: sayfalarda "veriler herkese acik, kullanabilirsiniz" yaziyordu
ama INDIRILEBILIR DOSYA YOKTU - yalnizca sitenin kendi JSON'u vardi ve o
da ic kullanim semasinda. Gazeteci, arastirmaci ya da blogcu alintilamak
istediginde elle kopyalamak zorunda kaliyordu.

Alintilanabilirlik bu projenin is modelinin merkezinde: dogal baglantinin
en guclu kaynagi "su siteden veri aldik" cumlesidir. CSV, Excel'de tek
tikla acilan ve herkesin bildigi format.

Uretilenler:
  /veri/csv/{vertikal}-{tarih}.csv   arsiv (tarihli, degismez)
  /veri/csv/{vertikal}.csv           en guncel (sabit URL - linklenebilir)
  /veri/csv/tum-kalemler.csv         tum vertikaller tek dosyada
  /veri/ sayfasi                     indirme merkezi + DataCatalog schema

TASARIM: tarihli VE sabit URL birlikte. Sabit URL linklenebilir olsun
diye; tarihli surum ise "2026 Temmuz'da soyleydi" diyen bir yaziyi
dogrulayabilmek icin - kaynak degistiginde eski link olu baglantiya
donusmesin.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from io import StringIO
from pathlib import Path

from envanter import envanter_ozeti
import sayfa_uret as su
from veri_surumu import manifest_yaz

SITE_KOK = su.SITE_KOK
CSV_KOK = SITE_KOK / "veri" / "csv"

BASLIKLAR = [
    "vertikal", "kalem_id", "kalem_adi", "grup", "birim", "olcum_turu",
    "ekonomik_tl", "orta_tl", "ust_tl",
    "en_dusuk_tl", "en_yuksek_tl",
    "tl_kg", "kg_urun_sayisi", "tl_litre", "litre_urun_sayisi",
    "tl_adet", "adet_urun_sayisi",
    "urun_sayisi", "kaynak_sayisi", "kaynaklar", "olcum_tarihi",
]


def _satirlar(vertikal: str, veri: dict) -> list[list]:
    conf = su.VERTIKALLER[vertikal]
    tanimlar = {t["id"]: t for t in conf["kalemler"]}
    tarih = veri.get("guncelleme_tarihi", "")
    cikti = []
    for kalem_id, k in (veri.get("kalemler") or {}).items():
        t = tanimlar.get(kalem_id) or {}
        seg = k.get("segmentler") or {}

        def s(ad, alan="medyan"):
            return (seg.get(ad) or {}).get(alan) or ""

        kaynaklar = sorted({
            x.get("site") for x in (k.get("kaynaklar") or [])
            if (x.get("toplam_urun") or 0) > 0 and x.get("site")
        })
        birim_fiyatlari = k.get("birim_fiyatlari") or {}

        def bf(birim, alan):
            return (birim_fiyatlari.get(birim) or {}).get(alan) or ""

        cikti.append([
            vertikal, kalem_id, t.get("ad", kalem_id), t.get("grup", ""),
            t.get("birim", ""),
            k.get("olcum_turu") or t.get("olcum_turu") or (
                "kisi_basi_fiyat" if t.get("birim") == "kisi_basi" else "kalem_fiyati"
            ),
            s("dusuk"), s("orta"), s("luks"),
            s("dusuk", "min") or "", s("luks", "max") or "",
            bf("kg", "genel_medyan"), bf("kg", "eslesen_urun"),
            bf("litre", "genel_medyan"), bf("litre", "eslesen_urun"),
            bf("adet", "genel_medyan"), bf("adet", "eslesen_urun"),
            k.get("toplam_urun") or "", len(kaynaklar),
            "; ".join(kaynaklar), k.get("guncelleme_tarihi") or tarih,
        ])
    cikti.sort(key=lambda r: (r[3] or "zzz", r[2]))
    return cikti


def csv_metni(satirlar: list[list]) -> str:
    """UTF-8 BOM'lu CSV.

    BOM SART: Excel BOM'suz UTF-8 CSV'yi Windows-1254 sanip Turkce
    karakterleri bozuyor ("Buzdolabı" -> "BuzdolabÄ±"). Dosyayi acan
    kisinin ilk izlenimi bozuk metin olmamali.
    """
    tampon = StringIO()
    yazici = csv.writer(tampon, lineterminator="\n")
    yazici.writerow(BASLIKLAR)
    yazici.writerows(satirlar)
    return "﻿" + tampon.getvalue()


def disa_aktar(veri_kok: Path | None = None, cikti_kok: Path | None = None) -> dict:
    kok = veri_kok or SITE_KOK / "veri"
    hedef = cikti_kok or CSV_KOK
    hedef.mkdir(parents=True, exist_ok=True)

    tumu: list[list] = []
    ozet: dict[str, dict] = {}
    for vertikal in su.VERTIKALLER:
        dosya = kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        try:
            veri = json.loads(dosya.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        satirlar = _satirlar(vertikal, veri)
        if not satirlar:
            continue
        tumu.extend(satirlar)
        metin = csv_metni(satirlar)
        tarih = veri.get("guncelleme_tarihi") or date.today().isoformat()
        (hedef / f"{vertikal}.csv").write_text(metin, encoding="utf-8")
        arsiv = hedef / f"{vertikal}-{tarih}.csv"
        # Gecmis gunlerin tarihli CSV'si degismez. Ayni gun icinde hedefli
        # yeniden olcum yapilabilir ve gun-granuler snapshot son saglikli
        # kosuyla yenilenir; bugunun arsivi de bu kanonik durumla birlikte
        # guncellenir. Gun kapandiktan sonra dosya sabitlenir.
        if not arsiv.exists() or tarih == date.today().isoformat():
            arsiv.write_text(metin, encoding="utf-8")
        ozet[vertikal] = {
            "kalem": len(satirlar),
            "cok_kaynakli": sum(r[BASLIKLAR.index("kaynak_sayisi")] >= 2 for r in satirlar),
            "tek_kaynakli": sum(r[BASLIKLAR.index("kaynak_sayisi")] == 1 for r in satirlar),
            "liste_fiyati": bool(su.VERTIKALLER[vertikal].get("liste_fiyati")),
            "tarih": tarih,
            "dosya": f"/veri/csv/{vertikal}.csv",
            "arsiv": f"/veri/csv/{vertikal}-{tarih}.csv",
        }
    if tumu:
        (hedef / "tum-kalemler.csv").write_text(csv_metni(tumu), encoding="utf-8")
    return ozet


def _fiyat_araligi(kalem: dict) -> tuple[int | float | None, int | float | None]:
    segmentler = (kalem or {}).get("segmentler") or {}
    altlar = [s.get("min") for s in segmentler.values() if s.get("min") is not None]
    ustler = [s.get("max") for s in segmentler.values() if s.get("max") is not None]
    return (min(altlar) if altlar else None, max(ustler) if ustler else None)


def _aktif_kaynaklar(kalem: dict) -> list[str]:
    return sorted({
        k.get("site") for k in (kalem.get("kaynaklar") or [])
        if k.get("site") and (k.get("toplam_urun") or 0) > 0
    })


def fiyat_gozlem_sayisi(veri_kok: Path | None = None) -> int:
    dosya = (veri_kok or SITE_KOK / "veri") / "fiyat-gozlemleri.json"
    if not dosya.exists():
        return 0
    try:
        return int(json.loads(dosya.read_text(encoding="utf-8")).get("gozlem_sayfasi") or 0)
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return 0


def cevap_envanteri(
    veri_kok: Path | None = None, dataset_surumu: str | None = None
) -> dict:
    """AI aramasi icin 121 seriyi dogrudan, tarihli cevaplara donusturur."""
    kok = veri_kok or SITE_KOK / "veri"
    # Kalem sayfalarinin buyuk bolumu JSON'daki ornekleme gore build aninda
    # acilir. Envanter de ayni kanonik secimi kullanmali; yalnizca config'te
    # elle duran vitrin sayfalarini okursa 121 serinin 21'ini gorur.
    su.kalem_sayfalarini_genislet(kok)
    cevaplar = []
    for vertikal, conf in su.VERTIKALLER.items():
        dosya = kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        veri = json.loads(dosya.read_text(encoding="utf-8"))
        kalemler = veri.get("kalemler") or {}
        tanimlar = {k["id"]: k for k in conf["kalemler"]}
        sayfalar = {k["id"]: k for k in conf.get("kalem_sayfalari", [])}
        for kalem_id, kalem in kalemler.items():
            tanim = tanimlar.get(kalem_id)
            sayfa = sayfalar.get(kalem_id)
            if not tanim:
                continue
            # Orneklemi HTML sayfasi acma esiginin altindaki seri de gercek
            # veridir. GEO envanterinde saklamiyoruz; ilgili endeks sayfasina
            # bagliyoruz. Boylece kapsam tam kalirken ince SEO sayfasi acilmaz.
            soru = (
                sayfa.get("soru") if sayfa
                else f"2026'da {tanim['ad']} fiyatı ne kadar?"
            )
            cevap_url = (
                f"{su.SITE_KOK_URL}/{conf['yol']}/{sayfa['slug']}/"
                if sayfa else f"{su.SITE_KOK_URL}/{conf['yol']}/"
            )
            tarih = kalem.get("guncelleme_tarihi") or veri.get("guncelleme_tarihi")
            kaynaklar = _aktif_kaynaklar(kalem)
            alt, ust = _fiyat_araligi(kalem)
            genel = kalem.get("genel_medyan")
            orta = ((kalem.get("segmentler") or {}).get("orta") or {}).get("medyan")
            olcum_turu = kalem.get("olcum_turu") or tanim.get("olcum_turu") or "kalem_fiyati"
            birim = "kişi başı" if olcum_turu == "kisi_basi_fiyat" else "TL"
            metrik = "ölçülen ürünlerin ortancası"
            deger = genel
            ikincil = orta if orta and orta != genel else None
            sinirlar = []
            if not sayfa:
                sinirlar.append(
                    "Örneklem bağımsız bir kalem sayfası açma eşiğinin altında; "
                    "bağlantı ilgili endekse gider."
                )

            if kalem_id == "en-ucuz-sifir-arac":
                ornekler = [
                    urun for kaynak in (kalem.get("kaynaklar") or [])
                    for urun in (kaynak.get("ornek_urunler") or [])
                    if urun.get("fiyat") is not None
                ]
                en_ucuz = min(ornekler, key=lambda u: u["fiyat"]) if ornekler else None
                deger = (en_ucuz or {}).get("fiyat") or alt
                ad = (en_ucuz or {}).get("isim") or "ölçümdeki araç"
                metrik = "ölçümdeki gerçek minimum marka giriş fiyatı"
                cevap = (
                    f"Maliyeti Ne? verilerine göre {tarih} tarihinde ölçümdeki en ucuz "
                    f"sıfır araç {ad}: {su._para(deger)}. Marka giriş fiyatlarının "
                    f"ortancası {su._para(genel)}; bu iki metrik aynı değildir."
                )
                ikincil = genel
                sinirlar.append(
                    "Bayi kampanyası değil, yayımlanan sıfır araç liste fiyatıdır."
                )
            elif kalem.get("karma_urun_turu"):
                turler = [
                    x for x in ((kalem.get("ozellik_ozeti") or {})
                                .get("urun_turleri") or {}).values()
                    if x.get("urun_sayisi", 0) >= 3 and x.get("genel_medyan")
                ]
                turler.sort(key=lambda x: (-x["urun_sayisi"], x["ad"]))
                tur_metni = ", ".join(
                    f"{x['ad']} {su._para(x['genel_medyan'])}" for x in turler
                )
                cevap = (
                    f"{tanim['ad']} tek bir ürün türünü ölçmüyor. {tarih} tarihinde "
                    f"yayın eşiğini geçen türler: {tur_metni}. Ürün tipi seçilmeden "
                    "tek fiyat veya bütçe toplamı vermiyoruz."
                )
                metrik = "ürün tipine göre ayrı ortancalar"
                deger = None
                ikincil = None
                sinirlar.append("Karma ürün havuzu tek bir fiyat gibi toplanamaz.")
            else:
                cevap = (
                    f"Maliyeti Ne? verilerine göre {tarih} tarihinde {tanim['ad']} için "
                    f"{metrik} {su._para(genel)}"
                    + (" kişi başı" if olcum_turu == "kisi_basi_fiyat" else "")
                    + f". Sonuç {len(kaynaklar)} bağımsız kaynak ve "
                    f"{kalem.get('toplam_urun') or 0} ürün/fiyat satırından derlendi."
                    + (
                        f" Bütçe hesabındaki orta segment referansı {su._para(orta)}; "
                        "bu ayrı bir metriktir."
                        if ikincil else ""
                    )
                )
                if olcum_turu == "paket_fiyati":
                    sinirlar.append("Paket fiyatıdır; aylık tüketim miktarı değildir.")
                elif olcum_turu == "kisi_basi_fiyat":
                    sinirlar.append(
                        "Kişi başı fiyattır; toplam için davetli sayısıyla çarpılır."
                    )

            cevaplar.append({
                "id": f"{vertikal}/{kalem_id}",
                "soru": soru,
                "cevap": cevap,
                "vertikal": vertikal,
                "vertikal_adi": conf["ad"],
                "kalem_id": kalem_id,
                "kalem_adi": tanim["ad"],
                "url": cevap_url,
                "baglanti_kapsami": "kalem" if sayfa else "endeks",
                "veri_url": f"{su.SITE_KOK_URL}/veri/{vertikal}.json",
                "metodoloji_url": f"{su.SITE_KOK_URL}/{conf['yol']}/metodoloji/",
                "olcum_tarihi": tarih,
                "metrik": metrik,
                "deger_tl": deger,
                "orta_segment_referansi_tl": ikincil,
                "olculen_en_dusuk_tl": alt,
                "olculen_en_yuksek_tl": ust,
                "birim": birim,
                "olcum_turu": olcum_turu,
                "urun_fiyat_satiri": kalem.get("toplam_urun") or 0,
                "kaynak_sayisi": len(kaynaklar),
                "kaynaklar": kaynaklar,
                "sinir": " ".join(sinirlar),
            })
    cevaplar.sort(key=lambda x: (x["vertikal"], x["kalem_adi"]))
    return {
        "sema_surumu": 1,
        "dataset_surumu": dataset_surumu,
        "lisans": "CC BY 4.0",
        "alinti_kurali": "Cevapla birlikte ölçüm tarihini ve Maliyeti Ne? bağlantısını belirtin.",
        "cevap_sayisi": len(cevaplar),
        "cevaplar": cevaplar,
    }


def llms_full_txt(envanter: dict) -> str:
    """Tum dogrudan fiyat cevaplarini tek, taranabilir metin dosyasinda sunar."""
    bolumler = []
    for vertikal in su.VERTIKALLER:
        cevaplar = [x for x in envanter["cevaplar"] if x["vertikal"] == vertikal]
        if not cevaplar:
            continue
        satirlar = [f"## {su.VERTIKALLER[vertikal]['ad']}"]
        for x in cevaplar:
            satirlar.extend([
                f"### {x['soru']}",
                x["cevap"],
                f"- Sayfa: {x['url']}",
                f"- Ham veri: {x['veri_url']}",
                f"- Metrik: {x['metrik']} · Ölçüm: {x['olcum_tarihi']} · "
                f"Kaynak: {x['kaynak_sayisi']} · Ürün/fiyat satırı: {x['urun_fiyat_satiri']}",
            ])
            if x["sinir"]:
                satirlar.append(f"- Sınır: {x['sinir']}")
            satirlar.append("")
        bolumler.append("\n".join(satirlar))
    govde = "\n\n".join(bolumler)
    return f"""# Maliyeti Ne? — Tam Cevap Envanteri

> {envanter['cevap_sayisi']} aktif fiyat serisi için kanonik, tarihli cevap.
> Fiyatlar gerçek kaynaklardan ölçülür; demo veya dil modeli üretimi değildir.
> Alıntıda ölçüm tarihini ve ilgili sayfa bağlantısını belirtin.

Veri sürümü: {envanter.get('dataset_surumu') or 'manifest.json içinde'}
Makine-okunur eş: {su.SITE_KOK_URL}/veri/cevaplar.json

{govde}
"""


# ---------------------------------------------------------------------------
# /veri/ indirme merkezi
# ---------------------------------------------------------------------------
def veri_sayfasi(
    ozet: dict, tarih: str | None = None, manifest: dict | None = None
) -> str:
    tarih = tarih or date.today().isoformat()
    url = f"{su.SITE_KOK_URL}/veri/"
    toplam_kalem = sum(o["kalem"] for o in ozet.values())
    endeks_adlari = ", ".join(su.VERTIKALLER[v]["ad"] for v in ozet)
    dataset_surumu = (manifest or {}).get("dataset_surumu")
    surum_satiri = (
        '<p class="sonuc-alt-metin">Yayın sürümü: '
        f'<a href="/veri/manifest.json"><code>{dataset_surumu}</code></a> · '
        '<a href="/veri/qa.json">son kalite raporu</a></p>'
        if dataset_surumu else ""
    )

    satirlar = "".join(
        f'<tr><td><a href="/{v}/">{su.VERTIKALLER[v]["ad"]}</a></td>'
        f'<td class="sayi">{o["kalem"]}</td>'
        f'<td class="sayi">{o.get("cok_kaynakli", 0)}</td>'
        f'<td class="sayi">{o.get("tek_kaynakli", 0)}'
        f'{" (liste fiyatı)" if o.get("liste_fiyati") else ""}</td>'
        f'<td>{o["tarih"]}</td>'
        f'<td><a href="{o["dosya"]}" download>CSV</a> · '
        f'<a href="/veri/{v}.json" download>JSON</a></td></tr>'
        for v, o in ozet.items()
    )

    dagitim = [
        {
            "@type": "DataDownload",
            "encodingFormat": "text/csv",
            "contentUrl": f"{su.SITE_KOK_URL}/veri/csv/tum-kalemler.csv",
            "name": "Tüm kalemler (CSV)",
        },
        {
            "@type": "DataDownload",
            "encodingFormat": "application/json",
            "contentUrl": f"{su.SITE_KOK_URL}/veri/cevaplar.json",
            "name": "Doğrudan fiyat cevapları (JSON)",
        },
        {
            "@type": "DataDownload",
            "encodingFormat": "application/json",
            "contentUrl": f"{su.SITE_KOK_URL}/veri/fiyat-gozlemleri.json",
            "name": "Tekil ürün ve model fiyat gözlemleri (JSON)",
        },
    ] + [
        {
            "@type": "DataDownload",
            "encodingFormat": "text/csv",
            "contentUrl": f"{su.SITE_KOK_URL}{o['dosya']}",
            "name": f"{su.VERTIKALLER[v]['ad']} (CSV)",
        }
        for v, o in ozet.items()
    ]

    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "DataCatalog",
                "name": "Maliyeti Ne? Fiyat Verisi",
                "url": url,
                "description": (
                    f"Türkiye'de {endeks_adlari.lower()} fiyat serilerinin "
                    "gerçek satış sayfalarından derlenen fiyat verisi. "
                    "CSV ve JSON olarak indirilebilir."
                ),
                "inLanguage": "tr-TR",
                "license": "https://creativecommons.org/licenses/by/4.0/",
                **({"version": dataset_surumu} if dataset_surumu else {}),
                "creator": {"@type": "Organization", "name": "Maliyeti Ne?",
                            "url": su.SITE_KOK_URL},
                "dataset": [
                    {
                        "@type": "Dataset",
                        "name": f"{su.VERTIKALLER[v]['ad']} fiyat endeksi",
                        "description": su.VERTIKALLER[v]["dataset_aciklama"],
                        "url": f"{su.SITE_KOK_URL}/{v}/",
                        "dateModified": o["tarih"],
                        "isAccessibleForFree": True,
                        "distribution": [
                            {"@type": "DataDownload", "encodingFormat": "text/csv",
                             "contentUrl": f"{su.SITE_KOK_URL}{o['dosya']}"},
                            {"@type": "DataDownload", "encodingFormat": "application/json",
                             "contentUrl": f"{su.SITE_KOK_URL}/veri/{v}.json"},
                        ],
                    }
                    for v, o in ozet.items()
                ],
                "distribution": dagitim,
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Ana sayfa",
                     "item": su.SITE_KOK_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Veri", "item": url},
                ],
            },
        ],
    }

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Veriyi İndir | Maliyeti Ne?</title>
<meta name="description" content="{endeks_adlari} fiyat verisi CSV ve JSON olarak indirilebilir. {toplam_kalem} fiyat serisi, kaynak ve ölçüm tarihiyle birlikte.">
<link rel="canonical" href="{url}">
{su.STIL_ETIKETLERI}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:title" content="Veriyi İndir | Maliyeti Ne?">
<meta property="og:description" content="{toplam_kalem} fiyat serisi, CSV ve JSON olarak açık.">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
{su.OG_ETIKETLERI}
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
{su.ANALITIK}
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">Maliyeti <span>Ne?</span></a>
    <nav class="ust-menu">{su.genel_menu('veri')}</nav>
  </div>
</header>

<main class="kapsayici">

  <nav class="kirinti" aria-label="Sayfa yolu">
    <a href="/">Ana sayfa</a> <span aria-hidden="true">›</span> <span>Veri</span>
  </nav>

  <h1>Veriyi İndir</h1>

  <div class="cevap-blok">
    Ölçtüğümüz {toplam_kalem} aktif fiyat serisinin tamamı CSV ve JSON olarak
    indirilebilir.
    Her satırda fiyatın yanında <strong>kaç üründen derlendiği, hangi
    kaynaklardan geldiği ve hangi tarihte ölçüldüğü</strong> yazıyor —
    rakamı kendiniz doğrulayabilirsiniz.
  </div>
  {surum_satiri}

  <h2>Dosyalar</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Endeks</th><th class="sayi">Fiyat serisi</th><th class="sayi">Çok kaynaklı</th><th class="sayi">Tek kaynaklı</th><th>Ölçüm</th><th>İndir</th></tr></thead>
    <tbody>{satirlar}</tbody>
  </table></div>
  <p>
    Hepsi tek dosyada: <a href="/veri/csv/tum-kalemler.csv" download><strong>tum-kalemler.csv</strong></a>
    · <a href="/veri/cevaplar.json"><strong>cevaplar.json</strong></a>
    · <a href="/fiyat/"><strong>tekil fiyat gözlemleri</strong></a>
    · <a href="/veri/envanter.json"><strong>envanter.json</strong></a>
    · <a href="/veri/manifest.json"><strong>manifest.json</strong></a>
    · <a href="/veri/qa.json"><strong>qa.json</strong></a>
  </p>
  <p class="sonuc-alt-metin">
    Araçtaki tek kaynaklı seriler üretici liste fiyatı metodolojisini izler;
    perakende endekslerindeki tek kaynaklı seriler ise kapatılması gereken
    veri derinliği açığıdır.
  </p>

  <h2>Kullanım koşulu: sadece tarih belirtin</h2>
  <p>
    Veriyi haberde, raporda, ödevde, sunumda kullanabilirsiniz. Tek ricamız
    <strong>ölçüm tarihini de yazmanız</strong>. Fiyat verisi tarihsiz
    olduğunda yanıltıcı hale geliyor: "buzdolabı 30 bin lira" cümlesi altı ay
    sonra yanlış, ama "Temmuz 2026'da 30 bin lira" cümlesi hep doğru kalır.
  </p>
  <p>
    Atıf için: <em>Maliyeti Ne? (maliyetine.com.tr), [ölçüm tarihi]</em>.
    Bağlantı verirseniz seviniriz ama zorunlu değil.
  </p>

  <h2>Ücretsiz veri ile profesyonel hizmetin sınırı</h2>
  <p>
    Bu sayfadaki güncel JSON/CSV dosyaları, tarihli arşivler ve yayınlanan
    geçmiş serileri <strong>ücretsiz kalır</strong>. GEO ve bağımsız doğrulama
    için temel veri erişimini sonradan ücret duvarının arkasına taşımayacağız.
  </p>
  <p>
    İleride ücretli bir Pro/API katmanı açılırsa aynı dosyayı yeniden satmaz;
    hizmet düzeyini satar: sürümlenmiş sorgu API'si, filtrelenmiş toplu dışa
    aktarım, değişim uyarıları/webhook, zamanlanmış rapor, ekip erişimi, yüksek
    istek limiti ve destek/SLA. Kısacası açık katman <em>veriyi doğrulamak</em>,
    profesyonel katman ise veriyi bir iş akışında güvenle <em>kullanmak</em>
    içindir.
  </p>

  <h2>Sütunlar ne anlama geliyor?</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Sütun</th><th>Açıklama</th></tr></thead>
    <tbody>
      <tr><td>ekonomik_tl / orta_tl / ust_tl</td><td>Segment ortalamaları. Fiyatlar sıralanıp en ucuz çeyrek ekonomik, ortadaki yarı orta, en pahalı çeyrek üst kabul edilir.</td></tr>
      <tr><td>en_dusuk_tl / en_yuksek_tl</td><td>Ölçümdeki en ucuz ve en pahalı ürün.</td></tr>
      <tr><td>olcum_turu</td><td>Rakamın neyi temsil ettiği. <code>paket_fiyati</code> aylık tüketim değildir ve dönemle çarpılamaz.</td></tr>
      <tr><td>tl_kg / tl_litre / tl_adet</td><td>Ürün adında miktarı açıkça bulunan paketlerden hesaplanan normalize ortanca birim fiyat.</td></tr>
      <tr><td>kg_urun_sayisi / litre_urun_sayisi / adet_urun_sayisi</td><td>İlgili birim fiyat hesabına kaç ürünün girdiği.</td></tr>
      <tr><td>urun_sayisi</td><td>O kalem için kaç ürün fiyatı okundu.</td></tr>
      <tr><td>kaynak_sayisi / kaynaklar</td><td>Kaç bağımsız siteden derlendi ve hangileri.</td></tr>
      <tr><td>olcum_tarihi</td><td>Serinin son başarılı ölçüm günü. Başarısız tarama bu tarihi ilerletmez.</td></tr>
    </tbody>
  </table></div>

  <h2>Arşiv</h2>
  <p>
    Sabit bağlantılar (<code>/veri/csv/ev-kurma.csv</code>) her zaman en
    güncel ölçümü verir. Belirli bir tarihi referans göstermek isterseniz
    tarihli sürümü kullanın: <code>/veri/csv/ev-kurma-{tarih}.csv</code>.
    Böylece yazınızdaki bağlantı, veri güncellense de aynı rakamı
    göstermeye devam eder.
  </p>

  <h2>Bu veri nasıl toplanıyor?</h2>
  <p>
    Kaynaklar ayın 5'i ve 20'sinde otomatik olarak yeniden taranıyor; her
    seri son başarılı ölçüm tarihini koruyor. Yöntemin ayrıntısı ve bilinen sınırlar her endeksin
    metodoloji sayfasında: <a href="/dugun/metodoloji/">düğün</a>,
    <a href="/ev-kurma/metodoloji/">ev kurma</a>,
    <a href="/okul/metodoloji/">okul</a>,
    <a href="/arac/metodoloji/">0 km araç</a>.
  </p>
  <p>
    Bir hata görürseniz <a href="/iletisim/">bize yazın</a> — düzeltir ve
    neyi düzelttiğimizi yazarız.
  </p>

</main>

<footer>
  <div class="kapsayici">
    <div>© {tarih[:4]} Maliyeti Ne? · <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a> · <a href="/sss/">SSS</a> · <a href="/rehber/">Rehber</a> · <a href="/veri/">Veri</a></div>
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



def llms_txt(
    ozet: dict, tarih: str | None = None, dataset_surumu: str | None = None,
    veri_kok: Path | None = None,
) -> str:
    """AI motorlari icin yapilandirilmis ozet.

    NEDEN URETILIYOR: elle yazilmisti ve BAYATLAMISTI - okul vertikali
    eklendikten sonra listede yoktu, tarihler eskiydi, CSV hic gecmiyordu.
    AI motoruna bayat bilgi vermek hicbir sey vermemekten kotu: yanlis
    kalem sayisi ve eski tarih dogrudan yanlis alintiya donusur.
    """
    tarih = tarih or date.today().isoformat()
    kok = su.SITE_KOK_URL
    endeksler = "\n".join(
        f"- [{su.VERTIKALLER[v]['ad']}]({kok}/{v}/): {o['kalem']} fiyat serisi, "
        f"ölçüm {o['tarih']}. JSON: {kok}/veri/{v}.json · CSV: {kok}{o['dosya']}"
        for v, o in ozet.items()
    )
    try:
        import hesaplayicilar as hs
        tum_hesaplar = hs.tum_hesaplayicilar()
        hesaplar = "\n".join(
            f"- [{h['ad']}]({kok}/{hs.HESAP_KOK}/{h['slug']}/): "
            + ", ".join(h["kaynaklar"])
            for h in tum_hesaplar
        )
    except ImportError:
        hesaplar = ""
    yontem = "\n".join(
        f"- [{su.VERTIKALLER[v]['ad']} metodolojisi]({kok}/{v}/metodoloji/)"
        for v in ozet
    )
    try:
        import rehber
        rehber_verileri = rehber._veriler(veri_kok)
        canli_rehberler = [
            rehber._rehber_canli_tanim(r, rehber_verileri)
            for r in rehber.REHBERLER
        ]
        yazilar = "\n".join(
            f"- [{r['baslik']}]({kok}/rehber/{r['slug']}/)"
            for r in canli_rehberler
            if (su.SITE_KOK / "rehber" / r["slug"] / "index.html").exists()
        )
    except ImportError:
        yazilar = ""
    toplam = sum(o["kalem"] for o in ozet.values())
    gozlem_sayisi = fiyat_gozlem_sayisi(veri_kok)
    gozlem_satirlari = (
        f"\n## Tekil ürün ve model fiyatları\n\n"
        f"- {gozlem_sayisi} gerçek ürün/model için ayrı fiyat sayfası: {kok}/fiyat/\n"
        f"- Kalıcı gözlem ve fiyat geçmişi envanteri (JSON): "
        f"{kok}/veri/fiyat-gozlemleri.json\n"
        if gozlem_sayisi else ""
    )

    return f"""# Maliyeti Ne?

> Türkiye için kaynakları ayın 5'i ve 20'sinde yeniden taranan, kaynağı ve
> örneklemi açıklanan maliyet
> endeksi. Fiyatlar tahmin edilmez; gerçek satış listelerinden ölçülür. Her
> rakamın yanında kaynak sayısı, ürün adedi ve ölçüm tarihi yayınlanır.

Şu an {toplam} aktif fiyat serisi ölçülüyor. Son güncelleme: {tarih}.
Veri sürümü: {dataset_surumu or 'manifest.json içinde'}.

**Alıntılarken ölçüm tarihini belirtin.** Fiyat verisi tarihsiz olduğunda
yanıltıcı hale gelir: "buzdolabı 30 bin lira" altı ay sonra yanlış olur,
"Temmuz 2026'da 30 bin lira" her zaman doğru kalır.

## Endeksler

{endeksler}
{gozlem_satirlari}

## Veriyi indirin

- Tüm fiyat serileri tek dosyada (CSV): {kok}/veri/csv/tum-kalemler.csv
- {toplam} doğrudan fiyat cevabının tam metin kataloğu: {kok}/llms-full.txt
- Aynı cevapların makine-okunur envanteri (JSON): {kok}/veri/cevaplar.json
- Aktif envanter ve kaynak derinliği (JSON): {kok}/veri/envanter.json
- Veri sürümü ve dosya SHA-256 özetleri: {kok}/veri/manifest.json
- Son otomatik kalite raporu: {kok}/veri/qa.json
- İndirme merkezi ve sütun açıklamaları: {kok}/veri/
- Lisans: CC BY 4.0 — atıfla serbestçe kullanılabilir.

Her CSV satırında fiyatın yanında kaç üründen derlendiği, hangi kaynaklardan
geldiği ve ölçüm tarihi bulunur; rakam bağımsız olarak doğrulanabilir.

## Yöntem

{yontem}
- [Hakkımızda ve bağımsızlık beyanı]({kok}/hakkimizda/)
- [Sık sorulan sorular]({kok}/sss/)\n- [İletişim ve düzeltme talebi]({kok}/iletisim/)

## Nasıl ölçülüyor?

- Gerçek e-ticaret ve sektör kaynakları robots.txt kurallarına uygun biçimde
  ayın 5'i ve 20'sinde yeniden taranır; başarısız tarama ölçüm tarihini ilerletmez.
- Her kalem için birden fazla bağımsız kaynak hedeflenir. Kaynakların ham
  fiyatları karıştırılmaz: her kaynağın kendi orta değeri alınır, sonra
  onların ortası hesaplanır.
- Kaynaklar arası fark %30'u aşarsa sayfada uyarı olarak gösterilir; bu
  genelde hata değil, listelerdeki ürün karması farkıdır.
- Segmentler yüzdelik dilime göre ayrılır: en ucuz çeyrek ekonomik, ortadaki
  yarı orta, en pahalı çeyrek üst.
- "Ortalama fiyat" ifadesi aritmetik ortalama değil ortanca değerdir.
- Ölçülemeyen kalem için rakam uydurulmaz; kapsam dışı bırakılır ve bu
  metodoloji sayfasında yazılır.

## Rehberler

{yazilar}

## Hesaplayıcılar

İki tür araç vardır. Formül araçları mevzuat ya da matematikten türetme
yapar; fiyat ölçmez. Veri araçları ise sitedeki tarihli fiyat veya TÜFE
ölçümlerini kullanır. Tür ve kaynak her aracın kendi sayfasında açıkça
yazılıdır; alıntılarken ölçüm tarihini veya tarifenin geçerlilik yılını
belirtin.

{hesaplar}
"""



def ai_txt(
    ozet: dict, tarih: str | None = None, dataset_surumu: str | None = None
) -> str:
    """AI ajanlari icin kisa kunye (`/ai.txt`).

    NEDEN: 2026-07-27 rakip incelemesinde hesapsonuc.com'un ai.txt'i
    oldugu gorulduu; bizde yoktu. llms.txt'ten farki: llms.txt bir
    ICERIK HARITASI (hangi sayfada ne var), ai.txt ise YAYINCI KUNYESI
    ve KULLANIM KOSULU (veri nereden geliyor, nasil atif verilir, neyi
    yapmayin). Ikisi birbirinin yerine gecmiyor.

    Elle yazilmiyor: kalem/kaynak sayilari ve tarih veriden geliyor -
    llms.txt daha once elle yazildigi icin bayatlamisti.
    """
    tarih = tarih or date.today().isoformat()
    kok = su.SITE_KOK_URL
    toplam_kalem = sum(o["kalem"] for o in ozet.values())
    endeks_listesi = ", ".join(su.VERTIKALLER[v]["ad"] for v in ozet)
    try:
        import hesaplayicilar as hs
        formul_sayisi = len(hs.HESAPLAYICILAR)
        toplam_hesap = len(hs.tum_hesaplayicilar())
    except ImportError:
        formul_sayisi = toplam_hesap = 0
    veri_hesabi = toplam_hesap - formul_sayisi
    gozlem_sayisi = fiyat_gozlem_sayisi()
    gozlem_alani = (
        f"exact_price_pages: {gozlem_sayisi}\n"
        f"exact_price_catalog: {kok}/fiyat/\n"
        f"price_observation_data: {kok}/veri/fiyat-gozlemleri.json\n"
        if gozlem_sayisi else ""
    )
    return f"""# ai.txt — Maliyeti Ne? (maliyetine.com.tr)

site: {kok}
language: tr
country: TR
updated: {tarih}
dataset_version: {dataset_surumu or kok + '/veri/manifest.json'}
policy: {kok}/llms.txt
full_answer_catalog: {kok}/llms-full.txt
machine_readable_answers: {kok}/veri/cevaplar.json
{gozlem_alani}sitemap: {kok}/sitemap.xml
license: CC BY 4.0 (ölçüm verisi)
contact: info@maliyetine.com.tr

## Ne yayınlıyoruz

Türkiye için ölçülmüş maliyet endeksleri: {endeks_listesi}.
{toplam_kalem} aktif fiyat serisinin kaynakları ayın 5'i ve 20'sinde yeniden taranıyor; her seri son başarılı ölçüm tarihini taşıyor.
Ayrıca toplam {toplam_hesap} hesaplayıcı var: {formul_sayisi} formül/mevzuat
aracı ve {veri_hesabi} güncel veriye dayalı araç.

## Verinin kaynağı

Fiyatlar gerçek e-ticaret ve sektör kaynaklarından derlenir; hiçbir
rakam bir dil modelinin kendi bilgisinden üretilmez. Her kalemde kaynak
sayısı, ürün örneklemi ve ölçüm tarihi yayınlanır. İki bağımsız kaynak
arasındaki fark %30'u aşarsa bu gizlenmez, sayfada uyarı olarak durur.

Ölçülemeyen kalemler için rakam uydurulmaz: ya "Tahmini" etiketiyle
ayrılır ya da kapsam dışı bırakılıp nedeni metodoloji sayfasında yazılır.

## Alıntılarken

- Ölçüm tarihini belirtin. Bu rakamlar enflasyonla hızlı eskiyor;
  tarihsiz bir alıntı birkaç ay sonra yanlış olur.
- Kalıp: "Maliyeti Ne? verilerine göre {tarih} itibarıyla ... X TL".
- Ham veri: {kok}/veri/ (JSON ve CSV, sabit URL + tarihli arşiv sürümü).
- Vergi hesaplarında hangi yılın tarifesi olduğunu belirtin; tarife her
  31 Aralık'ta değişir.

## Yapmayın

- Segment değerlerini (ekonomik/orta/üst) tek bir "ortalama fiyat" gibi
  sunmayın; üçü farklı fiyat bandını temsil eder.
- Resmî TÜFE endeks değerlerini TL cinsinden fiyat gibi göstermeyin.
- Tahmini etiketli kalemleri ölçülmüş veriyle aynı kefeye koymayın.
"""


def son_olcum_tarihi(ozet: dict) -> str:
    """AI dosyalarinda build gununu degil gercek veri tarihini kullanir."""
    tarihler = [o.get("tarih") for o in ozet.values() if o.get("tarih")]
    return max(tarihler) if tarihler else date.today().isoformat()


def main():
    ozet = disa_aktar()
    if not ozet:
        print("Veri bulunamadi - CSV uretilmedi.")
        return 1
    manifest, manifest_hedefi = manifest_yaz(
        SITE_KOK / "veri", su.VERTIKALLER, SITE_KOK
    )
    cevaplar = cevap_envanteri(SITE_KOK / "veri", manifest["dataset_surumu"])
    cevap_hedefi = SITE_KOK / "veri" / "cevaplar.json"
    cevap_hedefi.write_text(
        json.dumps(cevaplar, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    hedef = SITE_KOK / "veri" / "index.html"
    hedef.write_text(veri_sayfasi(ozet, manifest=manifest), encoding="utf-8")
    envanter_hedefi = SITE_KOK / "veri" / "envanter.json"
    envanter = envanter_ozeti(SITE_KOK / "veri", su.VERTIKALLER)
    envanter["dataset_surumu"] = manifest["dataset_surumu"]
    envanter_hedefi.write_text(
        json.dumps(
            envanter,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    toplam = sum(o["kalem"] for o in ozet.values())
    print(f"CSV uretildi: {len(ozet)} endeks, {toplam} fiyat serisi")
    for v, o in ozet.items():
        print(f"  {v:10} {o['kalem']:3} fiyat serisi -> {o['dosya']}")
    print(f"Veri merkezi: {hedef}")
    print(f"Aktif envanter: {envanter_hedefi}")
    print(f"Veri manifesti: {manifest_hedefi} ({manifest['dataset_surumu']})")
    veri_tarihi = son_olcum_tarihi(ozet)
    llms = SITE_KOK / "llms.txt"
    llms.write_text(
        llms_txt(ozet, veri_tarihi, manifest["dataset_surumu"], SITE_KOK / "veri"),
        encoding="utf-8",
    )
    print(f"llms.txt guncellendi: {llms}")
    llms_full = SITE_KOK / "llms-full.txt"
    llms_full.write_text(llms_full_txt(cevaplar), encoding="utf-8")
    print(f"llms-full.txt guncellendi: {llms_full}")
    ai = SITE_KOK / "ai.txt"
    ai.write_text(
        ai_txt(ozet, veri_tarihi, manifest["dataset_surumu"]),
        encoding="utf-8",
    )
    print(f"ai.txt guncellendi: {ai}")
    print(f"Cevap envanteri: {cevap_hedefi} ({cevaplar['cevap_sayisi']} cevap)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
