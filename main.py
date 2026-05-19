import socket
import ssl
import ubinascii
import os
import time
import gc
import sensor_log
import secrets

def send_email(temp, hum):
    """Στέλνει τα δεδομένα μεσω Gmail (raw SMTP)."""
    try:
        addr = socket.getaddrinfo(secrets.SMTP_SERVER, secrets.SMTP_PORT)[0][-1]
        s = socket.socket()
        s.settimeout(5.0)
        s.connect(addr)
        s = ssl.wrap_socket(s)
        
        def rx(): return s.readline()
        
        rx()
        s.write(b"EHLO esp\r\n"); rx(); rx(); rx(); rx(); rx(); rx(); rx()
        s.write(b"AUTH LOGIN\r\n"); rx()
        s.write(ubinascii.b2a_base64(secrets.SENDER_EMAIL.encode()).strip() + b"\r\n"); rx()
        s.write(ubinascii.b2a_base64(secrets.SENDER_PASSWORD.encode()).strip() + b"\r\n"); rx()
        s.write(b"MAIL FROM:<" + secrets.SENDER_EMAIL.encode() + b">\r\n"); rx()
        s.write(b"RCPT TO:<" + secrets.RECIPIENT_EMAIL.encode() + b">\r\n"); rx()
        s.write(b"DATA\r\n"); rx()
        
        msg = f"Subject: ECE Patras Alert\n\nΤρεχουσες μετρησεις:\nΘερμοκρασια: {temp}C\nΥγρασια: {hum}%\nΔειτε το log.txt στο Web Server."
        s.write(msg.encode('utf-8') + b"\r\n.\r\n"); rx()
        s.write(b"QUIT\r\n")
        s.close()
        return True
    except Exception as e:
        print("Mail error:", e)
        return False

def send_web_page(conn, temp, hum): 
    """Παράγει και στέλνει το HTML τμηματικά (chunks) με πλήρη διαγράμματα Chart.js και χρονική σήμανση."""
    history = sensor_log.get_recent_history()
    
    temp_data, hum_data, labels_data = [], [], []
    for record in history:
        parts = record.split(',')
        if len(parts) >= 3:
            # Απομόνωση της ώρας (HH:MM:SS) από το πλήρες timestamp για τον άξονα Χ
            time_part = parts[0].split(' ')
            if len(time_part) > 1:
                labels_data.append(time_part[1])
            else:
                labels_data.append("")
            temp_data.append(parts[1])
            hum_data.append(parts[2])
            
    if temp is not None and hum is not None:
        # Υπολογισμός τρέχουσας ώρας για τη νέα εγγραφή
        t = time.localtime(time.time() + 7200)
        current_time_str = "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])
        labels_data.append(current_time_str)
        temp_data.append(str(temp))
        hum_data.append(str(hum))
        
    js_temp_data = "[" + ",".join(temp_data) + "]"
    js_hum_data = "[" + ",".join(hum_data) + "]"
    js_labels = "['" + "','".join(labels_data) + "']"
    
    t_str = str(temp) if temp is not None else "--"
    h_str = str(hum) if hum is not None else "--"
    
    reaction = " 😊 Κανονική θερμοκρασία"
    if temp is not None:
        if temp > 25.0:
            reaction = " 🥵 Ουφ έσκασα!"
        elif temp < 15.0:
            reaction = " 🥶 Κρυώνω!"

    # Κομμάτι 1: HTTP Headers
    conn.sendall('HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\n\r\n'.encode('utf-8'))
    
    # Κομμάτι 2: HTML Head & CSS Styles
    html_head = """<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="utf-8">
    <title>ECE Patras Weather Station</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: sans-serif; text-align: center; background: #f4f4f4; padding-bottom: 30px;}
        .container { width: 90%; max-width: 700px; margin: auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
        .widgets { display: flex; justify-content: space-around; margin-bottom: 10px; }
        .value { font-size: 2.5em; font-weight: bold; }
        .temp-color { color: #ff6384; }
        .hum-color { color: #36a2eb; }
        button { padding: 10px 15px; margin: 5px; cursor: pointer; border-radius: 5px; border: none; font-weight:bold;}
        .btn-blue { background-color: #36a2eb; color: white; }
        .btn-red { background-color: #ff6384; color: white; }
        .chart-container { margin-top: 25px; padding: 15px; background: #fafafa; border-radius: 10px; border: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="container">
"""
    conn.sendall(html_head.encode('utf-8'))
    
    # Κομμάτι 3: Κύριο UI & Τρέχουσες Μετρήσεις
    html_body = f"""        <h1>Σταθμός ECE Patras</h1>
        <h2 style="color: #555;">{reaction}</h2>
        
        <div class="widgets">
            <div><p>Θερμοκρασία</p><span class="value temp-color">{t_str}°C</span></div>
            <div><p>Υγρασία</p><span class="value hum-color">{h_str}%</span></div>
        </div>
"""
    conn.sendall(html_body.encode('utf-8'))
    
    # Κομμάτι 4: Διαχείριση (Buttons, Φόρμα Διαγραφής) & Containers για τα διαγράμματα
    html_buttons = """        <div style="margin-bottom: 30px; border-top: 1px solid #ccc; padding-top: 15px;">
            <a href="/download"><button class="btn-blue">📥 Λήψη Δεδομένων (Log)</button></a>
            <a href="/email"><button class="btn-blue">✉️ Αποστολή Email</button></a>
            
            <form action="/delete" method="GET" style="margin-top:15px;">
                <input type="password" name="admin_pass" placeholder="Κωδικός Admin" required>
                <button type="submit" class="btn-red">🗑️ Διαγραφή Ιστορικού</button>
            </form>
        </div>
        
        <div class="chart-container"><canvas id="tempChart"></canvas></div>
        <div class="chart-container"><canvas id="humChart"></canvas></div>
    </div>
"""
    conn.sendall(html_buttons.encode('utf-8'))
    
    # Κομμάτι 5: Javascript κώδικας για το Chart.js & κλείσιμο ετικετών
    html_script = f"""    <script>
        const commonLabels = {js_labels};
        new Chart(document.getElementById('tempChart'), {{ 
            type: 'line', 
            data: {{ 
                labels: commonLabels, 
                datasets: [{{ 
                    label: 'Θερμοκρασία (°C)', 
                    data: {js_temp_data}, 
                    borderColor: 'rgb(255, 99, 132)', 
                    backgroundColor: 'rgba(255, 99, 132, 0.2)', 
                    fill: true, 
                    tension: 0.2, 
                    pointRadius: 2 
                }}] 
            }}, 
            options: {{ responsive: true, animation: false }}
        }});
        
        new Chart(document.getElementById('humChart'), {{ 
            type: 'line', 
            data: {{ 
                labels: commonLabels, 
                datasets: [{{ 
                    label: 'Υγρασία (%)', 
                    data: {js_hum_data}, 
                    borderColor: 'rgb(54, 162, 235)', 
                    backgroundColor: 'rgba(54, 162, 235, 0.2)', 
                    fill: true, 
                    tension: 0.2, 
                    pointRadius: 2 
                }}] 
            }}, 
            options: {{ responsive: true, animation: false }}
        }});
    </script>
</body>
</html>
"""
    conn.sendall(html_script.encode('utf-8'))

