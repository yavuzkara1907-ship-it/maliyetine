/*
 * Maliyeti Ne? — RESMÎ PARAMETRELER (2026)
 *
 * Formül hesaplayıcılarının kullandığı, mevzuatla belirlenmiş tüm sayılar
 * BURADA ve yalnızca burada durur.
 *
 * ------------------------------------------------------------------
 * NEDEN TEK DOSYA VE NEDEN HER SAYININ YANINDA KAYNAĞI VAR
 * ------------------------------------------------------------------
 * Bu sayılar fiyat değil MEVZUAT. Yanlış bir vergi oranı, yanlış bir
 * fiyattan daha kötü: kullanıcı ona göre karar veriyor ve hatayı
 * fark etmesinin yolu yok. O yüzden:
 *   - Her parametre kümesi `kaynak` (tebliğ/kanun adı) taşır ve bu
 *     kaynak sayfada GÖRÜNÜR.
 *   - Her küme `gecerli_baslangic` / `gecerli_bitis` taşır.
 *   - Süresi geçmiş parametreyle hesap yapılırsa sayfa UYARI gösterir,
 *     sessizce eski yılın vergisini vermez (bkz. `parametreGecerliMi`).
 *
 * Rakiplerin hiçbirinde bu yok: hesapsonuc.com metin içinde mevzuata
 * atıf yapıyor ama hangi sayının hangi tebliğden geldiği belli değil;
 * nekadar.com.tr ve maliyeti.com.tr hiç kaynak vermiyor.
 *
 * ------------------------------------------------------------------
 * YILLIK GÜNCELLEME ZORUNLU
 * ------------------------------------------------------------------
 * Vergi tarifesi ve hadler her 31 Aralık'ta Resmî Gazete'de yeniden
 * değerleme oranıyla değişir. Kıdem tazminatı tavanı ise YILDA İKİ KEZ
 * (Ocak ve Temmuz) değişir. Bu dosya o tarihlerde elle güncellenir;
 * bir test `gecerli_bitis` geçmişse başarısız olur.
 */

