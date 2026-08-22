// Kopek vertikali kalem tanimlari.
const KOPEK_KALEMLERI = [
  { id: "kopek-tasmasi", ad: "Köpek Tasması", birim: "sabit", kaynak_tipi: "gercek", grup: "Gezdirme" },
  { id: "kopek-tasima", ad: "Taşıma Çantası / Kafes", birim: "sabit", kaynak_tipi: "gercek", grup: "Gezdirme" },
  { id: "kopek-yatagi", ad: "Köpek Yatağı", birim: "sabit", kaynak_tipi: "gercek", grup: "Yaşam alanı" },
  { id: "kopek-oyuncagi", ad: "Köpek Oyuncağı", birim: "sabit", kaynak_tipi: "gercek", grup: "Yaşam alanı" },
  { id: "kopek-mama-kabi", ad: "Köpek Mama ve Su Kabı", birim: "sabit", kaynak_tipi: "gercek", grup: "Beslenme" },
  { id: "kopek-mamasi", ad: "Köpek Maması (paket)", birim: "sabit", olcum_turu: "paket_fiyati", kaynak_tipi: "gercek", grup: "Tekrarlayan ürün", varsayilan_dahil: false },
  { id: "cis-pedi", ad: "Çiş Pedi (paket)", birim: "sabit", olcum_turu: "paket_fiyati", kaynak_tipi: "gercek", grup: "Tekrarlayan ürün", varsayilan_dahil: false },
];

if (typeof module !== "undefined" && module.exports) {
  module.exports = { KOPEK_KALEMLERI };
}
