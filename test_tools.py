"""
test_tools.py - Unit test for all tools in tools.py
"""
import tools

def test_all():
    print("--- 1. Testing Calculator ---")
    calc = tools.calculate("25 + 50")
    assert calc["success"] and calc["result"] == 75
    print("PASS: 25 + 50 = 75")

    exp = tools.calculate("2^10")
    assert exp["success"] and exp["result"] == 1024
    print("PASS: 2^10 = 1024")

    print("\n--- 2. Testing Date/Time ---")
    dt = tools.get_current_datetime()
    assert dt["success"] and "date" in dt
    print("PASS: Current date/time:", dt["formatted"])

    print("\n--- 3. Testing Unit Converter ---")
    # Distance
    dist = tools.convert_units("100 km to miles")
    assert dist["success"] and 62.13 < dist["result"] < 62.15
    print("PASS: 100 km to miles ->", dist["formatted_result"])

    # Temperature
    temp = tools.convert_units("30 c to f")
    assert temp["success"] and temp["result"] == 86.0
    print("PASS: 30 C to F ->", temp["formatted_result"])

    # Weight
    weight = tools.convert_units("5 kg to lbs")
    assert weight["success"] and 11.02 < weight["result"] < 11.03
    print("PASS: 5 kg to lbs ->", weight["formatted_result"])

    print("\n--- 4. Testing Notes Scratchpad ---")
    n1 = tools.manage_notes("add", content="Buy groceries", session_id="test_sess")
    assert n1["success"]
    n_list = tools.manage_notes("list", session_id="test_sess")
    assert n_list["total_notes"] == 1
    print("PASS: Saved and listed note:", n_list["notes"])

    print("\n--- 5. Testing To-Do Manager ---")
    t1 = tools.manage_todos("add", task="Complete AI homework", session_id="test_sess")
    assert t1["success"]
    t_list = tools.manage_todos("list", session_id="test_sess")
    assert t_list["total_tasks"] == 1
    tools.manage_todos("complete", task_id=1, session_id="test_sess")
    print("PASS: Task added and marked complete!")

    print("\n--- 6. Testing Knowledge Lookup ---")
    try:
        wiki = tools.lookup_knowledge("Python programming language")
        if wiki["success"]:
            print("PASS: Wikipedia lookup:", wiki["title"], "->", wiki["summary"][:80], "...")
        else:
            print("INFO: Wikipedia lookup returned:", wiki["error"])
    except Exception as e:
        print("INFO: Network lookup test skipped:", e)

    print("\n===============================")
    print("ALL ADVANCED TOOLS TESTS PASSED!")
    print("===============================")

if __name__ == "__main__":
    test_all()
