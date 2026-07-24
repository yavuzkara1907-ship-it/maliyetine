# -*- coding: utf-8 -*-
"""
Sayfa yapisi tani araci (v0.2)

CSS secici doldurmak icin F12 ile elle bakmak yerine bu script'i
calistir - sayfayi ceker, JSON-LD/microdata/meta etiketi var mi
kontrol eder, en cok tekrar eden class isimlerini listeler (urun
karti adayi). Ciktiyi oldugu gibi paylas, css_secicileri oradan
doldurulur.

`requests` 403 alirsa (Akakce/Trendyol gibi WAF korumali siteler)
otomatik olarak motor.py'nin Playwright katmanina dusulur - ayrica
bir bayrak belirtmene gerek yok.

Kullanim:
  python sayfa_tani.py https://ORNEK-SITE.com/kategori
"""

import sys
from collections import Counter

import requests
from bs4 import BeautifulSoup

import motor


def _html_getir(url: str):
    try:
        r = requests.get(url, headers=motor.HEADERS, timeout=20)
    except requests.RequestException as e:
        print(f"[HATA] requests ile cekilemedi: {e}")
        return None

    print(f"HTTP durumu (requests): {r.status_code}")
    if r.status_code == 403:
        print("403 alindi - Playwright (gercek tarayici) ile deniyorum...")
        html = motor.getir_playwright(url)
        if html is None:
            print(
                "[HATA] Playwright ile de cekilemedi. 'playwright install "
                "chromium' calistirildi mi kontrol et."
            )
            return None
        print("Playwright ile basarili.")
        return html

    if r.status_code >= 400:
        print(f"[HATA] HTTP {r.status_code}")
        return None
    return r.text


def tani(url: str) -> None:
    html = _html_getir(url)
    if html is None:
        return
    print(f"Yanit uzunlugu: {len(html)} karakter\n")

    print("=== HAM HTML - ilk 1500 karakter (JS-render/SPA/captcha teshisi icin) ===")
    print(html[:1500])
    print("=== HAM HTML - son 500 karakter ===")
    print(html[-500:])
    print()

    soup = BeautifulSoup(html, "html.parser")

    # SPA/JS-render belirtileri: sayfa gercekte urun icermiyor olabilir,
    # sadece bos bir "app" kabugu + JS bundle donuyor olabilir.
    bos_kapsayicilar = soup.select("#root, #app, #__next, [data-reactroot]")
    script_sayisi = len(soup.find_all("script"))
    print(f"=== SPA/JS-render belirtileri ===")
    print(f"  <script> etiketi sayisi: {script_sayisi}")
    print(f"  #root/#app/#__next kapsayici sayisi: {len(bos_kapsayicilar)}")
    for k in bos_kapsayicilar[:2]:
        ic_uzunluk = len(k.get_text(strip=True))
        print(f"    {k.get('id') or k.get('class')}: ic metin uzunlugu {ic_uzunluk} karakter"
              f"{' (BOS - JS henuz doldurmamis olabilir)' if ic_uzunluk < 20 else ''}")
    print()

    json_ld = soup.find_all("script", type="application/ld+json")
    print(f"=== JSON-LD script sayisi: {len(json_ld)} ===")
    for i, tag in enumerate(json_ld[:3]):
        icerik = (tag.string or "")[:400]
        print(f"  [{i}] ilk 400 karakter:\n  {icerik}\n")

    microdata = soup.select('[itemtype*="schema.org"]')
    print(f"=== itemtype=schema.org eleman sayisi: {len(microdata)} ===")
    if microdata:
        print(f"  ornek itemtype: {microdata[0].get('itemtype')}")

    fiyat_meta = soup.select('meta[property*="price"], meta[itemprop="price"]')
    print(f"\n=== price meta/itemprop etiketi sayisi: {len(fiyat_meta)} ===")
    for m in fiyat_meta[:3]:
        print(f"  {m}")

    class_sayaci = Counter()
    for el in soup.find_all(class_=True):
        for c in el.get("class", []):
            class_sayaci[c] += 1
    print("\n=== En cok tekrar eden 25 class adi (urun karti/isim/fiyat adayi) ===")
    for c, n in class_sayaci.most_common(25):
        print(f"  {n:5d}  {c}")

    # "TL" veya "₺" iceren kisa metinli elemanlar - fiyat adayi
    print("\n=== 'TL' veya '₺' iceren ilk 10 eleman (fiyat adayi) ===")
    bulunan = 0
    for el in soup.find_all(string=lambda s: s and ("TL" in s or "₺" in s) and len(s.strip()) < 30):
        ebeveyn = el.parent
        print(f"  <{ebeveyn.name} class={ebeveyn.get('class')}> {el.strip()!r}")
        bulunan += 1
        if bulunan >= 10:
            break

    # Urun karti adayi tahmini: class adinda "product"/"item"/"card" gecen
    # ve makul sayida (2-500) tekrar eden konteynerlerin TAM HTML'ini
    # dokuyor - CSS secici doldurmak icin en degerli kisim burasi.
    print("\n=== URUN KARTI ADAYLARI - tam HTML (css_secicileri icin) ===")
    adaylar = {}
    for el in soup.find_all(class_=True):
        for c in el.get("class", []):
            cl = c.lower()
            if any(k in cl for k in ("product", "item", "card")) and "checkbox" not in cl:
                adaylar.setdefault(c, []).append(el)

    gosterilen = 0
    for sinif, elemanlar in sorted(adaylar.items(), key=lambda kv: -len(kv[1])):
        if not (2 <= len(elemanlar) <= 500):
            continue
        print(f"\n--- class='{sinif}' ({len(elemanlar)} eslesme) ---")
        # Once TEMIZ METIN (markup gurultusu olmadan isim/fiyat sirasini
        # gormek icin en degerli kisim), sonra kesilmis ham HTML.
        temiz_metin = elemanlar[0].get_text(separator=" | ", strip=True)
        print(f"  Temiz metin: {temiz_metin[:600]}")
        print(f"  Ham HTML (ilk 3000 karakter):")
        print(str(elemanlar[0])[:3000])
        gosterilen += 1
        if gosterilen >= 5:
            break


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Kullanim: python sayfa_tani.py <url>")
        sys.exit(1)
    tani(sys.argv[1])
