from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import sqlite3
import shutil
from functools import wraps

app = Flask(__name__)
app.secret_key = 'rvce_fee_management_secret_2024'  # Required for session management

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DB_PATH = os.path.join(BASE_DIR, 'rvce_fee.db')
TMP_DB_PATH = '/tmp/rvce_fee.db'
DB_PATH = None


def get_db_path():
    """
    Return a writable SQLite path.
    On serverless platforms, project files can be read-only, so we prefer /tmp.
    """
    global DB_PATH
    if DB_PATH:
        return DB_PATH

    env_db_path = os.environ.get('DB_PATH')
    candidates = [c for c in [env_db_path, TMP_DB_PATH, PROJECT_DB_PATH] if c]

    for candidate in candidates:
        try:
            parent = os.path.dirname(candidate) or '.'
            os.makedirs(parent, exist_ok=True)

            # Seed /tmp DB from bundled project DB when available.
            if candidate == TMP_DB_PATH and os.path.exists(PROJECT_DB_PATH) and not os.path.exists(candidate):
                shutil.copy2(PROJECT_DB_PATH, candidate)

            # Confirm writable path before using it.
            with open(candidate, 'a', encoding='utf-8'):
                pass

            DB_PATH = candidate
            return DB_PATH
        except OSError:
            continue

    # Last-resort fallback to keep app serving instead of crashing.
    DB_PATH = ':memory:'
    return DB_PATH


def get_db_connection():
    return sqlite3.connect(get_db_path())


def is_authenticated():
    """True when user has an active authenticated session."""
    return bool(session.get('role'))

