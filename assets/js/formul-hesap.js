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

/* ================================================================
 * 6. TAPU HARCI — 492 s. Harçlar K. (4) sayılı tarife
 * Alici ve satici AYRI AYRI binde 20; toplam binde 40. En sik yapilan
 * hata toplami tek tarafa yazmak.
 * ================================================================ */
function tapuHarciHesapla(satisBedeli, taraf) {
  if (!(satisBedeli > 0)) return null;
  const t = _P.tapu_harci;
  const tekTaraf = satisBedeli * t.taraf_orani;
  return {
    satis_bedeli: _yuvarla(satisBedeli),
    alici: _yuvarla(tekTaraf),
    satici: _yuvarla(tekTaraf),
    toplam: _yuvarla(tekTaraf * 2),
    odenecek: _yuvarla(taraf === "ikisi" ? tekTaraf * 2 : tekTaraf),
    parametreler: [t],
  };
}

/* ================================================================
 * 7. İŞSİZLİK ÖDENEĞİ — 4447 s. K. md. 50
 * Son 4 ayin ortalama brut kazancinin %40'i; tavan brut asgari
 * ucretin %80'i. Gelir vergisi YOK, yalnizca damga vergisi.
 * ================================================================ */
function issizlikOdenegiHesapla(ortalamaBrut, primGunu) {
  if (!(ortalamaBrut > 0)) return null;
  const io = _P.issizlik_odenegi;
  const av = _P.asgari_ucret;
  const dv = _P.damga_vergisi;

  const hamBrut = ortalamaBrut * io.oran;
  const tavanBrut = av.brut_aylik * io.tavan_orani;
  const brut = Math.min(hamBrut, tavanBrut);
  const damga = brut * dv.ucret_orani;

  // Odeme suresi prim gun sayisina gore; esigi tutturamayan hak kazanmaz.
  let sure = null;
  for (const k of io.sure_kademeleri) {
    if (primGunu >= k.asgari_gun) sure = k;
  }

  return {
    ortalama_brut: _yuvarla(ortalamaBrut),
    odenek_brut: _yuvarla(brut),
    tavan_uygulandi: hamBrut > tavanBrut,
    tavan_brut: _yuvarla(tavanBrut),
    damga: _yuvarla(damga),
    odenek_net: _yuvarla(brut - damga),
    sure_ay: sure ? sure.ay : 0,
    hak_kazanildi: !!sure,
    toplam: sure ? _yuvarla((brut - damga) * sure.ay) : 0,
    parametreler: [io, av, dv],
  };
}

/* ================================================================
 * 8. KİRA GELİR VERGİSİ — GVK md. 21 / 74
 * Mesken istisnasi yalnizca KONUT kirasinda; isyerinde yok.
 * ================================================================ */
function kiraGelirVergisiHesapla(yillikKira, tur, giderYontemi, gercekGider) {
  if (!(yillikKira > 0)) return null;
  const kg = _P.kira_geliri;
  const gv = _P.gelir_vergisi;

  const istisna = tur === "konut" ? Math.min(kg.mesken_istisnasi, yillikKira) : 0;
  const kalan = yillikKira - istisna;
  const gider =
    giderYontemi === "gercek"
      ? Math.min(Math.max(gercekGider || 0, 0), kalan)
      : kalan * kg.goturu_gider_orani;
  const matrah = Math.max(kalan - gider, 0);
  // Kira UCRET DISI gelir - tarifesi ucretten farkli (3. dilim 1.000.000).
  const vergi = _tarifedenVergi(gv.ucret_disi, matrah);

  return {
    yillik_kira: _yuvarla(yillikKira),
    istisna: _yuvarla(istisna),
    gider: _yuvarla(gider),
    matrah: _yuvarla(matrah),
    vergi: _yuvarla(vergi),
    kalan: _yuvarla(yillikKira - vergi),
    istisna_uygulandi: istisna > 0,
    parametreler: [kg, gv],
  };
}

/* ================================================================
 * 9. YILLIK İZİN — İş K. md. 53
 * ================================================================ */
