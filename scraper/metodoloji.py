# -*- coding: utf-8 -*-
"""Vertikal metodolojilerini kanonik JSON ve sayfa tanimindan uretir.

Metodoloji sayfasi rakamin kanitidir. Seri, kaynak veya kapsam sayilarini
elle yazmak; veri degisince sitenin kendi kendisiyle celismesine yol acar.
Bu modul yedi sayfayi her yayin turunda yeniden kurar.
"""

from __future__ import annotations

import html
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

import sayfa_uret as su


SITE_KOK = su.SITE_KOK
SITE_KOK_URL = su.SITE_KOK_URL


KAPSAM_NOTLARI = {
    "dugun": (
        "Ürün fiyatları Türkiye'deki çevrim içi satış listelerinden; salon ve "
        "hizmet kalemleri kapsamı açık, karşılaştırılabilir İstanbul "
        "ölçümlerinden gelir. Kişi başı kalemler varsayılan 150 davetliyle "
        "çarpılır; sabit kalemler bir kez eklenir. Yemekli ve kokteyl salon "
        "birbirinin alternatifidir, aynı bütçede birlikte toplanmaz."
    ),
    "ev-kurma": (
        "Bir ev için her üründen bir adetlik sepet ölçülür. Fırın/ocak gibi "
        "aynı listede set, ocaklı fırın ve solo fırın bulunan karma kategoriler "
        "tek fiyatla bütçeye sokulmaz; ürün tipleri ayrı gösterilir. Adet "
        "ihtiyacı haneye göre değişen ürünler hesaplayıcıda artırılabilir."
    ),
    "okul": (
        "Endeks bir öğrencinin okul alışverişini ölçer. Çanta, kırtasiye, "
        "yardımcı kitap ve ayakkabı varsayılan sepettedir. Tablet, çalışma "
        "masası ve sandalyesi her yıl alınmadığı için ana toplama girmez; "
        "hesaplayıcıda isteğe bağlı eklenir. Okul ücreti, servis ve yemek yoktur."
    ),
    "bebek": (
        "Endeks doğum öncesi tek seferlik bebek hazırlık sepetini ölçer. Bebek "
        "bezi kategori paket fiyatıdır; paket adedi ve günlük tüketim bilinmeden "
        "aylık gider sayılamayacağı için hazırlık toplamına girmez. Doğum, "
        "hastane ve sağlık giderleri ayrı kapsamdır."
    ),
    "kedi": (
        "Endeks bir kedi için tek seferlik başlangıç kurulumunu ölçer. Mama ve "
        "kum kategori paket fiyatıdır; tüketim miktarı kullanıcıdan gelmeden "
        "aylık gider türetilmez. Veteriner, aşı, kısırlaştırma ve pansiyon "
        "giderleri bu sepette yoktur."
    ),
    "kopek": (
        "Endeks bir köpek için tek seferlik başlangıç kurulumunu ölçer. Mama ve "
        "çiş pedi kategori paket fiyatıdır; ırk, boy ve kullanım sıklığı "
        "bilinmeden aylık gider türetilmez. Veteriner, eğitim, kuaför ve "
        "pansiyon giderleri bu sepette yoktur."
    ),
    "arac": (
        "Endeks Türkiye'de satışta olan sıfır kilometre araçların yayımlanmış "
        "liste fiyatlarını ölçer. Markalar birbirinin alternatifidir ve "
        "toplanmaz. En ucuz araç gerçek minimum fiyatı; giriş fiyatları "
        "ortancası ise 23 markanın tipik başlangıç seviyesini anlatır. Bayi "
        "kampanyası, kredi, sigorta, MTV ve kullanım giderleri dahil değildir."
    ),
}


def _liste(maddeler: list[str]) -> str:
    return "".join(f"<li>{m}</li>" for m in maddeler)


def _ad_haritasi(conf: dict) -> dict[str, str]:
    return {
        k["id"]: k["ad"]
        for k in conf.get("kalemler", []) + conf.get("tahmini_kalemler", [])
    }


