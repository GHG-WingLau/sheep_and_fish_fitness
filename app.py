"""
Elderly Online Training System
================================
Version: 1.0 (August 2026 Specification)
Description: A web-based adaptive exercise training platform for adults aged 60+
             delivering personalized exercise programs through AI/rule-driven assessments,
             eccentric focus timing, multi-language support, and RPE feedback loops.

Author: AI Senior Fitness Engineer
"""

import os
import sys
import json
import time
import math
import random
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

import pandas as pd
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor


# Setup Streamlit page configuration
st.set_page_config(
    page_title="Elderly Online Training System",
    page_icon="👵👴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Age Groups
AGE_GROUPS = ["60-64", "65-69", "70-74", "75-79", "80+"]

# Level Descriptions according to Section 4.1.9
LEVEL_INFO = {
    "Level 0": {
        "title": "Level 0: Chair-Assisted",
        "desc": "Chair-assisted exercises only, all movements seated.",
        "max_duration": "15 mins/day",
        "color": "#E53E3E"
    },
    "Level 1": {
        "title": "Level 1: Very Low Intensity",
        "desc": "Very low intensity, seated marching, pumps, Kegels, lying stretches.",
        "max_duration": "15 mins/day",
        "color": "#DD6B20"
    },
    "Level 2": {
        "title": "Level 2: Low Intensity",
        "desc": "Low intensity, seated/lying with chair support for standing.",
        "max_duration": "30 mins/day",
        "color": "#D69E2E"
    },
    "Level 3": {
        "title": "Level 3: Moderate Intensity",
        "desc": "Moderate intensity, full sets, static holds only.",
        "max_duration": "30 mins/day",
        "color": "#319795"
    },
    "Level 4": {
        "title": "Level 4: Standard Intensity",
        "desc": "Standard intensity, full dynamic with eccentric focus (4s lowering).",
        "max_duration": "30 mins/day",
        "color": "#38A169"
    }
}

# Weekly Focus Matrix according to Section 4.2.1
WEEKLY_FOCUS = {
    1: {"theme": "Foundation", "primary": "Breathing", "secondary": "Pelvic"},
    2: {"theme": "Stability", "primary": "Glutes", "secondary": "Balance"},
    3: {"theme": "Strength", "primary": "Calves", "secondary": "Glutes"},
    4: {"theme": "Endurance", "primary": "Cardio", "secondary": "Hip Flexors"},
    5: {"theme": "Consolidation", "primary": "Mobility", "secondary": "Balance"}
}



TRANSLATIONS = {
    "en": {
        "app_title": "Elderly Online Training System",
        "welcome": "Welcome to Your Personalized Senior Fitness Portal",
        "assessment_intro": "Complete our 10-minute assessment to receive a customized, safe exercise program tailored to your fitness level.",
        "nav_onboarding": "Assessment & Profile",
        "nav_training": "Daily Training",
        "nav_reflections": "Rest Day Reflections",
        "nav_progress": "Progress & History",
        "select_lang": "Language / 語言",
        "mode_register": "New Registration",
        "mode_update": "Update Assessment",
        "mode_retrieve": "Retrieve Profile",
        "email": "Email Address",
        "username": "User Name",
        "age_group": "Age Group",
        "safety_check": "Safety & Red Flag Screening",
        "red_flag_prompt": "Please select ANY conditions that apply to you currently:",
        "rf_chest_pain": "Chest pain or irregular heartbeat at rest",
        "rf_joint_replacement": "Hip, knee, or spine replacement in the last 6 months",
        "rf_bp_osteo": "Uncontrolled high blood pressure (>160/100) or severe osteoporosis",
        "rf_recent_falls": "2 or more falls within the last month",
        "sarcf_title": "SARC-F Strength & Mobility Assessment",
        "sarcf_q1": "1. How much difficulty do you have lifting and carrying 5kg?",
        "sarcf_q2": "2. How much difficulty do you have walking across a room?",
        "sarcf_q3": "3. How much difficulty do you have rising from a chair or bed?",
        "sarcf_q4": "4. How much difficulty do you have climbing 10 steps?",
        "sarcf_q5": "5. How many times have you fallen in the past year?",
        "opt_none": "None (0 pts)",
        "opt_some": "Some / 1-3 times (1 pt)",
        "opt_alot": "A lot / Unable / 4+ times (2 pts)",
        "gender": "Gender",
        "gender_male": "Male",
        "gender_female": "Female",
        "calf_circumference": "Calf Circumference (widest part of left calf in cm)",
        "single_leg_test": "Single-Leg Stance Duration (seconds with eyes open)",
        "chair_stand_test": "Chair Stand Count (complete stands in 15 seconds)",
        "submit_assessment": "Submit & Calculate Program",
        "retrieve_button": "Load Profile",
        "go_back": "Refresh Page",
        "download_summary": "Download Summary Report",
        "proceed_to_training": "Proceed to Daily Training",
        "return_to_dashboard": "Return to Dashboard",
        "assigned_level": "Assigned Program Level",
        "total_score": "Total Vulnerability Score",
        "lower_is_better": "Lower score represents higher baseline function",
        "week_day": "Week {week}, Day {day}",
        "exercise_of": "Exercise {current} of {total}",
        "target": "Target Muscle Group",
        "reps_holds": "Prescription",
        "reps": "Reps",
        "hold_sec": "Hold Seconds",
        "description": "Instructions",
        "key_cue": "Key Memory Cue",
        "eccentric_cue": "Eccentric Focus (Lowering)",
        "start_button": "Start Exercise",
        "pause_button": "Pause Narration",
        "resume_button": "Resume",
        "plus_rep_button": "+1 Rep Completed",
        "done_button": "Finish Exercise",
        "next_button": "Next Exercise",
        "rate_prompt": "Rate the Difficulty (RPE Score 1-10)",
        "submit_rating": "Submit RPE Rating",
        "complete_title": "Daily Workout Completed! 🎉",
        "rest_day_title": "Rest & Recovery Day 🌿",
        "rest_day_msg": "Rest days are crucial for muscle recovery and adaptation. Reflect on your recovery activity today.",
        "reflection_placeholder": "How are your muscles feeling today? Enter any notes or activities...",
        "save_reflection": "Save Reflection Log",
        "rpe_easy": "Very Easy / Easy",
        "rpe_mod": "Moderate",
        "rpe_hard": "Hard / Challenging",
        "rpe_vhard": "Very Hard"
    },
    "zh_HK": {
        "app_title": "長者線上運動訓練系統",
        "welcome": "歡迎使用長者個人化運動訓練平台",
        "assessment_intro": "請完成 10 分鐘健康評估，系統將為您量身定制最安全有效的運動方案。",
        "nav_onboarding": "健康評估與檔案",
        "nav_training": "每日訓練",
        "nav_reflections": "休息日感悟",
        "nav_progress": "進度歷史記錄",
        "select_lang": "Language / 語言",
        "mode_register": "新用戶登記 Assessment",
        "mode_update": "更新健康評估",
        "mode_retrieve": "讀取用戶檔案",
        "email": "電郵地址 Email",
        "username": "用戶姓名",
        "age_group": "年齡組別",
        "safety_check": "紅旗安全篩查 (Red Flag Screening)",
        "red_flag_prompt": "若您目前符合以下任何一項，請勾選：",
        "rf_chest_pain": "靜止時胸痛或心律不齊",
        "rf_joint_replacement": "過去6個月內曾接受髖/膝/脊椎置換手術",
        "rf_bp_osteo": "未受控的高血壓 (>160/100) 或嚴重骨質疏鬆症",
        "rf_recent_falls": "過去一個月內跌倒 2 次或以上",
        "sarcf_title": "SARC-F 肌少症與行動力問卷 Assessment",
        "sarcf_q1": "1. 提舉或搬運 5 公斤重物有否困難？",
        "sarcf_q2": "2. 步行穿過房間有否困難？",
        "sarcf_q3": "3. 從椅子或床上記起有否困難？",
        "sarcf_q4": "4. 爬 10 級樓梯有否困難？",
        "sarcf_q5": "5. 過去一年跌倒過多少次？",
        "opt_none": "沒有困難 (0 分)",
        "opt_some": "有些困難 / 1-3 次 (1 分)",
        "opt_alot": "非常困難 / 無法完成 / 4次以上 (2 分)",
        "gender": "性別",
        "gender_male": "男士",
        "gender_female": "女士",
        "calf_circumference": "小腿圍 (左腿最寬處，厘米 cm)",
        "single_leg_test": "單腳站立時間 (睜眼持績秒數)",
        "chair_stand_test": "15秒坐站測試 (雙手交叉胸前完成次數)",
        "submit_assessment": "提交並計算訓練等級",
        "retrieve_button": "讀取用戶資料",
        "go_back": "重新整理頁面",
        "download_summary": "下載評估報告",
        "proceed_to_training": "前往每日訓練",
        "return_to_dashboard": "返回主頁",
        "assigned_level": "獲派訓練等級",
        "total_score": "總風險評分",
        "lower_is_better": "分數越低代表基礎身體功能越佳",
        "week_day": "第 {week} 週，第 {day} 天",
        "exercise_of": "運動 {current} / {total}",
        "target": "目標肌肉群",
        "reps_holds": "運動處方",
        "reps": "次數",
        "hold_sec": "保持秒數",
        "description": "動作說明",
        "key_cue": "核心口訣",
        "eccentric_cue": "離心控制 (慢放4秒)",
        "start_button": "開始運動",
        "pause_button": "暫停語音",
        "resume_button": "繼續",
        "plus_rep_button": "+1 次完成",
        "done_button": "完成運動",
        "next_button": "下一個運動",
        "rate_prompt": "主觀疲勞感受評分 (RPE 1-10)",
        "submit_rating": "提交 RPE 評分",
        "complete_title": "今日訓練完成！🎉",
        "rest_day_title": "休息與恢復日 🌿",
        "rest_day_msg": "休息是肌肉修復與強化不可或缺的一環。請記錄今天的休息感受。",
        "reflection_placeholder": "今天肌肉感覺如何？輸入活動或感想...",
        "save_reflection": "儲存休息日記錄",
        "rpe_easy": "非常輕鬆 / 輕鬆",
        "rpe_mod": "適中",
        "rpe_hard": "辛苦 / 有挑戰",
        "rpe_vhard": "非常辛苦"
    },
    "zh_TW": {
        "app_title": "高齡線上運動訓練系統",
        "welcome": "歡迎使用長者個人化運動訓練平台",
        "assessment_intro": "請完成 10 分鐘健康評估，系統將為您量身定制最安全有效的運動方案。",
        "nav_onboarding": "健康評估與檔案",
        "nav_training": "每日訓練",
        "nav_reflections": "休息日感悟",
        "nav_progress": "進度歷史記錄",
        "select_lang": "Language / 語言",
        "mode_register": "新用戶註冊",
        "mode_update": "更新健康評估",
        "mode_retrieve": "讀取用戶檔案",
        "email": "電子郵件 Email",
        "username": "用戶姓名",
        "age_group": "年齡分組",
        "safety_check": "紅旗安全篩查 (Red Flag Screening)",
        "red_flag_prompt": "若您目前符合以下任何一項，請勾選：",
        "rf_chest_pain": "靜止時胸痛或心律不整",
        "rf_joint_replacement": "過去6個月內曾接受髖/膝/脊椎置換手術",
        "rf_bp_osteo": "未受控制的高血壓 (>160/100) 或嚴重骨質疏鬆症",
        "rf_recent_falls": "過去一個月內跌倒 2 次或以上",
        "sarcf_title": "SARC-F 肌少症與行動力問卷",
        "sarcf_q1": "1. 提舉或搬運 5 公斤重物是否有困難？",
        "sarcf_q2": "2. 步行穿過房間是否有困難？",
        "sarcf_q3": "3. 從椅子或床上站起是否有困難？",
        "sarcf_q4": "4. 爬 10 階樓梯是否有困難？",
        "sarcf_q5": "5. 過去一年跌倒過多少次？",
        "opt_none": "沒有困難 (0 分)",
        "opt_some": "有些困難 / 1-3 次 (1 分)",
        "opt_alot": "非常困難 / 無法完成 / 4次以上 (2 分)",
        "gender": "性別",
        "gender_male": "男性",
        "gender_female": "女性",
        "calf_circumference": "小腿圍 (左腿最寬處，公分 cm)",
        "single_leg_test": "單腳站立時間 (睜眼持續秒數)",
        "chair_stand_test": "15秒坐站測試 (雙手交叉胸前完成次數)",
        "submit_assessment": "提交並計算訓練等級",
        "retrieve_button": "讀取用戶資料",
        "go_back": "重新整理頁面",
        "download_summary": "下載評估報告",
        "proceed_to_training": "前往每日訓練",
        "return_to_dashboard": "返回主頁",
        "assigned_level": "獲派訓練等級",
        "total_score": "總風險評估分",
        "lower_is_better": "分數越低代表基礎身體功能越佳",
        "week_day": "第 {week} 週，第 {day} 天",
        "exercise_of": "運動 {current} / {total}",
        "target": "目標肌肉群",
        "reps_holds": "運動處方",
        "reps": "次數",
        "hold_sec": "保持秒數",
        "description": "動作說明",
        "key_cue": "核心口訣",
        "eccentric_cue": "離心控制 (慢放4秒)",
        "start_button": "開始運動",
        "pause_button": "暫停語音",
        "resume_button": "繼續",
        "plus_rep_button": "+1 次完成",
        "done_button": "完成運動",
        "next_button": "下一個運動",
        "rate_prompt": "主觀疲勞感受評分 (RPE 1-10)",
        "submit_rating": "提交 RPE 評分",
        "complete_title": "今日訓練完成！🎉",
        "rest_day_title": "休息與恢復日 🌿",
        "rest_day_msg": "休息是肌肉修復與強化不可或缺的一環。請記錄今天的休息感受。",
        "reflection_placeholder": "今天肌肉感覺如何？輸入活動或感想...",
        "save_reflection": "儲存休息日記錄",
        "rpe_easy": "非常輕鬆 / 輕鬆",
        "rpe_mod": "適中",
        "rpe_hard": "辛苦 / 有挑戰",
        "rpe_vhard": "非常辛苦"
    }
}


def get_text(lang: str, key: str, **kwargs) -> str:
    """Translation lookup with English fallback mechanism."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    template = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    try:
        return template.format(**kwargs)
    except Exception:
        return template


def get_db_connection():
    """
    Establish PostgreSQL connection using Neon database credentials from Streamlit secrets (.streamlit/secrets.toml).
    Expects st.secrets["connections"]["neon"]["url"], st.secrets["neon"]["url"], or st.secrets["DATABASE_URL"].
    """
    db_url = None
    try:
        if "connections" in st.secrets and "neon" in st.secrets["connections"]:
            db_url = st.secrets["connections"]["neon"]["url"]
        elif "neon" in st.secrets and "url" in st.secrets["neon"]:
            db_url = st.secrets["neon"]["url"]
        elif "DATABASE_URL" in st.secrets:
            db_url = st.secrets["DATABASE_URL"]
    except Exception:
        db_url = None

    if not db_url:
        st.error("⚠️ Neon PostgreSQL connection string missing in Streamlit secrets!")
        st.info("Please create or edit `.streamlit/secrets.toml` with your Neon PostgreSQL URL:")
        st.code("""
[connections.neon]
url = "postgresql://user:password@ep-xyz.region.aws.neon.tech/neondb?sslmode=require"
""", language="toml")
        st.stop()

    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        st.error(f"⚠️ Failed to connect to Neon PostgreSQL database: {e}")
        st.info("Ensure your Neon database is active and the connection string in `.streamlit/secrets.toml` is correct.")
        st.stop()


def init_db():
    """Create required PostgreSQL database tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            assessment_date TEXT NOT NULL,
            total_score INTEGER NOT NULL,
            level TEXT NOT NULL,
            sarc_score INTEGER,
            calf_score INTEGER,
            single_score INTEGER,
            chair_score INTEGER,
            chair_stands INTEGER,
            raw_payload TEXT
        )
    """)
    # Training Progress Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_progress (
            id SERIAL PRIMARY KEY,
            user_email TEXT NOT NULL,
            username TEXT NOT NULL,
            week INTEGER DEFAULT 1,
            day INTEGER DEFAULT 1,
            exercise_ids TEXT NOT NULL,
            rpe_scores TEXT NOT NULL,
            session_date TEXT NOT NULL,
            completed BOOLEAN DEFAULT FALSE
        )
    """)
    # Rest Reflections Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rest_reflections (
            id SERIAL PRIMARY KEY,
            user_email TEXT NOT NULL,
            username TEXT NOT NULL,
            week INTEGER,
            day INTEGER,
            reflection TEXT,
            rest_type TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# Initialize database schemas
