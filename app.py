from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify, make_response
import mysql.connector
import qrcode
import os
import io
import base64
import csv, pdfkit
from datetime import date, datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

app = Flask(__name__)
app.secret_key = "secret123"

serializer = URLSafeTimedSerializer(app.secret_key)

db = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "Azizul03112003", #database password goes here
    database = "smart_attendance"
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']

        cursor = db.cursor()

        if role == "admin":
            cursor.execute("SELECT * FROM admins WHERE username=%s AND password=%s", (username, password))
            user = cursor.fetchone()

            if user:
                session['admin_id'] = user[0]
                return redirect('/admin_dashboard')
            
        elif role == "instructor":
            cursor.execute("SELECT * FROM instructors WHERE email=%s AND password=%s", (username, password))
            user = cursor.fetchone()

            if user:
                session['instructor_id'] = user[0]
                return redirect('/instructor_dashboard')
            
        elif role == "student":
            cursor.execute("SELECT * FROM student_accounts WHERE student_id=%s AND password=%s", (username, password))
            user = cursor.fetchone()

            if user:
                session['student_id'] = username

                if 'pending_attendance' in session:
                    section_id = session['pending_attendance']
                    session.pop('pending_attendance')

                    return redirect(f'/mark_attendance/{section_id}')
                
                return redirect('/student_dashboard')
            
        return render_template('login.html', error="Invalid username or password")
        
    return render_template('login.html')

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

@app.context_processor
def inject_user():
    if 'admin_id' in session:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT first_name FROM admins WHERE admin_id=%s",
            (session['admin_id'],)
        )
        user = cursor.fetchone()
        return dict(user=user)
    
    return dict(user=None)

@app.route('/profile', methods=['GET','POST'])
def profile():
    cursor = db.cursor(dictionary=True)

    if 'student_id' not in session:
        return redirect('/login')

    user_id = session['student_id']

    # Fetch student info
    cursor.execute("""
        SELECT students.name, student_accounts.password
        FROM students
        JOIN student_accounts
        ON students.student_id = student_accounts.student_id
        WHERE students.student_id = %s
    """, (user_id,))
    user = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        new_password = request.form['new_password']
        current_password = request.form['current_password']

        if current_password != user['password']:
            flash("Incorrect current password", "error")
            return redirect('/student_dashboard?profile=open')

        # Update name
        cursor.execute(
            "UPDATE students SET name=%s WHERE student_id=%s",
            (name, user_id)
        )

        # Update password if provided
        if new_password:
            cursor.execute(
                "UPDATE student_accounts SET password=%s WHERE student_id=%s",
                (new_password, user_id)
            )

        db.commit()
        flash("Profile updated successfully!", "success")
        return redirect('/student_dashboard')

    return render_template("profile.html", user=user)

@app.route('/instructor_profile', methods=['GET','POST'])
def instructor_profile():
    cursor = db.cursor(dictionary=True)

    if 'instructor_id' not in session:
        return redirect('/login')

    user_id = session['instructor_id']
    cursor.execute("SELECT instructor_id, name, password FROM instructors WHERE instructor_id=%s", (user_id,))
    user = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        new_password = request.form['new_password']
        current_password = request.form['current_password']

        if current_password != user['password']:
            flash("Incorrect current password", "error")
            return redirect('/instructor_dashboard?profile=open')

        cursor.execute("UPDATE instructors SET name=%s WHERE instructor_id=%s", (name, user_id))
        if new_password:
            cursor.execute("UPDATE instructors SET password=%s WHERE instructor_id=%s", (new_password, user_id))
        db.commit()

        flash("Profile updated successfully!", "success")
        return redirect('/instructor_dashboard?profile=open')

    return render_template("profile_instructor.html", user=user)

