# -*- coding: utf-8 -*-
"""
Maliyeti Ne? - TÜFE (resmi enflasyon) verisi — TCMB EVDS

NE ISE YARAR: kendi olctugumuz fiyatlarin yaninda RESMI bir referans
gosterebilmek. Iki kullanimi var:
  1. Geriye donuk seri: bizim olcumumuz 2026 Temmuz'da basladi, ama
     "2026 Ocak'tan bu yana fiyatlar ne oldu?" sorusuna TUFE ile cevap
     verebiliyoruz.
  2. Capraz dogrulama (COK KAYNAK KURALI 5. katman): bizim olctugumuz
     kalem degisimi, ilgili TUFE alt grubuyla ayni yonde mi? Ters
     dusen siçramalar kazima hatasina isaret eder.

ONEMLI - KIRMIZI CIZGI: TUFE bizim fiyatimizin YERINE gecmez. TUFE bir
ENDEKS (2025=100), TL cinsinden fiyat degil. Sayfalarda her zaman
"TUIK/TCMB verisine gore ... yuzde X" diye ayri gosterilir; bizim
olctugumuz TL tutarlarla KARISTIRILMAZ.

API NOTU (2026-07-26'da tespit edildi): EVDS `evds2` -> `evds3`'e tasindi
ve klasik `/service/evds/series=...&key=...` yolu ARTIK CALISMIYOR (SPA
her yolu index.html'e dusuruyor, hatta gecersiz key'le bile ayni yaniti
veriyor - yani hata mesaji da alamiyorsunuz). Yeni yol:
  POST https://evds3.tcmb.gov.tr/igmevdsms-dis/fe   (JSON govde)
Govdede `groupSeperator` ve `isRaporSayfasi` alanlari ZORUNLU; eksikse
sunucu 500 doner. Arama icin: GET /igmevdsms-dis/searchResults?searchVal=

Kullanim:
  python enflasyon.py                 # /veri/enflasyon.json uretir
  python enflasyon.py --yil 2026
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent
KEY_DOSYASI = BASE_DIR / ".evds-key"
VARSAYILAN_CIKTI = BASE_DIR.parent / "veri" / "enflasyon.json"

API = "https://evds3.tcmb.gov.tr/igmevdsms-dis/fe"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

# TUFE serileri (2025=100 bazli). Kodlar EVDS aramasindan DOGRULANDI -
# tahmin edilmedi. Eski `TP.FG.J*` kodlari arsiv serileri; guncel veri
# vermiyor (2026 Ocak'ta duruyorlar).
#
# `vertikal` alani: bu grup hangi endeksimizle karsilastirilabilir.
# Birebir ayni sey DEGIL - TUFE'nin "Dayanikli Mallar" grubu beyaz esya +
# mobilyayi kapsar, bizim ev-kurma sepetimiz daha genis. Bu yuzden
# yayinlarken "ilgili TUFE grubu" diye sunulur, "ayni sey" diye degil.
SERILER = {
    "TP.FE25.OKTG01": {"ad": "TÜFE (genel)", "vertikal": None},
    # Giyim serisi iki vertikali de ilgilendiriyor (gelinlik/damatlik ve
    # okul ayakkabisi). `vertikaller` listesi tekil `vertikal`in yerine
    # gecer; ikisi de destekleniyor.
    "TP.FE25.OKTG19": {"ad": "Giyim ve ayakkabı", "vertikal": "dugun",
                       "vertikaller": ["dugun", "okul"]},
    "TP.FE25.OKTG20": {"ad": "Dayanıklı mallar (altın hariç)", "vertikal": "ev-kurma"},
    "TP.FE25.OKTG25": {"ad": "Lokanta ve oteller", "vertikal": "dugun"},
    "TP.FE25.OKTG22": {"ad": "Alkollü içecekler, tütün ve altın", "vertikal": "dugun"},
    # Okul: TUFE'de "kirtasiye/egitim malzemesi" diye ayri grup YOK.
    # En yakin karsilik "Diger temel mallar" (giyim/gida/enerji disi
    # dayaniksiz mallar) - kirtasiye buraya giriyor. Giyim ayakkabi
    # zaten ayri seri, o da okul sepetinin parcasi.
    "TP.FE25.OKTG21": {"ad": "Diğer temel mallar", "vertikal": "okul"},
}


def anahtar_oku(dosya: Path | None = None) -> str | None:
    d = dosya or KEY_DOSYASI
    if not d.exists():
        return None
    return d.read_text(encoding="utf-8").strip() or None


def _sayi(ham: str | None) -> float | None:
    """'129,99' / '1,234.56' -> float. EVDS binlik ayiraci virgul kullaniyor."""
    if ham in (None, "", "null"):
        return None
    try:
        return float(str(ham).replace(",", ""))
    except ValueError:
        return None


def tufe_cek(
    kodlar: list[str],
    baslangic: str,
    bitis: str,
    anahtar: str | None = None,
    zaman_asimi: int = 40,
) -> list[dict]:
    """EVDS'den aylik TUFE serilerini ceker. Basarisizsa BOS liste doner.

    Sessizce bos donmek yerine cagiran taraf uyari basar - veri yoksa
    sayfada "TUIK verisi" bolumu hic gosterilmez (uydurma rakam yok).
    """
    basliklar = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://evds3.tcmb.gov.tr/",
    }
    if anahtar:
        basliklar["key"] = anahtar

    govde = {
        "type": "json",
        "series": "-".join(kodlar),
        "aggregationTypes": "-".join(["last"] * len(kodlar)),
        "formulas": "-".join(["0"] * len(kodlar)),
        "startDate": baslangic,
        "endDate": bitis,
        "frequency": "5",  # 5 = aylik
        "decimalSeperator": ".",
        "decimal": "2",
        "dateFormat": "0",
        "lang": "tr",
        "ozelFormuller": [],
        # Bu iki alan ZORUNLU - eksikse sunucu 500 doner (deneyerek bulundu).
        "groupSeperator": True,
        "isRaporSayfasi": False,
    }
    try:
        yanit = requests.post(API, headers=basliklar, json=govde, timeout=zaman_asimi)
    except requests.RequestException:
        return []
    if yanit.status_code != 200 or not yanit.text.strip().startswith("{"):
        return []
    try:
        return json.loads(yanit.text).get("items") or []
    except json.JSONDecodeError:
        return []


def derle(yil: int, anahtar: str | None = None) -> dict:
    kayitlar = tufe_cek(list(SERILER), f"01-01-{yil}", f"31-12-{yil}", anahtar)
    gruplar: dict[str, dict] = {}
    olcumler: list[str] = []

    for kod, meta in SERILER.items():
        alan = kod.replace(".", "_")
        seri = []
        for kayit in kayitlar:
            deger = _sayi(kayit.get(alan))
            if deger is None:
                continue
            seri.append({"tarih": kayit.get("Tarih"), "endeks": deger})
        if len(seri) < 2:
            continue
        ilk, son = seri[0], seri[-1]
        gruplar[kod] = {
            "ad": meta["ad"],
            "vertikal": meta["vertikal"],
            # Bir TUFE grubu birden fazla vertikali ilgilendirebilir
            # (giyim: hem dugun hem okul). Cikti semasina tasinmazsa
            # rehber tarafi goremez.
            "vertikaller": meta.get("vertikaller") or [meta["vertikal"]],
            "seri": seri,
            "ilk": ilk,
            "son": son,
            "degisim_yuzde": round((son["endeks"] - ilk["endeks"]) / ilk["endeks"] * 100, 1),
        }
        olcumler = [x["tarih"] for x in seri]

    return {
        "kaynak": "TCMB EVDS (TÜİK Tüketici Fiyat Endeksi, 2025=100)",
        "kaynak_url": "https://evds3.tcmb.gov.tr/",
        "yil": yil,
        "uretim_tarihi": date.today().isoformat(),
        "olcumler": olcumler,
        "gruplar": gruplar,
    }


def yaz(veri: dict, hedef: Path | None = None) -> Path:
    h = hedef or VARSAYILAN_CIKTI
    h.parent.mkdir(parents=True, exist_ok=True)
    h.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    return h


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--yil", type=int, default=date.today().year)
    a.add_argument("--cikti", type=Path, default=None)
    args = a.parse_args()

    anahtar = anahtar_oku()
    if not anahtar:
        print("UYARI: scraper/.evds-key bulunamadi - anahtarsiz deneniyor.")

    veri = derle(args.yil, anahtar)
    if not veri["gruplar"]:
        print("TUFE verisi alinamadi - dosya YAZILMADI (uydurma rakam yok).")
        return 1
    hedef = yaz(veri, args.cikti)
    print(f"TÜFE derlendi: {len(veri['gruplar'])} grup, "
          f"{len(veri['olcumler'])} ay ({veri['olcumler'][0]} → {veri['olcumler'][-1]})")
    for kod, g in veri["gruplar"].items():
        print(f"  {g['ad']:34} %{g['degisim_yuzde']:+.1f}")
    print(f"-> {hedef}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
