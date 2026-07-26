# -*- coding: utf-8 -*-
"""
Maliyeti Ne? - Rehber (blog) sayfalari

NEDEN AYRI MODUL: sayfa_uret.py veri->tablo cevirisi yapiyor; buradaki
sayfalar ise YAZI. Ikisini ayni dosyada tutmak ikisini de okunmaz yapardi.

YAZIM KURALI (Yavuz'un talimati, 2026-07-26): "yapay zeka gibi degil,
gercekci". Pratikte:
  - Rakamla basla, girizgah yapma. "Bu yazida ele alacagiz" YOK.
  - Cumle uzunluklari degissin. Her paragraf ayni ritimde olmasin.
  - Her sey madde listesi olmasin - liste sadece gercekten liste olan
    seyler icin.
  - "Unutmayin ki", "Sonuc olarak", "Peki ya", "onemlidir" gibi dolgu
    kaliplari YOK.
  - Kendi olcumumuzden cikan sasirtici seyi soyle. Bir sey ters gittiyse
    onu da soyle - asil guveni o veriyor.
  - Abartma. "inanilmaz", "muhtesem", "cok onemli" YOK.

RAKAMLAR ELLE YAZILMAZ: govde fonksiyonlari veriyi parametre alir, tum
tutarlar /veri/*.json'dan gelir. Boylece aylik olcumde yazilar da
kendiliginden guncellenir - bayat rakamli blog yazisi, guven kaybinin
en hizli yolu.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import sayfa_uret as su

SITE_KOK = su.SITE_KOK
SITE_KOK_URL = su.SITE_KOK_URL


def _veriler(veri_kok: Path | None = None) -> dict:
    kok = veri_kok or SITE_KOK / "veri"
    cikti = {}
    for v in ("dugun", "ev-kurma", "arac"):
        dosya = kok / f"{v}.json"
        if dosya.exists():
            try:
                cikti[v] = json.loads(dosya.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
    return cikti


def _kalem(veri: dict, kalem_id: str, segment: str = "orta"):
    """Bir kalemin segment degeri. Yoksa None - rakam UYDURULMAZ."""
    k = (veri.get("kalemler") or {}).get(kalem_id) or {}
    seg = (k.get("segmentler") or {}).get(segment) or {}
    return seg.get("medyan") or k.get("genel_medyan")


def _p(n) -> str:
    return su._para(n) if n else "—"


# ---------------------------------------------------------------------------
# 1. 150 kisilik dugun
# ---------------------------------------------------------------------------
def _govde_dugun_150(v: dict) -> str | None:
    d = v.get("dugun")
    if not d:
        return None
    conf = su.VERTIKALLER["dugun"]
    kalemler = d.get("kalemler") or {}
    toplam, detaylar = su.ornek_toplam_hesapla(conf, kalemler, olcek=150, segment="orta")
    ekonomik, _ = su.ornek_toplam_hesapla(conf, kalemler, olcek=150, segment="ekonomik")
    if not toplam:
        return None

    salon = _kalem(d, "salon-yemekli")
    kokteyl = _kalem(d, "salon-kokteyl")
    gelinlik = _kalem(d, "gelinlik")
    taki = _kalem(d, "taki-altin")
    foto = _kalem(d, "fotografci")

    # En buyuk uc kalem - veriden, elle siralanmaz
    sirali = sorted(
        (x for x in detaylar if x.get("satir_toplam")),
        key=lambda x: -x["satir_toplam"],
    )[:3]
    buyukler = "".join(
        f"<tr><td>{x['ad']}</td><td class=\"sayi\">{_p(x['satir_toplam'])}</td>"
        f"<td class=\"sayi\">%{x['satir_toplam'] / toplam * 100:.0f}</td></tr>"
        for x in sirali
    )

    salon_toplam = salon * 150 if salon else None
    return f"""
  <p class="cevap-blok">
    150 kişilik, orta segment bir düğün {d.get('guncelleme_tarihi', '')} itibarıyla
    <strong>{_p(toplam)}</strong> tutuyor. Ekonomik tercihlerle aynı düğün
    {_p(ekonomik)} seviyesine iniyor. Bu rakamlar tek bir tahminden değil,
    her ay yeniden ölçtüğümüz kalem fiyatlarından çıkıyor.
  </p>

  <h2>Parayı asıl nereye veriyorsunuz?</h2>
  <p>
    Düğün bütçesi konuşulurken akla önce gelinlik gelir. Oysa gelinliğin orta
    segment fiyatı {_p(gelinlik)} — toplamın küçük bir dilimi. Bütçeyi asıl
    belirleyen kalem, kişi başı ödediğiniz salon bedeli.
  </p>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th class="sayi">Tutar</th><th class="sayi">Bütçe payı</th></tr></thead>
    <tbody>{buyukler}</tbody>
  </table></div>
  <p>
    Kişi başı {_p(salon)} olan yemekli bir salon, 150 davetlide
    {_p(salon_toplam)} demek. Davetli listesinden çıkardığınız her 10 kişi,
    yaklaşık {_p(salon * 10 if salon else None)} tasarruf. Hiçbir kalemde bu
    kadar hızlı sonuç alamazsınız.
  </p>

  <h2>Kokteyl gerçekten ucuz mu?</h2>
  <p>
    Kokteyl düzenin kişi başı fiyatı {_p(kokteyl)}, yemekliye göre belirgin
    düşük. Ama menü bedeli ortadan kalkmıyor, sadece faturadan çıkıp
    başka yere geçiyor: misafirlerinizi yemeksiz ağırlamayacaksanız
    catering'i ayrıca ödersiniz.
  </p>
  <p>
    Mekanların kendi yemekli ve kokteyl fiyatları arasındaki farkı ölçtük;
    bu fark, o mekanda menünün kişi başı bedelini veriyor. Ayrıntısı
    <a href="/rehber/yemekli-mi-kokteyl-mi/">yemekli mi kokteyl mi</a>
    yazısında.
  </p>

  <h2>Takı hesabın neresinde?</h2>
  <p>
    Bir altın bileziğin fiyatı {_p(taki)}. Bu kalem endeksin en oynak
    kısmı — gram altın hareket ettikçe ay içinde bile değişiyor. Düğünde
    takılan toplam altını hesaplamaya çalışmıyoruz; davetli sayısına ve
    aile geleneğine göre kat kat değiştiği için ölçülebilir bir şey değil.
  </p>

  <h2>Fotoğrafçı için ayırdığınız rakam muhtemelen fazla</h2>
  <p>
    İstanbul'da düğün fotoğrafçısı {_p(foto)} bandında. Biz de bu kalemi
    uzun süre tahminle taşıdık ve tahminimiz gerçeğin yaklaşık üç katıydı.
    Ölçmeye başlayınca düzelttik. Bütçe planlarken forumlarda dolaşan
    rakamlara değil, tarihi belli ölçümlere bakın.
  </p>

  <h2>Kendi düğününüzü hesaplayın</h2>
  <p>
    Davetli sayınızı ve segment tercihinizi girerek kendi tablonuzu
    çıkarabilirsiniz: <a href="/dugun/hesaplayici/">düğün maliyeti
    hesaplayıcısı</a>. Kalem kalem güncel fiyatlar
    <a href="/dugun/">düğün endeksinde</a>.
  </p>
