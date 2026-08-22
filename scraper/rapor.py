# -*- coding: utf-8 -*-
"""Guncel maliyet raporu, RSS ve dagitim paketi uretir.

Raporun butun rakamlari yayinlanan JSON'lardan gelir. Bu modul yeni fiyat
hesaplamaz; mevcut olcum sozlesmesini gazeteci, sosyal medya ve RSS icin
tek, alintilanabilir bir yayina donusturur.
"""

from __future__ import annotations

import html
import json
from datetime import date, datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape as xml_escape

from envanter import envanter_ozeti
import sayfa_uret as su
import sosyal


SITE_KOK = su.SITE_KOK
RAPOR_URL = f"{su.SITE_KOK_URL}/rapor/"
AYLAR = (
    "", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
)


def _manifest(veri_kok: Path) -> dict:
    yol = veri_kok / "manifest.json"
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def rapor_verisi(veri_kok: Path | None = None) -> dict:
    kok = veri_kok or SITE_KOK / "veri"
    envanter = envanter_ozeti(kok, su.VERTIKALLER)
    ozetler = [
        o for o in (su.vertikal_ozeti(v, kok) for v in su.VERTIKALLER) if o
    ]
    if not ozetler:
        raise ValueError("Rapor için yayınlanmış endeks verisi bulunamadı")

    tarih_metni = max(o["guncelleme_tarihi"] for o in ozetler if o.get("guncelleme_tarihi"))
    tarih = date.fromisoformat(tarih_metni)
    degisimler = sosyal.degisim_adaylari(kok / "gecmis")
    manifest = _manifest(kok)
    return {
        "tarih": tarih_metni,
        "baslik": f"{AYLAR[tarih.month]} {tarih.year} Türkiye Maliyet Raporu",
        "envanter": envanter,
        "endeksler": ozetler,
        "degisimler": degisimler,
        "dataset_surumu": manifest.get("dataset_surumu", ""),
    }


def _endeks_tablosu(veri: dict) -> str:
    satirlar = []
    for o in veri["endeksler"]:
        kapsam = o.get("kart_alt") or o["anasayfa_ifade"]
        satirlar.append(
            f'<tr><td><a href="/{o["yol"]}/">{html.escape(o["ad"])}</a>'
            f'<span class="tablo-not">{html.escape(kapsam)}</span></td>'
            f'<td class="sayi">{su._para(o["toplam"])}</td>'
            f'<td class="sayi">{o["gercek_kalem"]}</td>'
            f'<td class="sayi">{o["site_sayisi"]}</td>'
            f'<td>{o["guncelleme_tarihi"]}</td></tr>'
        )
    return "\n".join(satirlar)


def _degisimler_html(veri: dict) -> str:
    if not veri["degisimler"]:
        return (
            '<p>Karşılaştırılabilir iki ölçüm arasında; örneklemi kararlı, '
            'en az iki bağımsız kaynakla doğrulanmış ve %3 eşiğini geçen bir '
            'fiyat değişimi bulunmadı.</p>'
        )
    bloklar = []
    for aday in veri["degisimler"][:5]:
        ad = sosyal._kalem_adi(aday["vertikal"], aday["kalem_id"]) or aday["kalem_id"]
        metin = html.escape(aday["metin"]).replace("\n\n", "<br>")
        bloklar.append(
            '<article class="degisim-satir">'
            f'<h3><a href="{aday["url"]}">{html.escape(ad)}</a></h3>'
            f'<p>{metin}</p>'
            f'<p class="sonuc-alt-metin">{aday["kaynak_sayisi"]} bağımsız kaynak · '
            f'{aday.get("olcum_tarihi") or veri["tarih"]}</p></article>'
        )
    return '<div class="degisim-liste">' + "".join(bloklar) + "</div>"


