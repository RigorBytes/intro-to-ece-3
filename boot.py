import network
import gc

gc.collect()

ap = network.WLAN(network.AP_IF)
ap.active(True)
# Ρύθμιση SSID και κωδικού (προαιρετικά)
ap.config(essid="ECE_Patras_Monitor", authmode=0)

print("[-] AP Active: ECE_Patras_Monitor")
print("[-] IP Address:", ap.ifconfig()[0]) # Συνήθως 192.168.4.1