import json
from datetime import datetime

def process_onboarding(data):
    """
    Processes the onboarding data and returns a result dictionary.
    """
    # 1. Check Red Flags
    if data['red_flags']:
        return {
            'level': 'Level 0',
            'total_score': 'N/A',
            'status': 'Deferred to Doctor',
            'overview': 'You have reported one or more medical red flags. Please consult your physician before starting any exercise program.',
            'expectation': 'We recommend you share this assessment with your doctor to get personalized clearance.',
            'stored': True
        }

    # 2. Calculate SARC-F
    sarc_sum = sum(data['sarc_f'].values())

    # 3. Calf Score
    calf = data['calf_cm']
    if data['gender'] == 'male':
        calf_score = 0 if calf > 34 else (1 if calf >= 31 else 2)
    else:
        calf_score = 0 if calf > 33 else (1 if calf >= 30 else 2)

    # 4. Single-Leg Score (Age-based)
    age = data['age_bucket']
    sec = data['single_leg_seconds']
    if age in ['60-64', '65-69']:
        single_score = 0 if sec >= 25 else (1 if sec >= 10 else 2)
    elif age in ['70-74', '75-79']:
        single_score = 0 if sec >= 15 else (1 if sec >= 8 else 2)
    else: # 80+
        single_score = 0 if sec >= 8 else (1 if sec >= 4 else 2)

    # 5. Squat Score
    squat_map = {'full': 0, 'partial': 1, 'chair_touch': 2, 'unable': 3}
    squat_score = squat_map.get(data['deep_squat'], 3)

    # 6. Total Score
    total = sarc_sum + calf_score + single_score + squat_score

    # 7. Determine Level
    level = 'Level 4'
    age_num = int(age.split('-')[0])

    if age_num >= 80:
        level = 'Level 1'
    elif total >= 8:
        level = 'Level 1'
    elif total >= 5:
        if age_num >= 75:
            level = 'Level 1'
        else:
            level = 'Level 2'
    elif total >= 3:
        if age_num >= 75:
            level = 'Level 2'
        else:
            level = 'Level 3'
    elif total >= 0:
        level = 'Level 4'

    # 8. Generate Overview & Expectation
    level_desc = {
        'Level 1': 'very low intensity. Seated marching, pumps, Kegels, and lying stretches. Max 15 mins/day.',
        'Level 2': 'low intensity. Seated and lying exercises with chair support for standing moves. 30 mins/day.',
        'Level 3': 'moderate intensity. Full sets but static holds for all exercises. 30 mins/day.',
        'Level 4': 'standard intensity. Full dynamic exercises with progression to Weeks 3-4. 30 mins/day.'
    }
    
    intensity_text = level_desc.get(level, "requires medical clearance.")
    
    overview = (
        f"Based on your assessment (Total Score: {total}/17), you are recommended for {level}. "
        f"This means {intensity_text} "
        f"Your balance (Single-leg: {sec}s) and squat mobility ({data['deep_squat'].replace('_', ' ')}) were key factors."
    )

    expectation = (
        "With consistent daily 30-minute training (adjusted to your level), most participants see meaningful improvements within 4 weeks: "
        "better balance (longer single-leg stands), easier sit-to-stand transitions, reduced lower back tension, "
        "and greater confidence in daily activities like walking and climbing stairs. "
        "Progress is gradual—listen to your body and use the extra rest days when needed."
    )

    return {
        'level': level,
        'total_score': total,
        'sarc_score': sarc_sum,
        'calf_score': calf_score,
        'single_score': single_score,
        'squat_score': squat_score,
        'red_flags_checked': data['red_flags'],
        'overview': overview,
        'expectation': expectation,
        'stored': True
    }

def generate_summary_text(data):
    """
    Generates a clean text summary for download / email.
    """
    lines = []
    lines.append("=" * 50)
    lines.append("  ELDERLY TRAINING SYSTEM - PERSONAL SUMMARY")
    lines.append("=" * 50)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append(f"Username:  {data.get('username', 'N/A')}")
    lines.append(f"Email:     {data.get('email', 'N/A')}")
    lines.append(f"Level:     {data.get('level', 'N/A')}")
    lines.append(f"Total Score: {data.get('total_score', 'N/A')} (Lower is better)")
    lines.append("")
    lines.append("--- Breakdown Scores ---")
    lines.append(f"SARC-F:      {data.get('sarc_score', 'N/A')}")
    lines.append(f"Calf:        {data.get('calf_score', 'N/A')}")
    lines.append(f"Balance:     {data.get('single_score', 'N/A')}")
    lines.append(f"Squat:       {data.get('squat_score', 'N/A')}")
    lines.append("")
    lines.append("--- Assessment Overview ---")
    lines.append(data.get('overview', 'N/A'))
    lines.append("")
    lines.append("--- Expected Outcomes ---")
    lines.append(data.get('expectation', 'N/A'))
    lines.append("")
    lines.append("=" * 50)
    lines.append("  Keep this summary. Share it with your doctor or trainer.")
    lines.append("=" * 50)
    return "\n".join(lines)
