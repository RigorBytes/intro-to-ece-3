import socket
import sensor_log

def web_page():
    temp, hum = sensor_log.read_sensor()
    
    # 1. Λήψη Ιστορικού (200 τελευταίες)
    history = sensor_log.get_recent_history()
    
    temp_data = []
    hum_data = []
    
    for record in history:
        parts = record.split(',')
        if len(parts) == 3:
            temp_data.append(parts[1])
            hum_data.append(parts[2])
            
    # Προσθήκη της τωρινής μέτρησης
    if temp is not None and hum is not None:
        temp_data.append(str(temp))
        hum_data.append(str(hum))
        
    # Μετατροπή σε μορφή JavaScript [22.1, 22.3, ...]
    js_temp_data = "[" + ",".join(temp_data) + "]"
    js_hum_data = "[" + ",".join(hum_data) + "]"
    js_labels = "['" + "','".join(["" for _ in range(len(temp_data))]) + "']"
    
    t_str = str(temp) if temp is not None else "--"
    h_str = str(hum) if hum is not None else "--"
    
    html = """
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="15">
        <title>ECE Patras Weather Station</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: sans-serif; text-align: center; background: #f4f4f4; margin-top: 30px; padding-bottom: 30px;}
            .container { width: 90%; max-width: 700px; margin: auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
            .widgets { display: flex; justify-content: space-around; margin-bottom: 30px; }
            .value { font-size: 2.5em; font-weight: bold; }
            .temp-color { color: #ff6384; }
            .hum-color { color: #36a2eb; }
            .label { font-size: 1.2em; color: #555; }
            .chart-container { margin-bottom: 40px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Σταθμός ECE Patras</h1>
            
            <div class="widgets">
                <div>
                    <p class="label">Θερμοκρασία</p>
                    <span class="value temp-color">""" + t_str + """°C</span>
                </div>
                <div>
                    <p class="label">Υγρασία</p>
                    <span class="value hum-color">""" + h_str + """%</span>
                </div>
            </div>
            
            <div class="chart-container">
                <canvas id="tempChart"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="humChart"></canvas>
            </div>
        </div>

        <script>
            const commonLabels = """ + js_labels + """;

            const ctxTemp = document.getElementById('tempChart').getContext('2d');
            new Chart(ctxTemp, {
                type: 'line',
                data: {
                    labels: commonLabels,
                    datasets: [{
                        label: 'Θερμοκρασία (°C)',
                        data: """ + js_temp_data + """,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        fill: true,
                        tension: 0.1,
                        pointRadius: 0
                    }]
                },
                options: { responsive: true, animation: false }
            });

            const ctxHum = document.getElementById('humChart').getContext('2d');
            new Chart(ctxHum, {
                type: 'line',
                data: {
                    labels: commonLabels,
                    datasets: [{
                        label: 'Υγρασία (%)',
                        data: """ + js_hum_data + """,
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        fill: true,
                        tension: 0.1,
                        pointRadius: 0
                    }]
                },
                options: { responsive: true, animation: false }
            });
        </script>
    </body>
    </html>
    """
    return html

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 80))
s.listen(5)

print("[-] Web Server started. Listening on port 80.")

while True:
    try:
        conn, addr = s.accept()
        request = conn.recv(1024)
        
        # 2. Κάθε φορά που κάποιος μπαίνει (ή η σελίδα κάνει auto-refresh), καταγράφουμε νέα μέτρηση
        temp, hum = sensor_log.read_sensor()
        sensor_log.log_data(temp, hum)
        
        # 3. Σερβίρουμε τη σελίδα με τα φρέσκα δεδομένα
        response = web_page()
        
        conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n'.encode('utf-8'))
        conn.sendall(response.encode('utf-8'))
        conn.close()
    except OSError:
        conn.close()
        pass