init_db()


def calculate_sarcf_score(q1: int, q2: int, q3: int, q4: int, q5: int) -> int:
    """Calculates SARC-F score (0-10)."""
    return int(q1 + q2 + q3 + q4 + q5)


def calculate_calf_score(gender: str, cm: float) -> int:
    """
    Calf Circumference Scoring (Section 4.1.4):
    Male: >34cm (0), 31-34cm (1), <31cm (2)
    Female: >33cm (0), 30-33cm (1), <30cm (2)
    """
    if gender.lower() in ["male", "男士", "男性"]:
        if cm > 34.0:
            return 0
        elif cm >= 31.0:
            return 1
        else:
            return 2
    else:
        if cm > 33.0:
            return 0
        elif cm >= 30.0:
            return 1
        else:
            return 2


def calculate_balance_score(age_group: str, seconds: float) -> int:
    """
    Single-Leg Stance Scoring (Section 4.1.5):
    60-69: >=25s (0), 10-24s (1), <10s (2)
    70-79: >=15s (0), 8-14s (1), <8s (2)
    80+:   >=8s (0), 4-7s (1), <4s (2)
    """
    if age_group in ["60-64", "65-69"]:
        if seconds >= 25.0:
            return 0
        elif seconds >= 10.0:
            return 1
        else:
            return 2
    elif age_group in ["70-74", "75-79"]:
        if seconds >= 15.0:
            return 0
        elif seconds >= 8.0:
            return 1
        else:
            return 2
    else:  # 80+
        if seconds >= 8.0:
            return 0
        elif seconds >= 4.0:
            return 1
        else:
            return 2


