import network
import time
import ntptime
import secrets
import gc

gc.collect()

# 1. ΠΡΩΤΑ ρυθμίζουμε το STA mode (Προσπάθεια σύνδεσης στο Internet)
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
    print("[-] ΔΕΝ βρέθηκε ίντερνετ. Απενεργοποίηση STA για σταθερότητα του AP.")
    sta.active(False) # <--- ΚΡΙΣΙΜΗ ΠΡΟΣΘΗΚΗ: Σταματάει το background scanning

# 2. ΜΕΤΑ ρυθμίζουμε το AP mode (Το ESP φτιάχνει το δικό του δίκτυο)
ap = network.WLAN(network.AP_IF)
ap.active(True)
# Χρήση authmode=4 (WPA/WPA2-PSK) για μέγιστη συμβατότητα με σύγχρονα κινητά
ap.config(essid=secrets.AP_SSID, password=secrets.AP_PASS, authmode=4)

print("[-] Δημιουργήθηκε το δίκτυο:", secrets.AP_SSID)
print("[-] IP του Web Server:", ap.ifconfig()[0])