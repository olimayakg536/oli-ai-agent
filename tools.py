"""
tools.py
========
Tool implementations for the Oli AI Agent.

This module provides tools that Oli can use:
1. Safe Calculator: Evaluates mathematical expressions safely using Python's AST
   without dangerous eval().
2. Current Date/Time: Returns formatted local date and time.
3. Unit Converter: Converts length, weight, temperature, and speed units.
4. Notes & Memory Scratchpad: Saves and retrieves session notes.
5. To-Do Manager: Tracks tasks and checklists during the session.
6. Knowledge Lookup: Fetches real-world factual summaries from Wikipedia without API keys.
"""

import ast
import operator
import re
import math
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Union, List, Optional
import requests

# ==============================================================================
# 1. SAFE CALCULATOR (AST-based)
# ==============================================================================

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
    "ceil": math.ceil,
    "floor": math.floor,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log10,
    "ln": math.log,
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval_node(node: ast.AST) -> Union[int, float]:
    """Recursively evaluate an AST node safely."""
    if isinstance(node, ast.Expression):
        return _safe_eval_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Invalid constant type: {type(node.value).__name__}")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")

        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)

        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
            raise ZeroDivisionError("Division by zero is not allowed.")

        if op_type == ast.Pow:
            if isinstance(right, (int, float)) and right > 1000:
                raise ValueError("Exponent too large (maximum allowed exponent is 1000).")
            if isinstance(left, (int, float)) and abs(left) > 1000 and right > 50:
                raise ValueError("Result would be too large to calculate safely.")

        return SAFE_OPERATORS[op_type](left, right)

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _safe_eval_node(node.operand)
        return SAFE_OPERATORS[op_type](operand)

    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in SAFE_FUNCTIONS:
            func = SAFE_FUNCTIONS[node.func.id]
            if callable(func):
                args = [_safe_eval_node(arg) for arg in node.args]
                return func(*args)
        raise ValueError(f"Unsupported function call: {getattr(node.func, 'id', 'unknown')}")

    if isinstance(node, ast.Name):
        if node.id in SAFE_FUNCTIONS and not callable(SAFE_FUNCTIONS[node.id]):
            return SAFE_FUNCTIONS[node.id]
        raise ValueError(f"Unsupported variable or identifier: {node.id}")

    raise ValueError(f"Unsupported syntax expression: {type(node).__name__}")


def clean_math_expression(raw_expr: str) -> str:
    """Clean and extract mathematical expression from user input."""
    expr = raw_expr.strip()
    expr = re.sub(r'^(what is|calculate|compute|solve|how much is)\s+', '', expr, flags=re.IGNORECASE)
    expr = re.sub(r'[\?\.=]+$', '', expr).strip()
    expr = expr.replace('^', '**')
    expr = re.sub(r'(\d+)\s*[xX]\s*(\d+)', r'\1 * \2', expr)
    return expr.strip()


def calculate(expression: str) -> Dict[str, Any]:
    """Safely evaluate a mathematical expression."""
    if not expression or not expression.strip():
        return {
            "success": False,
            "expression": expression,
            "result": None,
            "formatted_result": "",
            "error": "Expression is empty."
        }

    cleaned = clean_math_expression(expression)

    try:
        parsed = ast.parse(cleaned, mode='eval')
        raw_result = _safe_eval_node(parsed)

        if isinstance(raw_result, float) and raw_result.is_integer():
            formatted_result = str(int(raw_result))
            val = int(raw_result)
        elif isinstance(raw_result, float):
            formatted_result = f"{raw_result:.6f}".rstrip('0').rstrip('.')
            val = round(raw_result, 6)
        else:
            formatted_result = str(raw_result)
            val = raw_result

        return {
            "success": True,
            "expression": expression.strip(),
            "cleaned_expression": cleaned,
            "result": val,
            "formatted_result": formatted_result,
            "error": None
        }

    except ZeroDivisionError:
        return {
            "success": False,
            "expression": expression.strip(),
            "cleaned_expression": cleaned,
            "result": None,
            "formatted_result": "",
            "error": "Cannot divide by zero."
        }
    except (SyntaxError, ValueError) as e:
        return {
            "success": False,
            "expression": expression.strip(),
            "cleaned_expression": cleaned,
            "result": None,
            "formatted_result": "",
            "error": f"Invalid expression: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "expression": expression.strip(),
            "cleaned_expression": cleaned,
            "result": None,
            "formatted_result": "",
            "error": f"Calculation error: {str(e)}"
        }


