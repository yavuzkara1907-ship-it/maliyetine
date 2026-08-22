# -*- coding: utf-8 -*-
"""
Maliyeti Ne? - Rehber (blog) sayfalari

NEDEN AYRI MODUL: sayfa_uret.py veri->tablo cevirisi yapiyor; buradaki
sayfalar ise YAZI. Ikisini ayni dosyada tutmak ikisini de okunmaz yapardi.

YAZIM KURALI (Yavuz'un talimati, 2026-07-26): "yapay zeka gibi degil,
gercekci". Pratikte:
  - Rakamla basla, girizgah yapma. "Bu yazida ele alacagiz" YOK.
  - Cumle uzunluklari degissin. Her paragraf ayni ritimde olmasin.
  - Her sey madde listesi olmasin - liste sadece gercekten liste olan
    seyler icin.
  - "Unutmayin ki", "Sonuc olarak", "Peki ya", "onemlidir" gibi dolgu
    kaliplari YOK.
  - Kendi olcumumuzden cikan sasirtici seyi soyle. Bir sey ters gittiyse
    onu da soyle - asil guveni o veriyor.
  - Abartma. "inanilmaz", "muhtesem", "cok onemli" YOK.

RAKAMLAR ELLE YAZILMAZ: govde fonksiyonlari veriyi parametre alir, tum
tutarlar /veri/*.json'dan gelir. Boylece her yeni olcumde yazilar da
kendiliginden guncellenir - bayat rakamli blog yazisi, guven kaybinin
en hizli yolu.
"""

from __future__ import annotations

import html
import json
from datetime import date
from pathlib import Path

import arac_maliyetleri as am
import sayfa_uret as su

SITE_KOK = su.SITE_KOK
SITE_KOK_URL = su.SITE_KOK_URL


