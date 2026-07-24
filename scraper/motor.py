# -*- coding: utf-8 -*-
"""
maliyetine.com - Fiyat Endeksi Kazima Motoru (v0.6)

Tek motor + kaynak kaydi (kaynaklar.yaml). Yeni site eklemek kod
yazmak degil, kaynaklar.yaml'a birkac satir eklemektir.

Uc katmanli cikarim stratejisi (sirayla, ilk basarili katman kullanilir):
  1. JSON-LD (schema.org/Product)
  2. Microdata / meta etiketleri (itemprop, og:price)
  3. Kaynaga ozel CSS secicileri (kaynaklar.yaml -> css_secicileri)

Guvenlik katmanlari:
  - robots.txt her URL icin otomatik kontrol edilir (protego kutuphanesi -
    stdlib urllib.robotparser KASITLI KULLANILMIYOR, bkz. asagidaki not).
    RET cikan URL atlanir ve loglanir.
  - Saglik kontrolu: bir kaynagin gecmis ortalamasina gore bu ayki urun
    sayisi cok dusukse (esik: ortalamanin %30'u), veri SESSIZCE kabul
    edilmez - "karantina" klasorune yazilir ve uyari basilir.
  - Nazik kazima: gercekci User-Agent, istekler arasi bekleme, basarisiz
    istekte exponential backoff ile yeniden deneme.
  - Bazi siteler (Akakce, Trendyol - 2026-07-24'te dogrulandi) tam
    tarayici basliklariyla bile `requests` istegini 403 ile reddediyor
    (muhtemelen TLS parmak izi tabanli tespit). Bu kaynaklar icin
    kaynaklar.yaml'da "render_gerekli: true" isaretlenir, motor gercek
    bir Chromium ile ceker (bkz. getir_playwright()).

Kullanim:
  pip install -r requirements.txt
  playwright install chromium       # sadece render_gerekli:true kaynaklar icin gerekli
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

import requests
import yaml
from bs4 import BeautifulSoup
from protego import Protego

BASE_DIR = Path(__file__).parent
VARSAYILAN_KAYNAKLAR = BASE_DIR / "kaynaklar.yaml"
VARSAYILAN_CIKTI = BASE_DIR / "veri"
GECMIS_DOSYA = BASE_DIR / "kaynak_gecmisi.json"

USER_AGENT_TARAYICI = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
USER_AGENT_ROBOTS = "maliyetine-bot"
# Sadece User-Agent yetmiyor: Akakce gibi WAF/bot-korumali siteler eksik
# tarayici basliklarina (Accept, Sec-Fetch-*, vb.) bakip 403 donebiliyor.
# Bu, gercek bir tarayicinin GET istegiyle gonderdigi basliklara olabildigince
# yaklasir - ama TLS parmak izi tabanli korumaya karsi yeterli olmayabilir,
# o durumda Playwright gerekir (bkz. CLAUDE.md).
HEADERS = {
    "User-Agent": USER_AGENT_TARAYICI,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    # DIKKAT: Accept-Encoding'i BILEREK burada BELIRTMIYORUZ. Once
    # "gzip, deflate, br" olarak sabitlenmisti - bu sunucuya "brotli'yi de
    # cozebilirim" diyordu ama `requests`/urllib3 brotli decoder'i
    # KURULU DEGILSE gelen br-sikistirilmis yaniti cozemiyor, r.text
    # cop/anlamsiz karakterlere donusuyor (Yavuz'un Ramsey/Atasay/Armut/
    # DugunBuketi testlerinde 2026-07-24'te tam olarak bu goruldu - "0
    # urun" aslinda CSS secici eksikligi degil, hic okunamayan bozuk
    # veriydi). `requests` bu basligi biz vermezsek KENDI KURULU
    # decoder'larina gore doğru ve guvenli sekilde otomatik olusturur.
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
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
#
# stdlib urllib.robotparser KASITLI KULLANILMIYOR - gercek sitelere karsi
# test ederken (Akakce) 3 ayri hata bulundu:
#   1. RobotFileParser.read() robots.txt'i varsayilan urllib User-Agent'i
#      ("Python-urllib/x.y") ile ceker - bircok sitenin bot korumasi bunu
#      403 ile reddediyor, read() de bunu "disallow_all=True" yani TUM
#      URL'leri RET olarak yorumluyor (site aslinda izin veriyor olsa bile).
#   2. parse() ayni User-agent grubuna ait birden fazla "User-agent:"
#      satiriyla onlari takip eden kurallar arasinda BOS SATIR varsa
#      o grubun TUMUNU sessizce dusuruyor (Akakce'nin robots.txt formati
#      tam olarak bu sekilde).
#   3. Disallow/Allow desenlerinde "*" joker karakterini HIC desteklemiyor
#      - "Disallow: /moda/*" harfi harfine "/moda/*" dizesini ariyor,
#      pratikte hicbir gercek URL'de eslesmiyor (kural sessizce etkisiz
#      kaliyor).
# `protego` (Scrapy'nin bagimliligi, Google'in robots.txt RFC 9309'unu
# dogru uyguluyor: joker karakter, coklu User-agent grubu, en-spesifik-
# kural-kazanir onceligi) bu ucunu de dogru cozuyor - gercek robots.txt
# metniyle karsilastirmali test edilip dogrulandi.
# ----------------------------------------------------------
_robots_onbellek: dict[str, Protego | None] = {}


def _robots_txt_getir(domain: str) -> Protego | None:
    robots_url = f"{domain}/robots.txt"
    try:
        yanit = requests.get(robots_url, headers=HEADERS, timeout=10)
    except requests.RequestException as e:
        logger.warning("robots.txt okunamadi (%s): %s - ihtiyatla RET kabul ediliyor", domain, e)
        return None

    if yanit.status_code in (401, 403):
        # Standart konvansiyon (RobotFileParser'in da izledigi): erisim
        # yasagi = ihtiyatla TUM URL'leri RET kabul et.
        return Protego.parse("User-agent: *\nDisallow: /")
    if 400 <= yanit.status_code < 500:
        # robots.txt yok (404 vb.) = konvansiyon geregi tum URL'lere izin var.
        return Protego.parse("User-agent: *\nAllow: /")
    if yanit.status_code >= 500:
        logger.warning(
            "robots.txt sunucu hatasi (%s): HTTP %d - ihtiyatla RET kabul ediliyor",
            domain, yanit.status_code,
        )
        return None

    return Protego.parse(yanit.text)


def robots_izin_var(url: str, user_agent: str = USER_AGENT_ROBOTS) -> bool:
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    if domain not in _robots_onbellek:
        _robots_onbellek[domain] = _robots_txt_getir(domain)

    rp = _robots_onbellek[domain]
    if rp is None:
        return False
    return rp.can_fetch(url, user_agent)


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
# PLAYWRIGHT - gercek tarayici motoru (TLS parmak izi / WAF korumasi
# olan siteler icin son care). `requests` + tam tarayici basliklari
# yetmedigi durumda (Akakce, Trendyol - 2026-07-24'te dogrulandi)
# kullanilir. kaynaklar.yaml'da "render_gerekli: true" ile secilir.
#
# Bir kerelik kurulum gerekir (pip'e ek olarak):
#   playwright install chromium
# Not: bazi onceden-kurulu ortamlarda (ör. bu gelistirme sandbox'i)
# PLAYWRIGHT_BROWSERS_PATH farkli bir Chromium revizyonu iceriyor olabilir
# ve pip'in kurdugu playwright surumuyle eslesmeyebilir - bu durumda
# `_ONCEDEN_KURULU_CHROMIUM` yolundaki tarayici acikca kullanilir.
# ----------------------------------------------------------
_ONCEDEN_KURULU_CHROMIUM = Path("/opt/pw-browsers/chromium")


def getir_playwright(url: str, deneme: int = 2, ilk_bekleme: float = 2.0):
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error(
            "playwright kurulu degil - 'pip install playwright && "
            "playwright install chromium' calistirilmali"
        )
        return None

    launch_ayarlari = {"headless": True}
    if _ONCEDEN_KURULU_CHROMIUM.exists():
        launch_ayarlari["executable_path"] = str(_ONCEDEN_KURULU_CHROMIUM)

    bekleme = ilk_bekleme
    for i in range(1, deneme + 1):
        try:
            with sync_playwright() as p:
                tarayici = p.chromium.launch(**launch_ayarlari)
                try:
                    sayfa = tarayici.new_page(
                        user_agent=USER_AGENT_TARAYICI,
                        extra_http_headers={"Accept-Language": HEADERS["Accept-Language"]},
                    )
                    sayfa.goto(url, timeout=30_000, wait_until="domcontentloaded")
                    # SPA/JS ile render edilen siteler icin: domcontentloaded
                    # cok erken tetiklenir (urun listesi henuz JS ile
                    # doldurulmadan). Sabit bir bekleme ile hydration'in
                    # oturmasina izin ver. 2500ms bazen yetmedi (Trendyol/
                    # davetiye ayni sablonu kullandigi halde 0 urun donmustu,
                    # ayni sayfa sayfa_tani.py ile hemen sonra tekrar
                    # cekildiginde dolu geldi - zamanlama/flakiness sorunu) -
                    # 4000ms'e cikarildi.
                    sayfa.wait_for_timeout(4000)
                    return sayfa.content()
                finally:
                    tarayici.close()
        except PlaywrightError as e:
            logger.warning("Playwright deneme %d/%d basarisiz (%s): %s", i, deneme, url, e)
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
# TEK YAML GIRDISI ICIN HAM VERI TOPLAMA (temizleme/segmentleme YOK -
# o "site" grubu seviyesinde yapilir, cok kaynak birlestirmesi icin)
# ----------------------------------------------------------
def kaynak_ham_veri_topla(kaynak: dict):
    ad = kaynak["ad"]
    sayfa_sayisi = kaynak.get("sayfa_sayisi", 1)
    bekleme_sn = kaynak.get("bekleme_sn", 2)
    tum_urunler = []
    kullanilan_katmanlar = set()

    for p in range(1, sayfa_sayisi + 1):
        url = kaynak["url"].format(page=p) if "{page}" in kaynak["url"] else kaynak["url"]

        if not robots_izin_var(url):
            logger.warning("[%s] robots.txt RET: %s - atlaniyor", ad, url)
            continue

        html = getir_playwright(url) if kaynak.get("render_gerekli") else getir(url)
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

    return tum_urunler, kullanilan_katmanlar


# ----------------------------------------------------------
# COK KAYNAK KURALI: yaml girdilerini (vertikal, kalem, site) bazinda
# grupla. Ayni "site" degerine sahip birden fazla girdi (ör. Akakce'nin
# 5 alt kategorisi) TEK bagimsiz kaynak sayilir.
# ----------------------------------------------------------
def gruplar_halinde_topla(kaynaklar: list[dict]):
    gruplar: dict[tuple[str, str, str], dict] = {}
    for kaynak in kaynaklar:
        if not kaynak.get("aktif", True):
            logger.info("[%s] pasif, atlaniyor", kaynak["ad"])
            continue

        urunler, katmanlar = kaynak_ham_veri_topla(kaynak)
        anahtar = (kaynak["vertikal"], kaynak["kalem"], kaynak["site"])
        grup = gruplar.setdefault(
            anahtar, {"urunler": [], "katmanlar": set(), "kaynak_adlari": []}
        )
        grup["urunler"].extend(urunler)
        grup["katmanlar"] |= katmanlar
        grup["kaynak_adlari"].append(kaynak["ad"])
    return gruplar


# ----------------------------------------------------------
# TEK SITE GRUBUNU ISLEME (temizleme + segmentleme + saglik kontrolu + kayit)
# ----------------------------------------------------------
def grup_isle(vertikal: str, kalem: str, site: str, grup: dict, gecmis: dict, cikti_kok: Path) -> dict:
    gecmis_anahtari = f"{vertikal}/{kalem}/{site}"

    temiz = aykiri_temizle(grup["urunler"])
    urun_sayisi = len(temiz)

    saglikli, ortalama = saglik_kontrolu(gecmis_anahtari, urun_sayisi, gecmis)

    if not saglikli:
        logger.warning(
            "[%s] SAGLIK KONTROLU BASARISIZ: %d urun (ortalama %.0f) - KARANTINAYA ALINDI",
            gecmis_anahtari, urun_sayisi, ortalama,
        )
        hedef_klasor = cikti_kok / "karantina"
    else:
        hedef_klasor = cikti_kok / vertikal
    hedef_klasor.mkdir(parents=True, exist_ok=True)

    genel_medyan = round(statistics.median(u["fiyat"] for u in temiz)) if temiz else None

    ozet = {
        "site": site,
        "kaynak_adlari": grup["kaynak_adlari"],
        "kalem": kalem,
        "vertikal": vertikal,
        "tarih": date.today().isoformat(),
        "toplam_urun": urun_sayisi,
        "saglikli": saglikli,
        "kullanilan_katmanlar": sorted(grup["katmanlar"]),
        "genel_medyan": genel_medyan,
        "segmentler": segmentle(temiz),
    }

    dosya = hedef_klasor / f"{kalem}_{ad_slug(site)}_{date.today().isoformat()}.json"
    dosya.write_text(json.dumps(ozet, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("[%s/%s] kaydedildi: %s", kalem, site, dosya)

    gecmis_guncelle(gecmis, gecmis_anahtari, urun_sayisi)
    return ozet


# ----------------------------------------------------------
# CAPRAZ DOGRULAMA - ayni (vertikal, kalem) icin >=2 bagimsiz saglikli
# site varsa genel medyanlarini karsilastirir. Fark esik_orani'ni
# asarsa uyari (CLAUDE.md "COK KAYNAK KURALI": esik %30).
# ----------------------------------------------------------
CAPRAZ_DOGRULAMA_ESIGI = 0.30


def capraz_dogrula(sonuclar: list[dict], cikti_kok: Path, esik_oran: float = CAPRAZ_DOGRULAMA_ESIGI):
    by_kalem: dict[tuple[str, str], list[dict]] = {}
    for s in sonuclar:
        if not s["saglikli"] or s["genel_medyan"] is None:
            continue
        by_kalem.setdefault((s["vertikal"], s["kalem"]), []).append(s)

    raporlar = []
    for (vertikal, kalem), grup in by_kalem.items():
        if len(grup) < 2:
            continue  # tek bagimsiz kaynak varsa capraz dogrulama yapilamaz

        medyanlar = {s["site"]: s["genel_medyan"] for s in grup}
        en_dusuk = min(medyanlar.values())
        en_yuksek = max(medyanlar.values())
        fark_orani = (en_yuksek - en_dusuk) / en_dusuk if en_dusuk else 0.0
        uyari = fark_orani > esik_oran

        if uyari:
            logger.warning(
                "[%s/%s] CAPRAZ DOGRULAMA UYARISI: siteler arasi fark %%%.0f (%s)",
                vertikal, kalem, fark_orani * 100, medyanlar,
            )
        else:
            logger.info(
                "[%s/%s] capraz dogrulama OK: fark %%%.0f (%s)",
                vertikal, kalem, fark_orani * 100, medyanlar,
            )

        rapor = {
            "vertikal": vertikal,
            "kalem": kalem,
            "tarih": date.today().isoformat(),
            "site_medyanlari": medyanlar,
            "fark_orani": round(fark_orani, 3),
            "esik_orani": esik_oran,
            "uyari": uyari,
        }
        raporlar.append(rapor)

        klasor = cikti_kok / vertikal
        klasor.mkdir(parents=True, exist_ok=True)
        dosya = klasor / f"{kalem}_capraz-dogrulama_{date.today().isoformat()}.json"
        dosya.write_text(json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")

    return raporlar


# ----------------------------------------------------------
# CALISTIR
# ----------------------------------------------------------
def calistir(
    kaynaklar_dosyasi: Path = VARSAYILAN_KAYNAKLAR,
    cikti_kok: Path = VARSAYILAN_CIKTI,
    gecmis_dosyasi: Path = GECMIS_DOSYA,
):
    veri = yaml.safe_load(kaynaklar_dosyasi.read_text(encoding="utf-8"))
    kaynaklar = veri.get("kaynaklar", [])

    gecmis = gecmisi_yukle(gecmis_dosyasi)
    gruplar = gruplar_halinde_topla(kaynaklar)

    sonuclar = [
        grup_isle(vertikal, kalem, site, grup, gecmis, cikti_kok)
        for (vertikal, kalem, site), grup in gruplar.items()
    ]
    gecmisi_kaydet(gecmis, gecmis_dosyasi)

    capraz_raporlar = capraz_dogrula(sonuclar, cikti_kok)

    saglikli_sayisi = sum(1 for s in sonuclar if s["saglikli"])
    uyarili_kalem_sayisi = sum(1 for r in capraz_raporlar if r["uyari"])
    logger.info(
        "== Bitti: %d kaynak-grubu islendi, %d saglikli, %d karantinada, "
        "%d kalemde capraz dogrulama uyarisi ==",
        len(sonuclar), saglikli_sayisi, len(sonuclar) - saglikli_sayisi, uyarili_kalem_sayisi,
    )
    return sonuclar, capraz_raporlar


def main():
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument("--kaynaklar", type=Path, default=VARSAYILAN_KAYNAKLAR)
    ayristirici.add_argument("--cikti", type=Path, default=VARSAYILAN_CIKTI)
    ayristirici.add_argument(
        "--gecmis", type=Path, default=GECMIS_DOSYA,
        help="saglik kontrolu gecmis dosyasi - test/deneme calistirmalarinda "
             "gercek kaynak_gecmisi.json'u kirletmemek icin ayri bir yol verilebilir",
    )
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
    calistir(args.kaynaklar, args.cikti, args.gecmis)


if __name__ == "__main__":
    main()
