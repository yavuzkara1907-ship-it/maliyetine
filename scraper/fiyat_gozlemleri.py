# -*- coding: utf-8 -*-
"""Gercek urun/model fiyat gozlemlerinden kalici exact-query sayfalari uretir.

Rakip sitelerin GEO avantaji, her fiyat sorusuna ayri bir URL vermeleri.
Buradaki fark: sayfa ancak kaynak verisinde urun adi + fiyat birlikte varsa
acilir. Bir kez acilan URL arsivde korunur; urun sonraki taramada gorunmezse
404 olmak yerine son olcum tarihiyle yayinda kalir.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import statistics
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

import sayfa_uret as su


SITE_KOK = su.SITE_KOK
VERI_KOK = SITE_KOK / "veri"
ENVANTER_DOSYASI = VERI_KOK / "fiyat-gozlemleri.json"
FIYAT_KOK = SITE_KOK / "fiyat"
SEMA_SURUMU = 1


def _duz_metin(deger: object) -> str:
    return re.sub(r"\s+", " ", str(deger or "")).strip()


def _kimlik_metni(ad: str) -> str:
    return _duz_metin(ad).casefold()


def _slug(ad: str, kimlik: str) -> str:
    ceviri = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "Ş": "s",
                            "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u",
                            "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"})
    sade = unicodedata.normalize("NFKD", ad.translate(ceviri))
    sade = "".join(c for c in sade if not unicodedata.combining(c)).lower()
    sade = re.sub(r"[^a-z0-9]+", "-", sade).strip("-")[:72].rstrip("-")
    ozet = hashlib.sha1(kimlik.encode("utf-8")).hexdigest()[:8]
    return f"{sade or 'urun'}-{ozet}"


def _para(deger: float | int | None) -> str:
    return su._para(deger) if deger is not None else "—"


def _baslik_adlarini_ayir(kayitlar: list[dict], sinir: int = 35) -> None:
    """Uzun urun adlarini title icin hem kisa hem benzersiz yapar."""
    adaylar = {}
    for x in kayitlar:
        ad = x["urun_adi"]
        if len(ad) <= sinir:
            secenekler = [ad]
        else:
            secenekler = [
                ad[:sinir - 1].rstrip() + "…",
                ad[:23].rstrip() + "…" + ad[-11:].lstrip(),
                ad[:17].rstrip() + "…" + ad[-17:].lstrip(),
                ad[:11].rstrip() + "…" + ad[-23:].lstrip(),
            ]
        adaylar[x["id"]] = secenekler
    for sira in range(4):
        sayilar = defaultdict(int)
        for secenekler in adaylar.values():
            aday = secenekler[min(sira, len(secenekler) - 1)].casefold()
            sayilar[aday] += 1
        for x in kayitlar:
            if x.get("seo_kisa_adi"):
                continue
            secenekler = adaylar[x["id"]]
            aday = secenekler[min(sira, len(secenekler) - 1)]
            if sayilar[aday.casefold()] == 1:
                x["seo_kisa_adi"] = aday
    for x in kayitlar:
        if not x.get("seo_kisa_adi"):
            x["seo_kisa_adi"] = x["urun_adi"][:29].rstrip() + " " + x["id"][:4]


def _kaynak_adi(site: str) -> str:
    adlar = {
        "amazon": "Amazon", "trendyol": "Trendyol", "mediamarkt": "MediaMarkt",
        "petzzshop": "Petzzshop", "ebebek": "e-bebek", "joker": "Joker",
        "donanimhaber": "DonanımHaber", "dugun-com": "Düğün.com",
        "dugunbuketi": "DüğünBuketi", "atasay": "Atasay", "cimri": "Cimri",
        "beymen": "Beymen", "boyner": "Boyner", "ramsey": "Ramsey",
        "vakko": "Vakko", "nezih": "Nezih", "dr": "D&R",
    }
    return adlar.get(site, site.replace("-", " ").title())


def _mevcut_envanter(dosya: Path = ENVANTER_DOSYASI) -> dict:
    if not dosya.exists():
        return {"sema_surumu": SEMA_SURUMU, "gozlemler": []}
    try:
        veri = json.loads(dosya.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"sema_surumu": SEMA_SURUMU, "gozlemler": []}
    return veri if isinstance(veri.get("gozlemler"), list) else {
        "sema_surumu": SEMA_SURUMU, "gozlemler": []
    }


def guncel_gozlemler(veri_kok: Path = VERI_KOK) -> list[dict]:
    """Agregali JSON'lardaki ad + fiyat orneklerini kaynaklariyla okur."""
    bulunan = []
    for vertikal, conf in su.VERTIKALLER.items():
        dosya = veri_kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        veri = json.loads(dosya.read_text(encoding="utf-8"))
        tanimlar = {k["id"]: k for k in conf["kalemler"]}
        for kalem_id, kalem in (veri.get("kalemler") or {}).items():
            tanim = tanimlar.get(kalem_id)
            if not tanim:
                continue
            for kaynak in kalem.get("kaynaklar") or []:
                site = _duz_metin(kaynak.get("site"))
                tarih = (kaynak.get("tarih") or kalem.get("guncelleme_tarihi")
                         or veri.get("guncelleme_tarihi"))
                for urun in kaynak.get("ornek_urunler") or []:
                    ad = _duz_metin(urun.get("isim") or urun.get("ad"))
                    fiyat = urun.get("fiyat")
                    if len(ad) < 3 or not isinstance(fiyat, (int, float)) or fiyat <= 0:
                        continue
                    bulunan.append({
                        "vertikal": vertikal,
                        "vertikal_adi": conf["ad"],
                        "vertikal_yolu": conf["yol"],
                        "kalem_id": kalem_id,
                        "kalem_adi": tanim["ad"],
                        "urun_adi": ad,
                        "site": site,
                        "kaynak_adi": _kaynak_adi(site),
                        "tarih": tarih,
                        "fiyat_tl": fiyat,
                        "kategori_ortancasi_tl": kalem.get("genel_medyan"),
                        "kategori_urun_sayisi": kalem.get("toplam_urun") or 0,
                        "kategori_kaynak_sayisi": kalem.get("kaynak_sayisi") or 0,
                    })
    return bulunan