def calculate_chair_score(age_group: str, count: int) -> int:
    """
    Chair Stand Test Scoring in 15 seconds (Section 4.1.6):
    60-69: >=8 (0), 5-7 (1), <=4 (2)
    70-74: >=7 (0), 4-6 (1), <=3 (2)
    75-79: >=6 (0), 4-5 (1), <=3 (2)
    80+:   >=5 (0), 3-4 (1), <=2 (2)
    """
    if age_group in ["60-64", "65-69"]:
        if count >= 8:
            return 0
        elif count >= 5:
            return 1
        else:
            return 2
    elif age_group == "70-74":
        if count >= 7:
            return 0
        elif count >= 4:
            return 1
        else:
            return 2
    elif age_group == "75-79":
        if count >= 6:
            return 0
        elif count >= 4:
            return 1
        else:
            return 2
    else:  # 80+
        if count >= 5:
            return 0
        elif count >= 3:
            return 1
        else:
            return 2


def assign_level_logic(age_group: str, total_score: int, red_flags: List[str]) -> str:
    """
    Level Assignment Rules (Section 4.1.8):
    1. If red flags or age >= 80+: Level 0
    2. If total score >= 8: Level 0
    3. If total score >= 5: If age >= 75: Level 1 Else: Level 2
    4. If total score >= 3: If age >= 75: Level 2 Else: Level 3
    5. If total score <= 2: Level 4
    """
    if len(red_flags) > 0 or age_group == "80+":
        return "Level 0"
    if total_score >= 8:
        return "Level 0"
    if total_score >= 5:
        if age_group in ["75-79", "80+"]:
            return "Level 1"
        return "Level 2"
    if total_score >= 3:
        if age_group in ["75-79", "80+"]:
            return "Level 2"
        return "Level 3"
    return "Level 4"



