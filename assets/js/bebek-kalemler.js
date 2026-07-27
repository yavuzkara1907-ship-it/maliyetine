// Bebek vertikali kalem tanimlari.
//
// varsayilan_dahil: false -> bebek bezi. Bez SARF malzemesi, aylik
// tekrarliyor; digerleri tek seferlik kurulum. Ikisini tek toplama
// katmak ne oldugu belirsiz bir rakam uretirdi.

const BEBEK_KALEMLERI = [
  { id: "bebek-arabasi", ad: "Bebek Arabası", birim: "sabit", kaynak_tipi: "gercek", grup: "Uyku ve taşıma" },
  { id: "besik", ad: "Beşik", birim: "sabit", kaynak_tipi: "gercek", grup: "Uyku ve taşıma" },
  { id: "park-yatak", ad: "Park Yatak / Oyun Parkı", birim: "sabit", kaynak_tipi: "gercek", grup: "Uyku ve taşıma" },
  { id: "oto-koltugu", ad: "Oto Koltuğu", birim: "sabit", kaynak_tipi: "gercek", grup: "Uyku ve taşıma" },
  { id: "mama-sandalyesi", ad: "Mama Sandalyesi", birim: "sabit", kaynak_tipi: "gercek", grup: "Beslenme" },
  { id: "biberon-seti", ad: "Biberon Seti", birim: "sabit", kaynak_tipi: "gercek", grup: "Beslenme" },
  { id: "gogus-pompasi", ad: "Göğüs Pompası", birim: "sabit", kaynak_tipi: "gercek", grup: "Beslenme" },
  { id: "bebek-kuveti", ad: "Bebek Küveti", birim: "sabit", kaynak_tipi: "gercek", grup: "Bakım" },
  { id: "zibin-seti", ad: "Zıbın / Body Seti", birim: "sabit", kaynak_tipi: "gercek", grup: "Tekstil" },
  { id: "uyku-tulumu", ad: "Uyku Tulumu", birim: "sabit", kaynak_tipi: "gercek", grup: "Tekstil" },
  { id: "bebek-bezi", ad: "Bebek Bezi (aylık)", birim: "sabit", kaynak_tipi: "gercek", grup: "Aylık sarf", varsayilan_dahil: false },
];

if (typeof module !== "undefined" && module.exports) {
  module.exports = { BEBEK_KALEMLERI };
}
