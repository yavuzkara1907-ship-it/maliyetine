// Ev kurma vertikali kalem tanimlari - hem hesaplayici hem endeks sayfasi
// bu listeyi kullanir. scraper/sayfa_uret.py'deki EV_KURMA_KALEMLERI ile
// ayni liste (kasitli kucuk tekrar, bkz. o dosyadaki not).
//
// Dugun'den farkli olarak burada HIC "tahmini" kalem YOK - 42 kalemin
// tamami motor.py ile gercekten kazinan, tarihli/orneklemli kaynaklardan
// geliyor. Kalemler tamamen urun bazli oldugu icin bu mumkun oldu.

const EV_KURMA_KALEMLERI = [
  // Beyaz eşya
  { id: "buzdolabi", ad: "Buzdolabı", birim: "sabit", grup: "Beyaz eşya", kaynak_tipi: "gercek" },
  { id: "camasir-makinesi", ad: "Çamaşır Makinesi", birim: "sabit", grup: "Beyaz eşya", kaynak_tipi: "gercek" },
  { id: "kurutma-makinesi", ad: "Kurutma Makinesi", birim: "sabit", grup: "Beyaz eşya", kaynak_tipi: "gercek" },
  { id: "bulasik-makinesi", ad: "Bulaşık Makinesi", birim: "sabit", grup: "Beyaz eşya", kaynak_tipi: "gercek" },
  { id: "firin-ocak", ad: "Fırın / Ocak (ürün tipine göre)", birim: "sabit", grup: "Beyaz eşya", kaynak_tipi: "gercek", varsayilan_dahil: false },
  { id: "davlumbaz", ad: "Davlumbaz", birim: "sabit", grup: "Beyaz eşya", kaynak_tipi: "gercek" },
  { id: "mikrodalga", ad: "Mikrodalga Fırın", birim: "sabit", grup: "Beyaz eşya", kaynak_tipi: "gercek" },
  { id: "klima", ad: "Klima", birim: "sabit", grup: "Beyaz eşya", kaynak_tipi: "gercek" },

  // Mobilya
  { id: "koltuk-takimi", ad: "Koltuk Takımı", birim: "sabit", grup: "Mobilya", kaynak_tipi: "gercek" },
  { id: "yemek-masasi", ad: "Yemek Odası Takımı", birim: "sabit", grup: "Mobilya", kaynak_tipi: "gercek" },
  { id: "tv-unitesi", ad: "TV Ünitesi", birim: "sabit", grup: "Mobilya", kaynak_tipi: "gercek" },
  { id: "sehpa", ad: "Orta Sehpa", birim: "sabit", grup: "Mobilya", kaynak_tipi: "gercek" },
  { id: "konsol", ad: "Konsol", birim: "sabit", grup: "Mobilya", kaynak_tipi: "gercek" },

  // Yatak odası
  { id: "yatak", ad: "Çift Kişilik Yatak", birim: "sabit", grup: "Yatak odası", kaynak_tipi: "gercek" },
  { id: "karyola", ad: "Karyola / Baza", birim: "sabit", grup: "Yatak odası", kaynak_tipi: "gercek" },
  { id: "gardirop", ad: "Gardırop", birim: "sabit", grup: "Yatak odası", kaynak_tipi: "gercek" },
  { id: "komodin", ad: "Komodin", birim: "sabit", grup: "Yatak odası", kaynak_tipi: "gercek" },
  { id: "sifonyer", ad: "Şifonyer", birim: "sabit", grup: "Yatak odası", kaynak_tipi: "gercek" },
  { id: "boy-aynasi", ad: "Boy Aynası", birim: "sabit", grup: "Yatak odası", kaynak_tipi: "gercek" },

  // Elektronik
  { id: "televizyon", ad: "Televizyon (4K)", birim: "sabit", grup: "Elektronik", kaynak_tipi: "gercek" },
  { id: "supurge", ad: "Robot Süpürge", birim: "sabit", grup: "Elektronik", kaynak_tipi: "gercek" },
  { id: "dikey-supurge", ad: "Dikey Süpürge", birim: "sabit", grup: "Elektronik", kaynak_tipi: "gercek" },

  // Küçük ev aleti
  { id: "airfryer", ad: "Airfryer", birim: "sabit", grup: "Küçük ev aleti", kaynak_tipi: "gercek" },
  { id: "kahve-makinesi", ad: "Kahve Makinesi", birim: "sabit", grup: "Küçük ev aleti", kaynak_tipi: "gercek" },
  { id: "su-isitici", ad: "Su Isıtıcı (Kettle)", birim: "sabit", grup: "Küçük ev aleti", kaynak_tipi: "gercek" },
  { id: "tost-makinesi", ad: "Tost Makinesi", birim: "sabit", grup: "Küçük ev aleti", kaynak_tipi: "gercek" },
  { id: "blender", ad: "Blender", birim: "sabit", grup: "Küçük ev aleti", kaynak_tipi: "gercek" },
  { id: "mutfak-robotu", ad: "Mutfak Robotu / Doğrayıcı", birim: "sabit", grup: "Küçük ev aleti", kaynak_tipi: "gercek" },
  { id: "utu", ad: "Ütü", birim: "sabit", grup: "Küçük ev aleti", kaynak_tipi: "gercek" },
  { id: "sac-kurutma-makinesi", ad: "Saç Kurutma Makinesi", birim: "sabit", grup: "Küçük ev aleti", kaynak_tipi: "gercek" },

  // Mutfak
  { id: "tencere-seti", ad: "Tencere Seti", birim: "sabit", grup: "Mutfak", kaynak_tipi: "gercek" },
  { id: "tava-seti", ad: "Tava Seti", birim: "sabit", grup: "Mutfak", kaynak_tipi: "gercek" },
  { id: "catal-kasik-bicak-takimi", ad: "Çatal-Kaşık-Bıçak Takımı", birim: "sabit", grup: "Mutfak", kaynak_tipi: "gercek" },
  { id: "yemek-takimi", ad: "Yemek Takımı", birim: "sabit", grup: "Mutfak", kaynak_tipi: "gercek" },
  { id: "kahvalti-takimi", ad: "Kahvaltı Takımı", birim: "sabit", grup: "Mutfak", kaynak_tipi: "gercek" },
  { id: "bardak-takimi", ad: "Bardak Takımı", birim: "sabit", grup: "Mutfak", kaynak_tipi: "gercek" },

  // Tekstil
  { id: "nevresim-takimi", ad: "Nevresim Takımı", birim: "sabit", grup: "Tekstil", kaynak_tipi: "gercek" },
  { id: "havlu-takimi", ad: "Havlu Takımı", birim: "sabit", grup: "Tekstil", kaynak_tipi: "gercek" },
  { id: "bornoz", ad: "Bornoz", birim: "sabit", grup: "Tekstil", kaynak_tipi: "gercek" },
  { id: "perde", ad: "Perde", birim: "sabit", grup: "Tekstil", kaynak_tipi: "gercek" },
  { id: "hali", ad: "Halı", birim: "sabit", grup: "Tekstil", kaynak_tipi: "gercek" },
  { id: "aydinlatma", ad: "Avize / Aydınlatma", birim: "sabit", grup: "Tekstil", kaynak_tipi: "gercek" },
];

if (typeof module === "object" && module.exports) {
  module.exports = EV_KURMA_KALEMLERI;
}