"""


# ---------------------------------------------------------------------------
# 2. Yemekli mi kokteyl mi
# ---------------------------------------------------------------------------
def _govde_yemekli_kokteyl(v: dict) -> str | None:
    d = v.get("dugun")
    if not d:
        return None
    yemekli = _kalem(d, "salon-yemekli")
    kokteyl = _kalem(d, "salon-kokteyl")
    menu = _kalem(d, "yemek-ikram")
    if not (yemekli and kokteyl):
        return None

    fark_150 = (yemekli - kokteyl) * 150
    return f"""
  <p class="cevap-blok">
    Yemekli salon kişi başı <strong>{_p(yemekli)}</strong>, kokteyl salon
    <strong>{_p(kokteyl)}</strong>. 150 kişilik bir düğünde aradaki fark
    {_p(fark_150)}. Ama bu farkın tamamı cebinizde kalmıyor — kokteyl
    seçerseniz yemeği başka yerden almanız gerekiyor.
  </p>

  <h2>İki fiyat neyi kapsıyor?</h2>
  <p>
    Düğün mekanları fiyatı kişi başı verir ve genellikle iki seçenek sunar.
    Yemekli seçenekte salon ve menü birlikte fiyatlanır. Kokteyl seçenekte
    salonu alırsınız, yemek yoktur; ikram genelde sınırlı bir açık büfeyle
    kalır.
  </p>
  <p>
    Bu ayrım göründüğünden önemli, çünkü mekanların ilan sayfalarında
    yazan "başlangıç fiyatı" çoğu zaman kokteyl fiyatıdır. Yemekli bir
    düğün planlarken kokteyl fiyatını baz alırsanız bütçeniz baştan
    yanlış kurulur.
  </p>

  <h2>Menünün kişi başı bedeli</h2>
  <p>
    Menünün gerçek maliyetini bulmanın temiz bir yolu var: aynı mekanın
    yemekli ve kokteyl fiyatını çıkarmak. Aradaki fark, o mekanda yemeğin
    kişi başı bedeli. Bunu tek tek mekanlar için hesapladık; orta segmentte
    {_p(menu)} çıkıyor.
  </p>
  <p>
    Farkı <em>aynı mekan içinde</em> almak şart. İki ayrı listenin
    ortalamasını çıkarmak yanlış sonuç verir, çünkü her mekan kokteyl
    seçeneği sunmuyor ve farkların ortası, ortaların farkına eşit değil.
    Bizim veride bu iki yöntem arasında gözle görülür bir sapma vardı.
  </p>

  <h2>Hangisi size uygun?</h2>
  <p>
    Kokteyl düzen, davetlilerin oturup yemek yemediği, daha kısa süren
    organizasyonlar için mantıklı. Akşam saatinde, uzun bir düğün
    planlıyorsanız misafirleriniz yemek bekler; kokteyl alıp dışarıdan
    catering getirmek çoğu zaman yemekli paketten ucuza gelmez.
  </p>
  <p>
    Mekanın kendi menüsü genelde daha ekonomik olur — mutfak zaten orada,
    servis ekibi zaten çalışıyor. Dışarıdan catering'in ulaşım, ekipman ve
    servis kalemleri fiyata biniyor.
  </p>

  <h2>Bir uyarı</h2>
  <p>
    Bu iki rakamı toplayıp tek bir "gerçek maliyet" çıkarmaya çalışmayın.
    Hesaplayıcımızda da toplamıyoruz: yemekli fiyat zaten menüyü içerdiği
    için üstüne ayrıca yemek eklemek aynı masrafı iki kez saymak olur.
    Seçtiğiniz düzen hangisiyse toplama yalnızca o giriyor.
  </p>
  <p>
    Kendi düğününüz için hesap:
    <a href="/dugun/hesaplayici/">düğün maliyeti hesaplayıcısı</a>.
    Yöntemin ayrıntısı <a href="/dugun/metodoloji/">metodoloji sayfasında</a>.
  </p>
