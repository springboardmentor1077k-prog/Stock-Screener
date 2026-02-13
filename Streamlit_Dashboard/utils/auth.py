import hashlib
import sqlite3
import os
import streamlit as st

# Path for the SQLite database
DB_FILE = os.path.join(os.path.dirname(__file__), "users.db")

def get_db_connection():
    """Create a database connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database and create users table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if table is empty to add predefined users
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        initial_users = [
            ("admin", hash_password("admin123")),
            ("user1", hash_password("user123")),
            ("user2", hash_password("user123")),
            ("analyst", hash_password("analyst123")),
            ("manager", hash_password("manager123"))
        ]
        cursor.executemany('INSERT INTO users (username, password_hash) VALUES (?, ?)', initial_users)
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password for storing using SHA-256."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_password_hash(password, hashed_password):
    """Check if the provided password matches the stored hash."""
    return hash_password(password) == hashed_password

def validate_password(password):
    """Validate password requirements (6-8 characters)."""
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    return True, ""

def register_user(username, password):
    """Register a new user in the database after validation."""
    if not username:
        return False, "Username cannot be empty."
    
    valid_pwd, pwd_msg = validate_password(password)
    if not valid_pwd:
        return False, pwd_msg
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                       (username, hash_password(password)))
        conn.commit()
        return True, "Registration successful! Please log in."
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    finally:
        conn.close()

def authenticate_user(username, password):
    """Authenticate a user against stored credentials in the database."""
    if not username or not password:
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result and check_password_hash(password, result['password_hash']):
        return True
    return False

def init_auth_session():
    """Initialize session state and ensure database is ready."""
    init_db() # Ensure DB and table exist
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "auth_page" not in st.session_state:
        st.session_state.auth_page = "login" # 'login' or 'signup'

def login(username):
    """Set the user as authenticated in the session state."""
    st.session_state.authenticated = True
    st.session_state.username = username
    st.rerun()

def logout():
    """Clear authentication from the session state and redirect to login."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.auth_page = "login"
    st.rerun()
