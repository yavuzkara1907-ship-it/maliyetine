# Maliyetine.com.tr — Proje Hafızası

> Her oturumun başında önce bunu oku. Kararları değiştirmeden önce
> Yavuz'a sor. Oturum sonunda "Teknik Durum" ve "Yapılacaklar"
> bölümlerini güncelle.

## Proje Sahibi
- Yavuz. Türkçe konuşur. Doğrudan iletişim ister, uzun açıklama değil
  aksiyon bekler. Teknik detayı ona sormak yerine sen çöz ve sonucu
  bildir.
- Python bilir, HTML/CSS'e hakim. Dağıtım/içerik tarafı güçlü.
- Soğuk satış YOK. Self-serve model.

## Vizyon (tek cümle)
Türkiye için canlı, doğrulanabilir maliyet endeksi: "2026'da X kaça mal
olur?" sorusunun güvenilir tek kaynağı olmak — hem insanlar hem AI
motorları için.

## Stratejik Zemin
- Tıkanıklık: insanlar her şeyi AI'a soruyor, klasik bilgi ürünleri
  değersizleşiyor.
- Çözüm: AI'ın BİLMEDİĞİ veriyi üretmek. AI'ın taze yerel fiyat verisi
  yok; enflasyon her rakamı 3 ayda eskitiyor.
- GEO hedefi: AI motorlarının alıntılamak zorunda olduğu kaynak olmak.
  Hedef cümle: "Maliyetine'ye göre 2026'da ... ortalama X TL."
- Yıl konsepti markanın parçası: her yıl "2027 versiyonu". Yıllık
  karşılaştırmalar ("düğün maliyeti %X arttı") bedava basın malzemesi.

## KIRMIZI ÇİZGİ — Veri Metodolojisi
- **Varsayılan/asıl kural değişmedi:** fiyat verisi ASLA LLM'in kendi
  bilgisinden üretilmez. Kaynak: gerçek e-ticaret/ilan/karşılaştırma
  sitelerinden kazıma (robots.txt'e ve rate-limit'e saygılı) +
  gerektiğinde insan teyidi. AI'ın rolü: kaynak değil RAFİNERİ —
  temizleme, kategorize etme, aykırı değer ayıklama, özetleme.
- Yayınlanan her GERÇEK KAYNAK rakamının yanında: kaynak, derleme tarihi,
  örneklem büyüklüğü ("14 Temmuz'da 2.340 üründen derlendi").
- Metodoloji sayfası zorunlu. Güven = tek ürün. Rakip çöp sitelerden
  tek farkımız bu.
