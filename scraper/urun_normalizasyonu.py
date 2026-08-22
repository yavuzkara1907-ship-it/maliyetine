# -*- coding: utf-8 -*-
"""Urun adlarini karsilastirilabilir veri alanlarina donusturur.

Bu modul fiyat kazimaz. Motorun zaten topladigi ``isim`` ve ``fiyat``
alanlarindan yalnizca urun adinda ACIKCA yazan miktar ve ozellikleri
cikarir. Cikarilamayan alan tahmin edilmez.
"""

from __future__ import annotations

import re
import statistics
from collections import defaultdict


BIRIM_KALEMLERI = {
    "bebek-bezi": ("adet",),
    "cis-pedi": ("adet",),
    "kedi-mamasi": ("kg",),
    "kopek-mamasi": ("kg",),
    "kedi-kumu": ("kg", "litre"),
}

BIRIM_ADLARI = {"kg": "TL/kg", "litre": "TL/litre", "adet": "TL/adet"}

_COKLU_MIKTAR = re.compile(
    r"(?<![\d.,/-])(?P<carpan>\d{1,3})\s*[x×]\s*"
    r"(?P<miktar>\d+(?:[.,]\d+)?)\s*"
    r"(?P<birim>kg|kilogram|g|gr|gram|l|lt|litre)\b",
    re.IGNORECASE,
)
_TOPLAM_MIKTAR = re.compile(
    r"(?<![\d.,/-])(?P<ilk>\d+(?:[.,]\d+)?)\s*\+\s*"
    r"(?P<ikinci>\d+(?:[.,]\d+)?)\s*"
    r"(?P<birim>kg|kilogram|g|gr|gram|l|lt|litre)\b",
    re.IGNORECASE,
)
_TEK_MIKTAR = re.compile(
    r"(?<![\d.,/-])(?P<miktar>\d+(?:[.,]\d+)?)\s*"
    r"(?P<birim>kg|kilogram|g|gr|gram|l|lt|litre)\b",
    re.IGNORECASE,
)
_COKLU_ADET = re.compile(
    r"(?<![\d.,/-])(?P<carpan>\d{1,3})\s*(?:paket|pk)\s*"
    r"(?:[x×]\s*)?(?P<adet>\d{1,4})\s*(?:adet|ad\.?)(?!\w)",
    re.IGNORECASE,
)
_TEK_ADET = re.compile(
    r"(?<![\d.,/-])(?P<adet>\d{1,4})\s*"
    r"(?:adet|ad\.?|['’]?\s*l[ıiuü])\b",
    re.IGNORECASE,
)


def _ondalik(deger: str) -> float:
    return float(deger.replace(",", "."))


def _birim(birim: str) -> tuple[str, float]:
    birim = birim.casefold()
    if birim in {"g", "gr", "gram"}:
        return "kg", 0.001
    if birim in {"kg", "kilogram"}:
        return "kg", 1.0
    return "litre", 1.0


def _cakisan(span: tuple[int, int], kullanilan: list[tuple[int, int]]) -> bool:
    return any(span[0] < bitis and span[1] > baslangic for baslangic, bitis in kullanilan)


