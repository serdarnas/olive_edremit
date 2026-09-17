#!/usr/bin/env python3
"""Ürün veri çekici — SoftTr XML beslemesinden ürün kataloğunu çeker, sade şemaya indirger.

Kullanım: python3 bin/urun_veri_cek.py
Çıktı: takimlar/urun-pazarlama/veri/YYYY-Www.json (aynı hafta üzerine yazar) + stdout özet.

Kaynak `.env` içindeki NIDA_XML_URL (bkz. sirket/KURUMSAL-BILGILER.md "Ürün veri kaynağı" — gizli
değil). Besleme ulaşılamaz ya da bozuksa "hata" ile çıkar — eski veriyi bugünkü gibi sunmaz.
"""
import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402


def _sayi(ham):
    try:
        return float(str(ham).replace(",", ".")) if ham not in (None, "") else None
    except ValueError:
        return None


def _metin(urun, etiket):
    return (urun.findtext(etiket) or "").strip() or None


def _resimler(urun):
    """`Resimler` altındaki dolu `ResimN` etiketlerinin tümü, sırayla — beslemede zaten var olan
    ama eskiden atılan 2.-6. fotoğraflar da dahil (bkz. defter.md: görsel/video eksikliği dersi)."""
    kapsayici = urun.find("Resimler")
    if kapsayici is None:
        return []
    return [cocuk.text.strip() for cocuk in kapsayici if cocuk.text and cocuk.text.strip()]


def urun_esle(urun):
    """XML `<Urun>` düğümü → sade şema. Besleme dışı hiçbir alan eklenmez, uydurulmaz."""
    resimler = _resimler(urun)
    return {"kod": _metin(urun, "Kod"), "barkod": _metin(urun, "Barkod"),
            "baslik": _metin(urun, "Baslik"), "kategori": _metin(urun, "Kategori"),
            "ana_kategori": _metin(urun, "AnaKategori"),
            "fiyat": _sayi(_metin(urun, "Fiyat")), "indirim": _sayi(_metin(urun, "Indirim")),
            "indirim_oran": _sayi(_metin(urun, "IndirimOran")),
            "para_birimi": _metin(urun, "ParaBirimi") or "TL",
            "stok": int(_sayi(_metin(urun, "Stok")) or 0),
            "durum": _metin(urun, "Durum") == "1",
            "resim": resimler[0] if resimler else None, "resimler": resimler}


def xml_cek(url):
    istek = urllib.request.Request(url, headers={"User-Agent": "a-sirketi/1.0"})
    try:
        with urllib.request.urlopen(istek, timeout=20) as yanit:
            kok = ET.fromstring(yanit.read())
    except (urllib.error.URLError, TimeoutError, ET.ParseError, OSError) as hata:
        return {"hata": f"besleme okunamadı: {hata}"}
    urunler = [urun_esle(u) for u in kok.findall("Urun") if _metin(u, "Kod")]
    return {"cekim_zamani": ayar.simdi_iso(), "kaynak": url, "urun_sayisi": len(urunler),
            "urunler": urunler}


def hafta_dosyasi(kok, zaman=None):
    yil, hafta, _ = (zaman or datetime.now(timezone.utc)).isocalendar()
    return Path(kok) / "takimlar/urun-pazarlama/veri" / f"{yil}-W{hafta:02d}.json"


def main(argv):
    ayar.ortam_yukle()
    url = os.environ.get("NIDA_XML_URL")
    if not url:
        print(json.dumps({"hata": "NIDA_XML_URL yok (.env)"}, ensure_ascii=False), file=sys.stderr)
        return 1
    veri = xml_cek(url)
    if "hata" in veri:
        print(json.dumps(veri, ensure_ascii=False), file=sys.stderr)
        return 1
    yol = hafta_dosyasi(ayar.KOK)
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dosya": str(yol.relative_to(ayar.KOK)), "urun_sayisi": veri["urun_sayisi"]},
                      ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