def _veriler(veri_kok: Path | None = None) -> dict:
    kok = veri_kok or SITE_KOK / "veri"
    cikti = {}
    # Vertikal listesi su.VERTIKALLER'den geliyor - elle yazilan liste yeni
    # vertikal eklenince sessizce eksik kaliyordu ("enflasyon" vertikal degil,
    # ayri bir veri dosyasi, o yuzden elle ekli).
    for v in (*su.VERTIKALLER, "enflasyon"):
        dosya = kok / f"{v}.json"
        if dosya.exists():
            try:
                cikti[v] = json.loads(dosya.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
    return cikti


def _kalem(veri: dict, kalem_id: str, segment: str = "orta"):
    """Bir kalemin segment degeri. Yoksa None - rakam UYDURULMAZ."""
    k = (veri.get("kalemler") or {}).get(kalem_id) or {}
    seg = (k.get("segmentler") or {}).get(segment) or {}
    return seg.get("medyan") or k.get("genel_medyan")


def _p(n) -> str:
    return su._para(n) if n else "—"


def _pb(n) -> str:
    """Birim fiyatlarda kurusu koruyan Turkce para bicimi."""
    if n is None:
        return "—"
    metin = f"{float(n):,.2f}"
    metin = metin.replace(",", "_").replace(".", ",").replace("_", ".")
    return metin + " TL"


def _tufe(v: dict, vertikal: str) -> str:
    """Resmi TUFE referansi cumlesi. Veri yoksa BOS doner (uydurma yok).

    Neden degerli: bizim olcumumuz 2026 Temmuz'da basladi. "Ocak'tan bu
    yana ne oldu?" sorusuna ancak resmi endeksle cevap verebiliyoruz.
    KIRMIZI CIZGI: TUFE bir ENDEKS, TL fiyat degil - bizim tutarlarimizla
    karistirilmaz, ayri cumlede ve kaynak adiyla verilir.
    """
    e = v.get("enflasyon")
    if not e:
        return ""
    ilgili = [g for g in (e.get("gruplar") or {}).values()
              if vertikal in (g.get("vertikaller") or [g.get("vertikal")])]
    genel = next((g for g in (e.get("gruplar") or {}).values() if g.get("vertikal") is None), None)
    if not ilgili or not genel:
        return ""
    olcumler = e.get("olcumler") or []
    if len(olcumler) < 2:
        return ""
    parcalar = ", ".join(
        f"{g['ad'].lower()} %{g['degisim_yuzde']:.1f}" for g in ilgili
    )
    return (
        "  <h2>Resmî enflasyonla karşılaştırma</h2>\n"
        f"    <p>TÜİK'in tüketici fiyat endeksine göre {olcumler[0]} — {olcumler[-1]} "
        f"arasında genel enflasyon %{genel['degisim_yuzde']:.1f} oldu; bu bütçeyi "
        f"doğrudan ilgilendiren gruplarda {parcalar}. Bizim ölçümümüz TL cinsinden "
        "gerçek fiyatları izler, bu endeks ise resmî sepetin değişimini — ikisi aynı "
        "şey değil, ama birlikte okununca fiyatın nereye gittiği daha net görünür.</p>\n"
        "    <p class=\"sonuc-alt-metin\">Kaynak: TCMB EVDS, TÜİK Tüketici Fiyat "
        "Endeksi (2025=100).</p>\n"
    )


# ---------------------------------------------------------------------------
# 1. 150 kisilik dugun
# ---------------------------------------------------------------------------
def _govde_dugun_150(v: dict) -> str | None:
    d = v.get("dugun")
    if not d:
        return None
    conf = su.VERTIKALLER["dugun"]
    kalemler = d.get("kalemler") or {}
    toplam, detaylar = su.ornek_toplam_hesapla(conf, kalemler, olcek=150, segment="orta")
    ekonomik, _ = su.ornek_toplam_hesapla(conf, kalemler, olcek=150, segment="ekonomik")
    if not toplam:
        return None

    salon = _kalem(d, "salon-yemekli")
    kokteyl = _kalem(d, "salon-kokteyl")
    gelinlik = _kalem(d, "gelinlik")
    taki = _kalem(d, "taki-altin")
    foto = _kalem(d, "fotografci")

    # En buyuk uc kalem - veriden, elle siralanmaz
    sirali = sorted(
        (x for x in detaylar if x.get("satir_toplam")),
        key=lambda x: -x["satir_toplam"],
    )[:3]
    buyukler = "".join(
        f"<tr><td>{x['ad']}</td><td class=\"sayi\">{_p(x['satir_toplam'])}</td>"
        f"<td class=\"sayi\">%{x['satir_toplam'] / toplam * 100:.0f}</td></tr>"
        for x in sirali
    )

    salon_toplam = salon * 150 if salon else None
    return f"""
  <p class="cevap-blok">
    150 kişilik, orta segment bir düğün {d.get('guncelleme_tarihi', '')} itibarıyla
    <strong>{_p(toplam)}</strong> tutuyor. Ekonomik tercihlerle aynı düğün
    {_p(ekonomik)} seviyesine iniyor. Bu rakamlar tek bir tahminden değil,
    her ay yeniden ölçtüğümüz kalem fiyatlarından çıkıyor.
  </p>

  <h2>Parayı asıl nereye veriyorsunuz?</h2>
  <p>
    Düğün bütçesi konuşulurken akla önce gelinlik gelir. Oysa gelinliğin orta
    segment fiyatı {_p(gelinlik)} — toplamın küçük bir dilimi. Bütçeyi asıl
    belirleyen kalem, kişi başı ödediğiniz salon bedeli.
  </p>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th class="sayi">Tutar</th><th class="sayi">Bütçe payı</th></tr></thead>
    <tbody>{buyukler}</tbody>
  </table></div>
  <p>
    Kişi başı {_p(salon)} olan yemekli bir salon, 150 davetlide
    {_p(salon_toplam)} demek. Davetli listesinden çıkardığınız her 10 kişi,
    yaklaşık {_p(salon * 10 if salon else None)} tasarruf. Hiçbir kalemde bu
    kadar hızlı sonuç alamazsınız.
  </p>

  <h2>Kokteyl gerçekten ucuz mu?</h2>
  <p>
    Kokteyl düzenin kişi başı fiyatı {_p(kokteyl)}, yemekliye göre belirgin
    düşük. Ama menü bedeli ortadan kalkmıyor, sadece faturadan çıkıp
    başka yere geçiyor: misafirlerinizi yemeksiz ağırlamayacaksanız
    catering'i ayrıca ödersiniz.
  </p>
  <p>
    Mekanların kendi yemekli ve kokteyl fiyatları arasındaki farkı ölçtük;
    bu fark, o mekanda menünün kişi başı bedelini veriyor. Ayrıntısı
    <a href="/rehber/yemekli-mi-kokteyl-mi/">yemekli mi kokteyl mi</a>
    yazısında.
  </p>

  <h2>Takı hesabın neresinde?</h2>
  <p>
    Bir altın bileziğin fiyatı {_p(taki)}. Bu kalem endeksin en oynak
    kısmı — gram altın hareket ettikçe ay içinde bile değişiyor. Düğünde
    takılan toplam altını hesaplamaya çalışmıyoruz; davetli sayısına ve
    aile geleneğine göre kat kat değiştiği için ölçülebilir bir şey değil.
  </p>

  <h2>Fotoğrafçı için ayırdığınız rakam muhtemelen fazla</h2>
  <p>
    İstanbul'da düğün fotoğrafçısı {_p(foto)} bandında. Biz de bu kalemi
    uzun süre tahminle taşıdık ve tahminimiz gerçeğin yaklaşık üç katıydı.
    Ölçmeye başlayınca düzelttik. Bütçe planlarken forumlarda dolaşan
    rakamlara değil, tarihi belli ölçümlere bakın.
  </p>

{_tufe(v, "dugun")}
  <h2>Kendi düğününüzü hesaplayın</h2>
  <p>
    Davetli sayınızı ve segment tercihinizi girerek kendi tablonuzu
    çıkarabilirsiniz: <a href="/dugun/hesaplayici/">düğün maliyeti
    hesaplayıcısı</a>. Kalem kalem güncel fiyatlar
    <a href="/dugun/">düğün endeksinde</a>.
  </p>
"""


# ---------------------------------------------------------------------------
# 2. Yemekli mi kokteyl mi
# ---------------------------------------------------------------------------
def _govde_yemekli_kokteyl(v: dict) -> str | None:
    d = v.get("dugun")
    if not d:
        return None
    yemekli = _kalem(d, "salon-yemekli")
    kokteyl = _kalem(d, "salon-kokteyl")
    menu = _kalem(d, "yemek-ikram")
    if not (yemekli and kokteyl):
        return None

    yemekli_150 = yemekli * 150
    kokteyl_150 = kokteyl * 150
    fark_150 = yemekli_150 - kokteyl_150
    menu_150 = menu * 150 if menu else None
    menu_satiri = (
        f'<tr><td>Aynı mekandaki menü farkı</td><td class="sayi">{_p(menu)}</td>'
        f'<td class="sayi">{_p(menu_150)}</td>'
        '<td>Türetilmiş karşılaştırma; ayrıca eklenmez</td></tr>'
        if menu else ""
    )
    menu_bolumu = f"""
  <h2>Menünün kişi başı bedeli</h2>
  <p>
    Aynı mekanın yemekli ve kokteyl fiyatları arasındaki farkı tek tek
    hesapladık; orta segmentte kişi başı {_p(menu)} çıkıyor. Bu değer
    bağımsız bir catering teklifi değil, aynı mekan içindeki paket farkından
    türetilmiş bir karşılaştırma metriği.
  </p>
  <p>
    Farkı <em>aynı mekan içinde</em> almak şart. İki ayrı listenin
    ortancasını çıkarmak yanlış sonuç verir, çünkü her mekan kokteyl
    seçeneği sunmuyor ve farkların ortancası, ortancaların farkına eşit
    değil.
  </p>
""" if menu else """
  <h2>Menü farkı neden ayrıca görünmüyor?</h2>
  <p>
    Aynı mekanın iki paketini eşleştiren yeterli ölçüm olmadan, yemekli ve
    kokteyl ortancalarını birbirinden çıkarıp menü bedeli uydurmuyoruz.
    Paket farkı ancak eşleşmiş mekan örnekleri bulunduğunda gösterilir.
  </p>
"""
    return f"""
  <p class="cevap-blok">
    150 kişilik varsayılan düğün bütçesine yalnızca yemekli salon senaryosu
    giriyor: <strong>{_p(yemekli_150)}</strong>. Kokteyl düzen
    <strong>{_p(kokteyl_150)}</strong> ile ayrı bir alternatif; iki paket
    birbirine eklenmiyor. Ölçülen fark {_p(fark_150)}.
  </p>

  <div class="tablo-sarmal"><table>
    <thead><tr><th>Senaryo</th><th class="sayi">Kişi başı</th><th class="sayi">150 kişi</th><th>Bütçedeki yeri</th></tr></thead>
    <tbody>
      <tr><td>Yemekli salon paketi</td><td class="sayi">{_p(yemekli)}</td><td class="sayi">{_p(yemekli_150)}</td><td>Varsayılan düğün toplamına dahil</td></tr>
      <tr><td>Kokteyl salon paketi</td><td class="sayi">{_p(kokteyl)}</td><td class="sayi">{_p(kokteyl_150)}</td><td>Alternatif; varsayılan toplama eklenmez</td></tr>
      {menu_satiri}
    </tbody>
  </table></div>

  <h2>İki fiyat neyi kapsıyor?</h2>
  <p>
    Düğün mekanları fiyatı kişi başı verir ve genellikle iki seçenek sunar.
    Yemekli seçenekte salon ve menü birlikte fiyatlanır. Kokteyl seçenekte
    mekanın listesinde tanımlanan daha sınırlı ikram paketi bulunur. Tam
    yemek servisi isteyip istememek ayrı bir planlama kararıdır; verimiz
    kokteyl seçen herkesin dışarıdan yemek alacağını varsaymaz.
  </p>
  <p>
    Bu ayrım göründüğünden önemli, çünkü mekanların ilan sayfalarında
    yazan "başlangıç fiyatı" çoğu zaman kokteyl fiyatıdır. Yemekli bir
    düğün planlarken kokteyl fiyatını baz alırsanız bütçeniz baştan
    yanlış kurulur.
  </p>

{menu_bolumu}

  <h2>Hangisi size uygun?</h2>
  <p>
    Kokteyl düzen, daha kısa ve ayakta ağırlama ağırlıklı organizasyonlar
    için düşünülebilir. Uzun bir akşam davetinde tam yemek servisi
    istiyorsanız dış catering teklifini ayrıca ölçmek gerekir; elimizde
    karşılaştırılabilir catering örneklemi olmadığı için bunun daha ucuz ya
    da pahalı olduğunu iddia etmiyoruz.
  </p>

  <h2>Bir uyarı</h2>
  <p>
    Bu iki rakamı toplayıp tek bir "gerçek maliyet" çıkarmaya çalışmayın.
    Hesaplayıcımızda da toplamıyoruz: yemekli fiyat zaten menüyü içerdiği
    için üstüne ayrıca yemek eklemek aynı masrafı iki kez saymak olur.
    Varsayılan 150 kişilik bütçeye yemekli paket giriyor. Kokteyl seçilirse
    yemekli paket onunla değiştirilir; menü farkı ayrıca eklenmez.
  </p>
  <p>
    Kendi düğününüz için hesap:
    <a href="/dugun/hesaplayici/">düğün maliyeti hesaplayıcısı</a>.
    Yöntemin ayrıntısı <a href="/dugun/metodoloji/">metodoloji sayfasında</a>.
  </p>
"""


# ---------------------------------------------------------------------------
# 3. Sifirdan ev kurma
# ---------------------------------------------------------------------------
def _govde_ev_kurma(v: dict) -> str | None:
    e = v.get("ev-kurma")
    if not e:
        return None
    conf = su.VERTIKALLER["ev-kurma"]
    kalemler = e.get("kalemler") or {}
    toplam, detaylar = su.ornek_toplam_hesapla(conf, kalemler, olcek=1, segment="orta")
    ekonomik, _ = su.ornek_toplam_hesapla(conf, kalemler, olcek=1, segment="ekonomik")
    ust, _ = su.ornek_toplam_hesapla(conf, kalemler, olcek=1, segment="luks")
    if not toplam:
        return None

    # Gruplara gore toplam - veriden
    gruplar: dict[str, int] = {}
    for x in detaylar:
        # toplama_dahil kontrolu: su an ev-kurmada varsayilan-kapali kalem
        # yok ama eklenirse grup yuzdeleri sessizce bozulurdu (okul
        # vertikalinde bu tam olarak yasandi).
        if not x.get("satir_toplam") or not x.get("toplama_dahil"):
            continue
        tanim = next((t for t in conf["kalemler"] if t["id"] == x["id"]), {})
        grup = tanim.get("grup") or "Diğer"
        gruplar[grup] = gruplar.get(grup, 0) + x["satir_toplam"]
    grup_satir = "".join(
        f"<tr><td>{g}</td><td class=\"sayi\">{_p(t)}</td>"
        f"<td class=\"sayi\">%{t / toplam * 100:.0f}</td></tr>"
        for g, t in sorted(gruplar.items(), key=lambda x: -x[1])
    )

    buzdolabi = _kalem(e, "buzdolabi")
    camasir = _kalem(e, "camasir-makinesi")
    koltuk = _kalem(e, "koltuk-takimi")
    kalem_sayisi = len([x for x in detaylar if x.get("satir_toplam")])

    return f"""
  <p class="cevap-blok">
    Sıfırdan bir evi eşyalandırmak orta segmentte
    <strong>{_p(toplam)}</strong> tutuyor. Ekonomik tercihlerle
    {_p(ekonomik)}, üst segmentte {_p(ust)}. Bu tutar {kalem_sayisi} kalemin
    toplamı: beyaz eşyadan mutfak gerecine, mobilyadan tekstile.
  </p>

  <h2>Bütçe nasıl dağılıyor?</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Grup</th><th class="sayi">Tutar</th><th class="sayi">Pay</th></tr></thead>
    <tbody>{grup_satir}</tbody>
  </table></div>
  <p>
    Beyaz eşya ve mobilya toplamın büyük kısmını alıyor. Küçük ev aletleri
    tek tek ucuz görünür ama sayıları fazla olduğu için topluca ciddi bir
    yer tutuyor — listeyi çıkarırken en çok bu kalemde şaşırılıyor.
  </p>

  <h2>Önce alınacaklar</h2>
  <p>
    Taşındığınız gün çalışması gerekenler kısa bir liste: buzdolabı
    ({_p(buzdolabi)}), çamaşır makinesi ({_p(camasir)}), bir yatak ve
    oturma grubu ({_p(koltuk)}). Geri kalanı zamana yayılabilir.
    Kahve makinesinden airfryer'a kadar olan kalemler, ilk ay
    ertelendiğinde hayatı zorlaştırmıyor.
  </p>
  <p>
    Eşyayı tek seferde almak zorunda değilsiniz. Ama tek seferde alacaksanız
    tutarı baştan bilmek, kredi ya da taksit planını doğru kurmanızı sağlar.
  </p>

  <h2>Bu rakamlarda ne yok?</h2>
  <p>
    Konutun kendisi, tadilat ve işçilik, nakliye, beyaz eşya montajı ve
    perde dikimi bu tutara dahil değil. Her kalemden bir adet varsayıyoruz;
    iki yatak odalı bir ev kuruyorsanız yatak, komodin ve gardırop
    kalemlerini çoğaltmanız gerekir.
  </p>

{_tufe(v, "ev-kurma")}
  <h2>Fiyatlar nereden geliyor?</h2>
  <p>
    Kaynaklar ayın 5'i ve 20'sinde yeniden taranıyor; her kalem son başarılı
    ölçüm tarihini taşıyor. Bir uyarı: kategori listelerinden derlediğimiz
    için üst segment rakamı piyasanın en pahalısını değil, yaygın ürünler
    içindeki üst çeyreği gösteriyor. Ankastre bir premium buzdolabı
    arıyorsanız gerçek fiyat bizim "üst" sütunumuzun üzerinde olacaktır.
  </p>
  <p>
    Kendi listenizi seçerek hesaplayın:
    <a href="/ev-kurma/hesaplayici/">ev kurma maliyeti hesaplayıcısı</a>.
    Kalem kalem güncel fiyatlar <a href="/ev-kurma/">ev kurma endeksinde</a>.
  </p>
"""


# ---------------------------------------------------------------------------
# 4. Sifir araba gercek maliyeti
# ---------------------------------------------------------------------------
def _govde_arac(v: dict) -> str | None:
    a = v.get("arac")
    if not a:
        return None
    kalem = (a.get("kalemler") or {}).get("en-ucuz-sifir-arac") or {}
    giris = (((kalem.get("segmentler") or {}).get("dusuk") or {}).get("min"))
    ortanca = kalem.get("genel_medyan")
    if not (giris and ortanca):
        return None
    en_ucuz = su._en_ucuz_ornek(kalem)
    model = (en_ucuz or {}).get("isim")
    model_ifadesi = f"<strong>{html.escape(model)}</strong>" if model else "bir marka"
    secilenler = ["mtv", "noter_tescil", "plaka_ruhsat", "trafik_sigortasi", "kasko"]
    ornek = am.hesapla(giris, 1500, secilenler)
    detay_satirlari = "".join(
        f'<tr><td>{html.escape(d["ad"])}</td><td class="sayi">{_p(d["tutar"])}</td>'
        f'<td>{"Resmî" if d["kaynak_tipi"] == "resmi" else "Tahmini"}</td></tr>'
        for d in ornek["detaylar"]
    )
    return f"""
  <p class="cevap-blok">
    Ölçümümüzde en ucuz sıfır araç {model_ifadesi}: <strong>{_p(giris)}</strong>.
    Marka giriş fiyatlarının ortancası {_p(ortanca)}; bu ikinci değer “en
    ucuz araç” cevabı değildir. 1301-1600 cc, 1-3 yaş ve üst taşıt değeri
    kademesindeki örnek senaryoda seçili ilk yıl kalemleri yaklaşık
    <strong>{_p(ornek["ek_toplam"])}</strong> ekliyor. Bunun
    {_p(ornek["resmi_toplam"])} tutarı resmî tarifeden,
    {_p(ornek["tahmini_toplam"])} tutarı piyasa varsayımlarından gelir.
  </p>

  <h2>Etiket fiyatının üstüne ne ekleniyor?</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th class="sayi">Tutar</th><th>Tür</th></tr></thead>
    <tbody>{detay_satirlari}</tbody>
  </table></div>
  <p>
    MTV, <a href="{am.PARAMETRELER['mtv']['kaynak_url']}">58 Seri No.lu
    Genel Tebliğ</a>; ilk tescil harcı ise
    <a href="{am.PARAMETRELER['noter_tescil']['kaynak_url']}">492 sayılı
    Harçlar Kanunu tarifesi</a> üzerinden hesaplanır. Noter hizmet/yazı
    giderleri değişebildiği için resmî toplama eklenmedi. Kasko ve trafik
    sigortası şirkete, ile ve sürücü profiline göre değişir; buradaki
    değerler teklif değil, açıkça etiketlenmiş yaklaşık varsayımlardır.
  </p>

  <h2>Motor hacmi vergiyi ikiye katlayabilir</h2>
  <p>
    MTV; motor hacmi, taşıt değeri, yaş ve tescil tarihine göre kademeli
    hesaplanıyor. Bu sayfadaki örnek 1-3 yaş ve üst taşıt değeri kademesini
    kullanır. Elektrikli araçların vergisi motor gücüne göre hesaplandığı
    için bu örneğe dahil değildir.
  </p>

  <h2>Neden tüm modellerin ortalamasını vermiyoruz?</h2>
  <p>
    Piyasadaki tüm modellerin ortasını almak yanıltıcı bir rakam üretiyor.
    Pahalı ve ucuz markaları satış adetlerinden bağımsız, eşit ağırlıkla
    saymış olur. Bunun yerine her markanın giriş modelini ölçüyor; en düşük
    liste fiyatını ve bu marka girişlerinin ortancasını ayrı gösteriyoruz.
  </p>

  <h2>Kendi aracınızı hesaplayın</h2>
  <p>
    Aracın fiyatını ve motor hacmini girip hangi kalemleri istediğinizi
    seçebilirsiniz: <a href="/arac/hesaplayici/">araç sahip olma maliyeti
    hesaplayıcısı</a>. Marka marka güncel liste fiyatları
    <a href="/arac/">sıfır araç endeksinde</a>.
  </p>
  <p>
    Bu hesap satın alma anını kapsıyor. Yakıt, bakım, lastik ve yıpranma
    gibi kullanım giderleri ayrı bir konu; onları henüz ölçmüyoruz.
  </p>
"""



# ---------------------------------------------------------------------------
# 5. Okul masrafi
# ---------------------------------------------------------------------------
def _govde_okul(v: dict) -> str | None:
    o = v.get("okul")
    if not o:
        return None
    conf = su.VERTIKALLER["okul"]
    kalemler = o.get("kalemler") or {}
    toplam, detaylar = su.ornek_toplam_hesapla(conf, kalemler, olcek=1, segment="orta")
    ekonomik, _ = su.ornek_toplam_hesapla(conf, kalemler, olcek=1, segment="ekonomik")
    if not toplam:
        return None

    gruplar: dict[str, int] = {}
    for x in detaylar:
        # `toplama_dahil` SART: tablet/masa/sandalye satir_toplam tasir ama
        # yillik toplama girmez. Sadece satir_toplam'a bakilirsa grup
        # yuzdeleri %100'u asar.
        if not x.get("satir_toplam") or not x.get("toplama_dahil"):
            continue
        tanim = next((t for t in conf["kalemler"] if t["id"] == x["id"]), {})
        g = tanim.get("grup") or "Diğer"
        gruplar[g] = gruplar.get(g, 0) + x["satir_toplam"]
    grup_satir = "".join(
        f'<tr><td>{g}</td><td class="sayi">{_p(t)}</td>'
        f'<td class="sayi">%{t / toplam * 100:.0f}</td></tr>'
        for g, t in sorted(gruplar.items(), key=lambda x: -x[1])
    )
    canta = _kalem(o, "okul-cantasi")
    ayakkabi = _kalem(o, "ayakkabi")
    tablet = _kalem(o, "tablet")

    return f"""
  <p class="cevap-blok">
    Bir öğrencinin okul alışverişi orta segmentte <strong>{_p(toplam)}</strong>
    tutuyor. Ekonomik tercihlerle {_p(ekonomik)}. İki çocuklu bir ailede bu
    rakam neredeyse ikiye katlanıyor — kırtasiyede toplu alım biraz indirim
    getirse de çanta, ayakkabı ve kitap kişi başı.
  </p>

  <h2>Para nereye gidiyor?</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Grup</th><th class="sayi">Tutar</th><th class="sayi">Pay</th></tr></thead>
    <tbody>{grup_satir}</tbody>
  </table></div>
  <p>
    Listeye tek tek bakınca kırtasiye ucuz görünür; defter 50 lira, kalem 30
    lira. Ama kalem sayısı fazla olduğu için toplamda ciddi yer tutuyor.
    Çanta ({_p(canta)}) ve ayakkabı ({_p(ayakkabi)}) ise tek kalemde
    bütçenin büyük dilimini alıyor.
  </p>

  <h2>Bu toplamda ne yok?</h2>
  <p>
    Kayıt ücreti, bağış, servis ve yemek bu rakamın dışında. Bunlar okula ve
    şehre göre o kadar değişiyor ki tek bir sayı vermek yanıltıcı olurdu.
    Devlet okullarında ders kitapları ücretsiz dağıtılıyor; buradaki kitap
    kalemi yardımcı kaynak ve test kitapları için.
  </p>
  <p>
    Tablet ({_p(tablet)}), çalışma masası ve sandalyesi de varsayılan
    toplamda yok. Bunlar her yıl değil, bir kez alınıp yıllarca kullanılıyor.
    İlk kez alacaksanız hesaplayıcıdan işaretleyebilirsiniz.
  </p>

  <h2>Nereden tasarruf edilir?</h2>
  <p>
    Geçen yıldan kalanları ayırmak en hızlı yöntem — kalem kutusu, cetvel,
    boya seti çoğu zaman bir yıl daha dayanıyor. Defter ve kalemde toplu
    alım birim fiyatı düşürüyor. Çantada ise ucuza kaçmak genelde pahalıya
    geliyor: sırt desteği zayıf bir çanta yıl ortasında değişiyor.
  </p>
{_tufe(v, "okul")}
  <h2>Kendi listenizi hesaplayın</h2>
  <p>
    Hangi kalemleri alacağınızı seçip kendi tutarınızı çıkarabilirsiniz:
    <a href="/okul/hesaplayici/">okul masrafı hesaplayıcısı</a>.
    Kalem kalem güncel fiyatlar <a href="/okul/">okul masrafı endeksinde</a>.
  </p>
"""



# ---------------------------------------------------------------------------
# 6. Ekonomik dugun
# ---------------------------------------------------------------------------
def _govde_ekonomik_dugun(v: dict) -> str | None:
    d = v.get("dugun")
    if not d:
        return None
    conf = su.VERTIKALLER["dugun"]
    kalemler = d.get("kalemler") or {}
    orta, _ = su.ornek_toplam_hesapla(conf, kalemler, olcek=150, segment="orta")
    eko, detay_eko = su.ornek_toplam_hesapla(conf, kalemler, olcek=150, segment="ekonomik")
    eko80, _ = su.ornek_toplam_hesapla(conf, kalemler, olcek=80, segment="ekonomik")
    if not (orta and eko):
        return None

    kokteyl = _kalem(d, "salon-kokteyl", "dusuk")
    yemekli = _kalem(d, "salon-yemekli", "dusuk")
    gelinlik_e = _kalem(d, "gelinlik", "dusuk")
    gelinlik_o = _kalem(d, "gelinlik", "orta")
    fark = orta - eko
    return f"""
  <p class="cevap-blok">
    150 kişilik bir düğün orta segmentte {_p(orta)}, ekonomik tercihlerle
    <strong>{_p(eko)}</strong>. Aradaki {_p(fark)} fark tek bir fedakârlıktan
    değil, her kalemde alt banda inmekten geliyor. Davetliyi 80 kişiye
    düşürürseniz tutar {_p(eko80)} oluyor.
  </p>

  <h2>En büyük tasarruf davetli listesinde</h2>
  <p>
    Düğün bütçesinin çoğu kişi başı ödenen salon bedeli. Kişi başı
    {_p(kokteyl)} olan ekonomik bir kokteyl düzende 150 yerine 80 kişi
    çağırmak, tek başına yüz binlerce liralık farka denk geliyor. Hiçbir
    kalemde pazarlıkla bu kadar hızlı sonuç alınmıyor.
  </p>
  <p>
    Liste kısaltmak zor bir konu, biliyoruz. Ama rakamı görmek kararı
    kolaylaştırıyor: her 10 kişi, ekonomik salonda bile dört haneli bir
    tutar demek.
  </p>

  <h2>Yemekli mi, kokteyl mi?</h2>
  <p>
    Ekonomik bantta yemekli salon kişi başı {_p(yemekli)}, kokteyl
    {_p(kokteyl)}. Kokteyl ucuz görünüyor ama misafirleri aç
    ağırlamayacaksanız yemeği dışarıdan almanız gerekiyor ve mekanın kendi
    mutfağı genelde daha ucuza çalışıyor. Ayrıntısını
    <a href="/rehber/yemekli-mi-kokteyl-mi/">ayrı bir yazıda</a> ölçtük.
  </p>

  <h2>Gelinlikte kiralama farkı</h2>
  <p>
    Ekonomik segmentte gelinlik {_p(gelinlik_e)}, orta segmentte
    {_p(gelinlik_o)}. Ölçtüğümüz fiyatlar satış fiyatı; kiralama bunun
    belirgin altında kalıyor ama kategori bazında düzenli izlenebilen bir
    kaynak bulamadığımız için endekse koymuyoruz. Tek günlük bir kıyafet
    için satın almak zorunda olmadığınızı hatırlatalım.
  </p>

  <h2>Kısmayacağınız kalemler</h2>
  <p>
    Fotoğraf ve video, geriye kalan tek somut şey. Ölçtüğümüz İstanbul
    ortalaması makul bir bantta ve burada en ucuza gitmek çoğu çiftin
    pişman olduğu tercih. Alyansta da benzer bir durum var: gramaj
    düşürmek mantıklı, ama günlük takılan bir eşyada kaliteden inmek
    uzun vadede daha pahalı.
  </p>
{_tufe(v, "dugun")}
  <h2>Kendi senaryonuzu deneyin</h2>
  <p>
    Davetli sayısını ve segmenti değiştirerek farkı kendiniz görebilirsiniz:
    <a href="/dugun/hesaplayici/">düğün maliyeti hesaplayıcısı</a>.
    Kalem kalem fiyatlar <a href="/dugun/">düğün endeksinde</a>.
  </p>
"""


# ---------------------------------------------------------------------------
# 7. Beyaz esya butcesi
# ---------------------------------------------------------------------------
def _govde_beyaz_esya(v: dict) -> str | None:
    e = v.get("ev-kurma")
    if not e:
        return None
    beyaz = ["buzdolabi", "camasir-makinesi", "bulasik-makinesi", "firin-ocak",
             "davlumbaz", "kurutma-makinesi", "mikrodalga", "klima"]
    satirlar, toplam = [], 0
    for kid in beyaz:
        deger = _kalem(e, kid)
        if not deger:
            continue
        tanim = next((t for t in su.VERTIKALLER["ev-kurma"]["kalemler"] if t["id"] == kid), {})
        ad = tanim.get("ad", kid)
        eko = _kalem(e, kid, "dusuk")
        ust = _kalem(e, kid, "luks")
        satirlar.append(
            f'<tr><td>{ad}</td><td class="sayi">{_p(eko)}</td>'
            f'<td class="sayi">{_p(deger)}</td><td class="sayi">{_p(ust)}</td></tr>'
        )
        toplam += deger
    if len(satirlar) < 4:
        return None

    buzdolabi = _kalem(e, "buzdolabi")
    kurutma = _kalem(e, "kurutma-makinesi")
    return f"""
  <p class="cevap-blok">
    Bir evin beyaz eşyasını sıfırdan almak orta segmentte
    <strong>{_p(toplam)}</strong> tutuyor. Bu, tüm ev kurma bütçesinin en
    büyük kalemi — mobilyadan da mutfaktan da fazla.
  </p>

  <h2>Kalem kalem</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Ürün</th><th class="sayi">Ekonomik</th><th class="sayi">Orta</th><th class="sayi">Üst</th></tr></thead>
    <tbody>{''.join(satirlar)}</tbody>
  </table></div>

  <h2>Hepsini birden almak zorunda değilsiniz</h2>
  <p>
    Taşındığınız gün çalışması gerekenler kısa: buzdolabı ({_p(buzdolabi)})
    ve çamaşır makinesi. Bulaşık makinesi, kurutma makinesi ({_p(kurutma)})
    ve mikrodalga sonraya bırakılabilir. Bu sıralama tek başına bütçeyi
    ikiye bölüyor.
  </p>

  <h2>Enerji sınıfı fiyata değer mi?</h2>
  <p>
    Üst segmentteki modellerin çoğu daha iyi enerji sınıfında. Aradaki fark
    elektrik faturasında yıllara yayılıp kendini amorti edebiliyor —
    özellikle çamaşır ve bulaşık makinesi gibi sık çalışan cihazlarda.
    Bunu biz ölçmüyoruz; ürünün enerji etiketindeki yıllık tüketim
    değerini kendi tarifenizle çarpmak en doğrusu.
  </p>

  <h2>Bu rakamların sınırı</h2>
  <p>
    Fiyatlar kategori listelerindeki yaygın modellerden derleniyor. Ankastre
    setler, gardırop tipi buzdolapları ve premium markalar bu listelere
    girmiyor; dolayısıyla "üst" sütunu piyasanın en pahalısını değil,
    yaygın ürünler içindeki üst çeyreği gösteriyor. Montaj ve nakliye de
    dahil değil.
  </p>
{_tufe(v, "ev-kurma")}
  <h2>Kendi listenizi hesaplayın</h2>
  <p>
    <a href="/ev-kurma/hesaplayici/">Ev kurma hesaplayıcısında</a> yalnızca
    beyaz eşyaları işaretleyip kendi toplamınızı çıkarabilirsiniz. Kalem
    kalem güncel fiyatlar <a href="/ev-kurma/">ev kurma endeksinde</a>.
  </p>
"""



# ---------------------------------------------------------------------------
# 9. Bebek masraflari - ILK YIL HESABININ SINIRI
#
# Bebek endeksi tek seferlik hazirligi ve bez KATEGORI PAKET fiyatini
# olcuyor. Paket adedi/gunluk tuketim normalize edilmedigi icin bez medyani
# 12 ile carpilamaz. Sayfa tam da bu siniri anlatir; guclu gorunen ama
# dayanaksiz bir "ilk yil toplami" yayinlamaz.
# ---------------------------------------------------------------------------
def _govde_bebek_ilk_yil(v: dict) -> str | None:
    b = v.get("bebek")
    if not b:
        return None
    conf = su.VERTIKALLER["bebek"]
    kalemler = b.get("kalemler") or {}
    tek_seferlik, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "orta")
    bez = _kalem(b, "bebek-bezi")
    if not (tek_seferlik and bez):
        return None
    eko, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "ekonomik")
    bez_eko = _kalem(b, "bebek-bezi", "dusuk")
    bez_ust = _kalem(b, "bebek-bezi", "luks")
    bez_birim = ((kalemler.get("bebek-bezi") or {}).get("birim_fiyatlari") or {}).get("adet") or {}
    bez_birim_gecerli = (bez_birim.get("eslesen_urun", 0) >= 5
                          and bez_birim.get("eslesme_orani", 0) >= 0.2)
    if bez_birim_gecerli:
        bez_birim_blok = f"""
  <h2>Bez için normalize birim fiyat</h2>
  <p>
    {b.get('guncelleme_tarihi') or '—'} ölçümünde ürün adında paket adedi
    açıkça bulunan <strong>{bez_birim['eslesen_urun']} bez paketinden</strong>
    hesaplanan ortanca fiyat <strong>adet başına {_pb(bez_birim['genel_medyan'])}</strong>.
    Günlük kullanımınızı <a href="/hesap/aylik-tuketim-maliyeti/">aylık tüketim
    maliyeti hesaplayıcısına</a> girerek aylık ve yıllık bez karşılığını
    bulabilirsiniz.
  </p>
"""
        ilk_yil_aciklama = (
            "Bez için adet başı fiyat artık ölçülüyor; kişisel günlük kullanım "
            "hesaplayıcıda kullanıcıdan alınıyor. Mama, ek gıda, sağlık, giyim ve "
            "bakım verileri tamamlanmadan burada tek bir ilk yıl toplamı yine yayınlanmaz."
        )
    else:
        bez_birim_blok = ""
        ilk_yil_aciklama = (
            "Bir sonraki veri aşamamız paket adedini ürün adından ayırıp adet başı "
            "fiyat üretmek; o alan tamamlanmadan burada kesin ilk yıl toplamı göstermeyeceğiz."
        )

    en_pahali = sorted(
        ((t["ad"], _kalem(b, t["id"])) for t in conf["kalemler"]
         if t.get("varsayilan_dahil", True) and _kalem(b, t["id"])),
        key=lambda x: -x[1])[:4]
    satirlar = "".join(
        f'<tr><td>{ad}</td><td class="sayi">{_p(d)}</td>'
        f'<td class="sayi">%{d / tek_seferlik * 100:.0f}</td></tr>'
        for ad, d in en_pahali)

    return f"""
  <p class="cevap-blok">
    Mevcut verimizle bir bebeğin ilk yılı için güvenilir tek toplam
    yayınlayamıyoruz. Ölçebildiğimiz orta segment
    <strong>tek seferlik hazırlık {_p(tek_seferlik)}</strong>; bebek bezinde
    ölçtüğümüz {_p(bez)} ise aylık tüketim değil, kategori listelerindeki
    <strong>paket fiyatı</strong>.
  </p>

  <h2>Neden paket fiyatını on ikiyle çarpmıyoruz?</h2>
  <p>
    Paketlerde beden ve adet aynı değil; günlük kullanım da bebeğin yaşına
    göre değişiyor. Kategori medyanını "bir aylık bez" saymak, örneğin 40'lı
    paketle 120'li fırsat paketini aynı tüketim birimiymiş gibi ele alır.
    Adet başı fiyat ve günlük tüketim olmadan yıllık rakam türetmek doğru
    olmaz.
  </p>

  <h2>Hazırlığın en büyük dört kalemi</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th class="sayi">Orta segment</th><th class="sayi">Payı</th></tr></thead>
    <tbody>{satirlar}</tbody>
  </table></div>
  <p>
    Ekonomik tercihlerle tek seferlik hazırlık {_p(eko)} seviyesine
    iniyor. Bez paketleri ölçümümüzde {_p(bez_eko)} ile {_p(bez_ust)}
    bandında; bu aralık paket büyüklüğü normalize edilmeden yalnızca alışveriş
    fiyatı göstergesidir.
  </p>

{bez_birim_blok}

  <h2>İlk yıl hesabı nasıl kurulmalı?</h2>
  <p>
    Doğru formül; tek seferlik hazırlığa, kullanılan toplam bez adedinin adet
    başı fiyatla çarpımını ve mama, ek gıda, sağlık, giyim ile bakım
    giderlerini eklemektir. {ilk_yil_aciklama}
  </p>

  <h2>Bu rakama neler dahil değil</h2>
  <p>
    Doğum ve hastane masrafı, mama ve ek gıda, sağlık harcamaları,
    kreş ve bakıcı bu hesapta yok. İkinci el ya da devralınan eşya da
    hesaba katılmıyor — pratikte beşik ve araba sıkça el değiştirir ve
    bu, hazırlık tutarını belirgin düşürür.
  </p>

{_tufe(v, "bebek")}
  <p>
    Kalem kalem güncel fiyatlar <a href="/bebek/">bebek endeksinde</a>;
    kendi listenizi <a href="/bebek/hesaplayici/">hesaplayıcıdan</a>
    çıkarabilirsiniz.
  </p>
"""


