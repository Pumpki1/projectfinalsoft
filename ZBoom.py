from flask import Flask, render_template, request, redirect, url_for, jsonify, session 
from supabase import create_client, Client
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import os


# Supabase credentials
SUPABASE_URL = 'https://lwjkwghmheajwoyosqes.supabase.co'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx3amt3Z2htaGVhandveW9zcWVzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYwMTkyNTYsImV4cCI6MjA2MTU5NTI1Nn0.YfZPE5xxXOFp0fXdMqBimChj8--XfIv2O5DKi_YBwT0'

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

app = Flask(__name__)
CORS(app)
app.secret_key = 'your-flask-secret-key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route('/')
def login():
    return render_template('login.html')



@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form['student-ID'].strip()  # Changed from 'student-email' to 'student-ID'
        passcode = request.form['passcode'].strip()

        if student_id and passcode:
            # Validate student credentials in your database
            student = supabase.table('students')\
                .select('*')\
                .eq('id', student_id)\
                .execute()
            
            # Check if student exists and password matches
            if student.data and len(student.data) > 0:
                # Store student ID in session for future requests
                session['student_id'] = student_id
                return redirect(url_for('student_equipment', student_id=student_id))
            else:
                return "Invalid student ID or passcode", 400
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
    # Get student ID from session or query parameter
    student_id = session.get('student_id') or request.args.get('student_id')
    
    if not student_id:
        return redirect(url_for('student_login'))

    inventory = supabase.table('inventory')\
        .select('*')\
        .execute()\
        .data

    notifications = (
        supabase
          .table('borrowed_requests')
          .select('*, borrowed_items(*)')
          .order('date_filed', desc=True)
          .limit(10)
          .execute()
          .data
    )

    return render_template(
        'student-equipments.html',
        equipments=inventory,
        notifications=notifications,
        student_id=student_id
    )


@app.route('/submit-borrow-request', methods=['POST'])
def submit_borrow_request():
    data = request.get_json()

    # 1. Upsert the student row (so the FK check will pass)
    #    Primary key is `id`, so include it in the dict for upsert.
    supabase.table('students').upsert({
        'id':      data['student_id'],   # e.g. "24-262718"
        'name':    data['student_name'],
        'section': data['section']
    }).execute()  # :contentReference[oaicite:0]{index=0}

    # 2. Insert master request, now that students.id exists
    req = {
      'laboratory':      data['laboratory'],
      'student_id':      data['student_id'],    # FK to students.id
      'student_name':    data['student_name'],
      'faculty_name':    data['faculty_name'],
      'subject':         data['subject'],
      'section':         data['section'],
      'date_filed':      data['date_filed'],
      'date_needed':     data['date_needed'],
      'status_professor':'pending'
    }
    res = supabase.table('borrowed_requests').insert(req).execute()
    rid = res.data[0]['id']

    # 3. Insert each item (unchanged)
    for item in data['items']:
        supabase.table('borrowed_items').insert({
            'request_id':   rid,
            'inventory_id': None,
            'item_name':    item['item_name'],
            'quantity':     item['quantity'],
            'status':       'pending',
            'updated_at':   data['date_filed']
        }).execute()

    return jsonify({'success': True}), 200




@app.route('/student-progress')
def student_progress():
    # Get student ID from session or query parameter
    student_id = session.get('student_id') or request.args.get('student_id')
    
    if not student_id:
        return redirect(url_for('student_login'))
    
    return render_template('student-progressreport.html', student_id=student_id)

