"""Strongly typed Pydantic schemas for data models and verification verdicts."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal
from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    sku: str
    name: str
    price: float
    is_sale_item: bool = False
    is_defective: bool = False


class OrderRecord(BaseModel):
    order_id: str
    customer_id: str
    order_date: date
    delivery_date: date | None = None
    status: Literal["processing", "shipped", "delivered", "returned", "cancelled"]
    items: list[OrderItem] = Field(default_factory=list)


class PolicyRule(BaseModel):
    standard_return_days: int = 30
    sale_item_policy: Literal["exchange_only", "store_credit", "non_refundable"] = "exchange_only"
    defective_item_exception: bool = True  # Defective sale items can receive full refunds


class VerificationVerdict(BaseModel):
    """Structured decision output from the agent."""

    is_eligible: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    decision: Literal["approved", "denied", "escalated_to_human"]
    reasoning: str
    applicable_policy_rule: str
    recommended_action: Literal["none", "refund", "exchange", "human_review"] = "none"
    case_ticket_id: str | None = None
