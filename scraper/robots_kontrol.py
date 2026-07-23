# -*- coding: utf-8 -*-
"""
robots.txt kontrol araci (v0.1)

ONEMLI: Bu ortamin (Claude Code sandbox) disariya network erisimi proxy
politikasiyla kisitli - hedef siteler (dugun.com, trendyol.com vb.) buradan
CONNECT ile 403 donuyor. Bu script BURADA CALISMAZ; Yavuz'un kendi
makinesinde ya da erisimi acik baska bir ortamda calistirmasi gerekir.

Kullanim:
  python robots_kontrol.py https://ORNEK-SITE.com/kategori/urun [url2 ...]

Standart kutuphane disinda bagimlilik yok (urllib.robotparser).
"""

import sys
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

USER_AGENT = "maliyetine-bot"


def kontrol_et(url: str) -> None:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception as e:
        print(f"[HATA] robots.txt okunamadi ({robots_url}): {e}")
        return

    izinli = rp.can_fetch(USER_AGENT, url)
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