# Full Exercise Catalog (20 Standard + 8 Chair-Assisted) according to Section 6.3.4
STANDARD_EXERCISES = [
    {
        "id": "1", "name": "Supine Glute Bridge", "muscle": "Glutes",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 1", "Level 2", "Level 3", "Level 4"],
        "reps": 8, "hold": 5, "osteoporosis_risk": False,
        "desc": "Lie on your back with knees bent. Squeeze glutes and lift hips upward.",
        "breath_cue": "Exhale as you lift hips; Inhale for 4 seconds as you lower down.",
        "key_cue": "Press heels into the floor and squeeze glutes."
    },
    {
        "id": "2", "name": "Side-Lying Hip Abduction", "muscle": "Glutes",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 2", "Level 3", "Level 4"],
        "reps": 10, "hold": 3, "osteoporosis_risk": False,
        "desc": "Lie on your side with legs straight. Slowly lift upper leg toward ceiling.",
        "breath_cue": "Exhale as leg lifts up; Inhale for 4 seconds returning.",
        "key_cue": "Keep hips stacked and toe pointed forward."
    },
    {
        "id": "3", "name": "Standing Hip Abduction (Chair)", "muscle": "Glutes",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 1", "Level 2", "Level 3", "Level 4"],
        "reps": 10, "hold": 3, "osteoporosis_risk": False,
        "desc": "Stand holding a chair for balance. Lift leg out to the side smoothly.",
        "breath_cue": "Exhale during lifting; Inhale during 4-second lowering.",
        "key_cue": "Keep torso straight and upright."
    },
    {
        "id": "4", "name": "Seated Calf Raise (Toes Up)", "muscle": "Calves",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 1", "Level 2"],
        "reps": 12, "hold": 3, "osteoporosis_risk": False,
        "desc": "Seated in a chair, raise heels up high onto toes, then lower gently.",
        "breath_cue": "Exhale on heel raise; Inhale 4s as heels touch floor.",
        "key_cue": "Push through the ball of the foot."
    },
    {
        "id": "5", "name": "Standing Calf Raise (Chair)", "muscle": "Calves",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 2", "Level 3", "Level 4"],
        "reps": 10, "hold": 4, "osteoporosis_risk": False,
        "desc": "Stand behind a sturdy chair, lift heels off ground and hold briefly.",
        "breath_cue": "Exhale rising; Inhale 4s returning down.",
        "key_cue": "Tall spine, controlled lowering."
    },
    {
        "id": "6", "name": "Loaded Calf Stretch", "muscle": "Calves",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 1", "Level 2", "Level 3", "Level 4"],
        "reps": 6, "hold": 8, "osteoporosis_risk": False,
        "desc": "Step one foot back, press heel firm to floor to stretch calf muscle.",
        "breath_cue": "Breathe gently and deeply while holding position.",
        "key_cue": "Keep back leg straight and heel pressed down."
    },
    {
        "id": "7", "name": "Kegel (Pelvic Floor)", "muscle": "Pelvic",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 1", "Level 2", "Level 3", "Level 4"],
        "reps": 10, "hold": 5, "osteoporosis_risk": False,
        "desc": "Contract pelvic floor muscles as if stopping urine flow.",
        "breath_cue": "Exhale while squeezing; Relax fully on inhale.",
        "key_cue": "Squeeze inwardly and upwardly."
    },
    {
        "id": "8", "name": "Bridge + Pelvic Integration", "muscle": "Pelvic",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 2", "Level 3", "Level 4"],
        "reps": 8, "hold": 5, "osteoporosis_risk": False,
        "desc": "Combine pelvic floor squeeze with gentle hip lift in bridge pose.",
        "breath_cue": "Exhale on contraction/lift; Inhale lowering down.",
        "key_cue": "Synchronize pelvic contraction with hip lift."
    },
    {
        "id": "9", "name": "Seated Marching", "muscle": "Hip Flexors",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 1", "Level 2"],
        "reps": 12, "hold": 2, "osteoporosis_risk": False,
        "desc": "Sit tall in chair, alternately raise right and left knees upward.",
        "breath_cue": "Exhale as knee lifts; Inhale as foot lowers.",
        "key_cue": "Engage core, keep back straight."
    },
    {
        "id": "10", "name": "Seated Resisted Leg Raise", "muscle": "Hip Flexors",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 2", "Level 3", "Level 4"],
        "reps": 10, "hold": 3, "osteoporosis_risk": False,
        "desc": "Press hand against thigh for mild resistance while raising knee.",
        "breath_cue": "Exhale pushing against leg; Inhale release.",
        "key_cue": "Steady hand pressure without straining."
    },
    {
        "id": "11", "name": "Single-Leg Stand (Chair)", "muscle": "Balance",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 2", "Level 3", "Level 4"],
        "reps": 5, "hold": 10, "osteoporosis_risk": False,
        "desc": "Stand holding chair lightly, lift one foot off floor and balance.",
        "breath_cue": "Continuous steady nasal breathing during balance hold.",
        "key_cue": "Focus eyes on a fixed spot straight ahead."
    },
    {
        "id": "12", "name": "Tandem Stand", "muscle": "Balance",
        "weeks": [2, 3, 4, 5], "levels": ["Level 3", "Level 4"],
        "reps": 4, "hold": 10, "osteoporosis_risk": False,
        "desc": "Place heel of one foot directly in front of toes of other foot.",
        "breath_cue": "Deep rhythmic belly breaths during hold.",
        "key_cue": "Keep weight evenly distributed across both feet."
    },
    {
        "id": "13", "name": "Static Forward Lunge", "muscle": "Breathing",
        "weeks": [3, 4, 5], "levels": ["Level 3", "Level 4"],
        "reps": 8, "hold": 4, "osteoporosis_risk": True,
        "desc": "Step one foot forward, lower hips into a gentle controlled lunge.",
        "breath_cue": "Exhale as you sink into lunge; Inhale returning back.",
        "key_cue": "Keep front knee behind toes."
    },
    {
        "id": "14", "name": "Static Side Lunge", "muscle": "Mobility",
        "weeks": [3, 4, 5], "levels": ["Level 3", "Level 4"],
        "reps": 8, "hold": 4, "osteoporosis_risk": True,
        "desc": "Step wide to side, bend one knee while keeping other leg straight.",
        "breath_cue": "Exhale bending side knee; Inhale rising to center.",
        "key_cue": "Hips shift backward like sitting into a stool."
    },
    {
        "id": "15", "name": "Modified Downward Dog (Wall)", "muscle": "Mobility",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 1", "Level 2", "Level 3", "Level 4"],
        "reps": 6, "hold": 8, "osteoporosis_risk": False,
        "desc": "Hands on wall at shoulder height, step back and hinge at hips.",
        "breath_cue": "Inhale deeply into chest; Exhale length in spine.",
        "key_cue": "Lengthen back without curving lower spine."
    },
    {
        "id": "16", "name": "Seated Lat Stretch", "muscle": "Breathing",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 1", "Level 2", "Level 3", "Level 4"],
        "reps": 6, "hold": 8, "osteoporosis_risk": False,
        "desc": "Reach one arm overhead and lean gently to opposite side.",
        "breath_cue": "Inhale reaching high; Exhale deepening side stretch.",
        "key_cue": "Keep both sit bones firm on chair."
    },
    {
        "id": "17", "name": "Supported Deep Squat Hold", "muscle": "Mobility",
        "weeks": [2, 3, 4, 5], "levels": ["Level 3", "Level 4"],
        "reps": 6, "hold": 6, "osteoporosis_risk": True,
        "desc": "Hold sturdy support, squat down comfortably keeping heels flat.",
        "breath_cue": "Exhale lowering down; Inhale pressing back to standing.",
        "key_cue": "Chest proud, knees align over middle toes."
    },
    {
        "id": "18", "name": "Partial Wall Squat", "muscle": "Cardio",
        "weeks": [2, 3, 4, 5], "levels": ["Level 2", "Level 3", "Level 4"],
        "reps": 8, "hold": 5, "osteoporosis_risk": False,
        "desc": "Back against wall, slide down into partial seated position.",
        "breath_cue": "Exhale sliding down; Inhale 4s pressing back up.",
        "key_cue": "Press lower back flat against wall."
    },
    {
        "id": "19", "name": "Seated Trunk Rotation", "muscle": "Breathing",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 1", "Level 2", "Level 3", "Level 4"],
        "reps": 8, "hold": 4, "osteoporosis_risk": True,
        "desc": "Sit upright, gently rotate upper torso to right then left.",
        "breath_cue": "Exhale on rotation; Inhale return to center.",
        "key_cue": "Rotate smoothly without forcing range."
    },
    {
        "id": "20", "name": "Supine Spinal Twist", "muscle": "Mobility",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 1", "Level 2", "Level 3", "Level 4"],
        "reps": 6, "hold": 8, "osteoporosis_risk": True,
        "desc": "Lying on back, guide bent knees to one side gently.",
        "breath_cue": "Exhale lowering knees; Deep inhalation into ribs.",
        "key_cue": "Keep shoulders flat on floor."
    }
]

