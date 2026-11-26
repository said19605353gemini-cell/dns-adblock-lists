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

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>DNS & uBlock Reklam Engelleyici</title>
  <style>
    :root {{ --bg:#0b0f19; --card:#131a2a; --text:#e5e7eb; --muted:#9ca3af; --accent:#38bdf8; --ok:#22c55e; --border:#1f2937; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:system-ui,-apple-system,sans-serif; background:var(--bg); color:var(--text); line-height:1.6; }}
    .wrap {{ max-width:860px; margin:0 auto; padding:32px 16px; }}
    h1 {{ margin:0 0 8px; font-size:1.9rem; }}
    .sub {{ color:var(--muted); margin-bottom:24px; }}
    .stats {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:24px; }}
    .pill {{ background:var(--card); border:1px solid var(--border); padding:8px 14px; border-radius:999px; font-size:.9rem; }}
    .pill b {{ color:var(--accent); }}
    .card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:18px; margin-bottom:16px; }}
    .card h2 {{ margin:0 0 10px; font-size:1.15rem; color:var(--accent); }}
    .row {{ display:flex; gap:8px; align-items:center; margin:8px 0; }}
    input {{ flex:1; background:#090d16; color:var(--text); border:1px solid var(--border); border-radius:8px; padding:10px; font-family:monospace; font-size:.88rem; }}
    button {{ background:var(--accent); color:#04101d; border:0; border-radius:8px; padding:10px 14px; font-weight:600; cursor:pointer; }}
    button:hover {{ opacity:.9; }}
    ul {{ margin:8px 0 0 18px; padding:0; color:var(--muted); }}
    li {{ margin:4px 0; }}
    code {{ background:#090d16; padding:2px 6px; border-radius:4px; color:var(--text); }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>DNS & uBlock Reklam Engelleyici</h1>
    <p class="sub">GitHub Actions ile her gün otomatik güncellenen modem, telefon (APK) ve tarayıcı reklam engelleme listeleri.</p>
    <div class="stats">
      <div class="pill">Engellenen Domain: <b>{len(sorted_domains):,}</b></div>
      <div class="pill">Son Güncelleme: <b>{now}</b></div>
    </div>

    <div class="card">
      <h2>Liste Adresleri (Tek Tıkla Kopyala)</h2>
      <div class="row"><input readonly value="https://said19605353gemini-cell.github.io/dns-adblock-lists/hosts.txt" id="u1" /><button onclick="cp('u1',this)">hosts.txt (APK / Modem)</button></div>
      <div class="row"><input readonly value="https://said19605353gemini-cell.github.io/dns-adblock-lists/domains.txt" id="u2" /><button onclick="cp('u2',this)">domains.txt (NextDNS / Pi-hole)</button></div>
      <div class="row"><input readonly value="https://said19605353gemini-cell.github.io/dns-adblock-lists/adblock.txt" id="u3" /><button onclick="cp('u3',this)">adblock.txt (uBlock Origin)</button></div>
      <div class="row"><input readonly value="https://said19605353gemini-cell.github.io/dns-adblock-lists/dnsmasq.conf" id="u4" /><button onclick="cp('u4',this)">dnsmasq.conf (Router)</button></div>
    </div>

    <div class="card">
      <h2>Telefonda (Android APK) Kurulum</h2>
      <ul>
        <li><b>AdAway (Root gerekmez):</b> VPN modunu seçin → Hosts Sources → <code>hosts.txt</code> linkini ekleyin.</li>
        <li><b>RethinkDNS / personalDNSfilter:</b> Özel filtre URL'si kısmına <code>hosts.txt</code> veya <code>domains.txt</code> ekleyin.</li>
      </ul>
    </div>

    <div class="card">
      <h2>Modem ve Gerçek IPv4 DNS Kurulumu</h2>
      <ul>
        <li><b>OpenWrt / Keenetic / Asuswrt:</b> <code>dnsmasq.conf</code> dosyasını yönlendiricinize bağlayın.</li>
        <li><b>Standart Modem (IPv4 DNS):</b> Ücretsiz <b>NextDNS</b> veya <b>AdGuard DNS</b> hesabınıza <code>domains.txt</code> linkini ekleyin; size verilen IPv4 adresini modeme yazın.</li>
      </ul>
    </div>
  </div>
  <script>
    function cp(id, btn) {{
      const el = document.getElementById(id);
      navigator.clipboard.writeText(el.value);
      const old = btn.textContent;
      btn.textContent = "Kopyalandı!";
      setTimeout(() => btn.textContent = old, 1500);
    }}
  </script>
</body>
</html>
"""
    (DIST / "index.html").write_text(html, encoding="utf-8")

    print(f"Tamamlandi! Toplam {len(sorted_domains)} domain dist/ klasorune yazildi.")


if __name__ == "__main__":
    main()
