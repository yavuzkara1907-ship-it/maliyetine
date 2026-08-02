# -*- coding: utf-8 -*-
"""
Duman testi icin HER SITEDEN BIR kaynak secer.

NEDEN VAR (2026-08-03)
----------------------
Duman testi `motor.py --vertikal arac` calistiriyordu. arac vertikali
TEK kaynakli (donanimhaber). Yani test "GitHub runner hedef sitelere
erisebiliyor mu" sorusunu bir tek site icin cevapliyordu.

2 Agustos'ta 20 yeni kaynak eklendi (nezih, dr, ebebek, joker,
mediamarkt, dogtas). Hicbiri GitHub IP'sinden denenmedi. Veri merkezi
IP'lerine ev baglantisindan farkli davranan siteler var - Akakce ve
Beymen'de tam bunu yasadik. Duman testinin VARLIK SEBEBI bu risk ve
en yeni, en az denenmis kaynaklara kor bakiyordu.

LISTE ELLE TUTULMUYOR: kaynaklar.yaml'dan uretiliyor. Elle yazilan
liste bu projede uc kez bayatladi (gecmis.py, rehber.py, workflow
vertikal dongusu) - yeni bir site eklendiginde duman testi onu
kendiliginden kapsar.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def duman_altkumesi(kaynaklar: list[dict]) -> list[dict]:
    """Her `site` degerinden EN AZ URUN VERECEK olani degil, ILKINI alir.

    Amac kapsam degil erisim testi: her siteye bir istek yeter.
    Pasif kaynaklar disarida (onlar zaten uretimde de calismiyor).
    """
    gorulen, secilen = set(), []
    for k in kaynaklar:
        if not k.get("aktif", True):
            continue
        site = k.get("site")
        if not site or site in gorulen:
            continue
        gorulen.add(site)
        secilen.append(k)
    return secilen


def yaz(kaynak_dosya: Path, hedef: Path) -> int:
    veri = yaml.safe_load(kaynak_dosya.read_text(encoding="utf-8"))
    altkume = duman_altkumesi(veri.get("kaynaklar") or [])
    hedef.write_text(
        yaml.dump({"kaynaklar": altkume}, allow_unicode=True, sort_keys=False),
        encoding="utf-8")
    return len(altkume)


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--kaynaklar", default="kaynaklar.yaml")
    a.add_argument("--cikti", default="/tmp/duman-kaynaklar.yaml")
    args = a.parse_args()
    n = yaz(Path(args.kaynaklar), Path(args.cikti))
    print(f"Duman testi icin {n} site secildi -> {args.cikti}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
