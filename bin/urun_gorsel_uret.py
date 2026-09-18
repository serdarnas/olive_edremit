#!/usr/bin/env python3
"""Bir ürünün beslemedeki GERÇEK fotoğraflarından reklam/gönderi formatları + kısa video üretir.

Kullanım:
  python3 bin/urun_gorsel_uret.py <kod> <veri/YYYY-Www.json> <cikti-onek>

Kullanım (isteğe bağlı seslendirmeyle):
  python3 bin/urun_gorsel_uret.py <kod> <veri/YYYY-Www.json> <cikti-onek> --anlatim "<metin>"

Çıktı: <cikti-onek>-1x1.jpg, -4x5.jpg, -9x16.jpg, -video.mp4, (GEMINI_API_KEY varsa) -9x16-sahne.jpg,
(--anlatim + edge-tts kuruluysa) -seslendirme.mp3 + -altyazi.srt (ses videoya eklenir; SRT ise
`bin/urun_video_render.py` (Remotion) tarafından kelime-kelime altyazı için okunur)

Deterministik kısım (fotoğraf kırpma + video) her zaman çalışır, hiçbir üretken model kullanmaz —
yalnız beslemedeki gerçek fotoğraflar kırpılır/birleştirilir. Yalnız **sahne** (arka plan) katmanı
Google Gemini API (`GEMINI_API_KEY`, `gemini-3.1-flash-image` / "Nano Banana 2") ile üretilir ve
GERÇEK ürün fotoğrafı bunun üstüne bindirilir — ürünün kendisi hiçbir zaman yapay zekayla
çizilmez/değiştirilmez (bkz. `bin/kapak_uret.py`, aynı ilke ve aynı `GEMINI_API_KEY` — ayrı takım,
ortak anahtar). `GEMINI_API_KEY` yoksa, üretim başarısız/zaman aşımına uğrarsa ya da `ffmpeg` yoksa
ilgili adım sessizce atlanır — koşu bloklanmaz, çıktıda "atlandı" notuyla devam eder.

Seslendirme `edge-tts` (MIT, ücretsiz, API anahtarı gerekmez — `pip install edge-tts`) ile
üretilir; bu projedeki `pip install` gerektiren ikinci istisna (birincisi Pillow), aynı nazik-atlama
deseniyle: kurulu değilse "atlandı" notuyla sessiz video üretilmeye devam eder. **Metni script
uydurmaz** — `--anlatim` ile verilen metin okunur, başka hiçbir cümle eklenmez.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402
from PIL import Image, ImageFilter, ImageOps  # noqa: E402

GEMINI_MODEL = "gemini-3.1-flash-image"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
GEMINI_ZAMAN_ASIMI_SN = 60
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


_KELIME_SRT_BETIGI = r"""
import asyncio, sys
import edge_tts

async def main():
    metin, ses, mp3_yolu, srt_yolu = sys.argv[1:5]
    iletisim = edge_tts.Communicate(metin, ses, boundary="WordBoundary")
    olusturucu = edge_tts.SubMaker()
    with open(mp3_yolu, "wb") as ses_dosyasi:
        async for parca in iletisim.stream():
            if parca["type"] == "audio":
                ses_dosyasi.write(parca["data"])
            elif parca["type"] == "WordBoundary":
                olusturucu.feed(parca)
    with open(srt_yolu, "w", encoding="utf-8") as srt_dosyasi:
        srt_dosyasi.write(olusturucu.get_srt())

