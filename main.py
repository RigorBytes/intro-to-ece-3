import socket
import ssl
import ubinascii
import os
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

# Προσθέσαμε τα temp, hum στα ορίσματα της συνάρτησης
def web_page(temp, hum): 
    history = sensor_log.get_recent_history()
    
    temp_data, hum_data = [], []
    for record in history:
        parts = record.split(',')
        if len(parts) >= 3:
            temp_data.append(parts[1])
            hum_data.append(parts[2])
            
    if temp is not None and hum is not None:
        temp_data.append(str(temp))
        hum_data.append(str(hum))
        
    js_temp_data = "[" + ",".join(temp_data) + "]"
    js_hum_data = "[" + ",".join(hum_data) + "]"
    js_labels = "['" + "','".join(["" for _ in range(len(temp_data))]) + "']"
    
    t_str = str(temp) if temp is not None else "--"
    h_str = str(hum) if hum is not None else "--"
    
    # --- Λειτουργία Αντίδρασης ---
    reaction = " 😊 Κανονική θερμοκρασία"
    if temp is not None:
        if temp > 25.0:
            reaction = " 🥵 Ουφ έσκασα!"
        elif temp < 15.0:
            reaction = " 🥶 Κρυώνω!"

    html = """
    <!DOCTYPE html>
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Σταθμός ECE Patras</h1>
            <h2 style="color: #555;">""" + reaction + """</h2>
            
            <div class="widgets">
                <div><p>Θερμοκρασία</p><span class="value temp-color">""" + t_str + """°C</span></div>
                <div><p>Υγρασία</p><span class="value hum-color">""" + h_str + """%</span></div>
            </div>
            
            <div style="margin-bottom: 30px; border-top: 1px solid #ccc; padding-top: 15px;">
                <a href="/download"><button class="btn-blue">📥 Λήψη Δεδομένων (Log)</button></a>
                <a href="/email"><button class="btn-blue">✉️ Αποστολή Email</button></a>
                
                <form action="/delete" method="GET" style="margin-top:15px;">
                    <input type="password" name="admin_pass" placeholder="Κωδικός Admin" required>
                    <button type="submit" class="btn-red">🗑️ Διαγραφή Ιστορικού</button>
                </form>
            </div>
            
            <div><canvas id="tempChart"></canvas></div>
            <div><canvas id="humChart"></canvas></div>
        </div>
        <script>
            const commonLabels = """ + js_labels + """;
            new Chart(document.getElementById('tempChart'), { type: 'line', data: { labels: commonLabels, datasets: [{ label: 'Θερμοκρασία (°C)', data: """ + js_temp_data + """, borderColor: 'rgb(255, 99, 132)', backgroundColor: 'rgba(255, 99, 132, 0.2)', fill: true, tension: 0.1, pointRadius: 0 }] }, options: { animation: false }});
            new Chart(document.getElementById('humChart'), { type: 'line', data: { labels: commonLabels, datasets: [{ label: 'Υγρασία (%)', data: """ + js_hum_data + """, borderColor: 'rgb(54, 162, 235)', backgroundColor: 'rgba(54, 162, 235, 0.2)', fill: true, tension: 0.1, pointRadius: 0 }] }, options: { animation: false }});
        </script>
    </body>
    </html>
    """
    return html

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 80))
s.listen(5)

print("[-] Web Server started.")

while True:
    try:
        conn, addr = s.accept()
        conn.settimeout(3.0)
        request = conn.recv(1024).decode('utf-8')
        
        # Αν το αίτημα είναι κενό, κλείνουμε τη σύνδεση και πάμε στο επόμενο
        if not request:
            conn.close()
            continue
            
        # 1. Λειτουργία Download
        if "GET /download" in request:
            conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Disposition: attachment; filename="log.txt"\r\nConnection: close\r\n\r\n'.encode('utf-8'))
            try:
                with open(sensor_log.LOG_FILE, 'r') as f:
                    for line in f:
                        conn.send(line.encode('utf-8'))
            except OSError:
                conn.send("Δεν βρέθηκαν δεδομένα.".encode('utf-8'))
                
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
            
            conn.send(('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n<meta charset="utf-8">' + msg).encode('utf-8'))
            
        # 3. Λειτουργία Email
        elif "GET /email" in request:
            temp, hum = sensor_log.read_sensor()
            success = send_email(temp, hum)
            if success:
                msg = "Το email εστάλη επιτυχώς! <br><br><a href='/'>Επιστροφή</a>"
            else:
                msg = "Αποτυχία αποστολής! (Ελέγξτε κωδικούς/δίκτυο). <br><br><a href='/'>Επιστροφή</a>"
                
            conn.send(('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n<meta charset="utf-8">' + msg).encode('utf-8'))
            
        # 4. Αρχική Σελίδα (Πιάνει ΜΟΝΟ το root / και αγνοεί το favicon.ico)
        elif "GET / " in request:
            # Διαβάζουμε τον αισθητήρα και καταγράφουμε
            temp, hum = sensor_log.read_sensor()
            sensor_log.log_data(temp, hum)
            
            # Δημιουργία HTML
            response = web_page(temp, hum)
            
            conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n'.encode('utf-8'))
            conn.sendall(response.encode('utf-8'))
            
        # 5. Οτιδήποτε άλλο (π.χ. requests του browser για favicon) το απορρίπτουμε
        else:
            conn.send('HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n'.encode('utf-8'))
            
        conn.close()
        
    except OSError:
        # Αν υπάρξει timeout ή άλλο σφάλμα δικτύου, κλείνουμε το socket με ασφάλεια
        try:
            conn.close()
        except:
            pass