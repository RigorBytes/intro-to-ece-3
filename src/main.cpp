#include <Arduino.h>
#include "DHT.h"
#include "LittleFS.h"

// Ορισμοί Pins και Αισθητήρα
#define DHTPIN 2    // Το Pin D4 του NodeMCU αντιστοιχεί στο GPIO2
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

// Μεταβλητές για το χρονόμετρο
unsigned long lastReadTime = 0;
const unsigned long interval = 60000;

// Δήλωση συνάρτησης αποθήκευσης
void saveToFlash(float temp, float hum);

void setup() {
  Serial.begin(115200);
  Serial.println("\n--- Εκκίνηση Συστήματος ---");

  // Ενεργοποίηση της εσωτερικής αντίστασης (Pull-up) για τον DHT22 χωρίς εξωτερική αντίσταση
  pinMode(DHTPIN, INPUT_PULLUP);
  delay(1000); // Χρόνος σταθεροποίησης ρεύματος
  
  dht.begin();
  
  // Εκκίνηση του συστήματος αρχείων (LittleFS)
  if(!LittleFS.begin()){
    Serial.println("Σφάλμα: Η προσάρτηση του LittleFS απέτυχε!");
  } else {
    Serial.println("Το LittleFS προσαρτήθηκε επιτυχώς.");
  }
}

void loop() {
  // Εκτέλεση μετρήσεων κάθε 1 λεπτό
  // Ελέγχος αν lastReadTime == 0
  if (millis() - lastReadTime >= interval || lastReadTime == 0) {
    lastReadTime = millis(); // Ενημέρωση του χρονομέτρου

    float currentHum = dht.readHumidity();    
    float currentTemp = dht.readTemperature();

    // Έλεγχος εγκυρότητας της μέτρησης
    if (isnan(currentHum) || isnan(currentTemp)) {
      Serial.println("Αποτυχία ανάγνωσης από τον DHT22! Ελέγξτε την καλωδίωση.");
      return;
    }

    // Εμφάνιση στο Serial Monitor του VS Code
    unsigned long uptimeSeconds = millis() / 1000;
    Serial.printf("Υγρασία: %.1f%%, Θερμοκρασία: %.1f°C\n",currentHum, currentTemp);

    // Κλήση της συνάρτησης για καταγραφή στη μνήμη
    saveToFlash(currentTemp, currentHum);
  }
}

// --- ΣΥΝΑΡΤΗΣΕΙΣ ---

void saveToFlash(float temp, float hum) {
  // 1. Έλεγχος Μεγέθους Αρχείου (Όριο 500KB = 512.000 bytes)
  File checkFile = LittleFS.open("/log.txt", "r");
  if (checkFile) {
    size_t fileSize = checkFile.size();
    checkFile.close();
    
    if (fileSize >= 512000) {
      Serial.println("ΠΡΟΣΟΧΗ: Το αρχείο ξεπέρασε τα 500KB. Διαγραφή και δημιουργία νέου...");
      LittleFS.remove("/log.txt");
    }
  }

  // 2. Εγγραφή των δεδομένων (Λειτουργία "a" - Append)
  File file = LittleFS.open("/log.txt", "a"); 
  if (!file) {
    Serial.println("Σφάλμα: Αδυναμία ανοίγματος του log.txt για εγγραφή.");
    return;
  }

  // Επειδή είμαστε offline, χρησιμοποιούμε τα δευτερόλεπτα λειτουργίας (uptime)
  unsigned long uptimeSeconds = millis() / 1000;
  file.printf("%lu, %.2f, %.2f\n", uptimeSeconds, temp, hum);
  file.close();
  
  Serial.println("Τα δεδομένα αποθηκεύτηκαν επιτυχώς στη μνήμη Flash.\n");
}