# Αρχικοποίηση Socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 80))
s.listen(5)

print("[-] Web Server started.")

while True:
    gc.collect()  # Αναγκαστική απελευθέρωση "ορφανής" μνήμης RAM σε κάθε λούπα
    try:
        conn, addr = s.accept()
        conn.settimeout(3.0)
        request = conn.recv(1024).decode('utf-8')
        
        if not request:
            conn.close()
            continue
            
        # 1. Λειτουργία Download
        if "GET /download" in request:
            conn.sendall('HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Disposition: attachment; filename="log.txt"\r\nConnection: close\r\n\r\n'.encode('utf-8'))
            try:
                with open(sensor_log.LOG_FILE, 'r') as f:
                    for line in f:
                        conn.sendall(line.encode('utf-8'))
            except OSError:
                conn.sendall("Δεν βρέθηκαν δεδομένα.".encode('utf-8'))
                
        # 2. Λειτουργία Διαγραφής
        elif "GET /delete" in request:
            if "admin_pass=" + secrets.ADMIN_PASS in request:
                try:
                    os.remove(sensor_log.LOG_FILE)
                    msg = "Η μνήμη διαγράφηκε! <br><br><a href='/'>Επιστροφή</a>"
                except OSError:
                    msg = "Δεν υπάρχει αρχείο για διαγραφή. <br><br><a href='/'>Επιστροφή</a>"
            else:
                msg = "Λάθος κωδικός Admin! <br><br><a href='/'>Επιστροφή</a>"
            
            conn.sendall(('HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\n\r\n<meta charset="utf-8">' + msg).encode('utf-8'))
            
        # 3. Λειτουργία Email
        elif "GET /email" in request:
            temp, hum = sensor_log.read_sensor()
            success = send_email(temp, hum)
            if success:
                msg = "Το email εστάλη επιτυχώς! <br><br><a href='/'>Επιστροφή</a>"
            else:
                msg = "Αποτυχία αποστολής! (Ελέγξτε κωδικούς/δίκτυο). <br><br><a href='/'>Επιστροφή</a>"
                
            conn.sendall(('HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\n\r\n<meta charset="utf-8">' + msg).encode('utf-8'))
            
        # 4. Αρχική Σελίδα
        elif "GET / " in request:
            temp, hum = sensor_log.read_sensor()
            sensor_log.log_data(temp, hum)
            
            # Κλήση της συνάρτησης που στέλνει τμηματικά τη σελίδα
            send_web_page(conn, temp, hum)
            
        # 5. Απόρριψη λοιπών αιτημάτων (δεν σπαταλάμε πόρους για favicon)
        else:
            conn.sendall('HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n'.encode('utf-8'))
            
        # Καθυστερούμε ελάχιστα για να προλάβει το Wi-Fi interface να αδειάσει τα TX buffers του
        time.sleep(0.1)
        conn.close()
        
    except OSError:
        try:
            conn.close()
        except:
            pass
    except Exception as e:
        print("\n[!] Εσωτερικό σφάλμα εκτέλεσης:", e)
        try:
            conn.close()
        except:
            pass