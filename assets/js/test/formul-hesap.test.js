const test = require("node:test");
const assert = require("node:assert");
const {
  kdvHesapla, brutdenNetUcret, nettenBrutUcret, kidemIhbarHesapla,
  krediTaksitHesapla, yuzdeHesapla, sonucParametreleriGecerliMi,
} = require("../formul-hesap.js");
const { RESMI_PARAMETRELER, tarifedenVergi, parametreGecerliMi } =
  require("../resmi-parametreler.js");

const yakin = (a, b, tol = 0.02) =>
  assert.ok(Math.abs(a - b) <= tol, `${a} ≈ ${b} degil (fark ${Math.abs(a - b)})`);

/* ============ TARİFE DOĞRULUĞU ============
 * Bu testler tarifenin KENDİ İÇİNDE tutarlı olduğunu kanıtlıyor:
 * kümülatif tutarlar dilim × oran ile birebir çıkıyor. Bir sayı yanlış
 * kopyalanmışsa burada patlar. */
test("gelir vergisi tarifesi kumulatif tutarlari aritmetikle tutuyor", () => {
  for (const ad of ["ucret", "ucret_disi"]) {
    const t = RESMI_PARAMETRELER.gelir_vergisi[ad];
    let birikmis = 0, onceki = 0;
    for (const d of t) {
      yakin(d.birikmis, birikmis, 0.5);
      if (d.ust === null) break;
      birikmis += (d.ust - onceki) * d.oran;
      onceki = d.ust;
    }
  }
});

test("ucret ve ucret disi tarife yalnizca 3. dilimden sonra ayrisiyor", () => {
  const u = RESMI_PARAMETRELER.gelir_vergisi.ucret;
  const d = RESMI_PARAMETRELER.gelir_vergisi.ucret_disi;
  assert.equal(u[0].ust, d[0].ust);
  assert.equal(u[1].ust, d[1].ust);
  assert.notEqual(u[2].ust, d[2].ust);
  assert.equal(u[2].ust, 1500000);
  assert.equal(d[2].ust, 1000000);
});

test("tarifeden vergi: dilim sinirlarinda dogru", () => {
  const t = RESMI_PARAMETRELER.gelir_vergisi.ucret;
  yakin(tarifedenVergi(t, 190000), 28500);
  yakin(tarifedenVergi(t, 400000), 70500);
  yakin(tarifedenVergi(t, 1500000), 367500);
  yakin(tarifedenVergi(t, 0), 0);
});

/* ============ EN ÖNEMLİ TEST ============
 * Resmî net asgari ücret 28.075,50 TL. Hesabımız bunu birebir vermek
 * ZORUNDA — vermiyorsa ya bir oran ya istisna mantığı yanlış, ve o
 * hata tüm maaş hesaplarına yayılır. */
test("net asgari ucret resmi aciklanan tutarla BIREBIR ayni", () => {
  const av = RESMI_PARAMETRELER.asgari_ucret;
  const s = brutdenNetUcret(av.brut_aylik, 1, 0);
  yakin(s.net, av.net_aylik, 0.05);
  assert.equal(s.gelir_vergisi, 0, "asgari ucretli gelir vergisi odemez");
  assert.equal(s.damga_vergisi, 0, "asgari ucretli damga vergisi odemez");
});

test("asgari ucret istisnasi ustteki ucretlere de uygulaniyor", () => {
  // Istisna atlanirsa net OLDUGUNDAN DUSUK cikar.
  const s = brutdenNetUcret(60000, 1, 0);
  assert.ok(s.gelir_vergisi_istisnasi > 0, "istisna hesaplanmali");
  assert.ok(s.damga_istisnasi > 0);
  assert.ok(s.net > 60000 * 0.6);
});

test("kumulatif matrah artinca ayni brut daha az net veriyor", () => {
  // Artan oranli tarifenin dogal sonucu; ayi sormayan hesaplayici
  // yilin ilk ayi disinda yanlis sonuc verir.
  const ocak = brutdenNetUcret(120000, 1, 0);
  const kasim = brutdenNetUcret(120000, 11, 900000);
  assert.ok(kasim.net < ocak.net, "kumulatif matrah neti dusurmeli");
});

test("SGK tavani asilinca prim tavandan kesiliyor", () => {
  const t = RESMI_PARAMETRELER.sgk.tavan_aylik;
  const s = brutdenNetUcret(t * 2, 1, 0);
  assert.equal(s.tavan_asildi, true);
  yakin(s.sgk_isci, t * RESMI_PARAMETRELER.sgk.isci_sgk_orani, 0.05);
  yakin(s.issizlik, t * RESMI_PARAMETRELER.sgk.isci_issizlik_orani, 0.05);
});

test("net -> brut -> net gidis donus tutuyor", () => {
  for (const net of [28075.5, 45000, 90000, 250000]) {
    const b = nettenBrutUcret(net, 1, 0);
    yakin(b.net, net, 0.05);
  }
});

test("kesintilerin toplami brut - net'e esit", () => {
  const s = brutdenNetUcret(75000, 5, 300000);
  yakin(s.kesinti_toplami, s.brut - s.net, 0.05);
});

/* ============ KIDEM / İHBAR ============ */
test("kidem tavani uygulaniyor, ihbarda tavan YOK", () => {
  const tavan = RESMI_PARAMETRELER.kidem_tavani.tutar;
  const s = kidemIhbarHesapla(tavan * 2, 60, true);
  assert.equal(s.tavan_uygulandi, true);
  assert.equal(s.esas_ucret, tavan);
  yakin(s.kidem_brut, tavan * 5, 1);
  // Ihbar giydirilmis ucretten, tavansiz -> tavanin ustunde cikmali
  assert.ok(s.ihbar_brut > tavan, "ihbarda tavan uygulanmamali");
});

