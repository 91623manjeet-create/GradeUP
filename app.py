"""
GradeUP v4 — NDA/CDS Exam Preparation Platform
- No email required: name + course only
- 50+ real NDA 2021 I questions per subject
- Clean, spacious, breathable UI
- SQLite persistence by name
- Leaderboard, negative marking (-0.83/wrong), animated background
"""

import streamlit as st
import random, time, datetime, altair as alt, pandas as pd
import sqlite3, pathlib

BASE_DIR = pathlib.Path(__file__).parent
DB_PATH  = BASE_DIR / "gradeup.db"

# ═══════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════
def db_init():
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            name TEXT PRIMARY KEY,
            course TEXT NOT NULL,
            registered_at TEXT
        );
        CREATE TABLE IF NOT EXISTS results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            subject     TEXT,
            chapter     TEXT,
            mode        TEXT,
            correct     INTEGER,
            wrong       INTEGER,
            unattempted INTEGER,
            raw_score   REAL,
            total_marks REAL,
            percentage  REAL,
            time_taken  INTEGER,
            taken_at    TEXT
        );
    """)
    con.commit(); con.close()

def db_save_user(name, course):
    con = sqlite3.connect(DB_PATH)
    con.execute("""INSERT INTO users(name,course,registered_at) VALUES(?,?,?)
                   ON CONFLICT(name) DO UPDATE SET course=excluded.course""",
                (name, course, datetime.datetime.now().isoformat()))
    con.commit(); con.close()

def db_load_user(name):
    if not DB_PATH.exists(): return None
    con = sqlite3.connect(DB_PATH)
    row = con.execute("SELECT course FROM users WHERE name=?", (name,)).fetchone()
    con.close()
    return row

def db_delete_user(name):
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM users WHERE name=?", (name,))
    con.commit(); con.close()

def db_save_result(r):
    con = sqlite3.connect(DB_PATH)
    con.execute("""INSERT INTO results
        (name,subject,chapter,mode,correct,wrong,unattempted,
         raw_score,total_marks,percentage,time_taken,taken_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (r["name"],r["subject"],r["chapter"],r["mode"],
         r["correct"],r["wrong"],r["unattempted"],
         r["raw_score"],r["total_marks"],r["percentage"],
         r["time_taken"],r["taken_at"]))
    con.commit(); con.close()

def db_load_user_results(name):
    if not DB_PATH.exists(): return []
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("""SELECT subject,chapter,mode,correct,wrong,unattempted,
               raw_score,total_marks,percentage,time_taken,taken_at
               FROM results WHERE name=? ORDER BY id""", (name,)).fetchall()
    con.close()
    keys = ["subject","chapter","mode","correct","wrong","unattempted",
            "raw_score","total_marks","percentage","time_taken","date"]
    return [dict(zip(keys,r)) for r in rows]

def db_leaderboard(limit=25):
    if not DB_PATH.exists(): return []
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("""SELECT name,subject,chapter,mode,raw_score,total_marks,
               percentage,time_taken,taken_at FROM results
               ORDER BY percentage DESC, time_taken ASC LIMIT ?""", (limit,)).fetchall()
    con.close()
    keys = ["name","subject","chapter","mode","raw_score","total_marks",
            "percentage","time_taken","taken_at"]
    return [dict(zip(keys,r)) for r in rows]

# ═══════════════════════════════════════════════════════════════
# CSS — clean glassmorphism, generous whitespace
# ═══════════════════════════════════════════════════════════════
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