const RESMI_PARAMETRELER = {
  // --------------------------------------------------------------
  // GELİR VERGİSİ TARİFESİ 2026
  // Kümülatif tutarlar aritmetik olarak dilim × oran ile birebir
  // tutuyor (190.000×%15 = 28.500; +210.000×%20 = 70.500; ...) —
  // veri kendi içinde tutarlı, bir test bunu doğruluyor.
  // --------------------------------------------------------------
  gelir_vergisi: {
    yil: 2026,
    kaynak: "332 Seri No.lu Gelir Vergisi Genel Tebliği",
    kaynak_detay: "31.12.2025 tarihli ve 33124 (5. Mükerrer) sayılı Resmî Gazete",
    gecerli_baslangic: "2026-01-01",
    gecerli_bitis: "2026-12-31",
    // Ücret gelirleri tarifesi — ücret dışından farkı 3. dilimde başlar.
    ucret: [
      { ust: 190000, oran: 0.15, birikmis: 0 },
      { ust: 400000, oran: 0.20, birikmis: 28500 },
      { ust: 1500000, oran: 0.27, birikmis: 70500 },
      { ust: 5300000, oran: 0.35, birikmis: 367500 },
      { ust: null, oran: 0.40, birikmis: 1697500 },
    ],
    ucret_disi: [
      { ust: 190000, oran: 0.15, birikmis: 0 },
      { ust: 400000, oran: 0.20, birikmis: 28500 },
      { ust: 1000000, oran: 0.27, birikmis: 70500 },
      { ust: 5300000, oran: 0.35, birikmis: 232500 },
      { ust: null, oran: 0.40, birikmis: 1737500 },
    ],
  },

  // --------------------------------------------------------------
  // ASGARİ ÜCRET VE SGK 2026
  // Doğrulama: 33.030 − %14 SGK − %1 işsizlik = 28.075,50 → açıklanan
  // net asgari ücretle birebir. Yani hem oranlar hem istisna yapısı
  // (asgari ücret gelir ve damga vergisinden istisna) teyit edildi.
  // --------------------------------------------------------------
  asgari_ucret: {
    yil: 2026,
    kaynak: "2026 Asgari Ücret Tespit Komisyonu Kararı",
    gecerli_baslangic: "2026-01-01",
    gecerli_bitis: "2026-12-31",
    brut_aylik: 33030.0,
    net_aylik: 28075.5,
  },

  sgk: {
    yil: 2026,
    kaynak: "5510 sayılı Kanun; 2026 SGK prime esas kazanç sınırları",
    gecerli_baslangic: "2026-01-01",
    gecerli_bitis: "2026-12-31",
    // 2026'da tavan, günlük asgari ücretin 7,5 katından 9 katına çıktı.
    tavan_aylik: 297270.0,
    taban_aylik: 33030.0,
    isci_sgk_orani: 0.14,
    isci_issizlik_orani: 0.01,
  },

  damga_vergisi: {
    yil: 2026,
    kaynak: "488 sayılı Damga Vergisi Kanunu (ücretlerde binde 7,59)",
    gecerli_baslangic: "2026-01-01",
    gecerli_bitis: "2026-12-31",
    ucret_orani: 0.00759,
  },

  // --------------------------------------------------------------
  // KIDEM TAZMİNATI TAVANI — YILDA İKİ KEZ DEĞİŞİR
  // Bu, dosyadaki en kısa ömürlü parametre. 31.12.2026'da yenisi gelir.
  // --------------------------------------------------------------
  kidem_tavani: {
    kaynak: "T.C. Çalışma ve Sosyal Güvenlik Bakanlığı — kıdem tazminatı tavan tutarı",
    gecerli_baslangic: "2026-07-01",
    gecerli_bitis: "2026-12-31",
    tutar: 73729.84,
  },

  // --------------------------------------------------------------
  // İHBAR SÜRELERİ — mevzuatla sabit, yıllık değişmez
  // --------------------------------------------------------------
  ihbar: {
    kaynak: "4857 sayılı İş Kanunu md. 17",
    gecerli_baslangic: "2003-06-10",
    gecerli_bitis: null, // süresiz — kanun değişmedikçe geçerli
    kademeler: [
      { etiket: "6 aydan az", max_ay: 6, hafta: 2 },
      { etiket: "6 ay – 1,5 yıl", max_ay: 18, hafta: 4 },
      { etiket: "1,5 – 3 yıl", max_ay: 36, hafta: 6 },
      { etiket: "3 yıldan fazla", max_ay: null, hafta: 8 },
    ],
  },

  // --------------------------------------------------------------
  // KDV ORANLARI
  // --------------------------------------------------------------
  kdv: {
    kaynak: "3065 sayılı KDV Kanunu; 2007/13033 sayılı BKK ekli listeler",
    gecerli_baslangic: "2023-07-10",
    gecerli_bitis: null,
    oranlar: [
      { oran: 0.01, etiket: "%1", ornek: "temel gıda, gazete, cenaze hizmetleri" },
      { oran: 0.10, etiket: "%10", ornek: "gıda, tekstil, ilaç, konaklama" },
      { oran: 0.20, etiket: "%20", ornek: "genel oran" },
    ],
  },
};

/*
 * Parametre kümesi bugün geçerli mi?
 *
 * NEDEN: 1 Ocak 2027'de bu dosya güncellenmezse site sessizce 2026
 * vergisini hesaplamaya devam eder — ve kullanıcı bunu anlamaz. Bu
 * fonksiyon süresi geçmiş kümeyi bildirir, sayfa da görünür uyarı
 * gösterir. "Sessizce yanlış" hiçbir zaman kabul edilebilir değil.
 */
function parametreGecerliMi(kume, bugun) {
  const t = (bugun || new Date()).toISOString().slice(0, 10);
  if (kume.gecerli_baslangic && t < kume.gecerli_baslangic) return false;
  if (kume.gecerli_bitis && t > kume.gecerli_bitis) return false;
  return true;
}

/* Artan oranlı tarifeden vergi. Tarife dilim listesi, matrah TL. */
function tarifedenVergi(tarife, matrah) {
  if (matrah <= 0) return 0;
  let onceki = 0;
  for (const d of tarife) {
    if (d.ust === null || matrah <= d.ust) {
      return d.birikmis + (matrah - onceki) * d.oran;
    }
    onceki = d.ust;
  }
  return 0;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { RESMI_PARAMETRELER, parametreGecerliMi, tarifedenVergi };
}
