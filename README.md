# GitHub DNS & uBlock Reklam Engelleyici Listesi

Bu repo, açık kaynak reklam ve takipçi (tracker) engelleme listelerini **her gün otomatik olarak** birleştirir, temizler ve **GitHub Pages** üzerinden modem, Pi-hole, AdGuard Home ve uBlock Origin için hazır URL'ler olarak yayınlar.

> **Not:** GitHub tek başına canlı bir DNS sunucusu (UDP:53) çalıştırmaz; bunun yerine modem/router veya DNS engelleyicilerin (AdGuard Home, Pi-hole, OpenWrt, Keenetic vb.) doğrudan okuyabileceği güncel engelleme listeleri sunar.

## Üretilen Listeler

GitHub Pages aktif edildikten sonra şu URL'ler oluşur (`<kullanici>` ve `<repo>` yerine kendi bilgilerinizi yazın):

- **Hosts formatı (Modem, Windows/Linux hosts, AdAway):**
  `https://<kullanici>.github.io/<repo>/hosts.txt`
- **Saf Domain listesi (Pi-hole, AdGuard Home):**
  `https://<kullanici>.github.io/<repo>/domains.txt`
- **Adblock formatı (uBlock Origin, AdGuard):**
  `https://<kullanici>.github.io/<repo>/adblock.txt`
- **Dnsmasq formatı (OpenWrt, Asuswrt-Merlin, Keenetic):**
  `https://<kullanici>.github.io/<repo>/dnsmasq.conf`

## Kurulum (GitHub'da Yayınlama)

1. Bu klasörü GitHub'da yeni bir repoya yükleyin (`git push`).
2. GitHub'da **Settings → Pages → Build and deployment → Source** kısmından **GitHub Actions** seçeneğini seçin.
3. **Actions** sekmesine girip **Update Adblock Lists** iş akışını **Run workflow** ile bir kez manuel başlatın.
4. İşlem bitince yukarıdaki URL'ler aktif olacaktır.

## Telefonda (Android APK) Kullanım

Bu listeyi telefonunuzda (root olmadan) kullanmak için açık kaynak APK uygulamalarından birini kurup liste URL'nizi ekleyebilirsiniz:

- **AdAway (Önerilen - Root gerektirmez):**
  1. [AdAway APK](https://adaway.org/) indirip kurun (VPN tabanlı engelleme modunu seçin).
  2. **Hosts Sources (Kaynaklar)** bölümüne girin ve `+` ile şu adresi ekleyin:
     `https://said19605353gemini-cell.github.io/dns-adblock-lists/hosts.txt`
- **personalDNSfilter / RethinkDNS (APK):**
  - Özel filtre / hosts URL'si kısmına `hosts.txt` veya `domains.txt` adresini yapıştırın.

## Kendi Kurallarınızı Ekleme

- `custom-block.txt`: Ekstra engellemek istediğiniz domainleri satır satır yazın.
- `custom-allow.txt`: Yanlışlıkla engellenen ve açmak istediğiniz domainleri yazın.