@app.route('/admin_profile', methods=['GET','POST'])
def admin_profile():
    cursor = db.cursor(dictionary=True)

    if 'admin_id' not in session:
        return redirect('/login')

    user_id = session['admin_id']
    cursor.execute("SELECT admin_id, username, password, first_name, last_name FROM admins WHERE admin_id=%s", (user_id,))
    user = cursor.fetchone()

    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']
        current_password = request.form['current_password']

        if current_password != user['password']:
            flash("Incorrect current password", "error")
            return redirect('/admin_dashboard?profile=open')

        cursor.execute("UPDATE admins SET username=%s WHERE admin_id=%s", (username, user_id))
        if new_password:
            cursor.execute("UPDATE admins SET password=%s WHERE admin_id=%s", (new_password, user_id))
        db.commit()

        flash("Profile updated successfully!", "success")
        return redirect('/admin_dashboard?profile=open')

    return render_template("admin_dashboard.html", user=user)

@app.route('/student_signup', methods=['GET','POST']) #main (student signup)
def student_signup():

    if request.method == 'POST':

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        student_id = request.form['student_id']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return "Passwords do not match"


        full_name = first_name + " " + last_name

        cursor = db.cursor()

        cursor.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))

        existing = cursor.fetchone()

        if existing:
            return "Student already registered."

        cursor.execute(
            "INSERT INTO students (student_id, name) VALUES (%s,%s)",
            (student_id, full_name)
        )

        cursor.execute(
            "INSERT INTO student_accounts (student_id, email, password) VALUES (%s,%s,%s)",
            (student_id, email, password)
        )

        db.commit()

        flash("Account created successfully! Please login.", "success")
        return redirect('/login')

    return render_template('student_signup.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin_dashboard') #main
def admin_dashboard():

    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM instructors")
    total_instructors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sections")
    total_sections = cursor.fetchone()[0]

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT admin_id, username, first_name, last_name FROM admins WHERE admin_id=%s", (session['admin_id'],))
    admin_user = cursor.fetchone();

    return render_template(
        "admin_dashboard.html",
        students = total_students,
        instructors = total_instructors,
        sections = total_sections,
        user = admin_user
    )

@app.route('/manage_instructors')
def manage_instructors():

    cursor = db.cursor()

    cursor.execute("SELECT * FROM instructors")
    instructors = cursor.fetchall()

    return render_template(
        "manage_instructors.html",
        instructors=instructors
    )

# adding instructor in admin dashboard

@app.route('/add_instructor', methods=['POST'])
def add_instructor():

    print("Route hit")
    print("FORM DATA:", request.form)
        
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    cursor = db.cursor()

    cursor.execute("SELECT * FROM instructors WHERE email = %s", (email,))
    existing = cursor.fetchone()

    if existing:
        return jsonify({
            "success": False,
            "message": "Instructor already exists"
        })

    cursor.execute(
        "INSERT INTO instructors (name, email, password) VALUES (%s, %s, %s)",
        (name, email, password)
    )
    db.commit()

    new_id = cursor.lastrowid

    return jsonify({
        "success": True,
        "id": new_id,
        "name": name,
        "email": email
    })

@app.route('/delete_instructor/<int:instructor_id>')
def delete_instructor(instructor_id):

    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM instructors WHERE instructor_id=%s",
        (instructor_id,)
    )

    db.commit()

    return redirect('/manage_instructors')

@app.route('/edit_instructor', methods=['POST'])
def edit_instructor():

    id = request.form['id']
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    cursor = db.cursor()

    if password:  # only update password if provided
        cursor.execute("""
            UPDATE instructors
            SET name=%s, email=%s, password=%s
            WHERE instructor_id=%s
        """, (name, email, password, id))
    else:
        cursor.execute("""
            UPDATE instructors
            SET name=%s, email=%s
            WHERE instructor_id=%s
        """, (name, email, id))

    db.commit()

    return jsonify({
        "success": True,
        "id": id,
        "name": name,
        "email": email
    })

@app.route('/view_students')
def view_students():

    cursor = db.cursor()

    cursor.execute("""
    SELECT s.student_id, s.name, a.email, a.password
    FROM students s
    JOIN student_accounts a
    ON s.student_id = a.student_id
    """)

    students = cursor.fetchall()

    return render_template(
        "view_students.html",
        students=students
    )