def envanter_uret(
    veri_kok: Path = VERI_KOK, mevcut_dosya: Path = ENVANTER_DOSYASI
) -> dict:
    """Yeni olcumleri kalici arsivle birlestirir; URL'ler silinmez."""
    mevcut = _mevcut_envanter(mevcut_dosya)
    kayitlar = {x["id"]: x for x in mevcut.get("gozlemler", []) if x.get("id")}
    bu_kosuda = set()

    for ham in guncel_gozlemler(veri_kok):
        kimlik = f"{ham['vertikal']}/{ham['kalem_id']}/{_kimlik_metni(ham['urun_adi'])}"
        kayit_id = hashlib.sha1(kimlik.encode("utf-8")).hexdigest()[:16]
        bu_kosuda.add(kayit_id)
        kayit = kayitlar.get(kayit_id) or {
            "id": kayit_id,
            "slug": _slug(ham["urun_adi"], kimlik),
            "vertikal": ham["vertikal"],
            "vertikal_adi": ham["vertikal_adi"],
            "vertikal_yolu": ham["vertikal_yolu"],
            "kalem_id": ham["kalem_id"],
            "kalem_adi": ham["kalem_adi"],
            "urun_adi": ham["urun_adi"],
            "ilk_olcum_tarihi": ham["tarih"],
            "olcumler": [],
        }
        olcum = {k: ham[k] for k in (
            "site", "kaynak_adi", "tarih", "fiyat_tl",
            "kategori_ortancasi_tl", "kategori_urun_sayisi",
            "kategori_kaynak_sayisi",
        )}
        anahtar = (olcum["site"], olcum["tarih"], olcum["fiyat_tl"])
        eski_anahtarlar = {
            (o.get("site"), o.get("tarih"), o.get("fiyat_tl"))
            for o in kayit.get("olcumler", [])
        }
        if anahtar not in eski_anahtarlar:
            kayit.setdefault("olcumler", []).append(olcum)
        kayit["olcumler"].sort(key=lambda o: (o.get("tarih") or "", o.get("site") or ""))
        kayit["son_olcum_tarihi"] = max(
            o.get("tarih") or "" for o in kayit["olcumler"]
        )
        kayit["bu_kosuda_goruldu"] = True
        kayitlar[kayit_id] = kayit

    for kayit_id, kayit in kayitlar.items():
        if kayit_id not in bu_kosuda:
            kayit["bu_kosuda_goruldu"] = False

    gozlemler = sorted(
        kayitlar.values(),
        key=lambda x: (x["vertikal"], x["kalem_adi"], x["urun_adi"].casefold()),
    )
    for x in gozlemler:
        x.pop("seo_kisa_adi", None)
    _baslik_adlarini_ayir(gozlemler)
    vertikal_sayilari = defaultdict(int)
    for x in gozlemler:
        vertikal_sayilari[x["vertikal"]] += 1
    return {
        "sema_surumu": SEMA_SURUMU,
        "uretim_tarihi": date.today().isoformat(),
        "gozlem_sayfasi": len(gozlemler),
        "bu_kosuda_gorulen": len(bu_kosuda),
        "vertikaller": dict(sorted(vertikal_sayilari.items())),
        "gozlemler": gozlemler,
    }


