"""
GradeUP — Premium Defence Exam Preparation Platform
A glassmorphism Streamlit app for NDA/CDS aspirants.
"""

import streamlit as st
import requests
import random
import time
import datetime
import html
import altair as alt
import pandas as pd
import sqlite3
import os

# ─────────────────────────────────────────────
# DATABASE — SQLite persistence
# ─────────────────────────────────────────────
DB_PATH = "gradeup_results.db"

def init_db():
    """Create tables if they don't exist."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT,
            email       TEXT,
            course      TEXT,
            date        TEXT,
            subject     TEXT,
            chapter     TEXT,
            mode        TEXT,
            score       INTEGER,
            total       INTEGER,
            percentage  REAL,
            time_taken  INTEGER
        )
    """)
    con.commit()
    con.close()

def db_save_result(result: dict, name: str, email: str, course: str):
    """Insert one test result into the database."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO test_results
            (name, email, course, date, subject, chapter, mode, score, total, percentage, time_taken)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name, email, course,
        result["date"], result["subject"], result["chapter"],
        result["mode"], result["score"], result["total"],
        result["percentage"], result["time_taken"]
    ))
    con.commit()
    con.close()

def db_get_leaderboard(limit: int = 20) -> list:
    """Return top scores sorted by percentage desc."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        SELECT name, course, subject, chapter, score, total, percentage, date
        FROM test_results
        ORDER BY percentage DESC, time_taken ASC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    con.close()
    return rows

# ─────────────────────────────────────────────
# GLOBAL CSS — injected first on every render
# ─────────────────────────────────────────────
GLOBAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(145deg, #0f1e45 0%, #1a3a6e 40%, #2a5298 75%, #3a6fd8 100%);
        background-attachment: fixed;
    }
    /* Animated subtle shimmer overlay */
    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        inset: 0;
        background: radial-gradient(ellipse at 20% 20%, rgba(100,160,255,0.12) 0%, transparent 60%),
                    radial-gradient(ellipse at 80% 80%, rgba(80,120,255,0.10) 0%, transparent 60%);
        pointer-events: none;
        z-index: 0;
    }
    .stApp > header {
        background: transparent !important;
    }
    section[data-testid="stSidebar"] {
        background: rgba(10, 25, 65, 0.65) !important;
        backdrop-filter: blur(20px) saturate(200%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(200%) !important;
        border-right: 1px solid rgba(168, 216, 255, 0.15) !important;
        border-radius: 0 32px 32px 0 !important;
        box-shadow: 4px 0 32px rgba(0,0,0,0.3) !important;
    }
    .block-container {
        background: rgba(255, 255, 255, 0.07) !important;
        backdrop-filter: blur(20px) saturate(160%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(160%) !important;
        border: 1px solid rgba(255, 255, 255, 0.13) !important;
        border-radius: 32px !important;
        box-shadow: 0 12px 48px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.1) !important;
        padding: 2.5rem !important;
        margin: 1rem !important;
    }
    /* Primary action buttons */
    .stButton > button {
        background: linear-gradient(135deg, rgba(168,216,255,0.22), rgba(100,160,255,0.18)) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(168,216,255,0.35) !important;
        border-radius: 999px !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.72rem 1.8rem !important;
        transition: all 0.25s ease !important;
        font-family: 'Poppins', sans-serif !important;
        letter-spacing: 0.02em !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.15) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) scale(1.02) !important;
        background: linear-gradient(135deg, rgba(168,216,255,0.38), rgba(100,160,255,0.30)) !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.2) !important;
        border-color: rgba(168,216,255,0.6) !important;
    }
    .stButton > button:active {
        transform: translateY(0px) scale(0.99) !important;
    }
    /* Inputs */
    input[type="text"], input[type="email"], textarea {
        background: rgba(255, 255, 255, 0.10) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(168,216,255,0.25) !important;
        color: white !important;
        padding: 0.65rem 1.1rem !important;
        font-family: 'Poppins', sans-serif !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    input[type="text"]:focus, input[type="email"]:focus, textarea:focus {
        border-color: rgba(168,216,255,0.6) !important;
        box-shadow: 0 0 0 3px rgba(168,216,255,0.15) !important;
        outline: none !important;
    }
    input::placeholder, textarea::placeholder {
        color: rgba(255,255,255,0.38) !important;
    }
    /* Selectbox */
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.10) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(168,216,255,0.25) !important;
        color: white !important;
    }
    /* Radio */
    .stRadio > div { gap: 0.5rem; }
    .stRadio label {
        background: rgba(255,255,255,0.09) !important;
        border-radius: 16px !important;
        padding: 0.6rem 1rem !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        transition: background 0.2s, border-color 0.2s !important;
    }
    .stRadio label:hover {
        background: rgba(168,216,255,0.15) !important;
        border-color: rgba(168,216,255,0.4) !important;
    }
    hr {
        border-color: rgba(255, 255, 255, 0.12) !important;
    }
    footer {visibility: hidden !important;}
    .watermark {
        position: fixed;
        bottom: 14px;
        left: 50%;
        transform: translateX(-50%);
        color: rgba(255, 255, 255, 0.45);
        font-size: 13px;
        font-family: 'Poppins', system-ui, sans-serif;
        z-index: 9999;
        pointer-events: none;
        text-shadow: 0 1px 4px rgba(0,0,0,0.5);
        white-space: nowrap;
    }
    .login-love {
        text-align: center;
        margin-top: 1.4rem;
        font-size: 1.1rem;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.92);
        font-family: 'Poppins', sans-serif;
        letter-spacing: 0.04em;
        text-shadow: 0 2px 12px rgba(168,216,255,0.5);
    }
    h1, h2, h3 {
        color: white !important;
        font-family: 'Poppins', sans-serif !important;
    }
    p, label, div, span {
        font-family: 'Poppins', sans-serif;
        color: rgba(255,255,255,0.92);
    }
    /* Glass card helper */
    .glass-card {
        background: rgba(255,255,255,0.09);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(168,216,255,0.18);
        border-radius: 28px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.08);
        padding: 1.8rem 2.2rem;
        margin-bottom: 1.2rem;
    }
    .timer-badge {
        display: inline-block;
        background: rgba(255,80,80,0.28);
        border: 1px solid rgba(255,120,120,0.4);
        border-radius: 999px;
        padding: 0.4rem 1.4rem;
        font-size: 1.1rem;
        font-weight: 700;
        color: white;
        letter-spacing: 0.05em;
        backdrop-filter: blur(8px);
    }
    .subject-tile {
        background: rgba(255,255,255,0.09);
        border: 1px solid rgba(168,216,255,0.18);
        border-radius: 24px;
        padding: 1.2rem 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 600;
        font-size: 1rem;
        color: white;
        margin-bottom: 0.5rem;
    }
    .subject-tile:hover {
        background: rgba(168,216,255,0.2);
        border-color: rgba(168,216,255,0.4);
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }
    .score-big {
        font-size: 3.5rem;
        font-weight: 800;
        color: white;
        text-align: center;
        line-height: 1;
    }
    .correct-answer { color: #7fffb0 !important; font-weight: 600; }
    .wrong-answer   { color: #ff9090 !important; font-weight: 600; }
    /* Info/error boxes */
    .stAlert {
        border-radius: 16px !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
    }
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); }
    ::-webkit-scrollbar-thumb { background: rgba(168,216,255,0.3); border-radius: 999px; }
