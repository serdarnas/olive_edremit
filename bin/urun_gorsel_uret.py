#!/usr/bin/env python3
"""Bir ürünün beslemedeki GERÇEK fotoğraflarından reklam/gönderi formatları + kısa video üretir.

Kullanım:
  python3 bin/urun_gorsel_uret.py <kod> <veri/YYYY-Www.json> <cikti-onek>

Çıktı: <cikti-onek>-1x1.jpg, -4x5.jpg, -9x16.jpg, -video.mp4, (FAL_KEY varsa) -9x16-sahne.jpg

Deterministik kısım (fotoğraf kırpma + video) her zaman çalışır, hiçbir üretken model kullanmaz —
yalnız beslemedeki gerçek fotoğraflar kırpılır/birleştirilir. Yalnız **sahne** (arka plan) katmanı
`FAL_KEY` ile üretilir ve GERÇEK ürün fotoğrafı bunun üstüne bindirilir — ürünün kendisi hiçbir
zaman yapay zekayla çizilmez/değiştirilmez (bkz. `bin/kapak_uret.py`, aynı ilke: AI yalnız zemin
çizer). `FAL_KEY` yoksa, üretim başarısız/zaman aşımına uğrarsa ya da `ffmpeg` yoksa ilgili adım
sessizce atlanır — koşu bloklanmaz, çıktıda "atlandı" notuyla devam eder.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402
from PIL import Image, ImageFilter, ImageOps  # noqa: E402

KUYRUK = "https://queue.fal.run"
MODEL = "fal-ai/nano-banana-pro"
BEKLEME_SN = 90  # kapak_uret.py'den kısa tutuldu: koşu başına azami 2 çağrı, ANAYASA §4 zaman tavanı
FORMATLAR = {"1x1": (1080, 1080), "4x5": (1080, 1350), "9x16": (1080, 1920)}
SAHNE_STIL = (" — fine engraved illustration on warm aged paper, muted ink browns with one warm "
              "accent colour, soft vignette, rustic olive branch and wood table, absolutely no "
              "product, no bottle, no jar, no text, no letters, no logo, no watermark")
SAHNE_VARSAYILAN = "a rustic Aegean olive grove table scene, warm afternoon light"


def _urun_bul(veri_dosyasi, kod):
    veri = json.loads(Path(veri_dosyasi).read_text(encoding="utf-8"))
    for urun in veri.get("urunler", []):
        if urun.get("kod") == kod:
            return urun
    return None


def _guvenli_url(url):
    """Besleme URL'lerinde ham Türkçe karakter (ör. 'zeytinyağı') geçebiliyor — `urlopen` bunu
    ASCII'ye çeviremeden çöküyor; yol/sorgu kısmını yüzde-kodlar, zaten kodlanmışsa bozmaz."""
    parca = urllib.parse.urlsplit(url)
    yol = urllib.parse.quote(parca.path, safe="/%")
    sorgu = urllib.parse.quote(parca.query, safe="=&%")
    return urllib.parse.urlunsplit((parca.scheme, parca.netloc, yol, sorgu, parca.fragment))


def _indir(url):
    istek = urllib.request.Request(_guvenli_url(url), headers={"User-Agent": "a-sirketi/1.0"})
    ham = Path(tempfile.mkstemp(prefix="urun-gorsel-", suffix=".jpg")[1])
    try:
        with urllib.request.urlopen(istek, timeout=20) as yanit, open(ham, "wb") as dosya:
            shutil.copyfileobj(yanit, dosya)
        return ham
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def kirp(kaynak_yolu, genislik, yukseklik):
    """Ölçekleyip ortadan kırpar — `kapak_uret.py`'nin `kirp_ve_yaz` mantığıyla aynı."""
    with Image.open(kaynak_yolu) as gorsel:
        kare = gorsel.convert("RGB")
        olcek = max(genislik / kare.width, yukseklik / kare.height)
        buyuk = kare.resize((round(kare.width * olcek), round(kare.height * olcek)), Image.LANCZOS)
    sol, ust = (buyuk.width - genislik) // 2, (buyuk.height - yukseklik) // 2
    return buyuk.crop((sol, ust, sol + genislik, ust + yukseklik))


