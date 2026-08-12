import streamlit as st
import json
from datetime import datetime
import random

# ---------- Import Custom Modules ----------
from db import (
    init_db,
    register_user,
    update_user,
    retrieve_user,
    user_exists,
    save_training_session,
    get_user_progress,
    get_current_week_day,
    save_rest_reflection
)
from onboarding_engine import process_onboarding, generate_summary_text
from exercise_engine import get_daily_exercises, EXERCISE_CATALOG

# ---------- Page Configuration ----------
st.set_page_config(
    page_title="Elderly Training System",
    page_icon="🧓",
    layout="centered"
)

# ---------- Initialize Database ----------
init_db()

# ---------- Session State Initialization ----------
if "language" not in st.session_state:
    st.session_state.language = "en"
if "user" not in st.session_state:
    st.session_state.user = {
        "email": "",
        "username": "",
        "level": 3,
        "week": 1,
        "day": 1,
        "last_rpe": 5,
        "has_osteoporosis": False
    }
if "training" not in st.session_state:
    st.session_state.training = {
        "exercises": [],
        "current_index": 0,
        "rep_count": 0,
        "is_paused": False,
        "is_complete": False,
        "rpe_scores": [],
        "coach_message": "",
        "exercise_started": False,
        "total_reps": 0
    }
if "page" not in st.session_state:
    st.session_state.page = "onboarding"

# ---------- Language Support ----------
LANGUAGES = {
    "en": "English",
    "zh_HK": "繁體中文 (廣東話)",
    "zh_TW": "繁體中文 (台灣)"
}

# Simplified translation loading (for demo, we could expand later)
def get_text(key, lang=None):
    """Placeholder for i18n - expand with JSON files later."""
    if lang is None:
        lang = st.session_state.language
    # For MVP, return a simple mapping or the key itself
    # In production, load from locales/{lang}/translations.json
    # We'll keep it simple for now.
    return key

# ---------- Helper Functions ----------
def navigate_to_training():
    st.session_state.page = "training"
    st.rerun()

def navigate_to_onboarding():
    st.session_state.page = "onboarding"
    st.rerun()

def load_workout():
    """Fetch or refresh the daily workout list based on user's current week/day."""
    if not st.session_state.training["exercises"]:
        exercises = get_daily_exercises(
            level=st.session_state.user["level"],
            week=st.session_state.user["week"],
            day=st.session_state.user["day"],
            last_rpe=st.session_state.user.get("last_rpe", 5),
            has_osteoporosis=st.session_state.user.get("has_osteoporosis", False)
        )
        st.session_state.training["exercises"] = exercises
        st.session_state.training["current_index"] = 0
        st.session_state.training["rep_count"] = 0
        st.session_state.training["is_complete"] = False
        st.session_state.training["rpe_scores"] = []
        st.session_state.training["coach_message"] = ""
        st.session_state.training["exercise_started"] = False
        # Compute total reps for progress
        total = 0
        for ex in exercises:
            total += ex.get('reps', 0)
        st.session_state.training["total_reps"] = total

def advance_exercise():
    if st.session_state.training["current_index"] < 2:
        st.session_state.training["current_index"] += 1
        st.session_state.training["rep_count"] = 0
        st.session_state.training["exercise_started"] = False
        st.session_state.training["coach_message"] = ""
    else:
        st.session_state.training["is_complete"] = True
        # Save session to database
        user = st.session_state.user
        ex_ids = [ex['id'] for ex in st.session_state.training["exercises"]]
        rpe_scores = st.session_state.training["rpe_scores"]
        save_training_session(
            user_email=user["email"],
            username=user["username"],
            week=user["week"],
            day=user["day"],
            exercise_ids=ex_ids,
            rpe_scores=rpe_scores,
            completed=True
        )

# ---------- RENDER FUNCTIONS ----------