@app.route('/api/student-requests/<student_id>')
def get_student_requests(student_id):
    """API endpoint to fetch requests for a specific student"""
    try:
        # Query requests for the specific student
        requests = supabase.table('borrowed_requests')\
            .select('*')\
            .eq('student_id', student_id)\
            .order('date_filed', desc=True)\
            .execute()
        
        return jsonify(requests.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/admin-dashboard')
def admin_dashboard():
    return render_template('admin-dashboard.html')

@app.route('/admin-equipment')
def admin_equipment():
    return render_template('admin-equipment.html')

@app.route('/api/equipment', methods=['GET'])
def get_equipment():
    res = supabase.table('inventory') \
                   .select('id, name, quantity') \
                   .order('id', desc=False) \
                   .execute()
    return jsonify(res.data), 200

@app.route('/api/equipment', methods=['POST'])
def upsert_equipment():
    payload = request.json
    name = payload.get('name', '').strip()
    quantity = payload.get('quantity')
    if not name or not isinstance(quantity, int) or quantity < 0:
        return jsonify({'error': 'Invalid name or quantity'}), 400
    record = {'name': name, 'quantity': quantity}
    if payload.get('id'):
        try:
            record['id'] = int(payload['id'])
        except ValueError:
            return jsonify({'error': 'ID must be an integer'}), 400
    res = supabase.table('inventory') \
                   .upsert(record, on_conflict='id') \
                   .execute()
    return jsonify(res.data), 200

@app.route('/api/equipment/<int:item_id>', methods=['DELETE'])
def delete_equipment(item_id):
    res = supabase.table('inventory') \
                   .delete() \
                   .eq('id', item_id) \
                   .execute()
    if res.count:
        return jsonify({'deleted': res.count}), 200
    return jsonify({'error': 'Item not found'}), 404


@app.route('/admin-reservation')
def admin_reservation():
    return render_template('admin-reservation.html')


@app.route('/fetch-admin-requests')
def fetch_admin_requests():
    rows = supabase.table('borrowed_requests')\
        .select('id, laboratory, student_name, faculty_name, subject, section, date_filed, date_needed, status_professor, status_admin, borrowed_items(item_name, quantity)')\
        .eq('status_professor', 'approved')\
        .execute().data
    return jsonify([{**r, 'items': r['borrowed_items']} for r in rows]), 200


@app.route('/admin-action/<int:req_id>/<action>', methods=['POST'])
def admin_action(req_id, action):
    new_status = 'approved' if action == 'approve' else 'declined'
    supabase.table('borrowed_requests').update({'status_admin': new_status}).eq('id', req_id).execute()
    supabase.table('borrowed_items').update({'status': new_status}).eq('request_id', req_id).execute()
    return jsonify({'success': True}), 200


@app.route('/fetch-admin-progress')
def fetch_admin_progress():
    # Modify this query to check for admin approval
    rows = supabase.table('borrowed_items')\
        .select('id, request_id, item_name, quantity, status, borrowed_requests(student_name, laboratory, subject, section, date_filed, date_needed, status_admin)')\
        .eq('status', 'approved')\
        .execute().data

    # Filter out items that don't have admin approval
    rows = [item for item in rows if item['borrowed_requests']['status_admin'] == 'approved']

    # Rest of your aggregation code remains the same
    # Aggregate items by request_id
    progress_data = {}
    for item in rows:
        req_id = item['request_id']
        if req_id not in progress_data:
            request = item['borrowed_requests']
            progress_data[req_id] = {
                'request_id': req_id,
                'student_name': request['student_name'],
                'laboratory': request['laboratory'],
                'subject': request['subject'],
                'section': request['section'],
                'date_filed': request['date_filed'],
                'date_needed': request['date_needed'],
                'item_statuses': [],
                'approval_status': request['status_admin']  # Include approval status
            }
        progress_data[req_id]['item_statuses'].append(item['status'])

    # Determine overall status
    for data in progress_data.values():
        statuses = data['item_statuses']
        if all(s == 'returned' for s in statuses):
            data['overall_status'] = 'returned'
        elif all(s == 'in' for s in statuses):
            data['overall_status'] = 'in'
        elif all(s == 'out' for s in statuses):
            data['overall_status'] = 'out'
        else:
            data['overall_status'] = 'mixed'

    return jsonify(list(progress_data.values())), 200


@app.route('/admin-item-action/<int:item_id>/<status>', methods=['POST'])
def admin_item_action(item_id, status):
    # Validate status
    if status not in ['in', 'out', 'returned']:
        return jsonify({'error': 'Invalid status'}), 400

    try:
        # Update the item's status - using item_status column, not status
        supabase.table('borrowed_items')\
            .update({
                'item_status': status,
            })\
            .eq('id', item_id)\
            .execute()
            
        return jsonify({'success': True}), 200
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error updating item status: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/fetch-request-items/<int:request_id>')
def fetch_request_items(request_id):
    rows = supabase.table('borrowed_items')\
        .select('id, item_name, quantity, status')\
        .eq('request_id', request_id)\
        .execute().data
    return jsonify(rows), 200



@app.route('/professor-dashboard')
def professor_dashboard():
    return render_template('professor-dashboard.html')


@app.route('/fetch-professor-requests')
def fetch_professor_requests():
 
    rows = supabase.table('borrowed_requests')\
        .select('id, laboratory, student_name, faculty_name, subject, section, date_filed, date_needed, status_professor, borrowed_items(item_name, quantity, status)')\
        .eq('status_professor', 'pending')\
        .execute().data
    
    return jsonify(rows), 200


@app.route('/professor-action/<int:request_id>/<action>', methods=['POST'])
def professor_action(request_id, action):
    # action should be 'approve' or 'decline'
    new_status = 'approved' if action == 'approve' else 'declined'
    # Update master row
    supabase.table('borrowed_requests')\
        .update({'status_professor': new_status})\
        .eq('id', request_id).execute()
    # Update all associated items
    supabase.table('borrowed_items')\
        .update({'status': new_status})\
        .eq('request_id', request_id).execute()
    return jsonify({'success': True}), 200




if __name__ == '__main__':
    app.run(debug=True)

    
    


