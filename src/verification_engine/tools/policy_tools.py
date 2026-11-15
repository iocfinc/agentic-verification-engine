"""Read-only policy simulation and draft verdict tools."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from langchain_core.tools import tool


@tool
def simulate_return_eligibility(
    order_date_str: str,
    delivery_date_str: str,
    is_sale_item: bool,
    is_defective: bool,
    current_date_str: str = "2026-11-14",
) -> dict[str, Any]:
    """Simulate return policy eligibility and calculate proposed resolution without mutating database state.

    Policy Rules:
    1. Standard window: Returns must be within 30 days of delivery.
    2. Sale items: Non-refundable (exchange only), UNLESS the item is verified defective.
    3. Defective items: Qualify for full refund even on sale items if within 90 days.

    Args:
        order_date_str: ISO date string of purchase (YYYY-MM-DD).
        delivery_date_str: ISO date string of delivery (YYYY-MM-DD).
        is_sale_item: Whether the item was marked down on sale.
        is_defective: Whether user reported physical defect/damage.
        current_date_str: Evaluation date (defaults to current system date).

    Returns:
        Structured draft verdict: eligibility, recommended action, and whether human review is required.
    """
    try:
        delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
        eval_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
    except ValueError as e:
        return {"error": f"Invalid date format: {e}", "eligible": False, "requires_human_review": True}

    days_since_delivery = (eval_date - delivery_date).days

    # Defective exception path
    if is_defective:
        if days_since_delivery <= 90:
            return {
                "eligible": True,
                "days_since_delivery": days_since_delivery,
                "proposed_action": "refund",
                "policy_clause": "Section 4.2: Defective Goods Exception (Refund Eligible within 90 days)",
                "requires_human_review": True,  # First iteration: Human executes the actual payment
                "human_review_reason": "First-iteration guardrail: Human approval required to disburse financial refund.",
            }
        else:
            return {
                "eligible": False,
                "days_since_delivery": days_since_delivery,
                "proposed_action": "escalate",
                "policy_clause": "Section 4.3: Defective claim past 90-day threshold",
                "requires_human_review": True,
                "human_review_reason": "Defective claim exceeds 90 days; managerial discretion required.",
            }

    # Standard non-defective return window (30 days)
    if days_since_delivery <= 30:
        if is_sale_item:
            return {
                "eligible": True,
                "days_since_delivery": days_since_delivery,
                "proposed_action": "exchange",
                "policy_clause": "Section 2.1: Final Sale Items are Exchange Only",
                "requires_human_review": False,
            }
        else:
            return {
                "eligible": True,
                "days_since_delivery": days_since_delivery,
                "proposed_action": "refund",
                "policy_clause": "Section 1.1: Standard 30-Day Money-Back Guarantee",
                "requires_human_review": True,
                "human_review_reason": "First-iteration guardrail: Human confirmation of refund disbursement.",
            }

    return {
        "eligible": False,
        "days_since_delivery": days_since_delivery,
        "proposed_action": "deny",
        "policy_clause": "Section 1.2: Returns past 30 days of delivery are ineligible",
        "requires_human_review": False,
    }
