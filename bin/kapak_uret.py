#!/usr/bin/env python3
"""X Article kapağı üretir — 3840×736 (5,2:1), tek satır başlık.

Hibrit yol: Google Gemini API (`gemini-3.1-flash-image`, "Nano Banana 2") **yalnızca zemini**
çizer (metinsiz), başlık zeminin üstüne yerelde PIL ile basılır. Gerekçe: üretken modeller
Türkçe metni, tırnakları ve noktalama işaretlerini bozuyor; kapak başlığı pazarlık konusu değil.

Kullanım:
  python3 bin/kapak_uret.py "<başlık>" <cikti.png> [--zemin "<İngilizce sahne tarifi>"]

Çıkış kodları: 0 üretildi · 2 GEMINI_API_KEY yok · 1 üretilemedi.
2 ve 1 durumunda çağıran pakete **"kapak: sen ekleyeceksin"** notunu yazar ve devam eder.
GEMINI_API_KEY yalnızca ortamdan okunur; hiçbir çıktıya, kayda, deftere yazılmaz.
"""
import base64
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402

GEMINI_MODEL = "gemini-3.1-flash-image"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
GEMINI_ZAMAN_ASIMI_SN = 120
DENEMELER = (("21:9", "4K"), ("21:9", "2K"), ("16:9", "2K"))
GENISLIK, YUKSEKLIK = 3840, 736
METIN_ALANI = 0.52      # sol yarı metne, sağ yarı görsele
KENAR = 170
METIN_RENGI = (27, 23, 19)

ZEMIN_VARSAYILAN = ("a quiet desk still life: brass instruments, folded charts and a single warm "
                    "lamp on dark wood")
ZEMIN_STIL = (" — fine engraved illustration on warm aged paper, muted ink browns with one warm "
              "accent colour, soft vignette, side light from the right, the LEFT HALF of the frame "
              "nearly empty paper for text, absolutely no text, no letters, no numbers, no logo, "
              "no watermark, no signature")
YEDEK_FONTLAR = ("/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
                 "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf")


def _gemini_istek(prompt, oran, cozunurluk):
    """Google Gemini Interactions API'ye tek senkron istek — üretilen görsel taban64 olarak
    doğrudan yanıtta döner, fal.ai'nin kuyruk+yoklama akışı gerekmiyor. Hata/zaman aşımında
    None döner, sıradaki oran/çözünürlük denemesine geçilir."""
    gövde = {
        "model": GEMINI_MODEL,
        "input": prompt,
        "response_format": {"type": "image", "mime_type": "image/jpeg",
                             "aspect_ratio": oran, "image_size": cozunurluk},
    }
    istek = urllib.request.Request(
        GEMINI_ENDPOINT, data=json.dumps(gövde).encode(),
        headers={"x-goog-api-key": os.environ.get("GEMINI_API_KEY", ""),
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(istek, timeout=GEMINI_ZAMAN_ASIMI_SN) as yanit:
            sonuc = json.loads(yanit.read())
    except urllib.error.HTTPError as exc:
        print(f"kapak: {oran}/{cozunurluk} kabul edilmedi (HTTP {exc.code}), sıradaki denenecek",
              file=sys.stderr)
        return None
    except (urllib.error.URLError, OSError, ValueError) as exc:
        print(f"kapak: {oran}/{cozunurluk} kabul edilmedi ({type(exc).__name__}), sıradaki denenecek",
              file=sys.stderr)
        return None

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
        ham = Path(tempfile.mkstemp(prefix="kapak-ham-", suffix=".jpg")[1])
        ham.write_bytes(base64.b64decode(taban64))
        return ham
    except (ValueError, OSError):
        return None


def zemin_uret(prompt):
    """Kabul edilen ilk oran/çözünürlükle zemini üretir, geçici dosya yolunu döner."""
    for oran, cozunurluk in DENEMELER:
        ham = _gemini_istek(prompt, oran, cozunurluk)
        if ham:
            return ham
    return None


def font_yolu():
    """Sistemde kurulu bir serif; hiçbiri yoksa None (PIL varsayılanı kullanılır)."""
    for klasor in (Path.home() / "Library/Fonts", Path("/Library/Fonts")):
        bulunan = sorted(klasor.glob("*[Ff]raunces*.ttf")) if klasor.is_dir() else []
        if bulunan:
            return str(bulunan[0])
    return next((y for y in YEDEK_FONTLAR if Path(y).exists()), None)


def _sigan_font(cizim, yol, metin, en_fazla_genislik):
    """Tek satıra sığana kadar puntoyu küçültür (en az 72)."""
    from PIL import ImageFont
    for boyut in range(190, 71, -6):
        font = ImageFont.truetype(yol, boyut) if yol else ImageFont.load_default()
        if not yol or cizim.textlength(metin, font=font) <= en_fazla_genislik:
            return font
    return ImageFont.truetype(yol, 72)


def kirp_ve_yaz(ham, baslik, cikti):
    """Zemini 3840×736'ya kırpar, başlığı sola basar, PNG yazar."""
    from PIL import Image, ImageDraw
    with Image.open(ham) as gorsel:
        kaynak = gorsel.convert("RGB")
        olcek = max(GENISLIK / kaynak.width, YUKSEKLIK / kaynak.height)
        buyuk = kaynak.resize((round(kaynak.width * olcek), round(kaynak.height * olcek)), Image.LANCZOS)
    sol, ust = (buyuk.width - GENISLIK) // 2, (buyuk.height - YUKSEKLIK) // 2
    kapak = buyuk.crop((sol, ust, sol + GENISLIK, ust + YUKSEKLIK))
    cizim = ImageDraw.Draw(kapak)
    font = _sigan_font(cizim, font_yolu(), baslik, METIN_ALANI * GENISLIK - 2 * KENAR)
    kutu = cizim.textbbox((0, 0), baslik, font=font)
    cizim.text((KENAR, (YUKSEKLIK - (kutu[3] - kutu[1])) // 2 - kutu[1]), baslik, font=font, fill=METIN_RENGI)
    Path(cikti).parent.mkdir(parents=True, exist_ok=True)
    kapak.save(cikti, "PNG")
    return cikti


def uret(baslik, cikti, zemin=None):
    ham = zemin_uret((zemin or ZEMIN_VARSAYILAN) + ZEMIN_STIL)
    if not ham:
        return None
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("kapak: PIL yok (pip install pillow) — başlık basılamadı", file=sys.stderr)
        return None
    return kirp_ve_yaz(ham, baslik, cikti)


def main(argv):
    ayar.ortam_yukle()
    if len(argv) < 2:
        print(__doc__)
        return 1
    if not os.environ.get("GEMINI_API_KEY"):
        print("kapak üretilmedi: GEMINI_API_KEY yok — pakete 'kapak: sen ekleyeceksin' notu düş",
              file=sys.stderr)
        return 2
    zemin = argv[argv.index("--zemin") + 1] if "--zemin" in argv[:-1] else None
    yol = uret(argv[0], argv[1], zemin)
    if not yol:
        print("kapak üretilemedi — pakete 'kapak: sen ekleyeceksin' notu düş", file=sys.stderr)
        return 1
    print(f"kapak: {yol} ({GENISLIK}×{YUKSEKLIK})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
