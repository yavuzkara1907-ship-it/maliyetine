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


  // ==================================================================
  // BÜTÇE DENGELEYİCİ
  //
  // "Bütçem 411.670 değil 300.000" diyen kullanıcıya, hedefe ulaşmak
  // için HANGİ KALEMDE NE YAPMASI gerektiğini söyler.
  //
  // ------------------------------------------------------------------
  // NEDEN BU BİR TAVSİYE MOTORU DEĞİL, ARİTMETİK
  // ------------------------------------------------------------------
  // Öneriler uydurulmuyor, ÖLÇÜLMÜŞ segment fiyatlarından çıkarılıyor.
  // "Yemekli yerine kokteyl seç" diyebiliyoruz çünkü iki varyantın da
  // kişi başı fiyatını ayrı ayrı ölçtük; "takıyı ekonomiğe indir"
  // diyebiliyoruz çünkü ekonomik segmentin medyanı elimizde.
  //
  // "Pazarlık yap, %10 indirim al" gibi ölçmediğimiz bir tasarruf
  // ÖNERİLMEZ - o tavsiye olurdu, veri değil.
  //
  // ------------------------------------------------------------------
  // HEDEFE ULAŞILAMIYORSA SÖYLENİR
  // ------------------------------------------------------------------
  // Tüm hamleler yapıldığında bile hedef tutmuyorsa uydurma bir yol
  // gösterilmez; "ölçtüğümüz kalemlerle en düşük X TL" denir. Bu, tüm
  // sitede uyguladığımız kuralın aynısı: cevabı olmayan soruya cevap
  // uydurmuyoruz.
  // ==================================================================

  const SEGMENT_SIRASI = ["luks", "orta", "dusuk"];
  const SEGMENT_ADI = { luks: "üst", orta: "orta", dusuk: "ekonomik" };

  function _birimFiyat(kalemVerisi, segAnahtari) {
    if (!kalemVerisi) return null;
    const seg = kalemVerisi.segmentler && kalemVerisi.segmentler[segAnahtari];
    return seg ? seg.medyan : null;
  }

  // Bir kalemi mevcut segmentten daha ucuz segmentlere indirmenin
  // tasarrufları. Segmentler arasi tutarsizlik varsa (blender ornegi -
  // orta > ust) o kalem ATLANIR: tutarsiz veriden "tasarruf" cikarmak
  // kullaniciyi yaniltir.
  function _segmentHamleleri(tanim, kalemVerisi, mevcutSeg, carpan) {
    const hamleler = [];
    if (!kalemVerisi || tanim.kaynak_tipi === "tahmini") return hamleler;
    if (kalemVerisi.segment_tutarsiz) return hamleler;
    const mevcutFiyat = _birimFiyat(kalemVerisi, mevcutSeg);
    if (mevcutFiyat == null) return hamleler;
    const baslangic = SEGMENT_SIRASI.indexOf(mevcutSeg);
    if (baslangic === -1) return hamleler;
    for (let i = baslangic + 1; i < SEGMENT_SIRASI.length; i++) {
      const hedefSeg = SEGMENT_SIRASI[i];
      const fiyat = _birimFiyat(kalemVerisi, hedefSeg);
      if (fiyat == null || fiyat >= mevcutFiyat) continue;
      hamleler.push({
        tip: "segment",
        kalem_id: tanim.id,
        ad: tanim.ad,
        from: SEGMENT_ADI[mevcutSeg],
        to: SEGMENT_ADI[hedefSeg],
        hedef_segment: hedefSeg,
        tasarruf: Math.round((mevcutFiyat - fiyat) * carpan),
      });
    }
    return hamleler;
  }

  /**
   * @param hedefButce  kullanicinin girdigi tutar
   * @param baslangic   hesapla() ciktisi ({toplam, detaylar})
   * Deterministik: en buyuk tasarruftan baslayip hedef tutana kadar
   * hamle ekler. Ayni kalemde birden fazla segment hamlesi varsa
   * yalnizca EN SON uygulanani sayilir (cift sayim olmasin).
   */
  function butceyiDengele(hedefButce, veriKalemleri, kalemTanimlari,
                          secilenIdler, segment, davetliSayisi) {
    const mevcutSeg = SEGMENT_ANAHTARI[segment] || "orta";
    const baslangic = hesapla(veriKalemleri, kalemTanimlari, secilenIdler,
                              segment, davetliSayisi);
    const acik = baslangic.toplam - hedefButce;
    if (!(hedefButce > 0)) return null;
    if (acik <= 0) {
      // `pay` = butceden ARTAN tutar. Ilk yazimda cikarma tersti
      // (mevcut - hedef) ve butcesi bol olan kullaniciya negatif pay
      // gosteriyordu. Test yakaladi.
      return { yeterli: true, mevcut: baslangic.toplam, hedef: hedefButce,
               pay: hedefButce - baslangic.toplam, hamleler: [], kalan_acik: 0 };
    }

    // Tum olasi hamleler
    let tumu = [];
    for (const tanim of kalemTanimlari) {
      if (!secilenIdler.includes(tanim.id)) continue;
      const carpan = tanim.birim === "kisi_basi" ? Math.max(davetliSayisi || 0, 0) : 1;
      tumu = tumu.concat(
        _segmentHamleleri(tanim, (veriKalemleri || {})[tanim.id], mevcutSeg, carpan)
      );
    }
    // Kalem basina EN BUYUK tasarrufu veren hamleyi tut (en ucuz segment)
    const enIyi = {};
    for (const h of tumu) {
      if (!enIyi[h.kalem_id] || h.tasarruf > enIyi[h.kalem_id].tasarruf) {
        enIyi[h.kalem_id] = h;
      }
    }
    const adaylar = Object.values(enIyi).sort((a, b) => b.tasarruf - a.tasarruf);

    const secilen = [];
    let birikim = 0;
    for (const h of adaylar) {
      if (birikim >= acik) break;
      secilen.push(h);
      birikim += h.tasarruf;
    }

    return {
      yeterli: false,
      mevcut: baslangic.toplam,
      hedef: hedefButce,
      acik: acik,
      hamleler: secilen,
      toplam_tasarruf: birikim,
      yeni_toplam: baslangic.toplam - birikim,
      kalan_acik: Math.max(acik - birikim, 0),
      // Hedef tutmuyorsa: olculen kalemlerle inilebilecek en dusuk tutar
      en_dusuk_mumkun: baslangic.toplam - adaylar.reduce((t, h) => t + h.tasarruf, 0),
    };
  }

  return { hesapla, kalemSatiriHesapla, butceyiDengele, SEGMENT_ANAHTARI };
});