function yillikIzinHesapla(hizmetYili, yas) {
  if (!(hizmetYili >= 1)) return null;
  const yi = _P.yillik_izin;
  const kademe =
    yi.kademeler.find((k) => k.max_yil !== null && hizmetYili <= k.max_yil) ||
    yi.kademeler[yi.kademeler.length - 1];
  let gun = kademe.gun;
  const yasIstisnasi = (yas && (yas < 18 || yas > 50)) && gun < yi.yas_asgari_gun;
  if (yasIstisnasi) gun = yi.yas_asgari_gun;
  return {
    hizmet_yili: hizmetYili,
    kademe: kademe.etiket,
    gun: gun,
    yas_istisnasi: yasIstisnasi,
    parametreler: [yi],
  };
}

/* ================================================================
 * 10. FAZLA MESAİ — İş K. md. 41 / 47
 * ================================================================ */
function fazlaMesaiHesapla(aylikBrut, fazlaSaat, tatilSaat) {
  if (!(aylikBrut > 0)) return null;
  const fm = _P.fazla_mesai;
  // Aylik 30 gun, gunluk 7,5 saat -> 225 saat kabulu (yerlesik uygulama)
  const aylikSaat = 225;
  const saatlik = aylikBrut / aylikSaat;
  const fazla = saatlik * (1 + fm.fazla_calisma_zam) * (fazlaSaat || 0);
  const tatil = saatlik * (1 + fm.tatil_zam) * (tatilSaat || 0);
  return {
    saatlik_ucret: _yuvarla(saatlik),
    fazla_mesai: _yuvarla(fazla),
    tatil_mesaisi: _yuvarla(tatil),
    toplam_brut: _yuvarla(fazla + tatil),
    yillik_limit_asildi: (fazlaSaat || 0) * 12 > fm.yillik_azami_saat,
    yillik_azami: fm.yillik_azami_saat,
    parametreler: [fm],
  };
}

/* ================================================================
 * 11. ALIM GÜCÜ (TÜFE) — parametresi RESMÎ TÜFE, veri EVDS'den
 *
 * Bu hesabin parametresi bir sabit degil, bizim ayda iki kez cektigimiz
 * resmi seri. Rakiplerin hicbirinde yok cunku hicbiri resmi endeksi
 * cekmiyor. Endeks disaridan veriliyor - modul veri UYDURMAZ, veri
 * yoksa null doner ve sayfa hic render edilmez.
 * ================================================================ */
function alimGucuHesapla(tutar, ilkEndeks, sonEndeks) {
  if (!(tutar > 0) || !(ilkEndeks > 0) || !(sonEndeks > 0)) return null;
  const carpan = sonEndeks / ilkEndeks;
  const bugunku = tutar * carpan;
  return {
    tutar: _yuvarla(tutar),
    bugunku_karsilik: _yuvarla(bugunku),
    fark: _yuvarla(bugunku - tutar),
    enflasyon_yuzde: _yuvarla((carpan - 1) * 100),
    // Ayni parayla bugun alinabilecek: alim gucunun eridigi oran
    erime_yuzde: _yuvarla((1 - 1 / carpan) * 100),
    parametreler: [],
  };
}

/* ================================================================
 * 12. İÇERİK GELİRİ (YouTube vb.)
 *
 * NEDEN FARKLI TASARLANDI: bu hesabin formulu onemsiz (izlenme x RPM
 * / 1000); butun mesele RPM'de ve RPM RESMÎ OLARAK YAYINLANMIYOR -
 * kanala, izleyici ulkesine ve donemine gore kat kat degisiyor.
 *
 * Rakipler oraya uydurma bir sabit koyup TEK BIR RAKAM basiyor. Biz
 * uyduramayiz. Cozum kacmak degil, belirsizligi GORUNUR kilmak:
 * kullanicidan kendi RPM'ini aliyoruz ve birden fazla RPM degeri icin
 * duyarlilik tablosu donuyoruz. "Cevap tek bir sayi degil" zaten bu
 * sitenin uslubu (segment yapisinin aynisi).
 * ================================================================ */
const ICERIK_RPM_ADIMLARI = [0.5, 1, 2, 4, 8];