def _sss_bebek_masrafi(v: dict) -> list[tuple[str, str]]:
    """Aylik bebek sorgusuna kapsam sinirini bozmadan cevap verir."""
    b = v.get("bebek")
    if not b:
        return []
    conf = su.VERTIKALLER["bebek"]
    kalemler = b.get("kalemler") or {}
    tek_seferlik, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "orta")
    bez = _kalem(b, "bebek-bezi")
    if not (tek_seferlik and bez):
        return []
    tarih = b.get("guncelleme_tarihi") or "—"
    bez_birim = ((kalemler.get("bebek-bezi") or {}).get("birim_fiyatlari") or {}).get("adet") or {}
    if bez_birim.get("eslesen_urun", 0) >= 5 and bez_birim.get("eslesme_orani", 0) >= 0.2:
        aylik_cevap = (
            f"{tarih} ölçümünde bebek bezi kategori medyanı paket başına {_p(bez)}, "
            f"normalize ortanca fiyat ise adet başına {_pb(bez_birim['genel_medyan'])}. "
            "Aylık tüketim kişisel günlük bez adedi girilerek hesaplanır; mama, sağlık "
            "ve bakım giderleri bu sonuçta yoktur."
        )
    else:
        aylik_cevap = (
            f"{tarih} ölçümünde bebek bezi kategori medyanı paket başına {_p(bez)}. "
            "Paket adedi ve günlük tüketim normalize edilmediği için bu rakam aylık "
            "gider değildir; tam aylık maliyet henüz hesaplanamaz."
        )
    return [
        (
            "Bir bebeğin aylık masrafı 2026'da ne kadar?",
            aylik_cevap,
        ),
        (
            "Bir bebeğin ilk yılı ne kadar tutar?",
            f"Ölçtüğümüz tek seferlik hazırlık orta segmentte {_p(tek_seferlik)}. "
            "İlk yıl toplamı için bez adedi, mama, ek gıda, sağlık, giyim ve bakım "
            "verileri de gerekir; mevcut paket medyanını on ikiyle çarpmıyoruz."
        ),
        (
            "Neden mama ve sağlık gideri için tahmin vermiyorsunuz?",
            "Bebeğin beslenme ve sağlık ihtiyacı kişiye göre değişir; doğrulanabilir "
            "ve karşılaştırılabilir fiyat verisi olmadan tek rakam yazmak yanıltıcı olur."
        ),
    ]


# ---------------------------------------------------------------------------
# 10. Ceyiz masraflari
# ---------------------------------------------------------------------------
def _govde_ceyiz(v: dict) -> str | None:
    e = v.get("ev-kurma")
    if not e:
        return None
    gruplar = {"Tekstil": [], "Mutfak": [], "Küçük ev aleti": []}
    for t in su.VERTIKALLER["ev-kurma"]["kalemler"]:
        if t.get("grup") in gruplar and _kalem(e, t["id"]):
            gruplar[t["grup"]].append((t["ad"], _kalem(e, t["id"])))
    if sum(len(x) for x in gruplar.values()) < 10:
        return None

    satirlar, toplam = [], 0
    for grup, ks in gruplar.items():
        alt = sum(d for _, d in ks)
        toplam += alt
        satirlar.append(
            f'<tr><td>{grup}</td><td class="sayi">{len(ks)} kalem</td>'
            f'<td class="sayi">{_p(alt)}</td></tr>')
    nevresim = _kalem(e, "nevresim-takimi")
    tencere = _kalem(e, "tencere-seti")

    return f"""
  <p class="cevap-blok">
    Geleneksel çeyiz kapsamına giren kalemler — tekstil, mutfak eşyası ve
    küçük ev aletleri — orta segmentte toplam <strong>{_p(toplam)}</strong>
    tutuyor. Beyaz eşya ve mobilya bu rakamın dışında; onlar ayrı ve çok
    daha büyük kalemler.
  </p>

  <h2>Çeyiz üç grupta toplanıyor</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Grup</th><th class="sayi">Kalem</th><th class="sayi">Orta segment</th></tr></thead>
    <tbody>{"".join(satirlar)}</tbody>
  </table></div>

  <h2>Ölçerken şaşırtan yer</h2>
  <p>
    Çeyiz denince akla önce tekstil gelir ama tutarı belirleyen küçük ev
    aletleri. Bir nevresim takımının orta segment fiyatı {_p(nevresim)},
    bir tencere seti {_p(tencere)} — buna karşılık robot süpürge,
    airfryer, kahve makinesi gibi kalemler tek başına bu ikisinin
    toplamını geçiyor.
  </p>

  <h2>Marka mağazası mı pazaryeri mi?</h2>
  <p>
    Nevresim ve tencerede iki ayrı kaynağı birlikte ölçüyoruz ve aradaki
    fark küçük değil: aynı kategoride marka mağazası ile pazaryeri
    arasında iki kata varan ayrım çıkabiliyor. Bu bir "ucuz site" listesi
    değil — iki listedeki ürün karması farklı. Ayrıntısı
    <a href="/rehber/trendyol-mu-amazon-mu-ucuz/">kaynak karşılaştırması</a>
    yazısında.
  </p>

{_tufe(v, "ev-kurma")}
  <p>
    Kalem kalem fiyatlar <a href="/ev-kurma/">ev kurma endeksinde</a>;
    yalnızca mutfak tarafı için
    <a href="/ev-kurma/mutfak-esyalari-fiyatlari/">mutfak eşyaları sayfasına</a>
    bakabilirsiniz.
  </p>
"""


# ---------------------------------------------------------------------------
# 11. Yatak odasi masraflari
# ---------------------------------------------------------------------------
def _govde_yatak_odasi(v: dict) -> str | None:
    e = v.get("ev-kurma")
    if not e:
        return None
    ks = [(t["ad"], _kalem(e, t["id"]), _kalem(e, t["id"], "dusuk"),
           _kalem(e, t["id"], "luks"))
          for t in su.VERTIKALLER["ev-kurma"]["kalemler"]
          if t.get("grup") == "Yatak odası" and _kalem(e, t["id"])]
    if len(ks) < 4:
        return None
    toplam = sum(x[1] for x in ks)
    eko = sum(x[2] or x[1] for x in ks)
    ust = sum(x[3] or x[1] for x in ks)
    satirlar = "".join(
        f'<tr><td>{ad}</td><td class="sayi">{_p(d)}</td>'
        f'<td class="sayi">{_p(o)}</td><td class="sayi">{_p(u)}</td></tr>'
        for ad, o, d, u in [(a, b, c, d2) for a, b, c, d2 in ks])
    yatak = _kalem(e, "yatak")

    return f"""
  <p class="cevap-blok">
    Bir yatak odasını sıfırdan kurmak orta segmentte
    <strong>{_p(toplam)}</strong> tutuyor. Ekonomik tercihlerle
    {_p(eko)}, üst segmentte {_p(ust)} — yani aradaki fark
    {su._kat(ust / eko)} kat.
  </p>

  <h2>Kalem kalem</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th class="sayi">Ekonomik</th><th class="sayi">Orta</th><th class="sayi">Üst</th></tr></thead>
    <tbody>{satirlar}</tbody>
  </table></div>

  <h2>Bütçeyi tek kalem belirliyor</h2>
  <p>
    Yatağın orta segment fiyatı {_p(yatak)} ve odanın toplamının
    yaklaşık %{(yatak or 0) / toplam * 100:.0f}'ini tek başına o
    oluşturuyor. Gardırop, komodin ve şifonyer birlikte bile yatağın
    altında kalıyor. Bütçeyi kısmak isteyen için sıra bellidir; ama
    her gün sekiz saat kullanılan tek eşya da odur.
  </p>

  <h2>Yatak odası, ev kurma bütçesinin neresi?</h2>
  <p>
    Sıfırdan ev kurmanın orta segment toplamı içinde yatak odası görece
    küçük bir dilim — beyaz eşya ve mobilya çok daha ağır basıyor.
    Karşılaştırmak için
    <a href="/rehber/beyaz-esya-butcesi/">beyaz eşya bütçesine</a> ve
    <a href="/ev-kurma/mobilya-fiyatlari/">mobilya fiyatlarına</a>
    bakabilirsiniz.
  </p>

{_tufe(v, "ev-kurma")}
  <p>
    Kendi listenizi <a href="/ev-kurma/hesaplayici/">ev kurma
    hesaplayıcısından</a> çıkarabilirsiniz.
  </p>
"""


# ---------------------------------------------------------------------------
# 8. Kaynak karsilastirmasi (Trendyol vs Amazon)
# ---------------------------------------------------------------------------
def _kaynak_karsilastirma_kayitlari(v: dict) -> list[dict]:
    """Iki sitede de gercek veri bulunan karsilastirilabilir kalemler."""
    kayitlar = []
    for vert in ("ev-kurma", "okul", "dugun"):
        d = v.get(vert)
        if not d:
            continue
        tanimlar = {t["id"]: t for t in su.VERTIKALLER[vert]["kalemler"]}
        for kid, k in (d.get("kalemler") or {}).items():
            ks = {
                x["site"]: x.get("genel_medyan")
                for x in (k.get("kaynaklar") or [])
                if (x.get("toplam_urun") or 0) > 0 and x.get("genel_medyan")
            }
            if "trendyol" in ks and "amazon" in ks:
                t, a = ks["trendyol"], ks["amazon"]
                kayitlar.append({
                    "ad": (tanimlar.get(kid) or {}).get("ad", kid),
                    "t": t, "a": a, "fark": (a - t) / t * 100,
                })
    return kayitlar


def _govde_kaynak_karsilastirma(v: dict) -> str | None:
    """Iki kaynagi da olctugumuz kalemlerde fiyat bandi karsilastirmasi.

    DURUST CERCEVE: bu "hangi site ucuz" listesi DEGIL. Olctugumuz sey
    kategori sayfalarindaki URUN KARMASI - Amazon'da markali urunler,
    pazaryerinde jenerik urunler agirlikta olabiliyor. Ayni urunun iki
    sitedeki fiyatini karsilastirmiyoruz; oyle bir iddiada bulunmak
    yaniltici olur ve yazi bunu acikca soyluyor.
    """
    import statistics
    kayitlar = _kaynak_karsilastirma_kayitlari(v)
    if len(kayitlar) < 10:
        return None

    pazar_ucuz = [x for x in kayitlar if x["fark"] > 5]
    amazon_ucuz = [x for x in kayitlar if x["fark"] < -5]
    yakin = len(kayitlar) - len(pazar_ucuz) - len(amazon_ucuz)
    medyan_fark = statistics.median([x["fark"] for x in kayitlar])

    def tablo(kayit_listesi, ters=False):
        secili = sorted(kayit_listesi, key=lambda x: x["fark"], reverse=ters)[:6]
        return "".join(
            f'<tr><td>{x["ad"]}</td><td class="sayi">{_p(round(x["t"]))}</td>'
            f'<td class="sayi">{_p(round(x["a"]))}</td>'
            f'<td class="sayi">%{abs(x["fark"]):.0f}</td></tr>'
            for x in secili
        )

    return f"""
  <p class="cevap-blok">
    Aynı {len(kayitlar)} kalemi iki büyük siteden ayrı ayrı ölçtük. Kategori
    listelerinin orta değeri arasındaki fark çoğu kalemde
    <strong>%{abs(medyan_fark):.0f} civarında</strong>. Ama bu "şu site
    ucuz" demek değil — sebebi fiyat politikası değil, listelerdeki ürün
    karması.
  </p>

  <h2>Önce şunu açıklayalım: aynı ürünü karşılaştırmıyoruz</h2>
  <p>
    Buradaki rakamlar, iki sitenin aynı kategori sayfasında listelediği
    ürünlerin orta değeri. Aynı marka ve modelin iki sitedeki fiyatını
    kıyaslamıyoruz — öyle bir iddiada bulunmak yanıltıcı olurdu.
  </p>
  <p>
    Fark şuradan geliyor: bir kategoride bir sitenin listesinde tanınmış
    markalar öne çıkarken diğerinde isimsiz, ucuz modeller ağırlıkta
    oluyor. İki liste de gerçek; farklı bir rafı gösteriyorlar.
  </p>

  <h2>Pazaryeri listesinin daha ucuz kaldığı kalemler</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th class="sayi">Trendyol</th><th class="sayi">Amazon</th><th class="sayi">Fark</th></tr></thead>
    <tbody>{tablo(pazar_ucuz, ters=True)}</tbody>
  </table></div>
  <p>
    Küçük ev aletlerinde ve kırtasiyede tablo genelde böyle. Bu kategorilerde
    pazaryeri listesi isimsiz üreticilerle dolu; giriş fiyatı çok aşağı
    çekiliyor. Marka aramıyorsanız burada gerçekten ucuza alırsınız —
    ama garanti ve servis konusunu ayrıca sormakta fayda var.
  </p>

  <h2>Diğer sitenin daha ucuz kaldığı kalemler</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th class="sayi">Trendyol</th><th class="sayi">Amazon</th><th class="sayi">Fark</th></tr></thead>
    <tbody>{tablo(amazon_ucuz)}</tbody>
  </table></div>
  <p>
    Kitap, defter ve bazı mobilya kalemlerinde yön tersine dönüyor.
    Toplamda {len(pazar_ucuz)} kalemde Trendyol listesi, {len(amazon_ucuz)}
    kalemde Amazon listesi daha aşağıda; {yakin} kalemde fark %5 eşiğinin
    içinde. Bu üç sayı karşılaştırılan {len(kayitlar)} kalemin tamamını verir.
    Tek bir siteyi "ucuz site" diye işaretlemek mümkün değil.
  </p>

  <h2>Pratikte ne işe yarar?</h2>
  <p>
    Bir kalem için bütçe ayırıyorsanız iki listeye de bakın; aradaki fark
    tek bir üründe bile dört haneli tutabiliyor. Marka önemliyse ucuz
    listedeki orta değer sizi yanıltır — o rakam isimsiz modellerden
    geliyor olabilir. Marka önemli değilse tersi geçerli.
  </p>

  <h2>Biz bu farkı ne yapıyoruz?</h2>
  <p>
    Endekste iki kaynağın ham fiyatlarını birbirine karıştırmıyoruz. Her
    kaynağın kendi orta değerini alıp <em>onların</em> ortasını
    hesaplıyoruz. Böylece tek bir sitenin ürün karması sonucu tek başına
    belirlemiyor. Fark %30'u aştığında da bunu gizlemeyip sayfada uyarı
    olarak gösteriyoruz.
  </p>
  <p>
    Ölçümün tamamını indirebilirsiniz: <a href="/veri/">veri sayfası</a>.
    Her satırda hangi kaynaklardan geldiği ve kaç üründen derlendiği yazıyor.
  </p>
"""


# ---------------------------------------------------------------------------
# 12. Damatlik kac para (UZUN KUYRUK)
#
# Yavuz (2026-07-31): "uzun kuyruklu anahtar kelimeli yazilar girelim...
# biraz halka in." Baslik "2026 Damatlik Fiyat Analizi" degil, insanin
# arama kutusuna yazdigi sey: "damatlik kac para".
#
# Bu yazinin govdesi bizim OLCTUGUMUZ ve baskasinin olcmedigi seye
# dayaniyor: ayni kalemde uc kaynak arasindaki %2121'lik fark.
# ---------------------------------------------------------------------------
def _govde_damatlik(v: dict) -> str | None:
    d = v.get("dugun")
    if not d:
        return None
    k = (d.get("kalemler") or {}).get("damatlik") or {}
    seg = k.get("segmentler") or {}
    if not seg.get("orta"):
        return None
    kaynaklar = sorted(
        ((x["site"], x.get("genel_medyan"), x.get("toplam_urun"))
         for x in (k.get("kaynaklar") or []) if x.get("toplam_urun")),
        key=lambda x: x[1] or 0)
    if len(kaynaklar) < 2:
        return None
    eko, orta, ust = seg["dusuk"]["medyan"], seg["orta"]["medyan"], seg["luks"]["medyan"]
    en_ucuz, en_pahali = seg["dusuk"]["min"], seg["luks"]["max"]
    satirlar = "".join(
        f'<tr><td>{ad.capitalize()}</td><td class="sayi">{_p(m)}</td>'
        f'<td class="sayi">{n}</td></tr>' for ad, m, n in kaynaklar)
    kat = (kaynaklar[-1][1] or 1) / (kaynaklar[0][1] or 1)

    return f"""
  <p class="cevap-blok">
    Damatlığın orta segment fiyatı <strong>{_p(orta)}</strong>. Ama tek bir
    rakam bu kalemi anlatmıyor: ölçtüğümüz ürünlerin en ucuzu {_p(en_ucuz)},
    en pahalısı {_p(en_pahali)}. Yani aynı isimle satılan iki şey arasında
    <strong>{su._kat(en_pahali / en_ucuz)} kat</strong> fark var.
  </p>

  <h2>Neden bu kadar geniş bir aralık?</h2>
  <p>
    Çünkü "damatlık" tek bir ürün değil. Aynı kelimeyle hem pazaryerindeki
    hazır takım hem tasarımcı markasının smokini satılıyor. Bunu üç ayrı
    yerden ölçünce net görülüyor:
  </p>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kaynak</th><th class="sayi">Ortalama fiyat</th><th class="sayi">Ürün</th></tr></thead>
    <tbody>{satirlar}</tbody>
  </table></div>
  <p>
    En ucuz kaynakla en pahalı kaynak arasında <strong>{su._kat(kat)} kat</strong>
    fark var. Bu bir ölçüm hatası değil; iki farklı pazarın fiyatı. Damatlık
    ararken önce hangi pazarda olduğunuza karar vermek, marka seçmekten
    daha belirleyici.
  </p>

  <h2>Üç bandın karşılığı ne?</h2>
  <ul>
    <li><strong>{_p(eko)} civarı</strong> — pazaryeri ve zincir mağaza; hazır
      beden, sınırlı kumaş seçeneği. Bir günlük kullanım için yeterli.</li>
    <li><strong>{_p(orta)} civarı</strong> — marka mağazası; kumaş ve dikiş
      farkı burada başlıyor, tadilat genelde dahil.</li>
    <li><strong>{_p(ust)} ve üzeri</strong> — tasarımcı markası, smokin ve
      özel dikim. Düğün sonrası da giyilecek bir yatırım olarak düşünülüyor.</li>
  </ul>

  <h2>Kiralamak ucuz mu?</h2>
  <p>
    Bunu <em>ölçmedik</em>, o yüzden rakam vermiyoruz. Kiralama fiyatları
    internette liste halinde yayınlanmıyor; mağazadan sorulup öğreniliyor.
    Ölçemediğimiz bir şeye tahmin yazmak bu sitenin kuralına aykırı — bu
    kalemde bir kaynağa ulaşırsak buraya ekleriz.
  </p>

  <h2>Düğün bütçesinin neresi?</h2>
  <p>
    Orta segment damatlık, 150 kişilik bir düğünün toplamında görece küçük
    bir kalem — bütçeyi asıl belirleyen kişi başı salon bedeli. Kalem kalem
    dağılım <a href="/rehber/150-kisilik-dugun-maliyeti/">150 kişilik düğün
    yazısında</a>; güncel fiyatlar
    <a href="/dugun/damatlik-fiyatlari/">damatlık fiyatları sayfasında</a>.
  </p>
"""


