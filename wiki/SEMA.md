# Nida Zeytin Bilgi Tabanı — Şema

> Fikrin kaynağı: [Andrej Karpathy — LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
> Bu dosya o fikrin Nida Zeytin (Olive Edremit Zeytincilik) için somutlaştırılmış hâli — LLM'in bu
> wiki'yi nasıl işlettiğini/bakımını yaptığını anlatır. `ANAYASA.md`'deki gibi değişmez bir kural
> değil; insan ve LLM birlikte zamanla geliştirir.

## Fikir (özet)
RAG'ın aksine, her soruda ham kaynaklardan yeniden parça toplamak yerine, LLM kaynakları okudukça
**kalıcı, birbirine bağlı bir markdown wiki'yi büyütür ve günceller**. Çapraz referanslar, çelişki
notları, sentez — hepsi zaten sayfalarda durur; her soruda yeniden inşa edilmez.

## Üç katman
1. **`kaynaklar/`** — ham kaynaklar (makale, rakip sayfası, müşteri yorumu, PDF, dışa aktarılmış
   veri). **Değişmez** — LLM buradan yalnız okur, asla üzerine yazmaz. Gerçeğin kaynağı burasıdır.
2. **`sayfalar/`** — LLM'in ürettiği/bakımını yaptığı markdown sayfaları (varlık, kavram,
   karşılaştırma, sentez). Bu katmanın sahibi LLM'dir — insan okur, LLM yazar.
3. **Bu dosya (`SEMA.md`)** — yapı, kategori, iş akışı sözleşmesi. İnsan ve LLM birlikte geliştirir.

## Bu bilgi tabanının A Şirketi ile ilişkisi
`takimlar/`'daki 5 otomasyon takımı (x-icerik, twitter-icerik, youtube-analiz, urun-pazarlama,
marka-izleme) **zamanlı, taslak üreten, sınırlı-araçlı** ajanlardır — ANAYASA'ya bağlıdırlar. Bu
wiki farklı bir şey: **etkileşimli, insan yönetiminde** bir bilgi biriktirme aracı, zamanlanmış
koşusu yoktur, `bin/kos.py` ile tetiklenmez. Yine de beslenebilir:
- Bir takımın haftalık raporu (`takimlar/<takim>/cikti/*.md`) ilginç bulunursa, insan onu
  `wiki/kaynaklar/`'a kopyalar, LLM'e "bunu işle" der — rapor kaynak, wiki'deki sentez ürün olur.
- Bu, ANAYASA §1'i ihlal etmez: dışarı hiçbir şey gitmiyor, yalnız içeri bilgi giriyor.

## Sayfa kategorileri (başlangıç — zamanla genişler)
- **Ürünler** — zeytin/zeytinyağı ürün ailesi, kategoriler, öne çıkan özellikler
- **Marka Algısı** — marka-izleme bulgularının sentezi, tekrarlayan temalar
- **Rakipler** — bölgedeki/kategorideki rakip markalar, konumlandırma notları
- **Müşteri Geri Bildirimi** — yorum/şikayet/övgü temaları, kaynağıyla
- **Pazar ve Tedarik** — hasat/üretim döngüsü, fiyat trendleri, tedarik notları
- **Sözlük** — tekrar eden terim/kısaltmaların tek satırlık açıklaması
Yeni bir kategori gerektiğinde buraya bir satır eklenir — sabit liste değil.

## `index.md` (içerik kataloğu)
Her sayfa: link + tek satır özet + kategori + son güncelleme tarihi. Besleme (ingest) sonrası
her zaman güncellenir. Soru yanıtlanırken önce burası okunur, sonra ilgili sayfalara inilir.

## `log.md` (kronolojik kayıt)
Ekleme-yalnız (append-only). Her satır şu biçimde başlar, `grep "^## \[" wiki/log.md` ile
taranabilir olsun diye:
```
## [YYYY-AA-GG] besleme | <kaynak adı>
## [YYYY-AA-GG] sorgu | <soru özeti>
## [YYYY-AA-GG] sağlık-kontrolü | <bulgu özeti>
```

## İşlemler

### Besleme (ingest)
1. Yeni kaynak `wiki/kaynaklar/`'a eklenir (insan koyar ya da bir takım raporundan kopyalanır).
2. LLM kaynağı okur, önemli noktaları çıkarır — insanla kısaca tartışır (özellikle vurgulanacak
   nokta varsa).
3. İlgili `sayfalar/` dosyalarını günceller: yeni sayfa açar ya da var olanı genişletir/düzeltir.
   Yeni veri eskisiyle çelişiyorsa **çelişkiyi sil, üzerine yazma** — "eski bilgi X diyordu, yeni
   kaynak Y diyor" notu sayfada kalır.
4. `index.md`'yi günceller.
5. `log.md`'ye tek satır ekler.

### Sorgu (query)
1. `index.md`'den ilgili sayfaları bul.
2. Sayfaları oku, kaynaklı bir yanıt sentezle (hangi sayfa/kaynaktan geldiği belli olsun).
3. Yanıt tekrar sorulacak nitelikteyse (karşılaştırma, analiz, yeni bağlantı) `sayfalar/`'a yeni
   bir sayfa olarak da yaz — sohbette kaybolmasın, wiki büyüsün.
4. `log.md`'ye tek satır ekler.

### Sağlık kontrolü (lint)
Periyodik, insan istediğinde:
- Sayfalar arası çelişki var mı?
- Yeni kaynakların geçersiz kıldığı eski iddia var mı?
- Hiçbir sayfadan link almayan (öksüz) sayfa var mı?
- Adı geçip kendi sayfası olmayan önemli bir kavram/varlık var mı?
- `log.md`'ye bulgu özeti eklenir.

## Kurallar
- `kaynaklar/` asla değiştirilmez — yalnız eklenir.
- Sayfalarda kaynaksız iddia yazılmaz; her önemli iddianın hangi kaynaktan geldiği bellidir
  (ANAYASA §2 "kaynaksız sayı yok" ilkesinin buradaki karşılığı — bu wiki'nin de disiplinidir,
  A Şirketi takımlarıyla aynı disiplin).
- Bu wiki hiçbir zaman dışarı (sosyal hesap, mail, müşteri) otomatik çıktı üretmez — tamamen içe
  dönük, insanın okuduğu bir bilgi tabanıdır.
