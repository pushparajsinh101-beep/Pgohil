from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import mysql.connector

# Clean initialization lets Flask automatically find your /templates folder
app = Flask(__name__)
app.secret_key = 'your_super_secret_session_key_here'

# SQL Configuration
db_config = {
    'host': 'localhost',
    'user': 'root', 
    'password': '', 
    'database': 'p_gohil_db'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL,
                role VARCHAR(50) DEFAULT 'User'
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("Database connectivity verified successfully.")
    except mysql.connector.Error as err:
        print(f"Database Init Warning: {err.msg}.")

# ----------------------------------------------------
# PAGE ROUTING
# ----------------------------------------------------

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/reset-password')
def reset_password_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('reset_password.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('pgohil.html', user_name=session.get('user_name'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


# ----------------------------------------------------
# BACKEND API ENDPOINTS
# ----------------------------------------------------

@app.route('/api/signin', methods=['POST'])
def sign_in():
    data = request.json
    email_input = data.get('email', '').strip()
    password_input = data.get('password', '')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email_input, password_input))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            return jsonify({"status": "success", "message": f"Welcome back, {user['name']}!"})
        else:
            return jsonify({"status": "error", "message": "Invalid email or password credentials."})
    except Exception:
        return jsonify({"status": "error", "message": "Database link unavailable."})


@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not name or not email or not password:
        return jsonify({"status": "error", "message": "All fields are required to register."})
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify unique email configuration
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "This email address is already registered."})
            
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'User')",
            (name, email, password)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Account created successfully!"})
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": f"Database processing error: {err.msg}"})


@app.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    data = request.json
    email = data.get('email', '').strip()
    new_password = data.get('password', '')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "No account configuration registered with this email address."})
        
        cursor.execute("UPDATE users SET password = %s WHERE email = %s", (new_password, email))
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Your profile password has been reset successfully!"})
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": f"Database error encountered: {err.msg}"})


# ----------------------------------------------------
# ADMINISTRATIVE TABLES UTILITY
# ----------------------------------------------------

@app.route('/api/users', methods=['GET'])
def get_users():
    if 'user_id' not in session:
        return jsonify([])
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email, role FROM users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(users)
    except Exception:
        return jsonify([])

@app.route('/api/users/edit/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"})
    data = request.json
    new_name = data.get('name', '').strip()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET name = %s WHERE id = %s", (new_name, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "User configuration updated successfully!"})
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": f"Failed to modify: {err.msg}"})

@app.route('/api/users/delete/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"})
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "User profile cleared successfully!"})
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": f"Failed to delete: {err.msg}"})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)