"""
The guard: deterministic rule checks (cheap, run first) plus an LLM
intent-match check (runs only once an order has been authorized,
right before the capture/void decision).
"""

import json
from dataclasses import dataclass
from typing import Optional

import httpx

from app import catalog
from app.config import LLM_API_BASE, LLM_API_KEY, LLM_MODEL, require_llm_credentials


@dataclass
class RuleCheckResult:
    decision: str  # "pass" | "nudge" | "blocked"
    reason: str
    alternative: Optional[dict] = None


@dataclass
class IntentCheckResult:
    matches: bool
    reason: str


def check_rules(product: dict, settings: dict, spent_this_month: float) -> RuleCheckResult:
    if product["category"] in settings["blocked_categories"]:
        return RuleCheckResult("blocked", f"'{product['category']}' is a blocked category.")

    if product["price"] > settings["per_purchase_cap"]:
        alt = catalog.cheaper_alternative(product, settings["per_purchase_cap"])
        if alt:
            return RuleCheckResult(
                "nudge",
                f"${product['price']:.2f} exceeds your ${settings['per_purchase_cap']:.2f} per-purchase cap.",
                alternative=alt,
            )
        return RuleCheckResult(
            "blocked", f"${product['price']:.2f} exceeds your ${settings['per_purchase_cap']:.2f} per-purchase cap."
        )

    remaining_budget = settings["monthly_budget"] - spent_this_month
    if product["price"] > remaining_budget:
        alt = catalog.cheaper_alternative(product, max(remaining_budget, 0))
        if alt:
            return RuleCheckResult(
                "nudge",
                f"Only ${remaining_budget:.2f} left in this month's budget.",
                alternative=alt,
            )
        return RuleCheckResult("blocked", f"Only ${remaining_budget:.2f} left in this month's budget.")

    return RuleCheckResult("pass", "Within budget and per-purchase cap.")


_INTENT_SYSTEM_PROMPT = """You are a purchase-intent checker. You are given the user's ORIGINAL \
REQUEST (captured before any shopping happened) and a PRODUCT an agent is about to buy on their \
behalf. Decide whether the product actually satisfies the original request, including any \
specific constraints it mentions (e.g. "unscented", "under $25", a specific brand or color). \
Be strict: a product that contradicts an explicit constraint does NOT match, even if it is in the \
same general category. Respond with ONLY a JSON object: {"matches": true|false, "reason": "..."}"""


def check_intent(product: dict, original_request: str) -> IntentCheckResult:
    require_llm_credentials()

    user_prompt = (
        f"ORIGINAL REQUEST: {original_request}\n\n"
        f"PRODUCT:\n"
        f"name: {product['name']}\n"
        f"category: {product['category']}\n"
        f"price: {product['price']}\n"
        f"description: {product['description']}"
    )

    response = httpx.post(
        f"{LLM_API_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": _INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        },
        timeout=30,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return IntentCheckResult(matches=bool(parsed["matches"]), reason=parsed["reason"])
