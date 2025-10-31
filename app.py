from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from datetime import datetime
from flask_mail import Mail, Message



app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session and flash messages

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # sender email
app.config['MAIL_PASSWORD'] = 'your_app_password'     # gmail app password
mail = Mail(app)

# -------------------- Home Page --------------------
@app.route('/')
def home():
    return render_template('index.html')

# -------------------- Student Login --------------------
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('complaints.db')
        c = conn.cursor()
        c.execute("SELECT * FROM students WHERE username = ? AND password = ?", (username, password))
        student = c.fetchone()
        conn.close()

        if student:
            session['student'] = username
            flash("Login successful!")
            return redirect('/student_profile')
        else:
            flash("Wrong username or password.")
    return render_template('student_login.html')

# -------------------- Student Logout --------------------
@app.route('/student_logout')
def student_logout():
    session.pop('student', None)
    flash("Logout successfull.")
    return redirect('/')

# -------------------- Student profile -------------------
@app.route('/student_profile')
def student_profile():
    if 'student' not in session:
        flash("Please login first.")
        return redirect('/student_login')

    username = session['student']

    conn = sqlite3.connect('complaints.db')
    c = conn.cursor()
    
    # Sirf us student ki complaints nikalna
    c.execute('''
        SELECT id, category, complaint, room, status, date, handled_by
        FROM complaints
        WHERE student_username = ?
    ''', (username,))
    
    complaints = c.fetchall()
    conn.close()

    return render_template('student_profile.html', username=username, complaints=complaints)

# -------------------- Edit complaint -----------------------
@app.route('/edit_complaint/<int:id>', methods=['GET', 'POST'])
def edit_complaint(id):
    if 'student' not in session:
        flash("First login.")
        return redirect('/student_login')

    conn = sqlite3.connect('complaints.db')
    c = conn.cursor()

    if request.method == 'POST':
        category = request.form['category']
        complaint = request.form['complaint']
        room = request.form['room']

        c.execute("UPDATE complaints SET category=?, complaint=?, room=? WHERE id=?", 
                  (category, complaint, room, id))
        conn.commit()
        conn.close()
        flash("Complaint updated!")
        return redirect('/student_profile')

    c.execute("SELECT * FROM complaints WHERE id=?", (id,))
    data = c.fetchone()
    conn.close()
    return render_template('edit_complaint.html', complaint=data)

#--------------------- Delete complaint --------------------
@app.route('/delete_complaint/<int:id>')
def delete_complaint(id):
    if 'student' not in session:
        flash("First login.")
        return redirect('/student_login')

    conn = sqlite3.connect('complaints.db')
    c = conn.cursor()
    c.execute("DELETE FROM complaints WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Complaint deleted.")
    return redirect('/student_profile')