def miktarlari_ayristir(metin: str) -> dict[str, float]:
    """Urun adindaki acik paket miktarlarini ortak birimlere cevirir.

    ``2 x 10 kg`` tek paket bilgisi olarak 20 kg'dir. Bir ad hem kg hem
    litre veriyorsa (kedi kumunda gorulur) ikisi de korunur; kg-litre
    arasinda yogunluk tahmini yapilmaz.
    """
    metin = str(metin or "")
    adaylar: list[tuple[str, float, tuple[int, int]]] = []
    kullanilan: list[tuple[int, int]] = []

    for eslesme in _TOPLAM_MIKTAR.finditer(metin):
        birim, katsayi = _birim(eslesme.group("birim"))
        miktar = (_ondalik(eslesme.group("ilk")) + _ondalik(eslesme.group("ikinci"))) * katsayi
        adaylar.append((birim, miktar, eslesme.span()))
        kullanilan.append(eslesme.span())

    for eslesme in _COKLU_MIKTAR.finditer(metin):
        birim, katsayi = _birim(eslesme.group("birim"))
        miktar = _ondalik(eslesme.group("miktar")) * int(eslesme.group("carpan")) * katsayi
        adaylar.append((birim, miktar, eslesme.span()))
        kullanilan.append(eslesme.span())

    for eslesme in _TEK_MIKTAR.finditer(metin):
        if _cakisan(eslesme.span(), kullanilan):
            continue
        birim, katsayi = _birim(eslesme.group("birim"))
        adaylar.append((birim, _ondalik(eslesme.group("miktar")) * katsayi, eslesme.span()))

    for eslesme in _COKLU_ADET.finditer(metin):
        miktar = int(eslesme.group("carpan")) * int(eslesme.group("adet"))
        adaylar.append(("adet", float(miktar), eslesme.span()))
        kullanilan.append(eslesme.span())

    for eslesme in _TEK_ADET.finditer(metin):
        if _cakisan(eslesme.span(), kullanilan):
            continue
        adaylar.append(("adet", float(eslesme.group("adet")), eslesme.span()))

    sonuc: dict[str, float] = {}
    for birim in ("kg", "litre", "adet"):
        birim_adaylari = [(miktar, span) for b, miktar, span in adaylar if b == birim]
        if not birim_adaylari:
            continue
        # ``15 kg + 2 kg`` gibi promosyonlarda iki miktar da pakete aittir.
        # Diger coklu ifadelerde son miktar genellikle asil paket bilgisidir.
        if len(birim_adaylari) > 1 and all(
            "+" in metin[birim_adaylari[i][1][1]:birim_adaylari[i + 1][1][0]]
            for i in range(len(birim_adaylari) - 1)
        ):
            miktar = sum(a[0] for a in birim_adaylari)
        else:
            miktar = birim_adaylari[-1][0]
        alt, ust = {"kg": (0.05, 100), "litre": (0.25, 200), "adet": (2, 1000)}[birim]
        if alt <= miktar <= ust:
            sonuc[birim] = round(miktar, 3)
    return sonuc


