# -*- coding: utf-8 -*-
"""
robots.txt kontrol araci (v0.2)

Kullanim:
  python robots_kontrol.py https://ORNEK-SITE.com/kategori/urun [url2 ...]

Bagimliliklar: requests, protego (bkz. requirements.txt).

NEDEN stdlib urllib.robotparser DEGIL: gercek sitelere (Akakce) karsi
test edilirken uc ayri hata bulundu - (1) robots.txt'i varsayilan
urllib User-Agent'iyla ("Python-urllib/x.y") cekiyor, bircok sitenin bot
korumasi bunu 403'le reddediyor ve RobotFileParser bunu "hicbir sey
kazinamaz" diye yanlis yorumluyor; (2) User-agent gruplarinda bos satir
varsa o grubu sessizce dusuruyor; (3) Disallow/Allow desenlerinde "*"
joker karakterini hic desteklemiyor. `protego` (Scrapy'nin bagimliligi)
Google'in robots.txt RFC 9309'unu dogru uyguluyor, bu ucunu de cozuyor.
"""

import sys

import requests
from protego import Protego

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9",
}
USER_AGENT = "maliyetine-bot"


def kontrol_et(url: str) -> None:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    try:
        yanit = requests.get(robots_url, headers=HEADERS, timeout=10)
    except requests.RequestException as e:
        print(f"[HATA] robots.txt okunamadi ({robots_url}): {e}")
        return

    if yanit.status_code in (401, 403):
        print(f"robots.txt : {robots_url}  (HTTP {yanit.status_code} - erisim yasagi)")
        print(f"URL        : {url}")
        print("Sonuc      : RET - kazima!  (robots.txt'e erisim yasakli, ihtiyatla RET)")
        return
    if 400 <= yanit.status_code < 500:
        print(f"robots.txt : {robots_url}  (HTTP {yanit.status_code} - robots.txt yok)")
        print(f"URL        : {url}")
        print("Sonuc      : ONAY - kazinabilir  (robots.txt yok, konvansiyon geregi izinli)")
        return
    if yanit.status_code >= 500:
        print(f"[HATA] robots.txt sunucu hatasi ({robots_url}): HTTP {yanit.status_code}")
        return

    rp = Protego.parse(yanit.text)
    izinli = rp.can_fetch(url, USER_AGENT)
    gecikme = rp.crawl_delay(USER_AGENT)

    print(f"robots.txt : {robots_url}")
    print(f"URL        : {url}")
    print(f"Sonuc      : {'ONAY - kazinabilir' if izinli else 'RET - kazima!'}")
    if gecikme:
        print(f"crawl-delay: {gecikme} sn (buna uy)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanim: python robots_kontrol.py <url> [<url2> ...]")
        sys.exit(1)
    for u in sys.argv[1:]:
        kontrol_et(u)
        print("-" * 40)
