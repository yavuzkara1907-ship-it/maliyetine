# -*- coding: utf-8 -*-
"""Marka, kategori, degisim ve karsilastirma kesif yuzeyini uretir.

Bu katman rakip fiyat sitelerinin talep yakalayan URL mimarisini kullanir;
ancak her sayfa Maliyeti Ne?'nin mevcut fiyat gozlemi veya tarihsel serisinden
uretilir. Veri yoksa URL acilmaz.
"""

from __future__ import annotations

import html
import json
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from itertools import combinations
from pathlib import Path

import fiyat_gozlemleri as fg
import sayfa_uret as su


SITE_KOK = su.SITE_KOK
VERI_KOK = SITE_KOK / "veri"
ENVANTER_DOSYASI = VERI_KOK / "kesif-yuzeyi.json"
MARKA_KOK = SITE_KOK / "marka"
KATEGORI_KOK = SITE_KOK / "kategori"
KARSILASTIR_KOK = SITE_KOK / "karsilastir"
RAPORLAR_KOK = SITE_KOK / "raporlar"

MARKA_ESIGI = 2
ARAC_KARSILASTIRMA_ESIGI = 4

SAHTE_MARKA_BASLANGICLARI = {
    "acik", "aktif", "ankastre", "bebek", "buz", "digital", "d.s",
    "ekonomik", "firsat", "flex", "kapali", "kampanya", "natural",
    "orijinal", "ovbzd41", "pro", "trend", "xxl", "yeni",
}
IKI_KELIMELI_MARKALAR = {
    "n&d", "pro plan", "royal canin", "baby turco", "little swimmers",
}


