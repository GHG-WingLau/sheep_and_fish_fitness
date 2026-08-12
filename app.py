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
from exercise_engine import get_daily_exercises
from i18n import get_text, LANGUAGES

# ---------- Page Configuration ----------
st.set_page_config(
    page_title=get_text("common.app_title"),
    page_icon="🧓",
    layout="centered"
)

# ---------- Initialize Database ----------
try:
    init_db()
except Exception as e:
    st.error(f"⚠️ Database connection error: {str(e)}")
    st.info("Please check your Neon connection string in secrets.")
    st.stop()

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

# ---------- LANGUAGE SELECTOR ----------
def render_language_selector():
    col1, col2, col3 = st.columns([4, 2, 1])
    with col1:
        st.markdown("🧓 **Elderly Training System**")
    with col2:
        current_lang = st.session_state.get("language", "en")
        lang = st.selectbox(
            "🌐 Language",
            options=list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES[x],
            key="lang_selector_top",
            label_visibility="collapsed"
        )
        if lang != current_lang:
            st.session_state.language = lang
            st.rerun()
    with col3:
        if st.button("🏠", help="Home"):
            st.session_state.page = "onboarding"
            st.rerun()
    st.divider()

# ---------- Helper Functions ----------
def navigate_to_training():
    st.session_state.page = "training"
    st.rerun()

def navigate_to_onboarding():
    st.session_state.page = "onboarding"
    st.rerun()

def load_workout():
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
        total = sum(ex.get('reps', 0) for ex in exercises)
        st.session_state.training["total_reps"] = total

def advance_exercise():
    if st.session_state.training["current_index"] < 2:
        st.session_state.training["current_index"] += 1
        st.session_state.training["rep_count"] = 0
        st.session_state.training["exercise_started"] = False
        st.session_state.training["coach_message"] = ""
    else:
        st.session_state.training["is_complete"] = True
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

