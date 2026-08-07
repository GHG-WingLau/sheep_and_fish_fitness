import streamlit as st
import json
from onboarding_engine import process_onboarding  # Import the script above

st.set_page_config(page_title="Elderly Training Onboarding", layout="centered")

st.title("🧓 Online Training System - Onboarding")
st.markdown("*Your 10-minute safety & readiness assessment*")

with st.form("onboarding_form"):
    # Step 1: Account
    email = st.text_input("📧 Email Address (for saving your progress)")
    username = st.text_input("👤 Your Name (or nickname)")

    # Step 2: Age
    age_bucket = st.selectbox("📅 What is your age group?", 
                              ["60-64", "65-69", "70-74", "75-79", "80+"])

    # Step 3: Red Flags
    st.subheader("🚨 Safety Check")
    st.caption("Check ANY box that applies to you:")
    red_flags = []
    if st.checkbox("Chest pain or irregular heartbeat at rest"): red_flags.append("chest_pain")
    if st.checkbox("Hip/knee/spine replacement in the last 6 months"): red_flags.append("replacement")
    if st.checkbox("Uncontrolled high BP (>160/100) or severe osteoporosis"): red_flags.append("bp_osteo")
    if st.checkbox("Fallen more than twice in the last month"): red_flags.append("falls")

    # Step 4: SARC-F
    st.subheader("💪 SARC-F Questionnaire")
    col1, col2 = st.columns(2)
    with col1:
        sarc_strength = st.radio("1. Difficulty lifting 5kg?", [0, 1, 2], format_func=lambda x: ["None (0)", "Some (1)", "A lot/Unable (2)"][x], index=0, key="s1")
        sarc_walk = st.radio("2. Difficulty walking across a room?", [0, 1, 2], format_func=lambda x: ["None (0)", "Some (1)", "A lot/Unable (2)"][x], index=0, key="s2")
        sarc_rise = st.radio("3. Difficulty rising from a chair?", [0, 1, 2], format_func=lambda x: ["None (0)", "Some (1)", "A lot/Unable (2)"][x], index=0, key="s3")
    with col2:
        sarc_stairs = st.radio("4. Difficulty climbing 10 stairs?", [0, 1, 2], format_func=lambda x: ["None (0)", "Some (1)", "A lot/Unable (2)"][x], index=0, key="s4")
        sarc_falls = st.radio("5. How many falls in the last year?", [0, 1, 2], format_func=lambda x: ["0 (0)", "1-3 (1)", "4+ (2)"][x], index=0, key="s5")

    # Step 5: Calf
    st.subheader("📏 Calf Circumference")
    gender = st.radio("Gender", ["Male", "Female"])
    calf_cm = st.number_input("Left calf measurement (cm)", min_value=20.0, max_value=50.0, step=0.5)

    # Step 6: Single Leg
    st.subheader("🦩 Single-Leg Stance Test")
    st.caption("Stand beside a chair. Lift one foot. Enter the longest time (seconds) you held it.")
    single_sec = st.number_input("Longest hold (seconds)", min_value=0.0, max_value=120.0, step=0.5)

    # Step 7: Deep Squat
    st.subheader("🏋️ Deep Squat Test (Chair-Assisted)")
    squat_option = st.selectbox("Your lowest comfortable squat position:", 
                                ["Full Squat", "Partial Squat", "Chair Touch Only", "Unable or Painful"])
    
    # Map display to internal key
    squat_map = {
        "Full Squat": "full",
        "Partial Squat": "partial",
        "Chair Touch Only": "chair_touch",
        "Unable or Painful": "unable"
    }
    squat_key = squat_map[squat_option]

    # Submit
    submitted = st.form_submit_button("📊 Complete Assessment & Get My Level")

if submitted:
    # Build payload
    payload = {
        'email': email,
        'username': username if username else "Guest",
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
    
    # Process
    result = process_onboarding(payload)
    
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
        
        st.caption(f"Record saved for: {result['email']} | Username: {result['username']}")
