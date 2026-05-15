import network
import time
import ntptime
import secrets
import gc

gc.collect()

# Απενεργοποίηση AP mode
ap = network.WLAN(network.AP_IF)
ap.active(False)

# Σύνδεση στο δίκτυο
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(secrets.WIFI_SSID, secrets.WIFI_PASS)

print("[-] Σύνδεση στο WiFi", end="")
while not sta.isconnected():
    time.sleep(1)
    print(".", end="")

print("\n[-] IP Address:", sta.ifconfig()[0])

# Συγχρονισμός Ώρας μέσω NTP
try:
    ntptime.settime()
    print("[-] Η ώρα συγχρονίστηκε επιτυχώς.")
except Exception as e:
    print("[-] Σφάλμα NTP:", e)