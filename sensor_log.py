import dht
import machine
import time
import os

sensor_pin = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_UP)
sensor = dht.DHT22(sensor_pin)

LOG_FILE = "log.txt"
OLD_LOG_FILE = "log_old.txt"
MAX_FILE_SIZE = 1_000_000
UI_RECORDS = 50

# Μνήμη (Caching) για να μην κρασάρει ο DHT22 από απανωτά requests
last_read_time = 0
cached_temp = None
cached_hum = None

def get_timestamp():
    t = time.localtime(time.time() + 7200)
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(t[0], t[1], t[2], t[3], t[4], t[5])

def read_sensor():
    global last_read_time, cached_temp, cached_hum
    current_time = time.ticks_ms()
    
    # Διαβάζει τον αισθητήρα ΜΟΝΟ αν έχουν περάσει 3 δευτερόλεπτα από την τελευταία φορά
    if last_read_time == 0 or time.ticks_diff(current_time, last_read_time) > 3000:
        try:
            sensor.measure()
            cached_temp = sensor.temperature()
            cached_hum = sensor.humidity()
            last_read_time = current_time
        except OSError as e:
            print("Σφάλμα ανάγνωσης DHT22:", e)
            # Αν αποτύχει η νέα μέτρηση, θα επιστρέψει τις παλιές cached τιμές

    return cached_temp, cached_hum

def log_data(temp, hum):
    if temp is None or hum is None:
        return
    try:
        size = os.stat(LOG_FILE)[6]
        if size > MAX_FILE_SIZE:
            try: os.remove(OLD_LOG_FILE)
            except OSError: pass
            os.rename(LOG_FILE, OLD_LOG_FILE)
    except OSError:
        pass
        
    timestamp = get_timestamp()
    new_record = "{},{},{}\n".format(timestamp, temp, hum)
    
    with open(LOG_FILE, "a") as f:
        f.write(new_record)

def get_recent_history():
    lines = []
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                lines.append(line.strip())
                if len(lines) > UI_RECORDS:
                    lines.pop(0)
    except OSError:
        pass
    return lines