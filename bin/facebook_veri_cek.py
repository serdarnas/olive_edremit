#!/usr/bin/env python3
"""Facebook/Instagram Graph API'den SALT OKUMA marka bahsi verisi çeker (marka-izleme okur).

Kullanım:
  python3 bin/facebook_veri_cek.py              → JSON listesi (sayfa + IG gönderi yorumları)
  python3 bin/facebook_veri_cek.py --kendini-sina  → token/kimlik doğrulamasını test eder, veri basmaz

Bu dosyada **hiçbir POST/publish/ads uç noktası çağrılmaz** — yalnız `urllib.request.urlopen` ile
GET isteği atılır, başka hiçbir HTTP metodu kullanılmaz (ANAYASA §1: hiçbir takım sosyal hesaba
yazamaz). `FACEBOOK_ACCESS_TOKEN` `.env`'de yoksa boş liste dönüp sessizce çıkar — koşuyu bloklamaz
(bkz. `FAL_KEY`'in twitter-icerik'teki "boş bırakılabilir" deseni).

`FACEBOOK_PAGE_ID` / `INSTAGRAM_BUSINESS_ID` `.env`'de boşsa `/me/accounts` ve
`{page-id}?fields=instagram_business_account` çağrılarıyla keşfedilir; bulunursa `--kendini-sina`
çıktısında gösterilir ki kullanıcı bunları `.env`'e ekleyebilsin.

Not: Instagram'ın "bizi başka birinin gönderisinde etiketledi" bilgisini (Mentions API) çekmek ayrı
bir uygulama incelemesi ve webhook aboneliği gerektirir — burada yalnız **kendi** sayfa/IG
gönderilerimize gelen yorumlar okunur. Bu da marka bahsi izlemek için pratik ve yeterli bir
başlangıçtır; tam "mention" taraması için WebSearch/X taraması (marka-izleme'nin zaten yaptığı) hâlâ
asıl yoldur.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402

API_SURUM = "v21.0"
TABAN = f"https://graph.facebook.com/{API_SURUM}"


def _get(yol, **parametreler):
    """Yalnız GET. Hata durumunda None döner, hiçbir zaman istisna fırlatmaz."""
    url = f"{TABAN}/{yol}?{urllib.parse.urlencode(parametreler)}"
    istek = urllib.request.Request(url, headers={"User-Agent": "a-sirketi/1.0"}, method="GET")
    try:
        with urllib.request.urlopen(istek, timeout=20) as yanit:
            return json.loads(yanit.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None


def sayfa_id_kesfet(token):
    veri = _get("me/accounts", access_token=token)
    hesaplar = (veri or {}).get("data") or []
    return hesaplar[0]["id"] if hesaplar and hesaplar[0].get("id") else None


def ig_id_kesfet(token, sayfa_id):
    veri = _get(sayfa_id, fields="instagram_business_account", access_token=token)
    ig = (veri or {}).get("instagram_business_account") or {}
    return ig.get("id")


def sayfa_yorumlari(token, sayfa_id):
    """Sayfa gönderilerine gelen yorumları düz liste hâline getirir (tweet_cek.py ile aynı şekil)."""
    veri = _get(f"{sayfa_id}/feed",
                fields="message,created_time,permalink_url,comments.limit(20){message,from,created_time,permalink_url}",
                access_token=token, limit=25)
    sonuc = []
    for gonderi in (veri or {}).get("data") or []:
        for yorum in (gonderi.get("comments") or {}).get("data") or []:
            sonuc.append({
                "link": yorum.get("permalink_url") or gonderi.get("permalink_url"),
                "kaynak": "facebook-yorum",
                "yazar": (yorum.get("from") or {}).get("name"),
                "metin": yorum.get("message"),
                "tarih": yorum.get("created_time"),
            })
    return sonuc


def instagram_yorumlari(token, ig_id):
    veri = _get(f"{ig_id}/media",
                fields="caption,timestamp,permalink,comments.limit(20){text,username,timestamp}",
                access_token=token, limit=25)
    sonuc = []
    for gonderi in (veri or {}).get("data") or []:
        for yorum in (gonderi.get("comments") or {}).get("data") or []:
            sonuc.append({
                "link": gonderi.get("permalink"),
                "kaynak": "instagram-yorum",
                "yazar": yorum.get("username"),
                "metin": yorum.get("text"),
                "tarih": yorum.get("timestamp"),
            })
    return sonuc


def kimlikleri_coz(token, ortam):
    sayfa_id = ortam.get("FACEBOOK_PAGE_ID") or sayfa_id_kesfet(token)
    ig_id = ortam.get("INSTAGRAM_BUSINESS_ID") or (ig_id_kesfet(token, sayfa_id) if sayfa_id else None)
    return sayfa_id, ig_id


def veri_cek():
    ortam = ayar.ortam_yukle()
    token = ortam.get("FACEBOOK_ACCESS_TOKEN")
    if not token:
        return []
    sayfa_id, ig_id = kimlikleri_coz(token, ortam)
    sonuc = []
    if sayfa_id:
        sonuc += sayfa_yorumlari(token, sayfa_id)
    if ig_id:
        sonuc += instagram_yorumlari(token, ig_id)
    return sonuc


def _me_ham(token):
    """`_get` gibi ama hata gövdesini yutmaz — `--kendini-sina` teşhis için gerçek Graph API
    hata mesajını (ör. 'token süresi dolmuş') gösterebilsin diye."""
    url = f"{TABAN}/me?" + urllib.parse.urlencode({"fields": "id,name", "access_token": token})
    istek = urllib.request.Request(url, headers={"User-Agent": "a-sirketi/1.0"}, method="GET")
    try:
        with urllib.request.urlopen(istek, timeout=20) as yanit:
            return json.loads(yanit.read().decode("utf-8")), None
    except urllib.error.HTTPError as hata:
        try:
            gövde = json.loads(hata.read().decode("utf-8"))
            return None, (gövde.get("error") or {}).get("message", str(hata))
        except (ValueError, OSError):
            return None, str(hata)
    except (urllib.error.URLError, TimeoutError, OSError) as hata:
        return None, str(hata)


def kendini_sina():
    ortam = ayar.ortam_yukle()
    token = ortam.get("FACEBOOK_ACCESS_TOKEN")
    if not token:
        print(json.dumps({"durum": "FACEBOOK_ACCESS_TOKEN yok (.env) — marka-izleme WebSearch'e düşer"},
                          ensure_ascii=False))
        return 1
    kim, hata = _me_ham(token)
    if not kim:
        print(json.dumps({"durum": "token geçersiz", "graph_api_hatasi": hata}, ensure_ascii=False))
        return 1
    sayfa_id, ig_id = kimlikleri_coz(token, ortam)
    print(json.dumps({"durum": "tamam", "token_sahibi": kim, "sayfa_id": sayfa_id,
                       "instagram_business_id": ig_id,
                       "not": "sayfa_id/instagram_business_id .env'e FACEBOOK_PAGE_ID / "
                              "INSTAGRAM_BUSINESS_ID olarak eklenirse tekrar keşfe gerek kalmaz"},
                      ensure_ascii=False, indent=2))
    return 0


def main(argv):
    if "--kendini-sina" in argv:
        return kendini_sina()
    print(json.dumps(veri_cek(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
