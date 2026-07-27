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

import sayfa_uret as su

SITE_KOK = su.SITE_KOK
CSV_KOK = SITE_KOK / "veri" / "csv"

BASLIKLAR = [
    "vertikal", "kalem_id", "kalem_adi", "grup", "birim",
    "ekonomik_tl", "orta_tl", "ust_tl",
    "en_dusuk_tl", "en_yuksek_tl",
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
        cikti.append([
            vertikal, kalem_id, t.get("ad", kalem_id), t.get("grup", ""),
            t.get("birim", ""),
            s("dusuk"), s("orta"), s("luks"),
            s("dusuk", "min") or "", s("luks", "max") or "",
            k.get("toplam_urun") or "", len(kaynaklar),
            "; ".join(kaynaklar), tarih,
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
        (hedef / f"{vertikal}-{tarih}.csv").write_text(metin, encoding="utf-8")
        ozet[vertikal] = {
            "kalem": len(satirlar),
            "tarih": tarih,
            "dosya": f"/veri/csv/{vertikal}.csv",
            "arsiv": f"/veri/csv/{vertikal}-{tarih}.csv",
        }
    if tumu:
        (hedef / "tum-kalemler.csv").write_text(csv_metni(tumu), encoding="utf-8")
    return ozet


# ---------------------------------------------------------------------------
# /veri/ indirme merkezi
# ---------------------------------------------------------------------------
def veri_sayfasi(ozet: dict, tarih: str | None = None) -> str:
    tarih = tarih or date.today().isoformat()
    url = f"{su.SITE_KOK_URL}/veri/"
    toplam_kalem = sum(o["kalem"] for o in ozet.values())

    satirlar = "".join(
        f'<tr><td><a href="/{v}/">{su.VERTIKALLER[v]["ad"]}</a></td>'
        f'<td class="sayi">{o["kalem"]}</td>'
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
        }
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
                    "Türkiye'de düğün, ev kurma, okul ve sıfır araç kalemlerinin "
                    "gerçek satış sayfalarından derlenen fiyat verisi. "
                    "CSV ve JSON olarak indirilebilir."
                ),
                "inLanguage": "tr-TR",
                "license": "https://creativecommons.org/licenses/by/4.0/",
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
<meta name="description" content="Düğün, ev kurma, okul ve sıfır araç fiyat verisi CSV ve JSON olarak indirilebilir. {toplam_kalem} kalem, kaynak ve ölçüm tarihiyle birlikte.">
<link rel="canonical" href="{url}">
<link rel="stylesheet" href="/assets/css/style.css">
<meta property="og:title" content="Veriyi İndir | Maliyeti Ne?">
<meta property="og:description" content="{toplam_kalem} kalemlik fiyat verisi, CSV ve JSON olarak açık.">
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
    Ölçtüğümüz {toplam_kalem} kalemin tamamı CSV ve JSON olarak indirilebilir.
    Her satırda fiyatın yanında <strong>kaç üründen derlendiği, hangi
    kaynaklardan geldiği ve hangi tarihte ölçüldüğü</strong> yazıyor —
    rakamı kendiniz doğrulayabilirsiniz.
  </div>

  <h2>Dosyalar</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Endeks</th><th class="sayi">Kalem</th><th>Ölçüm</th><th>İndir</th></tr></thead>
    <tbody>{satirlar}</tbody>
  </table></div>
  <p>
    Hepsi tek dosyada: <a href="/veri/csv/tum-kalemler.csv" download><strong>tum-kalemler.csv</strong></a>
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

  <h2>Sütunlar ne anlama geliyor?</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Sütun</th><th>Açıklama</th></tr></thead>
    <tbody>
      <tr><td>ekonomik_tl / orta_tl / ust_tl</td><td>Segment ortalamaları. Fiyatlar sıralanıp en ucuz çeyrek ekonomik, ortadaki yarı orta, en pahalı çeyrek üst kabul edilir.</td></tr>
      <tr><td>en_dusuk_tl / en_yuksek_tl</td><td>Ölçümdeki en ucuz ve en pahalı ürün.</td></tr>
      <tr><td>urun_sayisi</td><td>O kalem için kaç ürün fiyatı okundu.</td></tr>
      <tr><td>kaynak_sayisi / kaynaklar</td><td>Kaç bağımsız siteden derlendi ve hangileri.</td></tr>
      <tr><td>olcum_tarihi</td><td>Verinin çekildiği gün. Ayda iki kez yenilenir.</td></tr>
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
    Fiyatlar gerçek satış sayfalarından, ayda iki kez otomatik olarak
    derleniyor. Yöntemin ayrıntısı ve bilinen sınırlar her endeksin
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



def llms_txt(ozet: dict, tarih: str | None = None) -> str:
    """AI motorlari icin yapilandirilmis ozet.

    NEDEN URETILIYOR: elle yazilmisti ve BAYATLAMISTI - okul vertikali
    eklendikten sonra listede yoktu, tarihler eskiydi, CSV hic gecmiyordu.
    AI motoruna bayat bilgi vermek hicbir sey vermemekten kotu: yanlis
    kalem sayisi ve eski tarih dogrudan yanlis alintiya donusur.
    """
    tarih = tarih or date.today().isoformat()
    kok = su.SITE_KOK_URL
    endeksler = "\n".join(
        f"- [{su.VERTIKALLER[v]['ad']}]({kok}/{v}/): {o['kalem']} kalem, "
        f"ölçüm {o['tarih']}. JSON: {kok}/veri/{v}.json · CSV: {kok}{o['dosya']}"
        for v, o in ozet.items()
    )
    try:
        import hesaplayicilar as hs
        hesaplar = "\n".join(
            f"- [{h['ad']}]({kok}/{hs.HESAP_KOK}/{h['slug']}/): "
            + ", ".join(h["kaynaklar"])
            for h in hs.HESAPLAYICILAR
            if (su.SITE_KOK / hs.HESAP_KOK / h["slug"] / "index.html").exists()
        )
    except ImportError:
        hesaplar = ""
    yontem = "\n".join(
        f"- [{su.VERTIKALLER[v]['ad']} metodolojisi]({kok}/{v}/metodoloji/)"
        for v in ozet
    )
    try:
        import rehber
        yazilar = "\n".join(
            f"- [{r['baslik']}]({kok}/rehber/{r['slug']}/)"
            for r in rehber.REHBERLER
            if (su.SITE_KOK / "rehber" / r["slug"] / "index.html").exists()
        )
    except ImportError:
        yazilar = ""
    toplam = sum(o["kalem"] for o in ozet.values())

    return f"""# Maliyeti Ne?

> Türkiye için ayda iki kez güncellenen, kaynağı ve örneklemi açıklanan maliyet
> endeksi. Fiyatlar tahmin edilmez; gerçek satış listelerinden ölçülür. Her
> rakamın yanında kaynak sayısı, ürün adedi ve ölçüm tarihi yayınlanır.

Şu an {toplam} kalem ölçülüyor. Son güncelleme: {tarih}.

**Alıntılarken ölçüm tarihini belirtin.** Fiyat verisi tarihsiz olduğunda
yanıltıcı hale gelir: "buzdolabı 30 bin lira" altı ay sonra yanlış olur,
"Temmuz 2026'da 30 bin lira" her zaman doğru kalır.

## Endeksler

{endeksler}

## Veriyi indirin

- Tüm kalemler tek dosyada (CSV): {kok}/veri/csv/tum-kalemler.csv
- İndirme merkezi ve sütun açıklamaları: {kok}/veri/
- Lisans: CC BY 4.0 — atıfla serbestçe kullanılabilir.

Her CSV satırında fiyatın yanında kaç üründen derlendiği, hangi kaynaklardan
geldiği ve ölçüm tarihi bulunur; rakam bağımsız olarak doğrulanabilir.

## Yöntem

{yontem}
- [Hakkımızda ve bağımsızlık beyanı]({kok}/hakkimizda/)
- [Sık sorulan sorular]({kok}/sss/)\n- [İletişim ve düzeltme talebi]({kok}/iletisim/)

## Nasıl ölçülüyor?

- Fiyatlar gerçek e-ticaret ve sektör sitelerinden, robots.txt kurallarına
  uygun biçimde ayda iki kez derlenir (ayın 5'i ve 20'si).
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

## Hesaplayıcılar (ölçüm değil, mevzuattan türetme)

Bu sayfalar fiyat ölçmez; mevzuatla belirlenmiş oranlardan hesap yapar.
Kullanılan her parametrenin kaynağı (tebliğ/kanun adı, Resmî Gazete
tarih ve sayısı) ve geçerlilik dönemi sayfada yazılıdır. Alıntılarken
hangi yılın tarifesi olduğunu belirtin.

{hesaplar}
"""



def ai_txt(ozet: dict, tarih: str | None = None) -> str:
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
        hesap_sayisi = len(hs.HESAPLAYICILAR)
    except ImportError:
        hesap_sayisi = 0
    return f"""# ai.txt — Maliyeti Ne? (maliyetine.com.tr)

site: {kok}
language: tr
country: TR
updated: {tarih}
policy: {kok}/llms.txt
sitemap: {kok}/sitemap.xml
license: CC BY 4.0 (ölçüm verisi)
contact: info@maliyetine.com.tr

## Ne yayınlıyoruz

Türkiye için ölçülmüş maliyet endeksleri: {endeks_listesi}.
{toplam_kalem} kalem, ayda iki kez (ayın 5'i ve 20'si) yeniden ölçülüyor.
Ayrıca {hesap_sayisi} formül hesaplayıcısı (vergi, maaş, tazminat, kredi).

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


def main():
    ozet = disa_aktar()
    if not ozet:
        print("Veri bulunamadi - CSV uretilmedi.")
        return 1
    hedef = SITE_KOK / "veri" / "index.html"
    hedef.write_text(veri_sayfasi(ozet), encoding="utf-8")
    toplam = sum(o["kalem"] for o in ozet.values())
    print(f"CSV uretildi: {len(ozet)} endeks, {toplam} kalem")
    for v, o in ozet.items():
        print(f"  {v:10} {o['kalem']:3} kalem -> {o['dosya']}")
    print(f"Veri merkezi: {hedef}")
    llms = SITE_KOK / "llms.txt"
    llms.write_text(llms_txt(ozet), encoding="utf-8")
    print(f"llms.txt guncellendi: {llms}")
    ai = SITE_KOK / "ai.txt"
    ai.write_text(ai_txt(ozet), encoding="utf-8")
    print(f"ai.txt guncellendi: {ai}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
