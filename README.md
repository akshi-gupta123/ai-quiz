# 🤖 AI Quiz Challenge — KBC Style
### Streamlit App — Setup & Deployment Guide

---

## 📁 Files in This Package

```
ai_quiz_app/
├── app.py                  ← Main Streamlit application
├── requirements.txt        ← Python dependencies
├── .streamlit/
│   └── config.toml         ← Theme & server config
└── README.md               ← This file
```

---

## 🚀 OPTION 1 — Deploy on Streamlit Cloud (FREE, Shareable Link)

> **Best for sharing a public quiz link with all users**

### Step 1 — Push code to GitHub
1. Create a free account at [github.com](https://github.com)
2. Create a **new public repository** (e.g. `ai-quiz-challenge`)
3. Upload all files from this folder:
   - `app.py`
   - `requirements.txt`
   - `.streamlit/config.toml`

### Step 2 — Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repository, branch `main`, and set **Main file path** = `app.py`
5. Click **"Deploy!"**

### Step 3 — Share the link
- You'll get a URL like: `https://your-app-name.streamlit.app`
- Share this link with all participants — they can open it in any browser
- **Leaderboard is shared** — all players' scores appear together

---

## 💻 OPTION 2 — Run Locally (Your Computer)

### Step 1 — Install Python
- Download Python 3.10+ from [python.org](https://python.org)
- Make sure to check **"Add to PATH"** during installation

### Step 2 — Install dependencies
Open Terminal (Mac/Linux) or Command Prompt (Windows) and run:
```bash
pip install streamlit pandas
```

### Step 3 — Run the app
```bash
cd path/to/ai_quiz_app
streamlit run app.py
```

### Step 4 — Share on your local network
- The app opens at `http://localhost:8501`
- If all participants are on the **same WiFi**, they can access it via your IP:
  ```
  http://YOUR_IP_ADDRESS:8501
  ```
- Find your IP: run `ipconfig` (Windows) or `ifconfig` (Mac/Linux)

---

## ☁️ OPTION 3 — Deploy on Render (Free Hosting)

1. Push code to GitHub (same as Option 1, Step 1)
2. Go to [render.com](https://render.com) → Sign up free
3. Click **"New Web Service"** → Connect your GitHub repo
4. Set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Click **Deploy** → get a public URL

---

## 🏆 Leaderboard Notes

- **Scores are saved** in `leaderboard.json` in the same folder as `app.py`
- Rankings are sorted by: **highest score first**, then **fastest time**
- On Streamlit Cloud, the leaderboard resets if the app redeploys — for **permanent storage**, consider using a free database like [Supabase](https://supabase.com) or [PlanetScale](https://planetscale.com)
- You can **export the leaderboard as CSV** from the dashboard page

---

## 🎮 Quiz Features

| Feature | Details |
|---------|---------|
| 15 Questions | 3 Rounds of 5 questions each |
| 50:50 Lifeline | Available fresh for every question — eliminates 2 wrong options |
| Scoring | 10 pts per correct answer + speed bonus (up to +30 pts) |
| Timer | Live timer shown during quiz |
| Leaderboard | Real-time ranking by score, then by time |
| Answer Review | Full breakdown of answers shown at the end |
| CSV Export | Download leaderboard as Excel-compatible CSV |

---

## ❓ Troubleshooting

| Problem | Fix |
|---------|-----|
| `streamlit: command not found` | Run `pip install streamlit` again; restart terminal |
| Page not loading | Try `http://localhost:8501` in browser manually |
| Leaderboard not saving | Make sure app has write permission in the folder |
| Scores reset after redeploy | Use a database (Supabase) for persistent storage |

---

## 📞 Quick Reference Commands

```bash
# Install
pip install streamlit pandas

# Run
streamlit run app.py

# Run on specific port
streamlit run app.py --server.port 8080

# Run accessible on network (share with others on same WiFi)
streamlit run app.py --server.address 0.0.0.0
```

---

*Built with ❤️ using Streamlit · KBC-themed AI Quiz Challenge*
