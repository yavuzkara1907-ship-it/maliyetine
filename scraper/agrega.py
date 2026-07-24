# -*- coding: utf-8 -*-
"""
maliyetine.com - Veri Birlestirme (v0.1)

motor.py'nin urettigi site-basina JSON dosyalarini (scraper/veri/{vertikal}/
{kalem}_{site}_{tarih}.json) okuyup statik sitenin tek seferde fetch
edecegi bir "endeks" JSON'una birlestirir (/veri/{vertikal}.json).

COK KAYNAK KURALI geregi kalemler birbirine BENZETILMEZ/tek dagilima
GOMULMEZ (bkz. CLAUDE.md) - bunun yerine, ayni kalemdeki >=2 saglikli
kaynagin HER SEGMENTTEKI kendi medyanlarinin medyani alinir (medyan-of-
medyan). Bu, tek bir sapkin kaynagin sonucu domine etmesini engeller ve
kaynaklarin ham fiyat noktalarini birbirine karistirmadan tek bir
"gosterilebilir" rakam uretir. Tum katkida bulunan kaynaklar seffaflik
icin ayrica listelenir.

Kullanim:
  python agrega.py                          # scraper/veri/dugun -> ../veri/dugun.json
  python agrega.py --vertikal dugun
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

BASE_DIR = Path(__file__).parent
VARSAYILAN_VERI_KOK = BASE_DIR / "veri"
VARSAYILAN_SITE_VERI_KOK = BASE_DIR.parent / "veri"

SEGMENT_ADLARI = ("dusuk", "orta", "luks")


def kaynak_dosyalarini_oku(vertikal_klasoru: Path) -> list[dict]:
    """Bir vertikal klasorundeki (karantina haric) tum site-ozet JSON'larini
    okur. Capraz-dogrulama raporlari (dosya adinda 'capraz-dogrulama' gecen)
    ayri bir formatta oldugu icin burada atlanir, ayri fonksiyonla okunur."""
    kayitlar = []
    if not vertikal_klasoru.exists():
        return kayitlar
    for dosya in vertikal_klasoru.glob("*.json"):
        if "capraz-dogrulama" in dosya.name:
            continue
        try:
            veri = json.loads(dosya.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        kayitlar.append(veri)
    return kayitlar


def capraz_dogrulama_raporlarini_oku(vertikal_klasoru: Path) -> dict[str, dict]:
    """kalem -> en guncel capraz dogrulama raporu (varsa).

    NOT: motor.py'nin capraz_dogrula() fonksiyonu HER coklu-kaynakli kalem
    icin bir rapor dosyasi yazar (esigi asmasa bile, bkz. motor.py) - "uyari"
    alani gercekten esigi asip asmadigini gosterir. Bu yuzden sadece
    uyari=true olan raporlar aliniyor; digerleri (fark makul) sessizce
    atlaniyor. Ham rapor semasi motor.py'de "site_medyanlari" ve "fark_orani"
    (oran, 0-1+ araliginda - yuzde DEGIL) kullanir - agregali ciktidaki
    "medyanlar"/"fark_yuzdesi" isimleri burada donusturuluyor."""
    raporlar: dict[str, dict] = {}
    if not vertikal_klasoru.exists():
        return raporlar
    for dosya in vertikal_klasoru.glob("*_capraz-dogrulama_*.json"):
        try:
            veri = json.loads(dosya.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not veri.get("uyari"):
            continue
        kalem = veri.get("kalem")
        if not kalem:
            continue
        mevcut = raporlar.get(kalem)
        if mevcut is None or veri.get("tarih", "") >= mevcut.get("tarih", ""):
            raporlar[kalem] = veri
    return raporlar


def en_guncel_kayitlari_sec(kayitlar: list[dict]) -> list[dict]:
    """Ayni (kalem, site) icin birden fazla tarihli dosya varsa (aylar
    biriktikce olacak), sadece EN GUNCEL olani tutar - eskiler tarih
    gecmisi/grafik icin diskte kalir ama endekse dahil edilmez."""
    en_guncel: dict[tuple[str, str], dict] = {}
    for kayit in kayitlar:
        if not kayit.get("saglikli", False):
            continue
        anahtar = (kayit.get("kalem"), kayit.get("site"))
        mevcut = en_guncel.get(anahtar)
        if mevcut is None or kayit.get("tarih", "") >= mevcut.get("tarih", ""):
            en_guncel[anahtar] = kayit
    return list(en_guncel.values())


def kalem_birlestir(kaynak_kayitlari: list[dict]) -> dict:
    """Ayni kalemdeki N saglikli kaynagin kayitlarini tek bir ozet sozluge
    birlestirir. kaynak_kayitlari bos OLAMAZ (cagiran taraf garanti eder)."""
    segmentler: dict[str, dict] = {}
    for segment_adi in SEGMENT_ADLARI:
        medyanlar = []
        minler = []
        maksler = []
        urun_toplam = 0
        for kayit in kaynak_kayitlari:
            seg = kayit.get("segmentler", {}).get(segment_adi)
            if not seg:
                continue
            medyanlar.append(seg["medyan"])
            minler.append(seg["min"])
            maksler.append(seg["max"])
            urun_toplam += seg["urun_sayisi"]
        if medyanlar:
            segmentler[segment_adi] = {
                "min": min(minler),
                "medyan": round(statistics.median(medyanlar)),
                "max": max(maksler),
                "urun_sayisi": urun_toplam,
                "kaynak_sayisi": len(medyanlar),
            }

    genel_medyanlar = [k["genel_medyan"] for k in kaynak_kayitlari if k.get("genel_medyan") is not None]
    toplam_urun = sum(k.get("toplam_urun", 0) for k in kaynak_kayitlari)
    en_guncel_tarih = max(k["tarih"] for k in kaynak_kayitlari)

    return {
        "segmentler": segmentler,
        "genel_medyan": round(statistics.median(genel_medyanlar)) if genel_medyanlar else None,
        "toplam_urun": toplam_urun,
        "guncelleme_tarihi": en_guncel_tarih,
        "kaynak_sayisi": len(kaynak_kayitlari),
        "kaynaklar": [
            {
                "site": k["site"],
                "kaynak_adlari": k["kaynak_adlari"],
                "tarih": k["tarih"],
                "toplam_urun": k.get("toplam_urun", 0),
                "genel_medyan": k.get("genel_medyan"),
            }
            for k in sorted(kaynak_kayitlari, key=lambda k: k["site"])
        ],
    }


def vertikal_agregali(vertikal: str, veri_kok: Path = VARSAYILAN_VERI_KOK) -> dict:
    vertikal_klasoru = veri_kok / vertikal
    tum_kayitlar = kaynak_dosyalarini_oku(vertikal_klasoru)
    guncel_kayitlar = en_guncel_kayitlari_sec(tum_kayitlar)
    capraz_raporlar = capraz_dogrulama_raporlarini_oku(vertikal_klasoru)

    kalemler_gruplu: dict[str, list[dict]] = {}
    for kayit in guncel_kayitlar:
        kalemler_gruplu.setdefault(kayit["kalem"], []).append(kayit)

    kalemler = {}
    for kalem, kayitlar in kalemler_gruplu.items():
        ozet = kalem_birlestir(kayitlar)
        if kalem in capraz_raporlar:
            ham_rapor = capraz_raporlar[kalem]
            ozet["capraz_dogrulama_uyarisi"] = {
                "fark_yuzdesi": round(ham_rapor["fark_orani"] * 100, 1),
                "medyanlar": ham_rapor["site_medyanlari"],
            }
        else:
            ozet["capraz_dogrulama_uyarisi"] = None
        kalemler[kalem] = ozet

    guncelleme_tarihi = max((k["guncelleme_tarihi"] for k in kalemler.values()), default=None)

    return {
        "vertikal": vertikal,
        "guncelleme_tarihi": guncelleme_tarihi,
        "kalemler": kalemler,
    }


def yaz(vertikal: str, veri_kok: Path = VARSAYILAN_VERI_KOK, site_veri_kok: Path = VARSAYILAN_SITE_VERI_KOK) -> Path:
    agregali = vertikal_agregali(vertikal, veri_kok)
    site_veri_kok.mkdir(parents=True, exist_ok=True)
    hedef = site_veri_kok / f"{vertikal}.json"
    hedef.write_text(json.dumps(agregali, ensure_ascii=False, indent=2), encoding="utf-8")
    return hedef


def main():
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument("--vertikal", default="dugun")
    ayristirici.add_argument("--veri-kok", type=Path, default=VARSAYILAN_VERI_KOK)
    ayristirici.add_argument("--site-veri-kok", type=Path, default=VARSAYILAN_SITE_VERI_KOK)
    args = ayristirici.parse_args()

    hedef = yaz(args.vertikal, args.veri_kok, args.site_veri_kok)
    print(f"[{args.vertikal}] agregali veri yazildi: {hedef}")


if __name__ == "__main__":
    main()