- **İSTİSNA (2026-07-24, Yavuz'un açık talimatıyla):** kazıma kaynağı
  henüz bulunamamış kalemler (takı/altın, yemek/ikram, fotoğrafçı,
  orkestra/DJ, gelin arabası, kuaför/makyaj, organizasyon, nikah
  işlemleri) için WebSearch ile genel piyasa araştırmasından türetilmiş
  TEK SEFERLİK bir tahmini değer kullanılıyor ("bunlar önemli, senin
  bilgin dahilinde olan fiyatlandırmayı kullan" talimatı). Bu istisna
  KATI ŞARTLARLA sınırlı, sessizce genişletilmemeli:
  - Her tahmini kalem `assets/js/dugun-kalemler.js` ve
    `scraper/sayfa_uret.py`'de `kaynak_tipi: "tahmini"` ile ayrı
    tanımlanır, gerçek kaynaklı kalemlerle AYNI listeye/koda KARIŞTIRILMAZ.
  - UI'da HER YERDE (hesaplayıcı, endeks sayfası, tablo satırı) görünür
    bir `"Tahmini"` etiketiyle işaretlenir — gerçek kaynak rozetinden
    (kaynak sayısı) görsel olarak ayrıdır.
  - Cevap metni/toplam her zaman "gerçek kaynaklardan X TL, tahmini
    kalemlerden Y TL" şeklinde kırılımı açıkça belirtir; hiçbir zaman
    tahmini bir toplamı "N bağımsız kaynaktan derlendi" gibi göstermez.
  - Gerçek bir kazıma kaynağı bulunduğunda o kalem tahmini listeden
    ÇIKARILIP gerçek listeye taşınır — tahmini kalıcı bir durum değil.
  - Metodoloji sayfası bu ayrımı (`/dugun/metodoloji/` "Gerçek kaynak vs.
    tahmini kalemler" bölümü) açıkça anlatır, gizlemez.

## ÇOK KAYNAK KURALI (önemli)
- **Tek kaynağa BAĞLI KALINMAZ.** Akakçe sadece başlangıç kaynağıdır.
- Sebep 1 (kırılganlık): tek kaynak tasarım değiştirir/engellerse endeks
  tamamen durur.
- Sebep 2 (güvenilirlik): tek kaynak o sitenin fiyat politikasını
  yansıtır, piyasayı değil. "3 bağımsız kaynaktan derlendi" cümlesi hem
  okuyucu hem AI motorları için çok daha güçlü.
- **Hedef: kalem başına en az 2, ideal 3 kaynak.**
- Kaynak tipleri:
  1. Fiyat karşılaştırma siteleri (Akakçe vb.)
  2. Markaların/mağazaların kendi siteleri (genelde daha az korumalı,
     daha gerçekçi segment fiyatı)
  3. İkinci el / ilan platformları (alt segment için)
  4. Sektör platformları (düğün, tadilat vb. hizmet listeleri)
  5. **Doğrulama katmanı: TÜİK TÜFE alt kalemleri** (giyim, lokanta,
     kişisel bakım, mobilya). Kendi verimizle karşılaştırılır.
- **Çapraz doğrulama uyarısı:** kaynaklar arası fark %30'u aşarsa
  sistem uyarı versin (ya kazıma hatası ya farklı segment — ikisi de
  bilinmesi gereken şey). TÜİK trendiyle ters düşen sıçramalar
  karantinaya alınır.
- Metodoloji sayfasında "resmi verilerle çapraz doğrulanmıştır" ifadesi
  hedeflenir — ciddi güven sinyali.

## Ürün Kararları
- Format: her kalem için düşük / orta / lüks segment (persentil:
  ≤P25 düşük, P25–P75 orta, >P75 lüks) + min/medyan/max + örneklem
  sayısı + tarih.
- Aylık güncelleme. Aylık JSON'lar biriktirilir → fiyat geçmişi
  grafikleri (GEO + basın malzemesi).
- Başlangıç 2 vertikal: (1) Düğün maliyeti, (2) Ev tadilatı maliyeti.
  Sonra: ev kurma, 0 km araç, tatil, ilkokul, üniversite.
- Her vertikal üçlüsü: hesaplayıcı + endeks sayfası + metodoloji sayfası.
- Şehir/segment kırılımı hedeflenir.
- UYARI: Kaynak seçimi metodolojinin kendisidir. Genel e-ticaret
  sitesindeki 1.500 TL'lik "gelinlik" ile gelinlik evindeki 60.000 TL'lik
  gelinlik aynı ürün değil. Farklı segmentler ayrı kaynaklardan
  toplanır, karıştırılmaz.

### Vertikal veri tipi ayrımı (planlama için)
- **Ürün bazlı kalemler** (ev kurma, 0 km araç, gelinlik, alyans,
  okul malzemesi): fiyatlar açıkta, mevcut motorla neredeyse bedava
  gelir. Kolay.
- **Hizmet/işçilik bazlı kalemler** (tadilat işçiliği, düğün salonu,
  fotoğrafçı, üniversite yaşam gideri): internette listelenmez,
  telefonla sorulur. İlan siteleri, meslek odası birim fiyat tarifeleri,
  TÜİK verileri ve küçük elle toplanan örneklem gerekir. Zor.
- Bu yüzden ürün bazlı vertikaller önce yayına alınır.

## DÜĞÜN VERTİKALİ — Kalem Listesi (tam kapsam)
Hesaplayıcı bu kalemleri toplar. Her kalem: segment + kaynak + tarih.

**Ürün bazlı (kolay):**
1. Gelinlik (alt kırılım: hazır giyim / gelinlik evi / ikinci el —
   ayrı segment, karıştırılmaz)
2. Damatlık / takım elbise
3. Alyans
4. Takı ve altın (canlı altın/gram fiyatından hesaplanır; en oynak
   kalem, günlük güncellenebilir)
5. Nikah şekeri
6. Davetiye
7. Gelin ayakkabısı, duvak, aksesuar

**Hizmet bazlı (zor — kaynak sınırlı, "başlangıç fiyatı" uyarısı ile):**
8. Düğün salonu / davet (kişi başı × davetli sayısı)
9. Yemek/ikram (salona dahil değilse ayrı)
10. Fotoğraf ve video
11. Orkestra / DJ
12. Gelin arabası
13. Kuaför ve makyaj
14. Organizasyon/süsleme (çiçek, masa düzeni)
15. Nikah işlemleri (resmi harçlar)

**Ayrı gösterilecek:**
16. Balayı (ayrı bölüm; tatil vertikaliyle veri paylaşır — aynı kaynak
    iki vertikali besler)

- Kaynağı bulunamayan kalemler ilk sürümde tahmini değerle konur ve
  sayfada AÇIKÇA "tahmini" olarak işaretlenir. Dürüstlük ürünün parçası.
- Hesaplayıcı girdileri: şehir, davetli sayısı, segment (ekonomik/orta/
  lüks), opsiyonel kalem seçimleri.

## Gelir Modeli (sıralı)
1. Reklam (tüketici tarafı ücretsiz)
2. Affiliate (gerçek ürün linkleri — sadece gerçek veriyle mümkün)
3. Pro rapor / araç aboneliği (ustalar, müteahhitler, düğün firmaları)

## GEO Gereksinimleri (her sayfada)
- İlk 40-60 kelimede net, alıntılanabilir cevap bloğu.
- schema.org yapılandırılmış veri, güncelleme tarihi görünür.
- Soru formatında başlıklar ("2026'da İstanbul'da düğün kaça mal olur?").
- robots.txt AI bot'larına açık (GPTBot vb. engellenmez).

## Altyapı Kararları (KESİN)
- Domain: **maliyetine.com.tr** — alındı, DNS Cloudflare'e taşınıyor.
- Hosting: **statik site + Cloudflare Pages**. Ücretsiz. Backend YOK.
- WordPress KULLANILMAYACAK.
- Hesaplayıcılar tarayıcıda JavaScript ile çalışır.
- Kod deposu: GitHub `maliyetine` (private).
- Otomasyon: GitHub Actions (aylık cron).
- A/CNAME kayıtları elle eklenmez; Pages custom domain ekleyince oluşur.
- E-posta: gerekirse Cloudflare Email Routing (ücretsiz).
- Basit tut: gereksiz framework yok, hedef ~10-20K satır toplam kod.

## KAZIYICI MİMARİSİ
Her site için ayrı script YAZILMAZ. Tek motor + kaynak kaydı:

- **`kaynaklar.yaml`** — tüm kaynaklar burada tanımlanır. Yeni site
  eklemek = birkaç satır YAML, kod değil. Alanlar: ad, **site** (bağımsız
  kaynak kimliği — ÇOK KAYNAK KURALI/çapraz doğrulama buna göre
  gruplanır), url, vertikal, kalem, yöntem, (gerekirse)
  css_secicileri, aktif/pasif. Aynı `site` değerine sahip birden fazla
  girdi (ör. Akakçe'nin dar kategorilere bölünmüş 5 sayfası) TEK
  bağımsız kaynak sayılır — ürünleri birleştirilir, tek dosyaya yazılır.
- **Üç katmanlı çıkarım stratejisi, sırayla:**
  1. **JSON-LD** (`application/ld+json`, schema.org/Product) — siteler
     arası ortak, en temiz. ÖNCE BUNU DENE. `ItemList`/`itemListElement`
     ve `@graph` sarmalayıcıları da açılıyor.
  2. **Microdata / meta etiketleri** (`itemprop="price"`, og etiketleri)
  3. **Siteye özel CSS seçiciler** — son çare.
- **Sağlık kontrolü zorunlu:** bir kaynak normalde ~200 ürün dönerken
  ay içinde 3 ürün dönerse SESSİZCE devam etme, uyarı ver ve o ayki
  veriyi karantinaya al. Geçmiş `kaynak_gecmisi.json`'da site-grubu
  bazında (`vertikal/kalem/site`) tutulur.
- **Çapraz doğrulama (ÇOK KAYNAK KURALI):** aynı (vertikal, kalem) için
  ≥2 sağlıklı bağımsız site varsa genel medyanları karşılaştırılır; fark
  %30'u aşarsa uyarı loglanır ve `{kalem}_capraz-dogrulama_{tarih}.json`
  yazılır. TÜİK entegrasyonu henüz yok (bkz. Yapılacaklar).
- **Nazik kazıma:** gerçekçi User-Agent, istekler arası 2+ sn bekleme,
  retry + backoff, ayda bir çalıştırma.
- **robots.txt doğrulaması otomatik:** `urllib.robotparser` ile her URL
  kazımadan önce test edilir (domain başına önbellekli). RET çıkan URL
  atlanır ve loglanır. robots.txt okunamazsa (ağ hatası vb.) İHTİYATLA
  RET kabul edilir — sessizce izin verilmez.
- JS ile render edilen siteler için Playwright katmanı (sadece
  gerekince, henüz eklenmedi).

### Bilinen kaynak kısıtı — Akakçe
- robots.txt: `Allow: /` ama `Disallow: /*?sayfa=*` ve `/*,*,1..7.html`
  → **SAYFALAMA YASAK.**
- Strateji: tek kategoriyi çok sayfa gezmek yerine ÇOK SAYIDA DAR
  KATEGORİNİN 1. SAYFASINI topla (gelinlik, tesettür gelinlik, abiye,
  nişanlık, damatlık, takım elbise, alyans, tek taş...). Hem robots'a
  uygun, hem daha büyük örneklem, hem hazır segment kırılımı.
- Not: robots.txt ≠ kullanım şartları. Ticari yayın için sitenin
  kullanım sözleşmesine de bakılmalı; uzun vadede resmi veri anlaşması
  hedeflenir.
- **GÜNCELLEME (2026-07-24) — Akakçe şu an BIRAKILDI:** robots.txt ONAY
  veriyor ama site Cloudflare bot-doğrulaması ("Bir dakika lütfen...")
  kullanıyor — gerçek bir Chromium (Playwright) ile bile GERÇEK İÇERİK
  DEĞİL, Cloudflare'in JS-challenge sayfası dönüyor
  (`sayfa_tani.py` ile ham HTML incelenerek doğrulandı). Bunu aşmak
  (stealth eklentileri, captcha çözüm servisi vb.) "nazik kazıma"
  ilkesinden uzaklaşıp aktif bot-tespiti atlatmaya kayar. Yavuz'a
  soruldu, **karar: şimdilik bırak** — enerji çalışan kaynaklara
  (Trendyol çalışıyor) ve CSS seçici işine yönlendirildi. `kaynaklar.yaml`'da
  tüm 9 Akakçe girdisi `aktif: false, durum: "birakildi"`. İleride resmi
  bir veri anlaşması olursa yeniden değerlendirilebilir.
  **Etki:** damatlık ve alyans artık tek aktif kaynağa (sırasıyla
  ramsey, atasay) düştü; gelin-ayakkabısı'nın hiç aktif kaynağı kalmadı.

### Bilinen sandbox kısıtı — Claude Code network erişimi
- Claude Code'un (bu sandbox) çalıştığı ortamın proxy politikası, hedef
  sitelere (akakce.com, dugun.com, dugunbuketi.com, armut.com,
  trendyol.com, hepsiburada.com, dolap.com, ramsey.com.tr, atasay.com
  vb.) doğrudan bağlantıyı 403 ile reddediyor
  (`$HTTPS_PROXY/__agentproxy/status`'ta doğrulanabilir). PyPI
  (`pip install`) ise açık — bağımlılık kurulumu ve kod çalıştırma sorun
  değil, sadece hedef sitelere HTTP isteği atmak engelli.
- Sonuç: motor.py'nin robots.txt kontrolü ve gerçek kazıma katmanları
  BU ORTAMDAN gerçek sitelere karşı test edilemiyor. Doğrulama sahte
  HTML fixture'larıyla (`test_motor.py`) yapılıyor — mantığın doğruluğu
  kanıtlanıyor ama gerçek sitelerin JSON-LD/microdata/CSS yapısı henüz
  bilinmiyor.
- Motor bu kısıtla güvenli davranıyor: robots.txt okunamazsa (ki bu
  ortamda hep okunamıyor) ihtiyatla RET kabul ediyor, kaynağı atlıyor,
  0 ürünle "sağlıklı" (ilk çalıştırma, henüz baseline yok) olarak
  kaydediyor. Sandbox'ta çalıştırmak hataya değil sessiz-boş sonuca yol
  açıyor — Yavuz'un yerelinde çalıştırdığında gerçek veri gelecek.

### DÜZELTİLDİ — robots.txt kontrolü 3 ayrı stdlib bug'ı yüzünden yanlış sonuç veriyordu
- Yavuz gerçek Akakçe robots.txt'ini yerelinde `curl` ile çekip paylaştı;
  `python motor.py` çalıştırınca TÜM Akakçe URL'leri (daha önce ONAY
  bekleniyordu) RET çıktı. Kök nedeni bu sandbox'tan da (metni elle
  simüle ederek) doğrulandı — **`urllib.robotparser` (stdlib) 3 ayrı
  yerde yanlış davranıyor:**
  1. `RobotFileParser.read()` robots.txt'i varsayılan urllib User-Agent'i
     ("Python-urllib/x.y") ile çekiyor — birçok sitenin bot koruması bunu
     403'le reddediyor, `read()` de bunu "TÜM URL'ler RET" diye
     yorumluyor (site aslında izin veriyor olsa bile).
  2. `parse()`, aynı kural grubuna ait birden fazla `User-agent:`
     satırıyla onu takip eden kurallar arasında BOŞ SATIR varsa o grubun
     TAMAMINI sessizce düşürüyor — Akakçe'nin robots.txt formatı tam
     olarak bu.
  3. Disallow/Allow desenlerinde **`*` joker karakterini hiç
     desteklemiyor** — `Disallow: /moda/*` harfi harfine "/moda/*"
     dizesini arıyor, gerçek URL'lerde asla eşleşmiyor (kural sessizce
     etkisiz). Akakçe kurallarının neredeyse tamamı joker karakter
     kullanıyor.
- **Düzeltme:** `urllib.robotparser` tamamen bırakıldı, yerine
  `protego` (Scrapy'nin bağımlılığı, Google'ın robots.txt RFC 9309'unu
  doğru uyguluyor) + `requests` (gerçekçi tarayıcı User-Agent'iyla
  robots.txt'i biz çekiyoruz) kullanılıyor. Yavuz'un paylaştığı GERÇEK
  robots.txt metniyle test edildi: `kaynaklar.yaml`'daki 9 Akakçe
  URL'sinin hepsi artık doğru şekilde ONAY veriyor. `requirements.txt`'e
  `protego` eklendi.
- Ders: stdlib'in "çalışıyor gibi görünmesi" yeterli değil — gerçek
  robots.txt formatlarına (çoklu User-agent grubu, joker karakter, bot
  koruması) karşı test edilmeden güvenilmemeli.

## Teknik Durum
- GitHub repo `maliyetine` oluşturuldu.
- **Kazıma motoru v0.6**: robots.txt kontrolü `protego`'ya taşındı (bkz.
  yukarıdaki "DÜZELTİLDİ" notu) + ÇOK KAYNAK KURALI'na göre site-bazlı
  gruplama + çapraz doğrulama (v0.4'ten devam) + WAF/TLS korumalı
  siteler için Playwright son-çare katmanı (bkz. altındaki not).
  - `scraper/sayfa_tani.py` (yeni): CSS seçici doldurmak için F12 yerine
    kullanılacak teşhis aracı — bir URL'i çeker, JSON-LD/microdata
    varlığını, en sık tekrar eden class isimlerini ve "TL"/"₺" içeren
    metinleri raporlar.
  - `scraper/motor.py`: `gruplar_halinde_topla()` yaml girdilerini
    (vertikal, kalem, **site**) bazında gruplar — aynı site'nin birden
    fazla dar-kategori girdisi tek kaynak sayılıp birleştirilir.
    `grup_isle()` her site-grubu için temizleme + segmentleme + sağlık
    kontrolü + kayıt yapar (`kaynak_gecmisi.json` anahtarı artık
    `vertikal/kalem/site`). `capraz_dogrula()` aynı kalemdeki ≥2 sağlıklı
    sitenin genel medyanını karşılaştırıp %30 eşiğini aşan farkta uyarı
    üretir ve `{kalem}_capraz-dogrulama_{tarih}.json` yazar.
  - `scraper/kaynaklar.yaml`: her girdiye `site` alanı eklendi. Yeni
    kalemler: **damatlik** (akakce + ramsey), **alyans** (akakce genel +
    14 ayar + atasay). **gelinlik** artık 5 bağımsız site adayına sahip
    (akakce, dolap [ikinci el], dugunbuketi [gelinlik evi/lüks segment],
    trendyol, hepsiburada) — sadece akakce aktif, gerisi robots.txt
    doğrulaması bekliyor. Tüm yeni URL'ler WebSearch ile doğrulandı
    (uydurulmadı).
  - `scraper/test_motor.py`: 40 test, hepsi PASS. Yeni testler (bu
    oturumda +5): joker karakter senaryosu, çoklu User-agent grubu +
    boş satır senaryosu, 403/404/5xx robots.txt HTTP durumları — hepsi
    gerçek Akakçe formatını simüle ediyor. Ayrıca: aynı-site birleştirme,
    çapraz doğrulama (uyarı üretme/üretmeme, sağlıksız kaynağı dışlama,
    kalem başına ayrı raporlama), bilgilendirici "kapsam raporu" testi.
  - `python motor.py --cikti /tmp/...` ile gerçek yaml'a karşı tekrar
    uçtan uca çalıştırıldı: çökme yok, exit 0.
  - `scraper/robots_kontrol.py` v0.2'ye güncellendi (aynı protego
    düzeltmesi) — Yavuz'un yerelinde tekil URL hızlı kontrolü için.
- **Yavuz'un yerelinde robots.txt kontrolü yapıldı (2026-07-23), SONRA
  protego düzeltmesiyle DÜZELTİLDİ:**
  - İlk turda (eski, hatalı urllib.robotparser ile) TÜM Akakçe URL'leri
    yanlışlıkla RET çıktı — bu, gerçek bir robots.txt engeli değil,
    yukarıdaki "DÜZELTİLDİ" notundaki 3 stdlib bug'ının sonucuydu.
  - Yavuz gerçek robots.txt metnini paylaştı, protego ile yeniden analiz
    edildi: **9/9 Akakçe URL'si aslında ONAY** (zaten `aktif: true`
    olarak duruyordu, değişiklik gerekmedi — sadece motor.py'nin kendi
    değerlendirmesi artık doğru).
  - Aynı ilk turda Trendyol/Armut/Ramsey/Atasay ONAY, Hepsiburada/Dolap/
    DüğünBuketi(3 sayfa) RET çıkmıştı — bunlar eski (bug'lı) motor.py
    ile değil, doğrudan `robots_kontrol.py` ile o an test edilmişti; o
    scriptin eski sürümü de aynı 3 bug'a sahipti, yani **bu sonuçlar da
    şüpheli olabilir** ve protego'lu yeni `robots_kontrol.py` ile
    TEKRAR doğrulanmalı (özellikle RET çıkanlar — belki onlar da aslında
    ONAY'dı ve yanlışlıkla pasif bırakıldı).
  - CSS seçiciler henüz hiçbir yeni kaynak için girilmedi (Ramsey,
    Atasay, Trendyol, Armut) — motor JSON-LD/microdata katmanıyla
    otomatik çözmeyi deneyecek, bulamazsa sağlık kontrolü karantinaya
    alacak.
- **Yavuz'un yerelinde protego'lu ikinci turda TEKRAR test edildi
  (2026-07-24):**
  - robots.txt tarafı artık doğru: DüğünBuketi'nin 3 sayfası da gerçekte
    **ONAY** çıktı (şüphelendiğimiz gibi, eski hatalı script yanlış RET
    vermiş) → hepsi `aktif: true` yapıldı. Hepsiburada/Dolap robots.txt'in
    KENDİSİNE erişimde gerçek 403 alıyor (script hatası değil, sitenin
    kendi engeli) — ihtiyatlı RET doğru, bunlar gerçekten kullanılamaz.
  - **SORUN — Akakçe/Trendyol robots.txt ONAY veriyor ama gerçek sayfa
    isteğinde 403 alıyor.** Genişletilmiş tarayıcı başlıkları (Accept,
    Sec-Fetch-*, vb.) denendi, Yavuz'un yerelinde TEKRAR test edildi:
    **çözmedi**, hâlâ 403. Yani header eksikliği değil — TLS parmak izi
    veya benzeri WAF seviyesinde bir tespit.
  - **ÇÖZÜM — Playwright katmanı eklendi (motor v0.6).** `requests` yerine
    gerçek bir Chromium ile çeken `getir_playwright()` yazıldı;
    `kaynaklar.yaml`'da `render_gerekli: true` alanıyla seçiliyor (Akakçe'nin
    9 URL'sine ve Trendyol'a eklendi; Ramsey/Atasay/Armut/DüğünBuketi
    `requests` ile zaten 200 dönüyor, onlara gerek yok). Bu sandbox'ta
    Playwright'ın kendi tarayıcı indirici sistemi de engelli (`cdn.playwright.dev`
    "host not permitted") — ama ortamda önceden kurulu bir Chromium
    bulundu (`/opt/pw-browsers/chromium`, farklı revizyon) ve
    `executable_path` ile açıkça verilince ÇALIŞTI: tarayıcı gerçekten
    açılıp sayfaya gitmeyi denedi, sadece son adımda (asıl siteye
    bağlanma) proxy engeline takıldı (`ERR_TUNNEL_CONNECTION_FAILED`) —
    yani mekanik olarak doğrulandı, sadece hedef siteye erişim yine
    sandbox kısıtından dolayı test edilemedi. 44 test (4 yeni: başarılı
    çekim, playwright kurulu değilse hata vermeden None dönmesi,
    render_gerekli true/false dallanması) hepsi PASS.
  - **Yavuz'un yerelinde bir kerelik ek kurulum gerekiyor:**
    `pip install playwright && playwright install chromium`
    (requirements.txt'e playwright eklendi, ama tarayıcı ikili dosyası
    ayrı indirilir).
  - **Ayrı sorun — Ramsey/Atasay/Armut 200 dönüyor ama "0 ürün (hicbiri
    katmani)"**: bu 3 site `requests` ile erişilebilir, demek ki JSON-LD/
    microdata/CSS'in hiçbiri eşleşmedi. CSS seçici doldurmak için F12
    yerine yeni eklenen `scraper/sayfa_tani.py` scripti kullanılabilir —
    sayfayı çekip JSON-LD/microdata varlığını, en sık tekrar eden class
    isimlerini ve "TL"/"₺" içeren metinleri raporlar; çıktısı paylaşılırsa
    css_secicileri buradan doldurulabilir.
