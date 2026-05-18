import network
import time
import ntptime
import secrets
import gc

gc.collect()

# 1. Ενεργοποίηση AP mode (Το ESP φτιάχνει το δικό του δίκτυο)
ap = network.WLAN(network.AP_IF)
ap.active(True)
# Προσθήκη authmode=3 για να κλειδώσει με WPA2-PSK και να ζητάει κωδικό
ap.config(essid=secrets.AP_SSID, password=secrets.AP_PASS, authmode=3)
print("[-] Δημιουργήθηκε το δίκτυο:", secrets.AP_SSID)
print("[-] IP του Web Server:", ap.ifconfig()[0])

# 2. Ενεργοποίηση STA mode (Το ESP ψάχνει για ίντερνετ στο κινητό σου)
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(secrets.WIFI_SSID, secrets.WIFI_PASS)

print("[-] Προσπάθεια σύνδεσης στο Internet (Hotspot)", end="")
timeout = 15 # Περιμένει το πολύ 15 δευτερόλεπτα
while not sta.isconnected() and timeout > 0:
    time.sleep(1)
    print(".", end="")
    timeout -= 1

print("\n")
if sta.isconnected():
    print("[-] Συνδέθηκε στο ίντερνετ επιτυχώς!")
    try:
        ntptime.settime()
        print("[-] Η ώρα συγχρονίστηκε (NTP).")
    except Exception as e:
        print("[-] Σφάλμα συγχρονισμού ώρας:", e)
else:
    print("[-] ΔΕΝ βρέθηκε ίντερνετ. Ο Web Server θα ξεκινήσει, αλλά τα email δεν θα λειτουργούν.")