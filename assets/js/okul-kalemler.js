// Okul vertikali kalem tanimlari - hesaplayici ve endeks sayfasi kullanir.
// Yapi ev-kurma ile ayni; tek fark bazi kalemlerin varsayilan olarak
// KAPALI gelmesi.
//
// varsayilan_dahil: false -> tablet, calisma masasi ve sandalyesi HER YIL
// alinmaz, bir kez alinip yillarca kullanilir. "Yillik okul masrafi"
// sorusuna cevap veren toplam bunlari icermez; isteyen hesaplayicidan
// ekler. Aksi halde tek seferlik harcamalar yillik masrafmis gibi
// gorunur ve rakam yaniltici cikar.

const OKUL_KALEMLERI = [
  { id: "okul-cantasi", ad: "Okul Çantası", birim: "sabit", kaynak_tipi: "gercek", grup: "Çanta ve beslenme" },
  { id: "beslenme-cantasi", ad: "Beslenme Çantası", birim: "sabit", kaynak_tipi: "gercek", grup: "Çanta ve beslenme" },
  { id: "matara", ad: "Suluk / Matara", birim: "sabit", kaynak_tipi: "gercek", grup: "Çanta ve beslenme" },
  { id: "kalem-kutusu", ad: "Kalem Kutusu", birim: "sabit", kaynak_tipi: "gercek", grup: "Kırtasiye" },
  { id: "defter", ad: "Defter", birim: "sabit", kaynak_tipi: "gercek", grup: "Kırtasiye" },
  { id: "kalem", ad: "Kalem", birim: "sabit", kaynak_tipi: "gercek", grup: "Kırtasiye" },
  { id: "boya-seti", ad: "Boya Seti", birim: "sabit", kaynak_tipi: "gercek", grup: "Kırtasiye" },
  { id: "resim-malzemeleri", ad: "Resim ve Sanat Malzemeleri", birim: "sabit", kaynak_tipi: "gercek", grup: "Kırtasiye" },
  { id: "ders-kitabi", ad: "Ders ve Yardımcı Kitap", birim: "sabit", kaynak_tipi: "gercek", grup: "Kitap" },
  { id: "sozluk", ad: "Sözlük", birim: "sabit", kaynak_tipi: "gercek", grup: "Kitap" },
  { id: "ayakkabi", ad: "Spor Ayakkabı", birim: "sabit", kaynak_tipi: "gercek", grup: "Giyim" },
  { id: "tablet", ad: "Tablet", birim: "sabit", kaynak_tipi: "gercek", grup: "Teknoloji", varsayilan_dahil: false },
  { id: "calisma-masasi", ad: "Çalışma Masası", birim: "sabit", kaynak_tipi: "gercek", grup: "Çalışma alanı", varsayilan_dahil: false },
  { id: "calisma-sandalyesi", ad: "Çalışma Sandalyesi", birim: "sabit", kaynak_tipi: "gercek", grup: "Çalışma alanı", varsayilan_dahil: false },
];

if (typeof module !== "undefined" && module.exports) {
  module.exports = { OKUL_KALEMLERI };
}
