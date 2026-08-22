# -*- coding: utf-8 -*-
"""
Maliyeti Ne? - Paylasim gorseli (Open Graph)

NEDEN URETILIYOR: gorsel elle yapilmisti ve BAYATLADI - uzerinde
"Dugun · Ev kurma · 0 km arac" yaziyordu, okul vertikali eklendikten
sonra da oyle kaldi; "aylik guncellenen" diyordu, oysa olcum ayda iki
kez. Bu gorsel X/WhatsApp/LinkedIn'de baglanti paylasildiginda gorulen
ILK sey. Bayat bilgi, sitenin en gorunur yerinde duruyordu.

Artik veriden uretiliyor: vertikal adlari ve kalem sayisi gercek
veriden geliyor, her olcumde tazeleniyor.

Cikti: assets/og-gorsel.png (1200x630 - X, Facebook, LinkedIn standardi)
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from envanter import envanter_ozeti
import sayfa_uret as su

SITE_KOK = su.SITE_KOK
HEDEF = SITE_KOK / "assets" / "og-gorsel.png"

# Boyut sayfa_uret'ten geliyor - HTML'deki og:image:width/height ile
# ayni olmak ZORUNDA. Iki yerde ayri tutulsa biri degisip oteki kalir ve
# Facebook'a YANLIS boyut beyan edilir; bir test bunu dogruluyor.
GENISLIK, YUKSEKLIK = su.OG_GENISLIK, su.OG_YUKSEKLIK


# Renkler style.css ile AYNI olmali - iki yerde ayri tutulup biri
# degisirse paylasim karti siteyle alakasiz gorunur.
KAGIT = "#fbfaf7"
MUREKKEP = "#14140f"
SOLUK = "#6a6a5e"
VURGU = "#9c2b1a"
CIZGI = "#ddd9cd"

KALEM_KOK = SITE_KOK / "assets" / "og"


def _yazi_tipi_uret(ImageFont, boyut, kalin=True):
    adaylar = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if kalin
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if kalin
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for a in adaylar:
        if Path(a).exists():
            try:
                return ImageFont.truetype(a, boyut)
            except OSError:
                continue
    return ImageFont.load_default()


def _sar(d, metin, font, azami_genislik, azami_satir=2):
    """Basligi kutuya sigacak sekilde satirlara boler."""
    kelimeler = metin.split()
    satirlar, gecerli = [], ""
    for k in kelimeler:
        deneme = (gecerli + " " + k).strip()
        if d.textlength(deneme, font=font) <= azami_genislik or not gecerli:
            gecerli = deneme
        else:
            satirlar.append(gecerli)
            gecerli = k
    if gecerli:
        satirlar.append(gecerli)
    return satirlar[:azami_satir]


def kalem_karti(baslik: str, tutar: int, alt_satir: str, hedef: Path):
    """Tek bir olcum icin paylasim karti.

    NEDEN GEREKLI (2026-08-02 denetimi): 175 sayfanin TAMAMI ayni
    jenerik gorseli paylasiyordu. /ev-kurma/buzdolabi-fiyatlari/
    WhatsApp'ta paylasildiginda kartta "2026 Maliyet Endeksi" yaziyordu,
    "Buzdolabi 29.597 TL" YAZMIYORDU. Ilk trafik olcumunde referans
    kaynagi %95 m.facebook.com cikmisti - yani paylasim karti bu sitede
    dogrudan tiklanma oraninin kendisi.

    Kartin uzerindeki her sey VERIDEN gelir; sabit metin yalnizca
    marka adi ve alan adi.
    """
    try:
        from PIL import Image, ImageDraw
        from PIL import ImageFont
    except ImportError:
        return None

    img = Image.new("RGB", (GENISLIK, YUKSEKLIK), KAGIT)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, GENISLIK, 12], fill=MUREKKEP)

    d.text((70, 74), "Maliyeti Ne?", font=_yazi_tipi_uret(ImageFont, 38), fill=VURGU)

    bf = _yazi_tipi_uret(ImageFont, 58, False)
    satirlar = _sar(d, baslik, bf, GENISLIK - 140)
    y = 152
    for sat in satirlar:
        d.text((70, y), sat, font=bf, fill=MUREKKEP)
        y += 68

    # Rakam kartin ANA ogesi: en buyuk punto, renk degil buyukluk.
    y = max(y + 24, 300)
    d.text((70, y), "{:,} TL".format(tutar).replace(",", "."),
           font=_yazi_tipi_uret(ImageFont, 128), fill=MUREKKEP)

    d.line([(70, 512), (GENISLIK - 70, 512)], fill=CIZGI, width=2)
    d.text((70, 532), alt_satir, font=_yazi_tipi_uret(ImageFont, 27, False), fill=SOLUK)
    d.text((GENISLIK - 70 - d.textlength("maliyetine.com.tr",
           font=_yazi_tipi_uret(ImageFont, 27, False)), 532),
           "maliyetine.com.tr", font=_yazi_tipi_uret(ImageFont, 27, False), fill=SOLUK)

    return _kaydet(img, hedef)


def _kaydet(img, hedef: Path):
    """Kartlari PALETLI PNG olarak kaydeder.

    2026-08-02: 167 kart x ~33 KB = 5,5 MB. Kartlar RAKAM TASIDIGI icin
    her olcumde (ayda iki kez) yeniden uretiliyor ve depoya giriyor -
    yilda ~130 MB git gecmisi demekti. Bu kartlar duz zemin + duz metin;
    16 renklik palet gorsel olarak ayirt edilemez ama dosyayi ucte
    birine indiriyor (33 -> 9 KB).
    """
    from PIL import Image
    hedef.parent.mkdir(parents=True, exist_ok=True)
    img.convert("P", palette=Image.ADAPTIVE, colors=16).save(
        hedef, "PNG", optimize=True)
    return hedef


def kart_baslikli(baslik: str, alt_satir: str, hedef: Path,
                  vurgu_satiri: str | None = None):
    """BASLIK ODAKLI kart - rehber ve hesaplayici sayfalari icin.

    Kalem kartlari tek bir olculmus rakami buyutuyor. Rehberde tek bir
    "ana rakam" yok (cogu yazi iki rakami KARSILASTIRIYOR), hesaplayicida
    ise olculmus rakam HIC yok - orada cevabi kullanici uretiyor,
    bizim sagladigimiz sey MEVZUAT PARAMETRESI.

    O yuzden bu kartta iddiayi BASLIK tasiyor; alt satir da bos bir
    slogan degil, dayanagi soyluyor:
      - rehberde  : hangi endeksten besleniyor, kac kaynak, olcum tarihi
      - hesapta   : hangi teblig/kanun (rakiplerin paylasim kartinda
                    mevzuat atfi yok - bu bizim ayirt edici yerimiz)
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None

    img = Image.new("RGB", (GENISLIK, YUKSEKLIK), KAGIT)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, GENISLIK, 12], fill=MUREKKEP)
    d.text((70, 74), "Maliyeti Ne?", font=_yazi_tipi_uret(ImageFont, 38), fill=VURGU)

    bf = _yazi_tipi_uret(ImageFont, 66)
    satirlar = _sar(d, baslik, bf, GENISLIK - 140, azami_satir=3)
    # Blogu 150-500 bandinda DIKEYDE ORTALA: tek satirlik bir hesaplayici
    # adiyla uc satirlik bir rehber basligi ayni kartta dengeli dursun.
    ek = [vurgu_satiri] if vurgu_satiri else []
    yukseklik = len(satirlar) * 80 + (52 if ek else 0)
    y = 150 + max(0, (350 - yukseklik) // 2)
    for sat in satirlar:
        d.text((70, y), sat, font=bf, fill=MUREKKEP)
        y += 80
    for sat in ek:
        d.text((70, y + 8), sat, font=_yazi_tipi_uret(ImageFont, 34, False), fill=SOLUK)

    d.line([(70, 512), (GENISLIK - 70, 512)], fill=CIZGI, width=2)
    kf = _yazi_tipi_uret(ImageFont, 26, False)
    # Alt satir uzunsa kirp - tasan metin kartin disina cikar.
    while d.textlength(alt_satir, font=kf) > GENISLIK - 340 and len(alt_satir) > 12:
        alt_satir = alt_satir[:-4] + "…"
    d.text((70, 532), alt_satir, font=kf, fill=SOLUK)
    d.text((GENISLIK - 70 - d.textlength("maliyetine.com.tr", font=kf), 532),
           "maliyetine.com.tr", font=kf, fill=SOLUK)

    return _kaydet(img, hedef)


def rehber_ve_hesap_kartlari(veri_kok: Path | None = None) -> int:
    """Rehber ve hesaplayici sayfalari icin baslik odakli kartlar."""
    kok = veri_kok or SITE_KOK / "veri"
    sayi = 0

    # --- Rehberler: alt satir BESLENDIGI ENDEKSTEN gelir ---
    try:
        import rehber
    except ImportError:
        rehber = None
    if rehber:
        ozet = {}
        for vertikal, conf in su.VERTIKALLER.items():
            dosya = kok / f"{vertikal}.json"
            if not dosya.exists():
                continue
            try:
                veri = json.loads(dosya.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            kalemler = veri.get("kalemler") or {}
            toplam, _ = su.ornek_toplam_hesapla(
                conf, kalemler, conf.get("olcek_varsayilan", 1), "orta")
            siteler = {x["site"] for k in kalemler.values()
                       for x in (k.get("kaynaklar") or []) if x.get("toplam_urun")}
            ozet[vertikal] = (toplam, len(siteler), veri.get("guncelleme_tarihi") or "")

        for r in rehber.REHBERLER:
            # Kart sayfadan ONCE uretilir. Aksi halde yeni bir rehber ilk
            # workflow kosusunda jenerik karta duser ve ancak bir sonraki
            # olcumde kendi kartini kullanir. Yetim bir PNG zararsizdir;
            # og:image'i zaten yalniz gercekten uretilen HTML yayinlar.
            if r.get("og_alt"):
                alt = r["og_alt"]
            else:
                t, n, tarih = ozet.get(r.get("vertikal"), (None, 0, ""))
                conf = su.VERTIKALLER.get(r.get("vertikal")) or {}
                alt = "{} endeksi · {} bağımsız kaynak · {}".format(
                    conf.get("ad", "Maliyet"), n, tarih) if n else "ölçülmüş fiyat verisi"
            # VERTIKAL TOPLAMI KARTA YAZILMAZ.
            # Ilk halde yaziyordu ve YANILTICIYDI: damatlik yazisinin
            # kartinda "406.375 TL" (dugun TOPLAMI) goruluyordu, oysa
            # damatlik 46.450 TL. Karti goren "damatlik 406 bin" anlar.
            # Yazinin kendi rakami govdede hesaplaniyor ve buraya
            # guvenilir sekilde tasinamiyor; iddiayi BASLIK tasisin.
            if kart_baslikli(r["baslik"], alt,
                             KALEM_KOK / "rehber-{}.png".format(r["slug"]),
                             vurgu_satiri=None):
                sayi += 1

    # --- Hesaplayicilar: alt satir MEVZUAT DAYANAGI ---
    try:
        import hesaplayicilar as hs
    except ImportError:
        return sayi
    for h in hs.tum_hesaplayicilar():
        kaynaklar = h.get("kaynaklar") or []
        alt = kaynaklar[0] if kaynaklar else "formülün kendisi kaynaktır"
        ozet = (h.get("ozet") or "").strip()
        if len(ozet) > 74:
            ozet = ozet[:71].rsplit(" ", 1)[0] + "…"
        if kart_baslikli(h.get("ad") or h["baslik"], alt,
                         KALEM_KOK / "hesap-{}.png".format(h["slug"]),
                         vurgu_satiri=ozet or None):
            sayi += 1
    return sayi


def kalem_kartlarini_uret(veri_kok: Path | None = None) -> int:
    """Her kalem sayfasi ve her endeks icin ayri kart uretir."""
    kok = veri_kok or SITE_KOK / "veri"
    # kalem_sayfalari calisma aninda genisletiliyor (hangi kalemin
    # sayfayi hak ettigi O AYKI olcume bagli). Bu cagrilmadan yalnizca
    # statik tanimdaki 28 kalem gorunuyordu, oysa 97 sayfa var.
    su.kalem_sayfalarini_genislet(veri_kok)
    sayi = 0
    for vertikal, conf in su.VERTIKALLER.items():
        dosya = kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        try:
            veri = json.loads(dosya.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        kalemler = veri.get("kalemler") or {}
        tarih = veri.get("guncelleme_tarihi") or ""

        # Endeks karti: vertikalin kendi toplami
        toplam, _ = su.ornek_toplam_hesapla(
            conf, kalemler, conf.get("olcek_varsayilan", 1), "orta")
        if toplam:
            siteler = {x["site"] for k in kalemler.values()
                       for x in (k.get("kaynaklar") or []) if x.get("toplam_urun")}
            if kalem_karti(conf["ad"] + " maliyeti",  int(toplam),
                           f"{conf.get('kart_alt', 'orta segment')} · "
                           f"{len(siteler)} bağımsız kaynak · {tarih}",
                           KALEM_KOK / f"{vertikal}.png"):
                sayi += 1

        # Kalem kartlari: yalnizca SAYFASI OLAN kalemler icin.
        # Kalem ADI tanimdan gelir (kalem_sayfalari yalnizca id+slug tasir).
        adlar = {t["id"]: t["ad"] for t in conf["kalemler"]}
        for sayfa in conf.get("kalem_sayfalari") or []:
            k = kalemler.get(sayfa["id"]) or {}
            orta = ((k.get("segmentler") or {}).get("orta") or {}).get("medyan")
            if not orta:
                continue
            n = len({x["site"] for x in (k.get("kaynaklar") or [])
                     if x.get("toplam_urun")})
            urun = k.get("toplam_urun") or 0
            kalem_tarihi = k.get("guncelleme_tarihi") or tarih
            ad = adlar.get(sayfa["id"])
            if not ad:
                continue
            if k.get("karma_urun_turu"):
                ozellik_ozeti = k.get("ozellik_ozeti") or {}
                turler = [o for o in (ozellik_ozeti.get("urun_turleri") or {}).values()
                          if o.get("urun_sayisi", 0) >= 3]
                eslesen = ozellik_ozeti.get("ozellik_eslesen_urun", 0)
                alt = (f"{len(turler)} ürün tipi · {eslesen} ayrıştırılmış ürün · "
                       f"{kalem_tarihi}")
                if kart_baslikli(ad + " fiyatları", alt,
                                 KALEM_KOK / f"{vertikal}-{sayfa['slug']}.png",
                                 vurgu_satiri="Ürün tipine göre ayrı medyanlar"):
                    sayi += 1
                continue
            alt = f"orta segment · {n} kaynak · {urun} üründen · {kalem_tarihi}"
            if kalem_karti(ad + " fiyatları", int(orta), alt,
                           KALEM_KOK / f"{vertikal}-{sayfa['slug']}.png"):
                sayi += 1
    return sayi


def _ozet(veri_kok: Path | None = None) -> dict:
    kok = veri_kok or SITE_KOK / "veri"
    ortak = envanter_ozeti(kok, su.VERTIKALLER)
    adlar = []
    for vertikal, conf in su.VERTIKALLER.items():
        if vertikal in ortak["vertikaller"]:
            adlar.append(conf["ad"])
    return {
        "adlar": adlar,
        "kalem": ortak["fiyat_serisi"],
        "kaynak": ortak["kaynak"],
    }


def uret(hedef: Path | None = None, veri_kok: Path | None = None) -> Path | None:
    """PIL yoksa None doner - gorsel uretimi zorunlu bir adim degil,
    eksikligi yayini durdurmamali (mevcut gorsel yerinde kalir)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL kurulu degil - og gorseli guncellenmedi.")
        return None

    o = _ozet(veri_kok)
    if not o["adlar"]:
        return None

    h = hedef or HEDEF
    img = Image.new("RGB", (GENISLIK, YUKSEKLIK), KAGIT)
    d = ImageDraw.Draw(img)

    def yazi_tipi(boyut, kalin=True):
        adaylar = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if kalin
            else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if kalin
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for a in adaylar:
            if Path(a).exists():
                try:
                    return ImageFont.truetype(a, boyut)
                except OSError:
                    continue
        return ImageFont.load_default()

    # Ust seride marka rengi
    d.rectangle([0, 0, GENISLIK, 12], fill=MUREKKEP)

    d.text((70, 78), "Maliyeti Ne?", font=yazi_tipi(44), fill=VURGU)
    d.text((70, 168), "2026", font=yazi_tipi(92), fill=MUREKKEP)
    d.text((70, 272), "Maliyet Endeksi", font=yazi_tipi(92), fill=MUREKKEP)

    d.text((70, 415), " · ".join(o["adlar"]), font=yazi_tipi(36, False), fill=SOLUK)

    # Rakamlar: soyut "guvenilir veri" iddiasi yerine olculebilir kanit
    d.text(
        (70, 480),
        f"{o['kalem']} fiyat serisi · {o['kaynak']} bağımsız kaynak · kaynaklar 5/20'de taranır",
        font=yazi_tipi(30, False), fill=MUREKKEP,
    )
    d.text((70, 540), "maliyetine.com.tr", font=yazi_tipi(28, False), fill=SOLUK)

    h.parent.mkdir(parents=True, exist_ok=True)
    img.save(h, "PNG", optimize=True)
    return h



def senaryo_ve_arac_kartlari(veri_kok: Path | None = None) -> int:
    """Senaryo sayfalari (rakam odakli) + vertikal hesaplayici ve
    metodoloji sayfalari (baslik odakli).

    Senaryo sayfalarinin GERCEK bir toplami var ("100 kisilik dugun
    303.470 TL") - bunlar rakam kartini hak ediyor ve zaten en yuksek
    niyetli sorgulari hedefliyorlar.
    """
    kok = veri_kok or SITE_KOK / "veri"
    sayi = 0
    try:
        import senaryo as sen
    except ImportError:
        sen = None

    for vertikal, conf in su.VERTIKALLER.items():
        dosya = kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        try:
            veri = json.loads(dosya.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        kalemler = veri.get("kalemler") or {}
        tarih = veri.get("guncelleme_tarihi") or ""
        siteler = {x["site"] for k in kalemler.values()
                   for x in (k.get("kaynaklar") or []) if x.get("toplam_urun")}

        # Hesaplayici ve metodoloji: baslik odakli
        for alt_yol, baslik in (
                ("hesaplayici", conf["ad"] + " hesaplayıcı"),
                ("metodoloji", conf["ad"] + " — nasıl ölçüyoruz?")):
            if kart_baslikli(
                    baslik,
                    "{} bağımsız kaynak · son başarılı veri {}".format(
                        len(siteler), tarih),
                    KALEM_KOK / f"{vertikal}-{alt_yol}.png"):
                sayi += 1

        if not sen:
            continue
        # Olcek senaryolari: kisi sayisina gore gercek toplam
        for x in (sen.OLCEK_SENARYOLARI.get(vertikal) or []):
            t, _ = su.ornek_toplam_hesapla(conf, kalemler, x["olcek"], "orta")
            if not t:
                continue
            if kart_karti_yaz(x["baslik"], int(t),
                              "orta segment · {} bağımsız kaynak · {}".format(
                                  len(siteler), tarih),
                              KALEM_KOK / f"{vertikal}-{x['slug']}.png"):
                sayi += 1
        # Grup senaryolari: yalnizca o gruptaki kalemlerin toplami
        for x in (sen.GRUP_SENARYOLARI.get(vertikal) or []):
            gruplar = set(x["gruplar"])
            t = sum(
                ((kalemler.get(tn["id"]) or {}).get("segmentler") or {})
                .get("orta", {}).get("medyan", 0)
                for tn in conf["kalemler"]
                if tn.get("grup") in gruplar and tn.get("varsayilan_dahil") is not False
                and not tn.get("bilgi_amacli")
                and not (kalemler.get(tn["id"]) or {}).get("karma_urun_turu"))
            if not t:
                continue
            if kart_karti_yaz(x["baslik"], int(t),
                              "orta segment · {} bağımsız kaynak · {}".format(
                                  len(siteler), tarih),
                              KALEM_KOK / f"{vertikal}-{x['slug']}.png"):
                sayi += 1
    return sayi


def kart_karti_yaz(baslik, tutar, alt, hedef):
    """kalem_karti icin ince sarmalayici - okunurluk icin ayri ad."""
    return kalem_karti(baslik, tutar, alt, hedef)


def rapor_karti_uret(veri_kok: Path | None = None) -> int:
    """Guncel veri raporu icin baslik odakli paylasim karti."""
    try:
        import rapor
        veri = rapor.rapor_verisi(veri_kok)
    except (ImportError, ValueError, OSError, json.JSONDecodeError):
        return 0
    e = veri["envanter"]
    alt = (
        f"{e['fiyat_serisi']} fiyat serisi · {e['kaynak']} bağımsız kaynak · "
        f"son veri {veri['tarih']}"
    )
    return int(bool(kart_baslikli(
        veri["baslik"], alt, KALEM_KOK / "maliyet-raporu.png",
        vurgu_satiri=f"{e['cok_kaynakli']} çok kaynaklı seri",
    )))


def tum_kartlar(veri_kok: Path | None = None) -> int:
    """Butun paylasim kartlari TEK CAGRIDAN.

    Iki ayri fonksiyon vardi ve workflow yalnizca birini cagiriyordu;
    bu tam olarak `sss/` sayfasinin commit listesinden dusme hatasinin
    ayni turu. Tek giris noktasi olsun ki eklenen kart tipi otomatik
    uretilsin.
    """
    return (kalem_kartlarini_uret(veri_kok)
            + rehber_ve_hesap_kartlari(veri_kok)
            + senaryo_ve_arac_kartlari(veri_kok)
            + rapor_karti_uret(veri_kok))

def main():
    yol = uret()
    if not yol:
        return 1
    o = _ozet()
    print(f"OG gorseli uretildi: {yol}")
    print(f"  {' · '.join(o['adlar'])} | {o['kalem']} fiyat serisi | {o['kaynak']} kaynak")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