@app.route('/add_student', methods=['POST'])
def add_student():

    student_id = request.form['student_id']
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE student_id = %s",
        (student_id,)
    )

    existing = cursor.fetchone()

    if existing:
        return jsonify({
            "success": False,
            "message": "Student ID already exists"
        })

    # insert into students
    cursor.execute(
        "INSERT INTO students (student_id, name) VALUES (%s, %s)",
        (student_id, name)
    )

    # insert into accounts
    cursor.execute(
        "INSERT INTO student_accounts (student_id, email, password) VALUES (%s, %s, %s)",
        (student_id, email, password)
    )

    db.commit()

    return jsonify({
        "success": True,
        "id": student_id,
        "name": name,
        "email": email
    })

@app.route('/delete_student/<student_id>')
def delete_student(student_id):

    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM attendance WHERE student_id=%s",
        (student_id,)
    )

    cursor.execute(
        "DELETE FROM section_students WHERE student_id=%s",
        (student_id,)
    )

    cursor.execute(
        "DELETE FROM student_accounts WHERE student_id=%s",
        (student_id,)
    )

    cursor.execute(
        "DELETE FROM students WHERE student_id=%s",
        (student_id,)
    )

    db.commit()

    return redirect('/view_students')

@app.route('/edit_student', methods=['POST'])
def edit_student():

    student_id = request.form['id']
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')

    cursor = db.cursor()

    try:
        # update name
        if name:
            cursor.execute(
                "UPDATE students SET name=%s WHERE student_id=%s",
                (name, student_id)
            )

        # get existing account
        cursor.execute(
            "SELECT email, password FROM student_accounts WHERE student_id=%s",
            (student_id,)
        )
        existing = cursor.fetchone()

        if not existing:
            return jsonify({"success": False, "message": "Student account not found"})

        current_email, current_password = existing

        new_email = email if email else current_email
        new_password = password if password else current_password

        cursor.execute(
            "UPDATE student_accounts SET email=%s, password=%s WHERE student_id=%s",
            (new_email, new_password, student_id)
        )

        db.commit()

        return jsonify({"success": True})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"success": False, "message": str(e)})
    
@app.route('/view_sections')
def view_sections():
    if 'admin_id' not in session:
        return redirect('/login')

    cursor = db.cursor()
    
    # 1. Fetch Admin Info for the Sidebar (Index 1: first_name)
    cursor.execute("SELECT first_name FROM admins WHERE admin_id = %s", (session['admin_id'],))
    admin_row = cursor.fetchone()
    user = {'first_name': admin_row[0]} if admin_row else {'first_name': 'Admin'}

    # 2. Fetch ALL Instructors (For the "Add Section" Modal Dropdown)
    cursor.execute("SELECT instructor_id, name FROM instructors")
    instructors = cursor.fetchall()

    # 3. Fetch Sections with Instructor Names (Handling Search correctly)
    search = request.args.get('search')
    
    query = """
        SELECT s.section_id, s.section_name, i.name 
        FROM sections s
        LEFT JOIN instructors i ON s.instructor_id = i.instructor_id
    """
    
    if search:
        # We use the same JOIN logic even when searching so we don't lose instructor names
        query += " WHERE s.section_name LIKE %s"
        cursor.execute(query, ('%' + search + '%',))
    else:
        cursor.execute(query)
        
    sections = cursor.fetchall()

    return render_template(
        "view_sections.html",
        sections=sections,
        instructors=instructors,
        user=user, 
        now=datetime.now()
    )

