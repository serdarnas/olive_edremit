#!/usr/bin/env python3
"""`bin/urun_gorsel_uret.py`'nin ürettiği varlıklardan (9x16 fotoğraf, seslendirme, altyazı)
Remotion ile animasyonlu fiyat/indirim etiketi + kelime-kelime (TikTok tarzı) altyazılı bir
"gelişmiş video" üretir.

Kullanım:
  python3 bin/urun_video_render.py <kod> <veri/YYYY-Www.json> <cikti-onek>

Çıktı: <cikti-onek>-video-gelismis.mp4

Bu, `bin/urun_gorsel_uret.py`'nin ürettiği sade ffmpeg videosunun (`-video.mp4`) YERİNE değil,
YANINA eklenen isteğe bağlı bir katmandır — o video hep üretilir ve güvenilir kalır. Bu script
`video-uretici/` (Node.js + Remotion) kurulu değilse, ya da `<cikti-onek>-9x16.jpg` henüz
üretilmemişse, sessizce "atlandı" ile çıkar (0 döner) — akış hiçbir zaman bloklanmaz.

Fiyat/indirim etiketi ve altyazı yalnız `veri/YYYY-Www.json` ve `bin/urun_gorsel_uret.py`'nin
ürettiği `.srt` dosyasından gelir; bu script ve Remotion bileşeni hiçbir sayı/cümle uydurmaz.
"""
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
NODE_PROJESI = KOK / "video-uretici"
GECICI_KOK = NODE_PROJESI / "public" / "gecici"


def _urun_bul(veri_dosyasi, kod):
    veri = json.loads(Path(veri_dosyasi).read_text(encoding="utf-8"))
    for urun in veri.get("urunler", []):
        if urun.get("kod") == kod:
            return urun
    return None


def _ses_suresi(yol):
    if not yol or not shutil.which("ffprobe"):
        return None
    komut = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
              "-of", "default=noprint_wrappers=1:nokey=1", yol]
    try:
        calisti = subprocess.run(komut, capture_output=True, timeout=15, text=True)
        return float(calisti.stdout.strip())
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return None


def kurulu_mu():
    return bool(shutil.which("npx")) and (NODE_PROJESI / "node_modules").is_dir()


def render(kod, veri_dosyasi, cikti_onek):
    if not kurulu_mu():
        return None
    gorsel = Path(f"{cikti_onek}-9x16.jpg")
    if not gorsel.exists():
        return None
    urun = _urun_bul(veri_dosyasi, kod) or {}
    ses_yolu = Path(f"{cikti_onek}-seslendirme.mp3")
    srt_yolu = Path(f"{cikti_onek}-altyazi.srt")
    ses_yolu = ses_yolu if ses_yolu.exists() else None
    altyazi_metni = srt_yolu.read_text(encoding="utf-8") if srt_yolu.exists() else None
    sure = _ses_suresi(str(ses_yolu)) if ses_yolu else None

    gecici_ad = f"{kod}-{uuid.uuid4().hex[:8]}"
    gecici_dizin = GECICI_KOK / gecici_ad
    gecici_dizin.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copyfile(gorsel, gecici_dizin / "gorsel.jpg")
        gorsel_yolu_props = f"gecici/{gecici_ad}/gorsel.jpg"
        ses_yolu_props = None
        if ses_yolu:
            shutil.copyfile(ses_yolu, gecici_dizin / "ses.mp3")
            ses_yolu_props = f"gecici/{gecici_ad}/ses.mp3"

        props = {
            "gorselYolu": gorsel_yolu_props,
            "sesYolu": ses_yolu_props,
            "altyaziSrtMetni": altyazi_metni,
            "baslik": urun.get("baslik"),
            "fiyat": urun.get("fiyat"),
            "indirim": urun.get("indirim"),
            "indirimOran": urun.get("indirim_oran"),
            "paraBirimi": urun.get("para_birimi") or "TL",
            "sureSaniye": sure or 6,
        }
        cikti = Path(f"{cikti_onek}-video-gelismis.mp4").resolve()
        cikti.parent.mkdir(parents=True, exist_ok=True)
        komut = ["npx", "remotion", "render", "src/index.jsx", "UrunVideosu", str(cikti),
                 "--props", json.dumps(props, ensure_ascii=False)]
        try:
            calisti = subprocess.run(komut, cwd=NODE_PROJESI, capture_output=True, timeout=180)
        except (subprocess.TimeoutExpired, OSError):
            return None
        return str(cikti) if calisti.returncode == 0 and cikti.exists() else None
    finally:
        shutil.rmtree(gecici_dizin, ignore_errors=True)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    kod, veri_dosyasi, cikti_onek = argv[0], argv[1], argv[2]
    sonuc = render(kod, veri_dosyasi, cikti_onek)
    print(json.dumps({
        "kod": kod,
        "video_gelismis": sonuc or "atlandı (Node/Remotion kurulu değil ya da 9x16 fotoğraf yok)",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
