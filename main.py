import socket
import sensor_log

def web_page():
    temp, hum = sensor_log.read_sensor()
    # Δημιουργία HTML με ενσωματωμένο CSS και JS (Chart.js)
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ECE Patras Weather Station</title>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: sans-serif; text-align: center; background: #f4f4f4; }
            .container { width: 80%; margin: auto; background: white; padding: 20px; border-radius: 10px; }
            .value { font-size: 2em; font-weight: bold; color: #007bff; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Σταθμός ECE Patras</h1>
            <p>Θερμοκρασία: <span class="value">""" + str(temp) + """°C</span></p>
            <p>Υγρασία: <span class="value">""" + str(hum) + """%</span></p>
            <canvas id="myChart"></canvas>
        </div>
        <script>
            const ctx = document.getElementById('myChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['10m', '8m', '6m', '4m', '2m', 'Now'],
                    datasets: [{
                        label: 'Θερμοκρασία (°C)',
                        data: [22, 23, 22, 24, 23, """ + str(temp) + """],
                        borderColor: 'rgb(255, 99, 132)',
                        tension: 0.1
                    }]
                }
            });
        </script>
    </body>
    </html>
    """
    return html

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

print("[-] Web Server started.")
while True:
    conn, addr = s.accept()
    request = conn.recv(1024)
    response = web_page()
    conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n')
    conn.sendall(response)
    conn.close()