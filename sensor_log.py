import dht
import machine
import time
import os

sensor_pin = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_UP)
sensor = dht.DHT22(sensor_pin)

LOG_FILE = "log.txt"
OLD_LOG_FILE = "log_old.txt"
MAX_FILE_SIZE = 1_000_000  # 1MB
UI_RECORDS = 200  # Κρατάει 200 μετρήσεις για το γράφημα

def read_sensor():
    try:
        sensor.measure()
        return sensor.temperature(), sensor.humidity()
    except OSError as e:
        print("Σφάλμα ανάγνωσης:", e)
        return None, None

def log_data(temp, hum):
    """Αποθηκεύει τη μέτρηση στη Flash με ασφάλεια."""
    if temp is None or hum is None:
        return
    
    # Έλεγχος μεγέθους για να μην γεμίσει ποτέ η Flash (Log Rotation)
    try:
        size = os.stat(LOG_FILE)[6]
        if size > MAX_FILE_SIZE:
            try:
                os.remove(OLD_LOG_FILE)
            except OSError:
                pass
            os.rename(LOG_FILE, OLD_LOG_FILE)
    except OSError:
        pass
        
    timestamp = time.ticks_ms() // 1000 
    new_record = "{},{},{}\n".format(timestamp, temp, hum)
    
    # Γράφει μόνο στο τέλος του αρχείου (ταχύτατο)
    with open(LOG_FILE, "a") as f:
        f.write(new_record)

def get_recent_history():
    """Φορτώνει μόνο τα τελευταία UI_RECORDS για να μην κρασάρει ο Server."""
    lines = []
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                lines.append(line.strip())
                if len(lines) > UI_RECORDS:
                    lines.pop(0) # Πετάει το παλαιότερο
    except OSError:
        pass
    return lines