def _son_olcumler(kayit: dict) -> list[dict]:
    son_tarih = kayit["son_olcum_tarihi"]
    return [o for o in kayit["olcumler"] if o.get("tarih") == son_tarih]


def _schema(kayit: dict, fiyatlar: list[float], url: str) -> dict:
    sonlar = _son_olcumler(kayit)
    soru = f"{kayit['urun_adi']} fiyatı ne kadar?"
    cevap = (
        f"{kayit['son_olcum_tarihi']} tarihli kaynak gözlemlerinde ortanca fiyat "
        f"{_para(statistics.median(fiyatlar))}."
    )
    offer = {
        "@type": "AggregateOffer",
        "priceCurrency": "TRY",
        "lowPrice": min(fiyatlar),
        "highPrice": max(fiyatlar),
        "offerCount": len(sonlar),
    }
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Product", "name": kayit["urun_adi"], "url": url,
                "category": kayit["kalem_adi"], "offers": offer,
            },
            {
                "@type": "FAQPage",
                "mainEntity": [{
                    "@type": "Question", "name": soru,
                    "acceptedAnswer": {"@type": "Answer", "text": cevap},
                }],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Ana sayfa",
                     "item": su.SITE_KOK_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Fiyat gözlemleri",
                     "item": su.SITE_KOK_URL + "/fiyat/"},
                    {"@type": "ListItem", "position": 3, "name": kayit["vertikal_adi"],
                     "item": su.SITE_KOK_URL + f"/fiyat/{kayit['vertikal']}/"},
                    {"@type": "ListItem", "position": 4, "name": kayit["urun_adi"],
                     "item": url},
                ],
            },
        ],
    }


def gozlem_sayfasi(kayit: dict, ayni_kalem: list[dict]) -> str:
    sonlar = _son_olcumler(kayit)
    fiyatlar = [o["fiyat_tl"] for o in sonlar]
    medyan = statistics.median(fiyatlar)
    url = f"{su.SITE_KOK_URL}/fiyat/{kayit['slug']}/"
    soru = f"{kayit['urun_adi']} fiyatı ne kadar?"
    durum = "güncel taramada görüldü" if kayit["bu_kosuda_goruldu"] else "son görülen ölçüm"
    kategori_medyan = next(
        (o.get("kategori_ortancasi_tl") for o in reversed(kayit["olcumler"])
         if o.get("kategori_ortancasi_tl")), None
    )
    fark = ((medyan / kategori_medyan - 1) * 100) if kategori_medyan else None
    fark_metni = ""
    if fark is not None:
        yon = "üzerinde" if fark >= 0 else "altında"
        fark_metni = (
            f" Bu gözlem, {kayit['kalem_adi']} kategori ortancasının "
            f"%{abs(fark):.0f} {yon}."
        )
    kaynak_satirlari = "".join(
        f'<tr><td>{html.escape(o["kaynak_adi"])}</td>'
        f'<td>{html.escape(o["tarih"])}</td><td class="sayi">{_para(o["fiyat_tl"])}</td></tr>'
        for o in sorted(sonlar, key=lambda x: x["fiyat_tl"])
    )
    gecmis = list(reversed(kayit["olcumler"]))[:20]
    gecmis_satirlari = "".join(
        f'<tr><td>{html.escape(o["tarih"])}</td><td>{html.escape(o["kaynak_adi"])}</td>'
        f'<td class="sayi">{_para(o["fiyat_tl"])}</td></tr>' for o in gecmis
    )
    ilgili = [x for x in ayni_kalem if x["id"] != kayit["id"]][:8]
    ilgili_html = " · ".join(
        f'<a href="/fiyat/{x["slug"]}/">{html.escape(x["urun_adi"])}</a>' for x in ilgili
    ) or f'<a href="/{kayit["vertikal_yolu"]}/">{html.escape(kayit["vertikal_adi"])}</a>'
    schema = _schema(kayit, fiyatlar, url)
    title = f"{kayit['seo_kisa_adi']} Fiyatı 2026 | Maliyeti Ne?"
    aciklama = (
        f"{kayit['urun_adi']} fiyatı {_para(medyan)}. Ölçüm "
        f"{kayit['son_olcum_tarihi']}; {len(sonlar)} kaynak gözlemi ve kategori karşılaştırması."
    )
    return f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(aciklama)}">
