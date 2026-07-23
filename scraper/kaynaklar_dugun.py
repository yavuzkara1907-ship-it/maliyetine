# -*- coding: utf-8 -*-
"""
Dugun maliyeti vertikali - aday kaynak kayit defteri (v0.1)

Bu liste WebSearch ile bulundu. Bu ortamin (Claude Code sandbox) network
politikasi bu domain'lere dogrudan baglantiyi engelliyor (CONNECT 403,
bkz. $HTTPS_PROXY/__agentproxy/status) - yani robots.txt icerigi VE
sayfa HTML'i (CSS secici tespiti icin) BU ORTAMDAN dogrulanamadi.

Yavuz'un yapmasi gerekenler (kendi makinesinde / erisimi acik bir ortamda):
  1. Her aday URL icin robots_kontrol.py calistir.
  2. ONAY cikanlarda sayfayi F12 ile ac, urun_karti / isim_secici /
     fiyat_secici CSS seciciyi bul, asagidaki "css" alanini doldur.
  3. RET cikanlari veya kullanim sartlarina aykiri olanlari "reddedildi"
     olarak isaretle, KULLANMA.

DURUM DEGERLERI:
  "arastirildi"   -> sadece WebSearch ile bulundu, hicbir sey dogrulanmadi.
  "onaylandi"     -> robots.txt + KS incelendi, kazima icin acik.
  "reddedildi"    -> robots.txt engelliyor veya KS uygun degil, KULLANMA.
"""

KALEMLER = {
    "gelinlik": {
        "aciklama": (
            "Gelinlik urun fiyatlari. Genis SKU sayisi oldugu icin "
            "persentil segmentleme (dusuk/orta/luks) icin en uygun kalem."
        ),
        "adaylar": [
            {
                "site": "trendyol.com",
                "url_ornek": "https://www.trendyol.com/gelinlik-x-c57",
                "durum": "arastirildi",
                "not": (
                    "Buyuk e-ticaret katalogu, cok sayida urun. Cloudflare/"
                    "Akamai tipi bot korumasi olasi - Playwright gerekebilir."
                ),
                "css": None,
            },
            {
                "site": "hepsiburada.com",
                "url_ornek": "https://www.hepsiburada.com/gelinlik-modelleri-c-12087251",
                "durum": "arastirildi",
                "not": "Ayni sekilde genis katalog.",
                "css": None,
            },
        ],
    },
    "salon": {
        "aciklama": "Dugun salonu / mekan kisi basi veya paket fiyatlari.",
        "adaylar": [
            {
                "site": "dugunbuketi.com",
                "url_ornek": "https://dugunbuketi.com/c/dugun-mekanlari/istanbul",
                "durum": "arastirildi",
                "not": (
                    "Sehir bazli mekan listesi, fiyat araligi gosteriyor "
                    "gibi gorunuyor (arama sonucu ozetinden). Lead-gen "
                    "sitesi - bot korumasi ve KS'yi dikkatle oku."
                ),
                "css": None,
            },
        ],
    },
    "fotografci": {
        "aciklama": "Dugun fotografcisi / dis cekim paket fiyatlari.",
        "adaylar": [
            {
                "site": "dugunbuketi.com",
                "url_ornek": "https://dugunbuketi.com/p/dis-cekim-dugun-fotografcisi/istanbul",
                "durum": "arastirildi",
                "not": "Sehir bazli fotografci listesi + fiyat araligi.",
                "css": None,
            },
            {
                "site": "armut.com",
                "url_ornek": "https://armut.com/fiyatlari/dugun-fotografcisi_194",
                "durum": "arastirildi",
                "not": (
                    "Bu 'fiyatlari' sayfalari tek bir agregat ortalama "
                    "gosteriyor olabilir - percentile segmentleme icin "
                    "yeterli sayida ham fiyat noktasi saglamayabilir. "
                    "Once sayfa yapisini kontrol et."
                ),
                "css": None,
            },
        ],
    },
}


def ozet_yazdir():
    for kalem, veri in KALEMLER.items():
        print(f"\n## {kalem} - {veri['aciklama']}")
        for aday in veri["adaylar"]:
            print(f"  - [{aday['durum']}] {aday['site']}: {aday['url_ornek']}")
            print(f"    not: {aday['not']}")


if __name__ == "__main__":
    ozet_yazdir()
