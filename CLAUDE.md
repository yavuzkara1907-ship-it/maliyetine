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
- Fiyat verisi ASLA LLM'den üretilmez / LLM'e sorulmaz. Pazarlıksız.
  İhlali projenin varlık sebebini yok eder.
- Kaynak: gerçek e-ticaret/ilan/karşılaştırma sitelerinden kazıma
  (robots.txt'e ve rate-limit'e saygılı) + gerektiğinde insan teyidi.
- AI'ın rolü: kaynak değil RAFİNERİ — temizleme, kategorize etme,
  aykırı değer ayıklama, özetleme.
- Yayınlanan her rakamın yanında: kaynak, derleme tarihi, örneklem
  büyüklüğü ("14 Temmuz'da 2.340 üründen derlendi").
- Metodoloji sayfası zorunlu. Güven = tek ürün. Rakip çöp sitelerden
  tek farkımız bu.

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

## Teknik Durum
- GitHub repo `maliyetine` oluşturuldu.
- **Kazıma motoru v0.4**: ÇOK KAYNAK KURALI'na göre site-bazlı gruplama +
  çapraz doğrulama eklendi.
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
  - `scraper/test_motor.py`: 35 test, hepsi PASS. Yeni testler:
    aynı-site birleştirme, çapraz doğrulama (uyarı üretme/üretmeme,
    sağlıksız kaynağı dışlama, kalem başına ayrı raporlama), ve
    bilgilendirici bir "kapsam raporu" testi (hangi kalemler hâlâ tek
    kaynaklı, stdout'a basar, başarısız olmaz).
  - `python motor.py --cikti /tmp/...` ile gerçek yaml'a karşı tekrar
    uçtan uca çalıştırıldı: 5 Akakçe gelinlik girdisi doğru şekilde tek
    "akakce" grubuna birleşti (kaynak_adlari listesinde 5 ad görünüyor),
    4 kaynak-grubu işlendi, çökme yok, exit 0. Sandbox network kısıtı
    yüzünden gerçek ürün gelmedi (bkz. yukarıdaki not).
  - `scraper/robots_kontrol.py` korunuyor — Yavuz'un yerelinde tekil URL
    hızlı kontrolü için.
- **Yavuz'un yerelinde robots.txt kontrolü yapıldı (2026-07-23)** —
  `robots_kontrol.py` gerçek sonuç döndürdü (bu sandbox'tan yapılamayan
  tek adımdı). Sonuçlara göre `kaynaklar.yaml` güncellendi:
  - **ONAY (aktif: true yapıldı):** Trendyol (gelinlik), Armut (fotoğrafçı
    fiyatları — ama "fiyatları" sayfası tek agregat ortalama gösteriyor
    olabilir, ilk gerçek çalıştırmada 0/az ürün dönerse bu şüphe
    doğrulanmış olur), Ramsey (damatlık, marka mağazası), Atasay (alyans,
    marka mağazası).
  - **RET (durum: reddedildi, aktif kalmayacak):** Hepsiburada (gelinlik),
    Dolap (gelinlik ikinci el), DüğünBuketi'nin 3 sayfası da (gelinlik
    moda evleri, düğün mekanları/salon, fotoğrafçı) — hepsi robots.txt
    tarafından engelleniyor, KULLANILAMAZ.
  - **Sonuç — kapsam durumu (bu sandbox'ın test_motor.py kapsam raporundan):**
    alyans (akakce+atasay, 2 aktif) OK, damatlik (akakce+ramsey, 2 aktif)
    OK, gelinlik (akakce+trendyol, 2 aktif) OK, fotografci artık SADECE
    armut aktif (dugunbuketi RET oldu — tek kaynağa düştü, ikincisi
    aranmalı), **salon artık HİÇBİR aktif kaynağı yok** (tek adayı
    dugunbuketi RET çıktı) — yeni kaynak bulunması gerekiyor,
    gelin-ayakkabısı hâlâ tek kaynaklı (akakce).
  - CSS seçiciler henüz hiçbir yeni kaynak için girilmedi (Ramsey,
    Atasay, Trendyol, Armut) — motor JSON-LD/microdata katmanıyla
    otomatik çözmeyi deneyecek, bulamazsa sağlık kontrolü karantinaya
    alacak. Yavuz'un ilk gerçek `python motor.py` çalıştırmasında hangi
    kaynakların karantinaya düştüğünü görüp gerekirse F12 ile CSS
    seçici girmesi gerekebilir.

## Modüller (sırayla)
1. **Kazıma hattı** — kaynaklar.yaml + üç katmanlı çıkarım + robots
   doğrulama + sağlık kontrolü + ÇOK KAYNAK çapraz doğrulama + log. ✅
   Motor v0.4 hazır, sahte veriyle test edildi (35 test). robots.txt
   kontrolü Yavuz'un yerelinde yapıldı (bkz. Teknik Durum) — 4 yeni
   kaynak aktifleşti. Kalan: Yavuz'un yerelinde `python motor.py`
   çalıştırıp (a) hangi kaynakların gerçekten ürün döndürdüğünü
   görmesi, (b) JSON-LD/microdata bulamayıp karantinaya düşenler için
   F12 ile CSS seçici doldurması, (c) salon ve fotoğrafçı/gelin-ayakkabısı
   kalemleri için eksik/tek kalan kaynaklara alternatif bulması.
2. **Veri saklama** — aylık snapshot şeması (SQLite yeterli).
3. **İlk hesaplayıcı + endeks sayfası** (düğün).
4. **Metodoloji sayfası + schema.org işaretlemesi.**
5. **Yayın** — Cloudflare Pages, custom domain, SSL.
6. **Aylık otomasyon** — GitHub Actions cron.
7. **Fiyat geçmişi grafikleri** (3+ ay veri sonrası).

## Yapılacaklar (kod dışı)
- [x] Domain alındı
- [ ] Cloudflare nameserver propagasyon onayı
- [x] GitHub repo kurulumu
- [x] robots.txt kontrolü yapıldı (Yavuz'un yerelinde,
      `scraper/robots_kontrol.py` ile, 2026-07-23): Trendyol/Ramsey/
      Atasay/Armut ONAY → aktif edildi. Hepsiburada/Dolap/DüğünBuketi
      (3 sayfa) RET → pasif kaldı.
- [ ] Yavuz'un yerelinde `python motor.py` çalıştırıp yeni aktif
      kaynakların (Trendyol, Ramsey, Atasay, Armut) gerçek veri
      döndürdüğünü doğrulaması ve karantinaya düşenler için gerekirse
      CSS seçici doldurması (bu sandbox'tan yapılamıyor — network kısıtı)
- [ ] "salon" kalemi için YENİ kaynak bulma (tek adayı RET oldu, şu an
      hiç aktif kaynağı yok)
- [ ] "fotografci" için 2. bağımsız kaynak bulma (dugunbuketi RET oldu,
      sadece armut kaldı)
- [ ] "gelin-ayakkabisi" ve gelinlik'in "gelinlik evi/lüks segment"i
      için 2. bağımsız kaynak bulma (dugunbuketi RET oldu)
- [ ] Düğün kalem listesindeki geri kalanlar için kaynak bulma: takı/
      altın (canlı fiyat), nikah şekeri, davetiye
- [ ] TÜİK doğrulama verisi entegrasyonu (ÇOK KAYNAK KURALI 5. katman)
- [ ] (İleride) Türk Patent marka başvurusu
- [ ] (İleride) yakın domain varyantlarını kapat

## Çalışma Şekli
- Strateji claude.ai sohbetinde, inşaat Claude Code'da.
- Her oturum TEK modüle odaklanır.
- Oturum sonunda bu dosya güncellenir.
