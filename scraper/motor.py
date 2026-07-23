# -*- coding: utf-8 -*-
"""
maliyetine.com - Fiyat Endeksi Kazima Motoru (v0.3)

Tek motor + kaynak kaydi (kaynaklar.yaml). Yeni site eklemek kod
yazmak degil, kaynaklar.yaml'a birkac satir eklemektir.

Uc katmanli cikarim stratejisi (sirayla, ilk basarili katman kullanilir):
  1. JSON-LD (schema.org/Product)
  2. Microdata / meta etiketleri (itemprop, og:price)
  3. Kaynaga ozel CSS secicileri (kaynaklar.yaml -> css_secicileri)

Guvenlik katmanlari:
  - robots.txt her URL icin otomatik kontrol edilir (urllib.robotparser).
    RET cikan URL atlanir ve loglanir.
  - Saglik kontrolu: bir kaynagin gecmis ortalamasina gore bu ayki urun
    sayisi cok dusukse (esik: ortalamanin %30'u), veri SESSIZCE kabul
    edilmez - "karantina" klasorune yazilir ve uyari basilir.
  - Nazik kazima: gercekci User-Agent, istekler arasi bekleme, basarisiz
    istekte exponential backoff ile yeniden deneme.

Kullanim:
  pip install -r requirements.txt
  python motor.py                  # kaynaklar.yaml'daki tum aktif kaynaklari isler
  python motor.py --kaynaklar test_kaynaklari.yaml --cikti /tmp/deneme
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import statistics
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
import yaml
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent
VARSAYILAN_KAYNAKLAR = BASE_DIR / "kaynaklar.yaml"
VARSAYILAN_CIKTI = BASE_DIR / "veri"
GECMIS_DOSYA = BASE_DIR / "kaynak_gecmisi.json"

USER_AGENT_TARAYICI = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
USER_AGENT_ROBOTS = "maliyetine-bot"
HEADERS = {
    "User-Agent": USER_AGENT_TARAYICI,
    "Accept-Language": "tr-TR,tr;q=0.9",
}

logger = logging.getLogger("maliyetine.motor")


# ----------------------------------------------------------
# FIYAT TEMIZLEME - "45.999,00 TL" -> 45999.0
# ----------------------------------------------------------
def fiyat_ayikla(metin: str):
    if not metin:
        return None
    metin = metin.replace("TL", "").replace("₺", "").strip()
    metin = metin.replace(".", "").replace(",", ".")
    sayilar = re.findall(r"\d+(?:\.\d+)?", metin)
    return float(sayilar[0]) if sayilar else None


def ad_slug(ad: str) -> str:
    cevrim = str.maketrans("çÇğĞıİöÖşŞüÜ", "cCgGiIoOsSuU")
    s = ad.translate(cevrim).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "kaynak"


# ----------------------------------------------------------
# KATMAN 1: JSON-LD (schema.org/Product)
# ----------------------------------------------------------
def _json_ld_duzlestir(veri):
    if isinstance(veri, list):
        for v in veri:
            yield from _json_ld_duzlestir(v)
    elif isinstance(veri, dict):
        if "@graph" in veri:
            yield from _json_ld_duzlestir(veri["@graph"])
        elif "itemListElement" in veri:
            yield from _json_ld_duzlestir(veri["itemListElement"])
        elif veri.get("@type") == "ListItem" and "item" in veri:
            yield from _json_ld_duzlestir(veri["item"])
        else:
            yield veri


def _json_ld_urun_mu(obj: dict) -> bool:
    tip = obj.get("@type")
    if isinstance(tip, list):
        return "Product" in tip
    return tip == "Product"


def _json_ld_fiyat(obj: dict):
    offers = obj.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else None
    if isinstance(offers, dict):
        ham = offers.get("price") or offers.get("lowPrice")
        if ham is not None:
            try:
                return float(str(ham).replace(",", "."))
            except ValueError:
                return None
    return None


def json_ld_urunler(soup: BeautifulSoup, min_fiyat: float):
    urunler = []
    for etiket in soup.find_all("script", type="application/ld+json"):
        try:
            veri = json.loads(etiket.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for obj in _json_ld_duzlestir(veri):
            if not isinstance(obj, dict) or not _json_ld_urun_mu(obj):
                continue
            isim = obj.get("name")
            fiyat = _json_ld_fiyat(obj)
            if isim and fiyat and fiyat > min_fiyat:
                urunler.append({"isim": str(isim).strip(), "fiyat": fiyat})
    return urunler


# ----------------------------------------------------------
# KATMAN 2: Microdata / meta etiketleri
# ----------------------------------------------------------
def microdata_urunler(soup: BeautifulSoup, min_fiyat: float):
    urunler = []
    for kapsayici in soup.select('[itemtype*="schema.org/Product"]'):
        isim_el = kapsayici.select_one('[itemprop="name"]')
        fiyat_el = kapsayici.select_one('[itemprop="price"], [itemprop="lowPrice"]')
        if not (isim_el and fiyat_el):
            continue
        isim = isim_el.get("content") or isim_el.get_text(strip=True)
        fiyat_metni = fiyat_el.get("content") or fiyat_el.get_text(strip=True)
        f = fiyat_ayikla(fiyat_metni)
        if isim and f and f > min_fiyat:
            urunler.append({"isim": isim.strip(), "fiyat": f})

    if urunler:
        return urunler

    # Tek urun sayfalari icin og/product meta etiketi yedegi
    isim_meta = soup.select_one('meta[property="og:title"]')
    fiyat_meta = soup.select_one(
        'meta[property="product:price:amount"], meta[property="og:price:amount"]'
    )
    if isim_meta and fiyat_meta:
        isim = isim_meta.get("content")
        f = fiyat_ayikla(fiyat_meta.get("content", ""))
        if isim and f and f > min_fiyat:
            urunler.append({"isim": isim.strip(), "fiyat": f})
    return urunler


# ----------------------------------------------------------
# KATMAN 3: Kaynaga ozel CSS secicileri (son care)
# ----------------------------------------------------------
def css_urunler(soup: BeautifulSoup, css_secicileri: dict | None, min_fiyat: float):
    if not css_secicileri:
        return []
    urunler = []
    for kart in soup.select(css_secicileri["urun_karti"]):
        isim_el = kart.select_one(css_secicileri["isim_secici"])
        fiyat_el = kart.select_one(css_secicileri["fiyat_secici"])
        if not (isim_el and fiyat_el):
            continue
        f = fiyat_ayikla(fiyat_el.get_text())
        if f and f > min_fiyat:
            urunler.append({"isim": isim_el.get_text(strip=True), "fiyat": f})
    return urunler


def uc_katman_cikar(soup: BeautifulSoup, kaynak: dict):
    min_fiyat = kaynak.get("min_fiyat", 100)

    urunler = json_ld_urunler(soup, min_fiyat)
    if urunler:
        return urunler, "json-ld"

    urunler = microdata_urunler(soup, min_fiyat)
    if urunler:
        return urunler, "microdata"

    urunler = css_urunler(soup, kaynak.get("css_secicileri"), min_fiyat)
    if urunler:
        return urunler, "css"

    return [], "hicbiri"


# ----------------------------------------------------------
# ROBOTS.TXT - otomatik dogrulama (domain basina onbellekli)
# ----------------------------------------------------------
_robots_onbellek: dict[str, RobotFileParser | None] = {}


def robots_izin_var(url: str, user_agent: str = USER_AGENT_ROBOTS) -> bool:
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    if domain not in _robots_onbellek:
        rp = RobotFileParser()
        rp.set_url(f"{domain}/robots.txt")
        try:
            rp.read()
            _robots_onbellek[domain] = rp
        except Exception as e:
            logger.warning("robots.txt okunamadi (%s): %s - ihtiyatla RET kabul ediliyor", domain, e)
            _robots_onbellek[domain] = None

    rp = _robots_onbellek[domain]
    if rp is None:
        return False
    return rp.can_fetch(user_agent, url)


# ----------------------------------------------------------
# HTTP - retry + exponential backoff
# ----------------------------------------------------------
def getir(url: str, deneme: int = 3, ilk_bekleme: float = 2.0):
    bekleme = ilk_bekleme
    for i in range(1, deneme + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            logger.warning("Deneme %d/%d basarisiz (%s): %s", i, deneme, url, e)
            if i < deneme:
                time.sleep(bekleme)
                bekleme *= 2
    return None


# ----------------------------------------------------------
# AYKIRI DEGER TEMIZLIGI (IQR yontemi)
# ----------------------------------------------------------
def aykiri_temizle(urunler):
    fiyatlar = sorted(u["fiyat"] for u in urunler)
    n = len(fiyatlar)
    if n < 20:
        return urunler
    q1 = fiyatlar[n // 4]
    q3 = fiyatlar[(3 * n) // 4]
    iqr = q3 - q1
    alt, ust = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return [u for u in urunler if alt <= u["fiyat"] <= ust]


# ----------------------------------------------------------
# SEGMENTLEME - dusuk / orta / luks (persentil bazli)
# ----------------------------------------------------------
def segmentle(urunler):
    if not urunler:
        return {}
    fiyatlar = sorted(u["fiyat"] for u in urunler)
    n = len(fiyatlar)
    p25, p75 = fiyatlar[n // 4], fiyatlar[(3 * n) // 4]

    seg = {"dusuk": [], "orta": [], "luks": []}
    for u in urunler:
        if u["fiyat"] <= p25:
            seg["dusuk"].append(u["fiyat"])
        elif u["fiyat"] <= p75:
            seg["orta"].append(u["fiyat"])
        else:
            seg["luks"].append(u["fiyat"])

    ozet = {}
    for ad, liste in seg.items():
        if liste:
            ozet[ad] = {
                "min": round(min(liste)),
                "medyan": round(statistics.median(liste)),
                "max": round(max(liste)),
                "urun_sayisi": len(liste),
            }
    return ozet


# ----------------------------------------------------------
# SAGLIK KONTROLU - gecmis calismalara gore anomali tespiti
# ----------------------------------------------------------
def gecmisi_yukle(dosya: Path = GECMIS_DOSYA) -> dict:
    if dosya.exists():
        return json.loads(dosya.read_text(encoding="utf-8"))
    return {}


def gecmisi_kaydet(gecmis: dict, dosya: Path = GECMIS_DOSYA) -> None:
    dosya.write_text(json.dumps(gecmis, ensure_ascii=False, indent=2), encoding="utf-8")


def saglik_kontrolu(ad: str, urun_sayisi: int, gecmis: dict, esik_oran: float = 0.3):
    """Onceki calismalarin ortalamasina gore anomali var mi kontrol eder.

    Ilk calistirmada (gecmis yoksa) her zaman saglikli kabul edilir -
    baseline burada olusur.
    """
    kayitlar = gecmis.get(ad, {}).get("urun_sayilari", [])
    if not kayitlar:
        return True, None
    ortalama = statistics.mean(kayitlar)
    if urun_sayisi < ortalama * esik_oran:
        return False, ortalama
    return True, ortalama


def gecmis_guncelle(gecmis: dict, ad: str, urun_sayisi: int, en_fazla_kayit: int = 12) -> None:
    kayit = gecmis.setdefault(ad, {"urun_sayilari": []})
    kayit["urun_sayilari"].append(urun_sayisi)
    kayit["urun_sayilari"] = kayit["urun_sayilari"][-en_fazla_kayit:]
    kayit["son_calisma"] = date.today().isoformat()


# ----------------------------------------------------------
# TEK KAYNAK ISLEME
# ----------------------------------------------------------
def kaynak_isle(kaynak: dict, gecmis: dict, cikti_kok: Path) -> dict | None:
    ad = kaynak["ad"]
    if not kaynak.get("aktif", True):
        logger.info("[%s] pasif, atlaniyor", ad)
        return None

    sayfa_sayisi = kaynak.get("sayfa_sayisi", 1)
    bekleme_sn = kaynak.get("bekleme_sn", 2)
    tum_urunler = []
    kullanilan_katmanlar = set()

    for p in range(1, sayfa_sayisi + 1):
        url = kaynak["url"].format(page=p) if "{page}" in kaynak["url"] else kaynak["url"]

        if not robots_izin_var(url):
            logger.warning("[%s] robots.txt RET: %s - atlaniyor", ad, url)
            continue

        html = getir(url)
        if html is None:
            logger.error("[%s] sayfa %d alinamadi (retry tukendi): %s", ad, p, url)
            continue

        soup = BeautifulSoup(html, "html.parser")
        urunler, katman = uc_katman_cikar(soup, kaynak)
        kullanilan_katmanlar.add(katman)
        logger.info("[%s] sayfa %d: %d urun (%s katmani)", ad, p, len(urunler), katman)
        tum_urunler.extend(urunler)

        if p < sayfa_sayisi:
            time.sleep(bekleme_sn)

    temiz = aykiri_temizle(tum_urunler)
    urun_sayisi = len(temiz)

    saglikli, ortalama = saglik_kontrolu(ad, urun_sayisi, gecmis)

    if not saglikli:
        logger.warning(
            "[%s] SAGLIK KONTROLU BASARISIZ: %d urun (ortalama %.0f) - KARANTINAYA ALINDI",
            ad, urun_sayisi, ortalama,
        )
        hedef_klasor = cikti_kok / "karantina"
    else:
        hedef_klasor = cikti_kok / kaynak["vertikal"]
    hedef_klasor.mkdir(parents=True, exist_ok=True)

    ozet = {
        "kaynak": ad,
        "kalem": kaynak["kalem"],
        "vertikal": kaynak["vertikal"],
        "tarih": date.today().isoformat(),
        "toplam_urun": urun_sayisi,
        "saglikli": saglikli,
        "kullanilan_katmanlar": sorted(kullanilan_katmanlar),
        "segmentler": segmentle(temiz),
    }

    dosya = hedef_klasor / f"{kaynak['kalem']}_{ad_slug(ad)}_{date.today().isoformat()}.json"
    dosya.write_text(json.dumps(ozet, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("[%s] kaydedildi: %s", ad, dosya)

    gecmis_guncelle(gecmis, ad, urun_sayisi)
    return ozet


# ----------------------------------------------------------
# CALISTIR
# ----------------------------------------------------------
def calistir(kaynaklar_dosyasi: Path = VARSAYILAN_KAYNAKLAR, cikti_kok: Path = VARSAYILAN_CIKTI):
    veri = yaml.safe_load(kaynaklar_dosyasi.read_text(encoding="utf-8"))
    kaynaklar = veri.get("kaynaklar", [])

    gecmis = gecmisi_yukle()
    sonuclar = []
    for kaynak in kaynaklar:
        sonuc = kaynak_isle(kaynak, gecmis, cikti_kok)
        if sonuc:
            sonuclar.append(sonuc)
    gecmisi_kaydet(gecmis)

    saglikli_sayisi = sum(1 for s in sonuclar if s["saglikli"])
    logger.info(
        "== Bitti: %d/%d kaynak islendi, %d saglikli, %d karantinada ==",
        len(sonuclar), len(kaynaklar), saglikli_sayisi, len(sonuclar) - saglikli_sayisi,
    )
    return sonuclar


def main():
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument("--kaynaklar", type=Path, default=VARSAYILAN_KAYNAKLAR)
    ayristirici.add_argument("--cikti", type=Path, default=VARSAYILAN_CIKTI)
    ayristirici.add_argument("--log-seviyesi", default="INFO")
    args = ayristirici.parse_args()

    logging.basicConfig(
        level=args.log_seviyesi,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(BASE_DIR / "kazima.log", encoding="utf-8"),
        ],
    )
    calistir(args.kaynaklar, args.cikti)


if __name__ == "__main__":
    main()
