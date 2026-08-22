# -*- coding: utf-8 -*-
"""Yayindaki veri dosyalari icin icerik tabanli surum manifesti."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


BASE_DIR = Path(__file__).parent
SITE_KOK = BASE_DIR.parent
VARSAYILAN_VERI_KOK = SITE_KOK / "veri"
SEMA_SURUMU = 1


def dosya_ozeti(dosya: Path, site_kok: Path = SITE_KOK) -> dict:
    return {
        "yol": "/" + dosya.relative_to(site_kok).as_posix(),
        "sha256": hashlib.sha256(dosya.read_bytes()).hexdigest(),
        "bayt": dosya.stat().st_size,
    }


def manifest_uret(
    veri_kok: Path = VARSAYILAN_VERI_KOK,
    vertikaller=None,
    site_kok: Path = SITE_KOK,
) -> dict:
    if vertikaller is None:
        import sayfa_uret
        vertikaller = sayfa_uret.VERTIKALLER

    dikeyler = {}
    surum_parcalari = []
    tum_tarihler = []
    toplam_seri = 0
    for vertikal in vertikaller:
        guncel = veri_kok / f"{vertikal}.json"
        if not guncel.exists():
            raise FileNotFoundError(f"Manifest icin veri eksik: {guncel}")
        veri = json.loads(guncel.read_text(encoding="utf-8"))
        kalemler = veri.get("kalemler") or {}
        tarihler = sorted({
            k.get("guncelleme_tarihi") for k in kalemler.values()
            if k.get("guncelleme_tarihi")
        })
        dosyalar = {"guncel_json": dosya_ozeti(guncel, site_kok)}
        adaylar = {
            "gecmis_json": veri_kok / "gecmis" / f"{vertikal}.json",
            "guncel_csv": veri_kok / "csv" / f"{vertikal}.csv",
        }
        for ad, dosya in adaylar.items():
            if dosya.exists():
                dosyalar[ad] = dosya_ozeti(dosya, site_kok)
        dikeyler[vertikal] = {
            "fiyat_serisi": len(kalemler),
            "olcum_baslangici": tarihler[0] if tarihler else None,
            "olcum_sonu": tarihler[-1] if tarihler else None,
            "dosyalar": dosyalar,
        }
        toplam_seri += len(kalemler)
        tum_tarihler.extend(tarihler)
        surum_parcalari.append(
            f"{vertikal}:{dosyalar['guncel_json']['sha256']}"
        )

    veri_tarihi = max(tum_tarihler) if tum_tarihler else "tarihsiz"
    parmak_izi = hashlib.sha256("\n".join(surum_parcalari).encode("utf-8")).hexdigest()
    return {
        "sema_surumu": SEMA_SURUMU,
        "dataset_surumu": f"{veri_tarihi}-{parmak_izi[:16]}",
        "olcum_tarihi_sonu": None if veri_tarihi == "tarihsiz" else veri_tarihi,
        "fiyat_serisi": toplam_seri,
        "dikeyler": dikeyler,
    }


def manifest_yaz(
    veri_kok: Path = VARSAYILAN_VERI_KOK,
    vertikaller=None,
    site_kok: Path = SITE_KOK,
) -> tuple[dict, Path]:
    manifest = manifest_uret(veri_kok, vertikaller, site_kok)
    hedef = veri_kok / "manifest.json"
    hedef.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest, hedef


def manifest_hatalari(manifest: dict, site_kok: Path = SITE_KOK) -> list[str]:
    hatalar = []
    for vertikal, ozet in (manifest.get("dikeyler") or {}).items():
        for tur, dosya in (ozet.get("dosyalar") or {}).items():
            yol = dosya.get("yol", "").lstrip("/")
            hedef = site_kok / yol
            if not hedef.exists():
                hatalar.append(f"{vertikal}/{tur}: dosya yok ({yol})")
                continue
            gercek = hashlib.sha256(hedef.read_bytes()).hexdigest()
            if gercek != dosya.get("sha256"):
                hatalar.append(f"{vertikal}/{tur}: SHA-256 manifestten farkli")
    return hatalar
