# -*- coding: utf-8 -*-
"""
Maliyeti Ne? - Formul hesaplayicilari (/hesap/...)

NEDEN VAR: 2026-07-27'de dort rakip incelendi (nekadar.com.tr,
yenibirhesap.com, hesapsonuc.com, maliyeti.com.tr). Dordunun de
trafigi FORMUL HESAPLAYICILARINDAN geliyor - KDV, maas, kredi, kidem.
Bizde bu kategoride SIFIR sayfa vardi. "kdv hesaplama" aramasi "dugun
maliyeti"nden kat kat buyuk ve o sorgularda hic yoktuk.

BU KIRMIZI CIZGIYI IHLAL ETMIYOR: buradaki sayilar fiyat degil MEVZUAT.
Kidem tazminati bir kanun formulu, gelir vergisi bir teblig tarifesi,
taksit bir annuite denklemi - cevap TURETILEBILIR ve DOGRULANABILIR.
Olculmesi gereken bir seyi tahminle doldurmuyoruz.

RAKIPLERDEN AYRISTIGIMIZ NOKTA (kasitli):
  1. Her parametrenin yaninda kaynagi GORUNUR (teblig adi + Resmi
     Gazete tarih/sayi). hesapsonuc metin icinde mevzuata atif yapiyor
     ama hangi sayinin nereden geldigi belli degil; nekadar ve
     maliyeti.com.tr hic kaynak vermiyor.
  2. Her parametre kumesi GECERLILIK DONEMI tasiyor. Suresi gecmisse
     sayfa gorunur uyari basiyor - sessizce eski yilin vergisini
     vermiyor. Dort rakipte de bu yok; nekadar'in tum sitesi tek bir
     build (24 Haziran), maliyeti.com.tr alti aydir hic guncellenmemis.
  3. Maas hesabi AY soruyor. Gelir vergisi artan oranli ve matrah yil
     icinde birikiyor; ayi sormayan hesap yilin ilk ayi disinda yanlis.

MTV BILINCLI OLARAK YOK: elimizdeki dogrulanmis kademeler 1800 cc'ye
kadar. 2.0 motorlu araca yanlis rakam vermek yerine kalemi hic
acmiyoruz - eksik vergi tarifesi yayinlamak, hic yayinlamamaktan kotu.
(Arac sahip olma maliyeti hesaplayicisi /arac/hesaplayici/'da duruyor,
orada hangi kademeleri kapsadigi yazili.)

Kullanim:
  python hesaplayicilar.py            # tum hesap sayfalari + dizin
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import sayfa_uret as su

SITE_KOK = su.SITE_KOK
SITE_KOK_URL = su.SITE_KOK_URL
HESAP_KOK = "hesap"


# ----------------------------------------------------------
# TANIMLAR
#
# Her hesaplayici: gorunur metni, formulu, ornegi, SSS'i ve kullandigi
# resmi parametrelerin kaynagini tasir. `alanlar` formu, `js_govde`
# sonucu ekrana basan koddur.
#
# `kaynaklar` alani ZORUNLU (bir test bunu dogruluyor): parametresiz saf
# matematik hesaplarda formulun kendisi yazilir, mevzuata bagli
# hesaplarda teblig/kanun adi.
# ----------------------------------------------------------
HESAPLAYICILAR = [
    {
        "id": "kdv",
        "slug": "kdv-hesaplama",
        "ad": "KDV Hesaplama",
        "baslik": "KDV Hesaplama: Dahil ve Hariç Tutar",
        "soru": "KDV dahil ve hariç tutar nasıl hesaplanır?",
        "meta": "KDV dahil ve hariç tutarı %1, %10 ve %20 oranlarıyla anında hesaplayın. Oranların dayandığı mevzuat sayfada yazılı.",
        "ozet": (
            "KDV hariç tutara oranı uygulayıp eklersiniz; dahil tutardan "
            "geri gitmek için <strong>dahil ÷ (1 + oran)</strong> yaparsınız. "
            "Yürürlükteki üç oran %1, %10 ve %20."
        ),
        "formul": "KDV = matrah × oran &nbsp;·&nbsp; Hariç tutar = dahil tutar ÷ (1 + oran)",
        "kaynaklar": ["3065 sayılı KDV Kanunu", "2007/13033 sayılı BKK ekli listeler"],
        "alanlar": [
            {"id": "tutar", "etiket": "Tutar (TL)", "tip": "number", "varsayilan": "1000", "adim": "0.01"},
            {"id": "oran", "etiket": "KDV oranı", "tip": "select",
             "secenekler": [("0.20", "%20 — genel oran"), ("0.10", "%10 — gıda, tekstil, konaklama"),
                            ("0.01", "%1 — temel gıda, gazete")]},
            {"id": "yon", "etiket": "Hesaplama yönü", "tip": "select",
             "secenekler": [("haricten-dahile", "KDV hariç → dahil"),
                            ("dahilden-harice", "KDV dahil → hariç")]},
        ],
        "js": """
      const s = kdvHesapla(sayi("tutar"), parseFloat(deger("oran")), deger("yon"));
      if (!s) return null;
      return [
        ["KDV hariç tutar", s.haric, false],
        ["KDV (" + (s.oran * 100).toFixed(0) + "%)", s.kdv, false],
        ["KDV dahil tutar", s.dahil, true],
      ];""",
        "sss": [
            ("KDV dahil tutardan hariç tutar nasıl bulunur?",
             "Dahil tutarı (1 + oran)'a bölersiniz. %20 KDV'li 1.200 TL'nin hariç tutarı 1.200 ÷ 1,20 = 1.000 TL, KDV 200 TL'dir."),
            ("Hangi üründe hangi KDV oranı uygulanır?",
             "Oranlar 2007/13033 sayılı Bakanlar Kurulu Kararı'na ekli listelerle belirlenir: I. listede %1, II. listede %10, listelerde yer almayan her şeyde genel oran %20 uygulanır."),
            ("KDV'yi tutardan çıkarırken oranı doğrudan düşmek neden yanlış?",
             "1.200 TL'den %20 düşmek 960 TL verir; doğrusu 1.000 TL. Çünkü oran hariç tutar üzerinden hesaplanır, dahil tutar üzerinden değil. En sık yapılan hata bu."),
        ],
    },
    {
        "id": "maas",
        "slug": "brutten-nete-maas-hesaplama",
        "ad": "Brütten Nete Maaş Hesaplama",
        "baslik": "Brütten Nete Maaş Hesaplama (2026)",
        "soru": "2026'da brüt maaştan net maaş nasıl hesaplanır?",
        "meta": "2026 vergi tarifesi ve SGK oranlarıyla brütten nete, netten brüte maaş hesabı. Asgari ücret istisnası ve kümülatif matrah dahil.",
        "ozet": (
            "Brüt ücretten önce <strong>%14 SGK</strong> ve <strong>%1 işsizlik</strong> "
            "primi kesilir; kalan tutar gelir vergisi matrahıdır. Vergi 2026 ücret "
            "tarifesinden hesaplanır, sonra <strong>asgari ücret istisnası</strong> "
            "düşülür. Son olarak binde 7,59 damga vergisi uygulanır."
        ),
        "formul": (
            "Net = Brüt − (SGK %14 + İşsizlik %1) − (Gelir vergisi − asgari ücret istisnası) "
            "− (Damga ‰7,59 − asgari ücret istisnası)"
        ),
        "kaynaklar": [
            "332 Seri No.lu Gelir Vergisi Genel Tebliği (31.12.2025 R.G. 33124, 5. Mükerrer)",
            "5510 sayılı Kanun — 2026 prime esas kazanç sınırları",
            "488 sayılı Damga Vergisi Kanunu",
            "2026 Asgari Ücret Tespit Komisyonu Kararı",
        ],
        "alanlar": [
            {"id": "yon", "etiket": "Hesaplama yönü", "tip": "select",
             "secenekler": [("brutten", "Brütten nete"), ("netten", "Netten brüte")]},
            {"id": "ucret", "etiket": "Aylık ücret (TL)", "tip": "number", "varsayilan": "50000", "adim": "0.01"},
            {"id": "ay", "etiket": "Hangi ay?", "tip": "select",
             "secenekler": [(str(i), ad) for i, ad in enumerate(
                 ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
                  "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"], start=1)]},
        ],
        "alan_notu": (
            "Ay bilgisi şart: gelir vergisi artan oranlıdır ve matrah yıl içinde "
            "birikir. Aynı brüt ücret Ocak'ta ve Kasım'da farklı net verir. "
            "Hesap, yıl başından beri aynı ücretin alındığını varsayar."
        ),
        "js": """
      const ay = parseInt(deger("ay"), 10);
      const ucret = sayi("ucret");
      // Yil basindan beri ayni ucret varsayimi: onceki aylarin matrahi
      // tek bir ayin matrahinin (ay-1) katidir.
      let s;
      if (deger("yon") === "netten") {
        const tek = nettenBrutUcret(ucret, 1, 0);
        if (!tek) return null;
        s = nettenBrutUcret(ucret, ay, tek.vergi_matrahi * (ay - 1));
      } else {
        const tek = brutdenNetUcret(ucret, 1, 0);
        if (!tek) return null;
        s = brutdenNetUcret(ucret, ay, tek.vergi_matrahi * (ay - 1));
      }
      if (!s) return null;
      const satirlar = [
        ["Brüt ücret", s.brut, false],
        ["SGK primi (%14)", -s.sgk_isci, false],
        ["İşsizlik sigortası (%1)", -s.issizlik, false],
        ["Gelir vergisi", -s.gelir_vergisi, false],
        ["Damga vergisi", -s.damga_vergisi, false],
        ["Net ücret", s.net, true],
      ];
      if (s.gelir_vergisi_istisnasi > 0) {
        satirlar.push(["— bunun içinde asgari ücret istisnası", s.gelir_vergisi_istisnasi, false, "not"]);
      }
      if (s.tavan_asildi) {
        satirlar.push(["— SGK tavanı aşıldı, prim tavandan kesildi", null, false, "not"]);
      }
      return satirlar;""",
        "sss": [
            ("Asgari ücret istisnası nedir, benim maaşımı etkiler mi?",
             "Evet. 2022'den beri her çalışanın ücretinin asgari ücrete isabet eden kısmı gelir ve damga vergisinden istisna. Yani maaşınız ne olursa olsun, asgari ücretli bir çalışanın ödemediği vergiyi siz de ödemezsiniz. Bunu hesaba katmayan hesaplayıcılar net ücreti olduğundan düşük gösterir."),
            ("Aynı brüt maaş neden her ay farklı net veriyor?",
             "Gelir vergisi artan oranlıdır ve vergi matrahı yıl içinde birikir. Kümülatif matrah bir üst dilime geçtiğinde kesinti artar, net maaş düşer. Bu yüzden hesaplayıcı hangi ay olduğunu soruyor."),
            ("2026 net asgari ücret ne kadar?",
             "Brüt 33.030,00 TL, net 28.075,50 TL. Aradaki fark yalnızca %14 SGK ve %1 işsizlik primidir; asgari ücretli gelir vergisi ve damga vergisi ödemez."),
            ("SGK tavanı nedir?",
             "Primler ücretin tamamı üzerinden değil, tavana kadar olan kısmı üzerinden kesilir. 2026'da tavan aylık 297.270,00 TL — bu tutarın üzerindeki ücretlerde prim tavandan hesaplanır."),
            ("Bu hesap bordroyla birebir aynı çıkar mı?",
             "Kesintilerin ana kalemleri aynıdır. Ancak AGİ sonrası düzenlemeler, engellilik indirimi, özel sigorta veya sendika kesintisi, eksik gün ve teşvikler bordroya göre değişir. Bu hesap standart bir tam ay çalışması varsayar."),
        ],
    },
    {
        "id": "kidem",
        "slug": "kidem-tazminati-hesaplama",
        "ad": "Kıdem ve İhbar Tazminatı Hesaplama",
        "baslik": "Kıdem ve İhbar Tazminatı Hesaplama (2026)",
        "soru": "2026'da kıdem tazminatı nasıl hesaplanır?",
        "meta": "Kıdem ve ihbar tazminatını 2026 tavan tutarıyla hesaplayın. Kıdem tavanı 73.729,84 TL (Temmuz–Aralık 2026).",
        "ozet": (
            "Kıdem tazminatı, her tam hizmet yılı için <strong>30 günlük giydirilmiş "
            "brüt ücret</strong> kadardır; yıllık tutar <strong>kıdem tavanını</strong> "
            "aşamaz. Gelir vergisinden istisnadır, yalnızca damga vergisi kesilir. "
            "İhbar tazminatında tavan uygulanmaz ve gelir vergisine tabidir."
        ),
        "formul": (
            "Kıdem = min(giydirilmiş brüt, tavan) × hizmet yılı &nbsp;·&nbsp; "
            "İhbar = (giydirilmiş brüt ÷ 30) × ihbar süresi (gün)"
        ),
        "kaynaklar": [
            "1475 sayılı İş Kanunu md. 14 (kıdem tazminatı)",
            "4857 sayılı İş Kanunu md. 17 (ihbar süreleri)",
            "T.C. Çalışma ve Sosyal Güvenlik Bakanlığı — kıdem tazminatı tavanı: 73.729,84 TL (1 Temmuz – 31 Aralık 2026)",
            "488 sayılı Damga Vergisi Kanunu",
        ],
        "alanlar": [
            {"id": "ucret", "etiket": "Giydirilmiş brüt aylık ücret (TL)", "tip": "number",
             "varsayilan": "45000", "adim": "0.01"},
            {"id": "ay", "etiket": "Toplam hizmet süresi (ay)", "tip": "number",
             "varsayilan": "42", "adim": "1"},
            {"id": "ihbar", "etiket": "İhbar tazminatı da hesaplanacak mı?", "tip": "select",
             "secenekler": [("evet", "Evet"), ("hayir", "Hayır, yalnızca kıdem")]},
        ],
        "alan_notu": (
            "\"Giydirilmiş\" ücret, çıplak brüt ücrete yol, yemek, ikramiye gibi süreklilik "
            "arz eden yan ödemelerin aylık karşılığının eklenmiş halidir — kıdem hesabı "
            "bu tutar üzerinden yapılır, çıplak ücret üzerinden değil."
        ),
        "js": """
      const s = kidemIhbarHesapla(sayi("ucret"), sayi("ay"), deger("ihbar") === "evet");
      if (!s) return null;
      const satirlar = [
        ["Hesaba esas ücret", s.esas_ucret, false],
        ["Hizmet süresi", null, false, "not", s.hizmet_yili + " yıl " + s.artan_ay + " ay"],
        ["Kıdem tazminatı (brüt)", s.kidem_brut, false],
        ["Damga vergisi", -s.kidem_damga, false],
        ["Kıdem tazminatı (net)", s.kidem_net, !s.ihbar_brut],
      ];
      if (s.tavan_uygulandi) {
        satirlar.splice(1, 0, ["— ücret tavanı aştı, hesap tavandan yapıldı", s.tavan, false, "not"]);
      }
      if (s.ihbar_brut) {
        satirlar.push(["İhbar süresi", null, false, "not", s.ihbar_hafta + " hafta (" + s.ihbar_kademe + ")"]);
        satirlar.push(["İhbar tazminatı (brüt)", s.ihbar_brut, false]);
        satirlar.push(["Gelir vergisi", -s.ihbar_gelir_vergisi, false]);
        satirlar.push(["Damga vergisi", -s.ihbar_damga, false]);
        satirlar.push(["İhbar tazminatı (net)", s.ihbar_net, false]);
        satirlar.push(["TOPLAM (net)", s.toplam_net, true]);
      }
      return satirlar;""",
        "sss": [
            ("Kıdem tazminatı tavanı 2026'da ne kadar?",
             "1 Temmuz – 31 Aralık 2026 dönemi için 73.729,84 TL. Tavan yılda iki kez, Ocak ve Temmuz'da değişir. Giydirilmiş brüt ücretiniz bu tutarın üzerindeyse hesap tavandan yapılır."),
            ("Kıdem tazminatından vergi kesilir mi?",
             "Gelir vergisi kesilmez — kıdem tazminatı gelir vergisinden istisnadır. Yalnızca binde 7,59 damga vergisi kesilir. İhbar tazminatı ise gelir vergisine tabidir; en sık karıştırılan nokta budur."),
            ("İhbar tazminatında da tavan var mı?",
             "Hayır. Kıdemde tavan var, ihbarda yok. İhbar tazminatı giydirilmiş ücretin tamamı üzerinden hesaplanır, bu yüzden yüksek ücretlerde kıdemden daha büyük çıkabilir."),
            ("İhbar süresi ne kadar?",
             "İş Kanunu md. 17'ye göre hizmet süresine bağlıdır: 6 aydan az için 2 hafta, 6 ay–1,5 yıl için 4 hafta, 1,5–3 yıl için 6 hafta, 3 yıldan fazla için 8 hafta."),
            ("Yıldan artan aylar hesaba katılır mı?",
             "Evet, artan süre oransal olarak eklenir. 2 yıl 6 ay çalışan biri 2,5 yıllık kıdem tazminatına hak kazanır."),
        ],
    },
    {
        "id": "tapu",
        "slug": "tapu-harci-hesaplama",
        "ad": "Tapu Harcı Hesaplama",
        "baslik": "Tapu Harcı Hesaplama (2026)",
        "soru": "Tapu harcı nasıl hesaplanır, kim ne kadar öder?",
        "meta": "Satış bedeline göre tapu harcı: alıcı ve satıcı ayrı ayrı binde 20 öder. 492 sayılı Harçlar Kanunu (4) sayılı tarife.",
        "ozet": (
            "Tapu harcı, beyan edilen satış bedelinin <strong>binde 20'si</strong> "
            "kadardır ve <strong>alıcı ile satıcı bunu ayrı ayrı öder</strong> — "
            "yani devlete giden toplam binde 40, yani %4."
        ),
        "formul": "Bir tarafın harcı = satış bedeli × 0,02 &nbsp;·&nbsp; Toplam = satış bedeli × 0,04",
        "kaynaklar": ["492 sayılı Harçlar Kanunu — (4) sayılı tarife, 20/a bendi"],
        "alanlar": [
            {"id": "bedel", "etiket": "Beyan edilen satış bedeli (TL)", "tip": "number",
             "varsayilan": "5000000", "adim": "1"},
            {"id": "taraf", "etiket": "Kim için hesaplansın?", "tip": "select",
             "secenekler": [("alici", "Yalnızca alıcı"), ("satici", "Yalnızca satıcı"),
                            ("ikisi", "İkisinin toplamı")]},
        ],
        "alan_notu": (
            "Harç, gerçek satış bedeli üzerinden hesaplanır. Emlak vergisi değerinin "
            "altında beyan yapılamaz; düşük beyan tespit edilirse harç farkı ve "
            "vergi ziyaı cezası doğar. Döner sermaye ve ipotek harcı bu hesaba dahil değildir."
        ),
        "js": """
      const s = tapuHarciHesapla(sayi("bedel"), deger("taraf"));
      if (!s) return null;
      return [
        ["Satış bedeli", s.satis_bedeli, false],
        ["Alıcının harcı (binde 20)", s.alici, false],
        ["Satıcının harcı (binde 20)", s.satici, false],
        ["Ödenecek tutar", s.odenecek, true],
      ];""",
        "sss": [
            ("Tapu harcını alıcı mı satıcı mı öder?",
             "Kanunen ikisi de öder: alıcı binde 20, satıcı binde 20. Uygulamada tarafların anlaşıp tamamını bir tarafa yüklediği görülür ama bu kanuni yükümlülüğü değiştirmez."),
            ("5 milyon TL'lik evin tapu harcı ne kadar?",
             "Gerçek satış bedeli 5.000.000 TL ise alıcı 100.000 TL, satıcı "
             "100.000 TL; toplam 200.000 TL tapu harcı doğar. Döner sermaye "
             "hizmet bedeli bu örneğe dahil değildir."),
            ("Harç hangi tutar üzerinden hesaplanır?",
             "Beyan edilen gerçek satış bedeli üzerinden. Beyan, taşınmazın emlak vergisi değerinin altında olamaz. Düşük beyan tespit edilirse eksik harç ile birlikte vergi ziyaı cezası istenir."),
            ("Tapuda ödenen tek masraf harç mı?",
             "Hayır. Harcın yanında döner sermaye hizmet bedeli alınır; kredili alımda ayrıca ipotek harcı ve ekspertiz ücreti doğar. Bu hesaplayıcı yalnızca tapu harcını verir."),
            ("Bu araç ipotek, bağış, miras veya intifa harcını hesaplar mı?",
             "Hayır. Araç yalnız Türkiye'deki bedelli gayrimenkul satışının 20/a "
             "tapu harcını hesaplar. İpotek, bağış/hibe, miras-intikal ve intifa "
             "hakkı farklı işlem ve matrahlara tabidir; KKTC işlemleri de bu "
             "kapsamda değildir."),
        ],
    },
    {
        "id": "issizlik",
        "slug": "issizlik-maasi-hesaplama",
        "ad": "İşsizlik Maaşı Hesaplama",
        "baslik": "İşsizlik Maaşı Hesaplama (2026)",
        "soru": "2026'da işsizlik maaşı ne kadar, kaç ay ödenir?",
        "meta": "Son 4 ayın ortalama brüt kazancına göre işsizlik ödeneği ve ödeme süresi. 2026 tavanı 26.223,44 TL net.",
        "ozet": (
            "İşsizlik ödeneği, son dört ayın <strong>ortalama brüt kazancının "
            "%40'ı</strong>dır ve brüt asgari ücretin %80'ini aşamaz — 2026'da "
            "tavan <strong>26.223,44 TL net</strong>. Gelir vergisi kesilmez, "
            "yalnızca damga vergisi düşülür."
        ),
        "formul": "Ödenek = min(son 4 ay ortalama brüt × 0,40 ; brüt asgari ücret × 0,80) − damga vergisi",
        "kaynaklar": [
            "4447 sayılı İşsizlik Sigortası Kanunu md. 50",
            "2026 Asgari Ücret Tespit Komisyonu Kararı (tavan hesabı için)",
            "488 sayılı Damga Vergisi Kanunu",
        ],
        "alanlar": [
            {"id": "brut", "etiket": "Son 4 ayın ortalama brüt ücreti (TL)", "tip": "number",
             "varsayilan": "50000", "adim": "0.01"},
            {"id": "gun", "etiket": "Son 3 yıldaki prim gün sayısı", "tip": "select",
             "secenekler": [("600", "600 gün → 6 ay ödeme"), ("900", "900 gün → 8 ay ödeme"),
                            ("1080", "1080 gün ve üzeri → 10 ay ödeme")]},
        ],
        "alan_notu": (
            "Ödenek almak için son 120 gün kesintisiz hizmet akdine tabi olmak ve "
            "son 3 yılda en az 600 gün prim ödemiş olmak gerekir. İstifa eden "
            "ya da haklı nedenle işten çıkarılan çalışan ödenek alamaz."
        ),
        "js": """
      const s = issizlikOdenegiHesapla(sayi("brut"), parseInt(deger("gun"), 10));
      if (!s) return null;
      const satirlar = [
        ["Ortalama brüt kazanç", s.ortalama_brut, false],
        ["Aylık ödenek (brüt)", s.odenek_brut, false],
        ["Damga vergisi", -s.damga, false],
        ["Aylık ödenek (net)", s.odenek_net, true],
        ["Ödeme süresi", null, false, "not", s.sure_ay + " ay"],
        ["Toplam alacağınız", s.toplam, false],
      ];
      if (s.tavan_uygulandi) {
        satirlar.splice(2, 0, ["— tavan uygulandı (brüt asgari ücretin %80'i)", s.tavan_brut, false, "not"]);
      }
      return satirlar;""",
        "sss": [
            ("İşsizlik maaşı 2026'da en fazla ne kadar?",
             "Net 26.223,44 TL. Tavan, brüt asgari ücretin %80'i olarak hesaplanır: 33.030 × 0,80 = 26.424 TL brüt, binde 7,59 damga vergisi düşülünce 26.223,44 TL net kalır."),
            ("50.000 TL brüt ücretle işsizlik maaşı ne kadar?",
             "Son dört ayın ortalama brüt kazancı 50.000 TL ise ödenek 20.000 TL "
             "brüt, damga vergisi sonrası 19.848,20 TL nettir. 600 prim gününde "
             "6 ay boyunca toplam 119.089,20 TL ödenir; diğer hak kazanma şartları "
             "ayrıca sağlanmalıdır."),
            ("Kaç ay ödenir?",
             "Son üç yıldaki prim gün sayısına göre: 600 gün için 6 ay, 900 gün için 8 ay, 1080 gün ve üzeri için 10 ay."),
            ("İşsizlik ödeneğinden vergi kesilir mi?",
             "Gelir vergisi kesilmez. Yalnızca binde 7,59 damga vergisi düşülür."),
            ("İstifa edersem işsizlik maaşı alabilir miyim?",
             "Hayır. Ödenek, kendi isteği ve kusuru dışında işini kaybedenlere ödenir. İstifa ya da işverenin haklı nedenle feshi durumunda hak doğmaz."),
        ],
    },
    {
        "id": "kira",
        "slug": "kira-gelir-vergisi-hesaplama",
        "ad": "Kira Gelir Vergisi Hesaplama",
        "baslik": "Kira Gelir Vergisi Hesaplama (2026)",
        "soru": "2026'da kira gelirinden ne kadar vergi ödenir?",
        "meta": "Konut ve işyeri kira geliri vergisi: 58.000 TL mesken istisnası, götürü veya gerçek gider yöntemi, 2026 tarifesi.",
        "ozet": (
            "Konut kira gelirinin <strong>58.000 TL'si istisna</strong>dır (2026). "
            "Kalan tutardan gider düşülür — <strong>götürü yöntemde %15</strong>, "
            "gerçek yöntemde belgelendirilen giderler. Kalan matraha ücret dışı "
            "gelir vergisi tarifesi uygulanır."
        ),
        "formul": "Matrah = (yıllık kira − istisna) − gider &nbsp;·&nbsp; Vergi = artan oranlı tarife(matrah)",
        "kaynaklar": [
            "332 Seri No.lu Gelir Vergisi Genel Tebliği — 2026 mesken istisnası 58.000 TL",
            "193 sayılı Gelir Vergisi Kanunu md. 21 (mesken istisnası) ve md. 74 (götürü gider %15)",
        ],
        "alanlar": [
            {"id": "kira", "etiket": "Yıllık toplam kira geliri (TL)", "tip": "number",
             "varsayilan": "180000", "adim": "0.01"},
            {"id": "tur", "etiket": "Taşınmaz türü", "tip": "select",
             "secenekler": [("konut", "Konut (mesken istisnası var)"),
                            ("isyeri", "İşyeri (istisna yok)")]},
            {"id": "yontem", "etiket": "Gider yöntemi", "tip": "select",
             "secenekler": [("goturu", "Götürü gider (%15)"), ("gercek", "Gerçek gider")]},
            {"id": "gercek", "etiket": "Gerçek gider tutarı (TL)", "tip": "number",
             "varsayilan": "0", "adim": "0.01"},
        ],
        "alan_notu": (
            "Mesken istisnası yalnızca konut kirasında geçerlidir ve ticari/zirai "
            "kazancı olanlar ile beyan etmesi gerekip etmeyenler için istisnadan "
            "yararlanma şartları farklıdır. Götürü gider seçen mükellef iki yıl "
            "geçmeden gerçek gider yöntemine dönemez."
        ),
        "js": """
      const s = kiraGelirVergisiHesapla(sayi("kira"), deger("tur"), deger("yontem"), sayi("gercek"));
      if (!s) return null;
      const satirlar = [["Yıllık kira geliri", s.yillik_kira, false]];
      if (s.istisna_uygulandi) satirlar.push(["Mesken istisnası", -s.istisna, false]);
      satirlar.push(["Gider", -s.gider, false]);
      satirlar.push(["Vergi matrahı", s.matrah, false]);
      satirlar.push(["Ödenecek gelir vergisi", s.vergi, true]);
      satirlar.push(["Vergi sonrası kalan", s.kalan, false]);
      return satirlar;""",
        "sss": [
            ("2026 kira geliri istisnası ne kadar?",
             "Konut kira gelirinde 58.000 TL. Bu tutarın altında konut kira geliri elde eden ve başka beyan gerektiren geliri olmayan kişi beyanname vermez. İşyeri kirasında mesken istisnası uygulanmaz."),
            ("Yıllık 180.000 TL konut kirasının vergisi ne kadar?",
             "2026 parametreleri ve götürü gider yöntemiyle: 58.000 TL istisna, "
             "18.300 TL götürü gider sonrası matrah 103.700 TL; hesaplanan gelir "
             "vergisi 15.555 TL'dir. Başka beyana tabi gelirler sonucu değiştirebilir."),
            ("Götürü gider mi gerçek gider mi avantajlı?",
             "Götürü yöntem, istisna sonrası kalan tutarın %15'ini belge aramadan düşer. Gerçek giderleriniz (faiz, amortisman, tamir, sigorta) bu oranın üzerindeyse gerçek gider daha avantajlıdır. Götürü seçen mükellef iki yıl geçmeden gerçek yönteme dönemez."),
            ("Kira geliri hangi tarifeden vergilendirilir?",
             "Ücret dışı gelir tarifesinden. Ücret tarifesiyle ilk iki dilimi aynıdır, üçüncü dilimde ayrışır: kirada 1.000.000 TL, ücrette 1.500.000 TL."),
            ("Kirayı elden aldım, yine de beyan etmem gerekir mi?",
             "Evet. Ayrıca konutlarda tutarı ne olursa olsun kira tahsilatının banka veya PTT üzerinden yapılması zorunludur; aksi halde ceza uygulanır."),
            # 2026-08-09, Search Console: "kira vergisi cezasi hesaplama"
            # ve varyantlari gosterim aliyordu ama sayfada karsiligi yoktu.
            # CEZA TUTARI YAZILMIYOR - oranlar VUK'a ve yeniden degerlemeye
            # bagli, birincil kaynaktan dogrulanmadan rakam vermeyiz.
            # Yazilan sey KESIN olan kural: istisnanin kaybi (GVK md.21).
            ("Kira gelirini beyan etmezsem ne olur?",
             "En somut sonuç şu: <strong>istisnadan yararlanma hakkınızı "
             "kaybedersiniz</strong>. Konut kira geliri istisnası, beyanname "
             "verilmediği ya da eksik beyan edildiği idarece tespit edilirse "
             "uygulanmaz (GVK md. 21). Yani 58.000 TL'lik indirim düşer ve "
             "verginiz kiranın tamamı üzerinden hesaplanır. Buna ek olarak "
             "vergi ziyaı cezası ve gecikme faizi işler; bu tutarlar Vergi Usul "
             "Kanunu'na ve ilgili döneme göre değiştiği için burada oran "
             "yazmıyoruz — güncel tutar için Gelir İdaresi Başkanlığı'na bakın."),
            # "tarla kira vergisi hesaplama" sorgusu geliyordu; bu hesap
            # ONU KAPSAMIYOR ve bunu soylemek, yanlis sonuc vermekten iyi.
            ("Tarla veya arazi kirası da bu hesaba girer mi?",
             "Hayır. Bu hesaplayıcı <strong>konut ve işyeri</strong> kira geliri "
             "içindir. Tarım arazisi kirası da gayrimenkul sermaye iradı sayılır "
             "ama <strong>58.000 TL'lik istisna yalnızca konuta özgüdür</strong> — "
             "araziye uygulanmaz. Araziyi kendiniz işletiyorsanız gelir kira "
             "değil zirai kazanç olur ve tamamen farklı kurallara tabidir. "
             "Yanlış sonuç vermemek için bu hesabı arazi kirası için kullanmayın."),
        ],
    },
    {
        "id": "izin",
        "slug": "yillik-izin-hesaplama",
        "ad": "Yıllık İzin Hesaplama",
        "baslik": "Yıllık Ücretli İzin Süresi Hesaplama",
        "soru": "Kaç gün yıllık iznim var?",
        "meta": "Hizmet sürenize göre yıllık ücretli izin gün sayısı. 4857 sayılı İş Kanunu md. 53 kademeleri.",
        "ozet": (
            "Yıllık izin hizmet süresine bağlıdır: <strong>1–5 yıl arası 14 gün, "
            "5–15 yıl arası 20 gün, 15 yıl ve üzeri 26 gün</strong>. 18 yaşından "
            "küçük ve 50 yaşından büyük çalışanlarda izin 20 günden az olamaz."
        ),
        "formul": "İzin günü = İş Kanunu md. 53 kademesi (yaş istisnası saklı)",
        "kaynaklar": ["4857 sayılı İş Kanunu md. 53 ve md. 56"],
        "alanlar": [
            {"id": "yil", "etiket": "Hizmet süresi (yıl)", "tip": "number",
             "varsayilan": "6", "adim": "1"},
            {"id": "yas", "etiket": "Yaşınız", "tip": "number", "varsayilan": "35", "adim": "1"},
        ],
        "alan_notu": (
            "İzin hakkı için en az bir yıl çalışmış olmak gerekir; deneme süresi bu "
            "bir yılın içinde sayılır. İzin günleri iş günü olarak hesaplanır — "
            "hafta tatili ve genel tatil günleri izinden düşülmez."
        ),
        "js": """
      const s = yillikIzinHesapla(sayi("yil"), sayi("yas"));
      if (!s) return null;
      const satirlar = [
        ["Hizmet süresi kademesi", null, false, "not", s.kademe],
        ["Yıllık izin hakkı", null, true, "not", s.gun + " iş günü"],
      ];
      if (s.yas_istisnasi) {
        satirlar.push(["— yaş istisnası uygulandı (18 altı / 50 üstü en az 20 gün)", null, false, "not"]);
      }
      return satirlar;""",
        "sss": [
            ("Yıllık izin iş günü mü takvim günü mü?",
             "İş günü. İzin süresine rastlayan hafta tatili, ulusal bayram ve genel tatil günleri izinden sayılmaz, izne eklenir."),
            ("Kullanılmayan izin ne olur?",
             "Yıllık izin ücreti ancak iş sözleşmesi sona erdiğinde ödenir. Çalışırken iznin parayla değiştirilmesi kanunen mümkün değildir; hak kaybolmaz, birikir."),
            ("İzin hakkı ne zaman doğar?",
             "İşe başladığı günden itibaren, deneme süresi de dahil, en az bir yıl çalışmış olan işçi yıllık izne hak kazanır."),
        ],
    },
    {
        "id": "mesai",
        "slug": "fazla-mesai-hesaplama",
        "ad": "Fazla Mesai Ücreti Hesaplama",
        "baslik": "Fazla Mesai Ücreti Hesaplama",
        "soru": "Fazla mesai ücreti nasıl hesaplanır?",
        "meta": "Saatlik ücret üzerinden %50 zamlı fazla çalışma ve %100 zamlı tatil mesaisi hesabı. İş Kanunu md. 41 ve 47.",
        "ozet": (
            "Haftalık 45 saati aşan çalışma fazla çalışmadır ve saat ücreti "
            "<strong>%50 zamlı</strong> ödenir. Hafta tatili ve genel tatil "
            "çalışması <strong>%100 zamlı</strong>dır. Fazla çalışma yılda "
            "270 saati aşamaz."
        ),
        "formul": "Fazla mesai = (aylık brüt ÷ 225) × 1,50 × saat &nbsp;·&nbsp; Tatil mesaisi = (aylık brüt ÷ 225) × 2,00 × saat",
        "kaynaklar": [
            "4857 sayılı İş Kanunu md. 41 (fazla çalışma, %50 zam, yıllık 270 saat sınırı)",
            "4857 sayılı İş Kanunu md. 47 (genel tatil ve hafta tatili çalışması)",
        ],
        "alanlar": [
            {"id": "brut", "etiket": "Aylık brüt ücret (TL)", "tip": "number",
             "varsayilan": "50000", "adim": "0.01"},
            {"id": "fazla", "etiket": "Aylık fazla çalışma (saat)", "tip": "number",
             "varsayilan": "20", "adim": "1"},
            {"id": "tatil", "etiket": "Tatil günü çalışması (saat)", "tip": "number",
             "varsayilan": "0", "adim": "1"},
        ],
        "alan_notu": (
            "Saatlik ücret, aylık brüt ücretin 225'e bölünmesiyle bulunur "
            "(30 gün × 7,5 saat). Sonuç brüt tutardır; ele geçen tutar için "
            "SGK ve vergi kesintileri ayrıca düşülür."
        ),
        "js": """
      const s = fazlaMesaiHesapla(sayi("brut"), sayi("fazla"), sayi("tatil"));
      if (!s) return null;
      const satirlar = [
        ["Saatlik brüt ücret", s.saatlik_ucret, false],
        ["Fazla çalışma (%50 zamlı)", s.fazla_mesai, false],
        ["Tatil mesaisi (%100 zamlı)", s.tatil_mesaisi, false],
        ["Toplam (brüt)", s.toplam_brut, true],
      ];
      if (s.yillik_limit_asildi) {
        satirlar.push(["— bu tempo yıllık " + s.yillik_azami + " saat sınırını aşar", null, false, "not"]);
      }
      return satirlar;""",
        "sss": [
            ("Fazla mesai ücreti ne kadar zamlı ödenir?",
             "Haftalık 45 saati aşan çalışmada saat ücretinin %50 fazlası ödenir. Hafta tatili ve genel tatil günlerindeki çalışmada zam %100'dür."),
            ("Fazla çalışmanın yıllık sınırı var mı?",
             "Evet, yılda 270 saat. Ayrıca fazla çalışma için işçinin yazılı onayı gerekir ve bu onay her yıl yenilenmelidir."),
            ("Zam yerine izin verilebilir mi?",
             "Evet. İşçi isterse her fazla çalışma saati karşılığında 1 saat 30 dakika serbest zaman kullanabilir; bu hakkı altı ay içinde kullanması gerekir."),
        ],
    },
    {
        "id": "icerik",
        "slug": "youtube-gelir-hesaplama",
        "ad": "YouTube Gelir Hesaplama",
        "baslik": "YouTube Para Kazanma ve Gelir Hesaplama",
        "soru": "YouTube'dan para kazanmak için kaç izlenme gerekir?",
        "meta": "YouTube para kazanma şartları ve izlenme/RPM'e göre gelir hesabı. Tek uydurma rakam değil, resmi eşikler ve duyarlılık tablosu.",
        "ozet": (
            "YouTube gelir hesabının formülü basit: <strong>(izlenme ÷ 1000) × RPM</strong>. "
            "Ama para kazanmanın iki ayrı eşiği var. 2026-08-22 itibarıyla fan "
            "destekli özellikler için 500 abone + son 90 günde 3 yükleme + "
            "3.000 saat izlenme ya da 3 milyon Shorts görüntülemesi; reklam geliri "
            "için 1.000 abone + 4.000 saat izlenme ya da 10 milyon Shorts "
            "görüntülemesi aranıyor. RPM ise <strong>resmî olarak yayınlanmıyor</strong>; "
            "kanala, ülkeye ve döneme göre değiştiği için tek rakam vermiyoruz."
        ),
        "formul": "Aylık gelir = (aylık izlenme ÷ 1000) × RPM × kur",
        "kaynaklar": [
            "YouTube Help — YouTube İş Ortağı Programı koşulları: "
            "<a href=\"https://support.google.com/youtube/answer/72857?hl=tr\">support.google.com/youtube/answer/72857</a>",
            "Google Blog, 11 Ağustos 2026 — 1 Şubat 2027 YPP eşik değişikliği: "
            "<a href=\"https://blog.google/intl/en-mena/product-updates/connect-communicate/new-opportunities-to-earn-and-changes-to-the-youtube-partner-program/\">blog.google</a>",
            "Hesap saf aritmetiktir. RPM değeri kullanıcıdan alınır — resmî bir "
            "kaynağı olmadığı için tarafımızdan varsayılmaz.",
        ],
        "alanlar": [
            {"id": "izlenme", "etiket": "Aylık izlenme", "tip": "number",
             "varsayilan": "500000", "adim": "1"},
            {"id": "rpm", "etiket": "RPM (1000 izlenme başına gelir, boş bırakabilirsiniz)",
             "tip": "number", "varsayilan": "", "adim": "0.01", "zorunlu": False},
            {"id": "kur", "etiket": "Kur (RPM dolarsa güncel USD/TRY, TL ise 1)",
             "tip": "number", "varsayilan": "1", "adim": "0.01"},
        ],
        "alan_notu": (
            "RPM'inizi YouTube Studio → Analizler → Gelir sekmesinde görebilirsiniz. "
            "1 Şubat 2027'den itibaren yeni reklam/Premium başvurularında eşik "
            "8.000 saat ya da 20 milyon Shorts görüntülemesine çıkacak; Google'ın "
            "duyurusuna göre mevcut YPP üreticileri bundan etkilenmiyor. Bu hesap "
            "sponsorluk, üyelik ve ürün satışını içermez."
        ),
        "js": """
      const s = icerikGeliriHesapla(sayi("izlenme"), sayi("rpm"), sayi("kur"));
      if (!s) return null;
      const satirlar = [];
      if (s.secilen_rpm) {
        satirlar.push(["Girdiğiniz RPM ile aylık", s.secilen_aylik, true]);
        satirlar.push(["Yıllık", s.secilen_yillik, false]);
        satirlar.push(["RPM bilinmiyorsa cevap bir aralıktır:", null, false, "not"]);
      } else {
        satirlar.push(["RPM girmediniz — cevap tek sayı değil, aralık:", null, false, "not"]);
      }
      s.duyarlilik.forEach(function (d) {
        satirlar.push(["RPM " + d.rpm + " ise aylık", d.aylik, false]);
      });
      return satirlar;""",
        "sss": [
            ("YouTube'dan para kazanma şartları ne?",
             "2026-08-22 itibarıyla ilk YPP eşiği 500 abone, son 90 günde 3 herkese açık yükleme ve 3.000 saat izlenme ya da 3 milyon Shorts görüntülemesi. Reklam geliri için eşik 1.000 abone ve 4.000 saat izlenme ya da 10 milyon Shorts görüntülemesi."),
            ("2027'de YouTube para kazanma şartları değişiyor mu?",
             "Evet. Google'ın 11 Ağustos 2026 duyurusuna göre 1 Şubat 2027'den itibaren yeni reklam ve YouTube Premium gelir başvurularında izlenme eşiği 8.000 saat ya da 20 milyon Shorts görüntülemesi olacak. Duyuru mevcut YPP üreticilerinin etkilenmediğini söylüyor."),
            ("Neden tek bir rakam vermiyorsunuz?",
             "Çünkü veremeyiz. Gelirin tamamı RPM'e bağlı ve RPM'in resmî, yayınlanmış bir değeri yok; kanalın konusuna, izleyicinin bulunduğu ülkeye ve reklam sezonuna göre kat kat değişiyor. Tek bir sayı vermek uydurma olurdu; onun yerine RPM'e göre nasıl değiştiğini gösteriyoruz."),
            ("RPM ile CPM aynı şey mi?",
             "Değil. CPM reklamverenin 1000 gösterim için ödediği tutar; RPM ise YouTube payı düşüldükten sonra size 1000 izlenme başına kalan tutardır. Kazancınızı belirleyen RPM'dir."),
            ("Kendi RPM'imi nereden öğrenirim?",
             "YouTube Studio → Analizler → Gelir sekmesinde geçmiş dönem RPM'iniz yazar. Hesaplamayı o değerle yaparsanız sonuç size özel olur."),
            ("Reklam geliri kanalın tek geliri mi?",
             "Hayır ve çoğu kanalda en büyüğü de değil. Sponsorluk, kanal üyeliği, süper sohbet ve ürün satışı genellikle reklamdan daha büyük kalem olur. Bu hesap yalnızca reklam tarafını modeller."),
        ],
    },
    {
        "id": "bilesik-faiz",
        "slug": "bilesik-faiz-hesaplama",
        "ad": "Bileşik Faiz Hesaplama",
        "baslik": "Bileşik Faiz ve Birikim Hesaplama",
        "soru": "Bileşik faizle param ne kadar büyür?",
        "meta": "Anapara, aylık düzenli katkı ve yıllık getiri oranıyla bileşik faiz hesabı. Kaç yılda ne kadar birikir?",
        "ozet": (
            "Bileşik faizde getiri anaparaya eklenir ve sonraki dönemde o da "
            "kazandırır. Düzenli aylık katkı varsa <strong>süre, orandan daha "
            "belirleyici</strong> olur — hesabı iki senaryoyla karşılaştırarak "
            "bunu görebilirsiniz."
        ),
        "formul": "Gelecek değer = A × (1+i)ⁿ + K × ((1+i)ⁿ − 1) ÷ i &nbsp;— i: aylık oran, n: ay",
        "kaynaklar": ["Bileşik faiz ve annüite gelecek değeri formülü — finansal matematik"],
        "alanlar": [
            {"id": "anapara", "etiket": "Başlangıç tutarı (TL)", "tip": "number", "varsayilan": "100000", "adim": "0.01"},
            {"id": "katki", "etiket": "Aylık düzenli katkı (TL)", "tip": "number", "varsayilan": "5000", "adim": "0.01"},
            {"id": "oran", "etiket": "Yıllık getiri oranı (%)", "tip": "number", "varsayilan": "40", "adim": "0.01"},
            {"id": "yil", "etiket": "Süre (yıl)", "tip": "number", "varsayilan": "10", "adim": "1"},
        ],
        "alan_notu": (
            "Hesap nominal getiriyi verir; enflasyon düşülmemiştir. Paranın "
            "gerçek alım gücündeki değişim için "
            "<a href=\"/hesap/alim-gucu-hesaplama/\">alım gücü hesaplayıcısına</a> bakın."
        ),
        "js": """
      const s = bilesikFaizHesapla(sayi("anapara"), sayi("katki"), sayi("oran"), sayi("yil"));
      if (!s) return null;
      return [
        ["Toplam birikim", s.toplam, true],
        ["Yatırdığınız para", s.yatirilan, false],
        ["Getiri", s.kazanc, false],
        ["Süre", null, false, "not", s.ay + " ay"],
      ];""",
        "sss": [
            ("Bileşik faiz basit faizden nasıl farklı?",
             "Basit faiz her dönem sadece anaparadan hesaplanır; bileşik faizde kazanılan getiri anaparaya eklenir ve sonraki dönem o da kazandırır. Fark kısa vadede küçük, uzun vadede belirleyicidir."),
            ("Yıllık oranı 12'ye bölmek doğru mu?",
             "Bu hesap öyle yapar (nominal aylık oran). Efektif yıllık getiri bileşiklenme yüzünden biraz daha yüksek çıkar: aylık %3, yıllık %42,6 eder — 12 × 3 = %36 değil."),
            ("Enflasyon hesaba dahil mi?",
             "Hayır, sonuç nominaldir. %40 getiri, enflasyon %40 ise alım gücünüz aynı kalmış demektir. Reel değişim için alım gücü hesaplayıcısını kullanın."),
        ],
    },
    {
        "id": "birikim",
        "slug": "birikim-hedefi-hesaplama",
        "ad": "Birikim Hedefi Hesaplama",
        "baslik": "Birikim Hedefi: Ayda Ne Kadar Biriktirmeliyim?",
        "soru": "Hedefime ulaşmak için ayda ne kadar biriktirmeliyim?",
        "meta": "Hedef tutar, süre ve getiri oranına göre aylık biriktirmeniz gereken tutar. Bileşik faizin tersi hesap.",
        "ozet": (
            "Bir hedefe belirli sürede ulaşmak için ayda ne kadar ayırmanız "
            "gerektiğini hesaplar. Elinizde başlangıç sermayesi varsa onun "
            "getirisi de düşülür."
        ),
        "formul": "Aylık = (hedef − başlangıç×(1+i)ⁿ) ÷ ((1+i)ⁿ − 1) ÷ i",
        "kaynaklar": ["Annüite formülünün tersi — finansal matematik"],
        "alanlar": [
            {"id": "hedef", "etiket": "Hedef tutar (TL)", "tip": "number", "varsayilan": "500000", "adim": "0.01"},
            {"id": "baslangic", "etiket": "Şu an elinizdeki (TL)", "tip": "number", "varsayilan": "50000", "adim": "0.01"},
            {"id": "oran", "etiket": "Yıllık getiri oranı (%)", "tip": "number", "varsayilan": "40", "adim": "0.01"},
            {"id": "ay", "etiket": "Süre (ay)", "tip": "number", "varsayilan": "24", "adim": "1"},
        ],
        "js": """
      const s = birikimHedefiHesapla(sayi("hedef"), sayi("baslangic"), sayi("oran"), sayi("ay"));
      if (!s) return null;
      if (s.zaten_yeterli) {
        return [["Elinizdeki para bu sürede hedefi zaten geçiyor", s.baslangic_getirisi, true]];
      }
      return [
        ["Ayda biriktirmeniz gereken", s.aylik, true],
        ["Başlangıç sermayenizin getirisi", s.baslangic_getirisi, false],
        ["Toplam yatıracağınız", s.toplam_yatirilacak, false],
        ["Hedef", s.hedef, false],
      ];""",
        "sss": [
            ("Getiri oranını kaç girmeliyim?",
             "Riski olmayan bir getiri varsaymak yanıltıcı olur. Mevduat, fon ve borsa getirileri farklıdır ve geçmiş getiri geleceği garanti etmez. İhtiyatlı bir oranla hesaplayıp sonucu iyimser senaryoyla karşılaştırmak daha sağlıklı."),
            ("Enflasyonu nasıl hesaba katarım?",
             "Hedefiniz bugünün fiyatlarıyla belirlenmişse, süre sonunda o tutar aynı şeyi almaya yetmez. Hedefi enflasyona göre büyütmek için alım gücü hesaplayıcısını kullanabilirsiniz."),
            ("Aylık katkıyı artırırsam ne değişir?",
             "Kısa vadede süre ve katkı miktarı, getiri oranından daha belirleyicidir. 24 ayda hedefe ulaşmakta oranı iki katına çıkarmak, katkıyı %20 artırmak kadar bile etki etmeyebilir."),
        ],
    },
    {
        "id": "yakit",
        "slug": "yakit-maliyeti-hesaplama",
        "ad": "Yakıt Maliyeti Hesaplama",
        "baslik": "Arabam Ne Kadar Yakar? Yakıt Maliyeti Hesaplama",
        "soru": "Bu yol bana yakıt olarak kaça patlar?",
        "meta": "Mesafe, ortalama tüketim ve litre fiyatına göre yolun yakıt "
                "maliyeti, km başına gider ve 100 km maliyeti.",
        "ozet": (
            "Yakıt maliyeti <strong>mesafe × tüketim ÷ 100 × litre fiyatı</strong>. "
            "Litre fiyatını siz giriyorsunuz: akaryakıt fiyatı günlük değişiyor ve "
            "ilden ile farklı, buraya sabit bir rakam yazsak ertesi gün yanlış olurdu."
        ),
        "formul": "Yakıt = (mesafe × ortalama tüketim ÷ 100) × litre fiyatı",
        "kaynaklar": ["Orantı — temel aritmetik"],
        "alanlar": [
            {"id": "mesafe", "etiket": "Mesafe (km)", "tip": "number", "varsayilan": "450", "adim": "1"},
            {"id": "tuketim", "etiket": "Ortalama tüketim (litre/100 km)", "tip": "number", "varsayilan": "7.2", "adim": "any"},
            {"id": "litre", "etiket": "Litre fiyatı (TL)", "tip": "number", "varsayilan": "48", "adim": "any"},
            {"id": "gidisdonus", "etiket": "Gidiş-dönüş", "tip": "secim", "varsayilan": "0",
             "secenekler": [["0", "Tek yön"], ["1", "Gidiş-dönüş"]]},
        ],
        "alan_notu": (
            "Ortalama tüketim aracın kendi bilgisayarından okunabilir; şehir içi "
            "ve şehir dışı değerleri belirgin farklıdır. Katalog tüketimi genelde "
            "gerçek kullanımın altında kalır."
        ),
        "js": """
      const nd = (x) => String(x).replace(".", ",");
      const s = yakitMaliyetiHesapla(sayi("mesafe"), sayi("tuketim"),
                                     sayi("litre"), sayi("gidisdonus") === 1);
      if (!s) return null;
      return [
        ["Yakıt maliyeti", s.tutar, true],
        ["Toplam mesafe", null, false, "not", s.mesafe + " km"],
        ["Harcanan yakıt", null, false, "not", nd(s.litre) + " litre"],
        ["Kilometre başına", s.km_basina, false],
        ["100 km maliyeti", s.yuz_km, false],
      ];""",
        "sss": [
            ("Litre fiyatını neden siz yazmıyorsunuz?",
             "Akaryakıt fiyatı günlük değişiyor ve dağıtıcıya, ile göre farklılaşıyor. "
             "Buraya bir rakam gömseydik ertesi gün yanlış olurdu; ölçemediğimiz ya da "
             "hızla eskiyecek bir parametreyi uydurmak yerine sizden alıyoruz."),
            ("Şehir içi tüketim neden daha yüksek?",
             "Dur-kalk trafiğinde motor sık sık rölantide ve düşük viteste çalışıyor; "
             "aynı mesafe için daha çok yakıt gidiyor. Aracınızın şehir içi ve şehir "
             "dışı ortalamaları genelde ayrı ayrı gösterilir."),
            ("Aracın toplam maliyeti sadece yakıt mı?",
             'Hayır. Etiket fiyatının üzerine MTV, noter, tescil, sigorta ve kasko '
             'biniyor. Bunları <a href="/arac/hesaplayici/">araç sahip olma maliyeti '
             'hesaplayıcısında</a> resmî tarifelerle ayırıyoruz.'),
        ],
    },
    {
        "id": "boya",
        "slug": "boya-hesaplama",
        "ad": "Boya Hesaplama",
        "baslik": "Oda Boyama Maliyeti: Kaç Litre Boya Gerekir?",
        "soru": "Bu odayı boyamak kaç litre boya ve kaç para eder?",
        "meta": "Oda ölçülerine göre boyanacak alan, gereken boya litresi ve "
                "litre fiyatını girerseniz toplam boya maliyeti.",
        "ozet": (
            "Duvar alanı <strong>2 × (en + boy) × yükseklik</strong>. Gereken boya "
            "<strong>alan × kat sayısı ÷ verim</strong> — verim (m²/litre) boya "
            "kutusunun üzerinde yazar ve markaya göre değişir, o yüzden sizden "
            "alıyoruz."
        ),
        "formul": "Litre = (2×(en+boy)×yükseklik + tavan) × kat ÷ verim",
        "kaynaklar": ["Alan hesabı — temel geometri"],
        "alanlar": [
            {"id": "en", "etiket": "Oda eni (m)", "tip": "number", "varsayilan": "4", "adim": "any"},
            {"id": "boy", "etiket": "Oda boyu (m)", "tip": "number", "varsayilan": "5", "adim": "any"},
            {"id": "yuk", "etiket": "Tavan yüksekliği (m)", "tip": "number", "varsayilan": "2.8", "adim": "any"},
            {"id": "kat", "etiket": "Kaç kat boyanacak?", "tip": "number", "varsayilan": "2", "adim": "1"},
            {"id": "verim", "etiket": "Boya verimi (m²/litre) — kutuda yazar", "tip": "number", "varsayilan": "12", "adim": "any"},
            {"id": "fiyat", "etiket": "Litre fiyatı (TL) — boşsa yalnız litre hesaplanır",
             "tip": "number", "varsayilan": "", "adim": "any", "zorunlu": False},
            {"id": "tavan", "etiket": "Tavan da boyanacak mı?", "tip": "secim", "varsayilan": "1",
             "secenekler": [["1", "Evet"], ["0", "Hayır"]]},
        ],
        "alan_notu": (
            "Kapı ve pencere alanı düşülmez. Uydurma bir \"%10 düş\" katsayısı "
            "koymuyoruz; artan boya rötuş için zaten işe yarıyor. İşçilik bu hesaba "
            "dahil değil — onu ölçmüyoruz."
        ),
        "js": """
      const nd = (x) => String(x).replace(".", ",");
      const s = boyaHesapla(sayi("en"), sayi("boy"), sayi("yuk"), sayi("kat"),
                            sayi("verim"), sayi("fiyat"), sayi("tavan") === 1);
      if (!s) return null;
      const satirlar = [];
      if (s.tutar !== null) satirlar.push(["Boya maliyeti", s.tutar, true]);
      satirlar.push(["Gereken boya", null, s.tutar === null, "not", nd(s.litre) + " litre"]);
      satirlar.push(["Duvar alanı", null, false, "not", nd(s.duvar_alani) + " m²"]);
      if (s.tavan_alani > 0) satirlar.push(["Tavan alanı", null, false, "not", nd(s.tavan_alani) + " m²"]);
      satirlar.push(["Toplam boyanacak alan", null, false, "not", nd(s.toplam_alan) + " m²"]);
      return satirlar;""",
        "sss": [
            ("Kaç kat boya gerekir?",
             "Aynı renk üzerine genelde iki kat yeterli. Koyu rengin üzerine açık "
             "renk atılıyorsa üç kat gerekebilir; astar kullanmak kat sayısını düşürür."),
            ("Kapı ve pencereyi neden düşmüyorsunuz?",
             "Düşmek için bir varsayım katsayısı uydurmamız gerekirdi. Artan boya "
             "rötuş için zaten kullanılıyor; eksik kalması, fazla kalmasından kötü."),
            ("İşçilik dahil mi?",
             'Hayır. Boyacı yevmiyesi internette liste halinde yayınlanmıyor ve '
             'ölçemediğimiz bir şeye rakam yazmıyoruz. Bu hesap yalnızca malzeme.'),
        ],
    },
    {
        "id": "basabas",
        "slug": "basa-bas-noktasi-hesaplama",
        "ad": "Başa Baş Noktası Hesaplama",
        "baslik": "Başa Baş Noktası: Kaç Adet Satmam Gerekiyor?",
        "soru": "Sabit giderimi çıkarmak için kaç adet satmalıyım?",
        "meta": "Sabit gider, birim satış fiyatı ve birim değişken maliyete göre "
                "başa baş satış adedi, birim katkı payı ve gereken ciro.",
        "ozet": (
            "Başa baş adet = <strong>sabit gider ÷ birim katkı payı</strong>. "
            "Birim katkı payı, satış fiyatından birim değişken maliyetin "
            "çıkarılmasıyla bulunur — yani her bir satışın sabit gideri karşılamaya "
            "bıraktığı tutar."
        ),
        "formul": "Adet = sabit gider ÷ (birim fiyat − birim değişken maliyet)",
        "kaynaklar": ["Başa baş analizi — temel aritmetik"],
        "alanlar": [
            {"id": "sabit", "etiket": "Aylık sabit gider (TL)", "tip": "number", "varsayilan": "50000", "adim": "1"},
            {"id": "fiyat", "etiket": "Birim satış fiyatı (TL)", "tip": "number", "varsayilan": "120", "adim": "any"},
            {"id": "degisken", "etiket": "Birim değişken maliyet (TL)", "tip": "number", "varsayilan": "45", "adim": "any"},
        ],
        "alan_notu": (
            "Sabit gider: kira, maaş, abonelikler — satış olmasa da ödenen kalemler. "
            "Değişken maliyet: her bir satışla birlikte oluşan maliyet (hammadde, "
            "komisyon, kargo)."
        ),
        "js": """
      const nd = (x) => String(x).replace(".", ",");
      const s = basaBasHesapla(sayi("sabit"), sayi("fiyat"), sayi("degisken"));
      if (!s) return null;
      if (s.mumkun_degil) {
        return [
          ["Başa baş noktası", null, true, "not", "YOK"],
          ["Birim katkı payı", s.katki, false],
          ["Durum", null, false, "not",
           "Satış fiyatı değişken maliyeti karşılamıyor; her satış zararı büyütür."],
          ["Başa baş için gereken en düşük fiyat", s.gereken_fiyat, false],
        ];
      }
      return [
        ["Başa baş satış adedi", null, true, "not", String(s.adet) + " adet"],
        ["Birim katkı payı", s.birim_katki, false],
        ["Katkı oranı", null, false, "not", "%" + nd(s.katki_orani)],
        ["Gereken ciro", s.ciro, false],
      ];""",
        "sss": [
            ("Satış fiyatım değişken maliyetin altındaysa ne olur?",
             "Başa baş noktası <strong>yoktur</strong>. Her satış zararı büyütür; "
             "daha çok satmak durumu kötüleştirir. Bu hesap o durumda uydurma bir "
             "adet vermiyor, açıkça söylüyor ve başa baş için gereken en düşük "
             "fiyatı gösteriyor."),
            ("Katkı oranı ne işe yarar?",
             "Her 100 TL'lik satışın kaç lirasının sabit giderlere kaldığını "
             "gösterir. Oran düştükçe aynı sabit gideri karşılamak için çok daha "
             "fazla satış gerekir."),
            ("KDV bu hesaba dahil mi?",
             'Hayır, tutarları KDV hariç girin. KDV dahil/hariç çevrimi için '
             '<a href="/hesap/kdv-hesaplama/">KDV hesaplayıcısını</a> '
             'kullanabilirsiniz.'),
        ],
    },
    {
        "id": "lot",
        "slug": "lot-hesaplama",
        "ad": "Borsa Lot Hesaplama",
        "baslik": "Borsa Lot Hesaplama: Bütçemle Kaç Lot Alırım?",
        "soru": "Belirli bir bütçeyle kaç lot hisse alabilirim?",
        "meta": "Bütçenize ve hisse fiyatına göre kaç lot alabileceğinizi, "
                "komisyon dahil toplam tutarı ve kalan bakiyeyi hesaplayın.",
        "ozet": (
            "BIST'te <strong>1 lot = 1 adet pay</strong>dır; yani \"kaç lot "
            "alırım\" sorusu \"bütçem kaç paya yeter\" sorusudur. Komisyon alış "
            "tutarı üzerinden alındığı için efektif birim maliyet "
            "<strong>fiyat × (1 + komisyon oranı)</strong> olur ve lot sayısı "
            "buna göre bulunur."
        ),
        "formul": "Lot = ⌊bütçe ÷ (fiyat × (1 + komisyon oranı))⌋",
        # SAF MATEMATIK: hicbir mevzuat parametresi ya da olculmus veri yok.
        # Komisyon oranini KULLANICIDAN aliyoruz - araci kurumlara gore
        # degisiyor ve yayinlanmis TEK bir oran yok; varsayilan gomsek
        # uydurma olurdu.
        "kaynaklar": ["Tam sayıya yuvarlama — temel aritmetik"],
        "alanlar": [
            {"id": "butce", "etiket": "Bütçeniz (TL)", "tip": "number", "varsayilan": "10000", "adim": "1"},
            {"id": "fiyat", "etiket": "Hisse fiyatı (TL)", "tip": "number", "varsayilan": "42.50", "adim": "0.01"},
            {"id": "kom", "etiket": "Aracı kurum komisyonu (%) — bilmiyorsanız boş bırakın",
             "tip": "number", "varsayilan": "", "adim": "any", "zorunlu": False},
        ],
        "alan_notu": (
            "Komisyon oranı aracı kurumunuza göre değişir ve tek bir yayınlanmış "
            "oran yoktur; o yüzden buraya sabit bir değer koymuyoruz. Boş "
            "bırakırsanız komisyonsuz hesaplanır. Bu bir hesap aracıdır, "
            "yatırım tavsiyesi değildir."
        ),
        "js": """
      const s = lotHesapla(sayi("butce"), sayi("fiyat"), sayi("kom"));
      if (!s) return null;
      if (s.yetersiz) {
        return [
          ["Alınabilecek lot", null, true, "not", "0 lot"],
          ["Bir lot için gereken", s.gereken, false],
          ["Bütçeniz", s.butce, false],
          ["Durum", null, false, "not",
           "Bütçe tek bir lota bile yetmiyor."],
        ];
      }
      return [
        ["Alınabilecek lot", null, true, "not", String(s.lot) + " lot"],
        ["Hisse tutarı", s.tutar, false],
        ["Komisyon", s.komisyon, false],
        ["Toplam ödeme", s.toplam, false],
        ["Kalan bakiye", s.kalan, false],
      ];""",
        "sss": [
            ("BIST'te 1 lot kaç adet hisse?",
             "1 lot = 1 adet paydır. Eskiden 1 lot 1.000 adede karşılık geliyordu; "
             "bu birim 2005'te değişti. Yani bugün \"500 lot aldım\" demek "
             "\"500 adet pay aldım\" demektir."),
            ("Küsuratlı lot alınabilir mi?",
             "Hayır, pay adedi tam sayıdır. Bu yüzden hesap aşağı yuvarlar ve "
             "artan tutarı \"kalan bakiye\" olarak gösterir."),
            ("Komisyonu neden siz yazmıyorsunuz?",
             "Aracı kurumların komisyon oranları birbirinden farklı ve tek bir "
             "resmî oran yok. Buraya bir sayı gömseydik çoğu kullanıcı için "
             "yanlış olurdu; ölçemediğimiz bir parametreyi uydurmak yerine "
             "sizden alıyoruz."),
            ("Aldıktan sonra ortalama maliyetim ne olur?",
             "Mevcut pozisyonunuza ekleme yapıyorsanız yeni ortalamayı "
             "<a href=\"/hesap/hisse-maliyet-hesaplama/\">borsa hisse maliyet "
             "hesaplayıcısından</a> görebilirsiniz."),
        ],
    },
    {
        "id": "hisse-maliyet",
        "slug": "hisse-maliyet-hesaplama",
        "ad": "Borsa Hisse Maliyet Hesaplama",
        "baslik": "Borsa Hisse Maliyet Düşürme Hesaplama",
        "soru": "Hisse alınca ortalama maliyetim ne olur, maliyet nasıl düşer?",
        "meta": "Borsada hisse senedi alımında yeni ortalama maliyet, başa baş "
                "fiyat ve maliyet düşürme hesabı. Kaç lot alınca maliyet nereye iner?",
        "ozet": (
            "Borsada mevcut pozisyonunuza ekleme yaptığınızda yeni ortalama "
            "maliyetiniz <strong>toplam tutar ÷ toplam adet</strong> olur. Sonuç "
            "aynı zamanda <strong>başa baş fiyatınızdır</strong> — bu fiyatın "
            "altında satarsanız zarardasınız. BIST'te 1 lot 1 adet paya eşittir, "
            "yani adet ve lot aynı sayıdır."
        ),
        "formul": "Yeni maliyet = (eski adet × eski maliyet + yeni adet × yeni fiyat) ÷ toplam adet",
        "kaynaklar": ["Ağırlıklı ortalama — temel aritmetik"],
        "alanlar": [
            {"id": "madet", "etiket": "Mevcut adet", "tip": "number", "varsayilan": "1000", "adim": "1"},
            {"id": "mmaliyet", "etiket": "Mevcut ortalama maliyet (TL)", "tip": "number", "varsayilan": "50", "adim": "0.01"},
            {"id": "yadet", "etiket": "Alınacak adet", "tip": "number", "varsayilan": "500", "adim": "1"},
            {"id": "yfiyat", "etiket": "Alış fiyatı (TL)", "tip": "number", "varsayilan": "35", "adim": "0.01"},
        ],
        "alan_notu": (
            "Bu bir hesap aracıdır, yatırım tavsiyesi değildir. Maliyet düşürmek "
            "zararı azaltmaz — yalnızca başa baş fiyatını aşağı çeker ve pozisyon "
            "büyüklüğünüzü artırır."
        ),
        "js": """
      const s = hisseMaliyetHesapla(sayi("madet"), sayi("mmaliyet"), sayi("yadet"), sayi("yfiyat"));
      if (!s) return null;
      return [
        ["Yeni ortalama maliyet", s.yeni_maliyet, true],
        ["Toplam adet", null, false, "not", String(s.toplam_adet)],
        ["Toplam yatırılan", s.toplam_tutar, false],
        ["Eski maliyet", s.eski_maliyet, false],
        ["Maliyetteki değişim", s.degisim, false],
      ];""",
        "sss": [
            ("Maliyet düşürmek zararı kapatır mı?",
             "Hayır. Zararınız aynı kalır; sadece başa baş fiyatınız düşer ve pozisyonunuz büyür. Düşmeye devam eden bir varlıkta ekleme yapmak zararı büyütür."),
            ("1000 lot 50 TL maliyete 500 lotu 35 TL'den eklersem ortalamam ne olur?",
             "Toplam tutar 67.500 TL, toplam adet 1.500 olur; yeni ortalama maliyet "
             "45 TL'ye iner. Komisyon dahil değildir."),
            ("Başa baş fiyat nedir?",
             "Yeni ortalama maliyetinizin kendisi. Bu fiyattan satarsanız (komisyon hariç) ne kâr ne zarar edersiniz."),
            ("Komisyon hesaba dahil mi?",
             "Bu hesapta değil. Komisyonlu kâr/zarar için kâr-zarar hesaplayıcısını kullanın."),
        ],
    },
    {
        "id": "kar-zarar",
        "slug": "kar-zarar-hesaplama",
        "ad": "Kâr Zarar Hesaplama",
        "baslik": "Alış Satış Kâr Zarar Hesaplama",
        "soru": "Bu alım satımdan ne kadar kâr ettim?",
        "meta": "Alış ve satış fiyatına göre kâr/zarar, yüzde getiri ve komisyon dahil başa baş fiyat.",
        "ozet": (
            "Kâr, satış hasılatından alış maliyetinin çıkarılmasıyla bulunur; "
            "komisyon <strong>iki tarafta da</strong> ödendiği için başa baş "
            "fiyat alış fiyatının biraz üzerindedir."
        ),
        "formul": "Kâr = satış×adet×(1−k) − alış×adet×(1+k) &nbsp;·&nbsp; Başa baş = alış×(1+k) ÷ (1−k)",
        "kaynaklar": ["Kâr/zarar ve yüzde getiri — temel aritmetik"],
        "alanlar": [
            {"id": "alis", "etiket": "Alış fiyatı (TL)", "tip": "number", "varsayilan": "50", "adim": "0.01"},
            {"id": "satis", "etiket": "Satış fiyatı (TL)", "tip": "number", "varsayilan": "65", "adim": "0.01"},
            {"id": "adet", "etiket": "Adet", "tip": "number", "varsayilan": "1000", "adim": "1"},
            {"id": "komisyon", "etiket": "Komisyon oranı (%)", "tip": "number", "varsayilan": "0.2", "adim": "0.01"},
        ],
        "js": """
      const s = karZararHesapla(sayi("alis"), sayi("satis"), sayi("adet"), sayi("komisyon"));
      if (!s) return null;
      return [
        ["Kâr / zarar", s.kar_zarar, true],
        ["Getiri", null, false, "not", "%" + s.getiri_yuzde],
        ["Alış maliyeti (komisyon dahil)", s.alis_maliyeti, false],
        ["Satış neti (komisyon düşülmüş)", s.satis_neti, false],
        ["Ödenen komisyon", s.komisyon, false],
        ["Başa baş satış fiyatı", s.basa_bas_fiyat, false],
      ];""",
        "sss": [
            ("Başa baş fiyat neden alış fiyatından yüksek?",
             "Komisyonu hem alırken hem satarken ödersiniz. Alış fiyatına eşit satmak, iki komisyon kadar zarar demektir."),
            ("Yüzde getiri neye göre hesaplanıyor?",
             "Komisyon dahil alış maliyetine göre. Ham alış fiyatına bölmek getiriyi olduğundan yüksek gösterir."),
            ("Vergi dahil mi?",
             "Hayır. Hisse senedinde stopaj ve beyan kuralları araca ve elde tutma süresine göre değişir; bu hesap yalnızca alım satım sonucunu verir."),
        ],
    },
    {
        "id": "temettu",
        "slug": "temettu-verimi-hesaplama",
        "ad": "Temettü Verimi ve Geliri Hesaplama",
        "baslik": "Temettü Geliri ve Verimi Hesaplama",
        "soru": "Temettü geliri ve verimi nasıl hesaplanır, formülü nedir?",
        "meta": "Hisse başına temettüye göre yıllık temettü geliri, temettü verimi "
                "(kâr payı oranı) ve geri dönüş süresi. Formülüyle birlikte.",
        "ozet": (
            "Temettü verimi = <strong>hisse başına temettü ÷ hisse fiyatı</strong>. "
            "Yüksek verim her zaman iyi haber değildir: fiyat düştüğü için de "
            "yükselmiş olabilir."
        ),
        "formul": "Verim (%) = (hisse başına temettü ÷ hisse fiyatı) × 100",
        "kaynaklar": ["Temettü verimi tanımı — temel aritmetik"],
        "alanlar": [
            {"id": "fiyat", "etiket": "Hisse fiyatı (TL)", "tip": "number", "varsayilan": "50", "adim": "0.01"},
            {"id": "temettu", "etiket": "Hisse başına yıllık temettü (TL)", "tip": "number", "varsayilan": "4", "adim": "0.01"},
            {"id": "adet", "etiket": "Adet", "tip": "number", "varsayilan": "1000", "adim": "1"},
        ],
        "alan_notu": (
            "Temettü şirketin kararına bağlıdır; geçmişte ödenmiş olması gelecekte "
            "ödeneceğini göstermez. Ayrıca temettüde stopaj kesintisi vardır, bu "
            "hesap brüt tutarı verir."
        ),
        "js": """
      const s = temettuVerimiHesapla(sayi("fiyat"), sayi("temettu"), sayi("adet"));
      if (!s) return null;
      return [
        ["Temettü verimi", null, true, "not", "%" + s.verim_yuzde],
        ["Yıllık temettü geliri (brüt)", s.yillik_temettu, false],
        ["Yatırım tutarı", s.yatirim, false],
        ["Yatırımın temettüyle geri dönüşü", null, false, "not", s.geri_donus_yili + " yıl"],
      ];""",
        "sss": [
            ("50 TL'lik hisse 4 TL temettü verirse temettü verimi kaçtır?",
             "Temettü verimi %8'dir: 4 ÷ 50 × 100. 1.000 pay için brüt yıllık "
             "temettü 4.000 TL olur; stopaj sonrası net tutar bu hesapta gösterilmez."),
            ("Yüksek temettü verimi iyi midir?",
             "Her zaman değil. Verim bir orandır: payda olan hisse fiyatı düştüğünde de yükselir. Şirketin kârı azalırken verimin artması uyarı işareti olabilir."),
            ("Temettüden vergi kesilir mi?",
             "Evet, temettü ödemesinde stopaj yapılır ve tutara göre beyan yükümlülüğü doğabilir. Bu hesap brüt temettüyü gösterir."),
            ("Geri dönüş süresi ne anlama geliyor?",
             "Fiyat ve temettü sabit kalsaydı, yatırdığınız paranın yalnızca temettüyle geri gelmesi kaç yıl sürerdi. İkisi de sabit kalmadığı için bu bir karşılaştırma ölçüsüdür, tahmin değil."),
        ],
    },
    {
        "id": "kart-borcu",
        "slug": "kredi-karti-borcu-hesaplama",
        "ad": "Kredi Kartı Borcu Hesaplama",
        "baslik": "Kredi Kartı Borcu Kaç Ayda Biter?",
        "soru": "Kredi kartı borcum bu ödemeyle kaç ayda biter?",
        "meta": "Borç, aylık faiz ve ödeme tutarına göre borcun kaç ayda biteceği ve toplam ödenecek faiz. Asgari ödeme tuzağı.",
        "ozet": (
            "Aylık ödemeniz o ayın faizinden düşükse <strong>borç hiç bitmez</strong> "
            "— her ay ödediğiniz para faize gider, anapara aynı kalır. Bu hesap "
            "önce onu kontrol eder, sonra süreyi verir."
        ),
        "formul": "Her ay: kalan = kalan + kalan×faiz − ödeme &nbsp;(ödeme ≤ kalan×faiz ise borç azalmaz)",
        "kaynaklar": ["Bileşik faizli borç itfası — finansal matematik"],
        "alanlar": [
            {"id": "borc", "etiket": "Toplam borç (TL)", "tip": "number", "varsayilan": "50000", "adim": "0.01"},
            {"id": "faiz", "etiket": "Aylık akdi faiz oranı (%)", "tip": "number", "varsayilan": "4", "adim": "0.01"},
            {"id": "odeme", "etiket": "Aylık ödeyeceğiniz tutar (TL)", "tip": "number", "varsayilan": "5000", "adim": "0.01"},
        ],
        "alan_notu": (
            "Kredi kartı faiz oranları TCMB tarafından azami sınırla belirlenir ve "
            "dönem dönem değişir; kendi kartınızın güncel oranını ekstrenizden "
            "girin. Gecikme faizi ve kart aidatı bu hesaba dahil değildir."
        ),
        "js": """
      const s = kartBorcuHesapla(sayi("borc"), sayi("faiz"), sayi("odeme"));
      if (!s) return null;
      if (s.bitmez) {
        return [
          ["Bu ödemeyle borç BİTMEZ", null, true, "not", "aylık ödeme faizi karşılamıyor"],
          ["Ayda işleyen faiz", s.aylik_faiz_tutari, false],
          ["Sizin ödemeniz", s.aylik_odeme, false],
          ["Borcun azalmaya başlaması için en az", s.gereken_asgari, false],
        ];
      }
      return [
        ["Borç bitiş süresi", null, true, "not", s.ay + " ay"],
        ["Toplam ödeyeceğiniz", s.toplam_odeme, false],
        ["Bunun faiz kısmı", s.toplam_faiz, false],
        ["Anapara", s.anapara, false],
      ];""",
        "sss": [
            ("Asgari ödeme yaparsam borç ne olur?",
             "Asgari ödeme genellikle işleyen faizi ancak karşılar. Bu durumda anapara neredeyse hiç azalmaz ve borç yıllarca sürebilir. Hesaplayıcı bu durumu ayrıca uyarır."),
            ("Toplam faiz neden bu kadar yüksek çıkıyor?",
             "Kredi kartında faiz her ay kalan borç üzerinden yeniden işler. Süre uzadıkça ödediğiniz toplam faiz anaparayı geçebilir."),
            ("Borcu kredi ile kapatmak mantıklı mı?",
             "İhtiyaç kredisinin aylık faizi kart faizinden düşükse toplam maliyet azalır. İki senaryoyu karşılaştırmak için kredi taksit hesaplayıcısını kullanabilirsiniz."),
        ],
    },
    {
        "id": "freelancer",
        "slug": "serbest-meslek-vergi-hesaplama",
        "ad": "Serbest Meslek Vergi Hesaplama",
        "baslik": "Freelancer Vergi Hesaplama (2026)",
        "soru": "Freelancer olarak ne kadar vergi öderim?",
        "meta": "Serbest meslek kazancında stopaj, KDV ve gelir vergisi. 2026 genç girişimci istisnası 400.000 TL dahil.",
        "ozet": (
            "Serbest meslek makbuzunda <strong>%20 stopaj</strong> kesilir ve "
            "<strong>%20 KDV</strong> eklenir. Yıllık beyanda kazancınızdan giderler "
            "düşülür, varsa <strong>genç girişimci istisnası (2026: 400.000 TL)</strong> "
            "uygulanır; yıl içinde kesilen stopaj hesaplanan vergiden <strong>mahsup "
            "edilir</strong> — çoğu hesaplayıcının atladığı kısım budur ve iade "
            "doğurabilir."
        ),
        "formul": "Matrah = hasılat − gider − istisna &nbsp;·&nbsp; Ödenecek = tarife(matrah) − yıl içinde kesilen stopaj",
        "kaynaklar": [
            "193 sayılı Gelir Vergisi Kanunu md. 94 (serbest meslek stopajı)",
            "193 sayılı GVK mükerrer md. 20 — genç girişimci kazanç istisnası",
            "332 Seri No.lu Gelir Vergisi Genel Tebliği — 2026 istisna tutarı 400.000 TL",
            "3065 sayılı KDV Kanunu",
        ],
        "alanlar": [
            {"id": "hasilat", "etiket": "Yıllık brüt hasılat (TL)", "tip": "number", "varsayilan": "600000", "adim": "0.01"},
            {"id": "gider", "etiket": "Belgelendirilen yıllık gider (TL)", "tip": "number", "varsayilan": "100000", "adim": "0.01"},
            {"id": "genc", "etiket": "Genç girişimci istisnasından yararlanıyor musunuz?", "tip": "select",
             "secenekler": [("hayir", "Hayır"), ("evet", "Evet (29 yaş altı, ilk 3 dönem)")]},
        ],
        "alan_notu": (
            "Genç girişimci istisnası, faaliyete başlanan dönemden itibaren üç "
            "vergilendirme dönemi ve 29 yaşını doldurmamış olmak şartıyla "
            "uygulanır. Bu hesap yıllık beyanı modellemektedir; geçici vergi, "
            "Bağ-Kur primi ve KDV beyanı ayrıca yürütülür."
        ),
        "js": """
      const s = serbestMeslekVergiHesapla(sayi("hasilat"), sayi("gider"), deger("genc") === "evet");
      if (!s) return null;
      const satirlar = [
        ["Brüt hasılat", s.brut_hasilat, false],
        ["Müşteriden tahsil edilen KDV (%20)", s.kdv, false, "not"],
        ["Yıl içinde kesilen stopaj (%20)", s.stopaj, false],
        ["Belgelendirilen gider", -s.gider, false],
        ["Kazanç", s.kazanc, false],
      ];
      if (s.istisna > 0) satirlar.push(["Genç girişimci istisnası", -s.istisna, false]);
      satirlar.push(["Vergi matrahı", s.matrah, false]);
      satirlar.push(["Hesaplanan gelir vergisi", s.hesaplanan_vergi, false]);
      if (s.iade > 0) {
        satirlar.push(["Stopaj mahsubu sonrası İADE", s.iade, true]);
      } else {
        satirlar.push(["Ödenecek gelir vergisi", s.odenecek_vergi, true]);
      }
      return satirlar;""",
        "sss": [
            ("Freelancer olarak hangi vergileri öderim?",
             "Serbest meslek kazancınız gelir vergisine tabidir. Kuruma fatura kesiyorsanız ödemede %20 stopaj kesilir ve bu yıllık beyanda mahsup edilir. Ayrıca %20 KDV hesaplar ve beyan edersiniz — KDV sizin geliriniz değildir, müşteriden tahsil edip devlete aktarırsınız."),
            ("2026 genç girişimci istisnası ne kadar?",
             "400.000 TL. Faaliyete başlanan dönemden itibaren üç vergilendirme dönemi boyunca, 29 yaşını doldurmamış olmak şartıyla uygulanır. Kazancınızın bu tutara kadar olan kısmı gelir vergisinden istisnadır."),
            ("Kesilen stopajı geri alabilir miyim?",
             "Hesaplanan gelir verginiz kesilen stopajdan düşükse aradaki fark size iade edilir. Genç girişimci istisnasından yararlanan freelancer'larda bu sık görülür — hesaplayıcı bu durumu ayrıca gösterir."),
            ("Hangi giderleri düşebilirim?",
             "Faaliyetle doğrudan ilgili ve belgelendirilen giderler: işyeri kirası, internet, bilgisayar amortismanı, mesleki yazılım abonelikleri, ulaşım. Belgesiz gider düşülemez."),
        ],
    },
    {
        "id": "website",
        "slug": "web-sitesi-gelir-hesaplama",
        "ad": "Web Sitesi Gelir Hesaplama",
        "baslik": "Web Sitesi Ne Kadar Kazandırır?",
        "soru": "Web sitesi reklamdan aylık ne kadar kazandırır?",
        "meta": "Sayfa görüntülenmesi ve RPM'e göre web sitesi reklam geliri. Tek bir uydurma rakam değil, RPM'e göre aralık.",
        "ozet": (
            "Formül basit: <strong>(sayfa görüntülenme ÷ 1000) × RPM</strong>. "
            "Ama sonucu belirleyen RPM ve <strong>RPM'in yayınlanmış bir değeri "
            "yok</strong> — konuya, ziyaretçinin ülkesine ve reklam sezonuna göre "
            "kat kat değişir. Tek rakam vermiyoruz; kendi RPM'inizi girin ya da "
            "tablodan okuyun."
        ),
        "formul": "Aylık gelir = (aylık sayfa görüntülenme ÷ 1000) × RPM × kur",
        "kaynaklar": [
            "Hesap saf aritmetiktir. RPM değeri kullanıcıdan alınır — resmî bir "
            "kaynağı olmadığı için tarafımızdan varsayılmaz.",
        ],
        "alanlar": [
            {"id": "izlenme", "etiket": "Aylık sayfa görüntülenme", "tip": "number",
             "varsayilan": "100000", "adim": "1"},
            {"id": "rpm", "etiket": "RPM (1000 gösterim başına gelir, boş bırakabilirsiniz)",
             "tip": "number", "varsayilan": "", "adim": "0.01", "zorunlu": False},
            {"id": "kur", "etiket": "Kur (RPM dolarsa güncel USD/TRY, TL ise 1)",
             "tip": "number", "varsayilan": "1", "adim": "0.01"},
        ],
        "alan_notu": (
            "RPM'inizi AdSense panelinden görebilirsiniz. Bu hesap yalnızca "
            "görüntüleme bazlı reklam gelirini modeller; affiliate, sponsorlu "
            "içerik ve doğrudan reklam satışı dahil değildir."
        ),
        "js": """
      const s = icerikGeliriHesapla(sayi("izlenme"), sayi("rpm"), sayi("kur"));
      if (!s) return null;
      const satirlar = [];
      if (s.secilen_rpm) {
        satirlar.push(["Girdiğiniz RPM ile aylık", s.secilen_aylik, true]);
        satirlar.push(["Yıllık", s.secilen_yillik, false]);
        satirlar.push(["RPM bilinmiyorsa cevap bir aralıktır:", null, false, "not"]);
      } else {
        satirlar.push(["RPM girmediniz — cevap tek sayı değil, aralık:", null, false, "not"]);
      }
      s.duyarlilik.forEach(function (d) {
        satirlar.push(["RPM " + d.rpm + " ise aylık", d.aylik, false]);
      });
      return satirlar;""",
        "sss": [
            ("Neden tek bir rakam vermiyorsunuz?",
             "Çünkü veremeyiz. Gelirin tamamı RPM'e bağlı ve RPM'in resmî, yayınlanmış bir değeri yok; finans ve sigorta gibi konularda yüksek, genel içerikte düşüktür. Tek sayı vermek uydurma olurdu."),
            ("RPM ile CPM farkı ne?",
             "CPM reklamverenin 1000 gösterim için ödediği tutar; RPM ise yayıncı payı düşüldükten sonra size kalan tutardır. Kazancınızı belirleyen RPM'dir."),
            ("Trafik iki katına çıkarsa gelir de iki katına çıkar mı?",
             "Yaklaşık olarak, RPM sabit kalırsa. Ancak trafiğin geldiği ülke ve konu değişirse RPM de değişir; sırf trafik büyüdü diye gelir orantılı büyümeyebilir."),
        ],
    },
    {
        "id": "kredi",
        "slug": "kredi-taksit-hesaplama",
        "ad": "Kredi Taksit Hesaplama",
        "baslik": "Kredi Taksit Hesaplama (Annüite)",
        "soru": "Kredi taksiti nasıl hesaplanır?",
        "meta": "Anapara, aylık faiz ve vadeye göre eşit taksitli kredi ödemesi, toplam geri ödeme ve toplam faiz.",
        "ozet": (
            "Eşit taksitli (annüite) kredide her ay aynı tutar ödenir. Taksit, "
            "anapara ve aylık faiz oranından <strong>annüite formülüyle</strong> "
            "bulunur. Bu hesap saf matematiktir; vergi ve masraflar dahil değildir."
        ),
        "formul": "Taksit = A × i × (1 + i)ⁿ ÷ ((1 + i)ⁿ − 1) &nbsp;— A: anapara, i: aylık faiz, n: vade",
        "kaynaklar": ["Annüite (eşit taksitli ödeme) formülü — finansal matematik"],
        "alanlar": [
            {"id": "anapara", "etiket": "Kredi tutarı (TL)", "tip": "number", "varsayilan": "500000", "adim": "1"},
            {"id": "faiz", "etiket": "Aylık faiz oranı (%)", "tip": "number", "varsayilan": "3.5", "adim": "0.01"},
            {"id": "vade", "etiket": "Vade (ay)", "tip": "number", "varsayilan": "36", "adim": "1"},
        ],
        "alan_notu": (
            "Bu hesap yalnızca faizi içerir. Tüketici kredilerinde ayrıca KKDF ve BSMV "
            "alınır, bankalar dosya/tahsis ücreti uygulayabilir — oranlar kredi türüne "
            "göre değiştiği için tek bir doğru değer yazamıyoruz. Bankanın vereceği "
            "toplam geri ödeme bu rakamın üzerinde olur."
        ),
        "js": """
      const s = krediTaksitHesapla(sayi("anapara"), sayi("faiz"), sayi("vade"));
      if (!s) return null;
      return [
        ["Aylık taksit", s.taksit, true],
        ["Toplam geri ödeme", s.toplam_odeme, false],
        ["Toplam faiz", s.toplam_faiz, false],
        ["Anapara", s.anapara, false],
      ];""",
        "sss": [
            ("Aylık faiz oranından yıllık orana nasıl geçilir?",
             "Bileşik olarak: yıllık = (1 + aylık)¹² − 1. Aylık %3,5 faiz, yıllık yaklaşık %51 maliyete karşılık gelir — basitçe 12 ile çarpmak (%42) gerçek maliyeti olduğundan düşük gösterir."),
            ("Vade uzayınca taksit düşüyor, o zaman uzun vade daha mı iyi?",
             "Taksit düşer ama toplam faiz artar. 500.000 TL'yi 36 ay yerine 60 ayda ödemek aylık yükü hafifletir, toplamda ödediğiniz parayı büyütür. Hesaplayıcıda iki vadeyi karşılaştırarak farkı görebilirsiniz."),
            ("Bu hesap bankanın verdiği rakamla neden farklı?",
             "Bu hesap yalnızca faizi içerir. Tüketici kredilerinde KKDF ve BSMV, ayrıca dosya masrafı eklenir. Bankanın \"toplam geri ödeme\" tutarı bu yüzden daha yüksek çıkar."),
        ],
    },
    {
        "id": "yuzde",
        "slug": "yuzde-hesaplama",
        "ad": "Yüzde Hesaplama",
        "baslik": "Yüzde Hesaplama: Zam, İndirim ve Değişim",
        "soru": "Yüzde zam, indirim ve değişim nasıl hesaplanır?",
        "meta": "Zam, indirim, iki tutar arasındaki yüzde değişim ve oran hesabı. Dört yaygın yüzde işlemi tek sayfada.",
        "ozet": (
            "Zam için tutarı <strong>(1 + oran)</strong> ile, indirim için "
            "<strong>(1 − oran)</strong> ile çarparsınız. İki tutar arasındaki "
            "değişim <strong>(yeni − eski) ÷ eski × 100</strong> ile bulunur."
        ),
        "formul": "Zamlı = T × (1 + %) &nbsp;·&nbsp; İndirimli = T × (1 − %) &nbsp;·&nbsp; Değişim = (yeni − eski) ÷ eski × 100",
        "kaynaklar": ["Yüzde hesabı — temel aritmetik"],
        "alanlar": [
            {"id": "tur", "etiket": "İşlem", "tip": "select",
             "secenekler": [("zam", "Zam: tutara %X ekle"), ("indirim", "İndirim: tutardan %X çıkar"),
                            ("degisim", "Değişim: iki tutar arasındaki yüzde"),
                            ("oran", "Oran: A, B'nin yüzde kaçı?")]},
            {"id": "a", "etiket": "Birinci değer", "tip": "number", "varsayilan": "1000", "adim": "0.01"},
            {"id": "b", "etiket": "İkinci değer (oran ya da tutar)", "tip": "number", "varsayilan": "25", "adim": "0.01"},
        ],
        "js": """
      const tur = deger("tur");
      const s = yuzdeHesapla(tur, sayi("a"), sayi("b"));
      if (!s) return null;
      if (tur === "degisim") {
        return [["Yüzde değişim", null, true, "not", (s.sonuc > 0 ? "+" : "") + s.sonuc + "%"],
                ["Tutar farkı", s.fark, false]];
      }
      if (tur === "oran") {
        return [["Oran", null, true, "not", s.sonuc + "%"]];
      }
      return [["Sonuç", s.sonuc, true], [tur === "zam" ? "Eklenen" : "Düşülen", s.fark, false]];""",
        "sss": [
            ("%20 zam sonrası %20 indirim, başlangıç tutarını vermez mi?",
             "Vermez. 1.000 TL'ye %20 zam 1.200 TL, ardından %20 indirim 960 TL yapar. İndirim daha büyük bir tutar üzerinden hesaplandığı için sonuç 40 TL düşük çıkar."),
            ("Enflasyon %30 ise maaşıma %30 zam alınca alım gücüm korunur mu?",
             "Ancak zam enflasyonla aynı anda gelirse. Zam yılın sonunda gelirse yıl boyunca eski maaşla daha pahalı fiyatlara alışveriş yapmış olursunuz; kayıp geriye dönük telafi edilmez."),
            ("İki tutar arasındaki yüzde değişim hangi tutara bölünür?",
             "Her zaman ESKİ tutara. 1.000 TL'den 1.250 TL'ye çıkış %25 artıştır; yeni tutara bölmek (%20) yanlış sonuç verir."),
        ],
    },
]


# ----------------------------------------------------------
# ALIM GUCU HESABI - digerlerinden FARKLI
#
# Parametresi sabit bir mevzuat degeri degil, bizim ayda iki kez
# cektigimiz RESMI TUFE SERISI (TCMB EVDS). Rakiplerin hicbirinde bu
# hesap yok cunku hicbiri resmi endeksi cekmiyor.
#
# VERI YOKSA SAYFA URETILMEZ (rehber.py ile ayni kural): EVDS anahtari
# tanimli degilse enflasyon.json olusmaz; o durumda uydurma endeksle
# sayfa acmak yerine hic acmiyoruz.
# ----------------------------------------------------------
def _tufe_serisi(veri_kok: Path | None = None) -> dict | None:
    dosya = (veri_kok or SITE_KOK / "veri") / "enflasyon.json"
    if not dosya.exists():
        return None
    try:
        veri = json.loads(dosya.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    genel = next((g for g in (veri.get("gruplar") or {}).values()
                  if g.get("vertikal") is None and g.get("seri")), None)
    if not genel or len(genel.get("seri") or []) < 2:
        return None
    return {
        "ad": genel["ad"],
        "seri": [{"tarih": n["tarih"], "endeks": n["endeks"]} for n in genel["seri"]],
        "kaynak": veri.get("kaynak") or "TCMB EVDS — TÜİK Tüketici Fiyat Endeksi",
    }


def alim_gucu_tanimi(veri_kok: Path | None = None) -> dict | None:
    t = _tufe_serisi(veri_kok)
    if not t:
        return None
    ilk, son = t["seri"][0], t["seri"][-1]
    degisim = (son["endeks"] / ilk["endeks"] - 1) * 100
    aylar = [n["tarih"] for n in t["seri"]]
    return {
        "id": "alim-gucu",
        "slug": "alim-gucu-hesaplama",
        "ad": "Alım Gücü Hesaplama",
        "baslik": "Paranızın Alım Gücü Ne Kadar Eridi?",
        "soru": "Geçmişteki bir tutar bugün ne kadara denk geliyor?",
        "meta": (
            f"Resmî TÜFE ile alım gücü hesabı. {ilk['tarih']} — {son['tarih']} "
            f"arasında genel enflasyon %{degisim:.1f}. Kaynak: TCMB EVDS."
        ),
        "ozet": (
            f"<strong>{ilk['tarih']}</strong> ile <strong>{son['tarih']}</strong> "
            f"arasında resmî tüketici fiyat endeksi <strong>%{degisim:.1f}</strong> "
            "arttı. Bu hesap, geçmişteki bir tutarın bugün kaç liraya denk geldiğini "
            "ve alım gücünün ne kadar eridiğini gösterir."
        ),
        "formul": "Bugünkü karşılık = tutar × (son endeks ÷ ilk endeks)",
        "kaynaklar": [
            "TCMB EVDS — TÜİK Tüketici Fiyat Endeksi (2025=100), seri TP.FE25.OKTG01",
            f"Kullanılan seri: {aylar[0]} – {aylar[-1]}, ayda iki kez güncelleniyor",
        ],
        "alanlar": [
            {"id": "tutar", "etiket": "Tutar (TL)", "tip": "number",
             "varsayilan": "50000", "adim": "0.01"},
            {"id": "ilk", "etiket": "Hangi tarihteki tutar?", "tip": "select",
             "secenekler": [(n["tarih"], n["tarih"]) for n in t["seri"]]},
            {"id": "son", "etiket": "Hangi tarihe göre?", "tip": "select",
             "secenekler": [(n["tarih"], n["tarih"]) for n in reversed(t["seri"])]},
        ],
        "alan_notu": (
            "TÜFE bir ENDEKS'tir, TL cinsinden fiyat değil — sepetin ortalama "
            "değişimini ölçer. Sizin harcama sepetiniz farklıysa hissettiğiniz "
            "enflasyon bu rakamdan sapabilir. Sitedeki ölçülmüş fiyat endeksleri "
            "ise gerçek TL tutarları izler; ikisi ayrı şeydir."
        ),
        "js": """
      const seri = TUFE_SERISI;
      const bul = (t) => (seri.find((x) => x.tarih === t) || {}).endeks;
      const s = alimGucuHesapla(sayi("tutar"), bul(deger("ilk")), bul(deger("son")));
      if (!s) return null;
      return [
        [deger("ilk") + " tarihindeki tutar", s.tutar, false],
        [deger("son") + " tarihindeki karşılığı", s.bugunku_karsilik, true],
        ["Aradaki fark", s.fark, false],
        ["Bu dönemde enflasyon", null, false, "not", "%" + s.enflasyon_yuzde],
        ["Aynı parayla alım gücü kaybı", null, false, "not", "%" + s.erime_yuzde],
      ];""",
        "sss": [
            ("TÜFE ile kendi hissettiğim enflasyon neden farklı?",
             "TÜFE, hane halkının ortalama harcama sepetini ölçer. Sizin sepetiniz "
             "farklıysa — kira ağırlıklıysa, çocuğunuz varsa, araç kullanıyorsanız — "
             "hissettiğiniz oran resmî ortalamadan sapar. Bu yüzden bu sitede ayrıca "
             "düğün, ev kurma, okul, bebek gibi somut sepetlerin TL fiyatını ölçüyoruz."),
            ("Bu rakam nereden geliyor?",
             "TCMB'nin EVDS sisteminden çekilen TÜİK Tüketici Fiyat Endeksi (2025=100). "
             "Seriyi ayda iki kez tazeliyoruz; hesapta kullanılan dönem sayfada yazılı."),
            ("Maaşıma enflasyon kadar zam alırsam alım gücüm korunur mu?",
             "Tam olarak değil. Zam yıl sonunda gelirse yıl boyunca eski maaşla daha "
             "pahalı fiyatlara alışveriş yapmış olursunuz; o kayıp geriye dönük "
             "telafi edilmez. Ayrıca zam brütten verilir, artan oranlı vergi nedeniyle "
             "nete yansıması daha düşük olur."),
        ],
        "_tufe": t,
    }


def _butce_kalemleri(veri_kok: Path | None = None) -> list[dict]:
    """Olculmus kalemleri butce karar aracina hazirlar.

    Burada yeni fiyat URETILMEZ. Arac yalnizca yayinlanan ekonomik, orta
    ve ust segment ortancalarini kullanir. Uc bandi da olmayan ya da
    tahmini olan kalem listeye girmez; eksik veriden karar cikarmak,
    kullaniciya guvenilir gorunen ama dayanak olmayan bir cevap verirdi.
    """
    kok = veri_kok or SITE_KOK / "veri"
    satirlar = []
    for vertikal, conf in su.VERTIKALLER.items():
        dosya = kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        try:
            veri_seti = json.loads(dosya.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        tarih = veri_seti.get("guncelleme_tarihi") or "—"
        kalemler = veri_seti.get("kalemler") or {}
        for tanim in conf["kalemler"]:
            veri = kalemler.get(tanim["id"]) or {}
            if veri.get("kaynak_tipi") == "tahmini":
                continue
            # Ayni kalemde birden cok acik urun tipi varsa tek fiyat bandi
            # kullanicinin sectigi seyi temsil etmez. Ornek: firin-ocak
            # havuzunda ankastre firin, ocakli firin ve set birlikteyse
            # "butcem yeter mi" karari verilmez; tip bazli sayfa kullanilir.
            turler = (veri.get("ozellik_ozeti") or {}).get("urun_turleri") or {}
            guclu_turler = [o for o in turler.values() if o.get("urun_sayisi", 0) >= 3]
            if len(guclu_turler) > 1:
                continue
            degerler = su.segment_degerleri(veri)
            if not all(degerler.get(k) for k in ("dusuk", "orta", "luks")):
                continue
            if tanim.get("birim") == "kisi_basi":
                birim = "kişi başı"
            elif tanim.get("olcum_turu") == "paket_fiyati":
                birim = "paket"
            else:
                birim = "adet"
            kaynak_sayisi = len(
                su.bagimsiz_siteler({tanim["id"]: veri}, {tanim["id"]})
            ) or veri.get("kaynak_sayisi", 0)
            satirlar.append({
                "anahtar": f"{vertikal}:{tanim['id']}",
                "kategori": conf["ad"],
                "ad": su._kisa_kalem_adi(tanim["ad"]),
                "birim": birim,
                "dusuk": degerler["dusuk"],
                "orta": degerler["orta"],
                "luks": degerler["luks"],
                "tarih": tarih,
                "kaynak": kaynak_sayisi,
                "urun": veri.get("toplam_urun") or 0,
                "yol": f"/{conf['yol']}/",
            })
    return satirlar


def butcem_yeter_mi_tanimi(veri_kok: Path | None = None) -> dict | None:
    """Dogal AI sorgusunu urune cevirir: "X butceyle Y alinir mi?"""
    kalemler = _butce_kalemleri(veri_kok)
    if not kalemler:
        return None
    varsayilan = next(
        (k["anahtar"] for k in kalemler if k["anahtar"] == "ev-kurma:firin-ocak"),
        kalemler[0]["anahtar"],
    )
    kaynaklar = []
    for kategori in dict.fromkeys(k["kategori"] for k in kalemler):
        tarih = next(k["tarih"] for k in kalemler if k["kategori"] == kategori)
        kaynaklar.append(
            f"Maliyeti Ne? {kategori} veri seti — ölçüm tarihi {tarih}"
        )
    return {
        "id": "butcem-yeter-mi",
        "slug": "butcem-yeter-mi",
        "ad": "Bütçem Yeter mi?",
        "baslik": "Bütçem Bu Ürüne Yeter mi?",
        "soru": "Ayırdığım bütçe seçtiğim ürün için yeterli mi?",
        "meta": (
            f"{len(kalemler)} ölçülmüş kalemde bütçenizin ekonomik, orta veya "
            "üst fiyat bandına yetip yetmediğini güncel verilerle kontrol edin."
        ),
        "ozet": (
            f"<strong>{len(kalemler)} ölçülmüş kalemden</strong> birini ve bütçenizi "
            "seçin. Araç, bütçeyi güncel ekonomik, orta ve üst fiyat bandıyla "
            "karşılaştırır; marka ya da özellik uydurmadan hangi seviyeye "
            "ulaştığınızı söyler."
        ),
        "formul": (
            "Bütçe &lt; ekonomik → yetersiz &nbsp;·&nbsp; ekonomik ≤ bütçe &lt; orta → "
            "ekonomik banda yeter &nbsp;·&nbsp; orta ≤ bütçe &lt; üst → orta banda yeter"
        ),
        "kaynaklar": kaynaklar,
        "alanlar": [
            {
                "id": "kalem", "etiket": "Ne almak istiyorsunuz?", "tip": "select",
                "varsayilan": varsayilan,
                "secenekler": [
                    (k["anahtar"], f"{k['kategori']} — {k['ad']} ({k['birim']})")
                    for k in kalemler
                ],
            },
            {"id": "butce", "etiket": "Ayırdığınız bütçe (TL)", "tip": "number",
             "varsayilan": "50000", "adim": "1"},
        ],
        "alan_notu": (
            "Sonuç bir ürün önerisi değil, fiyat bandı kontrolüdür. Kategori "
            "sayfalarındaki ürün karması marka, kapasite ve özelliğe göre değişir; "
            "özellik uygunluğu ayrıca doğrulanmalıdır."
        ),
        "js": """
      const k = BUTCE_KALEMLERI.find((x) => x.anahtar === deger("kalem"));
      const butce = sayi("butce");
      if (!k || butce <= 0) return null;
      let karar, hedef, fark;
      if (butce < k.dusuk) {
        hedef = k.dusuk;
        fark = k.dusuk - butce;
        karar = "Ekonomik fiyat bandının altında; ekonomik bandın ortasına " + para(fark) + " eksik.";
      } else if (butce < k.orta) {
        hedef = k.orta;
        fark = k.orta - butce;
        karar = "Ekonomik banda yeter; orta bandın ortasına " + para(fark) + " eksik.";
      } else if (butce < k.luks) {
        hedef = k.luks;
        fark = k.luks - butce;
        karar = "Orta banda yeter; üst bandın ortasına " + para(fark) + " eksik.";
      } else {
        hedef = k.luks;
        fark = butce - k.luks;
        karar = "Üst fiyat bandının ortasına yeter; bütçede " + para(fark) + " kalır.";
      }
      const dayanak = k.kaynak + " bağımsız kaynak" + (k.urun ? ", " + k.urun + " ürün" : "");
      return [
        ["Seçilen kalem", null, false, "not", k.kategori + " — " + k.ad + " (" + k.birim + ")"],
        ["Bütçeniz", butce, false],
        ["Ekonomik bandın ortası", k.dusuk, false],
        ["Orta bandın ortası", k.orta, false],
        ["Üst bandın ortası", k.luks, false],
        ["Karar", null, true, "not", karar],
        ["Veri dayanağı", null, false, "not", dayanak + " · " + k.tarih],
      ];""",
        "sss": [
            (
                "Bütçemin yeterli olduğuna nasıl karar veriliyor?",
                "Bütçeniz seçtiğiniz kalemin ölçülmüş ekonomik, orta ve üst segment "
                "ortancalarıyla karşılaştırılır. Sonuç tek bir mağazanın en ucuz "
                "ürününe değil, birden fazla kaynaktaki fiyat bandına dayanır."
            ),
            (
                "Neden belirli bir marka veya model önermiyor?",
                "Çünkü bu araç fiyat ölçüyor; enerji sınıfı, kapasite, malzeme ve "
                "ürün özelliği ölçmüyor. Ölçmediğimiz bir özelliğe dayanarak model "
                "önermek güvenilir olmaz."
            ),
            (
                "Bütçe üst banda yetiyorsa istediğim ürünü kesin bulur muyum?",
                "Hayır. Segment tutarları kategori ortancasıdır, stok garantisi veya "
                "tekil ürün teklifi değildir. Satın almadan önce güncel mağaza "
                "fiyatını ve aradığınız özellikleri ayrıca kontrol edin."
            ),
            (
                "Fiyatlar ne zaman yenileniyor?",
                "Ölçümlü veri setleri her ayın 5'i ve 20'sinde yenilenir. Sonuç "
                "tablosunda seçtiğiniz kalemin ölçüm tarihi ayrıca gösterilir."
            ),
        ],
        "_butce": kalemler,
    }


