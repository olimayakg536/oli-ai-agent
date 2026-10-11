"""
test_agent.py - Unit and Integration tests for agent.py
"""
from agent import OliAgent

def test_oli_agent():
    oli = OliAgent()
    session_id = "test_session_123"

    print("--- 1. Testing Calculator Tool Routing ---")
    calc_tests = [
        ("25 + 50", 75),
        ("100 / 4", 25),
        ("15 * 8", 120),
        ("2^10", 1024),
        ("What is 25 + 50?", 75)
    ]
    for msg, expected in calc_tests:
        res = oli.process_message(msg, session_id=session_id)
        assert res["tool_used"] == "calculator", f"Expected calculator for '{msg}', got {res['tool_used']}"
        assert str(expected) in res["response"], f"Expected {expected} in response for '{msg}': {res['response']}"
        print(f"PASS: '{msg}' -> Tool: {res['tool_used']} | Response: {res['response']}")

    print("\n--- 2. Testing Date/Time Tool Routing ---")
    date_tests = ["What is today's date?", "What time is it?"]
    for msg in date_tests:
        res = oli.process_message(msg, session_id=session_id)
        assert res["tool_used"] == "datetime", f"Expected datetime for '{msg}', got {res['tool_used']}"
        assert "October" in res["response"] or "2026" in res["response"] or ":" in res["response"]
        print(f"PASS: '{msg}' -> Tool: {res['tool_used']} | Response: {res['response']}")

    print("\n--- 3. Testing Conversation Memory ---")
    mem_session = "memory_session_abc"
    res1 = oli.process_message("My name is Alex.", session_id=mem_session)
    print("User: 'My name is Alex.' -> Oli:", res1["response"])
    assert "Alex" in res1["response"]

    res2 = oli.process_message("What is my name?", session_id=mem_session)
    print("User: 'What is my name?' -> Oli:", res2["response"])
    assert "Alex" in res2["response"], f"Failed to recall name: {res2['response']}"
    print("PASS: Memory successfully recalled user's name!")

    print("\n--- 4. Testing Empty Input Handling ---")
    res_empty = oli.process_message("   ", session_id=mem_session)
    assert "Please enter a message" in res_empty["response"]
    print("PASS: Empty message properly handled!")

    print("\nAll Agent tests PASSED successfully!")

if __name__ == "__main__":
    test_oli_agent()
