import random
from typing import List, Dict, Any, Optional

# ---------- EXERCISE CATALOG (20 Standard Cards) ----------
EXERCISE_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "1",
        "name": "Supine Glute Bridge",
        "target": "Glutes",
        "weeks": [2, 5],
        "levels": [2, 3, 4],
        "reps": 10,
        "hold": 3,
        "desc": "Lie on your back, knees bent, feet flat. Press heels, lift hips.",
        "breath_cue": "Exhale (lift, 2s). Inhale (lower, 4s).",
        "key_cue": "Lower like pressing through honey—4 seconds down.",
        "image_path": "card_1_glute_bridge.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "2",
        "name": "Side-Lying Hip Abduction",
        "target": "Glutes",
        "weeks": [2, 5],
        "levels": [3, 4],
        "reps": 12,
        "hold": 0,
        "desc": "Lie on side, bottom knee bent, top leg lifted to 45°.",
        "breath_cue": "Exhale (lift, 2s). Inhale (lower, 4s).",
        "key_cue": "Don't drop—control the lowering.",
        "image_path": "card_2_side_abduction.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "3",
        "name": "Standing Hip Abduction (Chair)",
        "target": "Glutes",
        "weeks": [2, 5],
        "levels": [2, 3, 4],
        "reps": 12,
        "hold": 0,
        "desc": "Stand behind chair, hold backrest, lift leg out to side.",
        "breath_cue": "Exhale (lift, 2s). Inhale (lower, 4s).",
        "key_cue": "Lower as slowly as you lifted.",
        "image_path": "card_3_standing_abduction.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "4",
        "name": "Seated Calf Raise (Toes Up)",
        "target": "Calves",
        "weeks": [3],
        "levels": [1, 2, 3, 4],
        "reps": 20,
        "hold": 0,
        "desc": "Sit upright, feet flat. Lift toes, heels stay down.",
        "breath_cue": "Exhale (lift toes, 2s). Inhale (lower, 4s).",
        "key_cue": "The magic is in the lowering.",
        "image_path": "card_4_seated_calf_raise.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "5",
        "name": "Standing Calf Raise (Chair)",
        "target": "Calves",
        "weeks": [3],
        "levels": [3, 4],
        "reps": 15,
        "hold": 0,
        "desc": "Stand holding chair, rise onto balls of feet.",
        "breath_cue": "Exhale (rise, 2s). Inhale (lower, 4s).",
        "key_cue": "Count 1-2 up, 1-2-3-4 down.",
        "image_path": "card_5_standing_calf_raise.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "6",
        "name": "Loaded Calf Stretch",
        "target": "Mobility",
        "weeks": [3, 5],
        "levels": [1, 2, 3, 4],
        "reps": 1,
        "hold": 0,
        "desc": "Facing wall, one leg back. Front leg bends, back heel lifts (2s) and lowers (4s).",
        "breath_cue": "Exhale (heel up, 2s). Inhale (heel down, 4s).",
        "key_cue": "Control the heel lift and lower.",
        "image_path": "card_6_loaded_calf_stretch.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "7",
        "name": "Kegel (Pelvic Floor)",
        "target": "Pelvic",
        "weeks": [1, 2],
        "levels": [1, 2, 3, 4],
        "reps": 10,
        "hold": 10,
        "desc": "Sit or lie down. Squeeze pelvic floor muscles, hold, release slowly.",
        "breath_cue": "Exhale (squeeze, 2s). Hold (10s). Inhale (release, 4s).",
        "key_cue": "Release slowly—feel the full relaxation.",
        "image_path": "card_7_kegel.png",
        "eccentric_focus": "Slow release (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "8",
        "name": "Bridge + Pelvic Integration",
        "target": "Pelvic",
        "weeks": [2],
        "levels": [2, 3, 4],
        "reps": 10,
        "hold": 0,
        "desc": "Lie on back, knees bent. Engage pelvic floor, then lift hips.",
        "breath_cue": "Exhale (squeeze + lift, 2s). Inhale (lower, 4s).",
        "key_cue": "Engage pelvic floor BEFORE you lift the hips.",
        "image_path": "card_8_bridge_pelvic.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "9",
        "name": "Seated Marching",
        "target": "Cardio",
        "weeks": [4],
        "levels": [1, 2, 3, 4],
        "reps": 180,  # seconds
        "hold": 0,
        "desc": "Sit tall. March knees alternately.",
        "breath_cue": "Inhale 2 steps, exhale 2 steps.",
        "key_cue": "Don't drop—guide the foot down.",
        "image_path": "card_9_seated_marching.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "10",
        "name": "Seated Resisted Leg Raise",
        "target": "Hip Flexors",
        "weeks": [3, 4],
        "levels": [1, 2, 3, 4],
        "reps": 10,
        "hold": 0,
        "desc": "Sit tall. Lift one leg while pressing down with hands to resist (2s). Then use hands to push leg down while leg resists (4s).",
        "breath_cue": "Exhale (lift with resistance, 2s). Inhale (lower with resistance, 4s).",
        "key_cue": "Push up against your hands. Resist the push down.",
        "image_path": "card_10_seated_resisted_leg_raise.png",
        "eccentric_focus": "Slow lowering with resistance (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "11",
        "name": "Single-Leg Stand (Chair)",
        "target": "Balance",
        "weeks": [2, 5],
        "levels": [2, 3, 4],
        "reps": 1,
        "hold": 10,
        "desc": "Stand holding chair, lift one foot, hold.",
        "breath_cue": "Exhale (lift, 2s). Breathe steady during hold. Inhale (lower, 4s).",
        "key_cue": "Place the foot down like it's made of glass.",
        "image_path": "card_11_single_leg_stand.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "12",
        "name": "Tandem Stand (Heel-to-Toe)",
        "target": "Balance",
        "weeks": [2, 5],
        "levels": [3, 4],
        "reps": 1,
        "hold": 10,
        "desc": "Stand with one foot directly in front of the other, heel to toe.",
        "breath_cue": "Exhale (position, 2s). Breathe steady during hold. Inhale (return, 4s).",
        "key_cue": "Press your big toe and heel into the floor.",
        "image_path": "card_12_tandem_stand.png",
        "eccentric_focus": "Slow return (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "13",
        "name": "Static Forward Lunge",
        "target": "Glutes",
        "weeks": [3],
        "levels": [2, 3, 4],
        "reps": 10,
        "hold": 0,
        "desc": "Step forward, lower back knee toward floor.",
        "breath_cue": "Exhale (lower, 4s). Inhale (rise, 2s).",
        "key_cue": "The descent builds the muscle.",
        "image_path": "card_13_forward_lunge.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "14",
        "name": "Static Side Lunge",
        "target": "Glutes",
        "weeks": [3],
        "levels": [3, 4],
        "reps": 10,
        "hold": 0,
        "desc": "Step wide, shift weight to bent knee.",
        "breath_cue": "Exhale (lower sideways, 4s). Inhale (return, 2s).",
        "key_cue": "Control the slide sideways.",
        "image_path": "card_14_side_lunge.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "15",
        "name": "Modified Downward Dog (Wall)",
        "target": "Mobility",
        "weeks": [5],
        "levels": [1, 2, 3, 4],
        "reps": 1,
        "hold": 0,
        "desc": "Hands on wall, walk down into a forward bend.",
        "breath_cue": "Exhale (lower, 4s). Inhale (return, 2s).",
        "key_cue": "Press palms firmly. Draw shoulders down.",
        "image_path": "card_15_downward_dog.png",
        "eccentric_focus": "Slow return (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "16",
        "name": "Seated Lat Stretch",
        "target": "Mobility",
        "weeks": [5],
        "levels": [1, 2, 3, 4],
        "reps": 1,
        "hold": 0,
        "desc": "Sit tall, reach overhead, lean to one side.",
        "breath_cue": "Inhale (reach up). Exhale (lean). Inhale (return, 4s).",
        "key_cue": "Sitting bones stay planted.",
        "image_path": "card_16_lat_stretch.png",
        "eccentric_focus": "Slow return (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "17",
        "name": "Supported Deep Squat Hold",
        "target": "Calves",
        "weeks": [3],
        "levels": [2, 3, 4],
        "reps": 1,
        "hold": 10,
        "desc": "Hold counter, lower into deep squat.",
        "breath_cue": "Exhale (lower, 4s). Breathe in hold. Inhale (rise, 2s).",
        "key_cue": "Lower like a feather, rise like a spring.",
        "image_path": "card_17_deep_squat.png",
        "eccentric_focus": "Slow descent (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "18",
        "name": "Partial Wall Squat",
        "target": "Calves",
        "weeks": [3],
        "levels": [1, 2, 3, 4],
        "reps": 1,
        "hold": 10,
        "desc": "Back against wall, slide to 45° knee bend.",
        "breath_cue": "Exhale (slide down, 4s). Breathe in hold. Inhale (slide up, 2s).",
        "key_cue": "Wall squats build strength on the way down.",
        "image_path": "card_18_wall_squat.png",
        "eccentric_focus": "Slow descent (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "19",
        "name": "Seated Trunk Rotation",
        "target": "Mobility",
        "weeks": [5],
        "levels": [2, 3, 4],
        "reps": 10,
        "hold": 4,
        "desc": "Sit tall, arms crossed, rotate upper body to one side. Hold for 4s, return.",
        "breath_cue": "Exhale (rotate, 2s). Hold (4s, normal breath). Inhale (return, 4s).",
        "key_cue": "Hips glued to chair. Only upper body moves.",
        "image_path": "card_19_trunk_rotation.png",
        "eccentric_focus": "Slow return (4s)",
        "osteoporosis_risk": True  # Disabled for osteoporosis users
    },
    {
        "id": "20",
        "name": "Supine Spinal Twist",
        "target": "Mobility",
        "weeks": [5],
        "levels": [1, 2, 3, 4],
        "reps": 1,
        "hold": 10,
        "desc": "Lie flat, arms stretched out (T-shape). Both knees bent, rotate legs to one side. Hold.",
        "breath_cue": "Exhale (rotate legs, 4s). Hold (10s, normal breath). Inhale (return, 2s).",
        "key_cue": "Both shoulder blades stay on the floor.",
        "image_path": "card_20_spinal_twist.png",
        "eccentric_focus": "Slow return (2s)",
        "osteoporosis_risk": False
    }
]