def _tuketim_profilleri(veri_kok: Path | None = None) -> list[dict]:
    """Normalize birim fiyatlari aylik tuketim hesabina hazirlar.

    En az 5 urun ve %20 ad-eslesmesi arar. Daha zayif bir ayrisma teknik
    olarak rakam uretebilse de kullaniciya guvenilir bir medyan vermez.
    """
    kok = veri_kok or SITE_KOK / "veri"
    tanimlar = [
        ("kedi", "kedi-mamasi", "kg", "Kedi maması", "Günlük mama tüketimi (gram)", "günlük-gram"),
        ("kopek", "kopek-mamasi", "kg", "Köpek maması", "Günlük mama tüketimi (gram)", "günlük-gram"),
        ("kedi", "kedi-kumu", "kg", "Kedi kumu (kg)", "Aylık kum tüketimi (kg)", "aylık"),
        ("kedi", "kedi-kumu", "litre", "Kedi kumu (litre)", "Aylık kum tüketimi (litre)", "aylık"),
        ("bebek", "bebek-bezi", "adet", "Bebek bezi", "Günlük bez kullanımı (adet)", "günlük-adet"),
        ("kopek", "cis-pedi", "adet", "Çiş pedi", "Günlük ped kullanımı (adet)", "günlük-adet"),
    ]
    dosyalar = {}
    profiller = []
    for vertikal, kalem, birim, ad, girdi_etiketi, donusum in tanimlar:
        if vertikal not in dosyalar:
            dosya = kok / f"{vertikal}.json"
            try:
                dosyalar[vertikal] = json.loads(dosya.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                dosyalar[vertikal] = {}
        veri_seti = dosyalar[vertikal]
        kalem_verisi = (veri_seti.get("kalemler") or {}).get(kalem) or {}
        ozet = (kalem_verisi.get("birim_fiyatlari") or {}).get(birim) or {}
        if ozet.get("eslesen_urun", 0) < 5 or ozet.get("eslesme_orani", 0) < 0.2:
            continue
        profiller.append({
            "id": f"{vertikal}:{kalem}:{birim}",
            "ad": ad,
            "birim": birim,
            "birim_fiyat": ozet["genel_medyan"],
            "fiyat_etiketi": ozet.get("etiket") or f"TL/{birim}",
            "girdi_etiketi": girdi_etiketi,
            "donusum": donusum,
            "eslesen_urun": ozet["eslesen_urun"],
            "toplam_urun": ozet.get("toplam_urun", 0),
            "kaynak_sayisi": ozet.get("kaynak_sayisi", 0),
            "tarih": kalem_verisi.get("guncelleme_tarihi") or veri_seti.get("guncelleme_tarihi") or "—",
            "yol": f"/{vertikal}/",
        })
    return profiller


def aylik_tuketim_tanimi(veri_kok: Path | None = None) -> dict | None:
    profiller = _tuketim_profilleri(veri_kok)
    if not profiller:
        return None
    tarihler = sorted({p["tarih"] for p in profiller})
    return {
        "id": "aylik-tuketim-maliyeti",
        "slug": "aylik-tuketim-maliyeti",
        "ad": "Aylık Tüketim Maliyeti",
        "baslik": "Mama, Kum, Bez ve Ped Aylık Maliyet Hesabı",
        "soru": "Paket fiyatından gerçek aylık tüketim maliyeti nasıl hesaplanır?",
        "meta": (
            "Kedi ve köpek maması, kedi kumu, bebek bezi ve çiş pedi için "
            "ölçülmüş TL/kg, TL/litre veya TL/adet verisiyle aylık maliyet hesabı."
        ),
        "ozet": (
            f"Paket fiyatını aylık gider sanmak yerine <strong>{len(profiller)} normalize "
            "tüketim profili</strong> kullanıyoruz. Kendi tüketiminizi girin; araç "
            "ölçülmüş birim fiyatla aylık ve yıllık karşılığı hesaplasın."
        ),
        "formul": (
            "Mama = TL/kg × günlük gram × 30 ÷ 1.000 &nbsp;·&nbsp; "
            "Bez/ped = TL/adet × günlük adet × 30 &nbsp;·&nbsp; "
            "Kum = TL/kg veya TL/litre × aylık miktar"
        ),
        "kaynaklar": [
            f"Maliyeti Ne? normalize ürün verisi — ölçüm tarihleri {tarihler[0]} – {tarihler[-1]}",
            "Birim fiyat yalnız ürün adında gramaj veya paket adedi açıkça yazan ürünlerden hesaplanır",
        ],
        "alanlar": [
            {"id": "urun", "etiket": "Tüketim kalemi", "tip": "select",
             "varsayilan": profiller[0]["id"],
             "secenekler": [(p["id"], f'{p["ad"]} — {p["fiyat_etiketi"]}') for p in profiller]},
            {"id": "tuketim", "etiket": profiller[0]["girdi_etiketi"], "tip": "number",
             "varsayilan": "", "adim": "0.01"},
        ],
        "alan_notu": (
            "Tüketimi siz girersiniz; araç hayvan ağırlığı, bez değiştirme sıklığı "
            "veya kum yenileme alışkanlığı varsaymaz. Kedi kumunda kg ve litre "
            "birbirine çevrilmez; ambalajda yazan birimi seçin. Mama profilleri "
            "kaynakların kategori havuzunu ölçer ve kuru/yaş ürünleri içerebilir; "
            "kendi ürününüzün TL/kg değeri kategori ortancasından farklı olabilir."
        ),
        "js": """
      const p = TUKETIM_PROFILLERI.find((x) => x.id === deger("urun"));
      const giris = sayi("tuketim");
      if (!p || giris <= 0) return null;
      let aylikMiktar, miktarMetni;
      if (p.donusum === "günlük-gram") {
        aylikMiktar = giris * 30 / 1000;
        miktarMetni = aylikMiktar.toLocaleString("tr-TR", {maximumFractionDigits: 2}) + " kg/ay";
      } else if (p.donusum === "günlük-adet") {
        aylikMiktar = giris * 30;
        miktarMetni = aylikMiktar.toLocaleString("tr-TR", {maximumFractionDigits: 1}) + " adet/ay";
      } else {
        aylikMiktar = giris;
        miktarMetni = giris.toLocaleString("tr-TR", {maximumFractionDigits: 2}) + " " + p.birim + "/ay";
      }
      const aylik = p.birim_fiyat * aylikMiktar;
      return [
        ["Ölçülmüş birim fiyat", p.birim_fiyat, false, "not", para(p.birim_fiyat) + "/" + p.birim],
        ["Aylık tüketim", null, false, "not", miktarMetni],
        ["Aylık maliyet", aylik, true],
        ["Yıllık karşılık", aylik * 12, false],
        ["Veri dayanağı", null, false, "not", p.eslesen_urun + " eşleşen ürün, " + p.kaynak_sayisi + " kaynak · " + p.tarih],
      ];""",
        "sss": [
            (
                "Neden paket fiyatını doğrudan aylık gider kabul etmiyorsunuz?",
                "Aynı ürün 400 gramlık, 3 kilogramlık veya çoklu paket olabilir. "
                "Paket medyanını aylık gider saymak tüketimi ve paket boyunu birbirine "
                "karıştırır. Bu araç önce fiyatı ortak birime çevirir."
            ),
            (
                "Günlük mama miktarını nereden bulacağım?",
                "Kullandığınız mamanın ambalajındaki besleme tablosunu ve veterinerinizin "
                "önerisini esas alın. Site hayvanın kilosu, yaşı ve sağlık durumu hakkında "
                "varsayım yapmaz."
            ),
            (
                "Kedi kumunda kilogram mı litre mi seçmeliyim?",
                "Ambalajda hangi birim yazıyorsa onu seçin. Kumun yoğunluğu ürüne göre "
                "değiştiği için kilogram ile litre arasında sabit dönüşüm uygulamıyoruz."
            ),
            (
                "Birim fiyat verisi nasıl denetleniyor?",
                "Yalnız ürün adında miktarı açıkça bulunan kayıtlar kullanılır. Sonuçta "
                "eşleşen ürün sayısı, kaynak sayısı ve ölçüm tarihi gösterilir."
            ),
            (
                "Mama hesabı kuru ve yaş mamayı ayırıyor mu?",
                "Henüz ayrı bir kuru/yaş ürün sınıflaması uygulanmıyor. TL/kg değeri "
                "kaynağın mama kategori havuzunun ortancasıdır; bu nedenle kendi "
                "ürününüzün paket fiyatından hesaplanan TL/kg daha isabetli olabilir."
            ),
        ],
        "_tuketim": profiller,
    }


def _slug_haritasi() -> dict[str, dict]:
    return {h["slug"]: h for h in HESAPLAYICILAR}


# ----------------------------------------------------------
# HTML PARCALARI
# ----------------------------------------------------------
def _form_html(h: dict) -> str:
    parcalar = []
    for a in h["alanlar"]:
        if a["tip"] == "select":
            secenekler = "".join(
                f'<option value="{d}"{(" selected" if str(d) == str(a.get("varsayilan")) else "")}>{m}</option>'
                for d, m in a["secenekler"]
            )
            girdi = f'<select id="{a["id"]}" name="{a["id"]}">{secenekler}</select>'
        else:
            # step="1" / step="0.01" ONEMLI: `step` bir GECERLILIK KISITI.
            # Arac hesaplayicisinda step="50000" yuzunden kullanici gercek
            # bir tutar yazinca form SESSIZCE bloke oluyordu.
            # `required` VARSAYILAN AMA MECBURI DEGIL: YouTube hesabinda
            # RPM alani "bos birakabilirsiniz" diyor; ona da required
            # konunca HTML5 validation submit'i SESSIZCE blokluyordu ve
            # sayfa hic sonuc uretmiyordu. Bu, arac hesaplayicisindaki
            # step="50000" bug'inin ayni sinifi - form nitelikleri
            # "gorunum" degil GECERLILIK KISITI. Tarayici testi yakaladi.
            zorunlu = " required" if a.get("zorunlu", True) else ""
            yer_tutucu = f' placeholder="{a["placeholder"]}"' if a.get("placeholder") else ""
            girdi = (
                f'<input type="number" id="{a["id"]}" name="{a["id"]}" '
                f'value="{a.get("varsayilan", "")}" step="{a.get("adim", "0.01")}" min="0"{yer_tutucu}{zorunlu}>'
            )
        parcalar.append(
            f'    <div class="alan"><label for="{a["id"]}">{a["etiket"]}</label>{girdi}</div>'
        )
    notu = (
        f'  <p class="alan-notu">{h["alan_notu"]}</p>\n' if h.get("alan_notu") else ""
    )
    return (
        f'<form id="hesap-formu" class="hesap-formu">\n'
        f'  <div class="alan-izgara">\n' + "\n".join(parcalar) + "\n  </div>\n"
        + notu
        + '  <button type="submit">Hesapla</button>\n'
        '</form>\n<div id="sonuc" class="hesap-sonuc" hidden></div>'
    )


def _kaynak_kunyesi(h: dict) -> str:
    maddeler = "".join(f"<li>{k}</li>" for k in h["kaynaklar"])
    mevzuat = any(
        "Kanunu" in k or "Tebliğ" in k or "Bakanlığı" in k or "BKK" in k
        for k in h["kaynaklar"]
    )
    baslik = "Hesapta kullanılan mevzuat" if mevzuat else "Kaynak ve yöntem"
    not_metni = (
        "Vergi tarifesi ve hadler her 31 Aralık'ta Resmî Gazete'de yeniden "
        "değerleme oranıyla değişir; kıdem tazminatı tavanı yılda iki kez "
        "(Ocak ve Temmuz) güncellenir. Bu sayfadaki parametreler geçerlilik "
        "dönemiyle birlikte tutulur — dönem geçtiğinde sayfa uyarı gösterir."
        if mevzuat else
        "Mevzuata bağlı olmayan hesaplarda değişken parametreleri uydurmuyoruz: "
        "ya kullanıcıdan alıyoruz ya da resmi/teknik kaynağı görünür şekilde "
        "yazıyoruz. Bu yüzden bazı cevaplar tek sayı değil, aralık olarak verilir."
    )
    return (
        '<section class="kaynak-kunye">\n'
        f"  <h2>{baslik}</h2>\n"
        f"  <ul>{maddeler}</ul>\n"
        f'  <p class="sonuc-alt-metin">{not_metni}</p>\n'
        "</section>"
    )


def _sss_html(h: dict) -> str:
    govde = "".join(
        f"  <details><summary>{s}</summary><p>{c}</p></details>\n" for s, c in h["sss"]
    )
    return f'<section class="sss">\n  <h2>Sıkça sorulan sorular</h2>\n{govde}</section>'


def _schema(h: dict) -> str:
    url = f"{SITE_KOK_URL}/{HESAP_KOK}/{h['slug']}/"
    formul_duz = re.sub(r"<[^>]+>", "", h["formul"]).replace("&nbsp;", " ")
    ozet_duz = re.sub(r"<[^>]+>", "", h["ozet"])
    graf = [
        {
            "@type": "WebApplication",
            "name": h["ad"],
            "url": url,
            "applicationCategory": "FinanceApplication",
            "operatingSystem": "Web",
            "browserRequirements": "JavaScript",
            "inLanguage": "tr-TR",
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "TRY"},
            "publisher": {"@type": "Organization", "name": "Maliyeti Ne?", "url": SITE_KOK_URL + "/"},
        },
        {
            "@type": "HowTo",
            "name": h["baslik"],
            "description": ozet_duz,
            "inLanguage": "tr-TR",
            "step": [
                {"@type": "HowToStep", "position": i,
                 "name": a["etiket"], "text": f'{a["etiket"]} alanını doldurun.'}
                for i, a in enumerate(h["alanlar"], start=1)
            ] + [{"@type": "HowToStep", "position": len(h["alanlar"]) + 1,
                  "name": "Hesapla", "text": f'Sonuç şu formülle bulunur: {formul_duz}'}],
        },
        {
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": s,
                 "acceptedAnswer": {"@type": "Answer", "text": c}}
                for s, c in h["sss"]
            ],
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Ana sayfa", "item": SITE_KOK_URL + "/"},
                {"@type": "ListItem", "position": 2, "name": "Hesaplayıcılar", "item": f"{SITE_KOK_URL}/{HESAP_KOK}/"},
                {"@type": "ListItem", "position": 3, "name": h["ad"], "item": url},
            ],
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graf},
                      ensure_ascii=False, indent=1)


