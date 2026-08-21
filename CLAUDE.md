# Maliyetine.com.tr — Proje Hafızası

> Her oturumun başında önce bunu oku. Kararları değiştirmeden önce
> Yavuz'a sor. Oturum sonunda "GÜNCEL SON DURUM" ve "Yapılacaklar"
> bölümlerini güncelle; tarihî bölümlere yalnızca gerçekten yeni ders
> varsa ek yap.

## GÜNCEL SON DURUM (2026-08-22 kontrolü)
> **Önce burayı baz al.** Aşağıdaki uzun bölüm proje günlüğü ve ders
> arşividir; içinde tarihî kayıt olarak kalması gereken eski kararlar var.
> Karar verirken güncel gerçek bu bölümdür.

- Branch `claude/new-session-csygpf`. Remote:
  `github.com/yavuzkara1907-ship-it/maliyetine.git`. Teknik temizlik
  commit'i sonrası içerik/GEO turu açıldı: YouTube para kazanma sayfası
  resmi YPP şartlarıyla güçlendirildi, kart puanları için resmi kaynaklı
  rehber eklendi.
- Site artık tek konu değil, **veri ürünü + hesaplayıcı ağı**:
  **7 vertikal** (`dugun`, `ev-kurma`, `okul`, `bebek`, `kedi`, `kopek`,
  `arac`), **122 ölçülen kalem**, **25 bağımsız `/hesap/` hesaplayıcı**,
  **25 rehber**, **185 sitemap URL'i**.
- Yayın modeli: statik dosyalar Cloudflare tarafında **Worker** ile servis
  ediliyor. Eski Pages kurulum notları tarihî kayıt; bugün doğru altyapı
  "statik çıktı + Cloudflare Worker + GitHub Actions"tır.
- Otomasyon ayda iki kez çalışacak şekilde tasarlandı: ayın **5'i ve
  20'si**. **20 Ağustos 2026 koşusu kontrol edildi:** GitHub Actions run
  `32339864463` başarıyla bitti, `maliyetine-bot` `75ceda9` commit'ini attı
  ve canlı sitede 7 vertikal JSON'u + 7 CSV dosyası `2026-08-20` olarak 200
  dönüyor.
- Düğünde tahmini kalan kalem sayısı artık düşük: `orkestra-dj` ve
  `nikah-islemleri`. `taki-altin`, `yemek-ikram`, `fotografci`,
  `organizasyon`, `kuafor-makyaj`, `gelin-arabasi` gerçek kaynağa taşındı.
  `yemek-ikram` **bilgi amaçlıdır**, hiçbir toplamda toplanmaz.
- EVDS/TÜFE entegrasyonu var: `veri/enflasyon.json` üretilmiş, sayfalarda
  TCMB EVDS kaynaklı resmî enflasyon blokları görünüyor. TÜFE hiçbir zaman
  TL fiyatın yerine geçmez.
- Search Console artık veri veriyor. **2026-08-22 canlı export:** tarih
  filtresi "Son 3 ay" olsa da fiilî veri aralığı **2026-07-24 –
  2026-08-19**; **3.277 gösterim, 21 tık, %0,6 TO, konum 25,9, 306 sorgu**.
  Önceki tur 555 gösterim / 4 tık / 115 sorguydu; büyüme gerçek.
- GEO içerik sinyali başladı: Analytics'te **2 ChatGPT + 1 Gemini**
  yönlendirmesi görüldü. Bu küçük sayı ama doğru yönde sinyal; artık
  içerik üretirken yalnız Google snippet'i değil, AI cevabına girecek kısa,
  kaynaklı, tarihli cevap blokları da hedeflenmeli.
- AI/GEO ikinci turunda iki örnekten bağımsız ürün hamlesi yapıldı:
  **114 tam segmentli ölçümle çalışan `/hesap/butcem-yeter-mi/`**, aylık
  kedi ve köpek gider rehberleri, bebeğin aylık giderine dürüst alt sınır
  cevabı ve **1.000 kişilik düğün senaryosu**. Özellik verisi olmayan
  ürün sorularında (ör. buhar destekli fırın/indüksiyon) içerik uydurmak
  yerine önce yeni veri alanı toplanacak.
- OpenAI arama görünürlüğü için `robots.txt` artık **OAI-SearchBot**'u da
  açıkça kabul ediyor. `llms.txt` bütün 25 aracı listeliyor ve formül
  araçlarıyla güncel veriye dayalı iki aracı birbirine karıştırmıyor.
- Cloudflare `www` → kök domain 301 redirect **tamamlandı ve canlıda
  doğrulandı** (2026-08-22). Eski kural aktif görünüyordu ama expression,
  `URI Full wildcard` alanına yazıldığı için çalışmıyordu. Kural
  `www ve HTTP -> kök HTTPS 301` olarak düzeltildi; `https://www...` ve
  `http://www...` artık `https://maliyetine.com.tr/...` adresine 301
  dönüyor, query string korunuyor, kök HTTPS 200 kalıyor.
- En yüksek kaldıraçlı açık işler:
  1. 301 sonrası Search Console'u 7-14 gün sonra tekrar kontrol et:
     sayfa tablosunda `www` sinyali düşüyor mu, kök hosta birleşiyor mu?
  2. Search Console sorgu boşlukları: kira gelir vergisi, hisse/borsa
     maliyet, tapu/ipotek harcı, temettü ve düşük CTR'li iyi pozisyon
     sorguları. Yeni sayfa açmadan önce mevcut sayfanın cannibalize olup
     olmayacağı kontrol edilmeli; aylık evcil hayvan ve 1.000 kişilik
     düğün fırsatları bu turda kapatıldı.
  3. Tek kaynaklı kalem oranı hâlâ takip edilmeli. EV-kurma 0/42 tek
     kaynaklı duruma geldi; kedi/kopek kısmen kapandı ama tamamen bitmedi.
  4. Düğünde kalan iki tahmini kalem (`nikah-islemleri`, `orkestra-dj`)
     metodolojik karar + kaynak bulununca kapatılmalı.
  5. YouTube YPP şartları **2027-02-01** öncesi yeniden kontrol edilmeli;
     resmi eşik değişikliği tarihli notla sayfaya işlendi.
  6. Sosyal/Meta tarafına geçilecekse önce sayfa bazlı ölçüm kartı
     üretimi korunmalı; Instagram metin değil görsel ister.

## Proje Sahibi
- Yavuz. Türkçe konuşur. Doğrudan iletişim ister, uzun açıklama değil
  aksiyon bekler. Teknik detayı ona sormak yerine sen çöz ve sonucu
  bildir.
- Python bilir, HTML/CSS'e hakim. Dağıtım/içerik tarafı güçlü.
- Soğuk satış YOK. Self-serve model.

## MARKA ADI: "Maliyeti Ne?" (2026-07-25 Yavuz'un kararı)
- Görünen marka adı **"Maliyeti Ne?"**. Domain `maliyetine.com.tr`
  olarak KALIYOR — sadece görünen ad değişti.
- Logo: `Maliyeti <span>Ne?</span>`. Alıntı kalıbı:
  **"Maliyeti Ne? verilerine göre 2026'da ... X TL"**
  (eskiden "Maliyetine'ye göre" idi).
- Title kalıbı: `... | Maliyeti Ne?`. Organization schema `name` alanı da bu.

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
  Hedef cümle: "Maliyeti Ne? verilerine göre 2026'da ... ortalama X TL."
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
  henüz bulunamamış bazı düğün kalemleri için WebSearch ile genel piyasa
  araştırmasından türetilmiş TEK SEFERLİK tahmini değer kullanıldı
  ("bunlar önemli, senin bilgin dahilinde olan fiyatlandırmayı kullan"
  talimatı). Bu istisna kalıcı model değildir. **Güncel durumda tahmini
  kalanlar yalnızca `orkestra-dj` ve `nikah-islemleri`;** diğer hizmet
  kalemleri gerçek kaynağa taşındı. Bu istisna KATI ŞARTLARLA sınırlı,
  sessizce genişletilmemeli:
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
- **Tek kaynağa BAĞLI KALINMAZ.** Akakçe artık bırakıldı; kural bir
  kaynağa değil, kaynağa bağımlı kalmama disiplinine aittir.
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
  5. **Doğrulama katmanı: TÜİK TÜFE alt kalemleri / TCMB EVDS**
     (giyim, lokanta, dayanıklı mallar vb.). Kendi verimizle
     karşılaştırılır; TL fiyatın yerine geçmez.
- **Çapraz doğrulama uyarısı:** kaynaklar arası fark %30'u aşarsa
  sistem uyarı versin (ya kazıma hatası ya farklı segment — ikisi de
  bilinmesi gereken şey). TÜİK trendiyle ters düşen sıçramalar
  karantinaya alınır.
- Metodoloji sayfasında resmî verinin rolü açık yazılır: TÜFE trend
  doğrulamasıdır, fiyat kaynağı değildir.

## Ürün Kararları
- Format: her kalem için ekonomik / orta / üst segment (persentil:
  ≤P25 ekonomik, P25–P75 orta, >P75 üst) + min/ortalama diye görünen
  ortanca + max + örneklem sayısı + tarih. Eski "lüks" adı terk edildi;
  üst segment piyasanın mutlak lüksü değil, ölçülen örneklemin üst
  çeyreğidir.
- Ölçüm ayda iki kez: ayın 5'i ve 20'si. JSON snapshot'lar biriktirilir →
  fiyat geçmişi ve Search Console/PR malzemesi.
- Yayındaki vertikaller: düğün, ev-kurma, okul, bebek, kedi, köpek,
  araç. Ev tadilatı/tatil/üniversite gibi alanlar hâlâ adaydır ama
  işçilik/dinamik fiyat nedeniyle aceleye getirilmez.
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
4. Takı ve altın — **2026-07-25'te GERÇEK KAYNAĞA taşındı.** Kalem adı
   bilinçli olarak DARALTILDI: `Takı — Altın Bilezik (1 adet)`. Sebep:
   düğünde takılan TOPLAM altın ölçülemez (davetli sayısı/gelenek
   değişkeni), ama bir bileziğin fiyatı ölçülebilir. Kaynak: Atasay
   (alyansla aynı CSS seçiciler). En oynak kalem — gram altın fiyatı
   değiştikçe ay içinde değişir.
5. Nikah şekeri
6. Davetiye
7. Gelin ayakkabısı, duvak, aksesuar

**Hizmet bazlı (zor — tanım ve segment tuzağı var):**
8. Düğün salonu / davet (kişi başı × davetli sayısı) — **2026-07-25'te
   İKİ TANIMLI VARYANTA bölündü:** `salon-yemekli` (menü dahil kişi başı)
   ve `salon-kokteyl` (yemeksiz). Sebep: mekan listeleme sayfasındaki
   "başlangıç fiyatı" mekanın EN DÜŞÜK seçeneğidir (çoğunlukla yemeksiz
   kokteyl) ve ne ölçtüğü belirsizdi. Detay sayfalarında iki fiyat ayrı
   ayrı yazıyor, artık ayrı kalem olarak derleniyor.
9. Yemek/ikram (salona dahil değilse ayrı) — **`salon-yemekli` seçiliyse
   ÇİFT SAYIM olur**. Güncel karar daha katı: `yemek-ikram` bilgi
   amaçlıdır, hiçbir toplamda toplanmaz; mekanların menü bedeli için
   referans notu olarak gösterilir.
10. Fotoğraf ve video — **2026-07-26'da GERÇEK KAYNAĞA taşındı**
    (`dugun.com` İstanbul tablosu, tek değer).
11. Orkestra / DJ — hâlâ tahmini. Çoğu salonda paket içinde geçebilir;
    ayrı kalem mi paket kalemi mi olacağı metodolojik karar ister.
12. Gelin arabası — **2026-07-26'da GERÇEK KAYNAĞA taşındı**.
13. Kuaför ve makyaj — **2026-07-26'da GERÇEK KAYNAĞA taşındı**.
14. Organizasyon/süsleme (çiçek, masa düzeni) — **2026-07-26'da GERÇEK
    KAYNAĞA taşındı**.
15. Nikah işlemleri (resmi harçlar) — hâlâ tahmini; düşük etkili ama
    resmî kaynakla kapatılabilir.

**Ayrı gösterilecek:**
16. Balayı (ayrı bölüm; tatil vertikaliyle veri paylaşır — aynı kaynak
    iki vertikali besler)

- Kaynağı bulunamayan kalemler yalnızca açık "Tahmini" etiketiyle
  yayınlanır. Güncel tahmini kalemler: `orkestra-dj`, `nikah-islemleri`.
- Hesaplayıcı girdileri: şehir, davetli sayısı, segment (ekonomik/orta/
  üst), opsiyonel kalem seçimleri.

## EV KURMA VERTİKALİ — Kalem Listesi (2026-07-25 başlatıldı)
- Yavuz'un talimatıyla düğün'den sonraki 2. vertikal olarak seçildi
  (orijinal plan "ev tadilatı" idi, Yavuz bunun yerine ev kurma'yı
  istedi — plan güncellendi).
- **Tamamen ürün bazlı** (CLAUDE.md'nin "Vertikal veri tipi ayrımı"
  notuna göre kolay kategori) — her kalem tek bir fiziksel üründür,
  hizmet/işçilik karmaşıklığı yok. İlk tur Trendyol'la başladı, sonra
  Amazon, Karaca/English Home, Madame Coco, MediaMarkt, Doğtaş, Bellona
  ve İstikbal gibi kaynaklarla genişledi.
- **İLK TUR (tarihî kayıt): 42 kalem, tamamı Trendyol.** İlk 14'e (buzdolabı,
  çamaşır makinesi, bulaşık makinesi, fırın/ocak, mikrodalga, koltuk
  takımı, yemek masası takımı, yatak, gardırop, TV ünitesi, robot
  süpürge, perde, aydınlatma, klima) Yavuz'un ChatGPT'den aldığı
  kapsamlı bir "ev kurma maliyeti" listesini paylaşmasıyla 28 kalem
  daha eklendi: davlumbaz, kurutma makinesi, karyola, komodin, şifonyer,
  boy aynası, nevresim takımı, televizyon, dikey süpürge, airfryer,
  kahve makinesi, su ısıtıcı, tost makinesi, blender, mutfak robotu,
  ütü, saç kurutma makinesi, tencere seti, tava seti, çatal-kaşık-bıçak
  takımı, yemek takımı, kahvaltı takımı, bardak takımı, havlu takımı,
  bornoz, halı, sehpa, konsol. Tüm URL'ler WebSearch ile doğrulandı.
  `vertikal: "ev-kurma"` olarak `kaynaklar.yaml`'a eklendi.
  **ÖNEMLİ METODOLOJİ KARARI:** ChatGPT'nin paylaştığı TL rakamları
  (kaynaksız, aramasız, saf model tahmini) doğrudan KULLANILMADI — bu,
  düğün'deki WebSearch-grounded "tahmini" kalemlerden bile daha zayıf
  bir kaynaktı ve KIRMIZI ÇİZGİ'yi gerçek anlamda ihlal ederdi. Bunun
  yerine listedeki kalemler (kategoriler olarak) referans alınıp
  HEPSİ İÇİN gerçek Trendyol URL'si arandı — yani "tahmini" değil,
  gerçek kaynak listesi genişletildi. Vague/paket kalemler (temizlik
  malzemeleri, ilk yardım çantası, saklama kutuları vb.) kasıtlı olarak
  dışarıda bırakıldı — tek bir net "ürün" karşılığı yok, dedike kazıma
  girdisine değmez.
  **GÜNCELLEME (2026-08-09):** EV-kurma artık 42/42 kalemde gerçek veri
  üretiyor ve **tek kaynaklı kalem kalmadı**. Orta segment son yerel
  veriyle 369.371 TL, üst segment 600.942 TL; bağımsız site sayısı 9.