# ---------- ACCESS CONTROL DECORATOR ----------
def admin_owner_required(f):
    """Decorator to restrict access to admin and owner only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('role', '').lower()
        if role not in ['admin', 'owner']:
            return "Access Denied. This page is for Admin/Owner only.", 403
        return f(*args, **kwargs)
    return decorated_function

# ---------- DATABASE INIT ----------
def init_db():
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                dept TEXT,
                email TEXT,
                year TEXT,
                password TEXT
            )
        ''')
        # Pending fees table for imported Excel rows (server-side storage)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pending_fees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT,
                department TEXT,
                fee_type TEXT,
                amount REAL,
                due_date TEXT,
                imported_by TEXT,
                created_at TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                role TEXT PRIMARY KEY,
                profile_picture TEXT,
                profile_name TEXT,
                updated_at TEXT
            )
        ''')
        conn.commit()
    finally:
        conn.close()

init_db()


# ---------- HOME ----------
@app.route('/')
def index():
    if is_authenticated():
        return redirect(url_for('dashboard'))
    return render_template('index.html')


# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_authenticated():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        dept = request.form['dept']
        email = request.form['email']
        year = request.form['year']
        pwd = request.form['password']

        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO students (name, dept, email, year, password) VALUES (?,?,?,?,?)",
                (name, dept, email, year, pwd)
            )

        return redirect(url_for('login', role='STUDENT'))

    return render_template('register.html')


# ---------- LOGIN ----------
@app.route('/login/<role>', methods=['GET', 'POST'])
def login(role):
    if is_authenticated():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        entered_pwd = request.form['password']
        # store username in session for display in profile
        username = request.form.get('username', '').strip()

        if (role == 'ADMIN' and entered_pwd == 'admin.rvce.in') or \
           (role == 'OWNER' and entered_pwd == 'owner.rvce.in') or \
           (role == 'STUDENT'):

            # Store role and username in session
            session['role'] = role.lower()  # Store as lowercase: 'admin', 'owner', 'student'
            if username:
                session['username'] = username
            # 👉 Go to dashboard in SAME PAGE
            return redirect(url_for('dashboard'))

        return "Invalid Password"

    return render_template('login.html', role=role)

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if not is_authenticated():
        return redirect(url_for('index'))
    role = session.get('role', 'student')  # Default to 'student' if not in session
    user_id = session.get('username', '') or 'N/A'
    return render_template('dashboard.html', role=role, user_id=user_id)

# ---------- TOTAL BILLS PAGE ----------
@app.route('/total-bill')
@app.route('/total-bill.html')
@admin_owner_required
def total_bill():
    return render_template('total-bill.html')


# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.after_request
def add_no_cache_headers(response):
    """
    Prevent browser back-cache from showing old auth pages after login/logout.
    """
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# ---------- API: Pending Fees (server-side storage) ----------
@app.route('/api/pending-fees', methods=['GET'])
def get_pending_fees():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, student_name, department, fee_type, amount, due_date FROM pending_fees ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()

    data = []
    for r in rows:
        data.append({
            'id': r[0],
            'student_name': r[1],
            'department': r[2],
            'fee_type': r[3],
            'amount': r[4],
            'due_date': r[5]
        })
    return jsonify(data)


@app.route('/api/pending-fees/import', methods=['POST'])
def import_pending_fees():
    role = session.get('role', '').lower()
    if role not in ['admin', 'owner']:
        return "Access Denied", 403

    items = request.get_json() or []
    if not isinstance(items, list):
        return "Invalid payload", 400

    conn = get_db_connection()
    cur = conn.cursor()
    for it in items:
        student_name = it.get('student_name') or it.get('name') or ''
        department = it.get('department') or ''
        fee_type = it.get('fee_type') or it.get('type') or ''
        try:
            amount = float(it.get('amount') or 0)
        except Exception:
            amount = 0
        due_date = it.get('due_date') or ''

        cur.execute(
            "INSERT INTO pending_fees (student_name, department, fee_type, amount, due_date, imported_by, created_at) VALUES (?,?,?,?,?,?,datetime('now'))",
            (student_name, department, fee_type, amount, due_date, role)
        )

    conn.commit()

    # Return the last N inserted rows to the client
    cur.execute("SELECT id, student_name, department, fee_type, amount, due_date FROM pending_fees ORDER BY id DESC LIMIT ?", (len(items) or 0,))
    rows = cur.fetchall()
    conn.close()

    data = []
    for r in reversed(rows):
        data.append({
            'id': r[0],
            'student_name': r[1],
            'department': r[2],
            'fee_type': r[3],
            'amount': r[4],
            'due_date': r[5]
        })
    return jsonify(data), 201


@app.route('/api/pending-fees/<int:fee_id>', methods=['DELETE'])
def delete_pending_fee(fee_id):
    role = session.get('role', '').lower()
    if role not in ['admin', 'owner', 'student']:
        return "Access Denied", 403

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM pending_fees WHERE id = ?", (fee_id,))
    conn.commit()
    conn.close()
    return ('', 204)


@app.route('/api/pending-fees/delete-by-student', methods=['POST'])
def delete_pending_fee_by_student():
    role = session.get('role', '').lower()
    if role not in ['admin', 'owner']:
        return "Access Denied", 403

    data = request.get_json() or {}
    student_name = (data.get('student_name') or '').strip()
    due_date = (data.get('due_date') or '').strip()

    if not student_name or not due_date:
        return jsonify({'deleted': 0})

    conn = get_db_connection()
    cur = conn.cursor()
    # Normalize for case-insensitive matching
    cur.execute(
        "DELETE FROM pending_fees WHERE LOWER(student_name) = LOWER(?) AND due_date = ?",
        (student_name, due_date)
    )
    deleted_count = cur.rowcount
    conn.commit()
    conn.close()

    return jsonify({'deleted': deleted_count}), 200


# ---------- API: User Profile ----------
@app.route('/api/profile', methods=['GET'])
def get_profile():
    role = session.get('role', 'student').lower()
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get or create profile for this user (identified by role)
    cur.execute("SELECT profile_picture, profile_name FROM user_profiles WHERE role = ?", (role,))
    result = cur.fetchone()
    conn.close()
    
    # Prefer session username if available, else use stored profile_name or a role-based default
    session_name = session.get('username')
    profile_name = None
    picture = None
    if result:
        picture, profile_name = result[0], result[1]

    name_to_send = session_name or profile_name or (role.capitalize() + ' User')

    return jsonify({
        'picture': picture,
        'name': name_to_send,
        'role': role.capitalize()
    })


@app.route('/api/profile/upload', methods=['POST'])
def upload_profile():
    role = session.get('role', 'student').lower()
    data = request.get_json() or {}
    picture_base64 = data.get('picture')
    name = data.get('name', '')
    
    if not picture_base64:
        return "No picture provided", 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create table if not exists
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            role TEXT PRIMARY KEY,
            profile_picture TEXT,
            profile_name TEXT,
            updated_at TEXT
        )
    ''')
    
    # Insert or replace profile
    cur.execute(
        "INSERT OR REPLACE INTO user_profiles (role, profile_picture, profile_name, updated_at) VALUES (?, ?, ?, datetime('now'))",
        (role, picture_base64, name or (role.capitalize() + ' User'))
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Profile updated'}), 200


# ---------- RUN SERVER ----------
if __name__ == "__main__":
    app.run(debug=True)
