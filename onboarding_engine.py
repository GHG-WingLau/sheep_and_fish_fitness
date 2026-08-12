import json
from datetime import datetime

def process_onboarding(data):
    """
    Processes the onboarding data and returns a result dictionary.
    Handles red flags, SARC-F, calf circumference, single-leg stance,
    chair stand test (15-second), and assigns a Level (0–4).
    """
    # 1. Check Red Flags (immediate deferral)
    if data.get('red_flags'):
        return {
            'level': 'Level 0',
            'total_score': 'N/A',
            'status': 'Deferred to Doctor',
            'overview': 'You have reported one or more medical red flags. Please consult your physician before starting any exercise program.',
            'expectation': 'We recommend you share this assessment with your doctor to get personalized clearance.',
            'red_flags_checked': data['red_flags'],
            'stored': True
        }

    # 2. Calculate SARC-F (0–10)
    sarc_sum = sum(data['sarc_f'].values())

    # 3. Calf Circumference Score (0–2)
    calf = data['calf_cm']
    if data['gender'] == 'male':
        calf_score = 0 if calf > 34 else (1 if calf >= 31 else 2)
    else:
        calf_score = 0 if calf > 33 else (1 if calf >= 30 else 2)

    # 4. Single-Leg Stance Score (0–2)
    age = data['age_bucket']
    sec = data['single_leg_seconds']
    if age in ['60-64', '65-69']:
        single_score = 0 if sec >= 25 else (1 if sec >= 10 else 2)
    elif age in ['70-74', '75-79']:
        single_score = 0 if sec >= 15 else (1 if sec >= 8 else 2)
    else:  # 80+
        single_score = 0 if sec >= 8 else (1 if sec >= 4 else 2)

    # 5. Chair Stand Test (15-second) – Number of stands
    stands = data.get('chair_stands', 0)
    age_num = int(age.split('-')[0])
    
    # Normative values for 15-second chair stand
    if age_num >= 80:
        chair_score = 0 if stands >= 5 else (1 if stands >= 3 else 2)
    elif age_num >= 75:
        chair_score = 0 if stands >= 6 else (1 if stands >= 4 else 2)
    elif age_num >= 70:
        chair_score = 0 if stands >= 7 else (1 if stands >= 5 else 2)
    else:  # 60-69
        chair_score = 0 if stands >= 8 else (1 if stands >= 5 else 2)

    # 6. Total Score (0–14)
    total = sarc_sum + calf_score + single_score + chair_score

    # 7. Determine Level (0 = Chair-assisted, 1–4 = Standard)
    if age_num >= 80:
        level = 'Level 0'
    elif total >= 8:
        level = 'Level 0'
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
    else:  # 0–2
        level = 'Level 4'

    # 8. Generate Overview & Expectation
    level_desc = {
        'Level 0': 'chair-assisted exercises only. All movements performed seated. Max 15 mins/day.',
        'Level 1': 'very low intensity. Seated marching, pumps, Kegels, and lying stretches. Max 15 mins/day.',
        'Level 2': 'low intensity. Seated and lying exercises with chair support for standing moves. 30 mins/day.',
        'Level 3': 'moderate intensity. Full sets but static holds for all exercises. 30 mins/day.',
        'Level 4': 'standard intensity. Full dynamic exercises with eccentric focus. 30 mins/day.'
    }
    
    intensity_text = level_desc.get(level, "requires medical clearance.")

    overview = (
        f"Based on your assessment (Total Score: {total}/14), you are recommended for {level}. "
        f"This means {intensity_text}. "
        f"Your balance (Single-leg: {sec}s) and chair stand ability ({stands} stands in 15s) were key factors."
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
        'chair_score': chair_score,
        'chair_stands': stands,
        'red_flags_checked': data.get('red_flags', []),
        'overview': overview,
        'expectation': expectation,
        'stored': True
    }

def generate_summary_text(result, email, username):
    """
    Generates a clean text summary for download / email.
    """
    lines = []
    lines.append("=" * 50)
    lines.append("  ELDERLY TRAINING SYSTEM - PERSONAL SUMMARY")
    lines.append("=" * 50)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append(f"Username:  {username}")
    lines.append(f"Email:     {email}")
    lines.append(f"Level:     {result.get('level', 'N/A')}")
    lines.append(f"Total Score: {result.get('total_score', 'N/A')} (Lower is better)")
    lines.append("")
    lines.append("--- Breakdown Scores ---")
    lines.append(f"SARC-F:         {result.get('sarc_score', 'N/A')}")
    lines.append(f"Calf:           {result.get('calf_score', 'N/A')}")
    lines.append(f"Balance:        {result.get('single_score', 'N/A')}")
    lines.append(f"Chair Stands:   {result.get('chair_stands', 'N/A')} stands")
    lines.append("")
    lines.append("--- Assessment Overview ---")
    lines.append(result.get('overview', 'N/A'))
    lines.append("")
    lines.append("--- Expected Outcomes ---")
    lines.append(result.get('expectation', 'N/A'))
    lines.append("")
    lines.append("=" * 50)
    lines.append("  Keep this summary. Share it with your doctor or trainer.")
    lines.append("=" * 50)
    return "\n".join(lines)