@app.route('/admin_add_section', methods=['POST'])
def admin_add_section():

    if 'admin_id' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    section_name = request.form.get('section_name')
    instructor_email = request.form.get('instructor_email')

    if not section_name or not instructor_email:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    try:
        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM sections WHERE section_name = %s",
            (section_name,)
        )
        if cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "Section already exists"
            })

        cursor.execute(
            "SELECT instructor_id FROM instructors WHERE LOWER(email) = LOWER(%s)",
            (instructor_email,)
        )
        result = cursor.fetchone()

        if not result:
            return jsonify({
                "success": False,
                "message": "Instructor not found"
            })

        instructor_id = result[0]

        cursor.execute(
            "INSERT INTO sections (section_name, instructor_id) VALUES (%s, %s)",
            (section_name, instructor_id)
        )

        db.commit()

        return jsonify({
            "success": True,
            "message": "Section added successfully"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# Section details for the admin

@app.route('/admin_section/<int:section_id>')
def admin_section(section_id):

    cursor = db.cursor()

    cursor.execute("""
    SELECT sections.section_name, instructors.name
    FROM sections
    JOIN instructors
    ON sections.instructor_id = instructors.instructor_id
    WHERE sections.section_id = %s
    """, (section_id,))

    section = cursor.fetchone()

    cursor.execute("""
    SELECT students.student_id, students.name
    FROM section_students
    JOIN students
    ON section_students.student_id = students.student_id
    WHERE section_students.section_id = %s
    """, (section_id,))

    students = cursor.fetchall()

    return render_template(
        "admin_section.html",
        section_name=section[0],
        instructor_name=section[1],
        students=students
    )

@app.route('/admin_reports')
def admin_reports():
    if 'admin_id' not in session:
        return redirect('/login')

    cursor = db.cursor()
    
    #using admin data for the current admin
    cursor.execute("SELECT first_name FROM admins WHERE admin_id = %s", (session['admin_id'],))
    admin_row = cursor.fetchone()
    user = {'first_name': admin_row[0]} if admin_row else {'first_name': 'Admin'}

    cursor.execute("""
            SELECT 
                s.section_name,
                COUNT(DISTINCT ss.student_id) AS total_students,
                IFNULL(ROUND(COUNT(CASE WHEN a.status='Present' THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(a.id), 0), 1), 0) AS avg_attendance, 
                s.section_id
            FROM sections s
            LEFT JOIN section_students ss ON s.section_id = ss.section_id
            LEFT JOIN attendance a ON s.section_id = a.section_id
            GROUP BY s.section_id, s.section_name
        """)
    reports = cursor.fetchall()

    # Calculate Overall Daily Participation (Today's % vs total students)
    today = date.today().strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM attendance WHERE date = %s AND status = 'Present') * 100.0 / 
            NULLIF((SELECT COUNT(*) FROM section_students), 0)
    """, (today,))
    daily_participation = round(cursor.fetchone()[0] or 0, 1)

    # This finds students whose individual average across all their classes is low
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT student_id 
            FROM attendance 
            GROUP BY student_id 
            HAVING (COUNT(CASE WHEN status='Present' THEN 1 END) * 100.0 / COUNT(id)) < 75
        ) AS at_risk_subquery
    """)
    at_risk_count = cursor.fetchone()[0]

    return render_template("admin_reports.html", 
                           reports=reports, 
                           daily_participation=daily_participation,
                           at_risk_count=at_risk_count)

# view section details in reports

@app.route('/view_section_details/<int:section_id>')
def view_section_details(section_id):

    if 'admin_id' not in session:
        return redirect('/login')
    return redirect(url_for('admin_section', section_id=section_id))

# exporting report in csv format 

@app.route('/export_section_csv/<int:section_id>')
def export_section_csv(section_id):
    if 'admin_id' not in session:
        return redirect('/login')
    
    cursor = db.cursor()
    # Fetch all attendance records for this specific section
    cursor.execute("""
        SELECT a.date, s.student_id, s.name, a.status 
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.section_id = %s
        ORDER BY a.date DESC
    """, (section_id,))
    records = cursor.fetchall()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Student ID', 'Name', 'Status']) # Header
    for row in records:
        writer.writerow(row)
    
    # Prepare response for download
    output.seek(0)
    return Flask.response_class(
        output.read(),
        mimetype='text/csv',
        headers={"Content-disposition": f"attachment; filename=section_{section_id}_report.csv"}
    )

# Export in pdf format 

@app.route('/export_section_pdf/<int:section_id>')
def export_section_pdf(section_id):
    if 'admin_id' not in session:
        return redirect('/login')

    cursor = db.cursor(dictionary=True)
    
    # Fetch Section Info
    cursor.execute("SELECT section_name FROM sections WHERE section_id = %s", (section_id,))
    section = cursor.fetchone()
    if not section:
        return "Section not found", 404

    # Fetch Attendance Records
    cursor.execute("""
        SELECT a.date, s.student_id, s.name, a.status 
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.section_id = %s
        ORDER BY a.date DESC
    """, (section_id,))
    records = cursor.fetchall()

    rendered_html = render_template('report_pdf_template.html', 
                                   section_name=section['section_name'], 
                                   records=records,
                                   now=datetime.now().strftime("%B %d, %Y %I:%M %p"))

    # PDF Configuration
    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
    }

    # Path for the tool
    path_wkhtmltopdf = r'E:\html to pdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    
    pdf = pdfkit.from_string(rendered_html, False, configuration=config, options=options)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f"attachment; filename={section['section_name']}_Report.pdf"
    
    return response

