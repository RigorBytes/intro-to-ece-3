#!/bin/bash

# Άλλαξε αυτό το μονοπάτι με την πραγματική διαδρομή που βρίσκεται το project σου
PROJECT_DIR="/home/ilias/Documents/intro-to-ece-3"

echo "[-] 1. Μετάβαση στον φάκελο του project..."
cd "$PROJECT_DIR" || { echo "[!] Ο φάκελος δεν βρέθηκε! Ελέγξτε τη μεταβλητή PROJECT_DIR."; exit 1; }

echo "[-] 2. Αντιγραφή αρχείων στο NodeMCU μέσω mpremote..."
# Αντιγράφουμε μόνο τα αρχεία που χρειάζεται να τρέχουν στον μικροελεγκτή
mpremote cp boot.py :boot.py
mpremote cp main.py :main.py
mpremote cp sensor_log.py :sensor_log.py
mpremote cp secrets.py :secrets.py

echo "[-] 3. Εκτέλεση Soft Reset για να διαβαστούν τα νέα αρχεία..."
mpremote soft-reset
sleep 2 # Μικρή παύση για να προλάβει να εκκινήσει το boot.py

echo "[-] 4. Εκκίνηση του ngrok tunnel..."
# Ξεκινάει το ngrok με την IP που ζήτησες
ngrok http --domain=endanger-trickily-excavator.ngrok-free.dev 10.224.229.54