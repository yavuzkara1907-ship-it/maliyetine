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
  // 2026-07-25: TAHMINI -> GERCEK kaynak (Atasay altin bilezik, 24 urun).
  // Onceki tahmin orta 40.000 TL, gercek olcum ~81.000 - tahmin dusuktu.
  // Kalem adi daraltildi: toplam takilan altin olculemez, bir bilezigin
  // fiyati olculebilir.
  { id: "taki-altin", ad: "Takı — Altın Bilezik (1 adet)", birim: "sabit", kaynak_tipi: "gercek" },
  // Salon iki TANIMLI varyant halinde gelir (bkz. kaynaklar.yaml). Ayni
  // "secim_grubu" degerini paylasan kalemler hesaplayicida radyo gibi
  // davranir - biri secilir, digeri toplama girmez.
  //   yemek_dahil: true  -> menu dahil kisi basi fiyat. Bu secilince ayri
  //                         "yemek-ikram" kalemi CIFT SAYIM olur, otomatik
  //                         devre disi kalir.
  //   varsayilan_dahil   -> endeks sayfasinin ve hesaplayicinin acilis
  //                         senaryosunda toplama dahil mi. Tabloda her
  //                         iki varyant da fiyatiyla GORUNUR, sadece
  //                         toplama biri girer.
  {
    id: "salon-yemekli", ad: "Düğün Salonu — yemekli (menü dahil)",
    birim: "kisi_basi", kaynak_tipi: "gercek",
    secim_grubu: "salon", yemek_dahil: true, varsayilan_dahil: true,
  },
  {
    id: "salon-kokteyl", ad: "Düğün Salonu — kokteyl (yemeksiz)",
    birim: "kisi_basi", kaynak_tipi: "gercek",
    secim_grubu: "salon", yemek_dahil: false, varsayilan_dahil: false,
  },
  // 2026-07-25: TAHMINI listeden GERCEK kaynaga tasindi - deger artik
  // ayni mekanin yemekli/kokteyl fiyat farkindan OLCULUYOR (bkz.
  // kaynaklar.yaml fark modu). Onceki tahmin 700 TL/kisi idi, gercek
  // olcum 410 TL - 1.7 kat sapma.
  //
  // bilgi_amacli: TOPLAMA HIC GIRMEZ, hesaplayicida secim kutusu YOK.
  // Sebep: "kokteyl + menu bedeli" tanim geregi "yemekli" fiyatina esit
  // olmali (fark = yemekli - kokteyl), ayri kalem olarak toplamak ayni
  // sayiya dolambacli yoldan gitmek olur. Ustelik esitlik pratikte
  // bozuluyor: her kalem BAGIMSIZ segmentleniyor, "orta segment yemekli
  // mekan" ile "orta segment kokteyl mekan" ayni mekanlar degil (%24
  // tutarsizlik). Deger yalnizca REFERANS olarak gosterilir.
  {
    id: "yemek-ikram", ad: "Yemek / İkram (mekanın menü bedeli)",
    birim: "kisi_basi", kaynak_tipi: "gercek", bilgi_amacli: true,
  },
  // 2026-07-26: dort hizmet kalemi TAHMINI -> GERCEK kaynak (dugun.com il
  // bazli fiyat tablolari, Istanbul satiri). Tahminler ciddi sapmisti:
  // fotografci 45.000 -> 15.600 (3 kat yuksek), organizasyon 40.000 ->
  // 22.150, kuafor 5.000 -> 12.450 (2.5 kat dusuk), gelin arabasi
  // 3.000 -> 9.800 (3 kat dusuk). Sapmalar iki yonde de cikti.
  //
  // tek_deger: SEGMENT KIRILIMI YOK. Kaynak tek bir Istanbul rakami
  // veriyor; ekonomik/orta/ust secildiginde ayni deger kullanilir ve UI
  // bunu acikca yazar. 27 ilin tamamini alip persentille segmentlemedik
  // cunku cografi fark fiyat segmenti DEGILDIR - "ekonomik fotografci"
  // ucuz bir il demek olmaz.
  { id: "fotografci", ad: "Fotoğraf ve Video", birim: "sabit", kaynak_tipi: "gercek", tek_deger: true },
  { id: "organizasyon", ad: "Organizasyon / Süsleme", birim: "sabit", kaynak_tipi: "gercek", tek_deger: true },
  { id: "kuafor-makyaj", ad: "Kuaför ve Makyaj", birim: "sabit", kaynak_tipi: "gercek", tek_deger: true },
  { id: "gelin-arabasi", ad: "Gelin Arabası", birim: "sabit", kaynak_tipi: "gercek", tek_deger: true },

  {
    id: "orkestra-dj", ad: "Orkestra / DJ", birim: "sabit", kaynak_tipi: "tahmini",
    tahmini: { dusuk: 5000, orta: 25000, luks: 80000 },
    kaynak_notu: "Düğün orkestra/DJ kiralama fiyat araştırması (başlangıç – paket – tanınmış sanatçı).",
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

const SEGMENT_ETIKETLERI = { dusuk: "Ekonomik", orta: "Orta", luks: "Üst" };

if (typeof module !== "undefined" && module.exports) {
  module.exports = { DUGUN_KALEMLERI, DUGUN_BALAYI, SEGMENT_ETIKETLERI };
}