# ---------------------------------------------------------------------------
# 13. Asgari ucretle ev kurulur mu (UZUN KUYRUK)
# Iki ayri veri kumesini birlestiriyor: resmi asgari ucret + kendi ev
# kurma olcumumuz. Ikisi de bizde var, baska kimsede birlikte yok.
# ---------------------------------------------------------------------------
def _govde_asgari_ucret_ev(v: dict) -> str | None:
    e = v.get("ev-kurma")
    if not e:
        return None
    conf = su.VERTIKALLER["ev-kurma"]
    kalemler = e.get("kalemler") or {}
    eko, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "ekonomik")
    orta, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "orta")
    if not eko:
        return None
    net = 28075.5   # 2026 net asgari ucret
    brut = 33030.0
    ay_eko = eko / net
    ay_orta = orta / net

    beyaz = ["buzdolabi", "camasir-makinesi", "firin-ocak"]
    zorunlu = sum(_kalem(e, x, "dusuk") or 0 for x in beyaz)

    return f"""
  <p class="cevap-blok">
    Kısa cevap: <strong>tek maaşla ve tek seferde hayır.</strong> Ekonomik
    tercihlerle sıfırdan ev kurmak <strong>{_p(eko)}</strong> tutuyor; 2026
    net asgari ücret {_p(net)}. Yani ev, <strong>{ay_eko:.0f} aylık net
    asgari ücrete</strong> denk geliyor — hiç harcamadan biriktirseniz bile
    {ay_eko / 12:.1f} yıl.
  </p>

  <h2>Rakamı biraz açalım</h2>
  <ul>
    <li>Ekonomik segmentte toplam {_p(eko)} → {ay_eko:.0f} maaş</li>
    <li>Orta segmentte {_p(orta)} → {ay_orta:.0f} maaş</li>
    <li>Yalnızca buzdolabı, çamaşır makinesi ve fırın (ekonomik) → {_p(zorunlu)}</li>
  </ul>
  <p>
    Son satır önemli: listenin tamamını almak zorunda değilsiniz. Üç temel
    beyaz eşya, ekonomik segmentte toplamın küçük bir dilimi ve bir evi
    yaşanabilir kılmaya yetiyor. Geri kalanı zamana yayılabilir.
  </p>

  <h2>Pratikte nasıl yapılıyor?</h2>
  <p>
    Ölçtüğümüz rakam "her şeyi bugün, sıfırdan, yeni al" senaryosu. Gerçek
    hayatta ev kurma üç yoldan biriyle oluyor: ikinci el, aileden devralma
    ya da taksit. Üçü de bu hesabın dışında kalıyor çünkü ikinci el fiyatı
    ürünün durumuna göre değişiyor ve tek bir sayıyla ölçülemiyor.
  </p>
  <p>
    Taksit tarafında ise etiket fiyatı ödediğinizin tamamı değil: 12 ay
    vadede toplam geri ödemenin ne olduğunu
    <a href="/hesap/kredi-taksit-hesaplama/">kredi taksit hesaplayıcısıyla</a>
    görebilirsiniz.
  </p>

  <h2>Bir de şu var: rakam yerinde durmuyor</h2>
  <p>
    Kaynaklar ayın 5'i ve 20'sinde yeniden taranıyor; yazı her serinin son
    başarılı ölçümünü kullanıyor. Bugün {ay_eko:.0f} maaş olan şey, maaş artışı fiyat
    artışının gerisinde kalırsa gelecek yıl daha fazla maaş eder.
    Paranızın erimesini
    <a href="/hesap/alim-gucu-hesaplama/">alım gücü hesaplayıcısından</a>
    takip edebilirsiniz.
  </p>

{_tufe(v, "ev-kurma")}
  <p>
    Kalem kalem liste <a href="/ev-kurma/">ev kurma endeksinde</a>; kendi
    listenizi <a href="/ev-kurma/hesaplayici/">hesaplayıcıdan</a>
    çıkarabilirsiniz.
  </p>
"""


# ---------------------------------------------------------------------------
# 14. Gelinlik mi damatlik mi pahali (UZUN KUYRUK)
#
# BU YAZININ ASIL DEGERI: verimizde damatlik gelinlikten pahali cikiyor
# ama bu PIYASA GERCEGI DEGIL, OLCUM SINIRI - gelinlikte tek kaynak
# (pazaryeri) var, damatlikta uc kaynak ve ikisi luks marka. Bunu
# gizlemek yerine yazinin konusu yapiyoruz.
# ---------------------------------------------------------------------------
def _govde_gelinlik_damatlik(v: dict) -> str | None:
    d = v.get("dugun")
    if not d:
        return None
    kal = d.get("kalemler") or {}
    g, dm = kal.get("gelinlik") or {}, kal.get("damatlik") or {}
    gs, ds = (g.get("segmentler") or {}).get("orta"), (dm.get("segmentler") or {}).get("orta")
    if not (gs and ds):
        return None
    g_kaynak = [x for x in (g.get("kaynaklar") or []) if x.get("toplam_urun")]
    d_kaynak = [x for x in (dm.get("kaynaklar") or []) if x.get("toplam_urun")]

    return f"""
  <p class="cevap-blok">
    Ölçtüğümüz veride <strong>damatlık {_p(ds["medyan"])}</strong>,
    <strong>gelinlik {_p(gs["medyan"])}</strong> — yani damatlık daha
    pahalı görünüyor. Ama bu piyasa gerçeği değil,
    <strong>bizim ölçüm sınırımız</strong>. Nedenini gizlemek yerine
    anlatalım.
  </p>

  <h2>Fark nereden geliyor?</h2>
  <p>
    Damatlığı <strong>{len(d_kaynak)} ayrı kaynaktan</strong> ölçüyoruz ve
    bunların ikisi lüks marka mağazası. Gelinliği ise şu an
    <strong>{len(g_kaynak)} kaynaktan</strong> ölçebiliyoruz ve o da bir
    pazaryeri. Yani iki kalemi farklı pazarlarda ölçüp yan yana koymuş
    oluyoruz.
  </p>
  <p>
    Gerçek hayatta gelinlik evinden alınan bir gelinlik, pazaryerindeki
    hazır gelinliğin kat kat üzerinde. O fiyatları ölçemiyoruz çünkü
    gelinlik evleri fiyatlarını internette yayınlamıyor —
    denediğimiz kaynaklarda "fiyat için üye olun" yazıyordu.
  </p>

  <h2>Peki bu rakamlar işe yaramaz mı?</h2>
  <p>
    Yarar, ama neyi gösterdiğini bilerek. Gelinlik rakamımız
    <em>pazaryeri gelinliğinin</em> fiyatı; damatlık rakamımız
    <em>pazaryeri + marka mağazası karışımının</em> fiyatı. Kendi
    bütçenizi kurarken ikisini aynı kefeye koymayın; her kalemin kaç
    kaynaktan ölçüldüğü ilgili sayfada yazıyor.
  </p>

  <h2>Neden bunu yazıyoruz?</h2>
  <p>
    Çünkü bir maliyet sitesinin en kolay yalanı, elindeki iki rakamı yan
    yana koyup çarpıcı bir başlık atmak. Bizde de o başlık atılabilirdi:
    "damatlık gelinlikten pahalı". Doğru olmazdı. Verinin nereden
    geldiğini yazmadan verilen her karşılaştırma böyle bir risk taşıyor.
  </p>
  <p>
    Kalem kalem güncel fiyatlar:
    <a href="/dugun/gelinlik-fiyatlari/">gelinlik</a> ·
    <a href="/dugun/damatlik-fiyatlari/">damatlık</a> ·
    yöntem için <a href="/dugun/metodoloji/">metodoloji sayfası</a>.
  </p>
"""


# ---------------------------------------------------------------------------
# 15. Kedi mi kopek mi masrafli (UZUN KUYRUK)
# ---------------------------------------------------------------------------
def _govde_kedi_kopek(v: dict) -> str | None:
    ked, kop = v.get("kedi"), v.get("kopek")
    if not (ked and kop):
        return None
    sonuc = {}
    for ad, veri in (("Kedi", ked), ("Köpek", kop)):
        vert = "kedi" if ad == "Kedi" else "kopek"
        conf = su.VERTIKALLER[vert]
        kalemler = veri.get("kalemler") or {}
        kurulum, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "orta")
        paket = sum(
            ((kalemler.get(t["id"]) or {}).get("segmentler") or {}).get("orta", {}).get("medyan", 0)
            for t in conf["kalemler"] if t.get("olcum_turu") == "paket_fiyati")
        if not kurulum:
            return None
        sonuc[ad] = {"kurulum": kurulum, "paket": paket}
    k, p = sonuc["Kedi"], sonuc["Köpek"]
    kurulum_farki = (
        f"Bu ölçümde kedi kurulumu {_p(k['kurulum'])}, köpek kurulumu "
        f"{_p(p['kurulum'])}."
    )

    return f"""
  <p class="cevap-blok">
    Verimiz kediyle köpeğin toplam ya da ilk yıl masrafını güvenilir biçimde
    karşılaştırmaya yetmiyor. <strong>{kurulum_farki}</strong> Mama, kum ve ped
    tarafında ise yalnız paket fiyatlarını ölçüyoruz; tüketim ve paket boyu
    normalize edilmeden hangisinin yıllıkta daha pahalı olduğu söylenemez.
  </p>

  <h2>Neden kurulumda kedi öne geçiyor?</h2>
  <p>
    Tek kalem yüzünden: kedi tuvaleti. Kapalı modeller ve elek sistemi
    fiyatı yukarı çekiyor. Köpekte o kalemin karşılığı yok; onun yerine
    tasma ve taşıma çantası var, ikisi birlikte daha ucuza geliyor.
  </p>

  <h2>Tekrarlayan ürünleri neden karşılaştırmıyoruz?</h2>
  <p>
    Birer paket mama/kum göstergesi kedide {_p(k['paket'])}, mama/ped
    göstergesi köpekte {_p(p['paket'])}. Bunlar aynı miktarı temsil etmiyor:
    mamada kilogram, kumda litre/kilogram, pedde adet ve hayvanın tüketimi
    gerekir. Paket toplamlarını aylık kabul edip on ikiyle çarpmak sahte bir
    kesinlik üretirdi.
  </p>

  <div class="tablo-sarmal"><table>
    <thead><tr><th></th><th class="sayi">Kedi</th><th class="sayi">Köpek</th></tr></thead>
    <tbody>
      <tr><td>Tek seferlik kurulum</td><td class="sayi">{_p(k["kurulum"])}</td><td class="sayi">{_p(p["kurulum"])}</td></tr>
      <tr><td>Birer paketlik ürün göstergesi</td><td class="sayi">{_p(k["paket"])}</td><td class="sayi">{_p(p["paket"])}</td></tr>
      <tr><td>İlk yıl toplamı</td><td class="sayi">Ölçülmedi</td><td class="sayi">Ölçülmedi</td></tr>
    </tbody>
  </table></div>

  <h2>Bu rakamlara neler dahil değil</h2>
  <p>
    Veteriner, aşı, kısırlaştırma ve mikroçip yok — bunlar hem kliniğe göre
    değişiyor hem internette liste fiyatı olarak yayınlanmıyor. Pet
    kuaförü, pansiyon ve eğitim de dışarıda. Ölçmediğimiz kalemlerle ilgili
    alt sınır ya da yıllık toplam iddiası kurmuyoruz.
  </p>
  <p>
    Hayvanın kendisi de hesapta yok: sahiplenme ücretsizdir ve satın almayı
    ne ölçüyor ne teşvik ediyoruz.
  </p>
  <p>
    Kalem kalem: <a href="/kedi/">kedi masrafı</a> ·
    <a href="/kopek/">köpek masrafı</a> ·
    <a href="/evcil-hayvan/">ikisi bir arada</a>. Aylık hesabın veri sınırı:
    <a href="/rehber/aylik-kedi-masrafi/">kedi</a> ·
    <a href="/rehber/aylik-kopek-masrafi/">köpek</a>.
  </p>
"""


# ---------------------------------------------------------------------------
# AI SORGU KALIBI: "aylik X masrafi ne kadar?"
#
# Search Console'da bu kalip ilk sayfa sinirina geldi. Ancak kategori paket
# medyanlarini aylik diye etiketlemek talebe cevap vermek DEGIL, verinin
# tasimadigi bir iddia kurmaktir. Sayfa soruyu dogrudan yanitlar ve gereken
# normalizasyonu aciklar.
# ---------------------------------------------------------------------------
def _paket_evcil_ozeti(v: dict, vertikal: str) -> dict | None:
    veri = v.get(vertikal)
    conf = su.VERTIKALLER.get(vertikal)
    if not (veri and conf):
        return None
    kalemler = veri.get("kalemler") or {}
    tekrar = [t for t in conf["kalemler"] if t.get("olcum_turu") == "paket_fiyati"]
    satirlar = []
    toplamlar = {"dusuk": 0, "orta": 0, "luks": 0}
    for tanim in tekrar:
        degerler = {s: _kalem(veri, tanim["id"], s) for s in toplamlar}
        if not degerler["orta"]:
            continue
        for s, deger in degerler.items():
            toplamlar[s] += deger or 0
        satirlar.append({"ad": tanim["ad"].replace(" (paket)", ""), **degerler})
    if not satirlar or not toplamlar["orta"]:
        return None
    return {
        "tarih": veri.get("guncelleme_tarihi") or "—",
        "satirlar": satirlar,
        "toplamlar": toplamlar,
    }


def _normalize_evcil_ozeti(v: dict, vertikal: str) -> list[dict]:
    veri = v.get(vertikal) or {}
    kalemler = veri.get("kalemler") or {}
    adlar = {
        "kedi-mamasi": "Kedi maması",
        "kedi-kumu": "Kedi kumu",
        "kopek-mamasi": "Köpek maması",
        "cis-pedi": "Çiş pedi",
    }
    satirlar = []
    for kalem_id, ad in adlar.items():
        kalem = kalemler.get(kalem_id) or {}
        for birim, ozet in (kalem.get("birim_fiyatlari") or {}).items():
            if ozet.get("eslesen_urun", 0) < 5 or ozet.get("eslesme_orani", 0) < 0.2:
                continue
            satirlar.append({
                "ad": ad,
                "birim": birim,
                "etiket": ozet.get("etiket") or f"TL/{birim}",
                "fiyat": ozet["genel_medyan"],
                "urun": ozet["eslesen_urun"],
                "kaynak": ozet.get("kaynak_sayisi", 0),
                "tarih": kalem.get("guncelleme_tarihi") or veri.get("guncelleme_tarihi") or "—",
            })
    return satirlar


def _govde_aylik_evcil(vertikal: str, ad: str, ozel_not: str):
    def govde(v: dict) -> str | None:
        ozet = _paket_evcil_ozeti(v, vertikal)
        if not ozet:
            return None
        t = ozet["toplamlar"]
        satirlar = "".join(
            f'<tr><td>{x["ad"]}</td><td class="sayi">{_p(x["dusuk"])}</td>'
            f'<td class="sayi">{_p(x["orta"])}</td>'
            f'<td class="sayi">{_p(x["luks"])}</td></tr>'
            for x in ozet["satirlar"]
        )
        normalize = _normalize_evcil_ozeti(v, vertikal)
        if normalize:
            normalize_satirlari = "".join(
                f'<tr><td>{x["ad"]}</td><td>{x["etiket"]}</td>'
                f'<td class="sayi">{_pb(x["fiyat"])}</td>'
                f'<td class="sayi">{x["urun"]}</td>'
                f'<td class="sayi">{x["kaynak"]}</td><td>{x["tarih"]}</td></tr>'
                for x in normalize
            )
            normalize_blok = f"""
  <h2>Normalize birim fiyatları</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th>Birim</th><th class="sayi">Ortanca</th>
    <th class="sayi">Eşleşen ürün</th><th class="sayi">Kaynak</th><th>Ölçüm</th></tr></thead>
    <tbody>{normalize_satirlari}</tbody>
  </table></div>
  <p>
    Artık paket büyüklüğünü ortak birime çevirebiliyoruz. Geriye kişisel
    tüketim kalıyor: <a href="/hesap/aylik-tuketim-maliyeti/"><strong>aylık
    tüketim maliyeti hesaplayıcısına</strong></a> günlük mama gramını veya
    aylık kum/ped miktarını girerek kendi rakamınızı çıkarın.
  </p>
"""
            cevap = (
                f"{ozet['tarih']} ölçümünde paket fiyatlarının yanında normalize "
                f"birim fiyatlar da hazır. Tek bir aylık {ad.lower()} masrafı yok; "
                "kendi tüketiminizi girerek ölçülmüş TL/kg, TL/litre veya TL/adet "
                "değeriyle hesaplayabilirsiniz."
            )
        else:
            normalize_blok = """
  <h2>Aylık hesap için hangi veri eksik?</h2>
  <p>
    Mama için kilogram başı fiyat ve aylık tüketim; kum için karşılaştırılabilir
    litre/kilogram birimi ve değişim sıklığı; ped için adet başı fiyat ve aylık
    adet gerekir. Ürün adlarından bu alanları güvenilir biçimde ayırıp aynı
    birime çevirmeden paket medyanını on ikiyle çarpmıyoruz.
  </p>
"""
            cevap = (
                f"Mevcut verimizle güvenilir bir aylık {ad.lower()} masrafı hesaplanamaz. "
                f"{ozet['tarih']} ölçümünde mama ve diğer tekrarlayan ürünlerden birer "
                f"paketlik alışveriş göstergesi orta bantta <strong>{_p(t['orta'])}</strong>; "
                f"ekonomik bant {_p(t['dusuk'])}, üst bant {_p(t['luks'])}. Bu rakam aylık "
                "gider ya da bakım maliyeti alt sınırı değildir."
            )
        return f"""
  <p class="cevap-blok">
    {cevap}
  </p>

  <h2>Ölçtüğümüz paket fiyatları</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th class="sayi">Ekonomik</th><th class="sayi">Orta</th><th class="sayi">Üst</th></tr></thead>
    <tbody>{satirlar}</tbody>
  </table></div>
  <p>{ozel_not}</p>

{normalize_blok}

  <h2>Bu rakama neler dahil değil?</h2>
  <p>
    Veteriner muayenesi, aşı, kısırlaştırma, mikroçip, ilaç, kuaför,
    pansiyon ve eğitim dahil değil. Bunların fiyatı klinik, şehir, ırk ve
    ihtiyaca göre değişiyor; doğrulanabilir bir liste fiyatı olmadan tek
    rakam yazmıyoruz. Sağlık ve hizmet kalemleri ayrıca veri toplama gerektirir.
  </p>

  <h2>Kendi listenizi hesaplayın</h2>
  <p>
    Tek seferlik kurulumla paket fiyatlarını birlikte görmek için
    <a href="/{vertikal}/hesaplayici/">{ad.lower()} masrafı hesaplayıcısını</a>
    kullanın. Fiyat aralıkları ve kaynaklar
    <a href="/{vertikal}/">{ad.lower()} maliyeti endeksinde</a>.
  </p>
"""
    return govde


