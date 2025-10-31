import sqlite3

# Connect to existing complaints.db
conn = sqlite3.connect('complaints.db')
c = conn.cursor()

# 🔹 Add 'handled_by' column to complaints table
try:
    c.execute("ALTER TABLE complaints ADD COLUMN handled_by TEXT")
    print("✅ handled_by column added to complaints table.")
except sqlite3.OperationalError:
    print("⚠ handled_by column already exists.")

# 🔹 Add 'department' column to students table
try:
    c.execute("ALTER TABLE students ADD COLUMN department TEXT")
    print("✅ department column added to students table.")
except sqlite3.OperationalError:
    print("⚠ department column already exists.")

conn.commit()
conn.close()

print("🎉 Database update complete.")