- **Yavuz'un yerelinde `python motor.py` GERÇEKTEN çalıştırıldı
  (2026-07-24) — İLK GERÇEK VERİ:**
  - **Trendyol/gelinlik: 23 ürün, JSON-LD katmanıyla, başarılı.**
    Playwright'a bile gerek kalmadan `requests` + JSON-LD çalıştı
    (`render_gerekli: true` gereksiz olabilir, ama zararı yok — sadece
    yavaşlatır. İleride kaldırılabilir).
  - Akakçe'nin 9 URL'si de artık 403 ALMIYOR (Playwright çalışıyor,
    site engeli aşıldı) ama hepsi "0 ürün (hicbiri katmani)" — JSON-LD/
    microdata yok, CSS seçici gerekiyor.
  - Ramsey, Atasay, Armut, DüğünBuketi'nin 3 sayfası da aynı durumda:
    erişilebiliyor, 0 ürün, CSS seçici gerekiyor.
  - **Sonuç: network/bot-engeli sorunu tamamen çözüldü. Kalan tek şey
    CSS seçici doldurma işi** — bu artık salt bir "F12/sayfa_tani.py
    çalıştır, seçiciyi yaz" mekaniği, mimari sorun değil.
  - `sayfa_tani.py` v0.1'de bir eksik bulundu: Akakçe/Trendyol gibi
    siteler için de salt `requests` kullanıyordu, o da 403 alırdı.
    v0.2'de düzeltildi — `requests` 403 alırsa otomatik olarak
    `motor.getir_playwright()`'a düşüyor, Yavuz'un ayrı bir bayrak
    belirtmesine gerek yok.