<link rel="canonical" href="{url}">
{su.STIL_ETIKETLERI}<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(aciklama)}">
<meta property="og:type" content="website"><meta property="og:url" content="{url}">
{su.OG_ETIKETLERI}<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
{su.ANALITIK}</head><body>
<header class="ust-bar"><div class="kapsayici"><a href="/" class="logo">Maliyeti <span>Ne?</span></a>
<nav class="ust-menu">{su.genel_menu()}</nav></div></header>
<main class="kapsayici">
<nav class="kirinti" aria-label="Sayfa yolu"><a href="/">Ana sayfa</a> <span>›</span>
<a href="/fiyat/">Fiyat gözlemleri</a> <span>›</span>
<a href="/fiyat/{kayit['vertikal']}/">{html.escape(kayit['vertikal_adi'])}</a> <span>›</span>
<span>{html.escape(kayit['urun_adi'])}</span></nav>
<h1>{html.escape(soru)}</h1>
<div class="cevap-blok"><strong>{kayit['son_olcum_tarihi']}</strong> tarihli kaynak
gözlemlerinde ortanca fiyat <strong>{_para(medyan)}</strong>. Bu kayıt
<strong>{durum}</strong>; {len(sonlar)} kaynak fiyatı aynı ürün adı altında
birleştirildi.{fark_metni}</div>
<p class="sonuc-alt-metin">Bu rakam kategori tahmini değil, kaynakta bu adla listelenen
ürünün ölçümüdür. Kampanya, stok ve teslimat koşulları sonradan değişebilir.</p>
<h2>Son kaynak fiyatları</h2><div class="tablo-sarmal"><table><thead><tr>
<th>Kaynak</th><th>Ölçüm</th><th class="sayi">Fiyat</th></tr></thead>
<tbody>{kaynak_satirlari}</tbody></table></div>
<h2>Kategoriyle karşılaştırma</h2><p><a href="/{kayit['vertikal_yolu']}/">
{html.escape(kayit['vertikal_adi'])}</a> içindeki <a href="/{kayit['vertikal_yolu']}/">
{html.escape(kayit['kalem_adi'])}</a> serisinin ölçülen ürün ortancası
<strong>{_para(kategori_medyan)}</strong>. Tek ürün fiyatı ile kategori ortancası aynı metrik değildir.</p>
<h2>{html.escape(soru)}</h2><p>{kayit['son_olcum_tarihi']} tarihli ölçümlerde
cevap <strong>{_para(medyan)}</strong>. Kaynak fiyatları farklıysa tek kaynak seçmek yerine
ortanca kullanılır.</p>
<h2>Fiyat geçmişi</h2><div class="tablo-sarmal"><table><thead><tr>
<th>Ölçüm</th><th>Kaynak</th><th class="sayi">Fiyat</th></tr></thead>
<tbody>{gecmis_satirlari}</tbody></table></div>
<h2>Nasıl doğrulanır?</h2><p>Ham kategori verisi:
<a href="/veri/{kayit['vertikal']}.json">JSON</a> ·
<a href="/{kayit['vertikal_yolu']}/metodoloji/">yöntem ve sınırlar</a> ·
<a href="/veri/">veri merkezi</a>. Alıntıda ürün adını ve ölçüm tarihini birlikte kullanın.</p>
<h2>Benzer fiyat gözlemleri</h2><p>{ilgili_html}</p>
</main><footer><div class="kapsayici"><div>© 2026 Maliyeti Ne? ·
<a href="/fiyat/">Fiyat gözlemleri</a> · <a href="/veri/">Veri</a> ·
<a href="/hakkimizda/">Hakkımızda</a></div></div></footer></body></html>"""


def _hub_sayfasi(envanter: dict) -> str:
    satirlar = "".join(
        f'<tr><td><a href="/fiyat/{v}/">{html.escape(su.VERTIKALLER[v]["ad"])}</a></td>'
        f'<td class="sayi">{n}</td></tr>'
        for v, n in envanter["vertikaller"].items()
    )
    url = su.SITE_KOK_URL + "/fiyat/"
    return f"""<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Güncel Ürün ve Model Fiyatları 2026 | Maliyeti Ne?</title>
