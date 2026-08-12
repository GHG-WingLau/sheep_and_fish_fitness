import streamlit as st
import json
from datetime import datetime
import pandas as pd
import psycopg2
from psycopg2 import InterfaceError, OperationalError

# ---------- CONNECTION ----------
def get_raw_connection():
    """
    Get a raw psycopg2 connection. If the connection is closed, dispose the engine
    and retry once.
    """
    max_retries = 2
    for attempt in range(max_retries):
        try:
            conn = st.connection("neon", type="sql")
            engine = conn._instance
            raw_conn = engine.raw_connection()
            # Test the connection
            with raw_conn.cursor() as cur:
                cur.execute("SELECT 1")
            return raw_conn
        except (InterfaceError, OperationalError, AttributeError) as e:
            if attempt < max_retries - 1:
                st.warning(f"Database connection reconnecting... (attempt {attempt + 2}/{max_retries})")
                try:
                    engine = conn._instance
                    engine.dispose()
                except:
                    pass
                continue
            else:
                raise RuntimeError(f"Failed to connect to database after {max_retries} attempts: {e}")
    raise RuntimeError("Unable to establish database connection")

def execute_query(sql, params=None):
    """Execute a query that doesn't return results (INSERT, UPDATE, CREATE)."""
    raw_conn = get_raw_connection()
    try:
        with raw_conn.cursor() as cursor:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            raw_conn.commit()
    finally:
        raw_conn.close()

def fetch_query(sql, params=None):
    """Execute a query that returns results (SELECT), returns pandas DataFrame."""
    raw_conn = get_raw_connection()
    try:
        with raw_conn.cursor() as cursor:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]
            data = [dict(zip(col_names, row)) for row in rows]
            return pd.DataFrame(data)
    finally:
        raw_conn.close()

# ---------- INITIALIZATION ----------
def init_db():
    """Create all required tables if they don't exist."""
    execute_query("""
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
            chair_score INTEGER,
            chair_stands INTEGER,
            raw_payload TEXT
        )
    """)
    
    execute_query("""
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
    
    execute_query("""
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

# ---------- USER FUNCTIONS ----------
def user_exists(email):
    result = fetch_query("SELECT email FROM users WHERE email = %s", (email,))
    return len(result) > 0

def register_user(email, username, result):
    if user_exists(email):
        return False, "Email already registered. Please use 'Update Profile' or login with a different email."
    
    sql = """
        INSERT INTO users (email, username, assessment_date, total_score, level, sarc_score, calf_score, single_score, chair_score, chair_stands, raw_payload)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        email,
        username,
        datetime.now().isoformat(),
        result.get('total_score', 0),
        result.get('level', 'Level 0'),
        result.get('sarc_score', 0),
        result.get('calf_score', 0),
        result.get('single_score', 0),
        result.get('chair_score', 0),
        result.get('chair_stands', 0),
        json.dumps(result)
    )
    try:
        execute_query(sql, params)
        return True, "Registration successful! Your data has been saved."
    except Exception as e:
        return False, f"Registration failed: {str(e)}"

def update_user(email, username, result):
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
            chair_score = %s,
            chair_stands = %s,
            raw_payload = %s
        WHERE email = %s AND username = %s
    """
    params = (
        datetime.now().isoformat(),
        result.get('total_score', 0),
        result.get('level', 'Level 0'),
        result.get('sarc_score', 0),
        result.get('calf_score', 0),
        result.get('single_score', 0),
        result.get('chair_score', 0),
        result.get('chair_stands', 0),
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
    result = fetch_query("""
        SELECT email, username, assessment_date, total_score, level, sarc_score, calf_score, single_score, chair_score, chair_stands, raw_payload
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
        'chair_score': row['chair_score'],
        'chair_stands': row['chair_stands'],
        'raw_payload': raw_payload
    }

# ---------- TRAINING PROGRESS FUNCTIONS ----------
def save_training_session(user_email, username, week, day, exercise_ids, rpe_scores, completed=False):
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
    return fetch_query("""
        SELECT week, day, exercise_ids, rpe_scores, session_date, completed
        FROM training_progress
        WHERE user_email = %s AND username = %s
        ORDER BY session_date DESC
    """, (user_email, username))

def get_current_week_day(user_email, username):
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
    return fetch_query("""
        SELECT week, day, rest_type, reflection, created_at
        FROM rest_reflections
        WHERE user_email = %s AND username = %s
        ORDER BY created_at DESC
    """, (user_email, username))
