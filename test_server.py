"""
test_server.py - End-to-end integration tests for Flask app & advanced agent endpoints
"""
import json
from app import app

def run_tests():
    client = app.test_client()

    print("--- 1. Testing GET / (Frontend UI) ---")
    resp = client.get("/")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    html = resp.get_data(as_text=True)
    assert "Oli" in html
    assert "Interactive" in html
    print("PASS: Frontend index.html served successfully with advanced branding.")

    print("\n--- 2. Testing GET /api/status ---")
    resp = client.get("/api/status")
    assert resp.status_code == 200
    status_data = resp.get_json()
    assert status_data["agent"] == "Oli"
    assert status_data["status"] == "online"
    tool_names = [t["name"] for t in status_data["available_tools"]]
    assert "calculator" in tool_names
    assert "datetime" in tool_names
    assert "unit_converter" in tool_names
    assert "notes" in tool_names
    assert "todos" in tool_names
    assert "knowledge" in tool_names
    print(f"PASS: Status endpoint working with {len(tool_names)} tools: {tool_names}")

    print("\n--- 3. Testing POST /api/chat - Empty Message Validation ---")
    resp = client.post("/api/chat", json={"message": "   "})
    assert resp.status_code == 400
    err_data = resp.get_json()
    assert "cannot be empty" in err_data.get("error", "").lower()
    print("PASS: Empty message rejected with HTTP 400.")

    print("\n--- 4. Testing POST /api/chat - Calculations & Thought Steps ---")
    resp = client.post("/api/chat", json={"message": "25 + 50", "session_id": "test_e2e"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["tool_used"] == "calculator"
    assert "75" in data["response"]
    assert "thought_steps" in data
    assert len(data["thought_steps"]) >= 3
    print("PASS: 25 + 50 -> 75 with thought steps:", [s["step"] for s in data["thought_steps"]])

    print("\n--- 5. Testing POST /api/chat - Unit Converter ---")
    resp = client.post("/api/chat", json={"message": "convert 100 km to miles", "session_id": "test_e2e"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["tool_used"] == "unit_converter"
    assert "62.1" in data["response"]
    print("PASS: 100 km to miles ->", data["response"])

    print("\n--- 6. Testing POST /api/chat - Notes Scratchpad ---")
    resp1 = client.post("/api/chat", json={"message": "save note: Remember to push to GitHub", "session_id": "test_notes"})
    assert resp1.status_code == 200
    assert resp1.get_json()["tool_used"] == "notes"

    resp2 = client.post("/api/chat", json={"message": "show my notes", "session_id": "test_notes"})
    assert resp2.status_code == 200
    assert "Remember to push to GitHub" in resp2.get_json()["response"]
    print("PASS: Saved note and retrieved it via chat!")

    print("\n--- 7. Testing POST /api/chat - Task Manager ---")
    resp1 = client.post("/api/chat", json={"message": "add task: Deploy to Vercel", "session_id": "test_tasks"})
    assert resp1.status_code == 200
    assert resp1.get_json()["tool_used"] == "todos"

    resp2 = client.post("/api/chat", json={"message": "show my tasks", "session_id": "test_tasks"})
    assert resp2.status_code == 200
    assert "Deploy to Vercel" in resp2.get_json()["response"]
    print("PASS: Added task and listed tasks via chat!")

    print("\n--- 8. Testing Conversation Memory & Reset ---")
    mem_session = "e2e_mem_session"
    client.post("/api/chat", json={"message": "My name is Alex.", "session_id": mem_session})
    resp = client.post("/api/chat", json={"message": "What is my name?", "session_id": mem_session})
    assert "Alex" in resp.get_json()["response"]
    print("PASS: Session memory recalled name: Alex")

    client.post("/api/reset", json={"session_id": mem_session})
    resp_after = client.post("/api/chat", json={"message": "What is my name?", "session_id": mem_session})
    assert "Alex" not in resp_after.get_json()["response"] or "haven't told me" in resp_after.get_json()["response"]
    print("PASS: Memory successfully cleared after reset.")

    print("\n==========================================")
    print("ALL END-TO-END SERVER TESTS PASSED!!")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
