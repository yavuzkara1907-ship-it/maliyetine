# -*- coding: utf-8 -*-
"""
Maliyeti Ne? - Evcil hayvan hub sayfasi (/evcil-hayvan/)

Yavuz (2026-07-28): "evcil hayvan vertikalinin icinde kedi ve kopek
iki ayri yatay olsun."

NEDEN TEK VERTIKAL DEGIL, HUB + IKI VERTIKAL
--------------------------------------------
Iki hayvani tek vertikalde birlestirmek iki sorun dogururdu:

1. TOPLAM ANLAMSIZ OLURDU. Kimse hem kedi hem kopek mamasi almiyor;
   bu iki liste birbirinin ALTERNATIFI. Toplamak, arac vertikalinde
   yasadigimiz "marka kalemleri toplanmaz" hatasinin aynisi olurdu -
   orada Tesla + BYD + Suzuki toplanip 17,7 milyon TL gibi kimsenin
   odemedigi bir sayi cikmisti.

2. "kedi masrafi" ve "kopek masrafi" AYRI ARAMA SORGULARI. Ikisini
   tek sayfada birlestirmek her ikisinde de zayiflatirdi.

Bu yuzden her hayvan kendi vertikali: kendi toplami, kendi
hesaplayicisi, kendi sayfasi. Hub ikisini YAN YANA gosterir ve
ASLA TOPLAMAZ - sayfada bunun nedeni de yazili.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import sayfa_uret as su

SITE_KOK = su.SITE_KOK
SITE_KOK_URL = su.SITE_KOK_URL
YOL = "evcil-hayvan"


def vertikaller() -> list[str]:
    return [v for v, c in su.VERTIKALLER.items() if c.get("evcil_hayvan")]


def _kartlar(ozetler: list[dict]) -> str:
    parcalar = []
    for o in ozetler:
        parcalar.append(
            '    <a class="kart" href="/{yol}/">\n'
            "      <h2>{ad} masrafı</h2>\n"
            '      <p class="kart-rakam">{rakam}</p>\n'
            '      <p class="kart-alt">{alt} · {kalem} kalem</p>\n'
            "    </a>\n".format(
                yol=o["yol"], ad=o["ad"], rakam=su._para(o["toplam"]),
                alt=o["kart_alt"], kalem=o["gercek_kalem"])
        )
    return "".join(parcalar)


def _json_ld(ozetler: list[dict], url: str, bugun: str) -> str:
    sorular = [{
        "@type": "Question",
        "name": "2026'da {} bakım masrafı ne kadar?".format(o["ad"].lower()),
        "acceptedAnswer": {"@type": "Answer", "text": (
            "Maliyeti Ne? verilerine göre {} itibarıyla {} {} tutuyor. "
            "Bu rakam {} kalem için ölçülen fiyatlardan derlendi; mama, kum "
            "ve ped gibi aylık sarf giderleri ayrı gösteriliyor.".format(
                o["guncelleme_tarihi"] or bugun, o["anasayfa_ifade"],
                su._para(o["toplam"]), o["gercek_kalem"]))},
    } for o in ozetler]

    return json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "name": "Evcil Hayvan Masrafı",
             "url": url, "inLanguage": "tr-TR",
             "description": "Kedi ve köpek bakım masrafı, ölçülmüş fiyatlardan."},
            {"@type": "ItemList", "itemListElement": [
                {"@type": "ListItem", "position": i,
                 "name": "{} masrafı".format(o["ad"]),
                 "url": "{}/{}/".format(SITE_KOK_URL, o["yol"])}
                for i, o in enumerate(ozetler, start=1)]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Ana sayfa",
                 "item": SITE_KOK_URL + "/"},
                {"@type": "ListItem", "position": 2, "name": "Evcil Hayvan",
                 "item": url}]},
            {"@type": "FAQPage", "mainEntity": sorular},
        ],
    }, ensure_ascii=False, indent=1)


def uret(veri_kok: Path | None = None) -> str | None:
    """Verisi olan hayvan yoksa None doner - bos hub sayfasi acilmaz."""
    ozetler = [o for o in (su.vertikal_ozeti(v, veri_kok) for v in vertikaller()) if o]
    if not ozetler:
        return None

    url = "{}/{}/".format(SITE_KOK_URL, YOL)
    bugun = date.today().isoformat()
    cumle = " · ".join(
        "{} için {}".format(o["ad"].lower(), su._para(o["toplam"])) for o in ozetler)
    # Semadaki sorular sayfada da GORUNUR olmali (Google politikasi).
    sorular = json.loads(_json_ld(ozetler, url, bugun))["@graph"][-1]["mainEntity"]
    sss = su._sss_html(sorular)

    return """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Evcil Hayvan Masrafı 2026 — Kedi ve Köpek | Maliyeti Ne?</title>
