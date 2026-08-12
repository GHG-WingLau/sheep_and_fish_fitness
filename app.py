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
    page_title="🧓 Elderly Training System",
    page_icon="🧓",
    layout="centered"
)

# ---------- Initialize Database ----------
try:
    init_db()
except Exception as e:
    # Don't crash on DB init error - show message and continue
    st.warning(f"⚠️ Database connection initializing: {str(e)}")

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

# ---------- Page Routing using Query Params ----------
def navigate_to(page):
    """Navigate to a page using query parameters."""
    st.query_params["page"] = page
    st.rerun()

def get_current_page():
    """Get the current page from query params, default to onboarding."""
    return st.query_params.get("page", "onboarding")

# ---------- Language Selector ----------
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
            navigate_to("onboarding")
    st.divider()

# ---------- Helper Functions ----------
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
        try:
            save_training_session(
                user_email=user["email"],
                username=user["username"],
                week=user["week"],
                day=user["day"],
                exercise_ids=ex_ids,
                rpe_scores=rpe_scores,
                completed=True
            )
        except Exception as e:
            st.warning(f"Could not save session: {e}")

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
            try:
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
                            navigate_to("training")
                else:
                    st.error(get_text("onboarding.no_profile"))
            except Exception as e:
                st.error(f"Database error: {str(e)}. Please try again.")
        
        elif option == "🆕 Register as New User":
            if payload is None:
                st.error(get_text("onboarding.general_error"))
            else:
                try:
                    result = process_onboarding(payload)
                    if result.get('level') == 'Level 0':
                        st.warning(get_text("onboarding.medical_deferral"))
                        st.info(result.get('overview', ''))
                    else:
                        success, msg = register_user(email, username, result)
                        if success:
                            st.success(get_text("onboarding.registration_success"))
                            # Store user data in session
                            st.session_state.user["email"] = email
                            st.session_state.user["username"] = username
                            st.session_state.user["level"] = int(result['level'].split()[-1])
                            st.session_state.user["week"] = 1
                            st.session_state.user["day"] = 1
                            st.session_state.user["has_osteoporosis"] = "osteoporosis" in result.get('red_flags_checked', [])
                            st.session_state.user["last_rpe"] = 5
                            # Navigate to training
                            navigate_to("training")
                        else:
                            st.error(f"❌ {msg}")
                except Exception as e:
                    st.error(f"Registration error: {str(e)}. Please try again.")
        
        elif option == "✏️ Update Existing Profile":
            if payload is None:
                st.error(get_text("onboarding.general_error"))
            else:
                try:
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
                            navigate_to("training")
                        else:
                            st.error(f"❌ {msg}")
                except Exception as e:
                    st.error(f"Update error: {str(e)}. Please try again.")

