"""
GradeUP — Premium Defence Exam Preparation Platform (v2)
Enhanced with: harder PYQ-level questions, negative marking, animated background,
mobile responsiveness, user persistence via SQLite, and improved UI.
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
# DATABASE — SQLite for user persistence
# ─────────────────────────────────────────────
DB_PATH = "gradeup_users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name  TEXT NOT NULL,
            course TEXT NOT NULL,
            registered_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_user(name, email, course):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (email, name, course, registered_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET name=excluded.name, course=excluded.course
    """, (email, name, course, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def load_user(email):
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, course FROM users WHERE email=?", (email,))
    row = c.fetchone()
    conn.close()
    return row

def delete_user(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE email=?", (email,))
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
# GLOBAL CSS — animated BG + glass + mobile
# ─────────────────────────────────────────────
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

/* Animated defence-themed gradient — shifts every 18s */
@keyframes bgShift {
    0%   { background-position: 0%   50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0%   50%; }
}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 25%, #2c5364 50%, #1a3a5c 75%, #0f2027 100%);
    background-size: 300% 300%;
    animation: bgShift 18s ease infinite;
    background-attachment: fixed;
    min-height: 100vh;
}

/* Subtle radial texture overlay */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse at 20% 20%, rgba(255,255,255,0.03) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 80%, rgba(100,180,255,0.04) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
}

.stApp > header { background: transparent !important; }

section[data-testid="stSidebar"] {
    background: rgba(15,32,39,0.55) !important;
    backdrop-filter: blur(18px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(18px) saturate(180%) !important;
    border-right: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 0 32px 32px 0 !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.35) !important;
}

.block-container {
    background: rgba(255,255,255,0.09) !important;
    backdrop-filter: blur(18px) saturate(160%) !important;
    -webkit-backdrop-filter: blur(18px) saturate(160%) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    border-radius: 28px !important;
    box-shadow: 0 8px 40px rgba(0,0,0,0.3) !important;
    padding: 2rem !important;
    margin: 1rem auto !important;
    max-width: 1100px !important;
}

.stButton > button {
    background: linear-gradient(135deg, rgba(44,83,100,0.6), rgba(32,58,67,0.7)) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
    border-radius: 999px !important;
    color: white !important;
    font-weight: 600 !important;
    font-family: 'Poppins', sans-serif !important;
    padding: 0.7rem 1.8rem !important;
    transition: all 0.3s ease !important;
    min-height: 44px !important;
}
.stButton > button:hover {
    transform: translateY(-2px) scale(1.02) !important;
    background: linear-gradient(135deg, rgba(60,120,150,0.75), rgba(44,83,100,0.85)) !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
}

input, select, textarea {
    background: rgba(255,255,255,0.12) !important;
    border-radius: 20px !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    color: white !important;
    font-family: 'Poppins', sans-serif !important;
    min-height: 44px !important;
}
.stRadio > div > label {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: white !important;
    padding: 0.7rem 1rem !important;
    margin: 0.2rem 0 !important;
    transition: background 0.2s !important;
    min-height: 44px !important;
    display: flex !important;
    align-items: center !important;
    cursor: pointer !important;
}
.stRadio > div > label:hover { background: rgba(255,255,255,0.18) !important; }
.stSelectbox > div > div {
    background: rgba(255,255,255,0.12) !important;
    border-radius: 20px !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    color: white !important;
}

h1, h2, h3, h4 { color: white !important; font-family: 'Poppins', sans-serif !important; }
p, label, div, span, li { font-family: 'Poppins', sans-serif; color: rgba(255,255,255,0.9); }
hr { border-color: rgba(255,255,255,0.18) !important; }
footer { visibility: hidden !important; }

.watermark {
    text-align: center;
    color: rgba(255,255,255,0.4);
    font-size: 13px;
    font-family: 'Poppins', sans-serif;
    padding: 2rem 0 1rem;
}