def metodoloji_ozeti(vertikal: str, veri_kok: Path | None = None) -> dict:
    conf = su.VERTIKALLER[vertikal]
    kok = veri_kok or SITE_KOK / "veri"
    veri = json.loads((kok / f"{vertikal}.json").read_text(encoding="utf-8"))
    kalemler = veri.get("kalemler") or {}
    adlar = _ad_haritasi(conf)

    kaynak_serileri: dict[str, set[str]] = defaultdict(set)
    kaynak_urunleri: dict[str, int] = defaultdict(int)
    tek_kaynakli = []
    cok_kaynakli = []
    for kalem_id, kalem in kalemler.items():
        siteler = {
            kaynak.get("site") for kaynak in kalem.get("kaynaklar", [])
            if kaynak.get("site") and (kaynak.get("toplam_urun") or 0) > 0
        }
        for kaynak in kalem.get("kaynaklar", []):
            site = kaynak.get("site")
            if site and (kaynak.get("toplam_urun") or 0) > 0:
                kaynak_serileri[site].add(kalem_id)
                kaynak_urunleri[site] += kaynak.get("toplam_urun") or 0
        hedef = cok_kaynakli if len(siteler) > 1 else tek_kaynakli
        hedef.append(kalem_id)

    varsayilan_disi = [
        k["id"] for k in conf.get("kalemler", [])
        if k.get("varsayilan_dahil") is False or k.get("bilgi_amacli")
    ]
    tahmini = conf.get("tahmini_kalemler", [])
    return {
        "conf": conf,
        "tarih": veri.get("guncelleme_tarihi") or date.today().isoformat(),
        "seri": len(kalemler),
        "urun": sum((k.get("toplam_urun") or 0) for k in kalemler.values()),
        "kaynak": len(kaynak_serileri),
        "cok": len(cok_kaynakli),
        "tek": len(tek_kaynakli),
        "tek_adlari": [adlar.get(k, k) for k in tek_kaynakli],
        "tahmini": tahmini,
        "varsayilan_disi": [adlar.get(k, k) for k in varsayilan_disi],
        "kaynak_satirlari": [
            (site, len(kaynak_serileri[site]), kaynak_urunleri[site])
            for site in sorted(kaynak_serileri)
        ],
    }