@app.route('/instructor_dashboard')
def instructor_dashboard():
    if 'instructor_id' not in session:
        return redirect('/login')
    
    instructor_id = session['instructor_id']
    cursor = db.cursor(dictionary=True)

    # Fetch instructor name for the sidebar
    cursor.execute("SELECT name FROM instructors WHERE instructor_id = %s", (instructor_id,))
    user = cursor.fetchone()

    # Fetch sections as tuples for the loop
    cursor = db.cursor() 

    cursor.execute("""
    SELECT s.section_id, s.section_name, COUNT(ss.student_id) as student_count
    FROM sections s
    LEFT JOIN section_students ss ON s.section_id = ss.section_id
    WHERE s.instructor_id = %s
    GROUP BY s.section_id, s.section_name
    """, (session['instructor_id'],))

    sections = cursor.fetchall()

    return render_template("instructor_dashboard.html", user=user, sections=sections)

@app.route('/create_section', methods=['GET','POST']) #main
def create_section():

    if request.method == 'POST':

        section_name = request.form['section_name']
        instructor_id = session['instructor_id']

        cursor = db.cursor()

        cursor.execute("INSERT INTO sections (section_name, instructor_id) VALUES (%s,%s)", (section_name, instructor_id))

        db.commit()

        return redirect('/instructor_dashboard')

    return render_template('create_section.html')

@app.route('/delete_section/<int:section_id>')
def delete_section(section_id):
    # Check if either an Admin or an Instructor is logged in
    if 'admin_id' not in session and 'instructor_id' not in session:
        return redirect('/login')

    cursor = db.cursor()

    # 1. Delete Attendance Records (To avoid Foreign Key errors)
    cursor.execute("DELETE FROM attendance WHERE section_id=%s", (section_id,))

    # 2. Delete Student Mappings
    cursor.execute("DELETE FROM section_students WHERE section_id=%s", (section_id,))

    # 3. Delete the Section itself
    cursor.execute("DELETE FROM sections WHERE section_id=%s", (section_id,))

    db.commit()

    if 'admin_id' in session:
        return redirect('/view_sections')
    return redirect('/instructor_dashboard')

@app.route('/section/<int:section_id>') #main
def section_page(section_id):

    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT name FROM instructors WHERE instructor_id = %s", (session['instructor_id'],))
    user = cursor.fetchone()

    cursor.execute(
        "SELECT section_name FROM sections WHERE section_id = %s",
        (section_id,)
    )

    section = cursor.fetchone()

    search = request.args.get('search')

    if search:
        cursor.execute("""                          
        SELECT 
            students.student_id,
            students.name,

            COALESCE(SUM(CASE WHEN attendance.status='Present' THEN 1 ELSE 0 END), 0) AS presents,
            
            COALESCE(SUM(CASE WHEN attendance.status='Absent' THEN 1 ELSE 0 END), 0) AS absents,

            (
                SELECT COUNT(DISTINCT date)
                FROM attendance
                WHERE section_id = %s
            ) AS total_classes

        FROM section_students

        JOIN students
        ON section_students.student_id = students.student_id

        LEFT JOIN attendance
        ON attendance.student_id = students.student_id
        AND attendance.section_id = section_students.section_id

        WHERE section_students.section_id = %s
        AND students.student_id = %s

        GROUP BY students.student_id
        """, (section_id, section_id, search))

    else:
        cursor.execute("""
        SELECT 
            students.student_id,
            students.name,

            COALESCE(SUM(CASE WHEN attendance.status='Present' THEN 1 ELSE 0 END), 0) AS presents,

            COALESCE(SUM(CASE WHEN attendance.status='Absent' THEN 1 ELSE 0 END), 0) AS absents,

            (
                SELECT COUNT(DISTINCT date)
                FROM attendance
                WHERE section_id = %s
            ) AS total_classes

        FROM section_students

        JOIN students
        ON section_students.student_id = students.student_id

        LEFT JOIN attendance
        ON attendance.student_id = students.student_id
        AND attendance.section_id = section_students.section_id

        WHERE section_students.section_id = %s

        GROUP BY students.student_id
        """, (section_id, section_id))

    students = cursor.fetchall()

    cursor.execute("""
    SELECT section_id, section_name
    FROM sections
    WHERE instructor_id = %s
    ORDER BY section_name
    """, (session['instructor_id'],))

    sections = cursor.fetchall()

    return render_template(
        "section_page.html",
        section_name=section['section_name'],
        students=students,
        section_id=section_id,
        sections=sections,
        user=user
    )

