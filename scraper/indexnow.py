# -*- coding: utf-8 -*-
"""
maliyetine.com - IndexNow bildirimi (v0.1)

Sitemap'teki URL'leri IndexNow protokoluyle arama motorlarina bildirir.
Motorlar taramayi beklemek yerine "bu sayfalar degisti" bilgisini
dogrudan aliyor.

NEDEN GEO ICIN DEGERLI: **ChatGPT'nin web aramasi Bing altyapisini
kullaniyor.** Yani Bing indeksine hizli girmek, GEO hedefi (AI
motorlarinin alintiladigi kaynak olmak) icin dogrudan bir kazanc.
Yandex de destekliyor. Google IndexNow'u DESTEKLEMIYOR - onun icin
Search Console'a sitemap gonderimi gerekiyor (Yavuz'un tarafinda).

Kimlik dogrulama: {key}.txt dosyasi sitenin kokunde yayinlanir, icerigi
key'in kendisi olur. Key gizli DEGIL (sahiplik kaniti, parola degil),
o yuzden depoda durmasi sorun degil.

Kullanim:
  python indexnow.py                # sitemap'teki tum URL'leri bildir
  python indexnow.py --kuru-calisma # istek atmadan ne gonderilecegini goster
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent
SITE_KOK = BASE_DIR.parent
KEY_DOSYASI = BASE_DIR / ".indexnow-key"
SITE_HOST = "maliyetine.com.tr"
UC_NOKTA = "https://api.indexnow.org/indexnow"


def key_oku() -> str:
    if not KEY_DOSYASI.exists():
        raise SystemExit(
            f"IndexNow key bulunamadi: {KEY_DOSYASI}\n"
            "Yeni key uretmek icin: python -c \"import secrets;print(secrets.token_hex(16))\"\n"
            "Sonra key'i bu dosyaya yaz ve site kokune {key}.txt olarak koy."
        )
    return KEY_DOSYASI.read_text(encoding="utf-8").strip()


def sitemap_urlleri(sitemap: Path | None = None) -> list[str]:
    sitemap = sitemap or SITE_KOK / "sitemap.xml"
    if not sitemap.exists():
        raise SystemExit(f"sitemap.xml bulunamadi: {sitemap}")
    return re.findall(r"<loc>(.*?)</loc>", sitemap.read_text(encoding="utf-8"))


def key_dosyasi_yayinda_mi(key: str) -> bool:
    """Key dosyasi sitede erisilebilir mi? Erisilemezse IndexNow reddeder."""
    url = f"https://{SITE_HOST}/{key}.txt"
    try:
        with urllib.request.urlopen(url, timeout=15) as yanit:
            return yanit.status == 200 and yanit.read().decode().strip() == key
    except (urllib.error.URLError, urllib.error.HTTPError):
        return False


def bildir(urller: list[str], key: str) -> tuple[int, str]:
    govde = json.dumps({
        "host": SITE_HOST,
        "key": key,
        "keyLocation": f"https://{SITE_HOST}/{key}.txt",
        "urlList": urller,
    }).encode("utf-8")
    istek = urllib.request.Request(
        UC_NOKTA,
        data=govde,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(istek, timeout=30) as yanit:
            return yanit.status, yanit.read().decode(errors="replace")[:300]
    except urllib.error.HTTPError as hata:
        return hata.code, hata.read().decode(errors="replace")[:300]
    except urllib.error.URLError as hata:
        return 0, str(hata)


def main():
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument("--kuru-calisma", action="store_true")
    ayristirici.add_argument("--sitemap", type=Path, default=None)
    args = ayristirici.parse_args()

    key = key_oku()
    urller = sitemap_urlleri(args.sitemap)
    print(f"IndexNow: {len(urller)} URL, key {key[:8]}…")

    if args.kuru_calisma:
        for u in urller:
            print(f"  {u}")
        print("(kuru calisma - istek atilmadi)")
        return

    if not key_dosyasi_yayinda_mi(key):
        # Sessizce devam etmek yanlis olur: motor key'i dogrulayamazsa
        # gonderim reddedilir ve bunu fark etmeyiz.
        print(
            f"UYARI: key dosyasi yayinda degil ya da icerigi yanlis:\n"
            f"  https://{SITE_HOST}/{key}.txt\n"
            f"  Bu dosya deploy edilmeden bildirim REDDEDILIR. Yine de deneniyor…"
        )

    durum, yanit = bildir(urller, key)
    # IndexNow 200 = kabul, 202 = kabul (dogrulama bekliyor).
    if durum in (200, 202):
        print(f"OK ({durum}): {len(urller)} URL bildirildi.")
    else:
        print(f"BASARISIZ ({durum}): {yanit}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