# ---------- RENDER ONBOARDING ----------
def render_onboarding():
    render_language_selector()
    st.markdown(get_text("common.welcome"))
    st.divider()

    option = st.radio(
        label=get_text("onboarding.choose_action"),
        options=["🆕 Register as New User", "✏️ Update Existing Profile", "📋 Retrieve Daily Program"],
        format_func=lambda x: {
            "🆕 Register as New User": get_text("onboarding.register"),
            "✏️ Update Existing Profile": get_text("onboarding.update"),
            "📋 Retrieve Daily Program": get_text("onboarding.retrieve")
        }.get(x, x)
    )
    st.caption(get_text("onboarding.note"))

    show_full_form = option != "📋 Retrieve Daily Program"

    with st.form("onboarding_form"):
        email = st.text_input(get_text("common.email"))
        username = st.text_input(get_text("common.username"))

        if show_full_form:
            st.divider()
            st.subheader(get_text("onboarding.assessment_section"))
            age_bucket = st.selectbox(
                get_text("onboarding.age_group"),
                ["60-64", "65-69", "70-74", "75-79", "80+"]
            )
            st.subheader(get_text("onboarding.safety_check"))
            red_flags = []
            if st.checkbox(get_text("onboarding.safety_flags.chest_pain")): red_flags.append("chest_pain")
            if st.checkbox(get_text("onboarding.safety_flags.replacement")): red_flags.append("replacement")
            if st.checkbox(get_text("onboarding.safety_flags.bp_osteo")): red_flags.append("bp_osteo")
            if st.checkbox(get_text("onboarding.safety_flags.falls")): red_flags.append("falls")
            
            st.subheader(get_text("onboarding.sarcf"))
            col1, col2 = st.columns(2)
            with col1:
                sarc_strength = st.radio(get_text("onboarding.sarcf_questions.strength"), [0, 1, 2],
                    format_func=lambda x: [get_text("onboarding.sarcf_options.none"), get_text("onboarding.sarcf_options.some"), get_text("onboarding.sarcf_options.lot")][x], index=0, key="s1")
                sarc_walk = st.radio(get_text("onboarding.sarcf_questions.walk"), [0, 1, 2],
                    format_func=lambda x: [get_text("onboarding.sarcf_options.none"), get_text("onboarding.sarcf_options.some"), get_text("onboarding.sarcf_options.lot")][x], index=0, key="s2")
                sarc_rise = st.radio(get_text("onboarding.sarcf_questions.rise"), [0, 1, 2],
                    format_func=lambda x: [get_text("onboarding.sarcf_options.none"), get_text("onboarding.sarcf_options.some"), get_text("onboarding.sarcf_options.lot")][x], index=0, key="s3")
            with col2:
                sarc_stairs = st.radio(get_text("onboarding.sarcf_questions.stairs"), [0, 1, 2],
                    format_func=lambda x: [get_text("onboarding.sarcf_options.none"), get_text("onboarding.sarcf_options.some"), get_text("onboarding.sarcf_options.lot")][x], index=0, key="s4")
                sarc_falls = st.radio(get_text("onboarding.sarcf_questions.falls"), [0, 1, 2],
                    format_func=lambda x: [get_text("onboarding.sarcf_options.none"), get_text("onboarding.sarcf_options.some"), get_text("onboarding.sarcf_options.four")][x], index=0, key="s5")
            
            st.subheader(get_text("onboarding.calf_circumference"))
            gender = st.radio(get_text("onboarding.gender"), ["Male", "Female"])
            calf_cm = st.number_input(get_text("onboarding.calf_input"), min_value=20.0, max_value=50.0, step=0.5)
            
            st.subheader(get_text("onboarding.single_leg_test"))
            st.caption(get_text("onboarding.single_leg_help"))
            single_sec = st.number_input(get_text("onboarding.single_leg_input"), min_value=0.0, max_value=120.0, step=0.5)
            
            st.subheader(get_text("onboarding.chair_stand_test"))
            st.caption(get_text("onboarding.chair_stand_help"))
            st.info(get_text("onboarding.chair_stand_demo"))
            chair_stands = st.number_input(get_text("onboarding.chair_stand_input"), min_value=0, max_value=30, step=1, value=0)
            
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
                'chair_stands': chair_stands
            }
        else:
            payload = None

        submitted = st.form_submit_button(get_text("onboarding.process_button"))

    if submitted:
        if not email or not username:
            st.error(get_text("onboarding.email_required"))
        elif option == "📋 Retrieve Daily Program":
            user_data = retrieve_user(email, username)
            if user_data:
                st.success(get_text("onboarding.welcome_back", username=user_data['username']))
                st.divider()
                st.subheader(get_text("onboarding.stored_profile"))
                st.metric(get_text("onboarding.recommended_level"), user_data['level'])
                st.metric(get_text("onboarding.total_score"), user_data['total_score'], get_text("onboarding.score_metric"))
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("SARC-F", user_data['sarc_score'])
                col_b.metric("Calf", user_data['calf_score'])
                col_c.metric("Balance", user_data['single_score'])
                col_d.metric("Chair Stands", user_data.get('chair_stands', 'N/A'))
                st.caption(get_text("onboarding.last_assessed", date=user_data['assessment_date']))
                
                st.divider()
                col_act1, col_act2, col_act3 = st.columns(3)
                with col_act1:
                    if st.button(get_text("common.go_back")):
                        st.rerun()
                with col_act2:
                    result_data = {
                        'level': user_data['level'],
                        'total_score': user_data['total_score'],
                        'sarc_score': user_data['sarc_score'],
                        'calf_score': user_data['calf_score'],
                        'single_score': user_data['single_score'],
                        'chair_stands': user_data.get('chair_stands', 0),
                        'overview': user_data['raw_payload'].get('overview', 'Retrieved from stored profile.'),
                        'expectation': user_data['raw_payload'].get('expectation', 'Continue your training plan.')
                    }
                    summary_text = generate_summary_text(result_data, email, username)
                    st.download_button(
                        label=get_text("common.download_summary"),
                        data=summary_text,
                        file_name=f"{username}_training_summary.txt",
                        mime="text/plain"
                    )
                with col_act3:
                    if st.button(get_text("common.proceed_to_training")):
                        st.session_state.user["email"] = email
                        st.session_state.user["username"] = username
                        st.session_state.user["level"] = int(user_data['level'].split()[-1])
                        st.session_state.user["week"], st.session_state.user["day"] = get_current_week_day(email, username)
                        st.session_state.user["has_osteoporosis"] = "osteoporosis" in user_data['raw_payload'].get('red_flags_checked', [])
                        navigate_to_training()
            else:
                st.error(get_text("onboarding.no_profile"))
        
        elif option == "🆕 Register as New User":
            if payload is None:
                st.error(get_text("onboarding.general_error"))
            else:
                result = process_onboarding(payload)
                if result.get('level') == 'Level 0':
                    st.warning(get_text("onboarding.medical_deferral"))
                    st.info(result.get('overview', ''))
                else:
                    success, msg = register_user(email, username, result)
                    if success:
                        st.success(get_text("onboarding.registration_success"))
                        # Store user data
                        st.session_state.user["email"] = email
                        st.session_state.user["username"] = username
                        st.session_state.user["level"] = int(result['level'].split()[-1])
                        st.session_state.user["week"] = 1
                        st.session_state.user["day"] = 1
                        st.session_state.user["has_osteoporosis"] = "osteoporosis" in result.get('red_flags_checked', [])
                        st.session_state.user["last_rpe"] = 5
                        # Directly navigate to training
                        st.session_state.page = "training"
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
        
        elif option == "✏️ Update Existing Profile":
            if payload is None:
                st.error(get_text("onboarding.general_error"))
            else:
                result = process_onboarding(payload)
                if result.get('level') == 'Level 0':
                    st.warning(get_text("onboarding.medical_deferral"))
                    st.info(result.get('overview', ''))
                else:
                    success, msg = update_user(email, username, result)
                    if success:
                        st.success(get_text("onboarding.update_success"))
                        st.session_state.user["email"] = email
                        st.session_state.user["username"] = username
                        st.session_state.user["level"] = int(result['level'].split()[-1])
                        st.session_state.user["week"] = 1
                        st.session_state.user["day"] = 1
                        st.session_state.user["has_osteoporosis"] = "osteoporosis" in result.get('red_flags_checked', [])
                        st.session_state.user["last_rpe"] = 5
                        st.session_state.page = "training"
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

# ---------- RENDER TRAINING ----------
def render_training():
    render_language_selector()
    
    # Ensure user data is loaded
    if not st.session_state.user["email"]:
        st.warning("No user data found. Returning to onboarding.")
        st.session_state.page = "onboarding"
        st.rerun()
        return

    user = st.session_state.user
    training = st.session_state.training

    if not training["exercises"]:
        load_workout()
        st.rerun()
        return

    # Header, timeline, exercise display, controls, etc.
    # (Same as before – unchanged for brevity)
    # ... (all existing render_training logic remains exactly as you have it)

# ---------- MAIN ROUTER ----------
def main():
    if st.session_state.page == "onboarding":
        render_onboarding()
    elif st.session_state.page == "training":
        render_training()
    else:
        st.session_state.page = "onboarding"
        st.rerun()

if __name__ == "__main__":
    main()
