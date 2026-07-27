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
                f'<option value="{d}">{m}</option>' for d, m in a["secenekler"]
            )
            girdi = f'<select id="{a["id"]}" name="{a["id"]}">{secenekler}</select>'
        else:
            # step="1" / step="0.01" ONEMLI: `step` bir GECERLILIK KISITI.
            # Arac hesaplayicisinda step="50000" yuzunden kullanici gercek
            # bir tutar yazinca form SESSIZCE bloke oluyordu.
            girdi = (
                f'<input type="number" id="{a["id"]}" name="{a["id"]}" '
                f'value="{a.get("varsayilan", "")}" step="{a.get("adim", "0.01")}" min="0" required>'
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
    return (
        '<section class="kaynak-kunye">\n'
        "  <h2>Hesapta kullanılan mevzuat</h2>\n"
        f"  <ul>{maddeler}</ul>\n"
        '  <p class="sonuc-alt-metin">Vergi tarifesi ve hadler her 31 Aralık\'ta '
        "Resmî Gazete'de yeniden değerleme oranıyla değişir; kıdem tazminatı tavanı "
        "yılda iki kez (Ocak ve Temmuz) güncellenir. Bu sayfadaki parametreler "
        "geçerlilik dönemiyle birlikte tutulur — dönem geçtiğinde sayfa uyarı gösterir.</p>\n"
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
        for d in HESAPLAYICILAR if d["id"] != h["id"]
    )
    return f'<section><h2>Diğer hesaplayıcılar</h2><ul class="hesap-liste">{linkler}</ul></section>'


HESAP_MENU = (
    f'<a href="/{HESAP_KOK}/">Hesaplayıcılar</a>'
    f'<a href="/veri/">Veri</a>'
)


def _kabuk(baslik_etiketi: str, meta: str, kanonik: str, schema: str,
           govde: str, ekstra_js: str = "") -> str:
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
{su.OG_ETIKETLERI}
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="/assets/css/style.css">
<script type="application/ld+json">
{schema}
</script>
</head>
<body>

<header class="ust-bar">
  <div class="kapsayici">
    <a href="/" class="logo">Maliyeti <span>Ne?</span></a>
    <nav class="ust-menu">{HESAP_MENU}</nav>
  </div>
</header>

<main class="kapsayici">
{govde}
</main>

<footer>
  <div class="kapsayici">
    <div>© 2026 Maliyeti Ne? · <a href="/hakkimizda/">Hakkımızda</a> · <a href="/iletisim/">İletişim</a> · <a href="/sss/">SSS</a> · <a href="/veri/">Veri</a></div>
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
    param = "RESMI_PARAMETRELER ? Object.values(RESMI_PARAMETRELER) : []"
    if not any("Kanunu" in k or "Tebliğ" in k or "Bakanlığı" in k for k in h["kaynaklar"]):
        param = "[]"  # saf matematik - mevzuata bagli degil
    return HESAP_JS_KALIP % {"GOVDE": h["js"], "PARAM": param}


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
                  _schema(h), govde, _hesap_js(h))


def dizin_uret() -> str:
    url = f"{SITE_KOK_URL}/{HESAP_KOK}/"
    kartlar = "".join(
        f'    <a class="hesap-kart" href="/{HESAP_KOK}/{h["slug"]}/">'
        f'<strong>{h["ad"]}</strong><span>{re.sub(r"<[^>]+>", "", h["ozet"])[:110]}…</span></a>\n'
        for h in HESAPLAYICILAR
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
                for i, h in enumerate(HESAPLAYICILAR, start=1)]},
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
    <h2>Bunlar ölçülmüş fiyatlardan nasıl farklı?</h2>
    <p>Sitenin geri kalanı gerçek fiyat <em>ölçümü</em> yapar: ürünler
      e-ticaret kaynaklarından ayda iki kez derlenir, her rakamın yanında
      kaynak sayısı ve ölçüm tarihi durur. Bu sayfadaki hesaplar ise
      ölçüm değil <em>türetme</em>: kıdem tazminatı bir kanun formülü,
      gelir vergisi bir tebliğ tarifesi. İkisini bilinçli olarak ayrı
      tutuyoruz — biri ölçülür, diğeri mevzuattan okunur.</p>
    <p>Ölçülmüş fiyatlar için: {su.TUM_ENDEKS_LINKLERI}</p>
  </section>
"""
    return _kabuk(
        "Hesaplayıcılar: Vergi, Maaş, Tazminat, Kredi | Maliyeti Ne?",
        "KDV, brütten nete maaş, kıdem ve ihbar tazminatı, kredi taksiti ve "
        "yüzde hesaplama. Kullanılan resmî parametrelerin kaynağı sayfada yazılı.",
        url, schema, govde)


def yaz() -> list[Path]:
    yazilan = []
    dizin = SITE_KOK / HESAP_KOK / "index.html"
    dizin.parent.mkdir(parents=True, exist_ok=True)
    dizin.write_text(dizin_uret(), encoding="utf-8")
    yazilan.append(dizin)
    for h in HESAPLAYICILAR:
        hedef = SITE_KOK / HESAP_KOK / h["slug"] / "index.html"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(sayfa_uret(h), encoding="utf-8")
        yazilan.append(hedef)
    return yazilan


def sitemap_yollari() -> list[str]:
    """sayfa_uret.py sitemap uretirken buradan okuyor - elle liste
    tutulmuyor ki yeni hesaplayici eklenince unutulmasin."""
    return [f"{HESAP_KOK}/"] + [f"{HESAP_KOK}/{h['slug']}/" for h in HESAPLAYICILAR]


def main():
    for p in yaz():
        print("Hesap sayfasi:", str(p).replace(str(SITE_KOK), ""))
    print(f"Toplam {len(HESAPLAYICILAR)} hesaplayici + dizin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