def _sss_aylik_evcil(vertikal: str, ad: str):
    def sorular(v: dict) -> list[tuple[str, str]]:
        ozet = _paket_evcil_ozeti(v, vertikal)
        if not ozet:
            return []
        orta = ozet["toplamlar"]["orta"]
        kalem_adlari = ", ".join(x["ad"].lower() for x in ozet["satirlar"])
        normalize = _normalize_evcil_ozeti(v, vertikal)
        if normalize:
            birimler = ", ".join(
                f'{x["ad"].lower()} için {x["etiket"]} {_pb(x["fiyat"])}'
                for x in normalize
            )
            aylik_cevap = (
                f"{ozet['tarih']} ölçümünde {birimler}. Tek aylık rakam tüketim "
                "bilinmeden verilemez; aylık tüketim hesaplayıcısına günlük gram/adet "
                "veya aylık kum miktarınızı girerek kişisel sonucu bulabilirsiniz."
            )
            yillik_cevap = (
                "Hesaplayıcı ölçülmüş birim fiyatı kişisel aylık tüketimle çarpar ve "
                "yıllık karşılığı da gösterir. Veteriner ve diğer hizmet giderleri "
                "bu sarf ürünü hesabına dahil değildir."
            )
        else:
            aylik_cevap = (
                f"{ozet['tarih']} ölçümünde {kalem_adlari} için birer paketlik "
                f"alışveriş göstergesi orta bantta {_p(orta)}. Paket boyu ve tüketim "
                "normalize edilmediği için bu tutar aylık masraf değildir."
            )
            yillik_cevap = (
                "Mevcut kategori verisinden güvenilir yıllık toplam çıkarılamaz. "
                "Kilogram/adet başı fiyat, hayvanın tüketimi ve sağlık-hizmet "
                "giderleri birlikte ölçülmelidir."
            )
        return [
            (
                f"2026'da aylık {ad.lower()} masrafı ne kadar?",
                aylik_cevap,
            ),
            (
                f"Bir {ad.lower()} yılda ne kadar masraf çıkarır?",
                yillik_cevap,
            ),
            (
                "Veteriner ve aşı neden hesapta yok?",
                "Klinik ücretleri şehir, işlem ve hayvanın durumuna göre değişiyor; "
                "karşılaştırılabilir canlı fiyat listesi bulunmadan tahmin eklemiyoruz."
            ),
        ]
    return sorular


# ---------------------------------------------------------------------------
# TAVSIYE YAZILARI ICIN ORTAK YARDIMCI (2026-08-01)
#
# Yavuz: "tavsiyeler de cok araniyor sanki. ozellikle evcil hayvan vs
# konularinda."
#
# TAVSIYE YAZMANIN BU PROJEDEKI SINIRI
# ------------------------------------
# Genel bakim tavsiyesi ("kediyi haftada bir tarayin") YAZMIYORUZ.
# Bunu olcmuyoruz, veteriner degiliz ve o icerik rakiplerin yaptigi
# seyin ta kendisi - modelden uretilmis, kaynaksiz, herkeste ayni.
#
# Bizim verebilecegimiz tavsiye OLCUMDEN cikandir: hangi kalemde
# secim butceyi gercekten degistiriyor, hangisinde degistirmiyor.
# `aralik_siralamasi()` bunu veriden hesapliyor.
#
# YORUM TUZAGI - metinlerde acikca yazili:
# Genis aralik "kalitesi daha iyi urun daha pahali" demek DEGIL.
# Cogu zaman kategori FARKLI URUN TIPLERINI iceriyor. Kedi tuvaletinde
# 599 TL acik kap, 17.099 TL otomatik elekli sistem - ikisi ayni seyin
# ucuzu ve pahalisi degil, ayri urunler. Bu yuzden tavsiye "pahalisini
# al" ya da "ucuzunu al" degil: "once hangi TIPI istedigine karar ver".
# ---------------------------------------------------------------------------
def aralik_siralamasi(veri: dict, vertikal: str) -> list[dict]:
    """Kalemleri ekonomik-ust kat farkina gore siralar (genis -> dar).

    Yalnizca uc segmenti de dolu ve gercek olculmus kalemler girer;
    tahmini ve tek-olcum kalemleri disarida kalir (onlarda "aralik"
    diye bir sey yok, uc segment ayni degeri tasiyor).
    """
    conf = su.VERTIKALLER.get(vertikal)
    kalemler = (veri or {}).get("kalemler") or {}
    if not conf:
        return []
    cikti = []
    for tanim in conf["kalemler"]:
        k = kalemler.get(tanim["id"]) or {}
        if k.get("kaynak_tipi") == "tahmini" or k.get("tek_deger"):
            continue
        seg = k.get("segmentler") or {}
        eko, orta, ust = ((seg.get(x) or {}).get("medyan")
                          for x in ("dusuk", "orta", "luks"))
        if not (eko and orta and ust) or ust <= eko:
            continue
        cikti.append({
            "id": tanim["id"], "ad": tanim["ad"], "kat": ust / eko,
            "eko": eko, "orta": orta, "ust": ust,
            "toplam_harici": tanim.get("varsayilan_dahil") is False,
        })
    cikti.sort(key=lambda x: x["kat"], reverse=True)
    return cikti


def _aralik_tablosu(sira: list[dict], adet: int = 5) -> str:
    satir = "".join(
        '<tr><td>{ad}</td><td class="sayi">{e}</td><td class="sayi">{u}</td>'
        '<td class="sayi">{k}×</td></tr>'.format(
            ad=x["ad"], e=_p(x["eko"]), u=_p(x["ust"]), k=su._kat(x["kat"]))
        for x in sira[:adet])
    return ('<div class="tablo-sarmal"><table><thead><tr><th>Kalem</th>'
            '<th class="sayi">Ekonomik</th><th class="sayi">Üst</th>'
            '<th class="sayi">Fark</th></tr></thead>'
            "<tbody>{}</tbody></table></div>".format(satir))


# ---------------------------------------------------------------------------
# 16-17. Kedi / kopek sahiplenmeden once (TAVSIYE)
# Tek fonksiyon iki yaziyi da uretiyor - govde ayni veriden, hayvan
# adi ve kalem kirilimi farkli. Metin de farkli cikiyor cunku
# siralamayi VERI belirliyor (kedide tuvalet, kopekte mama one cikiyor).
# ---------------------------------------------------------------------------
def _govde_sahiplenme(vertikal: str, ad: str, oteki_yol: str, oteki_ad: str):
    def govde(v: dict) -> str | None:
        veri = v.get(vertikal)
        if not veri:
            return None
        conf = su.VERTIKALLER[vertikal]
        kalemler = veri.get("kalemler") or {}
        kurulum, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "orta")
        if not kurulum:
            return None
        paket_toplami = sum(
            ((kalemler.get(t["id"]) or {}).get("segmentler") or {}).get("orta", {}).get("medyan", 0)
            for t in conf["kalemler"] if t.get("olcum_turu") == "paket_fiyati")
        sira = [x for x in aralik_siralamasi(veri, vertikal) if not x["toplam_harici"]]
        if len(sira) < 3:
            return None
        en_genis, en_dar = sira[0], sira[-1]
        # IDDIALAR VERIYE BAGLI (2026-08-01, gercek hata sonrasi).
        # Ilk hal kedi verisine gore yazilmisti: "X ucta duruyor" ve
        # somut ornek olarak "bir ucta duz kap, obur ucta otomatik
        # sistem". Kedide dogruydu (28,5x'e karsi 6,0x, ve kalem
        # gercekten kedi tuvaleti). Kopekte AYNI metin uretiliyordu
        # ama orada en genis kalem YATAK ve siralama 5,8/5,2/5,1/4,5
        # -- ne bir uc var ne de "otomatik sistem" diye bir sey.
        # Artik: uc ancak ikinciden belirgin ayrisiyorsa "uc" denir,
        # dar ancak gercekten darsa "dar" denir, ve urun tipi
        # ORNEKLE ANLATILMAZ (hangi kalem oldugunu bilemeyiz).
        gercek_uc = en_genis["kat"] >= 2 * sira[1]["kat"]
        gercek_dar = en_dar["kat"] <= 2.0
        pahali = max((x for x in sira), key=lambda x: x["orta"])

        return f"""
  <p class="cevap-blok">
    {ad} sahiplenmeden önce ölçebildiğimiz tek karşılaştırılabilir toplam
    <strong>{_p(kurulum)}</strong> tutarındaki başlangıç kurulumudur.
    Tekrarlayan ürünlerden birer paketlik alışveriş göstergesi
    <strong>{_p(paket_toplami)}</strong>; paket boyu ve tüketim normalize
    edilmediği için bu rakam aylık gider değildir.
  </p>

  <h2>Kurulumda parayı belirleyen tek kalem</h2>
  <p>
    Ölçtüğümüz {len(sira)} tek seferlik kalemin içinde
    <strong>{pahali["ad"].lower()}</strong> tek başına {_p(pahali["orta"])}
    ile en büyük tutar. Bütçeyi burada verdiğiniz karar belirliyor;
    diğer kalemlerin toplamı bunun yanında küçük kalıyor.
  </p>

  <h2>Hangi kalemde seçim gerçekten fark ediyor?</h2>
  <p>
    Bunu tahmin etmek yerine ölçtük. Her kalemin ekonomik ve üst
    segmenti arasındaki fark şöyle:
  </p>
{_aralik_tablosu(sira)}
  <p>
    Listenin başındaki <strong>{en_genis["ad"].lower()}</strong> kaleminde
    ekonomik ile üst segment arasında {su._kat(en_genis["kat"])} kat fark var{
    " ve bu kalem diğerlerinden belirgin şekilde ayrışıyor" if gercek_uc else ""}.
    Ama geniş aralık "pahalısı daha kaliteli" demek değil: aynı isim
    altında <em>farklı ürün tipleri</em> listeleniyor — en yalın modelle
    en donanımlısı aynı kategoride duruyor.
    <strong>Yani burada verilecek ilk karar marka değil, tip kararı.</strong>
  </p>
  <p>
    Listenin sonundaki <strong>{en_dar["ad"].lower()}</strong> kaleminde
    fark {su._kat(en_dar["kat"])} kata iniyor. {
    "Bu kadar dar bir aralıkta ürünler birbirine yakın demektir; üst segmente çıkmanın bütçeye etkisi sınırlı."
    if gercek_dar else
    "Yani bu listede aralığı gerçekten dar bir kalem yok — hangi kalemde ne seçtiğiniz bütçeyi baştan sona etkiliyor."}
  </p>

  <h2>Bu rakamlara girmeyen ve muhtemelen daha çok tutacak şey</h2>
  <p>
    Veteriner, aşı, kısırlaştırma, mikroçip. Bunları <em>ölçmüyoruz</em>
    çünkü klinikten kliniğe değişiyor ve internette liste fiyatı olarak
    yayınlanmıyor. Pet kuaförü, pansiyon ve eğitim de dışarıda. Bu nedenle
    yukarıdaki rakamlardan gerçek yıllık gider ya da alt sınır türetilemez.
    Sahiplenmeden önce bir kliniğe telefon açıp
    kısırlaştırma ve ilk yıl aşı takvimini sormak, bu yazıdaki bütün
    rakamlardan daha çok işinize yarar.
  </p>

  <h2>Hayvanın kendisi hesapta yok</h2>
  <p>
    Sahiplenme ücretsizdir. Satın almayı ne ölçüyoruz ne teşvik
    ediyoruz — barınaklarda ve sokakta sahiplenmeyi bekleyen hayvan
    varken bu bir maliyet kalemi değil.
  </p>

  <h2>Neyi söylemiyoruz</h2>
  <p>
    Bakım, beslenme ve sağlık tavsiyesi vermiyoruz. Biz fiyat ölçüyoruz;
    hangi mamanın iyi olduğu ya da hangi aşının ne zaman yapılacağı
    veterinerin işi. Bu sayfada göreceğiniz her cümlenin arkasında bir
    ölçüm var, olmadığı yerde de bunu yazıyoruz.
  </p>
  <p>
    Kalem kalem güncel fiyatlar <a href="/{vertikal}/">{ad.lower()} masrafı
    sayfasında</a>; kendi listenizi
    <a href="/{vertikal}/hesaplayici/">hesaplayıcıdan</a> çıkarabilirsiniz.
    Yalnızca her ay tekrar eden sarf hesabı
    <a href="/rehber/aylik-{vertikal}-masrafi/">aylık {ad.lower()} masrafı
    rehberinde</a>.
    {oteki_ad} ile karşılaştırma
    <a href="/rehber/kedi-mi-kopek-mi-masrafli/">şurada</a>.
  </p>
"""
    return govde


# ---------------------------------------------------------------------------
# 18. Ev kurarken nerede tasarruf edilir (TAVSIYE)
# Ayni aralik olcusu, bu kez 42 kalemlik bir listede: hangi kalemde
# pazarlik/segment dusurmek gercekten para kazandiriyor.
# ---------------------------------------------------------------------------
def _govde_nerede_tasarruf(v: dict) -> str | None:
    veri = v.get("ev-kurma")
    if not veri:
        return None
    sira = aralik_siralamasi(veri, "ev-kurma")
    if len(sira) < 10:
        return None
    conf = su.VERTIKALLER["ev-kurma"]
    kalemler = veri.get("kalemler") or {}
    orta, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "orta")
    eko, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "ekonomik")
    dar = sira[-5:][::-1]
    # En cok para birakan hamle: kalem bazinda orta -> ekonomik TL farki
    kazanc = sorted(sira, key=lambda x: x["orta"] - x["eko"], reverse=True)[:5]
    kazanc_satir = "".join(
        '<tr><td>{ad}</td><td class="sayi">{o}</td><td class="sayi">{e}</td>'
        '<td class="sayi">−{f}</td></tr>'.format(
            ad=x["ad"], o=_p(x["orta"]), e=_p(x["eko"]), f=_p(x["orta"] - x["eko"]))
        for x in kazanc)
    ilk_uc = sum(x["orta"] - x["eko"] for x in kazanc[:3])

    return f"""
  <p class="cevap-blok">
    Orta segmentte sıfırdan ev kurmak <strong>{_p(orta)}</strong>, ekonomik
    tercihlerle <strong>{_p(eko)}</strong> tutuyor — arada
    {_p(orta - eko)} var. Ama bu farkın hepsini kovalamak gerekmiyor:
    <strong>yalnızca üç kalemde segment düşürmek {_p(ilk_uc)} bırakıyor.</strong>
  </p>

  <h2>Parayı bırakan üç beş kalem</h2>
  <p>
    Ölçtüğümüz {len(sira)} kalemi, orta segmentten ekonomiğe inince kaç
    lira kazandırdığına göre sıraladık:
  </p>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th class="sayi">Orta</th><th class="sayi">Ekonomik</th><th class="sayi">Kazanç</th></tr></thead>
    <tbody>{kazanc_satir}</tbody>
  </table></div>
  <p>
    Listenin geri kalanında tek tek uğraşmanın karşılığı küçük. Kırk
    kalemin hepsinde ucuzunu aramak yerine bu birkaçına odaklanmak,
    aynı tasarrufu çok daha az yorularak veriyor.
  </p>

  <h2>Nerede ucuza kaçmanın karşılığı yok</h2>
  <p>
    Bunun tersi de veriden çıkıyor. Bazı kalemlerde ekonomik ile üst
    segment arasındaki fark o kadar dar ki, o kategoride ürünler
    birbirine benziyor demektir:
  </p>
{_aralik_tablosu(dar)}
  <p>
    Örneğin {dar[0]["ad"].lower()} kaleminde ekonomikten üste çıkmak
    fiyatı yalnızca {su._kat(dar[0]["kat"])} katına çıkarıyor. Buralarda
    "en ucuzunu bulayım" diye vakit harcamak, kazandırdığından fazlasını
    götürüyor.
  </p>

  <h2>Bir uyarı: geniş aralık her zaman kalite farkı değil</h2>
  <p>
    {sira[0]["ad"]} kaleminde ekonomik ile üst arasında
    {su._kat(sira[0]["kat"])} kat var. Bu, pahalısının {su._kat(sira[0]["kat"])} kat
    iyi olduğu anlamına gelmiyor — o kategoride farklı <em>ürün tipleri</em>
    aynı isimle listeleniyor. Önce hangi tipi istediğinize karar verin;
    marka karşılaştırması ondan sonra anlamlı.
  </p>

  <h2>Ölçmediğimiz için söylemediğimiz şey</h2>
  <p>
    "Şu markayı alın", "şu üründen kaçının" demiyoruz. Dayanıklılık ve
    servis kalitesi bizim ölçtüğümüz şeyler değil; fiyat ölçüyoruz. Aynı
    sebeple "pazarlık yapın, %10 indirim alırsınız" gibi bir tasarruf da
    önermiyoruz — onu ölçemiyoruz, o yüzden yazmıyoruz.
  </p>
  <p>
    Kendi listenizi <a href="/ev-kurma/hesaplayici/">hesaplayıcıdan</a>
    çıkarabilir, bütçenizi girip hangi kalemde ne yapmanız gerektiğini
    orada görebilirsiniz. Kalem kalem fiyatlar
    <a href="/ev-kurma/">ev kurma endeksinde</a>.
  </p>
"""


# ---------------------------------------------------------------------------
# 19. Bebek alisverisinde nelere dikkat (TAVSIYE)
# ---------------------------------------------------------------------------
def _govde_bebek_tavsiye(v: dict) -> str | None:
    veri = v.get("bebek")
    if not veri:
        return None
    conf = su.VERTIKALLER["bebek"]
    kalemler = veri.get("kalemler") or {}
    hazirlik, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "orta")
    if not hazirlik:
        return None
    bez = ((kalemler.get("bebek-bezi") or {}).get("segmentler") or {}).get("orta", {}).get("medyan", 0)
    sira = [x for x in aralik_siralamasi(veri, "bebek") if not x["toplam_harici"]]
    if len(sira) < 3:
        return None
    pahali = sorted(sira, key=lambda x: x["orta"], reverse=True)[:3]
    pahali_toplam = sum(x["orta"] for x in pahali)

    return f"""
  <p class="cevap-blok">
    Tek seferlik bebek hazırlığı orta segmentte <strong>{_p(hazirlik)}</strong>.
    Bunun <strong>{_p(pahali_toplam)}</strong>'si yalnızca üç kalemden
    geliyor: {", ".join(x["ad"].lower() for x in pahali)}. Yani listenin
    tamamını dert etmek yerine bu üçünde doğru kararı vermek, bütçenin
    büyük kısmını çözüyor.
  </p>

  <h2>Bez paket fiyatı ayrı ölçüm</h2>
  <p>
    Bebek bezi tekrar alınan bir ürün; ölçümümüzdeki {_p(bez)} ise aylık
    tüketim değil kategori paket medyanı. Paket adedi ve günlük kullanım
    aynı birime çevrilmediği için hazırlık toplamına katmıyor, on ikiyle
    çarpmıyoruz. Bütçe kurarken adet başı fiyatı ve kendi tüketiminizi
    kullanmanız gerekir.
  </p>

  <h2>Hangi kalemde seçim bütçeyi değiştiriyor?</h2>
{_aralik_tablosu(sira)}
  <p>
    Üstteki kalemlerde ekonomik ile üst segment arasında büyük fark var;
    alttakilerde ürünler birbirine yakın. Ama bu tablo "pahalısını alın"
    demek değil — geniş aralık genelde o kategoride
    <em>farklı ürün tiplerinin</em> aynı isimle listelenmesinden geliyor.
  </p>

  <h2>Güvenlik bizim ölçtüğümüz şey değil</h2>
  <p>
    Oto koltuğu ve beşik gibi kalemlerde asıl kriter fiyat değil
    <strong>güvenlik standardı</strong> — ve biz onu ölçmüyoruz. Fiyat
    tablosuna bakıp en ucuzu seçmek bu iki kalemde doğru yöntem değil;
    ürünün taşıdığı belge ve standart, bizim verebileceğimiz her
    rakamdan önce gelir. Bunu yazmak zorundayız çünkü sayfada fiyat
    sıralaması var ve tek başına yanıltıcı olabilir.
  </p>

  <h2>İkinci el ve devralma bu hesapta yok</h2>
  <p>
    Ölçtüğümüz rakam "her şeyi bugün, sıfır ve yeni al" senaryosu.
    Pratikte bebek eşyasının önemli kısmı devralınıyor ya da ikinci el
    alınıyor; ikinci el fiyatı ürünün durumuna göre değiştiği için tek
    bir sayıyla ölçülemiyor, o yüzden kapsam dışında.
  </p>
  <p>
    İlk yılın toplamı <a href="/rehber/bebek-masraflari-ilk-yil/">şurada</a>,
    kalem kalem fiyatlar <a href="/bebek/">bebek masrafları endeksinde</a>.
  </p>
"""