asyncio.run(main())
"""


def _edge_tts_python():
    """`edge-tts` konsol betiğinin shebang satırından kurulduğu (pipx/venv) python
    yorumlayıcısını bulur. CLI'nin `--write-subtitles`'ı sabit cümle-bazlı altyazı üretir
    (`Communicate`'in varsayılanı `boundary="SentenceBoundary"`); kelime-bazlı altyazı için
    kütüphaneye `boundary="WordBoundary"` ile doğrudan erişmek gerekiyor. Bulunamazsa None döner
    — çağıran taraf CLI'nin cümle-bazlı altyazısına düşer, hiçbir zaman çökmez."""
    yol = shutil.which("edge-tts")
    if not yol:
        return None
    try:
        ilk_satir = Path(yol).open(encoding="utf-8", errors="ignore").readline().strip()
    except OSError:
        return None
    if ilk_satir.startswith("#!"):
        yorumlayici = ilk_satir[2:].strip().split()[0]
        if Path(yorumlayici).exists():
            return yorumlayici
    return None


def sesli_anlatim_uret(metin, cikti_onek, ses="tr-TR-EmelNeural"):
    """`edge-tts` (MIT, ücretsiz, API anahtarı gerekmez) ile Türkçe seslendirme + kelime zamanlı
    altyazı (.srt) üretir — `bin/urun_video_render.py`'nin (Remotion) kelime-kelime altyazısı
    bunu okur, ekstra maliyeti yoktur. Metni script asla uydurmaz — yalnız `metin` parametresiyle
    verileni okur. `edge-tts` kurulu değilse ya da üretim başarısız olursa None döner — sessizce
    atlanır."""
    if not metin or not shutil.which("edge-tts"):
        return None
    yol = f"{cikti_onek}-seslendirme.mp3"
    srt_yol = f"{cikti_onek}-altyazi.srt"
    Path(yol).parent.mkdir(parents=True, exist_ok=True)

    yorumlayici = _edge_tts_python()
    if yorumlayici:
        komut = [yorumlayici, "-c", _KELIME_SRT_BETIGI, metin, ses, yol, srt_yol]
        try:
            calisti = subprocess.run(komut, capture_output=True, timeout=30)
        except (subprocess.TimeoutExpired, OSError):
            calisti = None
        if calisti is not None and calisti.returncode == 0 and Path(yol).exists():
            return yol

    # Kelime-bazlı yol kullanılamadı (yorumlayıcı bulunamadı ya da betik başarısız oldu) — CLI'nin
    # cümle-bazlı altyazısına düş, yine de bir seslendirme üretilmiş olsun.
    komut = ["edge-tts", "--voice", ses, "--text", metin, "--write-media", yol,
             "--write-subtitles", srt_yol]
    try:
        calisti = subprocess.run(komut, capture_output=True, timeout=30)
    except (subprocess.TimeoutExpired, OSError):
        return None
    return yol if calisti.returncode == 0 and Path(yol).exists() else None


def _ses_suresi(yol):
    """`ffprobe` ile saniye cinsinden ses süresi; okunamazsa None."""
    if not shutil.which("ffprobe"):
        return None
    komut = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
              "-of", "default=noprint_wrappers=1:nokey=1", yol]
    try:
        calisti = subprocess.run(komut, capture_output=True, timeout=15, text=True)
        return float(calisti.stdout.strip())
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return None


def video_uret(fotograf_yollari, cikti_onek, ses_dosyasi=None):
    """Gerçek fotoğraflardan ffmpeg ile yumuşak yakınlaşmalı slayt videosu (1080x1920, mp4).
    `ses_dosyasi` verilirse kare süresi seslendirmenin uzunluğuna göre ayarlanır (2-6 sn/kare
    arasında sınırlı) ve ses videoya eklenir; verilmezse sabit 3 sn/kare, sessiz üretilir.
    `ffmpeg` yoksa ya da bir adım başarısız olursa None döner — sessizce atlanır, uydurmaz."""
    if not fotograf_yollari or not shutil.which("ffmpeg"):
        return None
    genislik, yukseklik = FORMATLAR["9x16"]
    fps = 25
    kare_adedi = min(len(fotograf_yollari), 4)
    sure_kare = 3.0
    if ses_dosyasi:
        ses_suresi = _ses_suresi(ses_dosyasi)
        if ses_suresi:
            sure_kare = max(2.0, min(6.0, ses_suresi / kare_adedi))
    kare_sayisi = round(sure_kare * fps)
    with tempfile.TemporaryDirectory(prefix="urun-video-") as gecici:
        klipler = []
        for i, yol in enumerate(fotograf_yollari[:kare_adedi]):
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
        sessiz = Path(gecici) / "sessiz.mp4"
        komut = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(liste_dosyasi),
                 "-c", "copy", str(sessiz)]
        try:
            calisti = subprocess.run(komut, capture_output=True, timeout=60)
        except (subprocess.TimeoutExpired, OSError):
            return None
        if calisti.returncode != 0:
            return None
        cikti = f"{cikti_onek}-video.mp4"
        Path(cikti).parent.mkdir(parents=True, exist_ok=True)
        if not ses_dosyasi:
            shutil.copyfile(sessiz, cikti)
            return cikti
        komut = ["ffmpeg", "-y", "-i", str(sessiz), "-i", ses_dosyasi, "-c:v", "copy",
                 "-c:a", "aac", "-shortest", cikti]
        try:
            calisti = subprocess.run(komut, capture_output=True, timeout=60)
        except (subprocess.TimeoutExpired, OSError):
            return None
        if calisti.returncode == 0:
            return cikti
        shutil.copyfile(sessiz, cikti)  # ses eklenemedi, sessiz video yine de teslim edilir
        return cikti


