# -*- coding: utf-8 -*-
"""
Maliyeti Ne? - Sohbet asistani

NEDEN VAR: kullanicilar "bana buzdolabi bul", "150 kisilik dugun kac
para" diye YAZMAK istiyor. Arama kutusu bunu kismen cozuyor ama "200
kisilik dugun ne tutar" gibi HESAP gerektiren soruyu cozmuyor.

NEDEN LLM DEGIL - en kritik tasarim karari:
Bu sitenin tum degeri "fiyat uydurmuyoruz" iddiasinda. Bir dil modeli
"buzdolabi 25.000 TL" derse ve verimiz 30.552 diyorsa, o iddia biter.
Bu yuzden asistan CEVAP URETMIYOR - cevaplari VERIDEN SECIYOR:
  - Rakamlar dogrudan /veri/*.json'dan geliyor
  - Cumleler sabit sablonlar; degisken yalnizca rakam, kalem adi, tarih
  - Eslesme bulunamazsa UYDURMUYOR, "bunu olcmuyoruz" diyor
Yani halusinasyon teknik olarak IMKANSIZ, "dikkatli prompt" meselesi
degil - model yok ki uydursun.

Ne yapabiliyor:
  1. Kalem fiyati        "buzdolabi kac para"   -> segment + kaynak + link
  2. Olcekli hesap       "200 kisilik dugun"    -> gercek hesaplama
  3. Grup butcesi        "beyaz esya"           -> senaryo sayfasi + tutar
  4. Kapsam sorusu       "kira", "tadilat"      -> durustce "olcmuyoruz"
  5. Yontem sorusu       "nereden aliyorsunuz"  -> metodolojiye
Hicbiri icin sunucu gerekmiyor; tamami client-side, veri gomulu.
"""

from __future__ import annotations

import json
from pathlib import Path

import sayfa_uret as su

SITE_KOK = su.SITE_KOK

# Olcmedigimiz ama sorulacagi kesin olan konular. Bunlara "bilmiyorum"
# demek yerine NEDEN olcmedigimizi soylemek hem durust hem faydali.
KAPSAM_DISI = [
    {"anahtar": ["kira", "kiralik"], "cevap":
     "Kira ölçmüyoruz. Aynı şehirde iki mahalle arasında ikiye "
     "katlanabildiği için tek bir sayı vermek yanıltıcı olurdu."},
    {"anahtar": ["konut", "ev fiyat", "daire", "emlak"], "cevap":
     "Konut fiyatı kapsam dışında — ölçtüğümüz şey evin kendisi değil, "
     "içine giren eşya."},
    {"anahtar": ["tadilat", "boya badana", "iscilik", "işçilik", "usta"], "cevap":
     "Tadilat ve işçilik ölçmüyoruz. Bu fiyatlar internette listelenmiyor, "
     "telefonla soruluyor; güvenilir biçimde ölçemediğimiz için kapsam "
     "dışında bırakıyoruz."},
    {"anahtar": ["balayi", "balayı", "tatil", "otel"], "cevap":
     "Balayı ve tatil henüz kapsamda değil. Dinamik fiyatlı oldukları için "
     "(aynı otel gün içinde bile değişiyor) standart fiyat serisi modelimize uymuyor."},
    {"anahtar": ["yakit", "yakıt", "benzin", "mazot"], "cevap":
     "Yakıt fiyatı ölçmüyoruz. Araç endeksimiz satın alma anını kapsıyor; "
     "kullanım giderleri ayrı bir konu."},
    {"anahtar": ["servis", "yemek ucreti", "okul ucreti", "okul ücreti", "kayit"], "cevap":
     "Okul servisi, yemek ve kayıt ücreti kapsam dışında — okula ve şehre "
     "göre o kadar değişiyor ki tek bir rakam yanıltıcı olur."},
]

YONTEM_ANAHTARLARI = [
    "nereden", "nasil", "nasıl", "kaynak", "guvenilir", "güvenilir",
    "dogru mu", "doğru mu", "yontem", "yöntem", "metodoloji", "kim",
]


