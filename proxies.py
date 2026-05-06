import os
import time
import random
import itertools
import threading
import requests
from contextlib import contextmanager
from fake_useragent import UserAgent
from config import WEBSHARE_PROXY_URLS, PROXY_MODE, DIRECT_IP_DELAY, WEBSHARE_DELAY

ua = UserAgent()
_proxy_cycle = itertools.cycle(WEBSHARE_PROXY_URLS)
_proxy_lock = threading.Lock()
_env_proxy_lock = threading.Lock()
_request_times = {"webshare": 0, "direct": 0}
_request_locks = {"webshare": threading.Lock(), "direct": threading.Lock()}


def get_random_headers() -> dict:
    """Return realistic browser headers for each request."""
    return {
        "User-Agent":      ua.random,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer":         "https://www.google.com/",
        "DNT":             "1",
    }


def get_webshare_proxy() -> dict:
    """Return the next Webshare proxy as a requests-compatible dict."""
    if not WEBSHARE_PROXY_URLS:
        raise ValueError("WEBSHARE_PROXIES not set in .env")
    with _proxy_lock:
        proxy_url = next(_proxy_cycle)
    return {"http": proxy_url, "https": proxy_url}


def get_proxy_for_source(source: str) -> dict:
    """Get proxy dict for a given source: 'webshare' or 'direct'."""
    if source == "webshare":
        return get_webshare_proxy()
    elif source == "direct":
        return {}  # Empty dict = direct connection (own IP)
    else:
        raise ValueError(f"Unknown proxy source: {source}")


def apply_request_delay(source: str):
    """Apply staggered delay based on proxy source to avoid collisions."""
    if source == "webshare":
        delay_config = WEBSHARE_DELAY
    elif source == "direct":
        delay_config = DIRECT_IP_DELAY
    else:
        return
    
    with _request_locks[source]:
        now = time.time()
        last_request = _request_times[source]
        elapsed = now - last_request
        if elapsed < delay_config:
            sleep_time = delay_config - elapsed
            time.sleep(sleep_time)
        _request_times[source] = time.time()


@contextmanager
def webshare_env_proxy():
    """Set one rotating Webshare proxy as env vars for libraries that read env."""
    with _env_proxy_lock:
        old_http  = os.environ.get("HTTP_PROXY")
        old_https = os.environ.get("HTTPS_PROXY")
        proxy = get_webshare_proxy()["http"]
        os.environ["HTTP_PROXY"]  = proxy
        os.environ["HTTPS_PROXY"] = proxy
        try:
            yield
        finally:
            if old_http:
                os.environ["HTTP_PROXY"] = old_http
            else:
                os.environ.pop("HTTP_PROXY", None)
            if old_https:
                os.environ["HTTPS_PROXY"] = old_https
            else:
                os.environ.pop("HTTPS_PROXY", None)


@contextmanager
def env_proxy_for_source(source: str):
    """Set env proxy for a given source ('webshare' or 'direct')."""
    if source == "direct":
        old_http = os.environ.get("HTTP_PROXY")
        old_https = os.environ.get("HTTPS_PROXY")
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)
        try:
            yield
        finally:
            if old_http:
                os.environ["HTTP_PROXY"] = old_http
            if old_https:
                os.environ["HTTPS_PROXY"] = old_https
    else:
        with webshare_env_proxy():
            yield


def test_webshare() -> bool:
    """Test if the Webshare proxy is working. Returns True on success."""
    try:
        proxy  = get_webshare_proxy()
        resp   = requests.get("https://httpbin.org/ip", proxies=proxy, timeout=15)
        ip     = resp.json().get("origin", "unknown")
        print(f"[Proxy] Webshare OK - Exit IP: {ip}")
        return True
    except Exception as e:
        print(f"[Proxy] Webshare FAILED: {e}")
        return False


def test_direct() -> bool:
    """Test if direct IP connection is working. Returns True on success."""
    try:
        resp = requests.get("https://httpbin.org/ip", timeout=15)
        ip = resp.json().get("origin", "unknown")
        print(f"[Proxy] Direct IP OK - Exit IP: {ip}")
        return True
    except Exception as e:
        print(f"[Proxy] Direct IP FAILED: {e}")
        return False


def random_delay():
    """Sleep for a random human-like duration."""
    delay = random.uniform(5, 15)
    time.sleep(delay)