@app.route('/add_student_to_section/<int:section_id>', methods=['POST'])
def add_student_to_section(section_id):

    student_id = request.form['student_id'].strip()

    cursor = db.cursor()

    # Check if student exists
    cursor.execute("""
        SELECT * FROM students
        WHERE student_id = %s
    """, (student_id,))

    student_exists = cursor.fetchone()

    if not student_exists:
        flash("Student does not exist.", "error")
        return redirect(f'/section/{section_id}')

    # Check if student already enrolled in section
    cursor.execute("""
        SELECT * FROM section_students
        WHERE section_id = %s AND student_id = %s
    """, (section_id, student_id))

    already_enrolled = cursor.fetchone()

    if already_enrolled:
        flash("Student is already enrolled in this section.", "warning")
        return redirect(f'/section/{section_id}')

    # Add student to section
    cursor.execute("""
        INSERT INTO section_students (section_id, student_id)
        VALUES (%s, %s)
    """, (section_id, student_id))

    db.commit()

    flash("Student added successfully.", "success")
    return redirect(f'/section/{section_id}')

@app.route('/remove_student/<int:section_id>/<student_id>') #main
def remove_student(section_id, student_id):

    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM section_students WHERE section_id=%s AND student_id=%s",
        (section_id, student_id)
    )

    db.commit()

    return redirect(f'/section/{section_id}')

@app.route('/take_attendance/<int:section_id>')
def take_attendance(section_id):

    cursor = db.cursor()
    today = date.today()

    cursor.execute("""
        SELECT id 
        FROM attendance
        WHERE section_id = %s AND date = %s
        LIMIT 1
    """, (section_id, today))

    existing_session = cursor.fetchone()

    if existing_session:
        return "Attendance has already been taken for this section today."

    cursor.execute("""
        SELECT student_id
        FROM section_students
        WHERE section_id = %s
    """, (section_id,))

    students = cursor.fetchall()

    for student in students:

        cursor.execute("""
            INSERT INTO attendance (student_id, section_id, date, time, status)
            VALUES (%s, %s, %s, NOW(), 'Absent')
        """, (student[0], section_id, today))

    db.commit()

    token = serializer.dumps(section_id)

    qr_data = url_for('mark_attendance', token=token, _external=True)

    qr = qrcode.make(qr_data)

    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")

    img_str = base64.b64encode(buffer.getvalue()).decode()

    return render_template(
        "attendance_session.html",
        qr_code=img_str,
        section_id=section_id
    )

@app.route('/mark_attendance/<token>') #main
def mark_attendance(token):

    try:
        section_id = serializer.loads(token, max_age=120)
    except SignatureExpired:
        return "Attendance session expired."
    except BadSignature:
        return "Invalid attendance session."

    if 'student_id' not in session:
        session['pending_attendance'] = token
        return redirect('/login')

    student_id = session['student_id']
    today = date.today()

    cursor = db.cursor()

    cursor.execute("""
        SELECT status FROM attendance
        WHERE student_id=%s AND section_id=%s AND date=%s
    """, (student_id, section_id, today))

    existing = cursor.fetchone()

    if existing and existing[0] == "Present":
        return "Attendance already recorded for today."

    cursor.execute("""
    UPDATE attendance
    SET status = 'Present', time = NOW()
    WHERE student_id = %s
    AND section_id = %s
    AND date = %s
    """, (student_id, section_id, date.today()))

    db.commit()

    return "Attendance marked successfully!"

