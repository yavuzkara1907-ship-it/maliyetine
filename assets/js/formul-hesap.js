/*
 * Maliyeti Ne? — FORMÜL HESAPLAYICILARI
 *
 * Ölçülmüş fiyat değil, MEVZUATLA/MATEMATİKLE TÜREYEN hesaplar.
 *
 * ------------------------------------------------------------------
 * BU KIRMIZI ÇİZGİYİ NEDEN İHLAL ETMİYOR
 * ------------------------------------------------------------------
 * Projenin kuralı "fiyat verisi ASLA LLM'in kendi bilgisinden
 * üretilmez". Buradaki sayılar fiyat değil: kıdem tazminatı bir kanun
 * formülü, gelir vergisi bir tebliğ tarifesi, taksit bir annüite
 * denklemi. Cevap TÜRETİLEBİLİR ve DOĞRULANABİLİR — uydurma değil.
 *
 * Ayrım şudur: bir ürünün kaça satıldığını ölçmek gerekir; bir verginin
 * ne olduğunu ise mevzuat söyler. İkincisinde kaynak Resmî Gazete'dir
 * ve `resmi-parametreler.js` içinde her sayının yanında yazılıdır.
 *
 * ------------------------------------------------------------------
 * TASARIM
 * ------------------------------------------------------------------
 * Her fonksiyon SAF: girdi alır, kırılımlı sonuç döner, DOM'a
 * dokunmaz. Böylece node ile test edilebiliyor — bu proje bir
 * hesaplayıcıda daha önce gerçek bir bug yakalamıştı (araç
 * hesaplayıcısında `step` niteliği formu sessizce bloke ediyordu),
 * o yüzden hesap mantığı testsiz bırakılmıyor.
 *
 * Her sonuç `parametreler` alanında kullandığı mevzuat kaynağını
 * taşır; sayfa bunu görünür künyeye basıyor.
 */

/* eslint-disable no-undef */
const _P =
  typeof RESMI_PARAMETRELER !== "undefined"
    ? RESMI_PARAMETRELER
    : require("./resmi-parametreler.js").RESMI_PARAMETRELER;
const _tarifedenVergi =
  typeof tarifedenVergi !== "undefined"
    ? tarifedenVergi
    : require("./resmi-parametreler.js").tarifedenVergi;
const _gecerliMi =
  typeof parametreGecerliMi !== "undefined"
    ? parametreGecerliMi
    : require("./resmi-parametreler.js").parametreGecerliMi;

function _yuvarla(n) {
  const r = Math.round(n * 100) / 100;
  return r === 0 ? 0 : r; // -0 uretmesin: ekranda "-0 TL" cikiyordu
}

/* ================================================================
 * 1. KDV
 * ================================================================ */
function kdvHesapla(tutar, oran, yon) {
  if (!(tutar > 0) || !(oran > 0)) return null;
  let haric, kdv, dahil;
  if (yon === "dahilden-harice") {
    dahil = tutar;
    haric = tutar / (1 + oran);
    kdv = dahil - haric;
  } else {
    haric = tutar;
    kdv = tutar * oran;
    dahil = haric + kdv;
  }
  return {
    haric: _yuvarla(haric),
    kdv: _yuvarla(kdv),
    dahil: _yuvarla(dahil),
    oran: oran,
    parametreler: [_P.kdv],
  };
}

/* ================================================================
 * 2. BRÜT → NET ÜCRET
 *
 * KÜMÜLATİF MATRAH NEDEN GİRDİ: gelir vergisi artan oranlı ve matrah
 * yıl içinde BİRİKİYOR. Aynı brüt ücret Ocak'ta ve Kasım'da farklı net
 * verir. Ayı sormayan bir hesaplayıcı yılın ilk ayı için doğru,
 * sonrası için yanlış sonuç üretir — rakiplerin çoğu bunu atlıyor.
 *
 * ASGARİ ÜCRET İSTİSNASI: 2022'den beri tüm çalışanların ücretinin
 * asgari ücrete isabet eden kısmı gelir ve damga vergisinden istisna.
 * Yani her çalışan, asgari ücretli bir çalışanın ödemediği vergiyi
 * ödemez. Bunu atlayan hesap, net ücreti OLDUĞUNDAN DÜŞÜK gösterir.
 * ================================================================ */
