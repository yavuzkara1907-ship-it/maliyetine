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

# Boyut sayfa_uret'ten geliyor - HTML'deki og:image:width/height ile
# ayni olmak ZORUNDA. Iki yerde ayri tutulsa biri degisip oteki kalir ve
# Facebook'a YANLIS boyut beyan edilir; bir test bunu dogruluyor.
GENISLIK, YUKSEKLIK = su.OG_GENISLIK, su.OG_YUKSEKLIK


# Renkler style.css ile AYNI olmali - iki yerde ayri tutulup biri
# degisirse paylasim karti siteyle alakasiz gorunur.
KAGIT = "#fbfaf7"
MUREKKEP = "#14140f"
SOLUK = "#6a6a5e"
VURGU = "#9c2b1a"
CIZGI = "#ddd9cd"

KALEM_KOK = SITE_KOK / "assets" / "og"


def _yazi_tipi_uret(ImageFont, boyut, kalin=True):
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


def _sar(d, metin, font, azami_genislik):
    """Basligi kutuya sigacak sekilde satirlara boler."""
    kelimeler = metin.split()
    satirlar, gecerli = [], ""
    for k in kelimeler:
        deneme = (gecerli + " " + k).strip()
        if d.textlength(deneme, font=font) <= azami_genislik or not gecerli:
            gecerli = deneme
        else:
            satirlar.append(gecerli)
            gecerli = k
    if gecerli:
        satirlar.append(gecerli)
    return satirlar[:2]


def kalem_karti(baslik: str, tutar: int, alt_satir: str, hedef: Path):
    """Tek bir olcum icin paylasim karti.

    NEDEN GEREKLI (2026-08-02 denetimi): 175 sayfanin TAMAMI ayni
    jenerik gorseli paylasiyordu. /ev-kurma/buzdolabi-fiyatlari/
    WhatsApp'ta paylasildiginda kartta "2026 Maliyet Endeksi" yaziyordu,
    "Buzdolabi 29.597 TL" YAZMIYORDU. Ilk trafik olcumunde referans
    kaynagi %95 m.facebook.com cikmisti - yani paylasim karti bu sitede
    dogrudan tiklanma oraninin kendisi.

    Kartin uzerindeki her sey VERIDEN gelir; sabit metin yalnizca
    marka adi ve alan adi.
    """
    try:
        from PIL import Image, ImageDraw
        from PIL import ImageFont
    except ImportError:
        return None

    img = Image.new("RGB", (GENISLIK, YUKSEKLIK), KAGIT)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, GENISLIK, 12], fill=MUREKKEP)

    d.text((70, 74), "Maliyeti Ne?", font=_yazi_tipi_uret(ImageFont, 38), fill=VURGU)

    bf = _yazi_tipi_uret(ImageFont, 58, False)
    satirlar = _sar(d, baslik, bf, GENISLIK - 140)
    y = 152
    for sat in satirlar:
        d.text((70, y), sat, font=bf, fill=MUREKKEP)
        y += 68

    # Rakam kartin ANA ogesi: en buyuk punto, renk degil buyukluk.
    y = max(y + 24, 300)
    d.text((70, y), "{:,} TL".format(tutar).replace(",", "."),
           font=_yazi_tipi_uret(ImageFont, 128), fill=MUREKKEP)

    d.line([(70, 512), (GENISLIK - 70, 512)], fill=CIZGI, width=2)
    d.text((70, 532), alt_satir, font=_yazi_tipi_uret(ImageFont, 27, False), fill=SOLUK)
    d.text((GENISLIK - 70 - d.textlength("maliyetine.com.tr",
           font=_yazi_tipi_uret(ImageFont, 27, False)), 532),
           "maliyetine.com.tr", font=_yazi_tipi_uret(ImageFont, 27, False), fill=SOLUK)

    hedef.parent.mkdir(parents=True, exist_ok=True)
    img.save(hedef, "PNG", optimize=True)
    return hedef


def kalem_kartlarini_uret(veri_kok: Path | None = None) -> int:
    """Her kalem sayfasi ve her endeks icin ayri kart uretir."""
    kok = veri_kok or SITE_KOK / "veri"
    # kalem_sayfalari calisma aninda genisletiliyor (hangi kalemin
    # sayfayi hak ettigi O AYKI olcume bagli). Bu cagrilmadan yalnizca
    # statik tanimdaki 28 kalem gorunuyordu, oysa 97 sayfa var.
    su.kalem_sayfalarini_genislet(veri_kok)
    sayi = 0
    for vertikal, conf in su.VERTIKALLER.items():
        dosya = kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        try:
            veri = json.loads(dosya.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        kalemler = veri.get("kalemler") or {}
        tarih = veri.get("guncelleme_tarihi") or ""

        # Endeks karti: vertikalin kendi toplami
        toplam, _ = su.ornek_toplam_hesapla(
            conf, kalemler, conf.get("olcek_varsayilan", 1), "orta")
        if toplam:
            siteler = {x["site"] for k in kalemler.values()
                       for x in (k.get("kaynaklar") or []) if x.get("toplam_urun")}
            if kalem_karti(conf["ad"] + " maliyeti",  int(toplam),
                           f"{conf.get('kart_alt', 'orta segment')} · "
                           f"{len(siteler)} bağımsız kaynak · {tarih}",
                           KALEM_KOK / f"{vertikal}.png"):
                sayi += 1

        # Kalem kartlari: yalnizca SAYFASI OLAN kalemler icin.
        # Kalem ADI tanimdan gelir (kalem_sayfalari yalnizca id+slug tasir).
        adlar = {t["id"]: t["ad"] for t in conf["kalemler"]}
        for sayfa in conf.get("kalem_sayfalari") or []:
            k = kalemler.get(sayfa["id"]) or {}
            orta = ((k.get("segmentler") or {}).get("orta") or {}).get("medyan")
            if not orta:
                continue
            n = len({x["site"] for x in (k.get("kaynaklar") or [])
                     if x.get("toplam_urun")})
            urun = k.get("toplam_urun") or 0
            alt = f"orta segment · {n} kaynak · {urun} üründen · {k.get('tarih') or tarih}"
            ad = adlar.get(sayfa["id"])
            if not ad:
                continue
            if kalem_karti(ad + " fiyatları", int(orta), alt,
                           KALEM_KOK / f"{vertikal}-{sayfa['slug']}.png"):
                sayi += 1
    return sayi


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
    img = Image.new("RGB", (GENISLIK, YUKSEKLIK), KAGIT)
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
    d.rectangle([0, 0, GENISLIK, 12], fill=MUREKKEP)

    d.text((70, 78), "Maliyeti Ne?", font=yazi_tipi(44), fill=VURGU)
    d.text((70, 168), "2026", font=yazi_tipi(92), fill=MUREKKEP)
    d.text((70, 272), "Maliyet Endeksi", font=yazi_tipi(92), fill=MUREKKEP)

    d.text((70, 415), " · ".join(o["adlar"]), font=yazi_tipi(36, False), fill=SOLUK)

    # Rakamlar: soyut "guvenilir veri" iddiasi yerine olculebilir kanit
    d.text(
        (70, 480),
        f"{o['kalem']} kalem · {o['kaynak']} bağımsız kaynak · ayda iki kez ölçülüyor",
        font=yazi_tipi(30, False), fill=MUREKKEP,
    )
    d.text((70, 540), "maliyetine.com.tr", font=yazi_tipi(28, False), fill=SOLUK)

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