def metodoloji_html(vertikal: str, veri_kok: Path | None = None) -> str:
    o = metodoloji_ozeti(vertikal, veri_kok)
    conf = o["conf"]
    ad = conf["ad"]
    yol = conf["yol"]
    url = f"{SITE_KOK_URL}/{yol}/metodoloji/"
    liste_fiyati = bool(conf.get("liste_fiyati"))

    kaynak_satirlari = "".join(
        f"<tr><td>{html.escape(site.replace('-', ' ').title())}</td>"
        f'<td class="sayi">{seri}</td><td class="sayi">{urun}</td></tr>'
        for site, seri, urun in o["kaynak_satirlari"]
    )
    tek_aciklama = (
        "Araç serileri üreticilerin belirlediği liste fiyatını izler; ikinci "
        "bir site aynı fiyatı tekrar ettiği için pazar çeşitliliği sayılmaz. "
        "Buradaki tek kaynaklılık bir fiyat ortalaması iddiası değil, tanımlı "
        "liste fiyatı ölçümüdür."
        if liste_fiyati else
        (
            f'{o["tek"]} seri şu anda tek kaynaklıdır: '
            + ", ".join(html.escape(x) for x in o["tek_adlari"])
            + ". Bu seriler sayfada tek kaynak sınırıyla birlikte gösterilir; "
              "ikinci kaynak varmış gibi sunulmaz."
            if o["tek"] else
            "Yayındaki bütün seriler en az iki bağımsız kaynaktan besleniyor."
        )
    )
    tahmin_blok = ""
    if o["tahmini"]:
        tahminler = ", ".join(html.escape(x["ad"]) for x in o["tahmini"])
        tahmin_blok = f"""
    <h3>Tahmini bütçe kalemleri</h3>
    <p><strong>{tahminler}</strong> için sürekli ve karşılaştırılabilir bir
      fiyat akışı henüz yoktur. Bunlar {o['tahmini'][0]['arastirma_tarihi']}
      tarihli piyasa araştırmasıdır, fiyat serisi sayısına dahil edilmez ve
      sayfada <span class="tahmini-etiket">Tahmini</span> diye ayrılır.</p>"""

    varsayilan_not = ""
    if o["varsayilan_disi"]:
        varsayilan_not = (
            "<p><strong>Varsayılan toplama girmeyen seriler:</strong> "
            + ", ".join(html.escape(x) for x in o["varsayilan_disi"])
            + ". Bunlar ölçülür ve yayımlanır; ancak alternatif, dönemsel ya da "
              "tüketim bilgisi gerektiren kalemler oldukları için otomatik bütçe "
              "toplamına eklenmez.</p>"
        )

    kunye = su.yayin_kunyesi_html(
        [("Fiyat serisi", o["seri"]), ("Bağımsız kaynak", o["kaynak"]),
         ("Çok kaynaklı seri", o["cok"]), ("Son veri", o["tarih"])],
        [("Ham veri", f"/veri/{vertikal}.json"),
         ("QA raporu", "/veri/qa.json"), ("Hata bildir", "/iletisim/")],
        "Bu sayfanın canlı kapsamı",
    )
    cevap = (
        f"{ad} endeksi {o['tarih']} itibarıyla <strong>{o['seri']} fiyat "
        f"serisini</strong>, <strong>{o['kaynak']} bağımsız kaynaktan</strong> "
        f"derlenen {o['urun']} ürün/fiyat satırıyla izliyor. "
        f"{o['cok']} seri çok kaynaklı, {o['tek']} seri tek kaynaklıdır."
    )
    sss = [
        (f"{ad} endeksinde kaç fiyat serisi var?",
         f"{o['tarih']} itibarıyla {o['seri']} ölçülmüş fiyat serisi var. "
         f"Bunların {o['cok']} tanesi çok, {o['tek']} tanesi tek kaynaklıdır."),
        ("Veriler ne zaman yenileniyor?",
         "Kaynaklar ayın 5'i ve 20'sinde yeniden taranır. Bir tarama başarısız "
         "olursa eski sağlıklı ölçüm korunur; son veri tarihi ilerletilmez."),
        ("Neden aritmetik ortalama değil ortanca kullanılıyor?",
         "Az sayıdaki aşırı pahalı veya ucuz ürünün bütün kategoriyi çekmesini "
         "önlemek için kaynak ve seri özetlerinde ortanca fiyat kullanılır."),
    ]
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            su.kurum_semantigi(),
            {"@type": "WebPage", "@id": url + "#webpage", "url": url,
             "name": f"{ad} Fiyat Metodolojisi", "dateModified": o["tarih"],
             "inLanguage": "tr-TR", "publisher": {"@id": SITE_KOK_URL + "/#kurum"},
             "about": {"@id": f"{SITE_KOK_URL}/{yol}/#dataset"}},
            {"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": s,
                 "acceptedAnswer": {"@type": "Answer", "text": c}}
                for s, c in sss
            ]},
        ],
    }
    sss_html = "".join(f"<h3>{s}</h3><p>{c}</p>" for s, c in sss)
    dahil = conf.get("dahil_olanlar") or []
    disarida = conf.get("dahil_olmayanlar") or []
    meta_aciklama = (
        f"{ad} fiyatları nasıl ölçülüyor? Güncel seri, kaynak, örneklem, "
        "kapsam ve hesaplama yöntemi."
    )

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ad} Fiyat Metodolojisi | Maliyeti Ne?</title>
<meta name="description" content="{meta_aciklama}">
<link rel="canonical" href="{url}">
{su.STIL_ETIKETLERI}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:title" content="{ad} Fiyat Metodolojisi">
<meta property="og:description" content="{meta_aciklama}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
{su.og_etiketleri(f"/assets/og/{vertikal}-metodoloji.png", f"{ad} fiyat metodolojisi")}
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{json.dumps(schema, ensure_ascii=False, indent=2)}
</script>
{su.ANALITIK}
</head>
<body>
<header class="ust-bar"><div class="kapsayici">
  <a href="/" class="logo">Maliyeti <span>Ne?</span></a>
  <nav class="ust-menu">{su.genel_menu(vertikal)}</nav>