.marking-note {
    background: rgba(255,200,50,0.1);
    border: 1px solid rgba(255,200,50,0.25);
    border-radius: 16px;
    padding: 0.6rem 1.1rem;
    font-size: 0.82rem;
    color: #ffe97d;
    margin-bottom: 1rem;
}
.q-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
}
.diff-badge {
    display: inline-block;
    border-radius: 999px;
    padding: 0.12rem 0.65rem;
    font-size: 0.7rem;
    font-weight: 700;
    margin-left: 0.4rem;
    vertical-align: middle;
}
.diff-hard   { background: rgba(255,80,80,0.25);  color:#ffaaaa; border:1px solid rgba(255,80,80,0.35); }
.diff-medium { background: rgba(255,200,50,0.2);  color:#ffe97d; border:1px solid rgba(255,200,50,0.3); }

/* Mobile responsive overrides */
@media (max-width: 768px) {
    .block-container {
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border-radius: 18px !important;
        padding: 1rem !important;
        margin: 0.4rem !important;
    }
    section[data-testid="stSidebar"] {
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border-radius: 0 18px 18px 0 !important;
    }
    .stButton > button { width: 100% !important; min-height: 50px !important; font-size: 1rem !important; }
    input, select, textarea { font-size: 16px !important; border-radius: 14px !important; }
    h1 { font-size: 1.7rem !important; }
    h2 { font-size: 1.3rem !important; }
}
@media (max-width: 480px) {
    .block-container { border-radius: 14px !important; padding: 0.7rem !important; }
}
</style>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
"""

WATERMARK = '<div class="watermark">Made with love ❤️ for NAUSHERA</div>'

# ─────────────────────────────────────────────
# NEGATIVE MARKING — NDA/CDS pattern
# ─────────────────────────────────────────────
CORRECT_MARKS = 4
WRONG_MARKS   = -1.33

# ─────────────────────────────────────────────
# QUESTION BANK — PYQ-level difficulty
# ─────────────────────────────────────────────
def _q(q, opts, c, diff="Hard", exp=""):
    return {"question": q, "options": opts, "correct": c, "difficulty": diff, "explanation": exp}

QUESTION_BANK = {

"English": {
"Grammar": [
    _q("Choose the grammatically correct sentence:",
       ["Neither of the students have submitted their assignments.",
        "Each of the boys were given a prize.",
        "The committee has announced its decision.",
        "The jury have given their verdict unanimously."],
       2, "Hard", "'Committee' is a collective noun taking singular verb 'has'."),
    _q("Select the correctly punctuated sentence:",
       ["The book, which I bought yesterday is torn.",
        "The book which I bought yesterday, is torn.",
        "The book, which I bought yesterday, is torn.",
        "The book which I bought, yesterday is torn."],
       2, "Hard", "Non-defining relative clause requires commas on both sides."),
    _q("Identify the sentence in the subjunctive mood:",
       ["If he studies hard, he will pass.",
        "I wish he were here right now.",
        "She is taller than her brother.",
        "He has been working for hours."],
       1, "Hard", "'Were' (not 'was') signals subjunctive mood after 'wish'."),
    _q("Fill in: 'The news ___ very disturbing.'",
       ["are", "were", "have been", "is"],
       3, "Medium", "'News' is uncountable; always takes singular verb."),
    _q("Indirect speech of: 'He said, \"I am going to Delhi tomorrow.\"'",
       ["He said that he was going to Delhi the next day.",
        "He said that he is going to Delhi tomorrow.",
        "He said that he had gone to Delhi the next day.",
        "He said that he will go to Delhi tomorrow."],
       0, "Hard", "Past tense; 'tomorrow' → 'the next day'."),
    _q("'Sine qua non' means:",
       ["A formal apology", "An indispensable condition", "Without any cause", "A surplus requirement"],
       1, "Hard", "Latin: 'without which not' — an essential condition."),
    _q("Which sentence uses the gerund correctly?",
       ["He enjoys to swim every morning.",
        "She is looking forward to meet you.",
        "They admitted stealing the money.",
        "I suggested him to leave early."],
       2, "Hard", "'Admit' is followed by gerund (-ing form)."),
    _q("'Perspicacious' means:",
       ["Sweating profusely", "Having ready insight", "Lacking clarity", "Being extremely stubborn"],
       1, "Hard"),
    _q("Correct subject-verb agreement:",
       ["Neither the teacher nor the students was present.",
        "Either the boys or the girl have done it.",
        "Either the manager or the employees are responsible.",
        "Neither the boys nor the girl are absent."],
       2, "Hard", "Verb agrees with the nearest subject ('employees' → plural 'are')."),
    _q("'He turned a blind eye to corruption.' This means:",
       ["He was visually impaired.", "He deliberately ignored it.",
        "He opposed corruption.", "He investigated corruption."],
       1, "Medium"),
    _q("Identify the misplaced modifier: 'Walking down the street, the trees looked beautiful.'",
       ["'Walking' is the misplaced modifier.", "'Trees' is misplaced.",
        "'Beautiful' is misplaced.", "There is no error."],
       0, "Hard", "The participial phrase must refer to the subject — trees cannot walk."),
    _q("Which is an example of oxymoron?",
       ["As brave as a lion", "The child is father of the man",
        "Deafening silence", "Time is money"],
       2, "Medium"),
    _q("Antonym of 'Taciturn':",
       ["Reticent", "Loquacious", "Morose", "Sullen"],
       1, "Medium"),
    _q("Fill in: 'It is time we ___ a decision.'",
       ["make", "made", "have made", "will make"],
       1, "Hard", "'It is time + subject + past tense' is a subjunctive construction."),
    _q("Correct version of: 'Having finished the exam, the hall was vacated.'",
       ["Having finished the exam, students vacated the hall.",
        "The hall, having finished the exam, was vacated.",
        "Having been finished, the hall was vacated by students.",
        "The exam finished, the hall vacated."],
       0, "Hard"),
    _q("'Equivocal' most nearly means:",
       ["Absolutely certain", "Deliberately vague", "Clearly defined", "Morally right"],
       1, "Hard"),
    _q("'The police ___ investigating the case.'",
       ["is", "are", "has", "was"],
       1, "Medium", "'Police' is a plural noun."),
    _q("Passive voice of: 'Someone has stolen my wallet.'",
       ["My wallet was stolen.", "My wallet is stolen.",
        "My wallet has been stolen.", "My wallet had been stolen."],
       2, "Hard", "Present perfect active → 'has been + past participle'."),
    _q("'Enervate' means:",
       ["To energise", "To weaken", "To enlighten", "To entangle"],
       1, "Hard"),
    _q("Which sentence is correct?",
       ["Between you and I, this is wrong.",
        "Between you and me, this is wrong.",
        "Between you and myself, this is wrong.",
        "Between me and yourself, this is wrong."],
       1, "Hard", "'Between' is a preposition; use objective pronoun 'me'."),
    _q("'Prolix' means:",
       ["Brief and to the point", "Tediously lengthy", "Extremely precise", "Highly emotional"],
       1, "Hard"),
    _q("'The pen is mightier than the sword.' This is:",
       ["Personification", "Hyperbole", "Metaphor", "Alliteration"],
       2, "Medium"),
    _q("Identify the anachronism: 'In ancient Rome, Caesar checked his smartphone.'",
       ["Caesar", "Ancient Rome", "Smartphone", "Checked"],
       2, "Medium"),
    _q("Which is NOT a figure of speech?",
       ["Synecdoche", "Metonymy", "Tautology", "Etymology"],
       3, "Hard", "Etymology is the study of word origins, not a figure of speech."),
    _q("'He was literally on cloud nine.' This uses:",
       ["Simile", "Metaphor", "Catachresis", "Hyperbole mixed with idiom"],
       3, "Hard"),
],
"Comprehension": [
    _q("'Didactic' literature primarily:",
       ["Entertains readers", "Teaches a moral lesson", "Describes nature", "Narrates historical events"],
       1, "Medium"),
    _q("'Catharsis' in literature refers to:",
       ["Character development", "Emotional release through art", "Plot climax", "A type of metaphor"],
       1, "Hard"),
    _q("Tone using understatement to describe tragedy is called:",
       ["Ironic", "Sarcastic", "Sardonic", "Pathetic fallacy"],
       0, "Hard"),
    _q("'Verisimilitude' in fiction means:",
       ["An unlikely plot twist", "Appearance of being true or real",
        "A moral flaw in the hero", "Excessive sentimentality"],
       1, "Hard"),
    _q("'Stream of consciousness' is associated with:",
       ["O. Henry", "Virginia Woolf", "Rudyard Kipling", "Thomas Hardy"],
       1, "Hard"),
    _q("A 'Bildungsroman' is:",
       ["A horror novel", "A coming-of-age story", "A political manifesto", "A war narrative"],
       1, "Hard"),
    _q("Which device is used in 'The fair breeze blew, the white foam flew'?",
       ["Assonance", "Alliteration", "Consonance", "Onomatopoeia"],
       1, "Medium"),
    _q("'Pathetic fallacy' attributes human emotions to:",
       ["Fictional characters", "The natural environment",
        "Political leaders", "Historical events"],
       1, "Hard"),
    _q("'Cogent' argument is one that is:",
       ["Weak and speculative", "Clear, logical and convincing",
        "Based entirely on emotion", "Historically inaccurate"],
       1, "Medium"),
    _q("'Apocryphal' means:",
       ["Widely accepted as true", "Of doubtful authenticity",
        "Revealed by divine inspiration", "Extremely frightening"],
       1, "Hard"),
    _q("Which word is closest in meaning to 'Loquacious'?",
       ["Taciturn", "Verbose", "Reticent", "Melancholic"],
       1, "Medium"),
    _q("'Ephemeral' means:",
       ["Eternal", "Short-lived", "Bright", "Powerful"],
       1, "Medium"),
    _q("Figure of speech in 'The moon was a ghostly galleon tossed upon cloudy seas':",
       ["Simile", "Personification", "Extended metaphor", "Alliteration"],
       2, "Hard"),
    _q("'Sesquipedalian' describes:",
       ["A person who walks long distances", "Use of very long words",
        "A six-sided figure", "An ancient Roman soldier"],
       1, "Hard"),
    _q("Synonym of 'Indolent' is:",
       ["Diligent", "Lazy", "Proud", "Honest"],
       1, "Medium"),
],
},

"Mathematics": {
"Algebra": [
    _q("If α,β are roots of 2x²-5x+3=0, find α²+β²:",
       ["25/4", "13/4", "19/4", "7/4"],
       1, "Hard", "α²+β² = (α+β)² - 2αβ = (5/2)² - 2(3/2) = 25/4 - 3 = 13/4"),
    _q("Real solutions of |x-2|+|x-5|=3:",
       ["0", "1", "Infinitely many", "2"],
       2, "Hard", "Equation holds for all x in [2,5] → infinite solutions."),
    _q("If log₂(log₃(log₂x))=0, then x:",
       ["8", "9", "512", "256"],
       0, "Hard", "log₃(log₂x)=1 → log₂x=3 → x=8"),
    _q("Sum of roots of x+1/x=10/3:",
       ["10/3", "0", "3", "10"],
       0, "Hard", "By Vieta's: sum of roots = 10/3"),
    _q("Remainder when P(x)=x³-3x²+4x-2 divided by (x-1):",
       ["0", "1", "2", "-1"],
       0, "Hard", "P(1)=1-3+4-2=0"),
    _q("Number of terms in expansion of (a+b+c)¹⁰:",
       ["33", "66", "11", "55"],
       1, "Hard", "C(10+2,2)=C(12,2)=66"),
    _q("If 2^x=3^y=6^(-z), then 1/x+1/y+1/z:",
       ["1", "0", "1/6", "-1"],
       1, "Hard", "Classic logarithm identity: 1/x+1/y+1/z=0"),
    _q("Harmonic mean of 2 and 3:",
       ["2.5", "12/5", "6/5", "5/6"],
       1, "Medium", "HM=2ab/(a+b)=12/5"),
    _q("4-digit numbers divisible by 7:",
       ["1286", "1285", "1287", "1288"],
       0, "Hard", "From 1001 to 9996: (9996-1001)/7+1=1286"),
    _q("If x real and y=(x²+2x+1)/(x²+2x+7), y lies in:",
       ["[0,1)", "[0,1/6]", "[0,1]", "(0,1/6)"],
       1, "Hard", "Let t=x²+2x≥-1: y=(t+1)/(t+7); range is [0,1/6]"),
    _q("If a,b,c are in GP and a^x=b^y=c^z, then x,y,z are in:",
       ["AP", "GP", "HP", "Neither"],
       2, "Hard"),
    _q("Coefficient of x⁵ in (1+x)^10:",
       ["210", "252", "120", "126"],
       1, "Hard", "C(10,5)=252"),
    _q("Sum of the infinite GP 1+1/2+1/4+...:",
       ["1", "2", "3/2", "4/3"],
       1, "Medium", "S=a/(1-r)=1/(0.5)=2"),
    _q("If x²-px+q=0 has equal roots, then p²=",
       ["4q", "q", "q/4", "2q"],
       0, "Hard", "Discriminant=0: p²-4q=0"),
    _q("For what value of k does kx²+4x+1=0 have real roots?",
       ["k≤4", "k≥4", "k≤4 (k≠0) or k<0", "k=4"],
       2, "Hard", "D=16-4k≥0 → k≤4; k=0 gives linear; k<0 also works."),
    _q("Integers between 100 and 999 with all distinct digits:",
       ["648", "576", "720", "504"],
       1, "Hard", "9×9×8=648? First digit: 9 choices (1-9), second: 9 (0-9 excl first), third: 8. =648"),
    _q("f(x)=x/(1+x), then f(f(x))=",
       ["x/(1+2x)", "x/(2+x)", "2x/(1+x)", "x²/(1+x)"],
       0, "Hard"),
    _q("Sum of all two-digit numbers divisible by 3:",
       ["1665", "1545", "1575", "1620"],
       0, "Hard", "AP:12..99; n=30; S=30/2×(12+99)=1665"),
    _q("Product of roots of √3x²-2x-√3=0:",
       ["-1", "1", "2/√3", "-√3"],
       0, "Hard", "Product=c/a=-√3/√3=-1"),
    _q("Which expression equals (a+b)²-(a-b)²?",
       ["4ab", "2ab", "a²-b²", "0"],
       0, "Medium", "(a+b)²-(a-b)²=4ab"),
    _q("Number of ways to select 3 cards of same suit from 52:",
       ["1144", "2196", "5148", "4368"],
       0, "Hard", "4×C(13,3)=4×286=1144"),
    _q("If A={1,2,3,4} and B={2,4,6,8}, |A∪B|=",
       ["6", "7", "8", "5"],
       0, "Hard", "{1,2,3,4,6,8} → 6 elements"),
],
"Trigonometry": [
    _q("If sinθ+cosθ=√2cosθ, then cotθ=",
       ["√2-1", "√2+1", "1-√2", "-(√2+1)"],
       1, "Hard", "sinθ=(√2-1)cosθ → cotθ=1/tanθ=√2+1"),
    _q("General solution of sinθ=-1/2:",
       ["nπ+(-1)ⁿπ/6", "nπ+(-1)ⁿ⁺¹π/6", "nπ-(-1)ⁿπ/6", "2nπ±7π/6"],
       1, "Hard"),
    _q("cos36°-cos72°=",
       ["1/2", "1", "√5/4", "1/4"],
       0, "Hard", "=(√5+1)/4-(√5-1)/4=2/4=1/2"),
    _q("If A+B+C=π, then sin²A+sin²B+sin²C=",
       ["2+2cosAcosBcosC", "4sinAsinBsinC", "2(1+cosAcosBcosC)", "1"],
       1, "Hard"),
    _q("tan75°=",
       ["2-√3", "2+√3", "√3-1", "√3+1"],
       1, "Hard", "tan(45+30)=2+√3"),
    _q("If sinα=3/5 and α in 2nd quadrant, cos2α=",
       ["-7/25", "7/25", "24/25", "-24/25"],
       1, "Hard", "cos2α=1-2sin²α=1-18/25=7/25"),
    _q("Maximum value of 3sinx+4cosx:",
       ["7", "5", "4", "3√3"],
       1, "Hard", "√(9+16)=5"),
    _q("sin18°=",
       ["(√5-1)/4", "(√5+1)/4", "(√5-1)/2", "(√10-2)/4"],
       0, "Hard"),
    _q("Period of |sinx|:",
       ["2π", "π", "π/2", "4π"],
       1, "Medium"),
    _q("In triangle ABC, a/sinA=b/sinB=c/sinC=k, then k=",
       ["Area of triangle", "2R (circumradius)", "r (inradius)", "s (semiperimeter)"],
       1, "Hard"),
    _q("cosAcos(60°-A)cos(60°+A)=",
       ["cos3A/4", "sin3A/4", "cos3A/2", "1/4 cos3A"],
       0, "Hard"),
    _q("Number of solutions of sin2x+cos4x=2 in [0,2π]:",
       ["1", "2", "0", "4"],
       2, "Hard", "Would require sin2x=1 AND cos4x=1 simultaneously — no solution exists."),
    _q("sin10°+sin50°-sin70°=",
       ["0", "1/2", "sin30°", "-1/2"],
       0, "Hard"),
    _q("If tanθ=t, then tan2θ+sec2θ=",
       ["(1+t)/(1-t)", "(1-t)/(1+t)", "t/(1+t)", "(t+1)²/(t²+1)"],
       0, "Hard"),
    _q("Equation 2cos²x+3sinx=0 gives sinx=",
       ["-1/2", "1/2", "-3/2", "1"],
       0, "Hard", "2(1-sin²x)+3sinx=0 → 2sin²x-3sinx-2=0 → sinx=-1/2"),
    _q("tan(A-B)=1 and sec(A+B)=2/√3; smallest +ve value of 2B:",
       ["30°", "45°", "25°", "15°"],
       3, "Hard"),
    _q("If cosα+cosβ=a and sinα+sinβ=b, then tan((α+β)/2)=",
       ["b/a", "a/b", "(a²+b²)/2", "a²-b²"],
       0, "Hard"),
    _q("Value of cos²10°+cos²110°+cos²130°:",
       ["3/2", "1", "3/4", "2"],
       0, "Hard"),
],
"Coordinate Geometry": [
    _q("Angle between lines x+√3y=5 and √3x-y=3:",
       ["30°", "45°", "60°", "90°"],
       3, "Hard", "Product of slopes = (-1/√3)(√3)=-1 → perpendicular."),
    _q("Circle x²+y²-6x+4y-12=0: centre and radius:",
       ["(3,-2), 5", "(-3,2), 5", "(3,-2), 4", "(6,-4), 12"],
       0, "Hard", "Centre=(3,-2), r=√(9+4+12)=5"),
    _q("Parabola y²=8x has focus at:",
       ["(2,0)", "(0,2)", "(-2,0)", "(4,0)"],
       0, "Hard", "y²=4ax → a=2 → focus (2,0)"),
    _q("Eccentricity of ellipse x²/16+y²/9=1:",
       ["√7/4", "√7/3", "3/4", "√(7/16)"],
       0, "Hard", "e=√(1-9/16)=√7/4"),
    _q("Lines ax²+2hxy+by²=0 are perpendicular if:",
       ["a=b", "a+b=0", "h²=ab", "a-b=0"],
       1, "Hard"),
    _q("Length of tangent from (5,1) to x²+y²+6x-4y-3=0:",
       ["7", "√51", "√44", "√81"],
       0, "Hard", "√(25+1+30-4-3)=√49=7"),
    _q("Director circle of ellipse x²/a²+y²/b²=1 is:",
       ["x²+y²=a²+b²", "x²+y²=a²-b²", "x²+y²=a²", "x²+y²=2(a²+b²)"],
       0, "Hard"),
    _q("Hyperbola x²/9-y²/16=1 has eccentricity:",
       ["5/3", "5/4", "4/3", "3/4"],
       0, "Hard", "e=√(1+16/9)=5/3"),
    _q("Line y=mx+c is tangent to x²+y²=r² if c²=",
       ["r²(1+m²)", "r²m²", "r²(m²-1)", "r²/m²"],
       0, "Hard"),
    _q("Area of triangle with vertices (0,0),(a,0),(0,b):",
       ["ab", "ab/2", "2ab", "a²+b²"],
       1, "Medium"),
    _q("Reflection of (3,-2) about y-axis:",
       ["(3,2)", "(-3,-2)", "(-3,2)", "(-2,3)"],
       1, "Medium"),
    _q("Line 3x+4y=k touches circle x²+y²=25 if k=",
       ["±15", "±25", "±5", "±10"],
       1, "Hard", "Distance from origin=|k|/5=5 → |k|=25"),
    _q("Number of common tangents to x²+y²=4 and x²+y²-6x-8y+24=0:",
       ["4", "3", "2", "1"],
       1, "Hard"),
    _q("Centroid divides each median in ratio:",
       ["2:1 from vertex", "1:2 from vertex", "1:1", "3:1"],
       0, "Hard"),
    _q("If mid-point of (3,4) and (k,7) lies on y=x+1, then k=",
       ["6", "5", "4", "7"],
       0, "Hard", "Mid=((3+k)/2, 11/2); 11/2=(3+k)/2+1 → k=6"),
    _q("Locus of point equidistant from (1,2) and (3,4):",
       ["x+y=5", "x+y=4", "x-y+1=0", "2x+2y=5"],
       1, "Hard"),
    _q("Pole of line x/a+y/b=1 w.r.t circle x²+y²=c²:",
       ["(c²/a, c²/b)", "(a/c², b/c²)", "(c/a, c/b)", "(a²/c, b²/c)"],
       0, "Hard"),
],
"Mensuration": [
    _q("Sphere inscribed in cube of side 6 cm. Volume (π≈3.14159):",
       ["≈113.1 cm³", "≈112.5 cm³", "≈113.5 cm³", "≈110 cm³"],
       0, "Hard", "r=3, V=4/3π(27)=36π≈113.1"),
    _q("Radius of sphere doubled; surface area increases by:",
       ["100%", "200%", "300%", "400%"],
       2, "Hard", "4πr²→4π(2r)²=4×4πr²→300% increase"),
    _q("Hollow cylinder: outer r=5, inner r=3, h=10. Volume:",
       ["≈502.4 cm³", "480 cm³", "≈502.8 cm³", "520 cm³"],
       0, "Hard", "π(25-9)(10)=160π≈502.4"),
    _q("Diagonal of rectangle is 13, one side is 5. Area:",
       ["60 cm²", "65 cm²", "30 cm²", "120 cm²"],
       0, "Hard", "Other side=√(169-25)=12; A=60"),
    _q("Total surface area of hemisphere of radius r:",
       ["3πr²", "2πr²", "4πr²", "πr²"],
       0, "Hard", "Curved SA=2πr², flat circle=πr²; total=3πr²"),
    _q("Cuboid l=8, b=6, h=4. Longest diagonal:",
       ["√116 cm", "10 cm", "√104 cm", "12 cm"],
       0, "Hard", "√(64+36+16)=√116"),
    _q("Frustum lateral SA with radii R,r and slant height l:",
       ["π(R+r)l", "π(R-r)l", "π(R²-r²)", "2π(R+r)l"],
       0, "Hard"),
    _q("Slant height of cone with h=12, base r=5:",
       ["13", "√119", "17", "15"],
       0, "Medium", "l=√(144+25)=13"),
    _q("Area of rhombus with diagonals 16 and 12 cm:",
       ["96 cm²", "192 cm²", "48 cm²", "144 cm²"],
       0, "Medium", "Area=d₁d₂/2=96"),
    _q("Sector of radius 7, angle 90°. Area (π=22/7):",
       ["38.5 cm²", "44 cm²", "77 cm²", "154 cm²"],
       0, "Medium", "θ/360×πr²=154/4=38.5"),
    _q("If radius of a circle is halved, area becomes:",
       ["Half", "One-quarter", "One-third", "Two-thirds"],
       1, "Medium", "Area∝r²; (r/2)²=r²/4"),
    _q("Volume of cone with base r=6, h=14 (π=22/7):",
       ["528 cm³", "264 cm³", "1056 cm³", "396 cm³"],
       0, "Hard", "1/3×22/7×36×14=528"),
],
"Arithmetic": [
    _q("Pipes A(12h), B(18h), C empties(36h). Time to fill together:",
       ["9 hours", "8 hours", "10 hours", "12 hours"],
       0, "Hard", "1/12+1/18-1/36=4/36=1/9 → 9 hours"),
    _q("Sum triples in 10 years at SI. Rate %:",
       ["15%", "20%", "25%", "12.5%"],
       1, "Hard", "SI=2P in 10yr → R=200/10=20%"),
    _q("200m train crosses 300m platform in 25s. Speed in km/h:",
       ["72", "60", "80", "64"],
       0, "Hard", "500/25=20m/s=72km/h"),
    _q("CP of 20 articles=SP of 16. Profit %:",
       ["25%", "20%", "16.67%", "30%"],
       0, "Hard", "SP/CP=20/16=5/4 → profit=25%"),
    _q("A:B=2:3, B:C=4:5, then A:B:C=",
       ["8:12:15", "2:4:5", "8:12:5", "6:9:10"],
       0, "Hard"),
    _q("CI on ₹10000 at 10% for 3 years:",
       ["₹3310", "₹3000", "₹3300", "₹3631"],
       0, "Hard", "10000(1.1³-1)=3310"),
    _q("Boat: 24km upstream in 6h, 24km downstream in 4h. Speed of current:",
       ["1 km/h", "2 km/h", "3 km/h", "4 km/h"],
       0, "Hard", "DS=6, US=4; current=(6-4)/2=1"),
    _q("40% of x=60% of y, then x:y=",
       ["2:3", "3:2", "4:6", "2:4"],
       1, "Hard", "40x=60y → x/y=3/2"),
    _q("₹6000 at 5% pa CI compounded half-yearly for 1 year:",
       ["₹6303.75", "₹6300", "₹6315", "₹6306"],
       0, "Hard", "6000(1.025)²=6303.75"),
    _q("Man sells 2/5 at 20% profit, rest at 15% loss. Overall:",
       ["2% loss", "1% loss", "2% gain", "No gain/loss"],
       1, "Hard", "2/5×20+3/5×(-15)=8-9=-1%"),
    _q("Water:milk costing ₹12/L to get mixture worth ₹8/L:",
       ["1:2", "2:1", "1:1", "3:1"],
       0, "Hard", "Alligation: (12-8):(8-0)=4:8=1:2"),
    _q("Ages A:B=4:5. 5 years hence 5:6. Present age of A:",
       ["20", "25", "15", "10"],
       0, "Hard", "(4x+5)/(5x+5)=5/6 → x=5; A=20"),
    _q("Dishonest shopkeeper uses 900g weight for 1kg. Profit %:",
       ["11.11%", "10%", "9.09%", "12.5%"],
       0, "Hard", "Profit=100/900×100=11.11%"),
    _q("If P and T both doubled, new SI vs original SI:",
       ["2×", "4×", "0.5×", "Same"],
       1, "Hard", "SI∝P×T; both doubled → 4×"),
    _q("Price rises 25%. Consumption should decrease by ___ to keep expenditure same:",
       ["20%", "25%", "16.67%", "30%"],
       0, "Hard", "25/125×100=20%"),
    _q("Three AP numbers: sum=30, product=910. The numbers:",
       ["5,10,15", "8,10,12", "7,10,13", "6,10,14"],
       2, "Hard", "a=10; 10(100-d²)=910 → d=3; 7,10,13"),
    _q("LCM of 4, 6 and 9:",
       ["36", "12", "18", "24"],
       0, "Hard", "LCM(4,6,9)=36"),
],
},

"General Science": {
"Physics": [
    _q("Ball projected vertically upward with speed u. Time to reach max height:",
       ["u/g", "2u/g", "u/2g", "g/u"],
       0, "Hard", "v=u-gt; at max v=0 → t=u/g"),
    _q("Power of lens is -2.5 D. Its nature and focal length:",
       ["-40 cm, concave", "+40 cm, convex", "-25 cm, concave", "+25 cm, convex"],
       0, "Hard", "f=1/P=-0.4m=-40cm; negative → concave"),
    _q("3Ω and 6Ω resistors in parallel across 12V. Total current:",
       ["6A", "4A", "3A", "2A"],
       0, "Hard", "Rp=2Ω; I=12/2=6A"),
    _q("Charged particle moves perpendicular to B-field. Path is:",
       ["Straight line", "Parabola", "Circle", "Ellipse"],
       2, "Hard", "F=qvB (centripetal) → circular path"),
    _q("Ratio of electric to gravitational force between two electrons:",
       ["~10⁴²", "~10³⁶", "~10²⁸", "~10²⁰"],
       0, "Hard", "ke²/Gm²≈10⁴²"),
    _q("In Young's double slit experiment, fringe width ∝",
       ["1/d", "1/λ", "d", "1/D"],
       0, "Hard", "β=λD/d → β∝1/d"),
    _q("Efficiency of Carnot engine between 500K and 300K:",
       ["40%", "60%", "37.5%", "50%"],
       0, "Hard", "η=1-300/500=40%"),
    _q("Wire of resistance R bent into circle. Resistance between diametrically opposite points:",
       ["R/4", "R/2", "R", "2R"],
       0, "Hard", "Two R/2 in parallel → R/4"),
    _q("Moment of inertia of solid sphere about diameter:",
       ["2/5 MR²", "2/3 MR²", "MR²", "7/5 MR²"],
       0, "Hard"),
    _q("Object at 2f from convex lens. Image is:",
       ["At f, diminished", "At 2f, same size, real, inverted",
        "At infinity", "Virtual and magnified"],
       1, "Hard"),
    _q("de Broglie wavelength with momentum p:",
       ["h/p", "hp", "p/h", "h²/p"],
       0, "Hard", "λ=h/p"),
    _q("Escape velocity from Earth (g=10, R=6400km):",
       ["≈11.2 km/s", "≈7.9 km/s", "≈16 km/s", "≈8 km/s"],
       0, "Hard", "ve=√(2gR)≈11.2km/s"),
    _q("Magnetic field inside a solenoid is:",
       ["Zero", "Non-uniform", "Uniform and parallel to axis", "Proportional to 1/r"],
       2, "Hard"),
    _q("Which nuclear reaction releases maximum energy per unit mass?",
       ["Fission of U-235", "Fusion of hydrogen",
        "Chemical combustion", "Alpha decay"],
       1, "Hard"),
    _q("Thermodynamic process where ΔQ=0:",
       ["Isothermal", "Isobaric", "Adiabatic", "Isochoric"],
       2, "Hard"),
    _q("Doppler effect: source moves toward observer, frequency:",
       ["Decreases", "Increases", "Same", "Zero"],
       1, "Medium"),
    _q("Critical angle for total internal reflection depends on:",
       ["Angle of incidence only", "Refractive index of the media",
        "Wavelength only", "Amplitude of light"],
       1, "Hard"),
    _q("Beats phenomenon arises due to:",
       ["Diffraction", "Same-frequency interference",
        "Superposition of slightly different frequencies", "Reflection"],
       2, "Hard"),
],
"Chemistry": [
    _q("Hybridization of C in diamond and graphite respectively:",
       ["sp³, sp²", "sp², sp³", "sp³, sp", "sp, sp²"],
       0, "Hard"),
    _q("Highest electronegativity:",
       ["O", "F", "N", "Cl"],
       1, "Hard"),
    _q("In 2Na+2H₂O→2NaOH+H₂, Na undergoes:",
       ["Oxidation only", "Reduction only", "Neither",
        "Disproportionation (both oxidised and reduced)"],
       3, "Hard"),
    _q("Molarity of pure water (density=1g/mL, MW=18):",
       ["55.5 M", "18 M", "1 M", "50 M"],
       0, "Hard", "M=1000/18≈55.5"),
    _q("Strongest oxidising agent among halogens:",
       ["F₂", "Cl₂", "Br₂", "I₂"],
       0, "Hard"),
    _q("Sigma and pi bonds in CH₂=CH-CHO:",
       ["6σ, 2π", "7σ, 2π", "5σ, 2π", "8σ, 2π"],
       1, "Hard", "C=C(1σ+1π)+C-C(1σ)+C=O(1σ+1π)+4C-H=7σ,2π"),
    _q("Mond process purifies:",
       ["Copper", "Aluminium", "Nickel", "Iron"],
       2, "Hard"),
    _q("Which quantum number determines shape of orbital?",
       ["Principal (n)", "Azimuthal (l)", "Magnetic (m)", "Spin (s)"],
       1, "Hard"),
    _q("Le Chatelier: pressure increased in N₂+3H₂⇌2NH₃, reaction shifts:",
       ["Backward", "Forward (fewer moles side)", "No shift", "Cannot be determined"],
       1, "Hard"),
    _q("IUPAC name of CH₃-CH(OH)-COOH:",
       ["2-hydroxypropanoic acid", "Lactic acid", "Propan-2-ol-1-oic acid", "1-hydroxypropanoic acid"],
       0, "Hard"),
    _q("Wurtz reaction produces:",
       ["Alkene", "Higher alkane", "Alcohol", "Ether"],
       1, "Hard"),
    _q("Not a colligative property:",
       ["Osmotic pressure", "Elevation of boiling point",
        "Optical rotation", "Depression in freezing point"],
       2, "Hard"),
    _q("Nylon-6,6 is polymer of:",
       ["Hexamethylenediamine + adipic acid", "Caprolactam",
        "Glycine + alanine", "Vinyl chloride"],
       0, "Hard"),
    _q("pH of pure water at 25°C:",
       ["5", "6", "7", "8"],
       2, "Medium"),
    _q("Gas that turns lime water milky:",
       ["SO₂", "CO₂", "H₂S", "HCl"],
       1, "Medium"),
    _q("Buffer solution resists change in:",
       ["Temperature", "Volume", "pH", "Concentration"],
       2, "Medium"),
    _q("pKa of acetic acid≈4.74. Its Ka:",
       ["≈1.8×10⁻⁵", "≈4.74×10⁻⁵", "≈10⁻⁴", "≈2×10⁻⁴"],
       0, "Hard", "Ka=10^(-4.74)≈1.8×10⁻⁵"),
],
"Biology": [
    _q("Enzyme that unwinds DNA during replication:",
       ["DNA polymerase", "Helicase", "Ligase", "Primase"],
       1, "Hard"),
    _q("Phenylketonuria: deficiency of enzyme:",
       ["Tyrosinase", "Phenylalanine hydroxylase", "Amylase", "Lactase"],
       1, "Hard"),
    _q("Brain part controlling body temperature:",
       ["Cerebellum", "Hypothalamus", "Medulla oblongata", "Pons"],
       1, "Hard"),
    _q("ABO blood group is example of:",
       ["Incomplete dominance", "Codominance with multiple alleles",
        "Sex-linked inheritance", "Epistasis"],
       1, "Hard"),
    _q("CO₂ is first fixed in Calvin cycle as:",
       ["3-PGA", "RuBP", "G3P", "Oxaloacetate"],
       0, "Hard"),
    _q("Insulin is produced by ___ cells of Islets of Langerhans:",
       ["Alpha", "Beta", "Delta", "PP"],
       1, "Hard"),
    _q("Crossing over occurs during:",
       ["Leptotene", "Zygotene", "Pachytene", "Diplotene"],
       2, "Hard"),
    _q("Bowman's capsule function:",
       ["Reabsorption of glucose", "Filtration of blood",
        "Hormone secretion", "Urine concentration"],
       1, "Hard"),
    _q("Restriction enzymes cut DNA at:",
       ["Random positions", "Specific palindromic sequences",
        "Only introns", "Promoter regions"],
       1, "Hard"),
    _q("Hardy-Weinberg equilibrium is disturbed by:",
       ["Large population", "Random mating", "Mutations", "No migration"],
       2, "Hard"),
    _q("Vector for Plasmodium (malaria):",
       ["Aedes aegypti", "Female Anopheles", "Culex", "Sandfly"],
       1, "Medium"),
    _q("Photosystem I absorption maxima at:",
       ["680 nm", "700 nm", "660 nm", "730 nm"],
       1, "Hard", "PS I = P700"),
    _q("Light reaction products used in Calvin cycle:",
       ["O₂ and CO₂", "ATP and NADPH", "Glucose and H₂O", "RuBP"],
       1, "Hard"),
    _q("Erythroblastosis fetalis occurs when:",
       ["Rh- mother carries Rh+ fetus (2nd pregnancy)",
        "Rh+ mother carries Rh- fetus",
        "Both parents Rh-",
        "ABO incompatibility always"],
       0, "Hard"),
    _q("Vitamin synthesised by gut bacteria:",
       ["Vitamin C", "Vitamin K", "Vitamin D", "Vitamin A"],
       1, "Medium"),
    _q("Powerhouse of the cell:",
       ["Nucleus", "Ribosome", "Mitochondria", "Lysosome"],
       2, "Medium"),
    _q("Normal human body temperature:",
       ["35°C", "36°C", "37°C", "38°C"],
       2, "Medium"),
],
},

"History": {
"Ancient India": [
    _q("Arthashastra deals primarily with:",
       ["Military strategy only", "Statecraft, economic policy and military strategy",
        "Astronomy and mathematics", "Philosophy"],
       1, "Hard"),
    _q("'Ashtadhyayi' is associated with:",
       ["Chanakya", "Panini", "Aryabhata", "Charaka"],
       1, "Hard"),
    _q("Gupta king known as 'Kaviraj':",
       ["Chandragupta I", "Samudragupta", "Chandragupta II", "Skandagupta"],
       1, "Hard"),
    _q("Mahavamsam chronicles history of:",
       ["India", "Sri Lanka", "Burma", "Nepal"],
       1, "Hard"),
    _q("Kautilya's Arthashastra was rediscovered by:",
       ["Max Müller", "R. Shamasastry", "Vincent Smith", "A.L. Basham"],
       1, "Hard"),
    _q("'Shreni' in ancient India refers to:",
       ["Royal treasury", "Craft guilds/merchant associations",
        "Land revenue system", "Military units"],
       1, "Hard"),
    _q("Founder of Sunga dynasty:",
       ["Agnimitra", "Pushyamitra Sunga", "Devabhuti", "Vasumitra"],
       1, "Hard"),
    _q("Battle of Hydaspes (326 BC): Alexander vs:",
       ["Chandragupta Maurya", "Porus (Paurava king)",
        "Dhana Nanda", "Ambhi of Taxila"],
       1, "Hard"),
    _q("Nalanda University founded during whose reign?",
       ["Chandragupta II", "Kumaragupta I", "Ashoka", "Harshavardhana"],
       1, "Hard"),
    _q("Megasthenes wrote:",
       ["Indica", "Arthashastra", "Mudrarakshasa", "Ashtadhyayi"],
       0, "Hard"),
    _q("Sangam Age corresponds to approximately:",
       ["600 BCE–600 CE", "200 BCE–300 CE", "100 CE–600 CE", "1000 BCE–200 BCE"],
       1, "Hard"),
    _q("Ajivikas sect was founded by:",
       ["Mahavira", "Makkhali Gosala", "Ajita Kesakambali", "Purana Kassapa"],
       1, "Hard"),
    _q("Ashoka belonged to which dynasty?",
       ["Gupta", "Maurya", "Nanda", "Kushan"],
       1, "Medium"),
    _q("Capital of Mauryan Empire:",
       ["Taxila", "Pataliputra", "Ujjain", "Vaishali"],
       1, "Medium"),
    _q("'Vikramaditya' title is historically associated with:",
       ["Chandragupta I", "Chandragupta II", "Bindusara", "Kumaragupta"],
       1, "Hard"),
    _q("Buddhist text 'Tripitaka' is written in:",
       ["Sanskrit", "Pali", "Prakrit", "Tamil"],
       1, "Hard"),
],
"Modern India": [
    _q("Charter Act of 1813 significance:",
       ["Ended EIC's commercial monopoly with India (except tea & China)",
        "Gave Indians representation in legislative councils",
        "Introduced English education",
        "Allowed missionaries freely"],
       0, "Hard"),
    _q("Newspaper started by Bal Gangadhar Tilak:",
       ["Kesari and Mahratta", "Amrita Bazar Patrika", "The Hindu", "Tribune"],
       0, "Hard"),
    _q("Minto-Morley reforms (1909) introduced:",
       ["Diarchy in provinces", "Separate electorate for Muslims",
        "Universal suffrage", "Full responsible government"],
       1, "Hard"),
    _q("Simon Commission boycotted because:",
       ["It proposed partition", "It had no Indian member",
        "It recommended dominion status immediately",
        "It suggested abolishing princely states"],
       1, "Hard"),
    _q("'Drain of Wealth' theory propounded by:",
       ["Gopal Krishna Gokhale", "Dadabhai Naoroji",
        "B.G. Tilak", "M.G. Ranade"],
       1, "Hard"),
    _q("Rowlatt Act (1919) was opposed because:",
       ["It imposed heavy taxes", "It allowed detention without trial",
        "It banned Indian newspapers", "It reduced ICS quotas"],
       1, "Hard"),
    _q("Sardar Patel known as 'Iron Man' for:",
       ["Military leadership in 1947", "Integration of 562 princely states",
        "Drafting the Constitution", "Leading salt march"],
       1, "Hard"),
    _q("Constitution adopted on:",
       ["26 Jan 1950", "15 Aug 1947", "26 Nov 1949", "26 Nov 1950"],
       2, "Hard", "Adopted 26 Nov 1949; enacted 26 Jan 1950."),
    _q("First General Elections in India:",
       ["1948", "1950", "1952", "1957"],
       2, "Hard"),
    _q("'Swadeshi' literally means:",
       ["Self-rule", "Own country's goods", "Civil disobedience", "Non-cooperation"],
       1, "Medium"),
    _q("Indians got representation in central legislature first through:",
       ["Indian Councils Act 1892", "Morley-Minto Reforms 1909",
        "Montagu-Chelmsford 1919", "GOI Act 1935"],
       1, "Hard"),
    _q("'August Offer' (1940) was made by:",
       ["Viceroy Linlithgow", "Lord Wavell", "Churchill", "Cripps Mission"],
       0, "Hard"),
    _q("Cripps Mission (1942) failed primarily because:",
       ["Congress rejected dominion status; ML wanted Pakistan directly",
        "Britain refused to negotiate",
        "Gandhi opposed all negotiations",
        "Japan invaded before talks concluded"],
       0, "Hard"),
    _q("Indian National Congress founded in:",
       ["1857", "1885", "1905", "1920"],
       1, "Medium"),
    _q("'Dandi March' was related to:",
       ["Salt tax", "Land tax", "Freedom of press", "Partition"],
       0, "Medium"),
    _q("Who gave the slogan 'Jai Hind'?",
       ["Bhagat Singh", "Subhas Chandra Bose", "Gandhi", "Tilak"],
       1, "Medium"),
],
},

"Geography": {
"Physical Geography": [
    _q("'Roaring forties', 'furious fifties', 'screaming sixties' are:",
       ["Ocean currents in tropics",
        "Westerly winds in Southern Ocean latitudes",
        "Cyclonic systems of Northern Hemisphere",
        "Tidal zones near poles"],
       1, "Hard"),
    _q("El Niño is associated with weakening of:",
       ["Trade winds in the Pacific", "Westerlies in Atlantic",
        "Monsoon winds in Asia", "Polar jet stream"],
       0, "Hard"),
    _q("Deccan Plateau is classified as:",
       ["Depositional plain", "Structural/table land plateau",
        "Intermontane plateau", "Dissected plateau only"],
       1, "Hard"),
    _q("Ocean current keeping Western Europe warmer than its latitude:",
       ["Humboldt Current", "North Atlantic Drift",
        "Canary Current", "Labrador Current"],
       1, "Hard"),
    _q("'Temperature inversion' leads to:",
       ["Rapid upward convection", "Smog and fog in cities",
        "Increased precipitation", "Reduced humidity"],
       1, "Hard"),
    _q("Laterite soil forms due to:",
       ["Intense leaching in humid tropics", "Alluvial deposition",
        "Wind erosion in deserts", "Volcanic activity"],
       0, "Hard"),
    _q("Which river system drains into Arabian Sea?",
       ["Ganga-Brahmaputra", "Mahanadi-Godavari", "Narmada-Tapi", "Cauvery"],
       2, "Hard"),
    _q("'Hadley Cell' involves:",
       ["Rising air at poles, sinking at 60°",
        "Rising air at equator, sinking at 30°",
        "Horizontal airflow at mid-latitudes",
        "Rising at 30° and sinking at equator"],
       1, "Hard"),
    _q("'Regur' soil is another name for:",
       ["Alluvial soil", "Black cotton soil", "Red soil", "Laterite"],
       1, "Medium"),
    _q("Standard meridian of India passes through:",
       ["Bhopal", "Allahabad (Prayagraj)", "Nagpur", "Varanasi"],
       1, "Hard", "82.5°E passes through the Prayagraj/Mirzapur area."),
    _q("'Loo' is:",
       ["A monsoon wind", "A local hot and dry summer wind of North India",
        "A sea breeze", "A polar wind"],
       1, "Medium"),
    _q("Ten Degree Channel separates:",
       ["India and Sri Lanka", "Andaman and Nicobar Islands",
        "Lakshadweep and Minicoy", "North and South Andaman"],
       1, "Hard"),
    _q("Tropopause is highest at:",
       ["Poles", "Equator", "Tropics", "45° latitude"],
       1, "Hard"),
    _q("Soil erosion is maximum when angle of slope is approximately:",
       ["0°", "45°", "25-40°", "90°"],
       2, "Hard"),
    _q("Tidal forests (mangroves) are found in:",
       ["Desert coasts", "High altitude coasts",
        "Saline mudflats near river deltas", "Rocky Mediterranean coasts"],
       2, "Hard"),
    _q("Tropic of Cancer passes through how many Indian states?",
       ["6", "7", "8", "9"],
       2, "Hard"),
    _q("Which type of rainfall is associated with tropical cyclones?",
       ["Orographic", "Convectional", "Cyclonic/frontal", "Relief"],
       2, "Hard"),
],
"World Geography": [
    _q("Country with longest coastline:",
       ["Russia", "Australia", "Canada", "Norway"],
       2, "Hard"),
    _q("Great Barrier Reef is located in:",
       ["Indian Ocean", "Coral Sea (off NE Australia)",
        "Caribbean Sea", "South China Sea"],
       1, "Hard"),
    _q("Mariana Trench is in:",
       ["Atlantic Ocean", "Arctic Ocean", "Indian Ocean", "Pacific Ocean"],
       3, "Hard"),
    _q("World's most saline water body:",
       ["Dead Sea", "Red Sea", "Mediterranean Sea", "Caspian Sea"],
       0, "Hard"),
    _q("'Pampas' grasslands are in:",
       ["North America", "South America (Argentina/Uruguay)",
        "South Africa", "Central Asia"],
       1, "Hard"),
    _q("Suez Canal connects:",
       ["Red Sea and Arabian Sea", "Red Sea and Mediterranean Sea",
        "Black Sea and Caspian Sea", "Persian Gulf and Arabian Sea"],
       1, "Hard"),
    _q("International Date Line mostly passes through:",
       ["Land masses", "Pacific Ocean", "Atlantic Ocean", "Arctic Ocean"],
       1, "Medium"),
    _q("'Ring of Fire' is associated with:",
       ["Hotspot volcanism in mid-Pacific",
        "Volcanic and earthquake zones circling the Pacific",
        "Atlantic ridge system",
        "Himalayan orogenic belt"],
       1, "Hard"),
    _q("Strait of Malacca connects:",
       ["Bay of Bengal and South China Sea",
        "Indian Ocean and Pacific via Andaman/South China Sea",
        "Arabian Sea and Red Sea",
        "South China Sea and Philippine Sea"],
       0, "Hard"),
    _q("Greenwich Meridian passes through which African country?",
       ["Nigeria", "Algeria", "Ghana", "Mali"],
       2, "Hard"),
    _q("Deepest lake in the world:",
       ["Lake Baikal", "Lake Superior", "Caspian Sea", "Lake Tanganyika"],
       0, "Hard"),
    _q("'Sahel' region is:",
       ["Dense tropical forest", "Semi-arid transition zone south of Sahara",
        "Coastal wetland", "Mediterranean scrubland"],
       1, "Hard"),
    _q("Largest proven oil reserves:",
       ["Saudi Arabia", "Russia", "Iran", "Venezuela"],
       3, "Hard"),
    _q("Amazon basin is world's largest:",
       ["Desert", "Tropical rainforest", "Savanna", "Temperate grassland"],
       1, "Medium"),
    _q("Country known as 'Land of Midnight Sun':",
       ["Iceland", "Greenland", "Norway", "Finland"],
       2, "Medium"),
    _q("Largest continent is:",
       ["Africa", "North America", "Asia", "Europe"],
       2, "Medium"),
],
},

"Economics": {
"Microeconomics": [
    _q("PED=-2; 10% price rise leads to:",
       ["5% fall", "20% fall", "2% fall", "10% fall"],
       1, "Hard", "|PED|=2; 2×10=20% fall in quantity demanded"),
    _q("Under perfect competition in long run, firms earn:",
       ["Supernormal profits", "Normal profits (zero economic profit)",
        "Losses", "Monopoly rents"],
       1, "Hard"),
    _q("'Invisible hand' concept introduced by:",
       ["John Maynard Keynes", "Adam Smith", "David Ricardo", "Alfred Marshall"],
       1, "Hard"),
    _q("Giffen goods violate law of demand because:",
       ["Inferior goods where income effect > substitution effect",
        "They are luxury goods",
        "Inelastic supply",
        "Demand determined by government"],
       0, "Hard"),
    _q("Kinked demand curve explains:",
       ["Price rigidity in oligopoly", "Monopoly pricing",
        "Perfect competition equilibrium", "Monopsony in labour market"],
       0, "Hard"),
    _q("When MR=0, total revenue is:",
       ["Zero", "Maximum", "At minimum", "Equal to AR"],
       1, "Hard"),
    _q("Indifference curves cannot intersect because:",
       ["They represent different income levels",
        "It would violate transitivity/consistency of preferences",
        "They are parallel by definition",
        "Each has different slope"],
       1, "Hard"),
    _q("Lerner Index measures:",
       ["Market concentration", "Degree of monopoly power",
        "Price elasticity", "Consumer surplus"],
       1, "Hard", "Lerner Index = (P-MC)/P"),
    _q("MRTS in isoquant analysis equals:",
       ["Ratio of output prices", "Ratio of marginal products (MPL/MPK)",
        "Slope of isocost line", "Average product ratio"],
       1, "Hard"),
    _q("Deadweight loss in monopoly arises because:",
       ["P>MC, leading to underproduction vs competitive output",
        "Costs are too high",
        "Consumers have too much surplus",
        "P=MC causes losses"],
       0, "Hard"),
    _q("Negative cross-price elasticity means goods are:",
       ["Substitutes", "Complements", "Independent", "Inferior"],
       1, "Hard"),
    _q("Price discrimination requires:",
       ["Perfect competition", "Market segmentation + no resale",
        "Homogeneous goods", "Identical elasticities"],
       1, "Hard"),
    _q("'Engel curve' relates:",
       ["Price and quantity demanded", "Income and quantity demanded",
        "Two inputs in production", "Consumer surplus and price"],
       1, "Hard"),
    _q("Monopsony refers to market with:",
       ["Single seller", "Single buyer", "Few sellers", "Few buyers"],
       1, "Hard"),
    _q("ATC - AVC always equals:",
       ["AFC", "MC", "Zero", "Profit margin"],
       0, "Hard"),
    _q("Consumer surplus is maximised under:",
       ["Monopoly", "Oligopoly", "Perfect competition", "Monopsony"],
       2, "Hard"),
    _q("Most product differentiation in which market structure?",
       ["Perfect competition", "Monopoly",
        "Monopolistic competition", "Oligopoly"],
       2, "Hard"),
],
"Macroeconomics": [
    _q("Nominal GDP=₹200cr, deflator=125. Real GDP=",
       ["₹160cr", "₹250cr", "₹175cr", "₹200cr"],
       0, "Hard", "Real=Nominal/Deflator×100=200/125×100=160"),
    _q("MPC=0.8. Keynesian multiplier=",
       ["4", "5", "0.2", "8"],
       1, "Hard", "1/(1-0.8)=5"),
    _q("'Stagflation' refers to:",
       ["High growth + low inflation", "High inflation + high unemployment",
        "Deflation + high employment", "Recession + falling prices"],
       1, "Hard"),
    _q("In MV=PQ, if M doubles and V,Q constant, P:",
       ["Halves", "Doubles", "Same", "Quadruples"],
       1, "Hard"),
    _q("Repo rate is the rate at which:",
       ["Banks lend to public", "RBI lends to commercial banks",
        "Banks borrow from public", "Government borrows from RBI"],
       1, "Hard"),
    _q("CRR reduced → money supply:",
       ["Decrease", "Increase", "Same", "Zero"],
       1, "Hard", "Lower CRR → banks keep less reserve → more credit."),
    _q("India's GDP base year (current National Income series):",
       ["2004-05", "2011-12", "2010-11", "2015-16"],
       1, "Hard"),
    _q("Laffer Curve illustrates:",
       ["Money supply and inflation", "Tax rate and tax revenue",
        "GDP and employment", "Interest rate and investment"],
       1, "Hard"),
    _q("'Narrow money' (M1) includes:",
       ["Currency + demand + time deposits",
        "Currency in circulation + demand deposits",
        "Only currency notes and coins",
        "All bank deposits"],
       1, "Hard"),
    _q("Phillips Curve shows:",
       ["GDP and investment", "Inflation and unemployment",
        "Trade balance and exchange rate", "Money supply and price level"],
       1, "Hard"),
    _q("Fiscal deficit =",
       ["Revenue deficit + capital expenditure",
        "Total expenditure minus total receipts excl. borrowings",
        "Revenue expenditure - revenue receipts only",
        "Budget surplus"],
       1, "Hard"),
    _q("'World Economic Outlook' published by:",
       ["World Bank", "IMF", "WTO", "UNCTAD"],
       1, "Medium"),
    _q("Gini coefficient measures:",
       ["GDP per capita", "Income inequality", "Inflation rate", "Trade openness"],
       1, "Medium"),
    _q("'Revenue deficit' is:",
       ["Total expenditure - total receipts",
        "Revenue expenditure - revenue receipts",
        "Capital expenditure - capital receipts",
        "Trade deficit"],
       1, "Hard"),
    _q("NITI Aayog replaced:",
       ["Finance Commission", "Planning Commission",
        "Economic Advisory Council", "National Development Council"],
       1, "Medium"),
    _q("Base effect in inflation refers to:",
       ["Current month price level",
        "Influence of prior year's price on current inflation",
        "RBI's target inflation",
        "Average price across states"],
       1, "Hard"),
    _q("Foreign exchange reserves held as buffer against:",
       ["Domestic inflation", "CAD / exchange rate instability",
        "Tax evasion", "Budget deficits"],
       1, "Hard"),
],
},
}  # end QUESTION_BANK

CHAPTERS = {
    "English":         ["Grammar", "Comprehension"],
    "Mathematics":     ["Algebra", "Trigonometry", "Coordinate Geometry", "Mensuration", "Arithmetic"],
    "General Science": ["Physics", "Chemistry", "Biology"],
    "History":         ["Ancient India", "Modern India"],
    "Geography":       ["Physical Geography", "World Geography"],
    "Economics":       ["Microeconomics", "Macroeconomics"],
}
SUBJECTS      = list(QUESTION_BANK.keys())
SUBJECT_ICONS = {"English":"📝","Mathematics":"📐","General Science":"🔬",
                 "History":"🏛️","Geography":"🌏","Economics":"💹"}

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "page":"landing","name":"","email":"","course":"NDA",
        "results":[],"current_subject":None,"current_chapter":None,
        "current_mode":None,"questions":[],"answers":{},
        "test_start":None,"test_duration":1200,"test_done":False,"last_result":None,
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ─────────────────────────────────────────────
# QUESTION SOURCING
# ─────────────────────────────────────────────
def fetch_opentdb(category_id=17, amount=10):
    try:
        r = requests.get(
            f"https://opentdb.com/api.php?amount={amount}&category={category_id}&type=multiple&difficulty=hard",
            timeout=5)
        data = r.json()
        if data.get("response_code") != 0:
            return []
        qs = []
        for item in data["results"]:
            q      = html.unescape(item["question"])
            correct= html.unescape(item["correct_answer"])
            wrong  = [html.unescape(x) for x in item["incorrect_answers"]]
            opts   = wrong + [correct]
            random.shuffle(opts)
            qs.append({"question":q,"options":opts,"correct":opts.index(correct),
                       "difficulty":"Hard","explanation":""})
        return qs
    except Exception:
        return []

def get_questions(subject, chapter=None, mode="chapter"):
    questions = []
    if subject == "General Science" and mode == "full":
        questions = fetch_opentdb(17, 20)
        if not questions:
            st.toast("Using backup question bank.", icon="ℹ️")

    if not questions:
        if chapter and chapter in QUESTION_BANK.get(subject, {}):
            pool = list(QUESTION_BANK[subject][chapter])
        else:
            pool = []
            for qs in QUESTION_BANK.get(subject, {}).values():
                pool.extend(qs)
        k = 20 if mode == "chapter" else len(pool)
        questions = random.sample(pool, min(k, len(pool)))

    # Shuffle option order (preserving correct answer)
    out = []
    for q in questions:
        opts       = list(q["options"])
        correct_t  = opts[q["correct"]]
        random.shuffle(opts)
        out.append({**q, "options": opts, "correct": opts.index(correct_t)})
    return out

# ─────────────────────────────────────────────
# SCORE CALCULATION
# ─────────────────────────────────────────────
def calculate_score(questions, answers):
    correct = wrong = unattempted = 0
    for i, q in enumerate(questions):
        chosen = answers.get(i)
        if chosen is None:
            unattempted += 1
        elif chosen == q["options"][q["correct"]]:
            correct += 1
        else:
            wrong += 1
    raw        = correct * CORRECT_MARKS + wrong * WRONG_MARKS
    total_marks= len(questions) * CORRECT_MARKS
    pct        = round(max(0, raw) / total_marks * 100, 1) if total_marks else 0
    return {"correct":correct,"wrong":wrong,"unattempted":unattempted,
            "raw_score":round(raw,2),"total_marks":total_marks,"percentage":pct}

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding:0.8rem 0 0.5rem;">
            <div style="font-size:2rem; font-weight:800; color:white; font-family:'Poppins',sans-serif;">
                Grade<span style="color:#7ecfff;">UP</span>
            </div>
            <div style="font-size:0.72rem; color:rgba(255,255,255,0.45);">Defence Exam Prep</div>
        </div>
        <hr style="border-color:rgba(255,255,255,0.12); margin:0.6rem 0;">
        <div style="background:rgba(255,255,255,0.08); border-radius:18px; padding:1rem;
                    border:1px solid rgba(255,255,255,0.1); text-align:center;">
            <div style="font-size:1rem; font-weight:700; color:white;">👤 {st.session_state.name}</div>
            <div style="font-size:0.75rem; color:rgba(255,255,255,0.5); word-break:break-all;">
                {st.session_state.email}
            </div>
            <div style="margin-top:0.5rem;">
                <span style="background:rgba(30,120,200,0.3); border-radius:999px;
                             padding:0.2rem 0.8rem; font-size:0.78rem; color:#a8d8ff;">
                    🎯 {st.session_state.course}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        results = st.session_state.results
        if results:
            avg = sum(r["percentage"] for r in results) / len(results)
            best= max(results, key=lambda r: r["percentage"])
            st.markdown(f"""
            <div style="text-align:center; padding:0.7rem 0; font-size:0.8rem;">
                <span style="color:rgba(255,255,255,0.5);">Tests</span>
                <span style="font-size:1.5rem; font-weight:800; color:white; display:block;">{len(results)}</span>
                <span style="color:rgba(255,255,255,0.5);">Avg</span>
                <span style="font-size:1.2rem; font-weight:700; color:#7ecfff; display:block;">{avg:.1f}%</span>
                <span style="color:rgba(255,255,255,0.5);">Best</span>
                <span style="font-size:0.85rem; color:#7fffb0; display:block;">{best['subject']}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"; st.rerun()
        if st.button("🚪 Logout", use_container_width=True):
            delete_user(st.session_state.email)
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

# ─────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────
def page_landing():
    st.markdown("""
    <div style="text-align:center; padding:2rem 0 0.5rem;">
        <div style="font-size:3.8rem; font-weight:800; color:white;
                    font-family:'Poppins',sans-serif; letter-spacing:-1px;">
            Grade<span style="color:#7ecfff;">UP</span>
        </div>
        <div style="color:rgba(255,255,255,0.72); font-size:1rem; margin-top:0.4rem;">
            Elevate Your Preparation for
            <strong style="color:#a8d8ff;">NDA, CDS &amp; Defence Exams</strong>
        </div>
        <div style="margin-top:0.8rem; display:flex; gap:0.5rem; justify-content:center; flex-wrap:wrap;">
            <span style="background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.18);
                         border-radius:999px; padding:0.2rem 0.75rem; font-size:0.78rem;">📋 PYQ-Level</span>
            <span style="background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.18);
                         border-radius:999px; padding:0.2rem 0.75rem; font-size:0.78rem;">⏱️ Timed Tests</span>
            <span style="background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.18);
                         border-radius:999px; padding:0.2rem 0.75rem; font-size:0.78rem;">📉 Negative Marking</span>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("### 🎖️ Sign In / Register")
        email = st.text_input("Email Address", placeholder="you@example.com")

        returning = None
        if email and "@" in email:
            returning = load_user(email.strip())

        if returning:
            st.markdown(f"""
            <div style="background:rgba(100,200,100,0.12); border:1px solid rgba(100,200,100,0.28);
                        border-radius:16px; padding:0.65rem 1rem; font-size:0.88rem; margin:0.4rem 0;">
                ✅ Welcome back, <strong>{returning[0]}</strong>! Course: {returning[1]}
            </div>""", unsafe_allow_html=True)
            if st.button(f"▶️  Continue as {returning[0]}", use_container_width=True):
                st.session_state.name   = returning[0]
                st.session_state.email  = email.strip()
                st.session_state.course = returning[1]
                st.session_state.page   = "dashboard"
                st.rerun()
            st.markdown("<div style='text-align:center; color:rgba(255,255,255,0.4); font-size:0.78rem; margin:0.4rem 0;'>— or update details —</div>", unsafe_allow_html=True)

        name   = st.text_input("Full Name", placeholder="Your full name")
        course = st.selectbox("Select Course", ["NDA", "CDS", "Other"])

        if st.button("🚀  Start Your Journey", use_container_width=True):
            if not name.strip():
                st.error("Please enter your name.")
            elif not email.strip() or "@" not in email:
                st.error("Please enter a valid email.")
            else:
                save_user(name.strip(), email.strip(), course)
                st.session_state.name   = name.strip()
                st.session_state.email  = email.strip()
                st.session_state.course = course
                st.session_state.page   = "dashboard"
                st.rerun()

    st.markdown(WATERMARK, unsafe_allow_html=True)


def page_dashboard():
    render_sidebar()
    st.markdown(f"""
    <h1 style="font-size:2.1rem; margin-bottom:0.2rem;">Welcome back, {st.session_state.name}! 👋</h1>
    <p style="color:rgba(255,255,255,0.55); font-size:0.9rem; margin-bottom:1.5rem;">
        Pick a subject to practise or launch a full mock test.
    </p>""", unsafe_allow_html=True)

    st.markdown("### 📚 Select a Subject")
    cols = st.columns(3)
    for i, subject in enumerate(SUBJECTS):
        with cols[i % 3]:
            if st.button(f"{SUBJECT_ICONS.get(subject,'📖')}  {subject}",
                         use_container_width=True, key=f"sub_{subject}"):
                st.session_state.current_subject = subject
                st.session_state.page = "mode_select"
                st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Performance Analysis")
    results = st.session_state.results
    if not results:
        st.info("No tests taken yet — complete a test to see your analytics!")
    else:
        df = pd.DataFrame(results)
        sc = "background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.13); border-radius:18px; padding:1rem; text-align:center;"
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.markdown(f'<div style="{sc}"><div style="font-size:2rem;font-weight:800;color:white;">{len(df)}</div><div style="font-size:0.78rem;color:rgba(255,255,255,0.5);">Tests Taken</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div style="{sc}"><div style="font-size:2rem;font-weight:800;color:#7ecfff;">{df["percentage"].mean():.1f}%</div><div style="font-size:0.78rem;color:rgba(255,255,255,0.5);">Avg Score</div></div>', unsafe_allow_html=True)
        with c3:
            best = df.groupby("subject")["percentage"].mean().idxmax()
            st.markdown(f'<div style="{sc}"><div style="font-size:1.1rem;font-weight:700;color:#7fffb0;">{best}</div><div style="font-size:0.78rem;color:rgba(255,255,255,0.5);">Best Subject</div></div>', unsafe_allow_html=True)
        with c4:
            total_w = sum(r.get("wrong",0) for r in results)
            st.markdown(f'<div style="{sc}"><div style="font-size:2rem;font-weight:800;color:#ff9090;">{total_w}</div><div style="font-size:0.78rem;color:rgba(255,255,255,0.5);">Wrong Answers</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        df["test_num"] = range(1, len(df)+1)
        ax = alt.Axis(labelColor="rgba(255,255,255,0.65)", titleColor="rgba(255,255,255,0.65)", gridColor="rgba(255,255,255,0.07)")
        line = alt.Chart(df).mark_line(point={"filled":True,"size":55}, strokeWidth=2.5, color="#7ecfff").encode(
            x=alt.X("test_num:Q", title="Test #", axis=ax),
            y=alt.Y("percentage:Q", title="Score %", scale=alt.Scale(domain=[0,100]), axis=ax),
            tooltip=["test_num","subject","mode","percentage","correct","wrong"]
        ).properties(title=alt.TitleParams("Score Trend",color="white",font="Poppins"),
                     background="transparent", height=200).configure_view(strokeWidth=0).configure_axis(domain=False)
        st.altair_chart(line, use_container_width=True)

        sub_df = df.groupby("subject")["percentage"].mean().reset_index()
        sub_df.columns = ["Subject","Average %"]
        bar = alt.Chart(sub_df).mark_bar(cornerRadiusTopLeft=8,cornerRadiusTopRight=8).encode(
            x=alt.X("Subject:N",axis=ax),
            y=alt.Y("Average %:Q",scale=alt.Scale(domain=[0,100]),axis=ax),
            color=alt.Color("Average %:Q",scale=alt.Scale(scheme="teals"),legend=None),
            tooltip=["Subject","Average %"]
        ).properties(title=alt.TitleParams("Subject-wise Average",color="white",font="Poppins"),
                     background="transparent", height=200).configure_view(strokeWidth=0).configure_axis(domain=False)
        st.altair_chart(bar, use_container_width=True)

    st.markdown(WATERMARK, unsafe_allow_html=True)


def page_mode_select():
    render_sidebar()
    subject = st.session_state.current_subject
    st.markdown(f"<h2>{SUBJECT_ICONS.get(subject,'📖')} {subject}</h2>", unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        st.markdown("""<div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.13);
                    border-radius:22px;padding:1.6rem;text-align:center;min-height:155px;">
            <div style="font-size:2.3rem;">📋</div>
            <div style="font-size:1.05rem;font-weight:700;color:white;margin-top:0.4rem;">Chapter-wise Practice</div>
            <div style="color:rgba(255,255,255,0.45);font-size:0.8rem;margin-top:0.3rem;">
                20 Qs · 20 Min · Focused drill</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Start Chapter Test →", key="btn_ch", use_container_width=True):
            st.session_state.current_mode = "chapter"
            st.session_state.page = "chapter_select"; st.rerun()

    with c2:
        st.markdown("""<div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.13);
                    border-radius:22px;padding:1.6rem;text-align:center;min-height:155px;">
            <div style="font-size:2.3rem;">🏆</div>
            <div style="font-size:1.05rem;font-weight:700;color:white;margin-top:0.4rem;">Full Subject Mock</div>
            <div style="color:rgba(255,255,255,0.45);font-size:0.8rem;margin-top:0.3rem;">
                All chapters · 60 Min · Exam simulation</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Start Full Mock →", key="btn_full", use_container_width=True):
            qs = get_questions(subject, chapter=None, mode="full")
            st.session_state.current_mode     = "full"
            st.session_state.current_chapter  = None
            st.session_state.questions        = qs
            st.session_state.answers          = {}
            st.session_state.test_start       = time.time()
            st.session_state.test_duration    = 3600
            st.session_state.test_done        = False
            st.session_state.page             = "test"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to Dashboard"): st.session_state.page = "dashboard"; st.rerun()
    st.markdown(WATERMARK, unsafe_allow_html=True)


def page_chapter_select():
    render_sidebar()
    subject  = st.session_state.current_subject
    st.markdown(f"<h2>📑 Chapter Selection — {subject}</h2>", unsafe_allow_html=True)
    chapter  = st.selectbox("Select Chapter", CHAPTERS.get(subject, []))
    c1,c2,c3 = st.columns([1,2,1])
    with c2:
        if st.button("▶️  Begin Chapter Test", use_container_width=True):
            qs = get_questions(subject, chapter=chapter, mode="chapter")
            st.session_state.current_chapter = chapter
            st.session_state.questions       = qs
            st.session_state.answers         = {}
            st.session_state.test_start      = time.time()
            st.session_state.test_duration   = 1200
            st.session_state.test_done       = False
            st.session_state.page            = "test"; st.rerun()
    if st.button("← Back"): st.session_state.page = "mode_select"; st.rerun()
    st.markdown(WATERMARK, unsafe_allow_html=True)


def page_test():
    render_sidebar()
    subject   = st.session_state.current_subject
    chapter   = st.session_state.current_chapter
    mode      = st.session_state.current_mode
    questions = st.session_state.questions
    elapsed   = time.time() - st.session_state.test_start
    remaining = max(0, st.session_state.test_duration - elapsed)

    if remaining == 0 and not st.session_state.test_done:
        st.session_state.test_done = True
        _save_result(); st.session_state.page = "results"; st.rerun()

    mins, secs = int(remaining//60), int(remaining%60)
    t_ok = remaining > 300
    timer_bg  = "rgba(44,100,83,0.3)" if t_ok else "rgba(255,80,80,0.25)"
    timer_bdr = "rgba(80,200,140,0.4)" if t_ok else "rgba(255,120,120,0.4)"
    label = f"{subject} — {chapter}" if chapter else f"{subject} (Full Mock)"

    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
                flex-wrap:wrap;gap:0.5rem;margin-bottom:0.8rem;">
        <div>
            <h2 style="margin:0;font-size:1.5rem;">{label}</h2>
            <span style="color:rgba(255,255,255,0.45);font-size:0.8rem;">
                {mode.capitalize()} · {len(questions)} Qs ·
                <strong style="color:#ffe97d;">+{CORRECT_MARKS} / {WRONG_MARKS}</strong> marks
            </span>
        </div>
        <div style="background:{timer_bg};border:1.5px solid {timer_bdr};border-radius:999px;
                    padding:0.4rem 1.2rem;font-size:1.05rem;font-weight:700;color:white;
                    backdrop-filter:blur(8px);">
            ⏱️ {mins:02d}:{secs:02d}
        </div>
    </div>
    <div class="marking-note">
        ⚠️ <strong>+{CORRECT_MARKS}</strong> correct &nbsp;|&nbsp;
        <strong>{WRONG_MARKS}</strong> wrong &nbsp;|&nbsp;
        <strong>0</strong> unattempted — skip if unsure!
    </div>""", unsafe_allow_html=True)

    with st.form("test_form"):
        for i, q in enumerate(questions):
            diff  = q.get("difficulty","Hard")
            dc    = "diff-hard" if diff=="Hard" else "diff-medium"
            st.markdown(f"""
            <div class="q-card">
                <div style="font-size:0.73rem;color:rgba(255,255,255,0.4);">
                    Q{i+1}/{len(questions)}
                    <span class="diff-badge {dc}">{diff}</span>
                </div>
                <div style="font-weight:600;color:white;font-size:0.95rem;margin-top:0.3rem;">
                    {q['question']}
                </div>
            </div>""", unsafe_allow_html=True)
            st.radio(f"q_{i}", q["options"], index=None, key=f"radio_{i}", label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)

        if st.form_submit_button("✅  Submit Test", use_container_width=True):
            for i in range(len(questions)):
                st.session_state.answers[i] = st.session_state.get(f"radio_{i}")
            _save_result(); st.session_state.page = "results"; st.rerun()

    time.sleep(1); st.rerun()


def _save_result():
    questions = st.session_state.questions
    answers   = {}
    for i in range(len(questions)):
        answers[i] = st.session_state.get(f"radio_{i}", st.session_state.answers.get(i))
    sd = calculate_score(questions, answers)
    result = {
        "date":        datetime.datetime.now().strftime("%d %b %Y %H:%M"),
        "subject":     st.session_state.current_subject,
        "chapter":     st.session_state.current_chapter or "Full",
        "mode":        st.session_state.current_mode,
        "percentage":  sd["percentage"], "raw_score":   sd["raw_score"],
        "total_marks": sd["total_marks"],"correct":     sd["correct"],
        "wrong":       sd["wrong"],       "unattempted": sd["unattempted"],
        "time_taken":  int(time.time() - st.session_state.test_start),
        "answers":     answers,
    }
    st.session_state.results.append(result)
    st.session_state.last_result = result


def page_results():
    render_sidebar()
    r = st.session_state.last_result
    if not r: st.session_state.page = "dashboard"; st.rerun()

    pct   = r["percentage"]
    mt    = r["time_taken"]//60
    st_   = r["time_taken"]%60
    emoji = "🏆" if pct>=75 else "👍" if pct>=50 else "📚"
    clr   = "#7fffb0" if pct>=75 else "#ffd97d" if pct>=50 else "#ff9090"
    verd  = "Excellent!" if pct>=75 else "Good effort!" if pct>=50 else "Keep Practising!"

    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.18);
                border-radius:28px;padding:2rem;text-align:center;margin-bottom:1.2rem;">
        <div style="font-size:3rem;">{emoji}</div>
        <div style="font-size:0.85rem;color:rgba(255,255,255,0.5);">{r['subject']} · {r['chapter']} · {r['date']}</div>
        <div style="font-size:2.8rem;font-weight:800;color:{clr};line-height:1.1;margin-top:0.4rem;">
            {r['raw_score']} / {r['total_marks']}
        </div>
        <div style="font-size:1.8rem;font-weight:700;color:white;">{pct}%</div>
        <div style="font-size:1rem;font-weight:600;color:{clr};margin-top:0.3rem;">{verd}</div>
        <div style="margin-top:0.8rem;display:flex;gap:0.6rem;justify-content:center;flex-wrap:wrap;">
            <span style="background:rgba(100,200,100,0.18);border:1px solid rgba(100,200,100,0.28);
                         border-radius:999px;padding:0.25rem 0.9rem;font-size:0.82rem;">✅ {r['correct']} correct</span>
            <span style="background:rgba(255,80,80,0.18);border:1px solid rgba(255,80,80,0.28);
                         border-radius:999px;padding:0.25rem 0.9rem;font-size:0.82rem;">❌ {r['wrong']} wrong</span>
            <span style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.18);
                         border-radius:999px;padding:0.25rem 0.9rem;font-size:0.82rem;">⬜ {r['unattempted']} skipped</span>
            <span style="background:rgba(100,150,255,0.18);border:1px solid rgba(100,150,255,0.28);
                         border-radius:999px;padding:0.25rem 0.9rem;font-size:0.82rem;">⏱️ {mt}m {st_}s</span>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("### 📋 Answer Review")
    questions = st.session_state.questions
    user_ans  = r["answers"]

    for i, q in enumerate(questions):
        chosen    = user_ans.get(i)
        correct_t = q["options"][q["correct"]]
        is_ok     = chosen == correct_t
        skipped   = chosen is None
        bg        = "rgba(100,200,100,0.1)" if is_ok else ("rgba(255,255,255,0.04)" if skipped else "rgba(255,80,80,0.1)")
        ico       = "✅" if is_ok else ("⬜" if skipped else "❌")
        wrong_html= "" if (is_ok or skipped) else f'<div style="font-size:0.83rem;color:#7fffb0;margin-top:0.2rem;">✔ {correct_t}</div>'
        exp       = q.get("explanation","")
        exp_html  = f'<div style="font-size:0.75rem;color:rgba(255,225,100,0.72);margin-top:0.25rem;">💡 {exp}</div>' if exp else ""

        st.markdown(f"""
        <div style="background:{bg};border-radius:16px;padding:0.9rem 1.1rem;
                    border:1px solid rgba(255,255,255,0.09);margin-bottom:0.5rem;">
            <div style="font-size:0.72rem;color:rgba(255,255,255,0.35);">Q{i+1}</div>
            <div style="font-weight:600;color:white;font-size:0.93rem;margin-bottom:0.3rem;">{ico} {q['question']}</div>
            <div style="font-size:0.83rem;color:rgba(255,255,255,0.65);">Your answer: <strong>{chosen if chosen else 'Not answered'}</strong></div>
            {wrong_html}{exp_html}
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        if st.button("🏠 Back to Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"; st.rerun()
    with c2:
        if st.button("🔄 Retry Subject", use_container_width=True):
            st.session_state.page = "mode_select"; st.rerun()
    st.markdown(WATERMARK, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="GradeUP – Defence Exam Prep",
        page_icon="🎖️", layout="wide",
        initial_sidebar_state="expanded"
    )
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    init_db()
    init_state()

    p = st.session_state.page
    if   p == "landing":        page_landing()
    elif p == "dashboard":      page_dashboard()
    elif p == "mode_select":    page_mode_select()
    elif p == "chapter_select": page_chapter_select()
    elif p == "test":           page_test()
    elif p == "results":        page_results()
    else:
        st.session_state.page = "landing"; st.rerun()

if __name__ == "__main__":
    main()
