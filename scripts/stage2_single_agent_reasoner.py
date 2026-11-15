"""Stage 2: Single-Agent Dynamic Reasoner with OpenRouter & Typed Tools.

CLI interface for evaluating customer requests using live LLM reasoning and read-only policy simulation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Add src to pythonpath for standalone execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from verification_engine.config import get_model
from verification_engine.schemas import VerificationVerdict
from verification_engine.tools.order_tools import query_order_details
from verification_engine.tools.policy_tools import simulate_return_eligibility


def run_stage2_single_agent(
    order_id: str,
    customer_message: str,
    customer_id: str | None = None,
    model_name: str | None = None,
) -> VerificationVerdict:
    """Run single-agent verification workflow with live OpenRouter model."""
    # 1. Deterministic Order Lookup (Read-Only)
    order_data = query_order_details.invoke({"order_id": order_id})
    if not order_data.get("exists"):
        return VerificationVerdict(
            is_eligible=False,
            confidence_score=1.0,
            decision="denied",
            reasoning=f"Order {order_id} does not exist in store records.",
            applicable_policy_rule="Order Verification Gate",
            recommended_action="none",
        )

    order = order_data["order"]
    item = order["items"][0]

    # 2. Live Agent Semantic Reasoning via OpenRouter
    model = get_model(model_name=model_name)
    prompt = (
        f"You are a policy compliance verifier. Analyze this customer message: '{customer_message}'.\n"
        f"Determine if the customer is reporting a physical product defect, material failure, or damage.\n"
        f"Respond ONLY with a JSON object in this format:\n"
        f'{{"is_defective": true/false, "confidence": 0.0-1.0, "reasoning": "brief explanation"}}\n'
    )
    
    response = model.invoke(prompt)
    content = response.content.strip()
    
    # Strip markdown code blocks if model formatted with ```json
    if content.startswith("```"):
        content = content.strip("`").replace("json\n", "", 1).strip()
    
    try:
        parsed = json.loads(content)
        is_defective = parsed.get("is_defective", False)
        llm_reasoning = parsed.get("reasoning", "LLM semantic extraction")
        confidence = float(parsed.get("confidence", 0.95))
    except Exception as e:
        is_defective = any(w in customer_message.lower() for w in ["detached", "unraveled", "broken", "ripped", "defect"])
        llm_reasoning = f"Direct parse fallback ({e}): extracted defect from message content."
        confidence = 0.85

    # 3. Read-Only Policy Simulation
    policy_sim = simulate_return_eligibility.invoke(
        {
            "order_date_str": order["order_date"],
            "delivery_date_str": order["delivery_date"],
            "is_sale_item": item["is_sale_item"],
            "is_defective": is_defective,
        }
    )

    decision = "approved" if policy_sim["eligible"] else "denied"
    if policy_sim.get("requires_human_review"):
        decision = "escalated_to_human"

    return VerificationVerdict(
        is_eligible=policy_sim["eligible"],
        confidence_score=confidence,
        decision=decision,
        reasoning=(
            f"[OpenRouter: {model.model_name}] {llm_reasoning} | "
            f"Policy Result: {policy_sim.get('policy_clause', '')}. "
            f"{policy_sim.get('human_review_reason', '')}"
        ),
        applicable_policy_rule=policy_sim.get("policy_clause", "Standard Policy"),
        recommended_action=policy_sim.get("proposed_action", "none"),
        case_ticket_id=f"TCK-{order_id}-{customer_id or 'GUEST'}",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stage 2: Single-Agent Dynamic Reasoner CLI (Agentic Verification Engine)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--order-id", "-o", required=True, help="Order ID to evaluate (e.g. ORD-1001)")
    parser.add_argument("--query", "-q", required=True, help="Customer message text or inquiry")
    parser.add_argument("--customer-id", "-c", default=None, help="Optional Customer identifier")
    parser.add_argument("--model", "-m", default=None, help="OpenRouter model (e.g. openai/gpt-4o-mini, anthropic/claude-3.5-sonnet)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON for eval runners")

    args = parser.parse_args()

    verdict = run_stage2_single_agent(
        order_id=args.order_id,
        customer_message=args.query,
        customer_id=args.customer_id,
        model_name=args.model,
    )

    if args.json:
        print(verdict.model_dump_json())
    else:
        print("\n=== STAGE 2: SINGLE AGENT VERIFICATION RESULT ===")
        print(verdict.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
