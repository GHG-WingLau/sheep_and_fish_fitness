import streamlit as st
import json
from datetime import datetime

# ---------- CONNECTION ----------
def get_connection():
    """Get Neon PostgreSQL connection using st.connection."""
    return st.connection("neon", type="sql")

# ---------- INITIALIZATION ----------
def init_db():
    """Create all required tables if they don't exist."""
    conn = get_connection()
    
    # Users table
    conn.execute("""
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS training_progress (
            id SERIAL PRIMARY KEY,
            user_email TEXT NOT NULL,
            username TEXT NOT NULL,
            week INTEGER DEFAULT 1,
            day INTEGER DEFAULT 1,
            exercise_ids TEXT,
            rpe_scores TEXT,
            session_date TEXT,
            completed BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    """)
    
    # Rest reflections table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rest_reflections (
            id SERIAL PRIMARY KEY,
            user_email TEXT NOT NULL,
            username TEXT NOT NULL,
            week INTEGER,
            day INTEGER,
            reflection TEXT,
            rest_type TEXT,
            created_at TEXT,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    """)
    
    conn.commit()
    st.success("✅ Database initialized successfully!")

# ---------- USER FUNCTIONS ----------
def user_exists(email):
    """Check if a user with the given email exists."""
    conn = get_connection()
    result = conn.query("SELECT email FROM users WHERE email = %s", (email,))
    conn.commit()
    return len(result) > 0

def register_user(email, username, result):
    """Register a new user with onboarding results."""
    if user_exists(email):
        return False, "Email already registered. Please use 'Update Profile' or login with a different email."
    
    conn = get_connection()
    conn.execute("""
        INSERT INTO users (email, username, assessment_date, total_score, level, sarc_score, calf_score, single_score, squat_score, raw_payload)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
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
    ))
    conn.commit()
    return True, "Registration successful! Your data has been saved."

def update_user(email, username, result):
    """Update an existing user's profile."""
    conn = get_connection()
    
    # Verify both email and username match
    verify = conn.query("SELECT email, username FROM users WHERE email = %s AND username = %s", (email, username))
    if len(verify) == 0:
        conn.commit()
        return False, "No matching user found. Please check your email and username."
    
    conn.execute("""
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
    """, (
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
    ))
    conn.commit()
    return True, "Profile updated successfully!"

def retrieve_user(email, username):
    """Retrieve a user's stored profile."""
    conn = get_connection()
    result = conn.query("""
        SELECT email, username, assessment_date, total_score, level, sarc_score, calf_score, single_score, squat_score, raw_payload
        FROM users
        WHERE email = %s AND username = %s
    """, (email, username))
    conn.commit()
    
    if len(result) == 0:
        return None
    
    row = result.iloc[0]
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
        'raw_payload': json.loads(row['raw_payload']) if row['raw_payload'] else {}
    }

# ---------- TRAINING PROGRESS FUNCTIONS ----------
def save_training_session(user_email, username, week, day, exercise_ids, rpe_scores, completed=False):
    """Save a training session record."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO training_progress (user_email, username, week, day, exercise_ids, rpe_scores, session_date, completed)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_email,
        username,
        week,
        day,
        json.dumps(exercise_ids),
        json.dumps(rpe_scores),
        datetime.now().isoformat(),
        completed
    ))
    conn.commit()

def get_user_progress(user_email, username):
    """Get all training progress for a user."""
    conn = get_connection()
    result = conn.query("""
        SELECT week, day, exercise_ids, rpe_scores, session_date, completed
        FROM training_progress
        WHERE user_email = %s AND username = %s
        ORDER BY session_date DESC
    """, (user_email, username))
    conn.commit()
    return result

def get_current_week_day(user_email, username):
    """Get the current week and day for a user."""
    conn = get_connection()
    result = conn.query("""
        SELECT week, day
        FROM training_progress
        WHERE user_email = %s AND username = %s
        ORDER BY session_date DESC
        LIMIT 1
    """, (user_email, username))
    conn.commit()
    
    if len(result) == 0:
        return 1, 1  # Default to Week 1, Day 1
    row = result.iloc[0]
    return row['week'], row['day']

# ---------- REST REFLECTION FUNCTIONS ----------
def save_rest_reflection(user_email, username, week, day, rest_type, reflection):
    """Save a rest day reflection."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO rest_reflections (user_email, username, week, day, rest_type, reflection, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        user_email,
        username,
        week,
        day,
        rest_type,
        reflection,
        datetime.now().isoformat()
    ))
    conn.commit()

def get_rest_reflections(user_email, username):
    """Get all rest reflections for a user."""
    conn = get_connection()
    result = conn.query("""
        SELECT week, day, rest_type, reflection, created_at
        FROM rest_reflections
        WHERE user_email = %s AND username = %s
        ORDER BY created_at DESC
    """, (user_email, username))
    conn.commit()
    return result
