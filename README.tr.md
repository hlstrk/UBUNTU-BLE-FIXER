# Ubuntu BLE Fixer

[English](README.md)

Ubuntu BLE Fixer, Bluetooth kulaklığın codec profilini masaüstü tepsisinden değiştirmeni sağlar. Uygulama PipeWire veya PulseAudio tarafından sunulan profilleri okur ve terminal açmadan seçim yapar.

## Özellikler

- Kurulum sırasında Ubuntu sürümünü, ses sunucusunu, masaüstü oturumunu ve Bluetooth ses kartlarını kontrol eder.
- Kulaklık ile Linux ses sisteminin anlaşabildiği codec profillerini gösterir.
- Yetkisiz bir `systemd --user` servisi olarak çalışır.
- Durum kontrolü ve codec değişimi için komut satırı aracı sunar.
- Çalışırken ağ bağlantısı kurmaz ve kullanım verisi toplamaz.

## Gereksinimler

- Ubuntu 22.04 veya daha yeni bir sürüm
- AppIndicator destekli masaüstü oturumu
- Ubuntu ayarlarından eşleştirilmiş Bluetooth kulaklık

Kurulum betiği gerekli Ubuntu paketlerini belirler. Değişiklik yapmadan önce sistem bilgilerini, paket listesini ve kurulum dizinini gösterir.

## Tek komutla kurulum

```bash
curl -fsSL https://raw.githubusercontent.com/hlstrk/UBUNTU-BLE-FIXER/main/install.sh | bash
```

Betik senden onay ister. `sudo` yetkisini yalnızca eksik Ubuntu paketlerini kurmak için kullanır. Uygulama dosyalarını `~/.local` altına yerleştirir ve kullanıcı servisini etkinleştirir.

Onay sorusunu atlamak için:

```bash
curl -fsSL https://raw.githubusercontent.com/hlstrk/UBUNTU-BLE-FIXER/main/install.sh | bash -s -- --yes
```

Kurulum planını değişiklik yapmadan görmek için repoyu klonlayıp şu komutu çalıştır:

```bash
./install.sh --dry-run
```

## Kullanım

Üst çubuktaki kulaklık simgesine tıkla ve codec seç. Menü aktif codec'i işaretler, bağlantı değiştiğinde kendini yeniler.

Komut satırından kullanım:

```bash
ubuntu-ble-fixer status
ubuntu-ble-fixer doctor
ubuntu-ble-fixer set aptx --device "MOMENTUM 4"
ubuntu-ble-fixer set ldac --device "WH-1000XM5"
ubuntu-ble-fixer status --json
```

PipeWire veya PulseAudio hangi profillerin kullanılabileceğine karar verir. Bluetooth adaptörü, kulaklık veya kurulu ses sistemi bir codec'i sunmuyorsa uygulama o codec'i ekleyemez.

## Kulaklık desteği

Uygulama, A2DP profillerini `pactl` üzerinden sunan tüm BlueZ ses kartlarıyla çalışır. Kısa tepsi adları için şu aileleri tanır:

| Marka | Aileler |
| --- | --- |
| Sennheiser | MOMENTUM 4 |
| Sony | WH-1000XM3 ile XM6, WF-1000XM3 ile XM6 |
| Bose | QuietComfort ve QC modelleri |
| Apple | AirPods ve AirPods Max |
| Samsung | Galaxy Buds |
| JBL | Tour, Live, Tune ve Quantum |
| Anker | Soundcore ve Space modelleri |

Listede bulunmayan kulaklıklar Bluetooth adlarıyla görünür ve codec seçimi çalışmaya devam eder.

## Servis yönetimi

```bash
systemctl --user status ubuntu-ble-fixer.service
systemctl --user restart ubuntu-ble-fixer.service
journalctl --user -u ubuntu-ble-fixer.service -n 50
```

## Kaldırma

```bash
~/.local/share/ubuntu-ble-fixer/uninstall.sh
```

Kaldırıcı kullanıcı servisini ve uygulama dosyalarını siler. Başka masaüstü programları kullanabileceği için Ubuntu paketlerine dokunmaz.

## Sorun giderme

Önce sistem raporunu al:

```bash
ubuntu-ble-fixer doctor
```

Tepsi simgesi görünmüyorsa servisi ve Ubuntu AppIndicator eklentisini kontrol et:

```bash
systemctl --user status ubuntu-ble-fixer.service
gnome-extensions enable ubuntu-appindicators@ubuntu.com
systemctl --user restart ubuntu-ble-fixer.service
```

Bir codec görünmüyorsa kulaklığı yeniden bağla ve `pactl list cards` çıktısını kontrol et. Uygulamanın seçebilmesi için codec'in kullanılabilir A2DP profili olarak listelenmesi gerekir.

## Lisans

[MIT](LICENSE)
