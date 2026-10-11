# Oli - Simple AI Agent 🤖

**Oli** is a beginner-friendly, lightweight AI Agent built with **Python, Flask, HTML, CSS, and JavaScript**.

It is designed to demonstrate how real AI agents are constructed from scratch—without relying on heavy, opaque frameworks or unnecessary complexity.

---

## Table of Contents

1. [What is Oli?](#1-what-is-oli)
2. [Features](#2-features)
3. [Project Architecture](#3-project-architecture)
4. [Folder Structure](#4-folder-structure)
5. [How the AI Agent Works (Agent Loop)](#5-how-the-ai-agent-works-agent-loop)
6. [How to Install Python Dependencies](#6-how-to-install-python-dependencies)
7. [How to Configure the API Key](#7-how-to-configure-the-api-key)
8. [How to Run the Flask Server](#8-how-to-run-the-flask-server)
9. [How to Open the Website](#9-how-to-open-the-website)
10. [How the Calculator Tool Works (Safe AST)](#10-how-the-calculator-tool-works)
11. [How the Date/Time Tool Works](#11-how-the-datetime-tool-works)
12. [How Conversation Memory Works](#12-how-conversation-memory-works)
13. [Cost-Conscious Deployment (Free vs Paid)](#13-cost-conscious-deployment)
14. [Future Improvements](#14-future-improvements)

---

## 1. What is Oli?

**Oli** is a simple personal AI assistant that can:
- **Understand** user requests in natural language.
- **Decide** whether a tool (like a calculator or calendar/clock) is needed to give an accurate answer.
- **Execute tools safely** in Python.
- **Remember** previous parts of the conversation (such as your name).
- **Generate responses** using an LLM (Google Gemini or OpenAI) or smart local reasoning.

---

## 2. Features

- **Clean Chat Interface**: White/light, modern aesthetic with rounded bubbles, avatar "O", responsive layout, and quick suggestion chips.
- **Agent Decision Loop**: Analyzes user intent, invokes tools when required, and crafts contextual responses.
- **Safe Calculator**: Solves math expressions (e.g. `25 + 50`, `100 / 4`, `15 * 8`, `2^10`) safely using Python's Abstract Syntax Tree (`ast`), rejecting arbitrary code execution.
- **Date & Time Tool**: Answers real-time questions like *"What is today's date?"* and *"What time is it?"*.
- **Session Memory**: Remembers context across the conversation (e.g., *"My name is Alex."* -> *"What is my name?"* -> *"Your name is Alex!"*).
- **Secure Key Management**: API keys are loaded strictly from `.env` and never exposed to the frontend.
- **Zero-Crash Offline Mode**: Works out of the box even before adding an API key, so you can test calculations and date/time immediately!

---

## 3. Project Architecture

```
User Browser (HTML / CSS / JS)
       │
       ▼  (POST /api/chat)
Flask Web Server (app.py)
       │
       ▼
Oli Agent Controller (agent.py)
       ├── 1. Memory Check (ConversationMemory)
       ├── 2. Tool Decision (decide_tool)
       │         │
       │         ├──> tools.py (Safe Calculator & Date/Time)
       │
       └── 3. Response Generation (LLM REST API or local fallback)
                 │
                 └──> Returns JSON response to Frontend
```

---

## 4. Folder Structure

```text
e:\AI_Agent/
│
├── app.py              # Flask server and API endpoints (/api/chat, /api/reset, /api/status)
├── agent.py            # Oli's core loop, memory manager, and LLM connection
├── tools.py            # Tool implementations (Safe AST calculator, Date/Time)
├── requirements.txt    # Minimal Python dependencies (Flask, python-dotenv, requests)
├── .env                # Secret environment variables (ignored by git)
├── .env.example        # Environment variables template
├── .gitignore          # Prevents pushing .env and virtual environments to git
│
├── templates/
│   └── index.html      # Modern chat interface with Oli branding
│
└── static/
    ├── style.css       # Clean light styling, rounded bubbles, and animations
    └── script.js       # Client logic: API fetch, session management, Markdown rendering
```

### Purpose of Each File:
- **`app.py`**: Handles incoming HTTP requests, serves the HTML page, validates messages, and connects requests to the agent.
- **`agent.py`**: The "brain" of Oli. Analyzes queries, executes tools, calls the AI API, and maintains conversation history.
- **`tools.py`**: Standalone tool functions that Oli can call (calculator, date/time).
- **`templates/index.html`**: The web structure showing the Oli avatar, chat history, and input box.
- **`static/style.css`**: Styling that gives Oli a clean, friendly look.
- **`static/script.js`**: Communicates with the Flask backend via `fetch('/api/chat')`.

---

## 5. How the AI Agent Works (Agent Loop)

When you send a message, Oli follows this step-by-step agent loop:

```text
       User types a message (e.g. "What is 25 + 50?")
                             ↓
                    1. Receive Request
          Flask receives POST /api/chat with JSON
                             ↓
                   2. Understand Task
        Oli analyzes the text to determine intent
                             ↓
            3. Decide if a Tool is Required
      Does the question need a calculation or date/time?
            ├── YES ──> 4. Execute Tool (e.g. calculate 25 + 50 = 75)
            └── NO  ──> Proceed directly
                             ↓
                   5. Generate Response
    Combine conversation history + tool result + prompt
    and generate natural response via LLM (or smart fallback)
                             ↓
                   6. Update Memory
         Save user message and Oli's response to session
                             ↓
                   7. Return Response
              Frontend displays message to user
```

---

## 6. How to Install Python Dependencies

### Step 1: Create a virtual environment

In your terminal or PowerShell:

```bash
python -m venv venv
```

### Step 2: Activate the virtual environment

**On Windows (PowerShell):**
```powershell
venv\Scripts\activate
```

*(If you encounter execution policy restrictions, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

**On macOS / Linux:**
```bash
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

---

## 7. How to Configure the API Key

1. Copy `.env.example` to `.env` (or edit the created `.env` file):
   ```bash
   cp .env.example .env
   ```

2. Open `.env` in any text editor:
   ```env
   # Choose provider: "gemini" (recommended) or "openai"
   AI_PROVIDER=gemini

   # Replace with your actual key:
   AI_API_KEY=your_api_key_here
   ```

### Where to get a free API Key:
- **Google Gemini (Recommended - Free Tier)**:
  1. Visit [Google AI Studio](https://aistudio.google.com/)
  2. Sign in with your Google account.
  3. Click **"Get API key"** and create a free key.
  4. Paste the key into `AI_API_KEY` in `.env`.
- **OpenAI**:
  If you prefer OpenAI, set `AI_PROVIDER=openai` and add your OpenAI key from [platform.openai.com](https://platform.openai.com/).

> **Security Note:** `.env` is listed in `.gitignore`. Never commit or share your `.env` file!

---

## 8. How to Run the Flask Server

With your virtual environment activated:

```bash
python app.py
```

You should see output similar to:
```text
Starting Oli AI Agent on http://127.0.0.1:5000
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000
```

---

## 9. How to Open the Website

Open your favorite web browser (Chrome, Edge, Firefox, Safari) and navigate to:

👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

You will see Oli's interface ready to chat!

---

## 10. How the Calculator Tool Works

Mathematical calculations are handled in `tools.py` using Python's built-in **`ast` (Abstract Syntax Tree)** module instead of dangerous `eval()`.

### Why NOT `eval()`?
Using `eval("user_input")` is a severe security vulnerability because a malicious user could pass `__import__('os').system('rm -rf /')` and run destructive code on your computer.

### Safe AST Evaluation:
1. `tools.clean_math_expression()` strips conversational filler words and converts `^` to `**`.
2. `ast.parse(expr, mode='eval')` breaks down the expression into a syntax tree of numbers and mathematical operations.
3. `_safe_eval_node()` walks through the tree:
   - Only permits numbers (`ast.Constant`)
   - Only permits safe operators: `+`, `-`, `*`, `/`, `//`, `%`, `**`
   - Explicitly checks for division by zero (`ZeroDivisionError`)
   - Limits powers to prevent memory overflow
   - Rejects any functions, variables, loops, or imports!

Example test calculations supported:
- `25 + 50` ➔ `75`
- `100 / 4` ➔ `25`
- `15 * 8` ➔ `120`
- `2^10` ➔ `1024`

---

## 11. How the Date/Time Tool Works

The date/time tool in `tools.py` uses Python's standard `datetime` library:

```python
from datetime import datetime

def get_current_datetime():
    now = datetime.now()
    return {
        "formatted": now.strftime("%A, %B %d, %Y at %I:%M %p"),
        "date": now.strftime("%A, %B %d, %Y"),
        "time": now.strftime("%I:%M %p").lstrip("0")
    }
```

When Oli detects phrases like:
- *"What time is it?"*
- *"What is today's date?"*
- *"What day is it?"*

It invokes `get_current_datetime()` and formats a friendly reply with the real-time clock.

---

## 12. How Conversation Memory Works

Oli maintains conversation memory per session using the `ConversationMemory` class in `agent.py`:

1. Each browser session is assigned a unique `session_id` stored in the frontend (`localStorage`).
2. When a message is sent, `session_id` is passed to `/api/chat`.
3. The backend stores messages in memory:
   ```python
   self._sessions[session_id] = [
       {"role": "user", "content": "My name is Alex."},
       {"role": "assistant", "content": "Nice to meet you, Alex!"}
   ]
   ```
4. When you ask *"What is my name?"*, Oli inspects previous conversation history to find that your name is Alex!
5. Clicking **"New Chat"** calls `/api/reset`, which clears the memory dictionary for that session.

---

## 13. Cost-Conscious Deployment

Oli was intentionally built to keep hosting and running costs at **₹0 / $0**.

| Category | Cost | Details |
|---|---|---|
| **One-Time Development** | **₹0** | Built entirely with open-source Python, standard libraries, and vanilla web tech. |
| **AI API (Recurring)** | **₹0** | **Google Gemini Free Tier** provides generous free requests per minute for developers. |
| **Hosting (Recurring)** | **₹0** | Can be deployed for free on platforms like **Render**, **Railway**, or **PythonAnywhere**. |

### Free Cloud Deployment Options:
- **Render.com (Free Tier Web Service)**:
  1. Push code to a private GitHub repository.
  2. Create a "Web Service" on Render.
  3. Build Command: `pip install -r requirements.txt`
  4. Start Command: `gunicorn app:app` (or `python app.py`)
  5. Add `AI_API_KEY` to Render Environment Variables.
- **PythonAnywhere (Free Tier)**:
  Upload files and configure WSGI to point to `app.py`.

---

## 14. Future Improvements

Once you are comfortable with this foundation, you can easily expand Oli:
- [ ] **Web Search Tool**: Allow Oli to fetch live Wikipedia summaries or search the web.
- [ ] **Voice Input / Output**: Add speech-to-text with the Web Speech API.
- [ ] **Persistent Database**: Store conversations in SQLite for multi-day memory.
- [ ] **Custom Personas**: Add a selector to change Oli's tone (e.g. Teacher, Code Mentor, Friendly Buddy).