"""


# ---------------------------------------------------------------------------
# 3. Sifirdan ev kurma
# ---------------------------------------------------------------------------
def _govde_ev_kurma(v: dict) -> str | None:
    e = v.get("ev-kurma")
    if not e:
        return None
    conf = su.VERTIKALLER["ev-kurma"]
    kalemler = e.get("kalemler") or {}
    toplam, detaylar = su.ornek_toplam_hesapla(conf, kalemler, olcek=1, segment="orta")
    ekonomik, _ = su.ornek_toplam_hesapla(conf, kalemler, olcek=1, segment="ekonomik")
    ust, _ = su.ornek_toplam_hesapla(conf, kalemler, olcek=1, segment="luks")
    if not toplam:
        return None

    # Gruplara gore toplam - veriden
    gruplar: dict[str, int] = {}
    for x in detaylar:
        if not x.get("satir_toplam"):
            continue
        tanim = next((t for t in conf["kalemler"] if t["id"] == x["id"]), {})
        grup = tanim.get("grup") or "Diğer"
        gruplar[grup] = gruplar.get(grup, 0) + x["satir_toplam"]
    grup_satir = "".join(
        f"<tr><td>{g}</td><td class=\"sayi\">{_p(t)}</td>"
        f"<td class=\"sayi\">%{t / toplam * 100:.0f}</td></tr>"
        for g, t in sorted(gruplar.items(), key=lambda x: -x[1])
    )

    buzdolabi = _kalem(e, "buzdolabi")
    camasir = _kalem(e, "camasir-makinesi")
    koltuk = _kalem(e, "koltuk-takimi")
    kalem_sayisi = len([x for x in detaylar if x.get("satir_toplam")])

    return f"""
  <p class="cevap-blok">
    Sıfırdan bir evi eşyalandırmak orta segmentte
    <strong>{_p(toplam)}</strong> tutuyor. Ekonomik tercihlerle
    {_p(ekonomik)}, üst segmentte {_p(ust)}. Bu tutar {kalem_sayisi} kalemin
    toplamı: beyaz eşyadan mutfak gerecine, mobilyadan tekstile.
  </p>

  <h2>Bütçe nasıl dağılıyor?</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Grup</th><th class="sayi">Tutar</th><th class="sayi">Pay</th></tr></thead>
    <tbody>{grup_satir}</tbody>
  </table></div>
  <p>
    Beyaz eşya ve mobilya toplamın büyük kısmını alıyor. Küçük ev aletleri
    tek tek ucuz görünür ama sayıları fazla olduğu için topluca ciddi bir
    yer tutuyor — listeyi çıkarırken en çok bu kalemde şaşırılıyor.
  </p>

  <h2>Önce alınacaklar</h2>
  <p>
    Taşındığınız gün çalışması gerekenler kısa bir liste: buzdolabı
    ({_p(buzdolabi)}), çamaşır makinesi ({_p(camasir)}), bir yatak ve
    oturma grubu ({_p(koltuk)}). Geri kalanı zamana yayılabilir.
    Kahve makinesinden airfryer'a kadar olan kalemler, ilk ay
    ertelendiğinde hayatı zorlaştırmıyor.
  </p>
  <p>
    Eşyayı tek seferde almak zorunda değilsiniz. Ama tek seferde alacaksanız
    tutarı baştan bilmek, kredi ya da taksit planını doğru kurmanızı sağlar.
  </p>

  <h2>Bu rakamlarda ne yok?</h2>
  <p>
    Konutun kendisi, tadilat ve işçilik, nakliye, beyaz eşya montajı ve
    perde dikimi bu tutara dahil değil. Her kalemden bir adet varsayıyoruz;
    iki yatak odalı bir ev kuruyorsanız yatak, komodin ve gardırop
    kalemlerini çoğaltmanız gerekir.
  </p>

  <h2>Fiyatlar nereden geliyor?</h2>
  <p>
    Kalemlerin fiyatı büyük e-ticaret sitelerinden ve marka mağazalarından
    aylık olarak derleniyor. Bir uyarı: kategori listelerinden derlediğimiz
    için üst segment rakamı piyasanın en pahalısını değil, yaygın ürünler
    içindeki üst çeyreği gösteriyor. Ankastre bir premium buzdolabı
    arıyorsanız gerçek fiyat bizim "üst" sütunumuzun üzerinde olacaktır.
  </p>
  <p>
    Kendi listenizi seçerek hesaplayın:
    <a href="/ev-kurma/hesaplayici/">ev kurma maliyeti hesaplayıcısı</a>.
    Kalem kalem güncel fiyatlar <a href="/ev-kurma/">ev kurma endeksinde</a>.
  </p>
