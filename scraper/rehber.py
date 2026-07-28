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
tutarlar /veri/*.json'dan gelir. Boylece aylik olcumde yazilar da
kendiliginden guncellenir - bayat rakamli blog yazisi, guven kaybinin
en hizli yolu.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

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

    fark_150 = (yemekli - kokteyl) * 150
    return f"""
  <p class="cevap-blok">
    Yemekli salon kişi başı <strong>{_p(yemekli)}</strong>, kokteyl salon
    <strong>{_p(kokteyl)}</strong>. 150 kişilik bir düğünde aradaki fark
    {_p(fark_150)}. Ama bu farkın tamamı cebinizde kalmıyor — kokteyl
    seçerseniz yemeği başka yerden almanız gerekiyor.
  </p>

  <h2>İki fiyat neyi kapsıyor?</h2>
  <p>
    Düğün mekanları fiyatı kişi başı verir ve genellikle iki seçenek sunar.
    Yemekli seçenekte salon ve menü birlikte fiyatlanır. Kokteyl seçenekte
    salonu alırsınız, yemek yoktur; ikram genelde sınırlı bir açık büfeyle
    kalır.
  </p>
  <p>
    Bu ayrım göründüğünden önemli, çünkü mekanların ilan sayfalarında
    yazan "başlangıç fiyatı" çoğu zaman kokteyl fiyatıdır. Yemekli bir
    düğün planlarken kokteyl fiyatını baz alırsanız bütçeniz baştan
    yanlış kurulur.
  </p>

  <h2>Menünün kişi başı bedeli</h2>
  <p>
    Menünün gerçek maliyetini bulmanın temiz bir yolu var: aynı mekanın
    yemekli ve kokteyl fiyatını çıkarmak. Aradaki fark, o mekanda yemeğin
    kişi başı bedeli. Bunu tek tek mekanlar için hesapladık; orta segmentte
    {_p(menu)} çıkıyor.
  </p>
  <p>
    Farkı <em>aynı mekan içinde</em> almak şart. İki ayrı listenin
    ortalamasını çıkarmak yanlış sonuç verir, çünkü her mekan kokteyl
    seçeneği sunmuyor ve farkların ortası, ortaların farkına eşit değil.
    Bizim veride bu iki yöntem arasında gözle görülür bir sapma vardı.
  </p>

  <h2>Hangisi size uygun?</h2>
  <p>
    Kokteyl düzen, davetlilerin oturup yemek yemediği, daha kısa süren
    organizasyonlar için mantıklı. Akşam saatinde, uzun bir düğün
    planlıyorsanız misafirleriniz yemek bekler; kokteyl alıp dışarıdan
    catering getirmek çoğu zaman yemekli paketten ucuza gelmez.
  </p>
  <p>
    Mekanın kendi menüsü genelde daha ekonomik olur — mutfak zaten orada,
    servis ekibi zaten çalışıyor. Dışarıdan catering'in ulaşım, ekipman ve
    servis kalemleri fiyata biniyor.
  </p>

  <h2>Bir uyarı</h2>
  <p>
    Bu iki rakamı toplayıp tek bir "gerçek maliyet" çıkarmaya çalışmayın.
    Hesaplayıcımızda da toplamıyoruz: yemekli fiyat zaten menüyü içerdiği
    için üstüne ayrıca yemek eklemek aynı masrafı iki kez saymak olur.
    Seçtiğiniz düzen hangisiyse toplama yalnızca o giriyor.
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
    Kalemlerin fiyatı büyük e-ticaret sitelerinden ve marka mağazalarından
    aylık olarak derleniyor. Bir uyarı: kategori listelerinden derlediğimiz
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
    giris = _kalem(a, "en-ucuz-sifir-arac")
    if not giris:
        return None

    # arac-ek-maliyetler.js ile AYNI kurallar - tek kaynak olsun diye
    # buradaki degerler o dosyadan turetilmis sabitler.
    mtv = 12028          # 1301-1600 cc, ilk yil (58 Seri No.lu MTV Teblig)
    noter = max(giris * 0.002, 1000) + 1920
    kasko = max(giris * 0.03, 12000)
    trafik = 9500
    plaka = 4500
    ek = mtv + noter + kasko + trafik + plaka
    return f"""
  <p class="cevap-blok">
    Sıfır aracın etiket fiyatı ödediğiniz tutar değil. Bir markanın giriş
    modeli ortalama <strong>{_p(giris)}</strong>; üzerine vergi, harç ve
    sigorta olarak yaklaşık <strong>{_p(ek)}</strong> biniyor. Anahtarı
    almanın gerçek maliyeti <strong>{_p(giris + ek)}</strong> civarında.
  </p>

  <h2>Etiket fiyatının üstüne ne ekleniyor?</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th class="sayi">Tutar</th><th>Tür</th></tr></thead>
    <tbody>
      <tr><td>MTV (ilk yıl, 1301–1600 cc)</td><td class="sayi">{_p(mtv)}</td><td>Resmî tarife</td></tr>
      <tr><td>Noter ve ilk tescil</td><td class="sayi">{_p(round(noter))}</td><td>Resmî tarife</td></tr>
      <tr><td>Kasko (yıllık)</td><td class="sayi">{_p(round(kasko))}</td><td>Tahmini</td></tr>
      <tr><td>Zorunlu trafik sigortası</td><td class="sayi">{_p(trafik)}</td><td>Tahmini</td></tr>
      <tr><td>Plaka ve ruhsat</td><td class="sayi">{_p(plaka)}</td><td>Tahmini</td></tr>
    </tbody>
  </table></div>
  <p>
    MTV ve noter harcı resmî tarifeye bağlı; Resmî Gazete'de yayımlanan
    tutarlar. Kasko ve trafik sigortası ise şirkete, sürücünün yaşına ve
    hasarsızlık geçmişine göre değişiyor — buradaki rakamlar piyasa
    ortalaması, teklif değil.
  </p>

  <h2>Motor hacmi vergiyi ikiye katlayabilir</h2>
  <p>
    MTV kademeli hesaplanıyor ve kademeler arasındaki fark büyük. 1300 cc'ye
    kadar olan bir araçta ilk yıl MTV'si 6.903 TL iken, 1601–1800 cc bandında
    21.252 TL'ye çıkıyor. İki benzer araç arasında karar veriyorsanız motor
    hacmi, yalnızca yakıt tüketimi değil vergi farkı demek.
  </p>

  <h2>Neden ortalama araç fiyatı vermiyoruz</h2>
  <p>
    Piyasadaki tüm modellerin ortasını almak yanıltıcı bir rakam üretiyor.
    Denedik: 3,2 milyon TL çıkıyor. Sebebi listede Porsche ile Fiat'ın eşit
    ağırlıkta sayılması — oysa Türkiye'de satılan araçların dağılımı böyle
    değil. Bunun yerine her markanın giriş modelini ölçüyoruz; net tanımlı
    ve karşılaştırılabilir bir rakam.
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
# 9. Bebek masraflari - ILK YIL
#
# NEDEN AYRI BIR YAZI: bebek endeksi TEK SEFERLIK hazirligi olcuyor;
# bez `varsayilan_dahil: False` oldugu icin toplama girmiyor. "Ilk yil ne
# kadar?" sorusunun cevabi ise ikisinin TOPLAMI - ve bu ayrimi yapan
# baska bir kaynak yok. Rakiplerin verdigi tek rakam ikisini karistirir.
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
    yillik_bez = bez * 12
    toplam = tek_seferlik + yillik_bez
    eko, _ = su.ornek_toplam_hesapla(conf, kalemler, 1, "ekonomik")
    bez_eko = _kalem(b, "bebek-bezi", "dusuk")

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
    Bir bebeğin ilk yılı, ölçtüğümüz kalemlerle orta segmentte
    <strong>{_p(toplam)}</strong> tutuyor. Bunun {_p(tek_seferlik)} kadarı
    <strong>tek seferlik hazırlık</strong> (araba, beşik, oto koltuğu,
    mama sandalyesi), {_p(yillik_bez)} kadarı ise <strong>yalnızca bezin
    yıllık tutarı</strong>.
  </p>

  <h2>Neden iki rakamı ayrı tutuyoruz?</h2>
  <p>
    Bebek masrafı sorulduğunda verilen tek rakamlar genelde bu ikisini
    karıştırır. Beşik bir kez alınır; bez her ay tekrar eder. İkisini
    toplayıp tek sayı vermek, ikinci yılı planlayan biri için yanıltıcı
    olur — ikinci yılda beşiği yeniden almazsınız ama bezi almaya devam
    edersiniz. Bu yüzden endeksimizde bez varsayılan toplama girmez,
    ayrıca gösterilir.
  </p>

  <h2>Hazırlığın en büyük dört kalemi</h2>
  <div class="tablo-sarmal"><table>
    <thead><tr><th>Kalem</th><th class="sayi">Orta segment</th><th class="sayi">Payı</th></tr></thead>
    <tbody>{satirlar}</tbody>
  </table></div>
  <p>
    Ekonomik tercihlerle tek seferlik hazırlık {_p(eko)} seviyesine
    iniyor; bez tarafında ekonomik paket aylık {_p(bez_eko)} demek, yani
    yılda {_p(bez_eko * 12 if bez_eko else None)}.
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
    {ust / eko:.1f} kat.
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
def _govde_kaynak_karsilastirma(v: dict) -> str | None:
    """Iki kaynagi da olctugumuz kalemlerde fiyat bandi karsilastirmasi.

    DURUST CERCEVE: bu "hangi site ucuz" listesi DEGIL. Olctugumuz sey
    kategori sayfalarindaki URUN KARMASI - Amazon'da markali urunler,
    pazaryerinde jenerik urunler agirlikta olabiliyor. Ayni urunun iki
    sitedeki fiyatini karsilastirmiyoruz; oyle bir iddiada bulunmak
    yaniltici olur ve yazi bunu acikca soyluyor.
    """
    import statistics
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
    if len(kayitlar) < 10:
        return None

    pazar_ucuz = [x for x in kayitlar if x["fark"] > 5]
    amazon_ucuz = [x for x in kayitlar if x["fark"] < -5]
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
    Toplamda {len(pazar_ucuz)} kalemde bir liste, {len(amazon_ucuz)} kalemde
    diğeri daha aşağıda kalıyor — yani tek bir siteyi "ucuz site" diye
    işaretlemek mümkün değil.
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


REHBERLER = [
    {
        "slug": "bebek-masraflari-ilk-yil",
        "baslik": "Bebek Masrafları: İlk Yıl Ne Kadar Tutuyor?",
        "seo_baslik": "Bebek Masrafları 2026 — İlk Yıl Toplamı",
        "meta": "Tek seferlik hazırlık ile aylık tekrarlayan bez masrafı ayrı ayrı, "
                "ölçülmüş fiyatlarla. İlk yılın gerçek toplamı.",
        "govde": _govde_bebek_ilk_yil,
        "vertikal": "bebek",
    },
    {
        "slug": "ceyiz-masraflari",
        "baslik": "Çeyiz Masrafları: Tekstil, Mutfak ve Küçük Ev Aletleri",
        "seo_baslik": "Çeyiz Masrafları 2026 — Kalem Kalem Liste",
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
        "baslik": "Trendyol mu Amazon mu Daha Ucuz? 45 Kalemde Ölçtük",
        "seo_baslik": "Trendyol mu Amazon mu Daha Ucuz? 45 Ürün Karşılaştırması",
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
                "masrafı kalem kalem. Aylık güncellenen gerçek fiyatlarla.",
        "govde": _govde_okul,
        "vertikal": "okul",
    },
    {
        "slug": "150-kisilik-dugun-maliyeti",
        "baslik": "2026 150 Kişilik Düğün Maliyeti",
        "seo_baslik": "150 Kişilik Düğün Maliyeti 2026 — Kalem Kalem",
        "meta": "150 kişilik düğünün kalem kalem maliyeti: salon, gelinlik, takı, "
                "fotoğrafçı. Gerçek fiyat ölçümlerinden, aylık güncellenen rakamlarla.",
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
                "ve bütçe dağılımı. Aylık güncellenen gerçek fiyatlarla.",
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
            "ölçümü ayda iki kez tekrarlıyoruz.</p>\n"
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


def rehber_uret(rehber: dict, veriler: dict, tarih: str | None = None) -> str | None:
    """Tek bir rehber sayfasi. Veri yoksa None - bos sayfa YAYINLANMAZ."""
    govde = rehber["govde"](veriler)
    if not govde:
        return None
    tarih = tarih or date.today().isoformat()
    url = f"{SITE_KOK_URL}/rehber/{rehber['slug']}/"
    vconf = su.VERTIKALLER[rehber["vertikal"]]

    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": rehber["baslik"],
                "description": rehber["meta"],
                "datePublished": tarih,
                "dateModified": tarih,
                "inLanguage": "tr-TR",
                "mainEntityOfPage": url,
                "author": {"@type": "Organization", "name": "Maliyeti Ne?"},
                "publisher": {
                    "@type": "Organization",
                    "name": "Maliyeti Ne?",
                    "url": SITE_KOK_URL,
                },
            },
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
        ],
    }

    digerleri = "".join(
        f'<a href="/rehber/{r["slug"]}/">{r["baslik"]}</a>'
        for r in REHBERLER if r["slug"] != rehber["slug"]
    )

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_title(rehber)}</title>
<meta name="description" content="{rehber["meta"]}">
<link rel="canonical" href="{url}">
<link rel="stylesheet" href="/assets/css/style.css">
<meta property="og:title" content="{rehber["baslik"]}">
<meta property="og:description" content="{rehber["meta"]}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
{su.OG_ETIKETLERI}
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

  <span class="guncelleme-etiketi">Güncelleme: {tarih}</span>
  <h1>{rehber["baslik"]}</h1>
{govde}
  <p class="kunye">{tarih} tarihli ölçümlerden ·
    <a href="/{vconf['yol']}/metodoloji/">Yöntem</a></p>

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
<link rel="stylesheet" href="/assets/css/style.css">
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
    Her yazıdaki rakam, o gün ölçtüğümüz gerçek fiyatlardan geliyor ve
    veri yenilendikçe yazı da güncelleniyor.
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
        html = rehber_uret(r, veriler)
        if not html:
            print(f"  ATLANDI (veri yok): {r['slug']}")
            continue
        hedef = kok / r["slug"] / "index.html"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(html, encoding="utf-8")
        yazilanlar.append(r)
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
