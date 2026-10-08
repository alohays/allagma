#!/usr/bin/env python3
"""Check external documentation links; keep local/repository checks separate."""
from concurrent.futures import ThreadPoolExecutor
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urlparse
from urllib.request import Request, urlopen

TLS = ssl.create_default_context()
if not ssl.get_default_verify_paths().cafile and Path("/etc/ssl/cert.pem").is_file():
    # Framework Python on macOS may have no installed OpenSSL CA bundle. Load
    # the OS trust bundle explicitly; never disable certificate verification.
    TLS.load_verify_locations(cafile="/etc/ssl/cert.pem")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == "href" and value and value.startswith("https://"):
                self.urls.add(urldefrag(value)[0])


def check(url):
    host, path = urlparse(url).netloc, urlparse(url).path
    if (host == "github.com" and path.startswith("/alohays/allagma")) or host == "alohays.github.io":
        return {"url": url, "status": "repository-or-prelaunch-endpoint",
                "note": "Repository links are checked against tracked targets at build; public endpoint activation is an owner launch action."}
    for method in ("HEAD", "GET"):
        try:
            request = Request(url, method=method, headers={"User-Agent": "Allagma-docs-link-check/1.0"})
            with urlopen(request, timeout=15, context=TLS) as response:
                return {"url": url, "status": "pass", "http_status": response.status, "resolved": response.url}
        except HTTPError as error:
            if method == "HEAD":
                continue
            return {"url": url, "status": "unverified" if error.code in (401,403,429) else "fail", "http_status": error.code}
        except (URLError, TimeoutError, OSError) as error:
            return {"url": url, "status": "unverified", "error": str(error)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    links = Links()
    for file in args.site.rglob("*.html"):
        links.feed(file.read_text())
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(check, sorted(links.urls)))
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "results": results,
              "limitations": "HTTP availability is not source validity. Blocked/rate-limited endpoints are explicitly unverified, not passing."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({status: sum(r["status"] == status for r in results)
                      for status in ("pass", "fail", "unverified", "repository-or-prelaunch-endpoint")}, indent=2))
    raise SystemExit(any(r["status"] in ("fail", "unverified") for r in results))
