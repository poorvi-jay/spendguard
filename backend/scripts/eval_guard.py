"""
Scores SpendGuard's guard on evals/guard_cases.json: for each case, the same
rules -> intent-check sequence a real purchase goes through, against the
default settings. Calls the real LLM, so it needs LLM_API_KEY (a run costs
well under a cent with gpt-4o-mini).

Run from backend/:
    python scripts/eval_guard.py            # each case once
    python scripts/eval_guard.py --runs 3   # a case passes only if all 3 runs agree
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
# A throwaway database, so the eval reads the default settings and never touches spendguard.db.
os.environ["DB_PATH"] = str(Path(tempfile.mkdtemp()) / "eval.db")

from app import catalog, core, guard  # noqa: E402

CASES_PATH = BACKEND_DIR / "evals" / "guard_cases.json"


def decide(case: dict) -> tuple[str, str]:
    """The guard's decision for one case, as checkout + confirm_purchase would reach it."""
    product = catalog.get_product(case["product_id"])
    settings = {**core.get_settings(), **case.get("settings", {})}
    rules = guard.check_rules(product, settings, case.get("spent", 0))
    if rules.decision != "pass":
        return rules.decision, rules.reason
    intent = guard.check_intent(product, case["request"])
    return ("approved" if intent.matches else "blocked"), intent.reason


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=1)
    runs = parser.parse_args().runs

    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    passed = 0
    for case in cases:
        results = [decide(case) for _ in range(runs)]
        decisions = [d for d, _ in results]
        ok = all(d == case["expected"] for d in decisions)
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {case['id']:<18} expected {case['expected']:<8} got {', '.join(decisions)}")
        if not ok:
            print(f"      {results[0][1]}")
            if case.get("note"):
                print(f"      note: {case['note']}")

    print(f"\n{passed}/{len(cases)} cases correct ({passed / len(cases):.0%}), {runs} run(s) each")


if __name__ == "__main__":
    main()
