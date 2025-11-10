import sqlite3

conn = sqlite3.connect('reedz.db')
cursor = conn.cursor()

print("\n=== USERS ===")
cursor.execute("SELECT * FROM users")
for row in cursor.fetchall():
    print(row)

print("\n=== BETS ===")
cursor.execute("SELECT * FROM bets")
for row in cursor.fetchall():
    print(row)

print("\n=== PREDICTIONS ===")
cursor.execute("SELECT * FROM predictions")
for row in cursor.fetchall():
    print(row)

conn.close()
