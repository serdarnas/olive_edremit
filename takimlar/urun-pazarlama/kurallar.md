# Kurallar — urun-pazarlama

> Bekçi bu dosyayı okur ve koşu kaydını buna göre denetler. Yalnızca insan değiştirir.

## Neye göre çalışır
- ANAYASA madde 2: **`veri/` dosyasında olmayan sayı yazılmaz.** Fiyat, indirim, stok, ürün adı
  yalnız `veri/YYYY-Www.json`'dan gelir; her rapor satırında `[veri/YYYY-Www.json]` durur.
- Fırsat (yeni ürün / stok geldi / yeni indirim) yalnız **iki** haftalık veri dosyası kıyaslanarak
  çıkarılır. Kıyaslanacak önceki dosya yoksa fırsat uydurulmaz — "ilk koşu" denir.
- Yasal ibare, adres, telefon, vergi no, marka adı yalnız `sirket/KURUMSAL-BILGILER.md`'den gelir;
  bu dosya insanındır, ajan değiştirmez.
- Taslaklar patronun onayına gider — yayına gitmez (ANAYASA §1).

## Asla yapmaz
- Sosyal hesaba yazmaz, gönderi paylaşmaz, yorum bırakmaz.
- XML beslemesinde olmayan fiyat/stok/ürün bilgisi yazmaz.
- İlk koşuda (önceki veri yokken) fırsat ya da taslak üretmez.
- `Aciklama` alanını birebir kopyalayıp özgün metin diye sunmaz.
- Yasal/iletişim bilgisini tahmin etmez — `sirket/KURUMSAL-BILGILER.md`'de yoksa boş bırakır.
- Besleme `hata` döndürdüğünde eski veriyi bugünkü gibi sunmaz.

## Çıktı kalite ölçütleri
- Her fırsat satırında veri dosyası referansı ve fırsat türü etiketi.
- Her taslak gönderi tek dosya, tek fırsata bağlı, kaynağı belli.
- Koşu kaydında kaç ürün, kaç fırsat (türe göre), kaç taslak, maliyet yazılı.

- Fiyat/indirim etiketi ve altyazı yalnız veri dosyasındaki/taslak metnindeki bilgiyi gösterir;
  Remotion bileşeni hiçbir sayı ya da cümle uydurmaz.
- Node/Remotion (`video-uretici/`) kurulu değilse gelişmiş video adımı sessizce atlanır, temel
  video (ffmpeg) ve sessiz/altyazısız akış etkilenmez.
