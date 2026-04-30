#include <Arduino.h> // ΑΠΑΡΑΙΤΗΤΟ για το VS Code (PlatformIO)
#include "DHT.h"
#include "LittleFS.h"
#include <ESP8266WiFi.h>
#include <time.h>
#include <ESP_Mail_Client.h>

// Ορισμοί Pins και Αισθητήρα
#define DHTPIN 2    
#define DHTTYPE DHT22

// Ρυθμίσεις SMTP (Email)
#define SMTP_HOST "smtp.gmail.com"
#define SMTP_PORT 465
#define AUTHOR_EMAIL "iliasvardaramatos@gmail.com"
#define AUTHOR_PASSWORD "llzb vpwv cbfh vozi" // ΠΡΟΣΟΧΗ: Να το σβήσετε αν ανεβάσετε τον κώδικα στο GitHub
#define RECIPIENT_EMAIL "leibadiotakesangelos@gmail.com"

// Ρυθμίσεις WiFi
const char* ssid     = "Pixel_1213";
const char* password = "densoulew"; // ΠΡΟΣΟΧΗ: Τα πραγματικά σου στοιχεία WiFi

// Ρυθμίσεις για την ώρα (NTP)
const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = 7200; // Ελλάδα UTC+2
const int   daylightOffset_sec = 3600;

DHT dht(DHTPIN, DHTTYPE);
SMTPSession smtp;

// Μεταβλητές ελέγχου
float lastTemp = 0;
float lastHum = 0;
unsigned long lastReportTime = 0;

// --- ΔΗΛΩΣΗ ΣΥΝΑΡΤΗΣΕΩΝ (Υποχρεωτικό στην C++ / VS Code) ---
void connectToWiFi();
String getTimestamp();
void saveToFlash(float temp, float hum);
void sendEmail(String subject, String content);

void setup() {
  Serial.begin(115200);
 
  // Το "κόλπο" για τον DHT22 χωρίς εξωτερική αντίσταση
  pinMode(DHTPIN, INPUT_PULLUP);
  delay(1000); // Μικρή παύση για να σταθεροποιηθεί το ρεύμα
 
  dht.begin();
 
  if(!LittleFS.begin()){
    Serial.println("Error: LittleFS mounting failed");
  } else {
    Serial.println("LittleFS mounted successfully");
  }

  connectToWiFi();
}

void loop() {
  delay(2000); // Αναμονή 2 δευτερολέπτων (απαραίτητο για τον DHT22)

  float currentHum = dht.readHumidity();    
  float currentTemp = dht.readTemperature();

  // Έλεγχος αν η ανάγνωση απέτυχε
  if (isnan(currentHum) || isnan(currentTemp)) {
    Serial.println("Measurement failed! Ελέγξτε τα καλώδια στο Breadboard.");
    return;
  }

  // Εκτύπωση στο Serial Monitor του VS Code
  Serial.printf("Humidity: %.1f%% | Temperature: %.1f°C\n", currentHum, currentTemp);

  // Αποθήκευση στη μνήμη Flash (Βήμα 3)
  saveToFlash(currentTemp, currentHum);

  // 1. Έλεγχος για απότομη μεταβολή (Βήμα 5)
  if (abs(currentTemp - lastTemp) >= 2.0 || abs(currentHum - lastHum) >= 10.0) {
    String msg = "Προσοχή! Μεγάλη μεταβολή συνθηκών:\n";
    msg += "Θερμοκρασία: " + String(currentTemp) + " C\n";
    msg += "Υγρασία: " + String(currentHum) + " %";
   
    sendEmail("ALERT: Μεταβολή Συνθηκών", msg);
   
    // Ενημέρωση των τελευταίων τιμών
    lastTemp = currentTemp;
    lastHum = currentHum;
  }

  // 2. Περιοδική αναφορά (Βήμα 5 - κάθε 1 ώρα = 3600000 ms)
  if (millis() - lastReportTime > 3600000) {
    sendEmail("Periodic Report", "Το σύστημα λειτουργεί κανονικά. Τρέχουσα Τ: " + String(currentTemp) + "C");
    lastReportTime = millis();
  }

  delay(8000); // Επιπλέον καθυστέρηση για να μην γεμίζει η οθόνη πολύ γρήγορα
}

// --- ΣΥΝΑΡΤΗΣΕΙΣ ---

void saveToFlash(float temp, float hum) {
  File file = LittleFS.open("/log.txt", "a"); // "a" για append (προσθήκη)
  if (!file) {
    Serial.println("Error: File can't be opened");
    return;
  }

  String timestamp = getTimestamp();
  file.printf("%s, %.2f, %.2f\n", timestamp.c_str(), temp, hum);
  file.close();
 
  Serial.println("Saved to Flash: " + timestamp);
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi...");
  
  // ΠΡΟΣΘΗΚΗ: Βάζουμε το ESP ρητά σε λειτουργία Station (πελάτη)
  WiFi.mode(WIFI_STA); 
  
  // ΠΡΟΣΘΗΚΗ: Διαγραφή παλιών ρυθμίσεων WiFi (καθαρή εκκίνηση)
  WiFi.disconnect(); 
  delay(100);

  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 60) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
}

String getTimestamp() {
  time_t now = time(nullptr);
  struct tm* timeinfo = localtime(&now);
  char buffer[25];
  strftime(buffer, sizeof(buffer), "%d/%m/%Y %H:%M:%S", timeinfo);
  return String(buffer);
}

void sendEmail(String subject, String content) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("No WiFi. Email cannot be sent.");
    return;
  }

  Session_Config config;
  config.server.host_name = SMTP_HOST;
  config.server.port = SMTP_PORT;
  config.login.email = AUTHOR_EMAIL;
  config.login.password = AUTHOR_PASSWORD;

  SMTP_Message message;
  message.sender.name = "ESP8266 Monitor";
  message.sender.email = AUTHOR_EMAIL;
  message.subject = subject;
  message.addRecipient("User", RECIPIENT_EMAIL);
  message.text.content = content.c_str();

  if (!smtp.connect(&config)) return;
  if (!MailClient.sendMail(&smtp, &message)) {
    Serial.println("Email Error: " + smtp.errorReason());
  } else {
    Serial.println("Email sent successfully!");
  }
}