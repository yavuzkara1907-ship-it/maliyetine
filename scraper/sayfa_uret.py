# -*- coding: utf-8 -*-
"""
maliyetine.com - Statik Sayfa Ureteci (v0.1)

/veri/{vertikal}.json'daki (agrega.py ciktisi) GERCEK sayilari statik
HTML'e gomer - GEO icin sart: AI botlarinin cogu (GPTBot vb.) JavaScript
calistirmaz, bu yuzden cevap bloğundaki rakam sayfa kaynagi HTML'inde
(fetch ile degil) bulunmak zorunda. Hesaplayici (JS, etkilesimli) bu
kisitlamaya tabi degil - ama endeks sayfasi (GEO'nun hedefi) build-time'da
uretilir.

Aylik otomasyonda sirasi: motor.py -> agrega.py -> sayfa_uret.py -> commit.

Kullanim:
  python sayfa_uret.py --vertikal dugun
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).parent
SITE_KOK = BASE_DIR.parent
VARSAYILAN_VERI = SITE_KOK / "veri" / "dugun.json"
VARSAYILAN_HEDEF = SITE_KOK / "dugun" / "index.html"

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

DUGUN_KALEMLERI_VERISIZ = [
    "Takı ve Altın", "Yemek / İkram (salona dahil değilse)", "Fotoğraf ve Video",
    "Orkestra / DJ", "Gelin Arabası", "Kuaför ve Makyaj",
    "Organizasyon / Süsleme", "Nikah İşlemleri (resmi harçlar)",
]

SEGMENT_ANAHTARI = {"ekonomik": "dusuk", "orta": "orta", "luks": "luks"}
SEGMENT_ETIKETLERI = {"dusuk": "Ekonomik", "orta": "Orta", "luks": "Lüks"}

ORNEK_DAVETLI_SAYISI = 150
ORNEK_SEGMENT = "orta"


def _para(n: int) -> str:
    return f"{n:,.0f}".replace(",", ".") + " TL"


def kalem_deger(kalem_verisi: dict | None, segment_anahtari: str) -> int | None:
    if not kalem_verisi:
        return None
    seg = kalem_verisi.get("segmentler", {}).get(segment_anahtari)
    if seg:
        return seg["medyan"]
    return kalem_verisi.get("genel_medyan")


def ornek_toplam_hesapla(kalemler: dict, davetli_sayisi: int, segment: str) -> tuple[int, list[dict]]:
    seg_anahtari = SEGMENT_ANAHTARI[segment]
    toplam = 0
    detaylar = []
    for tanim in DUGUN_KALEMLERI:
        veri = kalemler.get(tanim["id"])
        deger = kalem_deger(veri, seg_anahtari)
        if deger is None:
            detaylar.append({**tanim, "veri_var": False})
            continue
        carpan = davetli_sayisi if tanim["birim"] == "kisi_basi" else 1
        satir_toplam = round(deger * carpan)
        toplam += satir_toplam
        detaylar.append({**tanim, "veri_var": True, "birim_fiyat": deger, "satir_toplam": satir_toplam})
    return toplam, detaylar


def _kalem_satirlari_html(kalemler: dict) -> str:
    satirlar = []
    for tanim in DUGUN_KALEMLERI:
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
    return "\n".join(satirlar)


def _capraz_dogrulama_uyarilari_html(kalemler: dict) -> str:
    uyarilar = []
    ad_haritasi = {t["id"]: t["ad"] for t in DUGUN_KALEMLERI}
    for kalem_id, veri in kalemler.items():
        uyari = veri.get("capraz_dogrulama_uyarisi")
        if uyari:
            ad = ad_haritasi.get(kalem_id, kalem_id)
            uyarilar.append(
                f"<li><strong>{ad}:</strong> kaynaklar arası fark %{uyari['fark_yuzdesi']:.0f} "
                "— farklı segment/marka aralığını yansıtıyor olabilir, "
                '<a href="/dugun/metodoloji/">metodolojiye bakın</a>.</li>'
            )
    if not uyarilar:
        return ""
    return (
        '<div class="uyari-kutu"><strong>Çapraz doğrulama notu:</strong>'
        "<ul>" + "\n".join(uyarilar) + "</ul></div>"
    )


def _verisiz_liste_html() -> str:
    return "\n".join(f"<li>{ad}</li>" for ad in DUGUN_KALEMLERI_VERISIZ)


def sayfa_uret(veri_dosyasi: Path = VARSAYILAN_VERI) -> str:
    if veri_dosyasi.exists():
        agregali = json.loads(veri_dosyasi.read_text(encoding="utf-8"))
    else:
        agregali = {"vertikal": "dugun", "guncelleme_tarihi": None, "kalemler": {}}

    kalemler = agregali.get("kalemler", {})
    guncelleme_tarihi = agregali.get("guncelleme_tarihi")
    bugun = date.today().isoformat()

    ornek_toplam, ornek_detaylar = ornek_toplam_hesapla(kalemler, ORNEK_DAVETLI_SAYISI, ORNEK_SEGMENT)
    kapsanan_detaylar = [d for d in ornek_detaylar if d["veri_var"]]

    # "kalemler" dolu ama HEPSI genel_medyan=null (ör. o ay tum kaynaklar
    # 0 urun dondu) olabilir - bu durumda "0 TL" gibi yaniltici bir cevap
    # UYDURMAMAK icin gercek kapsanan kalem olup olmadigina bakiliyor,
    # sadece kalemler sozlugunun bos olmadigina degil.
    if kapsanan_detaylar:
        kapsanan_idler = {d["id"] for d in kapsanan_detaylar}
        kaynak_sayisi_toplam = sum(
            v.get("kaynak_sayisi", 0) for k, v in kalemler.items() if k in kapsanan_idler
        )
        kapsanan_kalem_sayisi = len(kapsanan_detaylar)
        cevap_metni = (
            f"Maliyetine'ye göre {guncelleme_tarihi or bugun} itibarıyla "
            f"{ORNEK_DAVETLI_SAYISI} kişilik, orta segment bir düğünün "
            f"<strong>{_para(ornek_toplam)}</strong> tutmasi bekleniyor. "
            f"Bu tahmin {kapsanan_kalem_sayisi} kalem için {kaynak_sayisi_toplam} "
            "bağımsız kaynaktan derlenen güncel fiyatlara dayanır (gelinlik, "
            "damatlık, alyans, salon ve diğerleri). Fotoğrafçı, kuaför ve "
            "balayı gibi henüz kaynağı doğrulanmamış kalemler dahil değildir."
        )
        cevap_disable = ""
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
                    "name": "2026'da İstanbul'da düğün kaça mal olur?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": cevap_metni.replace("<strong>", "").replace("</strong>", ""),
                    },
                }],
            },
            {
                "@type": "Dataset",
                "name": "Maliyetine Düğün Maliyeti Endeksi",
                "description": "Türkiye'de düğün kalemlerinin gerçek e-ticaret ve ilan verisinden derlenen aylık fiyat endeksi.",
                "dateModified": guncelleme_tarihi or bugun,
                "creator": {"@type": "Organization", "name": "Maliyetine.com.tr"},
            },
        ],
    }

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026'da Düğün Kaça Mal Olur? | Maliyetine.com.tr</title>
<meta name="description" content="Gerçek e-ticaret ve ilan verisinden derlenmiş, aylık güncellenen düğün maliyeti endeksi. Gelinlik, damatlık, alyans, salon ve daha fazlası — kaynak ve tarihiyle.">
<link rel="canonical" href="https://maliyetine.com.tr/dugun/">
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
      <a href="/dugun/hesaplayici/">Hesaplayıcı</a>
      <a href="/dugun/metodoloji/">Metodoloji</a>
    </nav>
  </div>
</header>

<main class="kapsayici">

  {guncelleme_etiketi}
  <h1>2026'da İstanbul'da Düğün Kaça Mal Olur?</h1>

  <div class="cevap-blok"{cevap_disable}>
    {cevap_metni}
  </div>

  <p><a href="/dugun/hesaplayici/">Kendi davetli sayınız ve segmentinizle hesaplayın →</a></p>

  <h2>Kalem kalem fiyatlar</h2>
  <table>
    <thead>
      <tr><th>Kalem</th><th class="sayi">Ekonomik</th><th class="sayi">Orta</th><th class="sayi">Lüks</th><th class="sayi">Kaynak</th></tr>
    </thead>
    <tbody>
      {_kalem_satirlari_html(kalemler)}
    </tbody>
  </table>

  {_capraz_dogrulama_uyarilari_html(kalemler)}

  <h2>Henüz veri kapsamında olmayan kalemler</h2>
  <p>Bu kalemler için henüz güvenilir bir kaynak bulunamadı, tahmini bir
    rakam <em>uydurulmuyor</em> — kaynak doğrulandığında eklenecek.</p>
  <ul>
    {_verisiz_liste_html()}
  </ul>

  <p>Yöntem, kaynaklar ve örneklem büyüklükleri için
    <a href="/dugun/metodoloji/">metodoloji sayfasına</a> bakın.</p>

</main>

<footer>
  <div class="kapsayici">
    <div>© 2026 Maliyetine.com.tr</div>
    <nav>
      <a href="/dugun/hesaplayici/">Hesaplayıcı</a>
      <a href="/dugun/metodoloji/">Metodoloji</a>
    </nav>
  </div>
</footer>

</body>
</html>
"""


def main():
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument("--veri", type=Path, default=VARSAYILAN_VERI)
    ayristirici.add_argument("--hedef", type=Path, default=VARSAYILAN_HEDEF)
    args = ayristirici.parse_args()

    html = sayfa_uret(args.veri)
    args.hedef.parent.mkdir(parents=True, exist_ok=True)
    args.hedef.write_text(html, encoding="utf-8")
    print(f"Sayfa uretildi: {args.hedef}")


if __name__ == "__main__":
    main()
