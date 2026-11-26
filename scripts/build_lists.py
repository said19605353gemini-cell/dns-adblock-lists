#!/usr/bin/env python3
"""
GitHub Actions ile otomatik güncellenen DNS & uBlock reklam engelleme listesi üreticisi.
Çıktılar (dist/ klasörüne):
  - hosts.txt     : Modem, /etc/hosts, AdAway için (0.0.0.0 domain)
  - domains.txt   : Pi-hole, AdGuard Home için saf domain listesi
  - adblock.txt   : uBlock Origin, AdGuard için (||domain^)
  - dnsmasq.conf  : Router/Modem dnsmasq için (address=/domain/)
"""

import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)

# Güvenilir açık kaynak reklam & tracker listeleri
SOURCES = [
    # StevenBlack Unified Hosts (reklam + zararlı yazılım)
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
    # Peter Lowe's Ad and tracking server list
    "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=0&mimetype=plaintext",
    # HaGeZi Multi LIGHT (hafif ve güvenli genel engelleme)
    "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/light.txt",
]

DOMAIN_RE = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
)

IGNORE_DOMAINS = {
    "localhost",
    "localhost.localdomain",
    "local",
    "broadcasthost",
    "ip6-localhost",
    "ip6-loopback",
    "ip6-localnet",
    "ip6-mcastprefix",
    "ip6-allnodes",
    "ip6-allrouters",
    "ip6-allhosts",
    "0.0.0.0",
}


def load_local_list(filename: str) -> set[str]:
    path = ROOT / filename
    items: set[str] = set()
    if not path.exists():
        return items
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip().lower()
        if line and DOMAIN_RE.match(line):
            items.add(line)
    return items


def parse_line(line: str) -> str | None:
    line = line.split("#", 1)[0].strip().lower()
    if not line or line.startswith(("!", "[")):
        return None

    # hosts formatı: 0.0.0.0 domain.com veya 127.0.0.1 domain.com
    parts = line.split()
    if len(parts) >= 2 and parts[0] in {"0.0.0.0", "127.0.0.1", "::1"}:
        candidate = parts[1]
    elif line.startswith("||") and "^" in line:
        # adblock formatı: ||domain.com^
        candidate = line[2:].split("^", 1)[0]
    else:
        candidate = parts[0]

    if candidate in IGNORE_DOMAINS:
        return None
    if DOMAIN_RE.match(candidate):
        return candidate
    return None


def fetch_domains(url: str) -> set[str]:
    domains: set[str] = set()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (DNS-Adblock-Builder)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8", errors="ignore")
    for line in text.splitlines():
        d = parse_line(line)
        if d:
            domains.add(d)
    return domains


def main() -> None:
    blocked: set[str] = set()
    for url in SOURCES:
        try:
            fetched = fetch_domains(url)
            print(f"[OK] {url} -> {len(fetched)} domain")
            blocked.update(fetched)
        except Exception as exc:
            print(f"[WARN] {url} indirilemedi: {exc}")

    blocked.update(load_local_list("custom-block.txt"))
    allowed = load_local_list("custom-allow.txt")
    blocked -= allowed

    sorted_domains = sorted(blocked)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = (
        f"# DNS Adblock List - Son Guncelleme: {now}\n"
        f"# Toplam Engellenen Domain: {len(sorted_domains)}\n"
    )

    (DIST / "domains.txt").write_text(
        header + "\n".join(sorted_domains) + "\n", encoding="utf-8"
    )
    (DIST / "hosts.txt").write_text(
        header + "\n".join(f"0.0.0.0 {d}" for d in sorted_domains) + "\n",
        encoding="utf-8",
    )
    (DIST / "adblock.txt").write_text(
        header.replace("#", "!")
        + "\n".join(f"||{d}^" for d in sorted_domains)
        + "\n",
        encoding="utf-8",
    )
    (DIST / "dnsmasq.conf").write_text(
        header + "\n".join(f"address=/{d}/" for d in sorted_domains) + "\n",
        encoding="utf-8",
    )

    print(f"Tamamlandi! Toplam {len(sorted_domains)} domain dist/ klasorune yazildi.")


if __name__ == "__main__":
    main()
