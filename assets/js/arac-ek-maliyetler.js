// BU DOSYA OTOMATIK URETILIR: scraper/arac_maliyetleri.py
// Resmi tarife ve tahmini varsayimlari Python rehberiyle ayni kaynaktan alir.

const ARAC_EK_MALIYETLER = {
  "yil": 2026,
  "mtv": {
    "ad": "MTV (ilk yıl)",
    "kaynak_tipi": "resmi",
    "kaynak": "58 Seri No.lu MTV Genel Tebliği (31.12.2025 R.G.)",
    "kaynak_url": "https://www.gib.gov.tr/mevzuat/kanun/441/teblig/11860",
    "not": "1-3 yaş içten yanmalı otomobil ve üst taşıt değeri kademesi. Elektrikli araçlar ile diğer değer kademeleri ayrıca hesaplanır.",
    "kademeler": [
      {
        "etiket": "1300 cc'ye kadar",
        "max_cc": 1300,
        "tutar": 6902
      },
      {
        "etiket": "1301 - 1600 cc",
        "max_cc": 1600,
        "tutar": 12028
      },
      {
        "etiket": "1601 - 1800 cc",
        "max_cc": 1800,
        "tutar": 21251
      },
      {
        "etiket": "1801 - 2000 cc",
        "max_cc": 2000,
        "tutar": 33474
      },
      {
        "etiket": "2001 - 2500 cc",
        "max_cc": 2500,
        "tutar": 50217
      },
      {
        "etiket": "2501 - 3000 cc",
        "max_cc": 3000,
        "tutar": 70018
      },
      {
        "etiket": "3001 - 3500 cc",
        "max_cc": 3500,
        "tutar": 106641
      },
      {
        "etiket": "3501 - 4000 cc",
        "max_cc": 4000,
        "tutar": 167671
      },
      {
        "etiket": "4001 cc ve üzeri",
        "max_cc": null,
        "tutar": 274415
      }
    ]
  },
  "noter_tescil": {
    "ad": "İlk tescil harcı",
    "kaynak_tipi": "resmi",
    "kaynak": "7566 sayılı Kanun ile 492 sayılı Harçlar Kanunu (2) sayılı tarife",
    "kaynak_url": "https://www.gib.gov.tr/mevzuat/kanun/439/ozelge/38881",
    "nispi_oran": 0.002,
    "asgari_harc": 1000,
    "not": "Satış bedelinin binde 2'si; asgari 1.000 TL. Değişebilen noter hizmet, yazı ve belge giderleri bu kaleme dahil değildir."
  },
  "plaka_ruhsat": {
    "ad": "Plaka + ruhsat/belge",
    "kaynak_tipi": "tahmini",
    "tutar": 3500,
    "not": "Plaka basımı, ruhsat ve belge giderleri için yaklaşık değer."
  },
  "trafik_sigortasi": {
    "ad": "Zorunlu trafik sigortası",
    "kaynak_tipi": "tahmini",
    "tutar": 9000,
    "not": "İl, araç tipi ve hasarsızlık basamağına göre değişir."
  },
  "kasko": {
    "ad": "Kasko (ilk yıl)",
    "kaynak_tipi": "tahmini",
    "oran": 0.03,
    "asgari": 12000,
    "not": "Araç değerinin yaklaşık %3'ü; şirkete ve sürücü profiline göre değişir."
  }
};

function aracEkMaliyetHesapla(aracFiyati, motorCc, secilenler) {
  const M = ARAC_EK_MALIYETLER;
  const detaylar = [];

  if (secilenler.includes("mtv")) {
    const kademe =
      M.mtv.kademeler.find((k) => k.max_cc !== null && motorCc <= k.max_cc) ||
      M.mtv.kademeler[M.mtv.kademeler.length - 1];
    detaylar.push({
      id: "mtv",
      ad: M.mtv.ad + " - " + kademe.etiket,
      tutar: kademe.tutar,
      kaynak_tipi: M.mtv.kaynak_tipi,
      not: M.mtv.kaynak + ". " + M.mtv.not,
    });
  }

  if (secilenler.includes("noter_tescil")) {
    const t = M.noter_tescil;
    const harc = Math.max(aracFiyati * t.nispi_oran, t.asgari_harc);
    detaylar.push({
      id: "noter_tescil", ad: t.ad, tutar: Math.round(harc),
      kaynak_tipi: t.kaynak_tipi, not: t.not,
    });
  }

  ["plaka_ruhsat", "trafik_sigortasi"].forEach((id) => {
    if (!secilenler.includes(id)) return;
    const t = M[id];
    detaylar.push({
      id, ad: t.ad, tutar: t.tutar,
      kaynak_tipi: t.kaynak_tipi, not: t.not,
    });
  });

  if (secilenler.includes("kasko")) {
    const t = M.kasko;
    detaylar.push({
      id: "kasko", ad: t.ad,
      tutar: Math.round(Math.max(aracFiyati * t.oran, t.asgari)),
      kaynak_tipi: t.kaynak_tipi, not: t.not,
    });
  }

  const ekToplam = detaylar.reduce((toplam, d) => toplam + d.tutar, 0);
  const resmiToplam = detaylar
    .filter((d) => d.kaynak_tipi === "resmi")
    .reduce((toplam, d) => toplam + d.tutar, 0);
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