function brutdenNetUcret(brut, ay, oncekiKumulatifMatrah) {
  if (!(brut > 0)) return null;
  const sgk = _P.sgk;
  const av = _P.asgari_ucret;
  const dv = _P.damga_vergisi;
  const gv = _P.gelir_vergisi;

  const primMatrahi = Math.min(Math.max(brut, 0), sgk.tavan_aylik);
  const sgkIsci = primMatrahi * sgk.isci_sgk_orani;
  const issizlik = primMatrahi * sgk.isci_issizlik_orani;
  const gvMatrahi = Math.max(brut - sgkIsci - issizlik, 0);

  // Asgari ücretin kendi vergi matrahı ve vergisi — istisna tutarı bu.
  const avPrim = Math.min(av.brut_aylik, sgk.tavan_aylik);
  const avMatrah = avPrim * (1 - sgk.isci_sgk_orani - sgk.isci_issizlik_orani);

  const oncekiMatrah = oncekiKumulatifMatrah || 0;
  const oncekiAy = Math.max((ay || 1) - 1, 0);

  // Artan oranlı tarifede bu ayın vergisi = (kümülatif dahil) − (kümülatif hariç)
  const buAyVergi =
    _tarifedenVergi(gv.ucret, oncekiMatrah + gvMatrahi) -
    _tarifedenVergi(gv.ucret, oncekiMatrah);

  // İstisna da kümülatif hesaplanır: asgari ücretlinin aynı aydaki vergisi.
  const avKumulatifOnce = avMatrah * oncekiAy;
  const avBuAyVergi =
    _tarifedenVergi(gv.ucret, avKumulatifOnce + avMatrah) -
    _tarifedenVergi(gv.ucret, avKumulatifOnce);

  const gelirVergisi = Math.max(buAyVergi - avBuAyVergi, 0);

  const damgaHam = brut * dv.ucret_orani;
  const damgaIstisna = av.brut_aylik * dv.ucret_orani;
  const damga = Math.max(damgaHam - damgaIstisna, 0);

  const net = brut - sgkIsci - issizlik - gelirVergisi - damga;

  return {
    brut: _yuvarla(brut),
    sgk_isci: _yuvarla(sgkIsci),
    issizlik: _yuvarla(issizlik),
    gelir_vergisi: _yuvarla(gelirVergisi),
    gelir_vergisi_istisnasi: _yuvarla(avBuAyVergi),
    damga_vergisi: _yuvarla(damga),
    damga_istisnasi: _yuvarla(Math.min(damgaHam, damgaIstisna)),
    kesinti_toplami: _yuvarla(sgkIsci + issizlik + gelirVergisi + damga),
    net: _yuvarla(net),
    vergi_matrahi: _yuvarla(gvMatrahi),
    tavan_asildi: brut > sgk.tavan_aylik,
    ay: ay || 1,
    parametreler: [gv, sgk, av, dv],
  };
}

/* NET → BRÜT: tersi kapalı formda çözülemez (istisna ve tavan
 * kırılmaları yüzünden parçalı fonksiyon). İkili arama ile çözülüyor —
 * 60 adımda kuruş hassasiyetinin çok altına iniyor. */
function nettenBrutUcret(net, ay, oncekiKumulatifMatrah) {
  if (!(net > 0)) return null;
  let alt = net,
    ust = net * 3 + 100000;
  for (let i = 0; i < 60; i++) {
    const orta = (alt + ust) / 2;
    const s = brutdenNetUcret(orta, ay, oncekiKumulatifMatrah);
    if (s.net < net) alt = orta;
    else ust = orta;
  }
  // Ikili arama ortayi seciyor; hedefi tam tutturan brut degeri kurusun
  // altinda kaciriyordu (28.075,50 net icin 33.029,99 doner, 33.030,00
  // olmasi gerekirdi). Iki komsu kurus degerinden hedefe yakin olani
  // seciyoruz - resmi asgari ucret rakamini birebir vermek onemli.
  const kaba = (alt + ust) / 2;
  let enIyi = null, enIyiFark = Infinity;
  for (const aday of [Math.floor(kaba * 100) / 100, Math.ceil(kaba * 100) / 100]) {
    const s = brutdenNetUcret(aday, ay, oncekiKumulatifMatrah);
    const fark = Math.abs(s.net - net);
    if (fark < enIyiFark) { enIyiFark = fark; enIyi = s; }
  }
  return enIyi;
}

/* ================================================================
 * 3. KIDEM VE İHBAR TAZMİNATI
 *
 * KIDEM: her tam yıl için 30 günlük GİYDİRİLMİŞ brüt ücret, ancak
 * yıllık tutar kıdem tavanını aşamaz. Gelir vergisinden istisna,
 * damga vergisine tabi.
 * İHBAR: İş K. md.17 sürelerine göre; gelir vergisine TABİ.
 * ================================================================ */
