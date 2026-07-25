const test = require("node:test");
const assert = require("node:assert/strict");
const { hesapla, kalemSatiriHesapla } = require("../hesapla.js");

const GELINLIK_TANIMI = { id: "gelinlik", ad: "Gelinlik", birim: "sabit", kaynak_tipi: "gercek" };
const SALON_TANIMI = { id: "salon", ad: "Düğün Salonu", birim: "kisi_basi", kaynak_tipi: "gercek" };
const TAHMINI_TANIMI = {
  id: "fotografci", ad: "Fotoğraf ve Video", birim: "sabit", kaynak_tipi: "tahmini",
  tahmini: { dusuk: 20000, orta: 45000, luks: 100000 },
  kaynak_notu: "test notu", arastirma_tarihi: "2026-07-24",
};
const TAHMINI_KISI_BASI_TANIMI = {
  id: "yemek-ikram", ad: "Yemek", birim: "kisi_basi", kaynak_tipi: "tahmini",
  tahmini: { dusuk: 400, orta: 700, luks: 2000 },
  kaynak_notu: "test notu", arastirma_tarihi: "2026-07-24",
};

const GELINLIK_VERISI = {
  genel_medyan: 5000,
  kaynak_sayisi: 2,
  guncelleme_tarihi: "2026-07-24",
  capraz_dogrulama_uyarisi: null,
  segmentler: {
    dusuk: { min: 2000, medyan: 3000, max: 4000, urun_sayisi: 10 },
    orta: { min: 4001, medyan: 5000, max: 7000, urun_sayisi: 12 },
    luks: { min: 7001, medyan: 15000, max: 30000, urun_sayisi: 5 },
  },
};

const SALON_VERISI = {
  genel_medyan: 800,
  kaynak_sayisi: 1,
  guncelleme_tarihi: "2026-07-24",
  capraz_dogrulama_uyarisi: null,
  segmentler: {
    dusuk: { min: 400, medyan: 500, max: 600, urun_sayisi: 3 },
    orta: { min: 601, medyan: 800, max: 1200, urun_sayisi: 4 },
  },
};

test("veri yoksa veri_var false doner, toplama katilmaz", () => {
  const satir = kalemSatiriHesapla(GELINLIK_TANIMI, null, "orta", 100);
  assert.equal(satir.veri_var, false);
});

test("sabit kalem: davetli sayisindan bagimsiz, segment medyanini kullanir", () => {
  const satir = kalemSatiriHesapla(GELINLIK_TANIMI, GELINLIK_VERISI, "orta", 500);
  assert.equal(satir.veri_var, true);
  assert.equal(satir.birim_fiyat, 5000);
  assert.equal(satir.satir_toplam, 5000);
  assert.equal(satir.genel_medyana_dusuldu, false);
});

test("ekonomik segment -> dusuk anahtarina esler", () => {
  const satir = kalemSatiriHesapla(GELINLIK_TANIMI, GELINLIK_VERISI, "ekonomik", 500);
  assert.equal(satir.birim_fiyat, 3000);
});

test("luks segment -> luks anahtarina esler", () => {
  const satir = kalemSatiriHesapla(GELINLIK_TANIMI, GELINLIK_VERISI, "luks", 500);
  assert.equal(satir.birim_fiyat, 15000);
});

test("segment verisi yoksa genel medyana duser ve isaretlenir", () => {
  const veri = { genel_medyan: 999, segmentler: {} };
  const satir = kalemSatiriHesapla(GELINLIK_TANIMI, veri, "luks", 500);
  assert.equal(satir.birim_fiyat, 999);
  assert.equal(satir.genel_medyana_dusuldu, true);
});

test("kisi basi kalem: davetli sayisiyla carpilir", () => {
  const satir = kalemSatiriHesapla(SALON_TANIMI, SALON_VERISI, "orta", 200);
  assert.equal(satir.birim_fiyat, 800);
  assert.equal(satir.satir_toplam, 160000);
});

