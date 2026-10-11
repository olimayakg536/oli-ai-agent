"""
app.py
======
Flask Web Server and API Backend for Oli AI Agent.

Configured for both standalone execution and Vercel Serverless deployment.
"""

import os
import uuid
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from agent import OliAgent

# Load environment variables
load_dotenv()

# Explicitly set template and static folders for Vercel serverless compatibility
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.secret_key = os.getenv("SECRET_KEY", "oli-secret-key-12345")

# Initialize the Oli AI Agent
agent = OliAgent()


@app.route("/")
def index():
    """Render the Oli chatbot web interface."""
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Primary chat endpoint.
    Expects JSON:
    {
        "message": "User query here",
        "session_id": "optional-session-id"
    }
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                "error": "Invalid request. Please provide JSON data with a 'message' field."
            }), 400

        message = data.get("message", "").strip()
        if not message:
            return jsonify({
                "error": "Message cannot be empty."
            }), 400

        session_id = data.get("session_id", "").strip()
        if not session_id:
            session_id = "default_session"

        # Run Oli's multi-step agent reasoning loop
        result = agent.process_message(user_message=message, session_id=session_id)

        return jsonify({
            "response": result["response"],
            "tool_used": result.get("tool_used"),
            "tool_result": result.get("tool_result"),
            "thought_steps": result.get("thought_steps", []),
            "success": True
        }), 200

    except Exception as e:
        app.logger.error(f"Error in /api/chat: {e}", exc_info=True)
        return jsonify({
            "error": "Oli encountered an unexpected internal error. Please try again.",
            "success": False
        }), 500


@app.route("/api/reset", methods=["POST"])
def reset_conversation():
    """Reset conversation memory for a session."""
    try:
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id", "default_session")

        agent.memory.clear(session_id)

        return jsonify({
            "message": "Conversation memory has been reset successfully.",
            "session_id": session_id,
            "success": True
        }), 200
    except Exception as e:
        app.logger.error(f"Error in /api/reset: {e}", exc_info=True)
        return jsonify({
            "error": "Failed to reset conversation memory.",
            "success": False
        }), 500


@app.route("/api/status", methods=["GET"])
def agent_status():
    """Check agent configuration and available tools."""
    return jsonify({
        "agent": "Oli",
        "status": "online",
        "provider": agent.provider,
        "model": agent.model,
        "api_key_configured": agent.has_valid_key,
        "available_tools": [
            {"name": "calculator", "description": "Safe AST mathematical calculation"},
            {"name": "datetime", "description": "Current date, time, and day"},
            {"name": "unit_converter", "description": "Unit converter (length, weight, temperature, speed)"},
            {"name": "notes", "description": "Scratchpad memory & notes manager"},
            {"name": "todos", "description": "To-do & task list manager"},
            {"name": "knowledge", "description": "Live Wikipedia knowledge lookup"}
        ]
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1")
    print(f"Starting Oli AI Agent on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
