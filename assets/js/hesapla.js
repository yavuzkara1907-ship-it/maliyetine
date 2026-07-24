// Saf hesaplama mantigi - DOM'a bagimli degil, hem tarayicida hem
// Node.js testlerinde calisir (hesapla.test.js).
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.maliyetHesapla = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  const SEGMENT_ANAHTARI = { ekonomik: "dusuk", orta: "orta", luks: "luks" };

  // Bir kalem icin, secilen segmentteki birim fiyati bulup (yoksa genel
  // medyana duser) satir toplamini hesaplar. Veri hic yoksa
  // { veri_var: false } doner - toplama KATILMAZ, cagiran taraf bunu
  // "veri henuz yok" olarak gostermeli.
  //
  // kalemTanimi.kaynak_tipi === "tahmini" olan kalemler icin kalemVerisi
  // gerekmez - fiyat dogrudan kalemTanimi.tahmini'den okunur (bkz.
  // dugun-kalemler.js basindaki aciklama). Bu satirlar HER ZAMAN
  // tahmini_mi: true ile isaretlenir - UI bunlari "gercek kaynak"
  // verisinden ayri gostermek ZORUNDA.
  function kalemSatiriHesapla(kalemTanimi, kalemVerisi, segment, davetliSayisi) {
    const segAnahtari = SEGMENT_ANAHTARI[segment] || "orta";
    const carpan = kalemTanimi.birim === "kisi_basi" ? Math.max(davetliSayisi || 0, 0) : 1;

    if (kalemTanimi.kaynak_tipi === "tahmini") {
      const birimFiyat = kalemTanimi.tahmini[segAnahtari];
      return {
        id: kalemTanimi.id,
        ad: kalemTanimi.ad,
        veri_var: true,
        tahmini_mi: true,
        birim: kalemTanimi.birim,
        birim_fiyat: birimFiyat,
        satir_toplam: Math.round(birimFiyat * carpan),
        kaynak_notu: kalemTanimi.kaynak_notu,
        arastirma_tarihi: kalemTanimi.arastirma_tarihi,
      };
    }

    if (!kalemVerisi) {
      return { id: kalemTanimi.id, ad: kalemTanimi.ad, veri_var: false };
    }
    const segVeri = kalemVerisi.segmentler && kalemVerisi.segmentler[segAnahtari];
    const birimFiyat = segVeri ? segVeri.medyan : kalemVerisi.genel_medyan;
    if (birimFiyat == null) {
      return { id: kalemTanimi.id, ad: kalemTanimi.ad, veri_var: false };
    }
    return {
      id: kalemTanimi.id,
      ad: kalemTanimi.ad,
      veri_var: true,
      tahmini_mi: false,
      birim: kalemTanimi.birim,
      birim_fiyat: birimFiyat,
      satir_toplam: Math.round(birimFiyat * carpan),
      kaynak_sayisi: kalemVerisi.kaynak_sayisi || 0,
      guncelleme_tarihi: kalemVerisi.guncelleme_tarihi || null,
      capraz_dogrulama_uyarisi: kalemVerisi.capraz_dogrulama_uyarisi || null,
      // segment bazli veri yoktu, genel medyana dusuldu - UI'da belirtilmeli.
      genel_medyana_dusuldu: !segVeri,
    };
  }

  // kalemTanimlari: DUGUN_KALEMLERI benzeri liste ({id, ad, birim}).
  // veriKalemleri: /veri/dugun.json'daki "kalemler" nesnesi.
  // secilenIdler: kullanicinin isaretledigi kalem id'leri.
  function hesapla(veriKalemleri, kalemTanimlari, secilenIdler, segment, davetliSayisi) {
    const detaylar = [];
    let toplam = 0;
    for (const tanim of kalemTanimlari) {
      if (!secilenIdler.includes(tanim.id)) continue;
      const satir = kalemSatiriHesapla(tanim, (veriKalemleri || {})[tanim.id], segment, davetliSayisi);
      detaylar.push(satir);
      if (satir.veri_var) toplam += satir.satir_toplam;
    }
    return { toplam, detaylar };
  }

  return { hesapla, kalemSatiriHesapla, SEGMENT_ANAHTARI };
});