def asistan_verisi(veri_kok: Path | None = None) -> dict:
    """Asistanin konusabilecegi HER SEY. Disinda bir sey soyleyemez."""
    kok = veri_kok or SITE_KOK / "veri"
    kalemler = []
    hesaplar = {}
    for vertikal, conf in su.VERTIKALLER.items():
        dosya = kok / f"{vertikal}.json"
        if not dosya.exists():
            continue
        try:
            veri = json.loads(dosya.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        km = veri.get("kalemler") or {}
        tarih = veri.get("guncelleme_tarihi", "")
        sayfalar = {s["id"]: s["slug"] for s in conf.get("kalem_sayfalari", [])}

        for t in conf["kalemler"]:
            k = km.get(t["id"])
            if not k or not k.get("genel_medyan"):
                continue
            slug = sayfalar.get(t["id"])
            kaynaklar = sorted({
                x["site"] for x in (k.get("kaynaklar") or [])
                if (x.get("toplam_urun") or 0) > 0 and x.get("site")
            })
            kalemler.append({
                "ad": su._kisa_kalem_adi(t["ad"]),
                "grup": t.get("grup") or conf["ad"],
                "endeks": conf["ad"],
                "birim": "kişi başı" if t.get("birim") == "kisi_basi" else "",
                "orta": su.kalem_deger(k, "orta"),
                "eko": su.kalem_deger(k, "dusuk"),
                "ust": su.kalem_deger(k, "luks"),
                "urun": k.get("toplam_urun"),
                "kaynak": len(kaynaklar),
                "kaynaklar": ", ".join(kaynaklar),
                "tarih": tarih,
                "yol": f"/{conf['yol']}/{slug}/" if slug else f"/{conf['yol']}/",
                # Segment tutarsizsa asistan da segment SOYLEMEZ
                "segmentsiz": bool(k.get("segment_tutarsiz")),
            })

        # Olcekli hesap katsayilari (ana sayfa hesaplayicisiyla ayni mantik)
        if conf.get("hesaplayici_var", True) and conf.get("hizli_hesap", True):
            segmentler = {}
            for seg in ("ekonomik", "orta", "luks"):
                t1, _ = su.ornek_toplam_hesapla(conf, km, olcek=1, segment=seg)
                t2, _ = su.ornek_toplam_hesapla(conf, km, olcek=2, segment=seg)
                if t1:
                    segmentler[seg] = {"sabit": t1 - (t2 - t1), "kisi": t2 - t1}
            if len(segmentler) == 3:
                hesaplar[vertikal] = {
                    "ad": conf["ad"],
                    "yol": conf["yol"],
                    "olcek_var": any(x.get("birim") == "kisi_basi" for x in conf["kalemler"]),
                    "varsayilan": conf["olcek_varsayilan"],
                    "segmentler": segmentler,
                    "tarih": tarih,
                }

    # Grup butceleri (senaryo sayfalari)
    gruplar = []
    try:
        import senaryo
        for vertikal, senaryolar in senaryo.GRUP_SENARYOLARI.items():
            dosya = kok / f"{vertikal}.json"
            if not dosya.exists():
                continue
            km = json.loads(dosya.read_text(encoding="utf-8")).get("kalemler") or {}
            conf = su.VERTIKALLER[vertikal]
            for s in senaryolar:
                hedef = set(s["gruplar"])
                toplam = sum(
                    su.kalem_deger(km.get(t["id"]), "orta") or 0
                    for t in conf["kalemler"] if t.get("grup") in hedef
                )
                if toplam:
                    gruplar.append({
                        "ad": s["baslik"], "anahtar": [x.lower() for x in s["gruplar"]],
                        "toplam": toplam, "yol": f"/{conf['yol']}/{s['slug']}/",
                    })
    except ImportError:
        pass

    return {
        "kalemler": kalemler,
        "hesaplar": hesaplar,
        "gruplar": gruplar,
        "kapsam_disi": KAPSAM_DISI,
        "yontem": YONTEM_ANAHTARLARI,
    }


ASISTAN_JS = """
(function () {
  var D = __VERI__;
  var bicim = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
  function para(n) { return bicim.format(Math.round(n)) + " TL"; }
  function sade(s) {
    return (s || "").toLocaleLowerCase("tr")
      .replace(/ı/g, "i").replace(/ş/g, "s").replace(/ğ/g, "g")
      .replace(/ü/g, "u").replace(/ö/g, "o").replace(/ç/g, "c");
  }

  // --- Cevap uretimi: HER cumle sabit sablon, degisken yalnizca veri ---
  function kalemCevabi(k) {
    var s = "<strong>" + k.ad + "</strong> ";
    if (k.segmentsiz) {
      s += "ortalama <strong>" + para(k.orta) + "</strong>" + (k.birim ? " (" + k.birim + ")" : "") + ". ";
      s += "Bu kalemde segment kırılımı güvenilir değil, o yüzden tek rakam veriyorum. ";
    } else {
      s += "orta segmentte <strong>" + para(k.orta) + "</strong>" + (k.birim ? " (" + k.birim + ")" : "") + ". ";
      if (k.eko && k.ust) s += "Ekonomik " + para(k.eko) + ", üst " + para(k.ust) + ". ";
    }
    s += "<span class='as-kaynak'>" + k.urun + " üründen, " + k.kaynak +
         " kaynaktan (" + k.kaynaklar + ") · " + k.tarih + "</span>";
    s += "<a class='as-link' href='" + k.yol + "'>Ayrıntılı sayfa →</a>";
    return s;
  }

  function hesapCevabi(h, olcek, segment) {
    var seg = h.segmentler[segment] || h.segmentler.orta;
    var n = h.olcek_var ? olcek : 1;
    var toplam = seg.sabit + seg.kisi * n;
    var s = (h.olcek_var ? "<strong>" + n + " kişilik</strong> " : "") +
      h.ad.toLocaleLowerCase("tr") + " " +
      (segment === "orta" ? "orta segmentte" : segment === "ekonomik" ? "ekonomik tercihlerle" : "üst segmentte") +
      " <strong>" + para(toplam) + "</strong>. ";
    if (h.olcek_var && seg.kisi) {
      s += "Bunun " + para(seg.kisi * n) + " kadarı kişi başı kalemlerden — " +
           "listeden çıkardığınız her 10 kişi yaklaşık " + para(seg.kisi * 10) + " tasarruf. ";
    }
    s += "<span class='as-kaynak'>Ölçüm: " + h.tarih + "</span>";
    s += "<a class='as-link' href='/" + h.yol + "/hesaplayici/'>Kalem kalem hesapla →</a>";
    return s;
  }

  // --- Niyet tanima: kural tabanli, model yok ---
  function cevapla(soru) {
    var q = sade(soru);
    if (!q) return null;

    // 1) Kapsam disi konular - "bilmiyorum" degil, NEDEN olcmedigimiz
    for (var i = 0; i < D.kapsam_disi.length; i++) {
      var kd = D.kapsam_disi[i];
      for (var j = 0; j < kd.anahtar.length; j++) {
        if (q.indexOf(sade(kd.anahtar[j])) !== -1) {
          return kd.cevap + "<a class='as-link' href='/sss/'>Neyi ölçüyoruz? →</a>";
        }
      }
    }

    // 2-4) Hesap / grup / kalem YARISIYOR - en SPESIFIK eslesme kazanir.
    // Onceki surumde hesap once bakiliyordu ve "okul cantasi kac para"
    // sorusu OKUL BUTCESINI donduruyordu ("okul" kelimesi endeks adiyla
    // eslesip kalem kontrolune hic gelmiyordu). Artik eslesme uzunlugu
    // karsilastiriliyor: "okul cantasi" (12) > "okul" (4).
    var sayi = q.match(/(\\d{2,4})\\s*(kisi|kişi|davetli)?/);
    var segment = q.indexOf("ekonomik") !== -1 ? "ekonomik"
                : (q.indexOf("luks") !== -1 || q.indexOf("ust segment") !== -1) ? "luks" : "orta";

    var aday = null, puan = 0;

    for (var v in D.hesaplar) {
      var h = D.hesaplar[v], ha = sade(h.ad);
      if (q.indexOf(ha) === -1) continue;
      // Sayi varsa hesap niyeti guclu ("200 kisilik dugun")
      var hp = ha.length + (sayi && h.olcek_var ? 20 : 0);
      if (hp > puan) {
        puan = hp;
        aday = { tip: "hesap", h: h,
                 olcek: (sayi && h.olcek_var) ? parseInt(sayi[1], 10) : h.varsayilan };
      }
    }

    for (var g = 0; g < D.gruplar.length; g++) {
      var gr = D.gruplar[g];
      for (var a = 0; a < gr.anahtar.length; a++) {
        var ga = sade(gr.anahtar[a]);
        if (q.indexOf(ga) !== -1 && ga.length > puan) {
          puan = ga.length; aday = { tip: "grup", g: gr };
        }
      }
    }

    for (var m = 0; m < D.kalemler.length; m++) {
      var k = D.kalemler[m], ka = sade(k.ad);
      var parcalar = ka.split(/[\\s\\/(),-]+/).filter(function (x) { return x.length > 2; });
      var kp = 0;
      if (q.indexOf(ka) !== -1) kp = ka.length + 10;
      else {
        for (var pz = 0; pz < parcalar.length; pz++) {
          if (q.indexOf(parcalar[pz]) !== -1) kp = Math.max(kp, parcalar[pz].length);
        }
      }
      if (kp >= 4 && kp > puan) { puan = kp; aday = { tip: "kalem", k: k }; }
    }

    if (aday) {
      if (aday.tip === "hesap") return hesapCevabi(aday.h, aday.olcek, segment);
      if (aday.tip === "kalem") return kalemCevabi(aday.k);
      return "<strong>" + aday.g.ad + "</strong> orta segmentte <strong>" +
        para(aday.g.toplam) + "</strong>." +
        "<a class='as-link' href='" + aday.g.yol + "'>Kalem kalem gör →</a>";
    }

    // 5) Yontem sorulari
    for (var y = 0; y < D.yontem.length; y++) {
      if (q.indexOf(sade(D.yontem[y])) !== -1) {
        return "Kaynakları ayın 5'i ve 20'sinde yeniden tarıyoruz; her seri son başarılı ölçüm tarihini taşır. " +
          "Her rakamın yanında kaç üründen derlendiği, hangi kaynaklardan geldiği " +
          "ve ölçüm tarihi yazıyor — hiçbir fiyatı tahmin etmiyoruz." +
          "<a class='as-link' href='/sss/'>Sık sorulan sorular →</a>";
      }
    }

    // 6) UYDURMA YOK: eslesme bulunamadi
    return "Bunu ölçmüyorum — yalnızca kendi ölçtüğüm kalemler hakkında " +
      "konuşabiliyorum, tahmin yürütmüyorum." +
      "<a class='as-link' href='/veri/'>Ölçtüğüm her şey →</a>";
  }

  // --- Arayuz ---
  var kok = document.getElementById("asistan");
  if (!kok) return;
  var akis = kok.querySelector(".as-akis");
  var form = kok.querySelector("form");
  var girdi = kok.querySelector("input");

  function balon(metin, kim) {
    var d = document.createElement("div");
    d.className = "as-balon as-" + kim;
    d.innerHTML = metin;
    akis.appendChild(d);
    akis.scrollTop = akis.scrollHeight;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var s = girdi.value.trim();
    if (!s) return;
    balon(s.replace(/[<>]/g, ""), "ben");
    girdi.value = "";
    var c = cevapla(s);
    setTimeout(function () { balon(c, "asistan"); }, 120);
  });

  kok.querySelectorAll(".as-oneri").forEach(function (b) {
    b.addEventListener("click", function () {
      girdi.value = b.textContent;
      form.dispatchEvent(new Event("submit"));
    });
  });
})();
"""


def asistan_js(veri: dict) -> str:
    return "<script>" + ASISTAN_JS.replace(
        "__VERI__", json.dumps(veri, ensure_ascii=False)
    ) + "</script>\n"


ASISTAN_HTML = """  <section class="asistan" id="asistan">
    <h2>Sorun, ölçtüğüm rakamla cevaplayayım</h2>
    <p class="asistan-alt">Uydurmam — bilmediğim şeye "bilmiyorum" derim.</p>
    <div class="as-akis" role="log" aria-live="polite">
      <div class="as-balon as-asistan">
        Merhaba. Ölçtüğüm {kalem_sayisi} fiyat serisi hakkında soru sorabilirsiniz:
        bir ürünün fiyatı, kaç kişilik bir düğünün tutarı, ya da neyi
        ölçmediğimiz.
      </div>
    </div>
    <div class="as-oneriler">
      <button type="button" class="as-oneri">buzdolabı kaç para</button>
      <button type="button" class="as-oneri">200 kişilik düğün</button>
      <button type="button" class="as-oneri">beyaz eşya bütçesi</button>
      <button type="button" class="as-oneri">kira ölçüyor musunuz</button>
    </div>
    <form autocomplete="off">
      <input type="text" aria-label="Sorunuzu yazın" placeholder="Bir şey sorun…">
      <button type="submit" class="birincil-buton">Sor</button>
    </form>
  </section>
"""


def asistan_html(veri: dict) -> str:
    return ASISTAN_HTML.replace("{kalem_sayisi}", str(len(veri["kalemler"])))
