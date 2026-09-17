---
kategori: Ürünler
kaynaklar: [takimlar/urun-pazarlama/veri/2026-W38.json]
son_guncelleme: 2026-09-17
---

# Ürünler — Genel Bakış

*(Kaynak: [veri/2026-W38.json] — SoftTr XML beslemesi, `NIDA_XML_URL`, çekildiği tarih 2026-09-17.
Bu sayfa yeni haftalık veri geldikçe güncellenir; eski sayı üzerine değil, yanına "önceki: X" notu
düşülür.)*

## Katalog büyüklüğü ve kategori dağılımı
53 ürün, dört ana kategoride:

| Ana kategori | Ürün sayısı |
|---|---|
| ZEYTİN | 21 |
| Sabun | 18 |
| ZEYTİNYAĞI | 11 |
| Kolonya | 3 |

**Not:** Nida Zeytin yalnız zeytin/zeytinyağı satmıyor — zeytinyağı sabunu (18 ürün, kataloğun
%34'ü) ve kolonya da ürün ailesinde. Pazarlama/reklam planlarken bu üç kategorinin de görsel/video
ihtiyacı olduğu unutulmamalı — bkz. [[gorsel-video-durumu]] (aşağıda, henüz ayrı sayfa değil).

## Stok durumu (2026-W38 anlık görüntü)
53 üründen 13'ü bu hafta stoksuz (`stok == 0`). Hangi ürünler olduğu haftalık
`takimlar/urun-pazarlama/cikti/YYYY-Www-rapor.md`'de.

## Görsel/video durumu
XML beslemesindeki gerçek fotoğraf sayısı dağılımı (bkz. `bin/urun_veri_cek.py`'nin `resimler`
alanı — eskiden yalnız ilk fotoğraf tutuluyordu, artık hepsi):

| Fotoğraf sayısı | Ürün sayısı |
|---|---|
| 1 | 25 |
| 2 | 17 |
| 3 | 6 |
| 4 | 3 |
| 6 | 2 |

- **25 üründe (kataloğun %47'si) yalnız 1 gerçek fotoğraf var** — gerçek çekim ihtiyacı burada.
- **Hiçbir üründe kullanılabilir video yok.**
- `bin/urun_gorsel_uret.py` bu gerçek fotoğraflardan reklam/gönderi formatları (1:1/4:5/9:16) ve
  kısa slayt videosu üretebiliyor (bkz. `takimlar/urun-pazarlama/takim.md`) — ama 0-1 fotoğraflı
  ürünlerde üretecek malzeme az/yok, gerçek çekim bunun yerini tutmaz.
- Haftalık `urun-pazarlama` raporunun "Çekim gerekiyor" bölümü bu listeyi güncel tutar; bu sayfa
  yalnız genel tabloyu tutar, hafta hafta 25 sayısı değişirse buraya "önceki: 25 (2026-W38)" notu
  eklenir.

## Bağlantılı sayfalar
- [[sirket-profili]] — şirket kimliği, kanallar