- **Akakçe TAMAMEN BIRAKILDI (2026-07-24):** Playwright (gerçek Chromium)
  ile bile Akakçe'nin gerçek içeriği değil, Cloudflare'in "Bir dakika
  lütfen..." JS-challenge sayfası döndü. Bu robots.txt meselesi değil,
  WAF seviyesinde aktif bot tespiti — aşmak "nazik kazıma" ilkesinden
  uzaklaşıp aktif tespit atlatmaya kayardı. Yavuz'a AskUserQuestion ile
  soruldu, **karar: bırak**. Tüm 9 Akakçe girdisi `aktif: false,
  durum: "birakildi"`. Boşalan yerlere Trendyol + marka mağazaları
  (Vakko, Beymen, Ramsey, Atasay, Boyner) + sektör platformları
  (DüğünBuketi, Armut) + Cimri eklendi.
- **"çözmeyi deneyelim" turu (2026-07-24) — 5 kalan 0-ürün kaynağın
  `sayfa_tani.py` çıktıları teker teker teşhis edildi:**
  - **Beymen/damatlık (Erkek Smokin) — ÇÖZÜLDÜ.** JSON-LD sadece
    `ItemList` (meta, ürün değil), microdata yok. CSS seçiciler ham
    HTML'den doğrudan doğrulandı: `.m-productCard` /
    `.m-productCard__desc` / `.m-productCard__newPrice` (48 ürün,
    örnek "Ekru Şal Yaka Yün Smokin, 44.950 TL"). `kaynaklar.yaml` ve
    `test_motor.py`'ye eklendi, `durum: "onaylandi"`.
  - **DüğünBuketi'nin 3 girdisi (salon/fotoğrafçı/gelinlik-moda-evleri)
    — ÇÖZÜLDÜ.** JSON-LD'de gerçek işletme listesi var ama
    `@type: "LocalBusiness"` (motor sadece `"Product"` kabul ediyor —
    kasıtlı tasarım, bu yüzden CSS katmanına düşüyor). CSS seçiciler:
    `.bg-card` (kart) / `a.font-semibold.tracking-tight` (isim) /
    `.font-bold` (fiyat — "başlangıç fiyatı" olduğu unutulmamalı, kesin
    toplam değil). Üç girdi de aynı Vue/Tailwind şablonunu paylaşıyor,
    tek örnekten (salon sayfası) doğrulanıp üçüne de uygulandı.
    `test_motor.py`'ye eklendi.
  - **Beymen/gelinlik — KISMEN ÇÖZÜLDÜ, doğrulanmadı.** Smokin
    sayfasının aksine ham HTML'de HİÇBİR `m-productCard` izi yok —
    muhtemelen ürünler AJAX/JS ile sonradan yükleniyor (smokin SSR,
    gelinlik değil). Aynı Beymen CSS seçicileri varsayımla önceden
    dolduruldu (`render_gerekli: true` zaten vardı, motor gerçek
    Chromium ile deneyecek) ama gerçek sonuç doğrulanmadı.
  - **Boyner/damatlık — KÖK NEDEN BULUNDU, henüz çözülmedi.**
    `requests` ile çekilen HTML'de ürün kartları YÜKLENME İSKELETİ
    (`b-skeleton` class'lı boş placeholder) halinde — gerçek isim/fiyat
    JS ile sonradan doluyor. Bu, `sayfa_tani.py`'nin genel bir açığıydı:
    sadece HTTP 403'te Playwright'a düşüyordu, "200 ama iskelet" halini
    yakalamıyordu. **Düzeltme: `sayfa_tani.py`'ye `_iskelet_mi()`
    eklendi** — sayfada `skeleton`/`pulse` class'ı ≥10 ise otomatik
    Playwright'a düşüyor. `render_gerekli: true` zaten Boyner'de var,
    motor.py'nin gerçek çalışması muhtemelen zaten çalışıyordur — CSS
    seçiciler henüz dolu değil çünkü iskelet-öncesi HTML'den gerçek kart
    yapısı görülemedi. Yavuz'un yerelinde düzeltilmiş `sayfa_tani.py`'yi
    TEKRAR çalıştırması gerekiyor.
  - **Armut/fotoğrafçı — BIRAKILDI, kesin sonuç.** Şüphe doğrulandı: bu
    sayfa gerçekten TEK bir agregat `Product` JSON-LD döndürüyor (liste
    değil). Gerçek teklif kartları React (styled-components, hash'li
    class isimleri, ör. `sc-e484e4b8-0`) ile client-side render ediliyor
    — `sayfa_tani.py` hiçbir "product/item/card" eşleşmesi bulamadı
    (hash'li isimlerde bu kelimeler geçmiyor). Bu site tipi (CSS-in-JS)
    kolay kazınabilir değil, hash'ler build'den build'e değişir. `aktif:
    false, durum: "birakildi"` yapıldı. "fotoğrafçı" kalemi artık tek
    kaynaklı (sadece dugunbuketi) — yeni bağımsız kaynak aranmalı.
  - Tüm değişiklikler test edildi (49 test PASS, +2 yeni: Beymen ve
    DüğünBuketi gerçek HTML seçici kilit testleri) ve
    `python motor.py --cikti ...` ile uçtan uca çalıştırıldı (16
    kaynak-grubu işlendi, çökme yok, exit 0 — bu sandbox'ta hepsi
    robots.txt proxy engeline takılıp atlanıyor, beklenen davranış).
- **Yavuz'un yerelinde bu turun düzeltmeleri GERÇEK `python motor.py` ile
  test edildi (2026-07-24) — 2 YENİ BUG bulundu ve düzeltildi:**
  - **BUG 1 — DüğünBuketi'nin 3 sayfası hâlâ 0 ürün döndü** (CSS seçiciler
    doğru olmasına rağmen). Kök neden: `min_fiyat` eşiği ("başlangıç
    fiyatı" rakamları — 685 TL gibi, muhtemelen kişi başı/paket
    başlangıcı — çok üzerinde, salon 5000 TL, fotoğrafçı 1000 TL,
    gelinlik 3000 TL) TÜM kartları eliyordu. Bu sandbox'ta fixture testiyle
    doğrulandı (aynı örnek kart min_fiyat=5000 ile 0, min_fiyat=100 ile
    doğru eşleşiyor). **Düzeltme: üçünün de min_fiyat'ı 100'e düşürüldü.**
    Bu rakamların TOPLAM maliyet değil kişi başı/başlangıç fiyatı olduğu
    yayında açıkça belirtilmeli (dürüstlük ilkesi).
  - **BUG 2 — Beymen/Erkek Smokin CSS seçiciler DOĞRU olmasına rağmen
    0 ürün döndü.** Kök neden: `render_gerekli: true` yanlış bir
    varsayımla konmuştu ("büyük TR moda siteleri genelde 403 verir").
    Ama sayfa_tani.py teşhisi zaten `requests` ile İLK denemede HTTP 200
    + tam ürün HTML'i almıştı, hiç Playwright'a düşmemişti. `render_gerekli:
    true` olduğu için motor.py bu sefer Playwright/Chromium kullandı ve
    **Beymen'in Playwright'a (headless tarayıcı parmak izine) `requests`'ten
    FARKLI/BOŞ bir sayfa sunduğu ortaya çıktı** (muhtemelen bot-tespiti
    otomasyon işaretlerini ayırt ediyor — `navigator.webdriver` vb.).
    **Düzeltme: Beymen'in hem Erkek Smokin hem Gelinlik girdisinde
    `render_gerekli: false` yapıldı** — düz `requests` zaten yeterli ve
    doğru, ayrıca daha nazik (Chromium açmıyor).
  - Diğerleri beklendiği gibi hâlâ 0/teşhis bekliyor: Ramsey (JS'li fiyat,
    düşük öncelik), Boyner (skeleton — düzeltilmiş `sayfa_tani.py`'nin
    TEKRAR çalıştırılması gerekiyor), Cimri (düşük öncelik),
    Trendyol/davetiye (aynı şablon başka Trendyol sayfalarında çalışıyor,
    henüz teşhis edilmedi — URL/kategori kimliği hatalı olabilir).
  - Çapraz doğrulama uyarıları (alyans %351, damatlık %2121) beklendiği
    gibi tekrar üretildi — zaten kabul edilmiş, aksiyon gerekmiyor.
- **DÜZELTMELER SONRASI Yavuz'un yerelinde TEKRAR çalıştırıldı
  (2026-07-24) — İLK ÇALIŞMADA git pull YAPILMADIĞI İÇİN eski koda karşı
  test edilmiş olduğu anlaşıldı** (Beymen/DüğünBuketi çıktıları önceki
  turla birebir aynıydı, süre analizi de Beymen'in hâlâ Playwright
  kullandığını gösterdi — ~5.5sn, `requests`'in ~1sn'lik süresine karşı).
  `git pull` sonrası GERÇEK sonuçlar:
  - **Beymen/Erkek Smokin: 46 ürün, CSS katmanıyla — ÇALIŞIYOR.** Hem
    CSS seçici hem `render_gerekli: false` düzeltmesi doğrulandı.
  - **DüğünBuketi/salon (Istanbul Düğün Mekanları): 8 ürün, CSS
    katmanıyla — ÇALIŞIYOR.** min_fiyat düzeltmesi doğrulandı.
  - **Beymen/gelinlik: HÂLÂ 0 ürün, KESİN SONUÇ.** Artık iki olası sebep
    de (Playwright engeli / yanlış seçici) ayıklandı — Erkek Smokin aynı
    seçiciyle ve `render_gerekli: false` ile çalışıyor. Geriye tek
    açıklama kalıyor: bu URL'nin ham HTML'i gerçekten ürün kartı
    içermiyor (muhtemelen AJAX ile dolduruluyor) VE Beymen headless
    tarayıcıyı da engelliyor (Playwright ile de aşılamaz). **BIRAKILDI**
    — `aktif: false, durum: "birakildi"`. Gelinlik için Beymen'den başka
    kaynak aranmalı.
  - **DüğünBuketi/fotoğrafçı + gelinlik-moda-evleri: HÂLÂ 0 ürün,
    YENİ BULGU.** Aynı site, aynı (salon'dan kopyalanan) seçiciler, aynı
    düzeltilmiş min_fiyat — ama salon çalışırken bu ikisi çalışmıyor.
    Fark: salonun URL'i `/c/dugun-mekanlari/istanbul` (kategori deseni),
    bu ikisinin URL'i `/p/...` (hizmet+şehir deseni) — muhtemelen
    DüğünBuketi bu iki route tipi için FARKLI bir şablon/bileşen
    kullanıyor, salon'dan varsayımla kopyalanan seçiciler bu sayfalarda
    geçerli olmayabilir. `sayfa_tani.py` ile bu iki URL'ye ÖZEL yeniden
    teşhis gerekiyor (salon'un çıktısı yeterli değil) — durum
    `arastirildi`'ye çekildi (yanlışlıkla `onaylandi` idi).
- **Bu iki URL'ye özel `sayfa_tani.py` teşhisi Yavuz'un yerelinde
  yapıldı (2026-07-24) — ilk teşhis YANLIŞTI, sonra KESİN sonuca
  ulaşıldı:**
  - `/p/...` vs `/c/...` URL deseni teorisi de, "`.font-bold` yok,
    fiyat `<strong>` etiketinde" teorisi de İLK ETAPTA doğru sanıldı ve
    `fiyat_secici: "strong, .font-bold"` yapıldı — ama Yavuz'un
    yerelinde `python motor.py` ile tekrar test edildiğinde YİNE 0 ürün
    döndü.
  - **Kesin kanıt için geçici bir script yazıldı** (`.bg-card` kartlarının
    her birini tek tek kontrol eden) ve Yavuz'un yerelinde çalıştırıldı:
    **her iki sayfada da 13 karttan 0'ında (0/13) görünür fiyat var** —
    hepsi "Fiyat bilgisi için üye olun" gösteriyor. Sayfada görülen
    `<strong>...TL</strong>` metinleri kartların İÇİNDE değil, sayfanın
    başka bir yerinde (muhtemelen bir filtre/slider) — kartlarla alakasız
    bir UI elemanı.
  - **KESİN SONUÇ: DüğünBuketi, salon (mekan) kaleminde fiyat gösterirken
    gelinlik-moda-evleri ve fotoğrafçı kaleminde fiyatı KASITLI OLARAK
    GİZLİYOR** (üyelik/teklif-al iş modeli) — bu bir kazıma/seçici hatası
    değil, sitenin ürün kararı. Her iki girdi de **BIRAKILDI**
    (`aktif: false, durum: "birakildi"`), geçici teşhis scripti silindi.
  - **"fotoğrafçı" kalemi artık SIFIR aktif kaynaklı** (Armut da ayrı
    bir teşhiste kesin bırakılmıştı) — bu kalem için acilen yeni bir
    kaynak aranmalı. "gelinlik" kalemi etkilenmedi, Trendyol (23 ürün)
    ile hâlâ kapsanıyor.
- **Trendyol/davetiye de aynı turda teşhis edildi, DÜZELTİLDİ:** diğer
  Trendyol sayfalarında çalışan `.price-value`/
  `.seller-store-default-price-value` seçicisi bu sayfada eşleşmiyordu.
  Kök neden: bu sayfanın fiyatı `.sale-price` class'ında (ör. "92,50 TL",
  yanında `.strikethrough-price` ile eski fiyat) — Trendyol'un farklı
  kategori/kampanya sayfalarında birden fazla fiyat şablonu kullandığı
  ortaya çıktı. `.sale-price` fallback olarak eklendi.
- **Boyner: kısmen ilerleme, düşük önceliğe alındı.** Düzeltilmiş
  `sayfa_tani.py` Playwright'a başarıyla düştü ve gerçek fiyatları
  gördü (`price_priceMain__DrVVQ` class'ında, "16.999,99 TL" gibi
  gerçek veri — artık iskelet değil). Ama `sayfa_tani.py`'nin
  "product"/"item"/"card" anahtar kelimeli sezgisel tarayıcısı ürünün
  TAM kart sarmalayıcısını yakalayamadı (fiyat class'ı bu kelimeleri
  içermiyor, kart sarmalayıcısı ilk 5 aday arasına girmedi). CSS
  seçici hâlâ dolu değil. **Düşük önceliğe alındı** — damatlık kalemi
  zaten 3 çalışan kaynağa sahip (Trendyol 18, Vakko 48, Beymen 46 ürün),
  Boyner olmadan da ÇOK KAYNAK KURALI hedefi fazlasıyla aşılıyor.

## Modüller (sırayla)
1. **Kazıma hattı** — ✅✅ **motor GERÇEK VERİ üretiyor (2026-07-24).**
   `python motor.py`'nin son çalıştırılmış hali:
   - **Çalışan kaynaklar (11):** Trendyol/gelinlik (23, JSON-LD),
     Trendyol/alyans (4, JSON-LD), Trendyol/damatlık (18, CSS),
     Trendyol/gelin-ayakkabısı (8-10, CSS), Trendyol/nikah-şekeri
     (6, CSS), Trendyol/davetiye (8, CSS — `.sale-price` düzeltmesiyle),
     Atasay/alyans (24, CSS), **Vakko/damatlık (48, JSON-LD)**,
     **Beymen/damatlık (46, CSS)**, **DüğünBuketi/salon (7-8, CSS)**.
   - **Hâlâ 0 ürün, düşük öncelik:** Ramsey/damatlık (fiyat JS ile
     sonradan yükleniyor), Boyner/damatlık (gerçek fiyatlar Playwright
     ile görüldü ama `sayfa_tani.py`'nin sezgisel tarayıcısı tam kart
     sarmalayıcısını yakalayamadı — damatlık zaten 3 kaynaklı olduğu
     için düşük öncelik), Cimri/gelinlik (sadece 12 ürün, hydrate
     olmamış).
   - **Kesin BIRAKILDI (kod sorunu değil, site yapısı):**
     Armut/fotoğrafçı (agregat tek-ürün sayfası, gerçek teklifler
     hash'li class'lı React ile client-side render ediliyor, kolay
     kazınabilir değil), **Beymen/gelinlik** (CSS doğru, render_gerekli
     false denendi, hâlâ 0: ham HTML'de gerçekten ürün yok VE Beymen
     headless tarayıcıyı da engelliyor, aşılamaz), **DüğünBuketi/
     fotoğrafçı + gelinlik-moda-evleri** (2026-07-24 kesinleşti — kart/
     isim seçicileri doğru ama site bu iki kalemde fiyatı kasıtlı
     olarak gizliyor, 13 karttan 0'ında görünür fiyat var, üyelik/
     teklif-al modeli — kazıma hatası değil). **"fotoğrafçı" kalemi
     artık sıfır aktif kaynaklı, acil yeni kaynak aranmalı.**
   - **ÇOK KAYNAK KURALI 2 gerçek uyarı üretti:**
     - alyans: Atasay (19.405 TL) vs Trendyol (4.298 TL) — %351 fark.
     - damatlık: Vakko (71.970 TL) vs Trendyol (3.240 TL) — **%2121 fark**
       (kitlesel pazaryeri vs ultra-lüks tasarımcı markası).
     Yavuz'a soruldu: **karar — kalemler BÖLÜNMÜYOR**, her site kendi
     düşük/orta/lüks segmentini ayrı göstermeye devam ediyor (zaten
     birleştirilmiyor), fark sadece çapraz-doğrulama raporunda
     belgeleniyor.
   - Bulunan kritik bug: `Accept-Encoding: ...br` header'ı brotli
     decoder kurulu olmayan ortamlarda yanıtı çözülemez hale
     getiriyordu (düzeltildi).
   - Kaynak çeşitliliği Yavuz'un "Akakçe+Trendyol olmadan bu siteler
     saçma" geri bildirimiyle genişledi: Trendyol (5 kalem) +
     Beymen/Boyner/Vakko (damatlık, segment çeşitliliği) + Beymen
     (gelinlik) + n11/Cimri (gelinlik, denendi) eklendi.
   - Kalan: yeni eklenen markaların (Beymen, Boyner, Ramsey) CSS
     seçicileri, Trendyol/davetiye + DüğünBuketi(3) + Armut teşhisi.
2. **Veri saklama** — ✅ **SQLite'a hiç gerek kalmadı, JSON snapshot yeterli
   (2026-07-24).** motor.py zaten `scraper/veri/{vertikal}/{kalem}_{site}_
   {tarih}.json` şemasıyla site-başına aylık snapshot üretiyordu (backend
   yok, statik site kararına göre bu zaten "veri saklama" katmanının
   kendisi). Eksik olan tek şey — birden fazla kaynağı tek bir "endeks"
   rakamına birleştirme — `scraper/agrega.py` ile bu oturumda dolduruldu
   (bkz. Modül 3).
3. **İlk hesaplayıcı + endeks sayfası** — ✅ **İskelet tamamlandı
   (2026-07-24), GERÇEK VERİ bekliyor.**
   - **`scraper/agrega.py`** (yeni, 13 test PASS): `scraper/veri/dugun/*.json`
     dosyalarını okuyup `/veri/dugun.json`'a birleştirir. ÇOK KAYNAK
     KURALI'na sadık: ham fiyatlar kaynaklar arası KARIŞTIRILMAZ — her
     segment için her kaynağın KENDİ medyanı alınır, sonra bu medyanların
     medyanı hesaplanır ("medyan-of-medyan"). Karantinadaki (sağlıksız)
     kaynaklar otomatik dışlanır. Çapraz doğrulama raporları ilgili kaleme
     iliştirilir.
   - **`scraper/sayfa_uret.py`** (yeni, 9 test PASS): `/veri/dugun.json`'dan
     `/dugun/index.html`'i (endeks sayfası) BUILD-TIME'DA üretir — client-side
     fetch DEĞİL, çünkü GEO'nun hedeflediği AI botlarının (GPTBot vb.)
     çoğu JavaScript çalıştırmıyor, cevap bloğundaki rakam ham HTML'de
     olmak zorunda. FAQPage + Dataset schema.org JSON-LD üretir.
     **Kritik bug bulundu ve düzeltildi (regresyon testiyle kilitlendi):**
     `kalemler` sözlüğü dolu ama TÜM değerler `genel_medyan: null` olabilir
     (ör. o ay tüm kaynaklar 0 ürün döndü) — ilk halde bu durumda "0 TL"
     gibi yanıltıcı, güvenilir görünen bir cevap metni üretiliyordu. Artık
     gerçekten en az bir kalemde sayısal değer var mı diye kontrol ediyor,
     yoksa dürüst "veri toplama süreci devam ediyor" mesajı gösteriyor.
   - **`/dugun/hesaplayici/`**: etkileşimli, client-side (`/assets/js/
     dugun-hesapla.js`, 10 Node test PASS + `dugun-kalemler.js`).
     `/veri/dugun.json`'ı fetch eder, davetli sayısı + segment (ekonomik/
     orta/lüks) + kalem seçimlerine göre toplam hesaplar.
   - **KIRMIZI ÇİZGİ karar — SONRADAN GÜNCELLENDİ (2026-07-24):** ilk
     halde, veri kaynağı olmayan kalemler (takı/altın, yemek/ikram,
     fotoğrafçı, orkestra/DJ, gelin arabası, kuaför/makyaj, organizasyon,
     nikah işlemleri) için tahmini rakam KONULMAMIŞTI — ayrı bir "henüz
     veri kapsamında değil" listesinde gösterilip toplama dahil
     edilmiyordu. **Yavuz açıkça bunun tersini istedi** ("bence ortalama
     bir fiyat girelim... bunlar önemli, senin bilgin dahilinde olan
     fiyatlandırmayı kullan") — AskUserQuestion ile netleştirmeye
     çalışıldı ama reddedildi, talimat tekrarlandı. Karar uygulandı:
     WebSearch ile (8 ayrı arama, güncel TR fiyat aralıkları) her kalem
     için düşük/orta/lüks tahmini değer araştırılıp `kaynak_tipi:
     "tahmini"` ile eklendi (bkz. yukarıdaki KIRMIZI ÇİZGİ bölümündeki
     istisna maddesi ve şartları). UI'da her yerde `Tahmini` etiketiyle
     gerçek kaynaktan görsel olarak ayrılıyor, toplam kırılımı ("gerçek
     kaynaklardan X TL, tahmini kalemlerden Y TL") her zaman gösteriliyor.
     Metodoloji sayfası bu ayrımı açıkça anlatacak şekilde güncellendi.
     25 test (JS+Python) bu davranışı kilitliyor.
   - **Site iskeleti:** `/index.html` (ana sayfa, vertikal kartları),
     `/assets/css/style.css` (framework yok, saf CSS), `/robots.txt`
     (AI botlarına açık: GPTBot, ClaudeBot, PerplexityBot vb.).
   - **Playwright ile uçtan uca duman testi yapıldı** (bu sandbox'ta,
     `python3 -m http.server` + headless Chromium): 3 sayfa da hatasız
     yükleniyor, hesaplayıcı formu dolduruluyor, submit ediliyor, "veri
     yok" durumunda dürüst mesaj gösteriyor (console'da JS hatası yok).
   - **BLOKE — gerçek veri yok:** `scraper/veri/` hiç commit edilmedi
     (Yavuz'un yerelinde şimdiye kadarki tüm `motor.py` çalıştırmaları
     test amaçlıydı, sonuçlar commit edilmedi). Bu yüzden `/veri/dugun.json`
     şu an dürüstçe boş (`{"kalemler": {}}`) ve `/dugun/index.html`
     "veri toplama süreci devam ediyor" gösteriyor. **Yavuz'un yerelinde
     gerçek `python motor.py` çalıştırıp `scraper/veri/` klasörünü commit
     etmesi, sonra `python agrega.py && python sayfa_uret.py` çalıştırıp
     o çıktıları da commit etmesi gerekiyor** — bu olmadan siteye
     GERÇEK bir rakam giremez (KIRMIZI ÇİZGİ).
4. **Metodoloji sayfası + schema.org işaretlemesi** — ✅ **Tamamlandı
   (2026-07-24).** `/dugun/metodoloji/` — kaynak türleri, çapraz doğrulama
   kuralı, segment tanımı (persentil), sağlık kontrolü, nazik kazıma
   ilkeleri, kapsanmayan kalemler notu. Statik (elle yazıldı, veriye bağımlı
   değil) - schema.org işaretlemesi `/dugun/`'de (sayfa_uret.py) yapıldı.
5. **Yayın** — Cloudflare Pages, custom domain, SSL.
6. **Aylık otomasyon** — GitHub Actions cron. **Artık 3 adımlı olacak:**
   `python motor.py` → `python agrega.py` → `python sayfa_uret.py` → commit.
7. **Fiyat geçmişi grafikleri** (3+ ay veri sonrası).

## Yapılacaklar (kod dışı)
- [x] Domain alındı, GitHub repo kuruldu
- [ ] Cloudflare nameserver propagasyon onayı
- [x] robots.txt kontrolü (protego ile düzeltilmiş script) — Hepsiburada/
      Dolap gerçekten erişim yasağı (RET doğru), diğerleri ONAY.
- [x] Akakçe → Cloudflare bot-doğrulaması nedeniyle BIRAKILDI (Yavuz
      onayladı), yerine Trendyol genişletildi (5 kalem + 2 yeni kalem:
      nikah-şekeri, davetiye).
- [x] Kritik bug düzeltildi: `Accept-Encoding: br` header'ı brotli
      decoder'sız ortamda yanıtı bozuyordu.
- [x] **`python motor.py` gerçek veri üretiyor (2026-07-24):** 8 kaynak
      çalışıyor. alyans (%351) ve damatlık (%2121) çapraz-doğrulama
      uyarısı verdi — Yavuz'a soruldu, **karar: kalemler bölünmüyor,
      olduğu gibi belgelenip bırakılıyor** (bkz. Teknik Durum).
- [x] Beymen/Boyner/Vakko damatlığa, Beymen gelinliğe eklendi (Yavuz'un
      önerisiyle) — Vakko damatlık hemen çalıştı (48 ürün), diğerleri
      CSS seçici bekliyor.
- [x] **Beymen/damatlık (Erkek Smokin) CSS seçici ÇÖZÜLDÜ (2026-07-24):**
      `.m-productCard` / `.m-productCard__desc` / `.m-productCard__newPrice`
      — `sayfa_tani.py` çıktısından doğrudan doğrulandı, `test_motor.py`'ye
      kilit test eklendi.
- [x] **DüğünBuketi'nin 3 sayfası CSS seçici ÇÖZÜLDÜ (2026-07-24):**
      `.bg-card` / `a.font-semibold.tracking-tight` / `.font-bold` —
      üçü de aynı şablonu paylaşıyor, salon sayfasından doğrulanıp
      hepsine uygulandı.
- [x] **Yavuz'un yerelinde `python motor.py` ile GERÇEK doğrulama
      yapıldı (2026-07-24) — 2 yeni bug bulundu ve düzeltildi:**
      DüğünBuketi'nin 3 sayfası CSS doğru olmasına rağmen `min_fiyat`
      eşiği (5000/3000/1000) "başlangıç fiyatı" rakamlarının (685 TL
      gibi) çok üzerindeydi, TÜM kartları eledi → 100'e düşürüldü.
      Beymen/Erkek Smokin CSS doğru olmasına rağmen `render_gerekli:
      true` yüzünden Playwright kullanıyordu — **Beymen'in Playwright'a
      requests'ten FARKLI/BOŞ sayfa sunduğu ortaya çıktı** (muhtemelen
      headless tarayıcı tespiti) → `render_gerekli: false` yapıldı
      (Beymen'in hem smokin hem gelinlik girdisinde).
- [x] **Beymen/Erkek Smokin ve DüğünBuketi/salon DOĞRULANDI (2026-07-24):**
      düzeltmeler sonrası Yavuz'un yerelinde `git pull` + `python motor.py`
      ile tekrar çalıştırıldı (ilk deneme yanlışlıkla pull edilmemiş eski
      kodla yapılmıştı) — **Beymen/Erkek Smokin: 46 ürün, ÇALIŞIYOR.**
      **DüğünBuketi/salon: 8 ürün, ÇALIŞIYOR.**
- [x] **Beymen/gelinlik KESİN BIRAKILDI (2026-07-24):** `render_gerekli:
      false` sonrası da hâlâ 0 ürün - Erkek Smokin aynı seçici+ayarla
      çalıştığı için hem "yanlış seçici" hem "Playwright engeli"
      ihtimalleri ayıklandı. Geriye tek açıklama kalıyor: bu URL'nin ham
      HTML'i gerçekten ürün içermiyor VE Beymen headless tarayıcıyı da
      engelliyor. `aktif: false, durum: "birakildi"` yapıldı - gelinlik
      için Beymen'den başka kaynak aranmalı.
- [x] **Boyner kök nedeni bulundu (2026-07-24):** sayfa JS-"skeleton"
      yükleme halinde geliyor (`b-skeleton` class'ları), gerçek kart
      JS ile sonradan doluyor. `sayfa_tani.py` bunu artık otomatik
      tespit edip Playwright'a düşüyor (`_iskelet_mi()` eklendi).
- [x] **Boyner tekrar teşhis edildi (2026-07-24), düşük önceliğe
      alındı:** düzeltilmiş `sayfa_tani.py` Playwright'a düştü, gerçek
      fiyatları gördü (`price_priceMain__DrVVQ`, "16.999,99 TL" gibi)
      ama sezgisel kart-tarayıcı tam kart sarmalayıcısını yakalayamadı.
      CSS seçici hâlâ dolu değil — damatlık zaten 3 çalışan kaynağa
      sahip olduğu için (Trendyol/Vakko/Beymen) bunu kovalamayı bıraktık.
- [x] **Trendyol/davetiye ÇÖZÜLDÜ ve DOĞRULANDI (2026-07-24):** bu
      sayfanın fiyatı `.price-value` değil `.sale-price` class'ında -
      Trendyol'un farklı kategori sayfalarında birden fazla fiyat
      şablonu var. `.sale-price` fallback olarak eklendi. Yavuz'un
      yerelinde `python motor.py` ile tekrar çalıştırıldı: **8 ürün,
      ÇALIŞIYOR.**
- [x] **DüğünBuketi/fotoğrafçı + gelinlik-moda-evleri KESİN BIRAKILDI
      (2026-07-24):** İlk teşhis ("fiyat `<strong>` etiketinde")
      YANLIŞ çıktı - düzeltme sonrası da hâlâ 0 ürün döndü. Geçici bir
      script ile TÜM 13 kart tek tek kontrol edildi: **0/13 kartta
      görünür fiyat var** - hepsi "Fiyat bilgisi için üye olun"
      gösteriyor. Sayfadaki `<strong>...TL</strong>` metinleri
      kartların DIŞINDA, alakasız bir UI elemanına ait. Site bu iki
      kalemde fiyatı KASITLI OLARAK GİZLİYOR (üyelik/teklif-al modeli)
      - kazıma hatası değil. `aktif: false, durum: "birakildi"` yapıldı,
      geçici teşhis scripti silindi.
- [x] **Armut/fotoğrafçı BIRAKILDI, kesin teşhis (2026-07-24):** agregat
      tek-ürün JSON-LD sayfası, gerçek teklifler React (hash'li
      class'lar) ile client-side render — kolay kazınabilir değil,
      `aktif: false` yapıldı.
- [ ] **ACİL: "fotoğrafçı" kalemi artık SIFIR aktif kaynaklı**
      (Armut + DüğünBuketi ikisi de bırakıldı) — yeni bağımsız kaynak
      aranmalı.
- [ ] Cimri/gelinlik: Akakçe gibi Cloudflare'e mi düştü, belirsiz —
      düşük öncelik (gelinlik zaten trendyol+beymen ile kapsanıyor,
      dugunbuketi/gelinlik de bırakıldığı için artık trendyol tek
      gerçek kaynak - ikinci bir kaynak aranabilir)
- [ ] "salon" için 2. bağımsız kaynak bulma (şu an sadece dugunbuketi)
- [x] **Site iskeleti + hesaplayıcı + endeks + metodoloji sayfaları
      YAZILDI (2026-07-24):** `agrega.py` (13 test), `sayfa_uret.py`
      (9 test), `/dugun/hesaplayici/` (10 Node test), `/dugun/`,
      `/dugun/metodoloji/`, `/index.html`, `/assets/css/style.css`,
      `/robots.txt`. Playwright ile duman testi yapıldı, JS hatası yok.
- [ ] **ACİL/BLOKE: gerçek veri commit edilmeli.** `scraper/veri/` hiç
      commit edilmedi (bugüne kadarki tüm `motor.py` çalıştırmaları test
      amaçlıydı). Yavuz'un yerelinde: `python motor.py` (gerçek veri) →
      `scraper/veri/` klasörünü commit et → `python agrega.py &&
      python sayfa_uret.py` çalıştır → `/veri/dugun.json` ve
      `/dugun/index.html`'i de commit et. Bu olmadan site "veri toplama
      süreci devam ediyor" dürüst-boş halinde kalır (KIRMIZI ÇİZGİ geregi
      sahte rakam koyulmadı).
- [ ] Takı/altın (canlı gram fiyatı) için kaynak bulma
- [ ] TÜİK doğrulama verisi entegrasyonu (ÇOK KAYNAK KURALI 5. katman)
- [ ] (İleride) Türk Patent marka başvurusu
- [ ] (İleride) yakın domain varyantlarını kapat

## Çalışma Şekli
- Strateji claude.ai sohbetinde, inşaat Claude Code'da.
- Her oturum TEK modüle odaklanır.
- Oturum sonunda bu dosya güncellenir.