CHAIR_EXERCISES = [
    {
        "id": "L0_1", "name": "Seated Glute Squeeze", "muscle": "Glutes",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 0"],
        "reps": 10, "hold": 5, "osteoporosis_risk": False,
        "desc": "Sit upright in chair. Squeeze buttock muscles tight together.",
        "breath_cue": "Exhale during 5s squeeze; Inhale during relaxation.",
        "key_cue": "Sit tall without slouching."
    },
    {
        "id": "L0_2", "name": "Seated Hip Abduction (Band)", "muscle": "Glutes",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 0"],
        "reps": 10, "hold": 3, "osteoporosis_risk": False,
        "desc": "With knees bent, press knees outward against resistance or hands.",
        "breath_cue": "Exhale pressing outward; Inhale 4s returning inward.",
        "key_cue": "Feel outer hips engaging."
    },
    {
        "id": "L0_3", "name": "Seated Knee Lift", "muscle": "Hip Flexors",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 0"],
        "reps": 8, "hold": 3, "osteoporosis_risk": False,
        "desc": "Lift one knee upward toward ceiling, then lower with control.",
        "breath_cue": "Exhale lifting knee; Inhale 4s lower foot.",
        "key_cue": "Maintain stable upright posture."
    },
    {
        "id": "L0_4", "name": "Seated Heel Raise", "muscle": "Calves",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 0"],
        "reps": 12, "hold": 3, "osteoporosis_risk": False,
        "desc": "Keep toes on floor and push heels up high off ground.",
        "breath_cue": "Exhale pushing heels up; Inhale lowering slowly.",
        "key_cue": "Squeeze calves at peak position."
    },
    {
        "id": "L0_5", "name": "Seated Single-Leg Lift", "muscle": "Balance",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 0"],
        "reps": 8, "hold": 4, "osteoporosis_risk": False,
        "desc": "Extend lower leg straight out in front and hold in air.",
        "breath_cue": "Exhale extending leg; Inhale returning foot.",
        "key_cue": "Keep thigh steady on chair seat."
    },
    {
        "id": "L0_6", "name": "Seated Leg Extension", "muscle": "Cardio",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 0"],
        "reps": 10, "hold": 3, "osteoporosis_risk": False,
        "desc": "Straighten knee completely, flexing thigh muscle tight.",
        "breath_cue": "Exhale extending knee; Inhale lowering.",
        "key_cue": "Flex toes back toward knee."
    },
    {
        "id": "L0_7", "name": "Seated Squat Reach", "muscle": "Breathing",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 0"],
        "reps": 8, "hold": 3, "osteoporosis_risk": False,
        "desc": "Lean slightly forward from hips and reach arms out in front.",
        "breath_cue": "Inhale reaching forward; Exhale returning upright.",
        "key_cue": "Keep flat spine when leaning."
    },
    {
        "id": "L0_8", "name": "Seated Toe Taps", "muscle": "Mobility",
        "weeks": [1, 2, 3, 4, 5], "levels": ["Level 0"],
        "reps": 12, "hold": 2, "osteoporosis_risk": False,
        "desc": "Keep heels on floor, tap toes rapidly and rhythmically.",
        "breath_cue": "Natural steady breathing throughout.",
        "key_cue": "Waken shin muscles with crisp taps."
    }
]


def select_daily_exercises(
    level: str,
    week: int,
    day: int,
    last_rpe: Optional[float] = None,
    has_osteoporosis: bool = False
) -> List[Dict[str, Any]]:
    """
    Daily Exercise Selection Algorithm according to Section 4.2.2 & 4.2.3:
    - Level 0: Picks 3 deterministic exercises from chair catalog.
    - Levels 1-4: Filters standard catalog by level, week, osteoporosis risk,
      focus area rotation, and applies RPE adjustment.
    """
    selected = []

    if level == "Level 0":
        # Deterministic shuffle based on day + week
        seed = day + (week * 10)
        rng = random.Random(seed)
        catalog = list(CHAIR_EXERCISES)
        rng.shuffle(catalog)
        selected = catalog[:3]
    else:
        # Filter standard catalog
        filtered = [
            ex for ex in STANDARD_EXERCISES
            if level in ex["levels"] and week in ex["weeks"]
        ]

        if has_osteoporosis:
            filtered = [ex for ex in filtered if not ex.get("osteoporosis_risk", False)]

        focus_info = WEEKLY_FOCUS.get(week, WEEKLY_FOCUS[1])
        primary_focus = focus_info["primary"]
        secondary_focus = focus_info["secondary"]

        primary_group = [ex for ex in filtered if ex["muscle"] == primary_focus]
        secondary_group = [ex for ex in filtered if ex["muscle"] == secondary_focus]

        if not primary_group:
            primary_group = list(filtered)

        # Seeded deterministic shuffle
        level_num = int(level.split()[-1]) if "Level" in level else 1
        seed = day + (week * 100) + (level_num * 10)
        rng = random.Random(seed)

        pool_primary = list(primary_group)
        rng.shuffle(pool_primary)

        pool_secondary = list(secondary_group) if secondary_group else list(filtered)
        rng.shuffle(pool_secondary)

        pool_remaining = list(filtered)
        rng.shuffle(pool_remaining)

        chosen_ids = set()

        # Pick primary
        if pool_primary:
            item = pool_primary[0]
            selected.append(item)
            chosen_ids.add(item["id"])

        # Pick secondary
        for item in pool_secondary:
            if item["id"] not in chosen_ids:
                selected.append(item)
                chosen_ids.add(item["id"])
                break

        # Pick remaining 3rd exercise
        for item in pool_remaining:
            if item["id"] not in chosen_ids:
                selected.append(item)
                chosen_ids.add(item["id"])
                break

        # Fallback if catalog was small
        while len(selected) < 3 and len(filtered) > 0:
            for item in filtered:
                if item["id"] not in chosen_ids:
                    selected.append(item)
                    chosen_ids.add(item["id"])
                    if len(selected) == 3:
                        break

    # RPE Adjustment Rule (Section 4.2.3)
    final_exercises = []
    for ex in selected:
        ex_copy = dict(ex)
        if last_rpe is not None and last_rpe >= 8.0:
            if ex_copy["reps"] > 5:
                ex_copy["reps"] = max(5, int(ex_copy["reps"] * 0.8))
            if ex_copy["hold"] > 5:
                ex_copy["hold"] = max(3, int(ex_copy["hold"] * 0.7))
        final_exercises.append(ex_copy)

    return final_exercises[:3]



