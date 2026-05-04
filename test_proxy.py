"""
test_proxy.py - Verify Webshare rotating proxy is working correctly.
Usage: python test_proxy.py
"""
import requests
from config import WEBSHARE_PROXY_URLS
from proxies import get_webshare_proxy, get_random_headers, webshare_env_proxy

def test_full_pipeline():
    print("=" * 50)
    print(" Webshare Proxy Test")
    print("=" * 50)

    # 1. Basic connectivity for all configured Webshare endpoints.
    if not WEBSHARE_PROXY_URLS:
        print("\n[FAIL] No proxies configured. Check WEBSHARE_PROXIES in .env.")
        return
    for idx in range(len(WEBSHARE_PROXY_URLS)):
        try:
            proxy = get_webshare_proxy()
            resp = requests.get("https://httpbin.org/ip", proxies=proxy, timeout=15)
            ip = resp.json().get("origin", "unknown")
            print(f"[OK] Webshare proxy {idx + 1}/{len(WEBSHARE_PROXY_URLS)} - Exit IP: {ip}")
        except Exception as e:
            print(f"[FAIL] Webshare proxy {idx + 1}/{len(WEBSHARE_PROXY_URLS)} failed: {e}")
            return

    # 2. Test against a real Play Store app page
    print("\n[Test] Attempting to reach Play Store via proxy...")
    try:
        proxy   = get_webshare_proxy()
        headers = get_random_headers()
        url     = "https://play.google.com/store/apps/details?id=com.whatsapp"
        resp    = requests.get(url, proxies=proxy, headers=headers, timeout=20)
        if resp.status_code == 200:
            print(f"[OK] Play Store reachable! Status: {resp.status_code}")
        else:
            print(f"[WARN] Play Store returned status: {resp.status_code}")
    except Exception as e:
        print(f"[FAIL] Play Store request failed: {e}")

    # 3. Test google-play-scraper with proxy
    print("\n[Test] Testing google-play-scraper with proxy...")
    try:
        from google_play_scraper import app as gps_app
        with webshare_env_proxy():
            result = gps_app("com.whatsapp", lang="en", country="us")
        print("[OK] google-play-scraper OK!")
        print(f"   App: {result.get('title')}")
        print(f"   Installs: {result.get('installs')}")
        print(f"   Rating: {result.get('score')}")
    except Exception as e:
        print(f"[FAIL] google-play-scraper failed: {e}")

    print("\n" + "=" * 50)
    print(" Test Complete")
    print("=" * 50)


if __name__ == "__main__":
    test_full_pipeline()