"""


# ---------------------------------------------------------------------------
# 4. Sifir araba gercek maliyeti
# ---------------------------------------------------------------------------
def _govde_arac(v: dict) -> str | None:
    a = v.get("arac")
    if not a:
        return None
    giris = _kalem(a, "en-ucuz-sifir-arac")
    if not giris:
        return None

    # arac-ek-maliyetler.js ile AYNI kurallar - tek kaynak olsun diye
    # buradaki degerler o dosyadan turetilmis sabitler.
    mtv = 12028          # 1301-1600 cc, ilk yil (58 Seri No.lu MTV Teblig)
    noter = max(giris * 0.002, 1000) + 1920
    kasko = max(giris * 0.03, 12000)
    trafik = 9500
    plaka = 4500
    ek = mtv + noter + kasko + trafik + plaka
    return f"""
  <p class="cevap-blok">
    Sıfır aracın etiket fiyatı ödediğiniz tutar değil. Bir markanın giriş
    modeli ortalama <strong>{_p(giris)}</strong>; üzerine vergi, harç ve
    sigorta olarak yaklaşık <strong>{_p(ek)}</strong> biniyor. Anahtarı
    almanın gerçek maliyeti <strong>{_p(giris + ek)}</strong> civarında.
  </p>

  <h2>Etiket fiyatının üstüne ne ekleniyor?</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th class="sayi">Tutar</th><th>Tür</th></tr></thead>
    <tbody>
      <tr><td>MTV (ilk yıl, 1301–1600 cc)</td><td class="sayi">{_p(mtv)}</td><td>Resmî tarife</td></tr>
      <tr><td>Noter ve ilk tescil</td><td class="sayi">{_p(round(noter))}</td><td>Resmî tarife</td></tr>
      <tr><td>Kasko (yıllık)</td><td class="sayi">{_p(round(kasko))}</td><td>Tahmini</td></tr>
      <tr><td>Zorunlu trafik sigortası</td><td class="sayi">{_p(trafik)}</td><td>Tahmini</td></tr>
      <tr><td>Plaka ve ruhsat</td><td class="sayi">{_p(plaka)}</td><td>Tahmini</td></tr>
    </tbody>
  </table></div>
  <p>
    MTV ve noter harcı resmî tarifeye bağlı; Resmî Gazete'de yayımlanan
    tutarlar. Kasko ve trafik sigortası ise şirkete, sürücünün yaşına ve
    hasarsızlık geçmişine göre değişiyor — buradaki rakamlar piyasa
    ortalaması, teklif değil.
  </p>

  <h2>Motor hacmi vergiyi ikiye katlayabilir</h2>
  <p>
    MTV kademeli hesaplanıyor ve kademeler arasındaki fark büyük. 1300 cc'ye
    kadar olan bir araçta ilk yıl MTV'si 6.903 TL iken, 1601–1800 cc bandında
    21.252 TL'ye çıkıyor. İki benzer araç arasında karar veriyorsanız motor
    hacmi, yalnızca yakıt tüketimi değil vergi farkı demek.
  </p>

  <h2>Neden ortalama araç fiyatı vermiyoruz</h2>
  <p>
    Piyasadaki tüm modellerin ortasını almak yanıltıcı bir rakam üretiyor.
    Denedik: 3,2 milyon TL çıkıyor. Sebebi listede Porsche ile Fiat'ın eşit
    ağırlıkta sayılması — oysa Türkiye'de satılan araçların dağılımı böyle
    değil. Bunun yerine her markanın giriş modelini ölçüyoruz; net tanımlı
    ve karşılaştırılabilir bir rakam.
  </p>

  <h2>Kendi aracınızı hesaplayın</h2>
  <p>
    Aracın fiyatını ve motor hacmini girip hangi kalemleri istediğinizi
    seçebilirsiniz: <a href="/arac/hesaplayici/">araç sahip olma maliyeti
    hesaplayıcısı</a>. Marka marka güncel liste fiyatları
    <a href="/arac/">sıfır araç endeksinde</a>.
  </p>
  <p>
    Bu hesap satın alma anını kapsıyor. Yakıt, bakım, lastik ve yıpranma
    gibi kullanım giderleri ayrı bir konu; onları henüz ölçmüyoruz.
  </p>