def _slug(metin: str) -> str:
    ceviri = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "Ş": "s",
                            "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u",
                            "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"})
    sade = unicodedata.normalize("NFKD", metin.translate(ceviri))
    sade = "".join(c for c in sade if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", sade).strip("-")


def _para(deger: float | int | None) -> str:
    return su._para(deger) if deger is not None else "—"


def _seo_kisa(ad: str, sinir: int = 24) -> str:
    temiz = re.sub(r"\s*\([^)]*\)\s*", " ", ad).strip()
    return temiz if len(temiz) <= sinir else temiz[:sinir - 1].rstrip() + "…"


def _kalem_yolu(vertikal: str, kalem_id: str) -> str:
    conf = su.VERTIKALLER[vertikal]
    for sayfa in conf.get("kalem_sayfalari", []):
        if sayfa.get("id") == kalem_id:
            return f"/{conf['yol']}/{sayfa['slug']}/"
    aday = SITE_KOK / conf["yol"] / f"{kalem_id}-fiyatlari" / "index.html"
    if aday.exists():
        return f"/{conf['yol']}/{kalem_id}-fiyatlari/"
    return f"/{conf['yol']}/"


def _sayfa(
    *, baslik: str, aciklama: str, yol: str, h1: str, govde: str,
    schema: dict | None = None,
) -> str:
    url = f"{su.SITE_KOK_URL}/{yol.strip('/')}/"
    schema_html = ""
    if schema:
        schema_html = (
            '<script type="application/ld+json">'
            + json.dumps(schema, ensure_ascii=False)
            + "</script>"
        )
    return f"""<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(baslik)}</title>
<meta name="description" content="{html.escape(aciklama)}">
<link rel="canonical" href="{url}">{su.STIL_ETIKETLERI}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:title" content="{html.escape(baslik)}">
<meta property="og:description" content="{html.escape(aciklama)}">
<meta property="og:type" content="website"><meta property="og:url" content="{url}">
{su.OG_ETIKETLERI}<meta name="twitter:card" content="summary_large_image">
{schema_html}{su.ANALITIK}</head><body><header class="ust-bar"><div class="kapsayici">
<a href="/" class="logo">Maliyeti <span>Ne?</span></a>
<nav class="ust-menu">{su.genel_menu()}</nav></div></header>
<main class="kapsayici"><nav class="kirinti" aria-label="Sayfa yolu">
<a href="/">Ana sayfa</a> <span>›</span><span>{html.escape(h1)}</span></nav>
<h1>{html.escape(h1)}</h1>{govde}</main><footer><div class="kapsayici"><div>
© 2026 Maliyeti Ne? · <a href="/fiyat/">Fiyatlar</a> ·
<a href="/markalar/">Markalar</a> · <a href="/kategoriler/">Kategoriler</a> ·
<a href="/veri/">Veri</a></div></div></footer></body></html>"""


def _envanter_oku(dosya: Path = fg.ENVANTER_DOSYASI) -> dict:
    return json.loads(dosya.read_text(encoding="utf-8"))


def _marka_adi(kayit: dict) -> str | None:
    if kayit["vertikal"] == "arac" and kayit["kalem_id"] != "en-ucuz-sifir-arac":
        return kayit["kalem_adi"]
    ad = re.sub(r"\s+", " ", kayit["urun_adi"]).strip()
    dusuk = ad.casefold()
    for aday in IKI_KELIMELI_MARKALAR:
        if dusuk == aday or dusuk.startswith(aday + " "):
            return aday.title() if aday != "n&d" else "N&D"
    ilk = re.split(r"[ /]", ad)[0].strip("-–—,.;:")
    if (len(ilk) < 2 or ilk[0].isdigit() or _slug(ilk) in SAHTE_MARKA_BASLANGICLARI
            or not re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", ilk)):
        return None
    return ilk


def marka_gruplari(gozlemler: list[dict]) -> dict[str, dict]:
    ham = defaultdict(list)
    yazimlar = defaultdict(Counter)
    for kayit in gozlemler:
        marka = _marka_adi(kayit)
        if not marka:
            continue
        anahtar = _slug(marka)
        ham[anahtar].append(kayit)
        yazimlar[anahtar][marka] += 1
    gruplar = {}
    for slug, urunler in ham.items():
        benzersiz = {x["id"]: x for x in urunler}
        if len(benzersiz) < MARKA_ESIGI:
            continue
        ad = yazimlar[slug].most_common(1)[0][0]
        if ad.isupper() and len(ad) > 4:
            ad = ad.title()
        gruplar[slug] = {"slug": slug, "ad": ad, "urunler": list(benzersiz.values())}
    return dict(sorted(gruplar.items(), key=lambda x: x[1]["ad"].casefold()))


def kategori_gruplari(gozlemler: list[dict]) -> dict[str, dict]:
    ham = defaultdict(list)
    for kayit in gozlemler:
        ham[(kayit["vertikal"], kayit["kalem_id"])].append(kayit)
    gruplar = {}
    for (vertikal, kalem_id), urunler in ham.items():
        slug = kalem_id
        if slug in gruplar:
            slug = f"{vertikal}-{kalem_id}"
        gruplar[slug] = {
            "slug": slug, "vertikal": vertikal, "kalem_id": kalem_id,
            "ad": urunler[0]["kalem_adi"], "urunler": urunler,
        }
    return dict(sorted(gruplar.items(), key=lambda x: x[1]["ad"].casefold()))


def _son_fiyat(kayit: dict) -> float:
    sonlar = fg._son_olcumler(kayit)
    return statistics.median(o["fiyat_tl"] for o in sonlar)


def _urun_listesi(urunler: list[dict], sinir: int | None = None) -> str:
    sirali = sorted(urunler, key=lambda x: (_son_fiyat(x), x["urun_adi"].casefold()))
    if sinir:
        sirali = sirali[:sinir]
    return "".join(
        f'<tr><td><a href="/fiyat/{x["slug"]}/">{html.escape(x["urun_adi"])}</a></td>'
        f'<td>{html.escape(x["kalem_adi"])}</td><td>{html.escape(x["son_olcum_tarihi"])}</td>'
        f'<td class="sayi">{_para(_son_fiyat(x))}</td></tr>' for x in sirali
    )


def _liste_schema(ad: str, yol: str, urunler: list[dict]) -> dict:
    return {
        "@context": "https://schema.org", "@type": "ItemList", "name": ad,
        "url": f"{su.SITE_KOK_URL}/{yol.strip('/')}/",
        "numberOfItems": len(urunler),
        "itemListElement": [
            {"@type": "ListItem", "position": i,
             "name": x["urun_adi"],
             "url": f"{su.SITE_KOK_URL}/fiyat/{x['slug']}/"}
            for i, x in enumerate(sorted(urunler, key=_son_fiyat), 1)
        ],
    }


def _marka_sayfasi(grup: dict) -> str:
    urunler = grup["urunler"]
    fiyatlar = [_son_fiyat(x) for x in urunler]
    kategoriler = Counter(x["kalem_adi"] for x in urunler)
    kategori_metni = ", ".join(f"{k} ({v})" for k, v in kategoriler.most_common())
    h1 = f"{grup['ad']} ürün ve model fiyatları"
    govde = f"""<div class="cevap-blok"><strong>{len(urunler)} gerçek {html.escape(grup['ad'])}
ürün/model gözlemi</strong> içinde fiyatlar {_para(min(fiyatlar))} ile
{_para(max(fiyatlar))} arasında; ortanca {_para(statistics.median(fiyatlar))}.</div>
<p class="sonuc-alt-metin">Kapsam: {html.escape(kategori_metni)}. Fiyatlar aynı gün ve
aynı ürün türü olmayabilir; aşağıdaki kategori alanı karşılaştırma sınırını gösterir.</p>
<h2>{html.escape(grup['ad'])} fiyat listesi</h2><div class="tablo-sarmal"><table>
<thead><tr><th>Ürün veya model</th><th>Kategori</th><th>Ölçüm</th>
<th class="sayi">Fiyat</th></tr></thead><tbody>{_urun_listesi(urunler)}</tbody></table></div>
<h2>Veri nasıl okunmalı?</h2><p>Bu sayfa marka adıyla eşleşen kaynak gözlemlerini
bir araya getirir. Tekil sayfalarda kaynak, tarih ve geçmiş ayrıntısı bulunur.
Marka ortancası farklı ürün türlerini içeriyorsa satın alma karşılaştırması sayılmaz.</p>"""
    return _sayfa(
        baslik=f"{_seo_kisa(grup['ad'], 23)} Marka Fiyat Arşivi 2026 | Maliyeti Ne?",
        aciklama=(f"{grup['ad']} için {len(urunler)} gerçek ürün ve model fiyatı; "
                  f"{_para(min(fiyatlar))} - {_para(max(fiyatlar))} aralığı, kaynak ve tarih."),
        yol=f"marka/{grup['slug']}", h1=h1, govde=govde,
        schema=_liste_schema(h1, f"marka/{grup['slug']}", urunler),
    )


def _markalar_hub(gruplar: dict[str, dict]) -> str:
    satirlar = "".join(
        f'<tr><td><a href="/marka/{g["slug"]}/">{html.escape(g["ad"])}</a></td>'
        f'<td class="sayi">{len(g["urunler"])}</td></tr>' for g in gruplar.values()
    )
    govde = f"""<div class="cevap-blok">En az {MARKA_ESIGI} gerçek ürün/model gözlemi
bulunan <strong>{len(gruplar)} marka</strong> listeleniyor.</div>
<div class="tablo-sarmal"><table><thead><tr><th>Marka</th>
<th class="sayi">Fiyat kaydı</th></tr></thead><tbody>{satirlar}</tbody></table></div>"""
    return _sayfa(
        baslik="Markalar ve Güncel Ürün Fiyatları 2026 | Maliyeti Ne?",
        aciklama=f"{len(gruplar)} marka için kaynak ve tarih içeren ürün/model fiyat listeleri.",
        yol="markalar", h1="Markalar ve güncel fiyatları", govde=govde,
    )


def _kategori_sayfasi(grup: dict) -> str:
    urunler = grup["urunler"]
    fiyatlar = [_son_fiyat(x) for x in urunler]
    h1 = f"{grup['ad']} marka ve model fiyat listesi"
    govde = f"""<div class="cevap-blok"><strong>{len(urunler)} kaynak gözlemi</strong>
içinde en düşük fiyat {_para(min(fiyatlar))}, en yüksek fiyat {_para(max(fiyatlar))},
ürün/model ortancası {_para(statistics.median(fiyatlar))}.</div>
<p class="sonuc-alt-metin">Bu liste kaynaklarda adı ve fiyatı birlikte yayımlanan örnekleri
gösterir; tüm pazarın eksiksiz ürün kataloğu değildir.</p>
<h2>{html.escape(grup['ad'])} modelleri ve fiyatları</h2><div class="tablo-sarmal"><table>
<thead><tr><th>Ürün veya model</th><th>Kategori</th><th>Ölçüm</th>
<th class="sayi">Fiyat</th></tr></thead><tbody>{_urun_listesi(urunler)}</tbody></table></div>
<h2>Kategori ortancası ile farkı</h2><p><a href="/{su.VERTIKALLER[grup['vertikal']]['yol']}/">
{html.escape(su.VERTIKALLER[grup['vertikal']]['ad'])}</a> endeksi pazar örnekleminin
ortancasını; bu sayfa ise adlandırılmış tekil ürün ve modelleri listeler.</p>"""
    return _sayfa(
        baslik=f"{_seo_kisa(grup['ad'])} Model Fiyatları 2026 | Maliyeti Ne?",
        aciklama=(f"{grup['ad']} için {len(urunler)} gerçek ürün/model fiyatı; "
                  f"{_para(min(fiyatlar))} - {_para(max(fiyatlar))} aralığı."),
        yol=f"kategori/{grup['slug']}", h1=h1, govde=govde,
        schema=_liste_schema(h1, f"kategori/{grup['slug']}", urunler),
    )


def _kategoriler_hub(gruplar: dict[str, dict]) -> str:
    satirlar = "".join(
        f'<tr><td><a href="/kategori/{g["slug"]}/">{html.escape(g["ad"])}</a></td>'
        f'<td>{html.escape(su.VERTIKALLER[g["vertikal"]]["ad"])}</td>'
        f'<td class="sayi">{len(g["urunler"])}</td></tr>' for g in gruplar.values()
    )
    govde = f"""<div class="cevap-blok"><strong>{len(gruplar)} fiyat kategorisi</strong>,
tekil ürün ve model kayıtlarına doğrudan erişim sağlıyor.</div>
<div class="tablo-sarmal"><table><thead><tr><th>Kategori</th><th>Endeks</th>
<th class="sayi">Kayıt</th></tr></thead><tbody>{satirlar}</tbody></table></div>"""
    return _sayfa(
        baslik="Fiyat Kategorileri ve Model Listeleri 2026 | Maliyeti Ne?",
        aciklama=f"{len(gruplar)} kategoride kaynaklı ürün ve model fiyat listeleri.",
        yol="kategoriler", h1="Fiyat kategorileri", govde=govde,
    )


def _tarihsel_seriler(gecmis_kok: Path = VERI_KOK / "gecmis") -> list[dict]:
    seriler = []
    for vertikal, conf in su.VERTIKALLER.items():
        dosya = gecmis_kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        veri = json.loads(dosya.read_text(encoding="utf-8"))
        adlar = {x["id"]: x["ad"] for x in conf["kalemler"]}
        for kalem_id, kayit in (veri.get("kalemler") or {}).items():
            seri = [x for x in kayit.get("seri", []) if x.get("medyan") is not None]
            if len(seri) < 2:
                continue
            seriler.append({
                "vertikal": vertikal, "vertikal_adi": conf["ad"],
                "vertikal_yolu": conf["yol"], "kalem_id": kalem_id,
                "kalem_adi": adlar.get(kalem_id, kalem_id.replace("-", " ").title()),
                "seri": sorted(seri, key=lambda x: x["tarih"]),
            })
    return seriler


def _degisimler(seriler: list[dict], gun: int) -> list[dict]:
    sonuclar = []
    for kayit in seriler:
        seri = kayit["seri"]
        son = seri[-1]
        son_tarih = datetime.fromisoformat(son["tarih"]).date()
        hedef = son_tarih - timedelta(days=gun)
        adaylar = [x for x in seri[:-1] if datetime.fromisoformat(x["tarih"]).date() <= hedef]
        if adaylar:
            once = adaylar[-1]
        else:
            once = seri[0]
            gercek_gun = (son_tarih - datetime.fromisoformat(once["tarih"]).date()).days
            if gercek_gun < max(5, int(gun * .75)):
                continue
        if not once.get("medyan"):
            continue
        fark = (son["medyan"] / once["medyan"] - 1) * 100
        gercek_gun = (son_tarih - datetime.fromisoformat(once["tarih"]).date()).days
        sonuclar.append({**{k: kayit[k] for k in kayit if k != "seri"},
                         "once": once, "son": son, "degisim_yuzde": fark,
                         "gun_araligi": gercek_gun})
    return sorted(sonuclar, key=lambda x: abs(x["degisim_yuzde"]), reverse=True)


def _degisim_tablosu(kayitlar: list[dict]) -> str:
    return "".join(
        f'<tr><td><a href="{_kalem_yolu(x["vertikal"], x["kalem_id"])}">'
        f'{html.escape(x["kalem_adi"])}</a></td><td>{x["once"]["tarih"]}</td>'
        f'<td class="sayi">{_para(x["once"]["medyan"])}</td><td>{x["son"]["tarih"]}</td>'
        f'<td class="sayi">{_para(x["son"]["medyan"])}</td>'
        f'<td class="sayi">%{x["degisim_yuzde"]:+.1f}</td></tr>' for x in kayitlar
    )


def _degisim_sayfasi(kayitlar: list[dict], gun: int) -> str:
    h1 = f"Son {gun} günde fiyatı değişenler"
    govde = f"""<div class="cevap-blok"><strong>{len(kayitlar)} fiyat serisi</strong>
için son ölçüm, {gun} gün önceki veya bu tarihe en yakın eski ölçümle karşılaştırıldı.</div>
<p class="sonuc-alt-metin">Ürün örneklemi veya kaynak sayısı değiştiğinde fark yalnız etiket
zammını göstermez. Her satırdaki gerçek başlangıç ve bitiş tarihini birlikte okuyun.</p>
<div class="tablo-sarmal"><table><thead><tr><th>Fiyat serisi</th><th>İlk ölçüm</th>
<th class="sayi">İlk</th><th>Son ölçüm</th><th class="sayi">Son</th>
<th class="sayi">Değişim</th></tr></thead><tbody>{_degisim_tablosu(kayitlar)}</tbody></table></div>"""
    return _sayfa(
        baslik=f"Son {gun} Günde Fiyatı Değişenler 2026 | Maliyeti Ne?",
        aciklama=f"{len(kayitlar)} fiyat serisinde son {gun} günlük artış ve düşüşler; tarihli ölçümlerle.",
        yol=f"fiyati-degisen/{gun}-gun", h1=h1, govde=govde,
    )


def _yon_sayfasi(kayitlar: list[dict], artis: bool) -> str:
    secilen = [x for x in kayitlar if (x["degisim_yuzde"] > 0) == artis]
    secilen.sort(key=lambda x: x["degisim_yuzde"], reverse=artis)
    ad = "Zamlanan" if artis else "Ucuzlayan"
    govde = f"""<div class="cevap-blok">Son 30 güne en yakın karşılaştırmada
<strong>{len(secilen)} {ad.casefold()} fiyat serisi</strong> bulundu.</div>
<p class="sonuc-alt-metin">Liste kategori ortancalarını izler; tek mağazanın kampanya etiketi
değildir. Örneklem değişimi farkı etkileyebilir.</p><div class="tablo-sarmal"><table>
<thead><tr><th>Fiyat serisi</th><th>İlk ölçüm</th><th class="sayi">İlk</th>
<th>Son ölçüm</th><th class="sayi">Son</th><th class="sayi">Değişim</th></tr></thead>
<tbody>{_degisim_tablosu(secilen)}</tbody></table></div>"""
    return _sayfa(
        baslik=f"{ad} Ürün Kategorileri 2026 | Maliyeti Ne?",
        aciklama=f"Son 30 güne en yakın ölçümlerde {ad.casefold()} ürün kategorileri ve fiyat değişimleri.",
        yol="zamlanan-urunler" if artis else "ucuzlayan-urunler",
        h1=f"{ad} ürün kategorileri", govde=govde,
    )


def arac_karsilastirmalari(gozlemler: list[dict]) -> list[dict]:
    gruplar = defaultdict(list)
    for x in gozlemler:
        if x["vertikal"] == "arac" and x["kalem_id"] != "en-ucuz-sifir-arac":
            gruplar[x["kalem_id"]].append(x)
    yeterli = [(k, v) for k, v in gruplar.items() if len(v) >= ARAC_KARSILASTIRMA_ESIGI]
    sonuc = []
    for (a_id, a), (b_id, b) in combinations(sorted(yeterli), 2):
        a_ad, b_ad = a[0]["kalem_adi"], b[0]["kalem_adi"]
        sonuc.append({
            "slug": f"{_slug(a_ad)}-vs-{_slug(b_ad)}-sifir-arac-fiyatlari",
            "a_id": a_id, "a_ad": a_ad, "a": a,
            "b_id": b_id, "b_ad": b_ad, "b": b,
        })
    return sonuc


def _marka_ozeti(urunler: list[dict]) -> dict:
    fiyatlar = [_son_fiyat(x) for x in urunler]
    en_ucuz = min(urunler, key=_son_fiyat)
    return {"medyan": statistics.median(fiyatlar), "min": min(fiyatlar),
            "max": max(fiyatlar), "sayi": len(urunler), "en_ucuz": en_ucuz}


def _karsilastirma_sayfasi(k: dict) -> str:
    a, b = _marka_ozeti(k["a"]), _marka_ozeti(k["b"])
    ucuz = k["a_ad"] if a["min"] < b["min"] else k["b_ad"]
    h1 = f"{k['a_ad']} ve {k['b_ad']} sıfır araç fiyat karşılaştırması"
    faq_soru = (f"{k['a_ad']} ve {k['b_ad']} arasında hangisinin "
                "başlangıç fiyatı daha düşük?")
    faq_cevap = (
        f"Ölçülen başlangıç fiyatlarında {ucuz} daha ucuz. "
        f"{k['a_ad']} başlangıcı {_para(a['min'])}, "
        f"{k['b_ad']} başlangıcı {_para(b['min'])}."
    )
    satirlar = "".join(
        f'<tr><td><a href="/fiyat/{x["slug"]}/">{html.escape(x["urun_adi"])}</a></td>'
        f'<td class="sayi">{_para(_son_fiyat(x))}</td></tr>'
        for x in sorted(k["a"] + k["b"], key=_son_fiyat)[:12]
    )
    govde = f"""<div class="cevap-blok">Ölçülen liste fiyatlarında en ucuz model
<strong>{html.escape(ucuz)}</strong> tarafında. {html.escape(k['a_ad'])} başlangıcı
{_para(a['min'])}, {html.escape(k['b_ad'])} başlangıcı {_para(b['min'])}.</div>
<div class="tablo-sarmal"><table><thead><tr><th>Marka</th><th class="sayi">Model</th>
<th class="sayi">En düşük</th><th class="sayi">Ortanca</th><th class="sayi">En yüksek</th>
</tr></thead><tbody><tr><td>{html.escape(k['a_ad'])}</td><td class="sayi">{a['sayi']}</td>
<td class="sayi">{_para(a['min'])}</td><td class="sayi">{_para(a['medyan'])}</td>
<td class="sayi">{_para(a['max'])}</td></tr><tr><td>{html.escape(k['b_ad'])}</td>
<td class="sayi">{b['sayi']}</td><td class="sayi">{_para(b['min'])}</td>
<td class="sayi">{_para(b['medyan'])}</td><td class="sayi">{_para(b['max'])}</td></tr></tbody></table></div>
<h2>En uygun fiyatlı modeller</h2><div class="tablo-sarmal"><table><thead>
<tr><th>Model/paket</th><th class="sayi">Liste fiyatı</th></tr></thead><tbody>{satirlar}</tbody></table></div>
<h2>Karar sınırı</h2><p>Bu karşılaştırma liste fiyatını cevaplar; motor, donanım,
teslim süresi, kampanya, ikinci el değeri ve kullanım maliyeti eşitlenmemiştir.
“Daha ucuz” ifadesi yalnız ölçülen başlangıç fiyatı içindir.</p>
<h2>{html.escape(faq_soru)}</h2><p>{html.escape(faq_cevap)}</p>"""
    return _sayfa(
        baslik=f"{k['a_ad']} vs {k['b_ad']} Sıfır Araç Fiyatları | Maliyeti Ne?",
        aciklama=(f"{k['a_ad']} ve {k['b_ad']} sıfır araç fiyatları: başlangıç, "
                  "ortanca, model sayısı ve en uygun paketlerin tarihli karşılaştırması."),
        yol=f"karsilastir/{k['slug']}", h1=h1, govde=govde,
        schema={
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{
                "@type": "Question",
                "name": faq_soru,
                "acceptedAnswer": {"@type": "Answer", "text": faq_cevap},
            }],
        },
    )


def _karsilastir_hub(karsilastirmalar: list[dict]) -> str:
    linkler = "".join(
        f'<li><a href="/karsilastir/{x["slug"]}/">{html.escape(x["a_ad"])} vs '
        f'{html.escape(x["b_ad"])} sıfır araç fiyatları</a></li>' for x in karsilastirmalar
    )
    govde = f"""<div class="cevap-blok">En az {ARAC_KARSILASTIRMA_ESIGI} gerçek model
fiyatı bulunan markalar arasında <strong>{len(karsilastirmalar)} karşılaştırma</strong>.</div>
<ul>{linkler}</ul>"""
    return _sayfa(
        baslik="Sıfır Araç Marka Fiyat Karşılaştırmaları | Maliyeti Ne?",
        aciklama=f"{len(karsilastirmalar)} sıfır araç marka karşılaştırması; başlangıç ve ortanca fiyatlarla.",
        yol="karsilastir", h1="Sıfır araç fiyat karşılaştırmaları", govde=govde,
    )


def _rapor_sayfasi(vertikal: str, seriler: list[dict]) -> str:
    conf = su.VERTIKALLER[vertikal]
    ilgili = [x for x in seriler if x["vertikal"] == vertikal]
    satirlar = "".join(
        f'<tr><td><a href="{_kalem_yolu(x["vertikal"], x["kalem_id"])}">'
        f'{html.escape(x["kalem_adi"])}</a></td><td>{x["seri"][0]["tarih"]}</td>'
        f'<td class="sayi">{_para(x["seri"][0]["medyan"])}</td><td>{x["seri"][-1]["tarih"]}</td>'
        f'<td class="sayi">{_para(x["seri"][-1]["medyan"])}</td></tr>' for x in ilgili
    )
    govde = f"""<div class="cevap-blok"><strong>{len(ilgili)} tarihsel fiyat serisi</strong>
ilk ve son ölçümleriyle bir arada.</div><div class="tablo-sarmal"><table><thead>
<tr><th>Seri</th><th>İlk tarih</th><th class="sayi">İlk</th><th>Son tarih</th>
<th class="sayi">Son</th></tr></thead><tbody>{satirlar}</tbody></table></div>"""
    return _sayfa(
        baslik=f"{conf['ad']} Fiyat Raporu 2026 | Maliyeti Ne?",
        aciklama=f"{conf['ad']} için {len(ilgili)} tarihsel fiyat serisinin ilk ve son ölçümleri.",
        yol=f"raporlar/{vertikal}", h1=f"{conf['ad']} fiyat raporu", govde=govde,
    )


def _raporlar_hub(seriler: list[dict]) -> str:
    sayilar = Counter(x["vertikal"] for x in seriler)
    linkler = "".join(
        f'<li><a href="/raporlar/{v}/">{html.escape(su.VERTIKALLER[v]["ad"])} fiyat raporu</a> '
        f'({n} seri)</li>' for v, n in sorted(sayilar.items())
    )
    govde = f"""<div class="cevap-blok"><strong>{len(seriler)} tarihsel seri</strong>
için endeks bazında ilk/son ölçüm raporları.</div><ul>{linkler}</ul>
<p><a href="/rapor/">Aylık Türkiye maliyet raporunu inceleyin</a> ·
<a href="/fiyati-degisen/7-gun/">7 günlük değişimler</a> ·
<a href="/fiyati-degisen/30-gun/">30 günlük değişimler</a> ·
<a href="/zamlanan-urunler/">zamlananlar</a> ·
<a href="/ucuzlayan-urunler/">ucuzlayanlar</a></p>"""
    return _sayfa(
        baslik="Fiyat ve Maliyet Raporları 2026 | Maliyeti Ne?",
        aciklama=f"{len(seriler)} tarihsel fiyat serisi için kategori raporları ve değişim tabloları.",
        yol="raporlar", h1="Fiyat ve maliyet raporları", govde=govde,
    )


def _yaz(yol: Path, icerik: str) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(icerik, encoding="utf-8")


def envanter_uret(fiyat_envanteri: dict | None = None) -> dict:
    fiyat_envanteri = fiyat_envanteri or _envanter_oku()
    gozlemler = fiyat_envanteri["gozlemler"]
    markalar = marka_gruplari(gozlemler)
    kategoriler = kategori_gruplari(gozlemler)
    karsilastirmalar = arac_karsilastirmalari(gozlemler)
    seriler = _tarihsel_seriler()
    rapor_vertikalleri = sorted({x["vertikal"] for x in seriler})
    yollar = ["markalar/", "kategoriler/", "karsilastir/", "raporlar/",
              "fiyati-degisen/7-gun/", "fiyati-degisen/30-gun/",
              "zamlanan-urunler/", "ucuzlayan-urunler/"]
    yollar += [f"marka/{x}/" for x in markalar]
    yollar += [f"kategori/{x}/" for x in kategoriler]
    yollar += [f"karsilastir/{x['slug']}/" for x in karsilastirmalar]
    yollar += [f"raporlar/{x}/" for x in rapor_vertikalleri]
    return {
        "sema_surumu": 1, "uretim_tarihi": date.today().isoformat(),
        "toplam_sayfa": len(yollar), "marka_sayfasi": len(markalar),
        "kategori_sayfasi": len(kategoriler),
        "karsilastirma_sayfasi": len(karsilastirmalar),
        "rapor_sayfasi": 1 + len(rapor_vertikalleri),
        "degisim_sayfasi": 4,
        "markalar": [
            {"ad": g["ad"], "urun_sayisi": len(g["urunler"]),
             "url": f"{su.SITE_KOK_URL}/marka/{g['slug']}/"}
            for g in markalar.values()
        ],
        "kategoriler": [
            {"ad": g["ad"], "urun_sayisi": len(g["urunler"]),
             "url": f"{su.SITE_KOK_URL}/kategori/{g['slug']}/"}
            for g in kategoriler.values()
        ],
        "karsilastirmalar": [
            {"marka_a": x["a_ad"], "marka_b": x["b_ad"],
             "url": f"{su.SITE_KOK_URL}/karsilastir/{x['slug']}/"}
            for x in karsilastirmalar
        ],
        "yollar": yollar,
    }


def sitemap_yollari(envanter_dosyasi: Path = ENVANTER_DOSYASI) -> list[str]:
    if not envanter_dosyasi.exists():
        return []
    veri = json.loads(envanter_dosyasi.read_text(encoding="utf-8"))
    return veri.get("yollar", [])


def main() -> int:
    fiyat_envanteri = _envanter_oku()
    gozlemler = fiyat_envanteri["gozlemler"]
    markalar = marka_gruplari(gozlemler)
    kategoriler = kategori_gruplari(gozlemler)
    karsilastirmalar = arac_karsilastirmalari(gozlemler)
    seriler = _tarihsel_seriler()
    degisim_7 = _degisimler(seriler, 7)
    degisim_30 = _degisimler(seriler, 30)

    _yaz(SITE_KOK / "markalar/index.html", _markalar_hub(markalar))
    for slug, grup in markalar.items():
        _yaz(MARKA_KOK / slug / "index.html", _marka_sayfasi(grup))
    _yaz(SITE_KOK / "kategoriler/index.html", _kategoriler_hub(kategoriler))
    for slug, grup in kategoriler.items():
        _yaz(KATEGORI_KOK / slug / "index.html", _kategori_sayfasi(grup))
    _yaz(KARSILASTIR_KOK / "index.html", _karsilastir_hub(karsilastirmalar))
    for k in karsilastirmalar:
        _yaz(KARSILASTIR_KOK / k["slug"] / "index.html", _karsilastirma_sayfasi(k))
    _yaz(SITE_KOK / "fiyati-degisen/7-gun/index.html", _degisim_sayfasi(degisim_7, 7))
    _yaz(SITE_KOK / "fiyati-degisen/30-gun/index.html", _degisim_sayfasi(degisim_30, 30))
    _yaz(SITE_KOK / "zamlanan-urunler/index.html", _yon_sayfasi(degisim_30, True))
    _yaz(SITE_KOK / "ucuzlayan-urunler/index.html", _yon_sayfasi(degisim_30, False))
    _yaz(RAPORLAR_KOK / "index.html", _raporlar_hub(seriler))
    for vertikal in sorted({x["vertikal"] for x in seriler}):
        _yaz(RAPORLAR_KOK / vertikal / "index.html", _rapor_sayfasi(vertikal, seriler))

    envanter = envanter_uret(fiyat_envanteri)
    ENVANTER_DOSYASI.write_text(
        json.dumps(envanter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Kesif yuzeyi: {envanter['toplam_sayfa']} sayfa "
        f"({envanter['marka_sayfasi']} marka, {envanter['kategori_sayfasi']} kategori, "
        f"{envanter['karsilastirma_sayfasi']} karsilastirma)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