function icerikGeliriHesapla(aylikIzlenme, rpm, kur) {
  if (!(aylikIzlenme > 0)) return null;
  const d = kur > 0 ? kur : 1;
  const hesapla = (r) => (aylikIzlenme / 1000) * r * d;
  return {
    aylik_izlenme: aylikIzlenme,
    kur: d,
    secilen_rpm: rpm > 0 ? rpm : null,
    secilen_aylik: rpm > 0 ? _yuvarla(hesapla(rpm)) : null,
    secilen_yillik: rpm > 0 ? _yuvarla(hesapla(rpm) * 12) : null,
    // Duyarlilik: RPM bilinmiyorsa cevap bir ARALIK'tir, tek sayi degil.
    duyarlilik: ICERIK_RPM_ADIMLARI.map((r) => ({
      rpm: r,
      aylik: _yuvarla(hesapla(r)),
      yillik: _yuvarla(hesapla(r) * 12),
    })),
    parametreler: [],
  };
}

/* ================================================================
 * 13. BİLEŞİK FAİZ / BİRİKİM — saf matematik
 * Aylık düzenli katkı varsa annüite gelecek değeri de eklenir.
 * ================================================================ */
function bilesikFaizHesapla(anapara, aylikKatki, yillikOranYuzde, yilSayisi) {
  if (!(yilSayisi > 0) || (!(anapara > 0) && !(aylikKatki > 0))) return null;
  const i = yillikOranYuzde / 100 / 12;
  const n = Math.round(yilSayisi * 12);
  const anaparaSon = (anapara || 0) * Math.pow(1 + i, n);
  const katkiSon = i === 0
    ? (aylikKatki || 0) * n
    : (aylikKatki || 0) * ((Math.pow(1 + i, n) - 1) / i);
  const toplam = anaparaSon + katkiSon;
  const yatirilan = (anapara || 0) + (aylikKatki || 0) * n;
  return {
    toplam: _yuvarla(toplam),
    yatirilan: _yuvarla(yatirilan),
    kazanc: _yuvarla(toplam - yatirilan),
    ay: n,
    parametreler: [],
  };
}

/* ================================================================
 * 14. BİRİKİM HEDEFİ — bileşik faizin tersi
 * "X TL biriktirmek için ayda ne kadar?"
 * ================================================================ */
function birikimHedefiHesapla(hedef, baslangic, yillikOranYuzde, ayS) {
  if (!(hedef > 0) || !(ayS > 0)) return null;
  const i = yillikOranYuzde / 100 / 12;
  const bas = (baslangic || 0) * Math.pow(1 + i, ayS);
  const kalan = hedef - bas;
  if (kalan <= 0) {
    return { aylik: 0, hedef: _yuvarla(hedef), zaten_yeterli: true,
             baslangic_getirisi: _yuvarla(bas), parametreler: [] };
  }
  const aylik = i === 0 ? kalan / ayS : kalan / ((Math.pow(1 + i, ayS) - 1) / i);
  return {
    aylik: _yuvarla(aylik),
    hedef: _yuvarla(hedef),
    zaten_yeterli: false,
    baslangic_getirisi: _yuvarla(bas),
    toplam_yatirilacak: _yuvarla((baslangic || 0) + aylik * ayS),
    parametreler: [],
  };
}

/* ================================================================
 * 15. HİSSE MALİYET ORTALAMASI — saf matematik
 * ================================================================ */
