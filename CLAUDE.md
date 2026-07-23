# Maliyetine.com.tr — Proje Hafızası

> Bu dosya, projenin strateji sohbetlerinde (claude.ai) alınan kararların
> damıtılmış halidir. Her oturumun başında önce bunu oku. Kararları
> değiştirmeden önce Yavuz'a sor. Oturum sonunda "Teknik Durum" ve
> "Yapılacaklar" bölümlerini güncelle.

## Proje Sahibi
- Yavuz. Türkçe konuşur; doğrudan iletişim, açıklamadan çok aksiyon ister.
- Python bilir (WeasyPrint ile programatik PDF üretim hattı kurdu),
  HTML/CSS'e hakim.
- Dağıtım/içerik kası güçlü — trafik SEO/GEO ve içerikle gelecek.
- Satış modeli tercihi: soğuk satış YOK. Self-serve.

## Vizyon (tek cümle)
Türkiye için canlı, doğrulanabilir maliyet endeksi: "2026'da X kaça mal
olur?" sorusunun güvenilir tek kaynağı olmak — hem insanlar hem AI
motorları için.

## Neden Bu Proje Var (stratejik zemin)
- Tıkanıklık: insanlar her şeyi AI'a soruyor, klasik bilgi ürünleri
  değersizleşiyor.
- Çözüm: AI'ın BİLMEDİĞİ veriyi üretmek. AI'ın taze yerel fiyat verisi
  yok; enflasyon her rakamı 3 ayda eskitiyor.
- GEO hedefi: AI motorlarının (ChatGPT, Gemini, Perplexity, Claude)
  alıntılamak ZORUNDA olduğu kaynak olmak. Hedef çıktı cümlesi:
  "Maliyetine'ye göre 2026'da ... ortalama X TL."
- Yıl konsepti markanın parçası: her yıl "2027 versiyonu" çıkar; tazelik
  iş modelinin doğasında. Yıllık karşılaştırmalar ("düğün maliyeti %X
  arttı") bedava basın malzemesi.

## KIRMIZI ÇİZGİ — Veri Metodolojisi
- Fiyat verisi ASLA LLM'den üretilmez / LLM'e sorulmaz. Bu kural
  pazarlıksızdır; ihlali projenin varlık sebebini yok eder.
- Veri kaynağı: gerçek ilan/e-ticaret/karşılaştırma sitelerinden kazıma
  (robots.txt ve kullanım şartlarına saygılı, rate-limit'li) +
  gerektiğinde insan teyidi.
- AI'ın rolü: kaynak değil RAFİNERİ — ham veriyi temizleme, kategorize
  etme, aykırı değer ayıklama, özetleme.
- Her yayınlanan rakamın yanında: kaynak açıklaması, derleme tarihi,
  örneklem büyüklüğü ("14 Temmuz'da 2.340 üründen derlendi").
- Metodoloji sayfası zorunlu. Güven = tek ürün.
- Rakip çöp sitelerden tek farkımız bu; ihlal edilirse fark kalmaz.

## Ürün Kararları
- Format standardı: her kalem için düşük / orta / lüks segmenti
  (persentil bazlı: ≤P25 düşük, P25–P75 orta, >P75 lüks) + min/medyan/max
  + örneklem sayısı + tarih.
- Aylık güncelleme ritmi. Aylık JSON'lar biriktirilir → fiyat geçmişi
  grafikleri = basın/GEO malzemesi.
- Başlangıç: 7 vertikal DEĞİL, 2 vertikal ile mükemmel açılış:
  1) Düğün maliyeti
  2) Ev tadilatı maliyeti
  Sonra sırayla: ev kurma, 0 km araç, tatil, ilkokul, üniversite.
- Her vertikal üçlüsü: hesaplayıcı + endeks sayfası + metodoloji sayfası.
- Şehir/segment kırılımı hedeflenir (İstanbul vs Anadolu, ekonomik vs
  orta segment).

## Gelir Modeli (sıralı)
1. Reklam (tüketici tarafı ücretsiz)
2. Affiliate (gerçek ürün linkleri — sadece gerçek veriyle mümkün;
   segment başına "en çok satılan 3 model" gibi)
3. Pro rapor / araç aboneliği (ustalar, müteahhitler, düğün firmaları
   için teklif aracı)

## GEO Gereksinimleri (her sayfada)
- İlk 40-60 kelimede net, alıntılanabilir cevap bloğu.
- Yapılandırılmış veri (schema.org), güncelleme tarihi görünür.
- Soru formatında başlıklar ("2026'da İstanbul'da düğün kaça mal olur?").
- AI bot'larına açık robots.txt (GPTBot vb. engellenmez).
- Metodoloji ve örneklem bilgisi = atıf edilebilirlik sinyali.