# ---------------------------------------------------------------------------
# 20. Ozel hastanede dogum maliyeti (2026-08-02, Yavuz'un istegi)
#
# BU YAZI RAKAM VERMIYOR VE SEBEBI YAZININ KENDISI.
# Ozel hastanelerin dogum paketi fiyatlari internette LISTE HALINDE
# YAYINLANMIYOR; telefonla ya da hastaneye gidilerek soruluyor.
# Olcemedigimiz bir seye "ortalama dogum 80 bin TL" yazmak KIRMIZI
# CIZGI ihlali olurdu - ve bu sorguda tam olarak boyle yapan cok
# sayfa var, hepsi kaynaksiz.
#
# Bizim verebilecegimiz sey: MEKANIZMAYI dogru anlatmak, hangi
# rakamin nereden ogrenilecegini soylemek ve olctugumuz kismi
# (dogum sonrasi hazirlik) gercek veriyle vermek.
#
# ILAVE UCRET TAVAN ORANI YAZILMADI: oran Cumhurbaskani kararina
# bagli ve degisiyor; birincil kaynaktan (Resmi Gazete / SGK tebligi)
# guncel oranı DOGRULAYAMADIM. Dogrulanmamis bir yuzde yazmak yerine
# SGK'nin kendi ilave ucret sorgu ekranina yonlendiriliyor - hem
# dogru hem bayatlamaz. Oran birincil kaynaktan dogrulanirsa buraya
# tebliğ adi ve R.G. tarih/sayisiyla eklenebilir.
# ---------------------------------------------------------------------------
def _govde_dogum_maliyeti(v: dict) -> str | None:
    b = v.get("bebek")
    if not b:
        return None
    conf = su.VERTIKALLER["bebek"]
    kalemler = b.get("kalemler") or {}
    hazirlik, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "orta")
    eko, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "ekonomik")
    if not hazirlik:
        return None
    bez = ((kalemler.get("bebek-bezi") or {}).get("segmentler") or {}).get("orta", {}).get("medyan", 0)

    return f"""
  <p class="cevap-blok">
    Dürüst cevap: <strong>özel hastane doğum ücretini ölçemiyoruz, o
    yüzden bir rakam yazmıyoruz.</strong> Hastaneler doğum paketi
    fiyatlarını internette liste halinde yayınlamıyor; fiyat telefonla
    ya da hastaneye gidilerek, üstelik gebelik haftasına ve doktora
    göre değişerek veriliyor. Ölçemediğimiz bir şeye tahmin yazmak bu
    sitenin kuralına aykırı.
  </p>

  <h2>Peki bu sayfa ne işe yarıyor?</h2>
  <p>
    İki işe. Birincisi: doğum ücretinin nasıl belirlendiğini bilirseniz
    aldığınız teklifi değerlendirebilirsiniz. İkincisi: doğumdan sonra
    gelen ve <em>ölçülebilen</em> masrafı buradan görebilirsiniz.
  </p>

  <h2>SGK'lıysanız ödeyeceğiniz şeyin adı "ilave ücret"</h2>
  <p>
    Genel sağlık sigortası kapsamındaysanız ve gittiğiniz özel hastane
    <strong>SGK ile sözleşmeliyse</strong>, doğumun bedelini SGK
    karşılar; hastane size ancak kanunun izin verdiği sınır içinde
    <strong>ilave ücret</strong> isteyebilir. Yani ödediğiniz şey
    doğumun tamamı değil, bu farktır.
  </p>
  <p>
    Tavan oran Cumhurbaşkanı kararıyla belirleniyor ve değişebiliyor.
    Bu yüzden buraya bir yüzde yazmıyoruz — <strong>eskiyeceği kesin bir
    sayıyı sabitlemek yerine</strong> kaynağı veriyoruz: gideceğiniz
    hastanenin sözleşmeli olup olmadığını ve uygulanan ilave ücret
    oranını
    <a href="https://gss.sgk.gov.tr/SaglikHizmetSunuculari/pages/ilaveUcretHesaplama.faces"
       rel="nofollow noopener" target="_blank">SGK'nın ilave ücret sorgu
    ekranından</a> doğrudan öğrenebilirsiniz.
  </p>
  <p>
    Sözleşmesiz bir özel hastaneye giderseniz durum değişir: orada
    fiyatı tamamen hastane belirler ve SGK katkısı çok daha sınırlı
    kalır. Acil hâllerde ilave ücret alınamayacağı da ayrıca
    düzenlenmiştir.
  </p>

  <h2>Teklif alırken sorulacak şeyler</h2>
  <p>
    Bunlar fiyat tahmini değil, aldığınız teklifi karşılaştırılabilir
    kılan sorular — çünkü iki hastanenin "doğum paketi" dediği şey aynı
    olmayabiliyor:
  </p>
  <ul>
    <li>Hastane SGK ile sözleşmeli mi? Alınan ilave ücret oranı ne?</li>
    <li>Fiyat normal doğum için mi, sezaryen dâhil mi? Sezaryene
      dönerse fark alınıyor mu?</li>
    <li>Kaç gece yatış dâhil? Oda tipi ne? Fazla gecenin bedeli ne?</li>
    <li>Doktor ücreti pakete dâhil mi, ayrı mı?</li>
    <li>Epidural, yenidoğan yoğun bakım ihtimali ve tarama testleri
      pakette mi?</li>
    <li>Teklif yazılı veriliyor mu? (İlave ücret için işlemden
      <em>önce</em> yazılı onay alınması gerekiyor.)</li>
  </ul>

  <h2>Ölçebildiğimiz kısım: doğumdan sonrası</h2>
  <p>
    Hastane faturası bittiğinde masraf bitmiyor. Bebeğin tek seferlik
    hazırlığı orta segmentte <strong>{_p(hazirlik)}</strong>, ekonomik
    tercihlerle <strong>{_p(eko)}</strong>. Bebek bezinde ölçülen {_p(bez)}
    kategori paket medyanıdır; paket adedi ve tüketim normalize edilmediği
    için aylık ya da yıllık gider olarak sunulmaz.
  </p>
  <p>
    Bu rakamlar gerçek satış sitelerinden ölçülüyor. Kaynaklar ayın 5'i ve
    20'sinde yeniden taranıyor; kalem kalem dökümü
    <a href="/bebek/">bebek masrafları endeksinde</a>, ilk yıl hesabının
    veri sınırı <a href="/rehber/bebek-masraflari-ilk-yil/">şurada</a>.
    Neye ne kadar ayırmanız gerektiğine
    <a href="/bebek/hesaplayici/">hesaplayıcıdan</a> karar
    verebilirsiniz.
  </p>

  <h2>Neden başka sitelerde rakam var da bizde yok?</h2>
  <p>
    Çünkü o rakamların çoğunun arkasında bir ölçüm yok. Doğum ücreti
    hastaneye, şehre, doktora, oda tipine ve gebeliğin seyrine göre
    değişen bir hizmet bedeli; tek bir "ortalama" vermek kolay ama
    yanıltıcı. Bu kalemde yayınlanmış bir fiyat listesine ulaşırsak
    ölçer ve buraya kaynağıyla ekleriz — bulamadığımız sürece
    bulamadığımızı yazarız.
  </p>
"""


# ---------------------------------------------------------------------------
# 21. Dogumdan once alinacaklar listesi (UZUN KUYRUK)
# "hastane cantasi" / "dogum oncesi alinacaklar" cok aranan bir sorgu;
# bizim farkimiz listeyi FIYATLA vermek.
# ---------------------------------------------------------------------------
def _govde_dogum_oncesi(v: dict) -> str | None:
    b = v.get("bebek")
    if not b:
        return None
    conf = su.VERTIKALLER["bebek"]
    kalemler = b.get("kalemler") or {}
    hazirlik, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "orta")
    eko, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "ekonomik")
    if not hazirlik:
        return None
    tek = []
    for t in conf["kalemler"]:
        if t.get("varsayilan_dahil") is False:
            continue
        m = ((kalemler.get(t["id"]) or {}).get("segmentler") or {}).get("orta", {}).get("medyan")
        if m:
            tek.append((m, t["ad"]))
    tek.sort(reverse=True)
    if len(tek) < 4:
        return None
    satir = "".join(
        f'<tr><td>{ad}</td><td class="sayi">{_p(m)}</td></tr>' for m, ad in tek)
    ilk3 = sum(m for m, _ in tek[:3])
    pay = ilk3 / hazirlik * 100

    return f"""
  <p class="cevap-blok">
    Doğumdan önce alınan tek seferlik eşyanın toplamı orta segmentte
    <strong>{_p(hazirlik)}</strong>, ekonomik tercihlerle
    <strong>{_p(eko)}</strong>. Listenin uzunluğu göz korkutuyor ama
    rakamı belirleyen üç kalem var:
    <strong>{", ".join(ad.lower() for _, ad in tek[:3])}</strong> —
    tek başlarına toplamın <strong>%{pay:.0f}</strong>'ini oluşturuyor.
  </p>

  <h2>Liste ve güncel fiyatlar</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th class="sayi">Orta segment</th></tr></thead>
    <tbody>{satir}</tbody>
  </table></div>
  <p>
    Bunlar tek seferlik alınan şeyler. Bebek bezi gibi tekrar alınan paketli
    ürünler bu toplama girmiyor; adet ve tüketim normalize edilmeden ikisini
    birleştirmek ne olduğu belirsiz bir rakam üretirdi.
  </p>

  <h2>Hepsi doğumdan önce alınmak zorunda değil</h2>
  <p>
    Listenin üst sıraları (bebek arabası, oto koltuğu, beşik) doğum
    günü lazım; alt sıralardaki çoğu kalem birkaç ay sonra da alınabilir.
    Mama sandalyesi ek gıdaya geçilene kadar, park yatak bebek
    yuvarlanmaya başlayana kadar kullanılmıyor. Bütçeyi zamana yaymanın
    en kolay yeri burası.
  </p>
  <p>
    Oto koltuğu bunun istisnası: hastaneden çıkışta gerekiyor ve burada
    asıl kriter fiyat değil <strong>güvenlik standardı</strong> — onu
    biz ölçmüyoruz, ürünün taşıdığı belgeye bakın.
  </p>

  <h2>Ölçtüğümüz şey "her şey sıfır ve yeni" senaryosu</h2>
  <p>
    Pratikte bebek eşyasının önemli kısmı devralınıyor ya da ikinci el
    alınıyor. İkinci el fiyatı ürünün durumuna göre değiştiği için tek
    bir sayıyla ölçülemiyor, o yüzden kapsam dışında. Yani üstteki
    tutar bir <em>üst sınır</em>: gerçek harcamanız büyük olasılıkla
    bunun altında kalacak.
  </p>
  <p>
    Kendi listenizi <a href="/bebek/hesaplayici/">hesaplayıcıdan</a>
    çıkarabilir, hastane tarafını
    <a href="/rehber/ozel-hastanede-dogum-maliyeti/">doğum maliyeti
    yazısından</a> okuyabilirsiniz.
  </p>
"""


# ---------------------------------------------------------------------------
# 22. Damatlik kiralamak mi almak mi (2026-08-09, Search Console)
#
# "damatlik kiralama fiyatlari 2026", "gelinlik kiralama fiyatlari 2026",
# "gelinlik tadilat fiyatlari" sorgulari gosterim aliyordu. Damatlik zaten
# TEK TIKLAMA ALDIGIMIZ sayfa (48 gosterim, 1 tik) - komsu niyeti
# yakalamak icin en dogru yer.
#
# KIRALAMA FIYATI OLCEMIYORUZ ve bu yazi onu ilk cumlede soyluyor.
# Yazinin degeri kiralama fiyati vermek DEGIL, karari kurmanin yolunu
# vermek: satin almanin rakami bizde olculmus, kiralama teklifini onunla
# karsilastirmak icin gereken cerceve kurulabiliyor.
# ---------------------------------------------------------------------------
def _govde_damatlik_kiralama(v: dict) -> str | None:
    d = v.get("dugun")
    if not d:
        return None
    k = (d.get("kalemler") or {}).get("damatlik") or {}
    seg = k.get("segmentler") or {}
    if not seg.get("orta"):
        return None
    eko, orta, ust = seg["dusuk"]["medyan"], seg["orta"]["medyan"], seg["luks"]["medyan"]

    return f"""
  <p class="cevap-blok">
    Önce dürüst olalım: <strong>kiralama fiyatı ölçmüyoruz.</strong> Damatlık
    kiralama bedelleri internette liste halinde yayınlanmıyor; mağazadan
    sorularak, üstelik sezona ve modele göre değişerek veriliyor. Ama
    <em>satın almanın</em> rakamı bizde ölçülü: ekonomik {_p(eko)},
    orta segment <strong>{_p(orta)}</strong>, üst segment {_p(ust)}.
    Aldığınız kiralama teklifini bu rakamlarla karşılaştırabilirsiniz.
  </p>

  <h2>Kararı kurmanın basit yolu</h2>
  <p>
    Tek soru var: <strong>kira bedeli, satın alma fiyatının kaçta kaçı?</strong>
    Orta segment bir takım {_p(orta)} tutuyorsa, bunun üçte birini aşan bir
    kiralama teklifi ekonomik olarak zayıflar — çünkü satın alsanız takım
    elinizde kalır ve ikinci kez giyilebilir.
  </p>
  <ul>
    <li><strong>Kira, satın almanın %25'inin altındaysa:</strong> tek
      kullanımda kiralama net avantajlı.</li>
    <li><strong>%25–40 arasındaysa:</strong> takımı bir daha giyip
      giymeyeceğinize bakın. İki kez giyecekseniz satın alma başa baş
      gelir.</li>
    <li><strong>%40'ın üzerindeyse:</strong> aynı paraya sahip olacağınız
      bir takım varken kiralamak zorlaşır.</li>
  </ul>
  <p>
    Bu eşikler bir formül değil, elimizdeki satın alma rakamından çıkan
    aritmetik bir çerçeve. Kiralamanın kendi rakamını ölçemediğimiz için
    "kiralama şu kadar" demiyoruz — teklifi siz alıp bu çerçeveye
    koyacaksınız.
  </p>

  <h2>Kiralamada fiyata dahil olmayanlar</h2>
  <p>
    Teklif alırken karşılaştırmayı bozan kalemler bunlar; sormadan
    kıyaslamak yanıltıcı olur:
  </p>
  <ul>
    <li><strong>Tadilat.</strong> Kiralıkta çoğu zaman sınırlı tadilat
      yapılır (paça, kol boyu); belden ciddi daraltma genelde mümkün
      değil. Satın almada tadilat sıklıkla fiyata dahil.</li>
    <li><strong>Depozito.</strong> İade edilir ama düğün öncesi nakit
      bağlar.</li>
    <li><strong>Gecikme ve hasar bedeli.</strong> Sözleşmede yazar,
      teklifte yazmaz.</li>
    <li><strong>Gömlek, kravat, ayakkabı, kol düğmesi.</strong> Kiralama
      paketine dahil olup olmadığı mağazaya göre değişiyor; satın almada
      zaten ayrı kalem.</li>
  </ul>

  <h2>Gelinlikte durum aynı değil</h2>
  <p>
    Gelinlik tarafında satın alma rakamımız yalnızca <em>bir</em> kaynaktan
    geliyor ve o da bir pazaryeri — gelinlik evlerinin fiyatları
    yayınlanmıyor. Yani gelinlikte yukarıdaki karşılaştırmayı kurmak için
    sağlam bir taban rakamımız yok. Bunu neden söylediğimizi
    <a href="/rehber/gelinlik-mi-damatlik-mi-pahali/">şurada</a> yazdık.
  </p>

  <h2>Bu sayfada neden fiyat listesi yok?</h2>
  <p>
    Çünkü ölçmediğimiz bir şeye rakam yazmıyoruz. Bu sorguda hazır fiyat
    listesi veren çok sayfa var; hiçbirinin arkasında tarihli, örneklemli
    bir ölçüm yok. Yayınlanmış bir kiralama fiyat listesine ulaşırsak
    ölçer ve kaynağıyla buraya ekleriz.
  </p>
  <p>
    Güncel satın alma fiyatları
    <a href="/dugun/damatlik-fiyatlari/">damatlık fiyatları sayfasında</a>;
    aradaki kaynak farkının neden bu kadar büyük olduğu
    <a href="/rehber/damatlik-kac-para/">şurada</a>.
  </p>
"""


def _govde_kart_puanlari(v: dict) -> str | None:
    """Resmi kaynakli rehber.

    Bu sayfa fiyat olcumu degil; bankalarin resmi program metinlerinden
    derlenen karar rehberi. Magaza listesini elle kopyalamiyoruz, cunku
    uye isyeri ve kampanya kosulu canli degisir.
    """
    return """
  <p class="cevap-blok">
    Kısa cevap: <strong>ParafPara Paraf üye işyerlerinde, Chip-Para Axess
    üye işyerlerinde, Bonus ise Bonus Card anlaşmalı işyerlerinde geçer.</strong>
    Üç programda da temel mantık 1 puan = 1 TL'dir; ama puanı gerçekten
    harcayıp harcayamayacağınızı POS/online ödeme entegrasyonu ve kampanya
    şartı belirler.
  </p>

  <h2>Üç programın farkı</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Program</th><th>Nerede geçer?</th><th>Dikkat edilmesi gereken</th></tr></thead>
    <tbody>
      <tr>
        <td><strong>ParafPara</strong></td>
        <td>Paraf üye işyerlerinde ve kampanya koşullarının izin verdiği alışverişlerde.</td>
        <td>Kampanyaya katılım, sektör ve pazar yeri istisnaları sayfaya göre değişebilir.</td>
      </tr>
      <tr>
        <td><strong>Chip-Para</strong></td>
        <td>Axess üye işyerlerinde; online tarafta entegre sanal mağazalarda.</td>
        <td>Mağazanın Axess üyesi olması yetmeyebilir; ödeme adımında chip-para harcama seçeneği görünmeli.</td>
      </tr>
      <tr>
        <td><strong>Bonus</strong></td>
        <td>Bonus Card anlaşmalı markalarda ve Bonus'un canlı marka listesindeki işyerlerinde.</td>
        <td>Genel marka listesi ayrı, tek tek kampanya şartları ayrı okunmalı.</td>
      </tr>
    </tbody>
  </table></div>

  <h2>Neden burada uzun mağaza listesi yok?</h2>
  <p>
    Çünkü bu konu bayatlamaya çok açık. Bugün geçerli olan bir market,
    akaryakıt istasyonu ya da e-ticaret mağazası yarın kampanyadan çıkabilir;
    aynı markanın fiziksel POS'u puan harcatırken online ödeme ekranı
    harcatmayabilir. Kopyalanmış "nerelerde geçer" listeleri bu yüzden güvenli
    değil. Doğru cevap, markanın resmi canlı listesine gitmek ve ödeme
    adımında puan kullanımı görünüyor mu diye kontrol etmektir.
  </p>

  <h2>Kampanya şartında bakılacak üç satır</h2>
  <p>
    Puanın geçip geçmediğini anlamak için kampanya metninde şu üç satırı
    arayın. Bunlardan biri tersse, marka listede olsa bile beklediğiniz puanı
    kazanamayabilir ya da harcayamayabilirsiniz.
  </p>
  <ul>
    <li><strong>Katılım şartı:</strong> SMS, mobil uygulama ya da çağrı merkeziyle
      kampanyaya katılım isteniyor mu?</li>
    <li><strong>Hariç tutulan yerler:</strong> pazar yerleri, cüzdan/ödeme kuruluşları,
      akaryakıt, vergi, sigorta veya taksitli işlemler dışarıda mı?</li>
    <li><strong>Yükleme ve son kullanım:</strong> puan ne zaman yükleniyor,
      hangi tarihe kadar harcanmalı?</li>
  </ul>

  <h2>Doğru kontrol sırası</h2>
  <p>
    Önce bankanın resmi marka/üye işyeri sayfasına bakın. Sonra alışveriş
    yapacağınız kampanyanın kendi koşullarını okuyun. Online alışverişte son
    kontrol ödeme ekranıdır: puanla ödeme alanı çıkmıyorsa, müşteri hizmetleri
    "üye işyeri" dese bile işlemde puan harcama açık olmayabilir.
  </p>

  <h2>Maliyeti nasıl etkiler?</h2>
  <p>
    Puan gerçek indirim gibi düşünülürse hata azalır: harcanabilir puan,
    sonraki alışverişte nakit çıkışını azaltır. Ama sadece puan kazanmak
    için daha pahalı mağazadan alışveriş yapmak çoğu zaman toplam maliyeti
    artırır. Kart borcunu erteleyerek puan kovalamadan önce
    <a href="/hesap/kredi-karti-borcu-hesaplama/">kredi kartı borcu
    hesaplayıcısıyla</a> faiz yükünü kontrol edin.
  </p>
"""