def _diger_hesaplar(h: dict) -> str:
    linkler = "".join(
        f'<li><a href="/{HESAP_KOK}/{d["slug"]}/">{d["ad"]}</a></li>'
        for d in tum_hesaplayicilar() if d["id"] != h["id"]
    )
    return f'<section><h2>Diğer hesaplayıcılar</h2><ul class="hesap-liste">{linkler}</ul></section>'


HESAP_MENU = (
    f'<a href="/{HESAP_KOK}/">Hesaplayıcılar</a>'
    f'<a href="/veri/">Veri</a>'
)


def _kabuk(baslik_etiketi: str, meta: str, kanonik: str, schema: str,
           govde: str, ekstra_js: str = "", og_kart: str | None = None,
           og_alt: str | None = None) -> str:
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{baslik_etiketi}</title>
<meta name="description" content="{meta}">
<link rel="canonical" href="{kanonik}">
<meta property="og:title" content="{baslik_etiketi}">
<meta property="og:description" content="{meta}">
<meta property="og:type" content="website">
<meta property="og:url" content="{kanonik}">
{su.og_etiketleri(og_kart, og_alt)}
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="/assets/css/style.css">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<script type="application/ld+json">
{schema}
</script>
{su.ANALITIK}
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">Maliyeti <span>Ne?</span></a>
    <nav class="ust-menu">{su.genel_menu('hesap')}</nav>
  </div>