def generate_exercise_svg(ex_name: str, step_title: str, breath_type: str) -> str:
    """
    Generates a high-quality SVG panel illustration matching Section 6.3.1 & 6.3.2:
    Elderly character, clean flat style, clear posture display, and breathing indicators.
    """
    lung_color = "#A0AEC0"
    if breath_type == "exhale":
        badge_bg = "#ED8936"
        badge_text = "EXHALE (2s) 👄"
    elif breath_type == "inhale":
        badge_bg = "#3182CE"
        badge_text = "INHALE (4s) 👃"
    else:
        badge_bg = "#718096"
        badge_text = "NORMAL BREATH 🫁"

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 280" width="100%" height="220" style="background:#F7FAFC; border-radius:12px; border:1px solid #E2E8F0;">
        <!-- Background Decor -->
        <rect x="10" y="10" width="380" height="260" rx="8" fill="#FFFFFF" stroke="#EDF2F7" stroke-width="2"/>

        <!-- Header Tag -->
        <rect x="25" y="25" width="130" height="28" rx="14" fill="{badge_bg}"/>
        <text x="90" y="43" fill="#FFFFFF" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">{badge_text}</text>

        <text x="375" y="43" fill="#718096" font-size="12" font-weight="bold" text-anchor="end" font-family="sans-serif">{step_title}</text>

        <!-- Minimal Vector Character Representation -->
        <g transform="translate(140, 70)">
            <!-- Chair representation -->
            <rect x="10" y="100" width="80" height="8" fill="#A0AEC0"/>
            <rect x="15" y="108" width="8" height="60" fill="#CBD5E0"/>
            <rect x="75" y="108" width="8" height="60" fill="#CBD5E0"/>

            <!-- Head & Short White-Grey Hair -->
            <circle cx="50" cy="30" r="18" fill="#FED7D7"/>
            <path d="M 32 25 Q 50 10 68 25 Q 68 15 50 15 Q 32 15 32 25 Z" fill="#E2E8F0"/>

            <!-- Body (Light Blue Top) -->
            <path d="M 35 48 L 65 48 L 70 95 L 30 95 Z" fill="#63B3ED" rx="5"/>

            <!-- Arms -->
            <path d="M 35 50 L 15 80" stroke="#63B3ED" stroke-width="8" stroke-linecap="round"/>
            <path d="M 65 50 L 85 80" stroke="#63B3ED" stroke-width="8" stroke-linecap="round"/>

            <!-- Legs (Grey Pants) -->
            <path d="M 38 95 L 38 150" stroke="#4A5568" stroke-width="10" stroke-linecap="round"/>
            <path d="M 62 95 L 62 150" stroke="#4A5568" stroke-width="10" stroke-linecap="round"/>
        </g>

        <!-- Movement Direction Arrow -->
        <path d="M 280 130 Q 310 100 280 70" fill="none" stroke="#38A169" stroke-width="4" stroke-dasharray="5,5"/>
        <polygon points="275,75 285,65 288,78" fill="#38A169"/>

        <!-- Exercise Title Footer -->
        <text x="200" y="250" fill="#2D3748" font-size="14" font-weight="bold" text-anchor="middle" font-family="sans-serif">{ex_name}</text>
    </svg>
    """
    return svg



def render_header(lang: str):
    """Render application header and language navigation bar."""
    col_title, col_lang = st.columns([3, 1])

    with col_title:
        st.title(f"👵👴 {get_text(lang, 'app_title')}")
        st.caption(get_text(lang, "welcome"))

    with col_lang:
        selected_lang = st.selectbox(
            get_text(lang, "select_lang"),
            options=["en", "zh_HK", "zh_TW"],
            format_func=lambda x: "English 🇬🇧" if x == "en" else ("廣東話 (香港) 🇭🇰" if x == "zh_HK" else "繁體中文 (台灣) 🇹🇼"),
            index=["en", "zh_HK", "zh_TW"].index(st.session_state.get("lang", "en")),
            key="lang_selector"
        )
        if selected_lang != st.session_state.get("lang"):
            st.session_state["lang"] = selected_lang
            st.rerun()



def render_onboarding_page(lang: str):
    """Render Onboarding Assessment Page according to Section 6.1."""
    st.markdown("---")
    st.subheader("📋 " + get_text(lang, "nav_onboarding"))
    st.info(get_text(lang, "assessment_intro"))

    mode = st.radio(
        "Mode Select",
        options=["register", "update", "retrieve"],
        format_func=lambda x: get_text(lang, f"mode_{x}"),
        horizontal=True
    )

    with st.form("onboarding_form"):
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input(get_text(lang, "email"), value=st.session_state.get("user_email", ""))
        with col2:
            username = st.text_input(get_text(lang, "username"), value=st.session_state.get("username", ""))

        if mode == "retrieve":
            submitted_retrieve = st.form_submit_button(get_text(lang, "retrieve_button"))
            if submitted_retrieve:
                if not email:
                    st.error("Please provide an email address.")
                else:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE email = %s", (email.strip().lower(),))
                    row = cursor.fetchone()
                    conn.close()
                    if row:
                        st.session_state["user_email"] = row["email"]
                        st.session_state["username"] = row["username"]
                        st.session_state["assigned_level"] = row["level"]
                        st.session_state["total_score"] = row["total_score"]
                        st.success(f"Profile loaded for {row['username']}! Assigned Level: {row['level']}")
                    else:
                        st.error("User profile not found. Please register as a new user.")
            return

        st.markdown("### 1. " + get_text(lang, "age_group"))
        age_group = st.selectbox(get_text(lang, "age_group"), options=AGE_GROUPS, index=1)

        st.markdown("### 2. " + get_text(lang, "safety_check"))
        st.write(get_text(lang, "red_flag_prompt"))
        rf1 = st.checkbox(get_text(lang, "rf_chest_pain"))
        rf2 = st.checkbox(get_text(lang, "rf_joint_replacement"))
        rf3 = st.checkbox(get_text(lang, "rf_bp_osteo"))
        rf4 = st.checkbox(get_text(lang, "rf_recent_falls"))

        red_flags_selected = []
        if rf1: red_flags_selected.append("chest_pain")
        if rf2: red_flags_selected.append("joint_replacement")
        if rf3: red_flags_selected.append("bp_osteo")
        if rf4: red_flags_selected.append("recent_falls")

        st.markdown("### 3. " + get_text(lang, "sarcf_title"))
        sarc_opts = [get_text(lang, "opt_none"), get_text(lang, "opt_some"), get_text(lang, "opt_alot")]

        q1 = st.radio(get_text(lang, "sarcf_q1"), options=[0, 1, 2], format_func=lambda x: sarc_opts[x])
        q2 = st.radio(get_text(lang, "sarcf_q2"), options=[0, 1, 2], format_func=lambda x: sarc_opts[x])
        q3 = st.radio(get_text(lang, "sarcf_q3"), options=[0, 1, 2], format_func=lambda x: sarc_opts[x])
        q4 = st.radio(get_text(lang, "sarcf_q4"), options=[0, 1, 2], format_func=lambda x: sarc_opts[x])
        q5 = st.radio(get_text(lang, "sarcf_q5"), options=[0, 1, 2], format_func=lambda x: sarc_opts[x])

        st.markdown("### 4. Physical Assessments")
        gender = st.radio(get_text(lang, "gender"), options=["Male", "Female"], format_func=lambda x: get_text(lang, f"gender_{x.lower()}"))
        calf_cm = st.number_input(get_text(lang, "calf_circumference"), min_value=20.0, max_value=50.0, value=33.0, step=0.5)
        single_leg_s = st.number_input(get_text(lang, "single_leg_test"), min_value=0.0, max_value=120.0, value=15.0, step=0.5)
        chair_stands = st.number_input(get_text(lang, "chair_stand_test"), min_value=0, max_value=30, value=6, step=1)

        submitted = st.form_submit_button(get_text(lang, "submit_assessment"))

        if submitted:
            if not email or not username:
                st.error("Please complete Email and Username fields.")
                return

            # Execute calculations
            sarc_score = calculate_sarcf_score(q1, q2, q3, q4, q5)
            calf_score = calculate_calf_score(gender, calf_cm)
            balance_score = calculate_balance_score(age_group, single_leg_s)
            chair_score = calculate_chair_score(age_group, chair_stands)

            total_score = sarc_score + calf_score + balance_score + chair_score
            assigned_level = assign_level_logic(age_group, total_score, red_flags_selected)

            raw_payload = {
                "age_group": age_group,
                "red_flags": red_flags_selected,
                "sarcf": [q1, q2, q3, q4, q5],
                "gender": gender,
                "calf_cm": calf_cm,
                "single_leg_s": single_leg_s,
                "chair_stands": chair_stands
            }

            iso_now = datetime.now().isoformat()

            # Save to Database (Neon PostgreSQL upsert)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (email, username, assessment_date, total_score, level, sarc_score, calf_score, single_score, chair_score, chair_stands, raw_payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(email) DO UPDATE SET
                    username=EXCLUDED.username,
                    assessment_date=EXCLUDED.assessment_date,
                    total_score=EXCLUDED.total_score,
                    level=EXCLUDED.level,
                    sarc_score=EXCLUDED.sarc_score,
                    calf_score=EXCLUDED.calf_score,
                    single_score=EXCLUDED.single_score,
                    chair_score=EXCLUDED.chair_score,
                    chair_stands=EXCLUDED.chair_stands,
                    raw_payload=EXCLUDED.raw_payload
            """, (
                email.strip().lower(), username, iso_now, total_score, assigned_level,
                sarc_score, calf_score, balance_score, chair_score, chair_stands, json.dumps(raw_payload)
            ))
            conn.commit()
            conn.close()

            st.session_state["user_email"] = email.strip().lower()
            st.session_state["username"] = username
            st.session_state["assigned_level"] = assigned_level
            st.session_state["total_score"] = total_score
            st.session_state["has_osteoporosis"] = rf3 or ("bp_osteo" in red_flags_selected)

            st.success("Assessment completed successfully!")

    # Display Assessment Results Card if user present in session
    if "assigned_level" in st.session_state:
        lvl = st.session_state["assigned_level"]
        info = LEVEL_INFO[lvl]

        st.markdown("---")
        st.markdown(f"## 🎯 {get_text(lang, 'assigned_level')}: **{lvl}**")

        st.metric(
            label=get_text(lang, "total_score"),
            value=f"{st.session_state['total_score']} / 14",
            help=get_text(lang, "lower_is_better")
        )

        st.write(f"**Program Profile:** {info['title']}")
        st.write(f"**Description:** {info['desc']}")
        st.write(f"**Max Session Time:** {info['max_duration']}")

        col_a, col_b = st.columns(2)
        with col_a:
            st.button(
                "➡️ " + get_text(lang, "proceed_to_training"),
                on_click=lambda: st.session_state.update({"current_page": "training"}),
                use_container_width=True
            )
        with col_b:
            summary_txt = f"User: {st.session_state['username']}\nLevel: {lvl}\nScore: {st.session_state['total_score']}/14"
            st.download_button(
                "📥 " + get_text(lang, "download_summary"),
                data=summary_txt,
                file_name=f"Assessment_{st.session_state['username']}.txt",
                mime="text/plain",
                use_container_width=True
            )