<meta name="description" content="Kedi ve köpek bakım masrafı ayrı ayrı, ölçülmüş fiyatlarla. Tek seferlik kurulum ile aylık sarf gideri ayrı gösteriliyor.">
<link rel="canonical" href="{url}">
<meta property="og:title" content="Evcil Hayvan Masrafı 2026 — Kedi ve Köpek">
<meta property="og:description" content="Kedi ve köpek bakım masrafı ayrı ayrı, ölçülmüş fiyatlarla.">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
{og}
<meta name="twitter:card" content="summary_large_image">
{stil_etiketleri}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<script type="application/ld+json">
{json_ld}
</script>
{analitik}
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">Maliyeti <span>Ne?</span></a>
    <nav class="ust-menu">{menu}</nav>
  </div>
</header>

<main class="kapsayici">
  <nav class="kirinti" aria-label="Sayfa yolu">
    <a href="/">Ana sayfa</a> <span aria-hidden="true">›</span> <span>Evcil Hayvan</span>
  </nav>

  <h1>2026 Evcil Hayvan Masrafı</h1>

  <div class="cevap-blok">
    Tek seferlik başlangıç kurulumu {cumle} tutuyor. Mama, kum ve ped gibi
    <strong>aylık sarf giderleri bu rakamlara dahil değil</strong> — tek
    seferlik alınan eşyayla her ay tekrarlayan gideri aynı toplama katmak
    yanıltıcı olurdu, o yüzden ayrı gösteriyoruz.
  </div>

  <div class="kart-grid">
{kartlar}  </div>

  <section class="icerik-bolumu">
    <h2>Kedi ve köpek rakamları neden toplanmıyor?</h2>
    <p>
      Çünkü toplamı kimsenin ödemediği bir sayı olurdu. Bu iki liste
      birbirinin <em>alternatifi</em>: bir kişi kedi ya da köpek sahiplenir,
      ikisinin masrafını birden üstlenmez. Aynı ilkeyi
      <a href="/arac/">0 km araç endeksinde</a> de uyguluyoruz — orada da
      marka fiyatları birbirinin alternatifi olduğu için toplanmıyor.
    </p>
  </section>

  <section class="icerik-bolumu">
    <h2>Aylık gider neden ayrı?</h2>
    <p>
      Yatak bir kez alınır, mama her ay tekrar eder. Bebek endeksinde
      kurduğumuz ayrım burada da geçerli: mama, kum ve çiş pedi varsayılan
      toplama girmez, her hayvanın kendi sayfasında aylık tutarıyla ayrıca
      listelenir. İki rakamı birleştirmek "kedi masrafı 20 bin TL" gibi ne
      olduğu belirsiz bir sayı üretirdi.
    </p>
  </section>

{sss}
  <p class="kunye">Her rakamın yanında kaynak sayısı ve derleme tarihi
    yazılıdır · <a href="/veri/">Ham veriyi indirin</a></p>

</main>

<footer>
  <div class="kapsayici">
    <div>© {yil} Maliyeti Ne? · <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a> · <a href="/sss/">SSS</a> · <a href="/rehber/">Rehber</a> · <a href="/veri/">Veri</a></div>
    <nav class="footer-endeksler" aria-label="Tüm endeksler">{endeksler}</nav>
  </div>
</footer>

</body>
</html>
""".format(url=url, og=su.OG_ETIKETLERI, json_ld=_json_ld(ozetler, url, bugun),
           stil_etiketleri=su.STIL_ETIKETLERI,
           analitik=su.ANALITIK, menu=su.genel_menu(YOL), cumle=cumle,
           kartlar=_kartlar(ozetler), sss=sss, yil=bugun[:4],
           endeksler=su.TUM_ENDEKS_LINKLERI)


def yaz(veri_kok: Path | None = None) -> Path | None:
    html = uret(veri_kok)
    if not html:
        return None
    hedef = SITE_KOK / YOL / "index.html"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(html, encoding="utf-8")
    return hedef


def main():
    yol = yaz()
    if not yol:
        print("Evcil hayvan verisi yok - hub uretilmedi.")
        return 1
    print("Evcil hayvan hub'i:", str(yol).replace(str(SITE_KOK), ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