def rapor_html(veri: dict) -> str:
    e = veri["envanter"]
    baslik = veri["baslik"]
    aciklama = (
        f"{e['fiyat_serisi']} fiyat serisi ve {e['kaynak']} bağımsız kaynaktan "
        f"üretilen {baslik.lower()}; güncel endeksler ve doğrulanmış değişimler."
    )
    paylasim = f"{baslik}: {e['fiyat_serisi']} fiyat serisi, {e['kaynak']} bağımsız kaynak."
    alinti = (
        f"Maliyeti Ne?, {baslik}, son veri {veri['tarih']}, "
        f"{RAPOR_URL} (erişim: {date.today().isoformat()})."
    )
    kurum = {"@type": "Organization", "name": "Maliyeti Ne?", "url": su.SITE_KOK_URL}
    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Report",
                "headline": baslik,
                "description": aciklama,
                "url": RAPOR_URL,
                "datePublished": veri["tarih"],
                "dateModified": veri["tarih"],
                "inLanguage": "tr-TR",
                "author": kurum,
                "publisher": kurum,
                "isBasedOn": f"{su.SITE_KOK_URL}/veri/",
            },
            {
                "@type": "Dataset",
                "name": f"{baslik} veri özeti",
                "url": f"{su.SITE_KOK_URL}/veri/rapor.json",
                "dateModified": veri["tarih"],
                "creator": kurum,
                "license": "https://creativecommons.org/licenses/by/4.0/",
                "isAccessibleForFree": True,
                **({"version": veri["dataset_surumu"]} if veri["dataset_surumu"] else {}),
            },
        ],
    }
    whatsapp = "https://wa.me/?text=" + quote(paylasim + " " + RAPOR_URL)
    linkedin = "https://www.linkedin.com/sharing/share-offsite/?url=" + quote(RAPOR_URL)
    x_url = "https://twitter.com/intent/tweet?text=" + quote(paylasim) + "&url=" + quote(RAPOR_URL)
    surum = (
        f' · Veri sürümü: <a href="/veri/manifest.json"><code>{veri["dataset_surumu"]}</code></a>'
        if veri["dataset_surumu"] else ""
    )
    return f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{baslik} | Maliyeti Ne?</title>
<meta name="description" content="{html.escape(aciklama)}">
<link rel="canonical" href="{RAPOR_URL}">
{su.STIL_ETIKETLERI}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:title" content="{baslik}">
<meta property="og:description" content="{html.escape(aciklama)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{RAPOR_URL}">
{su.og_etiketleri("/assets/og/maliyet-raporu.png", baslik)}
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False, indent=2)}</script>
{su.ANALITIK}
</head>
<body>
<header class="ust-bar"><div class="kapsayici">
  <a href="/" class="logo">Maliyeti <span>Ne?</span></a>
  <nav class="ust-menu">{su.genel_menu("rapor")}</nav>