def render_training_page(lang: str):
    """Render Daily Exercise Training Player according to Section 6.2."""
    st.markdown("---")
    if "user_email" not in st.session_state or "assigned_level" not in st.session_state:
        st.warning("No user profile loaded. Please complete or load an assessment first.")
        st.button("Go to Onboarding", on_click=lambda: st.session_state.update({"current_page": "onboarding"}))
        return

    level = st.session_state["assigned_level"]
    week = st.session_state.get("train_week", 1)
    day = st.session_state.get("train_day", 1)

    # 7-day timeline rendering
    st.subheader(get_text(lang, "week_day", week=week, day=day))
    timeline_cols = st.columns(7)
    for i, col in enumerate(timeline_cols, start=1):
        with col:
            if i == day:
                st.markdown(f"**🟢 Day {i}**")
            elif i in [6, 7]:
                st.markdown(f"🌿 Day {i} (Rest)")
            else:
                st.markdown(f"⚪ Day {i}")

    # Check for Rest Day (Days 6 & 7)
    if day in [6, 7]:
        st.info(f"### {get_text(lang, 'rest_day_title')}\n{get_text(lang, 'rest_day_msg')}")
        reflection = st.text_area(get_text(lang, "reflection_placeholder"))
        if st.button(get_text(lang, "save_reflection")):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rest_reflections (user_email, username, week, day, reflection, rest_type, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                st.session_state["user_email"], st.session_state["username"],
                week, day, reflection, "Rest", datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            st.success("Rest reflection saved successfully!")
            # Advance day
            st.session_state["train_day"] = (day % 7) + 1
            if st.session_state["train_day"] == 1:
                st.session_state["train_week"] = min(5, week + 1)
            st.rerun()
        return

    # Fetch daily exercises
    last_rpe = st.session_state.get("last_rpe", None)
    has_osteo = st.session_state.get("has_osteoporosis", False)
    daily_exercises = select_daily_exercises(level, week, day, last_rpe=last_rpe, has_osteoporosis=has_osteo)

    current_idx = st.session_state.get("current_ex_idx", 0)

    if current_idx >= len(daily_exercises):
        # All 3 exercises completed! Achievement view (Section 6.2.5)
        st.balloons()
        st.markdown(f"## {get_text(lang, 'complete_title')}")
        avg_rpe = sum(st.session_state.get("today_rpes", [5])) / max(1, len(st.session_state.get("today_rpes", [1])))
        st.metric("Session Average RPE", f"{avg_rpe:.1f} / 10")
        st.success("Excellent control! You have safely completed all prescribed exercises for today.")

        # Save training session to DB
        conn = get_db_connection()
        cursor = conn.cursor()
        ex_ids = json.dumps([e["id"] for e in daily_exercises])
        rpe_json = json.dumps(st.session_state.get("today_rpes", [5, 5, 5]))
        cursor.execute("""
            INSERT INTO training_progress (user_email, username, week, day, exercise_ids, rpe_scores, session_date, completed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
        """, (st.session_state["user_email"], st.session_state["username"], week, day, ex_ids, rpe_json, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        if st.button("Continue to Next Day ⏩"):
            st.session_state["current_ex_idx"] = 0
            st.session_state["today_rpes"] = []
            st.session_state["train_day"] = (day % 7) + 1
            if st.session_state["train_day"] == 1:
                st.session_state["train_week"] = min(5, week + 1)
            st.rerun()

        return

    ex = daily_exercises[current_idx]

    st.markdown(f"#### {get_text(lang, 'exercise_of', current=current_idx + 1, total=len(daily_exercises))}")
    st.progress((current_idx + 1) / len(daily_exercises))

    # Exercise Overview Card
    st.subheader(f"🏋️ {ex['name']}")
    col_c1, col_c2 = st.columns([1, 1])

    with col_c1:
        st.write(f"**{get_text(lang, 'target')}:** {ex['muscle']}")
        st.write(f"**{get_text(lang, 'reps_holds')}:** {ex['reps']} {get_text(lang, 'reps')} × {ex['hold']}s {get_text(lang, 'hold_sec')}")
        st.write(f"**{get_text(lang, 'description')}:** {ex['desc']}")
        st.write(f"**{get_text(lang, 'key_cue')}:** 💡 *{ex['key_cue']}*")
        st.info(f"**{get_text(lang, 'eccentric_cue')}:** {ex['breath_cue']}")

    with col_c2:
        # 3-Panel Illustration display
        tab1, tab2, tab3 = st.tabs(["Panel 1: Setup", "Panel 2: Concentric (2s)", "Panel 3: Eccentric (4s)"])
        with tab1:
            st.components.v1.html(generate_exercise_svg(ex['name'], "Setup Position", "hold"), height=240)
        with tab2:
            st.components.v1.html(generate_exercise_svg(ex['name'], "Concentric (Lift 2s)", "exhale"), height=240)
        with tab3:
            st.components.v1.html(generate_exercise_svg(ex['name'], "Eccentric (Lower 4s)", "inhale"), height=240)

    # Interactive Timer & Narration Coach Protocol (Section 4.3)
    st.markdown("---")
    st.markdown("### ⏱️ Virtual Coach Guidance")

    rep_counter = st.session_state.get("rep_counter", 1)
    st.write(f"**Current Repetition:** {rep_counter} / {ex['reps']}")

    col_btn1, col_btn2, col_btn3 = st.columns(3)

    if "timer_active" not in st.session_state:
        st.session_state["timer_active"] = False

    with col_btn1:
        if st.button("▶️ " + get_text(lang, "start_button"), use_container_width=True):
            st.session_state["timer_active"] = True

    with col_btn2:
        if st.button("➕ " + get_text(lang, "plus_rep_button"), use_container_width=True):
            st.session_state["rep_counter"] = min(ex["reps"], rep_counter + 1)
            st.rerun()

    with col_btn3:
        if st.button("✔️ " + get_text(lang, "done_button"), use_container_width=True):
            st.session_state["show_rpe_rating"] = True

    # Active Coach Narration Simulation
    if st.session_state.get("timer_active"):
        coach_placeholder = st.empty()
        # Simulated timing loop: Concentric (2s) -> Hold (ex['hold']s) -> Eccentric (4s)
        coach_placeholder.warning(f"🗣️ Coach: Let's begin rep {rep_counter} of {ex['name']}!")
        time.sleep(1)
        coach_placeholder.error("🗣️ Coach: EXHALE and lift/extend... 2 seconds.")
        time.sleep(1.5)
        coach_placeholder.info(f"🗣️ Coach: HOLD at the top... {ex['hold']} seconds.")
        time.sleep(1.5)
        coach_placeholder.success("🗣️ Coach: Now INHALE and lower slowly... 1... 2... 3... 4 seconds.")
        time.sleep(1.5)
        coach_placeholder.info("🗣️ Coach: Great control! Squeeze at the end.")
        st.session_state["timer_active"] = False

    # RPE Rating Modal/Prompt (Section 6.2.4)
    if st.session_state.get("show_rpe_rating", False):
        st.markdown("---")
        st.markdown(f"### 📊 {get_text(lang, 'rate_prompt')}")
        rpe_score = st.slider("RPE Scale (1 = Very Easy, 10 = Very Hard)", min_value=1, max_value=10, value=5)

        rpe_label = get_text(lang, "rpe_mod")
        if rpe_score <= 2: rpe_label = get_text(lang, "rpe_easy")
        elif rpe_score <= 6: rpe_label = get_text(lang, "rpe_mod")
        elif rpe_score <= 8: rpe_label = get_text(lang, "rpe_hard")
        else: rpe_label = get_text(lang, "rpe_vhard")

        st.caption(f"Rating: **{rpe_score}** - {rpe_label}")

        if st.button(get_text(lang, "submit_rating")):
            if "today_rpes" not in st.session_state:
                st.session_state["today_rpes"] = []
            st.session_state["today_rpes"].append(rpe_score)
            st.session_state["last_rpe"] = rpe_score

            # Reset flags for next exercise
            st.session_state["show_rpe_rating"] = False
            st.session_state["current_ex_idx"] = current_idx + 1
            st.session_state["rep_counter"] = 1
            st.rerun()



def render_progress_page(lang: str):
    """Render User Progress & Session History Dashboard."""
    st.markdown("---")
    st.subheader("📈 " + get_text(lang, "nav_progress"))

    if "user_email" not in st.session_state:
        st.warning("Please load or create a profile to view progress history.")
        return

    conn = get_db_connection()

    # Load Training History
    df_training = pd.read_sql_query(
        "SELECT week, day, rpe_scores, session_date, completed FROM training_progress WHERE user_email = %s ORDER BY id DESC",
        conn, params=(st.session_state["user_email"],)
    )

    # Load Reflections History
    df_reflections = pd.read_sql_query(
        "SELECT week, day, reflection, created_at FROM rest_reflections WHERE user_email = %s ORDER BY id DESC",
        conn, params=(st.session_state["user_email"],)
    )
    conn.close()

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Total Completed Sessions", len(df_training[df_training["completed"] == True]) if not df_training.empty else 0)
    with col_m2:
        st.metric("Rest Reflections Logged", len(df_reflections) if not df_reflections.empty else 0)

    st.markdown("### 🏋️ Training Session Log")
    if not df_training.empty:
        st.dataframe(df_training, use_container_width=True)
    else:
        st.info("No completed training sessions recorded yet.")

    st.markdown("### 🌿 Rest Day Reflections")
    if not df_reflections.empty:
        st.dataframe(df_reflections, use_container_width=True)
    else:
        st.info("No rest reflections recorded yet.")


def render_reflections_page(lang: str):
    """Render Rest Day Reflection Log entry page."""
    st.markdown("---")
    st.subheader("🌿 " + get_text(lang, "nav_reflections"))

    if "user_email" not in st.session_state:
        st.warning("Please load or create a profile to record rest day reflections.")
        return

    week = st.session_state.get("train_week", 1)
    day = st.session_state.get("train_day", 6)

    st.info(get_text(lang, "rest_day_msg"))
    reflection = st.text_area(get_text(lang, "reflection_placeholder"))

    if st.button(get_text(lang, "save_reflection")):
        if reflection.strip():
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rest_reflections (user_email, username, week, day, reflection, rest_type, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                st.session_state["user_email"],
                st.session_state["username"],
                week, day, reflection, "Rest", datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            st.success("Reflection saved successfully!")
        else:
            st.warning("Please enter reflection notes before saving.")


def main():
    """Main application layout and navigation router."""
    if "lang" not in st.session_state:
        st.session_state["lang"] = "en"
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "onboarding"

    lang = st.session_state["lang"]
    render_header(lang)

    # Sidebar Navigation
    st.sidebar.title("🧭 Navigation")

    # User status box in sidebar
    if "user_email" in st.session_state and st.session_state["user_email"]:
        st.sidebar.success(f"👤 **{st.session_state.get('username', 'User')}**")
        st.sidebar.caption(f"📧 {st.session_state['user_email']}")
        st.sidebar.caption(f"🏅 {st.session_state.get('assigned_level', 'Unassigned')}")
        st.sidebar.markdown("---")

    nav_choice = st.sidebar.radio(
        "Go to",
        options=["onboarding", "training", "reflections", "progress"],
        format_func=lambda x: {
            "onboarding": f"📋 {get_text(lang, 'nav_onboarding')}",
            "training": f"🏋️ {get_text(lang, 'nav_training')}",
            "reflections": f"🌿 {get_text(lang, 'nav_reflections')}",
            "progress": f"📈 {get_text(lang, 'nav_progress')}"
        }[x],
        index=["onboarding", "training", "reflections", "progress"].index(
            st.session_state.get("current_page", "onboarding")
            if st.session_state.get("current_page") in ["onboarding", "training", "reflections", "progress"]
            else "onboarding"
        )
    )

    if nav_choice != st.session_state.get("current_page"):
        st.session_state["current_page"] = nav_choice
        st.rerun()

    # Route page
    current_page = st.session_state["current_page"]
    if current_page == "onboarding":
        render_onboarding_page(lang)
    elif current_page == "training":
        render_training_page(lang)
    elif current_page == "reflections":
        render_reflections_page(lang)
    elif current_page == "progress":
        render_progress_page(lang)


if __name__ == "__main__":
    main()
