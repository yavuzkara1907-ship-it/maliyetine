// Dugun vertikali kalem tanimlari - hem hesaplayici hem endeks sayfasi
// bu listeyi kullanir.
//
// kaynak_tipi: "gercek" | "tahmini"
//   "gercek"   -> /veri/dugun.json'dan (motor.py ile kazinan, kaynak/tarih/
//                 orneklem bilgisiyle) gercek fiyat cekilir.
//   "tahmini"  -> henuz kazima kaynagi yok. Yavuz'un acik talimatiyla
//                 (2026-07-24) genel piyasa arastirmasindan (WebSearch,
//                 birden fazla ilan/fiyat sitesi) turetilmis TEK SEFERLIK
//                 bir tahmini deger kullaniliyor - motor.py'nin surekli
//                 kazidigi, tarihli/orneklemli "gercek kaynak" ile AYNI
//                 SEYIN degil. UI'da HER ZAMAN ayri "Tahmini" etiketiyle
//                 gosterilir, /dugun/metodoloji/'de bu ayrim aciklanir.
//                 arastirma_tarihi: WebSearch'in yapildigi tarih - bu
//                 rakamlar motor.py gibi otomatik guncellenmiyor, elle
//                 tekrar arastirilip gozden gecirilmedikce SABIT kalir.

const DUGUN_KALEMLERI = [
  { id: "gelinlik", ad: "Gelinlik", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "damatlik", ad: "Damatlık / Takım Elbise", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "alyans", ad: "Alyans", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "gelin-ayakkabisi", ad: "Gelin Ayakkabısı, Duvak, Aksesuar", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "nikah-sekeri", ad: "Nikah Şekeri", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "davetiye", ad: "Davetiye", birim: "sabit", kaynak_tipi: "gercek" },
  { id: "salon", ad: "Düğün Salonu", birim: "kisi_basi", kaynak_tipi: "gercek" },

  {
    id: "taki-altin", ad: "Takı ve Altın", birim: "sabit", kaynak_tipi: "tahmini",
    tahmini: { dusuk: 15000, orta: 40000, luks: 90000 },
    kaynak_notu: "Gram altın ~6.140 TL (24 Temmuz 2026) baz alınarak tipik hediye takı seti bütçesi.",
    arastirma_tarihi: "2026-07-24",
  },
  {
    id: "yemek-ikram", ad: "Yemek / İkram (salona dahil değilse)", birim: "kisi_basi", kaynak_tipi: "tahmini",
    tahmini: { dusuk: 400, orta: 700, luks: 2000 },
    kaynak_notu: "Kişi başı düğün catering fiyat araştırması (açık büfe – tabldot – premium menü).",
    arastirma_tarihi: "2026-07-24",
  },
  {
    id: "fotografci", ad: "Fotoğraf ve Video", birim: "sabit", kaynak_tipi: "tahmini",
    tahmini: { dusuk: 20000, orta: 45000, luks: 100000 },
    kaynak_notu: "Düğün fotoğraf/video paket fiyat araştırması (temel – standart – premium paket).",
    arastirma_tarihi: "2026-07-24",
  },
  {
    id: "orkestra-dj", ad: "Orkestra / DJ", birim: "sabit", kaynak_tipi: "tahmini",
    tahmini: { dusuk: 5000, orta: 25000, luks: 80000 },
    kaynak_notu: "Düğün orkestra/DJ kiralama fiyat araştırması (başlangıç – paket – tanınmış sanatçı).",
    arastirma_tarihi: "2026-07-24",
  },
  {
    id: "gelin-arabasi", ad: "Gelin Arabası", birim: "sabit", kaynak_tipi: "tahmini",
    tahmini: { dusuk: 800, orta: 3000, luks: 8000 },
    kaynak_notu: "Gelin arabası kiralama fiyat araştırması.",
    arastirma_tarihi: "2026-07-24",
  },
  {
    id: "kuafor-makyaj", ad: "Kuaför ve Makyaj", birim: "sabit", kaynak_tipi: "tahmini",
    tahmini: { dusuk: 1000, orta: 5000, luks: 15000 },
    kaynak_notu: "Gelin saçı ve makyajı fiyat araştırması.",
    arastirma_tarihi: "2026-07-24",
  },
  {
    id: "organizasyon", ad: "Organizasyon / Süsleme", birim: "sabit", kaynak_tipi: "tahmini",
    tahmini: { dusuk: 15000, orta: 40000, luks: 150000 },
    kaynak_notu: "Düğün organizasyon/dekorasyon fiyat araştırması.",
    arastirma_tarihi: "2026-07-24",
  },
  {
    id: "nikah-islemleri", ad: "Nikah İşlemleri (resmi harçlar)", birim: "sabit", kaynak_tipi: "tahmini",
    tahmini: { dusuk: 1500, orta: 3500, luks: 8000 },
    kaynak_notu: "Belediye nikah/evlendirme dairesi harç ücreti araştırması (2026 tarifeleri).",
    arastirma_tarihi: "2026-07-24",
  },
];

// Balayi CLAUDE.md'de ayri gosterilecek denmis (tatil vertikaliyle veri
// paylasacak) - hesaplayici toplamina hic dahil edilmiyor, ayri bolum.
const DUGUN_BALAYI = { id: "balayi", ad: "Balayı" };

const SEGMENT_ETIKETLERI = { dusuk: "Ekonomik", orta: "Orta", luks: "Lüks" };
