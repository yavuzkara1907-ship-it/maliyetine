const test = require("node:test");
const assert = require("node:assert/strict");
const { hesapla, kalemSatiriHesapla } = require("../dugun-hesapla.js");

const GELINLIK_TANIMI = { id: "gelinlik", ad: "Gelinlik", birim: "sabit" };
const SALON_TANIMI = { id: "salon", ad: "Düğün Salonu", birim: "kisi_basi" };

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
