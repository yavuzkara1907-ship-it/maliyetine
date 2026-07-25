const test = require("node:test");
const assert = require("node:assert");
const { ARAC_EK_MALIYETLER, aracEkMaliyetHesapla } = require("../arac-ek-maliyetler.js");

const HEPSI = ["mtv", "noter_tescil", "plaka_ruhsat", "trafik_sigortasi", "kasko"];

test("MTV motor hacmi kademesine gore secilir (resmi tarife)", () => {
  const kucuk = aracEkMaliyetHesapla(1000000, 1200, ["mtv"]);
  const orta = aracEkMaliyetHesapla(1000000, 1500, ["mtv"]);
  const buyuk = aracEkMaliyetHesapla(1000000, 1700, ["mtv"]);
  assert.equal(kucuk.detaylar[0].tutar, 6903);
  assert.equal(orta.detaylar[0].tutar, 12028);
  assert.equal(buyuk.detaylar[0].tutar, 21252);
});

test("kademe sinirlari dogru: 1300 kucuk, 1301 orta bandda", () => {
  assert.equal(aracEkMaliyetHesapla(1e6, 1300, ["mtv"]).detaylar[0].tutar, 6903);
  assert.equal(aracEkMaliyetHesapla(1e6, 1301, ["mtv"]).detaylar[0].tutar, 12028);
});

test("cok buyuk motor son kademeye duser (kademe disi kalmaz)", () => {
  const d = aracEkMaliyetHesapla(1e6, 5000, ["mtv"]).detaylar[0];
  assert.equal(d.tutar, 33000);
});

test("noter harci nispi: arac fiyatinin binde 2'si + sabit ucret", () => {
  const s = aracEkMaliyetHesapla(3000000, 1500, ["noter_tescil"]);
  // 3.000.000 * 0.002 = 6.000 (asgari 1.000'in ustunde) + 1.920 sabit
  assert.equal(s.detaylar[0].tutar, 7920);
});

test("noter harcinda ASGARI 1.000 TL tabani uygulanir", () => {
  // 200.000 * 0.002 = 400 -> asgari 1.000'e yukselir, + 1.920
  const s = aracEkMaliyetHesapla(200000, 1500, ["noter_tescil"]);
  assert.equal(s.detaylar[0].tutar, 2920);
});

test("kasko arac degerinin yuzdesi, asgari tabanli", () => {
  const pahali = aracEkMaliyetHesapla(3000000, 1500, ["kasko"]);
  assert.equal(pahali.detaylar[0].tutar, 90000); // 3M * 0.03
  const ucuz = aracEkMaliyetHesapla(200000, 1500, ["kasko"]);
  assert.equal(ucuz.detaylar[0].tutar, 12000); // asgari taban
});

test("resmi ve tahmini toplamlar AYRI raporlanir (KIRMIZI CIZGI)", () => {
  const s = aracEkMaliyetHesapla(2069000, 1500, HEPSI);
  // resmi = MTV + noter; tahmini = plaka + trafik + kasko
  const resmi = s.detaylar.filter((d) => d.kaynak_tipi === "resmi")
                          .reduce((t, d) => t + d.tutar, 0);
  const tahmini = s.detaylar.filter((d) => d.kaynak_tipi === "tahmini")
                            .reduce((t, d) => t + d.tutar, 0);
  assert.equal(s.resmiToplam, resmi);
  assert.equal(s.tahminiToplam, tahmini);
  assert.equal(s.resmiToplam + s.tahminiToplam, s.ekToplam);
});

test("genel toplam = arac fiyati + ek kalemler (aritmetik tutar)", () => {
  const fiyat = 2069000;
  const s = aracEkMaliyetHesapla(fiyat, 1500, HEPSI);
  assert.equal(s.genelToplam, fiyat + s.ekToplam);
  assert.equal(s.ekToplam, s.detaylar.reduce((t, d) => t + d.tutar, 0));
});

test("secilmeyen kalem hesaba GIRMEZ", () => {
  const s = aracEkMaliyetHesapla(2000000, 1500, ["mtv"]);
  assert.equal(s.detaylar.length, 1);
  assert.equal(s.ekToplam, 12028);      // yalnizca MTV (1301-1600 cc)
  assert.equal(s.tahminiToplam, 0);     // tahmini kalem secilmedi
});

test("hicbir kalem secilmezse ek maliyet sifir, toplam arac fiyati", () => {
  const s = aracEkMaliyetHesapla(1500000, 1500, []);
  assert.equal(s.ekToplam, 0);
  assert.equal(s.genelToplam, 1500000);
});

test("her kalem kaynak_tipi tasir - etiketsiz kalem olmamali", () => {
  const s = aracEkMaliyetHesapla(2000000, 1500, HEPSI);
  s.detaylar.forEach((d) => {
    assert.ok(["resmi", "tahmini"].includes(d.kaynak_tipi),
      d.id + " kalemi kaynak_tipi tasimiyor");
  });
});

test("MTV tarifesi kaynagi ve yili belgelenmis", () => {
  assert.equal(ARAC_EK_MALIYETLER.yil, 2026);
  assert.match(ARAC_EK_MALIYETLER.mtv.kaynak, /Resmi Gazete|R\.G\./i);
  assert.equal(ARAC_EK_MALIYETLER.mtv.kaynak_tipi, "resmi");
});