"""


REHBERLER = [
    {
        "slug": "150-kisilik-dugun-maliyeti",
        "baslik": "150 Kişilik Düğün Ne Kadar Tutuyor?",
        "meta": "150 kişilik düğünün kalem kalem maliyeti: salon, gelinlik, takı, "
                "fotoğrafçı. Gerçek fiyat ölçümlerinden, aylık güncellenen rakamlarla.",
        "govde": _govde_dugun_150,
        "vertikal": "dugun",
    },
    {
        "slug": "yemekli-mi-kokteyl-mi",
        "baslik": "Yemekli mi Kokteyl mi? Düğün Salonu Seçiminde Fiyat Farkı",
        "meta": "Yemekli ve kokteyl düğün salonu arasındaki kişi başı fark ne kadar, "
                "menünün gerçek bedeli nasıl hesaplanır?",
        "govde": _govde_yemekli_kokteyl,
        "vertikal": "dugun",
    },
    {
        "slug": "sifirdan-ev-kurma-listesi",
        "baslik": "Sıfırdan Ev Kurmak Ne Kadara Mal Oluyor?",
        "meta": "Beyaz eşyadan tekstile, sıfırdan ev kurmanın kalem kalem maliyeti "
                "ve bütçe dağılımı. Aylık güncellenen gerçek fiyatlarla.",
        "govde": _govde_ev_kurma,
        "vertikal": "ev-kurma",
    },
    {
        "slug": "sifir-araba-gercek-maliyeti",
        "baslik": "Sıfır Araba Alırken Etiket Fiyatı Yetmiyor",
        "meta": "MTV, noter, tescil, kasko ve trafik sigortası: sıfır aracın etiket "
                "fiyatının üstüne binen maliyetler ve toplam tutar.",
        "govde": _govde_arac,
        "vertikal": "arac",
    },
]


def rehber_uret(rehber: dict, veriler: dict, tarih: str | None = None) -> str | None:
    """Tek bir rehber sayfasi. Veri yoksa None - bos sayfa YAYINLANMAZ."""
    govde = rehber["govde"](veriler)
    if not govde:
        return None
    tarih = tarih or date.today().isoformat()
    url = f"{SITE_KOK_URL}/rehber/{rehber['slug']}/"
    vconf = su.VERTIKALLER[rehber["vertikal"]]

    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": rehber["baslik"],
                "description": rehber["meta"],
                "datePublished": tarih,
                "dateModified": tarih,
                "inLanguage": "tr-TR",
                "mainEntityOfPage": url,
                "author": {"@type": "Organization", "name": "Maliyeti Ne?"},
                "publisher": {
                    "@type": "Organization",
                    "name": "Maliyeti Ne?",
                    "url": SITE_KOK_URL,
                },
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Ana sayfa",
                     "item": SITE_KOK_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Rehber",
                     "item": f"{SITE_KOK_URL}/rehber/"},
                    {"@type": "ListItem", "position": 3, "name": rehber["baslik"],
                     "item": url},
                ],
            },
        ],
    }

    digerleri = "".join(
        f'<a href="/rehber/{r["slug"]}/">{r["baslik"]}</a>'
        for r in REHBERLER if r["slug"] != rehber["slug"]
    )

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{rehber["baslik"]} | Maliyeti Ne?</title>
<meta name="description" content="{rehber["meta"]}">
<link rel="canonical" href="{url}">
<link rel="stylesheet" href="/assets/css/style.css">
<meta property="og:title" content="{rehber["baslik"]}">
<meta property="og:description" content="{rehber["meta"]}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="Maliyeti Ne?">
<meta property="og:image" content="{SITE_KOK_URL}/assets/og-gorsel.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">Maliyeti <span>Ne?</span></a>
    <nav class="ust-menu">
      <a href="/dugun/">Düğün</a>
      <a href="/ev-kurma/">Ev Kurma</a>
      <a href="/arac/">0 km Araç</a>
    </nav>
  </div>
</header>

<main class="kapsayici">

  <span class="guncelleme-etiketi">Güncelleme: {tarih}</span>
  <h1>{rehber["baslik"]}</h1>
{govde}
  <p class="kunye">{tarih} tarihli ölçümlerden ·
    <a href="/{vconf['yol']}/metodoloji/">Yöntem</a></p>

  <section class="icerik-bolumu">
    <h2>Diğer rehberler</h2>
    <p class="kart-linkler">{digerleri}</p>
  </section>

</main>

<footer>
  <div class="kapsayici">
    <div>© {tarih[:4]} Maliyeti Ne? · <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a></div>
    <nav>
      <a href="/dugun/">Düğün</a>
      <a href="/ev-kurma/">Ev Kurma</a>
      <a href="/arac/">0 km Araç</a>
    </nav>
  </div>
</footer>

</body>
</html>
"""


