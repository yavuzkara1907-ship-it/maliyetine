# -*- coding: utf-8 -*-
"""
Maliyeti Ne? - Paylasim gorseli (Open Graph)

NEDEN URETILIYOR: gorsel elle yapilmisti ve BAYATLADI - uzerinde
"Dugun · Ev kurma · 0 km arac" yaziyordu, okul vertikali eklendikten
sonra da oyle kaldi; "aylik guncellenen" diyordu, oysa olcum ayda iki
kez. Bu gorsel X/WhatsApp/LinkedIn'de baglanti paylasildiginda gorulen
ILK sey. Bayat bilgi, sitenin en gorunur yerinde duruyordu.

Artik veriden uretiliyor: vertikal adlari ve kalem sayisi gercek
veriden geliyor, her olcumde tazeleniyor.

Cikti: assets/og-gorsel.png (1200x630 - X, Facebook, LinkedIn standardi)
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import sayfa_uret as su

SITE_KOK = su.SITE_KOK
HEDEF = SITE_KOK / "assets" / "og-gorsel.png"

GENISLIK, YUKSEKLIK = 1200, 630


def _ozet(veri_kok: Path | None = None) -> dict:
    kok = veri_kok or SITE_KOK / "veri"
    adlar, toplam_kalem, siteler = [], 0, set()
    for vertikal, conf in su.VERTIKALLER.items():
        dosya = kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        try:
            veri = json.loads(dosya.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        kalemler = veri.get("kalemler") or {}
        if not kalemler:
            continue
        adlar.append(conf["ad"])
        toplam_kalem += len(kalemler)
        for k in kalemler.values():
            for kaynak in k.get("kaynaklar") or []:
                if (kaynak.get("toplam_urun") or 0) > 0 and kaynak.get("site"):
                    siteler.add(kaynak["site"])
    return {"adlar": adlar, "kalem": toplam_kalem, "kaynak": len(siteler)}


def uret(hedef: Path | None = None, veri_kok: Path | None = None) -> Path | None:
    """PIL yoksa None doner - gorsel uretimi zorunlu bir adim degil,
    eksikligi yayini durdurmamali (mevcut gorsel yerinde kalir)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL kurulu degil - og gorseli guncellenmedi.")
        return None

    o = _ozet(veri_kok)
    if not o["adlar"]:
        return None

    h = hedef or HEDEF
    img = Image.new("RGB", (GENISLIK, YUKSEKLIK), "#ffffff")
    d = ImageDraw.Draw(img)

    def yazi_tipi(boyut, kalin=True):
        adaylar = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if kalin
            else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if kalin
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for a in adaylar:
            if Path(a).exists():
                try:
                    return ImageFont.truetype(a, boyut)
                except OSError:
                    continue
        return ImageFont.load_default()

    # Ust seride marka rengi
    d.rectangle([0, 0, GENISLIK, 10], fill="#0f5c8c")

    d.text((70, 80), "Maliyeti Ne?", font=yazi_tipi(44), fill="#0f5c8c")
    d.text((70, 175), "2026'da bir şey", font=yazi_tipi(86), fill="#16161d")
    d.text((70, 275), "kaça mal olur?", font=yazi_tipi(86), fill="#16161d")

    d.text((70, 415), " · ".join(o["adlar"]), font=yazi_tipi(36, False), fill="#5b5b6b")

    # Rakamlar: soyut "guvenilir veri" iddiasi yerine olculebilir kanit
    d.text(
        (70, 480),
        f"{o['kalem']} kalem · {o['kaynak']} bağımsız kaynak · ayda iki kez ölçülüyor",
        font=yazi_tipi(30, False), fill="#16161d",
    )
    d.text((70, 540), "maliyetine.com.tr", font=yazi_tipi(28, False), fill="#8a8a99")

    h.parent.mkdir(parents=True, exist_ok=True)
    img.save(h, "PNG", optimize=True)
    return h


def main():
    yol = uret()
    if not yol:
        return 1
    o = _ozet()
    print(f"OG gorseli uretildi: {yol}")
    print(f"  {' · '.join(o['adlar'])} | {o['kalem']} kalem | {o['kaynak']} kaynak")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
