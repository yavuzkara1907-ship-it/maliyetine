// Sifir arac ALIM ve ILK YIL sahip olma ek maliyetleri.
//
// Arac fiyati endeksten (gercek kazima verisi) gelir; bu dosya fiyatin
// UZERINE binen kalemleri tanimlar. Kaynak tipi HER KALEMDE ayri ayri
// isaretlenir - KIRMIZI CIZGI geregi resmi tarife ile tahmini deger
// birbirine karistirilmaz:
//
//   "resmi"   -> Resmi Gazete / GIB tarifesi ya da mevzuatla belirlenmis
//                formul. Yilda bir (genelde 31 Aralik) degisir, elle
//                guncellenir. Kaynak ve yururluk yili belirtilir.
//   "tahmini" -> piyasa arastirmasindan turetilmis yaklasik deger.
//                Sirkete, ile, surucu profiline gore degisir.
//
// GUNCELLEME NOTU: MTV ve harclar her yil 31 Aralik'ta Resmi Gazete'de
// yayimlanan yeniden degerleme oraniyla artiyor. 2027 tarifesi cikinca
// bu dosyadaki "yil" alani ve tutarlar guncellenmeli.

const ARAC_EK_MALIYETLER = {
  yil: 2026,

  // MTV 1-3 yas otomobil, motor silindir hacmine gore.
  // Kaynak: 58 Seri No.lu MTV Genel Tebligi (31.12.2025 tarihli Resmi
  // Gazete). NOT: gercek tarife hacim X arac DEGERI kademelidir; burada
  // her hacim icin YAYGIN deger kademesi kullaniliyor, ust deger
  // kademelerinde MTV daha yuksek olur (metodolojide belirtiliyor).
  mtv: {
    kaynak_tipi: "resmi",
    kaynak: "58 Seri No.lu MTV Genel Tebliği (31.12.2025 R.G.)",
    kademeler: [
      { etiket: "1300 cc'ye kadar", max_cc: 1300, tutar: 6903 },
      { etiket: "1301 - 1600 cc", max_cc: 1600, tutar: 12028 },
      { etiket: "1601 - 1800 cc", max_cc: 1800, tutar: 21252 },
      { etiket: "1801 cc ve üzeri", max_cc: null, tutar: 33000 },
    ],
  },

  // Noter + ilk tescil harci. 2026'da sabit ucret yerine NISPI HARC
  // sistemine gecildi: satis bedeli (ya da kasko degeri, hangisi yuksekse)
  // uzerinden binde 2, asgari 1.000 TL. Ustune sabit noter islem ucreti.
  noter_tescil: {
    kaynak_tipi: "resmi",
    kaynak: "2026 noter harç düzenlemesi (nispi harç sistemi)",
    nispi_oran: 0.002,
    asgari_harc: 1000,
    sabit_ucret: 1920, // 1.870-1.970 TL bandinin ortasi
  },

  // Plaka basimi + ruhsat/belge masraflari.
  plaka_ruhsat: {
    kaynak_tipi: "tahmini",
    tutar: 3500,
    not: "Plaka basımı, ruhsat ve belge masrafları.",
  },

  // Zorunlu trafik sigortasi: ile, arac tipine ve hasarsizlik basamagina
  // gore ciddi degisir. Burada yeni surucu/ortalama profil varsayimi.
  trafik_sigortasi: {
    kaynak_tipi: "tahmini",
    tutar: 9000,
    not: "İl, araç tipi ve hasarsızlık basamağına göre değişir.",
  },

  // Kasko genelde arac degerinin yuzdesi olarak fiyatlanir.
  kasko: {
    kaynak_tipi: "tahmini",
    oran: 0.03,
    asgari: 12000,
    not: "Araç değerinin yaklaşık %3'ü; şirkete ve sürücü profiline göre değişir.",
  },
};

// Verilen arac fiyati ve motor hacmi icin ek maliyet kalemlerini hesaplar.
// secilenler: hangi kalemlerin dahil edilecegi (id listesi).
function aracEkMaliyetHesapla(aracFiyati, motorCc, secilenler) {
  const M = ARAC_EK_MALIYETLER;
  const detaylar = [];

  if (secilenler.includes("mtv")) {
    const kademe =
      M.mtv.kademeler.find((k) => k.max_cc !== null && motorCc <= k.max_cc) ||
      M.mtv.kademeler[M.mtv.kademeler.length - 1];
    detaylar.push({
      id: "mtv",
      ad: "MTV (ilk yıl) — " + kademe.etiket,
      tutar: kademe.tutar,
      kaynak_tipi: M.mtv.kaynak_tipi,
      not: M.mtv.kaynak,
    });
  }

  if (secilenler.includes("noter_tescil")) {
    const nispi = Math.max(aracFiyati * M.noter_tescil.nispi_oran, M.noter_tescil.asgari_harc);
    detaylar.push({
      id: "noter_tescil",
      ad: "Noter + ilk tescil harcı",
      tutar: Math.round(nispi + M.noter_tescil.sabit_ucret),
      kaynak_tipi: M.noter_tescil.kaynak_tipi,
      not: "Binde 2 nispi harç (asgari 1.000 TL) + sabit noter ücreti.",
    });
  }

  if (secilenler.includes("plaka_ruhsat")) {
    detaylar.push({
      id: "plaka_ruhsat", ad: "Plaka + ruhsat",
      tutar: M.plaka_ruhsat.tutar,
      kaynak_tipi: M.plaka_ruhsat.kaynak_tipi, not: M.plaka_ruhsat.not,
    });
  }

  if (secilenler.includes("trafik_sigortasi")) {
    detaylar.push({
      id: "trafik_sigortasi", ad: "Zorunlu trafik sigortası",
      tutar: M.trafik_sigortasi.tutar,
      kaynak_tipi: M.trafik_sigortasi.kaynak_tipi, not: M.trafik_sigortasi.not,
    });
  }

  if (secilenler.includes("kasko")) {
    detaylar.push({
      id: "kasko", ad: "Kasko (ilk yıl)",
      tutar: Math.round(Math.max(aracFiyati * M.kasko.oran, M.kasko.asgari)),
      kaynak_tipi: M.kasko.kaynak_tipi, not: M.kasko.not,
    });
  }

  const ekToplam = detaylar.reduce((t, d) => t + d.tutar, 0);
  const resmiToplam = detaylar.filter((d) => d.kaynak_tipi === "resmi")
                              .reduce((t, d) => t + d.tutar, 0);
  return {
    detaylar,
    ekToplam,
    resmiToplam,
    tahminiToplam: ekToplam - resmiToplam,
    genelToplam: aracFiyati + ekToplam,
  };
}

if (typeof module === "object" && module.exports) {
  module.exports = { ARAC_EK_MALIYETLER, aracEkMaliyetHesapla };
}