@app.route('/section_attendance/<int:section_id>')
def section_attendance(section_id):

    cursor = db.cursor()

    cursor.execute("SELECT name FROM instructors WHERE instructor_id = %s", (session['instructor_id'],))
    user = cursor.fetchone()

    cursor.execute("""
                   SELECT section_id, section_name
                   FROM sections
                   WHERE instructor_id = %s
                   """, (session['instructor_id'],))
    sections = cursor.fetchall()

    cursor.execute("""
    SELECT attendance.date, students.name,
           attendance.student_id, attendance.status
    FROM attendance
    JOIN students
    ON attendance.student_id = students.student_id
    WHERE attendance.section_id = %s
    ORDER BY attendance.date DESC, students.name
    """, (section_id,))

    records = cursor.fetchall()

    cursor.execute("""
    SELECT 
        COUNT(CASE WHEN status='Present' THEN 1 END) * 100.0 / NULLIF(COUNT(id), 0)
    FROM attendance
    WHERE section_id = %s
    """, (section_id,))

    avg_attendance = cursor.fetchone()[0]

    cursor.execute(
    "SELECT section_name FROM sections WHERE section_id = %s",
    (section_id,))
    section_name_result = cursor.fetchone()
    section_name = section_name_result[0] if section_name_result else "Section"

    return render_template(
        "section_attendance.html",
        records=records,
        avg_attendance=round(avg_attendance, 2) if avg_attendance else 0,
        section_id=section_id,
        user={'name': user[0] if user else None},
        sections=sections,
        section_name=section_name
    )

@app.route('/student_dashboard')
def student_dashboard():

    if 'student_id' not in session:
        return redirect('/login')

    student_id = session['student_id']

    cursor = db.cursor()

    cursor.execute(
        "SELECT name FROM students WHERE student_id=%s",
        (student_id,)
    )
    student = cursor.fetchone()

    cursor.execute("""
    SELECT 
        sections.section_id,
        sections.section_name,

        (
            SELECT COUNT(DISTINCT date)
            FROM attendance
            WHERE section_id = sections.section_id
        ) AS total_classes,

        (
            SELECT COUNT(*)
            FROM attendance
            WHERE section_id = sections.section_id
            AND student_id = %s
            AND status = 'Present'
        ) AS presents

    FROM section_students
    JOIN sections
    ON section_students.section_id = sections.section_id

    WHERE section_students.student_id = %s
    """, (student_id, student_id))

    sections = cursor.fetchall()

    section_data = []

    for s in sections:
        section_id, section_name, total, present = s

        if total == 0:
            percentage = 0
        else:
            percentage = round((present / total) * 100)

        section_data.append((section_id, section_name, total, present, percentage))

    # Get user info for profile panel
    cursor.execute("""
    SELECT students.name, student_accounts.password
    FROM students
    JOIN student_accounts
    ON students.student_id = student_accounts.student_id
    WHERE students.student_id = %s
    """, (student_id,))

    user = cursor.fetchone()

    return render_template(
        "student_dashboard.html",
        student_name = student[0],
        sections = section_data,
        user=user
    )

@app.route('/student_section/<int:section_id>')
def student_section(section_id):

    if 'student_id' not in session:
        return redirect('/login')

    student_id = session['student_id']

    cursor = db.cursor()

    cursor.execute(
        "SELECT section_name FROM sections WHERE section_id=%s",
        (section_id,)
    )

    section = cursor.fetchone()

    return render_template(
        "student_section.html",
        section_id = section_id,
        section_name = section[0]
    )

@app.route('/student_attendance')
def student_attendance():

    if 'student_id' not in session:
        return redirect('/login')

    student_id = session['student_id']

    cursor = db.cursor()

    cursor.execute("""
        SELECT sections.section_name, attendance.date, attendance.status
        FROM attendance
        JOIN sections
        ON attendance.section_id = sections.section_id
        WHERE attendance.student_id = %s
        ORDER BY attendance.date DESC
    """, (student_id,))

    records = cursor.fetchall()

    return render_template("student_attendance.html", records=records)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)