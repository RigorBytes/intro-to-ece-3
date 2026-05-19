import serial
import time
import subprocess
import sys

# --- ΡΥΘΜΙΣΕΙΣ ---
COM_PORT = 'COM3'  # Άλλαξέ το ανάλογα με τη θύρα σου (π.χ. COM3, COM4, /dev/ttyUSB0)
BAUD_RATE = 115200
NGROK_DOMAIN = 'endanger-trickily-excavator.ngrok-free.dev'
TARGET_IP_PORT = '10.12.143.54:80'

def clean_and_reset_esp():
    print("[-] 1. Σύνδεση με το NodeMCU για καθαρισμό και reset...")
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=2)
        time.sleep(1) 
        
        print("[-] Αποστολή σήματος διακοπής (Ctrl+C)...")
        ser.write(b'\r\n\x03\x03')
        time.sleep(1)
        
        print("[-] Διαγραφή του αρχείου log.txt...")
        ser.write(b"import os\r\n")
        time.sleep(0.2)
        
        # ΔΙΟΡΘΩΣΗ: Χρήση καθαρών ASCII (αγγλικών) χαρακτήρων στο byte string
        cmd = b"try: os.remove('log.txt'); print('-> Log file deleted successfully!')\r\nexcept: print('-> No log file found to delete.')\r\n"
        ser.write(cmd)
        time.sleep(1)
        
        while ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if "->" in line:
                print(line)
        
        print("[-] Εκτέλεση Soft Reset (Ctrl+D)...")
        ser.write(b'\x04')
        time.sleep(1)
        
        ser.close()
        print("[+] Το NodeMCU καθαρίστηκε και επανεκκινήθηκε επιτυχώς!")
        
    except serial.SerialException as e:
        print(f"[!] Σφάλμα Σειριακής Θύρας: {e}")
        print("[!] ΠΡΟΣΟΧΗ: Βεβαιώσου ότι έχεις κλείσει το Thonny πριν τρέξεις το script!")
        sys.exit(1)

def start_ngrok():
    print(f"[-] 2. Εκκίνηση του ngrok tunnel στο domain: {NGROK_DOMAIN}...")
    cmd = f"ngrok http --domain={NGROK_DOMAIN} {TARGET_IP_PORT}"
    
    try:
        subprocess.Popen(cmd, shell=True)
        print("[+] Το τούνελ ngrok ξεκίνησε! Μπορείς να επισκεφθείς το link σου.")
    except Exception as e:
        print(f"[!] Αποτυχία εκκίνησης του ngrok: {e}")

if __name__ == "__main__":
    print("=== ΕΝΑΡΞΗ ΑΥΤΟΜΑΤΟΠΟΙΗΜΕΝΟΥ SETUP ===")
    clean_and_reset_esp()
    print("-" * 40)
    start_ngrok()
    print("=======================================")