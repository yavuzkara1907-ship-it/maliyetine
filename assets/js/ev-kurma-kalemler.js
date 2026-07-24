// Ev kurma vertikali kalem tanimlari - hem hesaplayici hem endeks sayfasi
// bu listeyi kullanir. scraper/sayfa_uret.py'deki EV_KURMA_KALEMLERI ile
// ayni liste (kasitli kucuk tekrar, bkz. dugun-kalemler.js basindaki not).
//
// Dugun'den farki: hic "tahmini" kalem yok (CLAUDE.md "EV KURMA VERTIKALI"
// karari - ChatGPT'nin uydurma rakamlari kullanilmadi, hepsi icin gercek
// Trendyol kaynagi arandi) ve hic "kisi_basi" birim yok (tamamen urun
// bazli, sabit fiyatli kalemler).

const EV_KURMA_KALEMLERI = [
  { id: "buzdolabi", ad: "Buzdolabı", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "camasir-makinesi", ad: "Çamaşır Makinesi", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "bulasik-makinesi", ad: "Bulaşık Makinesi", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "firin-ocak", ad: "Fırın / Ocak (Ankastre Set)", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "mikrodalga", ad: "Mikrodalga Fırın", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "davlumbaz", ad: "Davlumbaz", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "kurutma-makinesi", ad: "Kurutma Makinesi", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "klima", ad: "Klima", birim: "sabit", kaynak_tipi: "gercek" },

  { id: "koltuk-takimi", ad: "Koltuk Takımı", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "yemek-masasi", ad: "Yemek Masası Takımı", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "yatak", ad: "Çift Kişilik Yatak", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "gardirop", ad: "Gardırop", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "tv-unitesi", ad: "TV Ünitesi", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "karyola", ad: "Karyola", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "komodin", ad: "Komodin", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "sifonyer", ad: "Şifonyer", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "boy-aynasi", ad: "Boy Aynası", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "sehpa", ad: "Orta Sehpa", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "konsol", ad: "Konsol", birim: "sabit", kaynak_tipi: "gercek" },

  { id: "supurge", ad: "Robot Süpürge", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "dikey-supurge", ad: "Dikey Süpürge", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "airfryer", ad: "Airfryer", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "kahve-makinesi", ad: "Kahve Makinesi", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "su-isitici", ad: "Su Isıtıcı (Kettle)", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "tost-makinesi", ad: "Tost Makinesi", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "blender", ad: "Blender", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "mutfak-robotu", ad: "Mutfak Robotu (Doğrayıcı)", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "utu", ad: "Ütü", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "sac-kurutma-makinesi", ad: "Saç Kurutma Makinesi", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "televizyon", ad: "Televizyon (4K)", birim: "sabit", kaynak_tipi: "gercek" },

  { id: "perde", ad: "Perde", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "aydinlatma", ad: "Aydınlatma (Avize)", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "nevresim-takimi", ad: "Nevresim Takımı", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "tencere-seti", ad: "Tencere Seti", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "tava-seti", ad: "Tava Seti", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "catal-kasik-bicak-takimi", ad: "Çatal-Kaşık-Bıçak Takımı", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "yemek-takimi", ad: "Yemek Takımı", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "kahvalti-takimi", ad: "Kahvaltı Takımı", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "bardak-takimi", ad: "Bardak Takımı", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "havlu-takimi", ad: "Havlu Takımı", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "bornoz", ad: "Bornoz", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "hali", ad: "Halı", birim: "sabit", kaynak_tipi: "gercek" },
];