# ==============================================================================
# 2. DATE AND TIME
# ==============================================================================

def get_current_datetime() -> Dict[str, Any]:
    """Get the current local date and time formatted in human-friendly format."""
    now = datetime.now()
    date_str = now.strftime("%A, %B %d, %Y")
    time_str = now.strftime("%I:%M %p").lstrip("0")
    day_str = now.strftime("%A")
    formatted_str = f"{date_str} at {time_str}"

    return {
        "success": True,
        "formatted": formatted_str,
        "date": date_str,
        "time": time_str,
        "day": day_str,
        "iso": now.isoformat()
    }


# ==============================================================================
# 3. UNIT CONVERTER
# ==============================================================================

LENGTH_CONVERSIONS = {
    "m": 1.0,
    "meter": 1.0,
    "meters": 1.0,
    "km": 1000.0,
    "kilometer": 1000.0,
    "kilometers": 1000.0,
    "cm": 0.01,
    "centimeter": 0.01,
    "centimeters": 0.01,
    "mm": 0.001,
    "millimeter": 0.001,
    "millimeters": 0.001,
    "mile": 1609.344,
    "miles": 1609.344,
    "mi": 1609.344,
    "foot": 0.3048,
    "feet": 0.3048,
    "ft": 0.3048,
    "inch": 0.0254,
    "inches": 0.0254,
    "in": 0.0254,
    "yard": 0.9144,
    "yards": 0.9144,
    "yd": 0.9144,
}

WEIGHT_CONVERSIONS = {
    "kg": 1.0,
    "kilogram": 1.0,
    "kilograms": 1.0,
    "g": 0.001,
    "gram": 0.001,
    "grams": 0.001,
    "mg": 0.000001,
    "milligram": 0.000001,
    "lb": 0.45359237,
    "lbs": 0.45359237,
    "pound": 0.45359237,
    "pounds": 0.45359237,
    "oz": 0.028349523,
    "ounce": 0.028349523,
    "ounces": 0.028349523,
}

SPEED_CONVERSIONS = {
    "m/s": 1.0,
    "mps": 1.0,
    "km/h": 0.27777778,
    "kph": 0.27777778,
    "mph": 0.44704,
    "miles/hour": 0.44704,
    "knot": 0.514444,
    "knots": 0.514444,
}