def render_onboarding():
    st.title("🧓 Elderly Online Training System")
    st.divider()

    # Introduction
    st.markdown("""
    *"Welcome. Before we design your personal 30-minute exercise program, we need to understand your current body. 
    This 10-minute assessment is not a test—it is a safety check. It helps us find the right starting level so you never push too hard or too fast. 
    Answer honestly. If something feels painful or unsafe, stop immediately. Your safety is our #1 priority."*
    """)
    st.divider()

    # Language selector
    lang = st.selectbox(
        "🌐 Language / 語言",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        key="lang_selector"
    )
    st.session_state.language = lang

    # --- User Option Selector ---
    option = st.radio(
        "Please choose an action:",
        ["🆕 Register as New User", "✏️ Update Existing Profile", "📋 Retrieve Daily Program"]
    )
    st.caption("📌 Note: For registration, we will save your data. For updates/retrieval, we require **both** your registered email and username to match.")

    show_full_form = option != "📋 Retrieve Daily Program"

    with st.form("onboarding_form"):
        email = st.text_input("📧 Email Address")
        username = st.text_input("👤 Username (your chosen nickname)")

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
            payload = None

        submitted = st.form_submit_button("📊 Process Request")

    # ---------- HANDLE SUBMISSION ----------
    if submitted:
        if not email or not username:
            st.error("❌ Email and Username are required.")
        elif option == "📋 Retrieve Daily Program":
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
                
                st.divider()
                col_act1, col_act2, col_act3 = st.columns(3)
                with col_act1:
                    if st.button("🔄 Go Back"):
                        st.rerun()
                with col_act2:
                    # Download summary
                    result_data = {
                        'level': user_data['level'],
                        'total_score': user_data['total_score'],
                        'sarc_score': user_data['sarc_score'],
                        'calf_score': user_data['calf_score'],
                        'single_score': user_data['single_score'],
                        'squat_score': user_data['squat_score'],
                        'overview': user_data['raw_payload'].get('overview', 'Retrieved from stored profile.'),
                        'expectation': user_data['raw_payload'].get('expectation', 'Continue your training plan.')
                    }
                    summary_text = generate_summary_text(result_data, email, username)
                    st.download_button(
                        label="📥 Download Summary",
                        data=summary_text,
                        file_name=f"{username}_training_summary.txt",
                        mime="text/plain"
                    )
                with col_act3:
                    if st.button("🏋️ Proceed to Training"):
                        # Load user into session
                        st.session_state.user["email"] = email
                        st.session_state.user["username"] = username
                        st.session_state.user["level"] = int(user_data['level'].split()[-1])  # e.g., "Level 3" -> 3
                        st.session_state.user["week"], st.session_state.user["day"] = get_current_week_day(email, username)
                        st.session_state.user["has_osteoporosis"] = "osteoporosis" in user_data['raw_payload'].get('red_flags_checked', [])
                        navigate_to_training()
            else:
                st.error("❌ No profile found. Please check your email and username, or register as a new user.")
        
        elif option == "🆕 Register as New User":
            if payload is None:
                st.error("Something went wrong.")
            else:
                result = process_onboarding(payload)
                if result.get('level') == 'Level 0':
                    st.warning("⚠️ Medical Deferral")
                    st.info(result.get('overview', ''))
                else:
                    success, msg = register_user(email, username, result)
                    if success:
                        st.success(msg)
                        # Store user in session
                        st.session_state.user["email"] = email
                        st.session_state.user["username"] = username
                        st.session_state.user["level"] = int(result['level'].split()[-1])
                        st.session_state.user["week"] = 1
                        st.session_state.user["day"] = 1
                        st.session_state.user["has_osteoporosis"] = "osteoporosis" in result.get('red_flags_checked', [])
                        st.session_state.user["last_rpe"] = 5
                        # Display results
                        display_results(result, email, username)
                        # Show proceed button
                        if st.button("🏋️ Proceed to Daily Training"):
                            navigate_to_training()
                    else:
                        st.error(f"❌ {msg}")
        
        elif option == "✏️ Update Existing Profile":
            if payload is None:
                st.error("Something went wrong.")
            else:
                result = process_onboarding(payload)
                if result.get('level') == 'Level 0':
                    st.warning("⚠️ Medical Deferral")
                    st.info(result.get('overview', ''))
                else:
                    success, msg = update_user(email, username, result)
                    if success:
                        st.success(msg)
                        # Update session
                        st.session_state.user["email"] = email
                        st.session_state.user["username"] = username
                        st.session_state.user["level"] = int(result['level'].split()[-1])
                        st.session_state.user["week"] = 1
                        st.session_state.user["day"] = 1
                        st.session_state.user["has_osteoporosis"] = "osteoporosis" in result.get('red_flags_checked', [])
                        st.session_state.user["last_rpe"] = 5
                        display_results(result, email, username)
                        if st.button("🏋️ Proceed to Daily Training"):
                            navigate_to_training()
                    else:
                        st.error(f"❌ {msg}")