</div></header>
<main class="kapsayici">
  <nav class="kirinti" aria-label="Sayfa yolu"><a href="/">Ana sayfa</a> ›
    <a href="/{yol}/">{ad}</a> › <span>Metodoloji</span></nav>
  <span class="guncelleme-etiketi">Son veri: {o['tarih']}</span>
  <h1>{ad} fiyatlarını nasıl ölçüyoruz?</h1>
  <div class="cevap-blok">{cevap}</div>
  {kunye}

  <section class="icerik-bolumu">
    <h2>Neyi ölçüyor, neyi ölçmüyor?</h2>
    <p>{KAPSAM_NOTLARI[vertikal]}</p>
    <h3>Dahil olanlar</h3><ul>{_liste(dahil)}</ul>
    <h3>Dahil olmayanlar</h3><ul>{_liste(disarida)}</ul>
    {varsayilan_not}
  </section>

  <section class="icerik-bolumu">
    <h2>Kaynak kapsamı</h2>
    <p>{tek_aciklama}</p>
    <div class="tablo-sarmal"><table>
      <thead><tr><th>Kaynak</th><th class="sayi">Beslediği seri</th>
      <th class="sayi">Ürün/fiyat satırı</th></tr></thead>
      <tbody>{kaynak_satirlari}</tbody>
    </table></div>
    <p class="sonuc-alt-metin">Aynı site birden fazla seriyi besleyebilir.
      Ürün/fiyat satırı toplamı benzersiz ürün iddiası değildir; her
      kaynak-kategori ölçümündeki geçerli satırların toplamıdır.</p>
{tahmin_blok}
  </section>

  <section class="icerik-bolumu">
    <h2>Fiyat nasıl hesaplanıyor?</h2>
    <ol>
      <li>Ürün adı ve satış fiyatı, robots.txt izni bulunan açık liste sayfalarından alınır.</li>
      <li>Fiyatı olmayan, yanlış ürün türündeki ve sağlık kontrolünü geçmeyen satırlar elenir.</li>
      <li>Her kaynağın kendi ürün havuzunda ortanca ve fiyat bantları hesaplanır.</li>
      <li>Birden fazla kaynak varsa kaynak ortancalarının ortancası ana fiyat olur; büyük ürün havuzuna sahip tek site diğerlerini ezmez.</li>
      <li>Ekonomik, orta ve üst bantlar kaynak içindeki fiyat dağılımından kurulur. Sıralama bozulursa segmentler gizlenir ve sınır açıkça yazılır.</li>
    </ol>
    <p>Geniş kategori sayfalarında yalnız ürün adında açıkça yazan tür,
      kapasite, model veya özellik ayrıştırılır. Eksik alan tahmin edilmez;
      düşük örneklemli alt kırılım yayımlanmaz.</p>
  </section>

  <section class="icerik-bolumu">
    <h2>Yenileme ve kalite kontrolü</h2>
    <p>Kaynaklar ayın <strong>5'i ve 20'sinde</strong> yeniden taranır.
      Son veri tarihi son başarılı ölçümdür; başarısız veya karantinaya
      alınan tarama tarihi ilerletmez. Ürün sayısı geçmiş ortalamanın çok
      altına düşerse kaynak sessizce kabul edilmez.</p>
    <p>Yayın öncesinde seri sayısı, kaynak ve ürün toplamı, geçmiş noktası,
      CSV, HTML ve veri sürümü birlikte denetlenir. Güncel sonuç
      <a href="/veri/qa.json">makinece okunabilir QA raporunda</a>, ham
      seri ise <a href="/veri/{vertikal}.json">JSON dosyasında</a> açıktır.</p>
  </section>

  <section class="icerik-bolumu"><h2>Sık sorulan sorular</h2>{sss_html}</section>
</main>
<footer><div class="kapsayici">© {o['tarih'][:4]} Maliyeti Ne? ·
  <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a> ·
  <a href="/veri/">Veri</a></div></footer>
</body>
</html>
"""


def metodolojileri_yaz(veri_kok: Path | None = None,
                       hedef_kok: Path | None = None) -> list[Path]:
    kok = hedef_kok or SITE_KOK
    yazilanlar = []
    for vertikal, conf in su.VERTIKALLER.items():
        hedef = kok / conf["yol"] / "metodoloji" / "index.html"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(metodoloji_html(vertikal, veri_kok), encoding="utf-8")
        yazilanlar.append(hedef)
    return yazilanlar


def main() -> None:
    for hedef in metodolojileri_yaz():
        print(f"Metodoloji üretildi: {hedef}")


if __name__ == "__main__":
    main()
