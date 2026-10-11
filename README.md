# Oli - Advanced Interactive AI Agent 🤖✨

**Oli** is an interactive, autonomous AI Agent built with **Python, Flask, HTML, CSS, and JavaScript**, pre-configured for both local execution and **Vercel Serverless Deployment**.

Unlike basic chatbots, Oli operates using a **multi-step reasoning loop** with visible thought traces, voice input & output, and a suite of autonomous tools (calculator, unit converter, notes scratchpad, task manager, date/time, and live Wikipedia knowledge search).

---

## Table of Contents

1. [Interactive Features](#1-interactive-features)
2. [Agent Architecture & Reasoning Loop](#2-agent-architecture--reasoning-loop)
3. [Autonomous Tool Suite](#3-autonomous-tool-suite)
4. [Project Structure](#4-project-structure)
5. [Local Setup & Execution](#5-local-setup--execution)
6. [How to Push to GitHub](#6-how-to-push-to-github)
7. [How to Deploy to Vercel](#7-how-to-deploy-to-vercel)
8. [Configuration & Environment Variables](#8-configuration--environment-variables)
9. [Zero-Crash Reliability](#9-zero-crash-reliability)

---

## 1. Interactive Features

- **💭 Multi-Step Thought Process Trace**:
  Oli exposes its internal chain of thought with an interactive accordion showing:
  - 💭 Intent analysis
  - ⚙️ Tool selection & parameter extraction
  - 🛠️ Tool execution status
  - 💡 AI synthesis & response formulation
- **🎙️ Voice Input (Speech-to-Text)**:
  Click the microphone icon in the message bar to speak directly to Oli using the browser's Web Speech API.
- **🔊 Read Aloud (Text-to-Speech)**:
  Click the "🔊 Listen" button on any response to hear Oli speak the answer.
- **📋 One-Click Copy**:
  Quickly copy answers and code snippets directly to your clipboard.
- **🌙 Dark / ☀️ Light Theme Switcher**:
  Seamless glassmorphic dark mode and clean light mode toggle, saved across sessions.
- **⬇️ Chat Transcript Export**:
  Download your conversation as a formatted Markdown (`.md`) file.
- **🏷️ Quick Category Filters**:
  Filter example prompts by *Math*, *Knowledge*, *Converter*, or *Notes & Tasks*.

---

## 2. Agent Architecture & Reasoning Loop

When a user submits a query, Oli follows this autonomous agent loop:

```text
User Message / Voice Input
           ↓
 1. INTENT ANALYSIS 💭
    Understand goal & analyze conversation memory
           ↓
 2. TOOL ROUTING ⚙️
    Match request against available autonomous tools
      ├── Math Calculation? ───> tools.calculate()
      ├── Unit Conversion? ────> tools.convert_units()
      ├── Live Knowledge? ─────> tools.lookup_knowledge()
      ├── Notes & Scratchpad? ─> tools.manage_notes()
      ├── Task Checklist? ─────> tools.manage_todos()
      └── Date & Time Clock? ──> tools.get_current_datetime()
           ↓
 3. TOOL EXECUTION 🛠️
    Execute Python tool safely in sandbox
           ↓
 4. SYNTHESIS & REASONING 💡
    Enrich prompt with tool results + session history
    Generate response via LLM (Gemini / OpenAI) or smart local engine
           ↓
 5. STATE & MEMORY UPDATE 💾
    Record conversation turn into in-memory session history
           ↓
 6. RETURNED INTERACTIVE PAYLOAD
    Deliver response, tool badge, and structured thought trace to frontend
```

---

## 3. Autonomous Tool Suite

| Tool | Trigger Examples | Description |
|---|---|---|
| **🧮 Safe Calculator** | `25 + 50`, `100 / 4`, `15 * 8`, `2^10` | Uses Python AST for safe parsing without `eval()`. |
| **🔄 Unit Converter** | `100 km to miles`, `30 C to F`, `5 kg to lbs` | Converts distance, weight, temperature, and speed. |
| **🌐 Wikipedia Knowledge** | `Who is Alan Turing?`, `What is Quantum Computing?` | Fetches live summaries via Wikipedia REST API (no API key needed). |
| **📝 Notes Scratchpad** | `Save note: Buy groceries`, `Show my notes`, `Delete note 1` | Manages persistent session notes and scratchpad entries. |
| **📋 Task Manager** | `Add task: Deploy to Vercel`, `Show my tasks`, `Complete task 1` | Interactive to-do list tracker. |
| **🕒 Date & Time** | `What is today's date?`, `What time is it?` | Formatted real-time clock and day of week. |

---

## 4. Project Structure

```text
oli-ai-agent/
│
├── app.py              # Flask server and REST API (/api/chat, /api/reset, /api/status)
├── agent.py            # OliAgent: Multi-step reasoning, tool routing, memory, LLM
├── tools.py            # Tool suite (calculator, converter, notes, todos, wiki, datetime)
├── requirements.txt    # Minimal dependencies (Flask, python-dotenv, requests)
├── vercel.json         # Vercel deployment configuration
├── .env                # Private API keys (git-ignored)
├── .env.example        # Environment variables template
├── .gitignore          # Excludes secrets, cache, and virtual environments
├── README.md           # Documentation
│
├── api/
│   └── index.py        # Vercel Serverless Function entrypoint
│
├── templates/
│   └── index.html      # Modern chat interface with voice, thought accordion, themes
│
└── static/
    ├── style.css       # Clean Light/Dark styling, animations, and tool pills
    └── script.js       # Client logic: speech, TTS, export, Markdown, thought rendering
```

---

## 5. Local Setup & Execution

### 1. Activate Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Run the Server
```powershell
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 6. How to Push to GitHub

The repository is already initialized and committed locally. To push it to your GitHub account:

### Step 1: Create a repository on GitHub
1. Go to [github.com/new](https://github.com/new).
2. Name your repository (e.g., `oli-ai-agent`).
3. Leave it public or private, and do **not** initialize with README or .gitignore (we already have them).
4. Click **Create repository**.

### Step 2: Push your local code
In your terminal:
```powershell
# Rename branch to main
git branch -M main

# Add your GitHub repository as origin (replace with your repo URL)
git remote add origin https://github.com/<your-username>/oli-ai-agent.git

# Push code to GitHub
git push -u origin main
```

---

## 7. How to Deploy to Vercel

Oli is pre-configured with `vercel.json` and `api/index.py` for seamless Vercel deployment.

### Option A: Deploy via GitHub (Recommended - 1 Click)
1. Go to [vercel.com](https://vercel.com) and log in.
2. Click **"Add New..."** $\rightarrow$ **"Project"**.
3. Select your GitHub repository (`oli-ai-agent`).
4. Under **Environment Variables**, add:
   - `AI_API_KEY`: Your Gemini or OpenAI key
   - `AI_PROVIDER`: `gemini` (or `openai`)
5. Click **Deploy**.
6. Vercel will build your serverless function and give you a live production URL (`https://oli-ai-agent.vercel.app`)!

### Option B: Deploy via Vercel CLI
1. Log in to Vercel in your terminal:
   ```powershell
   vercel login
   ```
2. Deploy to production:
   ```powershell
   vercel --prod
   ```

---

## 8. Configuration & Environment Variables

Edit [`.env`](file:///e:/AI_Agent/.env):

```env
# AI Provider: "gemini" (recommended free tier) or "openai"
AI_PROVIDER=gemini

# Your LLM API Key (Get a free key at https://aistudio.google.com/)
AI_API_KEY=your_actual_key_here

# Model name
AI_MODEL=gemini-1.5-flash

# Port for local server
PORT=5000
```

---

## 9. Zero-Crash Reliability

Oli is designed with **defensive architecture**:
- If an LLM API quota limit (429) is encountered or no API key is provided, Oli **never crashes**.
- It gracefully falls back to its local tool synthesis engine, allowing calculations, unit conversions, Wikipedia lookups, task management, and session memory to continue working seamlessly!