</header>

<main class="kapsayici">
{govde}
</main>

<footer>
  <div class="kapsayici">
    <div>© 2026 Maliyeti Ne? · <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a> · <a href="/sss/">SSS</a> · <a href="/rehber/">Rehber</a> · <a href="/veri/">Veri</a></div>
    <nav class="footer-endeksler" aria-label="Tüm endeksler">{su.TUM_ENDEKS_LINKLERI}</nav>
  </div>
</footer>
{ekstra_js}
</body>
</html>
"""


HESAP_JS_KALIP = """
<script src="/assets/js/resmi-parametreler.js"></script>
<script src="/assets/js/formul-hesap.js"></script>
<script>
(function () {
  var form = document.getElementById("hesap-formu");
  var kutu = document.getElementById("sonuc");
  if (!form || !kutu) return;

  function deger(id) { var e = document.getElementById(id); return e ? e.value : ""; }
  function sayi(id) { return parseFloat(String(deger(id)).replace(",", ".")) || 0; }
  function para(n) {
    // Tam sayida kurus gostermiyoruz ("1.000 TL"), ondalik varsa iki hane
    // ("4.624,20 TL"). Tek hane ("4.624,2 TL") amatorce duruyordu.
    // -0 duzeltmesi: sifir vergi satirlarinda "-0 TL" cikiyordu.
    // (-0 === 0 dogru oldugu icin karsilastirmayla degil ATAMAYLA cozulur.)
    if (n === 0) n = 0;
    var basamak = Number.isInteger(n) ? 0 : 2;
    return new Intl.NumberFormat("tr-TR", {
      minimumFractionDigits: basamak, maximumFractionDigits: basamak,
    }).format(n) + " TL";
  }

  function hesapla() {
%(GOVDE)s
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var satirlar;
    try { satirlar = hesapla(); } catch (hata) { satirlar = null; }
    if (!satirlar) {
      // Gecersiz girdide "0 TL" gibi guvenilir gorunen bir sonuc BASILMAZ.
      kutu.innerHTML = '<p class="uyari">Girdiğiniz değerlerle hesap yapılamadı. Alanları kontrol edin.</p>';
      kutu.hidden = false;
      return;
    }
    var gecerli = sonucParametreleriGecerliMi({ parametreler: %(PARAM)s });
    var html = "";
    if (!gecerli) {
      // Parametrenin gecerlilik donemi gecmis: sessizce eski yilin
      // vergisini vermek yerine acikca soyluyoruz.
      html += '<p class="uyari">Bu hesapta kullanılan resmî parametrelerin geçerlilik ' +
              'dönemi sona ermiş görünüyor. Sonucu yeni dönem tutarlarıyla ' +
              'doğrulamadan kullanmayın.</p>';
    }
    html += '<table class="sonuc-tablo"><tbody>';
    satirlar.forEach(function (s) {
      var ad = s[0], tutar = s[1], vurgu = s[2], tip = s[3], metin = s[4];
      var govde = metin ? metin : (tutar === null ? "" : para(tutar));
      html += '<tr' + (vurgu ? ' class="vurgu"' : (tip === "not" ? ' class="satir-not"' : '')) +
              '><td>' + ad + '</td><td class="sayi">' + govde + '</td></tr>';
    });
    html += "</tbody></table>";
    kutu.innerHTML = html;
    kutu.hidden = false;
  });
})();
</script>"""


def _hesap_js(h: dict) -> str:
    onek = ""
    if h.get("_tufe"):
        # Seri sayfaya GOMULUYOR (build-time). Client-side fetch DEGIL:
        # AI botlarinin cogu JS calistirmiyor ve yenibirhesap'i AI
        # motorlari icin gorunmez yapan sey tam olarak bu.
        onek = ("<script>const TUFE_SERISI = "
                + json.dumps(h["_tufe"]["seri"], ensure_ascii=False)
                + ";</script>\n")
    if h.get("_butce"):
        # Fiyat bantlari build-time gomulu. Arama/AI botu sayfanin neye
        # dayandigini JS calistirmadan gorur; kullanici etkilesiminde ayni
        # anlik veri kullanilir, istemci tarafinda ikinci kaynak fetch edilmez.
        onek += ("<script>const BUTCE_KALEMLERI = "
                 + json.dumps(h["_butce"], ensure_ascii=False)
                 + ";</script>\n")
    if h.get("_tuketim"):
        onek += ("<script>const TUKETIM_PROFILLERI = "
                 + json.dumps(h["_tuketim"], ensure_ascii=False)
                 + ";\n(function () {\n"
                   "  var secim = document.getElementById('urun');\n"
                   "  var etiket = document.querySelector('label[for=\"tuketim\"]');\n"
                   "  function yenile() {\n"
                   "    var p = TUKETIM_PROFILLERI.find(function (x) { return x.id === secim.value; });\n"
                   "    if (p && etiket) etiket.textContent = p.girdi_etiketi;\n"
                   "  }\n"
                   "  if (secim) { secim.addEventListener('change', yenile); yenile(); }\n"
                   "})();</script>\n")
    param = "RESMI_PARAMETRELER ? Object.values(RESMI_PARAMETRELER) : []"
    if not any("Kanunu" in k or "Tebliğ" in k or "Bakanlığı" in k for k in h["kaynaklar"]):
        param = "[]"  # saf matematik - mevzuata bagli degil
    return onek + HESAP_JS_KALIP % {"GOVDE": h["js"], "PARAM": param}


def sayfa_uret(h: dict) -> str:
    url = f"{SITE_KOK_URL}/{HESAP_KOK}/{h['slug']}/"
    govde = f"""  <nav class="kirinti" aria-label="Sayfa yolu">
    <a href="/">Ana sayfa</a> › <a href="/{HESAP_KOK}/">Hesaplayıcılar</a> › <span>{h["ad"]}</span>
  </nav>

  <h1>{h["baslik"]}</h1>

  <div class="cevap-blok">
    {h["ozet"]}
  </div>

  {_form_html(h)}

  <section>
    <h2>Nasıl hesaplanır?</h2>
    <p class="formul">{h["formul"]}</p>
  </section>

  {_kaynak_kunyesi(h)}

  {_sss_html(h)}

  {_diger_hesaplar(h)}

  <p class="sonuc-alt-metin">Bu sayfa bir hesap aracıdır, mali ya da hukuki
    danışmanlık değildir. Ölçülmüş gerçek fiyat verileri için
    <a href="/">maliyet endekslerimize</a> bakabilirsiniz.</p>