def rehber_dizini_uret(yazilanlar: list[dict], tarih: str | None = None) -> str:
    tarih = tarih or date.today().isoformat()
    kartlar = "".join(
        f'<div class="kart"><h3><a href="/rehber/{r["slug"]}/">{r["baslik"]}</a></h3>'
        f'<p>{r["meta"]}</p></div>'
        for r in yazilanlar
    )
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rehber | Maliyeti Ne?</title>
<meta name="description" content="Düğün, ev kurma ve sıfır araç bütçesi üzerine, gerçek fiyat ölçümlerine dayanan rehberler.">
<link rel="canonical" href="{SITE_KOK_URL}/rehber/">
<link rel="stylesheet" href="/assets/css/style.css">
<meta property="og:title" content="Rehber | Maliyeti Ne?">
<meta property="og:description" content="Gerçek fiyat ölçümlerine dayanan bütçe rehberleri.">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_KOK_URL}/rehber/">
<meta property="og:image" content="{SITE_KOK_URL}/assets/og-gorsel.png">
<meta name="twitter:card" content="summary_large_image">
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">Maliyeti <span>Ne?</span></a>
    <nav class="ust-menu">
      <a href="/dugun/">Düğün</a>
      <a href="/ev-kurma/">Ev Kurma</a>
      <a href="/arac/">0 km Araç</a>
    </nav>
  </div>