# ---------- LEVEL 0 (CHAIR-ASSISTED) CATALOG ----------
CHAIR_EXERCISE_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "L0_1",
        "name": "Seated Glute Squeeze",
        "target": "Glutes",
        "weeks": [1, 2, 3, 4, 5],
        "levels": [0],
        "reps": 10,
        "hold": 5,
        "desc": "Sit tall. Squeeze glutes together, hold, release.",
        "breath_cue": "Exhale (squeeze, 2s). Hold (5s). Inhale (release, 4s).",
        "key_cue": "Squeeze like holding a coin between your cheeks.",
        "image_path": "card_L0_1_seated_glute_squeeze.png",
        "eccentric_focus": "Slow release (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "L0_2",
        "name": "Seated Hip Abduction (Band)",
        "target": "Glutes",
        "weeks": [1, 2, 3, 4, 5],
        "levels": [0],
        "reps": 12,
        "hold": 0,
        "desc": "Sit tall. Push knees outward against band (or towel).",
        "breath_cue": "Exhale (push out, 2s). Inhale (return, 4s).",
        "key_cue": "Push against the band like opening a book.",
        "image_path": "card_L0_2_seated_abduction.png",
        "eccentric_focus": "Slow return (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "L0_3",
        "name": "Seated Knee Lift",
        "target": "Hip Flexors",
        "weeks": [1, 2, 3, 4, 5],
        "levels": [0],
        "reps": 12,
        "hold": 0,
        "desc": "Sit tall, hold chair sides. Lift knee toward chest.",
        "breath_cue": "Exhale (lift, 2s). Inhale (lower, 4s).",
        "key_cue": "Lift like stepping over a small log.",
        "image_path": "card_L0_3_seated_knee_lift.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "L0_4",
        "name": "Seated Heel Raise",
        "target": "Calves",
        "weeks": [1, 2, 3, 4, 5],
        "levels": [0],
        "reps": 15,
        "hold": 0,
        "desc": "Sit tall. Lift heels off floor, rise onto balls of feet.",
        "breath_cue": "Exhale (lift heels, 2s). Inhale (lower, 4s).",
        "key_cue": "Rise up, lower down like a feather.",
        "image_path": "card_L0_4_seated_heel_raise.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "L0_5",
        "name": "Seated Single-Leg Lift",
        "target": "Quads",
        "weeks": [1, 2, 3, 4, 5],
        "levels": [0],
        "reps": 10,
        "hold": 0,
        "desc": "Sit tall. Extend one leg forward, foot flexed.",
        "breath_cue": "Exhale (extend, 2s). Inhale (lower, 4s).",
        "key_cue": "Point toes up, lower with control.",
        "image_path": "card_L0_5_seated_leg_lift.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "L0_6",
        "name": "Seated Leg Extension",
        "target": "Quads",
        "weeks": [1, 2, 3, 4, 5],
        "levels": [0],
        "reps": 10,
        "hold": 0,
        "desc": "Sit tall. Straighten one knee, extend leg forward.",
        "breath_cue": "Exhale (extend, 2s). Inhale (lower, 4s).",
        "key_cue": "Straighten strong, lower slow.",
        "image_path": "card_L0_6_seated_extension.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "L0_7",
        "name": "Seated Squat Reach",
        "target": "Core",
        "weeks": [1, 2, 3, 4, 5],
        "levels": [0],
        "reps": 10,
        "hold": 0,
        "desc": "Sit tall. Lean forward, reach hands toward feet.",
        "breath_cue": "Exhale (reach forward, 4s). Inhale (return, 2s).",
        "key_cue": "Reach like picking up something from the floor.",
        "image_path": "card_L0_7_seated_squat_reach.png",
        "eccentric_focus": "Slow return (4s)",
        "osteoporosis_risk": False
    },
    {
        "id": "L0_8",
        "name": "Seated Toe Taps",
        "target": "Cardio",
        "weeks": [1, 2, 3, 4, 5],
        "levels": [0],
        "reps": 180,  # 3 minutes
        "hold": 0,
        "desc": "Sit tall. Tap toes alternately on the floor.",
        "breath_cue": "Steady breath with rhythm.",
        "key_cue": "Tap, tap, tap—keep the rhythm.",
        "image_path": "card_L0_8_seated_toe_taps.png",
        "eccentric_focus": "Slow lowering (4s)",
        "osteoporosis_risk": False
    }
]