test("kidem: tam yil + artan ay oransal", () => {
  const s = kidemIhbarHesapla(30000, 30, false); // 2 yil 6 ay
  assert.equal(s.hizmet_yili, 2);
  assert.equal(s.artan_ay, 6);
  yakin(s.kidem_brut, 30000 * 2 + 30000 * 0.5, 1);
});

test("ihbar kademeleri Is Kanunu md.17 ile ayni", () => {
  assert.equal(kidemIhbarHesapla(30000, 3, true).ihbar_hafta, 2);
  assert.equal(kidemIhbarHesapla(30000, 12, true).ihbar_hafta, 4);
  assert.equal(kidemIhbarHesapla(30000, 24, true).ihbar_hafta, 6);
  assert.equal(kidemIhbarHesapla(30000, 60, true).ihbar_hafta, 8);
});

test("kidem gelir vergisinden istisna, ihbar TABI", () => {
  const s = kidemIhbarHesapla(40000, 48, true);
  // Kidem netinden yalnizca damga dusulur
  yakin(s.kidem_net, s.kidem_brut - s.kidem_damga, 0.05);
  assert.ok(s.ihbar_gelir_vergisi > 0, "ihbar gelir vergisine tabi");
});

/* ============ KREDİ ============ */
test("annuite formulu: faiz 0 iken taksit = anapara / vade", () => {
  const s = krediTaksitHesapla(120000, 0, 12);
  yakin(s.taksit, 10000);
  yakin(s.toplam_faiz, 0);
});

test("annuite: toplam odeme = taksit x vade, faiz = toplam - anapara", () => {
  const s = krediTaksitHesapla(500000, 3.5, 36);
  yakin(s.toplam_odeme, s.taksit * 36, 0.5);
  yakin(s.toplam_faiz, s.toplam_odeme - 500000, 0.5);
  assert.ok(s.taksit > 500000 / 36, "faizli taksit anapara/vade'den buyuk olmali");
});

/* ============ YÜZDE ============ */
test("yuzde: zam, indirim, degisim, oran", () => {
  yakin(yuzdeHesapla("zam", 1000, 25).sonuc, 1250);
  yakin(yuzdeHesapla("indirim", 1000, 25).sonuc, 750);
  yakin(yuzdeHesapla("degisim", 1000, 1250).sonuc, 25);
  yakin(yuzdeHesapla("oran", 250, 1000).sonuc, 25);
});

/* ============ KDV ============ */
test("kdv iki yon birbirinin tersi", () => {
  const ileri = kdvHesapla(1000, 0.2, "haricten-dahile");
  yakin(ileri.dahil, 1200);
  const geri = kdvHesapla(1200, 0.2, "dahilden-harice");
  yakin(geri.haric, 1000);
  yakin(geri.kdv, 200);
});

test("kdv oranlari mevzuattaki uc oran", () => {
  assert.deepEqual(
    RESMI_PARAMETRELER.kdv.oranlar.map((o) => o.oran),
    [0.01, 0.10, 0.20]
  );
});

/* ============ GEÇERSİZ GİRDİ ============ */
test("gecersiz girdide null doner, 0 TL gibi guvenilir gorunen sonuc URETMEZ", () => {
  assert.equal(kdvHesapla(0, 0.2, "haricten-dahile"), null);
  assert.equal(kdvHesapla(-5, 0.2, "haricten-dahile"), null);
  assert.equal(brutdenNetUcret(0, 1, 0), null);
  assert.equal(nettenBrutUcret(-1, 1, 0), null);
  assert.equal(kidemIhbarHesapla(30000, 0, false), null);
  assert.equal(krediTaksitHesapla(100000, 2, 0), null);
  assert.equal(yuzdeHesapla("bilinmeyen", 1, 2), null);
});

/* ============ PARAMETRE GEÇERLİLİĞİ ============
 * 1 Ocak 2027'de bu dosya guncellenmezse site sessizce 2026 vergisini
 * hesaplamaya devam eder. Bu testler o sessizligi imkansiz kiliyor. */
test("her parametre kumesi kaynak ve gecerlilik tarihi tasiyor", () => {
  for (const [ad, k] of Object.entries(RESMI_PARAMETRELER)) {
    assert.ok(k.kaynak, `${ad}: kaynak yok`);
    assert.ok(k.gecerli_baslangic, `${ad}: gecerli_baslangic yok`);
    assert.ok("gecerli_bitis" in k, `${ad}: gecerli_bitis alani yok`);
  }
});

test("BUGUN kullanilan parametrelerin hepsi gecerli (suresi gecmisse bu test PATLAR)", () => {
  const bugun = new Date();
  for (const [ad, k] of Object.entries(RESMI_PARAMETRELER)) {
    assert.ok(
      parametreGecerliMi(k, bugun),
      `${ad} parametresinin suresi gecti (${k.gecerli_baslangic} - ${k.gecerli_bitis}). ` +
        `resmi-parametreler.js GUNCELLENMELI.`
    );
  }
});

test("suresi gecmis parametre sonucta yakalaniyor", () => {
  const s = brutdenNetUcret(50000, 1, 0);
  assert.equal(sonucParametreleriGecerliMi(s, new Date("2026-06-15")), true);
  // 2027'de ayni parametrelerle hesap yapilirsa gecersiz sayilmali
  assert.equal(sonucParametreleriGecerliMi(s, new Date("2027-03-01")), false);
});

test("kidem tavani en kisa omurlu parametre - 6 aylik pencere", () => {
  const k = RESMI_PARAMETRELER.kidem_tavani;
  assert.equal(parametreGecerliMi(k, new Date("2026-08-15")), true);
  assert.equal(parametreGecerliMi(k, new Date("2027-01-15")), false);
});