// ---------------- LOT HESAPLAMA ----------------
// 2026-08-09, Search Console: "borsa lot hesaplama" ve "hisse senedi
// lot hesaplama" sorgulari geliyordu, karsiligi olan sayfa yoktu.
//
// BIST'te 1 LOT = 1 ADET PAY (2005'teki lot birimi degisikliginden
// beri). Yani "kac lot alabilirim" sorusu aslinda "butcem kac paya
// yeter" sorusudur. Hesap saf aritmetik - hicbir mevzuat parametresi
// ya da olculmus veri icermiyor, o yuzden bayatlamaz.
//
// KOMISYON KULLANICIDAN ALINIYOR: araci kurum komisyon oranlari
// kuruma gore degisiyor ve yayinlanmis TEK bir oran yok. Varsayilan
// bir oran gomsek uydurma olurdu; kullanicidan istiyoruz ve bos
// birakilirsa komisyonsuz hesapliyoruz.
function lotHesapla(butce, fiyat, komisyonYuzde) {
  if (!(butce > 0) || !(fiyat > 0)) return null;
  const oran = komisyonYuzde > 0 ? komisyonYuzde / 100 : 0;
  // Komisyon alis tutari uzerinden alindigi icin efektif birim
  // maliyet fiyat*(1+oran) olur; lot sayisi buna gore bulunur.
  const birim = fiyat * (1 + oran);
  const lot = Math.floor(butce / birim);
  if (lot < 1) {
    return {
      yetersiz: true,
      gereken: _yuvarla(birim),
      butce: _yuvarla(butce),
    };
  }
  const tutar = lot * fiyat;
  const komisyon = tutar * oran;
  return {
    yetersiz: false,
    lot: lot,
    tutar: _yuvarla(tutar),
    komisyon: _yuvarla(komisyon),
    toplam: _yuvarla(tutar + komisyon),
    kalan: _yuvarla(butce - tutar - komisyon),
    birim_maliyet: _yuvarla(birim),
  };
}


// ---------------- YAKIT MALIYETI ----------------
// 2026-08-09. Rakiplerin listesinde "arabam ne kadar yakar" var ve
// bizde yoktu; arac vertikalimiz varken bu bosluk anlamsizdi.
//
// SAF MATEMATIK: mesafe x tuketim / 100 x litre fiyati. Hicbir mevzuat
// parametresi yok. LITRE FIYATI KULLANICIDAN aliniyor - akaryakit
// fiyati gunluk degisiyor ve il il farkli; sabit bir deger gomsek
// ertesi gun yanlis olurdu.
function yakitMaliyetiHesapla(mesafeKm, tuketim100, litreFiyat, gidisDonus) {
  if (!(mesafeKm > 0) || !(tuketim100 > 0) || !(litreFiyat > 0)) return null;
  const mesafe = gidisDonus ? mesafeKm * 2 : mesafeKm;
  const litre = (mesafe * tuketim100) / 100;
  const tutar = litre * litreFiyat;
  return {
    mesafe: _yuvarla(mesafe),
    litre: Math.round(litre * 100) / 100,
    tutar: _yuvarla(tutar),
    km_basina: Math.round((tutar / mesafe) * 100) / 100,
    yuz_km: _yuvarla((tuketim100 / 100) * 100 * litreFiyat),
  };
}


// ---------------- BOYA / ODA BOYAMA ----------------
// Alan hesabi saf geometri. VERIM (m2/litre) ve KAT SAYISI kullanicidan;
// boya markasina gore degisiyor ve kutunun uzerinde yazili.
// Kapi/pencere icin kaba bir dusum YAPILMIYOR - onun yerine kullanici
// isterse alan girer; uydurma bir "%10 dus" katsayisi koymuyoruz.
function boyaHesapla(en, boy, yukseklik, katSayisi, verim, litreFiyat,
                     tavanDahil) {
  if (!(en > 0) || !(boy > 0) || !(yukseklik > 0)) return null;
  const kat = katSayisi > 0 ? katSayisi : 2;
  const m2Litre = verim > 0 ? verim : 12;      // tipik: kutuda yazar
  const duvar = 2 * (en + boy) * yukseklik;
  const tavan = tavanDahil ? en * boy : 0;
  const alan = duvar + tavan;
  const litre = (alan * kat) / m2Litre;
  return {
    duvar_alani: Math.round(duvar * 10) / 10,
    tavan_alani: Math.round(tavan * 10) / 10,
    toplam_alan: Math.round(alan * 10) / 10,
    kat: kat,
    litre: Math.ceil(litre * 10) / 10,
    tutar: litreFiyat > 0 ? _yuvarla(Math.ceil(litre * 10) / 10 * litreFiyat) : null,
  };
}


