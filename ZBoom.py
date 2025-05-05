from flask import Flask, render_template, request, redirect, url_for 
from supabase import create_client, Client

# Supabase credentials
SUPABASE_URL = 'https://lwjkwghmheajwoyosqes.supabase.co'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx3amt3Z2htaGVhandveW9zcWVzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYwMTkyNTYsImV4cCI6MjA2MTU5NTI1Nn0.YfZPE5xxXOFp0fXdMqBimChj8--XfIv2O5DKi_YBwT0'

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

app = Flask(__name__)
app.secret_key = 'your-flask-secret-key'

@app.route('/')
def login():
    return render_template('login.html')



@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form['student-email'].strip()
        passcode = request.form['passcode'].strip()

        if student_id and passcode:
            
            return redirect(url_for('student_equipment'))  
        else:
            return "Please enter both Student ID and Passcode.", 400  

    return render_template('student-alogin.html')  


@app.route('/professor-login', methods=['GET', 'POST'])
def professor_login():
    if request.method == 'POST':
        professor_id = request.form['professor-email'].strip()
        passcode = request.form['professor-passcode'].strip()

        if professor_id and passcode:
            return redirect(url_for('professor_dashboard'))
        else:
            return "Please enter both Professor ID and Passcode.", 400

    return render_template('professor-alogin.html')


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_id = request.form['admin-email'].strip()
        passcode = request.form['admin-passcode'].strip()

        if admin_id and passcode:
            
            return redirect(url_for('admin_dashboard'))  
        else:
            return "Please enter both Admin ID and Passcode.", 400  

    return render_template('admin-alogin.html')  


@app.route('/student-equipment')
def student_equipment():
    return render_template('student-equipments.html')

@app.route('/student-progress')
def student_progress():
    return render_template('student-progressreport.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    return render_template('admin-dashboard.html')

@app.route('/admin-equipment')
def admin_equipment():
    return render_template('admin-equipment.html')

@app.route('/admin-reservation')
def admin_reservation():
    return render_template('admin-reservation.html')

@app.route('/professor-dashboard')
def professor_dashboard():
    return render_template('professor-dashboard.html')


if __name__ == '__main__':
    app.run(debug=True)

    
    


