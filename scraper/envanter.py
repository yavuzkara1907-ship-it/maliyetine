# -*- coding: utf-8 -*-
"""Aktif olcum envanteri ve JSON tabanli site sayaclari.

Ham snapshot arsivi bilincli olarak eski/devre disi kalemleri saklar. Yayina
giren envanter ise kaynaklar.yaml'daki aktif kalemlerden olusur. Sayaclar
bundan sonra yalnizca yayindaki birlesik JSON dosyalarindan hesaplanir.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path

import yaml


BASE_DIR = Path(__file__).parent
VARSAYILAN_KAYNAKLAR = BASE_DIR / "kaynaklar.yaml"


def aktif_kalem_idleri(
    vertikal: str, kaynaklar_dosyasi: Path = VARSAYILAN_KAYNAKLAR
) -> set[str]:
    """Bir vertikalde en az bir aktif olcum tanimi olan kalemler."""
    # Bu dosya yayin envanterinin kontratidir. Okuma/parse hatasini bos
    # envanter gibi ele almak, build'in mevcut veriyi sessizce silmesine
    # yol acar; hata burada gorunur bicimde durmali.
    veri = yaml.safe_load(kaynaklar_dosyasi.read_text(encoding="utf-8")) or {}
    kalemler = {
        kayit["kalem"]
        for kayit in veri.get("kaynaklar", [])
        if kayit.get("vertikal") == vertikal
        and kayit.get("aktif", True)
        and kayit.get("kalem")
    }
    if not kalemler:
        raise ValueError(f"{vertikal}: aktif fiyat serisi tanimi bulunamadi")
    return kalemler


def calisan_siteler(kalem: dict) -> set[str]:
    return {
        kaynak["site"]
        for kaynak in kalem.get("kaynaklar") or []
        if kaynak.get("site") and (kaynak.get("toplam_urun") or 0) > 0
    }


def envanter_ozeti(
    veri_kok: Path, vertikaller: Iterable[str] | Mapping[str, dict]
) -> dict:
    """Yayindaki JSON'lardan tek, ortak envanter ozeti uretir."""
    toplam_seri = 0
    toplam_cok_kaynakli = 0
    toplam_tek_kaynak = 0
    liste_fiyati_tek_kaynak = 0
    tum_siteler: set[str] = set()
    dikeyler = {}
    for vertikal in vertikaller:
        dosya = veri_kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        try:
            veri = json.loads(dosya.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        kalemler = veri.get("kalemler") or {}
        if not isinstance(kalemler, dict) or not kalemler:
            continue
        conf = vertikaller.get(vertikal, {}) if isinstance(vertikaller, Mapping) else {}
        liste_fiyati = bool(conf.get("liste_fiyati"))
        siteler = set().union(*(calisan_siteler(k) for k in kalemler.values()))
        tek_kaynak = sum(len(calisan_siteler(k)) == 1 for k in kalemler.values())
        cok_kaynakli = sum(len(calisan_siteler(k)) >= 2 for k in kalemler.values())
        dikeyler[vertikal] = {
            "fiyat_serisi": len(kalemler),
            "kaynak": len(siteler),
            "cok_kaynakli": cok_kaynakli,
            "tek_kaynak": tek_kaynak,
            "liste_fiyati": liste_fiyati,
            "tarih": veri.get("guncelleme_tarihi"),
        }
        toplam_seri += len(kalemler)
        toplam_cok_kaynakli += cok_kaynakli
        toplam_tek_kaynak += tek_kaynak
        if liste_fiyati:
            liste_fiyati_tek_kaynak += tek_kaynak
        tum_siteler.update(siteler)
    tarihler = [d.get("tarih") for d in dikeyler.values() if d.get("tarih")]
    return {
        "guncelleme_tarihi": max(tarihler) if tarihler else None,
        "fiyat_serisi": toplam_seri,
        "kaynak": len(tum_siteler),
        "cok_kaynakli": toplam_cok_kaynakli,
        "tek_kaynak": toplam_tek_kaynak,
        "liste_fiyati_tek_kaynak": liste_fiyati_tek_kaynak,
        "perakende_hizmet_derinlik_acigi": toplam_tek_kaynak - liste_fiyati_tek_kaynak,
        "vertikaller": dikeyler,
    }
