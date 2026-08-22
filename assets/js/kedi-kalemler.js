// Kedi vertikali kalem tanimlari.
//
// `varsayilan_dahil: false` -> mama ve kum. Olcum paket fiyatidir;
// gramaj ve tuketim normalize edilmeden aylik gider diye toplanamaz.
const KEDI_KALEMLERI = [
  { id: "kedi-tuvaleti", ad: "Kedi Tuvaleti", birim: "sabit", kaynak_tipi: "gercek", grup: "Tuvalet" },
  { id: "tasima-cantasi", ad: "Taşıma Çantası", birim: "sabit", kaynak_tipi: "gercek", grup: "Taşıma" },
  { id: "tirmalama", ad: "Tırmalama Tahtası", birim: "sabit", kaynak_tipi: "gercek", grup: "Yaşam alanı" },
  { id: "kedi-yatagi", ad: "Kedi Yatağı", birim: "sabit", kaynak_tipi: "gercek", grup: "Yaşam alanı" },
  { id: "mama-su-kabi", ad: "Mama ve Su Kabı", birim: "sabit", kaynak_tipi: "gercek", grup: "Beslenme" },
  { id: "kedi-oyuncagi", ad: "Kedi Oyuncağı", birim: "sabit", kaynak_tipi: "gercek", grup: "Yaşam alanı" },
  { id: "kedi-mamasi", ad: "Kedi Maması (paket)", birim: "sabit", olcum_turu: "paket_fiyati", kaynak_tipi: "gercek", grup: "Tekrarlayan ürün", varsayilan_dahil: false },
  { id: "kedi-kumu", ad: "Kedi Kumu (paket)", birim: "sabit", olcum_turu: "paket_fiyati", kaynak_tipi: "gercek", grup: "Tekrarlayan ürün", varsayilan_dahil: false },
];

if (typeof module !== "undefined" && module.exports) {
  module.exports = { KEDI_KALEMLERI };
}