test("davetli sayisi 0 veya negatifse carpan 0 kabul edilir", () => {
  const satir = kalemSatiriHesapla(SALON_TANIMI, SALON_VERISI, "orta", -5);
  assert.equal(satir.satir_toplam, 0);
});

test("hesapla: secilen kalemlerin toplamini dogru verir", () => {
  const veriKalemleri = { gelinlik: GELINLIK_VERISI, salon: SALON_VERISI };
  const sonuc = hesapla(
    veriKalemleri,
    [GELINLIK_TANIMI, SALON_TANIMI],
    ["gelinlik", "salon"],
    "orta",
    100
  );
  // gelinlik: 5000 (sabit) + salon: 800*100=80000 -> toplam 85000
  assert.equal(sonuc.toplam, 85000);
  assert.equal(sonuc.detaylar.length, 2);
});

test("hesapla: secilmeyen kalem detaylarda gorunmez", () => {
  const veriKalemleri = { gelinlik: GELINLIK_VERISI, salon: SALON_VERISI };
  const sonuc = hesapla(veriKalemleri, [GELINLIK_TANIMI, SALON_TANIMI], ["gelinlik"], "orta", 100);
  assert.equal(sonuc.detaylar.length, 1);
  assert.equal(sonuc.toplam, 5000);
});

test("hesapla: veri_var false olan kalem toplama eklenmez ama detayda gorunur", () => {
  const sonuc = hesapla({}, [GELINLIK_TANIMI], ["gelinlik"], "orta", 100);
  assert.equal(sonuc.toplam, 0);
  assert.equal(sonuc.detaylar[0].veri_var, false);
});

test("tahmini kalem: kalemVerisi olmadan (null) dogrudan tahmini degerini kullanir", () => {
  const satir = kalemSatiriHesapla(TAHMINI_TANIMI, null, "orta", 100);
  assert.equal(satir.veri_var, true);
  assert.equal(satir.tahmini_mi, true);
  assert.equal(satir.birim_fiyat, 45000);
  assert.equal(satir.satir_toplam, 45000);
  assert.equal(satir.kaynak_notu, "test notu");
});

test("tahmini kalem: segmente gore dogru degeri secer", () => {
  assert.equal(kalemSatiriHesapla(TAHMINI_TANIMI, null, "ekonomik", 100).birim_fiyat, 20000);
  assert.equal(kalemSatiriHesapla(TAHMINI_TANIMI, null, "luks", 100).birim_fiyat, 100000);
});

test("tahmini kalem: kisi basi ise davetli sayisiyla carpilir", () => {
  const satir = kalemSatiriHesapla(TAHMINI_KISI_BASI_TANIMI, null, "orta", 150);
  assert.equal(satir.birim_fiyat, 700);
  assert.equal(satir.satir_toplam, 105000);
});

test("gercek kalem tahmini_mi false olarak isaretlenir", () => {
  const satir = kalemSatiriHesapla(GELINLIK_TANIMI, GELINLIK_VERISI, "orta", 100);
  assert.equal(satir.tahmini_mi, false);
});

test("hesapla: tahmini ve gercek kalemler birlikte dogru toplanir", () => {
  const sonuc = hesapla({ gelinlik: GELINLIK_VERISI }, [GELINLIK_TANIMI, TAHMINI_TANIMI], ["gelinlik", "fotografci"], "orta", 100);
  assert.equal(sonuc.toplam, 5000 + 45000);
  assert.equal(sonuc.detaylar.find((d) => d.id === "fotografci").tahmini_mi, true);
});