def convert_units(query_or_val: Union[str, float], from_u: str = "", to_u: str = "") -> Dict[str, Any]:
    """
    Convert units of length, weight, speed, or temperature.
    Supports either string query like '100 km to miles', '30 c to f', or direct args.
    """
    val = None
    u_from = from_u.strip().lower()
    u_to = to_u.strip().lower()

    if isinstance(query_or_val, str) and (not u_from or not u_to):
        # Extract e.g. "convert 100 km to miles" or "100 km in miles"
        match = re.search(
            r'[-+]?\d*\.?\d+\s*([a-zA-Z/°]+)\s+(?:to|in|into)\s+([a-zA-Z/°]+)',
            query_or_val,
            re.IGNORECASE
        )
        if match:
            num_match = re.search(r'[-+]?\d*\.?\d+', query_or_val)
            if num_match:
                val = float(num_match.group(0))
                u_from = match.group(1).lower().strip('°')
                u_to = match.group(2).lower().strip('°')
        else:
            return {
                "success": False,
                "error": "Could not parse unit conversion pattern (e.g. '100 km to miles', '30 C to F')."
            }
    else:
        try:
            val = float(query_or_val)
        except (ValueError, TypeError):
            return {"success": False, "error": "Invalid numerical value for conversion."}

    # Normalize unit aliases
    temp_aliases = {"c": "celsius", "celsius": "celsius", "f": "fahrenheit", "fahrenheit": "fahrenheit", "k": "kelvin", "kelvin": "kelvin"}

    # 1. Temperature Conversion
    if u_from in temp_aliases and u_to in temp_aliases:
        src = temp_aliases[u_from]
        dst = temp_aliases[u_to]

        # Convert to Celsius first
        if src == "celsius":
            c_val = val
        elif src == "fahrenheit":
            c_val = (val - 32) * 5.0 / 9.0
        elif src == "kelvin":
            c_val = val - 273.15
        else:
            c_val = val

        # Convert from Celsius to destination
        if dst == "celsius":
            res = c_val
        elif dst == "fahrenheit":
            res = (c_val * 9.0 / 5.0) + 32
        elif dst == "kelvin":
            res = c_val + 273.15

        res_formatted = f"{res:.2f}".rstrip('0').rstrip('.')
        return {
            "success": True,
            "original_value": val,
            "from_unit": src.capitalize(),
            "to_unit": dst.capitalize(),
            "result": round(res, 4),
            "formatted_result": f"{val}° {src.capitalize()} = {res_formatted}° {dst.capitalize()}"
        }

    # 2. Length Conversion
    if u_from in LENGTH_CONVERSIONS and u_to in LENGTH_CONVERSIONS:
        in_meters = val * LENGTH_CONVERSIONS[u_from]
        res = in_meters / LENGTH_CONVERSIONS[u_to]
        res_formatted = f"{res:.4f}".rstrip('0').rstrip('.')
        return {
            "success": True,
            "original_value": val,
            "from_unit": u_from,
            "to_unit": u_to,
            "result": round(res, 4),
            "formatted_result": f"{val} {u_from} = {res_formatted} {u_to}"
        }

    # 3. Weight Conversion
    if u_from in WEIGHT_CONVERSIONS and u_to in WEIGHT_CONVERSIONS:
        in_kg = val * WEIGHT_CONVERSIONS[u_from]
        res = in_kg / WEIGHT_CONVERSIONS[u_to]
        res_formatted = f"{res:.4f}".rstrip('0').rstrip('.')
        return {
            "success": True,
            "original_value": val,
            "from_unit": u_from,
            "to_unit": u_to,
            "result": round(res, 4),
            "formatted_result": f"{val} {u_from} = {res_formatted} {u_to}"
        }

    # 4. Speed Conversion
    if u_from in SPEED_CONVERSIONS and u_to in SPEED_CONVERSIONS:
        in_mps = val * SPEED_CONVERSIONS[u_from]
        res = in_mps / SPEED_CONVERSIONS[u_to]
        res_formatted = f"{res:.2f}".rstrip('0').rstrip('.')
        return {
            "success": True,
            "original_value": val,
            "from_unit": u_from,
            "to_unit": u_to,
            "result": round(res, 4),
            "formatted_result": f"{val} {u_from} = {res_formatted} {u_to}"
        }

    return {
        "success": False,
        "error": f"Cannot convert between '{u_from}' and '{u_to}' (incompatible or unsupported unit types)."
    }


# ==============================================================================
# 4. NOTES & MEMORY SCRATCHPAD
# ==============================================================================

# In-memory session notes storage
_SESSION_NOTES: Dict[str, List[str]] = {}

def manage_notes(action: str, content: str = "", note_id: Optional[int] = None, session_id: str = "default") -> Dict[str, Any]:
    """
    Manage user scratchpad notes.
    action: 'add', 'list', 'delete', 'clear'
    """
    if session_id not in _SESSION_NOTES:
        _SESSION_NOTES[session_id] = []

    notes = _SESSION_NOTES[session_id]

    if action == "add":
        clean_text = content.strip()
        if not clean_text:
            return {"success": False, "error": "Note content cannot be empty."}
        notes.append(clean_text)
        return {
            "success": True,
            "action": "add",
            "note": clean_text,
            "total_notes": len(notes),
            "message": f"Saved note #{len(notes)}: '{clean_text}'"
        }

    elif action == "list":
        return {
            "success": True,
            "action": "list",
            "notes": notes,
            "total_notes": len(notes),
            "message": f"You have {len(notes)} saved note(s)."
        }

    elif action == "delete":
        if note_id is not None and 1 <= note_id <= len(notes):
            deleted = notes.pop(note_id - 1)
            return {
                "success": True,
                "action": "delete",
                "deleted_note": deleted,
                "total_notes": len(notes),
                "message": f"Deleted note #{note_id}: '{deleted}'"
            }
        return {"success": False, "error": f"Note #{note_id} not found."}

    elif action == "clear":
        _SESSION_NOTES[session_id] = []
        return {
            "success": True,
            "action": "clear",
            "message": "All notes for this session have been cleared."
        }

    return {"success": False, "error": f"Unknown action: {action}"}


# ==============================================================================
# 5. TO-DO & TASK MANAGER
# ==============================================================================

# In-memory session tasks storage
_SESSION_TODOS: Dict[str, List[Dict[str, Any]]] = {}

