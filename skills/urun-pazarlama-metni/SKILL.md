---
name: urun-pazarlama-metni
description: Bir ürün fırsatını (yeni ürün, stok geldi, yeni indirim) veri dosyasındaki alanlardan taslak bir sosyal medya gönderisine çevirir — sayı uydurmadan, ürün açıklamasını kopyalamadan, yayınlamadan. urun-pazarlama takımı her fırsat için taslak yazarken okur.
kaynak: A Şirketi kitinin kendi üretimi — dış kaynak yok
lisans: —
uyarlayan: A Şirketi (2026-09-17)
takimlar: [urun-pazarlama]
---

# Ürün pazarlama metni

## Ne zaman
Bir fırsat (yeni ürün / stok geldi / yeni indirim) veri kıyasıyla bulunduktan sonra, o fırsat için
`cikti/YYYY-Www-<kod>-taslak.md` yazılmadan önce. Stok uyarısı (bilgi amaçlı satır) için kullanılmaz —
o yalnız raporda kalır, taslağı yoktur.

## Girdi
Fırsatın kaynaklandığı `veri/YYYY-Www.json` satırı (`kod, baslik, kategori, fiyat, indirim,
indirim_oran, stok, resim`) ve gerekiyorsa `sirket/KURUMSAL-BILGILER.md`. Başka hiçbir kaynak
kullanılmaz — ürünün XML'de olmayan bir özelliği (ör. hasat yılı, menşei detayı) taslağa girmez.

## Adımlar
1. Fırsat türünü belirle ve açılışı ona göre kur: **yeni ürün** → "yeni geldi"; **stok geldi** →
   "stokta yeniden"; **yeni indirim** → indirim oranını söyle.
2. Fiyatı ve varsa indirim oranını **yalnız veri satırından** yaz; `indirim_oran` yoksa indirimden
   hiç bahsetme — "kampanyalı" gibi belirsiz ifadeyle telafi etme.
3. `Aciklama` alanı elindeyse (veri dosyasında yoksa bu adımı atla) yalnız **ilham** al: iki-üç
   cümlelik özgün bir tanıtım metni yaz, cümleleri veya kalıpları birebir kopyalama.
4. `resim` alanı varsa URL'ini "Görsel:" notu olarak ekle; yoksa "görsel yok" yaz, uydurma link kurma.
5. Yasal ibare ya da iletişim bilgisi (vergi no, telefon, adres) gerekiyorsa yalnız
   `sirket/KURUMSAL-BILGILER.md`'den al; orada yoksa o satırı boş bırak, tahmin etme.
6. Kapanışı sabit çağrıyla bitir: "İncele: nidazeytin.com" — başka bir link uydurma (XML'de ürün
   sayfası URL'i yok).
7. Başlığa **taslak** olduğunu ve yayınlanmadığını hatırlatan tek satır ekle (ör. "— taslak, yayın
   kararı patronda").

## Çıktı şablonu
```
# Taslak — <ürün adı> (<fırsat türü>)

> Kaynak: [veri/YYYY-Www.json] · kod: <kod> · — taslak, yayın kararı patronda

<2-3 cümlelik tanıtım metni>

Fiyat: <fiyat> <para_birimi>[, %<indirim_oran> indirimle <indirim> <para_birimi>]
Görsel: <resim URL'i ya da "görsel yok">

İncele: nidazeytin.com
```

## Yasaklar
- Veri satırında olmayan fiyat, stok, oran, özellik yazmak.
- `Aciklama` alanını cümle cümle kopyalayıp kendi metniymiş gibi sunmak.
- Yasal ibare / iletişim bilgisini `sirket/KURUMSAL-BILGILER.md` dışından tahmin etmek.
- Ürün sayfası, kampanya kodu ya da indirim linki uydurmak — XML'de yok.
- "Sınırlı stok", "son gün" gibi veri satırında karşılığı olmayan aciliyet ifadeleri eklemek.

## Öğrenilenler
Bu skill koşuda aldığı veriyle **kendini geliştirir**: her koşudan sonra ne işe yaradığını ve nerede
yanıldığını `takimlar/urun-pazarlama/defter.md`'ye tek ders olarak yaz. Aynı ders üç koşuda tekrar
ediyorsa koşu kaydına "yetenek önerisi: `urun-pazarlama-metni` → ## Öğrenilenler'e şu satır eklensin"
yaz; kararı patron verir, skill'i kendi başına değiştirme.

- (henüz ders yok)