</div></header>
<main class="kapsayici">
  <nav class="kirinti" aria-label="Sayfa yolu"><a href="/">Ana sayfa</a>
    <span aria-hidden="true">›</span> <span>Türkiye Maliyet Raporu</span></nav>
  <section class="rapor-ust">
    <span class="guncelleme-etiketi">Son veri: {veri["tarih"]}</span>
    <h1>{baslik}</h1>
    <div class="cevap-blok rapor-spot">Türkiye'de düğün, ev kurma, okul alışverişi, bebek,
      evcil hayvan ve sıfır araç maliyetlerinin aynı ölçüm sözleşmesiyle
      hazırlanmış güncel görünümü.</div>
    <div class="rapor-istatistikler">
      <div class="rapor-istatistik"><strong>{e["fiyat_serisi"]}</strong><span>fiyat serisi</span></div>
      <div class="rapor-istatistik"><strong>{e["kaynak"]}</strong><span>bağımsız kaynak</span></div>
      <div class="rapor-istatistik"><strong>{e["cok_kaynakli"]}</strong><span>çok kaynaklı seri</span></div>
      <div class="rapor-istatistik"><strong>{len(veri["endeksler"])}</strong><span>canlı endeks</span></div>
    </div>
    <p class="sonuc-alt-metin">Rakamlar farklı satın alma senaryolarıdır;
      birbirleriyle toplanmaz. Her satırın kapsamı ayrıca yazılır{surum}.</p>
  </section>

  <section class="icerik-bolumu">
    <h2>Güncel maliyet görünümü</h2>
    <div class="tablo-sarmal"><table>
      <thead><tr><th>Endeks ve kapsam</th><th class="sayi">Orta senaryo</th>
      <th class="sayi">Kalem</th><th class="sayi">Kaynak</th><th>Son veri</th></tr></thead>
      <tbody>{_endeks_tablosu(veri)}</tbody>
    </table></div>
  </section>

  <section class="icerik-bolumu">
    <h2>Doğrulanmış fiyat değişimleri</h2>
    <p>Yalnız en az 10 gün aralıklı ölçümler, kararlı örneklem, %3 ve üzeri
      değişim ve en az iki bağımsız kaynak eşiğini geçen hareketler burada
      yayımlanır. Resmî araç liste fiyatları ikinci kaynak gerektirmez.</p>
    {_degisimler_html(veri)}
  </section>

  <section class="icerik-bolumu">
    <h2>Paylaşın ve kaynak gösterin</h2>
    <p>Bu rapor bağlantısı her ölçümde güncellenir. Belirli bir rakamı
      kullanırken satırdaki son veri tarihini de belirtin.</p>
    <div class="paylasim-araclari" aria-label="Raporu paylaş">
      <a href="{whatsapp}" rel="nofollow noopener">WhatsApp</a>
      <a href="{linkedin}" rel="nofollow noopener">LinkedIn</a>
      <a href="{x_url}" rel="nofollow noopener">X</a>
      <button type="button" id="raporu-paylas">Paylaş</button>
      <button type="button" id="alintiyi-kopyala">Alıntıyı kopyala</button>
    </div>
    <p class="alinti-kunyesi" id="alinti-kunyesi">{html.escape(alinti)}</p>
    <p><a href="/feed.xml">RSS ile takip edin</a> ·
      <a href="/veri/rapor.json">Rapor verisini JSON olarak alın</a> ·
      <a href="/veri/">Tüm CSV ve JSON dosyaları</a></p>
  </section>

  <section class="icerik-bolumu">
    <h2>Nasıl hazırlanıyor?</h2>
    <p>Kaynaklar ayın 5'i ve 20'sinde yeniden taranır. Başarısız veya kalite
      kontrolünü geçmeyen ölçüm eski sağlıklı verinin tarihini ileri taşımaz.
      Ürün fiyatlarında kaynak başına ortanca, ardından kaynaklar arası
      ortanca kullanılır. Ayrıntılı yöntem ve kapsam sınırları
      <a href="/veri/">veri merkezinde</a> yayımlanır.</p>
  </section>
</main>
<footer><div class="kapsayici">
  <div>© {veri["tarih"][:4]} Maliyeti Ne? · <a href="/rapor/">Rapor</a> ·
    <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a> ·
    <a href="/veri/">Veri</a></div>
  <nav class="footer-endeksler" aria-label="Tüm endeksler">{su.TUM_ENDEKS_LINKLERI}</nav>
</div></footer>
<script>
(function() {{
  const url = {json.dumps(RAPOR_URL)};
  const title = {json.dumps(baslik, ensure_ascii=False)};
  const text = {json.dumps(paylasim, ensure_ascii=False)};
  const citation = {json.dumps(alinti, ensure_ascii=False)};
  const share = document.getElementById('raporu-paylas');
  const copy = document.getElementById('alintiyi-kopyala');
  if (!navigator.share) share.hidden = true;
  share.addEventListener('click', async () => {{
    try {{ await navigator.share({{title, text, url}}); }} catch (e) {{}}
  }});
  copy.addEventListener('click', async () => {{
    try {{
      await navigator.clipboard.writeText(citation);
      copy.textContent = 'Kopyalandı';
      setTimeout(() => copy.textContent = 'Alıntıyı kopyala', 1800);
    }} catch (e) {{}}
  }});
}})();
</script>
</body></html>'''


def rapor_json(veri: dict) -> dict:
    return {
        "baslik": veri["baslik"],
        "url": RAPOR_URL,
        "son_veri": veri["tarih"],
        "dataset_surumu": veri["dataset_surumu"],
        "envanter": {
            k: veri["envanter"][k]
            for k in ("fiyat_serisi", "kaynak", "cok_kaynakli", "tek_kaynak")
        },
        "endeksler": [
            {
                "id": o["vertikal"], "ad": o["ad"], "url": f"{su.SITE_KOK_URL}/{o['yol']}/",
                "orta_senaryo_tl": round(o["toplam"]), "kapsam": o["anasayfa_ifade"],
                "kalem_sayisi": o["gercek_kalem"], "kaynak_sayisi": o["site_sayisi"],
                "son_veri": o["guncelleme_tarihi"],
            }
            for o in veri["endeksler"]
        ],
        "dogrulanmis_degisimler": [
            {
                "vertikal": d["vertikal"], "kalem_id": d["kalem_id"],
                "degisim_yuzde_mutlak": d["onem"], "kaynak_sayisi": d["kaynak_sayisi"],
                "son_veri": d.get("olcum_tarihi"), "aciklama": d["metin"], "url": d["url"],
            }
            for d in veri["degisimler"]
        ],
        "lisans": "CC BY 4.0",
        "alinti_notu": "Rakamla birlikte son veri tarihini belirtin.",
    }


def rss_xml(veri: dict) -> str:
    e = veri["envanter"]
    aciklama = (
        f"{e['fiyat_serisi']} fiyat serisi ve {e['kaynak']} bağımsız kaynakla "
        f"güncellenen {veri['baslik']}."
    )
    gun = datetime.fromisoformat(veri["tarih"]).replace(tzinfo=timezone.utc, hour=9)
    guid = f"maliyetine-rapor-{veri['dataset_surumu'] or veri['tarih']}"
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>Maliyeti Ne? Veri Güncellemeleri</title>
  <link>{RAPOR_URL}</link>
  <description>Türkiye maliyet endeksleri, doğrulanmış fiyat değişimleri ve yeni veri yayınları.</description>
  <language>tr-TR</language>
  <lastBuildDate>{format_datetime(gun)}</lastBuildDate>
  <atom:link href="{su.SITE_KOK_URL}/feed.xml" rel="self" type="application/rss+xml" />
  <item>
    <title>{xml_escape(veri["baslik"])}</title>
    <link>{RAPOR_URL}</link>
    <guid isPermaLink="false">{xml_escape(guid)}</guid>
    <pubDate>{format_datetime(gun)}</pubDate>
    <description>{xml_escape(aciklama)}</description>
  </item>
</channel>
</rss>
'''