def formatlari_uret(fotograf_yollari, cikti_onek):
    """İlk gerçek fotoğraftan üç standart Meta formatını üretir. Dönen: {format: dosya_yolu}."""
    if not fotograf_yollari:
        return {}
    sonuc = {}
    for ad, (genislik, yukseklik) in FORMATLAR.items():
        kare = kirp(fotograf_yollari[0], genislik, yukseklik)
        yol = f"{cikti_onek}-{ad}.jpg"
        Path(yol).parent.mkdir(parents=True, exist_ok=True)
        kare.save(yol, "JPEG", quality=92)
        sonuc[ad] = yol
    return sonuc


def video_uret(fotograf_yollari, cikti_onek):
    """Gerçek fotoğraflardan ffmpeg ile yumuşak yakınlaşmalı slayt videosu (1080x1920, mp4).
    `ffmpeg` yoksa ya da bir adım başarısız olursa None döner — sessizce atlanır, uydurmaz."""
    if not fotograf_yollari or not shutil.which("ffmpeg"):
        return None
    genislik, yukseklik = FORMATLAR["9x16"]
    sure_kare, fps = 3, 25
    kare_sayisi = sure_kare * fps
    with tempfile.TemporaryDirectory(prefix="urun-video-") as gecici:
        klipler = []
        for i, yol in enumerate(fotograf_yollari[:4]):  # azami 4 kare, video çok uzamasın
            kirpilmis = kirp(yol, genislik, yukseklik)
            kare_dosyasi = Path(gecici) / f"kare-{i}.jpg"
            kirpilmis.save(kare_dosyasi, "JPEG", quality=92)
            klip = Path(gecici) / f"klip-{i}.mp4"
            zoompan = (f"scale=8000:-1,zoompan=z='min(zoom+0.0015,1.1)':d={kare_sayisi}:"
                       f"s={genislik}x{yukseklik}:fps={fps}")
            komut = ["ffmpeg", "-y", "-loop", "1", "-i", str(kare_dosyasi), "-vf", zoompan,
                     "-t", str(sure_kare), "-pix_fmt", "yuv420p", str(klip)]
            try:
                calisti = subprocess.run(komut, capture_output=True, timeout=60)
            except (subprocess.TimeoutExpired, OSError):
                return None
            if calisti.returncode != 0:
                return None
            klipler.append(klip)
        liste_dosyasi = Path(gecici) / "liste.txt"
        liste_dosyasi.write_text("".join(f"file '{k}'\n" for k in klipler))
        cikti = f"{cikti_onek}-video.mp4"
        Path(cikti).parent.mkdir(parents=True, exist_ok=True)
        komut = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(liste_dosyasi),
                 "-c", "copy", cikti]
        try:
            calisti = subprocess.run(komut, capture_output=True, timeout=60)
        except (subprocess.TimeoutExpired, OSError):
            return None
        return cikti if calisti.returncode == 0 else None