def _govde_okul_pahali_kalemler(v: dict) -> str | None:
    o = v.get("okul")
    if not o:
        return None
    conf = su.VERTIKALLER["okul"]
    toplam, detaylar = su.ornek_toplam_hesapla(
        conf, o.get("kalemler") or {}, olcek=1, segment="orta"
    )
    dahil = sorted(
        (d for d in detaylar if d.get("toplama_dahil") and d.get("satir_toplam")),
        key=lambda d: d["satir_toplam"],
        reverse=True,
    )
    if not toplam or len(dahil) < 5:
        return None
    ilk_bes = dahil[:5]
    ilk_bes_toplam = sum(d["satir_toplam"] for d in ilk_bes)
    sayfalar = [
        *conf.get("kalem_sayfalari", []),
        *su._ek_kalem_sayfalari(conf, o.get("kalemler") or {}),
    ]
    sluglar = {s["id"]: s["slug"] for s in sayfalar}
    satirlar = "".join(
        f'<tr><td><a href="/okul/{sluglar[d["id"]]}/">{html.escape(d["ad"])}</a></td>'
        f'<td class="sayi">{_p(d["satir_toplam"])}</td>'
        f'<td class="sayi">%{d["satir_toplam"] / toplam * 100:.0f}</td></tr>'
        for d in ilk_bes if d["id"] in sluglar
    )
    return f"""
  <p class="cevap-blok">
    Okul alışverişi sepetinde en pahalı beş kalem birlikte
    <strong>{_p(ilk_bes_toplam)}</strong> tutuyor ve ölçülen orta segment
    sepetinin %{ilk_bes_toplam / toplam * 100:.0f}'ini oluşturuyor. Bu,
    okulun yıllık toplam gideri değil; yalnızca sitede tanımlı alışveriş
    sepetinin dağılımı.
  </p>

  <h2>Sepette en yüksek payı alan kalemler</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th class="sayi">Orta segment</th><th class="sayi">Sepetteki pay</th></tr></thead>
    <tbody>{satirlar}</tbody>
  </table></div>
  <p>
    Sıralama ve yüzdeler sayfa üretilirken güncel okul verisinden yeniden
    hesaplanır. Fiyat değiştiğinde üstteki cevap da tablo da aynı veriyle
    birlikte değişir.
  </p>

  <h2>Bu karşılaştırmanın sınırı</h2>
  <p>
    Kayıt ücreti, bağış, servis, yemek ve özel okul ücreti ölçüm kapsamı
    dışında. Tablet, çalışma masası ve sandalye ise isteğe bağlı ve uzun
    ömürlü ürünler olduğu için varsayılan sepete eklenmiyor. Bu kalemleri
    dahil ederek sonucu <a href="/okul/hesaplayici/">okul alışverişi
    hesaplayıcısında</a> kişiselleştirebilirsiniz.
  </p>

  <h2>Kalem sayısı kadar adet de önemli</h2>
  <p>
    Tek bir çanta ile tek bir defterin fiyatını yan yana koymak, gerçek
    alışveriş adetlerini açıklamaz. Bu sayfa mevcut varsayılan sepette her
    kalemi bir kez sayar. Okulun verdiği ihtiyaç listesinde aynı üründen
    birden fazla isteniyorsa hesabı adetle çarpmak gerekir.
  </p>
"""


def _govde_marka_giris_fiyatlari(v: dict) -> str | None:
    a = v.get("arac")
    if not a:
        return None
    kalem = (a.get("kalemler") or {}).get("en-ucuz-sifir-arac") or {}
    ornekler = []
    for kaynak in kalem.get("kaynaklar") or []:
        ornekler.extend(kaynak.get("ornek_urunler") or [])
    benzersiz = {}
    for urun in ornekler:
        isim = str(urun.get("isim") or "").strip()
        fiyat = urun.get("fiyat")
        if isim and fiyat:
            benzersiz[(isim.casefold(), fiyat)] = {"isim": isim, "fiyat": fiyat}
    sirali = sorted(benzersiz.values(), key=lambda u: (u["fiyat"], u["isim"].casefold()))
    if len(sirali) < 5:
        return None
    gosterilen = sirali[:10]
    ortanca = kalem.get("genel_medyan")
    tarih = kalem.get("guncelleme_tarihi")
    satirlar = "".join(
        f'<tr><td>{i}</td><td>{html.escape(u["isim"])}</td>'
        f'<td class="sayi">{_p(u["fiyat"])}</td></tr>'
        for i, u in enumerate(gosterilen, start=1)
    )
    return f"""
  <p class="cevap-blok">
    {tarih} ölçümünde en düşük yayımlanmış marka giriş fiyatı
    <strong>{html.escape(sirali[0]["isim"])}</strong> için
    <strong>{_p(sirali[0]["fiyat"])}</strong>. Marka giriş fiyatlarının
    ortancası {_p(ortanca)}; en ucuz araç cevabıyla piyasanın orta noktasını
    aynı rakam gibi kullanmıyoruz.
  </p>

  <h2>En düşük marka giriş fiyatları</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Sıra</th><th>Marka / giriş modeli</th><th class="sayi">Liste fiyatı</th></tr></thead>
    <tbody>{satirlar}</tbody>
  </table></div>
  <p>
    Tablo bayi pazarlığı, stok kampanyası ve ikinci el ilanı değil; kaynağın
    yayımladığı sıfır araç liste fiyatlarını karşılaştırır. Her markadan
    yalnızca giriş seviyesi alındığı için markanın tüm model gamını temsil
    etmez.
  </p>

  <h2>Karar verirken etiket fiyatıyla kalmayın</h2>
  <p>
    Benzer giriş fiyatındaki iki araç, motor hacmi, kasko, yakıt ve bakımda
    farklı toplam maliyet çıkarabilir. Satın alma anındaki ek giderleri
    <a href="/arac/hesaplayici/">araç hesaplayıcısında</a>; ölçümün tamamını
    <a href="/arac/en-ucuz-sifir-araba/">en ucuz sıfır araç sayfasında</a>
    görebilirsiniz.
  </p>
"""


REHBERLER = [
    {
        "slug": "kredi-karti-puanlari-nerede-gecer",
        "baslik": "ParafPara, Chip-Para ve Bonus Nerelerde Geçerli?",
        "seo_baslik": "Kart Puanları Nerede Geçer? Paraf, Chip-Para, Bonus",
        "meta": "ParafPara, Chip-Para ve Bonus için doğru kontrol sırası: üye işyeri, "
                "puan karşılığı, kampanya şartı ve resmi canlı kaynaklar.",
        "govde": _govde_kart_puanlari,
        "kaynak_tipi": "resmi",
        "og_alt": "resmî kaynaklı kart puanı rehberi",
        "kaynaklar": [
            {
                "ad": "Bonus resmi marka listesi",
                "url": "https://www.bonus.com.tr/markalar",
                "not": "Bonus'un anlaşmalı marka ve işyeri kontrol noktası.",
            },
            {
                "ad": "Garanti BBVA sıkça sorulan sorular",
                "url": "https://www.garantibbva.com.tr/sikca-sorulan-sorular",
                "not": "Bonus kullanım mantığı ve 1 bonus = 1 TL bilgisi.",
            },
            {
                "ad": "ParafPara resmi tanıtım sayfası",
                "url": "https://www.paraf.com.tr/tr/parafi-taniyin/ParafPara.html",
                "not": "ParafPara'nın üye işyerlerinde kullanımı ve 1 ParafPara = 1 TL bilgisi.",
            },
            {
                "ad": "Akbank Free Kart",
                "url": "https://www.akbank.com/kartlar/kredi-kartlari/free-kart",
                "not": "Chip-para kazanımı, üye işyerlerinde kullanım ve 1 chip-para = 1 TL bilgisi.",
            },
            {
                "ad": "Akbank Sanal POS",
                "url": "https://eticaret.akbank.com/pos-urunleri/sanal-pos.html",
                "not": "Axess üye işyeri ve entegre sanal mağaza kullanım mantığı.",
            },
        ],
        "sss": [
            (
                "ParafPara, Chip-Para ve Bonus nakit gibi mi?",
                "Temel karşılık 1 puan = 1 TL'dir, ama puanın harcanacağı yer programın üye işyeri ve kampanya şartına bağlıdır. Bu yüzden puan nakde benzese de her yerde nakit gibi kullanılamaz.",
            ),
            (
                "Bir mağaza listede görünüyorsa puan kesin geçer mi?",
                "Hayır. Fiziksel POS, sanal POS, pazar yeri satıcısı ve kampanya koşulu ayrı ayrı çalışabilir. Son karar alışverişin ödeme ekranında ya da kampanya şartlarında görünür.",
            ),
            (
                "Neden tek tek tüm mağazaları yazmıyorsunuz?",
                "Çünkü banka üye işyeri listeleri ve kampanya istisnaları değişir. Elle kopyalanmış liste hızla yanlış olur; resmi canlı listeye bağlantı vermek daha güvenli.",
            ),
        ],
    },
    {
        "slug": "aylik-kedi-masrafi",
        "baslik": "Aylık Kedi Masrafı 2026: Verimiz Neyi Ölçüyor?",
        "seo_baslik": "Aylık Kedi Masrafı 2026 — Paket Fiyatı Değil Tüketim",
        "meta": "Aylık kedi masrafı neden paket fiyatından hesaplanamaz? Mama ve "
                "kum verisinin sınırı, eksik tüketim birimleri ve doğru formül.",
        "govde": _govde_aylik_evcil(
            "kedi", "Kedi",
            "Kedide ölçebildiğimiz tekrar eden iki kalem mama ve kum. Paket "
            "boyu ile tüketim süresi aynı olmadığı için bu tutar kişisel kullanımda "
            "değişebilir; tablo kategori fiyat bandını gösterir.",
        ),
        "sss": _sss_aylik_evcil("kedi", "Kedi"),
        "vertikal": "kedi",
    },
    {
        "slug": "aylik-kopek-masrafi",
        "baslik": "Aylık Köpek Masrafı 2026: Verimiz Neyi Ölçüyor?",
        "seo_baslik": "Aylık Köpek Masrafı 2026 — Paket Fiyatı Değil Tüketim",
        "meta": "Aylık köpek masrafı neden paket fiyatından hesaplanamaz? Mama ve "
                "ped verisinin sınırı, eksik tüketim birimleri ve doğru formül.",
        "govde": _govde_aylik_evcil(
            "kopek", "Köpek",
            "Çiş pedi her yetişkin köpekte sürekli gider değildir. Ped kullanmayan "
            "bir köpekte yalnızca mama satırını baz alın; tüketim de ırk ve kiloya "
            "göre değişir.",
        ),
        "sss": _sss_aylik_evcil("kopek", "Köpek"),
        "vertikal": "kopek",
    },
    {
        "slug": "damatlik-kiralamak-mi-almak-mi",
        "baslik": "Damatlık Kiralamak mı Almak mı? Kararı Nasıl Kurarsınız",
        "seo_baslik": "Damatlık Kiralamak mı Almak mı? 2026 Karşılaştırma",
        "meta": "Kiralama fiyatı yayınlanmıyor, ama satın almanın rakamı ölçülü. "
                "Aldığınız kiralama teklifini nasıl değerlendireceğinizi yazdık.",
        "govde": _govde_damatlik_kiralama,
        "vertikal": "dugun",
    },
    {
        "slug": "ozel-hastanede-dogum-maliyeti",
        "baslik": "Özel Hastanede Doğum Maliyeti: Neden Kimse Net Fiyat Vermiyor?",
        "seo_baslik": "Özel Hastanede Doğum Maliyeti — Ne Sorulmalı?",
        "meta": "Doğum paketi fiyatları yayınlanmıyor. İlave ücretin nasıl "
                "işlediğini, ne sorulacağını ve doğum sonrası ölçülmüş masrafı yazdık.",
        "govde": _govde_dogum_maliyeti,
        "vertikal": "bebek",
    },
    {
        "slug": "dogumdan-once-alinacaklar-listesi",
        "baslik": "Doğumdan Önce Alınacaklar Listesi — Fiyatlarıyla",
        "seo_baslik": "Doğumdan Önce Alınacaklar Listesi ve Fiyatları",
        "meta": "Tek seferlik bebek hazırlığının kalem kalem listesi ve "
                "ölçülmüş güncel fiyatları. Hangi üç kalem bütçeyi belirliyor?",
        "govde": _govde_dogum_oncesi,
        "vertikal": "bebek",
    },
    {
        "slug": "kedi-sahiplenmeden-once",
        "baslik": "Kedi Sahiplenmeden Önce: Neye Ne Kadar Para Gidiyor?",
        "seo_baslik": "Kedi Sahiplenmeden Önce Bilinmesi Gerekenler — Masraf",
        "meta": "Kedi kurulumunun büyük kısmını hangi kalem belirliyor? Paket "
                "fiyatı ile aylık tüketim arasındaki fark ve ölçümün sınırı.",
        "govde": _govde_sahiplenme("kedi", "Kedi", "kopek", "Köpek"),
        "vertikal": "kedi",
    },
    {
        "slug": "kopek-sahiplenmeden-once",
        "baslik": "Köpek Sahiplenmeden Önce: Neye Ne Kadar Para Gidiyor?",
        "seo_baslik": "Köpek Sahiplenmeden Önce Bilinmesi Gerekenler — Masraf",
        "meta": "Köpek kurulumunda bütçeyi hangi kalem belirliyor? Paket fiyatı "
                "ile aylık tüketim arasındaki fark ve ölçümün sınırı.",
        "govde": _govde_sahiplenme("kopek", "Köpek", "kedi", "Kedi"),
        "vertikal": "kopek",
    },
    {
        "slug": "ev-kurarken-nerede-tasarruf-edilir",
        "baslik": "Ev Kurarken Nerede Tasarruf Edilir, Nerede Edilmez?",
        "seo_baslik": "Ev Kurarken Nerede Tasarruf Edilir? Ölçülmüş Cevap",
        "meta": "Hangi kalemde segment düşürmek gerçekten para bırakıyor, "
                "hangisinde uğraşmanın karşılığı yok — kalem kalem ölçtük.",
        "govde": _govde_nerede_tasarruf,
        "vertikal": "ev-kurma",
    },
    {
        "slug": "bebek-alisverisinde-nelere-dikkat",
        "baslik": "Bebek Alışverişinde Nelere Dikkat Etmeli?",
        "seo_baslik": "Bebek Alışverişinde Nelere Dikkat Etmeli? Masraf Rehberi",
        "meta": "Hazırlık bütçesinin büyük kısmını üç kalem belirliyor. "
                "Hangileri olduğunu ve nerede fiyata bakılmayacağını yazdık.",
        "govde": _govde_bebek_tavsiye,
        "vertikal": "bebek",
    },
    {
        "slug": "damatlik-kac-para",
        "baslik": "Damatlık Kaç Para? Neden Kimse Aynı Fiyatı Söylemiyor",
        "seo_baslik": "Damatlık Kaç Para? 2026 Fiyatları — Üç Kaynaktan Ölçtük",
        "meta": "Damatlık fiyatları neden bu kadar geniş bir aralıkta? Üç ayrı "
                "kaynaktan ölçtük, aradaki farkın nereden geldiğini yazdık.",
        "govde": _govde_damatlik,
        "vertikal": "dugun",
    },
    {
        "slug": "asgari-ucretle-ev-kurulur-mu",
        "baslik": "Asgari Ücretle Ev Kurulur mu? Kaç Maaş Gerekiyor",
        "seo_baslik": "Asgari Ücretle Ev Kurulur mu? Kaç Maaş Ettiğini Hesapladık",
        "meta": "Sıfırdan ev kurmak kaç aylık asgari ücret ediyor? Ölçülmüş "
                "fiyatlarla, ekonomik ve orta segment için ayrı ayrı.",
        "govde": _govde_asgari_ucret_ev,
        "vertikal": "ev-kurma",
    },
    {
        "slug": "gelinlik-mi-damatlik-mi-pahali",
        "baslik": "Gelinlik mi Damatlık mı Pahalı? Verimiz Ne Diyor, Neyi Demiyor",
        "seo_baslik": "Gelinlik mi Damatlık mı Pahalı? Ölçüm Sonucu ve Sınırı",
        "meta": "Verimizde damatlık daha pahalı çıkıyor. Ama bu piyasa gerçeği "
                "değil, ölçüm sınırı — nedenini açıkça yazdık.",
        "govde": _govde_gelinlik_damatlik,
        "vertikal": "dugun",
    },
    {
        "slug": "kedi-mi-kopek-mi-masrafli",
        "baslik": "Kedi mi Köpek mi Daha Masraflı? Verinin Söylediği Sınır",
        "seo_baslik": "Kedi mi Köpek mi Daha Masraflı? Ölçümün Sınırı",
        "meta": "Kedi ve köpek kurulum fiyatları karşılaştırması. Paket boyu ve "
                "tüketim verisi olmadan neden aylık ya da ilk yıl toplamı vermiyoruz?",
        "govde": _govde_kedi_kopek,
        "vertikal": "kedi",
    },
    {
        "slug": "bebek-masraflari-ilk-yil",
        "baslik": "Bebek Masrafları: İlk Yıl Hesabı Nasıl Kurulur?",
        "seo_baslik": "Bebek Masrafları 2026 — İlk Yıl Hesabının Sınırı",
        "meta": "Tek seferlik bebek hazırlığı ölçümü, bez paket fiyatının sınırı "
                "ve güvenilir ilk yıl toplamı için gereken tüketim verileri.",
        "govde": _govde_bebek_ilk_yil,
        "sss": _sss_bebek_masrafi,
        "vertikal": "bebek",
    },
    {
        "slug": "ceyiz-masraflari",
        # 2026-08-09: "ceyiz ne kadar tutar 2026" sorgusundan GIRIS geldi.
        # Sayfa tam o soruyu cevapliyordu (cevap blogu "41.716 TL tutuyor"
        # diyor) ama basligi "Ceyiz Masraflari" idi - kullanicinin yazdigi
        # ifade H1'de hic gecmiyordu.
        "baslik": "Çeyiz Ne Kadar Tutar? Tekstil, Mutfak ve Küçük Ev Aletleri",
        "seo_baslik": "Çeyiz Ne Kadar Tutar? 2026 Kalem Kalem Liste",
        "meta": "Çeyiz kapsamındaki tekstil, mutfak eşyası ve küçük ev aletleri "
                "kalem kalem, ekonomik-orta-üst fiyatlarıyla.",
        "govde": _govde_ceyiz,
        "vertikal": "ev-kurma",
    },
    {
        "slug": "yatak-odasi-masraflari",
        "baslik": "Yatak Odası Masrafları: Sıfırdan Kurmak Ne Kadar?",
        "seo_baslik": "Yatak Odası Masrafları 2026 — Kalem Kalem",
        "meta": "Yatak, gardırop, komodin, şifonyer: bir yatak odasını sıfırdan "
                "kurmanın ekonomik, orta ve üst segment maliyeti.",
        "govde": _govde_yatak_odasi,
        "vertikal": "ev-kurma",
    },
    {
        "slug": "trendyol-mu-amazon-mu-ucuz",
        "baslik": "Trendyol mu Amazon mu Daha Ucuz? Verilerle Karşılaştırdık",
        "seo_baslik": "Trendyol mu Amazon mu Daha Ucuz? Veri Karşılaştırması",
        "meta": "Aynı kalemleri iki siteden ayrı ayrı ölçtük. Hangi kategoride "
                "hangi liste daha aşağıda kalıyor ve bu neden 'ucuz site' demek değil?",
        "govde": _govde_kaynak_karsilastirma,
        "vertikal": "ev-kurma",
    },
    {
        "slug": "ekonomik-dugun-nasil-yapilir",
        "baslik": "Ekonomik Düğün Nasıl Yapılır? Nereden Kısılır, Nereden Kısılmaz",
        "seo_baslik": "Ekonomik Düğün Nasıl Yapılır? 2026 Bütçesi",
        "meta": "150 kişilik düğünde orta ve ekonomik segment arasındaki fark "
                "ne kadar? Hangi kalemde tasarruf işe yarıyor, hangisinde geri tepiyor?",
        "govde": _govde_ekonomik_dugun,
        "vertikal": "dugun",
    },
    {
        "slug": "beyaz-esya-butcesi",
        "baslik": "2026 Beyaz Eşya Bütçesi: Sıfırdan Bir Eve Ne Kadar?",
        "seo_baslik": "Beyaz Eşya Bütçesi 2026 — Toplam Maliyet",
        "meta": "Buzdolabı, çamaşır ve bulaşık makinesi, fırın, klima: bir evin "
                "beyaz eşyası kalem kalem, ekonomik-orta-üst fiyatlarıyla.",
        "govde": _govde_beyaz_esya,
        "vertikal": "ev-kurma",
    },
    {
        "slug": "okul-masrafi-ne-kadar",
        "baslik": "2026 Okul Alışverişi Maliyeti: Bir Öğrenciye Ne Kadar?",
        "seo_baslik": "Okul Alışverişi Maliyeti 2026 — Liste ve Fiyatlar",
        "meta": "Çanta, kırtasiye, kitap ve ayakkabı: bir öğrencinin okul "
                "alışverişi kalem kalem, son başarılı ölçüm tarihiyle.",
        "govde": _govde_okul,
        "vertikal": "okul",
    },
    {
        "slug": "okul-alisverisinde-en-pahali-kalemler",
        "baslik": "Okul Alışverişinde En Pahalı Kalemler Hangileri?",
        "seo_baslik": "Okul Alışverişinde En Pahalı Kalemler 2026",
        "meta": "Okul alışverişi sepetinde en yüksek payı alan beş kalem, güncel "
                "ölçümlerden otomatik hesaplanan tutar ve yüzdelerle.",
        "govde": _govde_okul_pahali_kalemler,
        "vertikal": "okul",
    },
    {
        "slug": "150-kisilik-dugun-maliyeti",
        "baslik": "2026 150 Kişilik Düğün Maliyeti",
        "seo_baslik": "150 Kişilik Düğün Maliyeti 2026 — Kalem Kalem",
        "meta": "150 kişilik düğünün kalem kalem maliyeti: salon, gelinlik, takı, "
                "fotoğrafçı. Son başarılı ölçüm tarihi ve kapsam notlarıyla.",
        "govde": _govde_dugun_150,
        "vertikal": "dugun",
    },
    {
        "slug": "yemekli-mi-kokteyl-mi",
        "baslik": "Düğün Salonu Fiyatları: Yemekli mi Kokteyl mi?",
        "seo_baslik": "Düğün Salonu Yemekli mi Kokteyl mi? Kişi Başı Fark",
        "meta": "Yemekli ve kokteyl düğün salonu arasındaki kişi başı fark ne kadar, "
                "menünün gerçek bedeli nasıl hesaplanır?",
        "govde": _govde_yemekli_kokteyl,
        "vertikal": "dugun",
    },
    {
        "slug": "sifirdan-ev-kurma-listesi",
        "baslik": "Ev Kurarken Alınacaklar Listesi ve 2026 Maliyeti",
        "seo_baslik": "Ev Kurarken Alınacaklar Listesi 2026 — Fiyatlarıyla",
        "meta": "Beyaz eşyadan tekstile, sıfırdan ev kurmanın kalem kalem maliyeti "
                "ve bütçe dağılımı. Son başarılı ölçüm tarihiyle.",
        "govde": _govde_ev_kurma,
        "vertikal": "ev-kurma",
    },
    {
        "slug": "sifir-araba-gercek-maliyeti",
        "baslik": "2026 Sıfır Araba Masrafları: Etiket Fiyatı Yetmiyor",
        "seo_baslik": "Sıfır Araba Masrafları 2026 — MTV, Noter, Kasko",
        "meta": "MTV, noter, tescil, kasko ve trafik sigortası: sıfır aracın etiket "
                "fiyatının üstüne binen maliyetler ve toplam tutar.",
        "govde": _govde_arac,
        "vertikal": "arac",
    },
    {
        "slug": "marka-giris-fiyatlari",
        "baslik": "En Ucuz Sıfır Araçlar: Marka Giriş Fiyatları",
        "seo_baslik": "En Ucuz Sıfır Araçlar 2026 — Marka Giriş Fiyatları",
        "meta": "En düşük sıfır araç liste fiyatları ve marka giriş fiyatlarının "
                "ortancası; kampanya ile piyasa ortalamasını karıştırmadan.",
        "govde": _govde_marka_giris_fiyatlari,
        "vertikal": "arac",
    },
]


