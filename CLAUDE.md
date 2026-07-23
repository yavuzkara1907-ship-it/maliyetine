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
- UYARI: Kaynak seçimi metodolojinin kendisidir. Örn. genel e-ticaret
  sitesindeki 1.500 TL'lik "gelinlik" ile gelinlik evindeki 60.000 TL'lik
  gelinlik aynı ürün değil. Farklı segmentler ayrı kaynaklardan
  toplanır, karıştırılmaz.

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

## KAZIYICI MİMARİSİ (önemli)
Her site için ayrı script YAZILMAZ. Tek motor + kaynak kaydı:

- **`kaynaklar.yaml`** — tüm kaynaklar burada tanımlanır. Yeni site
  eklemek = birkaç satır YAML, kod değil. Alanlar: ad, url, vertikal,
  kalem, yöntem, (gerekirse) css_secicileri, aktif/pasif.
- **Üç katmanlı çıkarım stratejisi, sırayla:**
  1. **JSON-LD** (`application/ld+json`, schema.org/Product) — siteler
     arası ortak, en temiz. ÖNCE BUNU DENE.
  2. **Microdata / meta etiketleri** (`itemprop="price"`, og etiketleri)
  3. **Siteye özel CSS seçiciler** — son çare.
- **Sağlık kontrolü zorunlu:** bir kaynak normalde ~200 ürün dönerken
  ay içinde 3 ürün dönerse SESSİZCE devam etme, uyarı ver ve o ayki
  veriyi karantinaya al. Endeksin güvenilirliği buna bağlı.
- **Nazik kazıma:** gerçekçi User-Agent, istekler arası 2+ sn bekleme,
  retry + backoff, ayda bir çalıştırma. Amaç engellenmemek.
- **robots.txt doğrulaması otomatik:** `urllib.robotparser` ile her URL
  kazımadan önce test edilir. RET çıkan URL atlanır ve loglanır.
