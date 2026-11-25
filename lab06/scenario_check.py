"""Check that every scenario in spec.md references a valid goal and tool (Lab 6)."""

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE / "spec.md"
VALID_GOALS = {"G0", "G1", "G2", "G3", "G4", "G5", "G6",
               "G1.1", "G1.2", "G1.3", "G2.1", "G2.2"}
VALID_TOOLS = {"get_opening_hours", "get_service_info", "get_test_prep",
               "get_payment_info", "detect_emergency"}

text = SPEC.read_text(encoding="utf-8")
goals_found = set(re.findall(r"\bG\d(?:\.\d)?\b", text))
tools_found = set(re.findall(r"\bget_[a-z_]+\b|detect_[a-z_]+\b", text))

print("Goals referenced:", sorted(goals_found))
print("Tools referenced:", sorted(tools_found))
print("Unknown goals:", sorted(goals_found - VALID_GOALS))
print("Unknown tools:", sorted(tools_found - VALID_TOOLS))
if goals_found <= VALID_GOALS and tools_found <= VALID_TOOLS:
    print("scenario_check: PASS")
else:
    print("scenario_check: FAIL")
    raise SystemExit(1)
