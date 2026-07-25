# -*- coding: utf-8 -*-
"""
Maliyeti Ne? - Toplu Kaynak Tarayici (v0.1)

NEDEN VAR: yeni kaynak aramak en pahali isti - her aday icin ayri ayri
robots.txt kontrolu, URL tahmini, cekilebilirlik testi, "fiyat var mi"
teshisi yapiliyordu ve adaylarin cogu bos cikiyordu. Bu script hepsini
TEK SEFERDE yapip tek bir tablo doner; sadece YESIL cikan adaylarla
ugrasilir.

Her aday icin sirasiyla:
  1. robots.txt izni (protego, motor.py ile ayni mantik)
  2. ana sayfadan kategori linki avlama (URL tahmin etmek yerine - 404
     tahminleriyle vakit kaybetmenin panzehiri)
  3. kategori sayfasini cekme
  4. JSON-LD / microdata / gorunur fiyat var mi

Kullanim:
  python kaynak_tara.py                    # varsayilan aday listesi
  python kaynak_tara.py --anahtar televizyon buzdolabi
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from urllib.parse import urljoin, urlparse

warnings.filterwarnings("ignore")

from bs4 import BeautifulSoup  # noqa: E402

import motor  # noqa: E402

# Yavuz'un onerdigi adaylar (2026-07-26) + epey (fiyat gecmisi icin ayri
# degerli: urun sayfalarinda tarihsel fiyat grafigi tutuyor).
ADAYLAR = [
    ("idefix", "https://www.idefix.com"),
    ("epttavm", "https://www.epttavm.com"),
    ("bosch", "https://www.bosch-home.com.tr"),
    ("profilo", "https://www.profilo.com"),
    ("arcelik", "https://www.arcelik.com.tr"),
    ("beko", "https://www.beko.com.tr"),
    ("lg", "https://www.lg.com/tr"),
    ("samsung", "https://www.samsung.com/tr"),
    ("ciceksepeti", "https://www.ciceksepeti.com"),
    ("epey", "https://www.epey.com"),
]

VARSAYILAN_ANAHTARLAR = ["televizyon", "buzdolabi", "buzdolabı", "camasir", "çamaşır"]

FIYAT_DESENI = re.compile(r"[\d][\d.,]{2,}\s*(?:TL|₺)|₺\s*[\d][\d.,]{2,}")

# Fiyat gibi gorunup fiyat OLMAYAN metinler. idefix ilk taramada "62 fiyat"
# ile en umut verici aday cikmisti; sonra anlasildi ki bunlarin cogu
# "TROY ile 200 TL Indirim" gibi promosyon rozetleriydi. Bu filtre olmadan
# tarayici yanlis pozitif verip bir sonraki turu bosa harciyor.
SAHTE_FIYAT = re.compile(r"indirim|kupon|kampanya|hediye|kargo|taksit|puan", re.I)


def kategori_linkleri(ana_html: str, taban: str, anahtarlar: list[str]) -> list[str]:
    """Ana sayfadan anahtar kelime iceren kategori linklerini toplar.

    URL TAHMIN ETMEK YERINE bu: onceki turlarda tahmin edilen kategori
    URL'lerinin cogu 404 verdi (Vatan, IKEA, Bellona, Altinbas...) ve her
    404 bir tur kaybi oldu. Sitenin kendi verdigi linki kullanmak hem
    dogru hem tek istek.
    """
    corba = BeautifulSoup(ana_html, "html.parser")
    bulunan: list[str] = []
    for a in corba.select("a[href]"):
        href = a["href"]
        metin = (a.get_text(" ", strip=True) or "").lower()
        hedef = (href + " " + metin).lower()
        if not any(k in hedef for k in anahtarlar):
            continue
        tam = urljoin(taban, href).split("?")[0].split("#")[0]
        if urlparse(tam).netloc.replace("www.", "") != urlparse(taban).netloc.replace("www.", ""):
            continue
        if tam not in bulunan:
            bulunan.append(tam)
    return bulunan


def sayfa_teshis(html: str) -> dict:
    corba = BeautifulSoup(html, "html.parser")
    ld_urun = 0
    for blok in corba.select('script[type="application/ld+json"]'):
        try:
            veri = json.loads(blok.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for dugum in veri if isinstance(veri, list) else [veri]:
            if not isinstance(dugum, dict):
                continue
            tipler = json.dumps(dugum.get("@type", ""))
            if "Product" in tipler or "ItemList" in tipler:
                ld_urun += 1
    # Fiyati METIN DUGUMU bazinda say ve promosyon rozetlerini ele: tum
    # sayfa metninde regex saymak "200 TL Indirim" gibi ifadeleri fiyat
    # zanneder (idefix dersi).
    gercek_fiyat = 0
    kart_ici_fiyat = 0
    for dugum in corba.find_all(string=FIYAT_DESENI):
        if SAHTE_FIYAT.search(dugum):
            continue
        gercek_fiyat += 1
        # Fiyatin bir urun LINKI icinde olmasi, kart<->fiyat eslesmesinin
        # kurulabilecegini gosterir. idefix'te 97 urun linki vardi ama
        # fiyatlarin yalnizca 1'i link icindeydi - yani fiyatlar ayri bir
        # DOM dalinda ve hangi urune ait oldugu guvenilir sekilde
        # belirlenemiyordu. Bu sayi dusukse kaynak kazinabilir DEGIL.
        ata = dugum.parent
        for _ in range(8):
            if ata is None:
                break
            if ata.name == "a" and ata.get("href"):
                kart_ici_fiyat += 1
                break
            ata = ata.parent
    return {
        "boyut": len(html),
        "jsonld_urun": ld_urun,
        "microdata": len(corba.select('[itemprop="price"]')),
        "fiyat_metni": gercek_fiyat,
        "kart_ici": kart_ici_fiyat,
    }


def adayi_tara(ad: str, taban: str, anahtarlar: list[str]) -> dict:
    sonuc = {"ad": ad, "taban": taban, "durum": "", "url": "", "teshis": {}}
    if not motor.robots_izin_var(taban):
        sonuc["durum"] = "ROBOTS RET (ana sayfa)"
        return sonuc
    ana = motor.getir(taban)
    if not ana:
        sonuc["durum"] = "ANA SAYFA CEKILEMEDI"
        return sonuc

    adaylar = kategori_linkleri(ana, taban, anahtarlar)
    if not adaylar:
        sonuc["durum"] = "KATEGORI LINKI BULUNAMADI"
        return sonuc

    for url in adaylar[:3]:
        if not motor.robots_izin_var(url):
            sonuc["durum"] = "ROBOTS RET (kategori)"
            sonuc["url"] = url
            continue
        html = motor.getir(url)
        if not html:
            sonuc["durum"] = "KATEGORI CEKILEMEDI"
            sonuc["url"] = url
            continue
        t = sayfa_teshis(html)
        sonuc["url"] = url
        sonuc["teshis"] = t
        if t["jsonld_urun"]:
            sonuc["durum"] = "YESIL - JSON-LD"
        elif t["microdata"]:
            sonuc["durum"] = "YESIL - microdata"
        elif t["kart_ici"] >= 5:
            sonuc["durum"] = "SARI - fiyat var, CSS secici gerekir"
        elif t["fiyat_metni"] >= 5:
            # Fiyat var ama urun linkinin ICINDE degil - hangi urune ait
            # oldugu guvenilir sekilde belirlenemez (idefix dersi).
            sonuc["durum"] = "KIRMIZI - fiyat kart disinda, eslesme kurulamaz"
            continue
        else:
            sonuc["durum"] = "KIRMIZI - fiyat yok (JS ile yukleniyor olabilir)"
            continue
        break
    return sonuc


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--anahtar", nargs="*", default=VARSAYILAN_ANAHTARLAR)
    a.add_argument("--aday", nargs="*", default=None, help="ad=url biciminde")
    args = a.parse_args()

    adaylar = ADAYLAR
    if args.aday:
        adaylar = [tuple(x.split("=", 1)) for x in args.aday]

    sonuclar = []
    for ad, taban in adaylar:
        try:
            s = adayi_tara(ad, taban, [k.lower() for k in args.anahtar])
        except Exception as hata:  # tek adayin patlamasi taramayi bitirmesin
            s = {"ad": ad, "taban": taban, "durum": f"HATA: {hata}", "url": "", "teshis": {}}
        sonuclar.append(s)
        t = s["teshis"]
        ozet = (f"ld={t['jsonld_urun']} micro={t['microdata']} "
                f"fiyat={t['fiyat_metni']} kart_ici={t['kart_ici']}" if t else "")
        print(f"{s['ad']:13} {s['durum']:44} {ozet}", flush=True)
        if s["url"]:
            print(f"              {s['url']}", flush=True)

    print("\n--- OZET ---")
    for durum in ["YESIL", "SARI", "KIRMIZI"]:
        grup = [s["ad"] for s in sonuclar if s["durum"].startswith(durum)]
        if grup:
            print(f"{durum}: {', '.join(grup)}")
    return sonuclar


if __name__ == "__main__":
    main()
