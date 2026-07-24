# -*- coding: utf-8 -*-
"""Gecici teshis scripti - DugunBuketi/fotografci ve gelinlik-moda-evleri
sayfalarindaki .bg-card kartlarinin kacinda gercek fiyat oldugunu,
kacinda "uye olun" mesaji oldugunu gosterir. Kullanildiktan sonra
silinecek."""

import requests
from bs4 import BeautifulSoup

import motor

for url in [
    "https://dugunbuketi.com/p/dis-cekim-dugun-fotografcisi/istanbul",
    "https://dugunbuketi.com/p/gelinlik-moda-evleri/istanbul",
]:
    r = requests.get(url, headers=motor.HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")
    kartlar = soup.select(".bg-card")
    print(f"=== {url} ===")
    print(f"toplam kart: {len(kartlar)}")
    for k in kartlar:
        isim_el = k.select_one("a.font-semibold.tracking-tight")
        fiyat_el = k.select_one("strong, .font-bold")
        isim = isim_el.get_text(strip=True) if isim_el else "???"
        fiyat = fiyat_el.get_text(strip=True) if fiyat_el else "YOK"
        print(f"  {isim!r:50s} -> fiyat: {fiyat!r}")
    print()
