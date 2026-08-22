# -*- coding: utf-8 -*-
"""Yayin oncesi veri ve uretilmis sayfa tutarlilik kapisi.

Kritik hata varsa raporu yine yazar ama sifirdan farkli kodla cikar. Uyarilar
yayini durdurmaz; tek kaynak, dusuk orneklem ve sert degisim gibi gercek veri
kalitesi sinirlarini makinece okunabilir hale getirir.
"""

from __future__ import annotations

import csv
import json
import re
from datetime import date, datetime
from pathlib import Path

from bs4 import BeautifulSoup

from envanter import envanter_ozeti
import sayfa_uret as su
from veri_surumu import manifest_hatalari, manifest_uret


SITE_KOK = su.SITE_KOK
ASGARI_ORNEKLEM = 8
BAYATLAMA_GUNU = 45
SERT_DEGISIM_YUZDESI = 50


def _kayit(liste: list[dict], kod: str, mesaj: str, **baglam) -> None:
    liste.append({"kod": kod, "mesaj": mesaj, **baglam})


def _json_oku(dosya: Path) -> dict:
    return json.loads(dosya.read_text(encoding="utf-8"))


def _sayi(deger) -> int | None:
    if deger in (None, ""):
        return None
    return round(float(deger))


def _gun_yasi(tarih: str, bugun: date) -> int:
    return (bugun - datetime.strptime(tarih, "%Y-%m-%d").date()).days