<meta name="description" content="{envanter['gozlem_sayfasi']} gerçek ürün, model ve paket fiyatı; kaynak, ölçüm tarihi, fiyat geçmişi ve kategori karşılaştırmasıyla.">
<link rel="canonical" href="{url}">{su.STIL_ETIKETLERI}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:title" content="Güncel Ürün ve Model Fiyatları 2026 | Maliyeti Ne?">
<meta property="og:description" content="{envanter['gozlem_sayfasi']} gerçek fiyat gözlemi; kaynak ve tarihle.">
<meta property="og:type" content="website"><meta property="og:url" content="{url}">
{su.OG_ETIKETLERI}<meta name="twitter:card" content="summary_large_image">
{su.ANALITIK}</head><body>
<header class="ust-bar"><div class="kapsayici"><a href="/" class="logo">Maliyeti <span>Ne?</span></a>
<nav class="ust-menu">{su.genel_menu()}</nav></div></header><main class="kapsayici">
<nav class="kirinti" aria-label="Sayfa yolu"><a href="/">Ana sayfa</a> <span>›</span><span>Fiyat gözlemleri</span></nav>
<h1>Güncel ürün ve model fiyatları</h1><div class="cevap-blok">
Kaynaklarda adı ve fiyatı birlikte görülen <strong>{envanter['gozlem_sayfasi']} ürün,
model ve paket</strong> için ayrı fiyat kaydı yayınlıyoruz. Her sayfada kaynak,
ölçüm tarihi, kategori ortancası ve varsa geçmiş ölçümler bulunur.</div>
<h2>Kategoriler</h2><div class="tablo-sarmal"><table><thead><tr><th>Endeks</th>
<th class="sayi">Fiyat sayfası</th></tr></thead><tbody>{satirlar}</tbody></table></div>
<h2>Bu arşiv neden var?</h2><p>Endeks sayfaları bir kategorinin ortancasını,
buradaki sayfalar ise kaynakta görülen tekil ürün veya model fiyatını cevaplar.
İkisi birbirinin yerine kullanılmaz. Yeni gerçek gözlemler geldikçe arşiv büyür;
eski URL'ler ölçüm tarihiyle korunur.</p><p><a href="/veri/fiyat-gozlemleri.json">
Makine-okunur envanteri indirin</a> · <a href="/veri/">Veri merkezi</a></p>
</main><footer><div class="kapsayici"><div>© 2026 Maliyeti Ne? · <a href="/veri/">Veri</a> ·
<a href="/hakkimizda/">Hakkımızda</a></div></div></footer></body></html>"""


def _vertikal_hub(vertikal: str, kayitlar: list[dict]) -> str:
    conf = su.VERTIKALLER[vertikal]
    gruplar = defaultdict(list)
    for x in kayitlar:
        gruplar[x["kalem_adi"]].append(x)
    bolumler = []
    for kalem, urunler in sorted(gruplar.items()):
        linkler = "".join(
            f'<li><a href="/fiyat/{x["slug"]}/">{html.escape(x["urun_adi"])}</a> '
            f'<span class="sonuc-alt-metin">{html.escape(x["son_olcum_tarihi"])}</span></li>'
            for x in urunler
        )
        bolumler.append(f'<h2>{html.escape(kalem)} fiyatları</h2><ul>{linkler}</ul>')
    url = f"{su.SITE_KOK_URL}/fiyat/{vertikal}/"
    return f"""<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(conf['ad'])} Ürün Fiyatları 2026 | Maliyeti Ne?</title>