// ---------------- BASA BAS SATIS ADEDI ----------------
// Sabit gider / (birim fiyat - birim degisken maliyet). Saf matematik.
// Birim katki sifir ya da negatifse BASA BAS YOKTUR - uydurma bir adet
// dondurmek yerine bunu acikca soyluyoruz (kart borcu hesaplayicisinda
// aldigimiz kararin aynisi).
function basaBasHesapla(sabitGider, birimFiyat, birimDegisken) {
  if (!(sabitGider > 0) || !(birimFiyat > 0)) return null;
  const katki = birimFiyat - (birimDegisken > 0 ? birimDegisken : 0);
  if (katki <= 0) {
    return {
      mumkun_degil: true,
      katki: _yuvarla(katki),
      gereken_fiyat: _yuvarla((birimDegisken > 0 ? birimDegisken : 0) + 1),
    };
  }
  const adet = Math.ceil(sabitGider / katki);
  return {
    mumkun_degil: false,
    birim_katki: _yuvarla(katki),
    katki_orani: Math.round((katki / birimFiyat) * 1000) / 10,
    adet: adet,
    ciro: _yuvarla(adet * birimFiyat),
  };
}


function hisseMaliyetHesapla(mevcutAdet, mevcutMaliyet, yeniAdet, yeniFiyat) {
  if (!(mevcutAdet > 0) || !(mevcutMaliyet > 0) || !(yeniAdet > 0) || !(yeniFiyat > 0)) {
    return null;
  }
  const toplamAdet = mevcutAdet + yeniAdet;
  const toplamTutar = mevcutAdet * mevcutMaliyet + yeniAdet * yeniFiyat;
  const yeni = toplamTutar / toplamAdet;
  return {
    toplam_adet: toplamAdet,
    toplam_tutar: _yuvarla(toplamTutar),
    yeni_maliyet: _yuvarla(yeni),
    eski_maliyet: _yuvarla(mevcutMaliyet),
    degisim: _yuvarla(yeni - mevcutMaliyet),
    // Basa bas: yeni maliyetin uzerine cikmasi gereken fiyat
    basa_bas: _yuvarla(yeni),
    parametreler: [],
  };
}

/* ================================================================
 * 16. KÂR / ZARAR — komisyon dahil
 * ================================================================ */
function karZararHesapla(alis, satis, adet, komisyonYuzde) {
  if (!(alis > 0) || !(satis > 0) || !(adet > 0)) return null;
  const k = (komisyonYuzde || 0) / 100;
  const alisMaliyet = alis * adet * (1 + k);
  const satisNet = satis * adet * (1 - k);
  const kar = satisNet - alisMaliyet;
  return {
    alis_maliyeti: _yuvarla(alisMaliyet),
    satis_neti: _yuvarla(satisNet),
    kar_zarar: _yuvarla(kar),
    getiri_yuzde: _yuvarla((kar / alisMaliyet) * 100),
    komisyon: _yuvarla(alis * adet * k + satis * adet * k),
    // Komisyonu cikardiktan sonra basa bas satis fiyati
    basa_bas_fiyat: _yuvarla((alis * (1 + k)) / (1 - k)),
    parametreler: [],
  };
}

/* ================================================================
 * 17. TEMETTÜ VERİMİ — saf matematik
 * ================================================================ */
function temettuVerimiHesapla(hisseFiyati, hisseBasinaTemettu, adet) {
  if (!(hisseFiyati > 0) || !(hisseBasinaTemettu > 0)) return null;
  const n = adet > 0 ? adet : 1;
  return {
    verim_yuzde: _yuvarla((hisseBasinaTemettu / hisseFiyati) * 100),
    yillik_temettu: _yuvarla(hisseBasinaTemettu * n),
    yatirim: _yuvarla(hisseFiyati * n),
    // Yatirimin temettuyle geri donme suresi (fiyat ve temettu sabit varsayimi)
    geri_donus_yili: _yuvarla(hisseFiyati / hisseBasinaTemettu),
    parametreler: [],
  };
}

/* ================================================================
 * 18. KREDİ KARTI BORCU — asgari ödeme tuzağı
 *
 * EN ONEMLI DAVRANIS: aylik odeme, o ayin faizinden kucuk ya da esitse
 * BORC HIC BITMEZ. Bu durumda uydurma bir "N ay" sayisi vermek yerine
 * acikca soyluyoruz. Rakip hesaplayicilarin cogu burada ya sonsuz dongu
 * ya da sacma bir sayi uretiyor.
 * ================================================================ */