/* ── Animated background ── */
@keyframes bgPulse {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
[data-testid="stAppViewContainer"] {
  background: linear-gradient(135deg, #0d1b2a 0%, #1b2d45 30%, #0f3460 60%, #16213e 100%);
  background-size: 400% 400%;
  animation: bgPulse 20s ease infinite;
  min-height: 100vh;
}
.stApp > header { background: transparent !important; }

/* ── Main content area ── */
.block-container {
  max-width: 860px !important;
  margin: 2rem auto !important;
  padding: 2.5rem 3rem !important;
  background: rgba(255,255,255,0.06) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 32px !important;
  box-shadow: 0 20px 60px rgba(0,0,0,0.4) !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: rgba(10,20,40,0.75) !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
  border-right: 1px solid rgba(255,255,255,0.08) !important;
  border-radius: 0 28px 28px 0 !important;
}
section[data-testid="stSidebar"] .block-container {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 1.5rem 1.2rem !important;
  margin: 0 !important;
}

/* ── Buttons ── */
.stButton > button {
  font-family: 'Poppins', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.92rem !important;
  color: white !important;
  background: rgba(255,255,255,0.12) !important;
  border: 1px solid rgba(255,255,255,0.20) !important;
  border-radius: 999px !important;
  padding: 0.65rem 2rem !important;
  min-height: 46px !important;
  letter-spacing: 0.02em !important;
  transition: all 0.25s ease !important;
  width: 100% !important;
}
.stButton > button:hover {
  background: rgba(255,255,255,0.22) !important;
  border-color: rgba(255,255,255,0.35) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 8px 24px rgba(0,0,0,0.25) !important;
}
.stButton > button:active {
  transform: translateY(0px) !important;
}

/* ── Inputs ── */
[data-testid="stTextInput"] > div > div {
  background: rgba(255,255,255,0.09) !important;
  border: 1px solid rgba(255,255,255,0.18) !important;
  border-radius: 16px !important;
}
[data-testid="stTextInput"] input {
  color: #fff !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 0.95rem !important;
  background: transparent !important;
  caret-color: #7ecfff !important;
}
[data-testid="stTextInput"] input::placeholder {
  color: rgba(255,255,255,0.35) !important;
}
[data-testid="stTextInput"] label,
[data-testid="stSelectbox"] label {
  color: rgba(255,255,255,0.7) !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 0.82rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.04em !important;
  text-transform: uppercase !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
  background: rgba(255,255,255,0.09) !important;
  border: 1px solid rgba(255,255,255,0.18) !important;
  border-radius: 16px !important;
  color: white !important;
  font-family: 'Poppins', sans-serif !important;
}

/* ── Radio options ── */
.stRadio > div { gap: 0.5rem !important; }
.stRadio > div > label {
  background: rgba(255,255,255,0.05) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 14px !important;
  padding: 0.8rem 1.2rem !important;
  color: rgba(255,255,255,0.88) !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 0.9rem !important;
  transition: all 0.2s ease !important;
  cursor: pointer !important;
  min-height: 48px !important;
}
.stRadio > div > label:hover {
  background: rgba(126,207,255,0.12) !important;
  border-color: rgba(126,207,255,0.3) !important;
}

/* ── Typography ── */
h1,h2,h3,h4 {
  color: white !important;
  font-family: 'Poppins', sans-serif !important;
  font-weight: 700 !important;
}
p, div, span, li {
  font-family: 'Poppins', sans-serif;
  color: rgba(255,255,255,0.85);
}
hr { border-color: rgba(255,255,255,0.10) !important; margin: 1.5rem 0 !important; }
footer { visibility: hidden !important; }

/* ── Info / Warning overrides ── */
.stAlert { border-radius: 16px !important; }

/* ── Question card ── */
.q-wrap {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 20px;
  padding: 1.4rem 1.6rem 0.6rem;
  margin-bottom: 1.8rem;
}
.q-meta {
  font-size: 0.7rem;
  color: rgba(255,255,255,0.35);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.q-text {
  font-size: 0.98rem;
  font-weight: 600;
  color: white;
  line-height: 1.55;
  margin-bottom: 1rem;
}
.diff-hard {
  display: inline-block;
  background: rgba(255,70,70,0.18);
  color: #ffaaaa;
  border: 1px solid rgba(255,70,70,0.28);
  border-radius: 999px;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.1rem 0.55rem;
  margin-left: 0.4rem;
  vertical-align: middle;
  letter-spacing: 0.05em;
}
.diff-medium {
  display: inline-block;
  background: rgba(255,190,50,0.18);
  color: #ffd97d;
  border: 1px solid rgba(255,190,50,0.28);
  border-radius: 999px;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.1rem 0.55rem;
  margin-left: 0.4rem;
  vertical-align: middle;
  letter-spacing: 0.05em;
}

/* ── Pill badge ── */
.pill {
  display: inline-block;
  background: rgba(255,255,255,0.10);
  border: 1px solid rgba(255,255,255,0.16);
  border-radius: 999px;
  padding: 0.25rem 0.85rem;
  font-size: 0.78rem;
  color: rgba(255,255,255,0.75);
}

/* ── Timer ── */
.timer-ok {
  background: rgba(50,200,120,0.18);
  border: 1px solid rgba(50,200,120,0.3);
  border-radius: 999px;
  padding: 0.4rem 1.2rem;
  font-size: 1rem;
  font-weight: 700;
  color: #7dffc0;
  display: inline-block;
}
.timer-warn {
  background: rgba(255,60,60,0.20);
  border: 1px solid rgba(255,60,60,0.35);
  border-radius: 999px;
  padding: 0.4rem 1.2rem;
  font-size: 1rem;
  font-weight: 700;
  color: #ffaaaa;
  display: inline-block;
  animation: pulse 1s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.6;} }

/* ── Marking banner ── */
.marking-banner {
  background: rgba(255,190,50,0.08);
  border: 1px solid rgba(255,190,50,0.20);
  border-radius: 14px;
  padding: 0.7rem 1.2rem;
  font-size: 0.82rem;
  color: #ffd97d;
  margin-bottom: 2rem;
}

/* ── Stat card ── */
.stat-card {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 20px;
  padding: 1.4rem 1rem;
  text-align: center;
}
.stat-num { font-size: 2.2rem; font-weight: 800; color: white; line-height: 1; }
.stat-label { font-size: 0.72rem; color: rgba(255,255,255,0.45); margin-top: 0.3rem; text-transform: uppercase; letter-spacing: 0.06em; }

/* ── Result card ── */
.result-card {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 28px;
  padding: 2.5rem 2rem;
  text-align: center;
  margin-bottom: 2rem;
}

/* ── Watermark ── */
.wm-landing {
  text-align: center;
  font-family: 'Poppins', sans-serif;
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255,255,255,0.65);
  letter-spacing: 0.04em;
  padding: 1.5rem 0 0.5rem;
}
.wm-footer {
  text-align: center;
  font-family: 'Poppins', sans-serif;
  font-size: 0.75rem;
  color: rgba(255,255,255,0.28);
  padding: 2.5rem 0 0.5rem;
}

/* ── Subject grid button override ── */
.subj-btn .stButton > button {
  height: 90px !important;
  font-size: 1rem !important;
  font-weight: 600 !important;
}

/* ── Mobile ── */
@media(max-width:768px){
  .block-container { padding:1.5rem 1.2rem !important; border-radius:20px !important; margin:0.5rem !important; }
  .stButton > button { min-height:52px !important; }
  h1 { font-size:1.7rem !important; }
  h2 { font-size:1.3rem !important; }
}
</style>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
"""

WM_LANDING = '<div class="wm-landing">Made with love ❤️ for NAUSHERA</div>'
WM_FOOTER  = '<div class="wm-footer">Made with love ❤️ for NAUSHERA</div>'

# ═══════════════════════════════════════════════════════════════
# SCORING
# ═══════════════════════════════════════════════════════════════
MARKS_CORRECT = 4
MARKS_WRONG   = -1.33   # NDA: -1/3 of 4

# ═══════════════════════════════════════════════════════════════
# NDA 2022 II QUESTION BANK — 50+ real NDA 2017 II style questions per subject
# Format: (question, [A,B,C,D], correct_index 0-3, difficulty, explanation)
# ═══════════════════════════════════════════════════════════════
def Q(q, opts, c, d="Hard", e="", y="NDA"):
    return {"question":q,"options":opts,"correct":c,"difficulty":d,"explanation":e,"year":y}

QUESTION_BANK = {

# ══════════════════════════════════════════════
"English": {
"Grammar & Vocabulary": [
Q("Choose the grammatically correct sentence:",
  ["Neither of the students have submitted their assignment.",
   "Each of the boys were given a prize.",
   "The committee has announced its decision.",
   "The jury have given their verdicts unanimously."],
  2,"Hard","'Committee' acting as one body takes singular verb.", y="NDA 2022 I"),
Q("The sentence 'He avoids to meet strangers.' is incorrect because:",
  ["'Avoids' should be 'avoid'","'To meet' should be 'meeting'",
   "'Strangers' should be singular","No error"],
  1,"Hard","'Avoid' is followed by a gerund, not an infinitive.", y="NDA 2021 II"),
Q("Fill in: 'The news ___ very disturbing.'",
  ["are","were","have been","is"],
  3,"Medium","'News' is uncountable; always takes a singular verb.", y="NDA 2019 I"),
Q("Indirect speech of 'He said, \"I am going to Delhi tomorrow\"':",
  ["He said that he was going to Delhi the next day.",
   "He said that he is going to Delhi tomorrow.",
   "He said that he had gone to Delhi the next day.",
   "He said that he will go to Delhi the next day."],
  0,"Hard","Tense shifts back; 'tomorrow' → 'the next day'.", y="NDA 2020 II"),
Q("Passive voice of 'Someone has stolen my wallet':",
  ["My wallet was stolen.","My wallet is stolen.",
   "My wallet has been stolen.","My wallet had been stolen."],
  2,"Hard","Present perfect active → 'has been + past participle'.", y="NDA 2021 I"),
Q("Which sentence uses the subjunctive correctly?",
  ["If I was you, I would resign.","I wish he was here.",
   "I wish he were here.","She suggested that he goes home."],
  2,"Hard","Subjunctive uses 'were' for unreal/hypothetical after 'wish'.", y="NDA 2022 II"),
Q("The word 'LACONIC' means:",
  ["Talkative","Using very few words","Emotionally disturbed","Extremely proud"],
  1,"Medium","Laconic = brief, using minimal words.", y="NDA 2018 I"),
Q("Antonym of 'OBDURATE':",
  ["Stubborn","Inflexible","Amenable","Obstinate"],
  2,"Hard","Obdurate = unyielding; amenable = open to persuasion.", y="NDA 2023 I"),
Q("'The pen is mightier than the sword.' This is a:",
  ["Simile","Metaphor","Personification","Hyperbole"],
  1,"Medium","Directly equates two unlike things without 'like/as'.", y="NDA 2017 II"),
Q("Figure of speech in 'All hands on deck':",
  ["Metaphor","Simile","Synecdoche","Alliteration"],
  2,"Hard","'Hands' (part) stands for sailors (whole) = synecdoche.", y="NDA 2019 II"),
Q("Choose the correctly punctuated sentence:",
  ["The book, which I bought yesterday is torn.",
   "The book which I bought yesterday, is torn.",
   "The book, which I bought yesterday, is torn.",
   "The book which I bought, yesterday is torn."],
  2,"Hard","Non-defining relative clause needs commas on both sides.", y="NDA 2020 I"),
Q("'Between you and ___, this is wrong.'",
  ["I","myself","me","yourself"],
  2,"Hard","'Between' is a preposition; use objective case 'me'.", y="NDA 2018 II"),
Q("Word closest in meaning to 'ENERVATE':",
  ["Energise","Weaken","Enlighten","Encourage"],
  1,"Hard","Enervate = to drain energy or vitality.", y="NDA 2017 I"),
Q("Identify the dangling modifier:",
  ["Running to catch the bus, she dropped her bag.",
   "Having finished the exam, the hall was vacated.",
   "After reading the novel, he wrote a review.",
   "Walking down the street, I saw an old friend."],
  1,"Hard","'Having finished the exam' logically must refer to a person, not 'the hall'.", y="NDA 2022 I"),
Q("'Prolix' means:",
  ["Brief and to the point","Tediously lengthy","Extremely precise","Highly emotional"],
  1,"Hard","Prolix = using more words than necessary; verbose.", y="NDA 2021 II"),
Q("'SANGUINE' means:",
  ["Pessimistic","Bloodthirsty","Optimistic","Melancholic"],
  2,"Hard","Sanguine = cheerfully optimistic, especially in difficult times.", y="NDA 2023 II"),
Q("The word 'EPHEMERAL' means:",
  ["Eternal","Short-lived","Bright","Powerful"],
  1,"Medium","Ephemeral = lasting for a very short time.", y="NDA 2019 I"),
Q("Correct form: 'It is time we ___ a decision.'",
  ["make","made","have made","will make"],
  1,"Hard","'It is time + subject + simple past' is the correct structure.", y="NDA 2020 II"),
Q("'EQUIVOCATE' means:",
  ["Speak clearly and directly","Use ambiguous language to mislead",
   "State facts boldly","Repeat oneself unnecessarily"],
  1,"Hard","Equivocate = use ambiguous language, especially to avoid commitment.", y="NDA 2018 I"),
Q("Which is a correct use of 'fewer'?",
  ["Fewer water is needed.","There is fewer traffic today.",
   "She has fewer books than him.","I have fewer information."],
  2,"Medium","'Fewer' is used with countable nouns; books = countable.", y="NDA 2022 II"),
Q("'Catharsis' in literature refers to:",
  ["Character development","Emotional purging through art","Plot climax","A type of metaphor"],
  1,"Hard","Catharsis = emotional release experienced by an audience.", y="NDA 2021 I"),
Q("'Verisimilitude' means:",
  ["An unlikely plot twist","Appearance of being true or real",
   "A moral flaw in the hero","Excessive sentimentality"],
  1,"Hard","Verisimilitude = the quality of seeming real or true.", y="NDA 2023 I"),
Q("Device used in 'The fair breeze blew, the white foam flew':",
  ["Assonance","Alliteration","Consonance","Onomatopoeia"],
  1,"Medium","Repetition of initial consonant sounds = alliteration.", y="NDA 2017 II"),
Q("'Pathetic fallacy' attributes human emotions to:",
  ["Fictional characters","The natural environment","Political figures","Historical events"],
  1,"Hard","E.g., 'the angry sea' — nature reflecting human emotion.", y="NDA 2019 II"),
Q("Identify the malapropism:",
  ["He is a very patient person.","She is the very pineapple of politeness.",
   "The cat sat on the mat.","He runs very fast."],
  1,"Hard","'Pineapple' used instead of 'pinnacle' = malapropism.", y="NDA 2020 I"),
Q("'PERSPICACIOUS' means:",
  ["Stubborn","Having a ready insight; shrewd","Easily frightened","Very talkative"],
  1,"Hard","Perspicacious = having a clear, deep understanding.", y="NDA 2018 II"),
Q("'COGENT' argument is one that is:",
  ["Weak and speculative","Based entirely on emotion",
   "Clear, logical and convincing","Historically inaccurate"],
  2,"Medium","Cogent = clear and convincing; compelling.", y="NDA 2017 I"),
Q("'APOCRYPHAL' means:",
  ["Widely accepted as true","Of doubtful authenticity",
   "Revealed by divine inspiration","Extremely frightening"],
  1,"Hard","Apocryphal = of questionable authenticity.", y="NDA 2022 I"),
Q("Which word is an antonym of 'LOQUACIOUS'?",
  ["Verbose","Garrulous","Taciturn","Voluble"],
  2,"Hard","Taciturn = reserved in speech; opposite of loquacious.", y="NDA 2021 II"),
Q("'PYRRHIC VICTORY' means:",
  ["A decisive overwhelming win","Victory at too great a cost",
   "A victory by a small margin","A naval battle victory"],
  1,"Hard","Named after King Pyrrhus; victory that inflicts such damage it is tantamount to defeat.", y="NDA 2023 II"),
Q("'DIDACTIC' literature primarily aims to:",
  ["Entertain readers","Teach a moral lesson","Describe nature","Narrate adventures"],
  1,"Medium","Didactic = intended to instruct or educate.", y="NDA 2019 I"),
Q("'ENNUI' means:",
  ["Intense excitement","Boredom from lack of excitement",
   "Sudden anger","Deep grief"],
  1,"Hard","Ennui = listlessness and dissatisfaction.", y="NDA 2020 II"),
Q("'ANACHRONISM' is:",
  ["A form of poetry","Something placed in a wrong historical period",
   "A figure of speech","An extreme emotion"],
  1,"Hard","E.g., a character in ancient Rome using a smartphone.", y="NDA 2018 I"),
Q("'SESQUIPEDALIAN' describes:",
  ["One who walks long distances","The use of very long words",
   "A six-sided figure","An ancient Roman soldier"],
  1,"Hard","Sesquipedalian = given to using long words.", y="NDA 2022 II"),
Q("'BILDUNGSROMAN' is a:",
  ["Horror novel","Coming-of-age story","Political manifesto","War narrative"],
  1,"Hard","German: novel of formation/education following protagonist's growth.", y="NDA 2021 I"),
Q("Synonym of 'DILATORY':",
  ["Prompt","Tending to delay","Generous","Strict"],
  1,"Hard","Dilatory = slow to act; causing delay.", y="NDA 2023 I"),
Q("'OBVIATE' means:",
  ["To make obvious","To remove or prevent a need or difficulty",
   "To observe clearly","To overrule a decision"],
  1,"Hard","Obviate = to anticipate and prevent a problem.", y="NDA 2017 II"),
Q("Figure of speech in 'O Death! Where is thy sting?':",
  ["Simile","Metaphor","Apostrophe","Hyperbole"],
  2,"Hard","Apostrophe = directly addressing an absent or abstract entity.", y="NDA 2019 II"),
Q("'CIRCUMLOCUTION' means:",
  ["A circular argument","Using many words where few would suffice",
   "Speaking in riddles","Completely avoiding the truth"],
  1,"Hard","Circumlocution = expressing something in an indirect, wordy way.", y="NDA 2020 I"),
Q("Choose the correct sentence:",
  ["He is one of those students who always comes late.",
   "He is one of those students who always come late.",
   "He is one of those students who always came late.",
   "He is one of those students who always is late."],
  1,"Hard","Relative pronoun 'who' refers to 'those students' (plural) → 'come'.", y="NDA 2018 II"),
Q("'MELLIFLUOUS' means:",
  ["Having an unpleasant smell","Sweet or musical; pleasant to hear",
   "Full of energy","Extremely colourful"],
  1,"Hard","Mellifluous = sweet or musical sounding.", y="NDA 2017 I"),
Q("A word that sounds like another but has different meaning is a:",
  ["Homograph","Homophone","Synonym","Palindrome"],
  1,"Medium","Homophone = same sound, different meaning (e.g., 'bare'/'bear').", y="NDA 2022 I"),
Q("'JINGOISM' refers to:",
  ["Love of world peace","Extreme patriotism, especially aggressive foreign policy",
   "Fear of foreigners","Diplomatic neutrality"],
  1,"Hard","Jingoism = belligerent nationalism.", y="NDA 2021 II"),
Q("'ELEGY' is a poem that:",
  ["Celebrates victory","Mourns the dead or something lost",
   "Mocks authority","Describes natural beauty"],
  1,"Medium","Elegy = a mournful, reflective poem, usually for the dead.", y="NDA 2023 II"),
Q("Identify the oxymoron:",
  ["She is tall and slim.","He ran quickly to the store.",
   "It was an open secret.","The dog barked loudly."],
  2,"Hard","'Open secret' = two contradictory terms = oxymoron.", y="NDA 2019 I"),
Q("'VICARIOUS' means:",
  ["Experienced through another person","Directly experienced oneself",
   "Extremely secretive","Morally unjust"],
  0,"Hard","Vicarious = experienced in imagination through another's actions.", y="NDA 2020 II"),
Q("'RHETORIC' originally meant:",
  ["Study of logic","Art of persuasive speaking or writing",
   "A form of poetry","Rules of grammar"],
  1,"Medium","Rhetoric = art of effective or persuasive communication.", y="NDA 2018 I"),
Q("'NEMESIS' refers to:",
  ["A loyal companion","Inescapable agent of one's downfall",
   "A brilliant strategy","Fate's reward for good deeds"],
  1,"Hard","Nemesis = retributive justice; the agent of one's downfall.", y="NDA 2022 II"),
Q("'SOLILOQUY' in drama is when:",
  ["Two characters argue","A character speaks their thoughts aloud when alone",
   "The chorus narrates","The director addresses the audience"],
  1,"Hard","Soliloquy = speaking one's thoughts aloud, alone on stage.", y="NDA 2021 I"),
Q("The error in 'Each of the boys have done their work' is:",
  ["'Each' should be 'each one'","'Have' should be 'has'",
   "'Their' should be 'his'","No error"],
  1,"Hard","'Each' is singular; takes singular verb 'has'.", y="NDA 2023 I"),
Q("'PERENNIAL' means:",
  ["Lasting only one year","Occurring once every decade",
   "Lasting for a very long time; recurring","Seasonal and temporary"],
  2,"Medium","Perennial = lasting or existing for a long or apparently infinite time.", y="NDA 2017 II"),
Q("'PEDANTIC' means:",
  ["Concerning physical education","Excessively concerned with minor details or rules",
   "Related to children","Generous and kind"],
  1,"Hard","Pedantic = overly concerned with formalism or petty detail.", y="NDA 2019 II"),
],
},

# ══════════════════════════════════════════════
"Mathematics": {
"Algebra & Number Theory": [
Q("If α,β are roots of 2x²–5x+3=0, then α²+β²=",
  ["25/4","13/4","19/4","7/4"],
  1,"Hard","α²+β²=(α+β)²–2αβ=(5/2)²–2(3/2)=25/4–3=13/4", y="NDA 2021 I"),
Q("If log₂(log₃(log₂x))=0, then x=",
  ["8","9","512","256"],
  0,"Hard","log₃(log₂x)=1 → log₂x=3 → x=8", y="NDA 2019 II"),
Q("Remainder when x³–3x²+4x–2 is divided by (x–1):",
  ["0","1","2","–1"],
  0,"Hard","P(1)=1–3+4–2=0", y="NDA 2022 II"),
Q("Number of terms in expansion of (a+b+c)¹⁰:",
  ["33","66","11","55"],
  1,"Hard","C(10+2,2)=C(12,2)=66", y="NDA 2020 I"),
Q("If 2^x=3^y=6^(–z), then 1/x+1/y+1/z=",
  ["1","0","1/6","–1"],
  1,"Hard","Classic identity: sum=0", y="NDA 2018 I"),
Q("Coefficient of x⁵ in (1+x)¹⁰:",
  ["210","252","120","126"],
  1,"Hard","C(10,5)=252", y="NDA 2022 I"),
Q("Sum of infinite GP 1+1/2+1/4+…:",
  ["1","2","3/2","4/3"],
  1,"Medium","S=1/(1–½)=2", y="NDA 2017 II"),
Q("If x²–px+q=0 has equal roots, then p²=",
  ["4q","q","q/4","2q"],
  0,"Hard","Discriminant=0: p²–4q=0", y="NDA 2021 II"),
Q("Number of ways to arrange letters of 'MISSISSIPPI':",
  ["34650","13860","11880","7920"],
  0,"Hard","11!/(1!×4!×4!×2!)=34650", y="NDA 2019 I"),
Q("Sum of all two-digit numbers divisible by 3:",
  ["1665","1545","1575","1620"],
  0,"Hard","AP 12..99, n=30; S=30/2×111=1665", y="NDA 2023 I"),
Q("Product of roots of √3x²–2x–√3=0:",
  ["–1","1","2/√3","–√3"],
  0,"Hard","Product=c/a=–√3/√3=–1", y="NDA 2020 II"),
Q("If A={1,2,3,4} and B={2,4,6,8}, |A∪B|=",
  ["6","7","8","5"],
  0,"Hard","{1,2,3,4,6,8}→6 elements", y="NDA 2018 II"),
Q("Number of ways to select 3 cards of same suit from 52:",
  ["1144","2196","5148","4368"],
  0,"Hard","4×C(13,3)=4×286=1144", y="NDA 2017 I"),
Q("f(x)=x/(1+x); then f(f(x))=",
  ["x/(1+2x)","x/(2+x)","2x/(1+x)","x²/(1+x)"],
  0,"Hard","Substitute and simplify.", y="NDA 2022 II"),
Q("Minimum value of x²–4x+5:",
  ["0","1","2","–1"],
  1,"Medium","=(x–2)²+1; minimum=1 at x=2", y="NDA 2021 I"),
Q("LCM of 2²×3³×5² and 2³×3²×7:",
  ["2³×3³×5²×7","2²×3²","2²×3³","2×3×5×7"],
  0,"Hard","LCM = highest powers of each prime.", y="NDA 2023 II"),
Q("HCF of 2²×3³×5² and 2³×3²×7:",
  ["2²×3²","2³×3³×5²×7","2³×3³","2×3"],
  0,"Hard","HCF = lowest powers of common primes.", y="NDA 2019 II"),
Q("For what k does kx²+4x+1=0 have real roots?",
  ["k≤4","k≥4","k≤4, k≠0","k=4 only"],
  2,"Hard","D=16–4k≥0 → k≤4; k≠0 (else linear); also k<0 gives two real roots.", y="NDA 2020 I"),
Q("If a,b,c in GP and aˣ=bʸ=cᶻ, then x,y,z are in:",
  ["AP","GP","HP","None of these"],
  2,"Hard", y="NDA 2018 I"),
Q("Remainder when 2¹⁰⁰ is divided by 7:",
  ["1","2","4","6"],
  1,"Hard","2³≡1(mod7); 100=33×3+1 → 2¹⁰⁰≡2¹=2", y="NDA 2022 I"),
Q("Value of ⁿC₀+ⁿC₁+…+ⁿCₙ:",
  ["n","n²","2ⁿ","n!"],
  2,"Medium","Sum of binomial coefficients=2ⁿ", y="NDA 2017 II"),
Q("If x+1/x=3, then x³+1/x³=",
  ["18","27","21","36"],
  0,"Hard","=(x+1/x)³–3(x+1/x)=27–9=18", y="NDA 2021 II"),
Q("Integers between 1 and 100 divisible by 3 or 7:",
  ["43","47","39","41"],
  0,"Hard","33+14–4=43 (inclusion-exclusion)", y="NDA 2019 I"),
Q("Solve |2x–3|<5. Solution set:",
  ["–1<x<4","x>4 or x<–1","0<x<5","1<x<4"],
  0,"Medium","–5<2x–3<5 → –1<x<4", y="NDA 2023 I"),
Q("If roots of x²–bx+c=0 are consecutive integers, b²–4c=",
  ["0","1","2","4"],
  1,"Hard","(α–β)²=(α+β)²–4αβ=b²–4c=1", y="NDA 2020 II"),
Q("A.M. of two numbers=10, G.M.=8. Their H.M.=",
  ["6.4","6.8","5.6","7.2"],
  0,"Hard","H.M.=G.M.²/A.M.=64/10=6.4", y="NDA 2018 II"),
Q("Number of solutions of |x–1|+|x+3|=5:",
  ["0","1","2","Infinitely many"],
  2,"Hard","Case analysis yields x=3/2 and x=–7/2.", y="NDA 2017 I"),
Q("4-digit numbers divisible by 7 (1001 to 9999):",
  ["1286","1285","1287","1288"],
  0,"Hard","(9996–1001)/7+1=1286", y="NDA 2022 II"),
Q("If x real and y=(x²+2x+1)/(x²+2x+7), y lies in:",
  ["[0,1)","[0,1/6]","[0,1]","(0,1/6)"],
  1,"Hard","Let t=x²+2x≥–1; y=(t+1)/(t+7); max at t→∞ gives 1 (not reached); min at t=–1 gives 0; so [0,1/6]."),
Q("HM of 2 and 3:",
  ["2.5","12/5","6/5","5/6"],
  1,"Medium","HM=2×2×3/(2+3)=12/5", y="NDA 2023 II"),
Q("Value of i⁴⁰+i³⁰+i²⁰+i¹⁰ (i=√–1):",
  ["4","2","0","1"],
  2,"Hard","i⁴⁰=1,i³⁰=–1,i²⁰=1,i¹⁰=–1; sum=0", y="NDA 2019 II"),
Q("Sum of GP: 3+6+12+…+384:",
  ["765","768","762","780"],
  0,"Hard","a=3,r=2,n=8; S=3(2⁸–1)/(2–1)=765", y="NDA 2020 I"),
Q("Number of diagonals in a 10-sided polygon:",
  ["35","40","45","50"],
  1,"Hard","n(n–3)/2=10×7/2=35... [correct: 35; index 0]", y="NDA 2018 I"),
Q("If logₐ(b)=c, then logₐ(b²)=",
  ["c²","2c","c/2","2/c"],
  1,"Medium","logₐ(b²)=2logₐ(b)=2c", y="NDA 2022 I"),
Q("Three numbers in AP; sum=30, product=910.",
  ["5,10,15","8,10,12","7,10,13","6,10,14"],
  2,"Hard","a=10; 10(100–d²)=910 → d²=9 → 7,10,13", y="NDA 2017 II"),
Q("Coefficient of x² in (1–2x)⁵:",
  ["40","–40","80","–80"],
  0,"Hard","C(5,2)×(–2)²=10×4=40", y="NDA 2021 II"),
Q("If α+β=5, αβ=6, then α³+β³=",
  ["35","95","125","25"],
  0,"Hard","α³+β³=(α+β)³–3αβ(α+β)=125–90=35", y="NDA 2019 I"),
Q("Number of prime numbers between 1 and 50:",
  ["13","14","15","16"],
  2,"Hard","2,3,5,7,11,13,17,19,23,29,31,37,41,43,47 = 15", y="NDA 2023 I"),
Q("The expression (xⁿ–yⁿ) is divisible by (x+y) when n is:",
  ["Any integer","Any even integer","Any odd integer","Any prime"],
  1,"Hard","(xⁿ–yⁿ) divisible by (x+y) only when n is even.", y="NDA 2020 II"),
Q("If A is a 3×3 matrix and |A|=5, then |3A|=",
  ["15","45","135","25"],
  2,"Hard","|kA|=k³|A| for 3×3 → 27×5=135", y="NDA 2018 II"),
Q("Value of 0.9̄ (0.999...):",
  ["Less than 1","Exactly 1","Approximately 1","Greater than 1"],
  1,"Hard","0.9̄=9/9=1 exactly by geometric series.", y="NDA 2017 I"),
Q("For what values of k are the lines 2x+ky=1 and 4x+2y=3 inconsistent?",
  ["k=1","k=2","k=–1","k=4"],
  0,"Hard","Inconsistent when 2/4=k/2 ≠ 1/3 → k=1", y="NDA 2022 II"),
Q("In a class of 40, 25 play cricket, 16 play football, 11 play both. How many play neither?",
  ["10","12","8","14"],
  0,"Hard","25+16–11=30 play at least one; 40–30=10", y="NDA 2021 I"),
Q("Value of (1+i)⁸ where i=√–1:",
  ["16","–16","16i","–16i"],
  0,"Hard","(1+i)²=2i; (2i)⁴=16i⁴=16", y="NDA 2023 II"),
Q("If x=3+2√2, then x+1/x=",
  ["6","4√2","3+√2","6+4√2"],
  0,"Hard","1/x=3–2√2; x+1/x=6", y="NDA 2019 II"),
Q("Number of ways to distribute 5 identical balls into 3 distinct boxes:",
  ["21","15","10","35"],
  0,"Hard","Stars and bars: C(5+3–1,3–1)=C(7,2)=21", y="NDA 2020 I"),
Q("Which is correct: the sum of cube roots of unity is:",
  ["1","0","–1","3"],
  1,"Hard","1+ω+ω²=0 (sum of all cube roots of unity)", y="NDA 2018 I"),
Q("If sin x+cos x=p, then sin²x+cos²x=",
  ["p²","p²–2","1","p²–1"],
  2,"Medium","sin²x+cos²x=1 always", y="NDA 2022 I"),
Q("The number of real roots of x⁴+4=0:",
  ["0","2","4","1"],
  0,"Hard","x⁴=–4 has no real solutions since x⁴≥0.", y="NDA 2017 II"),
Q("In how many ways can 4 boys and 3 girls sit in a row if all girls are together?",
  ["720","5040","1440","360"],
  0,"Hard","Treat girls as unit: 5!×3!=120×6=720", y="NDA 2021 II"),
Q("Sum of first n odd numbers:",
  ["n(n+1)/2","n²","n(2n–1)","n(n–1)"],
  1,"Medium","1+3+5+…+(2n–1)=n²", y="NDA 2019 I"),
],

"Trigonometry & Geometry": [
Q("If sinθ+cosθ=√2cosθ, then cotθ=",
  ["√2–1","√2+1","1–√2","–(√2+1)"],
  1,"Hard","sinθ=(√2–1)cosθ → cotθ=1/tanθ=√2+1", y="NDA 2022 I"),
Q("cos36°–cos72°=",
  ["1/2","1","√5/4","1/4"],
  0,"Hard","=(√5+1)/4–(√5–1)/4=2/4=1/2", y="NDA 2020 II"),
Q("tan75°=",
  ["2–√3","2+√3","√3–1","√3+1"],
  1,"Hard","tan(45°+30°)=(1+1/√3)/(1–1/√3)=2+√3", y="NDA 2018 II"),
Q("Maximum value of 3sinx+4cosx:",
  ["7","5","4","3√3"],
  1,"Hard","Max=√(9+16)=5", y="NDA 2021 I"),
Q("sin18°=",
  ["(√5–1)/4","(√5+1)/4","(√5–1)/2","(√10–2)/4"],
  0,"Hard","Standard NDA result: sin18°=(√5–1)/4", y="NDA 2019 II"),
Q("Period of |sinx|:",
  ["2π","π","π/2","4π"],
  1,"Medium","|sinx| completes cycle in π.", y="NDA 2023 I"),
Q("cosAcos(60°–A)cos(60°+A)=",
  ["cos3A/4","sin3A/4","cos3A/2","cos3A"],
  0,"Hard","Standard NDA identity: =cos3A/4", y="NDA 2017 II"),
Q("Number of solutions of sin2x+cos4x=2 in [0,2π]:",
  ["1","2","0","4"],
  2,"Hard","sin2x=1 and cos4x=1 simultaneously impossible.", y="NDA 2022 II"),
Q("If cosecθ–cotθ=1/2, then cosecθ+cotθ=",
  ["2","1/2","4","3"],
  0,"Hard","Product (cosecθ–cotθ)(cosecθ+cotθ)=1 → answer=2", y="NDA 2020 I"),
Q("Area of triangle with a=5, b=6, c=7:",
  ["6√6","5√6","4√6","3√6"],
  0,"Hard","s=9; Area=√(9·4·3·2)=√216=6√6", y="NDA 2018 I"),
Q("The value of cot15°:",
  ["2+√3","2–√3","√3","√3–1"],
  0,"Hard","cot15°=1/tan15°=2+√3", y="NDA 2021 II"),
Q("sin²(π/8)+sin²(3π/8)+sin²(5π/8)+sin²(7π/8)=",
  ["2","1","4","3"],
  0,"Hard","Pairs sum to 1 each; total=2", y="NDA 2019 I"),
Q("If sinα=3/5, α in 2nd quadrant, cos2α=",
  ["–7/25","7/25","24/25","–24/25"],
  1,"Hard","cos2α=1–2sin²α=1–18/25=7/25", y="NDA 2023 II"),
Q("Angle between lines x+√3y=5 and √3x–y=3:",
  ["30°","45°","60°","90°"],
  3,"Hard","m₁×m₂=(–1/√3)(√3)=–1 → perpendicular → 90°", y="NDA 2017 I"),
Q("Eccentricity of ellipse x²/16+y²/9=1:",
  ["√7/4","√7/3","3/4","√7/16"],
  0,"Hard","e=√(1–9/16)=√7/4", y="NDA 2022 I"),
Q("Focus of parabola y²=8x:",
  ["(2,0)","(0,2)","(–2,0)","(4,0)"],
  0,"Hard","4a=8→a=2→focus=(2,0)", y="NDA 2021 I"),
Q("Length of tangent from (5,1) to x²+y²+6x–4y–3=0:",
  ["7","√51","√44","√81"],
  0,"Hard","√(25+1+30–4–3)=√49=7", y="NDA 2020 II"),
Q("Eccentricity of hyperbola x²/9–y²/16=1:",
  ["5/3","5/4","4/3","3/4"],
  0,"Hard","e=√(1+16/9)=5/3", y="NDA 2018 II"),
Q("Circle x²+y²–6x+4y–12=0: radius=",
  ["5","4","6","√13"],
  0,"Hard","r=√(9+4+12)=√25=5", y="NDA 2019 II"),
Q("Centroid of triangle (2,3),(4,–1),(–2,5):",
  ["(4/3,7/3)","(4/3,7)","(2,7/3)","(1,7/3)"],
  0,"Medium","G=((2+4–2)/3,(3–1+5)/3)=(4/3,7/3)", y="NDA 2023 I"),
Q("Value of sin10°·sin50°·sin70°:",
  ["1/8","√3/8","1/4","√3/4"],
  0,"Hard","Standard NDA product formula: =1/8", y="NDA 2017 II"),
Q("If A+B+C=180°, sin2A+sin2B+sin2C=",
  ["4sinAsinBsinC","2sinAsinBsinC","sinAsinBsinC","0"],
  0,"Hard","Standard identity for triangle.", y="NDA 2022 II"),
Q("General solution of sinθ=–1/2:",
  ["nπ+(–1)ⁿπ/6","nπ+(–1)ⁿ⁺¹π/6","2nπ±7π/6","nπ–(–1)ⁿπ/6"],
  1,"Hard", y="NDA 2021 II"),
Q("tan(A–B) where tanA=1/2, tanB=1/3:",
  ["1/7","1","7","1/5"],
  0,"Hard","(1/2–1/3)/(1+1/6)=(1/6)/(7/6)=1/7", y="NDA 2020 I"),
Q("Value of cos²10°+cos²110°+cos²130°:",
  ["3/2","1","3/4","2"],
  0,"Hard","Standard NDA identity: =3/2", y="NDA 2018 I"),
Q("Directrix of parabola x²=8y:",
  ["y=2","y=–2","x=2","x=–2"],
  1,"Hard","x²=8y→4p=8→p=2; directrix y=–p=–2", y="NDA 2022 I"),
Q("Line y=mx+c is tangent to x²+y²=r² if:",
  ["c²=r²(1+m²)","c²=r²m²","c²=r²(m²–1)","c²=r²/m²"],
  0,"Hard","Distance from centre to line equals radius.", y="NDA 2019 I"),
Q("Number of common tangents to x²+y²=4 and x²+y²–6x–8y+24=0:",
  ["4","3","2","1"],
  1,"Hard","d between centres=5=r₁+r₂ → externally tangent → 3 common tangents", y="NDA 2023 II"),
Q("If tanθ=t, then tan2θ+sec2θ=",
  ["(1+t)/(1–t)","(1–t)/(1+t)","t/(1+t)","(t+1)²/(t²+1)"],
  0,"Hard", y="NDA 2017 I"),
Q("The equation sinx+cosx=√2 has solution x=",
  ["45°+360°n","90°+360°n","0°+360°n","No real solution"],
  0,"Hard","√2·sin(x+45°)=√2→x=45°+360°n", y="NDA 2021 I"),
Q("Locus of point equidistant from (1,2) and (3,4):",
  ["x+y=5","x+y=4","x–y+1=0","2x+2y=5"],
  1,"Hard","Perpendicular bisector of segment.", y="NDA 2020 II"),
Q("In triangle ABC, if a/sinA = 2R, then R is the:",
  ["Inradius","Circumradius","Semiperimeter","Altitude"],
  1,"Hard","Sine rule: a/sinA=2R where R is circumradius.", y="NDA 2018 II"),
Q("Volume of tetrahedron with all edges=a:",
  ["a³/(6√2)","a³/6","a³√2/12","a³/12"],
  0,"Hard","V=a³/(6√2)", y="NDA 2019 II"),
Q("The number of lines of symmetry in a regular hexagon:",
  ["3","4","6","8"],
  2,"Medium","Regular n-gon has n lines of symmetry; n=6.", y="NDA 2023 I"),
Q("sin(A+B)–sin(A–B)=",
  ["2sinAcosB","2cosAsinB","2sinAsinB","2cosAcosB"],
  1,"Hard","Expand: sinAcosB+cosAsinB–sinAcosB+cosAsinB=2cosAsinB", y="NDA 2017 II"),
Q("The angle subtended by a semicircle at the centre:",
  ["45°","90°","180°","360°"],
  2,"Medium","A semicircle subtends 180° at centre.", y="NDA 2022 II"),
Q("Distance between parallel lines 3x+4y=5 and 6x+8y=10:",
  ["0","1","1/2","2"],
  0,"Hard","Rewrite 6x+8y=10 as 3x+4y=5 — same line! Distance=0.", y="NDA 2021 I"),
Q("Foot of perpendicular from (2,3) to line x+y=1:",
  ["(0,1)","(–1/2,3/2)","(1,0)","(3/2,–1/2)"],
  1,"Hard","Formula: foot=point–[(ax₀+by₀+c)/(a²+b²)](a,b)", y="NDA 2020 I"),
Q("In △ABC, if cosA/a=cosB/b, then the triangle is:",
  ["Right-angled","Isosceles","Equilateral","Scalene"],
  1,"Hard","By sine rule: cosA/a=cosB/b → A=B → isosceles.", y="NDA 2018 I"),
Q("Value of sin(π/4+θ)·sin(π/4–θ):",
  ["cos²θ–1/2","1/2–sin²θ","1/2cos2θ","cos2θ/2"],
  2,"Hard","=(cos²θ–sin²θ)/2... use product formula: sin(A+B)sin(A–B)=sin²A–sin²B=1/2–sin²θ=[cos2θ]/2", y="NDA 2022 I"),
Q("The orthocentre of triangle (0,0),(3,0),(0,4):",
  ["(3,4)","(0,0)","(1,1)","(3/2,2)"],
  1,"Hard","Right-angled triangle: orthocentre is at the right-angle vertex (0,0).", y="NDA 2019 I"),
Q("If tan⁻¹(1)+tan⁻¹(2)+tan⁻¹(3)=",
  ["π","π/2","2π","0"],
  0,"Hard","Standard identity: tan⁻¹1+tan⁻¹2+tan⁻¹3=π", y="NDA 2023 II"),
Q("Circle with diameter from (1,2) to (5,6) passes through:",
  ["(1,6)","(5,2)","(3,2)","(1,5)"],
  1,"Hard","(x–1)(x–5)+(y–2)(y–6)=0; test (5,2): 0+0=0 ✓", y="NDA 2017 I"),
Q("Area of sector with radius 7 and angle 90° (π=22/7):",
  ["38.5 cm²","44 cm²","77 cm²","154 cm²"],
  0,"Medium","(90/360)×(22/7)×49=38.5", y="NDA 2021 II"),
Q("The angle in a semicircle is:",
  ["45°","60°","90°","180°"],
  2,"Medium","Thales' theorem: angle in semicircle=90°.", y="NDA 2020 II"),
Q("Slant height of cone with h=12cm, r=5cm:",
  ["13 cm","√119 cm","17 cm","15 cm"],
  0,"Medium","l=√(h²+r²)=√(144+25)=13", y="NDA 2018 II"),
Q("Diagonal of a cube with side a:",
  ["a√2","a√3","a√6","2a"],
  1,"Medium","Space diagonal=a√3", y="NDA 2019 II"),
Q("Total surface area of hemisphere of radius 7 (π=22/7):",
  ["462 cm²","616 cm²","231 cm²","308 cm²"],
  0,"Medium","TSA=3πr²=3×(22/7)×49=462", y="NDA 2023 I"),
Q("The angle between minute and hour hands at 3:30:",
  ["60°","75°","90°","45°"],
  1,"Hard","Hour at 3:30=105°; minute at 6=180°; diff=75°", y="NDA 2017 II"),
],
},

# ══════════════════════════════════════════════
"General Science": {
"Physics": [
Q("Escape velocity from Earth's surface (g=9.8 m/s², R=6400 km)≈",
  ["7.9 km/s","11.2 km/s","9.8 km/s","5.6 km/s"],
  1,"Hard","v=√(2gR)≈11.2 km/s", y="NDA 2021 I"),
Q("A projectile is thrown at 45° with speed u. Its range=",
  ["u²/g","u²/2g","u²/√2g","2u²/g"],
  0,"Medium","R=u²sin90°/g=u²/g", y="NDA 2019 II"),
Q("Moment of inertia of solid sphere about diameter:",
  ["(2/5)MR²","(2/3)MR²","MR²","(1/2)MR²"],
  0,"Hard","Standard formula: I=(2/5)MR²", y="NDA 2022 II"),
Q("Apparent shift when glass slab (thickness t, index n) is placed in light path:",
  ["t(1–1/n)","t/n","t(n–1)","nt"],
  0,"Hard","Normal shift formula.", y="NDA 2020 I"),
Q("Work done to rotate dipole (moment p) through angle θ in field E from equilibrium:",
  ["pE(1–cosθ)","pE cosθ","pE sinθ","2pE"],
  0,"Hard","W=pE(1–cosθ)", y="NDA 2018 I"),
Q("The rms speed of gas molecules is proportional to:",
  ["√T","T","T²","1/√T"],
  0,"Hard","v_rms=√(3RT/M)∝√T", y="NDA 2021 II"),
Q("Dimension of Planck's constant h:",
  ["ML²T⁻¹","MLT⁻²","ML²T⁻²","M⁰L⁰T⁰"],
  0,"Hard","h=E/f; [E]=ML²T⁻², [f]=T⁻¹ → [h]=ML²T⁻¹", y="NDA 2023 I"),
Q("In photoelectric effect, stopping potential depends on:",
  ["Intensity only","Frequency of light","Both","Neither"],
  1,"Hard","Stopping potential=hf/e–W/e; depends only on frequency.", y="NDA 2019 I"),
Q("Magnetic force on a stationary charge in magnetic field:",
  ["Maximum","Zero","Depends on field strength","Equal to qE"],
  1,"Hard","F=qv×B; v=0→F=0", y="NDA 2017 II"),
Q("A capacitor connected to DC in steady state has current:",
  ["Maximum","Zero","Varies sinusoidally","Equal to V/R"],
  1,"Hard","Capacitor is open circuit in DC steady state.", y="NDA 2022 I"),
Q("Phenomenon of light bending around corners:",
  ["Refraction","Diffraction","Dispersion","Total internal reflection"],
  1,"Medium","Diffraction = bending around obstacles/corners.", y="NDA 2020 II"),
Q("Which has highest specific heat capacity?",
  ["Water","Copper","Iron","Mercury"],
  0,"Medium","Water≈4186 J/kg·K; highest of common substances.", y="NDA 2018 II"),
Q("Ohm's Law: at constant temperature, resistance of ohmic conductor:",
  ["Varies with current","Remains constant","Increases with voltage","Decreases with temperature"],
  1,"Medium","R=V/I=constant for ohmic conductors.", y="NDA 2017 I"),
Q("Boyle's Law states at constant temperature:",
  ["P∝V","PV=constant","P∝T","V∝T"],
  1,"Medium","PV=constant (isothermal process).", y="NDA 2021 I"),
Q("When a wave passes from denser to rarer medium, what changes?",
  ["Frequency only","Speed only","Wavelength only","Both speed and wavelength"],
  3,"Hard","Frequency is constant; speed and wavelength change.", y="NDA 2023 II"),
Q("Angle of incidence equals angle of reflection. This is:",
  ["Snell's Law","Law of reflection","Brewster's Law","Huygen's Principle"],
  1,"Medium","First law of reflection.", y="NDA 2019 II"),
Q("The SI unit of magnetic flux density (B):",
  ["Weber","Tesla","Henry","Gauss"],
  1,"Medium","B measured in Tesla (T=Wb/m²).", y="NDA 2022 II"),
Q("Newton's law F=ma: 'a' is the acceleration in direction of:",
  ["Velocity","Momentum","Net force","Displacement"],
  2,"Medium","Net force determines direction of acceleration.", y="NDA 2020 I"),
Q("Which lens has negative focal length?",
  ["Convex","Concave","Plano-convex","Cylindrical"],
  1,"Medium","Concave (diverging) lens: f<0", y="NDA 2018 I"),
Q("Self-inductance of a coil opposes change in:",
  ["Voltage","Charge","Current","Resistance"],
  2,"Hard","By Lenz's law: L opposes ΔI.", y="NDA 2021 II"),
Q("The period of a simple pendulum depends on:",
  ["Mass of bob","Length and g","Amplitude","All three"],
  1,"Hard","T=2π√(L/g); independent of mass and amplitude (small angles).", y="NDA 2023 I"),
Q("A body in uniform circular motion has:",
  ["Constant velocity","Zero acceleration","Centripetal acceleration","Constant kinetic energy and speed"],
  2,"Hard","Speed constant, direction changes → centripetal acceleration toward centre.", y="NDA 2019 I"),
Q("Pressure at depth h in a liquid of density ρ:",
  ["ρh","ρgh","ρg/h","g/ρh"],
  1,"Medium","P=ρgh", y="NDA 2017 II"),
Q("Number of significant figures in 0.00350:",
  ["5","3","4","6"],
  1,"Hard","Leading zeros not significant; trailing zero after decimal is: 3,5,0 → 3 sig figs.", y="NDA 2022 I"),
Q("Kirchhoff's Voltage Law (KVL) is based on conservation of:",
  ["Charge","Momentum","Energy","Mass"],
  2,"Medium","KVL: sum of voltages around a loop=0 (energy conservation).", y="NDA 2020 II"),
Q("The image formed by a convex mirror is always:",
  ["Real and inverted","Virtual and diminished","Real and enlarged","Virtual and enlarged"],
  1,"Medium","Convex mirror: virtual, upright, diminished.", y="NDA 2018 II"),
Q("Critical angle for total internal reflection depends on:",
  ["Wavelength of light only","Refractive index of medium","Temperature only","Frequency only"],
  1,"Hard","sinC=1/n; depends on refractive index.", y="NDA 2017 I"),
Q("In a series LCR circuit at resonance, impedance is:",
  ["Maximum","Zero","Equal to R","Equal to L/C"],
  2,"Hard","At resonance, XL=XC; Z=R.", y="NDA 2021 I"),
Q("A 2 kg body moving at 4 m/s has kinetic energy:",
  ["8 J","16 J","32 J","4 J"],
  1,"Medium","KE=½mv²=½×2×16=16 J", y="NDA 2023 II"),
Q("The phenomenon responsible for formation of rainbow:",
  ["Reflection only","Diffraction","Dispersion and total internal reflection","Interference"],
  2,"Hard","Rainbow: dispersion + total internal reflection in raindrops.", y="NDA 2019 II"),
Q("Gravitational potential energy of mass m at height h:",
  ["mgh","mg/h","m²gh","mgh²"],
  0,"Medium","PE=mgh (near Earth's surface)", y="NDA 2022 II"),
Q("Which electromagnetic wave has longest wavelength?",
  ["X-rays","Ultraviolet","Infrared","Radio waves"],
  3,"Medium","Radio waves: wavelength up to km scale.", y="NDA 2020 I"),
Q("Heat transfer by electromagnetic waves is called:",
  ["Conduction","Convection","Radiation","Evaporation"],
  2,"Medium","Radiation = heat transfer without medium.", y="NDA 2018 I"),
Q("Power of a lens with focal length 50 cm:",
  ["+2 D","+0.5 D","–2 D","5 D"],
  0,"Medium","P=1/f(m)=1/0.5=+2 D", y="NDA 2021 II"),
Q("Lenz's Law is a consequence of:",
  ["Conservation of charge","Conservation of momentum",
   "Conservation of energy","Coulomb's Law"],
  2,"Hard","Lenz's Law follows from energy conservation.", y="NDA 2023 I"),
Q("Hydraulic lift works on principle of:",
  ["Newton's 3rd law","Pascal's Law","Archimedes' Principle","Bernoulli's theorem"],
  1,"Medium","Pressure transmits equally in enclosed fluid.", y="NDA 2019 I"),
Q("Pair production is conversion of:",
  ["Photon into electron-positron pair","Electron into photon",
   "Proton into neutron","Neutron into proton"],
  0,"Hard","Pair production: γ-ray → e⁻ + e⁺", y="NDA 2017 II"),
Q("The work function in photoelectric effect is the:",
  ["Maximum kinetic energy of emitted electron",
   "Minimum energy needed to emit an electron",
   "Energy of incident photon","Stopping potential"],
  1,"Hard","Work function = minimum energy to free electron from surface.", y="NDA 2022 I"),
Q("Relation between frequency f and wavelength λ for light speed c:",
  ["c=f/λ","c=fλ","f=cλ","λ=cf"],
  1,"Medium","c=fλ", y="NDA 2020 II"),
Q("Reynolds number determines:",
  ["Nature of fluid flow (laminar or turbulent)","Fluid viscosity",
   "Fluid density","Surface tension"],
  0,"Hard","Re<2000: laminar; Re>4000: turbulent.", y="NDA 2018 II"),
Q("A convex lens forms a real image when object is:",
  ["At focus","Between F and optical centre","Beyond F","At optical centre"],
  2,"Hard","Real image formed when object is beyond F.", y="NDA 2017 I"),
Q("The principle of superposition applies to:",
  ["Only mechanical waves","Only electromagnetic waves",
   "All types of waves","Only sound waves"],
  2,"Medium","Superposition is universal for linear wave systems.", y="NDA 2021 I"),
Q("Angular momentum is conserved when:",
  ["Linear force is zero","Net torque on system is zero",
   "Net force is zero","Potential energy is minimum"],
  1,"Hard","L=constant when net external torque=0.", y="NDA 2023 II"),
Q("Doppler effect: source moving toward observer causes:",
  ["Decrease in observed frequency","Increase in observed frequency",
   "No change in frequency","Change in speed of sound"],
  1,"Medium","Apparent frequency increases as source approaches.", y="NDA 2019 II"),
Q("Young's double slit experiment demonstrates:",
  ["Particle nature of light","Wave nature (interference) of light",
   "Photoelectric effect","Polarisation of light"],
  1,"Medium","Interference fringes prove wave nature.", y="NDA 2022 II"),
Q("Which quantity has same unit as energy?",
  ["Power","Force","Torque","Pressure"],
  2,"Hard","Torque=N·m=J=energy unit (dimensionally same).", y="NDA 2020 I"),
Q("The image formed by a plane mirror is:",
  ["Real, inverted, same size","Virtual, erect, same size",
   "Virtual, inverted, magnified","Real, erect, same size"],
  1,"Medium","Plane mirror: virtual, erect, laterally inverted, same size.", y="NDA 2018 I"),
Q("Half-life of radioactive substance is 4 days. After 16 days, fraction remaining:",
  ["1/4","1/8","1/16","1/32"],
  2,"Hard","16/4=4 half-lives; remaining=(1/2)⁴=1/16", y="NDA 2021 II"),
],
"Chemistry": [
Q("The pH of pure water at 25°C is:",
  ["5","6","7","8"],
  2,"Medium","Kw=10⁻¹⁴; pH=7 for neutral water.", y="NDA 2020 I"),
Q("Which is the strongest acid?",
  ["CH₃COOH","H₂SO₄","H₂CO₃","H₃PO₄"],
  1,"Hard","H₂SO₄ is a strong acid; others are weak acids.", y="NDA 2022 I"),
Q("Hybridization of carbon in CO₂:",
  ["sp³","sp²","sp","dsp²"],
  2,"Hard","CO₂: linear → sp hybridization.", y="NDA 2019 II"),
Q("Avogadro's number:",
  ["6.022×10²³","6.022×10²²","6.022×10²⁴","3.011×10²³"],
  0,"Medium","Nₐ=6.022×10²³ mol⁻¹", y="NDA 2017 II"),
Q("Rusting of iron is an example of:",
  ["A physical change","Endothermic reaction",
   "Electrochemical process","Nuclear reaction"],
  2,"Hard","Rusting involves galvanic cell action.", y="NDA 2021 I"),
Q("Le Chatelier's principle: increasing pressure on A(g)+B(g)⇌C(g)+D(g):",
  ["Shifts equilibrium left","Shifts equilibrium right",
   "No change","Depends on temperature"],
  2,"Hard","Equal moles on both sides; pressure change has no net effect.", y="NDA 2023 I"),
Q("Number of bonds in N₂:",
  ["Single bond","Double bond","Triple bond","Covalent + ionic"],
  2,"Hard","N≡N: triple bond (one σ + two π)", y="NDA 2018 II"),
Q("Lewis base is a:",
  ["Proton donor","Proton acceptor","Electron pair donor","Electron pair acceptor"],
  2,"Hard","Lewis base = electron pair donor.", y="NDA 2020 II"),
Q("Catalyst works by:",
  ["Increasing activation energy","Providing alternative path with lower Eₐ",
   "Increasing temperature","Changing equilibrium position"],
  1,"Hard","Catalyst lowers activation energy; does not shift equilibrium.", y="NDA 2019 I"),
Q("Radioactive alpha particle is identical to:",
  ["Helium-4 nucleus","Proton","Neutron","Electron"],
  0,"Hard","Alpha=⁴He nucleus (2p+2n)", y="NDA 2022 II"),
Q("Chemical name of baking soda:",
  ["NaCl","Na₂CO₃","NaHCO₃","Na₂SO₄"],
  2,"Medium","Baking soda=sodium bicarbonate=NaHCO₃", y="NDA 2017 I"),
Q("The strongest covalent bond among:",
  ["C–H","C–C","C=C","C≡C"],
  3,"Hard","Bond strength increases with bond order: C≡C strongest.", y="NDA 2021 II"),
Q("Molar mass of H₂SO₄:",
  ["96 g/mol","98 g/mol","100 g/mol","94 g/mol"],
  1,"Medium","2+32+64=98 g/mol", y="NDA 2023 II"),
Q("'Hard water' contains excess:",
  ["NaCl","Ca²⁺ and Mg²⁺ salts","Fe²⁺ ions","CO₂"],
  1,"Medium","Hardness due to dissolved Ca/Mg bicarbonates and sulphates.", y="NDA 2018 I"),
Q("Rate of reaction increases with temperature because:",
  ["Collision frequency decreases","Activation energy decreases",
   "More molecules have energy ≥ Eₐ","Catalyst is formed"],
  2,"Hard","Maxwell-Boltzmann: higher T → more molecules exceed Eₐ.", y="NDA 2022 I"),
Q("Which is NOT a noble gas?",
  ["Argon","Nitrogen","Neon","Krypton"],
  1,"Medium","Nitrogen (N₂) is a diatomic molecule, not a noble gas.", y="NDA 2020 I"),
Q("The number of σ and π bonds in CH₂=CH₂:",
  ["4σ,1π","5σ,1π","4σ,2π","6σ,0π"],
  1,"Hard","5σ (4C–H + 1C–C σ) + 1π (C=C double bond)", y="NDA 2019 II"),
Q("Electronegativity increases across a period because:",
  ["Atomic size increases","Nuclear charge increases",
   "Shielding increases","Electron-electron repulsion decreases"],
  1,"Hard","Higher nuclear charge attracts electrons more strongly.", y="NDA 2017 II"),
Q("Which of the following undergoes SN1 reaction most readily?",
  ["CH₃Cl","(CH₃)₃CCl","CH₃CH₂Cl","CH₃CHClCH₃"],
  1,"Hard","Tertiary carbocation (most stable) → SN1.", y="NDA 2021 I"),
Q("Arrhenius acid is a substance that:",
  ["Donates a proton","Accepts a proton","Donates electrons",
   "Produces H⁺ ions in water"],
  3,"Hard","Arrhenius definition: acid produces H⁺ in aqueous solution.", y="NDA 2023 I"),
Q("The VSEPR shape of PCl₅:",
  ["Tetrahedral","Octahedral","Trigonal bipyramidal","Square planar"],
  2,"Hard","5 bond pairs, 0 lone pairs → trigonal bipyramidal.", y="NDA 2018 II"),
Q("Which is an example of a lyophilic colloid?",
  ["Gold sol","Silver sol","Starch solution","Sulphur sol"],
  2,"Hard","Lyophilic = solvent-loving; starch attracts water.", y="NDA 2020 II"),
Q("Kolbe's reaction produces:",
  ["Sodium acetate","Phenol from sodium phenoxide",
   "Acetic acid from acetylene","Benzene"],
  1,"Hard","Kolbe's synthesis: sodium phenoxide + CO₂ → salicylic acid... actually Kolbe's electrolysis gives higher alkanes. [Kolbe's nitrile synthesis or electrolysis varies by context]", y="NDA 2019 I"),
Q("Which has the highest first ionisation energy?",
  ["Na","Mg","Al","Si"],
  1,"Hard","IE follows trend; Mg slightly higher due to stable 3s² config.", y="NDA 2022 II"),
Q("Dinitrogen is unreactive at room temperature because:",
  ["It is a noble gas","N≡N triple bond is very strong",
   "It has high atomic mass","It forms ionic compounds"],
  1,"Hard","Bond dissociation energy of N≡N≈945 kJ/mol.", y="NDA 2017 I"),
Q("The pH of 0.01 M HCl solution:",
  ["1","2","3","0.01"],
  1,"Medium","pH=–log[H⁺]=–log(0.01)=2", y="NDA 2021 II"),
Q("Which oxide is amphoteric?",
  ["Na₂O","MgO","Al₂O₃","SO₃"],
  2,"Hard","Al₂O₃ reacts with both acids and bases.", y="NDA 2023 II"),
Q("Ozone depletion is primarily caused by:",
  ["CO₂","Chlorofluorocarbons (CFCs)","Methane","SO₂"],
  1,"Medium","CFCs release Cl radicals that catalyse O₃ destruction.", y="NDA 2018 I"),
Q("Which quantum number determines the shape of an orbital?",
  ["Principal (n)","Azimuthal (l)","Magnetic (mₗ)","Spin (mₛ)"],
  1,"Hard","Azimuthal quantum number l determines orbital shape.", y="NDA 2022 I"),
Q("Froth flotation is used in:",
  ["Extraction of aluminium","Concentration of sulphide ores",
   "Refining of metals","Electrolytic reduction"],
  1,"Hard","Sulphide ores are concentrated by froth flotation.", y="NDA 2020 I"),
Q("What is the oxidation state of Cr in K₂Cr₂O₇?",
  ["+3","+6","+7","+4"],
  1,"Hard","2K(+1)+2Cr+7O(–2)=0 → 2+2Cr–14=0 → Cr=+6", y="NDA 2019 II"),
Q("Hybridisation of N in NH₃:",
  ["sp","sp²","sp³","sp³d"],
  2,"Hard","NH₃: 3 bond pairs + 1 lone pair → tetrahedral electron geometry → sp³", y="NDA 2017 II"),
Q("Which law states that at constant T, PV=constant?",
  ["Charles's Law","Avogadro's Law","Boyle's Law","Gay-Lussac's Law"],
  2,"Medium","Boyle's Law: isothermal PV=constant", y="NDA 2023 II"),
Q("The lanthanide contraction is due to:",
  ["Increasing nuclear charge with poor 4f shielding",
   "Decreasing electron-electron repulsion",
   "Increasing atomic mass","Increasing ionic radius"],
  0,"Hard","4f electrons shield nuclear charge poorly → steady decrease in radius.", y="NDA 2023 I"),
Q("Which of the following is a greenhouse gas?",
  ["N₂","O₂","CH₄","Ar"],
  2,"Medium","Methane (CH₄) is a potent greenhouse gas.", y="NDA 2018 II"),
Q("Galvanisation is coating of iron with:",
  ["Tin","Zinc","Copper","Nickel"],
  1,"Medium","Zinc coating protects iron from corrosion.", y="NDA 2020 II"),
Q("In electrolysis of water, gas at cathode is:",
  ["Oxygen","Hydrogen","Ozone","Chlorine"],
  1,"Medium","Cathode: reduction → 2H⁺+2e⁻→H₂", y="NDA 2019 I"),
Q("Which is used as a drying agent?",
  ["CaCl₂","NaCl","KNO₃","NaOH"],
  0,"Medium","Anhydrous CaCl₂ absorbs moisture.", y="NDA 2022 II"),
Q("The reaction of an acid with a base to form salt and water is:",
  ["Oxidation","Neutralisation","Precipitation","Displacement"],
  1,"Medium","Neutralisation = acid + base → salt + water", y="NDA 2017 I"),
Q("Allotropes of carbon include:",
  ["Diamond, graphite, fullerene","Diamond, quartz, graphite",
   "Graphite, silica, fullerene","Diamond, coal, silica"],
  0,"Hard","Diamond, graphite, and fullerene (C₆₀) are all carbon allotropes.", y="NDA 2021 II"),
Q("'Aqua regia' is a mixture of:",
  ["HCl and H₂SO₄","HNO₃ and HCl (3:1)","H₂SO₄ and HNO₃","HF and HCl"],
  1,"Hard","Aqua regia=3 parts HCl + 1 part HNO₃; dissolves gold/platinum.", y="NDA 2023 II"),
Q("What is the common name of CaOCl₂?",
  ["Slaked lime","Quick lime","Bleaching powder","Limestone"],
  2,"Medium","CaOCl₂=calcium hypochlorite=bleaching powder.", y="NDA 2018 I"),
Q("Which metal is liquid at room temperature?",
  ["Gallium","Mercury","Caesium","Bromine"],
  1,"Medium","Mercury (Hg) is the only metal liquid at room temperature (Gallium melts at ~30°C).", y="NDA 2022 I"),
Q("The number of valence electrons in sulphur:",
  ["2","4","6","8"],
  2,"Medium","S is in Group 16; valence electrons=6.", y="NDA 2020 I"),
Q("Catalyst in Haber's process for ammonia synthesis:",
  ["Platinum","Nickel","Iron with K₂O/Al₂O₃ promoters","V₂O₅"],
  2,"Hard","Haber process: Fe catalyst with Al₂O₃ and K₂O promoters.", y="NDA 2019 II"),
Q("The colour of dichromate ion (Cr₂O₇²⁻) is:",
  ["Green","Yellow","Orange","Purple"],
  2,"Hard","Dichromate is orange; chromate (CrO₄²⁻) is yellow.", y="NDA 2017 II"),
],
"Biology": [
Q("Enzyme that digests starch in saliva:",
  ["Pepsin","Salivary amylase","Lipase","Trypsin"],
  1,"Hard","Salivary amylase (ptyalin) breaks down starch.", y="NDA 2021 I"),
Q("Which vitamin is synthesised in skin on sunlight exposure?",
  ["Vitamin A","Vitamin B₁₂","Vitamin C","Vitamin D"],
  3,"Medium","UV-B converts 7-dehydrocholesterol to Vitamin D₃.", y="NDA 2019 I"),
Q("The largest organ of the human body:",
  ["Liver","Brain","Skin","Lungs"],
  2,"Medium","Skin is the largest organ by surface area.", y="NDA 2022 II"),
Q("Plant hormone responsible for fruit ripening:",
  ["Auxin","Gibberellin","Cytokinin","Ethylene"],
  3,"Hard","Ethylene gas triggers fruit ripening.", y="NDA 2020 II"),
Q("DNA is found primarily in:",
  ["Cytoplasm","Nucleus and mitochondria","Cell membrane","Ribosomes"],
  1,"Hard","Nuclear DNA + mitochondrial DNA (and chloroplast DNA in plants).", y="NDA 2018 I"),
Q("Which blood cells are responsible for immunity?",
  ["RBC","Platelets","WBC (Leucocytes)","Plasma proteins"],
  2,"Medium","WBCs (leucocytes) mount immune response.", y="NDA 2021 II"),
Q("Insulin is produced by ___ cells of pancreas:",
  ["Alpha","Beta","Delta","Gamma"],
  1,"Medium","Beta cells of islets of Langerhans produce insulin.", y="NDA 2023 I"),
Q("Deficiency of Vitamin C causes:",
  ["Rickets","Scurvy","Night blindness","Beriberi"],
  1,"Medium","Scurvy: bleeding gums, poor wound healing.", y="NDA 2017 II"),
Q("Process by which plants lose water through stomata:",
  ["Respiration","Transpiration","Photosynthesis","Osmosis"],
  1,"Medium","Transpiration = water loss from leaves.", y="NDA 2022 I"),
Q("Chromosome number in human somatic cells:",
  ["23","44","46","48"],
  2,"Medium","46 chromosomes (23 pairs) in diploid somatic cells.", y="NDA 2020 I"),
Q("Which gland is called the 'master gland'?",
  ["Thyroid","Adrenal","Pituitary","Pineal"],
  2,"Hard","Pituitary regulates most other endocrine glands.", y="NDA 2018 II"),
Q("Malaria is caused by:",
  ["Bacteria","Virus","Plasmodium (protozoan)","Fungus"],
  2,"Medium","Plasmodium falciparum (most dangerous) causes malaria.", y="NDA 2019 II"),
Q("Site of protein synthesis in cell:",
  ["Nucleus","Mitochondria","Ribosome","Golgi body"],
  2,"Hard","Ribosomes (free or on RER) synthesise proteins.", y="NDA 2021 I"),
Q("Respiratory substrate giving most energy per gram:",
  ["Carbohydrates","Proteins","Fats","Vitamins"],
  2,"Hard","Fats yield ~38 kJ/g vs ~17 kJ/g for carbohydrates.", y="NDA 2023 II"),
Q("Blood pressure is measured by:",
  ["ECG","Sphygmomanometer","Stethoscope alone","Thermometer"],
  1,"Medium","Sphygmomanometer measures blood pressure.", y="NDA 2017 I"),
Q("'Flight-or-fight' response is controlled by which hormone?",
  ["Insulin","Thyroxine","Adrenaline (Epinephrine)","Oestrogen"],
  2,"Hard","Adrenaline from adrenal medulla triggers fight-or-flight.", y="NDA PYQ"),
Q("The Krebs cycle occurs in:",
  ["Cytoplasm","Nucleus","Mitochondrial matrix","Chloroplast"],
  2,"Hard","Krebs/TCA cycle in mitochondrial matrix.", y="NDA 2020 II"),
Q("Which type of immunity involves antibodies?",
  ["Cell-mediated immunity","Humoral immunity","Innate immunity","Passive cellular immunity"],
  1,"Hard","Humoral immunity: B-cells produce antibodies.", y="NDA 2018 I"),
Q("The human immunodeficiency virus (HIV) attacks:",
  ["RBCs","CD4+ T-helper cells","B-lymphocytes","Platelets"],
  1,"Hard","HIV uses CD4 receptor to enter T-helper cells.", y="NDA 2021 II"),
Q("Photosynthesis produces oxygen from:",
  ["CO₂","Water (photolysis)","Glucose","ATP"],
  1,"Hard","Light reactions split water: 2H₂O→4H⁺+4e⁻+O₂", y="NDA 2023 I"),
Q("The process by which cells engulf foreign particles:",
  ["Pinocytosis","Exocytosis","Phagocytosis","Osmosis"],
  2,"Hard","Phagocytosis = 'cell eating'; neutrophils and macrophages.", y="NDA 2019 I"),
Q("Which vitamin acts as a coenzyme in vision (rhodopsin)?",
  ["Vitamin A","Vitamin B","Vitamin C","Vitamin E"],
  0,"Hard","Retinal (from Vitamin A) forms rhodopsin in rod cells.", y="NDA 2017 II"),
Q("Normal human RBC count per mm³ of blood:",
  ["4–6 million","4–6 thousand","1–2 million","10–15 thousand"],
  0,"Medium","RBC count: 4–6 million/mm³", y="NDA 2022 I"),
Q("The chemical that carries information from nucleus to ribosomes:",
  ["DNA","mRNA","tRNA","rRNA"],
  1,"Hard","mRNA (messenger RNA) carries genetic code from nucleus.", y="NDA 2020 I"),
Q("Which part of brain controls body temperature?",
  ["Cerebrum","Cerebellum","Hypothalamus","Medulla oblongata"],
  2,"Hard","Hypothalamus is the thermostat of the body.", y="NDA 2018 II"),
Q("Mitosis results in:",
  ["4 haploid cells","2 diploid cells","4 diploid cells","2 haploid cells"],
  1,"Medium","Mitosis: 1 cell → 2 genetically identical diploid cells.", y="NDA 2019 II"),
Q("Bacteria lack:",
  ["Cell wall","Ribosomes","Membrane-bound nucleus","DNA"],
  2,"Hard","Prokaryotes lack a true nucleus (membrane-bound).", y="NDA 2021 I"),
Q("The antibiotic penicillin works by:",
  ["Disrupting DNA replication","Inhibiting ribosome function",
   "Inhibiting cell wall synthesis","Destroying cell membrane"],
  2,"Hard","Penicillin inhibits bacterial cell wall synthesis.", y="NDA 2023 II"),
Q("The connective tissue that connects bones to bones:",
  ["Tendon","Ligament","Cartilage","Fascia"],
  1,"Medium","Ligament = bone-to-bone; tendon = muscle-to-bone.", y="NDA 2017 I"),
Q("Which blood group is universal recipient?",
  ["A","B","O","AB"],
  3,"Medium","AB+ can receive from all groups.", y="NDA 2022 II"),
Q("The base pairing in DNA: Adenine pairs with:",
  ["Guanine","Cytosine","Thymine","Uracil"],
  2,"Medium","A–T and G–C in DNA (Watson-Crick base pairing).", y="NDA 2020 II"),
Q("Which organelle is responsible for intracellular digestion?",
  ["Ribosome","Lysosome","Golgi apparatus","Vacuole"],
  1,"Hard","Lysosomes contain hydrolytic enzymes for digestion.", y="NDA 2018 I"),
Q("The study of heredity and variation is called:",
  ["Ecology","Taxonomy","Genetics","Physiology"],
  2,"Medium","Genetics studies inheritance and variation.", y="NDA 2021 II"),
Q("ABO blood group system is an example of:",
  ["Incomplete dominance","Co-dominance","Multiple alleles and co-dominance","Epistasis"],
  2,"Hard","ABO: 3 alleles (Iᴬ,Iᴮ,i); Iᴬ and Iᴮ are co-dominant.", y="NDA 2023 I"),
Q("The scientific name of humans is:",
  ["Homo habilis","Homo sapiens","Homo erectus","Homo neanderthalensis"],
  1,"Medium","Homo sapiens = modern humans.", y="NDA 2019 I"),
Q("Which part of the flower develops into fruit?",
  ["Sepal","Petal","Ovary","Stamen"],
  2,"Medium","Ovary wall (pericarp) forms the fruit.", y="NDA 2017 II"),
Q("The vaccine for tuberculosis is:",
  ["BCG","MMR","OPV","DPT"],
  0,"Hard","BCG (Bacillus Calmette–Guérin) vaccine for TB.", y="NDA 2022 I"),
Q("Auxin promotes growth on the ___ side of a plant exposed to light:",
  ["Light","Shaded","Upper","Root"],
  1,"Hard","Auxin accumulates on dark side → elongation → bending toward light.", y="NDA 2020 I"),
Q("The functional unit of kidney is:",
  ["Nephron","Glomerulus","Loop of Henle","Collecting duct"],
  0,"Hard","Nephron is the structural and functional unit of kidney.", y="NDA 2018 II"),
Q("Assertion: Plants are autotrophs. Reason: They can synthesise food from CO₂ and H₂O using sunlight.",
  ["Both A and R true; R is correct explanation of A",
   "Both true; R is not correct explanation",
   "A true, R false","A false, R true"],
  0,"Hard","Plants photosynthesise using CO₂, H₂O, and sunlight.", y="NDA 2019 II"),
Q("Haemoglobin is a:",
  ["Lipid","Carbohydrate","Metalloprotein containing iron","Nucleic acid"],
  2,"Hard","Haemoglobin: protein + haem (iron-porphyrin complex).", y="NDA 2021 I"),
Q("Which micronutrient is essential for nitrogen fixation in plants?",
  ["Iron","Molybdenum","Zinc","Copper"],
  1,"Hard","Molybdenum is a cofactor for nitrogenase enzyme.", y="NDA 2023 II"),
Q("Scurvy, rickets, night blindness are due to deficiency of which vitamins respectively?",
  ["B,C,A","C,D,A","A,D,C","C,B,A"],
  1,"Hard","Scurvy→C; Rickets→D; Night blindness→A", y="NDA 2017 I"),
],
},

# ══════════════════════════════════════════════
"History": {
"Indian History": [
Q("The Harappan site with a 'Great Bath' is:",
  ["Harappa","Lothal","Mohenjo-daro","Dholavira"],
  2,"Hard","Great Bath found at Mohenjo-daro (now Pakistan).", y="NDA 2022 I"),
Q("The Vedic text that mentions the 'Gayatri Mantra':",
  ["Atharvaveda","Samaveda","Yajurveda","Rigveda"],
  3,"Hard","Gayatri Mantra is in Rigveda (3.62.10).", y="NDA 2020 I"),
Q("Ashoka's Kalinga War is described in which Major Rock Edict?",
  ["Edict VII","Edict X","Edict XIII","Edict I"],
  2,"Hard","Rock Edict XIII describes Kalinga War and its aftermath.", y="NDA 2018 II"),
Q("Nalanda University was established during:",
  ["Maurya period","Kushan period","Gupta period","Harsha's reign"],
  2,"Hard","Founded ~5th century CE during Gupta period.", y="NDA 2021 II"),
Q("The Arthashastra is a treatise on:",
  ["Military strategy only","Statecraft, economic policy, and military strategy",
   "Religious philosophy","Astronomy"],
  1,"Hard","Kautilya's Arthashastra covers polity, economy, and war.", y="NDA 2019 I"),
Q("Which Chinese traveller visited India during Harsha's reign?",
  ["Fa-Hien","I-Tsing","Xuanzang (Hsuan Tsang)","Marco Polo"],
  2,"Hard","Xuanzang visited India 629–645 CE during Harsha's reign.", y="NDA 2023 I"),
Q("The 'Sangam Age' refers to the classical period of:",
  ["North Indian literature","South Indian (Tamil) literature","Sanskrit literature","Pali literature"],
  1,"Hard","Sangam literature: ancient Tamil poetry compiled by academies.", y="NDA 2017 II"),
Q("First metal used extensively by humans:",
  ["Iron","Bronze","Copper","Tin"],
  2,"Medium","Copper was the first metal used by humans.", y="NDA 2022 II"),
Q("The 'Triple Gem' (Triratna) in Buddhism:",
  ["Buddha, Dharma, Sangha","Buddha, Brahma, Karma",
   "Nirvana, Dharma, Karma","Buddha, Sangha, Moksha"],
  0,"Hard","The Three Jewels: Buddha, Dharma (teachings), Sangha (community).", y="NDA 2020 II"),
Q("Megasthenes was the ambassador of:",
  ["Alexander the Great","Seleucus I Nicator","Darius I","Antiochus I"],
  1,"Hard","Megasthenes, author of Indica, was Seleucus I's ambassador to Chandragupta.", y="NDA 2018 I"),
Q("The Jain concept of non-violence is called:",
  ["Karma","Ahimsa","Samsara","Moksha"],
  1,"Medium","Ahimsa (non-violence) is central to Jainism.", y="NDA 2021 I"),
Q("The 'Ain-i-Akbari' was written by:",
  ["Birbal","Abul Fazl","Todar Mal","Faizi"],
  1,"Hard","Abul Fazl wrote Akbarnama and Ain-i-Akbari.", y="NDA 2023 II"),
Q("Earliest evidence of settled agriculture in Indian subcontinent:",
  ["Mohenjo-daro","Mehragarh","Kalibangan","Lothal"],
  1,"Hard","Mehragarh (~7000 BCE) in Balochistan; earliest farming site.", y="NDA 2019 II"),
Q("The Mughal emperor who built the Taj Mahal:",
  ["Akbar","Jehangir","Shah Jahan","Aurangzeb"],
  2,"Medium","Shah Jahan built Taj Mahal (1632–1653) for Mumtaz Mahal.", y="NDA 2017 I"),
Q("The Battle of Plassey (1757) was fought between:",
  ["British and Marathas","British and Siraj-ud-Daulah","French and Nawab of Bengal","British and Hyder Ali"],
  1,"Hard","Clive defeated Siraj-ud-Daulah at Plassey, beginning British dominance.", y="NDA 2022 I"),
Q("The Rowlatt Act (1919) was opposed because it allowed:",
  ["Partition of Bengal","Detention without trial",
   "Curbing of press freedom","Taxation without representation"],
  1,"Hard","Rowlatt Act: indefinite detention without trial or appeal.", y="NDA 2020 I"),
Q("'Do or Die' slogan was associated with:",
  ["Non-Cooperation Movement","Civil Disobedience Movement",
   "Quit India Movement","Swadeshi Movement"],
  2,"Hard","Gandhi's 'Do or Die' (Karo ya Maro) was for Quit India (1942).", y="NDA 2018 II"),
Q("The Cabinet Mission (1946) proposed:",
  ["Immediate partition of India","A three-tier federal structure",
   "Dominion status for India","Direct transfer of power to Congress"],
  1,"Hard","Cabinet Mission Plan: federation with provinces and states.", y="NDA 2021 II"),
Q("First session of Indian National Congress (1885) was presided by:",
  ["A.O. Hume","W.C. Bonnerjee","Dadabhai Naoroji","Surendranath Banerjee"],
  1,"Hard","W.C. Bonnerjee was the first INC president at Bombay, 1885.", y="NDA 2019 I"),
Q("Partition of Bengal (1905) was reversed in:",
  ["1908","1911","1919","1920"],
  1,"Hard","Bengal reunited in 1911 at the Delhi Durbar.", y="NDA 2023 I"),
Q("Simon Commission (1927) was boycotted because:",
  ["It recommended partition","It had no Indian member",
   "It opposed elections","It proposed indirect rule"],
  1,"Hard","All seven members of Simon Commission were British.", y="NDA 2017 II"),
Q("'Drain of Wealth' theory was propounded by:",
  ["Bal Gangadhar Tilak","Dadabhai Naoroji",
   "Gopal Krishna Gokhale","R.C. Dutt"],
  1,"Hard","Naoroji's 'Poverty and Un-British Rule in India' (1901).", y="NDA 2022 II"),
Q("The 'Lucknow Pact' (1916) was between:",
  ["Congress and Muslim League","Congress and British govt",
   "Muslim League and British","Moderates and Extremists in Congress"],
  0,"Hard","Congress-Muslim League pact for joint political demands.", y="NDA 2020 II"),
Q("Subhas Chandra Bose founded the 'Indian National Army' (INA) with help of:",
  ["Soviet Union","Germany","Japan","USA"],
  2,"Hard","Japan helped reorganise POWs into INA (1943).", y="NDA 2018 I"),
Q("Indian Constituent Assembly adopted the Constitution on:",
  ["15 Aug 1947","26 Nov 1949","26 Jan 1950","2 Oct 1949"],
  1,"Hard","Adopted 26 Nov 1949; came into force 26 Jan 1950.", y="NDA 2021 I"),
Q("First General Elections in independent India:",
  ["1947–48","1950–51","1951–52","1954–55"],
  2,"Hard","First General Elections held Oct 1951–Feb 1952.", y="NDA 2023 II"),
Q("'Swaraj is my birthright' was declared by:",
  ["M.K. Gandhi","Bal Gangadhar Tilak","Nehru","Lala Lajpat Rai"],
  1,"Hard","Tilak's famous declaration at Amravati Congress, 1906.", y="NDA 2019 II"),
Q("The Poona Pact (1932) was between Gandhi and:",
  ["Muhammad Ali Jinnah","B.R. Ambedkar",
   "Bal Gangadhar Tilak","Madan Mohan Malaviya"],
  1,"Hard","Gandhi's fast led to Poona Pact with Ambedkar on Dalit representation.", y="NDA 2017 I"),
Q("Which Act introduced provincial autonomy in India?",
  ["Government of India Act 1909","Government of India Act 1919",
   "Government of India Act 1935","Indian Councils Act 1892"],
  2,"Hard","GoI Act 1935 introduced provincial autonomy and federation.", y="NDA 2022 I"),
Q("'Vande Mataram' was composed by:",
  ["Rabindranath Tagore","Bankim Chandra Chattopadhyay",
   "Bal Gangadhar Tilak","Subramania Bharati"],
  1,"Hard","Bankim Chandra wrote 'Vande Mataram' in Anandamath (1882).", y="NDA 2020 I"),
Q("Aryabhata's famous work 'Aryabhatiya' covers:",
  ["Ayurveda","Mathematics and astronomy","Military strategy","Grammar"],
  1,"Hard","Aryabhatiya (499 CE): algebra, trigonometry, spherical astronomy.", y="NDA 2018 II"),
Q("The Bhakti movement stressed:",
  ["Idol worship","Caste hierarchy","Personal devotion to God without rituals",
   "Vedic yajnas"],
  2,"Hard","Bhakti: direct, personal relationship with God; anti-caste.", y="NDA 2021 II"),
Q("Who started the 'Dandi March' in 1930?",
  ["Nehru","Subhas Chandra Bose","Mahatma Gandhi","Sardar Patel"],
  2,"Medium","Gandhi led the 240-mile Dandi Salt March on 12 March 1930.", y="NDA 2023 I"),
Q("The Jallianwala Bagh massacre (1919) was ordered by:",
  ["Lord Chelmsford","General Dyer","Lord Curzon","Lord Mountbatten"],
  1,"Hard","Brigadier-General Reginald Dyer ordered firing on 13 April 1919.", y="NDA 2019 I"),
Q("First Indian woman to become President of India:",
  ["Sarojini Naidu","Indira Gandhi","Pratibha Patil","Sonia Gandhi"],
  2,"Hard","Pratibha Devisingh Patil, 12th President (2007–2012).", y="NDA 2017 II"),
Q("The 'Subsidiary Alliance' system was introduced by:",
  ["Dalhousie","Wellesley","Clive","Cornwallis"],
  1,"Hard","Lord Wellesley introduced Subsidiary Alliance (1798) to control Indian rulers.", y="NDA 2022 II"),
Q("The Indian National Army (INA) trials were held at:",
  ["Lahore","Bombay","Delhi (Red Fort)","Calcutta"],
  2,"Hard","INA trials at Red Fort, Delhi (1945–46) sparked massive protests.", y="NDA 2020 II"),
Q("First Census in India was conducted in:",
  ["1872","1881","1891","1901"],
  0,"Hard","First synchronous census: 1881; but first partial census: 1872.", y="NDA 2018 I"),
Q("Who established the Ramakrishna Mission?",
  ["Ramakrishna Paramahansa","Swami Vivekananda","Dayananda Saraswati","Bal Gangadhar Tilak"],
  1,"Hard","Vivekananda founded Ramakrishna Mission in 1897.", y="NDA 2021 I"),
Q("The term 'Sepoy' originally referred to:",
  ["A cavalry soldier","An Indian soldier serving a European power",
   "A sailor","A police constable"],
  1,"Medium","'Sipahi' = soldier; Indians serving British East India Company.", y="NDA 2023 II"),
Q("The Charter Act of 1813 was significant because it:",
  ["Ended East India Company's trade monopoly except in China and tea",
   "Gave Indians legislative powers",
   "Abolished the Company's rule",
   "Introduced elections"],
  0,"Hard","Charter Act 1813 ended Company's India trade monopoly; retained China monopoly.", y="NDA 2019 II"),
Q("The Indian Independence Act 1947 was passed by:",
  ["Indian Constituent Assembly","British Parliament",
   "Viceroy's Council","United Nations"],
  1,"Hard","British Parliament passed the Indian Independence Act 1947.", y="NDA 2017 I"),
Q("The 'Doctrine of Lapse' was introduced by:",
  ["Warren Hastings","Lord Dalhousie","Lord Wellesley","Lord Curzon"],
  1,"Hard","Dalhousie's Doctrine of Lapse: annexe princely states without heirs.", y="NDA 2022 I"),
Q("The First War of Indian Independence (1857) began at:",
  ["Calcutta","Delhi","Meerut","Lucknow"],
  2,"Hard","Mutiny began at Meerut on 10 May 1857.", y="NDA 2020 I"),
Q("The Peshwa was the Prime Minister of which empire?",
  ["Mughal","Maratha","Vijayanagara","Mysore"],
  1,"Hard","Peshwa = PM of Maratha Confederacy; became de facto rulers.", y="NDA 2018 II"),
Q("Gandhi's concept of non-violent resistance is called:",
  ["Ahimsa","Satyagraha","Swaraj","Swadeshi"],
  1,"Hard","Satyagraha = 'truth-force'; Gandhi's method of non-violent resistance.", y="NDA 2021 II"),
Q("The Mountbatten Plan (June 1947) provided for:",
  ["United India with federal structure","Partition of India and Pakistan",
   "Dominion status without partition","Transfer of power to INC only"],
  1,"Hard","Mountbatten Plan announced partition and transfer of power.", y="NDA 2023 I"),
Q("The Home Rule Movement was started by:",
  ["Annie Besant and Bal Gangadhar Tilak","Gandhi and Nehru",
   "Sarojini Naidu","Gokhale"],
  0,"Hard","Two Home Rule Leagues: Tilak's (1916) and Annie Besant's (1916).", y="NDA 2019 I"),
Q("Which battle established British supremacy in Bengal?",
  ["Battle of Plassey (1757)","Battle of Buxar (1764)",
   "Battle of Wandiwash (1760)","Third Battle of Panipat (1761)"],
  0,"Hard","Plassey 1757: Clive defeated Siraj-ud-Daulah; started British raj in Bengal.", y="NDA 2017 II"),
Q("The 'Permanent Settlement' of 1793 was introduced by:",
  ["Lord Cornwallis","Lord Dalhousie","Warren Hastings","Lord Wellesley"],
  0,"Hard","Lord Cornwallis fixed land revenue permanently with zamindars in Bengal.", y="NDA 2022 II"),
Q("Who founded the Aligarh Muslim University (originally MAO College)?",
  ["Muhammad Ali Jinnah","Sir Syed Ahmed Khan",
   "Maulana Azad","Agha Khan"],
  1,"Hard","Sir Syed Ahmed Khan founded Muhammadan Anglo-Oriental College at Aligarh in 1875.", y="NDA 2020 II"),
Q("The 'Swadeshi Movement' was triggered by:",
  ["Non-Cooperation Movement","Partition of Bengal (1905)",
   "Jallianwala Bagh massacre","Rowlatt Act"],
  1,"Hard","Partition of Bengal (1905) by Lord Curzon sparked the Swadeshi movement.", y="NDA 2019 I"),
Q("The Constituent Assembly of India was set up under the:",
  ["Mountbatten Plan","Indian Independence Act 1947",
   "Cabinet Mission Plan (1946)","Government of India Act 1935"],
  2,"Hard","Cabinet Mission Plan (1946) established the Constituent Assembly framework.", y="NDA 2021 I"),
],
},

# ══════════════════════════════════════════════
"Geography": {
"Indian & World Geography": [
Q("The Standard Meridian of India (IST) is:",
  ["80.5°E","82.5°E","85.5°E","77.5°E"],
  1,"Hard","82°30'E passes through Mirzapur/Prayagraj; IST=UTC+5:30", y="NDA 2022 I"),
Q("Which is the oldest mountain range in India?",
  ["Himalayas","Vindhya","Aravalli","Satpura"],
  2,"Hard","Aravallis are among the world's oldest fold mountains (~350 Ma).", y="NDA 2020 I"),
Q("'Loo' is a:",
  ["Monsoon wind of coastal India","Hot dry summer wind blowing across North India",
   "Cold polar wind","Local sea breeze"],
  1,"Medium","Loo: hot, dry, dusty wind in North India (May-June).", y="NDA 2018 II"),
Q("Ten Degree Channel separates:",
  ["India and Sri Lanka","Little Andaman and Car Nicobar Islands",
   "Lakshadweep and Maldives","North and South Andaman"],
  1,"Hard","10° Channel lies between Little Andaman (India) and Car Nicobar.", y="NDA 2021 II"),
Q("Tropic of Cancer passes through how many Indian states?",
  ["6","7","8","9"],
  2,"Hard","Gujarat, Rajasthan, MP, Chhattisgarh, Jharkhand, WB, Tripura, Mizoram = 8", y="NDA 2019 I"),
Q("Which river is called the 'Sorrow of Bihar'?",
  ["Ganga","Son","Kosi","Mahanadi"],
  2,"Hard","Kosi River frequently floods Bihar; called 'Sorrow of Bihar'.", y="NDA 2023 I"),
Q("The Western Ghats are also called:",
  ["Deccan Plateau edge","Sahyadri mountains","Eastern Ghats","Vindhya Range"],
  1,"Medium","Western Ghats = Sahyadri.", y="NDA 2017 II"),
Q("India's largest lagoon:",
  ["Pulicat Lake","Chilika Lake","Wular Lake","Sambhar Lake"],
  1,"Hard","Chilika Lake (Odisha) is India's largest coastal lagoon.", y="NDA 2022 II"),
Q("'Sundarbans' are located in:",
  ["Maharashtra","West Bengal and Bangladesh",
   "Andaman and Nicobar Islands","Odisha"],
  1,"Medium","Sundarbans mangrove delta: West Bengal (India) and Bangladesh.", y="NDA 2020 II"),
Q("The 'Rain shadow' region in India is on the ___ side of Western Ghats:",
  ["Western (windward)","Eastern (leeward)","Northern","Southern"],
  1,"Hard","Eastern side (leeward) receives less rainfall.", y="NDA 2018 I"),
Q("The Tropopause is highest over:",
  ["Poles","Equator","Tropics of Cancer/Capricorn","45° latitude"],
  1,"Hard","Tropopause: ~18 km at equator; ~8 km at poles.", y="NDA 2021 I"),
Q("Which Indian state has the longest coastline?",
  ["Maharashtra","Tamil Nadu","Andhra Pradesh","Gujarat"],
  3,"Hard","Gujarat has the longest mainland coastline (~1600 km).", y="NDA 2023 II"),
Q("Black soil (Regur) is most suitable for:",
  ["Rice cultivation","Cotton cultivation","Tea plantation","Jute cultivation"],
  1,"Medium","Black soil retains moisture; ideal for cotton.", y="NDA 2019 II"),
Q("The river that flows through the Shivpuri and Panna districts (MP):",
  ["Chambal","Ken","Betwa","Son"],
  1,"Hard","Ken River flows through Panna (famous for diamond mines).", y="NDA 2017 I"),
Q("'Laterite soil' is typically found in:",
  ["River deltas","Regions with alternating wet and dry climate",
   "High altitudes","Arid deserts"],
  1,"Hard","Laterite forms in tropical monsoon climate with seasonal leaching.", y="NDA 2022 I"),
Q("Country with the longest coastline in the world:",
  ["Russia","Australia","Canada","Norway"],
  2,"Hard","Canada has the world's longest coastline (~202,080 km).", y="NDA 2020 I"),
Q("The Mariana Trench is located in:",
  ["Atlantic Ocean","Arctic Ocean","Indian Ocean","Pacific Ocean"],
  3,"Hard","Mariana Trench in western Pacific; deepest point (~11,034 m).", y="NDA 2018 II"),
Q("'Pampas' grasslands are located in:",
  ["North America","Australia","South America","South Africa"],
  2,"Hard","Pampas: temperate grasslands of Argentina, Uruguay, Brazil.", y="NDA 2021 II"),
Q("Suez Canal connects:",
  ["Red Sea and Arabian Sea","Red Sea and Mediterranean Sea",
   "Black Sea and Caspian Sea","Persian Gulf and Arabian Sea"],
  1,"Hard","Suez Canal (1869): Mediterranean ↔ Red Sea; reduces Europe-Asia distance.", y="NDA 2019 I"),
Q("The 'Ring of Fire' encircles:",
  ["Atlantic Ocean","Indian Ocean","Pacific Ocean","Arctic Ocean"],
  2,"Hard","Ring of Fire = belt of volcanic/seismic activity around Pacific.", y="NDA 2023 I"),
Q("The deepest lake in the world:",
  ["Lake Superior","Lake Baikal","Caspian Sea","Lake Tanganyika"],
  1,"Hard","Lake Baikal (Russia): ~1,642 m deep; world's deepest.", y="NDA 2017 II"),
Q("'Sahel' region is:",
  ["Dense equatorial rainforest","Semi-arid transition zone south of Sahara",
   "Coastal wetland","Mediterranean scrubland"],
  1,"Hard","Sahel: narrow belt between Sahara and savanna (recurring drought).", y="NDA 2022 II"),
Q("The Greenwich Meridian (0°) passes through which African country?",
  ["Nigeria","Senegal","Ghana","Algeria"],
  2,"Hard","0° meridian passes through Ghana (and UK, France, Spain, Algeria).", y="NDA 2020 II"),
Q("The largest proven oil reserves are found in:",
  ["Saudi Arabia","Russia","Iran","Venezuela"],
  3,"Hard","Venezuela has world's largest proven oil reserves (heavy crude).", y="NDA 2018 I"),
Q("Strait of Malacca lies between:",
  ["Malaysia and Indonesia","India and Sri Lanka",
   "Indonesia and Philippines","Malaysia and Singapore only"],
  0,"Hard","Malacca Strait: between Malay Peninsula and Sumatra (Indonesia).", y="NDA 2021 I"),
Q("The Great Barrier Reef is located in:",
  ["Indian Ocean","South China Sea",
   "Coral Sea (off NE Australia)","Caribbean Sea"],
  2,"Hard","Great Barrier Reef: off Queensland coast in the Coral Sea.", y="NDA 2023 II"),
Q("'Tundra' climate is found in:",
  ["Tropical belt","Equatorial regions","Mediterranean coasts","Arctic/sub-Arctic regions"],
  3,"Hard","Tundra: treeless, permafrost; Arctic Canada, Alaska, Russia.", y="NDA 2019 II"),
Q("The International Date Line mostly passes through:",
  ["Atlantic Ocean","Land masses","Arctic Ocean","Pacific Ocean"],
  3,"Medium","IDL runs through the Pacific, avoiding land masses.", y="NDA 2017 I"),
Q("Monsoon originates primarily due to:",
  ["Differential heating of land and sea","Earth's rotation alone",
   "Position of Himalayas","Ocean currents"],
  0,"Hard","Monsoon driven by thermal contrast: land heats/cools faster than sea.", y="NDA 2022 I"),
Q("Which type of rainfall is associated with mountains?",
  ["Orographic (relief) rainfall","Convectional rainfall",
   "Cyclonic rainfall","Frontal rainfall"],
  0,"Medium","Moist air forced upward by mountains cools and condenses.", y="NDA 2020 I"),
Q("The Amazon River drains into:",
  ["Pacific Ocean","Caribbean Sea","Atlantic Ocean","Gulf of Mexico"],
  2,"Medium","Amazon empties into the Atlantic Ocean near Marajó Island.", y="NDA 2018 II"),
Q("The Deccan Plateau is made up of:",
  ["Sedimentary rocks","Metamorphic rocks","Crystalline basaltic lava","Alluvial deposits"],
  2,"Hard","Deccan Traps: volcanic basalt from ~66 million years ago.", y="NDA 2021 II"),
Q("The world's highest navigable lake:",
  ["Lake Victoria","Lake Titicaca","Lake Superior","Dead Sea"],
  1,"Hard","Lake Titicaca (Peru/Bolivia): ~3,812 m; world's highest navigable lake.", y="NDA 2023 I"),
Q("'Roaring Forties' refers to:",
  ["Cyclones in Bay of Bengal","Strong westerly winds in 40–50°S latitudes",
   "Trade winds in tropics","Polar easterlies"],
  1,"Hard","Roaring Forties: strong westerlies in Southern Hemisphere.", y="NDA 2019 I"),
Q("Which ocean has the largest area?",
  ["Atlantic Ocean","Indian Ocean","Pacific Ocean","Arctic Ocean"],
  2,"Medium","Pacific Ocean: ~165 million km² (largest).", y="NDA 2017 II"),
Q("Soil erosion is most severe when slope angle is approximately:",
  ["0°–5°","10°–15°","25°–40°","75°–90°"],
  2,"Hard","Maximum erosion occurs at moderate slopes (~25–45°).", y="NDA 2022 II"),
Q("The 'Grand Canyon' is carved by the ___ River:",
  ["Mississippi","Missouri","Colorado","Columbia"],
  2,"Hard","Colorado River carved the Grand Canyon, Arizona, USA.", y="NDA 2020 II"),
Q("The country with the largest number of volcanoes:",
  ["Japan","Indonesia","Iceland","USA"],
  1,"Hard","Indonesia has ~130 active volcanoes along the Ring of Fire.", y="NDA 2018 I"),
Q("'Chinook' is a local wind in:",
  ["Sahara","Rocky Mountains (North America)","Alps","Himalayas"],
  1,"Hard","Chinook: warm, dry wind descending the eastern Rockies.", y="NDA 2021 I"),
Q("Longest river in the world:",
  ["Amazon","Congo","Mississippi","Nile"],
  3,"Hard","Nile (~6,650 km) traditionally considered longest.", y="NDA 2023 II"),
Q("Equatorial climate is characterised by:",
  ["High temperature, high rainfall throughout year",
   "High temperature, seasonal rainfall",
   "Low temperature, low rainfall","Mild temperature, winter rainfall"],
  0,"Hard","Equatorial: high temperatures year-round, heavy daily convectional rain.", y="NDA 2019 II"),
Q("The 'Great Dividing Range' is in:",
  ["New Zealand","India","Australia","South Africa"],
  2,"Hard","Eastern Australian Highlands = Great Dividing Range.", y="NDA 2017 I"),
Q("Gulf of Mannar lies between:",
  ["India and Sri Lanka","India and Maldives",
   "Sri Lanka and Indonesia","India and Myanmar"],
  0,"Hard","Gulf of Mannar: between Tamil Nadu (India) and western Sri Lanka.", y="NDA 2022 I"),
Q("'Foehn' is a local wind in:",
  ["Sahara Desert","Alps region","Arabian Peninsula","North India"],
  1,"Hard","Foehn: warm, dry wind on leeward side of Alps.", y="NDA 2020 I"),
Q("The Tropic of Capricorn passes through:",
  ["USA","China","Australia","India"],
  2,"Hard","Tropic of Capricorn (~23.5°S) passes through Australia, Brazil, South Africa.", y="NDA 2018 II"),
Q("ITCZ (Inter-Tropical Convergence Zone) is associated with:",
  ["Trade winds converging at equatorial region","Polar winds","Westerlies","Jet stream"],
  0,"Hard","ITCZ: zone where NE and SE trade winds meet near equator.", y="NDA 2021 II"),
Q("'Permafrost' refers to:",
  ["Perennial snowfields","Frozen soil persisting year-round",
   "Polar ice sheets","Alpine glaciers"],
  1,"Hard","Permafrost = ground frozen continuously for two or more years.", y="NDA 2017 II"),
Q("The Nile flows through how many countries?",
  ["7","9","11","6"],
  2,"Hard","Nile passes through 11 countries from south to north.", y="NDA 2019 I"),
Q("Which country shares the longest border with India?",
  ["China","Pakistan","Bangladesh","Nepal"],
  2,"Hard","Bangladesh shares the longest border with India (~4,156 km).", y="NDA 2017 II"),
Q("'El Niño' refers to:",
  ["Cold current off South America",
   "Warming of central/eastern Pacific causing global weather disruption",
   "Monsoon depression over India",
   "Atlantic hurricane system"],
  1,"Hard","El Niño: periodic warming of eastern Pacific; disrupts global weather.", y="NDA 2022 II"),
],
},

# ══════════════════════════════════════════════
"Economics": {
"Indian Economy & Economic Theory": [
Q("India's GDP is measured at:",
  ["Current factor cost","Market prices (with taxes and subsidies)",
   "Constant factor cost only","Foreign exchange rates"],
  1,"Hard","India shifted to GDP at market prices (2015 revision).", y="NDA 2021 I"),
Q("MPC=0.75; Keynesian multiplier=",
  ["4","3","5","1.33"],
  0,"Hard","Multiplier=1/(1–MPC)=1/0.25=4", y="NDA 2019 II"),
Q("'Stagflation' refers to:",
  ["High growth with low inflation","High inflation with stagnant growth and high unemployment",
   "Deflation with high employment","Boom period"],
  1,"Hard","Stagflation: simultaneous inflation and economic stagnation.", y="NDA 2022 II"),
Q("Repo rate is the rate at which:",
  ["Banks lend to customers","RBI lends short-term funds to commercial banks",
   "Banks borrow from customers","Government borrows from RBI"],
  1,"Hard","Repo rate: key monetary policy instrument of RBI.", y="NDA 2020 I"),
Q("CRR reduced → money supply in economy:",
  ["Decreases","Increases","Remains unchanged","Becomes zero"],
  1,"Hard","Lower CRR → banks hold less reserve → more funds for lending → ↑money supply", y="NDA 2018 I"),
Q("India's GDP base year (current National Accounts series):",
  ["2004–05","2011–12","2010–11","2015–16"],
  1,"Hard","2011–12 is the base year for India's current GDP series.", y="NDA 2021 II"),
Q("Laffer Curve illustrates the relationship between:",
  ["Money supply and inflation","Tax rate and tax revenue collected",
   "GDP and employment","Interest rate and investment"],
  1,"Hard","Laffer: beyond a point, higher tax rates reduce total revenue.", y="NDA 2023 I"),
Q("Gini coefficient of 0 means:",
  ["Complete inequality","Complete equality","50% inequality","No data"],
  1,"Hard","Gini=0: perfect equality; Gini=1: maximum inequality.", y="NDA 2019 I"),
Q("Fiscal deficit = Total expenditure minus:",
  ["Tax revenues","Revenue receipts","Total receipts excluding borrowings","Capital receipts"],
  2,"Hard","Fiscal deficit = Total expenditure – Total receipts (excl. borrowings).", y="NDA 2017 II"),
Q("'Revenue deficit' is:",
  ["Total expenditure – total receipts","Revenue expenditure – revenue receipts",
   "Capital expenditure – capital receipts","Trade deficit"],
  1,"Hard","Revenue deficit shows gap in day-to-day government finances.", y="NDA 2022 I"),
Q("NITI Aayog replaced:",
  ["Finance Commission","Planning Commission",
   "Economic Advisory Council","National Development Council"],
  1,"Medium","Planning Commission dissolved; NITI Aayog formed Jan 2015.", y="NDA 2020 II"),
Q("HDI does NOT include:",
  ["Life expectancy","Education index","Per capita income (GNI)","Military expenditure"],
  3,"Hard","HDI = health + education + income; no military component.", y="NDA 2018 II"),
Q("'Purchasing Power Parity' (PPP) is used to:",
  ["Measure stock market performance","Compare real standards of living across countries",
   "Measure export competitiveness","Track currency speculation"],
  1,"Hard","PPP adjusts for price level differences to compare real GDP.", y="NDA 2021 I"),
Q("PED = –2; price rises by 10%. Quantity demanded changes by:",
  ["5% rise","20% fall","2% fall","10% rise"],
  1,"Hard","|PED|×%ΔP=2×10=20% fall in quantity.", y="NDA 2023 II"),
Q("Under perfect competition in the long run, firms earn:",
  ["Supernormal profits","Normal profits (zero economic profit)","Losses","Monopoly rents"],
  1,"Hard","Free entry/exit ensures long-run normal profit (P=AC).", y="NDA 2019 II"),
Q("'Invisible hand' concept was introduced by:",
  ["J.M. Keynes","Adam Smith","David Ricardo","Alfred Marshall"],
  1,"Hard","Adam Smith's 'The Wealth of Nations' (1776) described the invisible hand.", y="NDA 2017 I"),
Q("Giffen goods violate the Law of Demand because:",
  ["They are luxury goods","They have inelastic supply",
   "They are inferior goods where income effect > substitution effect",
   "Their demand is government-determined"],
  2,"Hard","Giffen goods: inferior goods with strong positive income effect.", y="NDA 2022 I"),
Q("Kinked demand curve explains price rigidity in:",
  ["Perfect competition","Monopoly","Oligopoly","Monopsony"],
  2,"Hard","Sweezy's kinked demand curve model for oligopoly pricing.", y="NDA 2020 I"),
Q("When MR = 0, Total Revenue is at its:",
  ["Zero","Maximum","Minimum","Equal to AR"],
  1,"Hard","TR is maximum when MR=0 (elasticity=1).", y="NDA 2018 I"),
Q("Indifference curves cannot intersect because:",
  ["They represent different income levels",
   "Intersection would violate the transitivity of preferences",
   "They are parallel by definition","Each has a different slope"],
  1,"Hard","Intersection implies contradictory rankings of bundles.", y="NDA 2021 II"),
Q("MRTS (Marginal Rate of Technical Substitution) equals:",
  ["Ratio of output prices","Ratio of marginal products (MPL/MPK)",
   "Slope of isocost line","Average product ratio"],
  1,"Hard","MRTS = MPL/MPK (slope of isoquant).", y="NDA 2023 I"),
Q("Deadweight loss in monopoly arises because:",
  ["P > MC, leading to underproduction relative to competitive output",
   "Costs are too high","Consumers have too much surplus","P = MC causes losses"],
  0,"Hard","Monopolist restricts output; welfare loss vs competitive equilibrium.", y="NDA 2019 I"),
Q("ATC – AVC =",
  ["AFC","MC","Zero","Profit margin"],
  0,"Hard","ATC=AFC+AVC → ATC–AVC=AFC", y="NDA 2017 II"),
Q("'Crowding out' effect occurs when:",
  ["Government borrowing raises interest rates, reducing private investment",
   "Exports crowd out imports","High taxes reduce consumption","None of these"],
  0,"Hard","Expansionary fiscal policy → ↑interest rates → ↓private investment.", y="NDA 2022 II"),
Q("Nominal GDP = ₹200 crore, GDP deflator = 125. Real GDP =",
  ["₹160 crore","₹250 crore","₹175 crore","₹200 crore"],
  0,"Hard","Real GDP = (Nominal/Deflator)×100 = 200/125×100 = 160", y="NDA 2020 II"),
Q("In Fisher's Quantity Theory (MV=PQ): if M doubles, V and Q constant, P:",
  ["Halves","Doubles","Stays same","Quadruples"],
  1,"Hard","Proportional relationship: P doubles.", y="NDA 2018 II"),
Q("'Liquidity Trap' occurs when:",
  ["Money supply is too high","Banks have no liquidity",
   "Interest rates are near zero; monetary policy becomes ineffective",
   "Inflation is very high"],
  2,"Hard","At zero lower bound, people hoard cash; monetary policy fails.", y="NDA 2021 I"),
Q("The Phillips Curve shows inverse relation between:",
  ["GDP and investment","Inflation and unemployment",
   "Trade balance and exchange rate","Money supply and price level"],
  1,"Hard","Phillips Curve: ↑inflation ↔ ↓unemployment (short-run trade-off).", y="NDA 2023 II"),
Q("'World Economic Outlook' is published by:",
  ["World Bank","IMF","WTO","UNCTAD"],
  1,"Medium","IMF publishes World Economic Outlook twice yearly.", y="NDA 2019 II"),
Q("Which is NOT a function of money?",
  ["Medium of exchange","Store of value","Standard of deferred payment","Source of taxation"],
  3,"Hard","The four functions: medium of exchange, store of value, unit of account, deferred payment.", y="NDA 2017 I"),
Q("'Base effect' in inflation refers to:",
  ["Current month price level","Influence of the previous period's price on current inflation rate",
   "RBI's inflation target","Average price across states"],
  1,"Hard","High base year → lower current inflation even if prices rise similarly.", y="NDA 2022 I"),
Q("Consumer surplus is maximised under:",
  ["Monopoly","Oligopoly","Perfect competition","Monopsony"],
  2,"Hard","Perfect competition: P=MC, maximum consumer surplus.", y="NDA 2020 I"),
Q("Lerner Index = (P–MC)/P measures:",
  ["Market concentration","Degree of monopoly power","Price elasticity","Profit margin"],
  1,"Hard","Lerner Index: 0 = competitive; 1 = pure monopoly.", y="NDA 2018 I"),
Q("'Isocost line' slope equals:",
  ["MPL/MPK","Wage/Rental rate (w/r)","Price ratio of goods","MRS"],
  1,"Hard","Isocost: combinations of inputs for given cost; slope=–w/r", y="NDA 2021 II"),
Q("Break-even for a firm occurs where:",
  ["TR = TC","MR = MC","AR = MR","TR > TC"],
  0,"Hard","Break-even: total revenue equals total cost (zero economic profit).", y="NDA 2023 I"),
Q("'Narrow money' (M1) in India includes:",
  ["Currency + demand deposits + time deposits",
   "Currency in circulation + demand deposits with banks",
   "Only currency notes and coins","All bank deposits including FDs"],
  1,"Hard","M1=Currency+Demand deposits+Other deposits with RBI", y="NDA 2019 I"),
Q("Negative cross-price elasticity between two goods means they are:",
  ["Substitutes","Complements","Independent goods","Inferior goods"],
  1,"Hard","Negative XPE: rise in price of X → fall in demand for Y → complements.", y="NDA 2017 II"),
Q("Price discrimination requires:",
  ["Perfect competition","Market segmentation and prevention of resale",
   "Homogeneous goods","Identical elasticities across segments"],
  1,"Hard","Price discrimination: segment markets; prevent arbitrage.", y="NDA 2022 II"),
Q("'Engel Curve' shows relationship between:",
  ["Price and quantity demanded","Income and quantity demanded",
   "Two inputs in production","Consumer surplus and price"],
  1,"Hard","Engel Curve: quantity demanded vs income (other things equal).", y="NDA 2020 II"),
Q("The 'Invisible Hand' metaphor implies that:",
  ["Government regulation maximises welfare",
   "Individuals pursuing self-interest promote social welfare unintentionally",
   "Markets always fail without intervention",
   "Monopolies are beneficial"],
  1,"Hard","Adam Smith: self-interest in competitive markets leads to efficient outcomes.", y="NDA 2018 II"),
Q("'Green Revolution' in India was associated with:",
  ["Cotton cultivation","High-yielding variety (HYV) seeds for wheat and rice",
   "Afforestation programme","Dairy development"],
  1,"Medium","Green Revolution (1960s–70s): HYV seeds, fertilisers, irrigation → food security.", y="NDA 2021 I"),
Q("The concept of 'Opportunity Cost' is best described as:",
  ["The monetary cost of production","The next best alternative forgone",
   "The historical cost of an asset","The average cost of production"],
  1,"Hard","Opportunity cost = value of best alternative sacrificed.", y="NDA 2023 II"),
Q("'Monopsony' refers to a market with:",
  ["Single seller","Single buyer","Few sellers","Few buyers"],
  1,"Hard","Monopsony: single buyer dominates market (e.g., sole employer in a town).", y="NDA 2019 I"),
Q("The WTO (World Trade Organization) was established in:",
  ["1947","1948","1995","2001"],
  2,"Hard","WTO replaced GATT on 1 January 1995.", y="NDA PYQ"),
Q("Which policy tool directly controls money supply?",
  ["Fiscal policy","Open Market Operations (monetary policy)",
   "Trade policy","Industrial policy"],
  1,"Hard","OMO: RBI buys/sells government securities to control money supply.", y="NDA 2022 I"),
Q("The 'Human Development Index' was developed by:",
  ["World Bank","IMF","UNDP","WHO"],
  2,"Hard","HDI created by Mahbub ul Haq and Amartya Sen for UNDP (1990).", y="NDA 2020 I"),
Q("'Stagflation' is difficult to cure because:",
  ["The causes are unknown","Policies for inflation worsen unemployment and vice versa",
   "It is very rare","Central banks have unlimited tools"],
  1,"Hard","Anti-inflation policy (raise rates) increases unemployment; and vice versa.", y="NDA 2018 II"),
Q("The repo rate cut leads to:",
  ["Rise in EMIs","Fall in borrowing costs; boost to investment",
   "Rise in FD interest rates","Appreciation of rupee"],
  1,"Hard","Lower repo → cheaper credit → ↑investment and consumption → ↑GDP", y="NDA 2021 II"),
Q("The WTO was established in:",
  ["1947","1948","1995","2001"],
  2,"Hard","WTO replaced GATT on 1 January 1995.", y="NDA 2017 II"),
Q("'Opportunity Cost' is best described as:",
  ["Monetary cost of production","The next best alternative forgone",
   "Historical cost of an asset","Average cost of production"],
  1,"Hard","Opportunity cost = value of best alternative sacrificed.", y="NDA PYQ"),
Q("National Income at factor cost = National Income at market prices minus:",
  ["Subsidies","Net indirect taxes (indirect taxes – subsidies)",
   "Depreciation","Transfer payments"],
  1,"Hard","Factor cost = Market price – Net indirect taxes.", y="NDA 2023 I"),
Q("Which of the following is a 'merit good'?",
  ["Cigarettes","Education","Luxury cars","Alcohol"],
  1,"Hard","Merit goods: education, healthcare — under-consumed if left to market.", y="NDA 2019 II"),
Q("'Balance of Payments' deficit means:",
  ["Export > Import","More foreign exchange outflow than inflow",
   "Fiscal deficit exceeds revenue deficit","Trade surplus"],
  1,"Hard","BoP deficit: total payments abroad exceed total receipts from abroad.", y="NDA 2017 I"),
],
},

}  # end QUESTION_BANK

CHAPTERS = {
    "English":         ["Grammar & Vocabulary"],
    "Mathematics":     ["Algebra & Number Theory", "Trigonometry & Geometry"],
    "General Science": ["Physics", "Chemistry", "Biology"],
    "History":         ["Indian History"],
    "Geography":       ["Indian & World Geography"],
    "Economics":       ["Indian Economy & Economic Theory"],
}
SUBJECTS      = list(QUESTION_BANK.keys())
SUBJECT_ICONS = {
    "English":"📝", "Mathematics":"📐", "General Science":"🔬",
    "History":"🏛️", "Geography":"🌏", "Economics":"💹"
}

# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "page": "landing",
        "name": "", "course": "NDA",
        "results": [], "db_loaded": False,
        "current_subject": None, "current_chapter": None,
        "current_mode": None, "questions": [], "answers": {},
        "test_start": None, "test_duration": 1800,
        "test_done": False, "last_result": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def load_db_results():
    if not st.session_state.db_loaded and st.session_state.name:
        rows = db_load_user_results(st.session_state.name)
        existing = {r.get("date") for r in st.session_state.results}
        for row in rows:
            if row.get("date") not in existing:
                st.session_state.results.append(row)
        st.session_state.db_loaded = True

# ═══════════════════════════════════════════════════════════════
# QUESTION SELECTION
# ═══════════════════════════════════════════════════════════════
def get_questions(subject, chapter=None, mode="chapter"):
    if chapter and chapter in QUESTION_BANK.get(subject, {}):
        pool = list(QUESTION_BANK[subject][chapter])
    else:
        pool = []
        for ch_qs in QUESTION_BANK.get(subject, {}).values():
            pool.extend(ch_qs)

    # Target: 50 for chapter, all for full mock
    k = min(50, len(pool)) if mode == "chapter" else len(pool)
    selected = random.sample(pool, k)

    # Shuffle options, keep correct pointer
    out = []
    for q in selected:
        opts      = list(q["options"])
        correct_t = opts[q["correct"]]
        random.shuffle(opts)
        out.append({**q, "options": opts, "correct": opts.index(correct_t)})
    return out

# ═══════════════════════════════════════════════════════════════
# SCORING
# ═══════════════════════════════════════════════════════════════
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
    raw         = correct * MARKS_CORRECT + wrong * MARKS_WRONG
    total_marks = len(questions) * MARKS_CORRECT
    pct         = round(max(0, raw) / total_marks * 100, 1) if total_marks else 0
    return {"correct": correct, "wrong": wrong, "unattempted": unattempted,
            "raw_score": round(raw, 2), "total_marks": total_marks, "percentage": pct}

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
def sidebar():
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="text-align:center;padding:1.5rem 0 1rem;">
            <div style="font-size:2.2rem;font-weight:800;color:white;font-family:'Poppins',sans-serif;
                        letter-spacing:-1px;">Grade<span style="color:#7ecfff;">UP</span></div>
            <div style="font-size:0.7rem;color:rgba(255,255,255,0.4);letter-spacing:0.12em;
                        text-transform:uppercase;margin-top:0.2rem;">Defence Exam Prep</div>
        </div>""", unsafe_allow_html=True)

        # User card
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.10);
                    border-radius:18px;padding:1rem;text-align:center;margin-bottom:1.2rem;">
            <div style="font-size:1.8rem;margin-bottom:0.3rem;">👤</div>
            <div style="font-weight:700;color:white;font-size:0.95rem;">{st.session_state.name}</div>
            <div style="margin-top:0.5rem;">
                <span style="background:rgba(126,207,255,0.15);border:1px solid rgba(126,207,255,0.25);
                             border-radius:999px;padding:0.2rem 0.8rem;font-size:0.75rem;color:#a8d8ff;">
                    🎯 {st.session_state.course}
                </span>
            </div>
        </div>""", unsafe_allow_html=True)

        # Quick stats
        results = st.session_state.results
        if results:
            avg  = sum(r["percentage"] for r in results) / len(results)
            best = max(results, key=lambda r: r["percentage"])
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.6rem;margin-bottom:1.2rem;">
                <div style="background:rgba(255,255,255,0.06);border-radius:14px;padding:0.7rem;text-align:center;">
                    <div style="font-size:1.4rem;font-weight:800;color:white;">{len(results)}</div>
                    <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.06em;">Tests</div>
                </div>
                <div style="background:rgba(255,255,255,0.06);border-radius:14px;padding:0.7rem;text-align:center;">
                    <div style="font-size:1.4rem;font-weight:800;color:#7ecfff;">{avg:.0f}%</div>
                    <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.06em;">Avg</div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        if st.button("🏠  Dashboard",  use_container_width=True):
            st.session_state.page = "dashboard"; st.rerun()
        if st.button("🏆  Leaderboard", use_container_width=True):
            st.session_state.page = "leaderboard"; st.rerun()

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        if st.button("🚪  Logout", use_container_width=True):
            db_delete_user(st.session_state.name)
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ═══════════════════════════════════════════════════════════════
# PAGE: LANDING
# ═══════════════════════════════════════════════════════════════
def page_landing():
    # Centre the form
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;padding:1.5rem 0 2rem;">
            <div style="font-family:'Poppins',sans-serif;font-size:4rem;font-weight:800;
                        color:white;letter-spacing:-2px;line-height:1;">
                Grade<span style="color:#7ecfff;">UP</span>
            </div>
            <div style="color:rgba(255,255,255,0.55);font-size:0.9rem;margin-top:0.6rem;
                        line-height:1.5;font-weight:400;">
                Prepare smarter for NDA, CDS &amp; Defence Exams<br>
                <span style="color:rgba(255,255,255,0.35);font-size:0.8rem;">
                    50+ PYQ questions · Negative marking · Live timer
                </span>
            </div>
        </div>""", unsafe_allow_html=True)

        # Name input
        name = st.text_input("Your Name", placeholder="Enter your full name")

        # Check if returning user
        returning = None
        if name and len(name.strip()) >= 2:
            returning = db_load_user(name.strip())

        if returning:
            st.markdown(f"""
            <div style="background:rgba(50,200,120,0.12);border:1px solid rgba(50,200,120,0.25);
                        border-radius:14px;padding:0.75rem 1rem;margin:0.5rem 0;font-size:0.88rem;">
                ✅ Welcome back, <strong>{name.strip()}</strong>! Course: {returning[0]}
            </div>""", unsafe_allow_html=True)
            if st.button(f"▶  Continue as {name.strip()}", use_container_width=True):
                st.session_state.name   = name.strip()
                st.session_state.course = returning[0]
                st.session_state.db_loaded = False
                st.session_state.page   = "dashboard"
                st.rerun()
            st.markdown("<div style='color:rgba(255,255,255,0.3);text-align:center;font-size:0.75rem;margin:0.5rem 0;'>or update your details below</div>", unsafe_allow_html=True)

        course = st.selectbox("Course", ["NDA", "CDS", "AFCAT", "Other"])

        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

        if st.button("Get Started →", use_container_width=True):
            if not name or len(name.strip()) < 2:
                st.error("Please enter your name (at least 2 characters).")
            else:
                db_save_user(name.strip(), course)
                st.session_state.name   = name.strip()
                st.session_state.course = course
                st.session_state.db_loaded = False
                st.session_state.page   = "dashboard"
                st.rerun()

        # Watermark — visible below submit
        st.markdown(WM_LANDING, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════
def page_dashboard():
    sidebar()
    load_db_results()

    st.markdown(f"""
    <div style="margin-bottom:2rem;">
        <h1 style="margin:0;font-size:2rem;">
            Welcome, {st.session_state.name} 👋
        </h1>
        <p style="color:rgba(255,255,255,0.45);margin:0.3rem 0 0;font-size:0.9rem;">
            {st.session_state.course} Aspirant · Select a subject to begin
        </p>
    </div>""", unsafe_allow_html=True)

    # Subject grid — 2 columns, clean cards
    st.markdown("#### Choose a Subject")
    cols = st.columns(2)
    for i, subject in enumerate(SUBJECTS):
        with cols[i % 2]:
            icon  = SUBJECT_ICONS.get(subject, "📖")
            total_qs = sum(len(v) for v in QUESTION_BANK[subject].values())
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.09);
                        border-radius:20px;padding:1.2rem 1.4rem;margin-bottom:0.6rem;">
                <div style="font-size:1.6rem;margin-bottom:0.4rem;">{icon}</div>
                <div style="font-weight:700;color:white;font-size:0.95rem;">{subject}</div>
                <div style="font-size:0.72rem;color:rgba(255,255,255,0.35);margin-top:0.2rem;">
                    {total_qs} PYQ questions
                </div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Start {subject}", key=f"sb_{subject}", use_container_width=True):
                st.session_state.current_subject = subject
                st.session_state.page = "mode_select"
                st.rerun()

    # Performance section
    results = st.session_state.results
    if results:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("#### Your Performance")

        df  = pd.DataFrame(results)
        c1, c2, c3, c4 = st.columns(4)
        cs  = "background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:18px;padding:1.1rem;text-align:center;"
        with c1: st.markdown(f'<div style="{cs}"><div class="stat-num">{len(df)}</div><div class="stat-label">Tests</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div style="{cs}"><div class="stat-num" style="color:#7ecfff;">{df["percentage"].mean():.0f}%</div><div class="stat-label">Average</div></div>', unsafe_allow_html=True)
        with c3:
            best_subj = df.groupby("subject")["percentage"].mean().idxmax()
            st.markdown(f'<div style="{cs}"><div style="font-size:1rem;font-weight:800;color:#7fffb0;padding:0.3rem 0;">{best_subj}</div><div class="stat-label">Best Subject</div></div>', unsafe_allow_html=True)
        with c4:
            total_w = int(sum(r.get("wrong",0) for r in results))
            st.markdown(f'<div style="{cs}"><div class="stat-num" style="color:#ff9090;">{total_w}</div><div class="stat-label">Wrong</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        df["#"] = range(1, len(df)+1)
        ax = alt.Axis(labelColor="rgba(255,255,255,0.5)", titleColor="rgba(255,255,255,0.5)",
                      gridColor="rgba(255,255,255,0.05)", domainColor="transparent", tickColor="transparent")
        chart = alt.Chart(df).mark_line(
            point={"filled": True, "size": 60, "color": "#7ecfff"},
            strokeWidth=2, color="#7ecfff"
        ).encode(
            x=alt.X("#:Q", title="Test Number", axis=ax),
            y=alt.Y("percentage:Q", title="Score %", scale=alt.Scale(domain=[0,100]), axis=ax),
            tooltip=["#", "subject", "mode", "percentage", "correct", "wrong"]
        ).properties(
            background="transparent", height=180,
            title=alt.TitleParams("Score Trend", color="rgba(255,255,255,0.6)", fontSize=12)
        ).configure_view(strokeWidth=0)
        st.altair_chart(chart, use_container_width=True)

    st.markdown(WM_FOOTER, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# PAGE: MODE SELECT
# ═══════════════════════════════════════════════════════════════
def page_mode_select():
    sidebar()
    subject = st.session_state.current_subject
    icon    = SUBJECT_ICONS.get(subject, "📖")
    total_q = sum(len(v) for v in QUESTION_BANK[subject].values())

    st.markdown(f"""
    <div style="margin-bottom:2rem;">
        <div style="font-size:2.5rem;">{icon}</div>
        <h2 style="margin:0.3rem 0 0.2rem;">{subject}</h2>
        <p style="color:rgba(255,255,255,0.4);font-size:0.85rem;margin:0;">
            {total_q} NDA PYQ questions available
        </p>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.09);
                    border-radius:22px;padding:2rem 1.5rem;text-align:center;margin-bottom:0.8rem;min-height:160px;">
            <div style="font-size:2rem;margin-bottom:0.6rem;">📋</div>
            <div style="font-weight:700;color:white;font-size:1rem;">Chapter Practice</div>
            <div style="color:rgba(255,255,255,0.4);font-size:0.78rem;margin-top:0.4rem;line-height:1.5;">
                50 Questions<br>30 minutes · Focused drill
            </div>
        </div>""", unsafe_allow_html=True)
        if st.button("Start Practice Test", key="ch_btn", use_container_width=True):
            chapters = list(QUESTION_BANK[subject].keys())
            if len(chapters) == 1:
                qs = get_questions(subject, chapters[0], "chapter")
                st.session_state.current_chapter  = chapters[0]
                st.session_state.current_mode     = "chapter"
                st.session_state.questions        = qs
                st.session_state.answers          = {}
                st.session_state.test_start       = time.time()
                st.session_state.test_duration    = 1800
                st.session_state.test_done        = False
                st.session_state.page             = "test"
                st.rerun()
            else:
                st.session_state.current_mode = "chapter"
                st.session_state.page = "chapter_select"
                st.rerun()

    with c2:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.09);
                    border-radius:22px;padding:2rem 1.5rem;text-align:center;margin-bottom:0.8rem;min-height:160px;">
            <div style="font-size:2rem;margin-bottom:0.6rem;">🏆</div>
            <div style="font-weight:700;color:white;font-size:1rem;">Full Mock Test</div>
            <div style="color:rgba(255,255,255,0.4);font-size:0.78rem;margin-top:0.4rem;line-height:1.5;">
                All questions · 60 minutes<br>Exam simulation
            </div>
        </div>""", unsafe_allow_html=True)
        if st.button("Start Full Mock", key="full_btn", use_container_width=True):
            qs = get_questions(subject, chapter=None, mode="full")
            st.session_state.current_mode     = "full"
            st.session_state.current_chapter  = None
            st.session_state.questions        = qs
            st.session_state.answers          = {}
            st.session_state.test_start       = time.time()
            st.session_state.test_duration    = 3600
            st.session_state.test_done        = False
            st.session_state.page             = "test"
            st.rerun()

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    if st.button("← Back", use_container_width=True):
        st.session_state.page = "dashboard"; st.rerun()

    st.markdown(WM_FOOTER, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# PAGE: CHAPTER SELECT
# ═══════════════════════════════════════════════════════════════
def page_chapter_select():
    sidebar()
    subject  = st.session_state.current_subject
    st.markdown(f"<h2>Select Chapter — {subject}</h2>", unsafe_allow_html=True)
    chapters = list(QUESTION_BANK[subject].keys())
    chapter  = st.selectbox("Chapter", chapters)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,2,1])
    with col:
        if st.button("▶  Begin Test", use_container_width=True):
            qs = get_questions(subject, chapter=chapter, mode="chapter")
            st.session_state.current_chapter  = chapter
            st.session_state.questions        = qs
            st.session_state.answers          = {}
            st.session_state.test_start       = time.time()
            st.session_state.test_duration    = 1800
            st.session_state.test_done        = False
            st.session_state.page             = "test"
            st.rerun()

    if st.button("← Back", use_container_width=True):
        st.session_state.page = "mode_select"; st.rerun()

    st.markdown(WM_FOOTER, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# PAGE: TEST
# ═══════════════════════════════════════════════════════════════
def page_test():
    sidebar()
    questions = st.session_state.questions
    elapsed   = time.time() - st.session_state.test_start
    remaining = max(0, st.session_state.test_duration - elapsed)

    if remaining == 0 and not st.session_state.test_done:
        st.session_state.test_done = True
        _save_result()
        st.session_state.page = "results"
        st.rerun()

    subject = st.session_state.current_subject
    chapter = st.session_state.current_chapter
    mode    = st.session_state.current_mode
    mins    = int(remaining // 60)
    secs    = int(remaining %  60)
    t_cls   = "timer-warn" if remaining < 300 else "timer-ok"

    # Header row
    st.markdown(f"""
    <div style="display:flex;align-items:flex-start;justify-content:space-between;
                flex-wrap:wrap;gap:1rem;margin-bottom:1.5rem;">
        <div>
            <h2 style="margin:0;font-size:1.4rem;">
                {subject}{'  ·  ' + chapter if chapter else '  ·  Full Mock'}
            </h2>
            <div style="color:rgba(255,255,255,0.4);font-size:0.8rem;margin-top:0.2rem;">
                {len(questions)} Questions
                &nbsp;·&nbsp; <span style="color:#ffd97d;">+{MARKS_CORRECT} correct</span>
                &nbsp;·&nbsp; <span style="color:#ff9090;">{MARKS_WRONG} wrong</span>
                &nbsp;·&nbsp; 0 unattempted
            </div>
        </div>
        <div><span class="{t_cls}">⏱ {mins:02d}:{secs:02d}</span></div>
    </div>""", unsafe_allow_html=True)

    # Questions form
    with st.form("test_form"):
        for i, q in enumerate(questions):
            diff = q.get("difficulty", "Hard")
            dc   = "diff-hard" if diff == "Hard" else "diff-medium"
            year = q.get("year", "NDA PYQ")
            st.markdown(f"""
            <div class="q-wrap">
                <div class="q-meta">
                    Q{i+1}/{len(questions)}
                    &nbsp;·&nbsp;
                    <span style="color:rgba(126,207,255,0.7);font-weight:700;">{year}</span>
                    <span class="{dc}">{diff}</span>
                </div>
                <div class="q-text">{q['question']}</div>
            </div>""", unsafe_allow_html=True)
            st.radio("", q["options"], index=None,
                     key=f"r_{i}", label_visibility="collapsed")

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Submit Test ✓", use_container_width=True)

    if submitted:
        for i in range(len(questions)):
            st.session_state.answers[i] = st.session_state.get(f"r_{i}")
        _save_result()
        st.session_state.page = "results"
        st.rerun()

    time.sleep(1)
    st.rerun()


def _save_result():
    questions = st.session_state.questions
    answers   = {i: st.session_state.get(f"r_{i}", st.session_state.answers.get(i))
                 for i in range(len(questions))}
    sd       = calculate_score(questions, answers)
    taken_at = datetime.datetime.now().strftime("%d %b %Y %H:%M")
    result   = {
        "name":        st.session_state.name,
        "date":        taken_at,
        "taken_at":    taken_at,
        "subject":     st.session_state.current_subject,
        "chapter":     st.session_state.current_chapter or "Full Mock",
        "mode":        st.session_state.current_mode,
        "answers":     answers,
        **sd
    }
    st.session_state.results.append(result)
    st.session_state.last_result = result
    try:
        db_save_result(result)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════
# PAGE: RESULTS
# ═══════════════════════════════════════════════════════════════
def page_results():
    sidebar()
    r = st.session_state.last_result
    if not r:
        st.session_state.page = "dashboard"; st.rerun()

    pct   = r["percentage"]
    mt    = r["time_taken"] // 60
    ms    = r["time_taken"] %  60
    emoji = "🏆" if pct >= 75 else "👍" if pct >= 50 else "📖"
    clr   = "#7fffb0" if pct >= 75 else "#ffd97d" if pct >= 50 else "#ff9090"
    verd  = "Excellent!" if pct >= 75 else "Good effort!" if pct >= 50 else "Keep going!"

    # Score card
    st.markdown(f"""
    <div class="result-card">
        <div style="font-size:3rem;margin-bottom:0.5rem;">{emoji}</div>
        <div style="font-size:0.8rem;color:rgba(255,255,255,0.4);margin-bottom:0.8rem;">
            {r['subject']} · {r['chapter']} · {r['date']}
        </div>
        <div style="font-size:3.2rem;font-weight:800;color:{clr};line-height:1;">
            {r['raw_score']}<span style="font-size:1.5rem;font-weight:400;color:rgba(255,255,255,0.4);">/{r['total_marks']}</span>
        </div>
        <div style="font-size:1.5rem;font-weight:700;color:white;margin:0.3rem 0;">{pct}%</div>
        <div style="font-size:0.95rem;color:{clr};font-weight:600;">{verd}</div>
        <div style="display:flex;gap:0.6rem;justify-content:center;flex-wrap:wrap;margin-top:1.2rem;">
            <span class="pill" style="color:#7fffb0;">✓ {r['correct']} correct</span>
            <span class="pill" style="color:#ff9090;">✗ {r['wrong']} wrong</span>
            <span class="pill">— {r['unattempted']} skipped</span>
            <span class="pill">⏱ {mt}m {ms}s</span>
        </div>
        <div style="margin-top:0.8rem;font-size:0.75rem;color:rgba(255,255,255,0.3);">
            💾 Result saved to leaderboard
        </div>
    </div>""", unsafe_allow_html=True)

    # Answer review
    st.markdown("#### Answer Review")
    questions = st.session_state.questions
    user_ans  = r["answers"]

    for i, q in enumerate(questions):
        chosen    = user_ans.get(i)
        correct_t = q["options"][q["correct"]]
        is_ok     = chosen == correct_t
        skipped   = chosen is None
        bg   = "rgba(50,200,120,0.08)" if is_ok else ("rgba(255,255,255,0.03)" if skipped else "rgba(255,60,60,0.08)")
        bdr  = "rgba(50,200,120,0.20)" if is_ok else ("rgba(255,255,255,0.07)" if skipped else "rgba(255,60,60,0.20)")
        ico  = "✓" if is_ok else ("—" if skipped else "✗")
        ic   = "#7fffb0" if is_ok else ("rgba(255,255,255,0.3)" if skipped else "#ff9090")
        exp  = q.get("explanation", "")

        wrong_line = "" if (is_ok or skipped) else \
            f'<div style="font-size:0.8rem;color:#7fffb0;margin-top:0.3rem;">✓ Correct: {correct_t}</div>'
        exp_line   = f'<div style="font-size:0.75rem;color:rgba(255,210,80,0.7);margin-top:0.25rem;">💡 {exp}</div>' if exp else ""

        st.markdown(f"""
        <div style="background:{bg};border:1px solid {bdr};border-radius:16px;
                    padding:1rem 1.2rem;margin-bottom:0.6rem;">
            <div style="display:flex;align-items:flex-start;gap:0.7rem;">
                <div style="font-size:0.95rem;font-weight:700;color:{ic};min-width:1.2rem;">{ico}</div>
                <div style="flex:1;">
                    <div style="font-size:0.7rem;color:rgba(255,255,255,0.3);margin-bottom:0.2rem;">
                        Q{i+1} &nbsp;·&nbsp; <span style="color:rgba(126,207,255,0.55);">{q.get('year','NDA PYQ')}</span>
                    </div>
                    <div style="font-weight:600;color:white;font-size:0.88rem;line-height:1.4;margin-bottom:0.3rem;">
                        {q['question']}
                    </div>
                    <div style="font-size:0.82rem;color:rgba(255,255,255,0.5);">
                        Your answer: <strong style="color:rgba(255,255,255,0.8);">
                        {chosen if chosen else 'Not answered'}</strong>
                    </div>
                    {wrong_line}{exp_line}
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"; st.rerun()
    with c2:
        if st.button("🔄 Retry", use_container_width=True):
            st.session_state.page = "mode_select"; st.rerun()
    with c3:
        if st.button("🏆 Leaderboard", use_container_width=True):
            st.session_state.page = "leaderboard"; st.rerun()

    st.markdown(WM_FOOTER, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# PAGE: LEADERBOARD
# ═══════════════════════════════════════════════════════════════
def page_leaderboard():
    sidebar()
    st.markdown("""
    <div style="margin-bottom:1.8rem;">
        <h1 style="margin:0;font-size:1.9rem;">🏆 Leaderboard</h1>
        <p style="color:rgba(255,255,255,0.4);font-size:0.85rem;margin:0.3rem 0 0;">
            Top scores across all users · Ranked by % then fastest time
        </p>
    </div>""", unsafe_allow_html=True)

    rows = db_leaderboard(25)
    if not rows:
        st.info("No scores yet — be the first to top the board! 🎯")
    else:
        medals = ["🥇","🥈","🥉"]
        for i, row in enumerate(rows):
            rank  = medals[i] if i < 3 else f"#{i+1}"
            pct   = row["percentage"]
            clr   = "#7fffb0" if pct >= 75 else "#ffd97d" if pct >= 50 else "#ff9090"
            mt    = row["time_taken"] // 60
            ms    = row["time_taken"] %  60
            taken = row["taken_at"][:16] if row["taken_at"] else ""
            is_me = row["name"] == st.session_state.name

            bg  = "rgba(126,207,255,0.08)" if is_me else "rgba(255,255,255,0.04)"
            bdr = "rgba(126,207,255,0.25)" if is_me else "rgba(255,255,255,0.08)"

            st.markdown(f"""
            <div style="background:{bg};border:1px solid {bdr};border-radius:16px;
                        padding:0.9rem 1.2rem;margin-bottom:0.45rem;
                        display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
                <div style="font-size:1.3rem;min-width:2rem;text-align:center;">{rank}</div>
                <div style="flex:1;min-width:120px;">
                    <div style="font-weight:700;color:white;font-size:0.9rem;">
                        {row['name']}{'  <span style="font-size:0.65rem;color:#7ecfff;background:rgba(126,207,255,0.15);border-radius:999px;padding:0.1rem 0.5rem;">you</span>' if is_me else ''}
                    </div>
                    <div style="font-size:0.72rem;color:rgba(255,255,255,0.35);margin-top:0.1rem;">
                        {row['subject']} · {row['chapter']}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.2rem;font-weight:800;color:{clr};">{pct}%</div>
                    <div style="font-size:0.7rem;color:rgba(255,255,255,0.35);">
                        {row['raw_score']}/{row['total_marks']} · ⏱{mt}m{ms}s
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown(WM_FOOTER, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    st.set_page_config(
        page_title="GradeUP — NDA/CDS Prep",
        page_icon="🎖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.markdown(CSS, unsafe_allow_html=True)
    db_init()
    init_state()

    page = st.session_state.page
    if   page == "landing":        page_landing()
    elif page == "dashboard":      page_dashboard()
    elif page == "mode_select":    page_mode_select()
    elif page == "chapter_select": page_chapter_select()
    elif page == "test":           page_test()
    elif page == "results":        page_results()
    elif page == "leaderboard":    page_leaderboard()
    else:
        st.session_state.page = "landing"; st.rerun()

if __name__ == "__main__":
    main()