## Altyapı Kararları (KESİN)
- Domain: **maliyetine.com.tr** — ALINDI. DNS Cloudflare'e taşınıyor
  (nameserver propagasyonu bekleniyor).
- Hosting: **statik site + Cloudflare Pages** (alternatif: Netlify).
  Ücretsiz. Backend YOK (şimdilik).
- WordPress KULLANILMAYACAK — yavaş, bakım yükü var, "veriden sayfa
  üret" hattımıza oturmuyor.
- Hesaplayıcılar tarayıcıda JavaScript ile çalışır; sunucu gerekmez.
- Kod deposu: GitHub (`maliyetine`).
- Otomasyon: GitHub Actions ile aylık kazıma + otomatik yayın.
- A/CNAME kayıtları elle eklenmeyecek; Cloudflare Pages'te custom domain
  eklenince otomatik oluşur.
- E-posta: gerekirse Cloudflare Email Routing (ücretsiz, Gmail'e
  yönlendirir). Acele değil.
- Basit tut: gereksiz framework yok, hedef toplam kod tabanı ~10-20K satır.

## Teknik Durum
- GitHub repo `maliyetine` oluşturuldu, ilk commit atıldı.
- `scraper/fiyat_endeksi.py` (v0.2): kazıma motoru artık `config` parametre
  alıyor (çoklu kalem/site için yeniden kullanılabilir) + Türkçe fiyat parse
  ("45.999,00 TL" → float) + IQR aykırı değer temizliği + persentil
  segmentleme + tarihli JSON çıktı. Mantık sahte veriyle test edildi.
- **ÖNEMLİ KISIT — Claude Code sandbox network erişimi**: Bu ortamın proxy
  politikası, hedef sitelere (dugun.com, dugunbuketi.com, armut.com,
  trendyol.com, hepsiburada.com vb.) doğrudan bağlantıyı 403 ile
  reddediyor (`$HTTPS_PROXY/__agentproxy/status`'ta görülebilir). Yani
  Claude Code bu ortamdan ne robots.txt doğrulayabiliyor ne de sayfa
  HTML'ine bakıp CSS seçici tespit edebiliyor. Bu adımlar Yavuz'un kendi
  makinesinde (veya erişimi açık bir ortamda) yapılmalı.
- `scraper/kaynaklar_dugun.py`: Düğün vertikali için WebSearch ile
  bulunmuş aday kaynak siteler (gelinlik → trendyol/hepsiburada, salon →
  dugunbuketi.com, fotoğrafçı → dugunbuketi.com/armut.com). Hepsi
  `durum: "arastirildi"` — robots.txt VE CSS seçiciler henüz doğrulanmadı.
- `scraper/robots_kontrol.py`: Yerelde çalıştırılacak robots.txt kontrol
  aracı (`urllib.robotparser`, ek bağımlılık yok). Her aday URL için
  ONAY/RET ve crawl-delay basar.

## Modüller (sırayla)
1. **Kazıma hattı** — kaynak site seçimi, CSS seçiciler, gerekirse
   Playwright katmanı (bot koruması olan siteler için), retry/log.
2. **Veri saklama** — aylık snapshot şeması (SQLite ile başla, yeter).
3. **İlk hesaplayıcı + endeks sayfası** (vertikal: tadilat veya düğün).
4. **Metodoloji sayfası + schema.org işaretlemesi.**
5. **Yayın** — Cloudflare Pages bağlantısı, custom domain, SSL.
6. **Aylık otomasyon** — GitHub Actions cron.
7. **Fiyat geçmişi grafikleri** (3+ ay veri biriktikten sonra).

## Yapılacaklar (kod dışı)
- [x] Domain alındı (maliyetine.com.tr)
- [ ] Cloudflare nameserver propagasyonu onayı
- [x] GitHub repo `maliyetine` oluştur
- [ ] İlk vertikal (düğün) için aday kaynak siteler bulundu
      (`scraper/kaynaklar_dugun.py`); robots.txt + CSS seçici doğrulaması
      Yavuz'un yerelinde yapılmalı (`scraper/robots_kontrol.py` ile)
- [ ] Sektörden fiyat teyidi için 2-3 temas noktası
- [ ] (İleride) Türk Patent marka başvurusu — gelir başlayınca
- [ ] (İleride) yakın domain varyantlarını kapat

## Çalışma Şekli
- Strateji claude.ai sohbetinde, inşaat Claude Code'da.
- Her oturum TEK modüle odaklanır.
- Oturum sonunda bu dosya güncellenir — süreklilik mekanizması bu dosya.