</header>

<main class="kapsayici">
  <h1>Rehber</h1>
  <p>
    Her yazıdaki rakam, o gün ölçtüğümüz gerçek fiyatlardan geliyor ve
    veri yenilendikçe yazı da güncelleniyor.
  </p>
  <div class="kart-grid">{kartlar}</div>
</main>

<footer>
  <div class="kapsayici">
    <div>© {tarih[:4]} Maliyeti Ne? · <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a></div>
  </div>
</footer>

</body>
</html>
"""


def rehberleri_yaz(veri_kok: Path | None = None, hedef_kok: Path | None = None) -> list[dict]:
    veriler = _veriler(veri_kok)
    kok = hedef_kok or SITE_KOK / "rehber"
    yazilanlar = []
    for r in REHBERLER:
        html = rehber_uret(r, veriler)
        if not html:
            print(f"  ATLANDI (veri yok): {r['slug']}")
            continue
        hedef = kok / r["slug"] / "index.html"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(html, encoding="utf-8")
        yazilanlar.append(r)
    if yazilanlar:
        (kok / "index.html").parent.mkdir(parents=True, exist_ok=True)
        (kok / "index.html").write_text(rehber_dizini_uret(yazilanlar), encoding="utf-8")
    return yazilanlar


def main():
    yazilanlar = rehberleri_yaz()
    for r in yazilanlar:
        print(f"Rehber uretildi: /rehber/{r['slug']}/")
    print(f"Toplam {len(yazilanlar)} rehber + dizin.")


if __name__ == "__main__":
    main()
