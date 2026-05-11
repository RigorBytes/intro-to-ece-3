import dht
import machine
import time

# Ρύθμιση του αισθητήρα DHT22 στο GPIO2 (D4)
# Ενεργοποιούμε το Internal Pull-up resistor μέσω κώδικα
sensor_pin = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_UP)
sensor = dht.DHT22(sensor_pin)

LOG_FILE = "log.txt"
MAX_RECORDS = 20  # Αποθήκευση των τελευταίων 20 μετρήσεων

def read_sensor():
    """Διαβάζει θερμοκρασία και υγρασία από τον DHT22."""
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()
        return temp, hum
    except OSError as e:
        print("Σφάλμα ανάγνωσης αισθητήρα:", e)
        return None, None

def get_history():
    """Ανακτά τα ιστορικά δεδομένα από τη Flash."""
    try:
        with open(LOG_FILE, "r") as f:
            return f.readlines()
    except OSError:
        # Αν το αρχείο δεν υπάρχει ακόμα (πρώτη εκτέλεση), επιστρέφει κενή λίστα
        return []

def log_data(temp, hum):
    """Καταγράφει τη νέα μέτρηση και διατηρεί το όριο των MAX_RECORDS."""
    if temp is None or hum is None:
        return
    
    # Χρησιμοποιούμε τα ticks του συστήματος ως υποτυπώδες timestamp 
    # (καθώς στο AP mode δεν έχουμε internet για NTP time)
    timestamp = time.ticks_ms() // 1000 
    new_record = "{},{},{}\n".format(timestamp, temp, hum)
    
    # Φόρτωση παλιών εγγραφών
    records = get_history()
    
    # Προσθήκη νέας εγγραφής
    records.append(new_record)
    
    # Διατήρηση μόνο των τελευταίων MAX_RECORDS
    if len(records) > MAX_RECORDS:
        records = records[-MAX_RECORDS:]
        
    # Εγγραφή των ανανεωμένων δεδομένων στη Flash (στο log.txt)
    with open(LOG_FILE, "w") as f:
        for r in records:
            f.write(r)
            
    print("Καταγράφηκε:", new_record.strip())