# ---------- ENGINE LOGIC ----------
def get_chair_exercises(week: int, day: int) -> List[Dict]:
    """Return 3 chair-assisted exercises for Level 0 users."""
    random.seed(day + week * 100)
    # Select 3 different chair exercises
    selected = random.sample(CHAIR_EXERCISE_CATALOG, min(3, len(CHAIR_EXERCISE_CATALOG)))
    return selected

def get_daily_exercises(
    level: int,
    week: int,
    day: int,
    last_rpe: Optional[int] = None,
    has_osteoporosis: bool = False
) -> List[Dict]:
    """
    Selects 3 exercises for the day based on level, week, day, and last RPE.
    Level 0 returns chair-assisted exercises.
    Levels 1-4 return standard eccentric exercises.
    """
    # 1. If Level 0, return chair-assisted exercises only
    if level == 0:
        return get_chair_exercises(week, day)

    # 2. Map week to primary focus areas
    week_focus_map = {
        1: ['Breathing', 'Pelvic'],
        2: ['Glutes', 'Balance', 'Pelvic'],
        3: ['Calves', 'Glutes'],
        4: ['Cardio', 'Hip Flexors'],
        5: ['Mobility', 'Balance']
    }
    focus_areas = week_focus_map.get(week, ['Glutes', 'Balance'])
    
    # 3. Filter exercises by level and week, and osteoporosis safety
    filtered = []
    for ex in EXERCISE_CATALOG:
        # Level filter
        if level not in ex.get('levels', []):
            continue
        # Week filter
        if week not in ex.get('weeks', []):
            continue
        # Osteoporosis safety filter
        if has_osteoporosis and ex.get('osteoporosis_risk', False):
            continue
        filtered.append(ex)
    
    # 4. If filtered is empty, fallback to a safe set (e.g., breathing and seated exercises)
    if not filtered:
        fallback_exercises = [ex for ex in EXERCISE_CATALOG if ex['id'] in ['0A', '0B', '0C', '7', '9', '10']]
        if level in [1, 2]:
            fallback_exercises = [ex for ex in EXERCISE_CATALOG if ex['id'] in ['0A', '0B', '7', '9']]
        return fallback_exercises[:3]
    
    # 5. Group by target
    primary_exercises = [ex for ex in filtered if ex['target'] in focus_areas]
    secondary_exercises = [ex for ex in filtered if ex['target'] not in focus_areas]
    
    # If no primary exercises, use all filtered
    if not primary_exercises:
        primary_exercises = filtered
        secondary_exercises = []
    
    # 6. Deterministic shuffle based on day/week to maintain consistency
    random.seed(day + week * 100 + level * 10)
    
    # Pick 1 from primary, 1 from secondary, and 1 from remaining
    ex1 = random.choice(primary_exercises) if primary_exercises else random.choice(filtered)
    
    # Remove ex1 from pool for next selection
    remaining = [ex for ex in filtered if ex['id'] != ex1['id']]
    ex2 = random.choice(secondary_exercises) if secondary_exercises else random.choice(remaining) if remaining else ex1
    
    # Remove ex2 from pool
    remaining_after_ex2 = [ex for ex in remaining if ex['id'] != ex2['id']]
    ex3 = random.choice(remaining_after_ex2) if remaining_after_ex2 else ex2
    
    selected = [ex1, ex2, ex3]
    
    # 7. Adjust reps based on last RPE (only if RPE >= 8)
    if last_rpe is not None and last_rpe >= 8:
        for ex in selected:
            if ex['reps'] > 5:
                ex['reps'] = int(ex['reps'] * 0.8)
                ex['adjusted'] = True
                if ex['reps'] < 5:
                    ex['reps'] = 5
            # Also reduce hold time if it's a hold exercise
            if ex['hold'] > 5:
                ex['hold'] = int(ex['hold'] * 0.7)
                if ex['hold'] < 3:
                    ex['hold'] = 3
    else:
        for ex in selected:
            ex['adjusted'] = False
    
    return selected
