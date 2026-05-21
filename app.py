import streamlit as st
import json, time, os, csv, random, threading
from datetime import datetime
import pandas as pd

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Quiz Challenge",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Questions bank ───────────────────────────────────────────────────────────
QUESTION_BANK = [
    {
        "q": "What distinguishes Generative AI from traditional AI?",
        "opts": ["A. It produces novel outputs", "B. It only classifies data",
                 "C. It does not use data", "D. It replaces algorithms"],
        "ans": 0,
        "expl": "Generative AI creates brand-new content — text, images, audio — rather than just classifying or analyzing existing data like traditional AI.",
    },
    {
        "q": "AI in education may reduce learning if:",
        "opts": ["A. Students access more material", "B. Students rely on AI without critical evaluation",
                 "C. Teachers adopt new tools", "D. Learning becomes faster"],
        "ans": 1,
        "expl": "Over-reliance on AI without critically evaluating its output can weaken students' own thinking, problem-solving, and learning skills.",
    },
    {
        "q": "Which is a key limitation of large language models?",
        "opts": ["A. Cannot generate text", "B. Lack true understanding despite fluent output",
                 "C. Do not use data", "D. Require no training"],
        "ans": 1,
        "expl": "LLMs produce fluent text but don't truly understand meaning — they predict word sequences based on patterns in training data.",
    },
    {
        "q": "In AI ethics, 'loss of human agency' refers to:",
        "opts": ["A. Slower systems", "B. Increased computation",
                 "C. Humans no longer making meaningful decisions", "D. Data privacy"],
        "ans": 2,
        "expl": "Loss of human agency means that as AI takes over decisions, people have less control over outcomes that affect their lives.",
    },
    {
        "q": "The transformation caused by Generative AI is most comparable to:",
        "opts": ["A. Industrial machinery replacing labor", "B. Writing systems replacing oral memory",
                 "C. Electricity usage", "D. Transportation systems"],
        "ans": 1,
        "expl": "Like writing systems changed how humans store knowledge, Generative AI is reshaping how we create, communicate, and think.",
    },
    {
        "q": "Which company created ChatGPT?",
        "opts": ["A. Google", "B. Meta", "C. OpenAI", "D. Microsoft"],
        "ans": 2,
        "expl": "ChatGPT was created by OpenAI. It was launched in November 2022 and became a global sensation.",
    },
    {
        "q": "Which deep learning framework was developed by Google?",
        "opts": ["A. TensorFlow", "B. Scikit-learn", "C. PyTorch", "D. Pandas"],
        "ans": 0,
        "expl": "TensorFlow is an open-source deep learning framework developed by Google Brain.",
    },
    {
        "q": "What is Apple's AI assistant 'Siri' primarily used for?",
        "opts": ["A. Playing video games", "B. Voice-based assistance and answering questions",
                 "C. Editing photos automatically", "D. Managing stock investments"],
        "ans": 1,
        "expl": "Siri helps users with tasks like setting reminders, answering questions, and controlling their device using voice commands.",
    },
    {
        "q": "Which everyday application uses Artificial Intelligence?",
        "opts": ["A. A basic calculator app", "B. A digital clock",
                 "C. Netflix recommending movies to you", "D. A USB charging cable"],
        "ans": 2,
        "expl": "Netflix uses AI to analyze your watch history and suggest movies/shows — this is called a recommendation system.",
    },
    {
        "q": "Amazon's 'Alexa' is an example of:",
        "opts": ["A. A social media platform", "B. An AI-powered virtual assistant",
                 "C. An online shopping website", "D. A type of computer processor"],
        "ans": 1,
        "expl": "Alexa is Amazon's AI-powered virtual assistant. It responds to voice commands and can control smart home devices.",
    },
    {
        "q": "What does 'NLP' stand for in Artificial Intelligence?",
        "opts": ["A. Neural Language Processing", "B. Numeric Logic Programming",
                 "C. Networked Learning Protocol", "D. Natural Language Processing"],
        "ans": 3,
        "expl": "NLP stands for Natural Language Processing — enabling machines to understand human language.",
    },
    {
        "q": "Which AI tool generates images from a text description?",
        "opts": ["A. Microsoft Word", "B. Google Maps", "C. WhatsApp", "D. DALL-E"],
        "ans": 3,
        "expl": "DALL-E, created by OpenAI, generates detailed images from a written description — a powerful example of Generative AI.",
    },
    {
        "q": "What is 'Hallucination' in Large Language Models?",
        "opts": ["A. When the model stops responding",
                 "B. When the model generates false or made-up information confidently",
                 "C. When the model uses too much memory", "D. When the model is overtrained"],
        "ans": 1,
        "expl": "Hallucination is when an LLM confidently generates factually incorrect or made-up content.",
    },
    {
        "q": "Which of these is an example of Generative AI?",
        "opts": ["A. A spam email classifier", "B. A chess-playing program",
                 "C. DALL-E creating images from text", "D. A fraud detection system"],
        "ans": 2,
        "expl": "DALL-E generates new images from text prompts — a core example of Generative AI.",
    },
    {
        "q": "Which task can AI NOT currently do on its own?",
        "opts": ["A. Translate text between languages", "B. Recognize faces in photos",
                 "C. Truly feel emotions like a human", "D. Generate realistic human voices"],
        "ans": 2,
        "expl": "AI can simulate emotional responses but cannot truly feel emotions. Translation, face recognition, and voice generation are all real AI capabilities today.",
    },
]