def _gemini_sahne_iste(prompt):
    """Google Gemini Interactions API'ye TEK senkron istek — fal.ai'nin kuyruk+yoklama akışının
    aksine, üretilen görsel taban64 olarak doğrudan yanıtta döner, ayrı bir "sonucu bekle" adımı
    yok. Herhangi bir hata/zaman aşımında None döner — sessizce atlanır, script çökmez."""
    import base64

    gövde = {
        "model": GEMINI_MODEL,
        "input": prompt,
        "response_format": {"type": "image", "mime_type": "image/jpeg",
                             "aspect_ratio": "9:16", "image_size": "2K"},
    }
    istek = urllib.request.Request(
        GEMINI_ENDPOINT, data=json.dumps(gövde).encode(),
        headers={"x-goog-api-key": os.environ.get("GEMINI_API_KEY", ""),
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(istek, timeout=GEMINI_ZAMAN_ASIMI_SN) as yanit:
            sonuc = json.loads(yanit.read())
    except (urllib.error.URLError, OSError, ValueError):
        return None

    # Yanıt şekli sürüm/uca göre değişebilir (`output_image` ya da `output` listesi içinde bir
    # görsel bloğu) — ikisini de dener, hiçbirini bulamazsa None döner.
    taban64 = None
    if isinstance(sonuc.get("output_image"), dict):
        taban64 = sonuc["output_image"].get("data")
    if not taban64:
        for ogun in sonuc.get("output") or []:
            if isinstance(ogun, dict) and ogun.get("type") == "image":
                taban64 = (ogun.get("image") or {}).get("data") or ogun.get("data")
                if taban64:
                    break
    if not taban64:
        return None
    try:
        ham = Path(tempfile.mkstemp(prefix="urun-sahne-", suffix=".jpg")[1])
        ham.write_bytes(base64.b64decode(taban64))
        return ham
    except (ValueError, OSError):
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
    """Yalnız dekoratif arka plan üretir (Google Gemini API), GERÇEK ürün fotoğrafını üstüne
    bindirir. Herhangi bir adımda hata/zaman aşımı olursa None döner — ürün asla AI ile çizilmez."""
    if not os.environ.get("GEMINI_API_KEY"):
        return None
    genislik, yukseklik = FORMATLAR["9x16"]
    sahne_ham = _gemini_sahne_iste((baglam or SAHNE_VARSAYILAN) + SAHNE_STIL)
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
    anlatim = argv[argv.index("--anlatim") + 1] if "--anlatim" in argv[:-1] else None
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
    ses_dosyasi = sesli_anlatim_uret(anlatim, cikti_onek)
    sonuc["seslendirme"] = ses_dosyasi or (
        "atlandı (edge-tts kurulu değil — pip install edge-tts)" if anlatim else "atlandı (--anlatim verilmedi)")
    sonuc["video"] = (video_uret(fotograf_yollari, cikti_onek, ses_dosyasi)
                       or "atlandı (ffmpeg yok ya da üretim başarısız)")
    sonuc["sahne"] = (sahne_uret(fotograf_yollari[0], cikti_onek, urun.get("ana_kategori"))
                       or "atlandı (GEMINI_API_KEY yok ya da üretim başarısız/zaman aşımı)")
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
