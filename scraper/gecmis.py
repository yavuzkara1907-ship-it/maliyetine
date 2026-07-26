# -*- coding: utf-8 -*-
"""
Maliyeti Ne? - Fiyat Gecmisi Derleyici (v0.1)

Aylik anlik goruntuleri (scraper/veri/{vertikal}/{kalem}_{site}_{tarih}.json)
tarayip her kalem icin ZAMAN SERISI uretir: /veri/gecmis/{vertikal}.json

NEDEN ONEMLI: Bu projenin kopyalanamaz tek varligi zaman serisi. Bugun
biri kaynaklarimizi gorse ayni endeksi iki haftada kurar - ama gecmise
donup 2026 Temmuz'un fiyatini toplayamaz. "Dugun maliyeti 12 ayda %X
artti" cumlesini soyleyebilen tek kaynak olmak, hem basin hem dogal
baglanti getirir.

Bu yuzden aylik veri birikimi ASLA kesilmemeli; bir ay atlanirsa seride
kalici delik olusur.

Cikti semasi:
{
  "vertikal": "dugun",
  "uretim_tarihi": "2026-08-01",
  "olcumler": ["2026-07-25", "2026-08-01"],      # kronolojik
  "kalemler": {
    "gelinlik": {
      "seri": [{"tarih": "...", "medyan": 8999, "urun": 21, "kaynak": 1}, ...],
      "ilk": {...}, "son": {...},
      "degisim_yuzde": 4.2,        # ilk -> son (yalnizca >=2 olcum varsa)
      "aylik_degisim_yuzde": 4.2,  # son iki olcum arasi
    }, ...
  },
  "ozet": {"artan": 12, "azalan": 3, "sabit": 1, "medyan_degisim_yuzde": 3.1}
}

Kullanim:
  python gecmis.py                    # tum vertikaller
  python gecmis.py --vertikal dugun
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

# Iki olcum arasinda en az bu kadar gun olmali ki "degisim" anlamli sayilsin.
# NEDEN: 24->25 Temmuz testinde "nikah sekeri %40 dustu" ciktı - gercek bir
# fiyat dususu degil, bir gunde kategori sayfasinda LISTELENEN URUNLERIN
# degismesi (orneklem gurultusu). Boyle bir rakami "fiyat %40 dustu" diye
# yayinlamak KIRMIZI CIZGI ihlali olurdu.
#
# 2026-07-26: olcum sikligi ayda 2'ye cikinca (ayin 1'i ve 15'i) esik
# 20 -> 10 gune indirildi. 20 kalsaydi 14 gunluk normal aralik reddedilir,
# HICBIR degisim hesaplanamazdi. 10 gun, tasarlanan 14-15 gunluk araligi
# kabul ederken elle tetiklenen ard arda calistirmalari (gurultu kaynagi)
# hala eliyor.
ASGARI_GUN_ARALIGI = 10

BASE_DIR = Path(__file__).parent
VARSAYILAN_VERI_KOK = BASE_DIR / "veri"
VARSAYILAN_CIKTI_KOK = BASE_DIR.parent / "veri" / "gecmis"

DOSYA_DESENI = re.compile(r"^(?P<kalem>.+)_(?P<site>[^_]+)_(?P<tarih>\d{4}-\d{2}-\d{2})\.json$")


def anlik_goruntuleri_oku(vertikal_klasoru: Path) -> dict[tuple[str, str], list[dict]]:
    """(kalem, tarih) -> o tarihte o kalemi olcen TUM site kayitlari."""
    gruplar: dict[tuple[str, str], list[dict]] = defaultdict(list)
    if not vertikal_klasoru.exists():
        return gruplar
    for dosya in vertikal_klasoru.glob("*.json"):
        if "capraz-dogrulama" in dosya.name:
            continue
        eslesme = DOSYA_DESENI.match(dosya.name)
        if not eslesme:
            continue
        try:
            veri = json.loads(dosya.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        # Saglıksız (karantina) kayitlar zaten ayri klasorde; yine de kontrol.
        if not veri.get("saglikli", True):
            continue
        if not veri.get("toplam_urun"):
            continue
        gruplar[(eslesme.group("kalem"), eslesme.group("tarih"))].append(veri)
    return gruplar


def olcum_noktasi(kayitlar: list[dict]) -> dict | None:
    """Ayni kalem+tarihteki N site kaydini TEK olcum noktasina indirger.

    agrega.py ile ayni ilke: siteler arasi medyan-of-medyan; ham fiyatlar
    birbirine karistirilmaz.
    """
    medyanlar = [k["genel_medyan"] for k in kayitlar if k.get("genel_medyan")]
    if not medyanlar:
        return None
    return {
        "medyan": round(statistics.median(medyanlar)),
        "urun": sum(k.get("toplam_urun", 0) for k in kayitlar),
        "kaynak": len({k.get("site") for k in kayitlar}),
    }


def _degisim(onceki: float, sonraki: float) -> float | None:
    if not onceki:
        return None
    return round((sonraki - onceki) / onceki * 100, 1)


def _gun_farki(t1: str, t2: str) -> int:
    b = datetime.strptime(t1, "%Y-%m-%d").date()
    s = datetime.strptime(t2, "%Y-%m-%d").date()
    return abs((s - b).days)


def _karsilastirilabilir(a: dict, b: dict) -> bool:
    """Iki olcum noktasi arasinda degisim hesaplanabilir mi?"""
    return _gun_farki(a["tarih"], b["tarih"]) >= ASGARI_GUN_ARALIGI


def vertikal_gecmisi(vertikal: str, veri_kok: Path = VARSAYILAN_VERI_KOK) -> dict:
    gruplar = anlik_goruntuleri_oku(veri_kok / vertikal)

    kalem_serileri: dict[str, list[dict]] = defaultdict(list)
    for (kalem, tarih), kayitlar in gruplar.items():
        nokta = olcum_noktasi(kayitlar)
        if nokta:
            kalem_serileri[kalem].append({"tarih": tarih, **nokta})

    kalemler: dict[str, dict] = {}
    tum_tarihler: set[str] = set()
    for kalem, seri in kalem_serileri.items():
        seri.sort(key=lambda x: x["tarih"])
        tum_tarihler.update(x["tarih"] for x in seri)
        kayit = {"seri": seri, "ilk": seri[0], "son": seri[-1]}
        # Degisim yalnizca YETERINCE UZAK iki olcum arasinda hesaplanir
        # (bkz. ASGARI_GUN_ARALIGI) - aksi halde orneklem gurultusunu
        # "fiyat degisimi" diye yayinlamis oluruz.
        if len(seri) >= 2 and _karsilastirilabilir(seri[0], seri[-1]):
            kayit["degisim_yuzde"] = _degisim(seri[0]["medyan"], seri[-1]["medyan"])
            kayit["gun_araligi"] = _gun_farki(seri[0]["tarih"], seri[-1]["tarih"])
            if _karsilastirilabilir(seri[-2], seri[-1]):
                kayit["aylik_degisim_yuzde"] = _degisim(seri[-2]["medyan"], seri[-1]["medyan"])
        kalemler[kalem] = kayit

    # Ozet yalnizca >=2 olcumu olan kalemlerden hesaplanir.
    degisimler = [
        k["degisim_yuzde"] for k in kalemler.values()
        if k.get("degisim_yuzde") is not None
    ]
    ozet = {
        "kalem_sayisi": len(kalemler),
        "karsilastirilabilir": len(degisimler),
        "artan": sum(1 for d in degisimler if d > 0.5),
        "azalan": sum(1 for d in degisimler if d < -0.5),
        "sabit": sum(1 for d in degisimler if -0.5 <= d <= 0.5),
        "medyan_degisim_yuzde": round(statistics.median(degisimler), 1) if degisimler else None,
    }

    return {
        "vertikal": vertikal,
        "uretim_tarihi": date.today().isoformat(),
        "olcumler": sorted(tum_tarihler),
        "kalemler": kalemler,
        "ozet": ozet,
    }


def yaz(veri: dict, cikti_kok: Path = VARSAYILAN_CIKTI_KOK) -> Path:
    cikti_kok.mkdir(parents=True, exist_ok=True)
    hedef = cikti_kok / f"{veri['vertikal']}.json"
    hedef.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    return hedef


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--vertikal", default=None)
    a.add_argument("--veri-kok", type=Path, default=VARSAYILAN_VERI_KOK)
    a.add_argument("--cikti-kok", type=Path, default=VARSAYILAN_CIKTI_KOK)
    args = a.parse_args()

    # Yeni vertikal eklenince BURAYA da eklenmeli - okul vertikali
    # eklendiginde unutuldu ve zaman serisi hic uretilmedi.
    vertikaller = [args.vertikal] if args.vertikal else ["dugun", "ev-kurma", "okul", "arac"]
    for v in vertikaller:
        veri = vertikal_gecmisi(v, args.veri_kok)
        hedef = yaz(veri, args.cikti_kok)
        o = veri["ozet"]
        print(
            f"[{v}] {len(veri['olcumler'])} ölçüm, {o['kalem_sayisi']} kalem, "
            f"{o['karsilastirilabilir']} karşılaştırılabilir"
            + (f", medyan değişim %{o['medyan_degisim_yuzde']}" if o["medyan_degisim_yuzde"] is not None else "")
            + f" -> {hedef}"
        )


if __name__ == "__main__":
    main()