def _istek(url, veri=None):
    istek = urllib.request.Request(
        url, data=json.dumps(veri).encode() if veri is not None else None,
        headers={"Authorization": f"Key {os.environ.get('FAL_KEY', '')}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(istek, timeout=180) as yanit:
        return json.loads(yanit.read())


def _sahne_bekle(is_, sure=BEKLEME_SN):
    biter = time.time() + sure
    while time.time() < biter:
        try:
            durum = _istek(is_["status_url"]).get("status")
        except (urllib.error.URLError, OSError, ValueError, KeyError):
            time.sleep(4)
            continue
        if durum == "COMPLETED":
            sonuc = _istek(is_["response_url"])
            return (sonuc.get("images") or [{}])[0].get("url")
        if durum in ("FAILED", "ERROR"):
            return None
        time.sleep(4)
    return None


def _duz_fon_sil(urun_rgba, alt_esik=200, ust_esik=245):
    """Ürünü açık/düz renkli stüdyo fonundan ayırır (basit parlaklık eşiği + kenar yumuşatma).
    Ürünün pikselleri hiç değişmez, yalnız etrafındaki neredeyse-beyaz fon saydamlaştırılır.
    Mükemmel değildir (çok açık renkli ambalajın kendi kenarları da incelebilir) — bu yüzden
    sahne dosyası taslak sayılır, insan yayınlamadan önce gözden geçirir."""
    gri = ImageOps.grayscale(urun_rgba)
    lut = [255 if deger <= alt_esik else (0 if deger >= ust_esik else
           round(255 * (ust_esik - deger) / (ust_esik - alt_esik))) for deger in range(256)]
    alfa = gri.point(lut).filter(ImageFilter.GaussianBlur(2))
    kesilmis = urun_rgba.copy()
    kesilmis.putalpha(alfa)
    return kesilmis


def sahne_uret(fotograf_yolu, cikti_onek, baglam=None):
    """Yalnız dekoratif arka plan üretir (fal), GERÇEK ürün fotoğrafını üstüne bindirir.
    Herhangi bir adımda hata/zaman aşımı olursa None döner — ürün asla AI ile çizilmez."""
    if not os.environ.get("FAL_KEY"):
        return None
    genislik, yukseklik = FORMATLAR["9x16"]
    try:
        is_ = _istek(f"{KUYRUK}/{MODEL}", {"prompt": (baglam or SAHNE_VARSAYILAN) + SAHNE_STIL,
                                            "aspect_ratio": "9:16", "resolution": "2K", "num_images": 1})
    except (urllib.error.URLError, OSError, ValueError):
        return None
    url = _sahne_bekle(is_)
    if not url:
        return None
    sahne_ham = _indir(url)
    if not sahne_ham:
        return None
    zemin = kirp(sahne_ham, genislik, yukseklik).convert("RGBA")
    with Image.open(fotograf_yolu) as urun_gorseli:
        urun = _duz_fon_sil(urun_gorseli.convert("RGBA"))
        oran = min((genislik * 0.7) / urun.width, (yukseklik * 0.45) / urun.height)
        urun = urun.resize((round(urun.width * oran), round(urun.height * oran)), Image.LANCZOS)
    konum = ((genislik - urun.width) // 2, yukseklik - urun.height - round(yukseklik * 0.08))
    zemin.alpha_composite(urun, konum)
    yol = f"{cikti_onek}-9x16-sahne.jpg"
    zemin.convert("RGB").save(yol, "JPEG", quality=92)
    return yol


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    kod, veri_dosyasi, cikti_onek = argv[0], argv[1], argv[2]
    ayar.ortam_yukle()
    urun = _urun_bul(veri_dosyasi, kod)
    if not urun:
        print(json.dumps({"hata": f"kod bulunamadı: {kod}"}, ensure_ascii=False), file=sys.stderr)
        return 1
    resim_urlleri = urun.get("resimler") or ([urun["resim"]] if urun.get("resim") else [])
    if not resim_urlleri:
        print(json.dumps({"kod": kod, "not": "beslemede gerçek fotoğraf yok, üretilecek bir şey yok"},
                          ensure_ascii=False))
        return 0
    fotograf_yollari = [y for y in (_indir(u) for u in resim_urlleri) if y]
    if not fotograf_yollari:
        print(json.dumps({"kod": kod, "hata": "fotoğraflar indirilemedi"}, ensure_ascii=False),
              file=sys.stderr)
        return 1
    sonuc = {"kod": kod, "kaynak_fotograf_sayisi": len(fotograf_yollari)}
    sonuc.update(formatlari_uret(fotograf_yollari, cikti_onek))
    sonuc["video"] = video_uret(fotograf_yollari, cikti_onek) or "atlandı (ffmpeg yok ya da üretim başarısız)"
    sonuc["sahne"] = (sahne_uret(fotograf_yollari[0], cikti_onek, urun.get("ana_kategori"))
                       or "atlandı (FAL_KEY yok ya da üretim başarısız/zaman aşımı)")
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