</style>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
"""

# ─────────────────────────────────────────────
# WATERMARK (required on every page)
# ─────────────────────────────────────────────
WATERMARK = '<div class="watermark">Made with love ❤️ for NAUSHERA</div>'

# ─────────────────────────────────────────────
# HARDCODED QUESTION BANKS (fallback)
# ─────────────────────────────────────────────
QUESTION_BANK = {
    "English": {
        "Grammar": [
            {"question": "Choose the correct form: 'Neither of the boys ___ done his homework.'",
             "options": ["have", "has", "had", "having"], "correct": 1},
            {"question": "Which sentence is grammatically correct?",
             "options": [
                 "She don't like apples.",
                 "She doesn't likes apples.",
                 "She doesn't like apples.",
                 "She not like apples."
             ], "correct": 2},
            {"question": "The antonym of 'abundant' is:",
             "options": ["plentiful", "scarce", "ample", "sufficient"], "correct": 1},
            {"question": "Fill in: 'He is looking forward ___ meeting you.'",
             "options": ["to", "for", "at", "of"], "correct": 0},
            {"question": "Identify the passive voice: 'The letter was written by Ravi.'",
             "options": [
                 "Active voice",
                 "Passive voice",
                 "Imperative",
                 "Interrogative"
             ], "correct": 1},
        ],
        "Comprehension": [
            {"question": "What does 'verbose' mean?",
             "options": ["Concise", "Using more words than needed", "Silent", "Aggressive"], "correct": 1},
            {"question": "A 'protagonist' in a story is the:",
             "options": ["Villain", "Narrator", "Main character", "Author"], "correct": 2},
            {"question": "Which figure of speech is used in 'The sun smiled down on us'?",
             "options": ["Simile", "Metaphor", "Personification", "Hyperbole"], "correct": 2},
            {"question": "'Ephemeral' means:",
             "options": ["Eternal", "Short-lived", "Bright", "Powerful"], "correct": 1},
            {"question": "Synonym of 'Indolent' is:",
             "options": ["Diligent", "Lazy", "Proud", "Honest"], "correct": 1},
        ],
    },
    "Mathematics": {
        "Algebra": [
            {"question": "If 3x + 6 = 21, then x = ?",
             "options": ["3", "5", "7", "9"], "correct": 1},
            {"question": "The roots of x² - 5x + 6 = 0 are:",
             "options": ["2 and 3", "1 and 6", "-2 and -3", "3 and 4"], "correct": 0},
            {"question": "Simplify: (a + b)² − (a − b)²",
             "options": ["4ab", "2ab", "a² − b²", "0"], "correct": 0},
            {"question": "If log₁₀(100) = x, then x = ?",
             "options": ["1", "2", "10", "100"], "correct": 1},
            {"question": "Sum of first n natural numbers is:",
             "options": ["n(n+1)", "n(n+1)/2", "n²", "n(n-1)/2"], "correct": 1},
        ],
        "Trigonometry": [
            {"question": "sin(90°) = ?",
             "options": ["0", "1", "√2/2", "1/2"], "correct": 1},
            {"question": "cos(0°) = ?",
             "options": ["0", "1", "-1", "undefined"], "correct": 1},
            {"question": "tan(45°) = ?",
             "options": ["0", "√3", "1/√3", "1"], "correct": 3},
            {"question": "sin²θ + cos²θ = ?",
             "options": ["0", "2", "1", "sin2θ"], "correct": 2},
            {"question": "The principal range of arcsin is:",
             "options": ["[0, π]", "[-π/2, π/2]", "(-π, π)", "[0, 2π]"], "correct": 1},
        ],
        "Coordinate Geometry": [
            {"question": "Distance between (0,0) and (3,4) is:",
             "options": ["5", "7", "3", "4"], "correct": 0},
            {"question": "Midpoint of (2,4) and (6,8) is:",
             "options": ["(4,6)", "(3,5)", "(8,12)", "(4,4)"], "correct": 0},
            {"question": "Slope of line y = 3x + 2 is:",
             "options": ["2", "1/3", "3", "-3"], "correct": 2},
            {"question": "Equation of x-axis is:",
             "options": ["x=0", "y=0", "x=y", "x+y=0"], "correct": 1},
            {"question": "Centre of circle x²+y²=25 is:",
             "options": ["(5,5)", "(0,0)", "(5,0)", "(0,5)"], "correct": 1},
        ],
        "Mensuration": [
            {"question": "Area of circle with radius 7 cm (π=22/7):",
             "options": ["144 cm²", "154 cm²", "132 cm²", "164 cm²"], "correct": 1},
            {"question": "Volume of cube with side 4 cm:",
             "options": ["16 cm³", "48 cm³", "64 cm³", "32 cm³"], "correct": 2},
            {"question": "Area of triangle with base 10 and height 6:",
             "options": ["30", "60", "15", "20"], "correct": 0},
            {"question": "Perimeter of rectangle (L=8, B=5):",
             "options": ["40", "26", "13", "20"], "correct": 1},
            {"question": "Lateral surface area of cylinder (r=3, h=7):",
             "options": ["132 cm²", "126 cm²", "110 cm²", "144 cm²"], "correct": 0},
        ],
        "Arithmetic": [
            {"question": "15% of 200 is:",
             "options": ["25", "30", "35", "20"], "correct": 1},
            {"question": "If A can do work in 12 days and B in 6 days, together they finish in:",
             "options": ["4 days", "5 days", "6 days", "9 days"], "correct": 0},
            {"question": "Simple interest on ₹1000 at 5% for 3 years:",
             "options": ["₹100", "₹125", "₹150", "₹175"], "correct": 2},
            {"question": "Speed = Distance/Time. If d=100km, t=2h, speed=?",
             "options": ["40 km/h", "50 km/h", "55 km/h", "60 km/h"], "correct": 1},
            {"question": "LCM of 4 and 6 is:",
             "options": ["6", "12", "24", "2"], "correct": 1},
        ],
    },
    "General Science": {
        "Physics": [
            {"question": "Unit of force in SI system is:",
             "options": ["Joule", "Newton", "Pascal", "Watt"], "correct": 1},
            {"question": "Speed of light in vacuum ≈",
             "options": ["3×10⁸ m/s", "3×10⁶ m/s", "3×10¹⁰ m/s", "3×10⁴ m/s"], "correct": 0},
            {"question": "Which law states F = ma?",
             "options": ["Newton's 1st", "Newton's 2nd", "Newton's 3rd", "Boyle's Law"], "correct": 1},
            {"question": "Ohm's law relates:",
             "options": ["Force and acceleration", "Voltage, current, resistance", "Power and energy", "Mass and velocity"], "correct": 1},
            {"question": "A body in uniform circular motion has:",
             "options": ["Constant velocity", "Zero acceleration", "Centripetal acceleration", "No force acting"], "correct": 2},
        ],
        "Chemistry": [
            {"question": "Atomic number of Carbon is:",
             "options": ["4", "6", "8", "12"], "correct": 1},
            {"question": "Chemical formula of water is:",
             "options": ["HO", "H₂O", "H₂O₂", "OH"], "correct": 1},
            {"question": "pH of pure water at 25°C is:",
             "options": ["5", "6", "7", "8"], "correct": 2},
            {"question": "Which gas is produced when acid reacts with metal?",
             "options": ["Oxygen", "Nitrogen", "Hydrogen", "Carbon dioxide"], "correct": 2},
            {"question": "Valency of Sodium (Na) is:",
             "options": ["1", "2", "3", "0"], "correct": 0},
        ],
        "Biology": [
            {"question": "Powerhouse of the cell is:",
             "options": ["Nucleus", "Ribosome", "Mitochondria", "Lysosome"], "correct": 2},
            {"question": "DNA stands for:",
             "options": [
                 "Deoxyribonucleic Acid",
                 "Diribonucleic Acid",
                 "Deoxyribose Nucleic Acid",
                 "Double Nucleic Acid"
             ], "correct": 0},
            {"question": "Photosynthesis occurs in:",
             "options": ["Mitochondria", "Chloroplast", "Nucleus", "Vacuole"], "correct": 1},
            {"question": "Normal human body temperature is approximately:",
             "options": ["35°C", "36°C", "37°C", "38°C"], "correct": 2},
            {"question": "Which blood group is the universal donor?",
             "options": ["A", "B", "AB", "O"], "correct": 3},
        ],
    },
    "History": {
        "Ancient India": [
            {"question": "The Indus Valley Civilisation is also known as:",
             "options": ["Aryan Civilisation", "Harappan Civilisation", "Vedic Civilisation", "Dravidian Civilisation"], "correct": 1},
            {"question": "Ashoka belonged to which dynasty?",
             "options": ["Gupta", "Maurya", "Nanda", "Kushan"], "correct": 1},
            {"question": "Buddhism was founded by:",
             "options": ["Mahavira", "Chandragupta", "Siddhartha Gautama", "Ashoka"], "correct": 2},
            {"question": "The capital of Mauryan Empire was:",
             "options": ["Taxila", "Pataliputra", "Ujjain", "Vaishali"], "correct": 1},
            {"question": "Who wrote the Arthashastra?",
             "options": ["Aryabhata", "Kautilya", "Kalidasa", "Vatsyayana"], "correct": 1},
        ],
        "Modern India": [
            {"question": "India got independence on:",
             "options": ["26 Jan 1950", "15 Aug 1947", "2 Oct 1947", "14 Aug 1947"], "correct": 1},
            {"question": "First Prime Minister of India:",
             "options": ["Sardar Patel", "Rajendra Prasad", "Jawaharlal Nehru", "B.R. Ambedkar"], "correct": 2},
            {"question": "Indian National Congress was founded in:",
             "options": ["1857", "1885", "1905", "1920"], "correct": 1},
            {"question": "The 'Dandi March' was related to:",
             "options": ["Salt tax", "Land tax", "Freedom of press", "Partition"], "correct": 0},
            {"question": "Who gave the slogan 'Jai Hind'?",
             "options": ["Bhagat Singh", "Subhas Chandra Bose", "Gandhi", "Tilak"], "correct": 1},
        ],
    },
    "Geography": {
        "Physical Geography": [
            {"question": "Longest river in India is:",
             "options": ["Godavari", "Ganga", "Brahmaputra", "Yamuna"], "correct": 1},
            {"question": "The Himalayas are an example of:",
             "options": ["Block mountains", "Fold mountains", "Volcanic mountains", "Residual mountains"], "correct": 1},
            {"question": "Tropic of Cancer passes through how many Indian states?",
             "options": ["6", "7", "8", "9"], "correct": 2},
            {"question": "Largest desert in India is:",
             "options": ["Deccan", "Rann of Kutch", "Thar", "None"], "correct": 2},
            {"question": "Which ocean is the smallest?",
             "options": ["Pacific", "Atlantic", "Indian", "Arctic"], "correct": 3},
        ],
        "World Geography": [
            {"question": "Largest continent is:",
             "options": ["Africa", "North America", "Asia", "Europe"], "correct": 2},
            {"question": "Amazon river flows through:",
             "options": ["Argentina", "Brazil", "Chile", "Colombia"], "correct": 1},
            {"question": "Mount Everest is in which country?",
             "options": ["India", "Tibet", "Nepal", "Bhutan"], "correct": 2},
            {"question": "Prime Meridian passes through:",
             "options": ["Paris", "London (Greenwich)", "New York", "Berlin"], "correct": 1},
            {"question": "Sahara desert is in which continent?",
             "options": ["Asia", "Australia", "Africa", "South America"], "correct": 2},
        ],
    },
    "Economics": {
        "Microeconomics": [
            {"question": "Law of demand states that price and demand are:",
             "options": ["Directly related", "Inversely related", "Unrelated", "Equal"], "correct": 1},
            {"question": "When supply increases and demand is constant, price:",
             "options": ["Increases", "Decreases", "Stays same", "Doubles"], "correct": 1},
            {"question": "GDP stands for:",
             "options": [
                 "Gross Domestic Product",
                 "General Domestic Production",
                 "Gross Direct Product",
                 "Global Domestic Product"
             ], "correct": 0},
            {"question": "Perfect competition has how many sellers?",
             "options": ["One", "Few", "Many", "Two"], "correct": 2},
            {"question": "Consumer surplus is:",
             "options": [
                 "Extra supply by producers",
                 "Difference between willingness to pay and actual price",
                 "Government subsidy",
                 "Tax on consumers"
             ], "correct": 1},
        ],
        "Macroeconomics": [
            {"question": "RBI is India's:",
             "options": ["Investment bank", "Central bank", "Commercial bank", "Development bank"], "correct": 1},
            {"question": "Inflation means:",
             "options": [
                 "Rise in GDP",
                 "General rise in price levels",
                 "Increase in exports",
                 "Fall in interest rates"
             ], "correct": 1},
            {"question": "Fiscal policy deals with:",
             "options": ["Interest rates", "Money supply", "Government revenue and expenditure", "Exchange rates"], "correct": 2},
            {"question": "India's financial year is:",
             "options": ["Jan–Dec", "Apr–Mar", "Jul–Jun", "Oct–Sep"], "correct": 1},
            {"question": "Which body presents Union Budget in India?",
             "options": ["RBI", "SEBI", "Finance Ministry", "Planning Commission"], "correct": 2},
        ],
    },
}

CHAPTERS = {
    "English": ["Grammar", "Comprehension"],
    "Mathematics": ["Algebra", "Trigonometry", "Coordinate Geometry", "Mensuration", "Arithmetic"],
    "General Science": ["Physics", "Chemistry", "Biology"],
    "History": ["Ancient India", "Modern India"],
    "Geography": ["Physical Geography", "World Geography"],
    "Economics": ["Microeconomics", "Macroeconomics"],
}

SUBJECTS = list(QUESTION_BANK.keys())

# ─────────────────────────────────────────────
# SESSION STATE INITIALISATION
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "page": "landing",          # landing | dashboard | mode_select | test | results
        "name": "",
        "email": "",
        "course": "NDA",
        "results": [],              # list of result dicts
        "current_subject": None,
        "current_chapter": None,
        "current_mode": None,       # "chapter" | "full"
        "questions": [],
        "answers": {},
        "test_start": None,
        "test_duration": 1200,      # seconds
        "test_done": False,
        "last_result": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ─────────────────────────────────────────────
# QUESTION FETCHING (web + fallback)
# ─────────────────────────────────────────────
def fetch_opentdb_questions(category_id: int = 17, amount: int = 10) -> list:
    """Fetch from OpenTDB API (category 17 = Science & Nature)."""
    try:
        url = f"https://opentdb.com/api.php?amount={amount}&category={category_id}&type=multiple"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("response_code") != 0:
            return []
        questions = []
        for item in data["results"]:
            q = html.unescape(item["question"])
            correct = html.unescape(item["correct_answer"])
            incorrect = [html.unescape(x) for x in item["incorrect_answers"]]
            options = incorrect + [correct]
            random.shuffle(options)
            correct_idx = options.index(correct)
            questions.append({"question": q, "options": options, "correct": correct_idx})
        return questions
    except Exception:
        return []

def get_questions(subject: str, chapter: str = None, mode: str = "chapter") -> list:
    """Return questions: try web, fallback to hardcoded bank."""
    questions = []
    # Try OpenTDB for General Science
    if subject == "General Science" and mode == "full":
        questions = fetch_opentdb_questions(category_id=17, amount=15)

    if not questions:
        # Use hardcoded bank
        if chapter and chapter in QUESTION_BANK.get(subject, {}):
            pool = QUESTION_BANK[subject][chapter]
        else:
            # Collect all chapters of subject
            pool = []
            for ch_qs in QUESTION_BANK.get(subject, {}).values():
                pool.extend(ch_qs)

        k = 10 if mode == "chapter" else min(20, len(pool))
        questions = random.sample(pool, min(k, len(pool)))

    return questions

# ─────────────────────────────────────────────
# PAGE: LANDING
# ─────────────────────────────────────────────
def page_landing():
    # Initialize selected course in session state
    if "selected_course" not in st.session_state:
        st.session_state.selected_course = "NDA"

    # ── Hero section ──
    st.markdown("""
    <div style="text-align:center; padding: 2.5rem 0 0.5rem;">
        <div style="display:inline-block; background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.25);
                    border-radius:999px; padding:0.35rem 1.2rem; font-size:0.85rem; font-weight:600;
                    color:rgba(255,255,255,0.85); letter-spacing:0.08em; margin-bottom:1rem;">
            🎖️ DEFENCE EXAM PREPARATION
        </div>
        <div style="font-family:'Poppins',sans-serif; font-size:4.2rem; font-weight:800; color:white;
                    text-shadow: 0 4px 32px rgba(0,0,0,0.35); letter-spacing:-2px; line-height:1.05;">
            Grade<span style="color:#a8d8ff; text-shadow:0 0 40px rgba(168,216,255,0.5);">UP</span>
        </div>
        <div style="color:rgba(255,255,255,0.75); font-size:1.05rem; margin-top:0.6rem; font-weight:400;
                    max-width:420px; margin-left:auto; margin-right:auto; line-height:1.6;">
            Your premium platform to crack <strong style="color:white;">NDA, CDS</strong> &amp; other defence exams
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats strip ──
    st.markdown("""
    <div style="display:flex; justify-content:center; gap:2.5rem; margin:1.4rem 0 2rem;
                flex-wrap:wrap;">
        <div style="text-align:center;">
            <div style="font-size:1.6rem; font-weight:800; color:#a8d8ff;">6</div>
            <div style="font-size:0.78rem; color:rgba(255,255,255,0.6); margin-top:0.1rem;">Subjects</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:1.6rem; font-weight:800; color:#a8d8ff;">200+</div>
            <div style="font-size:0.78rem; color:rgba(255,255,255,0.6); margin-top:0.1rem;">Questions</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:1.6rem; font-weight:800; color:#a8d8ff;">3</div>
            <div style="font-size:0.78rem; color:rgba(255,255,255,0.6); margin-top:0.1rem;">Exam Tracks</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Form card ──
    lcol, mcol, rcol = st.columns([1, 2, 1])
    with mcol:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.13); backdrop-filter:blur(20px);
                    border:1px solid rgba(255,255,255,0.22); border-radius:28px;
                    padding:2rem 2rem 1.5rem; box-shadow:0 16px 48px rgba(0,0,0,0.25);">
            <div style="font-size:1.15rem; font-weight:700; color:white; margin-bottom:1.4rem;
                        text-align:center; letter-spacing:0.02em;">✨ Create Your Profile</div>
        </div>
        """, unsafe_allow_html=True)

        # Name input
        st.markdown('<p style="color:rgba(255,255,255,0.85); font-weight:600; font-size:0.9rem; margin:0 0 0.25rem 0.2rem;">👤 Full Name</p>', unsafe_allow_html=True)
        name = st.text_input("Full Name", placeholder="e.g. Arjun Sharma", label_visibility="collapsed", key="inp_name")

        # Email input
        st.markdown('<p style="color:rgba(255,255,255,0.85); font-weight:600; font-size:0.9rem; margin:0.8rem 0 0.25rem 0.2rem;">📧 Email Address</p>', unsafe_allow_html=True)
        email = st.text_input("Email Address", placeholder="you@example.com", label_visibility="collapsed", key="inp_email")

        # Course selector — pill buttons
        st.markdown('<p style="color:rgba(255,255,255,0.85); font-weight:600; font-size:0.9rem; margin:0.8rem 0 0.5rem 0.2rem;">🎯 Select Your Course</p>', unsafe_allow_html=True)

        course_options = ["NDA", "CDS", "Other"]
        course_icons  = {"NDA": "⚔️", "CDS": "🛡️", "Other": "📚"}
        c1, c2, c3 = st.columns(3)
        for col, opt in zip([c1, c2, c3], course_options):
            is_selected = st.session_state.selected_course == opt
            with col:
                btn_style = (
                    "background:rgba(168,216,255,0.35) !important; "
                    "border:2px solid rgba(168,216,255,0.8) !important; "
                    "color:white !important; font-weight:700 !important;"
                ) if is_selected else (
                    "background:rgba(255,255,255,0.10) !important; "
                    "border:1px solid rgba(255,255,255,0.22) !important; "
                    "color:rgba(255,255,255,0.7) !important;"
                )
                st.markdown(f"""
                <style>
                div[data-testid="stButton"] > button[kind="secondary"]#{opt.lower()}-btn {{
                    {btn_style}
                }}
                </style>
                """, unsafe_allow_html=True)
                if st.button(f"{course_icons[opt]} {opt}", key=f"course_{opt}", use_container_width=True):
                    st.session_state.selected_course = opt
                    st.rerun()

        # Show selected badge
        sel = st.session_state.selected_course
        st.markdown(f"""
        <div style="text-align:center; margin:0.6rem 0 1rem;">
            <span style="background:rgba(168,216,255,0.25); border:1px solid rgba(168,216,255,0.5);
                         border-radius:999px; padding:0.25rem 1rem; font-size:0.85rem;
                         font-weight:600; color:#a8d8ff;">
                ✓ {sel} selected
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Submit button
        if st.button("🚀  Begin Your Journey", use_container_width=True, key="btn_submit"):
            if not name.strip():
                st.error("Please enter your name.")
            elif not email.strip() or "@" not in email:
                st.error("Please enter a valid email.")
            else:
                st.session_state.name  = name.strip()
                st.session_state.email = email.strip()
                st.session_state.course = st.session_state.selected_course
                st.session_state.page  = "dashboard"
                st.rerun()

        # Made with love — below submit
        st.markdown(
            '<div class="login-love">Made with love ❤️ for NAUSHERA</div>',
            unsafe_allow_html=True
        )

    st.markdown(WATERMARK, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR (dashboard + inner pages)
# ─────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding:1rem 0;">
            <div style="font-size:2.2rem; font-weight:800; color:white; font-family:'Poppins',sans-serif;">
                Grade<span style="color:#a8d8ff;">UP</span>
            </div>
            <hr style="border-color:rgba(255,255,255,0.2); margin:0.8rem 0;">
            <div style="font-size:1.1rem; font-weight:700; color:white;">👤 {st.session_state.name}</div>
            <div style="font-size:0.85rem; color:rgba(255,255,255,0.7); margin-top:0.2rem;">
                {st.session_state.email}
            </div>
            <div style="margin-top:0.6rem;">
                <span style="background:rgba(255,255,255,0.2); border-radius:999px; padding:0.3rem 1rem;
                             font-size:0.85rem; font-weight:600; color:white;">
                    🎯 {st.session_state.course}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        results = st.session_state.results
        if results:
            total_tests = len(results)
            avg_score = sum(r["percentage"] for r in results) / total_tests
            best = max(results, key=lambda r: r["percentage"])
            st.markdown(f"""
            <div style="text-align:center; padding:0.5rem 0;">
                <div style="color:rgba(255,255,255,0.7); font-size:0.8rem;">Tests Taken</div>
                <div style="font-size:1.8rem; font-weight:700; color:white;">{total_tests}</div>
                <div style="color:rgba(255,255,255,0.7); font-size:0.8rem; margin-top:0.5rem;">Avg Score</div>
                <div style="font-size:1.5rem; font-weight:700; color:#a8d8ff;">{avg_score:.1f}%</div>
                <div style="color:rgba(255,255,255,0.7); font-size:0.8rem; margin-top:0.5rem;">Best Subject</div>
                <div style="font-size:1rem; font-weight:600; color:#7fffb0;">{best['subject']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        if st.button("🏅 Leaderboard", use_container_width=True):
            st.session_state.page = "leaderboard"
            st.rerun()
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ─────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────
def page_dashboard():
    render_sidebar()
    st.markdown(f"""
    <h1 style="font-size:2.4rem; margin-bottom:0.3rem;">
        Welcome back, {st.session_state.name}! 👋
    </h1>
    <p style="color:rgba(255,255,255,0.7); font-size:1rem; margin-bottom:1.5rem;">
        Choose a subject to practice or take a mock test.
    </p>
    """, unsafe_allow_html=True)

    # Subject tiles
    st.markdown("### 📚 Select a Subject")
    cols = st.columns(3)
    icons = {"English": "📝", "Mathematics": "📐", "General Science": "🔬",
             "History": "🏛️", "Geography": "🌏", "Economics": "💹"}
    for i, subject in enumerate(SUBJECTS):
        with cols[i % 3]:
            if st.button(f"{icons.get(subject, '📖')}  {subject}", use_container_width=True, key=f"sub_{subject}"):
                st.session_state.current_subject = subject
                st.session_state.page = "mode_select"
                st.rerun()

    # Performance Analysis
    st.markdown("---")
    st.markdown("### 📊 Performance Analysis")

    results = st.session_state.results
    if not results:
        st.info("No tests taken yet. Start a test to see your performance here!")
    else:
        df = pd.DataFrame(results)
        total_tests = len(df)
        avg_score = df["percentage"].mean()
        best_subj = df.groupby("subject")["percentage"].mean().idxmax()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div style="text-align:center; background:rgba(255,255,255,0.1);
                        border-radius:24px; padding:1.2rem; border:1px solid rgba(255,255,255,0.2);">
                <div style="font-size:2.5rem; font-weight:800; color:white;">{total_tests}</div>
                <div style="color:rgba(255,255,255,0.7); font-size:0.9rem;">Tests Taken</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div style="text-align:center; background:rgba(255,255,255,0.1);
                        border-radius:24px; padding:1.2rem; border:1px solid rgba(255,255,255,0.2);">
                <div style="font-size:2.5rem; font-weight:800; color:#a8d8ff;">{avg_score:.1f}%</div>
                <div style="color:rgba(255,255,255,0.7); font-size:0.9rem;">Average Score</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div style="text-align:center; background:rgba(255,255,255,0.1);
                        border-radius:24px; padding:1.2rem; border:1px solid rgba(255,255,255,0.2);">
                <div style="font-size:1.5rem; font-weight:800; color:#7fffb0;">{best_subj}</div>
                <div style="color:rgba(255,255,255,0.7); font-size:0.9rem;">Best Subject</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Line chart: score trend
        df["test_num"] = range(1, len(df) + 1)
        line = alt.Chart(df).mark_line(point=True, color="#a8d8ff", strokeWidth=2.5).encode(
            x=alt.X("test_num:Q", title="Test #", axis=alt.Axis(labelColor="white", titleColor="white")),
            y=alt.Y("percentage:Q", title="Score %", scale=alt.Scale(domain=[0, 100]),
                    axis=alt.Axis(labelColor="white", titleColor="white")),
            tooltip=["test_num", "subject", "mode", "percentage"]
        ).properties(
            title=alt.TitleParams("Score Trend Over Time", color="white"),
            background="transparent",
            height=220,
        ).configure_view(strokeWidth=0)
        st.altair_chart(line, use_container_width=True)

        # Bar chart: subject-wise average
        sub_df = df.groupby("subject")["percentage"].mean().reset_index()
        sub_df.columns = ["Subject", "Average %"]
        bar = alt.Chart(sub_df).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, color="#667eea").encode(
            x=alt.X("Subject:N", axis=alt.Axis(labelColor="white", titleColor="white")),
            y=alt.Y("Average %:Q", scale=alt.Scale(domain=[0, 100]),
                    axis=alt.Axis(labelColor="white", titleColor="white")),
            tooltip=["Subject", "Average %"]
        ).properties(
            title=alt.TitleParams("Subject-wise Performance", color="white"),
            background="transparent",
            height=220,
        ).configure_view(strokeWidth=0)
        st.altair_chart(bar, use_container_width=True)

    st.markdown(WATERMARK, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE: MODE SELECT
# ─────────────────────────────────────────────
def page_mode_select():
    render_sidebar()
    subject = st.session_state.current_subject
    st.markdown(f"<h2>📖 {subject}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.8);'>Choose how you'd like to practise today:</p>",
                unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.22);
                    border-radius:28px; padding:2rem; text-align:center; min-height:160px;">
            <div style="font-size:2.5rem;">📋</div>
            <div style="font-size:1.2rem; font-weight:700; color:white; margin-top:0.5rem;">
                Chapter-wise Practice
            </div>
            <div style="color:rgba(255,255,255,0.65); font-size:0.88rem; margin-top:0.4rem;">
                Focus on one topic at a time · 20 min · 10 Qs
            </div>
        </div>""", unsafe_allow_html=True)
        if st.button("Start Chapter Test", key="btn_chapter", use_container_width=True):
            st.session_state.current_mode = "chapter"
            st.session_state.page = "chapter_select"
            st.rerun()

    with col2:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.22);
                    border-radius:28px; padding:2rem; text-align:center; min-height:160px;">
            <div style="font-size:2.5rem;">🏆</div>
            <div style="font-size:1.2rem; font-weight:700; color:white; margin-top:0.5rem;">
                Full Subject Mock Test
            </div>
            <div style="color:rgba(255,255,255,0.65); font-size:0.88rem; margin-top:0.4rem;">
                Comprehensive coverage · 60 min · 20 Qs
            </div>
        </div>""", unsafe_allow_html=True)
        if st.button("Start Full Mock Test", key="btn_full", use_container_width=True):
            st.session_state.current_mode = "full"
            st.session_state.current_chapter = None
            qs = get_questions(subject, chapter=None, mode="full")
            st.session_state.questions = qs
            st.session_state.answers = {}
            st.session_state.test_start = time.time()
            st.session_state.test_duration = 3600
            st.session_state.test_done = False
            st.session_state.page = "test"
            st.rerun()

    if st.button("← Back to Dashboard", key="back_dash"):
        st.session_state.page = "dashboard"
        st.rerun()

    st.markdown(WATERMARK, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE: CHAPTER SELECT
# ─────────────────────────────────────────────
def page_chapter_select():
    render_sidebar()
    subject = st.session_state.current_subject
    st.markdown(f"<h2>📑 Choose a Chapter — {subject}</h2>", unsafe_allow_html=True)

    chapters = CHAPTERS.get(subject, [])
    chapter = st.selectbox("Select Chapter", chapters)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶️  Begin Chapter Test", use_container_width=True):
            st.session_state.current_chapter = chapter
            qs = get_questions(subject, chapter=chapter, mode="chapter")
            st.session_state.questions = qs
            st.session_state.answers = {}
            st.session_state.test_start = time.time()
            st.session_state.test_duration = 1200  # 20 min
            st.session_state.test_done = False
            st.session_state.page = "test"
            st.rerun()

    if st.button("← Back"):
        st.session_state.page = "mode_select"
        st.rerun()

    st.markdown(WATERMARK, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE: TEST
# ─────────────────────────────────────────────
def page_test():
    render_sidebar()
    subject = st.session_state.current_subject
    chapter = st.session_state.current_chapter
    mode = st.session_state.current_mode
    questions = st.session_state.questions
    duration = st.session_state.test_duration
    elapsed = time.time() - st.session_state.test_start
    remaining = max(0, duration - elapsed)

    if remaining == 0 and not st.session_state.test_done:
        st.session_state.test_done = True
        _save_result()
        st.session_state.page = "results"
        st.rerun()

    # Timer display
    mins = int(remaining // 60)
    secs = int(remaining % 60)
    timer_color = "rgba(255,80,80,0.4)" if remaining < 120 else "rgba(255,255,255,0.18)"
    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem;">
        <div>
            <h2 style="margin:0;">{subject} {'— ' + chapter if chapter else '(Full Mock)'}</h2>
            <span style="color:rgba(255,255,255,0.6); font-size:0.9rem;">
                {mode.capitalize()} Test · {len(questions)} Questions
            </span>
        </div>
        <div style="background:{timer_color}; border:1px solid rgba(255,255,255,0.3);
                    border-radius:999px; padding:0.5rem 1.4rem; font-size:1.2rem;
                    font-weight:700; color:white; backdrop-filter:blur(8px);">
            ⏱️ {mins:02d}:{secs:02d}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Questions form
    with st.form("test_form"):
        for i, q in enumerate(questions):
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.1); border-radius:20px; padding:1rem 1.2rem;
                        border:1px solid rgba(255,255,255,0.18); margin-bottom:0.5rem;">
                <span style="color:rgba(255,255,255,0.6); font-size:0.85rem;">Q{i+1} / {len(questions)}</span><br>
                <span style="font-size:1rem; font-weight:600; color:white;">{q['question']}</span>
            </div>""", unsafe_allow_html=True)

            chosen = st.radio(
                label=f"q{i}",
                options=q["options"],
                index=None,
                key=f"radio_{i}",
                label_visibility="collapsed"
            )
            st.session_state.answers[i] = chosen
            st.markdown("<br>", unsafe_allow_html=True)

        submitted = st.form_submit_button("✅  Submit Test", use_container_width=True)

    if submitted:
        # Capture radio values from session_state
        for i in range(len(questions)):
            key = f"radio_{i}"
            if key in st.session_state:
                st.session_state.answers[i] = st.session_state[key]
        _save_result()
        st.session_state.page = "results"
        st.rerun()

    # Auto-refresh for timer
    time.sleep(0.1)
    st.rerun()

def _save_result():
    """Calculate score, push to session results list, and persist to DB."""
    questions = st.session_state.questions
    answers = st.session_state.answers
    score = 0
    for i, q in enumerate(questions):
        chosen = answers.get(i)
        if chosen is not None and chosen == q["options"][q["correct"]]:
            score += 1
    total = len(questions)
    pct = round(score / total * 100, 1) if total else 0
    elapsed = time.time() - st.session_state.test_start
    result = {
        "date": datetime.datetime.now().strftime("%d %b %Y %H:%M"),
        "subject": st.session_state.current_subject,
        "chapter": st.session_state.current_chapter or "Full",
        "mode": st.session_state.current_mode,
        "score": score,
        "total": total,
        "percentage": pct,
        "time_taken": int(elapsed),
        "answers": dict(answers),
    }
    st.session_state.results.append(result)
    st.session_state.last_result = result
    # ── Persist to SQLite ──
    try:
        db_save_result(result, st.session_state.name, st.session_state.email, st.session_state.course)
    except Exception:
        pass  # Don't crash if DB write fails

# ─────────────────────────────────────────────
# PAGE: RESULTS
# ─────────────────────────────────────────────
def page_results():
    render_sidebar()
    r = st.session_state.last_result
    if not r:
        st.session_state.page = "dashboard"
        st.rerun()

    score = r["score"]
    total = r["total"]
    pct = r["percentage"]
    elapsed = r["time_taken"]
    mins_taken = elapsed // 60
    secs_taken = elapsed % 60

    emoji = "🏆" if pct >= 80 else "👍" if pct >= 50 else "📚"
    color = "#7fffb0" if pct >= 80 else "#ffd97d" if pct >= 50 else "#ff9090"

    st.markdown(f"""
    <div style="text-align:center; background:rgba(255,255,255,0.14); border-radius:32px;
                border:1px solid rgba(255,255,255,0.22); padding:2.5rem; margin-bottom:1.5rem;">
        <div style="font-size:4rem;">{emoji}</div>
        <div style="font-size:3.5rem; font-weight:800; color:{color}; line-height:1.1;">
            {score}/{total}
        </div>
        <div style="font-size:2rem; font-weight:700; color:white; margin-top:0.3rem;">{pct}%</div>
        <div style="color:rgba(255,255,255,0.7); margin-top:0.5rem;">
            {r['subject']} · {r['chapter']} · ⏱️ {mins_taken}m {secs_taken}s
        </div>
        <div style="color:rgba(255,255,255,0.6); font-size:0.85rem; margin-top:0.3rem;">{r['date']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Answer review
    st.markdown("### 📋 Answer Review")
    questions = st.session_state.questions
    user_answers = r["answers"]
    for i, q in enumerate(questions):
        user_ans = user_answers.get(i)
        correct_ans = q["options"][q["correct"]]
        is_correct = user_ans == correct_ans
        icon = "✅" if is_correct else "❌"
        ans_color = "#7fffb0" if is_correct else "#ff9090"

        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.10); border-radius:20px; padding:1rem 1.2rem;
                    border:1px solid rgba(255,255,255,0.15); margin-bottom:0.7rem;">
            <div style="font-weight:600; color:white; margin-bottom:0.4rem;">{icon} Q{i+1}: {q['question']}</div>
            <div style="font-size:0.9rem; color:{ans_color};">
                Your answer: {user_ans if user_ans else 'Not answered'}
            </div>
            {"" if is_correct else f'<div style="font-size:0.9rem; color:#7fffb0;">Correct: {correct_ans}</div>'}
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Back to Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
    with col2:
        if st.button("🔄 Retry Same Subject", use_container_width=True):
            st.session_state.page = "mode_select"
            st.rerun()

    st.markdown(WATERMARK, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE: LEADERBOARD
# ─────────────────────────────────────────────
def page_leaderboard():
    # Guard — must be logged in
    if not st.session_state.get("name", "").strip():
        st.session_state.page = "landing"
        st.rerun()

    render_sidebar()
    st.markdown("<h2>🏅 Leaderboard — Top Scores</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.75);'>Scores are saved from all sessions. Ranked by % score, then fastest time.</p>", unsafe_allow_html=True)

    rows = db_get_leaderboard(limit=20)

    if not rows:
        st.markdown("""
        <div style="text-align:center; background:rgba(255,255,255,0.1); border-radius:24px;
                    padding:2.5rem; border:1px solid rgba(255,255,255,0.18);">
            <div style="font-size:3rem;">🏆</div>
            <div style="color:white; font-size:1.2rem; font-weight:600; margin-top:0.8rem;">
                No results yet!
            </div>
            <div style="color:rgba(255,255,255,0.65); margin-top:0.4rem;">
                Be the first to complete a test and claim the top spot.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        medals = ["🥇", "🥈", "🥉"]
        for idx, row in enumerate(rows):
            name, course, subject, chapter, score, total, pct, date = row
            medal = medals[idx] if idx < 3 else f"#{idx+1}"
            bar_color = "#7fffb0" if pct >= 80 else "#ffd97d" if pct >= 50 else "#ff9090"
            mins_taken = ""  # time_taken not fetched here for brevity
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:1.2rem;
                        background:rgba(255,255,255,{'0.22' if idx < 3 else '0.10'});
                        border:1px solid rgba(255,255,255,{'0.3' if idx < 3 else '0.15'});
                        border-radius:20px; padding:1rem 1.4rem; margin-bottom:0.7rem;">
                <div style="font-size:{'2rem' if idx < 3 else '1.3rem'}; min-width:2.5rem; text-align:center;">
                    {medal}
                </div>
                <div style="flex:1;">
                    <div style="font-weight:700; color:white; font-size:1.05rem;">{name}
                        <span style="font-size:0.78rem; color:rgba(255,255,255,0.55); font-weight:400; margin-left:0.5rem;">{course}</span>
                    </div>
                    <div style="color:rgba(255,255,255,0.65); font-size:0.85rem; margin-top:0.15rem;">
                        {subject} · {chapter}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.6rem; font-weight:800; color:{bar_color}; line-height:1;">{pct}%</div>
                    <div style="color:rgba(255,255,255,0.55); font-size:0.8rem;">{score}/{total} · {date}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()

    st.markdown(WATERMARK, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="GradeUP – Defence Exam Prep",
        page_icon="🎖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    init_db()
    init_state()

    page = st.session_state.page
    if page == "landing":
        page_landing()
    elif page == "dashboard":
        page_dashboard()
    elif page == "mode_select":
        page_mode_select()
    elif page == "chapter_select":
        page_chapter_select()
    elif page == "test":
        page_test()
    elif page == "results":
        page_results()
    elif page == "leaderboard":
        page_leaderboard()
    else:
        st.session_state.page = "landing"
        st.rerun()

main()