def dagitim_paketi(veri: dict) -> str:
    e = veri["envanter"]
    kisa = (
        f"{veri['baslik']} yayımlandı: {e['fiyat_serisi']} fiyat serisi, "
        f"{e['kaynak']} bağımsız kaynak, {e['cok_kaynakli']} çok kaynaklı seri. "
        f"{RAPOR_URL}"
    )
    degisimler = "\n".join(
        f"- {d['metin'].splitlines()[0]} ({d['kaynak_sayisi']} kaynak)\n  {d['url']}"
        for d in veri["degisimler"][:3]
    ) or "- Bu ölçümde dağıtım eşiğini geçen doğrulanmış değişim yok."
    return f"""# Dağıtım paketi — {veri['tarih']}

## WhatsApp / kısa paylaşım

{kisa}

## LinkedIn

{veri['baslik']} yayımlandı.

Bu sürümde {e['fiyat_serisi']} fiyat serisini {e['kaynak']} bağımsız kaynakla izliyoruz. {e['cok_kaynakli']} seri birden fazla kaynakla çapraz doğrulanıyor. Rapor; yedi endeksin güncel orta senaryolarını, yalnız kalite eşiğini geçen fiyat değişimlerini ve doğrudan kullanılabilir alıntı künyesini tek sayfada topluyor.

Veriyi kullanırken ölçüm tarihini belirtin: {veri['tarih']}.

{RAPOR_URL}

## X / Bluesky

{kisa}

## Doğrulanmış değişim adayları

{degisimler}
"""


def yaz(veri_kok: Path | None = None) -> dict[str, Path]:
    veri = rapor_verisi(veri_kok)
    rapor = SITE_KOK / "rapor" / "index.html"
    rapor.parent.mkdir(parents=True, exist_ok=True)
    rapor.write_text(rapor_html(veri), encoding="utf-8")

    json_yolu = SITE_KOK / "veri" / "rapor.json"
    json_yolu.write_text(
        json.dumps(rapor_json(veri), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    feed = SITE_KOK / "feed.xml"
    feed.write_text(rss_xml(veri), encoding="utf-8")
    paket = SITE_KOK / "veri" / "sosyal" / "dagitim-paketi.md"
    paket.parent.mkdir(parents=True, exist_ok=True)
    paket.write_text(dagitim_paketi(veri), encoding="utf-8")
    return {"rapor": rapor, "json": json_yolu, "feed": feed, "dagitim": paket}


def main() -> int:
    for ad, yol in yaz().items():
        print(f"{ad}: {yol}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
