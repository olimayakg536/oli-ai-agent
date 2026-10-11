"""
agent.py
========
Core AI Agent implementation for Oli (Advanced Interactive Agent).

Features:
1. Multi-Step Reasoning Engine (Generates visible thought traces & step metrics).
2. Advanced Tool Suite Routing:
   - Safe Calculator (AST)
   - Date & Time / Clock
   - Unit & Temperature Converter
   - Notes & Scratchpad Manager
   - To-Do & Task Manager
   - Live Knowledge & Wikipedia Search
3. Session Conversation Memory (Per-session context & history).
4. Dual LLM Support (Google Gemini & OpenAI / OpenAI-compatible).
5. Zero-Crash Fallback Mode (Works locally even without API keys).
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import requests
from dotenv import load_dotenv

import tools

# Load environment variables
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OliAgent")

# Oli's System Prompt
SYSTEM_PROMPT = """You are Oli, an advanced, helpful, and interactive AI assistant.
Your goal is to provide clear, accurate, and insightful answers.
Guidelines:
1. Be polite, warm, and encourage curiosity.
2. If tool information was provided (such as calculations, unit conversions, notes, or knowledge summaries), use it directly to answer accurately.
3. If you don't know something or information is missing, clearly state so without inventing facts.
4. Keep answers readable with markdown formatting (bullet points, bold text, code blocks when suitable).
5. Remember user details mentioned in the current conversation (such as their name or preferences)."""


class ConversationMemory:
    """Manages in-memory conversation history for each session."""

    def __init__(self, max_history_per_session: int = 30):
        self._sessions: Dict[str, List[Dict[str, str]]] = {}
        self.max_history = max_history_per_session

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        return self._sessions.get(session_id, []).copy()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({"role": role, "content": content})
        if len(self._sessions[session_id]) > self.max_history:
            self._sessions[session_id] = self._sessions[session_id][-self.max_history:]

    def clear(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id] = []

    def get_user_name_from_history(self, session_id: str) -> Optional[str]:
        history = self.get_history(session_id)
        name_pattern = re.compile(r"(?:my name is|i am|i'm|call me)\s+([A-Za-z]+)", re.IGNORECASE)
        for msg in reversed(history):
            if msg["role"] == "user":
                match = name_pattern.search(msg["content"])
                if match:
                    return match.group(1).capitalize()
        return None


class OliAgent:
    """
    Advanced AI Agent for Oli.
    Implements a multi-step agent reasoning loop:
    1. Receive input
    2. Analyze intent & break down task
    3. Determine tool requirements
    4. Execute tool(s) safely
    5. Generate response with thought trace
    6. Update session memory
    """

    def __init__(self):
        self.memory = ConversationMemory()
        self.reload_config()

    def reload_config(self) -> None:
        self.api_key = os.getenv("AI_API_KEY", "").strip()
        if not self.api_key or self.api_key == "your_api_key_here":
            self.api_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("OPENAI_API_KEY", "").strip()

        self.provider = os.getenv("AI_PROVIDER", "gemini").lower().strip()
        self.model = os.getenv("AI_MODEL", "").strip()
        self.api_base_url = os.getenv("AI_API_BASE_URL", "").strip()

        if not self.model:
            self.model = "gemini-1.5-flash" if self.provider == "gemini" else "gpt-4o-mini"

        self.has_valid_key = bool(self.api_key and self.api_key != "your_api_key_here")

    def _extract_math_expression(self, text: str) -> Optional[str]:
        """Extract a math expression from user text."""
        clean = re.sub(
            r'^(what is|calculate|compute|solve|how much is|can you calculate|tell me)\s+',
            '',
            text,
            flags=re.IGNORECASE
        )
        clean = re.sub(r'\b(please|for me|equals|result)\b', '', clean, flags=re.IGNORECASE)
        clean = clean.strip().rstrip('?.')

        if re.search(r'\d', clean) and (re.search(r'[\+\-\*\/\^%xX]', clean) or 'sqrt' in clean.lower()):
            return clean

        candidates = re.findall(r'\(?[\d\.\+\-\*\/\^\(\)%xX\s]+\)?', text)
        for c in candidates:
            c_str = c.strip()
            if re.search(r'\d', c_str) and re.search(r'[\+\-\*\/\^%xX]', c_str):
                return c_str

        return None

    def decide_tool(self, user_message: str, session_id: str = "default") -> Tuple[Optional[str], Any]:
        """
        Analyze user message to select the optimal tool.
        Returns (tool_name, tool_kwargs) or (None, None).
        """
        msg = user_message.strip()
        msg_lower = msg.lower()

        # 1. Date / Time Intent
        date_time_keywords = [
            "what time", "what is the time", "current time", "time now",
            "what date", "today's date", "todays date", "current date",
            "what day is it", "what day is today", "date today", "clock"
        ]
        if any(k in msg_lower for k in date_time_keywords):
            return "datetime", {}

        # 2. Unit Conversion Intent (e.g. "100 km to miles", "30 c to f", "convert 5 kg in lbs")
        if re.search(r'\b(?:convert\s+)?[-+]?\d*\.?\d+\s*[a-zA-Z/°]+\s+(?:to|in|into)\s+[a-zA-Z/°]+\b', msg_lower):
            return "unit_converter", {"query": msg}

        # 3. Notes Scratchpad Intent
        # "save note: ...", "remember note: ...", "add note: ..."
        note_add_match = re.search(r'\b(?:save|add|create|remember)\s+note\s*[:\-]?\s*(.+)$', msg, re.IGNORECASE)
        if note_add_match:
            return "notes", {"action": "add", "content": note_add_match.group(1).strip(), "session_id": session_id}

        if re.search(r'\b(?:show|list|view|get|read)\s+(?:my\s+)?notes\b', msg_lower):
            return "notes", {"action": "list", "session_id": session_id}

        note_del_match = re.search(r'\b(?:delete|remove)\s+note\s*#?\s*(\d+)\b', msg_lower)
        if note_del_match:
            return "notes", {"action": "delete", "note_id": int(note_del_match.group(1)), "session_id": session_id}

        if re.search(r'\b(?:clear|delete\s+all)\s+notes\b', msg_lower):
            return "notes", {"action": "clear", "session_id": session_id}

        # 4. To-Do / Task Manager Intent
        # "add task: ...", "add todo: ..."
        todo_add_match = re.search(r'\b(?:add|new|create)\s+(?:task|todo)\s*[:\-]?\s*(.+)$', msg, re.IGNORECASE)
        if todo_add_match:
            return "todos", {"action": "add", "task": todo_add_match.group(1).strip(), "session_id": session_id}

        if re.search(r'\b(?:show|list|view)\s+(?:my\s+)?(?:tasks|todos)\b', msg_lower):
            return "todos", {"action": "list", "session_id": session_id}

        todo_done_match = re.search(r'\b(?:complete|finish|done|mark)\s+(?:task|todo)\s*#?\s*(\d+)\b', msg_lower)
        if todo_done_match:
            return "todos", {"action": "complete", "task_id": int(todo_done_match.group(1)), "session_id": session_id}

        todo_del_match = re.search(r'\b(?:delete|remove)\s+(?:task|todo)\s*#?\s*(\d+)\b', msg_lower)
        if todo_del_match:
            return "todos", {"action": "delete", "task_id": int(todo_del_match.group(1)), "session_id": session_id}

        # 5. Math / Calculator Intent
        math_expr = self._extract_math_expression(user_message)
        if math_expr:
            return "calculator", {"expression": math_expr}

        # 6. Knowledge / Wikipedia Search Intent
        # e.g., "who is Alan Turing", "what is quantum computing", "tell me about Python"
        wiki_match = re.search(r'\b(?:who is|who was|tell me about|what is|search wikipedia for)\s+([a-zA-Z0-9\s]{2,40})[\?\.]*$', msg, re.IGNORECASE)
        # Avoid overriding simple self-intros or name questions
        if wiki_match and not any(k in msg_lower for k in ["my name", "your name", "today", "the time"]):
            candidate_topic = wiki_match.group(1).strip()
            # Ensure it's not a math or simple question
            if not re.search(r'[\+\-\*\/\^=]', candidate_topic) and len(candidate_topic.split()) <= 6:
                return "knowledge", {"query": candidate_topic}

        return None, None

    def execute_tool(self, tool_name: str, tool_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute selected tool and return structured payload."""
        if tool_name == "calculator":
            return tools.calculate(tool_kwargs.get("expression", ""))
        elif tool_name == "datetime":
            return tools.get_current_datetime()
        elif tool_name == "unit_converter":
            return tools.convert_units(tool_kwargs.get("query", ""))
        elif tool_name == "notes":
            return tools.manage_notes(
                action=tool_kwargs.get("action", "list"),
                content=tool_kwargs.get("content", ""),
                note_id=tool_kwargs.get("note_id"),
                session_id=tool_kwargs.get("session_id", "default")
            )
        elif tool_name == "todos":
            return tools.manage_todos(
                action=tool_kwargs.get("action", "list"),
                task=tool_kwargs.get("task", ""),
                task_id=tool_kwargs.get("task_id"),
                session_id=tool_kwargs.get("session_id", "default")
            )
        elif tool_name == "knowledge":
            return tools.lookup_knowledge(tool_kwargs.get("query", ""))
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def _call_gemini_api(self, prompt_text: str, history: List[Dict[str, str]]) -> str:
        """Call Google Gemini REST API."""
        model_name = self.model if self.model.startswith("gemini") else "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"

        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        contents.append({"role": "user", "parts": [{"text": prompt_text}]})

        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
        }

        resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=20)
        if resp.status_code != 200:
            err_msg = resp.text
            try:
                err_msg = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                pass
            raise RuntimeError(f"Gemini API Error ({resp.status_code}): {err_msg}")

        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return "Oli did not receive a response from the AI model."
        parts = candidates[0].get("content", {}).get("parts", [])
        return parts[0].get("text", "").strip() if parts else "Empty response."

    def _call_openai_api(self, prompt_text: str, history: List[Dict[str, str]]) -> str:
        """Call OpenAI or OpenAI-compatible API."""
        url = self.api_base_url or "https://api.openai.com/v1/chat/completions"
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt_text})

        payload = {
            "model": self.model or "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 800
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code != 200:
            err_msg = resp.text
            try:
                err_msg = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                pass
            raise RuntimeError(f"AI API Error ({resp.status_code}): {err_msg}")

        data = resp.json()
        choices = data.get("choices", [])
        return choices[0].get("message", {}).get("content", "").strip() if choices else "Empty response."

    def _generate_fallback_response(
        self,
        user_message: str,
        session_id: str,
        tool_name: Optional[str],
        tool_result: Optional[Dict[str, Any]]
    ) -> str:
        """Intelligent offline fallback response generator."""
        msg_lower = user_message.strip().lower()

        # 1. Calculator Tool Response
        if tool_name == "calculator" and tool_result:
            if tool_result.get("success"):
                return f"The calculation result of {tool_result.get('expression')} is **{tool_result.get('formatted_result')}**."
            return f"Calculation error: {tool_result.get('error')}"

        # 2. Date/Time Tool Response
        if tool_name == "datetime" and tool_result:
            if tool_result.get("success"):
                return f"Today is **{tool_result['date']}**, and the current time is **{tool_result['time']}** ({tool_result['formatted']})."
            return "Unable to determine current date/time."

        # 3. Unit Converter Tool Response
        if tool_name == "unit_converter" and tool_result:
            if tool_result.get("success"):
                return f"**Unit Conversion**: {tool_result['formatted_result']}"
            return f"Conversion error: {tool_result.get('error')}"

        # 4. Notes Tool Response
        if tool_name == "notes" and tool_result:
            if tool_result.get("success"):
                action = tool_result.get("action")
                if action == "add":
                    return f"📝 {tool_result['message']}"
                elif action == "list":
                    notes = tool_result.get("notes", [])
                    if not notes:
                        return "📝 You don't have any saved notes yet. You can add one by typing `save note: your note here`!"
                    formatted = "\n".join([f"{i+1}. {n}" for i, n in enumerate(notes)])
                    return f"📝 **Your Notes ({len(notes)}):**\n\n{formatted}"
                elif action in ("delete", "clear"):
                    return f"📝 {tool_result['message']}"
            return f"Notes error: {tool_result.get('error')}"

        # 5. To-Dos Tool Response
        if tool_name == "todos" and tool_result:
            if tool_result.get("success"):
                action = tool_result.get("action")
                if action == "add":
                    return f"✅ {tool_result['message']}"
                elif action == "list":
                    todos = tool_result.get("todos", [])
                    if not todos:
                        return "📋 Your task list is empty! Add one by typing `add task: write report`."
                    lines = [f"{i+1}. {'[x]' if t['done'] else '[ ]'} **{t['task']}** *(added {t['created_at']})*" for i, t in enumerate(todos)]
                    return f"📋 **Your To-Do List:**\n\n" + "\n".join(lines)
                elif action in ("complete", "delete"):
                    return f"✅ {tool_result['message']}"
            return f"Task error: {tool_result.get('error')}"

        # 6. Knowledge / Wikipedia Tool Response
        if tool_name == "knowledge" and tool_result:
            if tool_result.get("success"):
                return f"🌐 **{tool_result['title']}**\n\n{tool_result['summary']}\n\n*Source: [{tool_result['title']}]({tool_result['url']})*"
            return f"Knowledge search: {tool_result.get('error')}"

        # 7. Memory: User Introduction
        name_match = re.search(r"(?:my name is|i am|i'm|call me)\s+([A-Za-z]+)", user_message, re.IGNORECASE)
        if name_match:
            user_name = name_match.group(1).capitalize()
            return f"Nice to meet you, {user_name}! I am Oli, your simple AI assistant. How can I help you today?"

        # 8. Memory: Recall Name
        if any(q in msg_lower for q in ["what is my name", "what's my name", "do you know my name"]):
            saved_name = self.memory.get_user_name_from_history(session_id)
            if saved_name:
                return f"Your name is **{saved_name}**!"
            return "You haven't told me your name yet! What should I call you?"

        # 9. Conversational Greetings
        if any(greet in msg_lower for greet in ["hello", "hi oli", "hey", "good morning", "good evening"]):
            return "Hello! I'm Oli, your interactive AI assistant. How can I help you today?"

        # 10. Help & Capabilities
        if any(q in msg_lower for q in ["who are you", "what is oli", "what can you do", "help"]):
            return (
                "I am **Oli**, an interactive AI Agent! 🤖\n\n"
                "Here are the tools and skills I can use for you:\n"
                "- **🧮 Calculator**: Solve math like `25 + 50`, `100 / 4`, or `2^10`\n"
                "- **🕒 Date & Time**: Check the current time and today's date\n"
                "- **🔄 Unit Converter**: Convert units like `100 km to miles` or `30 C to F`\n"
                "- **📝 Scratchpad Notes**: Type `save note: Buy groceries` or `show notes`\n"
                "- **📋 Task Manager**: Type `add task: Complete homework` or `show tasks`\n"
                "- **🌐 Knowledge Lookup**: Search real-world topics like `who is Alan Turing`\n"
                "- **🧠 Conversation Memory**: Remember details you share during our chat!"
            )

        # Default notice
        return (
            "I'm Oli, your interactive AI assistant!\n\n"
            "I'm currently running in local tool mode. I can perform calculations, "
            "convert units, manage notes and tasks, look up Wikipedia knowledge, and remember your name.\n\n"
            "To enable open-ended generative chat, add your `AI_API_KEY` to the `.env` file!"
        )

    def process_message(self, user_message: str, session_id: str = "default") -> Dict[str, Any]:
        """
        The Full Multi-Step Agent Reasoning Loop:
        Returns response, tool execution details, and structured thought trace.
        """
        self.reload_config()

        thought_steps: List[Dict[str, str]] = []

        if not user_message or not user_message.strip():
            return {
                "response": "Please enter a message so I can help you!",
                "tool_used": None,
                "tool_result": None,
                "thought_steps": []
            }

        cleaned_input = user_message.strip()

        # Step 1: Intent Analysis
        thought_steps.append({
            "step": "Intent Analysis",
            "icon": "💭",
            "detail": f"Analyzed user query: \"{cleaned_input}\""
        })

        # Step 2: Tool Routing
        tool_name, tool_kwargs = self.decide_tool(cleaned_input, session_id=session_id)
        tool_result = None

        if tool_name:
            thought_steps.append({
                "step": "Tool Selection",
                "icon": "⚙️",
                "detail": f"Selected tool '{tool_name}' with parameters {json.dumps(tool_kwargs)}"
            })

            # Step 3: Tool Execution
            tool_result = self.execute_tool(tool_name, tool_kwargs)
            success_status = "successfully" if tool_result.get("success", False) else "with error"
            thought_steps.append({
                "step": "Tool Execution",
                "icon": "🛠️",
                "detail": f"Executed tool '{tool_name}' {success_status}"
            })
        else:
            thought_steps.append({
                "step": "Decision",
                "icon": "🧠",
                "detail": "No external tool required. Processing query using conversation memory and language model."
            })

        # Step 4: Response Generation
        history = self.memory.get_history(session_id)
        response_text = ""

        if self.has_valid_key:
            thought_steps.append({
                "step": "AI Synthesis",
                "icon": "✨",
                "detail": f"Calling {self.provider.capitalize()} LLM model ({self.model})"
            })
            try:
                if tool_name and tool_result:
                    tool_context = f"[Tool '{tool_name}' output: {json.dumps(tool_result)}]"
                    prompt_with_context = (
                        f"{tool_context}\n"
                        f"User request: {cleaned_input}\n"
                        f"Synthesize a friendly, informative answer incorporating the tool result."
                    )
                else:
                    prompt_with_context = cleaned_input

                if self.provider == "gemini":
                    response_text = self._call_gemini_api(prompt_with_context, history)
                else:
                    response_text = self._call_openai_api(prompt_with_context, history)

            except Exception as e:
                logger.error(f"AI API request failed: {e}")
                fallback = self._generate_fallback_response(cleaned_input, session_id, tool_name, tool_result)
                response_text = (
                    f"{fallback}\n\n"
                    f"*(Note: LLM API request failed: {str(e)}. Using local response)*"
                )
        else:
            thought_steps.append({
                "step": "Local Synthesis",
                "icon": "💡",
                "detail": "Formulating direct answer using local tool results and session memory"
            })
            response_text = self._generate_fallback_response(cleaned_input, session_id, tool_name, tool_result)

        # Step 5: Memory Update
        self.memory.add_message(session_id, "user", cleaned_input)
        self.memory.add_message(session_id, "assistant", response_text)

        thought_steps.append({
            "step": "Memory Updated",
            "icon": "💾",
            "detail": f"Turn saved to session memory (session: {session_id[:12]}...)"
        })

        return {
            "response": response_text,
            "tool_used": tool_name,
            "tool_result": tool_result,
            "thought_steps": thought_steps
        }
