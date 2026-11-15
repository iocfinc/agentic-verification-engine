"""Read-only order inspection tools for Agentic Verification Engine."""

from __future__ import annotations

from datetime import date
from typing import Any
from langchain_core.tools import tool
from verification_engine.schemas import OrderRecord, OrderItem

# In-memory mock database for simulation
MOCK_ORDERS: dict[str, dict[str, Any]] = {
    "ORD-1001": {
        "order_id": "ORD-1001",
        "customer_id": "CUST-882",
        "order_date": "2026-10-15",
        "delivery_date": "2026-10-18",
        "status": "delivered",
        "items": [
            {
                "sku": "SKU-JACKET-BLK",
                "name": "Waterproof Winter Shell",
                "price": 189.0,
                "is_sale_item": False,
                "is_defective": False,
            }
        ],
    },
    "ORD-2002": {
        "order_id": "ORD-2002",
        "customer_id": "CUST-994",
        "order_date": "2026-08-01",
        "delivery_date": "2026-08-05",
        "status": "delivered",
        "items": [
            {
                "sku": "SKU-BOOTS-BRN",
                "name": "Leather Trail Boots (Clearance)",
                "price": 85.0,
                "is_sale_item": True,
                "is_defective": True,
            }
        ],
    },
}


@tool
def query_order_details(order_id: str) -> dict[str, Any]:
    """Inspect customer order records, delivery dates, and item properties (Read-Only).

    Args:
        order_id: Standard order identifier (e.g. 'ORD-1001').

    Returns:
        Structured order records including item SKU, sale status, and delivery dates.
    """
    clean_id = order_id.strip().upper()
    order = MOCK_ORDERS.get(clean_id)
    if not order:
        return {"error": f"Order {clean_id} not found in database.", "exists": False}
    return {"exists": True, "order": order}
