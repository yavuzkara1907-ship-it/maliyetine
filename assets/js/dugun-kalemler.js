// Dugun vertikali kalem tanimlari - hem hesaplayici hem endeks sayfasi
// bu listeyi kullanir. "veri_var: true" olanlar /veri/dugun.json'dan
// gercek fiyat cekiyor; "veri_var: false" olanlar icin BILEREK sabit bir
// fiyat KOYULMUYOR (CLAUDE.md KIRMIZI CIZGI: fiyat verisi asla LLM'den
// uretilmez) - bunlar "veri henuz yok" olarak gosterilip toplama dahil
// EDILMIYOR, kaynak bulununca eklenecek.

const DUGUN_KALEMLERI = [
  { id: "gelinlik", ad: "Gelinlik", birim: "sabit", veri_var: true },
  { id: "damatlik", ad: "Damatlık / Takım Elbise", birim: "sabit", veri_var: true },
  { id: "alyans", ad: "Alyans", birim: "sabit", veri_var: true },
  { id: "gelin-ayakkabisi", ad: "Gelin Ayakkabısı, Duvak, Aksesuar", birim: "sabit", veri_var: true },
  { id: "nikah-sekeri", ad: "Nikah Şekeri", birim: "sabit", veri_var: true },
  { id: "davetiye", ad: "Davetiye", birim: "sabit", veri_var: true },
  { id: "salon", ad: "Düğün Salonu", birim: "kisi_basi", veri_var: true },
];

// Henuz kazima kaynagi bulunamamis kalemler (CLAUDE.md'deki tam listeden).
// Sayfada gosterilir ama toplama KATILMAZ - fiyat uydurulmaz.
const DUGUN_KALEMLERI_VERISIZ = [
  { id: "taki-altin", ad: "Takı ve Altın" },
  { id: "yemek-ikram", ad: "Yemek / İkram (salona dahil değilse)" },
  { id: "fotografci", ad: "Fotoğraf ve Video" },
  { id: "orkestra-dj", ad: "Orkestra / DJ" },
  { id: "gelin-arabasi", ad: "Gelin Arabası" },
  { id: "kuafor-makyaj", ad: "Kuaför ve Makyaj" },
  { id: "organizasyon", ad: "Organizasyon / Süsleme" },
  { id: "nikah-islemleri", ad: "Nikah İşlemleri (resmi harçlar)" },
];

// Balayi CLAUDE.md'de ayri gosterilecek denmis (tatil vertikaliyle veri
// paylasacak) - hesaplayici toplamina hic dahil edilmiyor, ayri bolum.
const DUGUN_BALAYI = { id: "balayi", ad: "Balayı" };

const SEGMENT_ETIKETLERI = { dusuk: "Ekonomik", orta: "Orta", luks: "Lüks" };
