// Saf hesaplama mantigi - DOM'a bagimli degil, hem tarayicida hem
// Node.js testlerinde calisir (dugun-hesapla.test.js).
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.dugunHesapla = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  const SEGMENT_ANAHTARI = { ekonomik: "dusuk", orta: "orta", luks: "luks" };

  // Bir kalem icin, secilen segmentteki birim fiyati bulup (yoksa genel
  // medyana duser) satir toplamini hesaplar. Veri hic yoksa
  // { veri_var: false } doner - toplama KATILMAZ, cagiran taraf bunu
  // "veri henuz yok" olarak gostermeli.
  function kalemSatiriHesapla(kalemTanimi, kalemVerisi, segment, davetliSayisi) {
    if (!kalemVerisi) {
      return { id: kalemTanimi.id, ad: kalemTanimi.ad, veri_var: false };
    }
    const segAnahtari = SEGMENT_ANAHTARI[segment] || "orta";
    const segVeri = kalemVerisi.segmentler && kalemVerisi.segmentler[segAnahtari];
    const birimFiyat = segVeri ? segVeri.medyan : kalemVerisi.genel_medyan;
    if (birimFiyat == null) {
      return { id: kalemTanimi.id, ad: kalemTanimi.ad, veri_var: false };
    }
    const carpan = kalemTanimi.birim === "kisi_basi" ? Math.max(davetliSayisi || 0, 0) : 1;
    return {
      id: kalemTanimi.id,
      ad: kalemTanimi.ad,
      veri_var: true,
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
