# -*- coding: utf-8 -*-
"""
maliyetine.com - Fiyat Endeksi Kazima Hatti (v0.1)
Ornek kategori: Buzdolabi

Kullanim:
  pip install requests beautifulsoup4
  python fiyat_endeksi.py

JS ile yuklenen siteler icin (gerekirse):
  pip install playwright && playwright install chromium
"""

import json
import re
import statistics
import time
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ----------------------------------------------------------
# 1) AYARLAR - Her kategori icin sadece burasi degisir
# ----------------------------------------------------------
CONFIG = {
    "kategori": "buzdolabi",
    # Hedef sitenin kategori/listeleme URL'i. {page} sayfa numarasi olur.
    "url_sablonu": "https://ORNEK-SITE.com/buzdolabi?sayfa={page}",
    "sayfa_sayisi": 5,  # kac sayfa gezilecek
    # CSS secicileri: hedef sitede F12 ile bakip doldur.
    "urun_karti": "div.product-card",      # her urunun kapsayicisi
    "isim_secici": "h3.product-name",      # urun adi
    "fiyat_secici": "span.price",          # fiyat
    "bekleme_sn": 2,  # sayfalar arasi bekleme (siteyi yorma!)
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
}


# ----------------------------------------------------------
# 2) FIYAT TEMIZLEME - "45.999,00 TL" -> 45999.0
# ----------------------------------------------------------
def fiyat_ayikla(metin: str):
    metin = metin.replace("TL", "").replace("₺", "").strip()
    metin = metin.replace(".", "").replace(",", ".")
    sayilar = re.findall(r"\d+(?:\.\d+)?", metin)
    return float(sayilar[0]) if sayilar else None


# ----------------------------------------------------------
# 3) KAZIMA
# ----------------------------------------------------------
def sayfa_kazi(url: str):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    urunler = []
    for kart in soup.select(CONFIG["urun_karti"]):
        isim = kart.select_one(CONFIG["isim_secici"])
        fiyat = kart.select_one(CONFIG["fiyat_secici"])
        if not (isim and fiyat):
            continue
        f = fiyat_ayikla(fiyat.get_text())
        if f and f > 1000:  # bariz hatalari ele
            urunler.append({"isim": isim.get_text(strip=True), "fiyat": f})
    return urunler


def tum_sayfalari_kazi():
    hepsi = []
    for p in range(1, CONFIG["sayfa_sayisi"] + 1):
        url = CONFIG["url_sablonu"].format(page=p)
        try:
            urunler = sayfa_kazi(url)
            print(f"Sayfa {p}: {len(urunler)} urun")
            hepsi.extend(urunler)
        except Exception as e:
            print(f"Sayfa {p} hata: {e}")
        time.sleep(CONFIG["bekleme_sn"])
    return hepsi


# ----------------------------------------------------------
# 4) AYKIRI DEGER TEMIZLIGI (IQR yontemi)
# ----------------------------------------------------------
def aykiri_temizle(urunler):
    fiyatlar = sorted(u["fiyat"] for u in urunler)
    n = len(fiyatlar)
    if n < 20:
        return urunler
    q1 = fiyatlar[n // 4]
    q3 = fiyatlar[(3 * n) // 4]
    iqr = q3 - q1
    alt, ust = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return [u for u in urunler if alt <= u["fiyat"] <= ust]


# ----------------------------------------------------------
# 5) SEGMENTLEME - dusuk / orta / luks
# ----------------------------------------------------------
def segmentle(urunler):
    fiyatlar = sorted(u["fiyat"] for u in urunler)
    n = len(fiyatlar)
    p25, p75 = fiyatlar[n // 4], fiyatlar[(3 * n) // 4]

    seg = {"dusuk": [], "orta": [], "luks": []}
    for u in urunler:
        if u["fiyat"] <= p25:
            seg["dusuk"].append(u["fiyat"])
        elif u["fiyat"] <= p75:
            seg["orta"].append(u["fiyat"])
        else:
            seg["luks"].append(u["fiyat"])

    ozet = {}
    for ad, liste in seg.items():
        if liste:
            ozet[ad] = {
                "min": round(min(liste)),
                "medyan": round(statistics.median(liste)),
                "max": round(max(liste)),
                "urun_sayisi": len(liste),
            }
    return ozet


# ----------------------------------------------------------
# 6) CALISTIR ve KAYDET
# ----------------------------------------------------------
def main():
    print(f"== {CONFIG['kategori']} kazima basliyor ==")
    urunler = tum_sayfalari_kazi()
    print(f"Toplam ham urun: {len(urunler)}")

    urunler = aykiri_temizle(urunler)
    print(f"Temiz urun: {len(urunler)}")

    if not urunler:
        print("Urun bulunamadi - CSS secicilerini kontrol et (F12).")
        return

    ozet = {
        "kategori": CONFIG["kategori"],
        "tarih": date.today().isoformat(),
        "toplam_urun": len(urunler),
        "segmentler": segmentle(urunler),
    }

    cikti = Path(f"{CONFIG['kategori']}_{date.today().isoformat()}.json")
    cikti.write_text(json.dumps(ozet, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    print(json.dumps(ozet, ensure_ascii=False, indent=2))
    print(f"\nKaydedildi: {cikti}")
    print("Bu JSON'u her ay biriktir -> fiyat gecmisi grafigin olusur.")


if __name__ == "__main__":
    main()