TOTAL_Q          = 15
Q_TIME_LIMIT     = 20
MAX_FIFTY        = 3
LEADERBOARD_FILE = "leaderboard.json"
PARTICIPANTS_FILE = "participants.csv"

# ── Concurrency lock ─────────────────────────────────────────────────────────
# A single module-level lock serialises all writes to leaderboard.json and
# participants.csv. Without this, if two users finish within milliseconds of
# each other, the second write can overwrite the first and a score is lost.
# Acquiring the lock takes microseconds, so users never notice any delay.
_file_lock = threading.Lock()

# ── File helpers ─────────────────────────────────────────────────────────────
def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE) as f:
            return json.load(f)
    except Exception:
        return []

def save_leaderboard(entries):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(entries, f, indent=2)

def add_to_leaderboard(name, score, correct, time_sec):
    # Lock-protected: read → modify → write happens atomically per user.
    with _file_lock:
        entries = load_leaderboard()
        m, s    = divmod(time_sec, 60)
        entries.append({
            "name":     name,
            "score":    score,
            "correct":  correct,
            "time_sec": time_sec,
            "time_str": f"{m}m {s}s" if m else f"{s}s",
            "date":     datetime.now().strftime("%d %b %Y, %I:%M %p"),
        })
        entries.sort(key=lambda x: (-x["score"], x["time_sec"]))
        save_leaderboard(entries)
        rank = next(
            i + 1 for i, e in enumerate(entries)
            if e["name"] == name and e["score"] == score and e["time_sec"] == time_sec
        )
        return rank