def anasayfa_yazisi(veriler: dict | None = None) -> str:
    """Ana sayfanin en altindaki yazi bolumu.

    NEDEN ANA SAYFADA YAZI: ana sayfa GEO'nun ilk temas noktasi ve en cok
    dis link alan sayfa. Ustteki kartlar rakami veriyor ama BAGLAM
    vermiyor - AI motorlari ve okuyucu icin "bu rakamlar ne anlama
    geliyor" kismi burada.

    Rakamlar veriden gelir, metne GOMULMEZ (rehber yazilariyla ayni kural).
    Veri yoksa ilgili satir atlanir; hicbiri yoksa bolum bos doner.
    """
    v = veriler if veriler is not None else _veriler()
    satirlar = []
    for vertikal, ad, yol in [("dugun", "150 kişilik bir düğün", "/dugun/"),
                              ("ev-kurma", "sıfırdan bir evi eşyalandırmak", "/ev-kurma/"),
                              ("okul", "bir öğrencinin okul alışverişi", "/okul/"),
                              ("arac", "bir markanın giriş seviyesi sıfır aracı", "/arac/")]:
        d = v.get(vertikal)
        if not d:
            continue
        conf = su.VERTIKALLER[vertikal]
        toplam, _ = su.ornek_toplam_hesapla(
            conf, d.get("kalemler") or {}, olcek=conf["olcek_varsayilan"], segment="orta")
        if toplam:
            satirlar.append(f'<li><a href="{yol}">{ad}</a>: <strong>{_p(toplam)}</strong></li>')
    if not satirlar:
        return ""

    e = v.get("enflasyon") or {}
    genel = next((g for g in (e.get("gruplar") or {}).values() if not g.get("vertikal")), None)
    olcumler = e.get("olcumler") or []
    enf = ""
    if genel and len(olcumler) >= 2:
        enf = (
            "    <p>Bu rakamlar hızlı eskiyor. TÜİK'in tüketici fiyat endeksine göre "
            f"{olcumler[0]} — {olcumler[-1]} arasında genel enflasyon "
            f"%{genel['degisim_yuzde']:.1f} oldu. Altı ay önce sorulmuş bir "
            "&quot;ne kadar tutar&quot; sorusunun cevabı bugün geçerli değil; bu yüzden "
            "kaynakları ayın 5'i ve 20'sinde yeniden tarıyoruz.</p>\n"
        )

    return (
        '  <section class="icerik-bolumu">\n'
        "    <h2>Bu rakamlar ne anlama geliyor?</h2>\n"
        "    <p>Türkiye'de bir şeyin kaça mal olduğunu öğrenmek şaşırtıcı derecede "
        "zor. Forumlarda dolaşan rakamların tarihi belirsiz, haberlerdeki sayıların "
        "kaynağı yok, yapay zekaya sorduğunuzda aldığınız cevap aylar önceki "
        "fiyatlara dayanıyor. Bu boşluğu kapatmak için kurduk: her kalemin fiyatını "
        "gerçek satış sayfalarından ölçüyoruz, kaç üründen derlendiğini ve hangi "
        "tarihte ölçüldüğünü yanına yazıyoruz.</p>\n"
        "    <p>Bugün itibarıyla ölçtüğümüz toplamlar:</p>\n"
        f"    <ul>{''.join(satirlar)}</ul>\n"
        + enf +
        "    <h3>Neyi ölçmüyoruz</h3>\n"
        "    <p>Konut fiyatı, kira, işçilik ve hizmet bedelleri bu endekslerde yok. "
        "Sebebi basit: bunlar tek bir sayıya sığmıyor. Aynı şehirde iki mahalle "
        "arasında kira ikiye katlanabiliyor. Ölçemediğimiz şeye rakam uydurmaktansa "
        "kapsam dışı bırakmayı tercih ediyoruz.</p>\n"
        "    <p>Bir de şu var: bazı kalemleri uzun süre tahminle taşıdık ve gerçek "
        "kaynak bulunca tahminlerin ne kadar saptığını gördük. Düğün fotoğrafçısı "
        "için öngördüğümüz rakam gerçeğin üç katıymış; gelin arabası içinse üçte "
        "biri kadarmış. Sapma iki yönde de çıkabiliyor — makul görünen bir tahmin "
        "doğru demek değil. Bugün düğün endeksinin yalnızca küçük bir dilimi "
        "tahmine dayanıyor, gerisi ölçüm.</p>\n"
        "    <h3>Rakamları kullanabilirsiniz</h3>\n"
        "    <p>Veriler herkese açık: her endeksin ham JSON dosyası indirilebilir "
        "durumda, yöntem sayfalarında neyi nasıl ölçtüğümüz yazıyor. Haber, rapor ya "
        "da araştırmada kullanırken ölçüm tarihini de belirtmenizi rica ediyoruz — "
        "fiyat verisi tarihsiz olduğunda yanıltıcı hale geliyor.</p>\n"
        "  </section>\n"
    )


def _title(rehber: dict) -> str:
    """SERP'te kesilmeyen baslik.

    Google basligi ~60 karakterde kesiyor ve " | Maliyeti Ne?" eki 15
    karakter yiyor. Uzun basliklarda marka ekini kisaltiyoruz; tamamen
    atmiyoruz cunku marka taninirligi da bir sinyal. Hedef ifade her
    zaman BASTA kaliyor - baslik kesilse bile anahtar kelime gorunur.
    """
    ana = rehber.get("seo_baslik") or rehber["baslik"]
    for ek in (" | Maliyeti Ne?", " · Maliyeti Ne?", ""):
        if len(ana + ek) <= 60:
            return ana + ek
    return ana


def _rehber_kaynaklari_html(rehber: dict) -> str:
    kaynaklar = rehber.get("kaynaklar") or []
    if not kaynaklar:
        return ""
    maddeler = []
    for kaynak in kaynaklar:
        ad = kaynak["ad"]
        url = kaynak["url"]
        notu = kaynak.get("not")
        aciklama = f" — {notu}" if notu else ""
        maddeler.append(
            f'<li><a href="{url}">{ad}</a>{aciklama}</li>'
        )
    return (
        '<section id="kaynaklar" class="kaynak-kunye">\n'
        "  <h2>Kaynaklar</h2>\n"
        f"  <ul>{''.join(maddeler)}</ul>\n"
        "  <p class=\"sonuc-alt-metin\">Dış kaynaklı program koşulları değişebilir; "
        "alışverişten önce bankanın kendi kampanya ve üye işyeri sayfası esas alınmalı.</p>\n"
        "</section>\n"
    )


def _rehber_sssleri(rehber: dict, veriler: dict) -> list[tuple[str, str]]:
    sorular = rehber.get("sss") or []
    if callable(sorular):
        sorular = sorular(veriler)
    return sorular or []


def _rehber_sss_html(sorular: list[tuple[str, str]]) -> str:
    if not sorular:
        return ""
    govde = "".join(
        f"  <details><summary>{s}</summary><p>{c}</p></details>\n" for s, c in sorular
    )
    return f'<section class="sss">\n  <h2>Sıkça sorulan sorular</h2>\n{govde}</section>\n'


def _rehber_canli_tanim(rehber: dict, veriler: dict) -> dict:
    """Basliktaki veri sayisini govdeyle ayni hesaplamadan kurar."""
    if rehber.get("slug") != "trendyol-mu-amazon-mu-ucuz":
        return rehber
    sayi = len(_kaynak_karsilastirma_kayitlari(veriler))
    if not sayi:
        return rehber
    canli = dict(rehber)
    canli["baslik"] = f"Trendyol mu Amazon mu Daha Ucuz? {sayi} Kalemde Ölçtük"
    canli["seo_baslik"] = f"Trendyol mu Amazon mu Daha Ucuz? {sayi} Kalem"
    canli["meta"] = (
        f"{sayi} kalemi Trendyol ve Amazon kategori listelerinden ayrı ayrı "
        "ölçtük. Ürün karması farkı hangi listeyi nasıl etkiliyor?"
    )
    return canli


def rehber_uret(rehber: dict, veriler: dict, tarih: str | None = None) -> str | None:
    """Tek bir rehber sayfasi. Veri yoksa None - bos sayfa YAYINLANMAZ."""
    rehber = _rehber_canli_tanim(rehber, veriler)
    govde = rehber["govde"](veriler)
    if not govde:
        return None
    tarih = tarih or date.today().isoformat()
    url = f"{SITE_KOK_URL}/rehber/{rehber['slug']}/"
    vconf = su.VERTIKALLER.get(rehber.get("vertikal"))
    olcum_tarihi = (
        ((veriler.get(rehber.get("vertikal")) or {}).get("guncelleme_tarihi"))
        if vconf else None
    ) or tarih
    article = {
        "@type": "Article",
        "headline": rehber["baslik"],
        "description": rehber["meta"],
        "datePublished": tarih,
        "dateModified": olcum_tarihi,
        "inLanguage": "tr-TR",
        "mainEntityOfPage": url,
        "author": {"@id": f"{SITE_KOK_URL}/#kurum"},
        "publisher": {"@id": f"{SITE_KOK_URL}/#kurum"},
    }
    if rehber.get("kaynaklar"):
        article["citation"] = [k["url"] for k in rehber["kaynaklar"]]

    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            article,
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Ana sayfa",
                     "item": SITE_KOK_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Rehber",
                     "item": f"{SITE_KOK_URL}/rehber/"},
                    {"@type": "ListItem", "position": 3, "name": rehber["baslik"],
                     "item": url},
                ],
            },
            su.kurum_semantigi(),
        ],
    }
    sss_sorulari = _rehber_sssleri(rehber, veriler)
    if sss_sorulari:
        json_ld["@graph"].append({
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": s,
                 "acceptedAnswer": {"@type": "Answer", "text": c}}
                for s, c in sss_sorulari
            ],
        })

    canli_rehberler = [_rehber_canli_tanim(r, veriler) for r in REHBERLER]
    digerleri = "".join(
        f'<a href="/rehber/{r["slug"]}/">{r["baslik"]}</a>'
        for r in canli_rehberler if r["slug"] != rehber["slug"]
    )
    kaynaklar_html = _rehber_kaynaklari_html(rehber)
    sss_html = _rehber_sss_html(sss_sorulari)
    if vconf:
        kalemler = (veriler.get(rehber.get("vertikal")) or {}).get("kalemler") or {}
        rehber_kunye = su.yayin_kunyesi_html(
            [("Fiyat serisi", len(kalemler)),
             ("Bağımsız kaynak", len(su.bagimsiz_siteler(kalemler, set(kalemler)))),
             ("Son ölçüm", olcum_tarihi),
             ("Yayıncı", "Maliyeti Ne? Veri Ekibi")],
            [("Yöntem", f'/{vconf["yol"]}/metodoloji/'),
             ("Ham veri", f'/veri/{rehber["vertikal"]}.json'),
             ("Hata bildir", "/iletisim/")],
        )
        kunye = (
            f'  <p class="kunye">{olcum_tarihi} tarihli ölçümlerden · '
            f'<a href="/{vconf["yol"]}/metodoloji/">Yöntem</a></p>'
        )
    else:
        rehber_kunye = su.yayin_kunyesi_html(
            [("Kaynak", len(rehber.get("kaynaklar") or [])),
             ("Kontrol tarihi", tarih),
             ("Yayıncı", "Maliyeti Ne? Veri Ekibi")],
            [("Kaynaklar", "#kaynaklar"),
             ("Yayın ilkeleri", "/hakkimizda/"),
             ("Hata bildir", "/iletisim/")],
            "Editoryal kontrol",
        )
        kunye = (
            f'  <p class="kunye">{tarih} tarihli resmi kaynak kontrolünden · '
            '<a href="#kaynaklar">Kaynaklar</a></p>'
        )

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_title(rehber)}</title>
<meta name="description" content="{rehber["meta"]}">
<link rel="canonical" href="{url}">
{su.STIL_ETIKETLERI}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:title" content="{rehber["baslik"]}">
<meta property="og:description" content="{rehber["meta"]}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
{su.og_etiketleri("/assets/og/rehber-" + rehber["slug"] + ".png", rehber["baslik"])}
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
{su.ANALITIK}
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">Maliyeti <span>Ne?</span></a>
    <nav class="ust-menu">{su.genel_menu('rehber')}</nav>
  </div>
</header>

<main class="kapsayici">

  <span class="guncelleme-etiketi">Son veri: {olcum_tarihi}</span>
  <h1>{rehber["baslik"]}</h1>
  {rehber_kunye}
{govde}
{kaynaklar_html}{sss_html}{kunye}

  <section class="icerik-bolumu">
    <h2>Diğer rehberler</h2>
    <p class="kart-linkler">{digerleri}</p>
  </section>

</main>

<footer>
  <div class="kapsayici">
    <div>© {tarih[:4]} Maliyeti Ne? · <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a> · <a href="/sss/">SSS</a> · <a href="/rehber/">Rehber</a> · <a href="/veri/">Veri</a></div>
    <nav>
      <a href="/dugun/">Düğün</a>
      <a href="/ev-kurma/">Ev Kurma</a>
      <a href="/okul/">Okul</a>
      <a href="/arac/">0 km Araç</a>
    </nav>
  </div>
</footer>

</body>
</html>
"""


def rehber_dizini_uret(yazilanlar: list[dict], tarih: str | None = None) -> str:
    tarih = tarih or date.today().isoformat()
    kartlar = "".join(
        f'<div class="kart"><h2><a href="/rehber/{r["slug"]}/">{r["baslik"]}</a></h2>'
        f'<p>{r["meta"]}</p></div>'
        for r in yazilanlar
    )
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rehber | Maliyeti Ne?</title>
<meta name="description" content="Düğün, ev kurma ve sıfır araç bütçesi üzerine, gerçek fiyat ölçümlerine dayanan rehberler.">
<link rel="canonical" href="{SITE_KOK_URL}/rehber/">
{su.STIL_ETIKETLERI}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:title" content="Rehber | Maliyeti Ne?">
<meta property="og:description" content="Gerçek fiyat ölçümlerine dayanan bütçe rehberleri.">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_KOK_URL}/rehber/">
{su.OG_ETIKETLERI}
<meta name="twitter:card" content="summary_large_image">
{su.ANALITIK}
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">Maliyeti <span>Ne?</span></a>
    <nav class="ust-menu">{su.genel_menu('rehber')}</nav>
  </div>
</header>

<main class="kapsayici">
  <h1>Rehber</h1>
  <p>
    Ölçümlü rehberlerdeki rakamlar gerçek fiyat verisinden geliyor ve veri
    yenilendikçe yazı da güncelleniyor. Resmi kaynak rehberlerinde ise
    değişken listeleri kopyalamak yerine canlı kaynak bağlantıları açık
    tutuluyor.
  </p>
  <div class="kart-grid">{kartlar}</div>
</main>

<footer>
  <div class="kapsayici">
    <div>© {tarih[:4]} Maliyeti Ne? · <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a> · <a href="/sss/">SSS</a> · <a href="/rehber/">Rehber</a> · <a href="/veri/">Veri</a></div>
  </div>
</footer>

</body>
</html>
"""


def rehberleri_yaz(veri_kok: Path | None = None, hedef_kok: Path | None = None) -> list[dict]:
    veriler = _veriler(veri_kok)
    kok = hedef_kok or SITE_KOK / "rehber"
    yazilanlar = []
    for r in REHBERLER:
        canli_r = _rehber_canli_tanim(r, veriler)
        html = rehber_uret(canli_r, veriler)
        if not html:
            print(f"  ATLANDI (veri yok): {r['slug']}")
            continue
        hedef = kok / r["slug"] / "index.html"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(html, encoding="utf-8")
        yazilanlar.append(canli_r)
    if yazilanlar:
        (kok / "index.html").parent.mkdir(parents=True, exist_ok=True)
        (kok / "index.html").write_text(rehber_dizini_uret(yazilanlar), encoding="utf-8")
    return yazilanlar


def main():
    yazilanlar = rehberleri_yaz()
    for r in yazilanlar:
        print(f"Rehber uretildi: /rehber/{r['slug']}/")
    print(f"Toplam {len(yazilanlar)} rehber + dizin.")


if __name__ == "__main__":
    main()