- ✅ **Kazıma DOĞRULANDI (2026-07-25, Yavuz'un yerelinde):** `python
  motor.py` çalıştırıldı, **42 kalemin 42'si de gerçek ürün döndürdü**
  (hepsi Trendyol, JSON-LD/CSS katmanıyla). Düğün'de yaşanan "bazı
  kategori sayfaları farklı şablon kullanıyor" sorunu ev-kurma'da HİÇ
  çıkmadı — Trendyol kategori sayfaları tutarlı. `scraper/veri/ev-kurma/`
  altında 42 snapshot dosyası mevcut, hepsinde segment kırılımı
  (düşük/orta/lüks) dolu.
- ✅ **Frontend TAMAMLANDI (2026-07-25):** `/ev-kurma/` üçlüsü
  (endeks + hesaplayıcı + metodoloji) yayında, gerçek veriyle. İlk
  yayın toplamı 353.827 TL idi; güncel rakamlar veri dosyalarından gelir,
  bu satırdaki tarihî tutar karar aldırmak için kullanılmamalı.
  Tarayıcıda uçtan uca doğrulandı (üç segmentin de bağımsız hesapla ile
  birebir eşleştiği, 42 satırın tamamının render olduğu, console'da JS
  hatası olmadığı, tüm sayfalardaki tüm linklerin 200 döndüğü).
- `sayfa_uret.py` **v0.2'de vertikal-agnostik hale getirildi** —
  vertikaller artık `VERTIKALLER` sözlüğünde tanımlanıyor (kalem listesi,
  başlıklar, ölçek alanı, dataset meta). Yeni vertikal eklemek = bir
  sözlük girdisi + bir kalem listesi, kod değil. Düğün sayfasının
  refactor sonrası **byte-byte aynı** kaldığı diff ile doğrulandı
  (regresyon yok). `assets/js/dugun-hesapla.js` → `hesapla.js` olarak
  yeniden adlandırıldı (global: `dugunHesapla` → `maliyetHesapla`),
  zaten tamamen jenerikti; her iki vertikal de aynı dosyayı kullanıyor.

## SEO / Keşfedilebilirlik Durumu (2026-07-25)
- **GÜNCELLEME (2026-08-09): Google artık veri veriyor.** Search Console
  28 günde 555 gösterim, 4 tık, ortalama konum 39,4 ve 115 sorgu
  gösterdi. En büyük teknik sorun `www`/kök host bölünmesi; 301 redirect
  hâlâ en önemli dış ayar.
- **TARİHÎ İLK GÜN NOTU:** `site:maliyetine.com.tr` sorgusu boştu —
  beklenen, site 2026-07-25'te yayına girdi ve sitemap hiçbir arama
  motoruna gönderilmemişti. (Arama sırasında **rakip tespit edildi:**
  `maliyeti.com.tr` — "Her Şeyin Maliyetini Öğrenin!", indeksli, "Havuz
  Maliyeti 2025" gibi sayfaları var. İncelemeye değer, bkz. Yapılacaklar.)
- **Teknik SEO denetimi yapıldı, düzeltildi:**
  - **THIN CONTENT (en ciddiydi):** 9 kalem sayfası ~100 kelimeydi.
    Google zayıf içerik sayıp indekslemeyebilirdi — halbuki uzun kuyruk
    trafiğini onlar getirecek. **Artık 330-390 kelime.** Eklenenlerin
    hepsi VERİDEN üretiliyor (uydurma yok): görünür SSS bölümü, segment
    detay tablosu (medyan+min+max+örneklem), bütçe payı hesabı, ekonomik/
    lüks kat farkı, çapraz doğrulama açıklaması, ilgili kalem linkleri.
  - **Görünür SSS neden önemli:** schema.org'da FAQ vardı ama HTML'de
    yoktu. Google yalnızca yapılandırılmış veriye güvenmiyor, AI motorları
    da sayfa metnini okuyor.
  - Open Graph + Twitter Card hiçbir sayfada yoktu → hepsine eklendi.
  - 6 sayfanın title'ı 60+ karakterdi (SERP'te kesilir) → hepsi 60 altı.
  - Meta description'lar artık gerçek rakam içeriyor (tıklanma oranı).
- **IndexNow kuruldu ve İLK BİLDİRİM GÖNDERİLDİ (202 = kabul, 16 URL).**
  `scraper/indexnow.py` + kök dizinde `{key}.txt` (key gizli değil,
  sahiplik kanıtı — depoda durması normal).
  - **Neden GEO için değerli: ChatGPT'nin web araması Bing altyapısını
    kullanıyor.** Bing indeksine hızlı girmek doğrudan GEO kazancı.
    Yandex de destekliyor.
  - **Google IndexNow'u DESTEKLEMİYOR** — onun için Search Console'a
    sitemap gönderimi şart (Yavuz'un tarafında).
  - Script key dosyasının yayında olduğunu doğruluyor; değilse sessizce
    devam etmiyor, uyarıyor.
  - **Bulunan bug (düzeltildi):** doğrulama `urllib`'in varsayılan
    User-Agent'ıyla istek atıyordu ve Cloudflare'e takılıp "key yayında
    değil" diye yanlış alarm veriyordu — motor.py'de robots.txt çekerken
    yaşanan sorunun aynısı. Gerçekçi tarayıcı UA'sı eklendi.
  - ✅ **AYLIK OTOMASYONA EKLENDİ (2026-07-25).** Yavuz PAT'a `workflow`
    scope'unu ekledi, workflow push edilebildi. Aylık cron artık:
    `motor.py` → her vertikal için (`dugun`, `ev-kurma`, `arac`)
    `agrega.py` + `sayfa_uret.py` → commit+push → **IndexNow bildirimi**.
    IndexNow adımı yalnızca gerçekten değişiklik olduysa çalışır (boş
    bildirim motorlarda güven kaybettirir) ve deploy tamamlansın diye
    90 sn bekler.

## 0 KM ARAÇ VERTİKALİ (2026-07-25 başlatıldı, YAYINDA)
- **Kaynak:** donanimhaber'in aylık güncellenen sıfır araç fiyat dosyası.
  robots.txt ONAY. İki kez çekilip içeriğin TUTARLI olduğu doğrulandı.
  - Elenen adaylar: sahibinden/Fiat/VW robots.txt RET; Toyota, Hyundai,
    arabam, arabalar.com.tr denenen URL'ler 404; Renault ve sifirfiyatlar
    erişilebilir ama fiyatlar JS ile yükleniyor (ham HTML'de yok).
- **motor.py'ye TABLO KATMANI eklendi** (`tablo_urunler`). Bazı kaynaklar
  veriyi ürün kartı değil DÜZ TABLO olarak yayınlıyor — ne JSON-LD ne
  ürün-kartı CSS deseni işe yarıyor. `baslik_metni` ile başlığa göre
  tablo seçiliyor (tablo sırasına bağlı kalmaktan sağlam: site araya
  tablo eklerse indeks kayar, başlık kaymaz). Başlık bulunamazsa sessizce
  yanlış tablo seçmek yerine boş döner. 6 test.
- **METODOLOJİ KARARI (Yavuz, hibrit yapı) — bu vertikalin en kritik
  noktası:** tüm modellerin ham medyanı YANILTICI olurdu. Ölçtük:
  **3,2 milyon TL** çıkıyor, oysa Türkiye'de gerçekte alınan araç çok
  daha ucuz. Sebep: **liste ağırlığı, satış ağırlığı değil** — listede
  Porsche ile Fiat eşit sayılıyor. Bunun yerine:
  - **`en-ucuz-sifir-arac`**: her markanın giriş (en ucuz) modelinin
    fiyatı, 24 marka → **medyan 2.069.000 TL** (en ucuz Dacia 1.295.000).
    Net tanımlı ve "en ucuz sıfır araba kaç para?" en çok sorulan
    sorulardan. TOPLAMA GİREN tek kalem.
  - **Marka kalemleri** (Tesla, BYD, Suzuki, Cupra): `bilgi_amacli`,
    TOPLANMAZ. Sebep: birbirinin ALTERNATİFİ — bir kişi hem Tesla hem
    Suzuki almaz. Toplandığında 17,7 milyon TL gibi anlamsız bir sayı
    çıkıyordu (ilk çalıştırmada bu görüldü ve düzeltildi).
- **Popüler markalar (Togg/Renault/Fiat) EKSİK:** o markaların tabloları
  sayfada JS ile yükleniyor, ham HTML'de yok — yalnızca Tesla/BYD/Suzuki/
  Cupra tabloları mevcut. Popüler markalar için ikinci kaynak aranmalı.
- **Bu vertikalde HESAPLAYICI YOK** (`hesaplayici_var: False`): kalemler
  alternatif olduğu için toplama hesabı anlamsız. sayfa_uret.py artık bu
  bayrağa göre sitemap'e ve menülere hesaplayıcı linki eklemiyor —
  **aksi halde sitemap'te 404 oluşuyordu ve sitemap Search Console'a
  gönderilmişti.**
- `/arac/metodoloji/` yazıldı: "neden ortalama araç fiyatı vermiyoruz",
  "marka kalemleri neden toplanmıyor", fiyata dahil olmayanlar (sigorta/
  MTV/tescil/yakıt), tek kaynak ve oynaklık uyarısı.

## ARAÇ SAHİP OLMA MALİYETİ HESAPLAYICISI (2026-07-25, Yavuz'un önerisi)
- **Bir tasarım hatası düzeltildi.** İlk turda "araç vertikalinde
  hesaplayıcı anlamsız" demiştim — kalemler birbirinin alternatifi
  olduğu için TOPLAMA hesabı gerçekten anlamsız, o kısmı doğruydu. Ama
  **eksik düşünülmüştü:** asıl değer araç fiyatının ÜZERİNE binen
  maliyetlerde. Etiket fiyatı aracın gerçek maliyeti değil ve bu toplamı
  kimse tek yerde vermiyor. Yavuz bunu fark etti.
- `assets/js/arac-ek-maliyetler.js` + `/arac/hesaplayici/`.
  **Her kalem `kaynak_tipi` taşır, resmî ile tahmini KARIŞTIRILMAZ:**
  - **RESMÎ — MTV (ilk yıl):** motor hacmi kademesine göre (1300cc'ye
    kadar 6.903, 1301–1600 12.028, 1601–1800 21.252 TL). Kaynak: 58 Seri
    No.lu MTV Genel Tebliği, 31.12.2025 R.G.
  - **RESMÎ — Noter + ilk tescil:** satış bedelinin binde 2'si (asgari
    1.000 TL) + sabit noter ücreti. 2026 nispi harç düzenlemesi.
  - **TAHMİNİ:** plaka/ruhsat, zorunlu trafik sigortası, kasko
    (araç değerinin ~%3'ü).
  - Sonuç ekranı resmî ve tahmini toplamı AYRI gösterir.
  - Örnek: 2.069.000 TL araç → 92.656 TL ek (18.086 resmî + 74.570
    tahmini) → 2.161.656 TL.
- **YILLIK GÜNCELLEME GEREKİR:** MTV ve harçlar her 31 Aralık'ta Resmî
  Gazete'de yeniden değerleme oranıyla artıyor. `arac-ek-maliyetler.js`
  içindeki `yil` alanı ve tutarlar elle güncellenmeli — bu kalemler
  kazınmıyor (yılda bir değiştiği için kazımaya değmez, ama TAHMİNİ de
  değil: kaynağı belli resmî tarife).
- **TARAYICI TESTİNDE GERÇEK BUG YAKALANDI:** `<input step="50000">`
  yüzünden kullanıcı 1.295.000 gibi gerçek bir araç fiyatı yazınca HTML5
  validation formu sessizce bloke ediyordu — sayfa **varsayılan değerle
  bile** submit olmuyordu. `step="1"` yapıldı.
  **DERS:** `step` niteliği "artış miktarı" değil, GEÇERLİLİK KISITI.
  Serbest sayı girilen alanlarda `step="1"` (veya `any`) kullanılmalı.
  Bu bug yalnızca gerçek tarayıcıda `requestSubmit()` denenince ortaya
  çıktı; `dispatchEvent(submit)` validation'ı atladığı için "çalışıyor"
  gösteriyordu — form testlerinde validation'ı ATLAYAN yöntem kullanmak
  yanıltıcı.
- 12 JS testi: kademe sınırları (1300/1301), asgari harç tabanı,
  resmî/tahmini ayrımı, aritmetik tutarlılık, seçilmeyen kalemin
  hesaba girmemesi.

## YAVUZ'UN ELEŞTİRİLERİ VE DÜZELTMELER (2026-07-25)
Yavuz sitenin canlı halini inceleyip beş ciddi eleştiri getirdi. Hepsi
haklıydı, hepsi düzeltildi:

1. **"Site çok açıklayıcı, bütün sırlarımızı ortaya döküyor. Bu dürüstlük
   değil enayilik."** → Metodoloji sayfalarından iş sırrı niteliğindeki
   bölümler ÇIKARILDI: "nazik kazıma ilkeleri" (istek aralığı, robots.txt
   detayı), sağlık kontrolü eşikleri, hangi kaynağın neden bırakıldığı,
   kaynak türü listesi. "Kazıyoruz/robots.txt/karantina/motor.py" gibi
   ifadeler metinden tamamen kaldırıldı ("derlenir", "ölçülür" oldu).
   **Kalan:** neyi ölçtüğümüz, segment tanımı, sınırlar, güncelleme
   sıklığı — yani güven veren kısım. Dosya boyutları ~%15 küçüldü.
   **KURAL: metodoloji "neyi ölçüyoruz"u anlatır, "nasıl kazıyoruz"u DEĞİL.**

2. **"Otomobil sekmesi çok zayıf, markalar yok, model isimleri yok."**
   → **ÇÖZÜLDÜ: 4 marka → 24 marka, 492 model.** Kök neden: marka
   tabloları JS ile yükleniyordu, `render_gerekli: true` eksikti.
   Ayrıca `tablo_urunler`'de **nbsp bug'ı** vardı: başlıklar
   "Sıfır\xa0Togg fiyatları" şeklinde geliyor, tam metin eşleşmesi
   tutmuyordu — başlık karşılaştırması artık boşlukları normalize ediyor.
   Togg, Renault, Dacia, Fiat, Hyundai, Toyota, VW, BMW, Mercedes dahil
   24 marka. 8 kalem sayfası (popüler markalar).

3. **"Trendyol'a bizim sitemizden gidecek insan yok, linklendirmiyoruz."**
   → Kalem sayfalarına **"Nereden bakabilirsiniz"** bölümü eklendi;
   `KAYNAK_SITELERI` + `kalem_kaynak_linkleri()` ile kaynaklar.yaml'dan
   otomatik üretiliyor. Şu an düz link (`rel="nofollow noopener"`).
   **Affiliate programına kabul alınınca takip parametresi YALNIZCA
   `KAYNAK_SITELERI` sözlüğüne eklenecek** — sayfa şablonlarına
   dokunmaya gerek yok, `rel` de o zaman `sponsored` olmalı.

4. **"Buzdolabı 45 bin TL lüks diyoruz ama asıl lüks 80.000'den başlıyor."**
   → Haklı: Trendyol kategori sayfasında max 62K var, gerçek premium
   modeller listede yok. `?sst=PRICE_BY_DESC` ve `?prc=` filtreleri
   denendi — **Trendyol tüm filtreleri JS ile uyguluyor, sunucu HTML'i
   değişmiyor**, o yüzden pahalı ürünler çekilemiyor.
   **Çözüm: "Lüks" → "Üst" segment.** 43K buzdolabı lüks değil, yaygın
   ürünler içindeki üst çeyrek. Metodolojiye "örneklem sınırı" uyarısı
   eklendi: üst segment = piyasanın en pahalısı değil, *listedeki* üst
   çeyrek. İleride premium marka kategorileri ayrı kaynak olarak eklenebilir.

5. **"Tekrar tekrar izin istiyorsun, tek seferde verdiğim izni kullan."**
   → **KURAL: Yavuz bir yön onayladıysa, o yönün alt kararlarını sorma —
   uygula ve sonucu bildir.** AskUserQuestion yalnızca gerçekten geri
   dönülemez ya da ürün stratejisini değiştiren çatallarda kullanılmalı.

## SEO/GEO — E-E-A-T VE EKSİKLER (2026-07-25)
Yavuz "daha önemli gördüğün bir eksik var mı?" diye sordu. Ölçüldü,
üç ciddi eksik bulundu ve kapatıldı:

1. **E-E-A-T YOKTU — en kritik olanı.** Sitede hakkımızda/iletişim/
   yayıncı kimliği hiç yoktu. **Neden kritik:** maliyet-fiyat içeriği
   Google'ın **YMYL** (Your Money or Your Life) kategorisine giriyor;
   bu kategoride kimliği belirsiz siteler kasıtlı olarak bastırılıyor.
   AI motorları da kaynak seçerken yayıncı kimliğine bakıyor —
   "Maliyeti Ne? verilerine göre" diye alıntılanmak istiyorsak "Maliyeti Ne? kim?"
   sorusunun cevabı sitede olmalı.
   → `/hakkimizda/` (neden kurduk, veriyi nasıl elde ediyoruz,
   **bağımsızlık beyanı**, gelir modeli şeffaflığı, **düzeltme
   politikası**) ve `/iletisim/` (hata bildirimi, basın, veri iş birliği)
   yazıldı. Organization schema'ya `contactPoint` eklendi, footer'a
   kurumsal linkler kondu. E-posta: **info@maliyetine.com.tr** —
   Cloudflare Email Routing ile ücretsiz kurulmalı (Yavuz'un tarafında).
2. **`og:image` hiçbir sayfada yoktu** → 1200×630 PNG üretildi
   (`assets/og-gorsel.png`), tüm şablonlara + `twitter:card` =
   `summary_large_image`. Paylaşımda artık boş kutu çıkmıyor.
3. **`www` duplicate content** → hâlâ AÇIK. Kök ve www ikisi de 200
   dönüyor. Canonical var ama 301 daha güçlü sinyal.
   **Yavuz'un tarafında:** Cloudflare → Rules → Redirect Rules ile
   `www.maliyetine.com.tr/*` → `maliyetine.com.tr/$1` (301).

**Ayrıca eklendi:**
- **Product/AggregateOffer schema** kalem sayfalarına (fiyat rich
  result adayı). Tek ürün değil ölçülen küme temsil edildiği için
  `AggregateOffer` + `lowPrice`/`highPrice`/`offerCount`.
- **`llms.txt`** — AI motorları için yapılandırılmış özet (endeksler,
  ham JSON bağlantıları, segment tanımı, "alıntılarken tarih belirtin"
  notu). Yeni ve deneysel bir standart ama maliyeti sıfır, GEO
  iddiamıza doğrudan uygun.
- **Özel `404.html`** — vertikal kartlarıyla, `noindex`.

**KAPATILAMAYAN EN BÜYÜK EKSİK: backlink yok (sıfır dış link).**
Teknik bir iş değil; zamanla ve içerikle gelir. Yıllık karşılaştırma
haberleri ("düğün maliyeti %X arttı") tam bu işe yarayacak — o yüzden
aylık veri birikimini kesintisiz sürdürmek stratejik öncelik.

## KALEM SAYFALARI: "ŞOV" DEĞİL FİYAT (2026-07-25 Yavuz'un ikinci uyarısı)
Yavuz `/arac/fiat-fiyatlari/` sayfasına girip şunu söyledi: *"donanımhaber'den
veriyi nasıl çektiğimiz yazıyor, kaynaklar ve yöntem yazıyor. İnsanlar bunları
okumaya mı giriyor araba fiyatları hakkında bilgi almaya mı? Bizim kişisel
şovumuzu mu okuyacaklar?"* — haklıydı.
- **KALDIRILDI:** kalem sayfalarındaki "Kaynaklar ve yöntem" bölümü (hangi
  siteden kaç ürün çekildiğini tek tek listeliyordu) ve SSS'deki uzun
  metodoloji anlatımı ("her kaynağın kendi medyanı alınır, sonra kaynaklar
  arası medyan hesaplanır, aykırı değerler ayıklanır…").
- **YERİNE:** sayfanın en altında **tek satır künye** —
  `15 üründen derlendi · 2026-07-25 · Yöntem` (metodoloji linki).
  Şeffaflık için gereken bilgi tek satıra sığıyor.
- SSS'de kalan: "X fiyatları ne kadar?", "aralarında ne kadar fark var?",
  "fiyatlar ne zaman güncellendi?" — hepsi KULLANICININ sorusu.
- Sonuç: kalem sayfası 324 → 249 kelime, içeriğin ağırlığı fiyat tablosuna
  ve "nereden bakabilirsiniz" bölümüne kaydı.
- **KURAL:** kalem sayfası ürünün fiyatını anlatır. Yöntem anlatımı
  YALNIZCA metodoloji sayfasında olur (oraya giren zaten detay istiyor).
  Şeffaflık = tek satır künye + metodoloji linki; sayfa doldurmak değil.

## KALEM SAYFALARI 9 → 59 (2026-07-25)
Kapsam veriye göre değil elle seçilmişti: **59 ürünlük nevresim takımının
sayfası yokken 4 ürünlük televizyonun vardı.** Ev-kurmanın 42, düğünün 8
kaleminden yalnızca 9'unun landing sayfası vardı — uzun kuyruk trafiğinin
tamamı buradan gelecekken. Kimse "ev kurma maliyeti" aramadan önce
"çamaşır makinesi fiyatları" arıyor.
- **`KALEM_SAYFA_NOTLARI`** (sayfa_uret.py): her kalem için ELLE yazılmış,
  o kaleme özgü bir not (kapasite, kumaş cinsi, motor tipi, BTU...).
  **Programmatic SEO kırmızı çizgisi böyle korunuyor:** sayfalar toplu
  üretiliyor ama gövde zaten kaleme özgü gerçek ölçülmüş veriden geliyor
  (fiyat tablosu, segment, örneklem, SSS, kaynak linkleri); tek elle
  yazılan alan bu not. **Notu yazılamayan kaleme sayfa AÇILMAZ** (testle
  kilitli) — şablon cümle üretmek yasak.
- **`KALEM_SAYFASI_ASGARI_URUN = 8`**: örneklemi düşük kaleme sayfa
  açılmaz. 3 üründen "halı fiyatları" sayfası yapmak hem okuyucuyu
  yanıltır hem ince içerik olur. Eşik çalışma anında uygulanıyor
  (`kalem_sayfalarini_genislet()`, main() başında) çünkü hangi kalemin
  sayfayı hak ettiği O AYKI ölçüme bağlı.
- **Dip bölümdeki "diğer kalemler" listesi 38 linke çıkmıştı** — sayfanın
  kendi içeriğini bastıran link-farm görünümü. Aynı GRUPTAN (Beyaz eşya,
  Tekstil…) en fazla 8 linkle sınırlandı; konu olarak da daha alakalı bir
  iç link sinyali. Endeks sayfası hub olduğu için orada tam liste kalıyor.
- **Doğrulama:** 169 segment rakamının tamamı `/veri/*.json` ile birebir
  aynı (uydurma sayı yok), 2621 iç linkte 0 kırık, 0 yetim sayfa, 59/59
  JSON-LD parse OK, sayfa başına 238–435 kelime, birebir aynı gövde yok.
  sitemap 29 → **68 URL**, IndexNow ile bildirildi.
- **Not:** `televizyon` sayfası 4 örneklemle eşiğin altında ama ZATEN
  açık olduğu için korunuyor (URL kırmamak için). Örneklemi büyütmek
  gerek — Trendyol televizyon kategorisi az ürün döndürüyor.

## TAHMİNİ ORAN %26 → %7 (2026-07-26)
Dört hizmet kalemi gerçek kaynağa taşındı. Kaynak: **dugun.com'un kategori
sayfalarındaki il bazlı fiyat tabloları** (İstanbul satırı).
- `motor.tablo_urunler`'e iki yetenek: **`icerik_metni`** (tabloyu kendi
  içeriğine göre seçer — bu sayfalarda tablonun üstündeki başlık tabloyla
  alakasız) ve **`satir_filtresi`** (yalnızca eşleşen satır alınır).
- **Tahminler İKİ YÖNE BİRDEN sapmış:** fotoğrafçı 45.000→15.600 (3× yüksek),
  organizasyon 40.000→22.150, kuaför 5.000→**12.450** (2,5× düşük),
  gelin arabası 3.000→**9.800** (3,3× düşük). Ders pekişti: "makul görünen"
  tahmin doğru demek değil, ve sapmanın yönü tahmin edilemiyor.
- **METODOLOJİ — neden 27 ilin tamamı alınmadı:** hepsini alıp persentille
  segmentlemek **coğrafi farkı fiyat segmenti gibi gösterirdi**. "Ekonomik
  fotoğrafçı" ucuz bir ilde çalışan fotoğrafçı demek olmaz. Dört kalem de
  `tek_deger` bayrağıyla işaretli, UI'da **"Tek ölçüm — segment kırılımı
  yok"** etiketi taşıyor, metodolojide ayrı bölüm var.
- **GÜVEN KANITI:** aynı sitenin salon tablosu İstanbul için 500 TL/kişi
  veriyor; bizim DüğünBuketi'nden **bağımsız** ölçtüğümüz kokteyl medyanı
  da 500 TL. İki ayrı kaynak aynı rakamda buluşuyor.
- **BULUNAN BUG (sessiz olurdu):** tek ürünlü kaynakta `segmentle()`
  yalnızca `dusuk` segmentini dolduruyordu — orta segment seçen kullanıcı
  bu kalemleri **hiç görmeyecekti**. `n == 1`'de üç segment de aynı değeri
  alır (2 test).
- Düğün toplamı **396.877 TL**; 368.377 TL'si (12 kalem, 6 bağımsız kaynak)
  gerçek, 28.500 TL'si (2 kalem) tahmini. Kalan tahminiler: orkestra-dj
  (Yavuz: "salla, çoğu salonda fiyata dahil") ve nikah-işlemleri 3.500 TL
  (ölçüldü: 2025 ilçe medyanı ~2.500, 2026 için doğru bantta).

## ÖLÇÜM SIKLIĞI: AYDA 2 KEZ (2026-07-26, Yavuz'un kararı)
Cron `0 6 5,20 * *`. Zaman serisi projenin kopyalanamaz tek varlığı.
- **`gecmis.ASGARI_GUN_ARALIGI` 20 → 10** yapılmak ZORUNDAYDI: 20 kalsaydı
  14 günlük normal aralık reddedilir, hiçbir değişim hesaplanamazdı.
- **`_fiyat_gecmisi_html`** kalem sayfalarına eklendi: zaman serisi tablosu
  + "X'ten Y'ye medyan %Z arttı" özeti. Yeterince uzak iki ölçüm yoksa
  bölüm **hiç render edilmiyor** (boş "geçmiş" başlığı veri varmış
  izlenimi verir). **5 Ağustos'taki ölçümde kendiliğinden açılacak.**

## KAYNAK ARAMA ARTIK TOPLU: `scraper/kaynak_tara.py` (2026-07-26)
Yeni kaynak aramak en pahalı işti — her aday için ayrı robots kontrolü,
URL tahmini, çekilebilirlik testi. Adayların çoğu boş çıkıyordu ve her
404 bir tur kaybıydı. Script hepsini tek turda yapıp tablo döner:
robots → **ana sayfadan kategori linki avlama** (URL tahmin etmek yerine —
Vatan/IKEA/Bellona/Altınbaş derslerinin panzehiri) → çekme → JSON-LD/
microdata/fiyat teşhisi. Çıktı: YEŞİL / SARI / KIRMIZI.
- **İlk tur sonucu (Yavuz'un önerdiği 10 site, ~2 dakika):**
  - **SARI (fiyat var, CSS seçici gerekir):** **idefix** (62 fiyat, en
    değerli aday — geniş kategori), bosch, profilo.
  - **robots RET:** epttavm, arçelik, beko.
  - **KIRMIZI/erişilemedi:** lg (JS), çiçeksepeti, samsung (kategori değil
    tek ürün sayfasına düşüyor).
  - **epey:** düz `requests` ile çekilemiyor ama **Playwright ile
    çekilebiliyor** (212KB). Fiyat geçmişi grafiği **canvasjs canvas'ına**
    çiziliyor — veri HTML'de YOK, ayrı AJAX endpoint keşfi gerekir.
    Üstelik tek ürün bazlı (belirli bir TV modeli), bizim kalem
    medyanımıza karşılık gelmiyor. **Geriye dönük seri için doğru kaynak
    TÜİK** (data.tuik.gov.tr robots ONAY, erişilebilir) — TÜFE alt
    kalemleri: ev eşyası (COICOP 05), giyim (03), lokanta (11).

## IDEFIX ve TÜİK TURU — İKİSİ DE KESİN SONUÇLA KAPANDI (2026-07-26)

### idefix — BIRAKILDI (kod sorunu değil, sayfa yapısı)
- Toplu tarayıcı idefix'i "62 fiyat" ile **en umut verici aday** göstermişti.
  **Yanlış pozitifti:** o metinler *"TROY ile 200 TL İndirim"* gibi
  **promosyon rozetleriydi.**
- **Lazy loading ÇÖZÜLDÜ:** ilk ekranda yalnızca 1 ürün fiyatı vardı,
  6 kaydırma sonrası **37 gerçek fiyat** geldi. `motor.getir_playwright`'a
  **`kaydirma` parametresi eklendi** (`kaynaklar.yaml` → `kaydirma: 6`).
  Bu yetenek kalıcı — başka lazy-load kaynaklarda da kullanılabilir.
- **AMA KESİN ENGEL:** sayfada 97 ürün linki var, fiyatların yalnızca
  **1'i** bir ürün linkinin İÇİNDE. Fiyatlar ayrı bir DOM dalında duruyor;
  hangi fiyatın hangi ürüne ait olduğu güvenilir şekilde belirlenemiyor.
  Zorlanırsa **yanlış ürüne yanlış fiyat** atanır — bu KIRMIZI ÇİZGİ
  ihlali olurdu. `aktif: false` bile eklenmedi, kaynak yazılmadı.
- **`kaynak_tara.py` bu dersle güçlendirildi:** artık (a) promosyon
  metinlerini fiyat saymıyor (`SAHTE_FIYAT` filtresi), (b) **`kart_ici`**
  sayıyor — fiyat bir ürün linkinin içinde mi? Kart dışındaysa
  "KIRMIZI - eşleşme kurulamaz" diyor. Bu olmadan tarayıcı gelecekte
  aynı tuzağa tekrar yönlendirirdi.

### TÜİK — API BULUNDU AMA ERİŞİLEMEDİ
- `data.tuik.gov.tr` → **`veriportali.tuik.gov.tr`'ye 302** (React SPA).
  Ham HTML boş kabuk (3.692b), link yok.
- Playwright ağ dinlemesiyle **gerçek REST API yakalandı:**
  `veriportali.tuik.gov.tr/api/tr/data/statistical-themes` ve
  `/api/tr/data/autocomplete?text=` (ikisi de sayfa yüklenirken HTTP 200).
- **AMA doğrudan çağrılınca 404** — hem `requests` ile hem sayfa
  içinden `fetch` ile. API yalnızca kendi SPA route bağlamında çalışıyor.
- **Menüde `SDMX` var** — uluslararası istatistik veri değişim standardı,
  genelde açık endpoint sunar. Bir sonraki turda İLK bakılacak yer burası.
- **ALTERNATİF (kesin çalışan): TCMB EVDS API.** Ücretsiz, resmî, JSON,
  TÜFE alt kalemlerini (ev eşyası COICOP 05, giyim 03, lokanta 11)
  veriyor. **Yalnızca API key gerekiyor — Yavuz'un 5 dakikalık işi**
  (evds2.tcmb.gov.tr → kayıt → profilden key). Key gelirse entegrasyon
  yazılabilir: geriye dönük seri + resmî çapraz doğrulama.

## REHBER (BLOG) SAYFALARI — `scraper/rehber.py` (2026-07-26)
Yavuz'un talimatı: *"SEO ve GEO tarafını çok mutlu edecek bloglar yaz.
Ama yapay zeka gibi değil, gerçekçi."*
- 4 yazı: `/rehber/150-kisilik-dugun-maliyeti/`, `/rehber/yemekli-mi-kokteyl-mi/`,
  `/rehber/sifirdan-ev-kurma-listesi/`, `/rehber/sifir-araba-gercek-maliyeti/`
  + `/rehber/` dizini. 315–354 kelime.
- **METİN elle yazılı, RAKAMLAR veriden.** Gövde fonksiyonları `/veri/*.json`
  okur; aylık ölçümde yazılar da kendiliğinden güncellenir. **Bayat rakamlı
  blog yazısı, güven kaybının en hızlı yolu** — bu yüzden hiçbir tutar
  metne gömülmedi.
- **Veri yoksa sayfa ÜRETİLMEZ** (testle kilitli). Boş/rakamsız yazı
  yayınlamıyoruz; ana sayfa ve sitemap de yalnızca gerçekten yazılmış
  dosyalara link veriyor (404'e link çıkmasın).
- **YAZIM KURALI dosyanın başında kayıtlı:** rakamla başla, girizgah yapma;
  cümle uzunlukları değişsin; her şey madde listesi olmasın; "Unutmayın ki /
  Sonuç olarak / Peki ya / Kısacası" gibi dolgu kalıpları YOK; kendi
  ölçümümüzden çıkan şaşırtıcı şeyi söyle; bir şey ters gittiyse onu da
  söyle. **Bir test bu klişe kalıpları arayıp bulursa başarısız oluyor.**
- Article + BreadcrumbList schema, ana sayfada "Rehberler" bölümü,
  yazılar birbirine iç link veriyor (kendine link vermiyor — testli).
  sitemap 66 → **71 URL**, IndexNow'a bildirildi.
- Workflow'a eklendi: `rehber.py` → ardından `sayfa_uret.py` (sitemap ve
  ana sayfa rehber dosyalarının varlığına baktığı için SIRA ÖNEMLİ).

## "MEDYAN" → "ORTALAMA" (2026-07-26, Yavuz'un kararı)
*"Medyan çok istatistik kelimesi kalıyor."* Görünür metinlerde terim
bırakıldı; tablo başlıkları, cevap blokları ve meta açıklamalar artık
"ortalama fiyat" diyor.
- **AMA metodolojide açıkça yazıyor** (üç metodoloji sayfasına
  `"Ortalama fiyat" derken` bölümü eklendi): kullandığımız değer
  aritmetik ortalama değil **ortanca**, ve nedeni — tek bir çok pahalı
  ürün aritmetik ortalamayı yukarı çekip kimsenin ödemediği bir rakam
  üretir. Bunu yazmadan "ortalama" demek yanıltıcı olurdu.
- schema.org `measurementTechnique` alanında teknik terim KALDI (orası
  AI motorlarına metodolojiyi anlatan teknik alan, kullanıcıya görünmüyor).

## BAYAT SAYFA SORUNU + HİSTEREZİS (2026-07-26)
Kalem sayfası sayısı 9→59'a çıkarken sessiz bir sorun birikti: bir sayfa
üretim listesinden düştüğünde **diskteki dosya olduğu gibi kalıyordu.**
Sonuç: canlıda 200 dönen, günler önce ölçülmüş rakamları gösteren,
sitemap'te olmayan yetim sayfalar. 6 tane birikmişti —
`/arac/tesla-fiyatlari/` hâlâ 07-25 verisini gösteriyordu.
- **`bayat_kalem_sayfalarini_temizle()`**: üretimde artık geçerli olmayan
  `{kalem}-fiyatlari` dizinlerini siler. `hesaplayici` ve `metodoloji`
  asla silinmez (testli).
- **`KALEM_SAYFASI_KAPATMA_ESIGI = 5`** (açma eşiği 8): örneklem ay ay
  dalgalanıyor (9→7→10). Tek eşikle aynı sayfa açılıp kapanıyor, her
  kapanışta canlı bir URL bayatlıyordu. Açmak için 8, kapatmak için 5.
- Sonuç: tesla/byd/suzuki (hiç geçerli listede olmamışlardı) silindi →
  canlıda 404; yemek-ikram, gelin-ayakkabısı, perde histerezisle korundu.
- **Yan bulgu:** araç kalem sayfaları 25 Temmuz'dan beri üretilmiyordu —
  bir tur çıktı `>/dev/null`'a basıldığı için fark edilmemişti.
  **DERS: üretim komutlarının çıktısını bastırma.**

## RESMÎ TÜFE ENTEGRASYONU — `scraper/enflasyon.py` (2026-07-26)
ÇOK KAYNAK KURALI'nın 5. katmanı (TÜİK doğrulaması) nihayet kuruldu.
Yavuz EVDS'ye üye olup API anahtarını verdi.

**EVDS API'sine erişim — yol uzundu, tekrar yaşanmasın diye kayıt:**
- `evds2` → **`evds3`'e taşınmış**. Klasik `/service/evds/series=...&key=...`
  yolu **artık çalışmıyor**: SPA her yolu `index.html`'e düşürüyor ve
  **geçersiz anahtarla bile aynı yanıtı veriyor** — yani hata mesajı da
  alamıyorsunuz, sessizce HTML dönüyor. Teşhis `allow_redirects=False`
  ile yapıldı (302 → evds3 göründü).
- **Yeni yol: `POST https://evds3.tcmb.gov.tr/igmevdsms-dis/fe`**, JSON
  gövde. Gövdede **`groupSeperator` ve `isRaporSayfasi` ZORUNLU** —
  eksikse sunucu 500 döner (bilinen çalışan seriyle bile).
- Arama: `GET /igmevdsms-dis/searchResults?searchVal=`
- Endpoint'ler Playwright ağ dinlemesiyle bulundu (arayüzün kendi
  isteklerini yakalayarak).

**SERİ KODLARI DOĞRULANDI, TAHMİN EDİLMEDİ — kritik:**
İnternette yaygın olan `TP.FG.J*` kodları **arşiv serisi** çıktı; 2026
Ocak'ta duruyorlar. Güncel seriler **`TP.FE25.*`** (2025=100 bazlı).
Arama endpoint'inden 28 seri adı çekilip eşlendi. Bu adım atlanıp
"01=genel, 02=gıda…" diye varsayılsaydı **"ev eşyası %12 arttı" derken
bambaşka bir grup gösterilecekti** — KIRMIZI ÇİZGİ ihlali.
- `TP.FE25.OKTG01` TÜFE genel · `OKTG19` Giyim ve ayakkabı (→ düğün) ·
  `OKTG20` Dayanıklı mallar, altın hariç (→ ev-kurma) · `OKTG25` Lokanta
  ve oteller (→ düğün) · `OKTG22` Alkollü içecek, tütün ve altın (→ düğün)
- 2026 Ocak–Haziran: genel **%12,3**, giyim %12,1, lokanta %12,0,
  dayanıklı mallar %5,8.

**KIRMIZI ÇİZGİ — TÜFE bizim fiyatımızın yerine GEÇMEZ.** TÜFE bir
ENDEKS (2025=100), TL cinsinden fiyat değil. Rehber yazılarında ayrı
bölümde, kaynak adıyla ve *"bizim ölçümümüz TL cinsinden gerçek
fiyatları izler"* cümlesiyle veriliyor. Bir test endeks değerinin TL
gibi sunulmadığını doğruluyor.

**Anahtar güvenliği:** `scraper/.evds-key` **gitignore'da**, dosya izni
600. Workflow anahtarı **GitHub Secrets'tan** (`EVDS_KEY`) okuyor.
Secret yoksa adım sessizce atlanıyor ve sayfalarda o bölüm hiç
görünmüyor (uydurma rakam yok).
- **YAVUZ'UN YAPMASI GEREKEN:** GitHub → repo → Settings → Secrets and
  variables → Actions → New repository secret → adı `EVDS_KEY`,
  değeri EVDS anahtarı. Bu yapılmazsa aylık otomasyonda TÜFE bölümü
  üretilmez (site çalışmaya devam eder, sadece o blok çıkmaz).

## OKUL VERTİKALİ — 4. vertikal (2026-07-26)
**Neden şimdi:** Ağustos'ta "okul alışverişi ne kadar" aramaları başlıyor,
Eylül'de zirve yapıyor. İndekslenme 3-4 hafta aldığı için pencere şimdi.
Diğer adaylar elendi: ev tadilatı işçilik ağırlıklı (fiyatlar internette
yok), tatil dinamik fiyatlı (aylık ölçüm modelimize uymuyor).

**14 kalem, 5 grup:** Çanta ve beslenme (okul çantası, beslenme çantası,
suluk) · Kırtasiye (kalem kutusu, defter, kalem, boya seti, resim
malzemeleri) · Kitap (ders/yardımcı kitap, sözlük) · Giyim (spor ayakkabı)
· Teknoloji + Çalışma alanı (tablet, çalışma masası, sandalyesi).

**`varsayilan_dahil: False` — önemli tasarım kararı:** tablet, çalışma
masası ve sandalyesi HER YIL alınmaz, bir kez alınıp yıllarca kullanılır.
Varsayılan toplam bunları İÇERMEZ; kullanıcı hesaplayıcıdan ekler. Aksi
halde tek seferlik harcamalar yıllık masrafmış gibi görünüp rakamı
yanıltıcı şişirirdi.

**KATEGORİ URL'LERİ NASIL BULUNDU (yöntem notu):** Trendyol'un
**"Okula Dönüş" koleksiyon sayfasından** (`/s/okul-alisverisi`, robots
ONAY) 61 temiz kategori linki toplandı. URL TAHMİN EDİLMEDİ.
- Denenip elenen yollar: Trendyol **arama sayfası (`/sr?q=`) robots.txt'te
  YASAK**; `sitemap.xml` yok, robots.txt'te sitemap satırı da yok;
  kategori sayfalarından gezinme JS yüzünden sayfa başına 2-6 link
  veriyor (verimsiz). Koleksiyon sayfası hepsini tek yerde topluyor —
  **yeni vertikal açarken önce böyle bir hub sayfası aranmalı.**
- Bulunamayan kalemler: **okul forması/önlüğü** (kategori yok),
  çocuk bedeni ayakkabı (genel "spor ayakkabı" kullanıldı, kaynakta
  not düşüldü).

**TÜFE eşlemesi:** TÜİK'te "kırtasiye/eğitim malzemesi" diye ayrı grup
YOK. En yakın karşılık `OKTG21` *Diğer temel mallar* (kırtasiye buraya
giriyor) + `OKTG19` *Giyim ve ayakkabı*. Bir TÜFE grubunun birden fazla
vertikali ilgilendirebilmesi için şemaya `vertikaller` listesi eklendi
(giyim: hem düğün hem okul).

## ANA SAYFA YAZISI (2026-07-26, Yavuz'un talebi)
Ana sayfanın en altına "Bu rakamlar ne anlama geliyor?" bölümü eklendi
(`rehber.anasayfa_yazisi()`). **Neden ana sayfada yazı:** ana sayfa
GEO'nun ilk temas noktası ve en çok dış link alacak sayfa; üstteki
kartlar rakamı veriyor ama BAĞLAM vermiyor.
- İçerik: dört endeksin toplamı bir arada (iç linkli) · TÜFE ile
  "bu rakamlar hızlı eskiyor" bağlantısı · "neyi ölçmüyoruz" (konut,
  kira, işçilik — tek sayıya sığmadığı için kapsam dışı) · tahminlerin
  iki yönde birden saptığı itirafı · veriyi kullanma daveti (ham JSON +
  "ölçüm tarihini belirtin" ricası).
- Rakamlar veriden gelir, metne gömülü DEĞİL.
- **BULUNAN BUG (test yakaladı):** yazı `veri_kok` parametresini yok
  sayıp her zaman canlı dosyaları okuyordu — `anasayfa_uret(veri_kok=X)`
  çağrısı yazıda yanlış veriyi gösterirdi. Aktarıldı, 2 test eklendi.

## TASARIM ELDEN GEÇİRİLDİ (2026-07-26)
Daha önce "hepsi kötü ama acelemiz yok" denip ertelenmişti. **Kör
çalışılmadı:** Playwright ile ekran görüntüsü alınıp bakılarak yapıldı —
sorunların çoğu ancak görünce fark edildi.
- Ana sayfa **3244px → 2532px**. Kartlar dengelendi.
- Renk: jenerik mavi → sakin teal-mavi (`#0f5c8c`); rakamın yanında link
  mavisiyle karışmıyor. **Karanlık mod** eklendi (`prefers-color-scheme`).
- Gövde **780 → 880px**: 5 sütunlu fiyat tabloları sıkışıyordu.
- Tablolar (sitenin asıl ürünü): zebra satır, hover, kalın başlık çizgisi,
  ilk sütun vurgusu, dar ekranda kendi içinde kaydırma.
- Cevap bloğu sol kenar vurgusu aldı (GEO'nun en önemli bloğu).
- **MOBİL:** üst bar kırılıyordu — logo *"Maliyeti / Ne?"* diye iki satıra,
  menü öğeleri sarkıyordu. Logo üstte tek satır, menü altta yatay kaydırmalı.

**Ekran görüntüsü iki bug ortaya çıkardı:**
1. **"Yakında" kartları SABİT LİSTEYDİ.** 0 km araç yayına girdikten sonra
   da "Yakında — Hazırlanıyor" kartıyla görünüyordu; aynı endeks sayfada
   hem gerçek rakamla hem "hazırlanıyor" diye **iki kez** çıkıyordu.
   Artık yayındaki vertikaller listeden düşüyor.
2. **Kart etiketinde "Düğün Salonu" iki kez.** Kısa ad em-dash'ten
   kesildiği için `salon-yemekli` ve `salon-kokteyl` aynı etikete
   dönüşüyordu. `_kisa_kalem_adi()` varyantı parantezle koruyor:
   "Düğün Salonu (yemekli)" / "(kokteyl)".

**`ANASAYFA_KART_LINK_SINIRI = 8`:** ev-kurma kartı 42 kalem linki üretip
diğerlerinin üç katına çıkıyor, grid'i eziyordu. Fazlası "+N kalem"
etiketiyle endekse yönlendiriliyor.

**DERS: tasarım işinde ekran görüntüsü almadan çalışmak körlük.** İki bug
da CSS'le ilgisizdi ama ancak sayfaya bakınca görüldü.

## REHBER YAZILARI: 7 (2026-07-26)
`/rehber/` altında: 150 kişilik düğün · yemekli mi kokteyl mi · sıfırdan
ev kurma · sıfır araba gerçek maliyeti · okul masrafı ·
**ekonomik düğün nasıl yapılır** · **beyaz eşya bütçesi**.
336–445 kelime, rakamlar veriden, klişe-kalıp testinden geçiyor.

## AMAZON — ev-kurma/okul/düğüne İKİNCİ KAYNAK (2026-07-26)
Yavuz'un önerisiyle denendi. **Çalışıyor** ve ÇOK KAYNAK KURALI'nın en
büyük boşluğunu kapatıyor: ev-kurmanın 42 kaleminin 40'ı, okulun 14'ünün
tamamı tek kaynaklıydı (Trendyol).
- **robots.txt ARAMA sayfasına bile ONAY veriyor** (`/s?k=`) — kategori
  URL'i avlamaya gerek kalmadı, Trendyol/okul turundaki en pahalı iş buydu.
- **Düz `requests` ile ÇALIŞMIYOR:** 2.186 byte'lık boş kabuk dönüyor,
  başlık bile yok. `render_gerekli: true` + `kaydirma: 3` şart.
- Kart yapısı: `div[data-asin]` > `h2` (isim) + `.a-price .a-offscreen`
  (fiyat). **Fiyat kartın İÇİNDE** — idefix'i eleyen eşleşme sorunu yok.
- Fiyat formatı "21.999,00 TL" (TR); daha önce düzelttiğimiz TR/EN format
  ayrımı burada işe yaradı.
- **59 kalem eklendi:** ev-kurma 42 · okul 14 · düğün 3.
- **KAPSAM DIŞI:** araç (Amazon'da satılmıyor), tüm hizmet kalemleri,
  ve **gelinlik/damatlık/alyans/takı** — bunlarda Amazon'un ürün karması
  bizim ölçtüğümüz segmentle örtüşmüyor, endeksi bozma riski yüksek.
- **Sorgu kalitesi ölçüldü, varsayılmadı:** en riskli 4 sorgu (kalem,
  defter, perde, nikah şekeri) tek tek çalıştırılıp dönen ürün adları
  okundu — hepsi alakalı çıktı. Genel sorgular (`kalem`) yerine
  daraltılmış sorgular (`kurşun kalem seti`) kullanılıyor.
- İlk karşılaştırma: buzdolabı Trendyol 29.000 / Amazon 32.299 (+%11),
  çamaşır makinesi 24.799 / 28.000 (+%13). **Çapraz doğrulama eşiğinin
  (%30) altında — iki kaynak birbirini teyit ediyor.**

## VERİ AÇIKLIĞI KATMANI (2026-07-26) — rekabet kozu
*"Veriler herkese açık, kullanabilirsiniz"* yazıyorduk ama **indirilebilir
dosya yoktu** — yalnızca iç şemalı JSON vardı. Gazeteci, araştırmacı ya da
blogcu alıntılamak istediğinde elle kopyalamak zorundaydı.
**Alıntılanabilirlik bu işin merkezinde:** doğal bağlantının en güçlü
kaynağı "şu siteden veri aldık" cümlesi.

- **`scraper/veri_disa_aktar.py`** — 96 kalemin tamamı CSV:
  `/veri/csv/{vertikal}.csv` (sabit URL, linklenebilir) + tarihli arşiv
  sürümü + `tum-kalemler.csv`. **Tarihli sürüm neden var:** "2026
  Temmuz'da şöyleydi" diyen bir yazının bağlantısı, veri güncellenince
  ölü bağlantıya dönüşmesin.
- **UTF-8 BOM ŞART:** Excel BOM'suz UTF-8 CSV'yi Windows-1254 sanıp Türkçe
  karakterleri bozuyor ("Buzdolabı" → "BuzdolabÄ±"). Dosyayı açanın ilk
  izlenimi bozuk metin olmamalı.
- Her satırda **kaynak listesi + ölçüm tarihi** → rakam bağımsız
  doğrulanabilir. Güven iddiasının kanıtı bu.
- **`/veri/` indirme merkezi:** DataCatalog + Dataset + DataDownload
  schema, **CC BY 4.0** lisans, sütun açıklamaları, atıf ricası
  ("sadece ölçüm tarihini belirtin").
- **`llms.txt` artık ÜRETİLİYOR.** Elle yazılmıştı ve bayatlamıştı: okul
  vertikali listede yoktu, tarihler eskiydi, CSV hiç geçmiyordu.
  **AI motoruna bayat bilgi vermek hiçbir şey vermemekten kötü** — yanlış
  kalem sayısı doğrudan yanlış alıntıya dönüşür.

**YENİ REHBER — kimsenin veremeyeceği içerik:**
`/rehber/trendyol-mu-amazon-mu-ucuz/` — 45 kalemde iki kaynağı da
ölçtüğümüz için elimizde olan karşılaştırma. **DÜRÜST ÇERÇEVE:** bu
"hangi site ucuz" listesi DEĞİL; aynı ürünü değil kategori listelerindeki
**ürün karmasını** karşılaştırıyoruz ve yazı bunu açıkça söylüyor.
34 kalemde bir liste, 10 kalemde diğeri aşağıda.

## SENARYO SAYFALARI (2026-07-26) — gerçek arama niyeti
Mevcut 59 kalem sayfası tek bir sorgu kalıbını hedefliyordu: *"X fiyatı"*.
Ama insanların aradığı şey **kendi durumları**: "100 kişilik düğün
maliyeti", "sadece beyaz eşya bütçesi". Bu sorguların hepsinde veri
elimizdeydi ama sayfa yoktu.
- **`scraper/senaryo.py`** — iki tip: **ölçek senaryoları** (düğün
  100/200/300 kişilik) ve **grup senaryoları** (ev-kurma: beyaz eşya /
  mobilya / mutfak).
- **İNCE İÇERİK KIRMIZI ÇİZGİSİ:** her sayfa farklı RAKAM, farklı kalem
  listesi ve o senaryoya özgü yorum taşıyor (100 kişi → minimum kişi
  şartı; 300 kişi → salon kapasitesi ayrışması). Test 6/6 gövdenin
  benzersiz olduğunu doğruluyor. **Kombinasyon sayısı KASITLA düşük
  tutuldu** — "her sayı için bir sayfa" tam olarak Google'ın
  cezalandırdığı şey.
- **TESTLER İKİ BUG YAKALADI:** (1) tabloda kalem adı yerine ham id
  görünüyordu (`orkestra-dj`) — tahmini kalemler ayrı listede olduğu için
  tanım bulunamıyordu; (2) gerçek ölçüm olmadan da sayfa üretiliyordu:
  yalnızca tahmini kalemlerle "100 kişilik düğün 28.500 TL" çıkardı ve
  **tahminler sabit olduğu için üç senaryoda da AYNI rakam** görünürdü.
  Artık en az 2 gerçek ölçülmüş kalem şartı var.
- Endeks sayfalarına "Hazır senaryolar" iç link bölümü. sitemap **102 URL**.

## SOHBET ASİSTANI — `scraper/asistan.py` (2026-07-26)
Yavuz "canlı chat koyabilir miyiz, referral link atsak" diye sordu. İlk
turda "halüsinasyon riski" deyip chat'i tamamen eledim; **"çok güvenli
liman" eleştirisi haklıydı.** Doğru iş riski elemek değil, riski
imkânsız kılan yapıyı kurmak.

**NASIL — en kritik tasarım kararı:** asistan cevap ÜRETMİYOR, cevabı
VERİDEN SEÇİYOR. Dil modeli yok, dışarı istek yok, `eval` yok (testle
kilitli). Rakamlar doğrudan `/veri/*.json`'dan; cümleler sabit şablon,
değişken yalnızca rakam/kalem adı/tarih. Yani halüsinasyon "dikkatli
prompt" meselesi değil — **model yok ki uydursun.**

Beş niyet, kural tabanlı: kalem fiyatı · ölçekli hesap · grup bütçesi ·
kapsam dışı konular · yöntem soruları. Eşleşme yoksa uydurmuyor:
*"Bunu ölçmüyorum — yalnızca kendi ölçtüğüm kalemler hakkında
konuşabiliyorum, tahmin yürütmüyorum."*
- Her kalem cevabında **kaynak + ürün sayısı + tarih** var.
- Segment tutarsız kalemde (blender) asistan da segment SÖYLEMİYOR.
- **CANLI TESTTE BUG YAKALANDI:** niyet tanıma sıralı çalışıyordu,
  "okul çantası kaç para" → okul BÜTÇESİNİ döndürüyordu. Artık üç niyet
  puanlanıp yarışıyor, en spesifik eşleşme kazanıyor.

**AFFILIATE ALTYAPISI:** `KAYNAK_SITELERI`'ne `takip` alanı eklendi.
Ortaklık yapılınca yalnızca oraya parametre yazılır; link otomatik
`rel="sponsored"` alır ve sayfada **görünür açıklama** çıkar ("ölçtüğümüz
fiyatlar ve kaynak sıralaması bundan etkilenmez"). Açıklama hem yasal
yükümlülük hem de asıl sermayeyi — güveni — koruyor.
**"Sana şunu al" formatı bilinçli olarak YAPILMADI:** o tavsiye satmaktır
ve bağımsızlık beyanıyla çelişir. Doğru format zaten var: "bu fiyatı şu
sitelerde bulabilirsiniz."

## SİTE İÇİ ARAMA (2026-07-26)
Ana sayfada 95 ölçülmüş kalem içinde arama. Türkçe karakter duyarsız.
Kalem sayfası olmayan kalem endekse yönlendiriliyor (kırık link yok).
Fiyat endeks sayfasındakiyle aynı — ikisi de testli.

## BEBEK VERTİKALİ — 5. vertikal (2026-07-27)
**Neden bu:** Yavuz "yeni bir ölçüm eklesek bu ne olmalı?" diye sordu.
Seçim kriterleri: (1) tamamen **ürün bazlı** — hizmet kalemlerinde
aylarca tahminle uğraştık, burada her kalem somut ürün; (2) **kaynak avı
gerekmedi** — Amazon'un arama sayfası robots'ta serbest, Trendyol
kategorileri aramayla doğrulandı, okul turundaki en pahalı iş (kategori
URL'i bulma) hiç yaşanmadı; (3) **yaşam döngüsü zinciri** — düğün → ev
kurma → bebek aynı kullanıcının sıradaki adımı, iç link ve kullanıcı
tutma değeri var; (4) **sürekli talep** — okul mevsimsel, düğün yazın
yoğun, bebek yıl boyu sabit.

**11 kalem, 5 grup.** Orta segment tek seferlik hazırlık **34.829 TL**
(ekonomik 16.507 / üst 63.039). **Baştan çok kaynaklı kuruldu:** 4 kalem
(bebek arabası, beşik, oto koltuğu, mama sandalyesi) hem Trendyol hem
Amazon'dan ölçülüyor. 14 sayfa, sitemap 105 → 119 URL.

**`bebek-bezi` `varsayilan_dahil: False`** — bez SARF malzemesi, aylık
tekrarlıyor; diğerleri tek seferlik kurulum. İkisini tek toplama katmak
"bebek maliyeti 45 bin" gibi ne olduğu belirsiz bir rakam üretirdi.
Toplam = tek seferlik hazırlık, bez ayrıca gösteriliyor.

**STERİLİZATÖR KAPSAM DIŞI BIRAKILDI.** 7 ürünün 3'ü sterilizatör değil
(temizleme sıvısı, kurutma ünitesi, biberon hediye seti); ad filtresinden
sonra ~3 ürün kalıyor, güvenilir medyan için çok az. Kaynak pasif, kalem
listesinden çıkarıldı, **metodolojide neden ölçemediğimiz yazıyor** —
gizlemek yerine söylüyoruz.

## AD FİLTRESİ KATMANI — sessiz bir segment bozulması (2026-07-27)
Bebek vertikalini kurarken bulundu, **tüm vertikalleri ilgilendiriyor.**
Pazaryeri kategorileri ve arama sayfaları, ölçülen ürünün
**AKSESUARLARINI** da listeliyor ve bunlar hep **ALT segmentte**
toplanıyor — yani ekonomik segmenti sistematik olarak aşağı çekiyorlar.
Ölçüldü: "beşik" aramasında 403 TL cibinlik, 409 TL alez, 737 TL
salıncak; "mama sandalyesi"nde 585 TL minder; "park yatak"ta park
yatağın kendisi değil **şiltesi**.
- **`min_fiyat`'ı yükseltmek bunu çözmez, ÖRTBAS EDER:** gerçek ekonomik
  segmenti de keser ve "ekonomik beşik 1.500 TL" derken alt ucu bilerek
  atmış oluruz. Doğru çözüm ürünü ADIYLA elemek.
- **`ad_gerekli` / `ad_dislama`** alanları (`tablo` katmanındaki
  `satir_filtresi` ile aynı ilke, ürün kartının adına uygulanıyor).
- **`SAYFA_MOBILYASI`** — her kaynakta geçerli, kaynakta filtre tanımlı
  olmasa bile eler. Trendyol'da *"Bebek Beşik & Karyola Modelleri ve
  Fiyatları 2026"* **başlığı ürün kartı olarak yakalanıp** yanındaki
  fiyatla eşleşiyordu: tamamen uydurma bir satır.
- **`_ad_norm`** — Python'da `"BEŞİK".lower()` → `"beşi̇k"` (i + U+0307
  birleşik nokta), düz `re.I` "beşik" desenini **TUTMUYOR**; noktasız ı
  ile noktalı i de ayrı karakter. i ailesi tek forma indiriliyor (s/ş,
  c/ç katlanmıyor — "kaş"ı "kas"a eşitlerdi).
- Filtre örneklemin yarısından fazlasını yerse **görünür uyarı** (sessizce
  küçük örneklemle devam etmek "0 ürün ama sağlıklı" tuzağının aynı türü).

**İLK DESEN YANLIŞTI, ölçüp düzeltildi — asıl ders bu.** Düz `cibinlik`
deseni gerçek ürünleri de eledi (*"Cibinlikli Anne Yanı Beşik"* — beşik,
cibinliği dahil) ve beşik medyanını **1.755'ten 2.978'e ÇIKARDI**: filtre
veriyi düzeltmek yerine bozdu. Aynı şey mama sandalyesinde *"mindersiz"*
ve *"4in1 ... Mama Oturağı"* ile yaşandı. **İyelik eki ile sıfat
ayrılmak zorunda:** `cibinlik(?!li)` — *cibinlikLİ beşik* ürün, *beşik
cibinliĞİ* aksesuar. **Filtre yazıp neyin elendiğine bakmamak, filtre
yazmamaktan kötü.**

**SABİT VERTİKAL LİSTELERİ KALDIRILDI.** `gecmis.py` ve `rehber.py` elle
yazılmış vertikal listesi tutuyordu — okul eklenince unutulmuş, zaman
serisi o vertikal için **hiç üretilmemişti** ve kimse fark etmemişti;
bebek'te aynısı olacaktı. İkisi de artık `sayfa_uret.VERTIKALLER` okuyor.
`motor.py`'ye **`--vertikal`** filtresi eklendi (tam tur 196 kaynakla
~50 dk; tek vertikal ~4 dk).

## SOSYAL MEDYA OTOMASYONU — `scraper/sosyal.py` (2026-07-27)
Yavuz'un sorusu: *"Sosyal medyada otomasyon kurabilir miyiz?"*
Paylaşılacak şey görüş değil **ölçüm sonucu** — sitenin en doğal tanıtım
biçimi bu.

**KIRMIZI ÇİZGİ, `asistan.py` ile aynı ilke:** metin ÜRETİLMİYOR,
veriden KURULUYOR. Dil modeli yok, dışarı istek yok. Cümleler sabit
şablon; değişen yalnızca rakam, kalem adı, tarih ve örneklem sayısı.
*"Fiyatlar uçtu"* gibi bir cümleyi bu kod **yazamaz**. **Sosyal medya bu
ilkeyi kırmak için en tehlikeli yer** — dikkat çekmek için abartma
basıncının en yüksek olduğu mecra, ve o iddia dışında satacak bir şeyimiz
yok.

**SUSMAK VARSAYILAN DAVRANIŞ.** Üç kapı, üçü de geçilmezse çıktı boş:
1. **Yeterli aralık** — `gecmis.ASGARI_GUN_ARALIGI` tek kaynaktan
   okunuyor (iki yerde ayrı eşik tutmak, birini güncelleyip ötekini
   unutmak olur). 24→25 Temmuz testinde "nikah şekeri %40 düştü" çıkmıştı;
   fiyat düşüşü değil, listelenen ürünlerin değişmesi.
2. **Örneklem kararlılığı** — ürün sayısı %35'ten fazla oynadıysa
   medyandaki değişim FİYATTAN değil ölçülen kümeden geliyor olabilir;
   hangisi olduğunu ayırt edemediğimiz için susuyoruz.
3. **Anlamlı büyüklük** — %3 altı paylaşılmaz.
Ayrıca ölçüm başına en fazla 3 gönderi (40 kalem değiştiyse 40 tweet
spam'dir).

**Değişim yoksa:** ayın 5'inde tek bir ölçüm özeti, vertikal **aya göre
dönüşümlü** (durum tutmadan deterministik — aynı ay iki kez çalıştırmak
yeni gönderi üretmez). Özet, sitedeki toplamla **aynı kuralı** uyguluyor:
`varsayilan_dahil: False` (bebek bezi) ve `bilgi_amacli` kalemler
toplama girmiyor — aksi halde sitede 34.829 yazarken sosyalde başka bir
rakam paylaşılmış olurdu (bir test bunu kilitliyor).

**GÖNDERİM — anahtar Yavuz'un kararı.** Varsayılan deneme modu.
`--gonder` verili ama secret yoksa hiçbir yere gönderilmez, yalnızca
`veri/sosyal/onizleme.md` yazılır ve commit'e girer. Yani otomasyon
anahtar eklenene kadar **"provayı" görünür şekilde yapıyor**; anahtarı
eklemek yayına alma kararının kendisi (EVDS'deki desenin aynısı).
- **X:** API v2 + OAuth 1.0a, ücretsiz katman ayda ~500 gönderi
  (bizim ihtiyacımız ayda 2-6). Secret'lar: `X_API_KEY`, `X_API_SECRET`,
  `X_ACCESS_TOKEN`, `X_ACCESS_SECRET` (developer.x.com → app → keys).
- **Bluesky:** en kolayı — onay/inceleme yok, app password yeter.
  Secret'lar: `BLUESKY_HANDLE`, `BLUESKY_SIFRE`.
- **Threads ve LinkedIn KURULMADI:** ikisi de Meta/LinkedIn uygulama
  incelemesi gerektiriyor (haftalar sürebilir, reddedilebilir).

### İLK TRAFİK ÖLÇÜMÜ (2026-07-27) — kanal seçimini veri belirledi
Yavuz'un analitiği, son 24 saat referans: **m.facebook.com 20**,
**www.yandex.ru 1**. İki çıkarım:
- **Facebook birinci kaynak ve trafiğin tamamı mobil.** Yavuz'un
  "Facebook ve Instagram önemli olabilir" sezgisi artık tahmin değil,
  ölçüm. Bu kanalda **paylaşım kartı doğrudan tıklama oranının kendisi.**
- **Yandex'ten gelen tek ziyaret bir ARAMA SONUCU tıklaması** — yani
  Yandex bizi indekslemiş. IndexNow yatırımının ilk somut karşılığı;
  Google henüz görmezken oradan organik ziyaret geliyor.
- Not: 20 ziyaret Yavuz'un kendi paylaşımından geliyor, organik keşif
  değil. Söylediği şey "Facebook kitlesi ulaşılabilir", "Facebook bizi
  kendiliğinden buluyor" DEĞİL.

**Bu ölçüm üzerine yapılan iş:** `og:image:width/height` hiçbir sayfada
yoktu (bkz. Paylaşım kartı maddesi). Facebook ilk taramada boyutu
bilmediği için küçük/boş kart gösterebiliyordu — ilk paylaşım en çok
tıklanan paylaşım olduğu için pahalı bir kayıptı. Ayrıca elle yazılan
12 sayfada (hesaplayıcılar dahil) `og:image` **hiç yoktu**.

**AÇIK KALAN, EN YÜKSEK KALDIRAÇLI İŞ:** her sayfa aynı jenerik görseli
paylaşıyor. `/bebek/besik-fiyatlari/` paylaşıldığında kartta
*"2026'da bir şey kaça mal olur?"* yazıyor, *"Beşik 4.315 TL"* yazmıyor.
Facebook birinci kanal olduğuna göre **sayfa başına ölçüm kartı görseli**
en çok getirisi olan bir sonraki iş — ve zaten Instagram için de zorunlu
(aşağı bkz.). Tek iş, iki kanal.

### SONRAKİ AŞAMA — X, Facebook, Instagram (2026-07-27 Yavuz'un yönü)
Yavuz: *"bir sonraki aşamaya bırakalım. X, Facebook ve Instagram önemli
olabilir."* Kod yazmadan önce bilinmesi gereken **tasarım kısıtı:**
- **Instagram metin gönderisi KABUL ETMİYOR.** Graph API'de içerik
  yayınlamak için görsel/video zorunlu; ayrıca açıklamadaki linkler
  tıklanabilir değil. **Şu anki "metin + link" formatı Instagram'da hiç
  çalışmaz.** Facebook Sayfası da görselle belirgin şekilde daha iyi.
- **Sonuç: Meta tarafına geçmek ÖLÇÜM KARTI GÖRSELİ üretmeyi zorunlu
  kılıyor** — rakam + kalem adı + örneklem + tarih taşıyan PNG.
  Altyapı hazır: `og_gorsel.py` PIL ile 1200×630 üretiyor, 1080×1080
  kart onun üzerine kurulur. Bu görsel X gönderisini de güçlendirir
  (veri kartları düz metinden çok daha fazla etkileşim alıyor).
- **Hesap/izin bürokrasisi (build anında teyit edilmeli):** Instagram
  için **işletme/içerik üretici hesabı + bağlı Facebook Sayfası** şart,
  kişisel hesaba API ile atılamıyor. Facebook Sayfası'na göndermek
  `pages_manage_posts` izni istiyor, bu izin uygulama incelemesinden
  geçiyor. X ve Bluesky'de bu bürokrasi YOK.
- **Doğru sıra:** (1) X'i aç — kod hazır, yalnızca 4 secret; (2) ölçüm
  kartı görseli üreticisi; (3) Facebook + Instagram.
- 17 test: üç kapının gerçekten kapattığı, **ham kalem id'sinin gönderiye
  sızmadığı** (senaryo sayfalarında yaşanmıştı), rakamsız özet
  üretilmediği, karakter sınırı (X 280'e göre), anahtar yoksa atlanma,
  ve kaynak dosyasında hiçbir LLM çağrısı olmadığı.

## RAKİP ANALİZİ (2026-07-27) — dört site ölçüldü
Yavuz dört benzer site paylaşıp *"bizde eksik onlarda olan, onlarda
eksik bizde olanları çıkar; nasıl önlerine geçeriz"* dedi. Hepsi
gerçekten çekilip incelendi (spekülasyon değil, ölçüm):

| | nekadar | yenibirhesap | hesapsonuc | maliyeti.com.tr |
|---|---|---|---|---|
| Sayfa | 220 | 1.885 | 258 | **2.400** |
| Son güncelleme | tek build, 24 Haz | bugün | 22 Tem | **Ocak 2026** |
| İçerik | formül hesap | formül + canlı kur | formül hesap | maliyet yazısı |
| Kaynak/örneklem/tarih | — | — | mevzuat atfı | **hiç** |
| llms.txt / ai.txt | var / — | — / — | var / **var** | — / — |

**Dördünde de `/metodoloji` ve `/veri` 404.** Hiçbirinde ölçüm tarihi,
örneklem büyüklüğü, zaman serisi ya da indirilebilir veri yok.

**maliyeti.com.tr — en yakın isim benzerimiz, en zayıf site.** 2.400
sayfanın tamamı 9–21 Ocak arasında (12 günde) yayınlanmış, o günden beri
hiç dokunulmamış. Yazar "admin". "Futbol kulübü kurma maliyeti" sayfasında
6.500.000 TL gibi çok spesifik rakamlar var; sayfada geçen "kaynak"
kelimesi sayısı **0**, "TÜİK" **0**. Üretilmiş rakamlar, gerçek gibi
sunulmuş, sonra terk edilmiş. Google'ın helpful-content sistemi tam bu
profili eliyor.

**hesapsonuc.com'u küçümsemek hata olur** — teknik olarak bizden ileride
olduğu yer var: 15 schema tipi (HowTo/HowToStep dahil), sayfa içinde
"Metodoloji" başlığı, mevzuat atıfları, hem `llms.txt` hem `ai.txt`.
Bilinçli yapılmış iş.

**Sömürülecek zaafiyetler:**
- **yenibirhesap'ın canlı fiyatları JS ile yükleniyor** — ham HTML'de tek
  TL rakamı yok, 4 `fetch` izi var. AI motorları JS çalıştırmıyor, yani
  en güçlü kozları GPTBot/ClaudeBot için **görünmez.** Biz bu sorunu
  build-time üretimle en başta çözdük.
- nekadar'ın tüm sitesi tek lastmod taşıyor → tazelik sinyali yok.

**KARAR — kapsamı genişletmiyoruz.** hesapsonuc'ta "juno lilith
hesaplama" var; kendini seyrelttiği yer orası. Biz maliyet + ona komşu
resmî hesaplarda kalıyoruz.

**X'E ÇIKMA ZAMANLAMASI (Yavuz'a verilen tavsiye):** şu an değil, **5–20
Ağustos.** Sebep teknik yetersizlik değil — dördünden de sağlamız. Google
henüz indekslemedi; şimdi atmak anlık sıçrama yapar, arkasında bir şey
kalmaz. Ağustos'ta iki şey birden elde olacak: ilk gerçek zaman serisi
sonucu ve indeksleme. O zaman paylaşılan şey "bir site yaptım" değil
**"şunu ölçtüm"** olur — kanıt, vaat değil.

## FORMÜL HESAPLAYICILARI — `/hesap/` (2026-07-27)
Rakip analizinin doğrudan sonucu: dördünün de trafiği formül
hesaplayıcılarından geliyor ve bizde bu kategoride **sıfır sayfa** vardı.
"kdv hesaplama" araması "düğün maliyeti"nden kat kat büyük.

**5 hesaplayıcı:** KDV · brütten nete maaş · kıdem+ihbar tazminatı ·
kredi taksiti · yüzde. sitemap 119 → **125**.

**KIRMIZI ÇİZGİ İHLAL EDİLMİYOR — ayrım şu:** bu sayılar fiyat değil
**mevzuat**. Bir ürünün kaça satıldığını *ölçmek* gerekir; bir verginin ne
olduğunu ise mevzuat *söyler*. Kıdem bir kanun formülü, gelir vergisi bir
tebliğ tarifesi, taksit bir annüite denklemi — cevap türetilebilir ve
doğrulanabilir.

**PARAMETRELER KENDİ BİLGİMDEN YAZILMADI, resmî kaynaktan doğrulandı**
(`assets/js/resmi-parametreler.js`):
- 2026 gelir vergisi tarifesi — **332 Seri No.lu GVGT, 31.12.2025 R.G.
  33124 (5. Mükerrer)**. Ücret ve ücret dışı tarife ayrı; fark 3. dilimde
  başlıyor (1.500.000 / 1.000.000).
- Asgari ücret 33.030 brüt / 28.075,50 net · SGK tavanı 297.270 (2026'da
  günlük asgari ücretin 7,5 katından **9 katına** çıktı) · işçi %14 + %1 ·
  damga binde 7,59 · **kıdem tavanı 73.729,84** (1 Tem–31 Ara 2026, ÇSGB).

**İKİ BAĞIMSIZ DOĞRULAMA:**
1. Tarifenin kümülatif tutarları aritmetikle birebir tutuyor
   (190.000×%15=28.500; +210.000×%20=70.500; …). Bir test bunu kontrol
   ediyor — yanlış kopyalanmış bir sayı orada patlar.
2. Hesabımız **resmî açıklanan net asgari ücreti birebir üretiyor**
   (33.030 → 28.075,50), tarayıcıda da doğrulandı. Tutmasaydı ya bir oran
   ya istisna mantığı yanlıştı ve hata tüm maaş hesaplarına yayılırdı.

**RAKİPLERDEN KASITLI ÜÇ AYRIM:**
1. Her parametrenin kaynağı sayfada **görünür** (tebliğ adı + R.G. tarih
   ve sayı). hesapsonuc metin içinde atıf yapıyor ama hangi sayının
   nereden geldiği belli değil; diğer ikisi hiç kaynak vermiyor.
2. Her parametre **geçerlilik dönemi** taşıyor. Süresi geçmişse sayfa
   görünür uyarı basar, sessizce eski yılın vergisini **vermez**. Bir test
   de dönem geçmişse başarısız olur — yani site bize haber veriyor.
   1 Ocak 2027'de bu dosya güncellenmezse testler patlar.
3. Maaş hesabı **AY soruyor**: gelir vergisi artan oranlı, matrah yıl
   içinde birikiyor. Ayı sormayan hesap yılın ilk ayı dışında yanlış.

**MTV HESAPLAYICISI BİLİNÇLİ OLARAK YOK.** Doğrulanmış kademelerimiz
1800 cc'ye kadar; 2.0 motorlu araca yanlış rakam vermek yerine kalemi hiç
açmıyoruz. **Eksik vergi tarifesi yayınlamak, hiç yayınlamamaktan kötü.**
Bir test bu kararı kilitliyor — MTV eklenecekse kademeler önce tam
doğrulanmalı.

**Tarayıcı testinde üç kusur bulunup düzeltildi:** "-0 TL" (sıfır vergi
satırında), "4.624,2 TL" (kuruş eksik), ve netten brüte hesabının hedefi
kuruşun altında kaçırması (33.029,99 → 33.030). Test yöntemi: gerçek
`requestSubmit()` — `dispatchEvent(submit)` HTML5 validation'ı atladığı
için yanıltıcı olur (araç hesaplayıcısındaki `step` bug'ı tam bu yüzden
gözden kaçmıştı).

### HESAPLAYICILAR 5 → 12 (2026-07-27, ikinci tur)
Yavuz: *"korkak gitmeyelim ve tüm hesaplayıcıları görünür hale
getirelim."* Haklıydı — kapsamı fazla dar çizmiştim.

**AYRIM YENİDEN TANIMLANDI: tehlikeli olan formül değil PARAMETRE.**
Her hesaplayıcı artık dört tipten birine giriyor ve tipi kaynak biçimini
belirliyor (bir test bunu zorunlu kılıyor — sınıflandırılmamış
hesaplayıcı eklenemiyor):
1. **Mevzuat** — kaynak tebliğ/kanun adı + R.G. tarih ve sayı
2. **Saf matematik** — formülün kendisi kaynaktır; sahte resmî atıf YASAK
3. **Kullanıcı parametresi** — parametrenin resmî kaynağı yok;
   kullanıcıdan alınır ve **belirsizlik görünür kılınır**
4. **Ölçülen veri** — parametresi bizim çektiğimiz resmî seri

**Beşinci tip (uydurma) yok.** Kural: her parametre ya kaynaklı ya
kullanıcıdan sorulan; arada boşluk bırakılmıyor. Bu kural genişlemeyi
engellemiyor, **güvenli kılıyor.**

**Yeni 7:** tapu harcı · işsizlik maaşı · kira gelir vergisi · yıllık
izin · fazla mesai · **alım gücü** · **YouTube geliri**.

- **Alım gücü en güçlüsü:** parametresi sabit değil, ayda iki kez
  çektiğimiz **resmî TÜFE serisi** (TCMB EVDS). Rakiplerin hiçbirinde
  yok çünkü hiçbiri resmî endeksi çekmiyor. Seri sayfaya **gömülü**
  (build-time), client-side fetch değil — yenibirhesap'ı AI motorları
  için görünmez yapan şey tam olarak fetch kullanması. Veri yoksa sayfa
  hiç üretilmiyor.
- **YouTube geliri — kuralı kırmadan yapılabildi.** Gelirin tamamı
  RPM'e bağlı ve RPM resmî olarak yayınlanmıyor. Rakipler oraya uydurma
  bir sabit koyup tek rakam basıyor. Çözüm kaçmak değil, **belirsizliği
  görünür kılmak**: RPM kullanıcıdan alınıyor, beş RPM değeri için
  duyarlılık tablosu dönüyor. "Cevap tek bir sayı değil" zaten bu sitenin
  üslubu — segment yapısının aynısı. Bir test hem parametrenin kaynaksız
  olduğunun söylendiğini hem aralık gösterildiğini doğruluyor.

**Doğrulamalar:** tapu 10M → alıcı 200.000 / satıcı 200.000 (kaynaktaki
örnekle birebir) · işsizlik tavanı 33.030×%80=26.424 brüt, damga sonrası
**26.223,44 net** = açıklanan 2026 tavanıyla birebir.

**TARAYICI TESTİ BİR BUG DAHA YAKALADI — araç `step` bug'ının aynı
sınıfı.** YouTube sayfası hiç sonuç üretmiyordu: RPM alanı "boş
bırakabilirsiniz" diyor ama form her sayı alanına `required` koyuyordu,
HTML5 validation submit'i **sessizce** blokluyordu. **Form nitelikleri
görünüm değil GEÇERLİLİK KISITI** — bu ders ikinci kez alındı.

**İkinci sessiz hata:** eklenen bir test dosyanın sonunda `if __name__`
bloğunun **içine** düşmüştü — hiç çalışmıyordu ama suite yeşil
görünüyordu. **Ders: yeni test eklendiğinde test SAYISININ arttığını
doğrula**, sadece "OK" görmek yetmez.

**KAPSAM KARARI:** burç/astroloji/matematik yok. hesapsonuc'un "juno
lilith hesaplama" ile seyreldiği yer orası; marka bir **maliyet** sitesi
olarak kalıyor.

sitemap 125 → **132**. Node 70/70, Python 11 suite.

**`ai.txt` EKLENDİ** (hesapsonuc'ta vardı, bizde yoktu). `llms.txt`'ten
farkı: llms.txt bir **içerik haritası**, ai.txt **yayıncı künyesi ve
kullanım koşulu** (veri nereden geliyor, nasıl atıf verilir, neyi
yapmayın). Elle yazılmıyor, veriden üretiliyor — llms.txt elle yazıldığı
için bir kez bayatlamıştı.

Testler: 18 yeni Python + 23 yeni Node. Toplam 11 Python suite, Node 54.

## GOOGLE AI ÖNERİLERİ — değerlendirme (2026-07-27)
Yavuz Google'ın yapay zekasından aldığı beş öneriyi paylaştı. Ölçülüp
tek tek değerlendirildi; **üçü zaten yapılmıştı.**

- **Dinamik sitemap** ✓ zaten var: 132 URL, build-time üretiliyor,
  workflow her ölçümde tazeliyor.
- **Schema markup** ✓ zaten var: sitede **26 farklı tip** kullanılıyor
  (WebApplication, HowTo, Dataset, DataCatalog, AggregateOffer,
  FAQPage, BreadcrumbList…).
- **Affiliate linkleri** ✓ altyapı hazır: `KAYNAK_SITELERI.takip`
  doldurulduğu an link `rel="sponsored"` alıp görünür açıklama
  gösteriyor. Kod işi yok, **programlara kabul alınması gerekiyor.**
- **DÜZELTME:** öneri "indeksli değilseniz sitemap ve schema
  yaptırın" diyordu. İndekslenmememizin sebebi o değil — ikisi de tam;
  site 3 günlük ve dış bağlantısı yok. O ikisini yeniden yapmak boşa
  emek olurdu.

**E-POSTA DUVARI ÖNERİSİ UYGULANMADI — sebebi kayda geçsin.** Öneri
"PDF indirmek için e-posta iste, sonra finans/sigorta reklamı at"
diyordu. Üç sorun: (1) ham veriyi CSV olarak CC BY 4.0 ile bedava
veriyoruz ve `/veri/` sayfası "alın kullanın" diyor — aynı rakamların
PDF'ini e-posta karşılığı vermek **tutarsız** olurdu ve ilk fark eden
bunu yazar; (2) Türkiye'de ticari e-posta **İYS kaydı ve açık rıza**
gerektiriyor; (3) statik sitede backend yok, e-posta toplamak üçüncü
taraf servis + KVKK sorumluluğu demek. **PDF/paylaşılabilir rapor
yapılabilir ama duvarsız.**

## BÜTÇE DENGELEYİCİ (2026-07-27) — önerinin en iyisi
*"Bütçem 411.670 değil 300.000"* diyen kullanıcıya hangi kalemde ne
yapması gerektiğini söylüyor. `hesapla.js` → `butceyiDengele()`.

**NEDEN BU BİR TAVSİYE MOTORU DEĞİL, ARİTMETİK:** öneriler
uydurulmuyor, **ölçülmüş segment fiyatlarından çıkarılıyor.** "Salon:
orta → ekonomik, −52.500 TL" diyebiliyoruz çünkü iki segmentin de
medyanı elimizde. **"Pazarlık yap, %10 indirim al" gibi ölçmediğimiz
bir tasarruf önerilmiyor** — o tavsiye olurdu, veri değil. Sayfada da
bu cümle yazılı.

**HEDEFE ULAŞILAMIYORSA SÖYLENİYOR.** Gerçek veriyle:
- hedef 300.000 → 3 hamle, yeni toplam 278.778, açık kapanıyor
- hedef 200.000 → 8 hamle, 266.077'de duruyor ve dürüstçe diyor ki
  *"bütçeye yine de 66.077 TL kalıyor; ölçtüğümüz kalemlerin hepsini
  ekonomiğe indirseniz bile inilebilecek en düşük tutar 266.077 TL"*

**Korunan sınırlar (testli):** `segment_tutarsiz` kalemden tasarruf
önerilmez (blender örneği — tutarsız veriden "tasarruf" çıkarmak
yanıltır) · tahmini kalemden önerilmez · aynı kalem için tek hamle
(çift sayım yok) · geçersiz hedefte `null`.

**Test gerçek bug yakaladı:** bütçe yeterliyken `pay` hesabı **tersti**
(mevcut − hedef) ve bütçesi bol kullanıcıya negatif pay gösteriyordu.

**Yan düzeltme:** `dugun-kalemler.js`'te `module.exports` **yoktu**
(diğer üç kalem dosyasında vardı) — bu yüzden dengeleyici gerçek veriye
karşı node ile test edilemiyordu. Eklendi.

**Araç → kredi bağlantısı:** öneri "banka affiliate butonu koy"
diyordu; önce **kendi** kredi hesaplayıcımıza bağlamak daha doğru —
kullanıcı siteden çıkmıyor ve rakam bizim hesabımızdan geliyor.
Affiliate ayrı ve Yavuz'un kararı.

Dört vertikal hesaplayıcısında var (araç hariç — orada kalemler
birbirinin alternatifi, toplam hesabı zaten yok). Node 80/80.

## SEO BAŞLIK YAPISI VE KONU KÜMESİ (2026-07-27)
Yavuz, Claude ve ChatGPT'den aldığı önerileri paylaştı. Uygulananlar ve
**uygulanmayanların sebebi:**

**1. ANAHTAR KELİME ÖNCE — ama asıl sorun öneride yoktu.**
Öneri rehber başlıklarını hedef alıyordu. Ölçünce daha büyük bir sorun
çıktı: **hub sayfalarının başlıklarında hedef ifade hiç geçmiyordu.**
`/ev-kurma/` başlığı *"2026'da Ev Kurmak Kaça Mal Olur?"* idi — "ev
kurma maliyeti" ifadesi yok. Senaryo sayfalarında ("Beyaz Eşya Seti
Fiyatları 2026") doğru yapılmış, hub'larda yapılmamıştı.
- `/ev-kurma/` → **Ev Kurma Maliyeti 2026 — Kalem Kalem**
- `/dugun/` → **Düğün Maliyeti 2026 — Kalem Kalem**
- `/okul/`, `/bebek/` aynı desen · ana sayfa → **Maliyet Hesaplama ve
  2026 Fiyat Endeksleri**
- **H1'lerde soru formu KORUNDU**, sadece başa hedef ifade alındı:
  *"2026 Ev Kurma Maliyeti: Sıfırdan Kaça Mal Olur?"* — SEO title'ı,
  GEO soru formunu ister; ikisi birden alınabiliyor.

**ÖNERİDEKİ TUZAK — kendi sayfamızı kendimizle yarıştırma.** Öneri
rehberi de *"2026 Ev Kurma Maliyeti"* yapmayı söylüyordu; ama o ifadeyi
zaten `/ev-kurma/` hedefliyor. İkisine aynı ifadeyi vermek
**cannibalization** olurdu. Her rehbere hub'la çakışmayan ayrı uzun
kuyruk verildi:
| hub | rehber |
|---|---|
| ev kurma maliyeti | ev kurarken alınacaklar listesi |
| okul masrafı | okul alışverişi maliyeti |
| sıfır araba fiyatları | sıfır araba masrafları |

**Title uzunluğu:** Google ~60 karakterde kesiyor, `" | Maliyeti Ne?"`
eki 15 karakter yiyor. `_title()` uzun başlıklarda marka ekini
kısaltıyor (tamamen atmıyor — marka tanınırlığı da sinyal). **Sitede 62
karakterden uzun title kalmadı.**

**2. KONU KÜMESİ.** Ölçüldü: en yüksek niyetli sorguları hedefleyen
senaryo sayfaları ("beyaz eşya fiyatları", "mobilya fiyatları") **her
biri yalnızca 1 iç link** veriyordu — küme değil, yalnız ada.
`senaryo._konu_kumesi_html()` eklendi: aynı vertikaldeki diğer
senaryolar + kalem sayfaları. **1 → 13 iç link.** Yalnızca diskte var
olan sayfalara link veriliyor, 12 ile sınırlı (link-farm görünümü
olmasın).

**3. ARAÇ ÇERÇEVESİ — önerinin ifadesi KULLANILMADI, sebebi kayda geçsin.**
Öneri: *"1 bağımsız kaynak" yerine "resmî üretici liste fiyatı" ya da
"doğrudan markaların yayınladığı liste fiyatlarından" yaz.*
**Kullanılamaz:** kaynağımız donanimhaber'in sıfır araç fiyat dosyası —
üretici DEĞİL, liste fiyatlarını derleyen bir kaynak. Öyle yazmak
**kaynağı olduğundan başka göstermek** olurdu.

Ama önerinin altındaki tespit doğru: perakende ürünlerde çoklu kaynak
piyasayı temsil eder çünkü her satıcı kendi fiyatını koyar; 0 km araçta
fiyatı **üretici belirler ve bayiden bayiye değişmez** — orada ikinci
kaynak aynı sayıyı verir, hiçbir şey kanıtlamaz. *"1 bağımsız kaynak"
zayıf değil, YANLIŞ ÇERÇEVE.*
**Doğru çözüm: kaynağı değil FİYATIN NİTELİĞİNİ anlatmak** →
*"üreticilerin belirlediği liste fiyatlarından derlenen"*. Bu cümle
doğru ve tek kaynağı bir eksiklik olmaktan çıkarıyor
(`_dayanak_ifadesi()`, `liste_fiyati` bayrağına bağlı).

**4. ÜÇ YENİ RAKİP — alınacak teknik bir şey yok.**
- **maliyetbul.com**: inşaat/geometri hesaplayıcıları. Schema YOK,
  sitemap YOK, H1 YOK, 0 iç link, 181 kelime.
- **hesaplamaci.com**: geniş hesaplayıcı sitesi, yalnızca Organization
  schema. **Alınmaya değer fikir:** "arabam ne kadar yakar" / akaryakıt
  hesapları — yakıt fiyatı ölçülebilir, tam bizim işimiz. (Sıraya alındı.)
- **fical.net**: finansal hesaplayıcılar, çok dilli; yalnızca
  BreadcrumbList. **Çok dillilik bize uymuyor** — TR'ye özgü olmak
  savunma hendeğimiz, dağıtmak onu zayıflatır.
Üçü de metodoloji, ölçüm tarihi, örneklem ve indirilebilir veri
tarafında bizden geride.

## ANALYTICS (2026-07-27)
Yavuz GA4 etiketini verdi (`G-JP07XQLV0L`). **133 sayfanın tamamına**
eklendi, tek yerde tanımlı (`sayfa_uret.ANALITIK`) — OG etiketlerinde
öğrenilen ders: sekiz şablonda ayrı ayrı duran bir şeyi güncellemek
unutuluyor. Üretilen sayfalar sabiti kullanıyor; elle yazılan 13 sayfa
ayrıca yamandı.

**KVKK notu:** GA4 çerez yazıyor ve bunun sitede **yazılı** olması
gerekiyor. `/hakkimizda/` sayfasına "Çerezler ve ölçüm" bölümü eklendi
(ne topladığımız, çerezin engellenebileceği, üyelik/e-posta/form
olmadığı). **Çerez onay banner'ı EKLENMEDİ** — o ayrı bir ürün kararı
(tıklama oranını düşürür), Yavuz'un tercihine bağlı.

## HESAPLAYICILAR 12 → 20 (2026-07-27, üçüncü tur)
Yavuz: *"bu hesaplama toolları çok değerli, o noktada cimrilik yapma."*

**FICAL İNCELEMESİ — "çok tıklanıyor" ama sebebi derinlik değil.**
Sitemap'te 146 URL var; gerçekte **yalnızca 4 hesaplayıcı** (bileşik
faiz, gelişmiş bileşik faiz, hisse maliyet, Kelly kriteri) + 3
istatistik sayfası, **13 dile kopyalanmış.** Çok dillilik bize uymuyor —
TR'ye özgü olmak savunma hendeğimiz, dağıtmak onu zayıflatır. Ama o dört
hesap alınmaya değerdi.

**Yeni 8:** bileşik faiz/birikim · birikim hedefi · hisse maliyet
ortalaması · kâr-zarar (komisyon dahil başa baş fiyat) · temettü verimi ·
kredi kartı borcu · **serbest meslek (freelancer) vergisi** · web sitesi
geliri.

**İKİ TASARIM KARARI — rakiplerin atladığı yerler:**
1. **Kredi kartı:** aylık ödeme o ayın faizinden küçükse **borç hiç
   bitmez.** Rakiplerin çoğu burada ya sonsuz döngüye giriyor ya saçma
   bir sayı üretiyor. Biz uydurma bir "N ay" vermek yerine açıkça
   söylüyoruz ve borcun azalmaya başlaması için gereken asgari ödemeyi
   veriyoruz.
2. **Freelancer:** yıl içinde kesilen stopaj beyanda **mahsup edilir**;
   çoğu hesaplayıcı bunu atlıyor. Genç girişimci istisnasından
   yararlanan bir freelancer'da ödenecek vergi değil **iade** çıkabiliyor.
   Canlı örnek: 600k hasılat, 100k gider, genç girişimci → 120k stopaj
   kesilmiş, hesaplanan vergi 15k, **105.000 TL iade.**

**Doğrulanan parametreler:** genç girişimci istisnası 2026 = **400.000
TL** (GVK mük. md.20, 332 Seri No.lu GVGT, ilk 3 vergilendirme dönemi,
29 yaş sınırı) · serbest meslek stopajı %20 (GVK md.94) · KDV %20.

**TEST YİNE BUG YAKALADI — `step` bug'ının ÜÇÜNCÜ tekrarı.** Bileşik
faiz ve birikim sayfalarında getiri oranı alanında `step="0.1"` vardı;
kullanıcı %40,25 yazamayacaktı. Test gevşetilmedi, alanlar düzeltildi.
**Bu hata artık kalıcı bir desen: form nitelikleri görünüm değil
geçerlilik kısıtı, ve her yeni hesaplayıcıda tekrar kontrol edilmeli.**

sitemap 132 → **140**. 20 hesaplayıcının tamamı gerçek tarayıcıda
doğrulandı: hepsi sonuç üretiyor, 0 konsol hatası, 20/20 analitik kodu
içeriyor.

## WORKFLOW DENETİMİ (2026-07-27) — `sss/` commit edilmiyordu
5 Ağustos'ta **ilk zaman serisi ölçümü** var. O gün workflow eksik
çalışırsa seride kalıcı delik oluşur. Bugün 8 yeni sayfa ve 3 yeni
script eklendiği için motor hariç tüm zincir baştan sona kuru
çalıştırıldı — zincir sorunsuz, ama bir eksik çıktı:

**`sss/` sayfası workflow'un `git add` listesinde YOKTU.** Sayfa veriye
göre değişiyor (testle doğrulandı) ama commit edilmediği için 5
Ağustos'ta her şey güncellenirken o sayfa 26 Temmuz verisinde donup
kalacaktı. **Sessiz hata:** canlıda 200 döner, hata vermez, sadece
rakamları bayattır — ve workflow yılda 24 kez çalışıp arada kimse
bakmadığı için aylarca sürebilirdi.

**`scraper/test_workflow.py` (6 test)** — workflow artık testle kilitli:
- **Üretilen her kök yol commit listesinde mi?** Kaynak koddan
  `SITE_KOK / "..."` yazımlarını çıkarıp `git add` listesiyle
  karşılaştırıyor. Yeni bir çıktı eklenip listeye yazılmazsa test patlar.
  (Doğrulandı: `sss` listeden çıkarılınca gerçekten patlıyor.)
- Çağrılan her script diskte var mı?
- Vertikal döngüsü `VERTIKALLER` ile aynı mı? (okul eklenirken
  `gecmis.py`'de yaşanan unutma hatasının workflow karşılığı)
- Kodun import ettiği üçüncü taraf paketler `requirements.txt`'te mi?
- Cron ayın 5'i ve 20'si mi? · IndexNow yalnızca değişiklik varsa mı?

**DERS:** üretim boru hattına yeni bir çıktı eklemek iki yerde iş
demek — üreten kod ve **onu yayına taşıyan liste.** İkincisi unutulunca
hiçbir şey kırılmıyor, sadece sessizce eskiyor.

## SEO/GEO DENETİMİ (2026-07-27) — 5 gerçek sorun
Yavuz: *"bir körlük olmasın."* Üretilmiş **sitenin tamamına** karşı 17
ayrı kontrol çalıştırıldı. Beşi de aynı cinsten çıktı: **bir yerde
düzeltip her yerde düzeldiğini varsaymak.**

**1. EN AĞIRI — FAQ şeması var ama sorular sayfada görünmüyor (6 sayfa).**
Beş hub sayfası + ana sayfa JSON-LD'de **14 soruya kadar** taşıyor ama
sayfada hiç görünmüyordu. Google'ın kuralı net: *"FAQ içeriği kullanıcıya
görünür olmalı."* Ayrıca AI motorları sayfa metnini de okuyor — yalnızca
şemaya güvenmek GEO kaybı.

*Körlüğün anatomisi:* `_sss_html()` fonksiyonu **zaten vardı** ve kalem
sayfalarında doğru çalışıyordu. CLAUDE.md'de "görünür SSS eklendi"
yazıyordu. Ama yalnızca **bir sayfa tipinde** çağrılıyordu.
**Fonksiyonun doğru olması, her yerde çağrıldığı anlamına gelmiyor.**

Düzeltme: şema ve görünür içerik **aynı listeden** besleniyor. Şemaya 14
koyup sayfada 10 göstermek de ihlal olduğu için kırpma tek yerde
(`sorular = sorular[:10]`).

**2. `/rehber/` tam yetim sayfa.** Sitemap'te vardı, sitede **hiçbir
sayfadan link almıyordu** — ana sayfa doğrudan yazılara gidip dizini
atlıyordu. Ana sayfa linki + her sayfanın footer'ı: **0 → 128 link.**

**3. Başlık hiyerarşisinde atlama** — `rehber/index.html` ve `404.html`
h1 → h3 atlıyordu.

**4. İç link dağılımı çarpık.** Ölçüldü: `okul/tablet-fiyatlari` ve
`bebek/bebek-bezi-fiyatlari`, 39 kalem sayfası varken **yalnızca 1 iç
link** alıyordu. Kök neden: "ilgili kalemler" listesi her sayfada
**baştan** dolduruluyordu, geç tanımlananlar hiç seçilmiyordu. Liste
artık mevcut sayfanın sırasına göre kaydırılıyor — **deterministik
kalıyor** (rastgelelik olsa her üretimde gereksiz diff olurdu) ama akış
eşit dağılıyor. En az link alan sayfa **1 → 3**, ortalama 21.

**5.** Elle yazılan sayfalarda footer kurumsal linki eksikti.

### `scraper/test_seo_denetim.py` (14 test)
Diğer testler tek tek fonksiyonları doğruluyor; **bu dosya üretilmiş
siteye bakıyor** — çünkü bu projedeki en sinsi hatalar birim
testlerinden geçip sayfa seviyesinde ortaya çıkanlar:
FAQ şeması/görünür içerik eşitliği · yetim sayfa · başlık hiyerarşisi ·
tek h1 · canonical kendine işaret ediyor mu · title+description
benzersizliği · title 62 karakter · paylaşım etiketleri · analitik ·
kırık iç link · jenerik anchor metni · cevap bloğu · **rakamların ham
HTML'de olması** (AI botları JS çalıştırmıyor) · AI botlarının
robots.txt'te engellenmediği.

**Temiz çıkanlar:** canonical 141/141 · title ve description'da hiç
tekrar yok · görsel alt'ı eksik yok · jenerik anchor yok · sitemap ile
disk birebir · JSON-LD zorunlu alan eksiği yok · birebir aynı gövde yok ·
`lang="tr"` her sayfada · yalnızca 404 `noindex`.

## TASARIM DENETİMİ (2026-07-27) — global menü, tipografi, tablet
Yavuz: *"header inanılmaz küçük... ne var ben anlamıyorum sitede. en
önemlisi google indekslemezse hesaplayıcılar da kayıp — ne headerda var
ne sitede görünür."* Hepsi haklıydı. **Ekran görüntüsü alarak
çalışıldı** — bu projede tasarıma bakmadan dokunmak körlük.

**1. HESAPLAYICILAR HİÇBİR SAYFANIN HEADER'INDA YOKTU.** Üst menüde
yalnızca 5 vertikal vardı; **20 hesaplayıcı, 8 rehber ve veri merkezi**
hiçbir yerden erişilemiyordu. Hesaplayıcılar bölümü ana sayfada
**4.581 px** aşağıdaydı (mobilde ~5,4 ekran). İç link, arama motoru için
keşif yolunun kendisi.
→ `sayfa_uret.genel_menu()`: **8 öğeli tek menü, 141 sayfanın hepsinde
aynı.** Elle yazılan 13 sayfa eski menüde kalmıştı, onlar da geçirildi.
Bulunulan bölüm `aria-current` ile işaretli.

**2. "NE VAR BEN ANLAMIYORUM SİTEDE".** H1 *"2026'da bir şey kaça mal
olur?"* idi. → *"2026'da Ne Kaça Mal Olur?"* + veriden üretilen kapsam
satırı: **"5 maliyet endeksi · 107 kalem · 20 hesaplayıcı."**
İlk hesap 78 veriyordu (yalnızca varsayılan toplama girenler) — `ai.txt`
107 diyordu. **Sitede iki farklı sayı dolaşması, güveni rakam
tutarlılığına dayanan bir sitede kabul edilemez;** ikisi de aynı yerden
sayılıyor artık.

**3. TİPOGRAFİ.** Logo 18,4 → 23,2px · gövde 16 → 17px · mobil h1
24,8 → 30,4px (mobil kuralındaki `1.55rem` ezmesi `clamp`'i boğuyordu).
Header sticky — ana sayfa 8.900px.

**4. TABLET TAŞMASI — en ciddi bulgu.** Menü 5 öğeden 8'e çıkınca
673px'e ulaştı; logoyla birlikte 838px istiyor. Mobil kırılımı 560px'ti,
yani **561–900px arasındaki HER genişlikte sayfa yatay taşıyordu** —
tablet, katlanır telefon, küçük pencere. **390 ve 1440 test ediliyordu,
arası hiç bakılmamıştı.** Kırılım 900px'e çekildi.
Ardından 320px'te ikinci taşma: asistan formunda `flex: 1` yetmiyordu —
flex öğesinin varsayılan `min-width: auto` değeri girdiyi içeriği kadar
büyük tutup butonu dışarı itiyordu. `min-width: 0`.
**DERS: kırılım noktası "telefon/masaüstü" diye değil, İÇERİĞİN GERÇEK
GENİŞLİĞİNE göre seçilir; doğrulama birden çok genişlikte yapılır.**

**5. DOKUNMA HEDEFLERİ.** Kalem seçim kutuları ve segment butonları
23px'ti (WCAG 40px). Ev-kurma hesaplayıcısında 42 kalem alt alta —
bu yoğunlukta yanlış kutuya basmak kaçınılmaz. 40/42px'e çıkarıldı.

### `scraper/test_gorsel.py` (5 test, ~8 sn, gerçek tarayıcı)
14 genişlik × 9 sayfa yatay taşma taraması · menü bütünlüğü · konsol
hatası · karanlık mod · dokunma hedefleri.

**İKİ TESTİN KENDİ HATASI ÖLÇEREK BULUNDU:**
- Dokunma hedefi testi `input` yüksekliğine bakıyordu; bir onay kutusu
  doğal olarak 18px'tir, **asıl hedef onu saran etiket.** Etiket
  ölçülünce çoğunun 41px olduğu, sorunun yalnızca kalem ve segment
  seçimlerinde olduğu görüldü.
- "Sınıf dışında kalmış test" kontrolü önce **yanlış pozitif** verdi:
  `if __name__` satırından sonra gelen bir `class` normaldir ve testleri
  çalışır (test_asistan 12/12 koşarak doğrulandı). Gerçek hata biçimine
  daraltıldı.

Vertikal izolasyon testleri header/footer'ı dışarıda bırakacak şekilde
**daraltıldı — gevşetilmedi;** gövdeye sızan link hâlâ yakalanır.

Python **14 suite**, Node 80/80. 135 genişlik-sayfa kombinasyonunda
yatay taşma yok; canlıda doğrulandı.

## KEDİ VERTİKALİ — 6. vertikal (2026-07-28)
Tamamen ürün bazlı. **8 kalem**, orta segment kurulum **5.267 TL**,
aylık sarf **1.330 TL**, ilk yıl **21.227 TL**. sitemap 143 → **154**.

**İKİ BİLİNÇLİ KAPSAM KARARI:**
1. **Kedi ve köpek AYRILDI.** Kimse hem kedi hem köpek maması almıyor;
   ikisini tek toplama katmak, araç vertikalindeki *"marka kalemleri
   birbirinin alternatifi, toplanmaz"* hatasının aynısı olurdu. Köpek
   ayrı vertikal olarak eklenebilir.
2. **mama ve kum `varsayilan_dahil: False`** — bebek bezindeki ayrımın
   aynısı. Toplam = tek seferlik kurulum; aylık sarf ayrıca gösteriliyor.

**Kaynak:** 8 Amazon araması. Trendyol kategori slug'ları önce **tahmin
edildi ve 4'ü de 0 ürün döndürdü** — okul turundaki *"URL TAHMİN
EDİLMEZ"* dersinin tekrarı.

### Bu turda bulunan üç bug

**1. TÜRKÇE ÜNSÜZ YUMUŞAMASI — ad filtresinde yeni bir hata sınıfı.**
Desenler `yatak`, `kap`, `oyuncak` yazıyordu; ürün adlarında ek alınca
**yatağı, kabı, oyuncağı** oluyor (k→ğ, p→b). Filtre **doğru ürünleri
eledi**: kedi yatağında 49'un 39'u, mama kabında 48'in 42'si. Desenler
`[kğ]`/`[pb]` ile düzeltildi + regresyon testi. **Sonu k/p/t/ç ile biten
her kelimede bu risk var.**

**2. `genel_menu()` sıralama bug'ı.** "Sayfa diskte var mı" diye
bakıyordu; yeni vertikalin sayfası henüz üretilmemiş olduğu için ondan
önce üretilen sayfalar onu menüde göremiyordu — 154 sayfanın 81'i eski
menüde kaldı, test yakaladı. Vertikaller için ölçüt artık **verinin
varlığı** (veri varsa sayfa aynı koşuda mutlaka üretilir).

**3. HESAPLAYICI ENDEKSTEN FARKLI RAKAM VERİYORDU — en önemlisi.**
Hesaplayıcı `varsayilan_dahil: false` bayrağını **yok sayıp** her kalemi
işaretli getiriyordu:

| vertikal | endeks | hesaplayıcı | fark |
|---|---|---|---|
| bebek | 34.829 | 35.394 | bez |
| kedi | 5.267 | 6.597 | mama + kum |

İkisi de "orta segment" diyordu. **Bu, Yavuz'un bildirdiği "aynı şeyin
iki farklı değeri" sınıfının ta kendisi ve bebek vertikali yayına
gireli beri canlıdaydı** — iki sayfaya aynı anda bakmak gerektiği için
kimse fark etmemişti. Dört hesaplayıcıda da düzeltildi; beş vertikalde
hesaplayıcı varsayılanı artık endeksle **birebir aynı**. (Araç hariç ve
bu doğru — orada hesaplayıcı *sahip olma* maliyetini ölçüyor.)
`test_hesaplayici_varsayilani_endeksle_AYNI` gerçek tarayıcıda
kilitliyor; bug geri konarak doğrulandı.

## EVCİL HAYVAN: HUB + İKİ YATAY (2026-07-28)
Yavuz: *"köpek de olsun ama evcil hayvan vertikalinin içinde kedi ve
köpek iki ayrı yatay olsun."*

**Yapı:** `/evcil-hayvan/` hub (ikisini yan yana gösterir, **asla
toplamaz**) + `/kedi/` ve `/kopek/` kendi toplamı, hesaplayıcısı ve
sayfasıyla. Menüde tek "Evcil Hayvan" girdisi — ayrı gösterilse menü
10 öğeye çıkıp dar ekranda kullanılamaz olurdu.

**NEDEN TEK VERTİKALDE BİRLEŞTİRİLMEDİ:**
1. **Toplam anlamsız olurdu.** Kimse hem kedi hem köpek maması almıyor;
   bu iki liste birbirinin **alternatifi**. Toplamak, araç vertikalinde
   yaşadığımız *"marka kalemleri toplanmaz"* hatasının aynısı olurdu.
2. **"kedi masrafı" ve "köpek masrafı" ayrı arama sorguları.** Tek
   sayfada birleştirmek her ikisinde de zayıflatırdı.
Hub sayfası bu gerekçeyi okuyucuya da yazıyor.

**Köpek:** 7 kalem, kurulum **3.921 TL**, aylık sarf **1.911 TL**, ilk
yıl **26.853 TL**. Veriden çıkan ilginç sonuç: **kedi kurulumu daha
pahalı (5.267 vs 3.921) ama köpeğin aylık gideri daha yüksek (1.911 vs
1.330)** — ilk yılda köpek öne geçiyor. Rehber yazısı için hazır malzeme.

### Bu turda bulunan dört sorun (hepsi testlerden)
1. **Ad çakışması:** "Amazon - Mama ve Su Kabı" hem kedide hem köpekte;
   iki kalem sayfası aynı title'ı üretiyordu.
2. **Header kapsayıcısı — viewport'tan bağımsız taşma.** Gövde 880px'lik
   okuma sütununda; menü 9 öğeye çıkınca logo+menü **923px** istedi ve
   880px'lik kapsayıcıdan taştı — 1024'te de 1440'ta da. **Kırılım
   noktası değiştirmek çözmezdi.** Header bir gezinme çubuğu, okuma
   sütununa hizalanmak zorunda değil → kapsayıcı 1180px.
3. **flex + overflow = `min-width: 0` (aynı tuzağa İKİNCİ düşüş).**
   Menüye `overflow-x: auto` verildi ama menü bir flex öğesi ve
   varsayılan `min-width: auto` onu içeriği kadar büyük tutup overflow'u
   etkisiz kıldı. **Asistan formunda da aynı hata yaşanmıştı.**
4. **Footer nav:** kural `.footer-endeksler` sınıfına yazılmıştı ama
   footer'da **sınıfsız** bir `<nav>` daha var ve 320px'te sayfayı
   taşıran oydu. Kural sınıfa göre değil **yapıya göre** yazıldı
   (`footer nav`). *Ders: bir düzen kuralını tek sınıfa bağlamak, aynı
   yapıdaki diğerlerini dışarıda bırakıyor.*

**Doğrulama:** 176 genişlik-sayfa kombinasyonu (16 genişlik × 11 sayfa),
yatay taşma hiçbirinde yok. 165 sayfada aynı menü, 0 kırık iç link.
sitemap 154 → **165**.

## SON DENETİM (2026-07-28) — veri yüklenmeden uydurma rakam
Yavuz'un istediği son hata kontrolünde **bir gerçek bug** çıktı.

**Yavaş ya da kopuk bağlantıda "Hesapla"ya fetch bitmeden basan
kullanıcıya güvenilir görünen yanlış bir rakam gösteriliyordu:**

| vertikal | gösterilen |
|---|---|
| ev-kurma / okul / bebek / kedi / köpek | **0 TL** |
| düğün | **28.500 TL** |

**İkincisi daha tehlikeli:** 0 TL bariz yanlışken 28.500 makul görünüyor.
Sebebi tahmini kalemlerin değerinin **JS'e gömülü** olması — onlar veri
beklemiyor, gerçek kalemler bekliyor; sonuç yalnızca tahminlerin toplamı
çıkıyor.

Bu, projenin her yerde uyguladığı kuralın doğrudan ihlaliydi: *cevabı
olmayan durumda uydurma sayı gösterme.* Aynı ilke `motor.py`'de
(0 ürün → karantina), `sosyal.py`'de (söylenecek şey yoksa sus),
`asistan.py`'de (eşleşme yoksa uydurma) ve hesaplayıcıların **geçersiz
girdi** yolunda zaten uygulanıyordu — yalnızca **bu yol atlanmıştı.**

**Düzeltme:** altı hesaplayıcıda `veriYuklendi` bayrağı. Veri gelmeden
sonuç kutusu açılmıyor, yerine açık mesaj çıkıyor.
`test_veri_yuklenmeden_rakam_gosterilmiyor` veri isteğini bilerek
düşürüp kontrol ediyor; bug geri konarak doğrulandı. **Araç hariç ve bu
doğru** — araç hesaplayıcısı veri çekmiyor, MTV ve harçları resmî
sabitlerden alıyor; test bu ayrımı kaynak koddan yapıyor.

### Denetimin geri kalanı temiz
- 14 Python suite + 80 Node testi
- **sitemap'teki 165 URL'nin tamamı canlıda 200**
- 7 vertikalin yayındaki toplamı güncel veriyle birebir; ana sayfa da
  aynı rakamları gösteriyor
- title/description tekrarı 0 · 62+ karakter title yok · canonical
  165/165 · OG etiketleri ve analitik 165/165
- 5 genişlik × 9 sayfa canlı tarama: yatay taşma yok, konsol hatası 0
- kedi/köpek her yere işlenmiş: llms.txt, ai.txt, sitemap, CSV, geçmiş,
  asistan (121 kalem), sosyal rotasyonu
- Sayfalardaki "veride bulunmayan" 35 rakam tek tek doğrulandı: hepsi
  meşru grup alt toplamı (köpek 2.141 = 597+1.544 Gezdirme)

## UZUN KUYRUK YAZILARI + KAYNAK TURU (2026-07-31)
Yavuz: *"uzun kuyruklu anahtar kelimeli yazilar girelim. bunlar gercekten
cok onemli. sen yapay zeka olarak pek onem vermiyorsun gibi. cok proper
gidiyorsun. biraz halka in... damatliklara girilmeye baslandi."*

**4 yeni rehber, 15'e cikti.** Basliklar arama kutusuna yazilan sey:
*"damatlik kac para"*, *"asgari ucretle ev kurulur mu"*,
*"gelinlik mi damatlik mi pahali"*, *"kedi mi kopek mi masrafli"*.
486-570 kelime (onceki yazilar 315-445) — uzun kuyruk sorgusu daha
fazla baglam istiyor.

- **`/rehber/damatlik-kac-para/`** — trafik almaya baslayan kalem.
  Yazinin govdesi bizim olctugumuz, baskasinin olcmedigi sey: ayni
  kalemde **Trendyol 3.240 / Beymen 44.950 / Vakko 71.970**, en ucuz ve
  en pahali urun arasinda **66 kat** fark. "Damatlik tek bir urun degil"
  tespiti bu tablodan cikiyor, iddiadan degil.
- **`/rehber/asgari-ucretle-ev-kurulur-mu/`** — resmi asgari ucret
  (28.075,50 net) + kendi ev kurma olcumumuz. Ekonomik ev **181.117 TL**
  = **6,5 aylik net asgari ucret**. Iki veri kumesini birlikte tutan
  baska kaynak yok.
- **`/rehber/gelinlik-mi-damatlik-mi-pahali/`** — **bu turun en onemli
  yazisi.** Verimizde damatlik (46.450) gelinlikten (18.172) pahali
  cikiyor. *Ama bu piyasa gercegi degil, OLCUM SINIRI:* gelinlikte tek
  kaynak var (Trendyol, pazaryeri), damatlikta uc ve ikisi luks marka.
  Carpici basligi atmak ("damatlik gelinlikten pahali cikti") teknik
  olarak yalan olmazdi ama yanlis olurdu. **Nedeni gizlemek yerine
  yazinin konusu yapildi** — yazi kendi verisinin sinirini anlatiyor.
- **`/rehber/kedi-mi-kopek-mi-masrafli/`** — kurulumda kedi pahali
  (5.267/3.921), aylikta kopek (1.911/1.330), 12 ayda makas tersine
  donuyor (26.853/21.227).

### YENI TEST: baslikta gomulu para tutari YASAK
**Kendi yaptigim hatadan cikti.** Damatlik yazisinin ilk basligi
*"3 Bin Liralik da Var, 165 Bin Liralik da"* idi — ikisi de o anki
olcumden geliyordu. Bir sonraki olcumde min/max degisince **govdedeki
rakam guncellenirken baslik donmus kalacak ve sessizce yalan olacakti.**
Projenin *"hicbir tutar metne gomulmedi"* kurali basliklarda
uygulanmiyordu. `test_basliklarda_rakam_gomulu_degil` baslik/seo_baslik/
meta alanlarinda para tutari ariyor; bug geri konarak patladigi
dogrulandi. ("150 kisilik", "45 kalemde", "2026" gibi sabit kavramlar
serbest — yasak olan olculen tutar.)

### KAYNAK TURU: 4 aday denendi, DORDU DE CIKMADI
Yavuz'un onerdigi pazarama/teknosa/lcw/avva. Zorlanmadi, sebepleri:
| aday | sonuc |
|---|---|
| **teknosa** | robots.txt RET + 403 — kapali |
| **lcw** | `ERR_HTTP2_PROTOCOL_ERROR`, hem `requests` hem Playwright'ta. Ag seviyesinde engel; ana sayfa 200 donuyor ama kategori sayfalari acilmiyor |
| **pazarama** | sayfa geliyor (1 MB), **0 urun ayikleniyor** — JSON-LD/microdata/CSS hicbiri tutmuyor |
| **avva** | **calisiyor** (JSON-LD, secici gerekmedi) **ama tam takim yok** |

**Avva'nin ayrintisi kayda deger:** `/takim-elbise` sayfasi 6 urun
donuyor ve bunlar *ceket* (4.799) ile *pantolon* (3.199) — **ayri ayri
satiliyor.** Bu fiyatlari "damatlik" kalemine yazmak endeksi bozardi:
olctugumuz sey tam takim. Calisan bir kaynagi kalem tanimina uymadigi
icin birakmak, bu projede daha once idefix'te (fiyat-urun eslesmesi
kurulamiyor) ve Trendyol/altin-bilezikte (alakasiz urun) yasandi.
**Kaynagin CEKILEBILIR olmasi, OLCTUGUMUZ SEYI olctugu anlamina
gelmiyor.**

**URL tahmin edilmedi** — dordunun de ana sayfasindan kategori linki
avlandi (avva 103 linkten 5 ilgili, lcw 429'dan 118, pazarama 1167'den
55). `kaynak_tara.py` dersinin uygulamasi.

sitemap 165 -> **169**, IndexNow'a bildirildi, dordu de canlida 200.
304 Python + 80 Node testi geciyor.


## TAVSIYE YAZILARI (2026-08-01) — ve sitedeki ondalik ayraci kusuru
Yavuz: *"tavsiyeler de cok araniyor sanki. ozellikle evcil hayvan vs
konularinda."*

**TAVSIYE YAZMANIN BU PROJEDEKI SINIRI** (`rehber.py` basinda kayitli):
genel bakim tavsiyesi (*"kediyi haftada bir tarayin"*) YAZILMIYOR.
Olcmuyoruz, veteriner degiliz, ve o icerik rakiplerin yaptigi seyin ta
kendisi — modelden uretilmis, kaynaksiz, herkeste ayni. **Bizim
verebilecegimiz tavsiye OLCUMDEN cikandir:** hangi kalemde secim
butceyi gercekten degistiriyor, hangisinde degistirmiyor.

**`rehber.aralik_siralamasi()`** kalemleri ekonomik-ust **kat farkina**
gore siraliyor. Ortaya cikan sey baska kimsede yok:
| kalem | ekonomik → ust | kat |
|---|---|---|
| Kedi tuvaleti | 599 → 17.099 | **28,5** |
| Kahve makinesi | 996 → 11.452 | 11,5 |
| Kopek yatagi | 396 → 2.277 | 5,8 |
| Camasir makinesi | 18.819 → 39.292 | 2,1 |
| Bulasik makinesi | 16.579 → 26.464 | **1,6** |

**YORUM TUZAGI, metinlerde acikca yazili:** genis aralik *"pahalisi
daha kaliteli"* demek DEGIL. Cogu zaman kategori **farkli urun
tiplerini** iceriyor (kedi tuvaletinde 599 TL duz kap, 17.099 TL
otomatik elekli sistem — ayni seyin ucuzu ve pahalisi degil). Bu yuzden
tavsiye *"pahalisini al"* degil: **"once hangi tipi istedigine karar
ver"**.

**4 yazi, rehber 19'a cikti:**
`kedi-sahiplenmeden-once` · `kopek-sahiplenmeden-once` ·
`ev-kurarken-nerede-tasarruf-edilir` · `bebek-alisverisinde-nelere-dikkat`

- **Bebek yazisinda kasitli bir uyari var:** oto koltugu ve besikte asil
  kriter fiyat degil **guvenlik standardi** ve biz onu olcmuyoruz.
  Sayfada fiyat siralamasi oldugu icin bunu yazmak zorundayiz — tek
  basina birakilirsa "en ucuzu sec" gibi okunur.
- Her yazida "neyi soylemiyoruz" bolumu var (veteriner/bakim tavsiyesi
  yok, marka tavsiyesi yok, olcmedigimiz tasarruf onerisi yok).

### METIN IDDIALARI ARTIK VERIYE BAGLI — gercek hata sonrasi
Ilk hal **kedi verisine gore** yazilmisti: *"X ucta duruyor"* ve somut
ornek olarak *"bir ucta duz kap, obur ucta otomatik sistem"*. Kedide
dogruydu (28,5x'e karsi 6,0x, ve kalem gercekten kedi tuvaleti). Ama
**ayni fonksiyon kopek yazisini da uretiyordu** ve orada en genis kalem
**yatak**, siralama da 5,8/5,2/5,1/4,5 — ne bir uc var ne "otomatik
sistem" diye bir sey. Duzeltme: uc ancak ikinciden **2 kat** ayrisiyorsa
"uc" denir, dar ancak **≤2,0** ise "dar" denir, urun tipi **ornekle
anlatilmaz** (hangi kalem oldugunu onceden bilemeyiz).
**DERS (bu projede tekrarlayan sinif): bir veri kumesi icin yazilmis
metni baska bir kumeye uygulamak.** Sabit vertikal listeleri, `sss/`
commit eksigi ve `_sss_html`'in tek sayfa tipinde cagrilmasi ayni
aileden.

### AYRI BULGU — SITENIN 107 SAYFASINDA ONDALIK AYRACI YANLISTI
`{kat:.1f}` dogrudan kullaniliyordu: **"2.1 kat"**, **"28.5 kat"**.
Nokta Turkce'de **binlik** ayraci; ayni cumlede *"29.382 TL"* ile
*"2.1 kat"* yan yana duruyordu — ayni karakter iki farkli anlamda.
Benim yeni sayfalarimda degil, **sitede zaten duran** bir kusurdu.
- **`sayfa_uret._kat()`** tek yerden cozuyor; tam sayida ondalik hic
  gosterilmiyor (6,0 degil **6**).
- Yeni test (`test_seo_denetim`) **uretilmis sayfalarin tamamini**
  tariyor, bug geri konarak patladigi dogrulandi.
- Mevcut bir test eski bicimi kilitliyordu (`"3.0 katı"`) — yeni kurala
  gore guncellendi, ondalikli bir vaka da eklendi.

**Mevcut testler bir hatami daha yakaladi:** kedi ve kopek yazilarina
ayni meta aciklamayi vermistim (description tekrari).

sitemap 169 → **173**, IndexNow'a bildirildi, dordu de canlida 200.
14 Python suite (306 test) + 80 Node testi geciyor.


## SEARCH CONSOLE: "aggregateRating / review eksik" (2026-08-01)
Yavuz sordu. **Ikisi de ISTEGE BAGLI alan, eksiklikleri hata degil** —
Search Console bunlari "kritik olmayan sorun" olarak listeliyor.
Etkisi: yildizli zengin sonuca aday olmuyoruz. Fiyat/Product parcacigi
calismaya devam ediyor.

**DOLDURMUYORUZ, karar kayitli:**
1. **Kullanici yorumu toplamiyoruz.** Olmayan yorumu isaretlemek
   Google'in *yapilandirilmis veri spam'i* manuel islemine dogrudan
   aday. Birkac yildiz icin alinacak risk degil — manuel islem tum
   sitenin gorunurlugunu vurur.
2. **Kendi urunumuze kendi puanimizi vermek** self-serving review;
   ayrica sayfada GORUNUR olmayan bir puani isaretlemek de ihlal.
3. **Zaten urun DEGERLENDIRMIYORUZ**, fiyat olcuyoruz. Bir buzdolabinin
   iyi olup olmadigi bizim olctugumuz sey degil — o yuzden bu alanlarin
   eksik olmasi bir kusur degil, kapsam tanimimizin dogru sonucu.

### AYNI TURDA GERCEK BIR KUSUR BULUNDU: `availability: InStock`
Semaya bakinca cikti. Product/AggregateOffer blogunda
`"availability": "https://schema.org/InStock"` yaziyordu ve **97
sayfada** duruyordu. **Hicbir sey satmiyoruz ve stok durumu
olcmuyoruz** — dogrulanmamis bir iddiaydi. Sitenin baska hicbir yerinde
olcmedigimiz bir sey iddia edilmiyor; semada da edilmemeli. Ustelik
AggregateOffer icin zorunlu alan degil (zorunlu olan `lowPrice` +
`priceCurrency`). Kaldirildi.

**DERS:** semanin dogrulanmasi (parse OK, zorunlu alan tam) icerigin
DOGRU oldugu anlamina gelmiyor. `InStock` gecerli bir degerdi, hicbir
denetim aracina takilmazdi — sadece gercek degildi. Sema, sayfa
metniyle ayni dogruluk standardina tabi.

**Yeni test** uretilmis sayfalarin TUM JSON-LD bloklarini tariyor:
`aggregateRating` / `ratingValue` / `reviewCount` / `availability`
gecerse patliyor. Gercekten yorum toplanmaya baslanirsa once o altyapi
kurulur, sonra test bilerek guncellenir.


## TASARIM DILI: SaaS SABLONUNDAN ISTATISTIK BULTENINE (2026-08-01)
Yavuz: *"siteyi kim gorse Claude isi diyor. demek ki tasarim dilin cok
standart. cikamadik oradan."* Haklıydı. Ekran goruntusu alinarak
calisildi (bu projede tasarima bakmadan dokunmak korluk).

**"URETILMIS SITE" DEDIRTEN SEYLER — tek tek belirlendi:**
1. **Sistem font yigini** (`-apple-system, Segoe UI, Roboto...`) —
   tek basina en net isaret. Tarayici varsayilani demek, yani hic
   tipografi karari verilmemis demek.
2. Her sey acik gri zemin uzerinde **10px yuvarlatilmis kart**.
3. **Tek mavi vurgu hem her linke hem her RAKAMA** ayni sekilde —
   yani hiyerarsi yok, okuyucu neyin tiklanabilir oldugunu ayirt
   edemiyor.
4. Her yerde **esit ve bol bosluk**; hicbir yerde gerginlik yok.
5. **999px yaricapli hap** radyo butonlari ve rozetler.

**KOK NEDEN: yanlis referans.** SaaS landing page'ine bakilmisti. Bu
sitenin isi olcum yayinlamak; dogru referans **istatistik bulteni ve
finans basini** — kart degil cetvel, yumusak degil keskin, dekoratif
degil isaretleyici renk.

**YAPILANLAR — yalnizca CSS, 173 sayfanin HTML'ine dokunulmadi:**
- **Source Serif 4** (baslik + rakam) + **IBM Plex Sans** (govde),
  **kendi sunucumuzda** (`assets/font/`). Google Fonts'a baglanmak
  ucuncu taraf istegi + KVKK tarafinda gereksiz yuk. `fontTools` ile
  Turkce+Latin karakter kumesine indirgendi: **396 -> 116 KB**.
  `unicode-range` ile latin/latin-ext ayri; `font-display: swap`.
- **Kart/golge/gri panel -> CETVEL ve bosluk.** `.cevap-blok`,
  `.kart`, `.sonuc-kutu`, `.hizli-hesap`, `.asistan` — hepsi kutu
  olmaktan cikti, ust kenar kuraliyla ayrisiyor.
- Kose yaricapi **10px -> 2px**; 999px'lik hap kalmadi.
- **RAKAM RENKLE DEGIL BUYUKLUKLE one cikiyor.** Renk artik yalnizca
  tiklanabilir seye ait. Toplamlar serif ve ~3rem.
- Kagit beyazi zemin (`#fbfaf7`) + basili yayin kirmizisi
  (`#9c2b1a`); karanlik mod da sicak tonda.
- **`tabular-nums`**: sitenin urunu fiyat sutunu, basamaklar alt alta
  hizalanmaliydi. Estetik degil islevsel kusurdu.

### Bu turda bulunan uc kusur (tasarimla ilgisiz, bakinca cikti)
1. `background: var(--renk-vurg, var(--renk-vurgu))` — **oyle bir
   degisken yok**; yalnizca fallback sayesinde calisiyordu. Birisi
   fallback'i sadelestirse buton renksiz kalirdi.
2. `.sonuc-kutu` sabit `#c7d5fb` kullaniyordu — degiskene bagli
   olmadigi icin **karanlik modda oldugu gibi kaliyordu**.
3. Yeni tipografide tabular rakamlar oransal olanlardan genis: dar
   sutunda **"46.450 TL" iki satira boluniyordu**. `td.sayi`'ya
   `white-space: nowrap`.

### VE BIR REGRESYONU KENDI GORSEL TESTIM YAKALADI
`.cevap-blok strong`'a `nowrap` koymustum — amac *"406.375 TL"*
ifadesinin bolunmemesiydi. Ama **cevap blogundaki her `<strong>`
rakam degil**: `/hesap/` sayfasinda uzun bir vurgulu cumle 665px'lik
kirilamaz bir satira donusup 320px'te sayfayi yatay tasirdi.
`test_gorsel` yakaladi, geri alindi, sebebi CSS'e yazildi.
**Ayni sinif: bir baglam icin dogru olan kurali tum bagalamlara
uygulamak** (kopek yazisindaki "otomatik sistem" cumlesi, `_sss_html`
tek sayfa tipinde cagrilmasi, sabit vertikal listeleri).

**Dogrulama:** 14 genislik x 9 sayfa yatay tasma taramasi temiz,
karanlik mod temiz, canlida 6/6 font 200 ve 0 konsol hatasi.


## KIRTASIYE ZINCIRLERI — okul 2 -> 4 bagimsiz kaynak (2026-08-01)
Yavuz: *"kirtasiye kismi iyi tiklama getirecek gibi. D&R, Nezih
kirtasiye ya da birkac yerden daha veri cekmeyi dener misin"*

Okul vertikalinin **14 kaleminin TAMAMI pazaryerinden** (trendyol +
amazon) geliyordu. Kirtasiye zinciri **farkli bir pazar**: marka karmasi
ve fiyat bandi pazaryerinden belirgin ayriliyor — COK KAYNAK KURALI'nin
istedigi turden gercek bir ikinci bakis acisi.

**Eklenen 6 kaynak:** nezih (defter, kalem-kutusu, boya-seti,
okul-cantasi, matara) + dr (defter).
**Okul toplami 5.624 -> 6.386 TL, bagimsiz site 2 -> 4.**

| kalem | trendyol | amazon | nezih | dr | endeks |
|---|---|---|---|---|---|
| defter | 296 | 141 | 245 | 400 | **270** |
| kalem-kutusu | 313 | 601 | 600 | — | **600** |
| boya-seti | 350 | 202 | 340 | — | **340** |
| okul-cantasi | 1.242 | 1.442 | 2.500 | — | **1.442** |
| matara | 247 | 800 | 1.050 | — | **800** |

### ELENENLER — sebepleriyle (yaml'a da yazildi)
- **ofix — teknik olarak EN TEMIZ adaydi ama alinamaz.** `kaynak_tara`
  SARI verdi: 115 fiyatin **114'u urun kartinin icinde** (idefix'i
  eleyen eslesme sorunu hic yok). **AMA B2B ofis tedarikcisi ve
  fiyatlari KDV HARIC gosteriyor** (*"57,45 TL + KDV"*). Pazaryerinin
  KDV dahil fiyatiyla ayni endekse koymak sistematik hata olurdu.
  *Kaynagin cekilebilir olmasi, OLCTUGUMUZ SEYI olctugu anlamina
  gelmiyor* — avva/takim-elbise dersinin ayni ailesi.
- **dr/matara:** "termos ve mataralar" kategorisi Stanley tipi TERMOS
  iceriyor; bizim kalem ogrenci sulugu.
- **dr/okul-cantasi:** ham HTML'de 1 urun (gerisi JS) — orneklem yok.
- **nezih/kuru-boya-kalemleri:** bizim `kalem` kalemi KURSUN kalem seti.
- **kitapyurdu, bkmkitap:** kategori sayfasinda fiyat yok (JS).

### NEZIH'TE SINIF ADLARI TERS — sessiz sisirme tuzagi
```
.currentPrice     = ODENEN fiyat             (499,90)
.discountedPrice  = ustu cizili liste fiyati (699,90)
```
Adina bakip `.discountedPrice` secilseydi (kulaga "indirimli fiyat"
gibi geliyor) endeks **sistematik olarak sisirilirdi** ve hicbir test
bunu yakalamazdi — rakamlar gecerli, sadece yanlis fiyat olurdu.
Uc urunde tek tek dogrulandi.

### kaynak_tara.py'nin KIRMIZI'si kesin sonuc DEGIL
Tarayici D&R'a *"fiyat kart disinda, eslesme kurulamaz"* dedi — ayni
teshis idefix'i hakli olarak elemisti. Ama D&R'da fiyat **karttan 6 kat
derinde** (`.prd-price` -> ... -> `div.product-card`) ve sezgisel
tarayici o kadar yukari bakmiyor. Elle bakinca cozuldu: 25 urun.
**Ders: KIRMIZI "bak" demek, "birak" demek degil** — ozellikle hedef
site elle secilmisse.

### Ve yine URL TAHMIN ETTIM
Ilk turda `dr.com.tr/.../defterler/grupno=00246` uydurdum, 404 aldi.
Dogru URL sitenin kendi ana sayfasindan avlandi. **Bu ders bu projede
en az dorduncu kez tekrarlaniyor** (okul/Trendyol, kedi/Trendyol,
Karaca, simdi D&R): kategori URL'i ASLA tahmin edilmez.

Cikan capraz dogrulama uyarilari (matara %325, okul-cantasi %101)
gizlenmiyor — endeks sayfasinda "Capraz dogrulama notu" kutusunda
yaziyor. sitemap 173, IndexNow'a bildirildi, canlida dogrulandi.


## BEBEK: EBEBEK KAYNAGI + DOGUM MALIYETI REHBERI (2026-08-02)
Yavuz: *"bebek kategorisini de hem rehber yazilariyla hem yeni maliyet
kaynaklariyla guncelleyebilir miyiz? ozel hastanede dogum maliyeti gibi
bir rehber de olabilir."*

**KAYNAK — ebebek eklendi (6 kalem).** Bebek hazirligi **34.829 ->
39.300 TL**, bagimsiz site **2 -> 3**. JSON-LD veriyor, CSS secici
gerekmedi.

| kalem | trendyol | amazon | ebebek | endeks |
|---|---|---|---|---|
| bebek-arabasi | 3.799 | 10.599 | 11.199 | **10.599** |
| besik | 1.744 | 5.729 | 4.399 | **4.399** |
| park-yatak | — | 5.399 | 4.899 | **5.149** |
| bebek-kuveti | — | 1.250 | 850 | **1.050** |
| gogus-pompasi | — | 1.259 | 3.299 | **2.279** |
| bebek-bezi | — | 720 | 248 | **484** |

**`render_gerekli: true` — ters yonlu bir ders.** ebebek ilk birkac
istekte duz `requests` ile DOLU HTML donuyor, sonrakilerde **2.418
byte'lik bos kabuk**. Yani "bir kez calisti" diye `false` yazmak
yaniltici olurdu. Beymen'de tam TERSINI ogrenmistik (orada
`render_gerekli: true` yanlisti cunku Playwright'a bos sayfa
veriliyordu). **Kural: iki modu da, birkac kez dene.**

**Elenenler:** ebebek biberon-seti / zibin-seti (bizim kalemler SET,
ebebek TEK urun listeliyor — farkli urun, segment farki degil) ·
ebebek mama-sandalyesi (6 urun, donen sey "bebek oturagi") · ebebek
oto-koltugu (bizimle %1 uyumlu **ama ham HTML'de 4 urun** — guvenilir
medyan icin az) · **joker** (calisiyor ama premium butik: Inglesina oto
koltugu 33.742 TL, bizim 8.573) · prenatal, mothercare (SSL/baglanti).

### `/rehber/ozel-hastanede-dogum-maliyeti/` — RAKAM VERMEYEN REHBER
**Bu yazinin degeri rakam vermemesinde.** Ozel hastane dogum paketi
fiyatlari internette liste halinde yayinlanmiyor; telefonla soruluyor
ve gebelik haftasina, doktora, oda tipine gore degisiyor. *"Ortalama
dogum 80 bin TL"* yazmak KIRMIZI CIZGI ihlali olurdu — ve bu sorguda
tam olarak oyle yapan cok sayfa var, hicbirinde kaynak yok.

Yazinin verdigi sey: **ilave ucret mekanizmasi** (SGK sozlesmeli
hastanede odenen sey doğumun tamami degil, kanunun izin verdigi fark),
teklif alirken sorulacak somut sorular (sezaryene donerse fark var mi,
doktor ucreti dahil mi, kac gece yatis...), ve **olcebildigimiz kisim**
(dogum sonrasi hazirlik, gercek veriyle).

**ILAVE UCRET TAVAN ORANI BILEREK YAZILMADI.** Oran Cumhurbaskani
kararina bagli ve degisiyor; birincil kaynaktan (Resmi Gazete / SGK
tebligi) guncel orani **dogrulayamadim**. Dogrulanmamis bir yuzde
yazmak yerine SGK'nin kendi **ilave ucret sorgu ekranina**
yonlendiriliyor — hem dogru hem bayatlamaz. Oran birincil kaynaktan
dogrulanirsa teblig adi + R.G. tarih/sayisiyla eklenebilir.

### `/rehber/dogumdan-once-alinacaklar-listesi/`
Cok aranan "dogum oncesi alinacaklar" sorgusu; farkimiz listeyi
**fiyatla** vermek. Uc kalem toplamin buyuk kismini belirliyor; hangi
kalemin dogum gunu gerektigi, hangisinin sonraya birakilabilecegi
veriden cikiyor. **Oto koltugunda kriterin fiyat degil GUVENLIK
STANDARDI oldugu ayrica yaziliyor** — sayfada fiyat siralamasi var ve
tek basina "en ucuzu sec" diye okunabilirdi.

sitemap 173 -> **175**, IndexNow'a bildirildi, canlida dogrulandi.


## EV KURMA UST SEGMENTI NIHAYET KAPANDI (2026-08-02)
Yavuz: *"buzdolabi ve o ev kurma kisminda hala eksigiz. dogru
kaynaklara ulasamadik. ust fiyatlar cok ucuz kaldi."*

**BU, 25 TEMMUZ'DAN BERI ACIK OLAN EKSIK.** O gun ayni tespit
yapilmisti (*"buzdolabi 45 bin TL luks diyoruz ama asil luks
80.000'den basliyor"*) ve **teshis dogruydu**: Trendyol kategori
sayfasinda max 62K var, premium modeller listede yok; `?prc=` ve
`?sst=PRICE_BY_DESC` filtreleri JS ile uygulaniyor, sunucu HTML'i
degismiyor. **Ama cozum eksikti: kalemi "luks" yerine "ust" diye
ADLANDIRDIK, gercek premium veriyi getirmedik.** Adlandirma bir cozum
degil, sorunun kabulüydu. Simdi veri getirildi.

### MediaMarkt — 17 kalem, JSON-LD, CSS secici gerekmedi
**Onceki turda yanlis elenmisti.** Kayitta *"robots ONAY ama JSON-LD/
microdata YOK -> CSS gerekir"* yaziyordu; o teshis **ANA SAYFAYA**
bakilarak yapilmisti. **Kategori sayfalarinda JSON-LD var.**
*Ders: bir siteyi ana sayfasina bakip elemek, kategori sayfasina
bakmadan karar vermek demek.*

| kalem | ust (once → sonra) | max (once → sonra) |
|---|---|---|
| firin-ocak | 25.690 → **38.564** | 31.049 → **53.528** |
| buzdolabi | 48.266 → 42.999 | 61.990 → **72.999** |
| dikey-supurge | — | 26.299 → **39.999** |
| utu | — | 9.999 → **27.499** |
| kahve-makinesi | — | 23.868 → **32.999** |

**12 URUN SINIRI:** her kategoride tam 12 urun donuyor ve
kaydirma/render bunu **degistirmiyor** (0/6/12 kaydirma denendi,
ucu de 12) — MediaMarkt JSON-LD ItemList'e 12 urun koyuyor. Orneklem
ince ama premium uctaki 12 urun tam da eksigimiz olan sey.

### Dogtas — 3 kalem, mobilya ust segmenti
| kalem | ust (once → sonra) | Dogtas / Trendyol |
|---|---|---|
| koltuk-takimi | 45.944 → **66.005** | 54.406 / 41.344 |
| gardirop | — | **42.003 / 6.000** |

Gardiropta pazaryeri ile marka magazasi arasindaki ucurum artik
gorunuyor: **7 kat.**

### 17 KALEMIN HEPSI EKLENDI, sadece rakami yukseltenler DEGIL
Oyle yapmak **kiraz toplamak** olurdu. Televizyon (bizim max 119.999 >
MediaMarkt 89.999), supurge (62.999 > 39.999) ve camasir makinesinde
bizim mevcut ust ucumuz zaten daha yuksek cikti — **bu da bilgi:**
her kalemde premium magaza daha pahali degil.

### ELENENLER
- **`dogtas/yatak` — en sinsi olani.** `/yataklar` sayfasi
  *"YATAK ODASI TAKIMI"* donduruyor (117.955 TL); bizim `yatak`
  kalemimiz **SILTE** (ust medyanimiz 3.826). Kategori adi tuttugu
  icin ilk bakista dogru gorunuyordu, **urun ADLARINA bakilinca**
  ortaya cikti. D&R/termos ve ebebek/biberon ile ayni tuzak.
- vatan, miele: kategori linki bulunamadi · siemens, vestel: fiyat JS
  ile · bosch, bellona, istikbal: fiyat var ama kart icinde degil ·
  enzahome: 66 fiyatin yalnizca 6'si kart icinde · vivense: robots RET

### Bulunan hata
Dogtas'ta ilk yazdigim `isim_secici: .c-p-i-link` **karti saran `<a>`**
idi ve metni **fiyatlari da iceriyordu**
(*"FIORENKoltuk Takimi56.984,43 TL63.316,03 TL"*). **Fiyat dogru
cikiyordu, o yuzden bu sessizce gecebilirdi** — urun adlari yalnizca
log ve ad filtresinde kullaniliyor. `.title` ile duzeltildi.

**ev-kurma:** eko 181.117 → **212.086** · orta 352.769 → **385.913** ·
**ust 622.136** · bagimsiz site **5 → 7**.
`tava-seti/trendyol` saglik kontrolunde karantinaya alindi (urun
sayisi anomalisi) — endekse girmedi.


## DENETIM TURU (2026-08-02) — paylasim karti, segment adi, og:title
Yavuz: *"bu turu kontrole ayiralim. Google'da nasil gorunuyor, sosyal
medyada ya da whatsapp'ta paylasilinca nasil gorunuyor? hata, eksik,
fazla var mi? GEO-SEO kontrolu"* — canli siteye karsi olculdu.

### 1. HER SAYFA AYNI JENERIK GORSELI PAYLASIYORDU (175 sayfa)
`/ev-kurma/buzdolabi-fiyatlari/` WhatsApp'ta paylasildiginda kartta
*"2026 Maliyet Endeksi"* yaziyordu, **"Buzdolabi 29.597 TL"
YAZMIYORDU.** Ilk trafik olcumunde referans kaynagi neredeyse tamamen
`m.facebook.com`'du — **bu kanalda paylasim karti dogrudan tiklanma
oraninin kendisi.** 27 Temmuz'da "en yuksek kaldiracli is" diye
kaydedilmisti; kapandi.
- **`og_gorsel.kalem_kartlarini_uret()`** — 106 kart (7 endeks +
  99 kalem), ortalama **31 KB** (WhatsApp'in 300 KB sinirinin cok
  altinda). Kartin uzerindeki her sey **veriden**; sabit metin
  yalnizca marka adi ve alan adi.
- **Kart dosyasi yoksa sessizce jenerige duser** — 404 veren bir
  `og:image`, jenerik gorselden kotudur (bos kart cikar).
- `kalem_sayfalarini_genislet()` cagrilmadan yalnizca **28** kart
  uretiliyordu (statik tanim), 97 sayfa varken. Calisma anindaki
  genisletme sarttir.
- Aylik workflow'a eklendi: kartlar **rakam tasiyor**, her olcumde
  yenilenmeli.

### 2. AYNI SEGMENTIN UC FARKLI ADI VARDI
25 Temmuz'da *"Lüks" → "Üst"* karari alinmisti (sebep: 43 bin TL'lik
buzdolabi luks degil, listedeki ust ceyrek). **Degisiklik yalnizca
hesaplayici butonlarina ve kalem sayfasi tablosuna uygulanmisti:**

| yer | yazan |
|---|---|
| endeks sayfasi tablo basligi | **Lüks** |
| kalem sayfasi tablosu | Üst |
| hesaplayici butonu | Üst |
| meta description | **lüks** |

108 sayfanin GORUNUR metninde, 99 meta aciklamada eski ad duruyordu.
Hepsi "Üst"e cevrildi ve `test_segment_adi_SITE_GENELINDE_ayni` ile
kilitlendi. (*"lüks marka magazasi"* gibi MARKAYI tarif eden kullanim
serbest — yasak olan **segment adi** olarak kullanmak.)
**Ayni sinif: bir yerde duzeltip her yerde duzeldigini varsaymak.**

### 3. ANA SAYFA og:title BAYATTI
*"2026'da ne kaça mal olur?"* diyordu; baslik bir gun once
*"2026 Maliyet Endeksi"* olmustu. Paylasilan kart, sayfanin baska bir
sayfasiymis gibi gorunuyordu.

### TEMIZ CIKANLAR
Googlebot / GPTBot / ClaudeBot / PerplexityBot / facebookexternalhit /
WhatsApp **hepsi 200** · robots.txt'te tek `Disallow: /` yok ·
sitemap **175 URL diskle BIREBIR** (ne eksik ne fazla) · llms.txt yeni
rehberleri iceriyor · *"17 bagimsiz kaynak"* iddiasi gercek veriyle
dogrulandi (17 benzersiz site) · og gorseli 1200x630, 50 KB, 1.90:1.

### ILK YAZDIGIM TEST ISE YARAMIYORDU
*"ozel kart sayisi > 50"* diye bakiyordu; bir vertikali jenerige
dondurunce **digerleri sayiyi ayakta tutuyor** ve test geciyordu (bug
geri konarak dogrulandi). Artik **kart dosyasi diskte olan her
sayfanin o karti gercekten gosterdigi** tek tek kontrol ediliyor — bu
haliyle bug geri konunca patliyor.
**DERS: esik degerli test (`> N`) bir seyin BOZULDUGUNU degil, hala
BIRAZ calistigini olcer.**

Ayrica bir test degisiklikten sonra **sessizce her zaman gecer** hale
gelmisti: `assertNotIn("lüks segmentte")` — o ifade artik hic
uretilmiyor. Iki ifadeyi de kontrol edecek sekilde guncellendi.


## PAYLASIM KARTLARI TAMAMLANDI: 167/174 (2026-08-02)
Yavuz: *"rehber ve hesaplayici sayfalarina da kart yapalim."*

**IKI FARKLI KART TIPI GEREKTI** cunku bu sayfalarda "ana rakam" yok:

| tip | nerede | kartta ne var |
|---|---|---|
| **rakam odakli** | kalem, endeks, **senaryo** | buyuk tutar + kaynak/orneklem/tarih |
| **baslik odakli** | rehber, hesaplayici, metodoloji | baslik + **dayanak** |

- **Senaryo sayfalari rakam kartini hak ediyor** — gercek toplamlari var
  (*"100 Kisilik Dugun 356.375 TL"*) ve zaten en yuksek niyetli
  sorgulari hedefliyorlar.
- **Hesaplayici kartinda alt satir MEVZUAT DAYANAGI:** *"332 Seri No.lu
  Gelir Vergisi Genel Tebligi (31.12.2025 R.G. 33124)"*. Rakiplerin
  paylasim kartinda mevzuat atfi yok — bu bizim ayirt edici yerimiz ve
  paylasilan gorselde gorunuyor.

### YAYINLAMADAN ONCE YAKALANAN HATA
Ilk halde rehber kartina o yazinin **vertikal toplami** vurgu olarak
basiliyordu. **Damatlik yazisinin kartinda "406.375 TL" goruluyordu —
o DUGUN TOPLAMI; damatlik 46.450 TL.** Karti goren *"damatlik 406 bin"*
anlar. Yazinin kendi rakami govdede hesaplaniyor ve karta guvenilir
sekilde tasinamiyor; vurgu satiri kaldirildi, iddiayi **baslik** tasiyor.
*Rakami one cikarmak her zaman iyi degil — YANLIS rakami one cikarmak
hic rakam olmamasindan kotu.*

### PALETLI PNG — depo sisme sorunu
167 kart x 33 KB = **5,5 MB**. Kartlar **rakam tasidigi** icin her
olcumde (ayda iki kez) yeniden uretilip depoya giriyor — **yilda
~130 MB git gecmisi** demekti. Duz zemin + duz metin oldugu icin
16 renklik palet gorsel olarak ayirt edilemiyor ama dosyayi ucte
birine indiriyor: **33 -> 9,5 KB**, toplam **5,5 -> 1,9 MB**.

### TEK GIRIS NOKTASI: `og_gorsel.tum_kartlar()`
Onceden iki ayri fonksiyon vardi ve workflow **yalnizca birini**
cagiriyordu — `sss/` sayfasinin commit listesinden dusmesiyle ayni tur
hata (uretilen sey var, yayina tasiyan adim eksik). Workflow tek
cagriya gecirildi.

**Kalan 7 jenerik sayfa DOGRU:** hakkimizda, iletisim, veri, sss,
rehber/hesap dizinleri, evcil-hayvan hub — bunlar tek bir olcumu
temsil etmiyor.

Kart rakamlarinin sayfa rakamlariyla birebir tuttugu dogrulandi
(100 kisilik dugun 356.375 · buzdolabi 29.597 · besik 5.729).


## 5 AGUSTOS KOSUSU + SEARCH CONSOLE DENETIMI (2026-08-09)

### ILK GERCEK URETIM KOSUSU CALISTI
5 Agustos'ta aylik workflow kendiliginden kostu ve commit atti
(`1fc7953 Aylik veri guncellemesi 2026-08-05`). Zaman serisi olustu:
arac 3 olcum / 25 kalem, ev-kurma 4 olcum, bebek 3.
**10 gunluk esik dogru calisti:** 2 Agustos'ta elle calistirdigim
vertikaller (ev-kurma 25 kalem, okul 6) esigin altinda kaldigi icin
reddedildi — uyardigim bedel aynen gerceklesti.

### AMA SAYFALARDA GORUNMUYORDU — SESSIZ SIRA HATASI
`gecmis.py` workflow'un **en sonunda** kosuyordu, `sayfa_uret.py` ise
ondan once. Yani **sayfalar uretilirken zaman serisi henuz o ayki
olcumu icermiyordu** → *"Fiyat gecmisi" bolumu HER ZAMAN BIR OLCUM
GERIDEYDI.*

Somut sonuc: 5 Agustos'ta damatlik sayfasi hala *"kendi olcumumuz yeni
basladi, ilk karsilastirmali rakamlar bir sonraki olcumde gorunecek"*
diyordu — oysa seride `2026-07-24` ve `2026-08-05` kayitlari vardi ve
`_fiyat_gecmisi_html` elle cagrildiginda karsilastirmayi uretiyordu.
**Projenin en cok beklenen ciktisi bir tur gecikiyordu ve hicbir sey
hata vermiyordu.**

Duzeltme: `agrega -> gecmis -> sayfa_uret`. Testle kilitlendi (eski
sirayla test patliyor, dogrulandi). Yeniden uretim sonrasi
**47/81 kalem sayfasinda gercek karsilastirma** gorunuyor (once 0).

### SEARCH CONSOLE — 28 gun: 555 gosterim, 4 tik, konum 39,4, 115 sorgu

**STRATEJIK SURPRIZ: gosterimlerin buyuk kismi maliyet endekslerinden
DEGIL, FINANS HESAPLAYICILARINDAN geliyor.**

| sayfa | gosterim |
|---|---|
| www/hesap/kira-gelir-vergisi-hesaplama | 66 |
| /dugun/damatlik-fiyatlari | 61 |
| www/hesap/temettu-verimi-hesaplama | 36 |
| www/hesap/hisse-maliyet-hesaplama | 28 |

Sorgu kumeleri: kira geliri vergisi ~72 · damatlik/gelinlik ~63 ·
hisse-borsa maliyet ~51 · temettu ~37 · tapu harci ~18.

**EN BUYUK TEKNIK SORUN — www:** dort varyant da (http/https ×
www/koksuz) **200 donuyor.** Google ayni sayfayi iki ana bilgisayara
bolmus: *tiklamalar www'ye, gosterimler koke gidiyor.* Dizine ekleme
raporu: **185 sayfa dizinde degil**, 123'u "kesfedildi-taranmadi" ve
**ana sayfanin kok surumu bile hic taranmamis** (son tarama: Yok).
Canonical dogru ama canonical bir IPUCU, 301 bir DIREKTIF.
`_redirects`/`_headers` dosyasi yok, Worker panelden yapilandirilmis —
**bu Cloudflare Redirect Rules isi, Yavuz'da.**

**KELIME BOSLUKLARI (sayfa aradiklari sey, kelimeleri farkli):**
1. **"borsa" kelimesi hisse-maliyet sayfasinda HIC GECMIYORDU.**
   "borsa maliyet hesaplama" 18 gosterimle en cok gosterim alan ikinci
   sorgumuz; varyantlariyla ~30 gosterim, hepsi 0 tik. Baslik
   *"Borsa Hisse Maliyet Dusurme Hesaplama"* oldu.
2. Temettu sayfasi yalnizca "verim" diyordu; sorgular "geliri" (8),
   "orani" (5), "formulu" (5), "kar payi" (3) diyor.
3. Kira gelirinde iki alt konu eksikti. **"kira vergisi cezasi"** icin
   CEZA TUTARI YAZILMADI (VUK'a ve yeniden degerlemeye bagli,
   dogrulamadan rakam vermeyiz); yazilan sey KESIN kural: beyan
   edilmezse **istisna hakki duser** (GVK md.21). **"tarla kira
   vergisi"** icin: bu hesap onu KAPSAMIYOR, 58.000 TL istisna yalnizca
   konuta ozgu — soylemek, yanlis sonuc vermekten iyi.

### Yan not
Search Console'da da **URL tahmin edip 404 aldim** (drilldown linki).
Bu ders artik tarayicida da tekrar etti.


## ARAMA VERISI: SORGU KUMELERI VE DURUMLARI (2026-08-22, guncel)
Search Console export: tarih filtresi **Son 3 ay**, fiilî veri aralığı
**2026-07-24 – 2026-08-19**. Toplam: **3.277 gosterim · 21 tik ·
%0,6 TO · konum 25,9 · 306 sorgu**. Önceki tur 555 gosterim / 4 tik /
115 sorguydu; gosterim ~5,9x, tik ~5,25x buyudu.

Host bolunmesi sayfa tablosunda acikti: kok host **16 tik / 2.514
gosterim**, `www` host **5 tik / 857 gosterim**. Cloudflare 301
2026-08-22'de duzeltildi; bir sonraki GSC turunda `www` sinyalinin
koke kayip kaymadigi kontrol edilmeli.

| kume | sorgu sayisi | tik | gosterim | durum |
|---|---:|---:|---:|---|
| dugun / gelinlik / damatlik | 36 | 6 | 292 | En guclu ticari kume. 1.000 kisilik senaryo acildi; yeni sayfadan once niyet ayrimi. |
| hisse / borsa | 45 | 0 | 272 | "borsa" eklendi; mevcut arac guclendirilecek, kopya hesaplayici acilmayacak. |
| kira | 36 | 0 | 254 | Sayfa var ama pozisyon zayif; cevap ve otorite sorunu, sadece yeni URL sorunu degil. |
| tapu / ipotek | 60 | 0 | 159 | Tapu araci var; ipotek ve KKTC sorgularinin ayri niyeti dogrulanacak. |
| calisan / maas / tazminat | 54 | 0 | 139 | Mevzuat sayfalari icin kaynak tazeligi ve sorgu dili oncelikli. |
| ev kurma / beyaz esya | 13 | 1 | 84 | Urun ozelligi sorulari geliyor; ozellik verisi toplamadan tavsiye yazilmayacak. |
| evcil hayvan | 3 | 0 | 24 | Aylik kedi sorgusu konum 11; iki aylik gider rehberi acildi. |
| bebek / dogum | 14 | 0 | 19 | Aylik gider cevabi alt sinirla eklendi; saglik/ucret iddiasinda dikkat. |

Ek sinyal: Ürün snippet'leri **40 gosterim, konum 5,55**, ancak 0 tik.

Ilk sayfaya en yakin sifir tikli sorgular: `defter fiyatları 2026`
(47 gosterim, konum 6,7), `aylık kedi masrafı 2026` (21, konum 11),
`1.000 kişilik düğün yemeği maliyeti 2026` (13, konum 8,1), `bir bebeğin
aylık masrafı 2026` (8, konum 7,5), `mikrodalga fırın fiyatları Türkiye
2026` (8, konum 10) ve `bir köpeğin aylık masrafı 2026` (8, konum 11,4).

### KAPATILAN BOSLUKLAR
1. **"borsa" kelimesi hisse-maliyet sayfasinda HIC GECMIYORDU** — oysa
   "borsa maliyet hesaplama" 18 gosterimle en cok gosterim alan ikinci
   sorgumuzdu. *Sayfa aradiklari seydi, sadece onlarin kelimesini
   kullanmiyordu.* Bu kalibi her turda ara.
2. **Aylik sarf cevap blogunda yoktu** (kedi/kopek/bebek). Rakam
   verimizde vardi. Cevap blogu Google'in ve AI motorlarinin
   alintiladigi parca — olctugumuz bir rakami oraya koymamak olcmemis
   gibi gorunmek demek.
3. **`/hesap/lot-hesaplama/`** acildi (saf matematik, komisyon
   kullanicidan).
4. **`/rehber/damatlik-kiralamak-mi-almak-mi/`** — kiralama fiyatini
   OLCMUYORUZ, yazi bunu ilk cumlede soyluyor; degeri karari kurmanin
   cercevesini vermek.
5. **Ceyiz basligi** "Ceyiz Masraflari" -> **"Ceyiz Ne Kadar Tutar?"**

### ACIK KALANLAR (siradaki tur)
- **temettu vergisi hesaplayici** (~4 gosterim). Stopaj orani birincil
  kaynaktan DOGRULANMADAN yazilmaz.
- **ipotek harci** (1 gosterim) — tapu sayfasina alt baslik olabilir.
- **kira geliri rehberi** — en buyuk kume ama hesaplayici sayfasi zaten
  siralaniyor; ayri rehber KANNIBALIZE edebilir. Once konum iyilessin.
- **Evcil hayvanda kalan tek kaynaklar:** kedi 2/8, kopek 3/7. Mama,
  kum, yatak, oyuncak ve tasma Petzzshop ile kapandi; kalan 5 kalem
  trafik/etki sirasiyla ikinci kaynaga tasinmali.
- **Bellona / Istikbal** — fiyat var ama kart eslesmesi kurulamadi;
  D&R'da ayni teshis elle bakilinca cozulmustu.

### ICERIK/GEO HAMLESI (2026-08-22)
Yavuz'un notu: Analytics'te **2 ChatGPT + 1 Gemini** yonlendirmesi var.
Bu, GEO hedefinin ilk kucuk sinyali. Bu turda iki ornek uzerinden
icerik standardi netlesti:

1. **YouTube'dan nasil para kazanilir?** Dogru konu. Ama yeni genel blog
   degil; mevcut `/hesap/youtube-gelir-hesaplama/` sayfasinin niyetini
   genisletmek daha dogruydu. Sayfa artik resmi YPP esiklerini, 2027-02-01
   degisikligini ve RPM belirsizligini ayni yerde veriyor. Kaynaklar:
   YouTube Help + Google Blog. KURAL: RPM yine uydurulmaz, kullanicidan
   alinir; sayfa tek gelir rakami basmaz.
2. **ParafPara / Chip-Para / Bonus nerelerde gecer?** Dogru konu ama
   "tum magaza listesi" elle yazilirsa hizla bayatlar. Bu yuzden
   `/rehber/kredi-karti-puanlari-nerede-gecer/` resmi kaynak rehberi
   olarak acildi: 1 puan = 1 TL mantigi, uye isyeri/kampanya/POS ayrimi,
   resmi canli kaynak baglantilari ve FAQ schema. KURAL: dinamik liste
   kopyalanmaz; bankanin canli listesine baglanilir, kampanya sarti
   okutulur.

Bu turda `rehber.py` yeni bir icerik tipi ogrendi: `kaynak_tipi: "resmi"`.
Olcumlu rehberler veri yoksa uretilmez; resmi kaynak rehberleri veri
istemeden uretilir ama gorunur kaynak + citation + FAQ tasimak zorundadir.
Rehber kunyesi de ayrildi: olcumlu rehberde olcum tarihi, resmi rehberde
kaynak kontrol tarihi gorunur.

SIRADAKI BENZER ADAYLAR:
- Banka puani serisi genisletilecekse "Worldpuan/Maximum/Nays/Hepsipay
  nerede gecer?" gibi sayfalar ancak resmi kaynak + canli liste baglantisi
  ile acilmali.
- "YouTube Shorts para kazanma", "TikTok Creator Fund Turkiye var mi?",
  "Instagram Reels para kazanma" gibi icerikler guncel resmi kaynak
  dogrulamasi ister; tahminle yazilmaz.
- GSC verisinden gelen kira/temettu/ipotek konulari hâlâ daha yakin para
  niyeti tasiyor; yeni sayfa acmadan once mevcut hesaplayiciyi
  cannibalize edip etmeyecegi kontrol edilmeli.

### AI-NATIVE URUN TURU (2026-08-22)

Onceki tur yalnizca Yavuz'un iki ornegine cevap verdi; bu tur 306 GSC
sorgusunun tamami urun niyetine gore incelendi. Sonuc: AI kullanicisi
yalnizca "fiyati ne" demiyor; **"butcem yeter mi", "aylik/yillik toplam
ne", "X kiside ne olur" ve "hangisi daha mantikli"** diye karar soruyor.
Site ham makale sayisini degil, olculmus veriden bu karar kaliplarini
cevaplayan araclari buyutecek.

Uygulananlar:
- **`/hesap/butcem-yeter-mi/`**: uc segmenti de bulunan, tahmini olmayan
  114 kalemi tek karar aracinda toplar. Butceyi ekonomik/orta/ust ortancayla
  karsilastirir; marka veya ozellik onerisi uydurmaz. Tarih, kaynak sayisi
  ve urun orneklemi sonucta gorunur.
- **Aylik kedi ve kopek rehberleri**: yalniz tekrar eden olculmus sarflari
  toplar. Veteriner, saglik ve diger olculmeyen giderler acikca haric;
  sonuc "tam maliyet" degil **olculmus alt sinir** olarak yayinlanir.
- **Bebegin aylik masrafi**: mevcut ilk-yil rehberine GSC sorgusunu
  karsilayan gorunur cevap + ayni metinli schema eklendi. Yalniz bez
  olculdugu icin mama, saglik, giyim, kres ve bakici haric tutulur.
- **1.000 kisilik dugun**: mevcut kisi basi olcumu 1.000 ile carpar;
  dogrulanmis teklif verisi olmadigi icin hayali hacim indirimi uygulamaz.
- `robots.txt`e **OAI-SearchBot** eklendi. OpenAI'nin yayinici dokumanina
  gore ChatGPT arama ozetleri/snippet'leri icin asil ilgili tarayici budur;
  GPTBot tek basina bu isi karsilamaz.
- `llms.txt`teki yanlis siniflandirma kapatildi: 23 formul/mevzuat araci
  ile 2 guncel veriye dayali arac artik ayri tanimlanir ve 25'inin tamami
  haritada yer alir.

GEO icin teknik karar: Google'in resmi AI Search dokumanlari ozel bir
"GEO schema", `llms.txt` veya AI metin dosyasi istemiyor. Standart SEO,
ham HTML'de gorunen benzersiz icerik, taranabilirlik, dogru ic link ve
gorunen metinle birebir uyumlu structured data esas. AI Mode'un query
fan-out davranisi nedeniyle her soru varyanti icin zayif sayfa acmak
yerine ayni niyetin cevabini tek guclu sayfada bolumlemek daha dogru.
FAQ schema gorunur soru-cevapla ayni kalir ama "sihirli GEO etiketi" veya
garantili rich result gibi ele alinmaz.

Siradaki urun rotasi:
1. **CTR turu:** defter, mikrodalga ve beyaz esya sayfalarinda yeni URL
   acmadan baslik/snippet ile cevap blogunu GSC verisiyle iyilestir.
2. **Otorite turu:** kira, hisse/borsa, tapu ve calisan kumelerinde mevcut
   araci sorgu dili + birincil kaynak + ic link bakimiyla guclendir.
3. **Yeni veri turu:** "buhar destekli firin ve induksiyonlu ocak fiyata
   deger mi?" gibi AI sorulari icin urun ozelligi alanlarini toplamadan
   karsilastirma yazisi acma. Ilk is fiyat kaydina ozellik/kapasite/enerji
   sinifi gibi karsilastirilabilir alanlar eklemek.
4. **Olcum turu:** ChatGPT yonlendirmelerini `utm_source=chatgpt.com`,
   Gemini ve Bing Webmaster AI Performance raporuyla sayfa bazinda izle;
   alinti alan sayfa kalibini veriyle cogalt.

### OLCUM: TEK KAYNAKLI KALEMLER (2026-08-09)
122 olculen kalemin **52'si (%43)** tek kaynakli:
arac 25 (yapisal ve dogru — uretici liste fiyati) · dugun 10 ·
**kedi 8/8** · **kopek 7/7** · bebek 2.


## ABD FIYAT KARSILASTIRMASI — DENENDI, SU AN YAPILAMIYOR (2026-08-09)
Yavuz: *"abd'de yasam maliyeti 2026 gibi bir hesaplama araci nasil olur?"*

**Cerceve yeniden kuruldu.** "ABD'de yasam maliyeti" icin kira/market/
ulasim rakamlari gerekir; bunlar ya Numbeo tipi KALABALIK KAYNAKLI
(beyan, olcum degil — bizim tanimimiza uymuyor) ya da uydurma olur.
Bunun yerine bize ait olabilecek soru: **ayni urun Turkiye'de kaca,
ABD'de kaca?** Zaten 122 kalemi olcuyoruz; ayni motorla ABD'de olcup
asgari ucrete oranlayabilirdik (TL/USD kuru icin TCMB EVDS'ye zaten
bagliyiz — resmi, tarihli, alintilanabilir).

**OLCULDU VE SU AN YAPILAMIYOR:**

| kaynak | robots | sonuc |
|---|---|---|
| amazon.com | **ONAY** | 16 urun karti geliyor ama **FIYAT YOK** — `a-offscreen` 0, `$X.XX` deseni 0. Captcha da yok. Muhtemelen ABD disi IP'ye fiyat sunulmuyor. |
| walmart.com | RET | — |
| bestbuy.com | RET | — |
| target.com | RET | — |

Yani uc buyuk perakendeci robots.txt ile kapali, Amazon ise fiyati
bizim IP'mize vermiyor. **Bu bir kod sorunu degil, erisim sorunu.**

**Ilerlemek icin gereken sey (bir sonraki tur degerlendirilir):**
- ABD cikisli bir istek yolu (workflow zaten GitHub runner'inda kosuyor
  ve o ABD'de olabilir — *duman testinde ayrica olculmeli*, ev
  baglantimizdan farkli davranabilir; bu tam olarak Akakce/Beymen'de
  yasadigimiz seyin tersi bir firsat).
- Ya da resmi ABD verisi: BLS "Average Price Data" gercek fiyat
  yayinliyor ama gida/enerji kalemleri icin — bizim urun listemizle
  ortusmuyor, AYRI BIR VERTIKAL olurdu.

**KDV/satis vergisi tuzagi (yapilirsa mutlaka):** ABD etiket fiyati
genelde satis vergisi HARIC, bizimki KDV DAHIL. Duzeltilmezse
karsilastirma sistematik olarak yanlis cikar — ofix'i elemekle ayni
sebep.


## TEK KAYNAK BOSLUGU KAPATILDI (2026-08-09)
Yavuz: *"sen bugunun tum islerini tek seferde hallet."*
Site geneli tek kaynakli kalem orani **%43 -> %34**.

### petzzshop — kedi/kopek (10 kalem)
Kedi **8/8**, kopek **7/7** tek kaynakliydi (hepsi Amazon) ve sayfalarda
*"1 bagimsiz kaynak"* yaziyordu — **kendi cok kaynak kuralimizla acikca
celisiyordu.** Simdi kedi 2/8, kopek 3/7.
`kedi 5.388 -> 6.351` · `kopek 3.895 -> 4.624`

Segment farki bekleniyor ve mesru (kedi yatagi Amazon 390 / petzz
2.400) ama **urun ADLARI tek tek okundu**: Ferplast Relax, Lepus
Comfort — gercek kedi yatagi, aksesuar degil.

**Ad filtresi bir kalemi KURTARDI, birini ELEDI:**
- `tasima-cantasi` ✓ ayni kategoride boyun tasmasi (155 TL) ve kafes
  (19.534 TL) vardi; `ad_gerekli: tasima` + `ad_dislama: kafes|tasma`
  ile **15 gercek canta** kaldi.
- `kedi-tuvaleti` ✗ kum torbasi (113), kedi kapisi (483), tuvalet
  (2.052) karisik. Filtre 24 urunun **23'unu eledi ve UYARI verdi**;
  geriye 1 urun kaldi — guvenilir medyan icin yetmez, alinmadi.
  *Filtre uyarisi tam bu is icin yazilmisti ve isini yapti.*

### Bellona + Istikbal — onceki KIRMIZI teshis YANLISTI
`kaynak_tara` *"fiyat kart disinda, eslesme kurulamaz"* demisti.
**Sezgisel tarayicinin yakaladigi ilk fiyat dugumu URUN DEGIL, kenar
cubugundaki FIYAT FILTRESI menusuydu.** Gercek fiyat
`.showcase-price-new`, kart `.showcase` — ikisi de ayni sablonu
kullaniyor (ayni yazilim evi).
**Bu, D&R'da yasananin aynisi. KIRMIZI "bak" demek, "birak" demek
degil** — ozellikle hedef site elle secilmisse.

**EN DEGERLI BULGU — YATAK (SILTE) UST SEGMENTI:**

| kaynak | medyan |
|---|---|
| Trendyol | 1.682 |
| Amazon | 2.799 |
| Istikbal | 12.369 |
| Bellona | 12.999 |

Ust segment **3.816 -> 12.909**. Gercek yatak fiyati endeksimizde
**hic gorunmuyordu**; pazaryerleri ucuz silte satiyor. Urun adlari
dogrulandi (Hybrid Sleep, Detox Prime).

**EV-KURMADA ARTIK TEK KAYNAKLI KALEM YOK: 0/42.**
`orta 383.814 -> 369.371` · `UST 600.942` · **9 bagimsiz site**.


## HESAPLAYICILAR 21 -> 24: RAKIP TARAMASI (2026-08-09)
Yavuz: *"rakiplerde olup bizde olmayan ya da gercekten tutabilecek
hesaplayicilari tespit edip ekleyelim."*

**Tahmin edilmedi, rakip listeleri CEKILDI:** hesapsonuc **275**,
yenibirhesap **253**, hesaplamaci **29** hesaplayici. Cogu kapsam disi
(burc, gebelik, sinav puani, vucut kitle) — marka bir **maliyet**
sitesi olarak kaliyoruz; hesapsonuc'un *"juno lilith hesaplama"* ile
seyreldigi yer orasi.

### ONCE MEVCUTLARI KONTROL ETTIM — iki "eksik" eksik degildi
- **"KDV matrah hesaplama"** (5 gosterim): KDV hesaplayicimiz zaten
  dahil/haric ceviriyor ve SSS'sinde anlatiyor. *Yeni sayfa degil,
  kelime meselesi.*
- **"asgari ucret hesaplama"**: maas hesaplayicisinin SSS'sinde
  kapsaniyor; ayri sayfa **kannibalize** ederdi.

*Yeni sayfa acmadan once mevcut sayfanin o isi yapip yapmadigina
bakmak, bu turda iki gereksiz sayfayi engelledi.*

### EKLENEN 3 — ucu de saf matematik, parametre riski sifir
| sayfa | neden guvenli |
|---|---|
| `/hesap/yakit-maliyeti-hesaplama/` | litre fiyati KULLANICIDAN — akaryakit gunluk degisiyor, il il farkli |
| `/hesap/boya-hesaplama/` | verim (m²/litre) kullanicidan — kutuda yazar, markaya gore degisir |
| `/hesap/basa-bas-noktasi-hesaplama/` | hicbir dis parametre yok |

**Her ucunde de "uydurma cevap verme" kurali uygulandi:**
- Boyada litre fiyati bos birakilirsa **tutar `null` doner**, 0 TL degil.
- Basa basta satis fiyati degisken maliyetin altindaysa **basa bas
  noktasi YOKTUR** — uydurma adet ya da "sonsuz" yerine acikca
  soyluyor ve gereken en dusuk fiyati veriyor (kart borcu
  hesaplayicisindaki kararin aynisi).
- Boyada kapi/pencere **dusulmuyor**: dusmek icin uydurma bir katsayi
  gerekirdi. Iscilik dahil degil ve sayfada yaziyor.

### AYNI ONDALIK HATASINI TEKRAR URETTIM
Ilk halde *"32.4 litre"*, *"%62.5"* yaziyordu — noktali ondalik.
**Bunu 2 Agustos'ta site genelinde duzeltmistim** (`_kat()` yardimcisi)
ama yeni hesaplayicilarda geri geldi, cunku o duzeltme Python
tarafindaydi, bunlar JS ciktisi. JS tarafinda ayri bir yardimciyla
duzeltildi.
**Ders: bir bicimlendirme kurali iki ayri dilde uygulanıyorsa iki
yerde de korunmasi gerekiyor; birini duzeltmek otekini kapsamiyor.**


## Gelir Modeli (sıralı)
1. Reklam (tüketici tarafı ücretsiz)
2. Affiliate (gerçek ürün linkleri — sadece gerçek veriyle mümkün)
3. Pro rapor / araç aboneliği (ustalar, müteahhitler, düğün firmaları)

## GEO Gereksinimleri (her sayfada)
- İlk 40-60 kelimede net, alıntılanabilir cevap bloğu.
- schema.org yapılandırılmış veri, güncelleme tarihi görünür.
- Soru formatında başlıklar ("2026'da İstanbul'da düğün kaça mal olur?").
- robots.txt AI bot'larına açık (GPTBot vb. engellenmez).
- ✅ **ÇÖZÜLDÜ (2026-07-25). Cloudflare'in robots.txt enjeksiyonu
  kapatıldı, canlı robots.txt artık depodaki dosyayla BİREBİR AYNI.**
  Doğrulandı: hiç `Disallow` yok, `Content-Signal` satırı yok; GPTBot,
  ClaudeBot, PerplexityBot ve Googlebot canlı sayfaya **HTTP 200**
  alıyor; www üzerinden de temiz. Yerel sitemap şu an **185 URL** içeriyor.
  Kapatma yolu (ileride tekrar gerekirse): Cloudflare Dashboard → zone →
  **AI Crawl Control → Robots.txt → "Disable robots.txt configuration"**
  (varsayılan "Content signals policy" idi).
  **Aşağıdaki kayıt sorunun ne olduğunu ve nasıl teşhis edildiğini
  belgeliyor — tarihî not, artık aktif sorun DEĞİL:**
- 📌 **(ÇÖZÜLDÜ, tarihî kayıt) Cloudflare bizim robots.txt'imizin
  ÜSTÜNE kendi "Managed content" bloğunu ENJEKTE ediyordu ve tam olarak
  hedeflediğimiz botları ENGELLİYORDU.** Canlı
  `https://maliyetine.com.tr/robots.txt` çıktısında:
  - `User-agent: ClaudeBot → Disallow: /`
  - `User-agent: GPTBot → Disallow: /`
  - `User-agent: Google-Extended → Disallow: /`
  - `CCBot`, `Applebot-Extended`, `Amazonbot`, `Bytespider`,
    `meta-externalagent` → hepsi `Disallow: /`
  - `Content-Signal: search=yes,ai-train=no,use=reference` (AB Telif
    Direktifi Madde 4 kapsamında hukuki hak rezervasyonu olarak
    ifade ediliyor).
  **Bu, projenin TEMEL STRATEJİSİNİ (AI motorlarının alıntıladığı kaynak
  olmak) doğrudan baltalıyor.** Cloudflare'in "Content Signals Policy"
  özelliği yeni zone'larda varsayılan olarak açık geliyor.
  - **Hafifletici:** WAF seviyesinde gerçek blok YOK — GPTBot/ClaudeBot/
    PerplexityBot/CCBot User-Agent'leriyle test edildi, hepsi **HTTP 200**
    alıyor. Ayrıca bizim `Allow: /` bloğumuz Cloudflare'inkinden SONRA
    geliyor; RFC 9309'a göre aynı user-agent'ın grupları birleştirilir ve
    eşit uzunluklu çakışmada "least restrictive" (Allow) kazanır.
    **Ama bu yoruma bağlı ve garanti değil** — GPTBot ve ClaudeBot
    robots.txt'e gerçekten uyan botlardır.
  - **KESİN TEŞHİS (2026-07-25):** `maliyetine.yavuzkara-1907.workers.dev/robots.txt`
    **TEMİZ** (Cloudflare bloğu yok), ama custom domain üzerinden gelen
    istekte blok VAR (her iki edge IP'de ve www'da). `cf-cache-status`
    header'ı hiç yok → enjeksiyon her istekte DİNAMİK yapılıyor, yani
    önbellek temizlemek İŞE YARAMAZ. **Depodaki `robots.txt` dosyamız
    doğru; sorun tamamen zone ayarında.** Cloudflare topluluk forumunda
    doğrulanmış: **Worker ile robots.txt'i override etmek bu enjeksiyonu
    engellemiyor** — tek çözüm zone ayarını kapatmak.
  - **YAVUZ'UN YAPMASI GEREKEN (net yol):** Cloudflare Dashboard →
    `maliyetine.com.tr` → sol menü **AI Crawl Control** → **Robots.txt**
    sekmesi → ayar şu an "Content signals policy" seçili, bunu
    **"Disable robots.txt configuration"** yap. (Ücretsiz planda bu bölüm
    `AI Crawl Control | Robots.txt` altındadır.) Alternatif yol:
    **Security → Settings** → "Instruct AI bot traffic with robots.txt".
    Sadece politika metnini gizlemek isterse: zone Overview →
    "Control AI Crawlers" → "Display Content Signals Policy" işaretini
    kaldır — ama bu bot Disallow'larını KALDIRMAZ, tam çözüm için
    yukarıdaki "Disable" seçeneği gerekir.
  - Kapatıldıktan sonra doğrulama: `curl -s https://maliyetine.com.tr/robots.txt`
    çıktısında "Cloudflare Managed content" bloğu OLMAMALI, yalnızca
    depodaki 7 `Allow: /` girdisi ve Sitemap satırı görünmeli.

## İçerik SEO Stratejisi (2026-07-25)
- **Ana prensip:** Maliyeti Ne? klasik blog sitesi değil; veri ürünü. İçerik
  SEO'su, genel tavsiye yazılarıyla değil, Google'ın "helpful, reliable,
  people-first content" çizgisine uygun şekilde **özgün veri + yöntem +
  karar yardımcısı** üretmek için yapılır. Kaynak notu:
  Google Search Central "Helpful content" ve "SEO Starter Guide".
- **Kazanılacak sorgu tipi:** "2026'da X kaça mal olur?", "X fiyatları
  2026", "X maliyeti hesaplama", "ekonomik/orta/lüks X bütçesi",
  "İstanbul'da X maliyeti", "X listesi fiyatları". Her sayfa tek bir
  gerçek kullanıcı sorusunu cevaplar.
- **İçerik mimarisi:** Her vertikal bir hub üçlüsüyle başlar:
  `/vertikal/` endeks, `/vertikal/hesaplayici/`, `/vertikal/metodoloji/`.
  Bunlara sonra iki tür destek sayfası bağlanır:
  1. **Kalem sayfaları:** `/dugun/gelinlik-fiyatlari/`,
     `/dugun/dugun-salonu-fiyatlari/`,
     `/ev-kurma/buzdolabi-fiyatlari/` gibi. Yalnızca gerçek veri veya
     açıkça etiketlenmiş tahmini veri varsa açılır.
  2. **Senaryo/listeler:** "150 kişilik düğün bütçesi", "ev kurma eşya
     listesi", "ekonomik ev kurma maliyeti", "yemekli vs kokteyl düğün
     salonu maliyeti" gibi hesaplayıcıya bağlanan rehberler.
- **Sayfa şablonu (her içerik sayfası):**
  - İlk 40-60 kelimede direkt cevap: rakam, tarih, segment, örneklem ve
    kaynak sayısı.
  - H1 soru formatında, title kısa ve tıklanabilir; abartılı vaat yok.
  - "Bu rakama neler dahil?", "Neler dahil değil?", "Nasıl hesaplandı?",
    "Segmentlere göre fiyat", "Kaynaklar ve güncelleme tarihi" blokları.
  - En az 3 iç link: ana endeks, hesaplayıcı, metodoloji; uygun olduğunda
    ilgili kalem/senaryo sayfası.
  - Görünür güncelleme tarihi; veri gerçekten değişmediyse sadece tarihi
    tazelemek YOK.
  - Kaynak, derleme tarihi, örneklem büyüklüğü ve tahmini/gerçek ayrımı
    metinde görünür kalır.
- **Programmatic SEO kırmızı çizgisi:** İnce/tekrarlı sayfa basılmaz.
  Şehir sayfası yalnızca şehir verisi varsa açılır; yoksa "İstanbul"
  veya "Türkiye geneli" diye dürüst yazılır. Kalem sayfası, ana sayfadaki
  satırı kopyalamaz; trend, dahil/dahil değil, segment açıklaması ve
  hesaplayıcı bağlantısıyla ek değer üretir.
- **E-E-A-T / güven sinyali:** Maliyeti Ne?'nin uzmanlığı "piyasa verisini
  toplama ve metodoloji"dir. Her sayfada "kim/how/why" net olmalı:
  yayıncı Maliyeti Ne?, veri nasıl toplandı, AI varsa rafineri rolünde
  kullanıldı, nihai rakamlar gerçek kaynak/tahmini ayrımıyla verildi.
- **İlk içerik kümeleri:**
  - Düğün: düğün maliyeti 2026, İstanbul düğün maliyeti, düğün salonu
    kişi başı fiyatı, yemekli/kokteyl farkı, gelinlik fiyatları,
    damatlık fiyatları, alyans fiyatları, altın bilezik fiyatı, davetiye,
    nikah şekeri, fotoğrafçı/organizasyon gerçek ölçüm notları,
    orkestra/DJ ve nikah işlemleri tahmini notları.
  - Ev kurma: ev kurma maliyeti 2026, sıfırdan ev eşyası maliyeti,
    çeyiz/eşya listesi fiyatları, beyaz eşya bütçesi, mobilya bütçesi,
    yatak odası bütçesi, mutfak ürünleri, buzdolabı, çamaşır makinesi,
    koltuk takımı, gardırop, televizyon.
- **Ölçüm:** Google Search Console'da sorgu bazında izlenecekler:
  gösterim, tıklama, ortalama konum, hangi long-tail soruların geldiği,
  hangi sayfaların indekslenmediği. AI görünürlüğü için ayrıca manuel
  "Maliyeti Ne? verilerine göre..." alıntı kontrolleri yapılır.

## Altyapı Kararları (KESİN)
- Domain: **maliyetine.com.tr** — alındı, DNS Cloudflare'de aktif.
- Hosting: **statik site + Cloudflare Worker**. Backend YOK. Eski
  "Cloudflare Pages" notları tarihî kayıt; canlı dağıtım Worker üzerinden.
- WordPress KULLANILMAYACAK.
- Hesaplayıcılar tarayıcıda JavaScript ile çalışır.
- Kod deposu: GitHub `maliyetine` (private).
- Otomasyon: GitHub Actions (ayın 5'i ve 20'si).
- `www` → kök domain 301 yönlendirmesi Cloudflare Redirect Rules ile
  **tamamlandı** (2026-08-22). Eski hatalı kural wildcard alanına expression
  yazdığı için çalışmıyordu; canlı doğrulamada `www` 301, kök HTTPS 200.
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
- **DETAY SAYFASI KATMANI (2026-07-25 eklendi, `detay_urunler()`).** Üç
  katmandan bağımsız, ayrı bir yöntem: kaynakta `detay:` bloğu varsa
  motor üç katmana HİÇ düşmez, bunun yerine kategori sayfasından detay
  linklerini toplar ve **her detay sayfasından regex ile tanımlı fiyatı**
  çeker. Alanlar: `link_secici`, `fiyat_regex` (1 yakalama grubu),
  `en_fazla_detay` (nazik kazıma sınırı; detaylar arası `bekleme_sn`
  kadar beklenir, her detay URL'i ayrıca robots.txt'ten geçer).
  - **Neden gerekli:** hizmet kalemlerinde kategori kartı yalnızca
    "başlangıç fiyatı" gösterir — mekanın EN DÜŞÜK seçeneği, ne ölçtüğü
    belirsiz. Gerçek tanımlı fiyat ("Yemekli kişi başı", "Kokteyl kişi
    başı") detay sayfasında ayrı ayrı yazıyor.
  - **Aynı kategori sayfası, farklı regex ile İKİ AYRI kalemi besler**
    (bkz. `salon-yemekli` / `salon-kokteyl`). Regex eşleşmezse o mekan
    sessizce atlanır (o seçeneği sunmuyor demektir, hata değil).
  - Gerçek DüğünBuketi'ne karşı doğrulandı: yemekli 11 mekan (orta
    medyan 1.100 TL/kişi), kokteyl 10 mekan (orta medyan 800 TL/kişi).
  - **Bu katman diğer hizmet kalemleri için de yol açıyor** — fotoğrafçı,
    organizasyon vb. aynı desende çözülebilir.
- **Sağlık kontrolü zorunlu:** bir kaynak normalde ~200 ürün dönerken
  ay içinde 3 ürün dönerse SESSİZCE devam etme, uyarı ver ve o ayki
  veriyi karantinaya al. Geçmiş `kaynak_gecmisi.json`'da site-grubu
  bazında (`vertikal/kalem/site`) tutulur.
- **Çapraz doğrulama (ÇOK KAYNAK KURALI):** aynı (vertikal, kalem) için
  ≥2 sağlıklı bağımsız site varsa genel medyanları karşılaştırılır; fark
  %30'u aşarsa uyarı loglanır ve `{kalem}_capraz-dogrulama_{tarih}.json`
  yazılır. Resmî EVDS/TÜFE serisi trend doğrulama katmanı olarak var; TL
  fiyatın yerine geçmez.
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
> **GÜNCELLEME (2026-07-25): Bu bölüm ARTIK HER ZAMAN GEÇERLİ DEĞİL.**
> Claude Code Yavuz'un MacBook'unda doğrudan terminalde çalıştığında
> (bu oturumda olduğu gibi, cwd `/Users/yavuzkara/Desktop/maliyetine`)
> hedef sitelere GERÇEK istek atılabiliyor — robots.txt taraması, gerçek
> kazıma ve `python3 motor.py` buradan çalıştırıldı ve gerçek veri
> döndürdü. Aşağıdaki kısıt, proxy'li/izole bir sandbox ortamında
> çalışıldığında geçerli. **Yeni bir kaynak araştırılacaksa önce basit
> bir `requests.get` ile network erişimi test edilsin** — varsayarak
> Yavuz'un elle çalıştırmasını beklemeye gerek yok.
- Claude Code'un (izole sandbox) çalıştığı ortamın proxy politikası, hedef
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

## Teknik Durum (tarihî ayrıntı; güncel durum yukarıda)
> Bu bölüm ilk kazıma/motor kuruluşunun ayrıntılı günlüğüdür. İçinde o
> gün doğru olan ama sonra kapanmış durumlar var. Güncel aksiyon için
> **GÜNCEL SON DURUM** ve **Yapılacaklar** bölümünü esas al.

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
  - **TARİHÎ NOT:** Bu noktada "fotoğrafçı" sıfır aktif kaynaklıydı
    (Armut da ayrı bir teşhiste kesin bırakılmıştı). 2026-07-26'da
    `dugun.com` İstanbul tablosuyla gerçek kaynağa taşındı. "gelinlik"
    kalemi bu teşhisten etkilenmedi.
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

## Modüller (tarihî kayıt; güncel özet yukarıda)
> Bu bölüm ilk kuruluş günlüğüdür. "Ne yapmalıyım?" sorusunun cevabı için
> önce **GÜNCEL SON DURUM** ve **Yapılacaklar** bölümüne bak.

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
     teklif-al modeli — kazıma hatası değil). **TARİHÎ NOT:** o gün
     "fotoğrafçı" sıfır aktif kaynaklıydı; 2026-07-26'da `dugun.com`
     İstanbul tablosuyla gerçek kaynağa taşındı.
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
   - **ÇÖZÜLDÜ (2026-07-25): artık GERÇEK VERİ ile yayında.** Yavuz'un
     yerelinde `python3 motor.py` (13 kaynak-grubu, 13 sağlıklı) →
     `scraper/veri/` commit → `agrega.py` + `sayfa_uret.py` → commit
     zinciri tamamlandı. Bu ilk gerçek çalıştırmada `agrega.py`'nin
     çapraz-doğrulama şema uyumsuzluğu bulunup düzeltildi (bkz.
     Yapılacaklar'daki ilgili madde). `/dugun/` artık "414.549 TL" gibi
     gerçek, kaynaklı bir toplam gösteriyor; Yavuz doğruladı.
   - **DÜZELTİLDİ (2026-07-25) — "N bağımsız kaynak" sayısı YANLIŞ
     hesaplanıyordu (dürüstlük bug'ı).** Cevap bloğu, kalem başına
     `kaynak_sayisi` alanlarını TOPLUYORDU. Aynı site birden fazla kalemi
     besleyince her kalemde tekrar sayılıyordu: düğün "20 bağımsız
     kaynak" diyordu ama gerçekte 10 site vardı; ev-kurma ise "42
     bağımsız kaynak" diyecekti — oysa 42 kalemin HEPSİ tek bir siteden
     (Trendyol) geliyor. Bu, projenin en temel güven iddiasını
     (ÇOK KAYNAK KURALI) olduğundan güçlü gösteriyordu. Düzeltme:
     `bagimsiz_siteler()` benzersiz `site` değerlerini sayıyor. Düğün
     artık doğru şekilde "10", ev-kurma "1" diyor. 3 regresyon testiyle
     kilitlendi.
   - **Yeni: tek kaynak uyarısı.** Bir vertikal tek siteden besleniyorsa
     endeks sayfasının en üstünde görünür bir uyarı kutusu çıkıyor
     ("Tek kaynak, o sitenin fiyat politikasını yansıtır — piyasanın
     tamamını değil"). ÇOK KAYNAK KURALI'nın karşılanmadığı gizlenmiyor,
     sayfada açıkça söyleniyor (dürüstlük ürünün parçası ilkesi).
     Ev-kurma'da şu an görünüyor, düğün'de görünmüyor (10 kaynak).
   - **✅ EV KURMA ÜÇLÜSÜ EKLENDİ (2026-07-25):** `/ev-kurma/` (endeks,
     `sayfa_uret.py --vertikal ev-kurma` ile üretiliyor),
     `/ev-kurma/hesaplayici/` (42 kalem, 7 grup halinde, tümünü seç/kaldır
     düğmeleri), `/ev-kurma/metodoloji/`. Ana sayfaya ve `sitemap.xml`'e
     eklendi. Düğün'den yapısal farkları: davetli/ölçek girdisi YOK
     (tüm kalemler "sabit" birimli), kalemler `grup` alanıyla
     kategorilere ayrılıyor (Beyaz eşya, Mobilya, Yatak odası,
     Elektronik, Küçük ev aleti, Mutfak, Tekstil), ve **hiç tahmini
     kalem yok** — 42 kalemin tamamı gerçek kaynaklı, bu yüzden cevap
     metni "tamamı ... bağımsız kaynaktan derlenen" diyor ve tahmini
     kırılımı hiç kurmuyor (ayrı kod yolu, testle kilitli).
4. **Metodoloji sayfası + schema.org işaretlemesi** — ✅ **Tamamlandı
   (2026-07-24, ev-kurma 2026-07-25).** `/dugun/metodoloji/` ve
   `/ev-kurma/metodoloji/` — kaynak türleri, çapraz doğrulama
   kuralı, segment tanımı (persentil), sağlık kontrolü, nazik kazıma
   ilkeleri, kapsanmayan kalemler notu. Statik (elle yazıldı, veriye bağımlı
   değil) - schema.org işaretlemesi endeks sayfalarında (sayfa_uret.py)
   yapıldı. Ev-kurma metodolojisi ayrıca "tek kaynak" sınırını ve
   "neyi ölçmüyoruz" bölümünü (konut, tadilat/işçilik, nakliye, sarf
   malzemesi; her kalemden 1 adet varsayımı) açıkça anlatıyor.
   **GÜNCELLEME (2026-07-25):** endeks sayfalarının JSON-LD bloğu GEO için
   zenginleştirildi: `Organization`, `BreadcrumbList`, genişletilmiş
   `FAQPage`, indirilebilir JSON'a bakan `Dataset.distribution`, `keywords`,
   `spatialCoverage`, `measurementTechnique` ve `variableMeasured` alanları
   eklendi. Kritik doğruluk notu: ek FAQ cevapları yalnızca gerçekten var
   olan segment medyanlarını yazar; eksik segmentte `genel_medyan` fallback'i
   "lüks/ekonomik" gibi gösterilmez. Bu bug ev-kurma `Televizyon (4K)`
   örneğinde yakalandı ve regresyon testiyle kilitlendi. Doğrulama:
   Python 105/105, JS 19/19, JSON-LD parse OK, iç link kontrolü OK,
   `dugun/index.html` ve `ev-kurma/index.html` jeneratör çıktısıyla birebir.
   **İÇERİK SEO NOTU (2026-07-25):** Google Search Central ilkeleri baz
   alınarak ayrı "İçerik SEO Stratejisi" bölümü eklendi. Odak: özgün veri,
   metodoloji, kalem/senaryo sayfaları, ince programmatic SEO'dan kaçınma.
   **İÇERİK SEO UYGULANDI (2026-07-25):** `/dugun/` ve `/ev-kurma/`
   endekslerine ham HTML'de görünen içerik blokları eklendi: dahil olanlar,
   dahil olmayanlar, en yüksek maliyet kalemleri, segment açıklaması ve
   ilgili fiyat sayfaları. İlk 9 kalem sayfası üretildi:
   düğün (`gelinlik-fiyatlari`, `damatlik-fiyatlari`,
   `alyans-fiyatlari`, `dugun-salonu-fiyatlari`) ve ev-kurma
   (`buzdolabi-fiyatlari`, `camasir-makinesi-fiyatlari`,
   `koltuk-takimi-fiyatlari`, `gardirop-fiyatlari`,
   `televizyon-fiyatlari`). `sitemap.xml` 16 URL'ye çıktı. Aylık
   workflow artık bu sayfaları ve sitemap'i de commit eder.
   **Dürüstlük düzeltmesi:** 0 ürün döndüren aday kaynaklar artık
   "bağımsız kaynak" sayısına dahil edilmiyor; düğün ana cevap bloğu bu
   yüzden 10 değil 5 çalışan kaynağı gösteriyor. Doğrulama:
   Python 110/110, JS 19/19, 16 sayfada JSON-LD parse OK, iç link OK.
5. **Yayın** — ✅ Canlıda Cloudflare **Worker** üzerinden statik dosyalar
   servis ediliyor. Eski Pages kurulum adımları tarihî kayıt; bugün
   bakılacak yer Worker/Cloudflare Redirect Rules tarafı. `www` → kök domain
   301 yönlendirmesi 2026-08-22'de düzeltildi ve canlıda doğrulandı.
6. **Aylık otomasyon** — ✅ **Tamamlandı (2026-07-24), sonra ayda iki kez
   çalışacak şekilde güncellendi.**
   `.github/workflows/aylik-veri-guncelleme.yml`: `python motor.py` →
   `python agrega.py` → `python sayfa_uret.py` → değişiklik varsa commit+push.
   **2026-07-25'te ev-kurma eklendi:** agrega+sayfa_uret adımı artık
   `for vertikal in dugun ev-kurma` döngüsüyle her iki vertikali de
   işliyor, commit'e `ev-kurma/` dizini de dahil.
   Tetikleyiciler: cron `0 6 5,20 * *` + `workflow_dispatch` (elle
   tetikleme).
   **DÜZELTME (2026-07-25):** eskiden cronun ayrı bir `main` dalı
   beklediği sanılmıştı — bu YANLIŞ. Repoda `main` diye ayrı bir dal
   YOK; **default branch zaten `claude/new-session-csygpf`**
   (`origin/HEAD` bunu gösteriyor). Yani cron ateşlenecek durumda.
   Not: bu branch adı bir üretim dalı için tuhaf; Yavuz istediğinde
   GitHub'dan `main` olarak yeniden adlandırılabilir; Cloudflare deploy /
   default branch ayarı da o zaman güncellenmeli.
   **Kritik düzeltme:** `scraper/kaynak_gecmisi.json` artık
   `.gitignore`'da DEĞİL — GitHub Actions runner'ları her seferinde
   sıfırdan başladığı için, bu dosya commit edilmezse `saglik_kontrolu()`
   hiçbir zaman gerçek bir geçmiş biriktiremez, her ay "ilk çalıştırma"
   sanıp anomali tespiti hiç çalışmazdı. Workflow bu dosyayı da commit
   ediyor. Ayrıca `/sitemap.xml` eklendi (robots.txt zaten ona işaret
   ediyordu ama dosya yoktu).
7. **Fiyat geçmişi** — ✅ sayfalarda görünmeye başladı; daha uzun seri
   biriktikçe yıllık karşılaştırma ve basın malzemesi güçlenecek.

## Yapılacaklar (güncel, 2026-08-22)
Tarihî tamamlanan işler yukarıdaki günlükte duruyor. Bu liste yalnızca
bugün gerçekten iş açan maddeleri taşımalı; biten iş burada kalmasın.

- [ ] **301 sonrası Search Console kontrolü.** Cloudflare `www` → kök domain
      redirect 2026-08-22'de düzeltildi ve canlı HTTP ile doğrulandı. 7-14
      gün sonra GSC sayfa tablosunda `www` gösterim/tık payı azalıyor mu
      bakılacak.
- [ ] **Search Console içerik turu.** 2026-08-22 export'ta en büyük kümeler:
      kira gelir vergisi (254 gösterim), damatlık/gelinlik (229),
      hisse/borsa maliyet (171), tapu/ipotek (148), temettü (83).
      Yeni sayfa açmadan önce mevcut sayfanın niyeti karşılayıp karşılamadığı
      ve cannibalization riski kontrol edilecek.
- [ ] **Yeni sayfa açmadan önce cannibalization kontrolü.** KDV matrah ve
      asgari ücret örneğinde olduğu gibi, bazı "eksikler" mevcut sayfanın
      kelime eksiği olabilir. Yeni sayfa ancak ayrı niyet varsa açılır.
- [ ] **Tek kaynaklı kalem raporu çıkar.** EV-kurma 0/42 tek kaynaklı hale
      geldi; kedi/kopek kısmen kapandı. Kalan tek kaynaklı kalemler veri
      dosyasından ölçülüp en yüksek trafik/etki sırasıyla kapatılmalı.
- [ ] **Düğünde kalan tahmini iki kalemi kapat.** `nikah-islemleri` için
      belediye/resmî tarife; `orkestra-dj` için ayrı kalem mi salon
      paketinin parçası mı önce metodolojik karar. Kaynak bulunmadan
      "gerçek" etiketi yok.
- [ ] **Sosyal yayın kararını netleştir.** X/Bluesky secret'ları eklenirse
      mevcut otomasyon gönderir. Facebook/Instagram için önce görsel kart
      mantığı korunmalı; Instagram düz metin/link formatı değil.
- [ ] **Marka koruması.** Türk Patent başvurusu ve yakın domain varyantları
      ileride yapılacak; teknik değil ama marka büyüdükçe ertelenmemeli.

## Çalışma Şekli
- Strateji claude.ai sohbetinde, inşaat Claude Code'da.
- Her oturum TEK modüle odaklanır.
- Oturum sonunda "GÜNCEL SON DURUM" ve "Yapılacaklar" güncellenir; uzun
  tarihî bölümlere yalnızca gerçekten yeni ders varsa ek yapılır.
