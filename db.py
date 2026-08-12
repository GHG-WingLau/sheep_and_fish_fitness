import streamlit as st
import json
from datetime import datetime

# ---------- CONNECTION ----------
def get_connection():
    """Get the underlying SQLAlchemy engine from st.connection."""
    conn = st.connection("neon", type="sql")
    # The actual SQLAlchemy engine is inside _instance
    return conn._instance

def get_raw_connection():
    """Get a raw psycopg2 connection for executing raw SQL."""
    engine = get_connection()
    return engine.raw_connection()

def execute_query(sql, params=None):
    """Execute a query that doesn't return results (INSERT, UPDATE, CREATE)."""
    raw_conn = get_raw_connection()
    cursor = raw_conn.cursor()
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        raw_conn.commit()
        return True
    except Exception as e:
        raw_conn.rollback()
        raise e
    finally:
        cursor.close()
        raw_conn.close()

def fetch_query(sql, params=None):
    """Execute a query that returns results (SELECT)."""
    # Use the SQLAlchemy engine directly for fetching
    engine = get_connection()
    with engine.connect() as conn:
        if params:
            result = conn.execute(sql, params)
        else:
            result = conn.execute(sql)
        # Fetch all rows as list of dicts
        rows = result.mappings().all()
        # Convert to pandas DataFrame for compatibility with original code
        import pandas as pd
        return pd.DataFrame(rows)

# ---------- INITIALIZATION ----------
def init_db():
    """Create all required tables if they don't exist."""
    raw_conn = get_raw_connection()
    cursor = raw_conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            assessment_date TEXT NOT NULL,
            total_score INTEGER,
            level TEXT,
            sarc_score INTEGER,
            calf_score INTEGER,
            single_score INTEGER,
            squat_score INTEGER,
            raw_payload TEXT
        )
    """)
    
    # Training progress table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_progress (
            id SERIAL PRIMARY KEY,
            user_email TEXT NOT NULL,
            username TEXT NOT NULL,
            week INTEGER DEFAULT 1,
            day INTEGER DEFAULT 1,
            exercise_ids TEXT,
            rpe_scores TEXT,
            session_date TEXT,
            completed BOOLEAN DEFAULT FALSE
        )
    """)
    
    # Rest reflections table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rest_reflections (
            id SERIAL PRIMARY KEY,
            user_email TEXT NOT NULL,
            username TEXT NOT NULL,
            week INTEGER,
            day INTEGER,
            reflection TEXT,
            rest_type TEXT,
            created_at TEXT
        )
    """)
    
    raw_conn.commit()
    cursor.close()
    raw_conn.close()

# ---------- USER FUNCTIONS ----------
def user_exists(email):
    """Check if a user with the given email exists."""
    result = fetch_query("SELECT email FROM users WHERE email = %s", (email,))
    return len(result) > 0

def register_user(email, username, result):
    """Register a new user with onboarding results."""
    if user_exists(email):
        return False, "Email already registered. Please use 'Update Profile' or login with a different email."
    
    sql = """
        INSERT INTO users (email, username, assessment_date, total_score, level, sarc_score, calf_score, single_score, squat_score, raw_payload)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        email,
        username,
        datetime.now().isoformat(),
        result['total_score'],
        result['level'],
        result['sarc_score'],
        result['calf_score'],
        result['single_score'],
        result['squat_score'],
        json.dumps(result)
    )
    try:
        execute_query(sql, params)
        return True, "Registration successful! Your data has been saved."
    except Exception as e:
        return False, f"Registration failed: {str(e)}"

def update_user(email, username, result):
    """Update an existing user's profile."""
    # Verify both email and username match
    verify = fetch_query("SELECT email, username FROM users WHERE email = %s AND username = %s", (email, username))
    if len(verify) == 0:
        return False, "No matching user found. Please check your email and username."
    
    sql = """
        UPDATE users SET
            assessment_date = %s,
            total_score = %s,
            level = %s,
            sarc_score = %s,
            calf_score = %s,
            single_score = %s,
            squat_score = %s,
            raw_payload = %s
        WHERE email = %s AND username = %s
    """
    params = (
        datetime.now().isoformat(),
        result['total_score'],
        result['level'],
        result['sarc_score'],
        result['calf_score'],
        result['single_score'],
        result['squat_score'],
        json.dumps(result),
        email,
        username
    )
    try:
        execute_query(sql, params)
        return True, "Profile updated successfully!"
    except Exception as e:
        return False, f"Update failed: {str(e)}"

def retrieve_user(email, username):
    """Retrieve a user's stored profile."""
    result = fetch_query("""
        SELECT email, username, assessment_date, total_score, level, sarc_score, calf_score, single_score, squat_score, raw_payload
        FROM users
        WHERE email = %s AND username = %s
    """, (email, username))
    
    if len(result) == 0:
        return None
    
    row = result.iloc[0]
    raw_payload = {}
    if row['raw_payload']:
        try:
            raw_payload = json.loads(row['raw_payload'])
        except:
            raw_payload = {}
    
    return {
        'email': row['email'],
        'username': row['username'],
        'assessment_date': row['assessment_date'],
        'total_score': row['total_score'],
        'level': row['level'],
        'sarc_score': row['sarc_score'],
        'calf_score': row['calf_score'],
        'single_score': row['single_score'],
        'squat_score': row['squat_score'],
        'raw_payload': raw_payload
    }

# ---------- TRAINING PROGRESS FUNCTIONS ----------
def save_training_session(user_email, username, week, day, exercise_ids, rpe_scores, completed=False):
    """Save a training session record."""
    sql = """
        INSERT INTO training_progress (user_email, username, week, day, exercise_ids, rpe_scores, session_date, completed)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        user_email,
        username,
        week,
        day,
        json.dumps(exercise_ids),
        json.dumps(rpe_scores),
        datetime.now().isoformat(),
        completed
    )
    execute_query(sql, params)

def get_user_progress(user_email, username):
    """Get all training progress for a user."""
    return fetch_query("""
        SELECT week, day, exercise_ids, rpe_scores, session_date, completed
        FROM training_progress
        WHERE user_email = %s AND username = %s
        ORDER BY session_date DESC
    """, (user_email, username))

def get_current_week_day(user_email, username):
    """Get the current week and day for a user."""
    result = fetch_query("""
        SELECT week, day
        FROM training_progress
        WHERE user_email = %s AND username = %s
        ORDER BY session_date DESC
        LIMIT 1
    """, (user_email, username))
    
    if len(result) == 0:
        return 1, 1
    row = result.iloc[0]
    return row['week'], row['day']

# ---------- REST REFLECTION FUNCTIONS ----------
def save_rest_reflection(user_email, username, week, day, rest_type, reflection):
    """Save a rest day reflection."""
    sql = """
        INSERT INTO rest_reflections (user_email, username, week, day, rest_type, reflection, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        user_email,
        username,
        week,
        day,
        rest_type,
        reflection,
        datetime.now().isoformat()
    )
    execute_query(sql, params)

def get_rest_reflections(user_email, username):
    """Get all rest reflections for a user."""
    return fetch_query("""
        SELECT week, day, rest_type, reflection, created_at
        FROM rest_reflections
        WHERE user_email = %s AND username = %s
        ORDER BY created_at DESC
    """, (user_email, username))