<meta name="description" content="{html.escape(conf['ad'])} için {len(kayitlar)} gerçek ürün/model fiyat gözlemi; kaynak ve tarihle.">
<link rel="canonical" href="{url}">{su.STIL_ETIKETLERI}<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:title" content="{html.escape(conf['ad'])} Ürün Fiyatları 2026 | Maliyeti Ne?">
<meta property="og:description" content="{len(kayitlar)} gerçek ürün/model fiyat gözlemi; kaynak ve tarihle.">
<meta property="og:type" content="website"><meta property="og:url" content="{url}">
{su.OG_ETIKETLERI}<meta name="twitter:card" content="summary_large_image">
{su.ANALITIK}</head><body><header class="ust-bar"><div class="kapsayici">
<a href="/" class="logo">Maliyeti <span>Ne?</span></a><nav class="ust-menu">{su.genel_menu()}</nav>
</div></header><main class="kapsayici"><nav class="kirinti" aria-label="Sayfa yolu">
<a href="/">Ana sayfa</a> <span>›</span><a href="/fiyat/">Fiyat gözlemleri</a>
<span>›</span><span>{html.escape(conf['ad'])}</span></nav>
<h1>{html.escape(conf['ad'])} ürün ve model fiyatları</h1>
<div class="cevap-blok"><strong>{len(kayitlar)} gerçek fiyat gözlemi</strong> kaynak adı,
ölçüm tarihi ve kategori bağlantısıyla listeleniyor.</div>{''.join(bolumler)}
</main><footer><div class="kapsayici"><div>© 2026 Maliyeti Ne? ·
<a href="/fiyat/">Fiyat gözlemleri</a> · <a href="/{conf['yol']}/">{html.escape(conf['ad'])}</a>
</div></div></footer></body></html>"""


def sitemap_yollari(envanter_dosyasi: Path = ENVANTER_DOSYASI) -> list[str]:
    envanter = _mevcut_envanter(envanter_dosyasi)
    yollar = ["fiyat/"]
    vertikaller = sorted({x["vertikal"] for x in envanter.get("gozlemler", [])})
    yollar.extend(f"fiyat/{v}/" for v in vertikaller)
    yollar.extend(f"fiyat/{x['slug']}/" for x in envanter.get("gozlemler", []))
    return yollar


def main() -> int:
    envanter = envanter_uret()
    ENVANTER_DOSYASI.write_text(
        json.dumps(envanter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    FIYAT_KOK.mkdir(parents=True, exist_ok=True)
    (FIYAT_KOK / "index.html").write_text(_hub_sayfasi(envanter), encoding="utf-8")
    gruplar = defaultdict(list)
    kalem_gruplari = defaultdict(list)
    for kayit in envanter["gozlemler"]:
        gruplar[kayit["vertikal"]].append(kayit)
        kalem_gruplari[(kayit["vertikal"], kayit["kalem_id"])].append(kayit)
    for vertikal, kayitlar in gruplar.items():
        hedef = FIYAT_KOK / vertikal / "index.html"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(_vertikal_hub(vertikal, kayitlar), encoding="utf-8")
    for kayit in envanter["gozlemler"]:
        hedef = FIYAT_KOK / kayit["slug"] / "index.html"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(
            gozlem_sayfasi(
                kayit, kalem_gruplari[(kayit["vertikal"], kayit["kalem_id"])]
            ),
            encoding="utf-8",
        )
    print(
        f"Fiyat gozlemleri: {envanter['gozlem_sayfasi']} sayfa, "
        f"{len(gruplar)} vertikal hub"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