def display_results(result, email, username):
    st.divider()
    st.subheader("📋 Your Personalized Report")
    
    if result.get('level') == 'Level 0':
        st.error("⚠️ MEDICAL DEFERRAL")
        st.warning(result.get('overview', ''))
    else:
        st.success(f"✅ Recommended Starting Level: **{result.get('level', 'N/A')}**")
        st.metric("Total Score", result.get('total_score', 'N/A'), "Lower is better")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("SARC-F", result.get('sarc_score', 'N/A'))
        col_b.metric("Calf Score", result.get('calf_score', 'N/A'))
        col_c.metric("Balance Score", result.get('single_score', 'N/A'))
        col_d.metric("Squat Score", result.get('squat_score', 'N/A'))
        
        st.info(f"📝 {result.get('overview', '')}")
        st.success(f"🎯 {result.get('expectation', '')}")
        st.caption(f"Data stored for: {email} | Username: {username}")

# ---------- TRAINING PAGE ----------
def render_training():
    st.title("🧓 Daily Training")
    
    # Language selector
    lang = st.selectbox(
        "🌐 Language / 語言",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        key="lang_selector_training"
    )
    st.session_state.language = lang

    user = st.session_state.user
    training = st.session_state.training

    # Ensure exercises are loaded
    if not training["exercises"]:
        load_workout()
        st.rerun()

    # Header with week/day
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"📅 Week {user['week']} · Day {user['day']}")
    with col2:
        st.metric("Level", user['level'])

    # Timeline dots
    cols = st.columns(7)
    for i in range(1, 8):
        status = "●" if i <= user['day'] else "○"
        day_name = "R" if i > 5 else str(i)
        cols[i-1].markdown(f"<center><span style='font-size:20px;'>{status}</span><br><span style='font-size:10px;'>D{day_name}</span></center>", unsafe_allow_html=True)

    st.divider()

    # --- Check if session is complete ---
    if training["is_complete"]:
        st.balloons()
        st.success("🎉 Congratulations! You've completed today's training!")
        st.subheader("📊 Daily Achievement")
        avg_rpe = sum(training["rpe_scores"]) / len(training["rpe_scores"]) if training["rpe_scores"] else 0
        st.metric("Average Exertion", f"{avg_rpe:.1f}/10", "Lower is better for consistency")
        st.caption(f"Total sessions completed: {len(training['rpe_scores'])}/3")
        st.info("💡 You're building a strong habit. Tomorrow is another step forward!")
        
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("🏠 Return to Dashboard"):
                st.session_state.training = {}  # Reset
                navigate_to_onboarding()
        with col_act2:
            if st.button("📊 View Progress"):
                # Placeholder for progress view
                st.info("Progress view coming soon.")
        return

    # --- Current Exercise ---
    ex = training["exercises"][training["current_index"]]
    
    # Display the exercise card with placeholder image
    # In production, use the actual image path: f"assets/{ex['image_path']}"
    st.image(f"https://via.placeholder.com/400x200/4CAF50/FFFFFF?text={ex['id']}+{ex['name'].replace(' ','+')}", use_container_width=True)
    
    st.subheader(f"Exercise {training['current_index']+1} of 3: {ex['name']}")
    st.caption(f"🎯 Target: {ex['target']} | Reps: {ex['reps']} | Holds: {ex['hold']}s")
    st.caption(f"📝 {ex['desc']}")
    st.caption(f"🔑 {ex['key_cue']}")

    # --- Coach Narration Area ---
    coach_msg = training["coach_message"]
    if coach_msg:
        st.info(f"👨‍🏫 Coach: {coach_msg}")
    else:
        st.info(f"👨‍🏫 Coach: Ready to start? Press 'Start'.")

    # --- Timer & Controls ---
    col_controls1, col_controls2, col_controls3 = st.columns([1, 1, 1])
    
    with col_controls1:
        if not training["exercise_started"]:
            if st.button("▶️ Start", use_container_width=True):
                training["exercise_started"] = True
                training["is_paused"] = False
                # Generate initial coach message
                training["coach_message"] = f"🏋️ {ex['name']}. {ex['breath_cue']} Let's begin!"
                st.rerun()
        elif training["is_paused"]:
            if st.button("▶️ Resume", use_container_width=True):
                training["is_paused"] = False
                training["coach_message"] = "▶️ Resuming. Let's go!"
                st.rerun()
        else:
            if st.button("⏸ Pause", use_container_width=True):
                training["is_paused"] = True
                training["coach_message"] = "⏸ Paused. Take a breath. Resume when ready."
                st.rerun()
    
    with col_controls2:
        # Simulate rep completion (for demo)
        if training["exercise_started"] and not training["is_paused"]:
            if training["rep_count"] < ex['reps']:
                if st.button("➕ +1 Rep (Demo)", use_container_width=True):
                    training["rep_count"] += 1
                    # Update coach message
                    remaining = ex['reps'] - training["rep_count"]
                    if remaining == 0:
                        training["coach_message"] = "✅ Exercise complete! Rate it below."
                    else:
                        training["coach_message"] = f"Great! {remaining} reps remaining. {ex['breath_cue']}"
                    st.rerun()
            else:
                # All reps done, show Done button
                if st.button("✅ Done", use_container_width=True):
                    # Mark exercise as complete, but we still need RPE
                    st.session_state["show_rpe"] = True
                    st.rerun()
        else:
            st.button("⏳ Waiting...", disabled=True, use_container_width=True)
    
    with col_controls3:
        # Next exercise button (only after RPE is submitted and reps done)
        if training["rep_count"] >= ex['reps'] and training["exercise_started"]:
            if len(training["rpe_scores"]) > training["current_index"]:
                if st.button("⏭ Next Exercise", use_container_width=True):
                    advance_exercise()
                    st.rerun()
            else:
                st.button("📊 Rate First", disabled=True, use_container_width=True)
        else:
            st.button("🔒 Locked", disabled=True, use_container_width=True)

    # --- RPE Rating Prompt ---
    if training["rep_count"] >= ex['reps'] and training["exercise_started"]:
        if len(training["rpe_scores"]) <= training["current_index"]:
            st.divider()
            st.subheader("📊 Rate This Exercise")
            st.caption("How hard was this exercise?")
            rpe_val = st.slider("", 1, 10, 5, key=f"rpe_{training['current_index']}")
            st.markdown(f"<center>{['😊','🙂','😐','😅','😰'][(rpe_val-1)//2] if rpe_val <= 10 else '😊'}</center>", unsafe_allow_html=True)
            if st.button("✅ Submit Rating", key="submit_rpe"):
                if len(training["rpe_scores"]) > training["current_index"]:
                    training["rpe_scores"][training["current_index"]] = rpe_val
                else:
                    training["rpe_scores"].append(rpe_val)
                st.session_state.user["last_rpe"] = rpe_val
                st.success(f"Rating saved! ({rpe_val}/10)")
                st.rerun()

    # --- Progress bar ---
    st.progress(training["rep_count"] / max(ex['reps'], 1))
    st.caption(f"Progress: {training['rep_count']} / {ex['reps']} reps")

    # --- Rest day suggestion (if day > 5) ---
    if user['day'] > 5:
        st.divider()
        st.subheader("🌿 Rest Day Activity")
        st.info("""
        Today is a rest day. Choose one:
        - 🚶 Walk outdoors for 30 mins
        - 📖 Read a chapter of the Bible
        - ✍️ Write a gratitude journal entry
        - 🎵 Listen to soft music
        - 🧘 Focus on 10 minutes of diaphragmatic breathing
        """)
        with st.form("rest_form"):
            rest_type = st.selectbox("Select your activity:", ["Walk", "Read", "Journal", "Music", "Breathing"])
            reflection = st.text_area("📝 Reflect on your rest today (optional):")
            if st.form_submit_button("💾 Save Reflection"):
                save_rest_reflection(
                    user_email=user["email"],
                    username=user["username"],
                    week=user["week"],
                    day=user["day"],
                    rest_type=rest_type,
                    reflection=reflection
                )
                st.success("Rest logged! Rest builds strength.")

# ---------- MAIN ROUTER ----------
def main():
    if st.session_state.page == "onboarding":
        render_onboarding()
    elif st.session_state.page == "training":
        render_training()
    else:
        # fallback
        st.session_state.page = "onboarding"
        st.rerun()

if __name__ == "__main__":
    main()