"""
    return _kabuk(f'{h["baslik"]} | Maliyeti Ne?', h["meta"], url,
                  _schema(h), govde, _hesap_js(h),
                  og_kart=f'/assets/og/hesap-{h["slug"]}.png',
                  og_alt=h.get("ad") or h["baslik"])


def dizin_uret() -> str:
    url = f"{SITE_KOK_URL}/{HESAP_KOK}/"
    kartlar = "".join(
        f'    <a class="hesap-kart" href="/{HESAP_KOK}/{h["slug"]}/">'
        f'<strong>{h["ad"]}</strong><span>{re.sub(r"<[^>]+>", "", h["ozet"])[:110]}…</span></a>\n'
        for h in tum_hesaplayicilar()
    )
    schema = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "name": "Hesaplayıcılar", "url": url,
             "inLanguage": "tr-TR",
             "description": "Vergi, maaş, tazminat ve kredi hesaplayıcıları — "
                            "kullanılan her resmî parametrenin kaynağı sayfada yazılı."},
            {"@type": "ItemList", "itemListElement": [
                {"@type": "ListItem", "position": i, "name": h["ad"],
                 "url": f"{SITE_KOK_URL}/{HESAP_KOK}/{h['slug']}/"}
                for i, h in enumerate(tum_hesaplayicilar(), start=1)]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Ana sayfa", "item": SITE_KOK_URL + "/"},
                {"@type": "ListItem", "position": 2, "name": "Hesaplayıcılar", "item": url}]},
        ],
    }, ensure_ascii=False, indent=1)

    govde = f"""  <nav class="kirinti" aria-label="Sayfa yolu">
    <a href="/">Ana sayfa</a> › <span>Hesaplayıcılar</span>
  </nav>

  <h1>Hesaplayıcılar</h1>

  <div class="cevap-blok">
    Vergi, maaş, tazminat ve kredi hesapları. Bu sayfalardaki sonuçlar
    mevzuatla belirlenmiş oranlardan türetilir; <strong>kullanılan her
    parametrenin kaynağı ve geçerlilik dönemi ilgili sayfada yazılıdır.</strong>
    Dönem geçtiğinde sayfa sessizce eski oranı kullanmaz, uyarı gösterir.
  </div>

  <div class="hesap-izgara">
{kartlar}  </div>

  <section>
    <h2>Sonuç neye dayanıyor?</h2>
    <p>Burada iki ayrı tür hesap var. Vergi, maaş ve tazminat sonuçları
      ölçüm değil; mevzuat ya da matematikten <em>türetme</em> yapar.
      Bütçem Yeter mi?
      aracı ise sitedeki güncel fiyat <em>ölçümlerini</em> ekonomik, orta ve
      üst bantla karşılaştırır. Hangi türün kullanıldığı her aracın kaynak
      bölümünde açıkça yazılıdır.</p>
    <p>Ölçülmüş fiyatlar için: {su.TUM_ENDEKS_LINKLERI}</p>
  </section>