# ---------- RENDER TRAINING ----------
def render_training():
    render_language_selector()
    
    # Ensure user data is loaded
    if not st.session_state.user["email"]:
        st.warning("No user data found. Returning to onboarding.")
        navigate_to("onboarding")
        return

    user = st.session_state.user
    training = st.session_state.training

    if not training["exercises"]:
        load_workout()
        st.rerun()
        return

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(get_text("training.week_day", week=user['week'], day=user['day']))
    with col2:
        st.metric(get_text("training.level"), user['level'])

    # Timeline dots
    cols = st.columns(7)
    for i in range(1, 8):
        status = "●" if i <= user['day'] else "○"
        day_name = "R" if i > 5 else str(i)
        cols[i-1].markdown(f"<center><span style='font-size:20px;'>{status}</span><br><span style='font-size:10px;'>D{day_name}</span></center>", unsafe_allow_html=True)

    st.divider()

    # Check if session complete
    if training["is_complete"]:
        st.balloons()
        st.success(get_text("training.complete_title"))
        st.subheader(get_text("training.daily_achievement"))
        avg_rpe = sum(training["rpe_scores"]) / len(training["rpe_scores"]) if training["rpe_scores"] else 0
        st.metric(get_text("training.avg_exertion"), f"{avg_rpe:.1f}/10", get_text("training.avg_help"))
        st.caption(get_text("training.sessions_completed", count=len(training['rpe_scores'])))
        st.info(get_text("training.habit_message"))
        
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button(get_text("common.return_to_dashboard")):
                st.session_state.training = {}
                navigate_to("onboarding")
        with col_act2:
            if st.button("📊 View Progress"):
                st.info("Progress view coming soon.")
        return

    # Current Exercise
    ex = training["exercises"][training["current_index"]]
    
    # Get translated exercise fields
    ex_id = ex['id']
    if ex_id.startswith("L0_"):
        name_key = f"level0_exercises.{ex_id}.name"
        desc_key = f"level0_exercises.{ex_id}.desc"
        breath_key = f"level0_exercises.{ex_id}.breath_cue"
        cue_key = f"level0_exercises.{ex_id}.key_cue"
    else:
        name_key = f"exercises.{ex_id}.name"
        desc_key = f"exercises.{ex_id}.desc"
        breath_key = f"exercises.{ex_id}.breath_cue"
        cue_key = f"exercises.{ex_id}.key_cue"
    
    ex_name = get_text(name_key, default=ex['name'])
    ex_desc = get_text(desc_key, default=ex['desc'])
    ex_breath = get_text(breath_key, default=ex['breath_cue'])
    ex_cue = get_text(cue_key, default=ex['key_cue'])

    # Display exercise card
    st.image(f"https://via.placeholder.com/400x200/4CAF50/FFFFFF?text={ex['id']}+{ex['name'].replace(' ','+')}", use_container_width=True)
    
    st.subheader(get_text("training.exercise_of", current=training['current_index']+1, name=ex_name))
    st.caption(get_text("training.target", target=ex['target']))
    st.caption(get_text("training.reps_holds", reps=ex['reps'], hold=ex['hold']))
    st.caption(get_text("training.description", desc=ex_desc))
    st.caption(get_text("training.key_cue", key_cue=ex_cue))

    # Coach message
    coach_msg = training["coach_message"]
    if coach_msg:
        st.info(get_text("training.coach_start", message=coach_msg))
    else:
        st.info(get_text("training.coach_ready"))

    # Controls
    col_controls1, col_controls2, col_controls3 = st.columns([1, 1, 1])
    
    with col_controls1:
        if not training["exercise_started"]:
            if st.button(get_text("training.start_button"), use_container_width=True):
                training["exercise_started"] = True
                training["is_paused"] = False
                training["coach_message"] = get_text("coach.lets_begin", exercise=ex_name)
                st.rerun()
        elif training["is_paused"]:
            if st.button(get_text("training.resume_button"), use_container_width=True):
                training["is_paused"] = False
                training["coach_message"] = "▶️ Resuming. Let's go!"
                st.rerun()
        else:
            if st.button(get_text("training.pause_button"), use_container_width=True):
                training["is_paused"] = True
                training["coach_message"] = "⏸ Paused. Take a breath. Resume when ready."
                st.rerun()
    
    with col_controls2:
        if training["exercise_started"] and not training["is_paused"]:
            if training["rep_count"] < ex['reps']:
                if st.button(get_text("training.rep_button"), use_container_width=True):
                    training["rep_count"] += 1
                    remaining = ex['reps'] - training["rep_count"]
                    if remaining == 0:
                        training["coach_message"] = "✅ Exercise complete! Rate it below."
                    else:
                        training["coach_message"] = get_text("coach.rep_count", current=training['rep_count'], total=ex['reps'])
                    st.rerun()
            else:
                if st.button(get_text("training.done_button"), use_container_width=True):
                    st.session_state["show_rpe"] = True
                    st.rerun()
        else:
            st.button(get_text("training.locked_button"), disabled=True, use_container_width=True)
    
    with col_controls3:
        if training["rep_count"] >= ex['reps'] and training["exercise_started"]:
            if len(training["rpe_scores"]) > training["current_index"]:
                if st.button(get_text("training.next_button"), use_container_width=True):
                    advance_exercise()
                    st.rerun()
            else:
                st.button("📊 Rate First", disabled=True, use_container_width=True)
        else:
            st.button(get_text("training.locked_button"), disabled=True, use_container_width=True)

    # RPE Rating
    if training["rep_count"] >= ex['reps'] and training["exercise_started"]:
        if len(training["rpe_scores"]) <= training["current_index"]:
            st.divider()
            st.subheader(get_text("training.rate_prompt"))
            st.caption(get_text("training.rate_help"))
            rpe_val = st.slider("", 1, 10, 5, key=f"rpe_{training['current_index']}")
            st.markdown(f"<center>{['😊','🙂','😐','😅','😰'][(rpe_val-1)//2] if rpe_val <= 10 else '😊'}</center>", unsafe_allow_html=True)
            if st.button(get_text("training.submit_rating")):
                if len(training["rpe_scores"]) > training["current_index"]:
                    training["rpe_scores"][training["current_index"]] = rpe_val
                else:
                    training["rpe_scores"].append(rpe_val)
                st.session_state.user["last_rpe"] = rpe_val
                st.success(get_text("training.rating_saved", rpe=rpe_val))
                st.rerun()

    # Progress
    st.progress(training["rep_count"] / max(ex['reps'], 1))
    st.caption(get_text("training.progress_label", current=training['rep_count'], total=ex['reps']))

    # Rest day
    if user['day'] > 5:
        st.divider()
        st.subheader(get_text("training.rest_day_title"))
        rest_choices = [
            "🚶 Walk outdoors for 30 mins",
            "📖 Read a chapter of the Bible",
            "✍️ Write a gratitude journal entry",
            "🎵 Listen to soft music",
            "🧘 Focus on 10 minutes of diaphragmatic breathing"
        ]
        with st.form("rest_form"):
            rest_type = st.selectbox(get_text("training.rest_select"), rest_choices)
            reflection = st.text_area(get_text("training.rest_reflect"))
            if st.form_submit_button(get_text("training.rest_save")):
                try:
                    save_rest_reflection(
                        user_email=user["email"],
                        username=user["username"],
                        week=user["week"],
                        day=user["day"],
                        rest_type=rest_type,
                        reflection=reflection
                    )
                    st.success(get_text("training.rest_saved"))
                except Exception as e:
                    st.warning(f"Could not save reflection: {e}")

# ---------- MAIN ROUTER ----------
def main():
    # Get current page from query params
    page = get_current_page()
    
    if page == "training":
        render_training()
    else:
        render_onboarding()

if __name__ == "__main__":
    main()