- JS ile render edilen siteler için Playwright katmanı (opsiyonel,
  sadece gerekince).

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
  trendyol.com, hepsiburada.com vb.) doğrudan bağlantıyı 403 ile
  reddediyor (`$HTTPS_PROXY/__agentproxy/status`'ta doğrulanabilir).
  PyPI (`pip install`) ise açık — bağımlılık kurulumu ve kod çalıştırma
  sorun değil, sadece hedef sitelere HTTP isteği atmak engelli.
- Sonuç: motor.py'nin robots.txt kontrolü ve gerçek kazıma katmanları
  BU ORTAMDAN gerçek sitelere karşı test edilemiyor. Doğrulama sahte
  HTML fixture'larıyla (`test_motor.py`) yapılıyor — mantığın doğruluğu
  kanıtlanıyor ama gerçek sitenin JSON-LD/microdata/CSS yapısı henüz
  bilinmiyor.
- Motor bu kısıtla güvenli davranıyor: robots.txt okunamazsa (ki bu
  ortamda hep okunamıyor) ihtiyatla RET kabul ediyor, kaynağı atlıyor,
  0 ürünle "sağlıklı" (ilk çalıştırma, henüz baseline yok) olarak
  kaydediyor. Yani sandbox'ta çalıştırmak hataya değil sessiz-boş
  sonuca yol açıyor — Yavuz'un yerelinde çalıştırdığında gerçek veri
  gelecek.

## Teknik Durum
- GitHub repo `maliyetine` oluşturuldu.
- **Kazıma motoru v0.3'e refactor edildi** (KAZIYICI MİMARİSİ bölümüne
  göre). `scraper/fiyat_endeksi.py` ve `scraper/kaynaklar_dugun.py`
  (v0.1/v0.2, tek-CONFIG modeli) SİLİNDİ, yerine geldi:
  - `scraper/motor.py` — tek motor: üç katmanlı çıkarım (JSON-LD →
    microdata/meta → CSS son çare), otomatik robots.txt kapısı (domain
    başına önbellekli), retry+exponential backoff, sağlık kontrolü
    (geçmişe göre ani düşüşte karantina), Türkçe fiyat parse, IQR aykırı
    değer temizliği, persentil segmentleme. `python motor.py` ile
    `kaynaklar.yaml`'daki tüm aktif kaynakları işler.
  - `scraper/kaynaklar.yaml` — kaynak kaydı. Akakçe için 6 aktif kaynak
    (gelinlik genel + tesettür + korseli + kısa + a-kesim + gelin
    ayakkabısı — WebSearch ile doğrulanmış gerçek URL'ler, sayfa_sayisi:1
    çünkü robots pagination'ı yasaklıyor). Trendyol/Hepsiburada/
    DüğünBuketi 4 kaynak `aktif: false` — robots.txt bu ortamdan hiç
    doğrulanamadı, Yavuz'un yerelinde `robots_kontrol.py` ile kontrol
    edip aktifleştirmesi gerekiyor.
  - `scraper/test_motor.py` — 28 test, hepsi PASS (`python -m unittest
    test_motor.py -v`). Sahte JSON-LD/microdata/CSS HTML fixture'ları,
    robots.txt kapısı (mock), sağlık kontrolü/karantina, uçtan uca
    `kaynak_isle()` (dosya yazma dahil), `kaynaklar.yaml` şema doğrulama.
    Bu süreçte gerçek bir bug bulundu ve düzeltildi: JSON-LD katmanı
    `ItemList`/`itemListElement` yapısını açmıyordu (çoğu kategori
    listeleme sayfası bu formatı kullanır) — düzeltildi.
  - `python motor.py --cikti /tmp/...` ile gerçek `kaynaklar.yaml`'a
    karşı uçtan uca çalıştırıldı: 6 aktif kaynak da robots.txt
    okunamadığı için (sandbox kısıtı) güvenli şekilde RET/atla, 0 ürün,
    "sağlıklı" (ilk çalıştırma) olarak kaydedildi, çökme yok, exit 0.
  - `scraper/robots_kontrol.py` korunuyor — Yavuz'un yerelinde tekil URL
    hızlı kontrolü için (motor.py'nin otomatik kapısından bağımsız,
    manuel ön-kontrol aracı).
  - `.gitignore` düzeltildi: eski `*_20*.json` kuralı aylık veri
    JSON'larını da (yanlışlıkla) gizliyordu — kaldırıldı. Aylık veri
    (`scraper/veri/`) BİLEREK commit edilecek (fiyat geçmişi = ürün).
    Sadece `kazima.log` ve `kaynak_gecmisi.json` (çalışma zamanı durumu)
    gitignore'da.

## Modüller (sırayla)
1. **Kazıma hattı** — kaynaklar.yaml + üç katmanlı çıkarım + robots
   doğrulama + sağlık kontrolü + log. ✅ Motor v0.3 hazır ve sahte
   veriyle test edildi. Kalan: Yavuz'un yerelinde gerçek siteye karşı
   çalıştırıp (a) Akakçe'nin 6 aktif kaynağının gerçekten ürün
   döndürdüğünü doğrulamak, (b) Trendyol/Hepsiburada/DüğünBuketi için
   robots.txt kontrolü yapıp uygun olanları `aktif: true` yapmak.
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
- [ ] Yavuz'un yerelinde `python motor.py` çalıştırıp Akakçe
      kaynaklarının gerçek veri döndürdüğünü doğrulaması (bu sandbox'tan
      yapılamıyor — network kısıtı)
- [ ] Trendyol/Hepsiburada/DüğünBuketi robots.txt kontrolü
      (`scraper/robots_kontrol.py` ile) → uygun olanları
      `kaynaklar.yaml`'da `aktif: true` yap
- [ ] (İleride) Türk Patent marka başvurusu
- [ ] (İleride) yakın domain varyantlarını kapat

## Çalışma Şekli
- Strateji claude.ai sohbetinde, inşaat Claude Code'da.
- Her oturum TEK modüle odaklanır.
- Oturum sonunda bu dosya güncellenir.