function kartBorcuHesapla(borc, aylikFaizYuzde, aylikOdeme) {
  if (!(borc > 0) || !(aylikOdeme > 0)) return null;
  const i = aylikFaizYuzde / 100;
  const ilkFaiz = borc * i;
  if (aylikOdeme <= ilkFaiz) {
    return {
      bitmez: true,
      aylik_faiz_tutari: _yuvarla(ilkFaiz),
      aylik_odeme: _yuvarla(aylikOdeme),
      // Borcu azaltmaya baslamak icin gereken asgari odeme
      gereken_asgari: _yuvarla(ilkFaiz + 1),
      parametreler: [],
    };
  }
  let kalan = borc, toplamFaiz = 0, ay = 0;
  while (kalan > 0 && ay < 1200) {
    const faiz = kalan * i;
    toplamFaiz += faiz;
    kalan = kalan + faiz - aylikOdeme;
    ay++;
  }
  const sonOdeme = aylikOdeme + kalan; // son ay eksik kapanir
  return {
    bitmez: false,
    ay: ay,
    toplam_odeme: _yuvarla(aylikOdeme * (ay - 1) + sonOdeme),
    toplam_faiz: _yuvarla(toplamFaiz),
    anapara: _yuvarla(borc),
    parametreler: [],
  };
}

/* ================================================================
 * 19. SERBEST MESLEK (FREELANCER) VERGİSİ
 *
 * Akis: brut hasilat -> gider dusulur -> (varsa) genc girisimci
 * istisnasi -> matrah -> ucret DISI tarife -> hesaplanan vergi.
 * Yil icinde kesilen stopaj beyanda MAHSUP edilir; bu yuzden odenecek
 * vergi negatif cikabilir (iade). Cogu hesaplayici bunu atliyor.
 * ================================================================ */
function serbestMeslekVergiHesapla(brutHasilat, gider, gencGirisimci) {
  if (!(brutHasilat > 0)) return null;
  const sm = _P.serbest_meslek;
  const gv = _P.gelir_vergisi;

  const kdv = brutHasilat * sm.kdv_orani;
  const stopaj = brutHasilat * sm.stopaj_orani;
  const kazanc = Math.max(brutHasilat - Math.max(gider || 0, 0), 0);
  const istisna = gencGirisimci
    ? Math.min(sm.genc_girisimci_istisnasi, kazanc)
    : 0;
  const matrah = Math.max(kazanc - istisna, 0);
  const hesaplanan = _tarifedenVergi(gv.ucret_disi, matrah);
  const odenecek = hesaplanan - stopaj;

  return {
    brut_hasilat: _yuvarla(brutHasilat),
    kdv: _yuvarla(kdv),
    stopaj: _yuvarla(stopaj),
    gider: _yuvarla(Math.max(gider || 0, 0)),
    kazanc: _yuvarla(kazanc),
    istisna: _yuvarla(istisna),
    matrah: _yuvarla(matrah),
    hesaplanan_vergi: _yuvarla(hesaplanan),
    odenecek_vergi: _yuvarla(Math.max(odenecek, 0)),
    iade: odenecek < 0 ? _yuvarla(-odenecek) : 0,
    net_kalan: _yuvarla(kazanc - Math.max(hesaplanan, 0)),
    parametreler: [sm, gv],
  };
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
    tapuHarciHesapla,
    issizlikOdenegiHesapla,
    kiraGelirVergisiHesapla,
    yillikIzinHesapla,
    fazlaMesaiHesapla,
    alimGucuHesapla,
    icerikGeliriHesapla,
    bilesikFaizHesapla,
    birikimHedefiHesapla,
    hisseMaliyetHesapla,
    lotHesapla,
    yakitMaliyetiHesapla,
    boyaHesapla,
    basaBasHesapla,
    karZararHesapla,
    temettuVerimiHesapla,
    kartBorcuHesapla,
    serbestMeslekVergiHesapla,
    ICERIK_RPM_ADIMLARI,
    brutdenNetUcret,
    nettenBrutUcret,
    kidemIhbarHesapla,
    krediTaksitHesapla,
    yuzdeHesapla,
    sonucParametreleriGecerliMi,
  };
}
