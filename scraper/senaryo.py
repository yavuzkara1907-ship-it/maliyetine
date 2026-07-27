# -*- coding: utf-8 -*-
"""
Maliyeti Ne? - Senaryo sayfalari

NEDEN VAR: mevcut 59 kalem sayfasi tek bir sorgu kalibini hedefliyor -
"X fiyati". Ama insanlarin aradigi sey KENDI DURUMLARI: "100 kisilik
dugun maliyeti", "sadece beyaz esya butcesi", "mutfak esyalari kac para".
Bu sorgularin hepsinde veri elimizde var ama sayfa yoktu.

IKI TIP:
  1. Olcek senaryolari (dugun): 100 / 200 / 300 kisilik. Her biri
     GERCEKTEN farkli bir toplam veriyor - kisi basi kalemler olcekle
     carpiliyor.
  2. Grup senaryolari (ev kurma): yalnizca beyaz esya / mobilya / mutfak.
     Her biri kalem alt kumesinin gercek toplami.

INCE ICERIK DEGIL - kirmizi cizgi kontrolu: her sayfa farkli bir RAKAM,
farkli bir kalem listesi ve o senaryoya ozgu bir yorum tasiyor. Ayni
metnin sayi degistirilmis kopyasi degil. Uretilebilecek kombinasyon
sayisi kasitla dusuk tutuldu (3+3); "her sayi icin bir sayfa" yaklasimi
tam olarak Google'in cezalandirdigi sey.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import sayfa_uret as su

SITE_KOK = su.SITE_KOK
SITE_KOK_URL = su.SITE_KOK_URL


def _p(n) -> str:
    return su._para(n) if n else "—"


# Olcek senaryolari: yalnizca kisi-basi kalemi olan vertikaller icin
OLCEK_SENARYOLARI = {
    "dugun": [
        {
            "olcek": 100, "slug": "100-kisilik-dugun-maliyeti",
            "baslik": "100 Kişilik Düğün Maliyeti",
            "yorum": (
                "100 kişi, salon seçeneklerinin çoğunda alt sınıra yakın. Bazı "
                "mekanlar bu sayının altında minimum kişi şartı koyuyor; sözleşme "
                "imzalamadan önce mutlaka sorun. Küçük düğünde kişi başı fiyat "
                "genelde düşmez, aksine paket iskontosu kaybedilir."
            ),
        },
        {
            "olcek": 200, "slug": "200-kisilik-dugun-maliyeti",
            "baslik": "200 Kişilik Düğün Maliyeti",
            "yorum": (
                "200 kişi Türkiye'de yaygın bir düğün ölçeği. Bu bantta salon "
                "seçenekleri genişliyor ve kişi başı fiyatta pazarlık payı doğuyor "
                "— mekanlar dolu bir salonu tercih ettiği için hafta içi ya da "
                "sezon dışı tarihlerde indirim isteyebilirsiniz."
            ),
        },
        {
            "olcek": 300, "slug": "300-kisilik-dugun-maliyeti",
            "baslik": "300 Kişilik Düğün Maliyeti",
            "yorum": (
                "300 kişide salon kapasitesi belirleyici hale geliyor; bu ölçeği "
                "kaldıran mekan sayısı azalıyor ve fiyatlar yukarı ayrışıyor. "
                "Bütçenin neredeyse tamamı kişi başı kalemlere gidiyor, sabit "
                "kalemlerin (gelinlik, alyans) payı görece küçülüyor."
            ),
        },
    ],
}

# Grup senaryolari: kalem alt kumesi
GRUP_SENARYOLARI = {
    "ev-kurma": [
        {
            "slug": "beyaz-esya-fiyatlari",
            "gruplar": ["Beyaz eşya"],
            "baslik": "Beyaz Eşya Seti Fiyatları",
            "soru": "Bir evin beyaz eşyası ne kadar tutuyor?",
            "yorum": (
                "Beyaz eşya, ev kurma bütçesinin tek kalemde en büyük dilimi. "
                "Hepsini birden almak zorunda değilsiniz: taşındığınız gün "
                "çalışması gerekenler buzdolabı ve çamaşır makinesi. Bulaşık "
                "makinesi, kurutucu ve mikrodalga sonraya bırakılabilir."
            ),
        },
        {
            "slug": "mobilya-fiyatlari",
            "gruplar": ["Mobilya", "Yatak odası"],
            "baslik": "Ev Mobilyası Fiyatları",
            "soru": "Bir evi mobilyayla döşemek ne kadar tutuyor?",
            "yorum": (
                "Mobilyada fiyat farkı malzemeden çok markadan geliyor. Oturma "
                "grubu ve yatak, günde saatlerce temas ettiğiniz iki eşya — "
                "burada en ucuza kaçmak genelde iki yıl sonra tekrar alım "
                "demek. Sehpa, konsol gibi kalemler ise sonraya bırakılabilir."
            ),
        },
        {
            "slug": "mutfak-esyalari-fiyatlari",
            "gruplar": ["Mutfak", "Küçük ev aleti"],
            "baslik": "Mutfak Eşyaları ve Küçük Ev Aletleri Fiyatları",
            "soru": "Mutfak eşyaları ve küçük ev aletleri ne kadar tutuyor?",
            "yorum": (
                "Tek tek bakınca ucuz görünen ama sayıca fazla olduğu için "
                "toplamda şaşırtan grup bu. Tencere seti, tava, çatal-kaşık ve "
                "yemek takımı çekirdek ihtiyaç; airfryer, kahve makinesi ve "
                "mutfak robotu ise yaşam tarzına göre değişiyor."
            ),
        },
    ],
}


def _kalem_satirlari(conf: dict, kalemler: dict, detaylar: list, olcek: int) -> str:
    # Tahmini kalemler AYRI listede duruyor; yalnizca conf["kalemler"]e
    # bakarsak tabloda kalem adi yerine ham id gorunuyor ("orkestra-dj").
    tanimlar = {t["id"]: t for t in conf["kalemler"] + conf.get("tahmini_kalemler", [])}
    satirlar = []
    for d in sorted(detaylar, key=lambda x: -(x.get("satir_toplam") or 0)):
        if not d.get("satir_toplam") or not d.get("toplama_dahil"):
            continue
        t = tanimlar.get(d["id"], {})
        birim = " (kişi başı)" if t.get("birim") == "kisi_basi" else ""
        satirlar.append(
            f'<tr><td>{su._kisa_kalem_adi(t.get("ad", d["id"]))}</td>'
            f'<td class="sayi">{_p(d["birim_fiyat"])}{birim}</td>'
            f'<td class="sayi">{_p(d["satir_toplam"])}</td></tr>'
        )
    return "".join(satirlar)


def _konu_kumesi_html(vertikal: str, mevcut_slug: str) -> str:
    """Ayni vertikaldeki diger senaryo ve kalem sayfalarina baglar.

    NEDEN: senaryo sayfalari ("beyaz esya fiyatlari", "mobilya
    fiyatlari") en yuksek niyetli sorgulari hedefliyor ama olculdugunde
    her biri yalnizca 1 ic link veriyordu - kume degil, yalniz ada.
    Google'in bir siteyi bir konuda otorite saymasi, o konudaki
    sayfalarin BIRBIRINE baglanmasindan gecer.

    Yalnizca DISKTE VAR OLAN sayfalara link verilir - kirik link
    uretmek, hic link vermemekten kotu (rehber.py'deki ayni kural).
    """
    conf = su.VERTIKALLER[vertikal]
    yol = conf["yol"]
    parcalar = []

    # 1) Ayni vertikalin diger senaryolari
    for kaynak in (OLCEK_SENARYOLARI, GRUP_SENARYOLARI):
        for sen in kaynak.get(vertikal, []):
            if sen["slug"] == mevcut_slug:
                continue
            if (SITE_KOK / yol / sen["slug"] / "index.html").exists():
                parcalar.append((sen["slug"], sen["baslik"]))

    # 2) Ilgili kalem sayfalari
    for sayfa in su._ek_kalem_sayfalari(conf, {}) if False else conf.get("kalem_sayfalari", []):
        if (SITE_KOK / yol / sayfa["slug"] / "index.html").exists():
            parcalar.append((sayfa["slug"], sayfa["baslik"]))

    # Diskteki tum {kalem}-fiyatlari sayfalarini da topla (kalem sayfalari
    # veriye gore acilip kapaniyor, sabit listede olmayabilirler)
    for dizin in sorted((SITE_KOK / yol).glob("*-fiyatlari")):
        slug = dizin.name
        if slug == mevcut_slug or any(p[0] == slug for p in parcalar):
            continue
        if not (dizin / "index.html").exists():
            continue
        ad = slug.replace("-fiyatlari", "").replace("-", " ")
        parcalar.append((slug, ad[:1].upper() + ad[1:] + " fiyatları"))

    if not parcalar:
        return ""
    # Cok uzun liste sayfanin kendi icerigini bastirir (link-farm
    # gorunumu) - 12 ile sinirli, gerisi endekse yonlendiriliyor.
    gosterilen = parcalar[:12]
    linkler = "".join(
        f'<a href="/{yol}/{slug}/">{ad}</a>' for slug, ad in gosterilen
    )
    fazla = ""
    if len(parcalar) > len(gosterilen):
        fazla = (f' <a href="/{yol}/">+{len(parcalar) - len(gosterilen)} kalem '
                 f'daha ({conf["ad"].lower()} endeksi)</a>')
    return (
        '  <section class="icerik-bolumu konu-kumesi">\n'
        f'    <h2>{conf["ad"]} ile ilgili diğer fiyatlar</h2>\n'
        f'    <p class="kart-linkler">{linkler}{fazla}</p>\n'
        '  </section>\n'
    )


def _title(baslik: str) -> str:
    """SERP'te kesilmeyen baslik. Google ~60 karakterde kesiyor;
    marka eki uzun basliklarda kisaltiliyor, hedef ifade basta kaliyor."""
    ana = f"{baslik} 2026"
    for ek in (" | Maliyeti Ne?", " · Maliyeti Ne?", ""):
        if len(ana + ek) <= 60:
            return ana + ek
    return ana


def _sayfa_html(baslik: str, soru: str, aciklama_blok: str, govde: str,
                url: str, meta: str, breadcrumb: list, tarih: str,
                sorular: list[dict], konu_kumesi: str = "") -> str:
    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": f"{SITE_KOK_URL}/#kurum",
                "name": "Maliyeti Ne?",
                "url": SITE_KOK_URL,
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": i + 1, "name": ad, "item": link}
                    for i, (ad, link) in enumerate(breadcrumb)
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q["s"],
                     "acceptedAnswer": {"@type": "Answer", "text": q["c"]}}
                    for q in sorular
                ],
            },
        ],
    }
    kirinti = " <span aria-hidden=\"true\">›</span> ".join(
        f'<a href="{link}">{ad}</a>' if link else f"<span>{ad}</span>"
        for ad, link in [(a, (l.replace(SITE_KOK_URL, "") if l else None))
                         for a, l in breadcrumb]
    )
    sss_html = "".join(
        f"    <h3>{q['s']}</h3>\n    <p>{q['c']}</p>\n" for q in sorular
    )
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_title(baslik)}</title>
<meta name="description" content="{meta}">
<link rel="canonical" href="{url}">
<link rel="stylesheet" href="/assets/css/style.css">
<meta property="og:title" content="{baslik} 2026">
<meta property="og:description" content="{meta}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
{su.OG_ETIKETLERI}
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
      <a href="/okul/">Okul</a>
      <a href="/arac/">0 km Araç</a>
    </nav>
  </div>
</header>

<main class="kapsayici">

  <nav class="kirinti" aria-label="Sayfa yolu">{kirinti}</nav>

  <span class="guncelleme-etiketi">Güncelleme: {tarih}</span>
  <h1>{baslik}</h1>

  <div class="cevap-blok">{aciklama_blok}</div>

{govde}
  <section class="icerik-bolumu">
    <h2>Sık sorulan sorular</h2>
{sss_html}  </section>

{konu_kumesi}
  <p class="kunye">{tarih} tarihli ölçümlerden · <a href="/sss/">Sık sorulan sorular</a> · <a href="/veri/">Veriyi indir</a></p>

</main>

<footer>
  <div class="kapsayici">
    <div>© {tarih[:4]} Maliyeti Ne? · <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a> · <a href="/sss/">SSS</a> · <a href="/veri/">Veri</a></div>
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


def olcek_sayfasi(vertikal: str, senaryo: dict, veri: dict, tarih: str) -> str | None:
    conf = su.VERTIKALLER[vertikal]
    kalemler = veri.get("kalemler") or {}
    olcek = senaryo["olcek"]
    toplam, detaylar = su.ornek_toplam_hesapla(conf, kalemler, olcek=olcek, segment="orta")
    eko, _ = su.ornek_toplam_hesapla(conf, kalemler, olcek=olcek, segment="ekonomik")
    ust, _ = su.ornek_toplam_hesapla(conf, kalemler, olcek=olcek, segment="luks")
    # GERCEK olculmus kalem sarti: yalnizca tahmini kalemlerle sayfa
    # uretmek "100 kisilik dugun 28.500 TL" gibi yaniltici bir rakam
    # yayinlamak olurdu - tahminler her senaryoda ayni sabit tutar.
    gercek_kalem = sum(
        1 for d in detaylar
        if d.get("toplama_dahil") and d.get("satir_toplam") and not d.get("tahmini_mi")
    )
    if not toplam or gercek_kalem < 2:
        return None

    # Kisi basi / sabit kirilimi - bu senaryonun ayirt edici bilgisi
    kisi_basi_toplam = sum(
        d["satir_toplam"] for d in detaylar
        if d.get("toplama_dahil") and d.get("satir_toplam")
        and next((t for t in conf["kalemler"] if t["id"] == d["id"]), {}).get("birim") == "kisi_basi"
    )
    sabit_toplam = toplam - kisi_basi_toplam
    kisi_basi_birim = round(kisi_basi_toplam / olcek) if olcek else 0

    url = f"{SITE_KOK_URL}/{conf['yol']}/{senaryo['slug']}/"
    sorular = [
        {"s": f"{olcek} kişilik düğün ne kadar tutar?",
         "c": (f"Orta segmentte {_p(toplam)}. Ekonomik tercihlerle {_p(eko)}, "
               f"üst segmentte {_p(ust)}. Rakamlar {tarih} tarihinde ölçülen "
               "gerçek fiyatlardan hesaplandı.")},
        {"s": "Bu tutarın ne kadarı davetli sayısına bağlı?",
         "c": (f"{_p(kisi_basi_toplam)} kısmı kişi başı ödenen kalemlerden "
               f"(kişi başı yaklaşık {_p(kisi_basi_birim)}), {_p(sabit_toplam)} "
               "kısmı ise davetli sayısından bağımsız sabit kalemlerden geliyor. "
               f"Yani listeden çıkardığınız her 10 kişi yaklaşık "
               f"{_p(kisi_basi_birim * 10)} tasarruf demek.")},
        {"s": "Bu rakama neler dahil değil?",
         "c": ("Balayı, nişan ve kına organizasyonu, davetli ulaşımı ve "
               "konaklaması dahil değil. Ayrıca mekanların sezon ve gün "
               "farkı bu ortalamalara yansımıyor.")},
    ]
    govde = f"""  <section class="icerik-bolumu">
    <h2>Bütçe nasıl dağılıyor?</h2>
    <p>{senaryo["yorum"]}</p>
    <div class="tablo-sarmal"><table>
      <thead><tr><th>Kalem</th><th class="sayi">Birim</th><th class="sayi">{olcek} kişide</th></tr></thead>
      <tbody>{_kalem_satirlari(conf, kalemler, detaylar, olcek)}</tbody>
    </table></div>
    <p class="sonuc-alt-metin">Kişi başı ödenen kalemler davetli sayısıyla
      çarpılır; diğerleri sabittir.</p>
  </section>

  <section class="icerik-bolumu">
    <h2>Segmente göre {olcek} kişilik düğün</h2>
{su._segment_grafigi({"dusuk": eko, "orta": toplam, "luks": ust})}    <p>
      Aynı davetli sayısında ekonomik ve üst segment arasında
      {_p(ust - eko)} fark var. Bu fark tek bir kalemden değil, her kalemde
      alt ya da üst banda kaymaktan geliyor.
    </p>
  </section>

  <section class="icerik-bolumu">
    <h2>Farklı davetli sayısı için</h2>
    <p>
      Kendi sayınızı girip hesaplamak için
      <a href="/{conf['yol']}/hesaplayici/">düğün maliyeti hesaplayıcısını</a>
      kullanabilirsiniz. Kalem kalem güncel fiyatlar
      <a href="/{conf['yol']}/">düğün endeksinde</a>.
    </p>
  </section>
"""
    return _sayfa_html(
        baslik=senaryo["baslik"],
        soru=f"{olcek} kişilik düğün ne kadar tutar?",
        aciklama_blok=(
            f"{olcek} kişilik, orta segment bir düğün {tarih} itibarıyla "
            f"<strong>{_p(toplam)}</strong> tutuyor. Ekonomik tercihlerle "
            f"{_p(eko)}, üst segmentte {_p(ust)}. Bunun {_p(kisi_basi_toplam)} "
            f"kadarı davetli sayısına bağlı."
        ),
        govde=govde, url=url,
        meta=(f"{olcek} kişilik düğün maliyeti {tarih} itibarıyla {_p(toplam)}. "
              "Kalem kalem döküm, segment karşılaştırması ve ölçüm kaynakları."),
        breadcrumb=[("Ana sayfa", SITE_KOK_URL + "/"),
                    (conf["ad"], f"{SITE_KOK_URL}/{conf['yol']}/"),
                    (senaryo["baslik"], None)],
        tarih=tarih, sorular=sorular,
        konu_kumesi=_konu_kumesi_html(vertikal, senaryo["slug"]),
    )


def grup_sayfasi(vertikal: str, senaryo: dict, veri: dict, tarih: str) -> str | None:
    conf = su.VERTIKALLER[vertikal]
    kalemler = veri.get("kalemler") or {}
    hedef_gruplar = set(senaryo["gruplar"])
    ilgili = [t for t in conf["kalemler"] if t.get("grup") in hedef_gruplar]
    if len(ilgili) < 3:
        return None

    def toplam_hesapla(segment):
        toplam = 0
        satirlar = []
        for t in ilgili:
            deger = su.kalem_deger(kalemler.get(t["id"]), su.SEGMENT_ANAHTARI[segment])
            if not deger:
                continue
            toplam += deger
            satirlar.append((t, deger))
        return toplam, satirlar

    orta, satirlar = toplam_hesapla("orta")
    eko, _ = toplam_hesapla("ekonomik")
    ust, _ = toplam_hesapla("luks")
    if not orta or len(satirlar) < 3:
        return None

    tablo = "".join(
        f'<tr><td>{su._kisa_kalem_adi(t["ad"])}</td>'
        f'<td class="sayi">{_p(su.kalem_deger(kalemler.get(t["id"]), "dusuk"))}</td>'
        f'<td class="sayi">{_p(d)}</td>'
        f'<td class="sayi">{_p(su.kalem_deger(kalemler.get(t["id"]), "luks"))}</td></tr>'
        for t, d in sorted(satirlar, key=lambda x: -x[1])
    )
    # Tum vertikal icindeki pay
    tum_toplam, _ = su.ornek_toplam_hesapla(conf, kalemler, olcek=1, segment="orta")
    pay = round(orta / tum_toplam * 100) if tum_toplam else 0

    url = f"{SITE_KOK_URL}/{conf['yol']}/{senaryo['slug']}/"
    sorular = [
        {"s": senaryo["soru"],
         "c": (f"Orta segmentte {_p(orta)}. Ekonomik tercihlerle {_p(eko)}, "
               f"üst segmentte {_p(ust)}. {len(satirlar)} kalemin toplamı, "
               f"{tarih} tarihinde ölçüldü.")},
        {"s": "Tüm ev kurma bütçesinin ne kadarı?",
         "c": (f"Yaklaşık %{pay}. Tüm kalemlerle birlikte sıfırdan bir evi "
               f"eşyalandırmak orta segmentte {_p(tum_toplam)} tutuyor.")},
        {"s": "Hepsini birden almak zorunda mıyım?",
         "c": ("Hayır. Listeyi ihtiyaç sırasına göre bölmek, tek seferde "
               "ödenecek tutarı belirgin düşürüyor. Hesaplayıcıdan "
               "istemediğiniz kalemleri çıkarabilirsiniz.")},
    ]
    govde = f"""  <section class="icerik-bolumu">
    <h2>Kalem kalem</h2>
    <p>{senaryo["yorum"]}</p>
    <div class="tablo-sarmal"><table>
      <thead><tr><th>Ürün</th><th class="sayi">Ekonomik</th><th class="sayi">Orta</th><th class="sayi">Üst</th></tr></thead>
      <tbody>{tablo}</tbody>
    </table></div>
  </section>

  <section class="icerik-bolumu">
    <h2>Segmente göre toplam</h2>
{su._segment_grafigi({"dusuk": eko, "orta": orta, "luks": ust})}    <p>
      Ekonomik ve üst segment arasında {_p(ust - eko)} fark var. Bu grup,
      tüm ev kurma bütçesinin yaklaşık %{pay}'ini oluşturuyor.
    </p>
  </section>

  <section class="icerik-bolumu">
    <h2>Kendi listenizi çıkarın</h2>
    <p>
      Yalnızca istediğiniz kalemleri işaretleyip toplamınızı görebilirsiniz:
      <a href="/{conf['yol']}/hesaplayici/">ev kurma hesaplayıcısı</a>.
      Tüm kalemler ve güncel fiyatlar
      <a href="/{conf['yol']}/">ev kurma endeksinde</a>.
    </p>
  </section>
"""
    return _sayfa_html(
        baslik=senaryo["baslik"],
        soru=senaryo["soru"],
        aciklama_blok=(
            f"{senaryo['soru']} Orta segmentte <strong>{_p(orta)}</strong>. "
            f"Ekonomik tercihlerle {_p(eko)}, üst segmentte {_p(ust)}. "
            f"{len(satirlar)} kalemin toplamı — tüm ev kurma bütçesinin "
            f"yaklaşık %{pay}'i."
        ),
        govde=govde, url=url,
        meta=(f"{senaryo['baslik']} {tarih} itibarıyla {_p(orta)}. "
              "Kalem kalem ekonomik, orta ve üst segment fiyatlarıyla."),
        breadcrumb=[("Ana sayfa", SITE_KOK_URL + "/"),
                    (conf["ad"], f"{SITE_KOK_URL}/{conf['yol']}/"),
                    (senaryo["baslik"], None)],
        tarih=tarih, sorular=sorular,
        konu_kumesi=_konu_kumesi_html(vertikal, senaryo["slug"]),
    )


def senaryolari_yaz(veri_kok: Path | None = None) -> list[tuple[str, str]]:
    kok = veri_kok or SITE_KOK / "veri"
    yazilanlar = []
    for vertikal, senaryolar in OLCEK_SENARYOLARI.items():
        dosya = kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        veri = json.loads(dosya.read_text(encoding="utf-8"))
        tarih = veri.get("guncelleme_tarihi") or date.today().isoformat()
        for s in senaryolar:
            html = olcek_sayfasi(vertikal, s, veri, tarih)
            if not html:
                continue
            hedef = SITE_KOK / su.VERTIKALLER[vertikal]["yol"] / s["slug"] / "index.html"
            hedef.parent.mkdir(parents=True, exist_ok=True)
            hedef.write_text(html, encoding="utf-8")
            yazilanlar.append((vertikal, s["slug"]))
    for vertikal, senaryolar in GRUP_SENARYOLARI.items():
        dosya = kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        veri = json.loads(dosya.read_text(encoding="utf-8"))
        tarih = veri.get("guncelleme_tarihi") or date.today().isoformat()
        for s in senaryolar:
            html = grup_sayfasi(vertikal, s, veri, tarih)
            if not html:
                continue
            hedef = SITE_KOK / su.VERTIKALLER[vertikal]["yol"] / s["slug"] / "index.html"
            hedef.parent.mkdir(parents=True, exist_ok=True)
            hedef.write_text(html, encoding="utf-8")
            yazilanlar.append((vertikal, s["slug"]))
    return yazilanlar


def tum_slugler() -> list[tuple[str, str]]:
    """sitemap ve ic link uretimi icin - dosya varligina bakmadan."""
    cikti = []
    for v, ss in OLCEK_SENARYOLARI.items():
        cikti += [(v, s["slug"]) for s in ss]
    for v, ss in GRUP_SENARYOLARI.items():
        cikti += [(v, s["slug"]) for s in ss]
    return cikti


def main():
    yazilanlar = senaryolari_yaz()
    for v, slug in yazilanlar:
        print(f"Senaryo sayfasi: /{su.VERTIKALLER[v]['yol']}/{slug}/")
    print(f"Toplam {len(yazilanlar)} senaryo sayfasi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
