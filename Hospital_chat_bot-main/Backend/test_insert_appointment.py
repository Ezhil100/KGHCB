from sqlite_appointments import insert_appointment
import os
from pathlib import Path

sample = {
    'appointment_id': 'test-' + os.urandom(4).hex(),
    'user_name': 'Test Patient',
    'phone_number': '+1234567890',
    'preferred_date': '2025-10-15',
    'preferred_time': '10:00 AM',
    'reason': 'Routine checkup',
    'user_role': 'patient',
    'original_message': 'I would like to book an appointment next week',
    'status': 'pending'
}

rowid = insert_appointment(sample)
print(f"Inserted row id: {rowid}")

# Print last 5 rows to verify
db_path = Path(__file__).parent / 'appointments.db'
import sqlite3
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()
for row in cur.execute("SELECT id, appointment_id, patient_name, phone_number, preferred_date, preferred_time, status, created_at FROM appointments ORDER BY id DESC LIMIT 5"):
    print(row)
conn.close()