"""
    return _kabuk(
        "Hesaplayıcılar: Vergi, Maaş, Tazminat, Kredi | Maliyeti Ne?",
        "KDV, brütten nete maaş, kıdem ve ihbar tazminatı, kredi taksiti ve "
        "yüzde hesaplama. Kullanılan resmî parametrelerin kaynağı sayfada yazılı.",
        url, schema, govde)


def tum_hesaplayicilar(veri_kok: Path | None = None) -> list[dict]:
    """Sabit liste + veriyle uretilen araclar. Veri yoksa o sayfalar hic
    uretilmez ve sitemap'e de girmez."""
    liste = list(HESAPLAYICILAR)
    tuketim = aylik_tuketim_tanimi(veri_kok)
    if tuketim:
        liste.insert(0, tuketim)
    butce = butcem_yeter_mi_tanimi(veri_kok)
    if butce:
        liste.insert(0, butce)
    ag = alim_gucu_tanimi(veri_kok)
    if ag:
        liste.insert(0, ag)
    return liste


def yaz() -> list[Path]:
    yazilan = []
    dizin = SITE_KOK / HESAP_KOK / "index.html"
    dizin.parent.mkdir(parents=True, exist_ok=True)
    dizin.write_text(dizin_uret(), encoding="utf-8")
    yazilan.append(dizin)
    for h in tum_hesaplayicilar():
        hedef = SITE_KOK / HESAP_KOK / h["slug"] / "index.html"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(sayfa_uret(h), encoding="utf-8")
        yazilan.append(hedef)
    return yazilan


def sitemap_yollari() -> list[str]:
    """sayfa_uret.py sitemap uretirken buradan okuyor - elle liste
    tutulmuyor ki yeni hesaplayici eklenince unutulmasin."""
    return [f"{HESAP_KOK}/"] + [f"{HESAP_KOK}/{h['slug']}/" for h in tum_hesaplayicilar()]


def main():
    for p in yaz():
        print("Hesap sayfasi:", str(p).replace(str(SITE_KOK), ""))
    print(f"Toplam {len(tum_hesaplayicilar())} hesaplayici + dizin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
