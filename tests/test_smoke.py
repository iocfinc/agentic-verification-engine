"""Smoke tests for verification engine schemas and simulated tools."""

from verification_engine.schemas import OrderRecord, PolicyRule, VerificationVerdict
from verification_engine.tools.order_tools import query_order_details
from verification_engine.tools.policy_tools import simulate_return_eligibility


def test_schema_defaults():
    verdict = VerificationVerdict(
        is_eligible=True,
        confidence_score=0.95,
        decision="approved",
        reasoning="Test passed",
        applicable_policy_rule="Standard 30-day window",
        recommended_action="refund",
    )
    assert verdict.is_eligible is True
    assert verdict.decision == "approved"


def test_order_tools():
    result = query_order_details.invoke({"order_id": "ORD-1001"})
    assert result.get("exists") is True
    assert result["order"]["customer_id"] == "CUST-882"


def test_policy_tools():
    res = simulate_return_eligibility.invoke(
        {
            "order_date_str": "2026-10-15",
            "delivery_date_str": "2026-10-18",
            "is_sale_item": False,
            "is_defective": False,
            "current_date_str": "2026-10-25",
        }
    )
    assert res is not None
    assert res["eligible"] is True
    assert res["proposed_action"] == "refund"