# -------------------- Complaint Submit --------------------
@app.route('/submit', methods=['GET', 'POST'])
def submit_complaint():
    if 'student' not in session:
        flash("Please login first.")
        return redirect('/student_login')

    if request.method == 'POST':
        category = request.form['category']
        complaint = request.form['complaint']
        room = request.form['room']
        date = datetime.now().strftime("%Y-%m-%d")
        student_username = session['student']

        conn = sqlite3.connect('complaints.db')
        c = conn.cursor()
        status = 'Pending'
        handled_by = 'Not Assigned'

        c.execute("INSERT INTO complaints (category, complaint, room, status, date, student_username, handled_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (category, complaint, room, status, date, student_username, handled_by))
        conn.commit()

        # Admin ke liye session mein store karo
        session['admin_notice'] = "A new complaint has been submitted!"

        conn.close()

        # Student ke liye flash message dikhao
        flash("Complaint submitted successfully!")
        return render_template('submit_complaint.html')

    return render_template('complaint_form.html')

# -------------------- Complaint Dashboard --------------------
@app.route('/dashboard')
def dashboard():
    if 'student' not in session and 'admin' not in session:
        flash("Please login first.")
        return redirect('/student_login')

    status = request.args.get('status', '')
    category = request.args.get('category', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    conn = sqlite3.connect('complaints.db')
    c = conn.cursor()

    # Student view
    if 'student' in session:
        student_username = session['student']
        query = '''
            SELECT complaints.id, complaints.category, complaints.complaint, complaints.room, 
                   complaints.status, complaints.date, complaints.handled_by,
                   students.name, students.student_id, students.email, students.mobile, students.department
            FROM complaints
            JOIN students ON complaints.student_username = students.username
            WHERE complaints.student_username = ?
        '''
        params = [student_username]

        if status:
            query += " AND complaints.status = ?"
            params.append(status)
        if category:
            query += " AND complaints.category = ?"
            params.append(category)
        if from_date and to_date:
            query += " AND complaints.date BETWEEN ? AND ?"
            params.append(from_date)
            params.append(to_date)
        elif from_date:
            query += " AND complaints.date >= ?"
            params.append(from_date)
        elif to_date:
            query += " AND complaints.date <= ?"
            params.append(to_date)

    # Admin view
    elif 'admin' in session:
        query = '''
            SELECT complaints.id, complaints.category, complaints.complaint, complaints.room, 
                   complaints.status, complaints.date, complaints.handled_by,
                   students.name, students.student_id, students.email, students.mobile, students.department
            FROM complaints
            JOIN students ON complaints.student_username = students.username
        '''
        params = []
        conditions = []

        if status:
            conditions.append("complaints.status = ?")
            params.append(status)
        if category:
            conditions.append("complaints.category = ?")
            params.append(category)
        if from_date and to_date:
            conditions.append("complaints.date BETWEEN ? AND ?")
            params.append(from_date)
            params.append(to_date)
        elif from_date:
            conditions.append("complaints.date >= ?")
            params.append(from_date)
        elif to_date:
            conditions.append("complaints.date <= ?")
            params.append(to_date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

    c.execute(query, params)
    complaints = c.fetchall()
    conn.close()

    # Admin notice flash
    if 'admin' in session and session.get('admin_notice'):
        flash(session.pop('admin_notice'), 'admin_notice')

    return render_template('dashboard.html', complaints=complaints)

# -------------------- Admin Login --------------------
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':
            session.pop('student', None)
            session['admin'] = username
            flash("Admin login successful!")
            return redirect('/dashboard')
        else:
            flash("Wrong admin credentials.")
    return render_template('admin_login.html')

# -------------------- Admin Logout --------------------
@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash("Admin logout.")
    return render_template('/index.html')

# -------------------- Status Update --------------------
@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    new_status = 'Resolved'
    handler = request.form.get('handled_by') or "Admin"

    conn = sqlite3.connect('complaints.db')
    c = conn.cursor()

    # ✅ Update complaint status + handler
    c.execute("UPDATE complaints SET status = ?, handled_by = ? WHERE id = ?", 
              (new_status, handler, id))

    # ✅ Complaint details nikalo
    c.execute("SELECT student_username FROM complaints WHERE id = ?", (id,))
    student_username = c.fetchone()[0]

    # ✅ Student ID nikalo
    c.execute("SELECT id FROM students WHERE username = ?", (student_username,))
    student_id = c.fetchone()[0]

    # ✅ Admin ID nikalo (abhi ke liye first admin lete hain)
    c.execute("SELECT id FROM admin WHERE username = ?", ("admin",))
    admin_id = 1

    # ✅ Notification message
    message = f"Your complaint {id} has been marked as {new_status} by {handler}."
    
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ✅ Notification insert
    c.execute("INSERT INTO notifications (student_id, complaint_id, admin_id, message, date) VALUES (?, ?, ?, ?, ?)",
              (student_id, id, admin_id, message, date))

    conn.commit()
    conn.close()

    flash(f"Complaint {id} resolved and notification sent.")
    return redirect('/dashboard')

# -------------------- Student Register --------------------
@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        student_id = request.form['student_id']
        email = request.form['email']
        mobile = request.form['mobile']
        department = request.form['department']

        conn = sqlite3.connect('complaints.db')
        c = conn.cursor()

        c.execute("SELECT * FROM students WHERE username = ?", (username,))
        existing = c.fetchone()

        if existing:
            flash("Username already exists. Try another.")
            conn.close()
            return redirect('/student_register')

        c.execute('''INSERT INTO students 
            (username, password, name, student_id, email, mobile,department)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (username, password, name, student_id, email, mobile,department))
        
        conn.commit()
        conn.close()
        flash("Registered successfully. Please login.")
        return redirect('/student_login')

    return render_template('student_register.html')

#---------------------Notification-----------------

@app.route('/notifications')
def notifications():
    if 'student' not in session:
        flash("Please login first.")
        return redirect('/student_login')

    username = session['student']

    conn = sqlite3.connect('complaints.db')
    c = conn.cursor()

    # ✅ Ab student ka id nikalenge
    c.execute("SELECT id FROM students WHERE username = ?", (username,))
    student = c.fetchone()

    if not student:
        conn.close()
        flash("Student not found.")
        return redirect('/student_profile')

    student_id = student[0]

    # ✅ Ab notifications fetch karenge
    c.execute("""
        SELECT message, date
        FROM notifications
        WHERE student_id = ?
        ORDER BY date DESC
    """, (student_id,))
    
    notes = c.fetchall()
    conn.close()

    return render_template('notifications.html', notifications=notes)

#---------------------------delete all complaints------------------
@app.route('/delete_all', methods=['POST'])
def delete_all():
    if 'admin' not in session:
        flash("You are not authorized!")
        return redirect('/dashboard')

    conn = sqlite3.connect('complaints.db')
    c = conn.cursor()

    # Delete all complaints
    c.execute("DELETE FROM complaints")

    # Delete all notifications (agar notifications table hai to)
    c.execute("DELETE FROM notifications")

    conn.commit()
    conn.close()

    flash("All complaints and notifications have been deleted!")
    return redirect('/dashboard')

# -------------------- Run App --------------------
if __name__ == '__main__':
    app.run(debug=True)