// ---- Salon varyantlari ve CIFT SAYIM korumasi ----
// Salon iki tanimli varyant halinde gelir: yemekli (menu dahil kisi basi)
// ve kokteyl (yemeksiz). Yemekli secilirken ayrica yemek/ikram eklenirse
// ayni yemek IKI KEZ sayilir - hesaplayicinin bunu yapmadigini kilitler.
const SALON_YEMEKLI_TANIMI = {
  id: "salon-yemekli", ad: "Düğün Salonu — yemekli", birim: "kisi_basi",
  kaynak_tipi: "gercek", secim_grubu: "salon", yemek_dahil: true,
  varsayilan_dahil: true,
};
const SALON_KOKTEYL_TANIMI = {
  id: "salon-kokteyl", ad: "Düğün Salonu — kokteyl", birim: "kisi_basi",
  kaynak_tipi: "gercek", secim_grubu: "salon", yemek_dahil: false,
  varsayilan_dahil: false,
};
const SALON_VERILERI = {
  "salon-yemekli": {
    genel_medyan: 1300, kaynak_sayisi: 1,
    segmentler: { orta: { min: 1000, medyan: 1300, max: 1500, urun_sayisi: 6 } },
  },
  "salon-kokteyl": {
    genel_medyan: 800, kaynak_sayisi: 1,
    segmentler: { orta: { min: 280, medyan: 800, max: 990, urun_sayisi: 5 } },
  },
};
const YEMEK_TANIMI = {
  id: "yemek-ikram", ad: "Yemek / İkram", birim: "kisi_basi",
  kaynak_tipi: "tahmini", tahmini: { dusuk: 400, orta: 700, luks: 2000 },
  kaynak_notu: "n", arastirma_tarihi: "2026-07-24",
  yemek_kalemi: true, varsayilan_dahil: false,
};
const SALON_TANIMLARI = [SALON_YEMEKLI_TANIMI, SALON_KOKTEYL_TANIMI, YEMEK_TANIMI];

test("yemekli salon secilirse yemek kalemi toplama GIRMEZ (cift sayim korumasi)", () => {
  // Hesaplayici UI'i yemekli secilince yemek kutusunu devre disi birakir,
  // yani secilenIdler'e "yemek-ikram" HIC gelmez.
  const sonuc = hesapla(SALON_VERILERI, SALON_TANIMLARI, ["salon-yemekli"], "orta", 150);
  assert.equal(sonuc.toplam, 1300 * 150);
  assert.equal(sonuc.detaylar.length, 1);
  assert.equal(sonuc.detaylar[0].id, "salon-yemekli");
});

test("kokteyl salon secilirse yemek kalemi AYRICA eklenir", () => {
  const sonuc = hesapla(SALON_VERILERI, SALON_TANIMLARI, ["salon-kokteyl", "yemek-ikram"], "orta", 150);
  assert.equal(sonuc.toplam, 800 * 150 + 700 * 150);
});

test("iki salon varyanti asla ayni anda toplanmaz (radyo davranisi)", () => {
  // Radyo grubu UI seviyesinde garanti eder; burada ikisinin AYRI AYRI
  // farkli sonuc verdigini ve toplamin karismadigini kilitliyoruz.
  const yemekli = hesapla(SALON_VERILERI, SALON_TANIMLARI, ["salon-yemekli"], "orta", 100);
  const kokteyl = hesapla(SALON_VERILERI, SALON_TANIMLARI, ["salon-kokteyl"], "orta", 100);
  assert.equal(yemekli.toplam, 130000);
  assert.equal(kokteyl.toplam, 80000);
  assert.notEqual(yemekli.toplam, kokteyl.toplam);
});

test("yemekli salon, kokteyl + yemek toplamindan farkli olmali (gercek veriyi yansitir)", () => {
  // Gercek DugunBuketi verisi: yemekli medyan 1300, kokteyl 800.
  // Bu iki senaryo esit DEGIL - "kokteyl + tahmini yemek" bir tahmindir,
  // "yemekli" ise dogrudan olculmus tanimli fiyattir.
  const yemekli = hesapla(SALON_VERILERI, SALON_TANIMLARI, ["salon-yemekli"], "orta", 150).toplam;
  const kokteylArtiYemek = hesapla(SALON_VERILERI, SALON_TANIMLARI, ["salon-kokteyl", "yemek-ikram"], "orta", 150).toplam;
  assert.equal(yemekli, 195000);
  assert.equal(kokteylArtiYemek, 225000);
});