function kidemIhbarHesapla(giydirilmisBrut, toplamAy, ihbarDahil) {
  if (!(giydirilmisBrut > 0) || !(toplamAy > 0)) return null;
  const tavan = _P.kidem_tavani;
  const dv = _P.damga_vergisi;

  const esas = Math.min(giydirilmisBrut, tavan.tutar);
  const yil = Math.floor(toplamAy / 12);
  const artanAy = toplamAy % 12;

  const kidemBrut = esas * yil + (esas * artanAy) / 12;
  const kidemDamga = kidemBrut * dv.ucret_orani;
  const kidemNet = kidemBrut - kidemDamga;

  const sonuc = {
    esas_ucret: _yuvarla(esas),
    tavan_uygulandi: giydirilmisBrut > tavan.tutar,
    tavan: tavan.tutar,
    hizmet_yili: yil,
    artan_ay: artanAy,
    kidem_brut: _yuvarla(kidemBrut),
    kidem_damga: _yuvarla(kidemDamga),
    kidem_net: _yuvarla(kidemNet),
    parametreler: [tavan, dv, _P.ihbar],
  };

  if (ihbarDahil) {
    const kademe =
      _P.ihbar.kademeler.find((k) => k.max_ay !== null && toplamAy < k.max_ay) ||
      _P.ihbar.kademeler[_P.ihbar.kademeler.length - 1];
    // İhbarda TAVAN YOK — kıdemden farkı bu, sık karıştırılıyor.
    const gunluk = giydirilmisBrut / 30;
    const ihbarBrut = gunluk * kademe.hafta * 7;
    sonuc.ihbar_hafta = kademe.hafta;
    sonuc.ihbar_kademe = kademe.etiket;
    sonuc.ihbar_brut = _yuvarla(ihbarBrut);
    sonuc.ihbar_damga = _yuvarla(ihbarBrut * dv.ucret_orani);
    // İhbar tazminatı gelir vergisine tabi; ücret tarifesiyle,
    // kümülatif matrah bilinmediği için ilk dilimden hesaplanır ve
    // sayfada bu varsayım AÇIKÇA yazılır.
    sonuc.ihbar_gelir_vergisi = _yuvarla(
      _tarifedenVergi(_P.gelir_vergisi.ucret, ihbarBrut)
    );
    sonuc.ihbar_net = _yuvarla(
      ihbarBrut - sonuc.ihbar_damga - sonuc.ihbar_gelir_vergisi
    );
    sonuc.toplam_net = _yuvarla(kidemNet + sonuc.ihbar_net);
  }
  return sonuc;
}

/* ================================================================
 * 4. KREDİ TAKSİTİ (annüite) — saf matematik, parametre yok
 * T = A · i · (1+i)^n / ((1+i)^n − 1)
 * ================================================================ */
function krediTaksitHesapla(anapara, aylikFaizYuzde, vade) {
  if (!(anapara > 0) || !(vade > 0)) return null;
  const i = aylikFaizYuzde / 100;
  let taksit;
  if (i === 0) {
    taksit = anapara / vade;
  } else {
    const k = Math.pow(1 + i, vade);
    taksit = (anapara * i * k) / (k - 1);
  }
  const toplam = taksit * vade;
  return {
    taksit: _yuvarla(taksit),
    toplam_odeme: _yuvarla(toplam),
    toplam_faiz: _yuvarla(toplam - anapara),
    anapara: _yuvarla(anapara),
    vade: vade,
    aylik_faiz: aylikFaizYuzde,
    // KKDF/BSMV kasıtla DIŞARIDA - oranlar kredi tipine göre degisiyor
    // ve tek bir dogru deger yok. Sayfada bu aciklikla yaziliyor.
    parametreler: [],
  };
}

/* ================================================================
 * 5. YÜZDE / ZAM — saf matematik
 * ================================================================ */
function yuzdeHesapla(tur, a, b) {
  if (tur === "zam") {
    if (!(a > 0)) return null;
    return { sonuc: _yuvarla(a * (1 + b / 100)), fark: _yuvarla(a * (b / 100)), parametreler: [] };
  }
  if (tur === "indirim") {
    if (!(a > 0)) return null;
    return { sonuc: _yuvarla(a * (1 - b / 100)), fark: _yuvarla(a * (b / 100)), parametreler: [] };
  }
  if (tur === "degisim") {
    if (!(a > 0)) return null;
    return { sonuc: _yuvarla(((b - a) / a) * 100), fark: _yuvarla(b - a), parametreler: [] };
  }
  if (tur === "oran") {
    if (!(b > 0)) return null;
    return { sonuc: _yuvarla((a / b) * 100), fark: null, parametreler: [] };
  }
  return null;
}

/* Sonuçtaki tüm parametre kümeleri bugün geçerli mi?
 * Geçerli değilse sayfa görünür uyarı gösterir — sessizce eski yılın
 * vergisini vermek kabul edilemez. */
function sonucParametreleriGecerliMi(sonuc, bugun) {
  if (!sonuc || !sonuc.parametreler) return true;
  return sonuc.parametreler.every((k) => _gecerliMi(k, bugun));
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    kdvHesapla,
    brutdenNetUcret,
    nettenBrutUcret,
    kidemIhbarHesapla,
    krediTaksitHesapla,
    yuzdeHesapla,
    sonucParametreleriGecerliMi,
  };
}
