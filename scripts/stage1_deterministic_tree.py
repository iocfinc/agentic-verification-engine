"""Stage 1: Deterministic Keyword & Logic Tree (The Baseline).

CLI interface for evaluating customer requests using legacy hardcoded string matching.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime


def run_deterministic_verification(
    message: str,
    delivery_date_str: str = "2026-10-20",
    is_sale_item: bool = True,
    current_date_str: str = "2026-11-14",
) -> dict:
    text = message.lower()

    # Brittle keyword check
    defect_keywords = ["defective", "broken", "damaged", "faulty"]
    is_defective = any(w in text for w in defect_keywords)

    delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
    days_elapsed = (current_date - delivery_date).days

    if is_defective:
        if days_elapsed <= 90:
            return {
                "stage": 1,
                "architecture": "Deterministic Keyword Tree",
                "verdict": "APPROVED_FOR_REVIEW",
                "action": "refund",
                "reason": "Matched defective keyword within 90-day warranty window.",
                "failure_risk": "High false negatives if customer uses novel phrasing (e.g., 'seam unraveled').",
            }

    if days_elapsed <= 30:
        if is_sale_item:
            return {
                "stage": 1,
                "architecture": "Deterministic Keyword Tree",
                "verdict": "APPROVED",
                "action": "exchange",
                "reason": "Sale item within standard 30-day window (exchange only).",
                "failure_risk": "Low on structured dates, but cannot negotiate or understand nuances.",
            }
        return {
            "stage": 1,
            "architecture": "Deterministic Keyword Tree",
            "verdict": "APPROVED",
            "action": "refund",
            "reason": "Standard item within 30-day window.",
            "failure_risk": "None for standard window.",
        }

    return {
        "stage": 1,
        "architecture": "Deterministic Keyword Tree",
        "verdict": "ESCALATED_OR_DENIED",
        "action": "escalate",
        "reason": "Exceeded standard window or unrecognized query.",
        "failure_risk": "Bottlenecks human support queue with false rejections.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stage 1: Deterministic Keyword Tree CLI (Baseline)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--query", "-q", required=True, help="Customer message text")
    parser.add_argument("--delivery-date", "-d", default="2026-10-20", help="Item delivery date (YYYY-MM-DD)")
    parser.add_argument("--sale-item", action="store_true", default=True, help="Whether item was on clearance/sale")
    parser.add_argument("--json", action="store_true", help="Output raw JSON for eval runners")

    args = parser.parse_args()

    result = run_deterministic_verification(
        message=args.query,
        delivery_date_str=args.delivery_date,
        is_sale_item=args.sale_item,
    )

    if args.json:
        print(json.dumps(result))
    else:
        print("\n=== STAGE 1: DETERMINISTIC TREE RESULT ===")
        for k, v in result.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