def _aykiri_temizle(kayitlar: list[dict], alan: str) -> list[dict]:
    if len(kayitlar) < 20:
        return kayitlar
    sirali = sorted(k[alan] for k in kayitlar)
    q1, q3 = sirali[len(sirali) // 4], sirali[(3 * len(sirali)) // 4]
    iqr = q3 - q1
    alt, ust = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return [k for k in kayitlar if alt <= k[alan] <= ust]


def _segmentle(kayitlar: list[dict], alan: str) -> dict:
    if not kayitlar:
        return {}
    degerler = sorted(k[alan] for k in kayitlar)
    if len(degerler) == 1:
        tek = round(degerler[0], 2)
        ozet = {"min": tek, "medyan": tek, "max": tek, "urun_sayisi": 1}
        return {ad: dict(ozet) for ad in ("dusuk", "orta", "luks")}
    p25, p75 = degerler[len(degerler) // 4], degerler[(3 * len(degerler)) // 4]
    gruplar = {
        "dusuk": [d for d in degerler if d <= p25],
        "orta": [d for d in degerler if p25 < d <= p75],
        "luks": [d for d in degerler if d > p75],
    }
    return {
        ad: {
            "min": round(min(liste), 2),
            "medyan": round(statistics.median(liste), 2),
            "max": round(max(liste), 2),
            "urun_sayisi": len(liste),
        }
        for ad, liste in gruplar.items() if liste
    }


def _daginik_ornek(kayitlar: list[dict], alan: str, sinir: int = 8) -> list[dict]:
    sirali = sorted(kayitlar, key=lambda k: (k[alan], k.get("isim", "").casefold()))
    if len(sirali) <= sinir:
        return sirali
    indisler = [round(i * (len(sirali) - 1) / (sinir - 1)) for i in range(sinir)]
    return [sirali[i] for i in indisler]


def birim_fiyat_ozeti(kalem: str, urunler: list[dict]) -> dict:
    izinli = BIRIM_KALEMLERI.get(kalem)
    if not izinli:
        return {}
    gruplar: dict[str, list[dict]] = defaultdict(list)
    for urun in urunler:
        fiyat = float(urun.get("fiyat") or 0)
        if fiyat <= 0:
            continue
        miktarlar = miktarlari_ayristir(urun.get("isim", ""))
        for birim in izinli:
            miktar = miktarlar.get(birim)
            if not miktar:
                continue
            # Mama paketine eklenmis adetli yas mama/odul urunu toplam
            # fiyatin parcasidir ama kg miktarinin parcasi degildir.
            if birim == "kg" and kalem in {"kedi-mamasi", "kopek-mamasi"} \
                    and miktarlar.get("adet"):
                continue
            birim_fiyat = fiyat / miktar
            alt, ust = {"kg": (5, 20000), "litre": (1, 5000), "adet": (0.1, 5000)}[birim]
            if not alt <= birim_fiyat <= ust:
                continue
            gruplar[birim].append({
                "isim": str(urun.get("isim", ""))[:240],
                "fiyat": round(fiyat, 2),
                "miktar": miktar,
                "birim_fiyat": round(birim_fiyat, 2),
            })

    sonuc = {}
    for birim in izinli:
        temiz = _aykiri_temizle(gruplar.get(birim, []), "birim_fiyat")
        if not temiz:
            continue
        sonuc[birim] = {
            "etiket": BIRIM_ADLARI[birim],
            "genel_medyan": round(statistics.median(k["birim_fiyat"] for k in temiz), 2),
            "eslesen_urun": len(temiz),
            "toplam_urun": len(urunler),
            "eslesme_orani": round(len(temiz) / len(urunler), 3) if urunler else 0,
            "segmentler": _segmentle(temiz, "birim_fiyat"),
            "ornek_urunler": _daginik_ornek(temiz, "birim_fiyat"),
        }
    return sonuc


_MARKALAR = (
    "Arçelik", "Beko", "Bosch", "Siemens", "Profilo", "Vestel", "Altus",
    "Regal", "Kumtel", "Luxell", "Simfer", "Ferre", "Silverline", "Teka",
    "Franke", "Electrolux", "Samsung", "Hoover", "Grundig", "Miele", "Smeg",
)
_OZELLIKLER = {
    "buhar-destekli": ("Buhar destekli", r"\bbuhar(?:\s+destekli)?\b|steam"),
    "pirolitik": ("Pirolitik temizleme", r"\bpirolitik\b|pyroly"),
    "airfry": ("AirFry", r"\bair\s*fry\b"),
    "induksiyon": ("İndüksiyon", r"\bind[uü]ksiyon"),
    "gazli": ("Gazlı", r"\bgazl[ıi]\b"),
    "elektrikli": ("Elektrikli", r"\belektrikli\b"),
}
_URUN_TURLERI = {
    "ankastre-set": "Ankastre set",
    "ocakli-firin": "Ocaklı fırın",
    "ankastre-firin": "Ankastre fırın",
    "ankastre-ocak": "Ankastre ocak",
    "solo-firin": "Solo fırın",
    "firin": "Fırın",
    "ocak": "Ocak",
}

# Tek kategori sayfasinda birbirinden farkli urun tipleri toplanabilen
# kalemler. Yalniz urun adinda ACIKCA gecen ifadeler kullanilir; fiyatina
# bakarak "bu otomatik olmali" gibi bir tahmin yapilmaz.
_GENIS_KATEGORI_TURLERI = {
    "kedi-tuvaleti": (
        ("otomatik-tuvalet", "Otomatik kedi tuvaleti", r"otomatik|ak[ıi]ll[ıi]|self[ -]?clean|robot"),
        ("kapali-tuvalet", "Kapalı kedi tuvaleti", r"kapal[ıi]|kapakl[ıi]|kabin|filtreli"),
        ("acik-tuvalet", "Açık kedi tuvaleti / kum kabı", r"a[çc][ıi]k|kum kab[ıi]"),
    ),
    "kahve-makinesi": (
        ("espresso", "Espresso makinesi", r"espresso|barista|cappuccino|latte|portafiltre|tam otomatik"),
        ("kapsul", "Kapsül kahve makinesi", r"kaps[uü]l|capsule|nespresso|dolce gusto"),
        ("filtre", "Filtre kahve makinesi", r"filtre kahve|drip"),
        ("turk-kahvesi", "Türk kahvesi makinesi", r"t[uü]rk kahve|turkish coffee|cezve"),
    ),
    "buzdolabi": (
        ("mini", "Mini / tezgah altı buzdolabı", r"\bmini\b|minibar|b[uü]ro tipi|tezg[aâ]h alt[ıi]"),
        ("gardiroplu", "Gardırop tipi buzdolabı", r"gard[ıi]rop tipi|side[ -]?by[ -]?side|multi[ -]?door|4 kap[ıi]"),
        ("standart", "Standart buzdolabı", r"buzdolab[ıi]|no[ -]?frost|komb[iı] tipi"),
    ),
    "dikey-supurge": (
        ("islak-kuru", "Islak-kuru dikey süpürge", r"[ıi]slak.?kuru|y[ıi]kama|mop"),
        ("sarjli", "Şarjlı dikey süpürge", r"[şs]arjl[ıi]|kablosuz|cordless"),
        ("kablolu", "Kablolu dikey süpürge", r"kablolu"),
        ("el-supurgesi", "El süpürgesi", r"el s[uü]p[uü]rgesi|handheld"),
    ),
}


def firin_ozelliklerini_ayristir(isim: str) -> dict:
    metin = str(isim or "")
    kucuk = metin.casefold()
    firin_var = bool(re.search(r"f[ıi]r[ıi]n", kucuk))
    ocak_var = bool(re.search(r"\bocak", kucuk))
    ankastre = "ankastre" in kucuk
    set_var = bool(re.search(r"\bset(?:i)?\b|\b[234]\s*['’]?l[üu]\b", kucuk))

    urun_turu = None
    if set_var and (ankastre or firin_var or ocak_var):
        urun_turu = "ankastre-set"
    elif re.search(r"ocakl[ıi].{0,30}f[ıi]r[ıi]n", kucuk):
        urun_turu = "ocakli-firin"
    elif ankastre and firin_var:
        urun_turu = "ankastre-firin"
    elif ankastre and ocak_var:
        urun_turu = "ankastre-ocak"
    elif "solo" in kucuk and firin_var:
        urun_turu = "solo-firin"
    elif firin_var:
        urun_turu = "firin"
    elif ocak_var:
        urun_turu = "ocak"

    marka = next((m for m in _MARKALAR if re.search(rf"(?<!\w){re.escape(m)}(?!\w)", metin, re.I)), None)
    enerji = None
    enerji_eslesme = re.search(
        r"(?:enerji\s+s[ıi]n[ıi]f[ıi]\s*[:\-]?\s*([a-g](?:\+{1,3})?))|"
        r"(?:\b([a-g](?:\+{1,3})?)\s+enerji)", kucuk, re.I,
    )
    if enerji_eslesme:
        enerji = (enerji_eslesme.group(1) or enerji_eslesme.group(2)).upper()

    kapasite = None
    kapasite_eslesmeleri = re.findall(r"(?<!\d)(\d{2,3})\s*(?:l|lt|litre)\b", kucuk)
    for aday in reversed(kapasite_eslesmeleri):
        if 30 <= int(aday) <= 150:
            kapasite = int(aday)
            break

    ozellikler = [anahtar for anahtar, (_, desen) in _OZELLIKLER.items()
                  if re.search(desen, kucuk, re.I)]
    model = None
    if marka:
        marka_sonu = re.search(re.escape(marka), metin, re.I).end()
        for token in re.findall(r"\b[A-Z0-9][A-Z0-9._/-]{3,}\b", metin[marka_sonu:], re.I):
            if re.search(r"[A-Za-z]", token) and re.search(r"\d", token):
                model = token
                break
    return {
        **({"urun_turu": urun_turu} if urun_turu else {}),
        **({"marka": marka} if marka else {}),
        **({"model": model} if model else {}),
        **({"kapasite_litre": kapasite} if kapasite else {}),
        **({"enerji_sinifi": enerji} if enerji else {}),
        **({"ozellikler": ozellikler} if ozellikler else {}),
    }


def _grup_ozeti(urunler: list[dict], alan: str, adlar: dict | None = None) -> dict:
    gruplar: dict[str, list[dict]] = defaultdict(list)
    for urun in urunler:
        deger = urun["nitelikler"].get(alan)
        if deger:
            gruplar[str(deger)].append(urun)
    return {
        deger: {
            "ad": (adlar or {}).get(deger, deger),
            "genel_medyan": round(statistics.median(u["fiyat"] for u in liste)),
            "urun_sayisi": len(liste),
            "segmentler": _segmentle(liste, "fiyat"),
        }
        for deger, liste in sorted(gruplar.items())
    }


def firin_ozellik_ozeti(kalem: str, urunler: list[dict]) -> dict:
    if kalem != "firin-ocak":
        return {}
    normal = []
    for urun in urunler:
        nitelikler = firin_ozelliklerini_ayristir(urun.get("isim", ""))
        if nitelikler:
            normal.append({
                "isim": str(urun.get("isim", ""))[:240],
                "fiyat": round(float(urun.get("fiyat") or 0), 2),
                "nitelikler": nitelikler,
            })
    if not normal:
        return {}

    ozellik_gruplari: dict[str, list[dict]] = defaultdict(list)
    for urun in normal:
        for ozellik in urun["nitelikler"].get("ozellikler", []):
            ozellik_gruplari[ozellik].append(urun)
    kapasiteler = [u for u in normal if u["nitelikler"].get("kapasite_litre")]
    ornekler = _daginik_ornek(normal, "fiyat", 15)
    return {
        "toplam_urun": len(urunler),
        "ozellik_eslesen_urun": len(normal),
        "urun_turleri": _grup_ozeti(normal, "urun_turu", _URUN_TURLERI),
        "markalar": _grup_ozeti(normal, "marka"),
        "enerji_siniflari": _grup_ozeti(normal, "enerji_sinifi"),
        "ozellikler": {
            anahtar: {
                "ad": _OZELLIKLER[anahtar][0],
                "genel_medyan": round(statistics.median(u["fiyat"] for u in liste)),
                "urun_sayisi": len(liste),
                "segmentler": _segmentle(liste, "fiyat"),
            }
            for anahtar, liste in sorted(ozellik_gruplari.items())
        },
        **({"kapasite_litre": {
            "min": min(u["nitelikler"]["kapasite_litre"] for u in kapasiteler),
            "medyan": round(statistics.median(u["nitelikler"]["kapasite_litre"] for u in kapasiteler)),
            "max": max(u["nitelikler"]["kapasite_litre"] for u in kapasiteler),
            "urun_sayisi": len(kapasiteler),
        }} if kapasiteler else {}),
        "ornek_urunler": ornekler,
        # Set, ocak ve firin birbirinin fiyat segmenti degil, ayri urundur.
        # Bu bayrak butce toplaminda tek bir ortak fiyat kullanilmasini engeller.
        "tek_metrik_gecersiz": True,
    }


def genis_kategori_urun_turu(kalem: str, isim: str) -> dict:
    """Genis kategori kaleminde urun adindan acik urun turunu cikarir."""
    desenler = _GENIS_KATEGORI_TURLERI.get(kalem)
    if not desenler:
        return {}
    metin = str(isim or "").casefold()
    for anahtar, _ad, desen in desenler:
        if re.search(desen, metin, re.I):
            return {"urun_turu": anahtar}
    return {}


def urun_ozellik_ozeti(kalem: str, urunler: list[dict]) -> dict:
    """Kaleme uygun yapisal urun ozeti.

    Firin/ocakta mevcut ayrintili ayristirici korunur. Genis kategori
    kalemlerinde yalniz urun tipi cikarilir; bu kirilim ana fiyati ortadan
    kaldirmaz, kullaniciya dagilimin hangi urun tiplerinden geldigini gosterir.
    """
    if kalem == "firin-ocak":
        return firin_ozellik_ozeti(kalem, urunler)
    desenler = _GENIS_KATEGORI_TURLERI.get(kalem)
    if not desenler:
        return {}

    normal = []
    for urun in urunler:
        nitelikler = genis_kategori_urun_turu(kalem, urun.get("isim", ""))
        if nitelikler:
            normal.append({
                "isim": str(urun.get("isim", ""))[:240],
                "fiyat": round(float(urun.get("fiyat") or 0), 2),
                "nitelikler": nitelikler,
            })
    if not normal:
        return {}
    adlar = {anahtar: ad for anahtar, ad, _desen in desenler}
    return {
        "toplam_urun": len(urunler),
        "ozellik_eslesen_urun": len(normal),
        "urun_turleri": _grup_ozeti(normal, "urun_turu", adlar),
        "ornek_urunler": _daginik_ornek(normal, "fiyat", 15),
    }


def _segment_ozetlerini_birlestir(ozetler: list[dict]) -> dict:
    sonuc = {}
    for segment in ("dusuk", "orta", "luks"):
        degerler = [o.get("segmentler", {}).get(segment) for o in ozetler]
        degerler = [d for d in degerler if d]
        if degerler:
            sonuc[segment] = {
                "min": min(d["min"] for d in degerler),
                "medyan": round(statistics.median(d["medyan"] for d in degerler), 2),
                "max": max(d["max"] for d in degerler),
                "urun_sayisi": sum(d["urun_sayisi"] for d in degerler),
                "kaynak_sayisi": len(degerler),
            }
    return sonuc


def birim_fiyatlarini_birlestir(kayitlar: list[dict]) -> dict:
    sonuc = {}
    for birim in ("kg", "litre", "adet"):
        ozetler = [k.get("birim_fiyatlari", {}).get(birim) for k in kayitlar]
        ozetler = [o for o in ozetler if o and o.get("eslesen_urun")]
        if not ozetler:
            continue
        ornekler = []
        for kayit in kayitlar:
            ozet = kayit.get("birim_fiyatlari", {}).get(birim) or {}
            ornekler.extend({**o, "site": kayit.get("site")} for o in ozet.get("ornek_urunler", []))
        sonuc[birim] = {
            "etiket": BIRIM_ADLARI[birim],
            "genel_medyan": round(statistics.median(o["genel_medyan"] for o in ozetler), 2),
            "eslesen_urun": sum(o["eslesen_urun"] for o in ozetler),
            "toplam_urun": sum(o.get("toplam_urun", 0) for o in ozetler),
            "kaynak_sayisi": len(ozetler),
            "segmentler": _segment_ozetlerini_birlestir(ozetler),
            "ornek_urunler": _daginik_ornek(ornekler, "birim_fiyat", 12),
        }
        toplam = sonuc[birim]["toplam_urun"]
        sonuc[birim]["eslesme_orani"] = round(sonuc[birim]["eslesen_urun"] / toplam, 3) if toplam else 0
    return sonuc


def _nitelik_gruplarini_birlestir(kayitlar: list[dict], bolum: str) -> dict:
    anahtarlar = sorted({
        anahtar
        for kayit in kayitlar
        for anahtar in (kayit.get("ozellik_ozeti", {}).get(bolum) or {})
    })
    sonuc = {}
    for anahtar in anahtarlar:
        ozetler = [k.get("ozellik_ozeti", {}).get(bolum, {}).get(anahtar) for k in kayitlar]
        ozetler = [o for o in ozetler if o and o.get("urun_sayisi")]
        if not ozetler:
            continue
        sonuc[anahtar] = {
            "ad": ozetler[0]["ad"],
            "genel_medyan": round(statistics.median(o["genel_medyan"] for o in ozetler)),
            "urun_sayisi": sum(o["urun_sayisi"] for o in ozetler),
            "kaynak_sayisi": len(ozetler),
            "segmentler": _segment_ozetlerini_birlestir(ozetler),
        }
    return sonuc


def ozellik_ozetlerini_birlestir(kayitlar: list[dict]) -> dict:
    ozetli = [k for k in kayitlar if k.get("ozellik_ozeti")]
    if not ozetli:
        return {}
    sonuc = {
        "toplam_urun": sum(k["ozellik_ozeti"].get("toplam_urun", 0) for k in ozetli),
        "ozellik_eslesen_urun": sum(k["ozellik_ozeti"].get("ozellik_eslesen_urun", 0) for k in ozetli),
        "kaynak_sayisi": len(ozetli),
    }
    for bolum in ("urun_turleri", "markalar", "enerji_siniflari", "ozellikler"):
        gruplar = _nitelik_gruplarini_birlestir(ozetli, bolum)
        if gruplar:
            sonuc[bolum] = gruplar
    kapasite = [k["ozellik_ozeti"]["kapasite_litre"] for k in ozetli
                if k["ozellik_ozeti"].get("kapasite_litre")]
    if kapasite:
        sonuc["kapasite_litre"] = {
            "min": min(k["min"] for k in kapasite),
            "medyan": round(statistics.median(k["medyan"] for k in kapasite)),
            "max": max(k["max"] for k in kapasite),
            "urun_sayisi": sum(k["urun_sayisi"] for k in kapasite),
            "kaynak_sayisi": len(kapasite),
        }
    ornekler = []
    for kayit in ozetli:
        ornekler.extend({**o, "site": kayit.get("site")}
                        for o in kayit["ozellik_ozeti"].get("ornek_urunler", []))
    sonuc["ornek_urunler"] = _daginik_ornek(ornekler, "fiyat", 20)
    return sonuc