def rapor_uret(site_kok: Path = SITE_KOK, bugun: date | None = None) -> dict:
    bugun = bugun or date.today()
    veri_kok = site_kok / "veri"
    hatalar: list[dict] = []
    uyarilar: list[dict] = []
    bilinen_sinirlar: list[dict] = []

    manifest_dosyasi = veri_kok / "manifest.json"
    if not manifest_dosyasi.exists():
        _kayit(hatalar, "manifest_yok", "veri/manifest.json bulunamadi")
        manifest = {}
    else:
        manifest = _json_oku(manifest_dosyasi)
        for hata in manifest_hatalari(manifest, site_kok):
            _kayit(hatalar, "manifest_hash", hata)
        beklenen_manifest = manifest_uret(veri_kok, su.VERTIKALLER, site_kok)
        if manifest != beklenen_manifest:
            _kayit(hatalar, "manifest_icerigi", "Manifest kanonik dosya listesinden yeniden uretilemiyor")

    toplam_seri = 0
    cok_kaynakli = 0
    tek_kaynakli = 0
    kalem_sayfasi = 0
    veri_by_vertikal: dict[str, dict] = {}

    for vertikal, conf in su.VERTIKALLER.items():
        dosya = veri_kok / f"{vertikal}.json"
        if not dosya.exists():
            _kayit(hatalar, "dikey_json_yok", f"{dosya.name} bulunamadi", vertikal=vertikal)
            continue
        veri = _json_oku(dosya)
        veri_by_vertikal[vertikal] = veri
        kalemler = veri.get("kalemler") or {}
        beklenen = {k["id"] for k in conf["kalemler"]}
        gercek = set(kalemler)
        if gercek != beklenen:
            _kayit(
                hatalar, "envanter_ayrismasi",
                f"JSON ile sayfa tanimi farkli; eksik={sorted(beklenen-gercek)}, fazla={sorted(gercek-beklenen)}",
                vertikal=vertikal,
            )
        toplam_seri += len(kalemler)

        gecmis_dosyasi = veri_kok / "gecmis" / f"{vertikal}.json"
        if not gecmis_dosyasi.exists():
            _kayit(hatalar, "gecmis_yok", "Gecmis JSON bulunamadi", vertikal=vertikal)
            gecmis_kalemler = {}
        else:
            gecmis_kalemler = (_json_oku(gecmis_dosyasi).get("kalemler") or {})
            if set(gecmis_kalemler) != gercek:
                _kayit(
                    hatalar, "gecmis_envanteri",
                    "Guncel JSON ile gecmis JSON kalemleri farkli",
                    vertikal=vertikal,
                )

        # Tarihli CSV fiyat kanitidir; fiyat satiri korunur ama olcum tarihi
        # o gunun kanonik kaynak durumundan daha yeni gorunemez.
        for arsiv in sorted((veri_kok / "csv").glob(f"{vertikal}-????-??-??.csv")):
            arsiv_tarihi = arsiv.stem[-10:]
            with arsiv.open(encoding="utf-8-sig", newline="") as f:
                arsiv_satirlari = list(csv.DictReader(f))
            for satir in arsiv_satirlari:
                seri = (gecmis_kalemler.get(satir.get("kalem_id")) or {}).get("seri") or []
                onceki = [n for n in seri if n.get("tarih", "") <= arsiv_tarihi]
                if not onceki:
                    continue
                veri_tarihi = onceki[-1].get("veri_tarihi", onceki[-1].get("tarih"))
                if satir.get("olcum_tarihi") != veri_tarihi:
                    _kayit(
                        hatalar, "arsiv_olcum_tarihi",
                        f"{arsiv.name} satir tarihi kanonik gecmisten farkli",
                        vertikal=vertikal, kalem=satir.get("kalem_id"),
                    )

        csv_dosyasi = veri_kok / "csv" / f"{vertikal}.csv"
        if not csv_dosyasi.exists():
            _kayit(hatalar, "csv_yok", "Guncel CSV bulunamadi", vertikal=vertikal)
            csv_satirlari = {}
        else:
            with csv_dosyasi.open(encoding="utf-8-sig", newline="") as f:
                csv_satirlari = {r["kalem_id"]: r for r in csv.DictReader(f)}
            if set(csv_satirlari) != gercek:
                _kayit(
                    hatalar, "csv_envanteri", "Guncel JSON ile CSV kalemleri farkli",
                    vertikal=vertikal,
                )

        for kalem_id, kalem in kalemler.items():
            baglam = {"vertikal": vertikal, "kalem": kalem_id}
            kaynaklar = [
                k for k in (kalem.get("kaynaklar") or [])
                if (k.get("toplam_urun") or 0) > 0
            ]
            kaynak_sayisi = len({k.get("site") for k in kaynaklar if k.get("site")})
            urun_sayisi = sum(k.get("toplam_urun") or 0 for k in kaynaklar)
            tarihler = [k.get("tarih") for k in kaynaklar if k.get("tarih")]

            if not kalem.get("genel_medyan") or not urun_sayisi or not kaynak_sayisi:
                _kayit(hatalar, "bos_fiyat_serisi", "Yayindaki kalemde kullanilabilir fiyat yok", **baglam)
            if kaynak_sayisi != kalem.get("kaynak_sayisi"):
                _kayit(hatalar, "kaynak_sayisi", "Kaynak listesi ile kaynak_sayisi farkli", **baglam)
            if urun_sayisi != kalem.get("toplam_urun"):
                _kayit(hatalar, "urun_sayisi", "Kaynak orneklemleri ile toplam_urun farkli", **baglam)
            if tarihler and max(tarihler) != kalem.get("guncelleme_tarihi"):
                _kayit(hatalar, "olcum_tarihi", "Kalem tarihi katkida bulunan en yeni kaynaktan farkli", **baglam)

            segmentler = kalem.get("segmentler") or {}
            sirali = [
                segmentler[ad].get("medyan") for ad in ("dusuk", "orta", "luks")
                if segmentler.get(ad, {}).get("medyan") is not None
            ]
            bozuk_sira = sirali != sorted(sirali)
            if bozuk_sira != bool(kalem.get("segment_tutarsiz")):
                _kayit(hatalar, "segment_isareti", "Segment sirasi ile tutarsizlik isareti uyusmuyor", **baglam)

            son = (gecmis_kalemler.get(kalem_id) or {}).get("son")
            if not son:
                _kayit(hatalar, "gecmis_noktasi", "Guncel kalemin son gecmis noktasi yok", **baglam)
            else:
                beklenen_son = {
                    "medyan": kalem.get("genel_medyan"),
                    "urun": kalem.get("toplam_urun"),
                    "kaynak": kalem.get("kaynak_sayisi"),
                    "veri_tarihi": kalem.get("guncelleme_tarihi"),
                }
                gercek_son = {
                    "medyan": son.get("medyan"),
                    "urun": son.get("urun"),
                    "kaynak": son.get("kaynak"),
                    "veri_tarihi": son.get("veri_tarihi", son.get("tarih")),
                }
                if gercek_son != beklenen_son:
                    _kayit(hatalar, "gecmis_guncel_farki", "Son gecmis noktasi guncel kanonik degerden farkli", **baglam)

            satir = csv_satirlari.get(kalem_id)
            if satir:
                csv_karsilastirma = {
                    "urun_sayisi": _sayi(satir.get("urun_sayisi")),
                    "kaynak_sayisi": _sayi(satir.get("kaynak_sayisi")),
                    "olcum_tarihi": satir.get("olcum_tarihi"),
                    "orta_tl": _sayi(satir.get("orta_tl")),
                }
                json_karsilastirma = {
                    "urun_sayisi": kalem.get("toplam_urun"),
                    "kaynak_sayisi": kalem.get("kaynak_sayisi"),
                    "olcum_tarihi": kalem.get("guncelleme_tarihi"),
                    "orta_tl": _sayi((segmentler.get("orta") or {}).get("medyan")),
                }
                if csv_karsilastirma != json_karsilastirma:
                    _kayit(hatalar, "csv_degeri", "CSV satiri guncel JSON'dan farkli", **baglam)

            if kaynak_sayisi >= 2:
                cok_kaynakli += 1
            else:
                tek_kaynakli += 1
                if not conf.get("liste_fiyati"):
                    _kayit(uyarilar, "tek_kaynak", "Perakende/hizmet serisi tek kaynakli", **baglam)
            if urun_sayisi < ASGARI_ORNEKLEM:
                _kayit(uyarilar, "dusuk_orneklem", f"Orneklem {urun_sayisi} urun", **baglam)
            if kalem.get("segment_tutarsiz"):
                _kayit(bilinen_sinirlar, "segment_tutarsiz", "Segment kirilimi sayfada gizleniyor", **baglam)
            if kalem.get("capraz_dogrulama_uyarisi"):
                _kayit(bilinen_sinirlar, "kaynak_farki", "Kaynak medyanlari arasinda gorunur fark var", **baglam)
            if kalem.get("guncelleme_tarihi") and _gun_yasi(kalem["guncelleme_tarihi"], bugun) > BAYATLAMA_GUNU:
                _kayit(uyarilar, "bayat_olcum", f"Olcum {BAYATLAMA_GUNU} gunden eski", **baglam)
            aylik = (gecmis_kalemler.get(kalem_id) or {}).get("aylik_degisim_yuzde")
            if aylik is not None and abs(aylik) >= SERT_DEGISIM_YUZDESI:
                _kayit(uyarilar, "sert_degisim", f"Son karsilastirilabilir degisim %{aylik}", **baglam)

        ozet = su.vertikal_ozeti(vertikal, veri_kok)
        sayfa = site_kok / conf["yol"] / "index.html"
        if not sayfa.exists():
            _kayit(hatalar, "dikey_sayfa_yok", "Dikey ana sayfasi bulunamadi", vertikal=vertikal)
        elif ozet:
            cevap = BeautifulSoup(sayfa.read_text(encoding="utf-8"), "html.parser").select_one(".cevap-blok")
            if not cevap or su._para(ozet["toplam"]) not in cevap.get_text(" ", strip=True):
                _kayit(hatalar, "dikey_sayfa_toplami", "Gorunur cevap kanonik toplamdan farkli", vertikal=vertikal)

    envanter = envanter_ozeti(veri_kok, su.VERTIKALLER)
    envanter_dosyasi = veri_kok / "envanter.json"
    if not envanter_dosyasi.exists():
        _kayit(hatalar, "envanter_yok", "veri/envanter.json bulunamadi")
    else:
        yayin_envanteri = _json_oku(envanter_dosyasi)
        for alan in ("fiyat_serisi", "cok_kaynakli", "tek_kaynak"):
            if yayin_envanteri.get(alan) != envanter.get(alan):
                _kayit(hatalar, "envanter_ozeti", f"envanter.json {alan} alani kanonik sayimdan farkli")
        if yayin_envanteri.get("dataset_surumu") != manifest.get("dataset_surumu"):
            _kayit(hatalar, "envanter_surumu", "envanter.json ile manifest surumu farkli")

    if manifest.get("fiyat_serisi") != toplam_seri:
        _kayit(hatalar, "manifest_envanteri", "Manifest fiyat serisi sayisi guncel JSON'lardan farkli")

    for yol in ("index.html", "veri/index.html", "llms.txt", "ai.txt"):
        dosya = site_kok / yol
        metin = dosya.read_text(encoding="utf-8") if dosya.exists() else ""
        if not re.search(rf"{toplam_seri}(?: aktif)? fiyat serisi", metin):
            _kayit(hatalar, "gorunur_envanter", f"{yol} ortak fiyat serisi sayisini tasimiyor")

    ana_sayfa = site_kok / "index.html"
    if ana_sayfa.exists():
        soup = BeautifulSoup(ana_sayfa.read_text(encoding="utf-8"), "html.parser")
        for vertikal, veri in veri_by_vertikal.items():
            ozet = su.vertikal_ozeti(vertikal, veri_kok)
            if not ozet:
                continue
            link = soup.select_one(f'h3 a[href="/{su.VERTIKALLER[vertikal]["yol"]}/"]')
            kart = link.find_parent(class_="kart") if link else None
            if not kart or su._para(ozet["toplam"]) not in kart.get_text(" ", strip=True):
                _kayit(hatalar, "anasayfa_toplami", "Ana sayfa karti kanonik toplamdan farkli", vertikal=vertikal)

    su.kalem_sayfalarini_genislet(veri_kok)
    for vertikal, conf in su.VERTIKALLER.items():
        kalemler = (veri_by_vertikal.get(vertikal) or {}).get("kalemler") or {}
        for sayfa in conf.get("kalem_sayfalari", []):
            kalem = kalemler.get(sayfa["id"])
            hedef = site_kok / conf["yol"] / sayfa["slug"] / "index.html"
            baglam = {"vertikal": vertikal, "kalem": sayfa["id"]}
            if not hedef.exists() or not kalem:
                _kayit(hatalar, "kalem_sayfasi_yok", "Yayinlanmasi gereken kalem sayfasi/verisi yok", **baglam)
                continue
            cevap = BeautifulSoup(hedef.read_text(encoding="utf-8"), "html.parser").select_one(".cevap-blok")
            cevap_metni = cevap.get_text(" ", strip=True) if cevap else ""
            beklenenler = [kalem.get("guncelleme_tarihi")]
            if kalem.get("karma_urun_turu"):
                beklenenler.extend(
                    su._para(o["genel_medyan"])
                    for o in (kalem.get("ozellik_ozeti", {}).get("urun_turleri") or {}).values()
                    if o.get("urun_sayisi", 0) >= 3
                )
            else:
                # Kalem detayinin ana metrigi fiyat gecmisiyle ayni:
                # genel_medyan. Orta segment yalniz butce referansidir ve
                # segment_tutarsiz kalemlerde gizlenebilir.
                beklenenler.append(
                    su._para(kalem.get("genel_medyan"))
                    if kalem.get("genel_medyan") else None
                )
                if vertikal == "arac" and sayfa["id"] == "en-ucuz-sifir-arac":
                    en_dusuk = (
                        ((kalem.get("segmentler") or {}).get("dusuk") or {}).get("min")
                    )
                    beklenenler.append(su._para(en_dusuk) if en_dusuk else None)
            if not cevap or any(b and b not in cevap_metni for b in beklenenler):
                _kayit(hatalar, "kalem_sayfasi_cevabi", "Gorunur kalem cevabi guncel JSON'dan farkli", **baglam)
            kalem_sayfasi += 1

    return {
        "dataset_surumu": manifest.get("dataset_surumu"),
        "kontrol_tarihi": bugun.isoformat(),
        "durum": "gecti" if not hatalar else "kaldi",
        "ozet": {
            "fiyat_serisi": toplam_seri,
            "cok_kaynakli": cok_kaynakli,
            "tek_kaynakli": tek_kaynakli,
            "kalem_sayfasi": kalem_sayfasi,
            "kritik_hata": len(hatalar),
            "uyari": len(uyarilar),
            "bilinen_sinir": len(bilinen_sinirlar),
        },
        "kritik_hatalar": hatalar,
        "uyarilar": uyarilar,
        "bilinen_sinirlar": bilinen_sinirlar,
    }


def main() -> int:
    rapor = rapor_uret()
    hedef = SITE_KOK / "veri" / "qa.json"
    hedef.write_text(
        json.dumps(rapor, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    ozet = rapor["ozet"]
    print(
        f"QA {rapor['durum']}: {ozet['fiyat_serisi']} seri, "
        f"{ozet['kalem_sayfasi']} kalem sayfasi, "
        f"{ozet['kritik_hata']} kritik hata, {ozet['uyari']} uyari, "
        f"{ozet['bilinen_sinir']} gorunur veri siniri"
    )
    for hata in rapor["kritik_hatalar"]:
        print(f"HATA [{hata['kod']}] {hata['mesaj']}")
    return 0 if rapor["durum"] == "gecti" else 1


if __name__ == "__main__":
    raise SystemExit(main())