def manage_todos(action: str, task: str = "", task_id: Optional[int] = None, session_id: str = "default") -> Dict[str, Any]:
    """
    Manage user tasks/to-dos.
    action: 'add', 'list', 'complete', 'delete'
    """
    if session_id not in _SESSION_TODOS:
        _SESSION_TODOS[session_id] = []

    todos = _SESSION_TODOS[session_id]

    if action == "add":
        clean_task = task.strip()
        if not clean_task:
            return {"success": False, "error": "Task description cannot be empty."}
        item = {"task": clean_task, "done": False, "created_at": datetime.now().strftime("%I:%M %p")}
        todos.append(item)
        return {
            "success": True,
            "action": "add",
            "item": item,
            "total_tasks": len(todos),
            "message": f"Added task #{len(todos)}: '{clean_task}'"
        }

    elif action == "list":
        return {
            "success": True,
            "action": "list",
            "todos": todos,
            "total_tasks": len(todos),
            "message": f"You have {len(todos)} task(s)."
        }

    elif action == "complete":
        if task_id is not None and 1 <= task_id <= len(todos):
            todos[task_id - 1]["done"] = True
            return {
                "success": True,
                "action": "complete",
                "task_id": task_id,
                "task": todos[task_id - 1]["task"],
                "message": f"Marked task #{task_id} as completed!"
            }
        return {"success": False, "error": f"Task #{task_id} not found."}

    elif action == "delete":
        if task_id is not None and 1 <= task_id <= len(todos):
            deleted = todos.pop(task_id - 1)
            return {
                "success": True,
                "action": "delete",
                "deleted": deleted["task"],
                "message": f"Removed task #{task_id}: '{deleted['task']}'"
            }
        return {"success": False, "error": f"Task #{task_id} not found."}

    return {"success": False, "error": f"Unknown action: {action}"}


# ==============================================================================
# 6. KNOWLEDGE & WIKIPEDIA LOOKUP
# ==============================================================================

def lookup_knowledge(query: str) -> Dict[str, Any]:
    """
    Fetch factual summary from Wikipedia REST API.
    Zero API key required.
    """
    clean_query = query.strip()
    clean_query = re.sub(r'^(who is|what is|tell me about|explain|search|lookup)\s+', '', clean_query, flags=re.IGNORECASE)
    clean_query = clean_query.strip().rstrip('?.')

    if not clean_query:
        return {"success": False, "error": "Search query cannot be empty."}

    headers = {"User-Agent": "OliAIAgent/2.0 (https://github.com; contact: oli@example.com)"}

    # 1. Try direct page summary
    encoded_title = urllib.parse.quote(clean_query.replace(' ', '_'))
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"

    try:
        resp = requests.get(summary_url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            title = data.get("title", clean_query)
            extract = data.get("extract", "")
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{encoded_title}")
            thumbnail = data.get("thumbnail", {}).get("source", None)

            if extract:
                return {
                    "success": True,
                    "title": title,
                    "summary": extract,
                    "url": page_url,
                    "thumbnail": thumbnail,
                    "message": f"**{title}**: {extract}"
                }

        # 2. If direct title 404s, use opensearch API to find the closest match
        search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(clean_query)}&limit=1&namespace=0&format=json"
        s_resp = requests.get(search_url, headers=headers, timeout=6)
        if s_resp.status_code == 200:
            s_data = s_resp.json()
            # format: [query, [titles], [descriptions], [urls]]
            if len(s_data) >= 4 and s_data[1]:
                matched_title = s_data[1][0]
                matched_desc = s_data[2][0] if s_data[2] else ""
                matched_url = s_data[3][0] if s_data[3] else ""

                if matched_title:
                    # Fetch summary of matched title
                    sec_resp = requests.get(
                        f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(matched_title.replace(' ', '_'))}",
                        headers=headers,
                        timeout=6
                    )
                    if sec_resp.status_code == 200:
                        sec_data = sec_resp.json()
                        return {
                            "success": True,
                            "title": sec_data.get("title", matched_title),
                            "summary": sec_data.get("extract", matched_desc),
                            "url": sec_data.get("content_urls", {}).get("desktop", {}).get("page", matched_url),
                            "thumbnail": sec_data.get("thumbnail", {}).get("source", None),
                            "message": f"**{matched_title}**: {sec_data.get('extract', matched_desc)}"
                        }

        return {
            "success": False,
            "query": clean_query,
            "error": f"No knowledge entry found for '{clean_query}'."
        }

    except Exception as e:
        return {
            "success": False,
            "query": clean_query,
            "error": f"Failed to retrieve knowledge: {str(e)}"
        }
