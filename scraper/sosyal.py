# -*- coding: utf-8 -*-
"""
Maliyeti Ne? - Sosyal medya gonderisi uretici (v0.1)

NE ISE YARIYOR: her olcumden sonra (ayin 5'i ve 20'si) paylasilmaya DEGER
bir sey var mi diye veriye bakar, varsa gonderi metnini uretir.

--------------------------------------------------------------------
KIRMIZI CIZGI - asistan.py ile AYNI ILKE
--------------------------------------------------------------------
Metin URETILMIYOR, veriden KURULUYOR. Dil modeli yok, disari istek yok.
Cumleler sabit sablon; degisen yalnizca rakam, kalem adi, tarih ve
orneklem sayisi. Yani "gecen ay bebek arabasi fiyatlari firladi" gibi
bir cumleyi bu kod YAZAMAZ - soyleyebilecegi tek sey olctugu sey.

Sosyal medya bu ilkeyi kirmak icin en tehlikeli yer: dikkat cekmek icin
abartma basincinin en yuksek oldugu mecra. Bir kez "fiyatlar ucuyor"
diye atmaya baslarsak, sitenin tum guven iddiasi coker - ve o iddia
disinda satacak bir seyimiz yok.

--------------------------------------------------------------------
SUSMAK VARSAYILAN DAVRANIS
--------------------------------------------------------------------
Her olcumde gonderi ATILMAZ. Uc kapi var, ucu de gecilmezse cikti bos:

1. YETERLI ARALIK: gecmis.ASGARI_GUN_ARALIGI'ndan yakin iki olcum
   arasindaki fark "fiyat degisimi" degil orneklem gurultusudur.
   (24->25 Temmuz testinde "nikah sekeri %40 dustu" cikmisti; gercek
   bir dusus degil, kategori sayfasinda LISTELENEN urunlerin degismesi.)

2. ORNEKLEM KARARLILIGI: urun sayisi iki olcum arasinda cok degistiyse
   medyandaki oynama FIYATTAN degil, olculen kumeden geliyor olabilir.
   Boyle bir degisimi "fiyat %X artti" diye atmak yanlis olur.

3. ANLAMLI BUYUKLUK: %1'lik oynamayi haber gibi sunmak guven yakar.

Ucu de gecilirse bile gonderi sayisi sinirli (EN_FAZLA_GONDERI) - bir
olcumde 40 kalem degistiyse 40 tweet atmak spam'dir.

--------------------------------------------------------------------
GONDERME
--------------------------------------------------------------------
Varsayilan DENEME modu: hicbir yere gonderilmez, metinler dosyaya
yazilir (veri/sosyal/onizleme.md). Gercek gonderim yalnizca ilgili
ortam degiskenleri/secret'lar varsa yapilir - EVDS entegrasyonundaki
desenin aynisi. Anahtar yoksa adim sessizce atlanir.

Kullanim:
  python sosyal.py                     # deneme - yalnizca metin uretir
  python sosyal.py --gonder            # secret varsa gercekten paylasir
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path

import gecmis

BASE_DIR = Path(__file__).parent
SITE_KOK = BASE_DIR.parent
SITE_URL = "https://maliyetine.com.tr"

VARSAYILAN_GECMIS_KOK = SITE_KOK / "veri" / "gecmis"
VARSAYILAN_VERI_KOK = SITE_KOK / "veri"
ONIZLEME = SITE_KOK / "veri" / "sosyal" / "onizleme.md"

# Bir olcumde en fazla kac gonderi. 40 kalem degistiyse 40 gonderi spam olur.
EN_FAZLA_GONDERI = 3

# Bunun altindaki degisim paylasilmaz. %1'lik oynamayi haber gibi sunmak
# guven yakar; ayrica medyan tam sayiya yuvarlandigi icin cok kucuk
# degisimler yuvarlama kaynakli bile olabilir.
ASGARI_DEGISIM_YUZDE = 3.0

# Orneklem iki olcum arasinda bu orandan fazla degistiyse degisim
# paylasilmaz - medyan oynamasi fiyattan degil olculen kumeden geliyor
# olabilir ve hangisi oldugunu ayirt edemiyoruz.
AZAMI_ORNEKLEM_OYNAMASI = 0.35

# Karakter sinirlari: X 280, Bluesky 300. Dar olana gore yaziyoruz.
AZAMI_KARAKTER = 280


def _tr_sayi(n: float) -> str:
    return f"{round(n):,}".replace(",", ".")


def _vertikal_adlari() -> dict[str, dict]:
    import sayfa_uret as su
    return su.VERTIKALLER


def _kalem_adi(vertikal: str, kalem_id: str) -> str | None:
    """Kalem adini vertikal tanimindan alir. Bulunamazsa None - ham id'yi
    ("bebek-arabasi") gonderiye YAZMAYIZ; senaryo sayfalarinda tam bu hata
    yasandi ve tabloda ham id gorunuyordu."""
    conf = _vertikal_adlari().get(vertikal)
    if not conf:
        return None
    for k in list(conf["kalemler"]) + list(conf.get("tahmini_kalemler") or []):
        if k["id"] == kalem_id:
            return k["ad"]
    return None


def _kalem_url(vertikal: str, kalem_id: str) -> str:
    """Kalem sayfasi varsa ona, yoksa endekse baglar. Kirik link atmak,
    hic link atmamaktan kotu."""
    slug_yolu = SITE_KOK / vertikal / f"{kalem_id}-fiyatlari" / "index.html"
    if slug_yolu.exists():
        return f"{SITE_URL}/{vertikal}/{kalem_id}-fiyatlari/"
    return f"{SITE_URL}/{vertikal}/"


# ----------------------------------------------------------
# ADAY 1: gercek fiyat degisimi
# ----------------------------------------------------------
def degisim_adaylari(gecmis_kok: Path = VARSAYILAN_GECMIS_KOK) -> list[dict]:
    adaylar = []
    for vertikal in _vertikal_adlari():
        dosya = gecmis_kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        try:
            veri = json.loads(dosya.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        for kalem_id, kayit in (veri.get("kalemler") or {}).items():
            seri = kayit.get("seri") or []
            if len(seri) < 2:
                continue
            onceki, son = seri[-2], seri[-1]

            # KAPI 1: yeterli aralik (gecmis.py ile ayni esik - tek yerden)
            if gecmis._gun_farki(onceki["tarih"], son["tarih"]) < gecmis.ASGARI_GUN_ARALIGI:
                continue

            degisim = kayit.get("aylik_degisim_yuzde")
            if degisim is None:
                continue

            # KAPI 2: orneklem kararliligi
            o_urun, s_urun = onceki.get("urun") or 0, son.get("urun") or 0
            if not o_urun or abs(s_urun - o_urun) / o_urun > AZAMI_ORNEKLEM_OYNAMASI:
                continue

            # KAPI 3: anlamli buyukluk
            if abs(degisim) < ASGARI_DEGISIM_YUZDE:
                continue

            ad = _kalem_adi(vertikal, kalem_id)
            if not ad:
                continue

            adaylar.append({
                "tip": "degisim",
                "onem": abs(degisim),
                "vertikal": vertikal,
                "kalem_id": kalem_id,
                "metin": _degisim_metni(ad, degisim, son, onceki),
                "url": _kalem_url(vertikal, kalem_id),
            })
    adaylar.sort(key=lambda x: -x["onem"])
    return adaylar


def _degisim_metni(ad: str, degisim: float, son: dict, onceki: dict) -> str:
    yon = "arttı" if degisim > 0 else "azaldı"
    gun = gecmis._gun_farki(onceki["tarih"], son["tarih"])
    kaynak = son.get("kaynak") or 1
    kaynak_notu = f"{kaynak} kaynaktan" if kaynak > 1 else "tek kaynaktan"
    return (
        f"{ad} ortalama fiyatı {gun} günde %{abs(degisim):.1f} {yon}: "
        f"{_tr_sayi(onceki['medyan'])} TL → {_tr_sayi(son['medyan'])} TL.\n\n"
        f"{son.get('urun')} üründen, {kaynak_notu} ölçüldü ({son['tarih']})."
    )


# ----------------------------------------------------------
# ADAY 2: olcum ozeti (degisim yoksa bile soylenebilecek gercek sey)
# ----------------------------------------------------------
def olcum_ozeti(vertikal: str, veri_kok: Path = VARSAYILAN_VERI_KOK) -> dict | None:
    dosya = veri_kok / f"{vertikal}.json"
    if not dosya.exists():
        return None
    try:
        veri = json.loads(dosya.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    conf = _vertikal_adlari().get(vertikal)
    if not conf:
        return None

    kalemler = veri.get("kalemler") or {}
    tanimlar = {k["id"]: k for k in conf["kalemler"]}
    toplam, sayilan, urun, siteler = 0, 0, 0, set()
    for kid, k in kalemler.items():
        tanim = tanimlar.get(kid)
        if not tanim or tanim.get("varsayilan_dahil") is False:
            continue
        if tanim.get("bilgi_amacli"):
            continue
        orta = ((k.get("segmentler") or {}).get("orta") or {}).get("medyan")
        if not orta:
            continue
        carpan = conf.get("olcek_varsayilan", 1) if tanim.get("birim") == "kisi" else 1
        toplam += orta * carpan
        sayilan += 1
        for kaynak in k.get("kaynaklar") or []:
            urun += kaynak.get("toplam_urun") or 0
            if (kaynak.get("toplam_urun") or 0) > 0 and kaynak.get("site"):
                siteler.add(kaynak["site"])

    # Rakamsiz gonderi atmiyoruz.
    if not toplam or sayilan < 3:
        return None

    return {
        "tip": "ozet",
        "onem": 0,
        "vertikal": vertikal,
        "metin": (
            f"{conf['baslik']}\n\n"
            f"Orta segmentte {_tr_sayi(toplam)} TL. "
            f"{sayilan} kalem, {urun} ürün, {len(siteler)} bağımsız kaynak. "
            f"Ölçüm: {veri.get('olcum_tarihi') or date.today().isoformat()}."
        ),
        "url": f"{SITE_URL}/{vertikal}/",
    }


# ----------------------------------------------------------
# SECIM
# ----------------------------------------------------------
def ozet_vertikali_sec(bugun: date | None = None) -> str:
    """Ozet gonderisi icin vertikal secer - AYA GORE DONUSUMLU.

    Neden rotasyon: her ay ayni vertikalin ozetini atmak (ve zaman serisi
    olusana kadar bu aylarca surecek) hem tekrar hem gereksiz. Neden aya
    gore: durum tutmadan deterministik - ayni ay iki kez calistirilirsa
    ayni vertikal secilir, yani ard arda calistirma yeni bir gonderi
    uretmez.
    """
    vertikaller = list(_vertikal_adlari())
    ay = (bugun or date.today()).month
    return vertikaller[ay % len(vertikaller)]


def gonderiler(
    gecmis_kok: Path = VARSAYILAN_GECMIS_KOK,
    veri_kok: Path = VARSAYILAN_VERI_KOK,
    ozet_vertikali: str | None = None,
) -> list[dict]:
    """Bu olcumde paylasilacak gonderiler. Soylenecek gercek bir sey yoksa
    BOS LISTE doner - bu bir hata degil, tasarlanan davranis."""
    secilen = degisim_adaylari(gecmis_kok)[:EN_FAZLA_GONDERI]

    # Degisim yoksa tek bir ozet gonderisi atilabilir; ama bunu her olcumde
    # tekrarlamak da spam olur, o yuzden yalnizca acikca istenirse.
    if not secilen and ozet_vertikali:
        ozet = olcum_ozeti(ozet_vertikali, veri_kok)
        if ozet:
            secilen = [ozet]

    for g in secilen:
        g["tam_metin"] = f"{g['metin']}\n{g['url']}"
        if len(g["tam_metin"]) > AZAMI_KARAKTER:
            # Kirpmak yerine kaynak notunu atiyoruz - rakam ve kaynak sayisi
            # gonderinin ASIL icerigi, once onlar korunur.
            g["tam_metin"] = g["tam_metin"][:AZAMI_KARAKTER - 1].rstrip() + "…"
    return secilen


# ----------------------------------------------------------
# GONDERME - anahtar yoksa sessizce atlanir
# ----------------------------------------------------------
def x_gonder(metin: str) -> bool:
    anahtarlar = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")
    if not all(os.environ.get(a) for a in anahtarlar):
        return False
    try:
        from requests_oauthlib import OAuth1Session
    except ImportError:
        print("requests_oauthlib kurulu degil - X gonderimi atlandi.")
        return False
    oturum = OAuth1Session(
        os.environ["X_API_KEY"], os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"],
    )
    yanit = oturum.post("https://api.twitter.com/2/tweets", json={"text": metin})
    if yanit.status_code >= 300:
        print(f"X hatasi {yanit.status_code}: {yanit.text[:200]}")
        return False
    return True


def bluesky_gonder(metin: str) -> bool:
    kimlik, sifre = os.environ.get("BLUESKY_HANDLE"), os.environ.get("BLUESKY_SIFRE")
    if not (kimlik and sifre):
        return False
    import requests
    tmpl = "https://bsky.social/xrpc/"
    oturum = requests.post(tmpl + "com.atproto.server.createSession",
                           json={"identifier": kimlik, "password": sifre}, timeout=20)
    if oturum.status_code >= 300:
        print(f"Bluesky oturum hatasi {oturum.status_code}")
        return False
    jeton = oturum.json()
    yanit = requests.post(
        tmpl + "com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {jeton['accessJwt']}"},
        json={
            "repo": jeton["did"],
            "collection": "app.bsky.feed.post",
            "record": {
                "$type": "app.bsky.feed.post",
                "text": metin,
                "createdAt": f"{date.today().isoformat()}T09:00:00Z",
                "langs": ["tr"],
            },
        },
        timeout=20,
    )
    if yanit.status_code >= 300:
        print(f"Bluesky hatasi {yanit.status_code}: {yanit.text[:200]}")
        return False
    return True


def onizleme_yaz(gonderi_listesi: list[dict], hedef: Path = ONIZLEME) -> Path:
    hedef.parent.mkdir(parents=True, exist_ok=True)
    satirlar = [f"# Sosyal medya önizleme — {date.today().isoformat()}", ""]
    if not gonderi_listesi:
        satirlar += [
            "Bu ölçümde paylaşılacak bir şey yok.", "",
            "Sebep: yeterince uzak iki ölçüm arasında, örneklemi kararlı ve "
            f"%{ASGARI_DEGISIM_YUZDE:g}'ten büyük bir değişim bulunamadı. "
            "Susmak varsayılan davranış.",
        ]
    for i, g in enumerate(gonderi_listesi, 1):
        satirlar += [f"## {i}. ({g['tip']}, {len(g['tam_metin'])} karakter)", "",
                     "```", g["tam_metin"], "```", ""]
    hedef.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    return hedef


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--gonder", action="store_true",
                   help="gercekten paylas (secret yoksa yine atlanir)")
    a.add_argument("--ozet-vertikali", default=None,
                   help="degisim yoksa bu vertikalin olcum ozetini paylas")
    a.add_argument("--gecmis-kok", type=Path, default=VARSAYILAN_GECMIS_KOK)
    a.add_argument("--veri-kok", type=Path, default=VARSAYILAN_VERI_KOK)
    args = a.parse_args()

    ozet = args.ozet_vertikali
    if ozet == "auto":
        ozet = ozet_vertikali_sec()
        print(f"Ozet vertikali (ay bazli rotasyon): {ozet}")

    liste = gonderiler(args.gecmis_kok, args.veri_kok, ozet)
    yol = onizleme_yaz(liste)
    print(f"{len(liste)} gonderi adayi -> {yol}")
    for g in liste:
        print("-" * 60)
        print(g["tam_metin"])
    if not liste:
        return 0

    if not args.gonder:
        print("\n(deneme modu - hicbir yere gonderilmedi)")
        return 0

    for g in liste:
        x = x_gonder(g["tam_metin"])
        b = bluesky_gonder(g["tam_metin"])
        print(f"X: {'gonderildi' if x else 'atlandi'} | Bluesky: {'gonderildi' if b else 'atlandi'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
