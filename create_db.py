import sqlite3

# Connect karo
conn = sqlite3.connect('complaints.db')
c = conn.cursor()

# ✅ Complaints table (with handled_by)
c.execute('''
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        complaint TEXT NOT NULL,
        room TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        date TEXT NOT NULL,
        student_username TEXT NOT NULL,
        handled_by TEXT
    )
''')

# ✅ Students table (with department)
c.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        student_id TEXT NOT NULL,
        email TEXT NOT NULL,
        mobile TEXT NOT NULL,
        department TEXT NOT NULL
    )
''')

# ✅ Admin table
c.execute('''
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')

# ✅ Notification table
c.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        complaint_id INTEGER NOT NULL,
        admin_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        date TEXT NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(complaint_id) REFERENCES complaints(id),
        FOREIGN KEY(admin_id) REFERENCES admin(id)
    )
''')

# Admin insert
try:
    c.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ('admin', 'admin123'))
except sqlite3.IntegrityError:
    print("🟡 Admin already exists.")

# Student insert with department
try:
    c.execute("INSERT INTO students (username, password, name, student_id, email, mobile, department) VALUES (?, ?, ?, ?, ?, ?, ?)",
              ('student1', 'pass123', 'Test User', '101', 'test@example.com', '9999999999', 'Computer Science'))
except sqlite3.IntegrityError:
    print("🟡 Sample student already exists.")

conn.commit()
conn.close()

print("✅ New database created with Notification table successfully.")