def load_participants():
    if not os.path.exists(PARTICIPANTS_FILE):
        return []
    with open(PARTICIPANTS_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows   = list(reader)
    normalised = []
    for row in rows:
        clean = {k.strip(): v.strip() if v else "" for k, v in row.items()}
        ci = {k.lower(): v for k, v in clean.items()}
        normalised.append({
            "Name":          ci.get("name", ""),
            "Registered At": ci.get("registered at", ci.get("registeredat", "—")),
        })
    return normalised

def name_taken(name):
    # Read inside the lock — prevents two users racing the duplicate check
    # in a tight window and both being allowed to register the same name.
    with _file_lock:
        taken = {p["Name"].strip().lower() for p in load_participants()}
        return name.strip().lower() in taken

def register_participant(name):
    # Lock-protected append so two users registering at the same moment
    # don't corrupt the CSV (header line, partial rows, etc.).
    with _file_lock:
        exists = os.path.exists(PARTICIPANTS_FILE)
        with open(PARTICIPANTS_FILE, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["Name", "Registered At"])
            if not exists:
                w.writeheader()
            w.writerow({
                "Name":          name.strip(),
                "Registered At": datetime.now().strftime("%d %b %Y, %I:%M %p"),
            })

# ── Session state init ───────────────────────────────────────────────────────
def init_state():
    defaults = {
        "page":          "home",
        "player_name":   "",
        "questions":     [],
        "current_q":     0,
        "score":         0,
        "correct_count": 0,
        "start_time":    None,
        "q_start_time":  None,
        "fifty_left":    MAX_FIFTY,
        "eliminated":    [],
        "chosen":        None,
        "timed_out":     False,
        "answers":       [],
        "final_rank":    None,
        "saved_to_lb":   False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
S = st.session_state

# ── Helpers ──────────────────────────────────────────────────────────────────
def goto(page):
    S.page = page
    st.rerun()

def fmt_time(sec):
    m, s = divmod(int(sec), 60)
    return f"{m}m {s}s" if m else f"{s}s"

def elapsed_total():
    return int(time.time() - S.start_time) if S.start_time else 0

def elapsed_q():
    return time.time() - S.q_start_time if S.q_start_time else 0

# ── PROFESSIONAL CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

:root {
  --bg-deep:        #07091A;
  --bg-base:        #0B1024;
  --bg-card:        #131A33;
  --bg-elevated:    #1A2342;
  --bg-hover:       #243057;
  --border-subtle:  rgba(255,255,255,.06);
  --border-default: rgba(255,255,255,.10);
  --border-accent:  rgba(251,191,36,.35);
  --text-hi:        #F1F5F9;
  --text-base:      #CBD5E1;
  --text-muted:     #94A3B8;
  --text-dim:       #64748B;
  --gold:           #FBBF24;
  --gold-dark:      #D97706;
  --gold-glow:      rgba(251,191,36,.18);
  --indigo:         #818CF8;
  --emerald:        #10B981;
  --emerald-dark:   #047857;
  --rose:           #F43F5E;
  --rose-dark:      #9F1239;
  --amber:          #F59E0B;
  --shadow-md:      0 4px 12px rgba(0,0,0,.35);
  --shadow-lg:      0 8px 24px rgba(0,0,0,.4);
  --shadow-glow:    0 0 0 1px var(--border-accent), 0 8px 32px var(--gold-glow);
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg-base) !important;
  background-image:
    radial-gradient(at 20% 0%, rgba(99,102,241,.05) 0%, transparent 50%),
    radial-gradient(at 80% 100%, rgba(251,191,36,.04) 0%, transparent 50%) !important;
  color: var(--text-hi);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
[data-testid="stAppViewContainer"] > .main > .block-container {
  padding: 2rem 1.5rem 3rem;
  max-width: 760px;
}
#MainMenu, footer, header { visibility: hidden; }

.kbc-title {
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
  font-size: 2.4rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #FBBF24 0%, #F59E0B 50%, #D97706 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-align: center;
  margin: 0;
  line-height: 1.1;
}
.kbc-sub {
  font-size: 1.05rem;
  color: var(--text-muted);
  font-weight: 400;
  text-align: center;
  margin: 8px 0 24px;
  letter-spacing: 0.01em;
}
.gold-bar {
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, var(--border-accent) 50%, transparent 100%);
  margin: 16px 0;
  border: none;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin: 16px 0 24px;
}
.chip {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: 999px;
  padding: 7px 16px;
  color: var(--text-base);
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.01em;
  transition: all 0.2s;
}
.chip:hover { border-color: var(--border-accent); color: var(--gold); }

.topbar {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-bottom: none;
  border-radius: 12px 12px 0 0;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.num-badge {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--gold) 0%, var(--gold-dark) 100%);
  color: #1A1A1A;
  font-size: 0.85rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px var(--gold-glow);
}
.tb-ctr {
  color: var(--text-base);
  font-size: 0.85rem;
  font-weight: 500;
  margin-left: 12px;
  letter-spacing: 0.01em;
}
.timer-wrap {
  background: var(--bg-card);
  border-left: 1px solid var(--border-default);
  border-right: 1px solid var(--border-default);
  padding: 10px 16px 12px;
}
.timer-label {
  font-size: 0.75rem;
  margin-bottom: 6px;
  font-weight: 500;
  letter-spacing: 0.02em;
  display: flex;
  justify-content: space-between;
}
.timer-bar-bg {
  width: 100%;
  height: 6px;
  background: rgba(255,255,255,0.05);
  border-radius: 999px;
  overflow: hidden;
}
.timer-bar-fg {
  height: 6px;
  border-radius: 999px;
  animation-name: timer-shrink;
  animation-timing-function: linear;
  animation-fill-mode: forwards;
}
@keyframes timer-shrink {
  0%   { width: 100%; background: linear-gradient(90deg, #10B981, #34D399); }
  50%  { width: 50%;  background: linear-gradient(90deg, #10B981, #34D399); }
  51%  { width: 49%;  background: linear-gradient(90deg, #F59E0B, #FBBF24); }
  75%  { width: 25%;  background: linear-gradient(90deg, #F59E0B, #FBBF24); }
  76%  { width: 24%;  background: linear-gradient(90deg, #F43F5E, #FB7185); }
  100% { width: 0%;   background: linear-gradient(90deg, #F43F5E, #FB7185); }
}
.q-card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-top: none;
  padding: 28px 24px;
  text-align: center;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-hi);
  line-height: 1.55;
  min-height: 100px;
  letter-spacing: -0.005em;
}
.hint-txt {
  color: var(--text-dim);
  font-size: 0.8rem;
  text-align: center;
  margin: 10px 0;
  letter-spacing: 0.01em;
}
.ll-hint {
  color: var(--amber);
  font-size: 0.8rem;
  font-weight: 500;
  text-align: center;
  margin: 10px 0;
  letter-spacing: 0.01em;
}
.opt-elim, .ans-opt-correct, .ans-opt-wrong, .ans-opt-neutral {
  width: 100%;
  min-height: 60px;
  height: 60px;
  padding: 0 18px;
  border-radius: 10px;
  font-size: 0.92rem;
  font-weight: 500;
  text-align: left;
  line-height: 1.4;
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 5px 0;
  box-sizing: border-box;
  transition: all 0.2s;
}
div[data-testid="stButton"] > button {
  width: 100% !important;
  min-height: 60px !important;
  height: 60px !important;
  padding: 0 18px !important;
  background: var(--bg-elevated) !important;
  color: var(--text-hi) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: 10px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.92rem !important;
  font-weight: 500 !important;
  text-align: left !important;
  line-height: 1.4 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  box-sizing: border-box !important;
  transition: all 0.2s !important;
  letter-spacing: 0.01em !important;
}
div[data-testid="stButton"] > button:hover {
  background: var(--bg-hover) !important;
  border-color: var(--border-accent) !important;
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}
div[data-testid="stButton"] > button:active { transform: translateY(0); }
div[data-testid="stButton"] { margin: 5px 0; }
div[data-testid="stButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, var(--gold) 0%, var(--gold-dark) 100%) !important;
  color: #1A1A1A !important;
  border: none !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 16px var(--gold-glow) !important;
  text-align: center !important;
  justify-content: center !important;
  letter-spacing: 0.02em !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
  background: linear-gradient(135deg, #FCD34D 0%, #F59E0B 100%) !important;
  box-shadow: 0 6px 20px var(--gold-glow) !important;
  transform: translateY(-1px);
}
.opt-elim {
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--border-subtle);
  color: var(--text-dim);
  text-decoration: line-through;
  opacity: 0.45;
}
.ans-opt-correct {
  background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(16,185,129,0.06));
  border: 1px solid var(--emerald);
  color: #6EE7B7;
  font-weight: 600;
  box-shadow: 0 0 0 1px rgba(16,185,129,0.2);
}
.ans-opt-wrong {
  background: linear-gradient(135deg, rgba(244,63,94,0.12), rgba(244,63,94,0.06));
  border: 1px solid var(--rose);
  color: #FCA5A5;
  font-weight: 500;
}
.ans-opt-neutral {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
}
.check-circle {
  background: var(--emerald);
  color: #fff;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 800;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(16,185,129,0.3);
}
.dots {
  display: flex;
  gap: 6px;
  justify-content: center;
  padding: 16px 0 12px;
  flex-wrap: wrap;
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255,255,255,0.08);
  flex-shrink: 0;
  transition: all 0.3s;
}
.dot.done { background: var(--gold); box-shadow: 0 0 8px var(--gold-glow); }
.dot.curr { background: var(--amber); transform: scale(1.4); box-shadow: 0 0 12px var(--gold-glow); }
.expl {
  background: var(--bg-card);
  border-left: 3px solid var(--gold);
  border-radius: 8px;
  padding: 14px 18px;
  color: var(--text-base);
  font-size: 0.88rem;
  line-height: 1.6;
  margin: 12px 0;
}
.expl strong { color: var(--gold); font-weight: 600; }
.dstat {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 18px 12px;
  text-align: center;
  transition: all 0.2s;
}
.dstat:hover { border-color: var(--border-accent); transform: translateY(-2px); box-shadow: var(--shadow-md); }
.dstat-val {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--gold);
  letter-spacing: -0.02em;
  line-height: 1.1;
}
.dstat-lbl {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: 6px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 500;
}
.section-heading {
  background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-elevated) 100%);
  border: 1px solid var(--border-default);
  border-radius: 12px 12px 0 0;
  padding: 16px 20px;
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--gold);
  letter-spacing: -0.01em;
  display: flex;
  align-items: center;
  gap: 8px;
}
[data-testid="stTextInput"] input {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-default) !important;
  color: var(--text-hi) !important;
  border-radius: 10px !important;
  padding: 14px 18px !important;
  font-size: 0.95rem !important;
  font-family: 'Inter', sans-serif !important;
  transition: all 0.2s !important;
}
[data-testid="stTextInput"] input:focus {
  border-color: var(--gold) !important;
  box-shadow: 0 0 0 3px var(--gold-glow) !important;
}
[data-testid="stTextInput"] input::placeholder { color: var(--text-dim) !important; }
[data-testid="stProgress"] > div > div > div > div {
  background: linear-gradient(90deg, var(--gold) 0%, var(--gold-dark) 100%) !important;
}
[data-testid="stProgress"] > div > div > div { background: rgba(255,255,255,0.05) !important; }
[data-testid="stAlert"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: 10px !important;
}
[data-testid="stExpander"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: 10px !important;
}
[data-testid="stExpander"] summary {
  color: var(--text-base) !important;
  font-weight: 500 !important;
}
[data-testid="stDataFrame"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: 10px !important;
  overflow: hidden;
}
.footer-note {
  color: var(--text-dim);
  font-size: 0.78rem;
  text-align: center;
  margin-top: 12px;
  line-height: 1.8;
  letter-spacing: 0.01em;
}
[data-testid="stDownloadButton"] > button {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-default) !important;
  color: var(--text-base) !important;
  border-radius: 10px !important;
}
[data-testid="stDownloadButton"] > button:hover {
  border-color: var(--gold) !important;
  color: var(--gold) !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  HOME
# ─────────────────────────────────────────────────────────────────────────────
if S.page == "home":
    st.markdown('<p class="kbc-title">AI Quiz Challenge</p>', unsafe_allow_html=True)
    st.markdown('<p class="kbc-sub">Test your knowledge</p>',
                unsafe_allow_html=True)
    st.markdown('<div class="gold-bar"></div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="chips">
        <span class="chip">📋 15 Questions</span>
        <span class="chip">⏱ {Q_TIME_LIMIT}s per question</span>
        <span class="chip">Three 50:50 Lifeline</span>
    </div>""", unsafe_allow_html=True)

    name = st.text_input("", placeholder="Enter your full name",
                         max_chars=40, label_visibility="collapsed", key="name_input")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start Quiz", use_container_width=True, type="primary"):
            n = name.strip()
            if not n:
                st.error("Please enter your name first!")
            elif name_taken(n):
                st.error(
                    f"**{n}** has already participated. "
                    "Each person can only attempt once."
                )
            else:
                register_participant(n)
                shuffled        = QUESTION_BANK.copy()
                random.shuffle(shuffled)
                S.player_name   = n
                S.questions     = shuffled
                S.current_q     = 0
                S.score         = 0
                S.correct_count = 0
                S.start_time    = time.time()
                S.q_start_time  = time.time()
                S.fifty_left    = MAX_FIFTY
                S.eliminated    = []
                S.chosen        = None
                S.timed_out     = False
                S.answers       = []
                S.final_rank    = None
                S.saved_to_lb   = False
                goto("quiz")

    st.markdown('<div class="gold-bar"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="footer-note">
        +5 points for each correct answer · 0 for wrong<br>
        Tied scores? Fastest completion time wins the higher rank
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  QUIZ
# ─────────────────────────────────────────────────────────────────────────────
elif S.page == "quiz":
    q_idx       = S.current_q
    q           = S.questions[q_idx]
    elim        = S.eliminated
    elapsed_q_s = elapsed_q()
    remaining   = max(0.0, Q_TIME_LIMIT - elapsed_q_s)

    if remaining <= 0 and not S.timed_out:
        S.timed_out = True
        S.chosen    = None
        goto("answer")

    st.markdown(f"""
    <div class="topbar">
      <div style="display:flex;align-items:center">
        <div class="num-badge">{q_idx+1}</div>
        <span class="tb-ctr">Question {q_idx+1} of {TOTAL_Q}</span>
      </div>
      <span style="color:var(--text-muted);font-size:.78rem;font-weight:500;
                   text-transform:uppercase;letter-spacing:.08em">
        {S.fifty_left}/{MAX_FIFTY} Lifelines
      </span>
    </div>""", unsafe_allow_html=True)

    rem_int   = max(0, int(remaining))
    label_col = "var(--rose)" if remaining <= 5 else "var(--text-muted)"
    st.markdown(f"""
    <div class="timer-wrap">
      <div class="timer-label" style="color:{label_col}">
        <span>Time Remaining</span>
        <span>{rem_int}s</span>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f'<div class="q-card">{q["q"]}</div>', unsafe_allow_html=True)

    if S.fifty_left > 0 and not elim:
        if st.button("Use 50:50 Lifeline · Remove two wrong options",
                     use_container_width=True):
            wrong         = [i for i in range(4) if i != q["ans"]]
            S.eliminated  = wrong[1:]
            S.fifty_left -= 1
            st.rerun()
    elif elim:
        st.markdown('<p class="ll-hint">50:50 used — two options eliminated</p>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<p class="hint-txt">All lifelines used</p>',
                    unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    def render_opt(col, i):
        opt_text = q["opts"][i]
        if i in elim:
            col.markdown(f'<div class="opt-elim">{opt_text}</div>',
                         unsafe_allow_html=True)
        else:
            with col:
                if st.button(opt_text, key=f"opt_{q_idx}_{i}",
                             use_container_width=True):
                    S.chosen    = i
                    S.timed_out = False
                    goto("answer")
    render_opt(col_a, 0); render_opt(col_b, 1)
    render_opt(col_a, 2); render_opt(col_b, 3)

    dots_html = '<div class="dots">'
    for i in range(TOTAL_Q):
        cls = "dot done" if i < q_idx else ("dot curr" if i == q_idx else "dot")
        dots_html += f'<div class="{cls}"></div>'
    dots_html += "</div>"
    st.markdown(dots_html, unsafe_allow_html=True)

    # Increased from 1.0s → 1.5s to reduce server load with concurrent users.
    # With 20 users this drops reruns/sec from ~20 → ~13, easing CPU and memory.
    # No visible difference to users since the timer label only ticks in seconds.
    time.sleep(1.5)
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  ANSWER
# ─────────────────────────────────────────────────────────────────────────────
elif S.page == "answer":
    q_idx      = S.current_q
    q          = S.questions[q_idx]
    chosen     = S.chosen
    timed_out  = S.timed_out
    is_correct = (chosen == q["ans"]) and not timed_out

    if len(S.answers) <= q_idx:
        pts = 5 if is_correct else 0
        if is_correct:
            S.score         += pts
            S.correct_count += 1
        S.answers.append({
            "q_idx": q_idx, "chosen": chosen, "correct": is_correct,
            "pts": pts, "timed_out": timed_out,
        })
    else:
        pts = S.answers[q_idx]["pts"]

    S.eliminated = []
    S.timed_out  = False

    if timed_out:
        accent_color, accent_label, accent_icon = "var(--indigo)", "Time's Up", "⏰"
        accent_grad = "linear-gradient(135deg, #8B5CF6, #6D28D9)"
    elif is_correct:
        accent_color, accent_label, accent_icon = "var(--emerald)", "Correct Answer", "✓"
        accent_grad = "linear-gradient(135deg, #10B981, #047857)"
    else:
        accent_color, accent_label, accent_icon = "var(--rose)", "Incorrect", "✗"
        accent_grad = "linear-gradient(135deg, #F43F5E, #9F1239)"

    pts_text = f"+{pts} points" if is_correct else "+0 points"

    st.markdown(f"""
    <div style="background:var(--bg-card);border:1px solid var(--border-default);
                border-bottom:2px solid {accent_color};border-radius:12px 12px 0 0;
                padding:14px 18px;display:flex;align-items:center;
                justify-content:space-between;gap:12px">
      <span style="color:var(--text-muted);font-size:.8rem;font-weight:500;
                   text-transform:uppercase;letter-spacing:.08em">
        Question {q_idx+1}
      </span>
      <span style="background:{accent_grad};color:#fff;border-radius:999px;
                   padding:6px 16px;font-size:.82rem;font-weight:600;
                   display:inline-flex;align-items:center;gap:6px;
                   letter-spacing:.01em">
        {accent_icon} {accent_label}
      </span>
      <span style="color:{accent_color};font-size:.82rem;font-weight:700;
                   letter-spacing:.01em">{pts_text}</span>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:var(--bg-card);border-left:1px solid var(--border-default);
                border-right:1px solid var(--border-default);padding:18px 20px;
                color:var(--text-base);font-size:1rem;text-align:center;
                line-height:1.55;font-weight:500">
      {q["q"]}
    </div>""", unsafe_allow_html=True)

    st.markdown('<div style="height:14px;background:var(--bg-card);'
                'border:1px solid var(--border-default);border-top:none;'
                'border-radius:0 0 12px 12px;margin-bottom:16px"></div>',
                unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    for i, opt_text in enumerate(q["opts"]):
        col = col_a if i % 2 == 0 else col_b
        if i == q["ans"]:
            col.markdown(
                f'<div class="ans-opt-correct">'
                f'<span class="check-circle">✓</span>{opt_text}</div>',
                unsafe_allow_html=True)
        elif i == chosen and not is_correct:
            col.markdown(
                f'<div class="ans-opt-wrong">'
                f'<span style="color:var(--rose);font-weight:700">✗</span> {opt_text}</div>',
                unsafe_allow_html=True)
        else:
            col.markdown(
                f'<div class="ans-opt-neutral">{opt_text}</div>',
                unsafe_allow_html=True)

    st.markdown(f'<div class="expl"><strong>Explanation</strong><br>{q["expl"]}</div>',
                unsafe_allow_html=True)

    dots_html = '<div class="dots">'
    for i in range(TOTAL_Q):
        cls = "dot done" if i <= q_idx else "dot"
        dots_html += f'<div class="{cls}"></div>'
    dots_html += "</div>"
    st.markdown(dots_html, unsafe_allow_html=True)

    is_last   = q_idx == TOTAL_Q - 1
    btn_label = "Finish Quiz & See Results" if is_last else "Next Question"
    if st.button(btn_label, use_container_width=True, type="primary"):
        S.current_q    = q_idx + 1
        S.chosen       = None
        S.q_start_time = time.time()
        goto("final" if is_last else "quiz")

# ─────────────────────────────────────────────────────────────────────────────
#  FINAL
# ─────────────────────────────────────────────────────────────────────────────
elif S.page == "final":
    total_sec = elapsed_total()

    if not S.saved_to_lb:
        S.final_rank  = add_to_leaderboard(S.player_name, S.score, S.correct_count, total_sec)
        S.saved_to_lb = True

    st.markdown(f"""
    <div style="text-align:center;padding:20px 0">
      <div style="font-size:3rem;line-height:1;margin-bottom:8px">🎉</div>
      <p class="kbc-title" style="font-size:2rem">Quiz Complete</p>
      <p style="color:var(--text-muted);margin:8px 0 0;font-size:1rem">
        Well done, <span style="color:var(--gold);font-weight:600">{S.player_name}</span>!
      </p>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="gold-bar"></div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, S.score,                  "Score"),
        (c2, f"{S.correct_count}/15",  "Correct"),
        (c3, fmt_time(total_sec),      "Time Taken"),
        (c4, f"#{S.final_rank}",       "Your Rank"),
    ]:
        col.markdown(f"""
        <div class="dstat">
          <div class="dstat-val">{val}</div>
          <div class="dstat-lbl">{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="gold-bar" style="margin:24px 0"></div>',
                unsafe_allow_html=True)

    with st.expander("View Your Answer Breakdown"):
        for rec in S.answers:
            qi           = rec["q_idx"]
            is_to        = rec.get("timed_out", False)
            icon         = "✓" if rec["correct"] else ("⏰" if is_to else "✗")
            pts_txt      = f"+{rec['pts']} pts" if rec["correct"] else "0 pts"
            border_color = "var(--emerald)" if rec["correct"] else ("var(--indigo)" if is_to else "var(--rose)")
            icon_color   = border_color
            st.markdown(f"""
            <div style="background:var(--bg-elevated);border-radius:10px;
                        padding:12px 16px;margin:8px 0;
                        border-left:3px solid {border_color};
                        display:flex;align-items:center;gap:12px">
              <span style="color:var(--gold);font-weight:700;font-size:.85rem;
                           min-width:36px">Q{qi+1}</span>
              <span style="color:var(--text-base);flex:1;font-size:.88rem">
                {S.questions[qi]["q"][:65]}…
              </span>
              <span style="color:{icon_color};font-weight:700;font-size:1rem">{icon}</span>
              <span style="color:var(--text-muted);font-size:.82rem;font-weight:500;
                           min-width:60px;text-align:right">{pts_txt}</span>
            </div>""", unsafe_allow_html=True)

    if st.button("View Full Leaderboard", use_container_width=True, type="primary"):
        goto("dashboard")

# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
elif S.page == "dashboard":
    st.markdown('<div class="section-heading">🏆 Leaderboard</div>',
                unsafe_allow_html=True)

    entries = load_leaderboard()
    if not entries:
        st.markdown("""
        <div style="background:var(--bg-card);border:1px solid var(--border-default);
                    border-top:none;border-radius:0 0 12px 12px;padding:40px 20px;
                    text-align:center;color:var(--text-muted);font-size:.95rem">
          No players have completed the quiz yet.<br>
          <span style="color:var(--gold);font-weight:500">Be the first!</span>
        </div>""", unsafe_allow_html=True)
    else:
        avg_score = round(sum(e["score"] for e in entries) / len(entries), 1)
        fastest   = min(entries, key=lambda x: x["time_sec"])
        top       = entries[0]

        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        for col, val, lbl in [
            (c1, len(entries),        "Players"),
            (c2, avg_score,           "Avg Score"),
            (c3, fastest["time_str"], "Fastest"),
            (c4, top["name"][:12],    "Top Player"),
        ]:
            col.markdown(f"""
            <div class="dstat">
              <div class="dstat-val" style="font-size:1.3rem">{val}</div>
              <div class="dstat-lbl">{lbl}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="gold-bar" style="margin:20px 0"></div>',
                    unsafe_allow_html=True)

        medals  = ["🥇", "🥈", "🥉"]
        df_rows = []
        for i, e in enumerate(entries):
            medal = medals[i] if i < 3 else ""
            df_rows.append({
                "Rank":    f"{medal} #{i+1}",
                "Name":    e["name"],
                "Score":   e["score"],
                "Correct": f"{e['correct']}/15",
                "Time":    e["time_str"],
            })
        df_lb = pd.DataFrame(df_rows)
        st.dataframe(
            df_lb,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank":    st.column_config.TextColumn("Rank",    width="small"),
                "Name":    st.column_config.TextColumn("Name",    width="medium"),
                "Score":   st.column_config.NumberColumn("Score", format="%d"),
                "Correct": st.column_config.TextColumn("Correct", width="small"),
                "Time":    st.column_config.TextColumn("Time",    width="small"),
            },
        )

        df_export = pd.DataFrame(entries).rename(columns={
            "name": "Name", "score": "Score", "correct": "Correct",
            "time_str": "Time", "time_sec": "Time (sec)",
        })[["Name", "Score", "Correct", "Time", "Time (sec)"]]
        df_export.index = range(1, len(df_export) + 1)
        df_export.index.name = "Rank"
        st.download_button(
            "Export Leaderboard as CSV",
            df_export.to_csv().encode("utf-8"),
            "ai_quiz_leaderboard.csv", "text/csv",
            use_container_width=True,
        )

    # Live auto-refresh indicator (replaces the manual button)
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:center;gap:8px;
                margin-top:20px;padding:10px;color:var(--text-muted);
                font-size:0.82rem;letter-spacing:0.02em">
      <span style="width:8px;height:8px;border-radius:50%;background:var(--emerald);
                   box-shadow:0 0 8px rgba(16,185,129,.5);
                   animation:pulse 1.5s ease-in-out infinite"></span>
      <span>Live · Auto-refreshes every 10 seconds</span>
    </div>
    <style>
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50%      { opacity: 0.3; }
      }
    </style>
    """, unsafe_allow_html=True)

    # Auto-refresh every 10 seconds — keeps leaderboard live without a button click
    time.sleep(10)
    st.rerun()