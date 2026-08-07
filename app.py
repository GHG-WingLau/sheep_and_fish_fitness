import streamlit as st
import json
import sqlite3
import pandas as pd
from datetime import datetime
from onboarding_engine import process_onboarding, generate_summary_text

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Elderly Training System", layout="centered")

# ---------- DATABASE FUNCTIONS ----------
def init_db():
    conn = sqlite3.connect('onboarding.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    ''')
    conn.commit()
    conn.close()

def user_exists(email):
    conn = sqlite3.connect('onboarding.db')
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE email = ?", (email,))
    result = c.fetchone()
    conn.close()
    return result is not None

def register_user(email, username, result):
    if user_exists(email):
        return False, "Email already registered. Please use 'Update Profile' or login with a different email."
    conn = sqlite3.connect('onboarding.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (email, username, assessment_date, total_score, level, sarc_score, calf_score, single_score, squat_score, raw_payload)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        email,
        username,
        datetime.now().isoformat(),
        result['total_score'],
        result['level'],
        result['sarc_score'],
        result['calf_score'],
        result['single_score'],
        result['squat_score'],
        json.dumps(result)  # store full result for future reference
    ))
    conn.commit()
    conn.close()
    return True, "Registration successful! Your data has been saved."

def update_user(email, username, result):
    conn = sqlite3.connect('onboarding.db')
    c = conn.cursor()
    # Strict match: BOTH email and username must match the existing record
    c.execute("SELECT email, username FROM users WHERE email = ? AND username = ?", (email, username))
    match = c.fetchone()
    if not match:
        conn.close()
        return False, "No matching user found. Please check your email and username."
    
    c.execute('''
        UPDATE users SET
            assessment_date = ?,
            total_score = ?,
            level = ?,
            sarc_score = ?,
            calf_score = ?,
            single_score = ?,
            squat_score = ?,
            raw_payload = ?
        WHERE email = ? AND username = ?
    ''', (
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
    conn.close()
    return True, "Profile updated successfully!"

def retrieve_user(email, username):
    conn = sqlite3.connect('onboarding.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ? AND username = ?", (email, username))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    # row structure: (id, email, username, assessment_date, total_score, level, sarc_score, calf_score, single_score, squat_score, raw_payload)
    return {
        'email': row[1],
        'username': row[2],
        'assessment_date': row[3],
        'total_score': row[4],
        'level': row[5],
        'sarc_score': row[6],
        'calf_score': row[7],
        'single_score': row[8],
        'squat_score': row[9],
        'raw_payload': json.loads(row[10]) if row[10] else {}
    }

# ---------- UI ----------
st.title("🧓 Elderly Online Training System")
st.divider()

# Introduction
st.markdown("""
*"Welcome. Before we design your personal 30-minute exercise program, we need to understand your current body. 
This 10-minute assessment is not a test—it is a safety check. It helps us find the right starting level so you never push too hard or too fast. 
Answer honestly. If something feels painful or unsafe, stop immediately. Your safety is our #1 priority."*
""")
st.divider()

# --- User Option Selector ---
option = st.radio(
    "Please choose an action:",
    ["🆕 Register as New User", "✏️ Update Existing Profile", "📋 Retrieve Daily Program"]
)
st.caption("📌 Note: For registration, we will save your data. For updates/retrieval, we require **both** your registered email and username to match.")

# --- Dynamic Form Based on Option ---
show_full_form = option != "📋 Retrieve Daily Program"

# Email & Username are ALWAYS shown
with st.form("onboarding_form"):
    email = st.text_input("📧 Email Address")
    username = st.text_input("👤 Username (your chosen nickname)")

    # Conditionally show the full assessment form
    if show_full_form:
        st.divider()
        st.subheader("📊 Assessment Section")
        
        # Age
        age_bucket = st.selectbox("📅 Age Group", ["60-64", "65-69", "70-74", "75-79", "80+"])
        
        # Red Flags
        st.subheader("🚨 Safety Check")
        red_flags = []
        if st.checkbox("Chest pain or irregular heartbeat at rest"): red_flags.append("chest_pain")
        if st.checkbox("Hip/knee/spine replacement in the last 6 months"): red_flags.append("replacement")
        if st.checkbox("Uncontrolled high BP (>160/100) or severe osteoporosis"): red_flags.append("bp_osteo")
        if st.checkbox("Fallen more than twice in the last month"): red_flags.append("falls")
        
        # SARC-F
        st.subheader("💪 SARC-F Questionnaire")
        col1, col2 = st.columns(2)
        with col1:
            sarc_strength = st.radio("1. Difficulty lifting 5kg?", [0, 1, 2], format_func=lambda x: ["None (0)", "Some (1)", "A lot/Unable (2)"][x], index=0, key="s1")
            sarc_walk = st.radio("2. Difficulty walking across a room?", [0, 1, 2], format_func=lambda x: ["None (0)", "Some (1)", "A lot/Unable (2)"][x], index=0, key="s2")
            sarc_rise = st.radio("3. Difficulty rising from a chair?", [0, 1, 2], format_func=lambda x: ["None (0)", "Some (1)", "A lot/Unable (2)"][x], index=0, key="s3")
        with col2:
            sarc_stairs = st.radio("4. Difficulty climbing 10 stairs?", [0, 1, 2], format_func=lambda x: ["None (0)", "Some (1)", "A lot/Unable (2)"][x], index=0, key="s4")
            sarc_falls = st.radio("5. How many falls in the last year?", [0, 1, 2], format_func=lambda x: ["0 (0)", "1-3 (1)", "4+ (2)"][x], index=0, key="s5")
        
        # Calf
        st.subheader("📏 Calf Circumference")
        gender = st.radio("Gender", ["Male", "Female"])
        calf_cm = st.number_input("Left calf measurement (cm)", min_value=20.0, max_value=50.0, step=0.5)
        
        # Single Leg
        st.subheader("🦩 Single-Leg Stance Test")
        st.caption("Stand beside a chair. Lift one foot. Enter the longest time (seconds) you held it.")
        single_sec = st.number_input("Longest hold (seconds)", min_value=0.0, max_value=120.0, step=0.5)
        
        # Deep Squat
        st.subheader("🏋️ Deep Squat Test (Chair-Assisted)")
        squat_option = st.selectbox("Your lowest comfortable squat position:", 
                                    ["Full Squat", "Partial Squat", "Chair Touch Only", "Unable or Painful"])
        squat_map = {
            "Full Squat": "full",
            "Partial Squat": "partial",
            "Chair Touch Only": "chair_touch",
            "Unable or Painful": "unable"
        }
        squat_key = squat_map[squat_option]
        
        payload = {
            'age_bucket': age_bucket,
            'red_flags': red_flags,
            'sarc_f': {
                'strength': sarc_strength,
                'walking': sarc_walk,
                'rise': sarc_rise,
                'stairs': sarc_stairs,
                'falls': sarc_falls
            },
            'gender': gender.lower(),
            'calf_cm': calf_cm,
            'single_leg_seconds': single_sec,
            'deep_squat': squat_key
        }
    else:
        # For "Retrieve" – we don't need the assessment fields
        payload = None

    # --- Submit Button ---
    submitted = st.form_submit_button("📊 Process Request")

# ---------- HANDLE SUBMISSION ----------
if submitted:
    if not email or not username:
        st.error("❌ Email and Username are required.")
    elif option == "📋 Retrieve Daily Program":
        # Just retrieve
        user_data = retrieve_user(email, username)
        if user_data:
            st.success(f"✅ Welcome back, {user_data['username']}!")
            st.divider()
            st.subheader("📋 Your Stored Profile")
            st.metric("Recommended Level", user_data['level'])
            st.metric("Total Score", user_data['total_score'])
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("SARC-F", user_data['sarc_score'])
            col_b.metric("Calf", user_data['calf_score'])
            col_c.metric("Balance", user_data['single_score'])
            col_d.metric("Squat", user_data['squat_score'])
            st.caption(f"Last assessed: {user_data['assessment_date']}")
            
            # Action buttons for this specific result
            st.divider()
            col_act1, col_act2, col_act3 = st.columns(3)
            with col_act1:
                if st.button("🔄 Go Back"):
                    st.experimental_rerun()
            with col_act2:
                # Generate downloadable summary
                summary_text = generate_summary_text(user_data)
                st.download_button(
                    label="📥 Download Summary",
                    data=summary_text,
                    file_name=f"{user_data['username']}_training_summary.txt",
                    mime="text/plain"
                )
            with col_act3:
                if st.button("🏋️ Proceed to Training"):
                    st.success("🚀 Redirecting to your daily training program... (Placeholder for exercise delivery system)")
        else:
            st.error("❌ No profile found. Please check your email and username, or register as a new user.")
    
    elif option == "🆕 Register as New User":
        # Process and register
        if payload is None:
            st.error("Something went wrong.")
        else:
            result = process_onboarding(payload)
            if result['level'] == 'Level 0':
                st.warning("⚠️ Medical Deferral")
                st.info(result['overview'])
            else:
                success, msg = register_user(email, username, result)
                if success:
                    st.success(msg)
                    display_results(result, email, username)
                else:
                    st.error(f"❌ {msg}")
    
    elif option == "✏️ Update Existing Profile":
        if payload is None:
            st.error("Something went wrong.")
        else:
            result = process_onboarding(payload)
            if result['level'] == 'Level 0':
                st.warning("⚠️ Medical Deferral")
                st.info(result['overview'])
            else:
                success, msg = update_user(email, username, result)
                if success:
                    st.success(msg)
                    display_results(result, email, username)
                else:
                    st.error(f"❌ {msg}")

# ---------- HELPER FUNCTION TO DISPLAY RESULTS ----------
def display_results(result, email, username):
    st.divider()
    st.subheader("📋 Your Personalized Report")
    
    if result['level'] == 'Level 0':
        st.error("⚠️ MEDICAL DEFERRAL")
        st.warning(result['overview'])
    else:
        st.success(f"✅ Recommended Starting Level: **{result['level']}**")
        st.metric("Total Score", result['total_score'], "Lower is better")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("SARC-F", result['sarc_score'])
        col_b.metric("Calf Score", result['calf_score'])
        col_c.metric("Balance Score", result['single_score'])
        col_d.metric("Squat Score", result['squat_score'])
        
        st.info(f"📝 {result['overview']}")
        st.success(f"🎯 {result['expectation']}")
        st.caption(f"Data stored for: {email} | Username: {username}")

        # --- Action Buttons ---
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        # 1. Go Back (refresh to reset)
        with col1:
            if st.button("🔄 Go Back to Start"):
                st.experimental_rerun()
        
        # 2. Download Summary
        with col2:
            # Build summary text
            summary_text = generate_summary_text(result)
            st.download_button(
                label="📥 Download Summary",
                data=summary_text,
                file_name=f"{username}_training_summary.txt",
                mime="text/plain"
            )
        
        # 3. Proceed to Training
        with col3:
            if st.button("🏋️ Proceed to Daily Training"):
                st.success("🚀 Redirecting to your daily training program... (Placeholder for future exercise delivery system)")

# ---------- INIT DB ----------
init_db()
